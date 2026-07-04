# TM-D700 P2 MITM — Architecture Document

**Project:** Kenwood TM-D700 Protocol Bridge / Control Head Replacement  
**Platform:** Parallax Propeller 2 (P2)  
**Status:** Design phase  
**Goal:** Inline protocol bridge enabling PC-controlled injection and monitoring of the head↔body UART link, as the development harness for a full software replacement control head.

---

## 1. Overview

The P2 sits inline in the J1 cable between the TM-D700 control head (J1) and RF deck (J602). In transparent passthrough mode it is invisible to both sides. The PC interface exposes the full bidirectional stream in human-readable form and accepts injection frames using the same format.

```
┌───────────────┐     57600 8N1     ┌─────────────────┐     57600 8N1     ┌───────────────┐
│  CONTROL HEAD │◄──────────────────►│   P2  (MITM)    │◄──────────────────►│   RF DECK     │
│   (J1)        │   HEAD UART pair  │                 │   BODY UART pair  │   (J602)      │
└───────────────┘                   │                 │                   └───────────────┘
                                    │    PC UART      │
                                    │  (USB serial)   │
                                    └────────┬────────┘
                                             │ 921600 baud
                                             ▼
                                        PC / Claude
```

---

## 2. PC Protocol

### 2.1 Monitoring output (P2 → PC)

Every frame observed on either UART is printed to the PC with direction prefix, tag, and payload. Non-printable bytes use `[0xNN]` hex notation; valid printable ASCII (0x20–0x7E) is rendered as-is. The 0x0D frame terminator is implicit and not printed.

```
HEAD: [0x87]
HEAD: [0x8F]01
BODY: N0144.390  
BODY: J1
BODY: L30
BODY: [0xFF]
HEAD: [0xFF]
```

Special structural bytes:
```
HEAD: [0x0D]           ← power-on sync byte (bare CR)
BODY: [0x0D]           ← power-on sync reply
HEAD: [0xFF]           ← idle keepalive
BODY: [0xFF]           ← idle keepalive
```

Injected frames are echoed back with a `!` marker so the PC can distinguish its own injections from observed traffic:
```
!HEAD: N0999.999       ← PC injected this; P2 forwarded to control head
!BODY: [0x87]          ← PC injected this; P2 forwarded to RF deck
```

### 2.2 Injection input (PC → P2)

The PC sends a line with a direction prefix and payload. The P2 reconstructs the raw frame (tag + payload + 0x0D) and forwards it to the appropriate target.

```
HEAD: N0144.390        ← inject to control head  (P2 acts as RF deck)
HEAD: J1               ← inject BUSY indicator to head
HEAD: [0xFF]           ← inject keepalive to head
BODY: [0x87]           ← inject [F] keypress to RF deck (P2 acts as head)
BODY: [0x8C]           ← inject OK/CTRL to RF deck
BODY: [0xC0][0x0F]     ← inject SQL A = 15 to RF deck
```

Payload encoding rules (same for both directions):
- `[0xNN]` = single raw byte with hex value NN
- Any other character = literal ASCII byte
- Tag byte is always the first character/token
- Newline (`\n`) terminates the injection command

### 2.3 Mode control (PC → P2)

Simple single-word commands control P2 behavior:

```
MODE PASS              ← transparent passthrough, log only (default)
MODE INJECT            ← enable injection; still passthrough between injections
MODE HEADLESS          ← disconnect head from body; P2 alone drives body (act as head)
MODE BODYLESS          ← disconnect body from head; P2 alone drives head (act as body)
QUIET ON               ← suppress [0xFF] keepalive lines from output
QUIET OFF              ← show all frames including keepalives
PTT ON                 ← assert PTT GPIO (P7 low → RF deck PTT pin)
PTT OFF                ← release PTT GPIO (P7 high-Z)
```

`HEADLESS` and `BODYLESS` modes are the key modes for state machine testing:
- **HEADLESS:** Real head disconnected. P2 sends boot handshake and keepalives to body, presents body's responses to PC. PC can command the radio directly.
- **BODYLESS:** Real body disconnected. P2 sends boot handshake and keepalives to head, presents head's button presses to PC. PC can drive the display directly.

