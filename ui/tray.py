import sys
import json
import threading
import time
import logging
from pathlib import Path
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem

from database.db import AuditDatabase
from core.verifier import VerificationEngine
from core.notifications import set_tray_icon, notify

log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.json"


def create_icon_image():
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((4, 4, 60, 60), fill="#1e1e2e", outline="#89b4fa", width=3)
    draw.rectangle((22, 28, 42, 48), fill="#89b4fa")
    draw.arc((24, 16, 40, 32), start=180, end=360, fill="#89b4fa", width=3)
    return img


class SentinelTrayApp:
    def __init__(self):
        self.db = AuditDatabase()
        self.verifier = VerificationEngine(self.db)
        self.stop_event = threading.Event()
        self.icon = None

    def get_interval(self) -> int:
        try:
            if CONFIG_PATH.exists():
                return json.loads(CONFIG_PATH.read_text()).get("presence_interval_s", 900)
        except Exception:
            pass
        return 900

    def set_interval(self, seconds: int):
        try:
            cfg = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
            cfg["presence_interval_s"] = seconds
            CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
            log.info(f"Updated presence_interval_s to {seconds} seconds.")
        except Exception as e:
            log.error(f"Failed to update interval: {e}")

    def on_open_dashboard(self, icon=None, menu_item=None):
        def launch_gui():
            from ui.dashboard import SentinelDashboard
            SentinelDashboard().mainloop()
        threading.Thread(target=launch_gui, daemon=True).start()

    def on_run_verify(self, icon=None, menu_item=None):
        def run():
            res = self.verifier.run_verification(is_manual_check=True)
            notify("SentinelFace", f"Manual check: {res.get('status')}")
        threading.Thread(target=run, daemon=True).start()

    def on_enroll(self, icon=None, menu_item=None):
        from ui.enroll_gui import run_face_enrollment
        threading.Thread(target=run_face_enrollment, daemon=True).start()

    def on_set_2min(self, icon=None, menu_item=None):
        self.set_interval(120)

    def on_set_15min(self, icon=None, menu_item=None):
        self.set_interval(900)

    def on_exit(self, icon=None, menu_item=None):
        log.info("SentinelFace tray app stopping...")
        self.stop_event.set()
        if self.icon:
            self.icon.stop()
        sys.exit(0)

    def background_scheduler_loop(self):
        log.info("SentinelFace background verification scheduler started.")
        while not self.stop_event.is_set():
            interval = self.get_interval()
            log.info(f"Scheduler: sleeping {interval}s until next check...")
            for _ in range(interval):
                if self.stop_event.is_set():
                    return
                time.sleep(1)
            if not self.stop_event.is_set():
                log.info("Scheduler: interval elapsed, running scheduled verification...")
                self.verifier.run_verification(is_manual_check=False)

    def run(self):
        sched_thread = threading.Thread(target=self.background_scheduler_loop, daemon=True)
        sched_thread.start()

        menu = pystray.Menu(
            MenuItem("🛡️ SentinelFace Dashboard", self.on_open_dashboard, default=True),
            MenuItem("🚀 Run Verification Now", self.on_run_verify),
            MenuItem("📸 Enroll Face Profile", self.on_enroll),
            pystray.Menu.SEPARATOR,
            MenuItem("⏱️ Set 2-Min Test Mode", self.on_set_2min),
            MenuItem("⏰ Set 15-Min Mode", self.on_set_15min),
            pystray.Menu.SEPARATOR,
            MenuItem("❌ Exit SentinelFace", self.on_exit),
        )
        self.icon = pystray.Icon("SentinelFace", create_icon_image(), "SentinelFace Security", menu)
        set_tray_icon(self.icon)
        log.info("SentinelFace system tray app running.")
        self.icon.run()


if __name__ == "__main__":
    SentinelTrayApp().run()
