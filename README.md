asetek_wheelbase_cli
====================

- [asetek\_wheelbase\_cli](#asetek_wheelbase_cli)
- [tldr](#tldr)
- [Warning](#warning)
- [Why not RaceHub](#why-not-racehub)
- [Development](#development)
  - [One-time: Udev-Setup](#one-time-udev-setup)
  - [One-time: Python-Setup](#one-time-python-setup)
  - [Test-Usage](#test-usage)
    - [Debug logs](#debug-logs)
- [Known issues](#known-issues)
- [How to use the wheelbase under Linux](#how-to-use-the-wheelbase-under-linux)
  - [One time setup](#one-time-setup)
  - [Per game setup](#per-game-setup)
    - [Alternative: Per Proton environment setup](#alternative-per-proton-environment-setup)


# tldr
Asetek Simsports wheelbases La Prima, Forte & Invicta can be used under Linux [without any driver and with full FFB with games](#how-to-use-the-wheelbase-under-linux).

They however currently (2024-10-18) cannot be configured under Linux (e.g. enabling High Torque mode), therefore this CLI could be useful.

# Warning
This CLI is currently not intended for regular use, highly experimental and maybe will never be finished.

This implementation is severely lacking knowledge about the datastructures Asetek has designed to encapsulate in USB HID reports. It may cause damage to the wheelbase through incorrect configuration.

Use at your own risk.

Also last testing was done with a firmware from around March 2024. Newer firmware may behave differently.

# Why not RaceHub
Asetek Simsports wheelbases (La Prima, Forte, Invicta) are configured through their proprietary software [RaceHub](https://www.asetek.com/simsports/racehub/).

At the time of writing, RaceHub only runs correctly on Windows. Running RaceHub under Linux via Proton or Wine leads to exceptions internally which likely causes the application to never discover USB devices properly.

So under Linux we currently (2024-10-18) have no way to configure the wheelbases.

This CLI currently only mimicks USB communication of RaceHub to read & configure few things in La Prima wheelbases.

# Development
## One-time: Udev-Setup
The CLI needs to be able to send and receive USB data via pyusb, therefore a udev rule is required.

The following udev rule will grant all unprivileged users all USB access to any Asetek USB device. It is highly permissive, but this way it will work for all wheelbases under Vendor Id `2433`:
```bash
SUBSYSTEMS=="usb", ATTRS{idVendor}=="2433", MODE="0660", TAG+="uaccess"
```

Create a file such as `/etc/udev/rules.d/60-asetek.rules` containing the line above.

Then reload udev rules:
```bash
$ sudo udevadm control --reload-rules && sudo udevadm trigger
```

## One-time: Python-Setup
In the directory of this cloned repository, create a Python venv and install the CLI in an editable manner, so that any changes are live:
```bash
$ python -m venv venv
$ . venv/bin/activate
$ pip install -e .
```

## Test-Usage
```bash
$ . venv/bin/activate
$ asetek-wheelbase-cli test
2024-10-18T00:25:49Z INFO     Found wheelbase La Prima 
2024-10-18T00:25:49Z INFO     Successful read data from device 
2024-10-18T00:25:50Z INFO     Successfully read configuration: LaPrimaWheelbaseConfiguration(high_torque_enabled=False, profile_id=1, profile_name='GT3')
$ asetek-wheelbase-cli config
2024-10-18T00:27:32Z INFO     Found wheelbase La Prima 
{
    "high_torque_enabled": false,
    "profile_id": 1,
    "profile_name": "GT3"
}
$ asetek-wheelbase-cli set high-torque on
2024-10-18T00:27:59Z INFO     Found wheelbase La Prima 
2024-10-18T00:27:00Z INFO     High Torque successfully enabled
$ asetek-wheelbase-cli config
2024-10-18T00:30:05Z INFO     Found wheelbase La Prima 
{
    "high_torque_enabled": true,
    "profile_id": 1,
    "profile_name": "GT3"
}
```

### Debug logs
Any sent/received USB HID data is logged, when running the CLI with `-v`, e.g.:
```bash
$ asetek-wheelbase-cli -v test
2024-10-18T00:29:00Z INFO     Found wheelbase La Prima 
2024-10-18T00:29:00Z DEBUG    Using configuration 0 
2024-10-18T00:29:00Z DEBUG    Using interface 0 
2024-10-18T00:29:00Z DEBUG    Using in endpoint 0 
2024-10-18T00:29:00Z DEBUG    Using out endpoint 1 
2024-10-18T00:29:00Z DEBUG    Received data: 04b680000000000000000000000000000000000000000000000000000000000000 
2024-10-18T00:29:00Z INFO     Successful read data from device 
2024-10-18T00:29:00Z DEBUG    Sending data: 6b000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 
2024-10-18T00:29:00Z DEBUG    Received data: 6c010100000018310b0000000000b6800100010001000400010200000000000000000000000000000000000000000000000000000014000000a5a5a500 
2024-10-18T00:29:00Z DEBUG    Sending data: 6b720100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000 
2024-10-18T00:29:00Z DEBUG    Received data: 6c79000000004754330044697361626c696e0000000000000000000000000000000000000000a5a5000000000000000000000000000000000000000000 
2024-10-18T00:29:00Z INFO     Successfully read configuration: LaPrimaWheelbaseConfiguration(high_torque_enabled=False, profile_id=1, profile_name='GT3')
```

To also enable debug logs of pyusb & libusb, you can use `-vv`.

# Known issues
- High torque mode can only be enabled and disabled once after connecting the wheelbase, as any further tries require more understanding of the communication structure
- Only La Prima is somewhat tested and implemented
- Exceptions are not being catched to be able to debug more easily

# How to use the wheelbase under Linux
No driver needed, only a one-time configuration:

## One time setup
1. Create an udev rule allowing unprivileged users access to wheelbase and wheel via hidraw
  e.g. a file `/etc/udev/rules.d/60-asetek.rules` with content:
  ```
# Asetek La Prima Wheelbase
KERNEL=="hidraw*", ATTRS{idVendor}=="2433", ATTRS{idProduct}=="f303", MODE="0660", TAG+="uaccess"
# Asetek La Prima Steering Wheel
KERNEL=="hidraw*", ATTRS{idVendor}=="2433", ATTRS{idProduct}=="f203", MODE="0660", TAG+="uaccess"
  ```
3. Reload udev rules: `sudo udevadm control --reload-rules && sudo udevadm trigger`

## Per game setup
Add Proton setting `PROTON_ENABLE_HIDRAW=0x2433/0xf303,0x2433/0xf203` to your environment. This can be done via Steam via `Game Properties > General > Launch Options`, so e.g.:
`PROTON_ENABLE_HIDRAW=0x2433/0xf303,0x2433/0xf203 %command%`

Forte and Invicta wheelbases and wheels have different PID values, so adjust accordingly.

### Alternative: Per Proton environment setup
Alternatively to per-game one can set this setting once for each Proton installation via `user_settings.py`: https://github.com/ValveSoftware/Proton/wiki/Proton-FAQ
