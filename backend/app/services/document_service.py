import hashlib
import os
import uuid
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

def calculate_sha256_bytes(file_bytes: bytes) -> str:
    sha256 = hashlib.sha256()
    sha256.update(file_bytes)
    return sha256.hexdigest()

def save_uploaded_file(file: UploadFile) -> Tuple[str, str, str]:
    """
    Reads file, calculates SHA-256, writes to storage, returns (file_name, file_url, checksum_sha256)
    """
    file_bytes = file.file.read()
    if len(file_bytes) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024):.1f} MB"
        )
    
    checksum = calculate_sha256_bytes(file_bytes)
    original_name = os.path.basename(file.filename or "uploaded_document.pdf")
    ext = os.path.splitext(original_name)[1]
    safe_filename = f"{uuid.uuid4().hex}_{original_name}"
    target_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    
    with open(target_path, "wb") as f:
        f.write(file_bytes)
        
    file_url = f"/api/documents/download/{safe_filename}"
    return original_name, file_url, checksum
