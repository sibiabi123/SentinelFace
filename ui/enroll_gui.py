import os
import sys
import cv2
import time
import logging
from pathlib import Path

log = logging.getLogger(__name__)
ENROLL_DIR = Path(os.environ.get("USERPROFILE", ".")) / ".sentinelface" / "enroll"
ALT_ENROLL_DIR = Path(os.environ.get("USERPROFILE", ".")) / ".face-unlock" / "enroll"

def run_face_enrollment(count: int = 15):
    ENROLL_DIR.mkdir(parents=True, exist_ok=True)
    ALT_ENROLL_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("      SENTINELFACE — FACE ENROLLMENT WIZARD      ")
    print("=" * 60)
    print("\nStarting webcam feed... Please look directly into your camera.")
    print("Move your head slightly (center, left, right, tilt).")
    print("Press SPACEBAR to capture photos, or ESC to exit.\n")

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("ERROR: Could not open camera.")
        return False

    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    captured_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

        display = frame.copy()
        cv2.putText(display, f"Captured: {captured_count}/{count} (Press SPACE to capture)", (20, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        for (x, y, w, h) in faces:
            cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.imshow("SentinelFace Enrollment - Look at Camera (SPACE = Capture)", display)

        key = cv2.waitKey(1) & 0xFF
        if key == 32:  # SPACE
            if len(faces) > 0:
                captured_count += 1
                img_name = f"face_{captured_count:02d}.jpg"
                path1 = ENROLL_DIR / img_name
                path2 = ALT_ENROLL_DIR / img_name
                cv2.imwrite(str(path1), frame)
                cv2.imwrite(str(path2), frame)
                print(f"[{captured_count}/{count}] Face captured: {img_name}")
                if captured_count >= count:
                    print("\n[SUCCESS] Enrollment photo capture completed!")
                    break
            else:
                print("No face detected in frame. Please align your face!")
        elif key == 27:  # ESC
            print("Enrollment cancelled.")
            break

    cap.release()
    cv2.destroyAllWindows()
    return captured_count > 0

if __name__ == "__main__":
    run_face_enrollment()
