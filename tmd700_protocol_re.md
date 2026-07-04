# Kenwood TM-D700 Control Head ↔ RF Deck Protocol — Reverse Engineering Notes

**Author:** Terry (KE4PJW)  
**Last updated:** 2026-06-30  
**Status:** Active research — core radio protocol substantially decoded; APRS/TNC tags and some boot-block tags remain open

---

## 1. Background and Goal

The Kenwood TM-D700 is a dual-band VHF/UHF mobile transceiver with a detachable control head. The head connects to the RF deck via a short cable carrying power, ground, and two UART serial lines. The communication protocol is proprietary and was undocumented.

**Goal:** Reverse-engineer the head↔body protocol fully enough to build a software-defined replacement for the control head.

**Constraint:** There is exactly one working control head available. It is irreplaceable. All hardware approaches must be non-destructive.

---

## 2. System Architecture

```
┌─────────────────────────────┐  4-wire cable   ┌──────────────────────────────┐
│     CONTROL HEAD            │◄───────────────►│        RF DECK               │
│  (Panel Unit X54-3290-00)   │ 9.65V,GND,TXD,RXD│     (TX-RX Unit X57-586)    │
│                             │                 │                              │
│  CPU: M30622M8759GP         │                 │  CPU: NEC 78F4218GCJVYC     │
│  (Kenwood-branded           │                 │  (NEC 78K series)           │
│   Renesas M16C/62 silicon,  │                 │                              │
│   100-pin QFP, ~1999)       │                 │  Config EEPROM:              │
│                             │                 │  AT25128N10SI27 (16KB SPI)   │
│  Program EEPROM:            │                 │  [Terry replaced this;       │
│  AT29C020-90TI              │                 │   required full alignment]   │
│  (256KB parallel flash,     │                 │                              │
│   44-pin TSOP)              │                 │  Speaker in RF deck          │
│                             │                 │  TNC on Band A (144.390 MHz) │
│  Crystal: 11.0592 MHz       │                 │  Panel UART: TXD3/RXD3      │
│  IC1/IC2: TC4S81F (buffers) │                 │  PC port: RS-232 D-SUB      │
│                             │                 │  Crystal: 11.0592 MHz        │
└─────────────────────────────┘                 └──────────────────────────────┘
         J1 (head)                                       J602 (deck)
```

**Same control head used on Kenwood TS-2000.**

### CPU boot architecture (head)

