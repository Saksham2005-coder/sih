from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any

class DigitalSignatureProvider(ABC):
    """
    Abstract integration boundary for cryptographic signing providers.
    Production integration requires an authorized Controller of Certifying Authorities (CCA)
    licensed DSC provider or UIDAI/CDAC/NIC Aadhaar e-Sign ESP service.
    """

    @abstractmethod
    def sign_document(self, document_bytes: bytes, metadata: Dict[str, Any]) -> Tuple[bytes, Dict[str, Any]]:
        """
        Signs document bytes using cryptographic hardware security module (HSM) or e-Sign service.
        Returns (signed_document_bytes, signature_telemetry).
        """
        pass

    @abstractmethod
    def verify_signature(self, document_bytes: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verifies embedded CMS/PKCS#7 cryptographic signature against trusted trust anchors.
        Returns verification details.
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Returns the identifier of the configured signing service."""
        pass


class PrototypeUnsignedProvider(DigitalSignatureProvider):
    """
    Default prototype provider.
    Strictly preserves raw generated PDF bytes and marks artifact as UNSIGNED_PROTOTYPE.
    Never fabricates a signer identity or simulates cryptographic digital certificates.
    """

    def sign_document(self, document_bytes: bytes, metadata: Dict[str, Any]) -> Tuple[bytes, Dict[str, Any]]:
        signing_telemetry = {
            "signature_status": "UNSIGNED_PROTOTYPE",
            "signing_provider": "NONE_PROTOTYPE_MODE",
            "is_cryptographically_signed": False,
            "certificate_present": False,
            "signer_identity": None,
            "legal_status": "UNSIGNED_PROTOTYPE_ARTIFACT",
            "disclaimer": (
                "Prototype document generated in evaluation mode. In accordance with Section 3A "
                "of the Information Technology Act, 2000, this document does NOT carry a legal "
                "cryptographic digital signature. Official statutory issuance requires integration "
                "with an authorized CCA-licensed DSC / Aadhaar e-Sign provider."
            )
        }
        return document_bytes, signing_telemetry

    def verify_signature(self, document_bytes: bytes, metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "signature_status": "UNSIGNED_PROTOTYPE",
            "is_valid_signature": False,
            "verification_error": "No cryptographic certificate attached; artifact is an unsigned prototype."
        }

    def get_provider_name(self) -> str:
        return "NONE_PROTOTYPE_MODE"


def get_signature_provider() -> DigitalSignatureProvider:
    """
    Factory resolving configured digital signature provider.
    Fails closed to PrototypeUnsignedProvider in prototype mode.
    """
    return PrototypeUnsignedProvider()
