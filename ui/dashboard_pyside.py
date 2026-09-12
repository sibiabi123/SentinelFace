import sys
import os
import json
import logging
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon, QColor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QMessageBox, QGraphicsDropShadowEffect
)

from database.db import AuditDatabase
from core.verifier import VerificationEngine
from core.autostart import AutostartManager

log = logging.getLogger(__name__)
CONFIG_PATH = Path("E:/SentinelFace/config.json")

class StatCard(QFrame):
    def __init__(self, title: str, initial_value: str, icon_str: str, parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setStyleSheet("""
            #StatCard {
                background-color: #1e293b;
                border-radius: 12px;
                border: 1px solid #334155;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)

        header_layout = QHBoxLayout()
        icon_lbl = QLabel(icon_str)
        icon_lbl.setStyleSheet("font-size: 16px; color: #38bdf8;")
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 12px; color: #94a3b8; font-weight: 600;")
        header_layout.addWidget(icon_lbl)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()

        self.value_lbl = QLabel(initial_value)
        self.value_lbl.setStyleSheet("font-size: 24px; font-weight: 700; color: #f8fafc;")

        layout.addLayout(header_layout)
        layout.addWidget(self.value_lbl)

    def set_value(self, val: str):
        self.value_lbl.setText(val)


class SentinelPySideDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SentinelFace — 10x Security Control Center")
        self.resize(1050, 680)
        self.setStyleSheet("background-color: #0f172a;")

        self.db = AuditDatabase()
        self.verifier = VerificationEngine(self.db)

        self.init_ui()
        self.refresh_stats()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Header Bar
        header = QHBoxLayout()
        title_lbl = QLabel("🛡️ SentinelFace Security")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #38bdf8;")

        self.badge_lbl = QLabel("● SYSTEM PROTECTED")
        self.badge_lbl.setStyleSheet("""
            background-color: #064e3b;
            color: #34d399;
            font-size: 11px;
            font-weight: 700;
            padding: 6px 12px;
            border-radius: 12px;
        """)

        header.addWidget(title_lbl)
        header.addStretch()
        header.addWidget(self.badge_lbl)
        main_layout.addLayout(header)

        # Cards Layout
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)

        self.card_total = StatCard("TOTAL CHECKS", "0", "📊")
        self.card_passes = StatCard("PASSES", "0", "✅")
        self.card_fails = StatCard("LOCK TRIGGERS", "0", "🔒")
        self.card_rate = StatCard("SUCCESS RATE", "100%", "📈")

        cards_layout.addWidget(self.card_total)
        cards_layout.addWidget(self.card_passes)
        cards_layout.addWidget(self.card_fails)
        cards_layout.addWidget(self.card_rate)
        main_layout.addLayout(cards_layout)

        # Control Panel Buttons
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        btn_style_primary = """
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-weight: 700;
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #0369a1; }
        """
        btn_style_secondary = """
            QPushButton {
                background-color: #334155;
                color: #f1f5f9;
                font-weight: 600;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #475569; }
        """

        self.btn_verify = QPushButton("🚀 Run Instant Probe")
        self.btn_verify.setStyleSheet(btn_style_primary)
        self.btn_verify.clicked.connect(self.run_instant_verify)

        self.btn_enroll = QPushButton("📸 Enroll Face")
        self.btn_enroll.setStyleSheet(btn_style_secondary)
        self.btn_enroll.clicked.connect(self.open_enrollment)

        self.btn_2min = QPushButton("⏱️ 2-Min Mode")
        self.btn_2min.setStyleSheet(btn_style_secondary)
        self.btn_2min.clicked.connect(lambda: self.set_interval(120))

        self.btn_15min = QPushButton("⏰ 15-Min Mode")
        self.btn_15min.setStyleSheet(btn_style_secondary)
        self.btn_15min.clicked.connect(lambda: self.set_interval(900))

        self.btn_autostart = QPushButton("⚡ Toggle Windows Autostart")
        self.btn_autostart.setStyleSheet(btn_style_secondary)
        self.btn_autostart.clicked.connect(self.toggle_autostart)

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.setStyleSheet(btn_style_secondary)
        self.btn_refresh.clicked.connect(self.refresh_stats)

        controls_layout.addWidget(self.btn_verify)
        controls_layout.addWidget(self.btn_enroll)
        controls_layout.addWidget(self.btn_2min)
        controls_layout.addWidget(self.btn_15min)
        controls_layout.addWidget(self.btn_autostart)
        controls_layout.addStretch()
        controls_layout.addWidget(self.btn_refresh)

        main_layout.addLayout(controls_layout)

        # Audit Log Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "TIMESTAMP", "RESULT", "CONFIDENCE", "MATCHES", "ACTION TAKEN", "NOTES"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e293b;
                border-radius: 10px;
                border: 1px solid #334155;
                gridline-color: #334155;
                color: #e2e8f0;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #0f172a;
                color: #38bdf8;
                font-weight: 700;
                border: none;
                padding: 8px;
            }
        """)

        main_layout.addWidget(self.table)

    def refresh_stats(self):
        stats = self.db.get_stats()
        self.card_total.set_value(str(stats["total_checks"]))
        self.card_passes.set_value(str(stats["passes"]))
        self.card_fails.set_value(str(stats["fails"]))
        self.card_rate.set_value(f"{stats['success_rate']}%")

        logs = self.db.get_recent_logs(50)
        self.table.setRowCount(len(logs))

        for row_idx, item in enumerate(logs):
            row_id, ts, res, conf, liv, match_str, act, notes = item
            conf_str = f"{conf:.1f}%" if conf else "N/A"

            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row_id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(ts))
            
            res_item = QTableWidgetItem(res)
            if res == "PASS":
                res_item.setForeground(QColor("#34d399"))
            else:
                res_item.setForeground(QColor("#f87171"))
            self.table.setItem(row_idx, 2, res_item)

            self.table.setItem(row_idx, 3, QTableWidgetItem(conf_str))
            self.table.setItem(row_idx, 4, QTableWidgetItem(match_str))
            self.table.setItem(row_idx, 5, QTableWidgetItem(act))
            self.table.setItem(row_idx, 6, QTableWidgetItem(notes or ""))

    def run_instant_verify(self):
        res = self.verifier.run_verification(is_manual_check=True)
        self.refresh_stats()
        status = res.get("status", "UNKNOWN")
        msg = f"Result: {status}\nMatches: {res.get('matches', 'N/A')}\nConfidence: {res.get('confidence', 0.0):.1f}%"
        if status == "PASS":
            QMessageBox.information(self, "SentinelFace Probe", f"✅ VERIFIED!\n\n{msg}")
        else:
            QMessageBox.warning(self, "SentinelFace Probe", f"⚠️ UNVERIFIED / ABSENT\n\n{msg}")

    def open_enrollment(self):
        from ui.enroll_gui import run_face_enrollment
        run_face_enrollment()
        self.refresh_stats()

    def set_interval(self, seconds: int):
        try:
            cfg = {}
            if CONFIG_PATH.exists():
                with open(CONFIG_PATH, "r") as f:
                    cfg = json.load(f)
            cfg["presence_interval_s"] = seconds
            with open(CONFIG_PATH, "w") as f:
                json.dump(cfg, f, indent=2)
            mins = seconds // 60
            QMessageBox.information(self, "Interval Updated", f"Interval set to {mins} minutes ({seconds}s).")
            self.refresh_stats()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update interval: {e}")

    def toggle_autostart(self):
        if AutostartManager.is_registered():
            AutostartManager.unregister_autostart()
            QMessageBox.information(self, "Autostart Disabled", "Removed Task Scheduler autostart entry.")
        else:
            AutostartManager.register_autostart()
            QMessageBox.information(self, "Autostart Enabled", "SentinelFace will now start silently in background at Windows login!")

def main():
    app = QApplication(sys.argv)
    window = SentinelPySideDashboard()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
