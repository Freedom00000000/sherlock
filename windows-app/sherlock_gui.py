#!/usr/bin/env python3
"""Sherlock Windows GUI — Username search across social networks."""

import sys
import threading
import queue
import webbrowser
import csv
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ── Path setup: works in dev (repo root) and PyInstaller bundle ───────────────
_HERE = Path(__file__).parent
_REPO = _HERE.parent

if hasattr(sys, "_MEIPASS"):
    _BUNDLE = Path(sys._MEIPASS)
    _DATA_JSON = _BUNDLE / "sherlock_project" / "resources" / "data.json"
    sys.path.insert(0, str(_BUNDLE))
else:
    _DATA_JSON = _REPO / "sherlock_project" / "resources" / "data.json"
    sys.path.insert(0, str(_REPO))

try:
    from sherlock_project.sherlock import sherlock
    from sherlock_project.sites import SitesInformation
    from sherlock_project.result import QueryStatus
    from sherlock_project.notify import QueryNotify
except ImportError as exc:
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Sherlock – Import Error",
            f"Cannot load Sherlock modules:\n\n{exc}\n\n"
            "Run sherlock_gui.py from the repository root or use the built .exe.",
        )
        root.destroy()
    except Exception:
        print(f"ERROR: {exc}", file=sys.stderr)
    sys.exit(1)


# ── Palette & fonts ───────────────────────────────────────────────────────────
BG        = "#1e1e2e"
BG2       = "#2a2a3e"
BG3       = "#313149"
ACCENT    = "#7c3aed"
ACCENT_HV = "#6d28d9"
FOUND_CLR = "#22c55e"
ERROR_CLR = "#f59e0b"
MUTED     = "#6b7280"
FG        = "#f8fafc"
FG2       = "#94a3b8"

FONT      = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_LG   = ("Segoe UI", 16, "bold")
FONT_MONO = ("Consolas", 9)


# ── Custom notifier: feeds results into a thread-safe queue ───────────────────
class _GUINotify(QueryNotify):
    def __init__(self, q: queue.Queue, stop_evt: threading.Event):
        super().__init__()
        self._q = q
        self._stop_evt = stop_evt

    def start(self, message=None):
        pass

    def update(self, result):
        if self._stop_evt.is_set():
            raise InterruptedError("Search stopped by user")
        self._q.put(("result", result))

    def finish(self):
        self._q.put(("done", None))


