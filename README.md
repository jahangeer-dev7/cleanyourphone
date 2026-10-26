<p align="center">
  <img src="assets/banner.png" alt="cleanyourphone — AI-driven Android smartphone optimization and debloating" width="100%" onerror="this.style.display='none'">
</p>

<h1 align="center">cleanyourphone</h1>

<p align="center">
  <b>The open-source, AI agent-driven Android phone transformation engine.</b><br>
  Turn your AI coding assistant (Claude Code, Codex, Cursor, Gemini CLI) into a personal mobile systems engineer.<br>
  Audits, debloats, accelerates, and secures any Android smartphone over <b>USB</b> or <b>Wireless ADB</b>.
</p>

<p align="center">
  <a href="#how-it-works">How It Works</a> &nbsp;·&nbsp;
  <a href="#supported-brands">Supported Brands</a> &nbsp;·&nbsp;
  <a href="#the-agent-setup">Run with AI</a> &nbsp;·&nbsp;
  <a href="#safety-pledge">Safety Guarantee</a> &nbsp;·&nbsp;
  <a href="#benchmarks">Live Benchmarks</a> &nbsp;·&nbsp;
  <a href="AGENTS.md">Agent Guide</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Android-API%2028%20to%2035%20(Android%209%20--%2015)-3DDC84?style=for-the-badge&logo=android&logoColor=white" alt="Android Versions"/>
  <img src="https://img.shields.io/badge/Root-ZERO%20ROOT%20REQUIRED-success?style=for-the-badge" alt="Zero Root"/>
  <img src="https://img.shields.io/badge/Safety-100%25%20Reversible-blue?style=for-the-badge" alt="100% Reversible"/>
  <img src="https://img.shields.io/badge/AI%20Agent%20Ready-Claude%20%7C%20Codex%20%7C%20Cursor-orange?style=for-the-badge" alt="AI Agent Ready"/>
  <img src="https://img.shields.io/badge/License-MIT-purple?style=for-the-badge" alt="MIT License"/>
</p>

---

## ⚡ The Problem: Modern Android is Flooded With Bloatware

Out of the box, even modern smartphones from major manufacturers ship with:
- **Lockscreen Wallpaper Ads (Glance & Magazines):** Intrusive sponsored news and ads waking your screen in your pocket.
- **Spam App Stores & Notification Hijackers:** Proprietary stores (Palm Store, GetApps, V-Appstore) pushing daily clickbait notifications.
- **Fake "Cleaners" & RAM Boosters:** Ironical OEM daemons (Phone Master, iManager) that consume 300+ MB of RAM just to show ads.
- **Stealth Analytics & Sales Trackers:** Background telemetry constantly profiling battery drain, app habits, and network activity.
- **Micro-Stuttering Display Engines:** Dynamic refresh rate governors dropping to 60Hz and lagging user scrolling.

Traditional debloaters are dangerous: they run destructive `pm uninstall` commands that brick devices, break camera pipelines, or revoke banking security.

**`cleanyourphone` changes this.** It gives your AI agent an exact, verified systems engineering toolkit to audit, safely freeze bloatware, and tune your device conversationally with zero risk.

---

## 🤖 The AI Experience (How It Works)

You don't need to know ADB terminal commands or package names. Your AI assistant executes everything conversationally.

```
You: "Set up https://github.com/jahangeer-dev7/cleanyourphone and clean my phone."

Agent: 
 1. Connects over USB or pairs over Wi-Fi (Wireless ADB).
 2. Probes hardware: detects Samsung One UI, Xiaomi HyperOS, Realme UI, Vivo, or Infinix.
 3. Auto-selects the verified community debloat manifest.
 4. Asks your preferences: (keep WhatsApp, cameras, banking apps, streaming).
 5. Safely freezes 40-60 background bloaters (pm disable-user --user 0).
 6. Locks buttery-smooth 120Hz display scaling and enables AdGuard encrypted DNS.
 7. Pulls a live screenshot to verify stability and outputs an executive Before/After benchmark.
```

---

## 📱 Universal Brand Support

`cleanyourphone` is brand-neutral and includes tailored, verified production profiles in [`profiles/`](profiles/):

| Brand / Operating System | What Gets Cleaned | Profile Manifest |
| :--- | :--- | :--- |
| **Samsung Galaxy** *(One UI 4 / 5 / 6 / 7)* | Glance lockscreen ads, Samsung Free, Bixby wakeups, Facebook services, Knox analytics | [`profiles/samsung-oneui.txt`](profiles/samsung-oneui.txt) |
| **Xiaomi / Redmi / POCO** *(HyperOS / MIUI)* | MSA (MIUI System Ads), GetApps spam, Analytics, Daemon, Joyose battery throttling | [`profiles/xiaomi-hyperos.txt`](profiles/xiaomi-hyperos.txt) |
| **Realme / Oppo / OnePlus** *(ColorOS / OxygenOS)* | HeyTap tracking, Lockscreen Magazine, Theme Store push ads, App Market | [`profiles/realme-oppo-oneplus.txt`](profiles/realme-oppo-oneplus.txt) |
| **Vivo & iQOO** *(Funtouch OS / OriginOS)* | V-Appstore, Jovi assistant wakeups, Vivo Push Service, background telemetry | [`profiles/vivo-iqoo.txt`](profiles/vivo-iqoo.txt) |
| **Infinix, Tecno & Itel** *(Transsion XOS / HiOS)* | Lockscreen Magazine ads, Palm Store, Phone Master fake booster, HiBrowser ads | [`profiles/transsion-xos-hios.txt`](profiles/transsion-xos-hios.txt) |
| **Motorola / Lenovo** *(MyUX / Hello UI)* | Motorola Glance, notification push daemons, preloaded partner adware | [`profiles/motorola-myux.txt`](profiles/motorola-myux.txt) |
| **Universal Google Bloat** | Optional Google Play Games, Google TV/Videos, YouTube Music stubs | [`profiles/universal-google-bloat.txt`](profiles/universal-google-bloat.txt) |

