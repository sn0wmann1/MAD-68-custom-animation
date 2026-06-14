# MAD68 HE (Hall Effect) — Solid Color Control

For the MAD68 HE model (PID `0x1058`), the per-key animation protocol differs from the Pro model (PID `0x10D4`).

## Files

- `mad68_he_solid.py` — Set all keys to a single solid color. Auto-detects between HE and Pro.
- `rgb_engine.py` — Full RGB engine for per-key animations. Now auto-detects model.

## Usage

```bash
# Set keyboard to solid color (hex RRGGBB) — auto-detects HE or Pro
python3 engine/mad68_he_solid.py FF0000   # Red
python3 engine/mad68_he_solid.py 00FF00   # Green
python3 engine/mad68_he_solid.py 0000FF   # Blue

# Force a specific model
python3 engine/mad68_he_solid.py FF0000 0x10D4  # Pro model

# Probe all known PIDs
python3 engine/mad68_he_solid.py FF0000 --pid
```

## Protocol

HE model uses 32-byte HID output reports (report ID 0):

```
[7, 65, 2, 0, 0x96, R, G, B, 0xB1, zero-pad...]
```

Reverse-engineered from [hub.f.gg](https://hub.f.gg) (Fierce Gaming Gear configurator) via WebHID JS console capture.

## Linux Setup

```bash
# Install hidapi
pip install hidapi

# Create udev rule for HID access (avoids needing sudo)
echo 'SUBSYSTEM=="hidraw", ATTRS{idVendor}=="373b", MODE="0666"' | sudo tee /etc/udev/rules.d/99-mad68.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

The keyboard must be in **Customization** mode (select "Custom" in the official software or via hub.f.gg).

## Other Models

This has been tested on MAD68 HE (PID `0x1058`) and should work on MAD68 Pro (PID `0x10D4`).

If you have another variant, open an issue or comment on the PR with:
- Your keyboard model name
- Your PID (check with `lsusb` on Linux or Device Manager on Windows)
- Whether the code works or fails

I don't have other models to test with, but I can help debug if you share logs.
