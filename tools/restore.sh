#!/usr/bin/env bash
#
# cleanyourphone - 1-Click Package Restore Script
# Restores and re-enables packages disabled by cleanyourphone.
#

set -euo pipefail

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${REPO_DIR}/backups"

SERIAL=""
RESTORE_FILE=""

usage() {
    cat <<EOF
Usage: $0 [OPTIONS] [RESTORE_MANIFEST_OR_PACKAGE]

Options:
  -s, --serial <SERIAL>   Target specific ADB device serial or IP:PORT
  -h, --help              Show this help message

Default: Restores packages from backups/last_disabled.txt or latest backup.
EOF
    exit 0
}

# Parse options
while [[ $# -gt 0 ]]; do
    case "$1" in
        -s|--serial)
            SERIAL="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            if [[ -z "$RESTORE_FILE" ]]; then
                RESTORE_FILE="$1"
                shift
            else
                echo -e "${RED}Unknown option: $1${NC}"
                usage
            fi
            ;;
    esac
done

ADB="adb"
if [[ -n "$SERIAL" ]]; then
    ADB="adb -s $SERIAL"
fi

if ! command -v adb &>/dev/null; then
    echo -e "${RED}Error: 'adb' binary not found in PATH.${NC}"
    exit 1
fi

DEVICE_COUNT=$($ADB devices | grep -v "List of devices" | grep -v "^$" | wc -l || true)
if [[ "$DEVICE_COUNT" -eq 0 ]]; then
    echo -e "${RED}Error: No ADB device connected.${NC}"
    exit 1
fi

DEVICE_MODEL=$($ADB shell getprop ro.product.model | tr -d '\r')
DEVICE_BRAND=$($ADB shell getprop ro.product.brand | tr -d '\r')

# If single package name is passed directly
if [[ -n "$RESTORE_FILE" && ! -f "$RESTORE_FILE" ]]; then
    # Check if user passed a single package name
    if [[ "$RESTORE_FILE" =~ ^[a-zA-Z0-9_.]+$ ]]; then
        PKG="$RESTORE_FILE"
        echo -e "[*] Enabling single package: ${BOLD}$PKG${NC}"
        OUT=$($ADB shell pm enable "$PKG" 2>&1 | tr -d '\r')
        echo -e "[+] Result: $OUT"
        exit 0
    fi
fi

# Locate restore manifest file
if [[ -z "$RESTORE_FILE" ]]; then
    if [[ -f "${BACKUP_DIR}/last_disabled.txt" ]] && [[ -s "${BACKUP_DIR}/last_disabled.txt" ]]; then
        RESTORE_FILE="${BACKUP_DIR}/last_disabled.txt"
    else
        LATEST_BACKUP=$(ls -t "${BACKUP_DIR}"/disabled_*.txt 2>/dev/null | head -n 1 || true)
        if [[ -n "$LATEST_BACKUP" && -s "$LATEST_BACKUP" ]]; then
            RESTORE_FILE="$LATEST_BACKUP"
        fi
    fi
fi

if [[ -z "$RESTORE_FILE" || ! -f "$RESTORE_FILE" ]]; then
    echo -e "${RED}Error: No restore manifest or backup file found in ${BACKUP_DIR}.${NC}"
    echo -e "You can specify a file directly: $0 <path_to_file>"
    exit 1
fi

echo -e "${CYAN}${BOLD}==============================================================${NC}"
echo -e "${CYAN}${BOLD}  CLEANYOURPHONE - 1-CLICK PACKAGE RESTORATION${NC}"
echo -e "${CYAN}${BOLD}==============================================================${NC}"
echo -e "  Target Device : ${BOLD}${DEVICE_BRAND} ${DEVICE_MODEL}${NC} (${SERIAL:-default})"
echo -e "  Manifest File : ${BOLD}${RESTORE_FILE}${NC}"
echo -e "${CYAN}--------------------------------------------------------------${NC}"

# Fetch currently disabled packages
DISABLED_PACKAGES=$($ADB shell pm list packages -d | sed 's/^package://' | tr -d '\r')
INSTALLED_PACKAGES=$($ADB shell pm list packages | sed 's/^package://' | tr -d '\r')

COUNT_RESTORED=0
COUNT_ALREADY=0
COUNT_NOTFOUND=0

while IFS= read -r line || [[ -n "$line" ]]; do
    pkg="$(echo "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    if [[ -z "$pkg" || "$pkg" =~ ^# ]]; then
        continue
    fi
    pkg="$(echo "$pkg" | awk '{print $1}')"

    if ! echo "$INSTALLED_PACKAGES" | grep -qx "$pkg"; then
        echo -e "  ${YELLOW}[NOT FOUND]${NC} $pkg"
        COUNT_NOTFOUND=$((COUNT_NOTFOUND + 1))
        continue
    fi

    if ! echo "$DISABLED_PACKAGES" | grep -qx "$pkg"; then
        echo -e "  ${BLUE}[ALREADY ACTIVE]${NC} $pkg"
        COUNT_ALREADY=$((COUNT_ALREADY + 1))
        continue
    fi

    OUT=$($ADB shell pm enable "$pkg" < /dev/null 2>&1 | tr -d '\r' || true)
    if echo "$OUT" | grep -qi "enabled"; then
        echo -e "  ${GREEN}[RESTORED] ${NC} $pkg"
        COUNT_RESTORED=$((COUNT_RESTORED + 1))
    else
        echo -e "  ${RED}[FAILED]   ${NC} $pkg (${OUT})"
    fi
done < "$RESTORE_FILE"

echo -e "\n${CYAN}==============================================================${NC}"
echo -e "${CYAN}${BOLD}  RESTORATION COMPLETE${NC}"
echo -e "${CYAN}==============================================================${NC}"
echo -e "  Successfully Restored : ${GREEN}${BOLD}${COUNT_RESTORED}${NC}"
echo -e "  Already Active        : ${BLUE}${COUNT_ALREADY}${NC}"
echo -e "  Not Installed         : ${YELLOW}${COUNT_NOTFOUND}${NC}"
echo -e "${CYAN}==============================================================${NC}"
