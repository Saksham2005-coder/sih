import hashlib
import os
import uuid
import re
from typing import Tuple, Dict, Any, Optional
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/pjpeg"
}

# Magic bytes signature lookup
MAGIC_SIGNATURES = {
    b"%PDF-": ("application/pdf", ".pdf"),
    b"\x89PNG\r\n\x1a\n": ("image/png", ".png"),
    b"\xff\xd8\xff": ("image/jpeg", ".jpg"),
}

def calculate_sha256_bytes(file_bytes: bytes) -> str:
    """Calculates SHA-256 integrity hash of bytes."""
    sha256 = hashlib.sha256()
    sha256.update(file_bytes)
    return sha256.hexdigest()

def detect_magic_signature(file_bytes: bytes) -> Optional[Tuple[str, str]]:
    """Detects content type by inspecting binary signature (magic bytes)."""
    if file_bytes.startswith(b"%PDF-"):
        return ("application/pdf", ".pdf")
    if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return ("image/png", ".png")
    if file_bytes.startswith(b"\xff\xd8\xff"):
        return ("image/jpeg", ".jpg")
    return None

def sanitize_filename(filename: str) -> str:
    """
    Sanitizes user-supplied filename to prevent directory traversal and special character injection.
    """
    # Extract basename only (strips ../ or \ traversal attempts)
    clean = os.path.basename(filename or "document.pdf")
    # Replace anything not alphanumeric, underscore, hyphen, or dot
    clean = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', clean)
    # Ensure not empty
    if not clean or clean.startswith('.'):
        clean = f"doc_{clean}"
    return clean

class StorageService:
    """
    Secure file storage service handling validation, content verification,
    safe storage keys, and transaction consistency.
    """

    @staticmethod
    def validate_and_save(file: UploadFile) -> Dict[str, Any]:
        """
        Validates size, extension, MIME, and magic bytes.
        Writes to local storage and returns structured metadata.
        """
        raw_name = file.filename or "uploaded_document.pdf"
        sanitized_name = sanitize_filename(raw_name)
        ext = os.path.splitext(sanitized_name)[1].lower()

        # 1. Extension check
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        # Read bytes
        file_bytes = file.file.read()
        file_size = len(file_bytes)

        # 2. Maximum file size check
        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            max_mb = settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum allowed size of {max_mb:.1f} MB (uploaded: {file_size / (1024*1024):.2f} MB)"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes)."
            )

        # 3. Content signature (magic bytes) validation
        detected = detect_magic_signature(file_bytes)
        if not detected:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File content signature validation failed. Content does not match expected PDF or image format."
            )

        detected_mime, _ = detected

        # 4. Content-Type header check
        content_type = (file.content_type or detected_mime).lower()
        if content_type not in ALLOWED_MIME_TYPES and detected_mime not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported MIME type '{content_type}'. Allowed types: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
            )

        # 5. Calculate integrity checksum
        checksum = calculate_sha256_bytes(file_bytes)

        # 6. Generate random storage key and safe path
        storage_key = f"{uuid.uuid4().hex}_{sanitized_name}"
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        target_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, storage_key))

        # Enforce target_path is strictly inside UPLOAD_DIR
        base_upload = os.path.abspath(settings.UPLOAD_DIR)
        if not target_path.startswith(base_upload):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file path detected."
            )

        try:
            with open(target_path, "wb") as f:
                f.write(file_bytes)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to persist file to storage: {str(e)}"
            )

        file_url = f"/api/documents/download/{storage_key}"

        return {
            "file_name": sanitized_name,
            "file_url": file_url,
            "storage_key": storage_key,
            "checksum_sha256": checksum,
            "file_size": file_size,
            "mime_type": detected_mime,
            "local_path": target_path
        }

    @staticmethod
    def cleanup_file(storage_key_or_path: str) -> bool:
        """Deletes file from disk in case of transaction failure or cleanup."""
        try:
            if os.path.isabs(storage_key_or_path):
                path = storage_key_or_path
            else:
                path = os.path.join(settings.UPLOAD_DIR, os.path.basename(storage_key_or_path))
            if os.path.exists(path):
                os.remove(path)
                return True
        except Exception:
            pass
        return False

# Backward compatibility helper
def save_uploaded_file(file: UploadFile) -> Tuple[str, str, str]:
    meta = StorageService.validate_and_save(file)
    return meta["file_name"], meta["file_url"], meta["checksum_sha256"]
