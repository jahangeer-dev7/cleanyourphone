#!/usr/bin/env python3
"""
cleanyourphone - Comprehensive benchmarking tool for Android devices.
Measures RAM, storage, process count, animation scales, and system responsiveness.
Supports baseline saving and delta comparison (--compare).
"""

import sys
import os
import argparse
import subprocess
import shutil
import json
import time
import re
from typing import Dict, Any, Optional, List


def get_adb_binary() -> str:
    bin_path = shutil.which("adb")
    if bin_path:
        return bin_path
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, ".local", "bin", "adb"),
        os.path.join(home, ".local", "share", "android-sdk", "platform-tools", "adb"),
        "/usr/bin/adb",
    ]
    for c in candidates:
        if os.path.exists(c) and os.access(c, os.X_OK):
            return c
    return "adb"


def adb_shell(cmd: str, serial: Optional[str] = None) -> str:
    adb_bin = get_adb_binary()
    full_cmd = [adb_bin]
    if serial:
        full_cmd.extend(["-s", serial])
    full_cmd.extend(["shell", cmd])
    try:
        res = subprocess.run(full_cmd, capture_output=True, text=True, timeout=30)
        return res.stdout.strip()
    except Exception as e:
        sys.stderr.write(f"Error executing adb shell: {e}\n")
        return ""


def parse_meminfo(serial: Optional[str] = None) -> Dict[str, Any]:
    raw = adb_shell("cat /proc/meminfo", serial)
    mem: Dict[str, int] = {}
    for line in raw.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            m = re.search(r"(\d+)", v)
            if m:
                mem[k.strip()] = int(m.group(1))

    total = mem.get("MemTotal", 0)
    free = mem.get("MemFree", 0)
    avail = mem.get("MemAvailable", 0)
    cached = mem.get("Cached", 0)
    buffers = mem.get("Buffers", 0)
    swap_total = mem.get("SwapTotal", 0)
    swap_free = mem.get("SwapFree", 0)
    used = total - avail if avail > 0 else total - free

    return {
        "mem_total_kb": total,
        "mem_free_kb": free,
        "mem_available_kb": avail,
        "mem_cached_kb": cached,
        "mem_buffers_kb": buffers,
        "mem_used_kb": used,
        "swap_total_kb": swap_total,
        "swap_free_kb": swap_free,
        "total_mb": round(total / 1024, 1),
        "available_mb": round(avail / 1024, 1),
        "free_mb": round(free / 1024, 1),
        "cached_mb": round(cached / 1024, 1),
        "used_mb": round(used / 1024, 1),
        "avail_percent": round((avail / total * 100), 1) if total > 0 else 0,
    }


def parse_storage(serial: Optional[str] = None) -> Dict[str, Any]:
    raw = adb_shell("df -k /data", serial)
    lines = raw.strip().splitlines()
    if len(lines) >= 2:
        parts = lines[1].split()
        if len(parts) >= 5:
            try:
                total_kb = int(parts[1])
                used_kb = int(parts[2])
                avail_kb = int(parts[3])
                pct_str = parts[4].replace("%", "")
                return {
                    "filesystem": parts[0],
                    "total_gb": round(total_kb / (1024 * 1024), 2),
                    "used_gb": round(used_kb / (1024 * 1024), 2),
                    "avail_gb": round(avail_kb / (1024 * 1024), 2),
                    "used_percent": int(pct_str) if pct_str.isdigit() else 0,
                }
            except ValueError:
                pass
    return {"total_gb": 0, "used_gb": 0, "avail_gb": 0, "used_percent": 0}


def parse_processes(serial: Optional[str] = None) -> Dict[str, Any]:
    raw = adb_shell("ps -A", serial)
    lines = [l for l in raw.splitlines() if l.strip()]
    header = lines[0] if lines else ""
    proc_count = max(0, len(lines) - 1)
    return {
        "total_processes": proc_count,
    }


def parse_animations(serial: Optional[str] = None) -> Dict[str, Any]:
    w = adb_shell("settings get global window_animation_scale", serial)
    t = adb_shell("settings get global transition_animation_scale", serial)
    a = adb_shell("settings get global animator_duration_scale", serial)
    return {
        "window_animation_scale": float(w) if w and w.replace(".", "", 1).isdigit() else 1.0,
        "transition_animation_scale": float(t) if t and t.replace(".", "", 1).isdigit() else 1.0,
        "animator_duration_scale": float(a) if a and a.replace(".", "", 1).isdigit() else 1.0,
    }


