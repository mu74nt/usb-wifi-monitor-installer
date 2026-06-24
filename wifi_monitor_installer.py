#!/usr/bin/env python3

import subprocess
import time
import re
import sys
import logging
import os
from pathlib import Path

TIMEOUT_USB = 60
WAIT_AFTER_INSTALL = 5
LOGFILE = "/tmp/wifi_monitor_installer.log"

try:

    if os.path.exists(LOGFILE):

        os.remove(LOGFILE)

except Exception:

    pass

logging.basicConfig(

    filename=LOGFILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    force=True

)

CHIPSET_DB = {

    "0bda:b812": {

        "name":"RTL88x2BU",
        "driver":"rtl88x2bu",
        "dkms":"rtl88x2bu-dkms",
        "module":"88x2bu"

    },

    "0bda:8812": {

        "name":"RTL8812AU",
        "driver":"rtl8812au",
        "dkms":"realtek-rtl88xxau-dkms",
        "module":"8812au"

    },

    "0bda:c811": {

        "name":"RTL8821CU",
        "driver":"rtl8821cu",
        "dkms":"rtl8821cu-dkms",
        "module":"8821cu"

    },

    "0cf3:e300": {

        "name":"ATH9K",
        "driver":"ath9k-htc-firmware",
        "dkms":None,
        "module":"ath9k_htc"

    }

}


def run(cmd, capture=True):

    logging.info(f"RUN: {cmd}")

    p = subprocess.run(
        cmd,
        shell=True,
        text=True,
        capture_output=capture
    )

    stdout = p.stdout if p.stdout else ""
    stderr = p.stderr if p.stderr else ""

    if stdout:

        logging.info(stdout)

    if stderr:

        logging.info(stderr)

    return (
        p.returncode,
        stdout.strip(),
        stderr.strip()
    )


def require_root():

    if subprocess.getoutput("id -u") != "0":

        print("Ejecutar como root")

        sys.exit(1)


def snapshot_usb():

    rc,out,_ = run("lsusb")

    if rc:

        return set()

    ids=set()

    for line in out.splitlines():

        m=re.search(
            r'ID ([0-9a-f]{4}:[0-9a-f]{4})',
            line,
            re.I
        )

        if m:

            ids.add(
                m.group(1).lower()
            )

    return ids

def wait_new_usb():

    current = snapshot_usb()

    for dev in current:

        if dev in CHIPSET_DB:

            print(
                f"Adaptador ya conectado: {dev}"
            )

            return dev

    print(
        f"Conectar adaptador ({TIMEOUT_USB}s)"
    )

    start=time.time()

    while time.time()-start < TIMEOUT_USB:

        now=snapshot_usb()

        for dev in now:

            if dev in CHIPSET_DB:

                return dev

        time.sleep(1)

    return None


def install_prerequisites():

    kernel=subprocess.getoutput(
        "uname -r"
    )

    pkgs=[

        "build-essential",
        "dkms",
        "git",
        "usbutils",
        "iw",
        f"linux-headers-{kernel}"

    ]

    cmd="apt update && apt install -y "

    cmd+=" ".join(pkgs)

    run(cmd,capture=False)


def install_package(pkg):

    if not pkg:

        return False

    rc,_,_=run(

        f"apt install -y {pkg}",
        capture=False

    )

    return rc==0


def fix_broken():

    run(

        "apt --fix-broken install -y",
        capture=False

    )


def dkms_ok(module):

    rc,out,_=run(
        "dkms status"
    )

    return module.lower() in out.lower()


def load_module(module):

    run(
        f"modprobe {module}",
        capture=False
    )


def reload_usb_stack():

    run(
        "udevadm trigger",
        capture=False
    )

    time.sleep(3)


def wireless_interfaces():

    rc,out,_=run(
        "iw dev"
    )

    if rc:

        return []

    return re.findall(
        r'Interface ([^\\s]+)',
        out
    )


def monitor_supported(iface):

    rc,_,_=run(

        f"iw dev {iface} set type monitor"

    )

    if rc:

        return False

    run(
        f"iw dev {iface} set type managed"
    )

    return True


def print_debug():

    print()

    print("===== DEBUG =====")

    run(
        "lsusb",
        capture=False
    )

    print()

    run(
        "dmesg | tail -50",
        capture=False
    )


def install_driver(data):

    print("Instalando driver")

    ok=install_package(
        data["driver"]
    )

    if ok:

        return True

    print("Fix broken")

    fix_broken()

    ok=install_package(
        data["driver"]
    )

    if ok:

        return True

    if data["dkms"]:

        print("Intentando DKMS")

        ok=install_package(
            data["dkms"]
        )

        if not ok:

            return False

        if not dkms_ok(
            data["module"]
        ):

            return False

    load_module(
        data["module"]
    )

    return True


def main():

    require_root()

    install_prerequisites()

    device=wait_new_usb()

    if not device:

        print("No detectado")

        return

    print(
        f"VID:PID {device}"
    )

    if device not in CHIPSET_DB:

        print(
            "Chipset desconocido"
        )

        print_debug()

        return

    driver=CHIPSET_DB[
        device
    ]

    print(
        f"Chipset: {driver['name']}"
    )

ok=install_driver(driver)

time.sleep(3)

interfaces = wireless_interfaces()

if interfaces:

    print(
        "La interfaz ya existe, continuando..."
    )

elif not ok:

    print(
        "Falló instalación"
    )

    return

    print(
        "Esperando interfaz..."
    )

    time.sleep(
        WAIT_AFTER_INSTALL
    )

    load_module(
        driver["module"]
    )

    interfaces=wireless_interfaces()

    if not interfaces:

        reload_usb_stack()

        interfaces=wireless_interfaces()

    if not interfaces:

        print(
            "Reconectar USB manualmente"
        )

        time.sleep(10)

        interfaces=wireless_interfaces()

    if not interfaces:

        print(
            "No apareció interfaz"
        )

        print_debug()

        return

    print()

    print("Interfaces:")

    for iface in interfaces:

        print(
            f"  {iface}"
        )

        if monitor_supported(
            iface
        ):

            print(
                "   monitor OK"
            )

        else:

            print(
                "   monitor FAIL"
            )

    print()

    print(
        f"Log: {LOGFILE}"
    )


if __name__=="__main__":

    main()
