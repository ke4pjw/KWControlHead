# TM-D700 Menu Map — head-side name/value table

The RF deck only sends the menu **number** (tag `b`) and the current **value** (tag `c`); the
**menu category and item names below are supplied by the head**, keyed by menu number. This table
is therefore the data source the replacement-head renderer needs to draw the menu screen:

```
<category>          <number>     ← top line   (category name + number, from b + this table)
▶<item name>                     ← item line  (item name, from b + this table)
              <value>            ← value line (from c)
ESC BACK   ↑   ↓    OK           ← menu-mode soft-keys (head-generated)
```

Source: TM-D700 instruction manual "MENU CONFIGURATION" table (pp.23–27), cross-checked against
our reverse-engineered `b`-tag menu map (`tmd700_tag_reference.md`).

**Numbering:** Group 1 (RADIO) is **3-level** (`1-L2-L3`); groups 2/3/4 are **2-level** (`G-L2`).
Level indices run `1`..`9` then `A`,`B`,… (single hex-ish char), matching the `b`-tag encoding.
`(ref)` = value is free-form / described on a manual reference page. Items marked *(US/Can)* exist
only on U.S./Canada units.

---

## Group 1 — RADIO  (3-level)

### 1-1 DISPLAY
| No. | Item | Selections | Default |
|-----|------|-----------|---------|
| 1-1-1 | Power-ON Message | text | `HELLO !!` |
| 1-1-2 | Contrast | Level 1–16 | Level 8 |
| 1-1-3 | Reverse mode | Positive / Negative | Positive |
| 1-1-4 | Auto Dimmer Change | ON / OFF | OFF |
| 1-1-5 | Multi-function button | Mode 1 / 2 / 3 | Mode 1 |

### 1-2 AUDIO
| No. | Item | Selections | Default |
|-----|------|-----------|---------|
| 1-2-1 | Beep volume | Level 1–7 / OFF | Level 5 |
| 1-2-2 | Key Beep | ON / OFF | ON |
| 1-2-3 | Speaker configuration | Mode 1 / 2 | Mode 1 |
| 1-2-4 | Voice Synthesizer *(VS-3 opt.)* | English / APRS only / Japanese / OFF | OFF |
| 1-2-5 | Voice volume *(VS-3 opt.)* | Level 1–7 | Level 5 |

### 1-3 TX/RX
| No. | Item | Selections | Default |
|-----|------|-----------|---------|
| 1-3-1 | Programmable VFO | (ref) | — |
| 1-3-2 | S-meter Squelch | ON / OFF | OFF |
| 1-3-3 | Squelch hang time | 125 / 250 / 500 msec / OFF | OFF |
| 1-3-4 | FM/AM mode | FM / AM | (ref) |
| 1-3-5 | Advanced Intercept Point | ON / OFF | OFF |
| 1-3-6 | TX/RX deviation *(D700E only)* | Wide / Narrow | Wide |

### 1-4 MEMORY
| No. | Item | Selections | Default |
|-----|------|-----------|---------|
| 1-4-1 | Auto PM Channel Store | ON / OFF | ON |
| 1-4-2 | Channel Display | ON / OFF | OFF |
| 1-4-3 | Memory Channel Lockout | ON / OFF | OFF |
| 1-4-4 | Memory channel name | text | — |

### 1-5 DTMF
| No. | Item | Selections | Default |
|-----|------|-----------|---------|
| 1-5-1 | Number Store | (ref) | — |
| 1-5-2 | TX speed | Fast / Slow | Fast |
| 1-5-3 | Pause | 100 / 250 / 500 / 750 / 1000 / 1500 / 2000 msec | 500 msec |

### 1-6 TNC
| No. | Item | Selections | Default |
|-----|------|-----------|---------|
| 1-6-1 | Data band | (ref) | Band A |
| 1-6-2 | DCD sense | A & B bands / Data (RX) band | Data (RX) band |
| 1-6-3 | Time | (ref) | — |
| 1-6-4 | Date | (ref) | — |
| 1-6-5 | Time zone | (ref) | — |

### 1-7 REPEATER
| No. | Item | Selections | Default |
|-----|------|-----------|---------|
| 1-7-1 | Offset frequency | 0.00–29.95 MHz (50 kHz steps) | (ref) |
| 1-7-2 | Automatic Repeater Offset | ON / OFF | ON |
| 1-7-3 | Call Button Function | Call / 1750 Hz TX | Call |
| 1-7-4 | TX Hold | ON / OFF | OFF |
| 1-7-5 | Repeater Hold *(US/Can)* | ON / OFF | OFF |
| 1-7-6 | Repeater function *(US/Can)* | Locked-band / Cross-band / OFF | OFF |

### 1-8 MIC
| No. | Item | Selections | Default |
|-----|------|-----------|---------|
| 1-8-1 | Mic PF Key | (ref) | A/B |
| 1-8-2 | Mic MR Key | (ref) | MR |
| 1-8-3 | Mic VFO Key | (ref) | VFO |
| 1-8-4 | Mic CALL Key | (ref) | CALL *(D700E: 1750 Hz Tone)* |
| 1-8-5 | Microphone Control | ON / OFF | OFF |
| 1-8-6 | DTMF Monitor | ON / OFF | OFF |

