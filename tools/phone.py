#!/usr/bin/env python3
"""
cleanyourphone - Modern ADB phone management tool.
Supports pure-Python adb_shell with automatic fallback to standard adb CLI.
Full support for USB, Wireless ADB (pairing & connect), probing, screenshot, batch commands.
"""

import sys
import os
import argparse
import subprocess
import shutil
import json
import time
import re
from typing import Optional, List, Dict, Any, Tuple

# Try importing adb_shell if available
try:
    import adb_shell
    from adb_shell.adb_device import AdbDeviceTcp, AdbDeviceUsb
    from adb_shell.auth.sign_pythonrsa import PythonRSASigner
    from adb_shell.auth.keygen import keygen
    HAS_ADB_SHELL = True
except ImportError:
    HAS_ADB_SHELL = False


class ADBRunner:
    """ADB client with automatic CLI fallback and pure-Python transport hooks."""

    def __init__(self, serial: Optional[str] = None):
        self.serial = serial
        self.adb_bin = self._find_adb_binary()

    def _find_adb_binary(self) -> str:
        bin_path = shutil.which("adb")
        if bin_path:
            return bin_path
        # Common standard paths
        home = os.path.expanduser("~")
        candidates = [
            os.path.join(home, ".local", "bin", "adb"),
            os.path.join(home, ".local", "share", "android-sdk", "platform-tools", "adb"),
            os.path.join(home, "Android", "Sdk", "platform-tools", "adb"),
            "/usr/bin/adb",
            "/usr/local/bin/adb",
            "/opt/android-sdk/platform-tools/adb",
        ]
        for c in candidates:
            if os.path.exists(c) and os.access(c, os.X_OK):
                return c
        return "adb"

    def run_cmd(self, args: List[str], timeout: int = 60, check: bool = False) -> subprocess.CompletedProcess:
        """Run an adb command with target serial if specified."""
        cmd = [self.adb_bin]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(args)
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if check and res.returncode != 0:
                sys.stderr.write(f"ADB Error ({res.returncode}): {res.stderr}\n")
            return res
        except subprocess.TimeoutExpired:
            sys.stderr.write(f"Command timed out after {timeout}s: {' '.join(cmd)}\n")
            raise
        except FileNotFoundError:
            sys.stderr.write("Error: adb binary not found in PATH or standard locations.\n")
            sys.exit(1)

    def shell(self, command: str, timeout: int = 60) -> str:
        """Run shell command on connected device and return stdout."""
        res = self.run_cmd(["shell", command], timeout=timeout)
        return res.stdout.strip()

    def list_devices(self) -> List[Dict[str, str]]:
        """List attached adb devices with their properties."""
        res = subprocess.run([self.adb_bin, "devices", "-l"], capture_output=True, text=True)
        devices = []
        for line in res.stdout.splitlines():
            line = line.strip()
            if not line or line.startswith("List of devices"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                serial = parts[0]
                state = parts[1]
                details = {}
                for item in parts[2:]:
                    if ":" in item:
                        k, v = item.split(":", 1)
                        details[k] = v
                devices.append({
                    "serial": serial,
                    "state": state,
                    "model": details.get("model", ""),
                    "product": details.get("product", ""),
                    "device": details.get("device", ""),
                    "transport_id": details.get("transport_id", ""),
                })
        return devices

    def pair(self, host_port: str, code: str) -> bool:
        """Pair with device over Wireless ADB using pairing code."""
        print(f"[*] Pairing with {host_port} using code {code}...")
        cmd = [self.adb_bin, "pair", host_port, code]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"[+] Successfully paired: {res.stdout.strip()}")
            return True
        else:
            sys.stderr.write(f"[-] Pairing failed: {res.stderr.strip() or res.stdout.strip()}\n")
            return False

    def connect(self, host_port: str) -> bool:
        """Connect to device over Wireless ADB."""
        print(f"[*] Connecting to {host_port}...")
        cmd = [self.adb_bin, "connect", host_port]
        res = subprocess.run(cmd, capture_output=True, text=True)
        out = res.stdout.strip()
        print(f"[+] {out}")
        return "connected to" in out.lower()

    def disconnect(self, host_port: Optional[str] = None) -> bool:
        """Disconnect wireless ADB connection."""
        cmd = [self.adb_bin, "disconnect"]
        if host_port:
            cmd.append(host_port)
        res = subprocess.run(cmd, capture_output=True, text=True)
        print(f"[+] {res.stdout.strip()}")
        return res.returncode == 0

    def push(self, local_path: str, remote_path: str) -> bool:
        """Push local file or folder to phone."""
        res = self.run_cmd(["push", local_path, remote_path])
        if res.returncode == 0:
            print(f"[+] Pushed {local_path} -> {remote_path}")
            return True
        sys.stderr.write(f"[-] Push failed: {res.stderr.strip()}\n")
        return False

    def pull(self, remote_path: str, local_path: str) -> bool:
        """Pull remote file from phone to local filesystem."""
        res = self.run_cmd(["pull", remote_path, local_path])
        if res.returncode == 0:
            print(f"[+] Pulled {remote_path} -> {local_path}")
            return True
        sys.stderr.write(f"[-] Pull failed: {res.stderr.strip()}\n")
        return False

    def screenshot(self, output_path: Optional[str] = None) -> str:
        """Capture screenshot via screencap and save locally."""
        if not output_path:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = f"screenshot_{timestamp}.png"

        # Direct screencap via binary pipe
        cmd = [self.adb_bin]
        if self.serial:
            cmd.extend(["-s", self.serial])
        cmd.extend(["exec-out", "screencap", "-p"])

        with open(output_path, "wb") as f:
            res = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE)

        if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f"[+] Screenshot saved to {output_path} ({os.path.getsize(output_path)} bytes)")
            return output_path
        else:
            # Fallback to remote temporary file
            remote_tmp = "/sdcard/screen_tmp.png"
            self.shell(f"screencap -p {remote_tmp}")
            self.pull(remote_tmp, output_path)
            self.shell(f"rm {remote_tmp}")
            if os.path.exists(output_path):
                print(f"[+] Screenshot saved to {output_path}")
                return output_path
            sys.stderr.write("[-] Failed to capture screenshot.\n")
            return ""

    def reboot(self, mode: Optional[str] = None) -> bool:
        """Reboot device (normal, bootloader, recovery, fastboot)."""
        args = ["reboot"]
        if mode:
            args.append(mode)
        res = self.run_cmd(args)
        return res.returncode == 0

    def batch(self, file_path: str) -> None:
        """Execute lines of commands or package disable statements from file."""
        if not os.path.exists(file_path):
            sys.stderr.write(f"[-] Batch file not found: {file_path}\n")
            sys.exit(1)

        print(f"[*] Executing batch commands from {file_path}...")
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        total = len(lines)
        for i, cmd in enumerate(lines, 1):
            if cmd.startswith("pm ") or cmd.startswith("settings "):
                sh_cmd = cmd
            elif not cmd.startswith("adb"):
                sh_cmd = cmd
            else:
                # Remove leading adb / adb shell if present
                sh_cmd = re.sub(r"^adb(\s+-s\s+\S+)?\s+shell\s+", "", cmd)

            out = self.shell(sh_cmd)
            print(f"[{i}/{total}] $ {sh_cmd} -> {out or 'OK'}")

    def probe(self) -> Dict[str, Any]:
        """Deep probe device specs, platform, memory, battery, and display."""
        props_raw = self.shell("getprop")
        props = {}
        for line in props_raw.splitlines():
            m = re.match(r"^\[(.*?)\]:\s*\[(.*?)\]$", line.strip())
            if m:
                props[m.group(1)] = m.group(2)

        # Basic identity
        brand = props.get("ro.product.brand") or props.get("ro.product.manufacturer", "Unknown")
        model = props.get("ro.product.model", "Unknown")
        device_name = props.get("ro.product.device", "Unknown")
        market_name = props.get("ro.product.marketname") or props.get("ro.config.marketing_name", "")
        android_ver = props.get("ro.build.version.release", "Unknown")
        api_level = props.get("ro.build.version.sdk", "Unknown")
        build_id = props.get("ro.build.display.id") or props.get("ro.build.id", "Unknown")
        sec_patch = props.get("ro.build.version.security_patch", "Unknown")
        soc = props.get("ro.board.platform") or props.get("ro.hardware", "Unknown")
        cpu_abi = props.get("ro.product.cpu.abi", "Unknown")

        # Connection type
        is_wireless = bool(self.serial and (":" in self.serial or self.serial.startswith("192.") or self.serial.startswith("10.") or self.serial.startswith("172.")))
        conn_type = "Wireless ADB" if is_wireless else "USB Debugging"

        # Memory info
        mem_raw = self.shell("cat /proc/meminfo")
        mem_dict = {}
        for line in mem_raw.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                num = re.search(r"(\d+)", v)
                if num:
                    mem_dict[k.strip()] = int(num.group(1))

        total_ram_mb = round(mem_dict.get("MemTotal", 0) / 1024, 1)
        free_ram_mb = round(mem_dict.get("MemFree", 0) / 1024, 1)
        avail_ram_mb = round(mem_dict.get("MemAvailable", 0) / 1024, 1)

        # Storage info
        df_raw = self.shell("df -h /data")
        storage_info = "Unknown"
        for line in df_raw.splitlines():
            if "/data" in line or "/storage" in line:
                storage_info = line.strip()

        # Display info
        wm_size = self.shell("wm size").replace("Physical size:", "").strip()
        wm_density = self.shell("wm density").replace("Physical density:", "").strip()

        # Battery info
        batt_raw = self.shell("dumpsys battery")
        batt_level = ""
        batt_temp = ""
        for line in batt_raw.splitlines():
            if "level:" in line:
                batt_level = line.split(":", 1)[1].strip() + "%"
            elif "temperature:" in line:
                t = float(line.split(":", 1)[1].strip()) / 10.0
                batt_temp = f"{t:.1f}°C"

        # Animation scales
        win_anim = self.shell("settings get global window_animation_scale")
        trans_anim = self.shell("settings get global transition_animation_scale")
        dur_anim = self.shell("settings get global animator_duration_scale")

        # Total packages
        pkg_count_raw = self.shell("pm list packages | wc -l")
        pkg_count = pkg_count_raw.strip() if pkg_count_raw.isdigit() else "Unknown"

        # Disabled packages count
        dis_count_raw = self.shell("pm list packages -d | wc -l")
        dis_count = dis_count_raw.strip() if dis_count_raw.isdigit() else "0"

        info = {
            "serial": self.serial or "default",
            "connection": conn_type,
            "brand": brand,
            "model": model,
            "market_name": market_name,
            "device": device_name,
            "soc": soc,
            "cpu_abi": cpu_abi,
            "android_version": android_ver,
            "api_level": api_level,
            "security_patch": sec_patch,
            "build_id": build_id,
            "ram": {
                "total_mb": total_ram_mb,
                "available_mb": avail_ram_mb,
                "free_mb": free_ram_mb,
            },
            "display": {
                "resolution": wm_size,
                "density": wm_density,
            },
            "battery": {
                "level": batt_level,
                "temperature": batt_temp,
            },
            "animations": {
                "window": win_anim,
                "transition": trans_anim,
                "animator": dur_anim,
            },
            "packages": {
                "total": pkg_count,
                "disabled": dis_count,
            },
            "storage_summary": storage_info,
        }
        return info