---

## 3. P2 Hardware

### 3.1 Pin assignments (proposed)

| P2 Pin | Direction | Signal | Notes |
|--------|-----------|--------|-------|
| P0 | TX→ | HEAD_TX | To control head RX (TC4S81F buffer on head side handles level) |
| P1 | ←RX | HEAD_RX | From control head TX |
| P2 | TX→ | BODY_TX | To RF deck RX (J602) |
| P3 | ←RX | BODY_RX | From RF deck TX |
| P4 | TX→ | PC_TX | USB-serial TX (3.3V to USB adapter) |
| P5 | ←RX | PC_RX | USB-serial RX |
| P6 | output | STATUS_LED | Heartbeat / injection indicator |

All signals are CMOS 3.3V. The existing TC4S81F buffers on the control head PCB handle impedance matching — the P2 connects to the cable conductors between head and deck, not directly to the PCB pads.

### 3.2 Inline connection

The J1 cable carries 4 wires: 9.65V, GND, TXD, RXD. The P2 taps TXD and RXD with its own UART receivers and inserts its own TX signals in the path. The 9.65V supply can power the P2 through a small regulator (the XL6019E1 SEPIC already evaluated for another project is well-suited here).

```
J1 Cable tap:
  9.65V ──────────────────────────────────────────────────────── J602 9.65V
  GND ────────────────────────────────────────────────────────── J602 GND
  HEAD TX (white) ──┬─► P2 HEAD_RX (P1)                        (cut wire)
                    │   P2 HEAD_TX (P0) ────────────────────── J602 RXD
  HEAD RX (green) ──┤   P2 BODY_TX (P2) ────────────────────── J602 TXD
                    └─► P2 BODY_RX (P3)                        (cut wire)
```

### 3.3 PTT — microphone on RF deck, not head

The microphone connector is physically on the **RF deck**, not the control head. CAT control, data port, and GPS input are also on the RF deck. This means PTT from the microphone goes directly to RF deck hardware and **never passes through J1 or the control head at all**.

There is no PTT in the J1/J602 protocol. The four wires (9.68V, GND, TXD, RXD) are the complete and only communication between head and deck. The body emits `f`/`J2`/`K2` when TX starts as a notification to the head for display purposes; the actual TX trigger is the mic PTT line at the RF deck's own connector.

**Implications for replacement head:**
- Voice PTT: mic stays plugged into RF deck as normal — no replacement head involvement required
- Programmatic PTT (APRS beacons, etc.): requires driving the PTT line at the RF deck's mic or data port connector directly — a separate interface from J1
- The replacement head only needs 4 wires to J602: 9.68V, GND, TXD, RXD

**PTT testing via P2 GPIO:**
For test and development purposes, a dedicated P2 GPIO can be wired to the RF deck's PTT input (mic connector or data port), controlled by a special PC command. This is entirely independent of the J1 serial link and allows the PC to key the transmitter without a physical mic — useful for APRS beacon testing, verifying `f`/`J2`/`K2` tag sequences, and TX power level capture.

```
P2 Pin additions:
  P7  output  PTT_TEST   GPIO → RF deck PTT pin (open-drain, active low)

PC command:
  PTT ON    ← assert PTT (P7 low, keys transmitter)
  PTT OFF   ← release PTT (P7 high-Z)
```

The P2 echoes PTT state changes to the PC log:
```
PTT ON                 ← P2 asserted PTT
BODY: f                ← body confirms TX start
BODY: J2               ← Band A transmitting
BODY: L70              ← high power meter
PTT OFF                ← P2 released PTT
BODY: J0               ← squelch closed, TX ended
```

**Full picture of what the control head actually is:**
- LCD display + key illumination
- Front panel buttons (serial keycodes)
- Tuning encoder (serial)
- SQL A/B and VOL A/B knobs (serial ADC readings)
- DIM level control (serial)

