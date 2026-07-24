#!/usr/bin/env python3

import subprocess
import os
from datetime import datetime

os.makedirs("/var/www/app", exist_ok=True)

APP_DIR = "/var/www/app"
os.chdir(APP_DIR)

# pretend new release files were copied here

result = subprocess.run(["systemctl", "restart", "cron"])

check = subprocess.run(
    ["systemctl", "is-active", "--quiet", "cron"]
)

if check.returncode == 0:
    print("Deploy OK", datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))
else:
    print("Deployment Not Successful!")
