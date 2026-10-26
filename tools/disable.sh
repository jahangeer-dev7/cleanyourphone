#!/usr/bin/env bash
#
# cleanyourphone - Safe batch package debloater
# Uses `pm disable-user --user 0` (100% reversible, non-destructive, zero brick risk)
# Automatically records state before modification for 1-click restoration.
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
DRY_RUN=0
PROFILE_FILE=""

# Protected packages blacklist (NEVER DISABLE THESE)
PROTECTED_PATTERNS=(
    "com.android.phone"
    "com.android.server.telecom"
    "com.android.incallui"
    "com.sh.smart.caller"
    "com.android.emergency"
    "com.android.systemui"
    "com.android.settings"
    "com.android.vending"
    "com.google.android.gms"
    "com.google.android.gsf"
    "com.google.android.packageinstaller"
    "com.android.packageinstaller"
    "com.android.permissioncontroller"
    "com.google.android.permissioncontroller"
    "com.fpsensor"
    "com.transsion.camera"
    "photo.android.hd.camera"
    "android"
)

usage() {
    cat <<EOF
Usage: $0 [OPTIONS] [PROFILE_FILE]

Options:
  -s, --serial <SERIAL>   Target specific ADB device serial or IP:PORT
  -d, --dry-run           Preview packages to be disabled without applying
  -h, --help              Show this help message

Default profile: profiles/infinix-xos.txt
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
        -d|--dry-run)
            DRY_RUN=1
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            if [[ -z "$PROFILE_FILE" ]]; then
                PROFILE_FILE="$1"
                shift
            else
                echo -e "${RED}Unknown option: $1${NC}"
                usage
            fi
            ;;
    esac
done

# Resolve ADB command with serial if provided
ADB="adb"
if [[ -n "$SERIAL" ]]; then
    ADB="adb -s $SERIAL"
fi

# Verify adb is available
if ! command -v adb &>/dev/null; then
    echo -e "${RED}Error: 'adb' binary not found in PATH.${NC}"
    exit 1
fi

# Verify device connectivity
DEVICE_COUNT=$($ADB devices | grep -v "List of devices" | grep -v "^$" | wc -l || true)
if [[ "$DEVICE_COUNT" -eq 0 ]]; then
    echo -e "${RED}Error: No ADB device connected.${NC}"
    exit 1
fi

DEVICE_MODEL=$($ADB shell getprop ro.product.model | tr -d '\r')
DEVICE_BRAND=$($ADB shell getprop ro.product.brand | tr -d '\r')

# Default profile if not provided
if [[ -z "$PROFILE_FILE" ]]; then
    PROFILE_FILE="${REPO_DIR}/profiles/infinix-xos.txt"
fi

if [[ ! -f "$PROFILE_FILE" ]]; then
    echo -e "${RED}Error: Profile file not found: ${PROFILE_FILE}${NC}"
    exit 1
fi

mkdir -p "$BACKUP_DIR"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_STATE_FILE="${BACKUP_DIR}/state_before_${TIMESTAMP}.txt"
AUDIT_LOG_FILE="${BACKUP_DIR}/disabled_${TIMESTAMP}.txt"
LAST_DISABLED_LINK="${BACKUP_DIR}/last_disabled.txt"

echo -e "${CYAN}${BOLD}==============================================================${NC}"
echo -e "${CYAN}${BOLD}  CLEANYOURPHONE - SAFE BATCH DEBLOATER${NC}"
echo -e "${CYAN}${BOLD}==============================================================${NC}"
echo -e "  Target Device : ${BOLD}${DEVICE_BRAND} ${DEVICE_MODEL}${NC} (${SERIAL:-default})"
echo -e "  Profile       : ${BOLD}${PROFILE_FILE}${NC}"
echo -e "  Dry Run Mode  : $([[ $DRY_RUN -eq 1 ]] && echo -e "${YELLOW}ENABLED (No changes will be made)${NC}" || echo "DISABLED")"
echo -e "${CYAN}--------------------------------------------------------------${NC}"

# Record state before modification
echo -e "[*] Recording baseline package states before modification..."
$ADB shell pm list packages -d > "${BACKUP_STATE_FILE}" || true
echo -e "[+] Saved baseline disabled packages to: ${BACKUP_STATE_FILE}"