Nothing else. Audio in, audio out, PTT, CAT, GPS, data — all RF deck rear panel. The head is purely a display/input panel connected by 4-wire serial.

### 4.1 COG layout

| COG | Role |
|-----|------|
| 0 | Main coordinator — frame routing, injection queue, mode control |
| 1 | HEAD UART — smart pin RX/TX at 57600 baud |
| 2 | BODY UART — smart pin RX/TX at 57600 baud |
| 3 | PC UART — smart pin RX/TX at 921600 baud |
| 4 | (reserved for display driver in Phase 2) |
| 5–7 | Available |

### 4.2 Frame flow (PASS mode)

```
HEAD_RX byte arrives
  → accumulate in head_rx_buf[] until 0x0D
  → complete frame: format as "HEAD: [tag][payload]\n"
  → write to PC_TX queue
  → copy raw frame bytes to BODY_TX queue (passthrough)

BODY_RX byte arrives
  → accumulate in body_rx_buf[] until 0x0D
  → complete frame: format as "BODY: [tag][payload]\n"
  → write to PC_TX queue
  → copy raw frame bytes to HEAD_TX queue (passthrough)

PC_RX line arrives (newline terminated)
  → parse direction prefix (HEAD: or BODY:)
  → parse payload (decode [0xNN] hex tokens)
  → reconstruct raw frame (decoded bytes + 0x0D)
  → queue to appropriate UART TX (HEAD_TX or BODY_TX)
  → echo as "!HEAD: ..." or "!BODY: ..." to PC_TX
```

### 4.3 Injection timing

The head/body link has natural idle gaps (keepalive period ~1.4s, inter-frame gaps ~100ms). Injection can occur in any idle gap — at 57600 baud, a 20-byte frame takes ~3.5ms, well within any gap. The P2 queues injection frames and sends them immediately when the UART is idle.

If the PC injects during an active frame, the P2 buffers and sends after the current frame completes. No collision is possible because injection targets a specific direction (HEAD_TX or BODY_TX) independently of what the other side is doing.

### 4.4 Boot sequence handling

Both HEADLESS and BODYLESS modes must generate the correct power-on handshake:

```
HEADLESS mode (P2 acts as head):
  1. Wait for BODY 0x0D sync
  2. Delay ~37ms
  3. Send 0x0D to BODY
  4. Send boot ID burst: 0x80,'1',0x0D  then 0xC0,0x03,0x0D  then 0xC1,0x17,0x0D
                         then 0xC2,0x0F,0x0D  then 0xC3,0x1A,0x0D
  5. Begin sending 0xFF keepalives every 1.4s
  6. Forward all BODY frames to PC

BODYLESS mode (P2 acts as body):
  1. Send 0x0D sync to HEAD
  2. Wait for HEAD 0x0D reply and boot ID burst
  3. Log received boot ID burst to PC
  4. Begin sending 0xFF keepalives every 1.4s
  5. Forward all HEAD frames to PC
  6. PC can now inject BODY→HEAD display frames
```

### 4.5 Key test procedure — state machine location

```
Test A: Does the head hold any state?
  1. BODYLESS mode — P2 acts as body
  2. PC injects: "HEAD: N0144.390  " (frequency for Band A)
  3. Observe head display — if it updates, head is purely a renderer
  4. PC injects: "HEAD: J2" (TX status)
  5. Observe if any TX indicator appears on head display
  6. PC injects: "HEAD: 49" (lock indicator)
  7. Observe if LOCK appears on display

Test B: Does the body respond to synthetic head commands?
  1. HEADLESS mode — P2 acts as head
  2. PC injects: "BODY: [0x83][0x0D]" (VFO button press)
  3. Observe body response in log — expect R0/N0/P0 VFO fields
  4. PC injects: "BODY: [0x8F]01[0x0D]" (encoder CW)
  5. Observe N0 frequency increment in body response
  6. PC injects: "BODY: [0xC0][0x0F][0x0D]" (SQL A = 15)
  7. Observe if body sends J1/J0 BUSY as squelch opens/closes
```

---

## 5. Phase Roadmap

