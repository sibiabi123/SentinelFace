import cv2
import logging

from ai.detector import FaceDetector
from ai.recognizer import FaceRecognizer, RecognitionError

log = logging.getLogger(__name__)


def run_face_enrollment(count: int = 15) -> bool:
    detector = FaceDetector()
    recognizer = FaceRecognizer()

    print("=" * 60)
    print("      SENTINELFACE — FACE ENROLLMENT WIZARD      ")
    print("=" * 60)
    print("\nLook directly at the camera. Move your head slightly between")
    print("captures (center / left / right / tilt) for a more robust profile.")
    print("Press SPACE to capture, ESC to cancel.\n")

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("ERROR: Could not open camera.")
        return False

    embeddings = []
    captured = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            norm = detector.normalize_lighting(frame)
            faces = detector.detect_faces(norm)

            display = frame.copy()
            cv2.putText(display, f"Captured: {captured}/{count}  (SPACE = capture, ESC = quit)",
                        (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            for (x, y, w, h) in faces:
                cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.imshow("SentinelFace Enrollment", display)

            key = cv2.waitKey(1) & 0xFF
            if key == 32:  # SPACE
                if len(faces) == 0:
                    print("No face detected — please align your face in frame.")
                    continue
                try:
                    emb = recognizer.compute_embedding(norm)
                except RecognitionError as e:
                    print(f"Recognition backend error, cannot enroll right now: {e}")
                    continue
                if emb is None:
                    print("Could not extract a clear face embedding, try again.")
                    continue
                embeddings.append(emb)
                captured += 1
                print(f"[{captured}/{count}] sample captured.")
                if captured >= count:
                    print("\n[SUCCESS] Enough samples captured.")
                    break
            elif key == 27:  # ESC
                print("Enrollment cancelled.")
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

    min_needed = max(3, count // 3)
    if len(embeddings) < min_needed:
        print(f"Only {len(embeddings)} usable sample(s) captured (need at least {min_needed}). Not saving.")
        return False

    recognizer.save_embeddings(embeddings)
    print(f"Enrollment complete: {len(embeddings)} encrypted embeddings saved. No raw face photos were kept on disk.")
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_face_enrollment()
