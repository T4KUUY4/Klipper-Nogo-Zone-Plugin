# Klipper No-Go Zone Plugin

A lightweight Klipper plugin that prevents your toolhead from entering defined restricted areas (bounding boxes). It intelligently checks the entire path of a movement using the Liang-Barsky line clipping algorithm, ensuring the toolhead cannot "leap over" a forbidden zone in a single long move.

This is highly useful for protecting bed clamps, physical Z-probes, nozzle brushes, and tool docks from accidental crashes.

## 🛠 Quick Installation

If you just want to grab the file and start using it, you can pull the plugin directly into your Klipper `extras` folder and restart Klipper with a single command via SSH:

```bash
curl -sSL -o ~/klipper/klippy/extras/nogo_zone.py https://raw.githubusercontent.com/T4KUUY4/Klipper-Nogo-Zone-Plugin/main/nogo_zone.py && sudo systemctl restart klipper
```

## 🔄 Moonraker Update Manager

If you want Moonraker (and frontends like Mainsail/Fluidd) to track updates for this plugin, you should install it by cloning the repository instead of downloading the single file.

**1. Clone the repository and link the plugin:**
Run these commands in your SSH terminal:
```bash
cd ~
git clone https://github.com/T4KUUY4/Klipper-Nogo-Zone-Plugin.git
ln -sf ~/Klipper-Nogo-Zone-Plugin/nogo_zone.py ~/klipper/klippy/extras/nogo_zone.py
sudo systemctl restart klipper
```

**2. Add the update manager block:**
Add the following configuration block to your `moonraker.conf` to enable update tracking:

```ini
[update_manager Klipper-Nogo-Zone-Plugin]
type: git_repo
path: ~/Klipper-Nogo-Zone-Plugin
origin: https://github.com/T4KUUY4/Klipper-Nogo-Zone-Plugin.git
managed_services: klipper
primary_branch: main
```

## ⚙️ Configuration

Define your restricted zones in your `printer.cfg`. 
*Note: Klipper requires a space between `nogo_zone` and its identifier number for multiple instances.*

```ini
[nogo_zone 0]
x_min: 10
x_max: 20
y_min: 10
y_max: 20

[nogo_zone 1]
x_min: 100
x_max: 120
y_min: 100
y_max: 120
```

## 🚨 How it works

- **Path Interception:** The plugin wraps Klipper's internal `toolhead.move` function, evaluating the complete path of every request.
- **Safe Homing:** If the printer's X and Y axes are not yet homed (e.g., during startup or `G28`), the check is safely bypassed. This prevents false positives when Klipper assumes the unhomed toolhead is at `0,0`.
- **Immediate Halt:** If a move attempts to enter or pass through a configured `nogo_zone`, the move is aborted before the motors act, throwing a fatal G-code error to protect your machine.
