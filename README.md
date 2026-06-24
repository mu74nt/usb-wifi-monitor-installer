# USB WiFi Monitor Installer

## Overview

This tool automatically detects supported USB Wi-Fi adapters on Linux, installs the required drivers (DKMS or in-kernel firmware), and verifies monitor mode capability.

It is intended for security testing environments and Linux-based penetration testing distributions.

## Supported Chipsets

The script currently supports the following USB Wi-Fi chipsets:

- Realtek RTL88x2BU (`0bda:b812`)
- Realtek RTL8812AU (`0bda:8812`)
- Realtek RTL8821CU (`0bda:c811`)
- Atheros AR9271 / ath9k_htc (`0cf3:e300`)

## Requirements

- Linux system (Debian-based recommended)
  - Kali Linux
  - Ubuntu
  - Debian
  - Parrot OS
- Root privileges
- Internet connection
- USB Wi-Fi adapter compatible with one of the supported chipsets

## Dependencies Installed

The script installs the following packages:

- build-essential
- dkms
- git
- usbutils
- iw
- linux-headers-$(uname -r)

## Features

- Automatic USB Wi-Fi adapter detection
- Chipset identification via VID:PID
- Automatic driver installation (APT/DKMS)
- Kernel module loading
- Interface detection
- Monitor mode support validation
- Debug logging (`/tmp/wifi_monitor_installer.log`)

## Usage

```bash
sudo python3 wifi_monitor_installer.py
```
##Notes

- The script must be run as root.
- Only explicitly supported chipsets will be recognized.
- Some drivers may require manual intervention depending on kernel version.
- 
##Disclaimer

This tool is intended for authorized security testing and educational purposes only.
