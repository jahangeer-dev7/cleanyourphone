# CLAUDE.md — Claude Code Instructions

This file guides Claude Code on project structure, commands, architecture, and safety rules for `cleanyourphone`.

---

## 🛠️ Project Overview
`cleanyourphone` is the phone counterpart to CleanYourTV (`tv-vibehack/CleanYourTV`). It provides a lightweight, pure-Python and bash toolkit to audit, debloat, benchmark, and optimize Android smartphones over USB or Wireless ADB without root access.

---

## 📁 Repository Layout
```
cleanyourphone/
├── AGENTS.md                 # Agent safety directives and non-negotiables
├── CLAUDE.md                 # Claude Code reference instructions
├── PROMPT.md                 # Universal copy-paste prompt for AI agents
├── README.md                 # Viral GitHub README with benchmark tables
├── backups/                  # Timestamped package state and benchmark dumps
├── profiles/                 # OEM brand debloat manifests
│   └── infinix-xos.txt       # Tested manifest for Infinix/Transsion XOS devices
└── tools/
    ├── bench.py              # RAM, storage, process count, and animation benchmark
    ├── disable.sh            # Safe batch debloater with automatic rollback logging
    ├── phone.py              # ADB client: probe, screencap, pair, connect, push/pull
    └── restore.sh            # 1-click package restoration script
```

---

## ⚡ Common Commands

### Device Probing & Control
```bash
# Probe device specs and health
python3 tools/phone.py --probe
python3 tools/phone.py --probe --json

# List attached devices
python3 tools/phone.py --devices

# Capture device screenshot
python3 tools/phone.py --screenshot phone_screen.png

# Wireless ADB pairing & connect
python3 tools/phone.py --pair 192.168.1.50:42115 123456
python3 tools/phone.py --connect 192.168.1.50:5555

# Run adb shell command directly
python3 tools/phone.py shell "getprop ro.product.model"
```

### Debloat & Restore
```bash
# Dry run preview (no modifications made)
./tools/disable.sh --dry-run profiles/infinix-xos.txt

# Apply debloat profile
./tools/disable.sh profiles/infinix-xos.txt

# 1-Click Restore all disabled packages
./tools/restore.sh backups/last_disabled.txt

# Restore single package
./tools/restore.sh com.transsion.camera
```

### Benchmarking & Performance
```bash
# Capture full system benchmark
python3 tools/bench.py

# Save baseline snapshot
python3 tools/bench.py --save /tmp/baseline_bench.json

# Compare current performance against baseline
python3 tools/bench.py --compare /tmp/baseline_bench.json
```

---

## 🔒 Safety Invariants
1. **Never use `pm uninstall`**: Always use `pm disable-user --user 0`.
2. **Never disable critical system services**: Telephony, Emergency SOS, SystemUI, InCallUI, Keyguard, Camera, Biometrics, and Google Play Store are strictly protected.
3. **Always redirect stdin in bash loops**: When calling `adb` inside `while read` loops in bash, always append `< /dev/null` to prevent `adb` from consuming subsequent lines.
4. **Standard library preferred**: Keep Python tools compatible with standard library (`argparse`, `subprocess`, `json`, `shutil`, `re`, `time`).