CNVSS pin tied to VSS (low) → CPU boots in single-chip mode from internal mask ROM ("8759" = Kenwood's mask code). Mask ROM bootstrap switches CPU to memory expansion mode to access the AT29C020. Two-tier firmware: (1) permanent internal mask ROM — holds recovery/bootstrap code, NOT dumpable; (2) AT29C020 — field-updatable application firmware, primary RE target.

When AT29C020 is blank, display shows **"PROG 115200 BPS"** — internal bootstrap waits for firmware image via UART at 115200 baud.

---

## 3. Physical Interface — Confirmed

**Connector J1 (head) / J602 (deck): 4 wires**

| Signal | Notes |
|--------|-------|
| 9.65V | Power from RF deck to head |
| GND | Common ground |
| TXD | Head transmits → Deck receives |
| RXD | Deck transmits → Head receives |

Signal levels: **CMOS** (not RS-232). TC4S81F line buffers on the head side. RS-232 driver (ADM202) on the RF deck connects only to the rear D-SUB PC port — not in the head/body path.

---

## 4. Protocol — Confirmed Parameters

| Parameter | Value | Confidence |
|-----------|-------|-----------|
| Baud rate | **57600** | Confirmed by timing measurement (17.369µs/bit) and zero-error framing scan |
| Format | 8N1, idle-high | Confirmed |
| Frame format | Tag byte + ASCII payload + 0x0D (CR) | Confirmed |
| Checksum | None | Confirmed — no extra bytes observed |
| Idle keepalive | Bare 0xFF, both sides, ~1.4s | Confirmed |
| Power-on handshake | Head: bare 0x0D → Body: bare 0x0D ~37ms later | Confirmed |

The 11.0592 MHz crystal on both head and deck is a "baud-rate crystal" that divides exactly to 57600 (÷192). All other standard rates (9600, 19200, 38400, 115200) are also exact divisors.

---

## 5. Architectural Conclusion — Dumb Head

The control head is functionally **stateless with respect to radio logic**:
- All radio state (frequency, mode, tone, band, memory channels) lives on the RF deck
- The head reports button presses and encoder/knob positions; the body decides what to do and pushes display updates back
- Lock state, PM state, DIM setting, power level — all owned by the RF deck
- The head has no audio hardware; speaker is in the RF deck; volume is sent to the body which adjusts its own amplifier silently

The head does retain local intelligence for: LCD controller, button matrix scanning, backlight/key illumination, and the recovery bootloader. None of it touches radio-domain logic.

This architecture explains why the same head works on both the TM-D700 and TS-2000 — no radio-specific logic is baked into the head.

---

## 6. Display Mode Indicator (tag `4`)

The body sends tag `4` to tell the head which display context is active, so it knows how to interpret context-sensitive tags like `N`/`O`:

| Value | Meaning |
|-------|---------|
| `40` | Normal VFO/MR display |
| `41` | `[F]` function key pressed (menu hint) |
| `45` | Encoder-driven list selection (step size, DIM level, etc.) |
| `46` | Tone/CTCSS/DCS frequency or code selection |
| `48` | PM selection UI active |
| `49` | Transceiver locked |
| `4E` | Transceiver locked + `[F]` pressed (unlock in progress) |

---

## 7. Frequency Payload Encoding

Tags `N` and `O` carry frequency data, but the separator and prefix bytes encode additional information:

**Separator byte** (between integer and decimal digits):
- `0x2E` (`.`) = FM standard, displays as dot
- `0x15` (NAK) = AM receive, displays as underscore `_` (aviation band; also menu-selected AM mode)

**Prefix byte** (before digit string):
- None = normal (e.g. `144.000`)
- `0x12` (DC2) = display "12" in small font before remaining digits (e.g. `¹²40.000` = 1240.000 MHz, 23cm band)

**Context-sensitive reuse** — `N`/`O` carry different data depending on tag `4`:
- Normal → frequency (e.g. `0144.390  `)
- `45` → selection label (e.g. `0DIM   4`, `0 10.0    `)
- `46` → tone Hz (e.g. `0123.0     `) or DCS code (e.g. `0125      `)
- Memory mode → channel frequency (updates per encoder click)
- REV active → offset/input frequency

**`P`/`Q` channel number encoding:**
- Prefix `0` + right-justified 3-char number = channels 1–199
- Prefix `1` + 3-char number = channels 200+ (e.g. `P1200` = channel 200)
- Prefix `8` + number = tone/CTCSS index during tone selection

---

## 8. Paired Band A/B Tag Pattern

All radio-state fields come in Band A/B pairs using adjacent alphabetic tags:

| Function | Band A | Band B |
|----------|--------|--------|
| TX power | `B` | `C` |
| Tone mode | `@` | `A` |
| Shift direction | `D` | `E` |
| REV/ASC status | `F` | `G` |
| Menu/selection display | `H` | `I` |
| BUSY indicator | `J` | `K` |

---

## 9. Complete Confirmed Tag Reference

See companion document **`tmd700_tag_reference.md`** for the complete confirmed tag table, unidentified tags, button keycode table, CTCSS tone table (38 tones), DCS code list (101 codes), and appendices.

### Summary — BODY→HEAD (29 confirmed)

`d` `V` `;` `2` `3` `5` `=` `N` `R` `O` `S` `P` `Q` `B` `C` `@` `A` `4` `D` `E` `F` `G` `H` `I` `J` `K` `Z` `b` `c`

### Summary — HEAD→BODY (22 confirmed)

**Button range 0x81–0x8E fully mapped:**

| Code | Button | Code | Button |
|------|--------|------|--------|
| `0x81` | PM | `0x88` | Tone/T.sel |
| `0x82` | MNU | `0x89` | REV/SHIFT |
| `0x83` | VFO | `0x8A` | LOW/STEP |
| `0x84` | MR | `0x8B` | MUTE |
| `0x85` | CALL | `0x8C` | CTRL/OK/DIM |
| `0x86` | MHz | `0x8D` | VOL A (press) |
| `0x87` | F / ESC | `0x8E` | VOL B (press) |

**Long-hold variants:**
- `0x99` = REV long-hold (~930ms): ASC activate
- `0x9D` = VOL A long-hold (~975ms): single-band display Band A toggle
- `0x9E` = VOL B long-hold (~950ms): single-band display Band B toggle

**Analog controls (per detent):**
- `0x8F` payload `0x01`/`0xFF`/`0x02` = encoder CW/CCW/×2
- `0xC0`/`0xC1`/`0xC2`/`0xC3` = SQL A / VOL A / SQL B / VOL B position

**Structural:** `0xB0` = end-of-burst marker

---

## 10. Boot "ID Burst" — Fully Decoded

At power-on, the head reports all five hardware control positions to the body before any user interaction:

| Tag | Boot value | Meaning |
|-----|-----------|---------|
| `0x80` | `'1'` | DIM level 1 at boot |
| `0xC0` | `0x03` | SQL A = 3 |
| `0xC1` | `0x17` | VOL A = 23 |
| `0xC2` | `0x0F` | SQL B = 15 |
| `0xC3` | `0x1A` | VOL B = 26 |

---

## 11. Known Menu Structure

The `b` tag payload encodes the current menu path: `[band][bank][L1][L2][focus][0][0]` where focus: 0=top, 1=at L1, 2=L2 browsing (c shows stored value), 3=value edit mode. The `c` tag shows the current item value, right-aligned in a fixed-width field.

Menu items discovered:

| Path | Values | Meaning |
|------|--------|---------|
| L1=2, L2=1 | OFF, LEVEL 1–7 | Key Beep |
| L1=2, L2=2 | ON | Unknown |
| L1=2, L2=3 | MODE1 | Unknown |
| L1=3, L2=1 | 136–199 MHz | Aviation AM range |
| L1=3, L2=2 | OFF | Unknown |
| L1=3, L2=3 | OFF | Unknown |
| L1=3, L2=4 | FM / AM | FM/AM mode |

**Note:** FM/AM is menu-only — no direct key shortcut. `[F]`+`[MHz]` (`0x87`+`0x86`) = Transceiver Lock, not FM/AM.

---

## 12. Tables

### Step sizes (both bands, 10 values, cyclic)
5.0 → 6.25 → 10.0 → 12.5 → 15.0 → 20.0 → 25.0 → 30.0 → 50.0 → 100.0 kHz

### Frequency ranges
- Band A (5): 144.000 → 223.000 → 300.000 → 440.000 → 118.000 (AM, underscore) → back
- Band B (4): 440.000 → 1240.000 (0x12 small-font prefix) → 144.000 → 300.000 → back

### CTCSS/Tone table (38 tones, no 69.3 Hz)
See `tmd700_tag_reference.md` Appendix A.

### DCS codes (101 codes)
See `tmd700_tag_reference.md` Appendix B.

---

## 13. Still Open

**Unidentified BODY→HEAD tags from boot block:** `1`, `[`, `7`, `L`, `M`, `k`, `X`, `Y` (plus contextual `i`, `j`, `0xCC`)

**TO-DO:** Investigate APRS payload parsing — determine whether the RF deck or control head parses the APRS info-field content. TNC is on Band A (144.390 MHz). When single-band Band B mode is active, Band A is suspended and TNC goes offline; use single-band-B mode as a clean baseline before receiving an APRS packet to isolate APRS-specific tags.

---

*For the complete tag reference, capture methodology, and full scenario list, see companion documents `tmd700_tag_reference.md` and `tmd700_capture_scenarios.md`.*
