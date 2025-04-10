# Qnap one-touch-copy for Linux

Qnap one-touch-copy for Linux is a daemon written in Python to re-implement
[Qnap's one-touch-copy](https://docs.qnap.com/operating-system/qts/4.5.x/en-us/GUID-86811138-8671-4B7E-BC28-57FE1173D343.html)
feature for Linux. It is still under development so installation and usage may not be user-friendly yet but don't
hesitate to contribute!

## Installation

This daemon relies on a kernel module available at https://github.com/0xGiddi/qnap8528.

1. Follow the installation instruction at https://github.com/0xGiddi/qnap8528 to install the kernel module
2. As root, activate the modules `qnap8528` and `ledtrig-timer` on boot by adding them to `/etc/modules`:
   ```bash
   cat << EOF >> /etc/modules
   qnap8528
   ledtrig-timer
   EOF
   # This activate the modules
   modprobe qnap8528
   modprobe ledtrig-timer
   ```
3. Clone the code under `/usr/share/onetouchcopy` (you can install it elsewhere but the systemd service currently use t
   this path:
   ```bash
   mkdir -p /usr/share/onetouchcopy
   git clone https://github.com/christophehenry/qnap-one-touch-copy-linux /usr/share/onetouchcopy
   cd /usr/share/onetouchcopy
   python3 -m venv venv
   activate venv/bin/activate
   pip install -e .
   ```
4. Install the systemd service and udev rule:
   ```bash
   cd /usr/share/onetouchcopy
   cp resources/10-qnap-usb-description.rules /etc/udev/rules.d/10-qnap-usb-description.rules
   # Reload udev rules
   udevadm control --reload-rules && udevadm trigger
   cp resources/10-qnap-usb-description.rules /etc/systemd/system/onetouchcopy.service
   # Activate service
   systemctl start onetouchcopy
   systemctl enable onetouchcopy
   ```
