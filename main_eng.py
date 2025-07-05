#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
.py v1.0.0

Self-contained Python GUI tool for polling-based directory monitoring.
Uses Tkinter and the standard library only. Features:

  • add/remove multiple folders to watch  
  • configurable polling interval  
  • optional recursive scan  
  • include or exclude hidden entries  
  • advanced glob filters (include/exclude)  
  • real-time log view in GUI and optional log file  
  • Start/Stop controls  

Requires Python 3.6+ with no external dependencies.
"""

import os
import sys
import time
import fnmatch
import logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, scrolledtext

def scan_directories(bases, recursive, include_hidden, includes, excludes):
    """
    Walk each base directory and return a snapshot dict:
      { "base|relative_path": last_mod_time }
    Applies recursive flag, hidden filter, and glob include/exclude.
    """
    snapshot = {}
    for base in bases:
        base = Path(base).resolve()
        if recursive:
            for root, dirs, files in os.walk(base):
                if not include_hidden:
                    dirs[:]  = [d for d in dirs  if not d.startswith('.')]
                    files[:] = [f for f in files if not f.startswith('.')]
                for name in dirs + files:
                    full = Path(root) / name
                    rel = full.relative_to(base).as_posix() + ('/' if full.is_dir() else '')
                    if _matches_filter(rel, includes, excludes):
                        try:
                            snapshot[f"{base}|{rel}"] = full.stat().st_mtime
                        except OSError:
                            pass
        else:
            for child in base.iterdir():
                if not include_hidden and child.name.startswith('.'):
                    continue
                rel = child.name + ('/' if child.is_dir() else '')
                if _matches_filter(rel, includes, excludes):
                    try:
                        snapshot[f"{base}|{rel}"] = child.stat().st_mtime
                    except OSError:
                        pass
    return snapshot

def _matches_filter(name, includes, excludes):
    """
    Return True if 'name' matches include/exclude glob lists.
    """
    if includes and not any(fnmatch.fnmatch(name, pat) for pat in includes):
        return False
    if excludes and any(fnmatch.fnmatch(name, pat) for pat in excludes):
        return False
    return True

def compare_snapshots(old, new):
    """
    Compare two snapshots and return sets: (added, removed, modified).
    """
    added   = set(new) - set(old)
    removed = set(old) - set(new)
    modified = {k for k in set(old) & set(new) if old[k] != new[k]}
    return added, removed, modified

class TextLoggerHandler(logging.Handler):
    """
    Custom logging handler that writes log records to a Tkinter Text widget.
    """
    def __init__(self, text_widget):
        super().__init__()
        self.text = text_widget
        self.text.configure(state='disabled')

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.see(tk.END)
            self.text.configure(state='disabled')
        self.text.after(0, append)

class DirectoryMonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Directory Polling Monitor – GUI")
        self.geometry("800x600")
        self._init_state()
        self._build_ui()

    def _init_state(self):
        self.watch_paths = []
        self.includes = []
        self.excludes = []
        self.snapshot = {}
        self.poll_job = None

    def _build_ui(self):
        # Watch list frame
        frame_paths = ttk.LabelFrame(self, text="Folders to Monitor")
        frame_paths.pack(fill='x', padx=10, pady=5)

        self.list_paths = tk.Listbox(frame_paths, height=4)
        self.list_paths.pack(side='left', fill='x', expand=True, padx=5, pady=5)

        frame_path_buttons = ttk.Frame(frame_paths)
        frame_path_buttons.pack(side='right', padx=5)
        ttk.Button(frame_path_buttons, text="Add...", command=self._add_folder).pack(fill='x', pady=2)
        ttk.Button(frame_path_buttons, text="Remove", command=self._remove_folder).pack(fill='x')

        # Settings frame
        frame_settings = ttk.LabelFrame(self, text="Settings")
        frame_settings.pack(fill='x', padx=10, pady=5)

        self.var_interval = tk.DoubleVar(value=5.0)
        self.var_recursive = tk.BooleanVar()
        self.var_hidden = tk.BooleanVar()

        ttk.Label(frame_settings, text="Interval (s):").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frame_settings, textvariable=self.var_interval, width=8).grid(row=0, column=1, pady=2)
        ttk.Checkbutton(frame_settings, text="Recursive", variable=self.var_recursive).grid(row=0, column=2, padx=20)
        ttk.Checkbutton(frame_settings, text="Include Hidden", variable=self.var_hidden).grid(row=0, column=3)

        # Filters frame
        frame_filters = ttk.LabelFrame(self, text="Advanced Filters (glob)")
        frame_filters.pack(fill='x', padx=10, pady=5)
        ttk.Button(frame_filters, text="Manage Filters...", command=self._open_filters_window).pack(padx=5, pady=5)

        # Log file frame
        frame_log = ttk.Frame(self)
        frame_log.pack(fill='x', padx=10, pady=5)
        ttk.Label(frame_log, text="Log File:").pack(side='left', padx=5)
        self.entry_log = ttk.Entry(frame_log)
        self.entry_log.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(frame_log, text="Browse...", command=self._choose_log_file).pack(side='left', padx=5)

        # Control buttons
        frame_controls = ttk.Frame(self)
        frame_controls.pack(fill='x', padx=10, pady=5)
        self.btn_start = ttk.Button(frame_controls, text="Start Monitoring", command=self._start_monitor)
        self.btn_start.pack(side='left', padx=5)
        self.btn_stop = ttk.Button(frame_controls, text="Stop Monitoring", command=self._stop_monitor, state='disabled')
        self.btn_stop.pack(side='left')

        # Log view
        self.text_log = scrolledtext.ScrolledText(self, height=15)
        self.text_log.pack(fill='both', expand=True, padx=10, pady=5)

    def _add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder")
        if folder:
            p = Path(folder)
            if p not in self.watch_paths:
                self.watch_paths.append(p)
                self.list_paths.insert(tk.END, str(p))

    def _remove_folder(self):
        selection = self.list_paths.curselection()
        if selection:
            idx = selection[0]
            self.watch_paths.pop(idx)
            self.list_paths.delete(idx)

    def _choose_log_file(self):
        filename = filedialog.asksaveasfilename(
            title="Log File",
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("All files", "*.*")]
        )
        if filename:
            self.entry_log.delete(0, tk.END)
            self.entry_log.insert(0, filename)

    def _open_filters_window(self):
        win = tk.Toplevel(self)
        win.title("Advanced Filters")
        win.geometry("450x300")

        # Include patterns
        frame_inc = ttk.LabelFrame(win, text="Include Patterns")
        frame_inc.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        list_inc = tk.Listbox(frame_inc)
        list_inc.pack(fill='both', expand=True, padx=5, pady=5)
        for pat in self.includes:
            list_inc.insert(tk.END, pat)
        btn_inc = ttk.Frame(frame_inc)
        btn_inc.pack(padx=5, pady=5)
        ttk.Button(btn_inc, text="+", width=3,
                   command=lambda: self._add_pattern(list_inc, self.includes)).pack(side='left')
        ttk.Button(btn_inc, text="–", width=3,
                   command=lambda: self._remove_pattern(list_inc, self.includes)).pack(side='left')

        # Exclude patterns
        frame_exc = ttk.LabelFrame(win, text="Exclude Patterns")
        frame_exc.pack(side='right', fill='both', expand=True, padx=5, pady=5)
        list_exc = tk.Listbox(frame_exc)
        list_exc.pack(fill='both', expand=True, padx=5, pady=5)
        for pat in self.excludes:
            list_exc.insert(tk.END, pat)
        btn_exc = ttk.Frame(frame_exc)
        btn_exc.pack(padx=5, pady=5)
        ttk.Button(btn_exc, text="+", width=3,
                   command=lambda: self._add_pattern(list_exc, self.excludes)).pack(side='left')
        ttk.Button(btn_exc, text="–", width=3,
                   command=lambda: self._remove_pattern(list_exc, self.excludes)).pack(side='left')

    def _add_pattern(self, listbox, target):
        pat = simpledialog.askstring("New Pattern", "Enter glob pattern:")
        if pat and pat not in target:
            target.append(pat)
            listbox.insert(tk.END, pat)

    def _remove_pattern(self, listbox, target):
        sel = listbox.curselection()
        if sel:
            i = sel[0]
            target.pop(i)
            listbox.delete(i)

    def _start_monitor(self):
        if not self.watch_paths:
            messagebox.showwarning("Warning", "No folders selected.")
            return
        logfile = self.entry_log.get().strip() or None

        handlers = [TextLoggerHandler(self.text_log)]
        if logfile:
            handlers.append(logging.FileHandler(logfile, encoding='utf-8'))
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)-8s %(message)s",
            handlers=handlers
        )
        logging.info("=== Monitoring Started ===")

        self.snapshot = scan_directories(
            self.watch_paths,
            self.var_recursive.get(),
            self.var_hidden.get(),
            self.includes,
            self.excludes
        )

        # Disable controls
        self.list_paths.configure(state='disabled')
        self.btn_start.configure(state='disabled')
        self.btn_stop.configure(state='normal')

        self._schedule_poll()

    def _stop_monitor(self):
        if self.poll_job:
            self.after_cancel(self.poll_job)
            self.poll_job = None
        logging.info("=== Monitoring Stopped ===")

        # Re-enable controls
        self.list_paths.configure(state='normal')
        self.btn_start.configure(state='normal')
        self.btn_stop.configure(state='disabled')

    def _schedule_poll(self):
        ms = int(self.var_interval.get() * 1000)
        self.poll_job = self.after(ms, self._do_poll)

    def _do_poll(self):
        new_snap = scan_directories(
            self.watch_paths,
            self.var_recursive.get(),
            self.var_hidden.get(),
            self.includes,
            self.excludes
        )
        added, removed, modified = compare_snapshots(self.snapshot, new_snap)

        for key in sorted(added):
            base, rel = key.split("|", 1)
            logging.info(f"[{base}] +Added   : {rel}")
        for key in sorted(removed):
            base, rel = key.split("|", 1)
            logging.info(f"[{base}] -Removed : {rel}")
        for key in sorted(modified):
            base, rel = key.split("|", 1)
            logging.info(f"[{base}] *Modified: {rel}")

        self.snapshot = new_snap
        self._schedule_poll()

def main():
    app = DirectoryMonitorApp()
    app.mainloop()

if __name__ == "__main__":
    main()
