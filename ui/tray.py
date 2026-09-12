import os
import sys
import json
import threading
import time
import logging
from pathlib import Path
from PIL import Image, ImageDraw

import pystray
from pystray import MenuItem as item

from database.db import AuditDatabase
from core.verifier import VerificationEngine

log = logging.getLogger(__name__)
CONFIG_PATH = Path("E:/SentinelFace/config.json")

def create_icon_image():
    # Generate a sleek 64x64 shield icon for system tray
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Outer dark background circle
    draw.ellipse((4, 4, 60, 60), fill="#1e1e2e", outline="#89b4fa", width=3)
    # Shield / Lock symbol in center
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
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, "r") as f:
                    cfg = json.load(f)
                    return cfg.get("presence_interval_s", 900)
            except Exception:
                pass
        return 900

    def set_interval(self, seconds: int):
        try:
            cfg = {}
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH, "r") as f:
                    cfg = json.load(f)
            cfg["presence_interval_s"] = seconds
            with open(CONFIG_PATH, "w") as f:
                json.dump(cfg, f, indent=2)
            log.info(f"Updated presence_interval_s to {seconds} seconds.")
        except Exception as e:
            log.error(f"Failed to update interval: {e}")

    def on_open_dashboard(self, icon=None, item=None):
        def launch_gui():
            from ui.dashboard import SentinelDashboard
            app = SentinelDashboard()
            app.mainloop()
        threading.Thread(target=launch_gui, daemon=True).start()

    def on_run_verify(self, icon=None, item=None):
        threading.Thread(target=lambda: self.verifier.run_verification(is_manual_check=True), daemon=True).start()

    def on_enroll(self, icon=None, item=None):
        from ui.enroll_gui import run_face_enrollment
        threading.Thread(target=run_face_enrollment, daemon=True).start()

    def on_set_2min(self, icon=None, item=None):
        self.set_interval(120)

    def on_set_15min(self, icon=None, item=None):
        self.set_interval(900)

    def on_exit(self, icon=None, item=None):
        log.info("SentinelFace Tray App stopping...")
        self.stop_event.set()
        if self.icon:
            self.icon.stop()
        sys.exit(0)

    def background_scheduler_loop(self):
        log.info("SentinelFace Background Verification Scheduler thread started.")
        while not self.stop_event.is_set():
            interval = self.get_interval()
            log.info(f"Scheduler: Sleeping for {interval} seconds until next continuous verification check...")
            
            # Sleep in 1-second increments so stop_event can terminate instantly
            for _ in range(interval):
                if self.stop_event.is_set():
                    return
                time.sleep(1)

            if not self.stop_event.is_set():
                log.info("Scheduler: Interval elapsed. Triggering 15-min background verification check...")
                self.verifier.run_verification(is_manual_check=False)

    def run(self):
        # Start background verification thread
        sched_thread = threading.Thread(target=self.background_scheduler_loop, daemon=True)
        sched_thread.start()

        menu = pystray.Menu(
            item("🛡️ SentinelFace Dashboard", self.on_open_dashboard, default=True),
            item("🚀 Run Verification Now", self.on_run_verify),
            item("📸 Enroll Face Profile", self.on_enroll),
            pystray.Menu.SEPARATOR,
            item("⏱️ Set 2-Min Test Mode", self.on_set_2min),
            item("⏰ Set 15-Min Mode", self.on_set_15min),
            pystray.Menu.SEPARATOR,
            item("❌ Exit SentinelFace", self.on_exit)
        )

        icon_img = create_icon_image()
        self.icon = pystray.Icon("SentinelFace", icon_img, "SentinelFace Security", menu)
        log.info("SentinelFace System Tray App running.")
        self.icon.run()

if __name__ == "__main__":
    app = SentinelTrayApp()
    app.run()
