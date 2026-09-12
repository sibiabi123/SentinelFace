import os
import sys
import argparse
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

log_file = BASE_DIR / "sentinelface.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s [%(name)s]: %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

log = logging.getLogger("SentinelFace")

def main():
    parser = argparse.ArgumentParser(description="SentinelFace — 10x Continuous Face Authentication System")
    parser.add_argument("--dashboard", action="store_true", help="Launch PySide6 Control Center Dashboard")
    parser.add_argument("--enroll", action="store_true", help="Launch Face Enrollment Wizard")
    parser.add_argument("--verify", action="store_true", help="Run instant verification check")
    parser.add_argument("--autostart", action="store_true", help="Register Task Scheduler autostart")
    args = parser.parse_args()

    log.info("Starting SentinelFace System...")

    if args.autostart:
        from core.autostart import AutostartManager
        AutostartManager.register_autostart()
        print("Registered Task Scheduler autostart.")
        return

    if args.dashboard:
        try:
            from ui.dashboard_pyside import main as dashboard_main
            dashboard_main()
        except Exception as e:
            log.warning(f"PySide6 dashboard fallback to Tkinter: {e}")
            from ui.dashboard import SentinelDashboard
            app = SentinelDashboard()
            app.mainloop()
    elif args.enroll:
        from ui.enroll_gui import run_face_enrollment
        run_face_enrollment()
    elif args.verify:
        from database.db import AuditDatabase
        from core.verifier import VerificationEngine
        db = AuditDatabase()
        verifier = VerificationEngine(db)
        res = verifier.run_verification(is_manual_check=True)
        print("\nVerification Result:", res)
    else:
        # Default: Run System Tray & Background Scheduler
        from ui.tray import SentinelTrayApp
        app = SentinelTrayApp()
        app.run()

if __name__ == "__main__":
    main()
