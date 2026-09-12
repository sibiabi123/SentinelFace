import base64
import logging

log = logging.getLogger(__name__)


class DPAPICrypto:
    """Windows DPAPI encryption for the local face-embedding file.

    On Windows with pywin32 installed, this uses the real per-user DPAPI key
    (CryptProtectData), so the encrypted file is only readable by your own
    Windows account. The XOR fallback below only exists so this module can
    be imported/tested on non-Windows machines - it is NOT secure and should
    never be relied on for a real deployment. It logs loudly if it's used.
    """

    @staticmethod
    def encrypt_data(data_bytes: bytes) -> bytes:
        try:
            import win32crypt  # type: ignore
            return win32crypt.CryptProtectData(data_bytes, "SentinelFaceKey", None, None, None, 0)
        except Exception as e:
            log.warning(
                f"DPAPI (win32crypt) unavailable - using a WEAK fallback encoding instead "
                f"of real encryption. Do not treat this as secure. ({e})"
            )
            key = b"SentinelFace2026_Secure_Key"
            out = bytearray(b ^ key[i % len(key)] for i, b in enumerate(data_bytes))
            return base64.b64encode(bytes(out))

    @staticmethod
    def decrypt_data(encrypted_bytes: bytes) -> bytes:
        try:
            import win32crypt  # type: ignore
            _, decrypted = win32crypt.CryptUnprotectData(encrypted_bytes, None, None, None, 0)
            return decrypted
        except Exception as e:
            log.warning(f"DPAPI unavailable - decoding with the WEAK fallback path. ({e})")
            raw = base64.b64decode(encrypted_bytes)
            key = b"SentinelFace2026_Secure_Key"
            out = bytearray(b ^ key[i % len(key)] for i, b in enumerate(raw))
            return bytes(out)