# ── Main application window ───────────────────────────────────────────────────
class SherlockApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sherlock — Username Search")
        self.geometry("960x680")
        self.minsize(720, 520)
        self.configure(bg=BG)
        try:
            # Windows taskbar icon (ICO bundled by PyInstaller or next to script)
            ico = _HERE / "sherlock.ico"
            if ico.exists():
                self.iconbitmap(str(ico))
        except Exception:
            pass

        self._q: queue.Queue = queue.Queue()
        self._thread: threading.Thread | None = None
        self._stop_evt = threading.Event()
        self._results: list = []
        self._total = 0

        self._build_ui()
        self._style()
        self.after(50, self._poll)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_input()
        self._build_options()
        self._build_progress()
        self._build_table()
        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self, bg=ACCENT, padx=20, pady=12)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🔍  Sherlock", font=FONT_LG,
                 bg=ACCENT, fg=FG).pack(side="left")
        tk.Label(hdr, text="  –  Find usernames across social networks",
                 font=FONT, bg=ACCENT, fg="#c4b5fd").pack(side="left", pady=2)

    def _build_input(self):
        row = tk.Frame(self, bg=BG2, padx=16, pady=12)
        row.pack(fill="x")

        tk.Label(row, text="Username", font=FONT_BOLD,
                 bg=BG2, fg=FG2).grid(row=0, column=0, sticky="w", padx=(0, 8))

        self._var_user = tk.StringVar()
        self._entry = ttk.Entry(row, textvariable=self._var_user,
                                font=("Segoe UI", 11), style="D.TEntry")
        self._entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self._entry.bind("<Return>", lambda _e: self._start())
        row.columnconfigure(1, weight=1)

        self._btn_go = ttk.Button(row, text="  Search  ",
                                  style="Go.TButton", command=self._start)
        self._btn_go.grid(row=0, column=2, padx=(0, 4))

        self._btn_stop = ttk.Button(row, text="  Stop  ",
                                    style="Stop.TButton", command=self._stop,
                                    state="disabled")
        self._btn_stop.grid(row=0, column=3)

    def _build_options(self):
        row = tk.Frame(self, bg=BG2, padx=16, pady=6)
        row.pack(fill="x")

        tk.Label(row, text="Timeout (s):", font=FONT,
                 bg=BG2, fg=FG2).pack(side="left")
        self._var_timeout = tk.IntVar(value=60)
        ttk.Spinbox(row, from_=5, to=180, width=5,
                    textvariable=self._var_timeout,
                    font=FONT).pack(side="left", padx=(4, 20))

        self._var_nsfw = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, text="Include NSFW sites",
                        variable=self._var_nsfw,
                        style="D.TCheckbutton").pack(side="left", padx=(0, 20))

        self._var_all = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, text="Show not-found results",
                        variable=self._var_all,
                        command=self._redraw,
                        style="D.TCheckbutton").pack(side="left")

    def _build_progress(self):
        row = tk.Frame(self, bg=BG, padx=16, pady=8)
        row.pack(fill="x")

        self._var_pct = tk.DoubleVar(value=0)
        self._pbar = ttk.Progressbar(row, variable=self._var_pct, maximum=100,
                                     style="S.Horizontal.TProgressbar")
        self._pbar.pack(side="left", fill="x", expand=True)

        self._lbl_prog = tk.Label(row, text="", font=FONT_MONO,
                                  bg=BG, fg=FG2, width=22, anchor="e")
        self._lbl_prog.pack(side="left", padx=(10, 0))

    def _build_table(self):
        wrapper = tk.Frame(self, bg=BG, padx=16)
        wrapper.pack(fill="both", expand=True)

        cols = ("icon", "site", "url")
        self._tree = ttk.Treeview(wrapper, columns=cols, show="headings",
                                   selectmode="browse", style="D.Treeview")
        self._tree.heading("icon", text="")
        self._tree.heading("site", text="Site")
        self._tree.heading("url",  text="Profile URL")
        self._tree.column("icon", width=26,  minwidth=26,  stretch=False, anchor="center")
        self._tree.column("site", width=170, minwidth=100, stretch=False)
        self._tree.column("url",  width=600, minwidth=200)

        self._tree.tag_configure("found",    foreground=FOUND_CLR)
        self._tree.tag_configure("notfound", foreground=MUTED)
        self._tree.tag_configure("error",    foreground=ERROR_CLR)

        vsb = ttk.Scrollbar(wrapper, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._tree.bind("<Double-1>", self._open)
        self._tree.bind("<Return>",   self._open)

        tip = tk.Label(wrapper, text="Double-click a row to open in browser",
                       font=("Segoe UI", 8), bg=BG, fg=MUTED, anchor="w")
        tip.pack(fill="x", pady=(2, 0))

    def _build_footer(self):
        bar = tk.Frame(self, bg=BG2, padx=16, pady=8)
        bar.pack(fill="x", side="bottom")

        self._lbl_found = tk.Label(bar, text="Found: 0", font=FONT_BOLD,
                                   bg=BG2, fg=FOUND_CLR)
        self._lbl_found.pack(side="left", padx=(0, 16))

        self._lbl_status = tk.Label(bar, text="Ready", font=FONT,
                                    bg=BG2, fg=FG2)
        self._lbl_status.pack(side="left")

        btns = tk.Frame(bar, bg=BG2)
        btns.pack(side="right")
        ttk.Button(btns, text="Export TXT", command=self._export_txt
                   ).pack(side="left", padx=2)
        ttk.Button(btns, text="Export CSV", command=self._export_csv
                   ).pack(side="left", padx=2)
        ttk.Button(btns, text="Clear", command=self._clear
                   ).pack(side="left", padx=2)

    # ── Styles ────────────────────────────────────────────────────────────────

    def _style(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure(".", background=BG, foreground=FG, font=FONT,
                    fieldbackground=BG2, borderwidth=0, relief="flat",
                    troughcolor=BG2, arrowcolor=FG2)

        s.configure("D.TEntry", fieldbackground=BG3, foreground=FG,
                    insertcolor=FG, borderwidth=1, relief="solid", padding=6)

        s.configure("D.TCheckbutton", background=BG2, foreground=FG2)
        s.map("D.TCheckbutton", background=[("active", BG2)])

        s.configure("Go.TButton", background=ACCENT, foreground=FG,
                    font=FONT_BOLD, padding=(10, 6), relief="flat")
        s.map("Go.TButton",
              background=[("active", ACCENT_HV), ("disabled", "#4c1d95")],
              foreground=[("disabled", "#c4b5fd")])

        s.configure("Stop.TButton", background="#dc2626", foreground=FG,
                    font=FONT_BOLD, padding=(10, 6), relief="flat")
        s.map("Stop.TButton",
              background=[("active", "#b91c1c"), ("disabled", BG3)],
              foreground=[("disabled", MUTED)])

        s.configure("TButton", background=BG3, foreground=FG2,
                    font=FONT, padding=(8, 5), relief="flat")
        s.map("TButton",
              background=[("active", BG2)],
              foreground=[("active", FG)])

        s.configure("S.Horizontal.TProgressbar",
                    troughcolor=BG3, background=ACCENT,
                    thickness=10, borderwidth=0)

        s.configure("D.Treeview", background=BG2, foreground=FG,
                    fieldbackground=BG2, rowheight=26, borderwidth=0,
                    relief="flat")
        s.map("D.Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", FG)])
        s.configure("D.Treeview.Heading", background=BG, foreground=FG2,
                    font=FONT_BOLD, relief="flat", borderwidth=0)
        s.map("D.Treeview.Heading", background=[("active", BG3)])

        s.configure("TScrollbar", background=BG3, troughcolor=BG,
                    borderwidth=0, relief="flat")

    # ── Search ────────────────────────────────────────────────────────────────

    def _start(self):
        username = self._var_user.get().strip()
        if not username:
            self._entry.focus()
            return
        if self._thread and self._thread.is_alive():
            return

        self._clear()
        self._status(f"Searching for '{username}' …")
        self._btn_go.config(state="disabled")
        self._btn_stop.config(state="normal")
        self._stop_evt.clear()

        self._thread = threading.Thread(
            target=self._worker,
            args=(username, self._var_timeout.get(), self._var_nsfw.get()),
            daemon=True,
        )
        self._thread.start()

    def _stop(self):
        self._stop_evt.set()
        self._status("Stopping …")

    def _worker(self, username: str, timeout: int, include_nsfw: bool):
        try:
            sites = SitesInformation(str(_DATA_JSON), honor_exclusions=False)
            if not include_nsfw:
                sites.remove_nsfw_sites()

            site_data = {s.name: s.information for s in sites}
            self._total = len(site_data)
            self._q.put(("total", self._total))

            notify = _GUINotify(self._q, self._stop_evt)
            sherlock(
                username=username,
                site_data=site_data,
                query_notify=notify,
                timeout=timeout,
            )
        except InterruptedError:
            pass
        except Exception as exc:
            self._q.put(("error", str(exc)))
        finally:
            self._q.put(("done", None))

    # ── Queue polling ─────────────────────────────────────────────────────────

    def _poll(self):
        batch = 0
        while not self._q.empty() and batch < 30:
            try:
                kind, payload = self._q.get_nowait()
            except queue.Empty:
                break
            batch += 1

            if kind == "total":
                self._total = payload

            elif kind == "result":
                self._results.append(payload)
                self._row(payload)
                self._refresh_counts()

            elif kind == "error":
                messagebox.showerror("Sherlock Error", payload)

            elif kind == "done":
                found = self._found_count()
                user  = self._var_user.get().strip()
                self._status(f"Done — {found} profile(s) found for '{user}'.")
                self._btn_go.config(state="normal")
                self._btn_stop.config(state="disabled")

        self.after(50, self._poll)

    # ── Table helpers ─────────────────────────────────────────────────────────

    def _row(self, result):
        status = result.status
        show_all = self._var_all.get()

        if status == QueryStatus.CLAIMED:
            icon, tag = "✓", "found"
        elif status in (QueryStatus.WAF, QueryStatus.UNKNOWN):
            icon, tag = "!", "error"
            if not show_all:
                return
        else:
            if not show_all:
                return
            icon, tag = "✗", "notfound"

        self._tree.insert("", "end",
                          values=(icon, result.site_name, result.site_url_user),
                          tags=(tag,))
        self._tree.yview_moveto(1)

    def _redraw(self):
        for item in self._tree.get_children():
            self._tree.delete(item)
        for r in self._results:
            self._row(r)

    def _refresh_counts(self):
        done  = len(self._results)
        total = self._total or 1
        found = self._found_count()
        self._var_pct.set(done / total * 100)
        self._lbl_prog.config(text=f"{done} / {total}   Found: {found}")
        self._lbl_found.config(text=f"Found: {found}")

    def _found_count(self) -> int:
        return sum(1 for r in self._results if r.status == QueryStatus.CLAIMED)

    # ── Interaction ───────────────────────────────────────────────────────────

    def _open(self, _event=None):
        sel = self._tree.selection()
        if not sel:
            return
        url = self._tree.item(sel[0])["values"][2]
        if isinstance(url, str) and url.startswith("http"):
            webbrowser.open(url)

    def _clear(self):
        self._results.clear()
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._var_pct.set(0)
        self._lbl_prog.config(text="")
        self._lbl_found.config(text="Found: 0")
        self._status("Ready")

    def _status(self, text: str):
        self._lbl_status.config(text=text)

    # ── Export ────────────────────────────────────────────────────────────────

    def _claimed(self):
        return [r for r in self._results if r.status == QueryStatus.CLAIMED]

    def _export_txt(self):
        rows = self._claimed()
        if not rows:
            messagebox.showinfo("Export", "No found profiles to export.")
            return
        user = self._var_user.get().strip()
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"sherlock_{user}_{datetime.now():%Y%m%d_%H%M%S}.txt",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(f"Sherlock results for: {user}\n")
            fh.write(f"Date: {datetime.now():%Y-%m-%d %H:%M:%S}\n")
            fh.write(f"Found: {len(rows)} profile(s)\n\n")
            for r in rows:
                fh.write(f"[+] {r.site_name}\n    {r.site_url_user}\n\n")
        self._status(f"Exported {len(rows)} results → {Path(path).name}")

    def _export_csv(self):
        rows = self._claimed()
        if not rows:
            messagebox.showinfo("Export", "No found profiles to export.")
            return
        user = self._var_user.get().strip()
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"sherlock_{user}_{datetime.now():%Y%m%d_%H%M%S}.csv",
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["Site", "Profile URL"])
            for r in rows:
                w.writerow([r.site_name, r.site_url_user])
        self._status(f"Exported {len(rows)} results → {Path(path).name}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = SherlockApp()
    app.mainloop()