### Phase 1 — MITM Bridge (current)
- Transparent passthrough with PC logging
- Injection support (PASS + INJECT modes)
- HEADLESS / BODYLESS modes for isolated testing
- Python host script for interactive and scripted injection
- **Deliverable:** Prove state machine location; complete APRS tag capture

### Phase 2 — Hybrid Head
- P2 drives a real display alongside the original head (both connected)
- Renders the same data the original head would show, as validation
- Confirms display rendering logic before disconnecting original head
- **Deliverable:** Mirror display — visually verified against original

### Phase 3 — Full Software Head (TM-D700)
- Original head disconnected entirely
- P2 drives display, scans button matrix, handles encoder and knobs
- Complete feature parity with original head
- **Deliverable:** Working TM-D700 replacement head

### Phase 4 — TS-2000 and Generic Platform
- Capture TS-2000 head/body protocol delta (same head hardware, different firmware)
- Radio-type configuration layer in firmware
- Community contribution framework for additional Kenwood radios
- **Deliverable:** Generic Kenwood aftermarket replacement head platform

---

## 6. Python Host Script (Sketch)

```python
import serial
import threading

class D700Bridge:
    def __init__(self, port, baud=921600):
        self.ser = serial.Serial(port, baud, timeout=0.1)
        self.running = True
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):
        buf = b''
        while self.running:
            data = self.ser.read(256)
            if data:
                buf += data
                while b'\n' in buf:
                    line, buf = buf.split(b'\n', 1)
                    print(line.decode('ascii', errors='replace'))

    def inject_to_head(self, tag, payload=''):
        """Inject a body→head frame (P2 sends to control head)."""
        frame = self._encode(tag, payload)
        self.ser.write(f'HEAD: {frame}\n'.encode())

    def inject_to_body(self, tag_byte, payload_bytes=b''):
        """Inject a head→body frame (P2 sends to RF deck)."""
        frame = self._encode_raw(bytes([tag_byte]) + payload_bytes)
        self.ser.write(f'BODY: {frame}\n'.encode())

    def _encode(self, tag, payload):
        """Encode tag + payload to mixed ASCII/[0xNN] string."""
        result = ''
        for byte in (tag + payload).encode('latin-1'):
            if 0x20 <= byte <= 0x7E:
                result += chr(byte)
            else:
                result += f'[0x{byte:02X}]'
        return result

    def set_mode(self, mode):
        self.ser.write(f'MODE {mode}\n'.encode())

# Usage examples:
# bridge = D700Bridge('/dev/ttyUSB0')
# bridge.set_mode('BODYLESS')
# bridge.inject_to_head('N', '0144.390  ')   # set Band A frequency display
# bridge.inject_to_head('J', '2')             # show TX indicator
# bridge.inject_to_head(';', '4')             # set DIM level 4
# bridge.inject_to_head('=', '3')             # Band B selected
# bridge.set_mode('HEADLESS')
# bridge.inject_to_body(0x83)                  # VFO button
# bridge.inject_to_body(0x8F, b'\x01')         # encoder CW one click
```

---

## 7. Open Questions to Resolve via MITM

| Question | Test |
|----------|------|
| Is the head a pure renderer? | BODYLESS: inject arbitrary display frames, confirm head just shows them |
| Does lock state live in body? | HEADLESS: send button presses while body is in locked state; confirm body ignores them |
| What are tags `1`, `[`, `7`, `X`, `Y`? | HEADLESS: drive body into APRS TX/RX and watch for these tags in body→PC output |
| Does encoder speed affect tag payload value? | BODYLESS: inject 0x8F with values 0x03, 0x05, etc.; observe body response |
| Can a replacement head TX programmatically? | Via P2 PTT_TEST GPIO (P7) wired to RF deck PTT pin — `PTT ON` / `PTT OFF` commands. Out of scope for Phase 1 serial work but planned for Phase 1 hardware. |
| PM channel without real head | HEADLESS: inject PM select sequence, confirm body loads all settings |

---

*Next step: implement Phase 1 P2 firmware (COG layout and smart pin UART setup in Spin2/PASM2).*