### 1-9 AUX
| No. | Item | Selections | Default |
|-----|------|-----------|---------|
| 1-9-1 | Scan Resume | Time-Operated / Carrier-Operated / Seek | Time-Operated |
| 1-9-2 | Number of Channels for Visual Scan | 31 / 61 / 91 / 181 | 61 |
| 1-9-3 | Automatic Power Off (APO) | ON / OFF | OFF |
| 1-9-4 | Time-Out Timer (TOT) | 3 / 5 / 10 minutes | 10 minutes |
| 1-9-5 | COM port | 9600 / 19200 / 38400 / 57600 bps | 9600 bps |
| 1-9-6 | Data port | 1200 / 9600 bps | 1200 bps |
| 1-9-7 | Reset | (ref) | — |

### 1-A REMOTE CON  *(US/Can)*
| No. | Item | Selections | Default |
|-----|------|-----------|---------|
| 1-A-1 | Secret code | (ref) | 000 |
| 1-A-2 | Acknowledgement | ON / OFF | OFF |
| 1-A-3 | Remote Control | ON / OFF | OFF |

---

## Group 2 — SSTV  (2-level)

| No. | Item | Selections | Default |
|-----|------|-----------|---------|
| 2-1 | My call sign | (ref) | — |
| 2-2 | Color for call sign | White / Black / Blue / Red / Magenta / Green / Cyan / Yellow | White |
| 2-3 | Message | (ref) | — |
| 2-4 | Color for message | (8 colors, as 2-2) | White |
| 2-5 | RSV report | (ref) | — |
| 2-6 | Color for RSV report | (8 colors, as 2-2) | White |
| 2-7 | Superimposition Execute | (ref) | — |
| 2-8 | SSTV mode | (ref) | — |
| 2-9 | VC-H1 Control | ON / OFF | OFF |

---

## Group 3 — APRS  (2-level)

| No. | Item | Selections | Default |
|-----|------|-----------|---------|
| 3-1 | My call sign | (ref) | — |
| 3-2 | GPS receiver | Not used / NMEA / NMEA96 | Not used |
| 3-3 | Waypoint | (ref) | OFF |
| 3-4 | My position | (ref) | — |
| 3-5 | Position Ambiguity | 1 / 2 / 3 / 4 digits / OFF | OFF |
| 3-6 | Position comment | (ref) | Off Duty |
| 3-7 | Reception restriction distance | 10–2500 (steps of 10) / OFF | OFF |
| 3-8 | Station icon | (ref) | — |
| 3-9 | Status text | (ref) | — |
| 3-A | Status text transmit rate | (ref) | OFF |
| 3-B | Packet path | (ref) | RELAY,WIDE |
| 3-C | Packet transmit method | Manual / PTT / Auto | Manual |
| 3-D | Packet transmit interval | 0.2 / 0.5 / 1 / 2 / 3 / 5 / 10 / 20 / 30 minutes | 3 minutes |
| 3-E | Group code | (ref) | APK101 |
| 3-F | Beep | Mine / All new / All / OFF | All |
| 3-G | Unit for distance | Mile / Kilometer | Kilometer *(US/Can: Mile)* |
| 3-H | Unit for temperature | °F / °C | °C *(US/Can: °F)* |
| 3-I | Data band | (ref) | Band A |
| 3-J | Packet transfer rate | 1200 / 9600 bps | 1200 bps |
| 3-K | Digipeater | ON / OFF | OFF |
| 3-L | Digipeating path | (ref) | RELAY |
| 3-M | Auto Answer Reply | ON / OFF | OFF |
| 3-N | Reply message | (ref) | — |
| 3-O | Bulletin group | (ref) | — |
| 3-P | Message group | (ref) | — |

---

## Group 4 — SKY CMD  *(US/Can)*  (2-level)

| No. | Item | Selections | Default |
|-----|------|-----------|---------|
| 4-1 | Commander call sign | (ref) | — |
| 4-2 | Transporter call sign | (ref) | — |
| 4-3 | Tone frequency | (ref) | 88.5 Hz |
| 4-4 | Sky Command mode | Commander / Transporter / OFF | OFF |

---

## Notes cross-linking to the protocol RE

- **`1-9-6` Data port (1200/9600 bps)** and **`3-J` Packet transfer rate** are the over-air packet
  rate — changing to 9600 is what set our `[` tag to `[4`. (`1-9-5` COM port is the *PC* port rate,
  separate.)
- **`1-A` REMOTE CON → `1-A-3` Remote Control (ON/OFF)** is the source of the `S…REMOTE CON`
  VFO-B display we chased; a Kenwood remote-control feature, not a fault.
- **`4-4` Sky Command mode → Commander / Transporter (OFF)** is the "SKYTRP" (SkyCommand Transporter)
  mode. Both this and `1-A-3` put the radio into a locked-down "goofy" state for normal APRS use.
- The APRS group `3-1`…`3-P` matches the reverse-engineered `b`-tag menu map exactly
  (`3-1` MY CALLSIGN, `3-4` GPS/`p` tag, `3-9` status text/`z` tag, `3-B` WIDE path, etc.).
