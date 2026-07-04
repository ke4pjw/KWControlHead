#!/usr/bin/env bash
# detect_p2.sh — Detect Propeller 2 COM port (FTDI VID_0403 PID_6001)
#
# Usage:
#   source detect_p2.sh   # sets P2_PORT, exit code 0=found 1=not found
#   bash detect_p2.sh     # prints port or error message
#
# Runs the PowerShell scan only once per session (cached in $TEMP).
# Re-scans if the cached port is no longer present.

CACHE_FILE="${TEMP:-/tmp}/p2_port.cache"
P2_VID="VID_0403"
P2_PID="PID_6001"

# --- helper: check if a COM port is currently enumerated ---
port_exists() {
  powershell.exe -NoProfile -Command \
    "Get-CimInstance -ClassName Win32_PnPEntity | Where-Object { \$_.Name -match '$1' }" \
    2>/dev/null | grep -qi "$1"
}

# --- 1. Check cache ---
if [[ -f "$CACHE_FILE" ]]; then
  cached_port=$(<"$CACHE_FILE")
  if port_exists "$cached_port"; then
    export P2_PORT="$cached_port"
    echo "P2 detected on $P2_PORT (cached)"
    return 0 2>/dev/null || exit 0
  else
    rm -f "$CACHE_FILE"
  fi
fi

# --- 2. Scan for FTDI P2 ports ---
scan_result=$(powershell.exe -NoProfile -Command \
  "Get-CimInstance -ClassName Win32_PnPEntity |
   Where-Object { \$_.DeviceID -match '${P2_VID}.*${P2_PID}' -and \$_.Name -match 'COM\d+' } |
   ForEach-Object { if (\$_.Name -match '(COM\d+)') { \$Matches[1] } }" 2>/dev/null | tr -d '\r')

if [[ -n "$scan_result" ]]; then
  # Take the first match (lowercase for spinc compatibility)
  P2_PORT=$(echo "$scan_result" | head -1 | tr '[:upper:]' '[:lower:]')
  echo "$P2_PORT" > "$CACHE_FILE"
  export P2_PORT
  echo "P2 detected on $P2_PORT"
  return 0 2>/dev/null || exit 0
fi

# --- 3. Port not found — check for stale spinc.exe ---
stale_pids=$(tasklist 2>/dev/null | grep -i 'spinc.exe' | awk '{print $2}')

if [[ -n "$stale_pids" ]]; then
  echo "ERROR: No P2 found. Stale spinc.exe process(es) may be holding the port:" >&2
  echo "$stale_pids" | while read -r pid; do
    echo "  PID $pid — kill with: taskkill //F //PID $pid" >&2
  done
else
  echo "ERROR: No Propeller 2 detected on any COM port." >&2
fi

unset P2_PORT
return 1 2>/dev/null || exit 1
