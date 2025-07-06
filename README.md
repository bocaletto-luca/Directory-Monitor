# Directory Monitor
#### Author: Bocaletto Luca

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue?style=for-the-badge&logo=gnu) 
![Python 3.6+](https://img.shields.io/badge/Python-3.6%2B-blue?style=for-the-badge&logo=python)  
![Linux-Compatible](https://img.shields.io/badge/Linux-Compatible-blue?style=for-the-badge&logo=linux)  
![Status: Complete](https://img.shields.io/badge/Status-Complete-brightgreen?style=for-the-badge)  

Directory Monitor GUI is a self-contained Python application with a Tkinter interface for configuring and monitoring multiple directories via polling. Add or remove folders, set polling intervals, toggle recursive scans and hidden entries, apply include/exclude glob filters, and view real-time logs in-app or export to a file. Use Start/Stop buttons to control sessions.

Languages English and Italian interfaces in two standalone scripts:

- **main_eng.py** – English UI and prompts  
- **main_ita.py** – Italian UI and prompts  

Author: Bocaletto Luca  
License: GPL v3  

[![Read Online (English)](https://img.shields.io/badge/Read%20Online-English-blue?style=for-the-badge)](https://bocaletto-luca.github.io/Directory-Monitor/index.html)  

[![Leggi Online (Italiano)](https://img.shields.io/badge/Leggi%20Online-Italiano-green?style=for-the-badge)](https://bocaletto-luca.github.io/Directory-Monitor/index-ita.html)

## Table of Contents

1. [Overview](#overview)  
2. [Features](#features)  
3. [Repository Structure](#repository-structure)  
4. [Requirements](#requirements)  
5. [Installation](#installation)  
6. [Usage](#usage)  
   - [English Version](#english-version)  
   - [Italian Version](#italian-version)  
7. [Configuration Options](#configuration-options)  
8. [Logging](#logging)  
9. [License](#license)  

---

## Overview

Directory Monitor is a lightweight, text-menu tool written in pure Python (stdlib only) that lets you watch one or more folders for filesystem changes via polling. It detects:

- File and folder **creation**  
- **Deletion**  
- **Modification**  

You can configure recursive scans, include/exclude hidden entries, and apply advanced glob filters. Press **ESC** at any time during monitoring to stop and return to the menu.

---

## Features

- Monitor **multiple** directories simultaneously  
- **Recursive** or non-recursive scanning  
- Toggle **hidden** file/folder inclusion  
- **Glob**-based include/exclude filters  
- Configurable **polling interval**  
- Real-time **console** and optional **file** logging  
- Easily switch between **English** and **Italian** interfaces  
- No external dependencies (Python 3.6+ stdlib only)  

---

## Repository Structure

```text
Directory-Monitor/
├── LICENSE
├── README.md
├── main_eng.py      # English interface
└── main_ita.py      # Italian interface
```

---

## Requirements

- Python **3.6** or later  
- Standard library modules only: `os`, `sys`, `time`, `fnmatch`, `logging`, `termios`, `tty`, `select`, `pathlib`  
- No third-party packages required  

---

## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/bocaletto-luca/Directory-Monitor.git
   cd Directory-Monitor
   ```

2. **(Optional) Make scripts executable**  
   ```bash
   chmod +x main_eng.py main_ita.py
   ```

---

## Usage

Run the script corresponding to your preferred language:

### English Version

```bash
python3 main_eng.py
# Or, if executable:
./main_eng.py
```

### Italian Version

```bash
python3 main_ita.py
# Or, if executable:
./main_ita.py
```

Follow the on-screen menu to configure directories, polling interval, recursion, hidden files, filters, and logging.

---

## Configuration Options

Once you start the script, you can:

1. **Add/Remove Directories**  
2. **Set Polling Interval** (in seconds)  
3. **Toggle Recursive Scan**  
4. **Toggle Hidden Entries**  
5. **Manage Advanced Filters**  
   - **Include patterns** (e.g. `*.log`, `data/**/*.csv`)  
   - **Exclude patterns** (e.g. `temp/*`, `*/.git/*`)  
6. **Specify Log File** (or use stdout)  
7. **Start/Stop Monitoring** (press ESC to stop)  
8. **Exit**  

---

## Logging

Events are logged in the format:

```
YYYY-MM-DD HH:MM:SS,mmm LEVEL   [base_path] +Added   FILE: example.txt
YYYY-MM-DD HH:MM:SS,mmm LEVEL   [base_path] *Modified DIR : docs/
YYYY-MM-DD HH:MM:SS,mmm LEVEL   [base_path] -Removed  FILE: old.log
```

- `+Added`    → new file/folder  
- `*Modified` → timestamp changed  
- `-Removed`  → file/folder deleted  

Logs appear in the console by default. To capture them in a file, specify a logfile path in the menu.

---

## License

This project is released under the **GNU General Public License v3.0**.  
See the [LICENSE](LICENSE) file for details.  

---

© 2025 Bocaletto Luca  
https://github.com/bocaletto-luca/Directory-Monitor