def parse_battery(serial: Optional[str] = None) -> Dict[str, Any]:
    raw = adb_shell("dumpsys battery", serial)
    level = 0
    temp = 0.0
    status = "Unknown"
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("level:"):
            try:
                level = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("temperature:"):
            try:
                temp = float(line.split(":", 1)[1].strip()) / 10.0
            except ValueError:
                pass
        elif line.startswith("status:"):
            status_code = line.split(":", 1)[1].strip()
            # 2 = charging, 3 = discharging, 5 = full
            status = {"2": "Charging", "3": "Discharging", "5": "Full"}.get(status_code, status_code)
    return {
        "level_percent": level,
        "temperature_c": temp,
        "status": status,
    }


def parse_packages(serial: Optional[str] = None) -> Dict[str, Any]:
    all_raw = adb_shell("pm list packages | wc -l", serial)
    dis_raw = adb_shell("pm list packages -d | wc -l", serial)
    tot = int(all_raw) if all_raw.isdigit() else 0
    dis = int(dis_raw) if dis_raw.isdigit() else 0
    return {
        "total_packages": tot,
        "disabled_packages": dis,
        "active_packages": tot - dis,
    }


def get_top_memory_consumers(serial: Optional[str] = None, top_n: int = 5) -> List[Dict[str, Any]]:
    raw = adb_shell("dumpsys meminfo | head -n 35", serial)
    consumers = []
    capture = False
    for line in raw.splitlines():
        if "Total PSS by process:" in line:
            capture = True
            continue
        if "Total PSS by OOM adjustment:" in line:
            break
        if capture:
            line = line.strip()
            # Pattern: 123,456K: com.example.app (pid 1234)
            m = re.match(r"^([\d,]+)K:\s+(\S+)", line)
            if m:
                pss_kb = int(m.group(1).replace(",", ""))
                pkg = m.group(2)
                consumers.append({
                    "package": pkg,
                    "pss_mb": round(pss_kb / 1024, 1),
                })
                if len(consumers) >= top_n:
                    break
    return consumers


def capture_benchmark(serial: Optional[str] = None) -> Dict[str, Any]:
    model = adb_shell("getprop ro.product.model", serial)
    brand = adb_shell("getprop ro.product.brand", serial)
    android = adb_shell("getprop ro.build.version.release", serial)
    api = adb_shell("getprop ro.build.version.sdk", serial)

    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "device": {
            "brand": brand,
            "model": model,
            "android_version": android,
            "api_level": api,
            "serial": serial or "default",
        },
        "ram": parse_meminfo(serial),
        "storage": parse_storage(serial),
        "processes": parse_processes(serial),
        "animations": parse_animations(serial),
        "battery": parse_battery(serial),
        "packages": parse_packages(serial),
        "top_consumers": get_top_memory_consumers(serial),
    }


def print_benchmark_table(data: Dict[str, Any]) -> None:
    bar = "=" * 65
    sub = "-" * 65
    dev = data.get("device", {})
    ram = data.get("ram", {})
    stg = data.get("storage", {})
    proc = data.get("processes", {})
    anim = data.get("animations", {})
    bat = data.get("battery", {})
    pkgs = data.get("packages", {})

    print(bar)
    print(f"  CLEANYOURPHONE - SYSTEM BENCHMARK REPORT")
    print(bar)
    print(f"  Device           : {dev.get('brand')} {dev.get('model')} (Android {dev.get('android_version')})")
    print(f"  Timestamp        : {data.get('timestamp')}")
    print(sub)
    print(f"  RAM Total        : {ram.get('total_mb')} MB ({round(ram.get('total_mb', 0)/1024, 2)} GB)")
    print(f"  RAM Available    : {ram.get('available_mb')} MB ({ram.get('avail_percent')}% free headroom)")
    print(f"  RAM Used         : {ram.get('used_mb')} MB (Buffers/Cache: {ram.get('cached_mb')} MB)")
    print(f"  Active Processes : {proc.get('total_processes')} processes running")
    print(f"  Internal Storage : {stg.get('avail_gb')} GB free / {stg.get('total_gb')} GB ({stg.get('used_percent')}% used)")
    print(f"  Animation Scales : Win: {anim.get('window_animation_scale')}x | Trans: {anim.get('transition_animation_scale')}x | Dur: {anim.get('animator_duration_scale')}x")
    print(f"  Package Health   : {pkgs.get('total_packages')} total | {pkgs.get('active_packages')} active | {pkgs.get('disabled_packages')} disabled")
    print(f"  Battery          : {bat.get('level_percent')}% ({bat.get('temperature_c')}°C, {bat.get('status')})")

    top = data.get("top_consumers", [])
    if top:
        print(sub)
        print("  Top Memory Consumers:")
        for idx, item in enumerate(top, 1):
            print(f"    {idx}. {item['package']:<40} {item['pss_mb']:>7.1f} MB PSS")
    print(bar)


