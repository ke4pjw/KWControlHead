# Kenwood TM-D700 Control Head — Protocol RE & P2 Replacement Head

Reverse-engineering the proprietary UART protocol between the Kenwood TM-D700
control head and its RF deck, and building a [Parallax Propeller 2](https://www.parallax.com/propeller-2/)
based software replacement control head — with the longer-term goal of a generic
Kenwood aftermarket head platform.

**Author:** Terry Trapp (KE4PJW) · GitHub [@ke4pjw](https://github.com/ke4pjw)

> ⚠️ This is active research on one irreplaceable control head. All hardware work
> is non-destructive; the P2 taps the head↔deck cable inline and is transparent
> in passthrough mode.

## The protocol in one paragraph

Four wires between head (J1) and RF deck (J602): 9.65 V, GND, and two UART lines.
**57600 baud, 8N1, idle-high, CMOS 3.3 V.** Each frame is a single tag byte + an
ASCII/binary payload + `0x0D` (CR); no checksum. Idle keepalive is a bare byte
(`0xFF`, or `0x0D` polls on this unit) roughly every 1.4 s. The control head is a
**dumb display/input panel** — all radio state lives in the deck; the head reports
buttons/knobs and renders what the deck pushes. This is why the same head works on
both the TM-D700 and TS-2000. See the tag reference for the full decode
(42 BODY→HEAD tags and 24 HEAD→BODY keycodes confirmed).

## Repository contents

| File | What it is |
|------|-----------|
| [`tmd700_tag_reference.md`](tmd700_tag_reference.md) | **Complete tag / keycode reference** — the master decode. CTCSS/DCS tables, menu map, keycode modifier-bit scheme. |
| [`tmd700_protocol_re.md`](tmd700_protocol_re.md) | Hardware teardown, protocol parameters, architecture. |
| [`tmd700_p2_mitm_architecture.md`](tmd700_p2_mitm_architecture.md) | P2 MITM design spec — pin map, PC protocol, COG layout, modes. |
| [`tmd700_capture_scenarios.md`](tmd700_capture_scenarios.md) | Systematic capture scenarios used to identify tags. |
| [`tmd700_project_handoff.md`](tmd700_project_handoff.md) | Project summary / phase roadmap. |
| [`TMD700_MITM_Top.spin2`](TMD700_MITM_Top.spin2) | **P2 MITM firmware** (Spin2/PASM2) — transparent passthrough + live decoded monitor. |
| [`uart_decoder.py`](uart_decoder.py) | Python decoder for Saleae CSV captures. |
| [`SPINC_BUILD.md`](SPINC_BUILD.md) / [`detect_p2.sh`](detect_p2.sh) | Spin Tools build/upload/debug pipeline + P2 COM-port auto-detect. |
| `tmd700_capture_*.log` | Raw decoded captures from the P2 MITM. |

## P2 MITM firmware

The P2 sits inline in the J1 cable. A dedicated PASM2 cog forwards every byte
transparently between head and deck (byte-exact, non-blocking) while pushing a
tagged copy into a hub ring buffer; a second cog decodes complete frames and
prints them over the DEBUG terminal:

```
HEAD: [0x83]              VFO button
HEAD: [0x8F]01            encoder one click CW
BODY: N0144.390          VFO A frequency
BODY: T10<callsign>...    received APRS station
```

Pin map (data-flow-grouped inline tap): `P0`=TX→head, `P1`=RX←deck (BODY→HEAD
repeater); `P2`=TX→deck, `P3`=RX←head (HEAD→BODY repeater). Radio links at
57600; PC/DEBUG at higher rate.

**Build & run** (Spin Tools `spinc.exe`, see [`SPINC_BUILD.md`](SPINC_BUILD.md)):

```bash
source ./detect_p2.sh
"C:/spin-tools/spinc.exe" -p $P2_PORT -d -t -r "TMD700_MITM_Top.spin2"
```

Engineering note: on an inline UART repeater, slew-limit the TX pins — they sit
next to the RX pins, and fast edges couple into them and corrupt received bytes.

## Roadmap

1. **P2 MITM bridge** — transparent passthrough + decoded monitor ✅, injection + HEADLESS/BODYLESS modes (in progress)
2. **Hybrid head** — P2 drives a display alongside the original head (validation)
3. **Full software head** — original head disconnected, P2 drives everything
4. **TS-2000 delta**, then a **generic Kenwood platform** with a radio-type config layer

## Reference

Parallax Spin2 documentation (v54) is used as the firmware language reference but
is not redistributed here — get it from [Parallax](https://www.parallax.com/).
