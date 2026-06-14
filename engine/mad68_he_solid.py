#!/usr/bin/env python3
"""Set MAD68 keyboard RGB using hub.f.gg protocol (solid color)

Supports both HE (PID 0x1058) and Pro (PID 0x10D4) models.
Auto-detects connected model by probing known PIDs.

Usage:
  python3 mad68_he_solid.py FF0000         # Red (auto-detect)
  python3 mad68_he_solid.py 00FF00 --pid    # Green, probe all PIDs
  python3 mad68_he_solid.py 0000FF 0x10D4  # Blue, force Pro model

Requirements:
  - Python hidapi (pip install hidapi)
  - On Linux: udev rule for HID access or run as root
"""
import hid, sys, os

KNOWN_PIDS = [0x1058, 0x10D4]  # HE, Pro
INTERFACE = 1

def find_device(pids):
    for pid in pids:
        for d in hid.enumerate(0x373B, pid):
            if d.get('interface_number') == INTERFACE:
                return d['path'], pid
    return None, None

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mad68_he_solid.py <hexcolor> [--pid|<force_pid>]")
        print("  hexcolor: RRGGBB (e.g. FF0000 for red)")
        print("  --pid: probe all known PIDs")
        print("  force_pid: e.g. 0x10D4 for Pro model")
        sys.exit(1)

    hex_color = sys.argv[1].lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

    pids = KNOWN_PIDS[:]
    if len(sys.argv) >= 3:
        arg = sys.argv[2]
        if arg != '--pid':
            pids = [int(arg, 16)]

    target, found_pid = find_device(pids)
    if not target:
        model_hint = "MAD68 HE" if 0x1058 in pids else ("MAD68 Pro" if 0x10D4 in pids else "MAD68")
        print(f"Error: {model_hint} keyboard not found.")
        print("  Check connection and try:")
        print("  - On Linux: sudo python3 mad68_he_solid.py <color>")
        print("  - Add udev rule: SUBSYSTEM==\"hidraw\", ATTRS{idVendor}==\"373b\", MODE=\"0666\"")
        print("  - Use --pid to probe: python3 mad68_he_solid.py FF0000 --pid")
        print(f"  - Force specific model: python3 mad68_he_solid.py FF0000 0x{KNOWN_PIDS[0]:04X}")
        sys.exit(1)

    model_name = "HE" if found_pid == 0x1058 else "Pro"
    print(f"Found MAD68 {model_name} (PID 0x{found_pid:04X})")

    dev = hid.device()
    try:
        dev.open_path(target)
    except Exception as e:
        print(f"Error opening device: {e}")
        print("  Try running with sudo, or install udev rule:")
        print(f'  SUBSYSTEM=="hidraw", ATTRS{{idVendor}}=="373b", ATTRS{{idProduct}}=="{found_pid:04x}", MODE="0666"')
        sys.exit(1)

    data = bytearray([7, 65, 2, 0, 0x96, r, g, b, 0xB1] + [0] * 23)
    dev.write(bytes(data))
    dev.close()
    print(f"Set color to #{hex_color}")

if __name__ == '__main__':
    main()
