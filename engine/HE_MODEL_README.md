# MAD68 HE (Hall Effect) - Solid Color Control

For the MAD68 HE model (PID `0x1058`), the per-key animation protocol differs from the Pro model (PID `0x10D4`). 

This directory contains:
- `mad68_he_solid.py` - Set all keys to a single solid color using the HE-specific HID protocol
- `rgb_engine.py` - Updated with `pid=0x1058` support (now auto-detects HE models)

## Usage

```bash
# Set keyboard to a static color (hex RRGGBB)
python3 engine/mad68_he_solid.py FF0000   # Red
python3 engine/mad68_he_solid.py 00FF00   # Green
python3 engine/mad68_he_solid.py 0000FF   # Blue
```

## Protocol

The HE model uses 32-byte HID output reports (report ID 0):
```
[7, 65, 2, 0, 0x96, R, G, B, 0xB1, zero-pad...]
```

This was reverse-engineered from hub.f.gg (Fierce Gaming Gear's configurator) and confirmed working on the MAD68 HE with PID `0x1058`.

## Requirements

- Python `hidapi` package
- Write access to the keyboard's HID device (udev rule recommended):
  ```
  SUBSYSTEM=="hidraw", ATTRS{idVendor}=="373b", ATTRS{idProduct}=="1058", MODE="0666"
  ```
- Keyboard must be in **Customization** mode
