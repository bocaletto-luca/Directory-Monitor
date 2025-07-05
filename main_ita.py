#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
monitor_gui.py v1.0.0

Strumento GUI per monitorare directory via polling, interamente in Python
(standard library only). Interfaccia basata su tkinter:

  • aggiungi/rimuovi più directory
  • intervallo di polling configurabile
  • scansione ricorsiva opzionale
  • includi/escludi file e cartelle nascosti
  • filtri avanzati (glob include/exclude)
  • log in tempo reale in finestra e su file
  • controlli Start/Stop per avviare o interrompere il monitor

Compatibile con Python 3.6+ senza dipendenze esterne.
"""

import os
import sys
import time
import fnmatch
import logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# -- Funzioni di scansione e confronto ----------------------------------------

def scan_dirs(bases, recursive, include_hidden, includes, excludes):
    """
    Scansiona le cartelle in 'bases' e restituisce uno snapshot dict:
      { "base|relative_path": mtime }
    Applica opzioni: recursive, hidden, include/exclude glob.
    """
    snap = {}
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
                    if _match_filter(rel, includes, excludes):
                        try:
                            snap[f"{base}|{rel}"] = full.stat().st_mtime
                        except OSError:
                            pass
        else:
            for child in base.iterdir():
                if not include_hidden and child.name.startswith('.'):
                    continue
                rel = child.name + ('/' if child.is_dir() else '')
                if _match_filter(rel, includes, excludes):
                    try:
                        snap[f"{base}|{rel}"] = child.stat().st_mtime
                    except OSError:
                        pass
    return snap

def _match_filter(name, includes, excludes):
    """Ritorna True se 'name' passa i filtri include/exclude."""
    if includes and not any(fnmatch.fnmatch(name, p) for p in includes):
        return False
    if excludes and any(fnmatch.fnmatch(name, p) for p in excludes):
        return False
    return True

def compare_snapshots(old, new):
    """Confronta snapshot, ritorna tuple (added, removed, modified)."""
    added   = set(new) - set(old)
    removed = set(old) - set(new)
    modified= {k for k in set(old)&set(new) if old[k] != new[k]}
    return added, removed, modified

# -- Handler di logging per inviare i messaggi alla Text widget -------------

class TextHandler(logging.Handler):
    """Logging handler che emette messaggi in una ScrolledText Tk."""
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

# -- Classe principale dell'applicazione --------------------------------------

class MonitorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Monitor Directory – GUI")
        self.geometry("800x600")
        self._build_ui()
        self._reset_state()

    def _reset_state(self):
        self.paths = []
        self.includes = []
        self.excludes = []
        self.snapshot = {}
        self.job = None

    def _build_ui(self):
        # Frame directory
        frm_dir = ttk.LabelFrame(self, text="Cartelle da monitorare")
        frm_dir.pack(fill='x', padx=10, pady=5)
        self.lst_dirs = tk.Listbox(frm_dir, height=4)
        self.lst_dirs.pack(side='left', fill='x', expand=True, padx=5, pady=5)
        btns = ttk.Frame(frm_dir)
        btns.pack(side='right', padx=5)
        ttk.Button(btns, text="Aggiungi...", command=self._add_dir).pack(fill='x', pady=2)
        ttk.Button(btns, text="Rimuovi",  command=self._remove_dir).pack(fill='x')

        # Frame impostazioni
        frm_cfg = ttk.LabelFrame(self, text="Impostazioni")
        frm_cfg.pack(fill='x', padx=10, pady=5)
        self.var_interval = tk.DoubleVar(value=5.0)
        self.var_rec      = tk.BooleanVar()
        self.var_hidden   = tk.BooleanVar()
        ttk.Label(frm_cfg, text="Intervallo (s):").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        ttk.Entry(frm_cfg, textvariable=self.var_interval, width=8).grid(row=0, column=1, pady=2)
        ttk.Checkbutton(frm_cfg, text="Ricorsivo", variable=self.var_rec).grid(row=0, column=2, padx=20)
        ttk.Checkbutton(frm_cfg, text="Includi nascosti", variable=self.var_hidden).grid(row=0, column=3)

        # Frame filtri
        frm_flt = ttk.LabelFrame(self, text="Filtri avanzati (glob)")
        frm_flt.pack(fill='x', padx=10, pady=5)
        ttk.Button(frm_flt, text="Gestisci filtri...", command=self._open_filter_window).pack(padx=5, pady=5)

        # Frame log file
        frm_log = ttk.Frame(self)
        frm_log.pack(fill='x', padx=10, pady=5)
        ttk.Label(frm_log, text="File di log:").pack(side='left', padx=5)
        self.ent_log = ttk.Entry(frm_log)
        self.ent_log.pack(side='left', fill='x', expand=True, padx=5)
        ttk.Button(frm_log, text="Sfoglia...", command=self._choose_logfile).pack(side='left', padx=5)

        # Pulsanti start/stop
        frm_btn = ttk.Frame(self)
        frm_btn.pack(fill='x', padx=10, pady=5)
        self.btn_start = ttk.Button(frm_btn, text="Avvia monitor", command=self._start)
        self.btn_start.pack(side='left', padx=5)
        self.btn_stop  = ttk.Button(frm_btn, text="Ferma monitor", command=self._stop, state='disabled')
        self.btn_stop.pack(side='left')

        # Area di log
        self.txt_log = scrolledtext.ScrolledText(self, height=15)
        self.txt_log.pack(fill='both', expand=True, padx=10, pady=5)

    # -- Azioni GUI ----------------------------------------------------------

    def _add_dir(self):
        d = filedialog.askdirectory(title="Seleziona cartella")
        if d:
            p = Path(d)
            if p not in self.paths:
                self.paths.append(p)
                self.lst_dirs.insert(tk.END, str(p))

    def _remove_dir(self):
        sel = self.lst_dirs.curselection()
        if sel:
            idx = sel[0]
            self.paths.pop(idx)
            self.lst_dirs.delete(idx)

    def _choose_logfile(self):
        f = filedialog.asksaveasfilename(title="File di log",
                                         defaultextension=".log",
                                         filetypes=[("Log file", "*.log"),("All files","*.*")])
        if f:
            self.ent_log.delete(0, tk.END)
            self.ent_log.insert(0, f)

    def _open_filter_window(self):
        win = tk.Toplevel(self)
        win.title("Filtri Avanzati")
        win.geometry("400x300")
        # Include
        frm_inc = ttk.LabelFrame(win, text="Include patterns")
        frm_inc.pack(fill='both', expand=True, side='left', padx=5, pady=5)
        lst_inc = tk.Listbox(frm_inc)
        lst_inc.pack(fill='both', expand=True, padx=5, pady=5)
        for p in self.includes: lst_inc.insert(tk.END, p)
        btns_i = ttk.Frame(frm_inc)
        btns_i.pack(padx=5, pady=5)
        ttk.Button(btns_i, text="+", width=3,
                   command=lambda: self._add_pattern(lst_inc, self.includes)).pack(side='left')
        ttk.Button(btns_i, text="–", width=3,
                   command=lambda: self._remove_pattern(lst_inc, self.includes)).pack(side='left')

        # Exclude
        frm_exc = ttk.LabelFrame(win, text="Exclude patterns")
        frm_exc.pack(fill='both', expand=True, side='right', padx=5, pady=5)
        lst_exc = tk.Listbox(frm_exc)
        lst_exc.pack(fill='both', expand=True, padx=5, pady=5)
        for p in self.excludes: lst_exc.insert(tk.END, p)
        btns_e = ttk.Frame(frm_exc)
        btns_e.pack(padx=5, pady=5)
        ttk.Button(btns_e, text="+", width=3,
                   command=lambda: self._add_pattern(lst_exc, self.excludes)).pack(side='left')
        ttk.Button(btns_e, text="–", width=3,
                   command=lambda: self._remove_pattern(lst_exc, self.excludes)).pack(side='left')

    def _add_pattern(self, listbox, target):
        pat = tk.simpledialog.askstring("Nuovo pattern", "Inserisci pattern glob:")
        if pat and pat not in target:
            target.append(pat)
            listbox.insert(tk.END, pat)

    def _remove_pattern(self, listbox, target):
        sel = listbox.curselection()
        if sel:
            idx = sel[0]
            target.pop(idx)
            listbox.delete(idx)

    def _start(self):
        if not self.paths:
            messagebox.showwarning("Attenzione", "Nessuna cartella selezionata.")
            return
        # configura logger
        logfile = self.ent_log.get().strip() or None
        handlers = [TextHandler(self.txt_log)]
        if logfile:
            handlers.append(logging.FileHandler(logfile, encoding='utf-8'))
        logging.basicConfig(level=logging.INFO,
                            format="%(asctime)s %(levelname)-8s %(message)s",
                            handlers=handlers)
        logging.info("=== Monitor Avviato ===")
        # snapshot iniziale
        self.snapshot = scan_dirs(
            self.paths,
            self.var_rec.get(),
            self.var_hidden.get(),
            self.includes,
            self.excludes
        )
        # disabilita controlli
        for w in (self.lst_dirs, self.btn_start):
            w.configure(state='disabled')
        # avvia polling
        self._schedule_poll()

    def _stop(self):
        if self.job:
            self.after_cancel(self.job)
            self.job = None
        logging.info("=== Monitor Interrotto ===")
        # ripristina controlli
        for w in (self.lst_dirs, self.btn_start):
            w.configure(state='normal')
        self.btn_stop.configure(state='disabled')

    def _schedule_poll(self):
        interval = int(self.var_interval.get() * 1000)
        self.job = self.after(interval, self._do_poll)

    def _do_poll(self):
        new_snap = scan_dirs(
            self.paths,
            self.var_rec.get(),
            self.var_hidden.get(),
            self.includes,
            self.excludes
        )
        added, removed, modified = compare_snapshots(self.snapshot, new_snap)
        for key in sorted(added):
            base, rel = key.split("|", 1)
            logging.info(f"[{base}] +Aggiunto FILE/DIR: {rel}")
        for key in sorted(removed):
            base, rel = key.split("|", 1)
            logging.info(f"[{base}] -Rimosso  FILE/DIR: {rel}")
        for key in sorted(modified):
            base, rel = key.split("|", 1)
            logging.info(f"[{base}] *Modificato FILE/DIR: {rel}")
        self.snapshot = new_snap
        # riabilita Stop, programma nuova tick
        self.btn_stop.configure(state='normal')
        self._schedule_poll()

# -- Punto di ingresso --------------------------------------------------------

if __name__ == "__main__":
    app = MonitorApp()
    app.mainloop()
