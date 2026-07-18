#!/usr/bin/env python3

import subprocess
import datetime

SERVICES = ["nginx", "cloudshift-payment.service", "cron"]

LOG = "/var/log/monitor.log"

for svc in SERVICES:
    check = subprocess.run(
        ["systemctl", "is-active", "--quiet", svc]
    )

    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

    with open(LOG, "a") as log:
        if check.returncode == 0:
            log.write(f"{stamp} {svc} OK\n")
        else:
            subprocess.run(["systemctl", "restart", svc])
            log.write(f"{stamp} {svc} was DOWN, restarted\n")
