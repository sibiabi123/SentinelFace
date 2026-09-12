import sys
import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from database.db import AuditDatabase
from core.verifier import VerificationEngine

CONFIG_PATH = Path("E:/SentinelFace/config.json")

class SentinelDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SentinelFace — Continuous Authentication Dashboard")
        self.geometry("950 x 620")
        self.configure(bg="#1e1e2e")

        self.db = AuditDatabase()
        self.verifier = VerificationEngine(self.db)

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configure_styles()

        self.build_ui()
        self.refresh_dashboard()

    def configure_styles(self):
        self.style.configure(".", background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#89b4fa", background="#1e1e2e")
        self.style.configure("StatValue.TLabel", font=("Segoe UI", 16, "bold"), foreground="#a6e3a1", background="#313244")
        self.style.configure("StatTitle.TLabel", font=("Segoe UI", 9), foreground="#bac2de", background="#313244")
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), background="#45475a", foreground="#cdd6f4", padding=6)
        self.style.map("TButton", background=[("active", "#585b70")])
        self.style.configure("Action.TButton", background="#89b4fa", foreground="#11111b")
        self.style.map("Action.TButton", background=[("active", "#b4befe")])

        # Treeview styling
        self.style.configure("Treeview", background="#181825", foreground="#cdd6f4", fieldbackground="#181825", rowheight=26)
        self.style.configure("Treeview.Heading", background="#313244", foreground="#89b4fa", font=("Segoe UI", 10, "bold"))

    def build_ui(self):
        # Header Frame
        header_frame = tk.Frame(self, bg="#1e1e2e")
        header_frame.pack(fill="x", px=20, py=15)

        title = ttk.Label(header_frame, text="🛡️ SentinelFace Security Dashboard", style="Header.TLabel")
        title.pack(side="left")

        self.status_lbl = tk.Label(header_frame, text="● ACTIVE", font=("Segoe UI", 11, "bold"), bg="#a6e3a1", fg="#11111b", px=10, py=4)
        self.status_lbl.pack(side="right")

        # Stats Cards Container
        stats_frame = tk.Frame(self, bg="#1e1e2e")
        stats_frame.pack(fill="x", px=20, py=10)

        self.card_total = self.create_card(stats_frame, "Total Checks", "0")
        self.card_total.pack(side="left", expand=True, fill="x", px=5)

        self.card_passes = self.create_card(stats_frame, "Passes", "0")
        self.card_passes.pack(side="left", expand=True, fill="x", px=5)

        self.card_fails = self.create_card(stats_frame, "Lock Triggers", "0")
        self.card_fails.pack(side="left", expand=True, fill="x", px=5)

        self.card_rate = self.create_card(stats_frame, "Success Rate", "100%")
        self.card_rate.pack(side="left", expand=True, fill="x", px=5)

        # Action Control Panel
        action_frame = tk.Frame(self, bg="#1e1e2e")
        action_frame.pack(fill="x", px=20, py=10)

        btn_verify = ttk.Button(action_frame, text="🚀 Run Instant Verification", style="Action.TButton", command=self.run_instant_verify)
        btn_verify.pack(side="left", px=5)

        btn_enroll = ttk.Button(action_frame, text="📸 Enroll Face Profile", command=self.open_enrollment)
        btn_enroll.pack(side="left", px=5)

        btn_2min = ttk.Button(action_frame, text="⏱️ Set 2-Min Mode", command=lambda: self.set_interval(120))
        btn_2min.pack(side="left", px=5)

        btn_15min = ttk.Button(action_frame, text="⏰ Set 15-Min Mode", command=lambda: self.set_interval(900))
        btn_15min.pack(side="left", px=5)

        btn_refresh = ttk.Button(action_frame, text="🔄 Refresh", command=self.refresh_dashboard)
        btn_refresh.pack(side="right", px=5)

        # Table Container
        table_frame = tk.Frame(self, bg="#1e1e2e")
        table_frame.pack(fill="both", expand=True, px=20, py=10)

        cols = ("id", "timestamp", "result", "confidence", "matches", "action", "notes")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.heading("result", text="Result")
        self.tree.heading("confidence", text="Confidence")
        self.tree.heading("matches", text="Matches")
        self.tree.heading("action", text="Action Taken")
        self.tree.heading("notes", text="Notes")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("timestamp", width=160, anchor="center")
        self.tree.column("result", width=80, anchor="center")
        self.tree.column("confidence", width=90, anchor="center")
        self.tree.column("matches", width=80, anchor="center")
        self.tree.column("action", width=120, anchor="center")
        self.tree.column("notes", width=180, anchor="w")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_card(self, parent, title_text, initial_val):
        card = tk.Frame(parent, bg="#313244", bd=0, relief="flat", px=15, py=10)
        lbl_title = ttk.Label(card, text=title_text, style="StatTitle.TLabel")
        lbl_title.pack(anchor="w")
        lbl_val = ttk.Label(card, text=initial_val, style="StatValue.TLabel")
        lbl_val.pack(anchor="w", py=(4, 0))
        card.val_label = lbl_val
        return card

    def refresh_dashboard(self):
        stats = self.db.get_stats()
        self.card_total.val_label.config(text=str(stats["total_checks"]))
        self.card_passes.val_label.config(text=str(stats["passes"]))
        self.card_fails.val_label.config(text=str(stats["fails"]))
        self.card_rate.val_label.config(text=f"{stats['success_rate']}%")

        # Clear tree
        for row in self.tree.get_children():
            self.tree.delete(row)

        logs = self.db.get_recent_logs(50)
        for item in logs:
            row_id, ts, res, conf, liv, match_str, act, notes = item
            conf_str = f"{conf:.1f}%" if conf else "N/A"
            self.tree.insert("", "end", values=(row_id, ts, res, conf_str, match_str, act, notes))

    def run_instant_verify(self):
        res = self.verifier.run_verification(is_manual_check=True)
        self.refresh_dashboard()
        status = res.get("status", "UNKNOWN")
        msg = f"Result: {status}\nMatches: {res.get('matches', 'N/A')}\nConfidence: {res.get('confidence', 0.0):.1f}%"
        if status == "PASS":
            messagebox.showinfo("SentinelFace Verification", f"✅ VERIFIED!\n\n{msg}")
        else:
            messagebox.showwarning("SentinelFace Verification", f"⚠️ UNVERIFIED / ABSENT\n\n{msg}")

    def open_enrollment(self):
        from ui.enroll_gui import run_face_enrollment
        self.withdraw()
        run_face_enrollment()
        self.deiconify()
        self.refresh_dashboard()

    def set_interval(self, interval_s: int):
        try:
            with open(CONFIG_PATH, "r") as f:
                cfg = json.load(f)
            cfg["presence_interval_s"] = interval_s
            with open(CONFIG_PATH, "w") as f:
                json.dump(cfg, f, indent=2)
            mins = interval_s // 60
            messagebox.showinfo("Config Updated", f"Interval successfully updated to {mins} minutes ({interval_s} seconds).")
            self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update config: {e}")

def main():
    app = SentinelDashboard()
    app.mainloop()

if __name__ == "__main__":
    main()
