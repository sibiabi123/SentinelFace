import sys
import argparse
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s]: %(message)s",
    handlers=[
        logging.FileHandler(BASE_DIR / "sentinelface.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("SentinelFace")


def main():
    parser = argparse.ArgumentParser(description="SentinelFace — continuous face authentication for a plain RGB webcam")
    parser.add_argument("--dashboard", action="store_true", help="Launch the dashboard GUI")
    parser.add_argument("--enroll", action="store_true", help="Run the face enrollment wizard")
    parser.add_argument("--verify", action="store_true", help="Run a single instant verification check")
    parser.add_argument("--register-autostart", action="store_true", help="Run SentinelFace automatically at Windows logon")
    parser.add_argument("--remove-autostart", action="store_true", help="Remove the autostart task")
    args = parser.parse_args()

    log.info("Starting SentinelFace...")

    if args.dashboard:
        from ui.dashboard import SentinelDashboard
        SentinelDashboard().mainloop()
    elif args.enroll:
        from ui.enroll_gui import run_face_enrollment
        run_face_enrollment()
    elif args.verify:
        from database.db import AuditDatabase
        from core.verifier import VerificationEngine
        db = AuditDatabase()
        result = VerificationEngine(db).run_verification(is_manual_check=True)
        print("\nVerification Result:", result)
    elif args.register_autostart:
        from core.autostart import register_autostart
        ok = register_autostart(str(BASE_DIR / "main.py"))
        print("Autostart registered." if ok else "Failed to register autostart - see sentinelface.log")
    elif args.remove_autostart:
        from core.autostart import remove_autostart
        ok = remove_autostart()
        print("Autostart removed." if ok else "Failed to remove autostart - see sentinelface.log")
    else:
        from ui.tray import SentinelTrayApp
        SentinelTrayApp().run()


if __name__ == "__main__":
    main()
