# Spin Tools Build, Upload & Debug Pipeline

Drop these files into your Spin2 project directory and update the variables below to match your environment.

## Files

| File | Description |
|------|-------------|
| `SPINC_BUILD.md` | This document |
| `detect_p2.sh` | Auto-detects the P2 COM port (Windows/bash) |
| `DebugTest_Top.spin2` | Test program to validate the pipeline |

## Variables

| Variable | Value | Description |
|----------|-------|-------------|
| `SPINC` | `C:\spin-tools\spinc.exe` | Path to the Spin Tools compiler |
| `TOP_FILE` | `DebugTest_Top.spin2` | Top-level Spin2 file to compile |
| `COM_PORT` | *(auto-detected)* | Serial port the P2 is connected to |
| `PROJECT_DIR` | `.` | Project directory containing the top file |

## Command Line Options

| Flag | Purpose |
|------|---------|
| `-p <COM_PORT>` | Serial port to use for upload |
| `-d` | Enable debug mode |
| `-t` | Send debug output to stdout (terminal) |
| `-r` | Load to RAM and run (not flash) |
| `-L <path>` | Add a library directory to the object search path |

**Library path (`-L`) is required.** `spinc` does not auto-search its own
`library/spin2` folder, and `TMD700_MITM_Top.spin2` uses the JonnyMac library
objects (`jm_strings`, `jm_nstr`). Always pass
`-L "C:\spin-tools\library\spin2"` or the build fails with `object ... not found`.

## COM Port Auto-Detection

The included `detect_p2.sh` script finds the P2 by scanning for its FTDI USB chip (`VID_0403 PID_6001`). It caches the result in `$TEMP/p2_port.cache` so the scan only runs once per session.

### When detection runs

- **First call** — scans all COM ports via PowerShell, caches the result.
- **Subsequent calls** — returns the cached port instantly (no scan).
- **Board unplugged** — cache is invalidated, triggers a fresh scan.
- **Reboot** — cache is in `$TEMP`, so it is cleared automatically.

### Usage

```bash
# Source to set P2_PORT in the current shell
source ./detect_p2.sh

# Use the detected port
"<SPINC>" -p $P2_PORT -d -t -r -L "C:\spin-tools\library\spin2" "<TOP_FILE>"
```

Or run standalone to print the detected port:

```bash
bash ./detect_p2.sh
```

### When detection fails

If no P2 is found, the script checks for stale `spinc.exe` processes that may be holding the port open and reports their PIDs:

```
ERROR: No P2 found. Stale spinc.exe process(es) may be holding the port:
  PID 12345 — kill with: taskkill //F //PID 12345
```

If no stale processes are found either:

```
ERROR: No Propeller 2 detected on any COM port.
```

## Build & Upload Command

```bash
source ./detect_p2.sh
"<SPINC>" -p $P2_PORT -d -t -r -L "C:\spin-tools\library\spin2" "<PROJECT_DIR>/<TOP_FILE>"
```

### Example

```bash
source ./detect_p2.sh
"C:/spin-tools/spinc.exe" -p $P2_PORT -d -t -r -L "C:/spin-tools/library/spin2" "./TMD700_MITM_Top.spin2"
```

## Exiting Terminal Mode

There are two ways the debug terminal session ends:

1. **Manual exit:** Press `Ctrl+C` to exit terminal mode and kill the process.
2. **Programmatic exit:** Call `debug(DEBUG_END_SESSION)` in your Spin2 code. This sends an `ESC CR LF` sequence that signals `spinc.exe` to exit terminal mode automatically. This is useful for automated pipelines or programs that run to completion.

## Notes

- **COM port conflicts:** If you get `No propeller chip on port <COM_PORT>`, check for stale `spinc.exe` processes holding the port open. Kill them before retrying, or run `detect_p2.sh` which will report stale PIDs for you.
- **Spurious PASM2 errors:** `spinc.exe` may report `symbol not found` errors for PASM2 inline assembly symbols. These are cosmetic — the compiler still produces a valid binary and uploads successfully.
- **Warnings are normal:** The compiler warns about unused methods in library files. These do not affect compilation.

## Expected Output (successful run)

```
P2 detected on com4
Spin Tools Compiler - Version 0.54.0
Copyright (c) 2021-26 Marco Maccaferri and others. All rights reserved.
Compiling...
<TOP_FILE>
 +-- dependency1.spin2
 +-- dependency2.spin2
Program size is XXXXX bytes
Uploading...
Propeller 2 on port <COM_PORT>
Loading binary image to hub memory
XXXXX bytes sent
Verifying checksum ... OK
Entering terminal mode. CTRL-C to exit.
Cog0  INIT $0000_0000 $0000_0000 load
Cog0  INIT $0000_0F64 $0000_1868 jump
Cog0  Hello from P2
Cog0  Result: value = 42
Cog0                      <--- DEBUG_END_SESSION (spinc exits automatically)
```

After `Entering terminal mode`, debug output from `debug()` statements in your Spin2 code will appear on stdout. If the program calls `debug(DEBUG_END_SESSION)`, the terminal exits cleanly without needing `Ctrl+C`.