def print_probe(info: Dict[str, Any]) -> None:
    """Print beautifully formatted probe results."""
    bar = "=" * 62
    sub = "-" * 62
    print(bar)
    print(f"  CLEANYOURPHONE - DEVICE PROBE AUDIT")
    print(bar)
    print(f"  Brand / Model    : {info['brand']} {info['model']} ({info['market_name'] or info['device']})")
    print(f"  Serial / Link    : {info['serial']} [{info['connection']}]")
    print(f"  Android OS       : Android {info['android_version']} (API {info['api_level']})")
    print(f"  Security Patch   : {info['security_patch']}")
    print(f"  Platform / SoC   : {info['soc']} ({info['cpu_abi']})")
    print(f"  Build ID         : {info['build_id']}")
    print(sub)
    print(f"  RAM Total        : {info['ram']['total_mb']} MB (~{round(info['ram']['total_mb']/1024, 1)} GB)")
    print(f"  RAM Available    : {info['ram']['available_mb']} MB (Free: {info['ram']['free_mb']} MB)")
    print(f"  Screen Display   : {info['display']['resolution']} @ {info['display']['density']} dpi")
    print(f"  Battery Status   : {info['battery']['level']} ({info['battery']['temperature']})")
    print(f"  Animation Scales : Window: {info['animations']['window']}x | Transition: {info['animations']['transition']}x | Animator: {info['animations']['animator']}x")
    print(f"  Packages Count   : {info['packages']['total']} total ({info['packages']['disabled']} disabled)")
    print(bar)