# Fetch installed packages for quick matching
echo -e "[*] Scanning installed packages on device..."
INSTALLED_PACKAGES=$($ADB shell pm list packages | sed 's/^package://' | tr -d '\r')
DISABLED_PACKAGES=$($ADB shell pm list packages -d | sed 's/^package://' | tr -d '\r')

is_protected() {
    local target="$1"
    for prot in "${PROTECTED_PATTERNS[@]}"; do
        if [[ "$target" == "$prot"* ]]; then
            return 0
        fi
    done
    return 1
}

COUNT_TOTAL=0
COUNT_DISABLED=0
COUNT_ALREADY=0
COUNT_NOTFOUND=0
COUNT_PROTECTED=0

# Clean audit log file
> "${AUDIT_LOG_FILE}"

echo -e "\n[*] Processing package manifests..."
while IFS= read -r line || [[ -n "$line" ]]; do
    # Trim whitespace
    pkg="$(echo "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    
    # Skip empty lines and comments
    if [[ -z "$pkg" || "$pkg" =~ ^# ]]; then
        continue
    fi
    
    # If line contains inline comment, strip it
    pkg="$(echo "$pkg" | awk '{print $1}')"
    COUNT_TOTAL=$((COUNT_TOTAL + 1))

    # Safety check
    if is_protected "$pkg"; then
        echo -e "  ${RED}[PROTECTED]${NC} Skipping critical system package: ${BOLD}$pkg${NC}"
        COUNT_PROTECTED=$((COUNT_PROTECTED + 1))
        continue
    fi

    # Check if installed
    if ! echo "$INSTALLED_PACKAGES" | grep -qx "$pkg"; then
        echo -e "  ${YELLOW}[NOT FOUND]${NC} $pkg"
        COUNT_NOTFOUND=$((COUNT_NOTFOUND + 1))
        continue
    fi

    # Check if already disabled
    if echo "$DISABLED_PACKAGES" | grep -qx "$pkg"; then
        echo -e "  ${BLUE}[ALREADY]  ${NC} $pkg"
        COUNT_ALREADY=$((COUNT_ALREADY + 1))
        continue
    fi

    if [[ $DRY_RUN -eq 1 ]]; then
        echo -e "  ${GREEN}[WOULD DIS]${NC} $pkg"
        COUNT_DISABLED=$((COUNT_DISABLED + 1))
        echo "$pkg" >> "${AUDIT_LOG_FILE}"
    else
        # Execute safe disable
        OUT=$($ADB shell pm disable-user --user 0 "$pkg" < /dev/null 2>&1 | tr -d '\r' || true)
        if echo "$OUT" | grep -qi "disabled"; then
            echo -e "  ${GREEN}[DISABLED] ${NC} $pkg"
            COUNT_DISABLED=$((COUNT_DISABLED + 1))
            echo "$pkg" >> "${AUDIT_LOG_FILE}"
        else
            echo -e "  ${RED}[FAILED]   ${NC} $pkg (${OUT})"
        fi
    fi
done < "$PROFILE_FILE"

# Create pointer to last disabled session
cp "${AUDIT_LOG_FILE}" "${LAST_DISABLED_LINK}"

echo -e "\n${CYAN}==============================================================${NC}"
echo -e "${CYAN}${BOLD}  BATCH DEBLOAT SUMMARY${NC}"
echo -e "${CYAN}==============================================================${NC}"
echo -e "  Total Audited    : ${BOLD}${COUNT_TOTAL}${NC}"
echo -e "  Newly Disabled   : ${GREEN}${BOLD}${COUNT_DISABLED}${NC}"
echo -e "  Already Disabled : ${BLUE}${COUNT_ALREADY}${NC}"
echo -e "  Not Installed    : ${YELLOW}${COUNT_NOTFOUND}${NC}"
echo -e "  Protected Skips  : ${RED}${COUNT_PROTECTED}${NC}"
echo -e "${CYAN}--------------------------------------------------------------${NC}"
echo -e "  Session Log      : ${AUDIT_LOG_FILE}"
echo -e "  1-Click Restore  : ${BOLD}./tools/restore.sh ${LAST_DISABLED_LINK}${NC}"
echo -e "${CYAN}==============================================================${NC}"
