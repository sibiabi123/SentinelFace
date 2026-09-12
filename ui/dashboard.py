import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from database.db import AuditDatabase
from core.verifier import VerificationEngine

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.json"


class SentinelDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SentinelFace — Continuous Authentication Dashboard")
        self.geometry("950x620")
        self.configure(bg="#1e1e2e")

        self.db = AuditDatabase()
        self.verifier = VerificationEngine(self.db)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._configure_styles()
        self._build_ui()
        self.refresh_dashboard()

    def _configure_styles(self):
        s = self.style
        s.configure(".", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        s.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#89b4fa", background="#1e1e2e")
        s.configure("StatValue.TLabel", font=("Segoe UI", 16, "bold"), foreground="#a6e3a1", background="#313244")
        s.configure("StatTitle.TLabel", font=("Segoe UI", 9), foreground="#bac2de", background="#313244")
        s.configure("TButton", font=("Segoe UI", 10, "bold"), background="#45475a", foreground="#cdd6f4", padding=6)
        s.map("TButton", background=[("active", "#585b70")])
        s.configure("Action.TButton", background="#89b4fa", foreground="#11111b")
        s.map("Action.TButton", background=[("active", "#b4befe")])
        s.configure("Treeview", background="#181825", foreground="#cdd6f4", fieldbackground="#181825", rowheight=26)
        s.configure("Treeview.Heading", background="#313244", foreground="#89b4fa", font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        header = tk.Frame(self, bg="#1e1e2e")
        header.pack(fill="x", padx=20, pady=15)
        ttk.Label(header, text="🛡️ SentinelFace Security Dashboard", style="Header.TLabel").pack(side="left")
        self.status_lbl = tk.Label(header, text="● ACTIVE", font=("Segoe UI", 11, "bold"),
                                    bg="#a6e3a1", fg="#11111b", padx=10, pady=4)
        self.status_lbl.pack(side="right")

        stats = tk.Frame(self, bg="#1e1e2e")
        stats.pack(fill="x", padx=20, pady=10)
        self.card_total = self._make_card(stats, "Total Checks", "0")
        self.card_total.pack(side="left", expand=True, fill="x", padx=5)
        self.card_passes = self._make_card(stats, "Passes", "0")
        self.card_passes.pack(side="left", expand=True, fill="x", padx=5)
        self.card_fails = self._make_card(stats, "Lock Triggers", "0")
        self.card_fails.pack(side="left", expand=True, fill="x", padx=5)
        self.card_rate = self._make_card(stats, "Success Rate", "100%")
        self.card_rate.pack(side="left", expand=True, fill="x", padx=5)

        actions = tk.Frame(self, bg="#1e1e2e")
        actions.pack(fill="x", padx=20, pady=10)
        ttk.Button(actions, text="🚀 Run Instant Verification", style="Action.TButton",
                   command=self.run_instant_verify).pack(side="left", padx=5)
        ttk.Button(actions, text="📸 Enroll Face Profile", command=self.open_enrollment).pack(side="left", padx=5)
        ttk.Button(actions, text="⏱️ Set 2-Min Test Mode", command=lambda: self.set_interval(120)).pack(side="left", padx=5)
        ttk.Button(actions, text="⏰ Set 15-Min Mode", command=lambda: self.set_interval(900)).pack(side="left", padx=5)
        ttk.Button(actions, text="🔄 Refresh", command=self.refresh_dashboard).pack(side="right", padx=5)

        table_frame = tk.Frame(self, bg="#1e1e2e")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        cols = ("id", "timestamp", "result", "confidence", "liveness", "matches", "action", "notes")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        headers = {"id": "ID", "timestamp": "Timestamp", "result": "Result", "confidence": "Confidence",
                   "liveness": "Liveness", "matches": "Matches", "action": "Action Taken", "notes": "Notes"}
        widths = {"id": 40, "timestamp": 150, "result": 70, "confidence": 90,
                  "liveness": 80, "matches": 70, "action": 120, "notes": 220}
        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c], anchor="center" if c != "notes" else "w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _make_card(self, parent, title_text, initial_val):
        card = tk.Frame(parent, bg="#313244", bd=0, relief="flat", padx=15, pady=10)
        ttk.Label(card, text=title_text, style="StatTitle.TLabel").pack(anchor="w")
        lbl_val = ttk.Label(card, text=initial_val, style="StatValue.TLabel")
        lbl_val.pack(anchor="w", pady=(4, 0))
        card.val_label = lbl_val
        return card

    def refresh_dashboard(self):
        stats = self.db.get_stats()
        self.card_total.val_label.config(text=str(stats["total_checks"]))
        self.card_passes.val_label.config(text=str(stats["passes"]))
        self.card_fails.val_label.config(text=str(stats["fails"]))
        self.card_rate.val_label.config(text=f"{stats['success_rate']}%")

        for row in self.tree.get_children():
            self.tree.delete(row)
        for row_id, ts, res, conf, liv, match_str, act, notes in self.db.get_recent_logs(50):
            conf_str = f"{conf:.1f}%" if conf is not None else "N/A"
            liv_str = f"{liv:.2f}" if liv is not None else "N/A"
            self.tree.insert("", "end", values=(row_id, ts, res, conf_str, liv_str, match_str, act, notes))

    def run_instant_verify(self):
        res = self.verifier.run_verification(is_manual_check=True)
        self.refresh_dashboard()
        status = res.get("status", "UNKNOWN")
        msg = f"Result: {status}\nMatches: {res.get('matches', 'N/A')}\nConfidence: {res.get('confidence', 0.0):.1f}%\nLiveness: {res.get('liveness', 0.0)}"
        if status == "PASS":
            messagebox.showinfo("SentinelFace Verification", f"✅ VERIFIED\n\n{msg}")
        else:
            messagebox.showwarning("SentinelFace Verification", f"⚠️ NOT VERIFIED\n\n{msg}")

    def open_enrollment(self):
        from ui.enroll_gui import run_face_enrollment
        self.withdraw()
        run_face_enrollment()
        self.deiconify()
        self.refresh_dashboard()

    def set_interval(self, interval_s: int):
        try:
            cfg = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
            cfg["presence_interval_s"] = interval_s
            CONFIG_PATH.write_text(json.dumps(cfg, indent=2))
            messagebox.showinfo("Config Updated", f"Interval set to {interval_s // 60} minute(s).")
            self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update config: {e}")


def main():
    app = SentinelDashboard()
    app.mainloop()


if __name__ == "__main__":
    main()