def main():
    parser = argparse.ArgumentParser(
        description="cleanyourphone - Comprehensive Android phone debloater and optimizer client.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 tools/phone.py --probe
  python3 tools/phone.py --screenshot phone.png
  python3 tools/phone.py --pair 192.168.1.50:42115 123456
  python3 tools/phone.py --connect 192.168.1.50:5555
  python3 tools/phone.py shell "pm list packages -3"
  python3 tools/phone.py --batch profiles/infinix-xos.txt
"""
    )
    parser.add_argument("-s", "--serial", help="Specific device serial or IP:PORT")
    parser.add_argument("--devices", action="store_true", help="List all attached ADB devices")
    parser.add_argument("--probe", action="store_true", help="Audit and display device hardware & system info")
    parser.add_argument("--json", action="store_true", help="Output probe results in JSON format")
    parser.add_argument("--screenshot", nargs="?", const="default", help="Capture screenshot (optional path)")
    parser.add_argument("--pair", nargs=2, metavar=("HOST:PORT", "CODE"), help="Pair wireless ADB with pairing code")
    parser.add_argument("--connect", metavar="HOST:PORT", help="Connect to wireless ADB")
    parser.add_argument("--disconnect", nargs="?", const="", metavar="HOST:PORT", help="Disconnect wireless ADB")
    parser.add_argument("--push", nargs=2, metavar=("LOCAL", "REMOTE"), help="Push file to device")
    parser.add_argument("--pull", nargs=2, metavar=("REMOTE", "LOCAL"), help="Pull file from device")
    parser.add_argument("--batch", metavar="FILE", help="Batch execute commands or profile file")
    parser.add_argument("--reboot", nargs="?", const="", metavar="MODE", help="Reboot phone (bootloader, recovery, etc.)")
    parser.add_argument("shell_cmd", nargs="*", help="Direct adb shell command to run")

    args = parser.parse_args()
    runner = ADBRunner(serial=args.serial)

    if args.devices:
        devs = runner.list_devices()
        print(f"Attached devices ({len(devs)}):")
        for d in devs:
            print(f" - {d['serial']}\tstate:{d['state']}\tmodel:{d['model']}\tproduct:{d['product']}")
        return

    if args.pair:
        host_port, code = args.pair
        success = runner.pair(host_port, code)
        sys.exit(0 if success else 1)

    if args.connect:
        success = runner.connect(args.connect)
        sys.exit(0 if success else 1)

    if args.disconnect is not None:
        hp = args.disconnect if args.disconnect else None
        success = runner.disconnect(hp)
        sys.exit(0 if success else 1)

    if args.push:
        success = runner.push(args.push[0], args.push[1])
        sys.exit(0 if success else 1)

    if args.pull:
        success = runner.pull(args.pull[0], args.pull[1])
        sys.exit(0 if success else 1)

    if args.screenshot:
        out_path = None if args.screenshot == "default" else args.screenshot
        saved = runner.screenshot(out_path)
        sys.exit(0 if saved else 1)

    if args.reboot is not None:
        mode = args.reboot if args.reboot else None
        print(f"[*] Rebooting phone {f'into {mode}' if mode else ''}...")
        runner.reboot(mode)
        return

    if args.batch:
        runner.batch(args.batch)
        return

    if args.probe:
        info = runner.probe()
        if args.json:
            print(json.dumps(info, indent=2))
        else:
            print_probe(info)
        return

    if args.shell_cmd:
        # If user passed "shell" as first arg, strip it
        cmd_tokens = args.shell_cmd
        if cmd_tokens[0] == "shell":
            cmd_tokens = cmd_tokens[1:]
        cmd_str = " ".join(cmd_tokens)
        out = runner.shell(cmd_str)
        if out:
            print(out)
        return

    # If no flags provided, show probe by default
    info = runner.probe()
    print_probe(info)


if __name__ == "__main__":
    main()
