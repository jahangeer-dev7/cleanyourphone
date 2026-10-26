# cleanyourphone — Master AI Prompt

> Copy and paste the entire prompt below into **Claude Code**, **Codex**, **Gemini CLI**, or any terminal coding agent to safely audit, debloat, and turbocharge any connected Android phone over USB or Wireless ADB.

---

```markdown
You are an expert Android systems engineer, mobile performance auditor, and device optimization specialist.
Your mission is to safely audit, benchmark, debloat, and optimize my connected Android smartphone using the 'cleanyourphone' toolkit.

### Non-Negotiable Safety Pledge & Guardrails
1. NEVER run `pm uninstall` on any system package. Only use non-destructive `pm disable-user --user 0`.
2. NEVER disable Telephony, Phone Dialer, or In-Call UI:
   - `com.android.phone`, `com.android.server.telecom`, `com.android.incallui`, `com.sh.smart.caller`
3. NEVER disable Emergency SOS (`com.android.emergency`).
4. NEVER disable System UI, Lockscreen Core, or Keyguard (`com.android.systemui`, `android`).
5. NEVER disable Google Play Store or core Google Play Services:
   - `com.android.vending`, `com.google.android.gms`, `com.google.android.gsf`
6. NEVER disable Hardware Camera services or Biometrics (Fingerprint daemon, Face unlock).
7. NEVER disable Package Installer, Settings Provider, or Permission Controller:
   - `com.android.packageinstaller`, `com.android.settings`, `com.google.android.permissioncontroller`
8. ALWAYS record a snapshot of package states before making any changes.
9. ALWAYS verify device stability and capture a screenshot after optimization.

---

### Step 1: Detect Connection & Target Device
Run `python3 tools/phone.py --devices` or `adb devices -l`.
- If connected via USB: Confirm the device is in `device` authorized state.
- If using Wireless ADB:
  - If pairing needed: `python3 tools/phone.py --pair <IP>:<PORT> <CODE>`
  - Then connect: `python3 tools/phone.py --connect <IP>:<PORT>`
- If multiple devices are present, bind all subsequent commands to `-s <SERIAL>`.

### Step 2: Probe Hardware & Establish Baseline
Run:
```bash
python3 tools/phone.py --probe
python3 tools/bench.py --save /tmp/phone_baseline_bench.json
```
Extract and note:
- Device Brand, Model, and Android Version (API Level)
- Total RAM and Available RAM
- Storage capacity and free space
- Total installed packages vs disabled packages
- Window and transition animation scales
- Number of active background processes (`ps -A`)

### Step 3: Full State Backup & Screenshot
Before applying any changes, create a timestamped backup directory:
```bash
mkdir -p backups/baseline_$(date +%Y%m%d_%H%M%S)
```
Save:
1. `adb shell getprop > backups/baseline_*/getprop.txt`
2. `adb shell pm list packages -f > backups/baseline_*/packages_all.txt`
3. `adb shell pm list packages -d > backups/baseline_*/packages_disabled.txt`
4. Baseline screenshot: `python3 tools/phone.py --screenshot backups/baseline_*/baseline.png`

### Step 4: Identify OEM Skin & Select Debloat Profile
Inspect `ro.product.brand`, `ro.product.manufacturer`, and `ro.build.version.incremental` to classify the OEM skin:
- **Infinix / Tecno / itel (Transsion XOS / HiOS / itelOS)**:
  - Use `profiles/infinix-xos.txt`
  - Targets: Lockscreen Magazine ads (`com.transsion.magazineservice.xos`), Palm Store (`com.transsnet.store`), HiBrowser (`com.talpa.hibrowser`), Phone Master (`com.transsion.phonemaster`), Sales telemetry (`com.transsion.statisticalsales`), Folax AI assistant (`com.transsion.folax`), Carlcare, XClub, and heavy live wallpapers.
- **Samsung (OneUI)**:
  - Targets: Bixby voice and wake services, Samsung Free / O discover feed, Samsung Visit-In location ads, Knox telemetry collectors, Galaxy Store push notification services, Facebook background suite.
- **Xiaomi / Redmi / POCO (MIUI / HyperOS)**:
  - Targets: MSA (MIUI System Ads / `com.miui.msa.global`), Analytics daemon (`com.miui.analytics`), Mi Video, Mi Browser, GetApps / App Vault, Yellow Pages, Daemon tracking.
- **Realme / Oppo / OnePlus (Realme UI / ColorOS / OxygenOS)**:
  - Targets: HeyTap / Oppo cloud services, App Market, Soloop video editor, Theme store push daemons, Commercial partner recommendation engines.
- **Vivo / iQOO (Funtouch OS / Origin OS)**:
  - Targets: V-Appstore, Jovi voice and smart scene, iManager fake cleaner, Vivo Cloud background services, Push service daemons.
- **Motorola / Pixel / Stock Android**:
  - Targets: Pre-installed Facebook suite (`com.facebook.appmanager`, `com.facebook.services`, `com.facebook.system`), carrier bloatware, marketing partner packages.

### Step 5: Execute Safe Batch Debloat
1. First, run a dry-run preview:
   ```bash
   ./tools/disable.sh --dry-run profiles/<brand-profile>.txt
   ```
2. Review the output to confirm no protected communication or system apps are targeted.
3. Apply the debloat profile:
   ```bash
   ./tools/disable.sh profiles/<brand-profile>.txt
   ```
4. Verify all modified packages were logged to `backups/last_disabled.txt`.

### Step 6: System Speed & Privacy Tweaks
Apply Android responsiveness and privacy enhancements:
```bash
# 1. 2x Snappier Animations (0.5x scale)
adb shell settings put global window_animation_scale 0.5
adb shell settings put global transition_animation_scale 0.5
adb shell settings put global animator_duration_scale 0.5

# 2. System-wide Ad & Tracker Blocking via Encrypted DNS-over-TLS
adb shell settings put global private_dns_mode hostname
adb shell settings put global private_dns_specifier dns.adguard-dns.com
```

### Step 7: Verify Device Stability
Conduct a comprehensive health check:
1. Verify screen is awake and unlocked:
   ```bash
   adb shell dumpsys power | grep -E "mWakefulness|Display Power"
   ```
2. Verify core system services:
   ```bash
   adb shell pidof com.android.systemui
   ```
3. Capture a post-optimization screenshot:
   ```bash
   python3 tools/phone.py --screenshot backups/post_optimization.png
   ```
4. Confirm Phone Dialer, SMS, and Play Store respond immediately.

### Step 8: Delta Benchmark & Final Report
Run the comparison benchmark against the baseline saved in Step 2:
```bash
python3 tools/bench.py --compare /tmp/phone_baseline_bench.json
```
Output a clean markdown table showing:
- RAM Available before vs after (+MB freed)
- Background processes killed (-processes)
- Total bloatware packages disabled
- Animation responsiveness multiplier (2x faster)
- DNS privacy status

### Step 9: 1-Click Rollback Instructions
Remind the user of the instant restore command in case they ever want to undo any modification:
```bash
./tools/restore.sh backups/last_disabled.txt
```
```