def print_comparison_table(before: Dict[str, Any], after: Dict[str, Any]) -> None:
    bar = "=" * 70
    sub = "-" * 70

    b_dev = before.get("device", {})
    a_dev = after.get("device", {})
    b_ram = before.get("ram", {})
    a_ram = after.get("ram", {})
    b_proc = before.get("processes", {})
    a_proc = after.get("processes", {})
    b_pkgs = before.get("packages", {})
    a_pkgs = after.get("packages", {})
    b_anim = before.get("animations", {})
    a_anim = after.get("animations", {})

    ram_gain_mb = round(a_ram.get("available_mb", 0) - b_ram.get("available_mb", 0), 1)
    ram_gain_sign = "+" if ram_gain_mb >= 0 else ""
    proc_delta = a_proc.get("total_processes", 0) - b_proc.get("total_processes", 0)
    proc_sign = "+" if proc_delta >= 0 else ""
    dis_delta = a_pkgs.get("disabled_packages", 0) - b_pkgs.get("disabled_packages", 0)

    print(bar)
    print(f"  CLEANYOURPHONE - OPTIMIZATION DELTA BENCHMARK")
    print(bar)
    print(f"  Target Device    : {a_dev.get('brand')} {a_dev.get('model')} (Android {a_dev.get('android_version')})")
    print(sub)
    print(f"  {'Metric':<26} | {'Baseline':<12} | {'Optimized':<12} | {'Delta':<12}")
    print(sub)
    print(f"  {'RAM Available (MB)':<26} | {b_ram.get('available_mb', 0):<12.1f} | {a_ram.get('available_mb', 0):<12.1f} | {ram_gain_sign}{ram_gain_mb} MB")
    print(f"  {'RAM Free (MB)':<26} | {b_ram.get('free_mb', 0):<12.1f} | {a_ram.get('free_mb', 0):<12.1f} | {a_ram.get('free_mb', 0) - b_ram.get('free_mb', 0):+0.1f} MB")
    print(f"  {'Running Processes':<26} | {b_proc.get('total_processes', 0):<12} | {a_proc.get('total_processes', 0):<12} | {proc_sign}{proc_delta}")
    print(f"  {'Disabled Packages':<26} | {b_pkgs.get('disabled_packages', 0):<12} | {a_pkgs.get('disabled_packages', 0):<12} | +{dis_delta}")
    print(f"  {'Active Packages':<26} | {b_pkgs.get('active_packages', 0):<12} | {a_pkgs.get('active_packages', 0):<12} | -{dis_delta}")
    print(f"  {'Window Anim Scale':<26} | {b_anim.get('window_animation_scale', 1.0):<12.1f} | {a_anim.get('window_animation_scale', 1.0):<12.1f} | -0.5x (2x speed)")
    print(f"  {'Transition Scale':<26} | {b_anim.get('transition_animation_scale', 1.0):<12.1f} | {a_anim.get('transition_animation_scale', 1.0):<12.1f} | -0.5x (2x speed)")
    print(f"  {'Animator Duration':<26} | {b_anim.get('animator_duration_scale', 1.0):<12.1f} | {a_anim.get('animator_duration_scale', 1.0):<12.1f} | -0.5x (2x speed)")
    print(bar)


def main():
    parser = argparse.ArgumentParser(
        description="cleanyourphone benchmark suite - Measure and compare Android performance.",
    )
    parser.add_argument("-s", "--serial", help="Specific device serial or IP:PORT")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--save", metavar="FILE", help="Save captured benchmark to JSON file")
    parser.add_argument("--compare", metavar="FILE", help="Compare current device against a baseline JSON file")

    args = parser.parse_args()

    current_data = capture_benchmark(args.serial)

    if args.save:
        with open(args.save, "w", encoding="utf-8") as f:
            json.dump(current_data, f, indent=2)
        print(f"[+] Benchmark saved to {args.save}")

    if args.compare:
        if not os.path.exists(args.compare):
            sys.stderr.write(f"[-] Baseline comparison file not found: {args.compare}\n")
            sys.exit(1)
        with open(args.compare, "r", encoding="utf-8") as f:
            baseline_data = json.load(f)

        if args.json:
            comparison = {
                "baseline": baseline_data,
                "current": current_data,
            }
            print(json.dumps(comparison, indent=2))
        else:
            print_comparison_table(baseline_data, current_data)
        return

    if args.json:
        print(json.dumps(current_data, indent=2))
    else:
        print_benchmark_table(current_data)


if __name__ == "__main__":
    main()
