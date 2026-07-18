#!/usr/bin/env python3

import subprocess
import datetime
import os
from pathlib import Path

script_dir = Path(__file__).resolve().parent
os.chdir(script_dir)

print("=== Toolkit run", datetime.datetime.now(), "===")

subprocess.run(["python3", "backup.py"])
subprocess.run(["python3", "monitor.py"])

print("=== Toolkit finished ===")
