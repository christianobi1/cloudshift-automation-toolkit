#!/usr/bin/env python3

import shutil
import os
from datetime import date

BACKUP_DIR = "/var/backups"
TODAY = date.today().isoformat()

os.makedirs(BACKUP_DIR, exist_ok=True)

shutil.make_archive(
    f"{BACKUP_DIR}/site-{TODAY}",
    "gztar",
    "/var/www"
)

print(f"Backup done: site-{TODAY}.tar.gz")
