# TM-D700 Protocol RE — Project Handoff Summary

**Date:** 2026-07-03  
**For:** Claude Code session starting P2 MITM firmware  
**Read first:** `tmd700_tag_reference.md`, then this document

---

## What This Project Is

Reverse-engineering the proprietary UART protocol between the Kenwood TM-D700 control head and RF deck, with the goal of building a P2-based software replacement control head — and eventually a generic Kenwood aftermarket head platform.

**Hardware:** Parallax Propeller 2 (P2) — Terry's primary maker platform.  
**Terry's callsign:** KE4PJW. Lebanon, Tennessee (UTC−5).  
**GitHub handle:** ironsheep.

---

## Protocol — Confirmed and Complete

**Physical link:** 4 wires — 9.8V, GND, Head TX, Body TX. That's it. No PTT wire. The microphone, speaker, CAT, GPS, and data port are all on the RF deck rear panel.

**UART parameters:** 57600 baud, 8N1, idle-high, CMOS levels. Frame = tag byte + ASCII/binary payload + 0x0D (CR). No checksum. Idle keepalive = bare 0xFF both sides ~1.4s.

**Breakout box wiring (Terry's box, verified working):**
- Black = 9.8V power
- Red = Ground  
- Green = Body TX → Channel 2 / CH1 in decoder (`ch1_name='BODY'`)
- Yellow = Head TX → Channel 1 / CH0 in decoder (`ch0_name='HEAD'`)

**PTT:** Mic connector is on the RF deck, not the head. PTT never appears in the serial protocol. For test TX, a separate P2 GPIO wired to the RF deck's PTT pin is planned (`PTT ON` / `PTT OFF` commands).

**Dumb head architecture:** The control head is a pure display/input panel. All radio state lives in the RF deck. The head reports button presses and knob positions; the body pushes display updates. Lock, PM, power level, frequency — all owned by the RF deck.

---

## Decoder Tool

`uart_decoder.py` — working Python decoder for Saleae CSV captures. Usage:

```python
from uart_decoder import decode_csv, merged_timeline
m0, m1 = decode_csv('capture.csv', baud=57600, ch0_name='HEAD', ch1_name='BODY')
for m in merged_timeline(m0, m1):
    if m.tag != 0xFF:
        print(f"{m.timestamp:.3f}s {m.channel} {m.tag_char}{m.payload_str}")
```

---

## Tag Summary (38 BODY→HEAD confirmed, 22 HEAD→BODY confirmed)

See `tmd700_tag_reference.md` for the full reference. Key points for firmware:

**Power-on — two paths:**
1. Last state OFF: HEAD `[0x0D]` → BODY `[0x0D]` 37ms later → HEAD `[0x80]DIM` → BODY `01` → state dump
2. Last state ON: BODY auto-resumes — HEAD `[0x00][0xFF][0xFF]` → BODY `[0x0D]` → HEAD `[0x80]DIM` → BODY `01` → state dump ~100ms (no button press needed)
3. Standby (DC applied, last state OFF): BODY responds `00` to DIM report; waits for `[0x0D]`

**Boot ID burst (HEAD→BODY at power-on):**
- `0x80` + ASCII DIM level = current DIM level
- `0xC0` + hex byte = SQL A position (0–31)
- `0xC1` + hex byte = VOL A position (0–63)
- `0xC2` + hex byte = SQL B position (0–31)
- `0xC3` + hex byte = VOL B position (0–63)

**Key BODY→HEAD tags:**
- `0` = power state: `00`=standby, `01`=on
- `d` = power-on message (programmed at menu 1-1-1; factory default: `HELLO !!`)
- `N`/`O` = VFO A/B display field (context-sensitive: freq / step / tone Hz / DCS code / REV offset)
- `=` = 3-bit field: Bit0=PTT on B, Bit1=Control on B, Bit2=single-band display
- `J`/`K` = Band A/B status: 0=squelch closed, 1=RX, 2=TX
- `L`/`M` = Band A/B meter: RX→S-meter (00–70), TX→power (20=Low, 50=Med, 70=High)
- `f` = TX start (bare tag, empty payload)
- `b` = menu position (7-char hex path)
- `c` = menu value display

**Key HEAD→BODY codes (all 0x81–0x8E confirmed):**

| Code | Button | Code | Button |
|------|--------|------|--------|
| 0x81 | PM | 0x88 | Tone / T.sel after [F] |
| 0x82 | MNU | 0x89 | REV / SHIFT after [F] |
| 0x83 | VFO | 0x8A | LOW / STEP after [F] |
| 0x84 | MR | 0x8B | MUTE |
| 0x85 | CALL | 0x8C | CTRL / OK / DIM after [F] |
| 0x86 | MHz / Lock after [F] | 0x8D | VOL A press |
| 0x87 | F / ESC in menus | 0x8E | VOL B press |

Long-hold variants: `0x99`=ASC (~930ms), `0x9D`=single-band A (~975ms), `0x9E`=single-band B (~950ms)

Analog controls (per detent): `0xC0`=SQL A (0x00–0x1F), `0xC1`=VOL A (0x00–0x3F), `0xC2`=SQL B, `0xC3`=VOL B

---

## Still Unidentified

Tags `[`, `7`, `X`, `Y` appear in the boot-time state dump on every power-on but have not changed value across any scenario. Almost certainly related to APRS/TNC state. Will resolve during APRS packet capture with MITM.

---

## MITM Architecture (next build)

See `tmd700_p2_mitm_architecture.md` for full spec. Summary:

**P2 pin assignments:**
| Pin | Signal |
|-----|--------|
| P0 | HEAD_TX (P2 → head RX) |
| P1 | HEAD_RX (head TX → P2) |
| P2 | BODY_TX (P2 → body RX) |
| P3 | BODY_RX (body TX → P2) |
| P4 | PC_TX (USB serial) |
| P5 | PC_RX |
| P6 | STATUS_LED |
| P7 | PTT_TEST (GPIO → RF deck PTT pin, open-drain) |

**PC protocol:**
```
HEAD: N0144.390      ← monitoring output: head sent this to body
BODY: J1             ← monitoring output: body sent this to head
HEAD: [0x87]         ← inject [F] keypress to RF deck (P2 acts as head)
BODY: N0999.999      ← inject freq display to control head (P2 acts as body)
!HEAD: [0x87]        ← echo: P2 forwarded this injection
PTT ON               ← assert PTT GPIO
PTT OFF              ← release PTT GPIO
MODE PASS            ← transparent passthrough + log (default)
MODE INJECT          ← enable injection
MODE HEADLESS        ← P2 acts as head; real head disconnected
MODE BODYLESS        ← P2 acts as body; real body disconnected
QUIET ON/OFF         ← suppress/show 0xFF keepalive lines
```

**COG layout:**
- COG 0: Main coordinator, frame routing, injection queue
- COG 1: HEAD UART (57600 baud smart pins)
- COG 2: BODY UART (57600 baud smart pins)
- COG 3: PC UART (921600 baud)
- COG 4+: Reserved for display driver (Phase 2)

**Boot handling in HEADLESS mode:**
1. Wait for BODY `[0x0D]`
2. Delay ~37ms, send `[0x0D]` to BODY
3. Send boot ID burst: `[0x80]1`, `[0xC0][0x03]`, `[0xC1][0x17]`, `[0xC2][0x0F]`, `[0xC3][0x1A]`
4. Begin 0xFF keepalives every 1.4s
5. Forward all BODY frames to PC

**First tests to run once MITM is working:**

1. **BODYLESS: inject display frames to head** — proves head is pure renderer
   ```
   MODE BODYLESS
   BODY: N0999.999  
   BODY: J2
   BODY: 49
   ```

2. **HEADLESS: synthetic button presses to body**
   ```
   MODE HEADLESS
   HEAD: [0x83]    ← VFO button
   HEAD: [0x8F]01  ← encoder CW
   ```

3. **APRS tag capture** — resolve `[`, `7`, `X`, `Y`
   ```
   MODE PASS
   QUIET ON
   # Wait for APRS packet on 144.390 MHz
   # Tags that appear only during packet = APRS data tags
   ```

---

## Phase Roadmap

1. **P2 MITM firmware** (current) — transparent passthrough + injection + HEADLESS/BODYLESS modes
2. **Python host script** — interactive injection, scripted test sequences
3. **Hybrid head** — P2 drives display alongside original head (validation)
4. **Full software head** — original head disconnected, P2 drives everything
5. **TS-2000 delta** — same head hardware, capture protocol differences
6. **Generic Kenwood platform** — radio-type config layer, community contributions

---

## Files in This Project

| File | Contents |
|------|----------|
| `tmd700_tag_reference.md` | Complete tag/keycode reference, CTCSS table, DCS codes, menu map |
| `tmd700_protocol_re.md` | Hardware, protocol parameters, architecture summary |
| `tmd700_p2_mitm_architecture.md` | MITM design spec, pin assignments, PC protocol |
| `tmd700_capture_scenarios.md` | All 20 capture scenarios with confirmed findings |
| `uart_decoder.py` | Python decoder for Saleae CSV captures |
| `tmd700_project_handoff.md` | This document |

