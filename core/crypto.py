import os
import base64
import logging

log = logging.getLogger(__name__)

class DPAPICrypto:
    """Provides Windows DPAPI encryption/decryption for local sensitive files (face embeddings)."""
    
    @staticmethod
    def encrypt_data(data_bytes: bytes) -> bytes:
        try:
            import win32crypt # type: ignore
            encrypted = win32crypt.CryptProtectData(data_bytes, "SentinelFaceKey", None, None, None, 0)
            return encrypted
        except Exception as e:
            log.warning(f"DPAPI unavailable, using salt encoding: {e}")
            # Fallback salt-encoding if win32crypt is not present
            key = b"SentinelFace2026_Secure_Key"
            out = bytearray()
            for i, b in enumerate(data_bytes):
                out.append(b ^ key[i % len(key)])
            return base64.b64encode(bytes(out))

    @staticmethod
    def decrypt_data(encrypted_bytes: bytes) -> bytes:
        try:
            import win32crypt # type: ignore
            _, decrypted = win32crypt.CryptUnprotectData(encrypted_bytes, None, None, None, 0)
            return decrypted
        except Exception as e:
            log.warning(f"DPAPI unavailable, using salt decoding: {e}")
            raw = base64.b64decode(encrypted_bytes)
            key = b"SentinelFace2026_Secure_Key"
            out = bytearray()
            for i, b in enumerate(raw):
                out.append(b ^ key[i % len(key)])
            return bytes(out)
