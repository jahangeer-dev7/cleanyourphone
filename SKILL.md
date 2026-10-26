---
name: cleanyourphone
description: Turn your AI coding assistant into a personal Android phone technician. Connects to any Android smartphone over USB or Wireless ADB, audits background bloatware, strips lockscreen ads (Glance), reclaims RAM, tunes 120Hz display fluidity, and boosts audio. Zero root required, 100% reversible.
user-invocable: true
tags: [android, adb, debloat, optimization, performance, privacy, phone]
---

# cleanyourphone Agent Skill

This skill teaches coding agents (Claude Code, OpenAI Codex, Gemini CLI, Cursor, Windsurf) how to audit, debloat, and optimize any Android smartphone connected via USB or Wireless ADB.

## Universal Brand Support
The agent auto-detects the connected device's manufacturer and maps to the appropriate production profile:
- **Samsung** (One UI 4 / 5 / 6 / 7) → `profiles/samsung-oneui.txt` (Kills Glance ads, Samsung Free, Bixby, Facebook bloat)
- **Xiaomi / Redmi / POCO** (HyperOS / MIUI) → `profiles/xiaomi-hyperos.txt` (Kills MSA system ads, GetApps spam, Analytics)
- **Realme / Oppo / OnePlus** (Realme UI / ColorOS) → `profiles/realme-oppo-oneplus.txt` (Kills HeyTap tracking, Lockscreen Magazine)
- **Vivo & iQOO** (Funtouch OS) → `profiles/vivo-iqoo.txt` (Kills V-Appstore, Jovi push engines)
- **Infinix, Tecno & Itel** (XOS / HiOS) → `profiles/transsion-xos-hios.txt` (Kills Palm Store, Phone Master, Lockscreen Magazine)
- **Motorola** (MyUX / Hello UI) → `profiles/motorola-myux.txt`
- **Universal Google Background Services** → `profiles/universal-google-bloat.txt`

## Core Invariants (Non-Negotiable)
1. **Never use `pm uninstall`**: Always use `pm disable-user --user 0 <pkg>`. It freezes packages safely and is 100% reversible via `tools/restore.sh`.
2. **Never break critical phone functions**: Never touch Phone Dialer (`InCallUI`), Emergency SOS, Keyguard, System UI, Camera, Biometrics, or Google Play Store.
3. **Always take a baseline snapshot before modifying**: Record package states, free RAM, and take a screenshot before touching anything.
4. **Always verify stability after changes**: Inspect `dumpsys power` and take a verification screenshot (`tools/phone.py --screenshot`).

## Everyday Agent Workflow

When a user asks: *"clean my phone"*, *"speed up my phone"*, or *"remove bloatware"*:

```
1. Detect Connection ──▶ 2. Probe Device ──▶ 3. Baseline Audit ──▶ 4. Confirm With User ──▶ 5. Apply & Verify
   (USB or Wireless)        (Brand & Model)     (RAM, Storage, Ads)   (Safe checklist)        (Delta Benchmark)
```

### Command Execution
```bash
# 1. Probe connected hardware and auto-detect profile
python3 tools/phone.py --probe

# 2. Record hardware baseline benchmark
python3 tools/bench.py --save backups/baseline.json

# 3. Preview debloat manifest
./tools/disable.sh --dry-run profiles/<brand>.txt

# 4. Apply non-destructive debloat
./tools/disable.sh profiles/<brand>.txt

# 5. Apply system fluidity & security tweaks
python3 tools/phone.py shell "settings put global window_animation_scale 0.5"
python3 tools/phone.py shell "settings put global transition_animation_scale 0.5"
python3 tools/phone.py shell "settings put global animator_duration_scale 0.5"
python3 tools/phone.py shell "settings put global private_dns_mode hostname"
python3 tools/phone.py shell "settings put global private_dns_specifier dns.adguard-dns.com"

# 6. Capture verification screenshot and compare benchmarks
python3 tools/phone.py --screenshot backups/post_clean.png
python3 tools/bench.py --compare backups/baseline.json
```