---

## 🛡️ The Non-Negotiable Safety Pledge

Safety is hardcoded into [`AGENTS.md`](AGENTS.md) and [`tools/disable.sh`](tools/disable.sh):

* **Zero Root Required:** Operates strictly within user-space ADB permissions.
* **Banking Apps Never Break:** Google Pay, PhonePe, Paytm, and banking apps remain 100% functional because Android integrity (SafetyNet / Play Integrity) is untouched.
* **Widevine L1 DRM Intact:** Netflix and Prime Video continue streaming in full 1080p/4K.
* **Never Uses `pm uninstall`:** Every package is frozen with `pm disable-user --user 0`. The APK remains safely on the read-only system partition.
* **Hardcoded Hardware Guardrails:** The agent is physically prevented from disabling Phone Calling (`InCallUI`), Emergency SOS, Keyguard, System UI, Cameras, or Biometrics.
* **1-Click Instant Disaster Recovery:** Run `./tools/restore.sh` to re-enable every package in seconds.

---

## 📊 Live Reference Benchmark

Verified on an **Infinix Note 30 5G (`X6711`, Dimensity 6080, 8 GB RAM, Android 14)**:

| Metric | Before Optimization | After Optimization | Live Gain |
| :--- | :--- | :--- | :--- |
| **Available RAM** | 1,916.9 MB (1.87 GB) | **2,614.0 MB (2.55 GB)** | **+697.1 MB (+36.3%) Free RAM** |
| **Free Physical RAM** | 105.6 MB | **198.9 MB** | **+88.3% Direct Headroom** |
| **Swap Headroom** | 2,351.7 MB | **2,940.9 MB** | **+589.2 MB Swap Reclaimed** |
| **Background Bloaters** | 464 active packages | **411 active packages** | **53 Bloatware Daemons Killed** |
| **UI Animation Latency** | 1.0x (Standard) | **0.5x (Snappy)** | **2.0× Faster App Transitions** |
| **Lockscreen Ads** | Active (Magazine) | **Disabled (0 Ads)** | **Clean Lockscreen** |
| **Network Protection** | Disabled (`null`) | `dns.adguard-dns.com` | **System-Wide Ad & Tracker Shield** |

---

## 🚀 Quick Start (Running It Yourself)

### Option A: The AI Agent Flow (Recommended)
Paste this prompt into **Claude Code**, **Codex**, or **Gemini CLI**:

```text
Set up https://github.com/jahangeer-dev7/cleanyourphone for me.

Read AGENTS.md first for safety invariants and strict non-destructive rules.
Then run `python3 tools/phone.py --probe` to audit my connected phone, record a baseline benchmark,
preview the matching profile from profiles/, and ask me for confirmation before disabling anything.
```

### Option B: Manual CLI Execution
If you prefer running the scripts yourself:

```bash
# 1. Clone repository
git clone https://github.com/jahangeer-dev7/cleanyourphone.git
cd cleanyourphone

# 2. Probe device specs & auto-match profile
python3 tools/phone.py --probe

# 3. Record baseline benchmark
python3 tools/bench.py --save backups/baseline.json

# 4. Apply matching brand profile
./tools/disable.sh profiles/samsung-oneui.txt    # Or xiaomi, realme, vivo, transsion...

# 5. Measure improvement
python3 tools/bench.py --compare backups/baseline.json
```

---

## 🔌 Connecting Over Wi-Fi (Wireless ADB)

No USB cable needed on Android 11+:
1. On phone: **Developer options** $\rightarrow$ **Wireless debugging** $\rightarrow$ **Pair device with pairing code**.
2. Run pair:
   ```bash
   python3 tools/phone.py --pair 192.168.1.50:PORT PAIRING_CODE
   ```
3. Connect:
   ```bash
   python3 tools/phone.py --connect 192.168.1.50:PORT
   ```

---

## 🤝 Contributing

We welcome verified community profiles! To contribute a profile for your phone:
1. Fork the repo and create your list in `profiles/<oem>-<os>.txt`.
2. Follow the commenting format (categorized into Ads, Telemetry, Fake Cleaners, Social Bloat).
3. Verify that Calling, Camera, Biometrics, and Play Store remain 100% functional.
4. Submit a Pull Request.

---

## 👤 Author & Credits

* **Creator:** **Jahangeer I** ([@jahangeer-dev7](https://github.com/jahangeer-dev7))
* **Inspiration:** Built as the open-source smartphone counterpart to [`tv-vibehack` / CleanYourTV](https://github.com/Gathin23/cleanyourtv).
* **License:** [MIT License](LICENSE) — free for everyone to use, fork, and build upon.
