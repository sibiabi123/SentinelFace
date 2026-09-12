import os
import logging
import numpy as np
from pathlib import Path

log = logging.getLogger(__name__)

APPDATA_DIR = Path(os.environ.get("USERPROFILE", ".")) / ".sentinelface"
EMBEDDINGS_FILE = APPDATA_DIR / "embeddings.enc"
EMBEDDINGS_META = APPDATA_DIR / "embeddings.meta"


class RecognitionError(Exception):
    """Raised when the recognition backend itself cannot be trusted to give an
    answer (import failure, model crash, corrupted profile, etc).

    Callers MUST treat this as a FAILED verification, never as an automatic
    pass. The previous version of this file did the opposite: if DeepFace
    failed to import or crashed for any reason, it fell back to "any face
    detected = match", which meant a stranger's face would pass whenever the
    ML backend hiccuped. That is a fail-open bug in a security tool and is
    the single most important thing fixed in this rewrite.
    """
    pass


class FaceRecognizer:
    def __init__(self, threshold: float = 0.60, model_name: str = "ArcFace",
                 min_agreement: int = 2):
        self.threshold = threshold          # cosine distance; LOWER = stricter
        self.model_name = model_name
        self.min_agreement = min_agreement  # how many enrolled samples must independently agree
        self._enrolled_embeddings = None

    # ---------- enrollment storage ----------

    def is_enrolled(self) -> bool:
        return EMBEDDINGS_FILE.exists() and EMBEDDINGS_META.exists()

    def _load_embeddings(self) -> list:
        if self._enrolled_embeddings is not None:
            return self._enrolled_embeddings
        if not self.is_enrolled():
            return []
        from core.crypto import DPAPICrypto
        try:
            dim = int(EMBEDDINGS_META.read_text().strip())
            decrypted = DPAPICrypto.decrypt_data(EMBEDDINGS_FILE.read_bytes())
            arr = np.frombuffer(decrypted, dtype=np.float64).reshape(-1, dim)
            self._enrolled_embeddings = [row for row in arr]
        except Exception as e:
            log.error(f"Failed to load/decrypt enrolled face profile: {e}")
            self._enrolled_embeddings = []
        return self._enrolled_embeddings

    def save_embeddings(self, embeddings: list):
        from core.crypto import DPAPICrypto
        arr = np.array(embeddings, dtype=np.float64)
        APPDATA_DIR.mkdir(parents=True, exist_ok=True)
        EMBEDDINGS_META.write_text(str(arr.shape[1]))
        EMBEDDINGS_FILE.write_bytes(DPAPICrypto.encrypt_data(arr.tobytes()))
        self._enrolled_embeddings = list(arr)
        log.info(f"Saved {len(embeddings)} encrypted face embeddings to {EMBEDDINGS_FILE}.")

    # ---------- inference ----------

    def compute_embedding(self, frame: np.ndarray):
        """Returns an embedding vector for the given frame, or None if no
        usable face is found in THIS frame (that's normal, not an error).
        Raises RecognitionError only for genuine backend failure - callers
        must fail closed on that, not fall back to a pass."""
        try:
            from deepface import DeepFace
        except Exception as e:
            raise RecognitionError(f"face recognition backend unavailable ({e})")
        try:
            reps = DeepFace.represent(
                img_path=frame,
                model_name=self.model_name,
                enforce_detection=True,
                detector_backend="opencv",
            )
            if not reps:
                return None
            return np.array(reps[0]["embedding"], dtype=np.float64)
        except ValueError:
            # DeepFace raises ValueError when it simply can't find a face -
            # that's a "no face this frame" case, not a backend failure.
            return None
        except RecognitionError:
            raise
        except Exception as e:
            raise RecognitionError(f"embedding extraction failed ({e})")

    @staticmethod
    def _cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
        a = a / (np.linalg.norm(a) + 1e-9)
        b = b / (np.linalg.norm(b) + 1e-9)
        return float(1.0 - np.dot(a, b))

    def verify_embedding(self, embedding: np.ndarray) -> tuple:
        """
        Compares one probe embedding against every enrolled embedding.
        Returns (matched, best_distance, num_agreeing).

        matched requires at least `min_agreement` enrolled samples to
        independently fall within threshold - a single near-miss embedding
        can no longer flip a whole verification, unlike the original
        "break on first match against the first 3 files" logic.
        """
        enrolled = self._load_embeddings()
        if not enrolled:
            return False, 1.0, 0
        distances = sorted(self._cosine_distance(embedding, e) for e in enrolled)
        num_agreeing = sum(1 for d in distances if d <= self.threshold)
        matched = num_agreeing >= min(self.min_agreement, len(enrolled))
        return matched, distances[0], num_agreeing
