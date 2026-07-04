# Kenwood TM-D700 Control Head ↔ RF Deck Protocol — Tag Reference

**Last updated:** 2026-06-30
**Source captures:** D700boot.csv, ctcss_test.csv, Scenario1–7 (Band A and B)

This is a standalone reference for every tag observed on the head↔body UART link. For the full hardware investigation and methodology, see `tmd700_protocol_re.md`.

---

## Physical / Framing Quick Reference

- **Baud rate:** 57600, 8N1, idle-high
- **Connector:** J1 (head) / J602 (deck) — 4 wires: 9.65V, GND, TXD, RXD
- **Frame format:** one tag byte + variable-length payload, terminated by `0x0D` (CR); no checksum
- **Idle/keepalive:** bare `0xFF` sent by both sides ~every 1.4s
- **Power-on handshake:** head sends bare `0x0D`; body replies bare `0x0D` ~37ms later

**BODY→HEAD** = transmitted by RF deck, received by control head.
**HEAD→BODY** = transmitted by control head, received by RF deck.

---

## Display Mode Indicator (tag `4`)

The `4` tag signals the current display context. The head uses this to know how to interpret other context-sensitive tags (especially `N`/`O` and `P`/`Q`).

| Value | Meaning |
|-------|---------|
| `40` | Normal VFO/MR display |
| `48` | PM selection mode active |
| `41` | `[F]` function key just pressed (menu hint active) |
| `45` | General encoder-driven list selection (step size, DIM level — any encoder-pick-from-list mode) |
| `46` | Tone/CTCSS/DCS frequency/code selection mode |
| `49` | Transceiver locked |
| `4C` | APRS received-station popup active (accompanies `T` tag; clears to `40`) |
| `4E` | Transceiver locked + [F] pressed (unlock in progress) |

---

## Frequency / Display Payload Encoding

Tags `N`, `O`, `P`, and `Q` are context-sensitive — they carry different data depending on the current display mode (`4` tag value):

| Mode | `N`/`O` carries | `P`/`Q` carries |
|------|----------------|----------------|
| Normal VFO | Frequency (e.g. `0144.390  `) | `0`+channel# or blank |
| Step select (`45`) | Step size (e.g. `  5.0`, `100.0`) | Blank |
| Tone/CTCSS select (`46`) | Tone frequency in Hz (e.g. ` 123.0`) | `8`+tone index# |
| DCS select (`46`) | DCS code 3-digit (e.g. `023`, `125`) | `0` (blank) |

**Frequency separator byte** (between integer and decimal digits) encodes receive mode:
- `0x2E` (`.`) = FM standard, displays as dot
- `0x15` (NAK) = AM receive, displays as underscore `_` (aviation band 118 MHz)

**Frequency prefix byte** (before digit string) encodes leading digits in small font:
- `0x12` (DC2) = display "12" in small font before remaining digits (e.g. `¹²40.000` = 1240.000 MHz, 23cm band)

---

## Confirmed Tags — BODY→HEAD (RF Deck sends, Control Head displays)

### Radio state tags

| Tag | Meaning | Example payload | Notes |
|-----|---------|-----------------|-------|
| `d` | Power-on message / station ID | `HELLO !!` (factory default); `KE4PJW` (Terry's setting, menu 1-1-1) | Carries whatever is programmed at menu 1-1-1 (POWER-ON MSG). Not a separate callsign register. Factory reset restores `HELLO !!`. |
| `N` | VFO A display field | `0144.390  ` (freq); `  5.0` (step); ` 123.0` (tone Hz); `023` (DCS) | Context-sensitive — see encoding table above. Updates on every encoder detent. |
| `R` | VFO A channel/memory name | `0APRS TS ` (memory); `0CALL` (on CALL channel) (memory); blank (VFO mode) | Goes blank when leaving memory mode. Resent on every encoder pulse even when blank. |
| `O` | VFO B display field | `0440.000  ` | Band B equivalent of `N`. Same context-sensitive encoding. |
| `S` | VFO B channel/memory name | `0FRS 10  ` (memory); `0CALL` (on CALL channel) | Band B equivalent of `R`. |
| `P` | VFO A memory/tone display | `0199`=ch.199; `0  1`=ch.1; `1200`=ch.200; `8 18`=tone idx 18; `P<199`=nearest ch when [F] pressed | Prefix `0`=channel 1-199 (right-justified 3 chars); prefix `1`=channel 200+ (e.g. `1200`=ch.200); prefix `8`=tone index. Goes blank in VFO mode. Per-channel state (shift, tone) updates on every encoder click in memory mode. |
| `Q` | VFO B memory/tone display | `0 39`=ch.39; `0 44`=ch.44; `8  1`=tone idx 1 | Band B equivalent of `P`. Same channel number encoding. `Q< 39` pattern when [F] pressed. |
| `V` | Live boot-status / display text | `12           OPENING TNC` → `0` | Carries literal UI strings. Body decides text; head just renders. |
| `@` | Band A tone mode | `0`=off, `1`=Tone, `2`=CTCSS, `3`=DCS | See Appendix A for full tone/DCS tables. |
| `A` | Band B tone mode | `0`=off, `1`=Tone, `2`=CTCSS, `3`=DCS | Band B equivalent of `@`. Confirmed Scenario7_Band_B.csv. |
| `=` | PTT × Control × Display band state | `0`=dual/PTT-A/Ctrl-A; `1`=dual/PTT-B/Ctrl-A; `2`=dual/PTT-A/Ctrl-B; `3`=dual/PTT-B/Ctrl-B; `4`=single-band-A/PTT-A/Ctrl-A; `7`=single-band-B/PTT-B/Ctrl-B | 3-bit field: Bit0(+1)=PTT on Band B; Bit1(+2)=Control on Band B; Bit2(+4)=Single-band display active. Toggled by long-hold VOL A (`0x9D`) or VOL B (`0x9E`). Values 5 and 6 theoretically possible but not yet observed. Confirmed Scenario13_V1.csv. |
| `3` | PM active status | `31`=no PM active (normal); `32`=PM1 active | Part of full state dump on PM recall and PM OFF. Confirmed ScenarioPM_V1.csv. |
| `4` | Display mode indicator | `40`, `41`, `45`, `46` | See Display Mode table above. Also used during frequency range cycling. |
| `B` | Band A TX power level | `B0`=High; `B1`=Medium (boot default); `B2`=Low | Cycle confirmed M→L→H→M: B1→B2→B0→B1. Both bands boot at Medium. Confirmed Scenario12_V1.csv. |
| `C` | Band B TX power level | `C0`=High; `C1`=Medium (boot default); `C2`=Low | Band B equivalent of `B`. Same cycle and encoding. |
| `D` | Band A repeater shift direction | `D0`=simplex, `D1`=+shift, `D2`=−shift | Each memory channel stores its own shift direction — `D` updates on every encoder click in memory mode. Confirmed Scenario8 and Scenario16. |
| `E` | Band B repeater shift direction | `E0`=simplex, `E1`=+shift, `E2`=−shift | Band B equivalent of `D`. **Corrects earlier hypothesis** that `E` was a "default-range flag." Confirmed Scenario8_V1.csv. |
| `F` | Band A REV / ASC status | `F0`=normal; `F1`=REV active (N shows offset/input freq); `F2`=ASC active (N reverts to simplex freq) | 3-state field. REV → F1; long-hold REV (ASC) → F2; cancel → F0 directly. Confirmed Scenario9 and Scenario10. |
| `G` | Band B REV / ASC status | `G0`=normal; `G1`=REV active; `G2`=ASC active | Band B equivalent of `F`. Same 3-state encoding. Confirmed Scenario10_V1.csv. |
| `5` | Mute status | `50`=mute OFF (normal); `52`=mute ON | Retroactively explains `50` appearing in PM recall dumps and boot state dump. Confirmed ScenarioMUTE_V1.csv. |
| `H` | Band A menu/selection display | `H?30` in selection mode; `H000` on exit | `0x3F`=cursor/selection indicator displayed while in menu mode. |
| `I` | Band B menu/selection display | `I?30` in selection mode; `I000` on exit | Band B equivalent of `H`. |
| `J` | Band A RX/TX status | `J0`=squelch closed; `J1`=squelch open (signal present); `J2`=transmitting | 3-state. During TX, body also sends L tag showing TX power level. Confirmed ScenarioTX_V1.csv. |
| `K` | Band B BUSY indicator | `K1`=squelch open; `K0`=squelch closed | Band B equivalent of `J`. |
| `E` | Default-range flag (tentative) | `E1`=on home range; `E0`=cycled away | Appeared during frequency range cycling — needs further confirmation. |

| `2` | Display state indicator | `20`=single-band display mode; `21`=normal dual-band VFO/MR; `22`=menu mode | Confirmed Scenario13_V1.csv. Boot dump appearance sets initial display state. |
| `0` | Power state indicator | `00`=standby (DC applied, last state OFF); `01`=powered on and active | Body checks stored last-power-state in SPI EEPROM on DC application. If last OFF → `00` (standby); head must send `[0x0D]` (power button) to trigger `01`+state dump. If last ON → `01` immediately, state dump follows ~100ms later without button press. The `[0x0D]` handshake only occurs on soft power-on via button. Confirmed powerapplied-thenpresspower.csv and powerapplied-laststatepowedon.csv. |
| `1` | Unknown (boot state) | `11` observed in every boot dump, after `d` tag | Payload always `1` in all captures. Appears between power-on message and mute status. Meaning unclear — possibly display layout or configuration flag. Confirmed in factory-default boot. |
| `;` | Illumination / DIM level | `;0`=DIM OFF; `;1`=DIM level 1 (boot default); `;2`=DIM 2; `;3`=DIM 3; `;4`=DIM 4 | Confirmed Scenario17_V1.csv. DIM adjusted via [F]+[OK/CTRL]. Retroactively resolves boot burst `0x80` payload `'1'` = DIM level 1 at startup. |
| `j` | Polarity/deviation status (tentative) | `j0` observed when menu 1-3 "POSITIVE" saved | Appears in boot block. Likely deviation polarity: j0=positive, j1=negative (unconfirmed). Confirmed present ScenarioMenu1-1to1-3. |
| `k` | Mode setting status (tentative) | `k0` observed when menu 1-5 "MODE1" saved | Lowercase — distinct from `K` (Band B RX/TX). Appears in boot block. Linked to mode configuration item 1-5. Confirmed present ScenarioMenu1-1to1-3. |
| `e` | DEMO mode indicator | `e1`=demo mode active (`e0` presumed = normal, not yet observed) | Body sends `e1` right after the boot state dump when the head requested demo mode (head sends `0xA7` = `[F]` held at power-on). Lowercase — distinct from any uppercase tag. The demo itself (graphics screen, DIM cycling, video-invert) runs **entirely in the head** with no further tag exchange. Confirmed 2026-07-04 via P2 MITM. |
| `T` | APRS received-station popup | `T10[0x06]KM4BJZ-2[0x00]  ...Grundy County ARES...`; `T0`=clear | Carries a decoded APRS packet for on-screen display. Format: `T10` + `0x06` (field-start, same marker as text-edit) + station callsign + `0x00` + comment/status text (fixed-width, space-padded to display columns; `0x00` pads, `0x7F` seen for special glyphs). Accompanied by display-mode `4C`; `T0` + `40` clears the popup. Confirmed 2026-07-04 via P2 MITM on live 144.390 traffic. |
| `f` | TX start indicator | *(empty payload)* | Bare tag sent by body at the very start of every transmit event, immediately before the TX-state burst (J2/K2, L/M power level). Confirmed ScenarioTX_V1.csv. |
| `p` | GPS/position data display | `p00B400   1: [lat/lon 0xFF=unlocked][0xDF=deg sym] OK51OE` | Raw APRS coordinate display in menu 3-4. 0xFF bytes = no GPS lock; 0xDF = degree symbol. Hemisphere may show S instead of N when unprogrammed (GPS not locked). Confirmed ScenarioMenu3. |
| `z` | APRS beacon comment/message | `z004008 * 1: Life is good !!` (browse); edit uses 0x06/0x14/0x0F cursor encoding | Lowercase z, distinct from uppercase Z. Carries APRS beacon text in menu 3-9. 29-char field. Confirmed ScenarioMenu3. |
| `b` | Menu navigation / position | `0134200`=Band A,bank1,L1=3,L2=4,focus=2 | 7-char: `[band][bank][L1][L2][focus][sub][cursor]`. Focus: 0=top, 1=L1, 2=L2-browse (c=stored value), 3=value-edit, 4=text-edit (sub/cursor encode field and position). Positions 6-7 are non-zero in text-edit mode. Menu map: L1=1→(1-1=MY CALLSIGN text,1-2=LEVEL 9,1-3=POSITIVE polarity,1-4=ON,1-5=MODE1); L1=2→(2-1=KeyBeep,2-2=ON/OFF,2-3=MODE); L1=3→(3-1=136-199MHz,3-2=OFF,3-3=OFF,3-4=FM/AM,3-5=OFF); L1=4→(4-1=ON,4-2=OFF); L1=5→(5-1=APRS path text,5-2=FAST beacon rate,5-3=500ms delay); L1=6→(6-1=A/data band,6-2=DATA(RX)BAND,6-3=30:55 timer,6-4=DTMF ID,6-5=UTC-5:00); L1=7→(7-1=0.60MHz offset,7-2=ON,7-3=CALL,7-4=OFF,7-5=OFF,7-6=OFF); L1=8→(8-1=A/B,8-2=MR,8-3=VFO,8-4=CALL,8-5=OFF,8-6=OFF); L1=9→(9-1=TIME,9-2=MODE2:61ch,9-3=ON,9-4=10min,9-5=9600bps,9-6=1200bps,9-7=NO); L1=A→(A-1=000,A-2=OFF,A-3=OFF); BANK2-group0→(1=KE4PJW,2/4/6=WHITE,3/5=blank,7=EXECUTING,8=CONFIRMING,9=OFF); BANK3-APRS(3-1to3-P)→(1=KE4PJW-9,2=NMEA,3=9DIGITS NMEA,4=GPS[p tag],5=OFF,6=In Service,7=OFF,8=3007,9=beacon comment[z tag],A=1/1,B=WIDE2-2,C=AUTO,D=1min,E=APK101,F=ALL,G=mile,H=degF,I=A,J=1200bps,K=OFF,L=RELAY,M=OFF,N/O=blank,P=ALL,QST,CQ,KWD). L1 field uses HEX (groups 1-9 then A=10). c prefix in text-edit=field length (c009=9-char,c010=10-char,c015=15-char). c000=browse,c001=saved,c002=2nd save. Sub-field IDs also hex (A,D observed). Confirmed Menu1-7to1-9,Menu1-A-to-2-9. |
| `c` | Menu value display | `000                FM`; `001      136- 199 MHz`; `009[ctrl]text`=text-edit 9-char field; `EXECUTING`; `CONFIRMING` | Prefix `000`=browse; `001`=saved; `002`=2nd save; `0NN`=text-edit where NN=field character length (009=9-char,010=10-char,015=15-char). Values can be commands: `EXECUTING`=active command running, `CONFIRMING`=awaiting confirmation. |

| `L` | Band A signal/power meter | RX (J1): `L00`=none...`L70`=full S-meter deflection. TX (J2): `L20`=Low power, `L50`=Medium, `L70`=High | Dual-purpose: S-meter during RX, TX power meter during TX. 2-digit ASCII decimal, ~100-200ms updates. `L00`≠`J0` (squelch hysteresis). Confirmed ScenarioBandA_SMETER and ScenarioTX. |
| `M` | Band B signal/power meter | RX (K1): `M00`=none...`M70`=full S-meter. TX (K2): `M20`=Low power, `M50`=Medium, `M70`=High | Dual-purpose same as `L`. Band B equivalent. Confirmed ScenarioBandB_SMETER and ScenarioTX. |
| `Z` | Single/dual-band display indicator | `Z0`=single-band mode active; `Z1`=dual-band display restored | Only observed for Band B single-band toggle. When Band B single-band is activated, Band A (which carries the TNC on 144.390 MHz) is suspended — on returning to dual-band (`Z1`), Band A re-enables and the TNC must re-initialize (`V` shows "OPENING TNC", tag `6` also fires). Band A single-band toggle does not trigger Z because Band A remains active. Confirmed Scenario13_V1.csv. |

### Structural / special bytes (BODY→HEAD)

| Byte | Meaning | Notes |
|------|---------|-------|
| `0x0D` bare | Power-on sync reply (button press path only) | Body replies ~37ms after head sends bare 0x0D (power button pressed). NOT sent when body auto-resumes to powered state (last state ON) — in that case body goes directly to tag `0` value `01`. |
| `0xFF` bare | Idle keepalive | Sent ~every 1.4s when link is otherwise quiet. |

---

## Confirmed Tags — HEAD→BODY (Control Head sends, RF Deck processes)

### Button keycodes

All physical button presses send a high-bit-set byte (0x80+). The RF deck interprets the same keycode differently depending on current context (e.g. 0x8C = CTRL normally, OK/confirm in menu mode; 0x87 = [F] normally, ESC/cancel in menu mode).

**Keycode modifier bits (confirmed 2026-07-04):** the base short-press code is `0x8x`. Two modifier bits layer on top of it:
- `| 0x10` → `0x9x` = **long-hold** of that button
- `| 0x20` → `0xAx` = that button **held while powering on**

This unifies the previously-listed long-holds and the new codes: `0x99`=REV long-hold (`0x89|0x10`), `0x9D`/`0x9E`=VOL A/B long-hold (`0x8D`/`0x8E |0x10`), `0x97`=`[F]` long-hold (`0x87|0x10`), `0xA7`=`[F]` held at power-on (`0x87|0x20`, enters demo). Other combinations are predictable (e.g. `0x92` would be MNU long-hold) but not yet individually confirmed.

| Tag | Physical button | Normal press meaning | [F]+ shifted meaning |
|-----|----------------|---------------------|---------------------|
| `0x81` | PM | Enter PM selection UI; in UI: [Tone]=select PM1, [F]=PM OFF (if PM active) or cancel | **Confirmed** ScenarioPM_V1.csv. |
| `0x82` | MNU | Open main menu | **Confirmed** Scenario11_V1.csv. Previous guess of CALL was wrong — CALL keycode still unknown. |
| `0x83` | VFO | Enter VFO mode | — |
| `0x84` | MR | Enter memory recall mode | — |
| `0x85` | CALL | Toggle CALL channel (jumps to/from configured CALL freq); CALL channel carries its own shift setting | **Confirmed** ScenarioCALL_V1.csv. |
| `0x86` | MHz | FM/AM toggle or lock (context-dependent); [F]+[0x86]=Transceiver Lock/Unlock | **Confirmed** Scenario15_V1.csv. |
| `0x87` | F | Function shift; ESC/cancel in menus | — |
| `0x88` | Tone cycle | Cycle tone mode (@/A) | T.sel — enter tone/DCS selection |
| `0x89` | REV / SHIFT | Reverse toggle (without [F]); cycle shift direction (after [F]) | Key-down fires immediately. Body responds F1/G1. If held ~930ms, head also sends `0x99`. Confirmed Scenario8 and 9. |
| `0x99` | REV long-hold | ASC (Automatic Simplex Checker) activate | Sent ~930ms after `0x89` if key still held. Head times the hold; body responds F2/G2 and reverts N/O to simplex freq. Confirmed Scenario10_V1.csv. |
| `0x8A` | LOW/STEP | Power level change | Step size selection |
| `0x8B` | MUTE | Toggle mute on/off | **Confirmed** ScenarioMUTE_V1.csv. |
| `0x8C` | CTRL / OK | CTRL (shift control band) | OK/confirm in menus |
| `0x8D` | VOL A (rotate=volume, **press**=band select) | Select Band A / move PTT to Band A | — |
| `0x8E` | VOL B (rotate=volume, **press**=band select) | Select Band B / move PTT to Band B | — |
| `0xA7` | F held at power-on | Enter DEMO mode | Sent once, immediately after the power-on handshake, when `[F]` is held down while powering on the head. Body replies `e1` (demo active). Encoding: `0xA7 = 0x87 ([F]) \| 0x20` — the head flags the F-held-at-boot condition with a distinct variant of the normal `[F]` code. Confirmed 2026-07-04 via P2 MITM. |
| `?` | PM | Unknown keycode | Unknown |
| `?` | MNU | Unknown keycode | Unknown |
| `0xB0` | End-of-burst marker | Sent at close of every button-press burst | Not a button — constant structural byte. |

### Encoder

| Tag | Payload | Meaning |
|-----|---------|---------|
| `0x8F` | `0x01` | Tuning encoder one click clockwise (up) |
| `0x8F` | `0xFF` | Tuning encoder one click counter-clockwise (down) |
| `0x8F` | `0x02` | Tuning encoder two clicks clockwise (fast spin) |

The body responds to each `0x8F` within ~2ms, sending the updated display field set (`N`/`R`/`P` or `O`/`S`/`Q`).

### Analog control knobs (HEAD→BODY)

All four knobs send their current position as a raw hex byte payload on every detent. The RF deck processes silently with no acknowledgment for volume (no display indicator); squelch changes may trigger BUSY indicator updates.

| Tag | Control | Range | Resolution | Notes |
|-----|---------|-------|-----------|-------|
| `0xC0` | SQL A (Band A squelch) | `0x00`–`0x1F` | 32 levels | Body responds with `J1`/`J0` BUSY when squelch opens/closes |
| `0xC1` | VOL A (Band A volume) | `0x00`–`0x3F` | 64 levels | Body silently adjusts RF deck audio amp — no response (no volume indicator on radio) |
| `0xC2` | SQL B (Band B squelch) | `0x00`–`0x1F` | 32 levels | Body responds with `K1`/`K0` BUSY |
| `0xC3` | VOL B (Band B volume) | `0x00`–`0x3F` | 64 levels | Body silently adjusts RF deck audio amp |

### Boot control position report

At power-on, before any user interaction, the head sends the following burst reporting all current hardware control positions so the body knows initial knob states:

| Tag | Boot value observed | Meaning |
|-----|---------------------|---------|
| `0x80` | `'1'` (ASCII) | DIM level 1 at boot — **CONFIRMED** by Scenario17_V1.csv. Head reports current DIM level to body at startup alongside SQL/VOL positions. |
| `0xC0` | `0x03` | SQL A at boot = level 3 |
| `0xC1` | `0x17` | VOL A at boot = level 23 |
| `0xC2` | `0x0F` | SQL B at boot = level 15 |
| `0xC3` | `0x1A` | VOL B at boot = level 26 |

### Structural / special bytes (HEAD→BODY)

| Byte | Meaning |
|------|---------|
| `0x0D` bare | Power-on sync — first byte head transmits at startup |
| `0xFF` bare | Idle keepalive ~every 1.4s |

---

## Paired Band A/B Tag Pattern

All radio state fields come in symmetric pairs using adjacent alphabetic tags:

| Function | Band A | Band B |
|----------|--------|--------|
| TX power | `B` | `C` |
| Tone mode | `@` | `A` |
| Shift direction | `D` | `E` |
| REV status | `F` | `G` |
| Menu display field | `H` | `I` |
| RX/TX status (0=closed,1=RX,2=TX) | `J` | `K` |
| S-meter level | `L` | `M` |

---

## Unidentified Tags (BODY→HEAD)

Observed in boot dump or scenario captures; meaning not yet confirmed:

| Tag | Example payload | Where seen | Notes |
|-----|-----------------|------------|-------|
| `0` | `1` | Boot | — |
| `i` | (blank) | Boot | — |
| `0xCC` | `8` | Boot | Non-ASCII tag |
| `1` | `1` | Boot settings block | — |
| `[` | `0` / `4` | Boot settings block | **Likely resolved — TNC data rate / packet mode:** `[0`=1200 baud, `[4`=9600 baud. Flipped 0→4 the instant the TNC baud was changed to 9600 and persisted across reboots (boot-latched). Drives the `1200`/`9600` status-row annunciator. NOTE: that 9600 change also destabilized the deck (see session note) so needs a clean single-toggle re-confirm. |
| `<` | `8` | ScenarioMenu (save of menu 1-2 LEVEL 9) | Standalone tag (distinct from `<` as payload char in P<199); fires on menu item save; meaning unclear |
| `7` | `00` | Boot settings block | Static through TNC enable; likely APRS/packet-RX state (needs live packet) |
| `X` | `000` | Boot settings block | Static through TNC enable; likely APRS/packet-RX state (needs live packet) |
| `Y` | `000` | Boot | Static through TNC enable; likely APRS/packet-RX state (needs live packet) |
| ~~`6`~~ | — | — | **RESOLVED — see confirmed tags: `6` = TNC status** (`6001` fired when TNC opened, 2026-07-04) |
| ~~`m`~~ | — | — | **RESOLVED — see confirmed tags: `m` = TNC status** (`m00` fired when TNC opened, 2026-07-04) |

---

## Summary Table — Confirmed Tags Only

| Tag | Direction | Meaning |
|-----|-----------|---------|
| `d` | BODY→HEAD | Callsign / display identity |
| `N` | BODY→HEAD | VFO A display field (freq/step/tone Hz/DCS code — context-sensitive) |
| `R` | BODY→HEAD | VFO A channel/memory name |
| `O` | BODY→HEAD | VFO B display field (same encoding as N) |
| `S` | BODY→HEAD | VFO B channel/memory name |
| `P` | BODY→HEAD | VFO A memory channel / tone index (prefix-encoded) |
| `Q` | BODY→HEAD | VFO B memory channel / tone index |
| `V` | BODY→HEAD | Live boot-status / display text |
| `@` | BODY→HEAD | Band A tone mode (0=off, 1=T, 2=CT, 3=DCS) |
| `A` | BODY→HEAD | Band B tone mode (0=off, 1=T, 2=CT, 3=DCS) |
| `=` | BODY→HEAD | PTT × Control × Display state (3-bit field, 8 states; values 0-4,7 observed) |
| `0` | BODY→HEAD | Power state (00=standby/DC-applied, 01=powered on) |
| `1` | BODY→HEAD | Boot state flag (always 1; appears after d tag in state dump) |
| `;` | BODY→HEAD | Illumination/DIM level (;0=OFF, ;1=DIM1/boot, ;2=DIM2, ;3=DIM3, ;4=DIM4) |
| `2` | BODY→HEAD | Display state (20=single-band, 21=dual-band VFO, 22=menu) |
| `3` | BODY→HEAD | PM active status (31=normal, 32=PM1 active) |
| `4` | BODY→HEAD | Display mode indicator |
| `5` | BODY→HEAD | Mute status (50=off, 52=on) |
| `H` | BODY→HEAD | Band A menu/selection display field |
| `I` | BODY→HEAD | Band B menu/selection display field |
| `F` | BODY→HEAD | Band A REV/ASC status (F0=normal, F1=REV, F2=ASC) |
| `G` | BODY→HEAD | Band B REV/ASC status (G0=normal, G1=REV, G2=ASC) |
| `B` | BODY→HEAD | Band A TX power (B0=High, B1=Medium/boot, B2=Low; cycle M→L→H→M) |
| `C` | BODY→HEAD | Band B TX power (same encoding as B) |
| `D` | BODY→HEAD | Band A repeater shift direction (0=simplex,1=+shift,2=−shift) |
| `E` | BODY→HEAD | Band B repeater shift direction (same encoding as D) |
| `j` | BODY→HEAD | Polarity/deviation status (j0=positive; confirmed linked to menu 1-3) |
| `k` | BODY→HEAD | Mode setting status (k0 confirmed linked to menu 1-5 MODE1; distinct from K) |
| `f` | BODY→HEAD | TX start indicator (bare tag, empty payload; precedes TX burst) |
| `e` | BODY→HEAD | DEMO mode indicator (e1=demo active; demo is head-local after this) |
| `6` | BODY→HEAD | TNC status (fires on TNC open; `6001` seen with "OPENING TNC"; `6031` at boot) |
| `m` | BODY→HEAD | TNC status (fires on TNC open; `m00` seen with "OPENING TNC"; `m16` at boot) |
| `T` | BODY→HEAD | APRS received-station popup (callsign + comment; display-mode 4C; T0 clears) |
| `p` | BODY→HEAD | GPS/position data display (APRS menu 3-4; 0xFF=no lock) |
| `z` | BODY→HEAD | APRS beacon comment/text (menu 3-9; 29-char; distinct from Z uppercase) |
| `b` | BODY→HEAD | Menu navigation position (7-char structured path) |
| `c` | BODY→HEAD | Menu value display field |
| `J` | BODY→HEAD | Band A RX/TX status (J0=closed, J1=RX/open, J2=TX) |
| `K` | BODY→HEAD | Band B RX/TX status (K0=closed, K1=RX/open, K2=TX) |
| `L` | BODY→HEAD | Band A S-meter level (L00=none, L70=full; ~100-200ms updates) |
| `M` | BODY→HEAD | Band B S-meter level — same encoding as L (M00=none, M70=full) |
| `Z` | BODY→HEAD | Single/dual-band display indicator (Z0=single-band, Z1=dual-band restored) |
| `0x83` | HEAD→BODY | VFO button |
| `0x84` | HEAD→BODY | MR (Memory) button |
| `0x85` | HEAD→BODY | CALL button (toggle CALL channel) |
| `0x86` | HEAD→BODY | MHz button ([F]+0x86 = Transceiver Lock/Unlock) |
| `0x87` | HEAD→BODY | [F] function key / ESC in menus |
| `0x88` | HEAD→BODY | Tone cycle button / T.sel after [F] |
| `0x89` | HEAD→BODY | REV/SHIFT physical button (REV normally; SHIFT direction after [F]) |
| `0xA7` | HEAD→BODY | [F] held at power-on — enter DEMO mode (body replies e1; 0xA7 = 0x87\|0x20) |
| `0x97` | HEAD→BODY | [F] long-hold (0x87\|0x10); seen giving display-mode `42` |
| `0x99` | HEAD→BODY | REV long-hold — ASC activate (~930ms after 0x89) |
| `0x9D` | HEAD→BODY | VOL A long-hold — single-band display toggle Band A |
| `0x9E` | HEAD→BODY | VOL B long-hold — single-band display toggle Band B |
| `0x8A` | HEAD→BODY | LOW/STEP button |
| `0x8C` | HEAD→BODY | CTRL button / OK in menus |
| `0x8D` | HEAD→BODY | VOL A press (Band A select) |
| `0x8E` | HEAD→BODY | VOL B press (Band B select) |
| `0x8F` | HEAD→BODY | Tuning encoder (payload = step count/direction) |
| `0xC0` | HEAD→BODY | SQL A position (0x00–0x1F, 32 levels) |
| `0xC1` | HEAD→BODY | VOL A position (0x00–0x3F, 64 levels) |
| `0xC2` | HEAD→BODY | SQL B position (0x00–0x1F, 32 levels) |
| `0xC3` | HEAD→BODY | VOL B position (0x00–0x3F, 64 levels) |
| `0x0D` bare | both | Power-on sync byte |
| `0xFF` bare | both | Idle/keepalive heartbeat |
| `0xB0` bare | HEAD→BODY | End-of-burst marker |

**Confirmed: 42 BODY→HEAD tags, 24 HEAD→BODY tags/codes, 3 structural bytes.**

*New 2026-07-04 (P2 MITM live decode):*
- *BODY→HEAD: `e` (demo indicator); `6` and `m` (TNC status — fire on TNC open, were previously unidentified boot-block tags).*
- *HEAD→BODY: `0xA7` ([F] held at power-on → demo), `0x97` ([F] long-hold) — and the general **keycode modifier-bit scheme**: `|0x10`=long-hold, `|0x20`=held-at-power-on (see Button keycodes).*
- *Demo mode is head-local (graphics, DIM cycle, video-invert), establishing the head LCD supports video inversion + head-driven DIM.*
- *APRS callsign = menu 3-1 (default `NOCALL`), a register distinct from the `d` power-on message. Text-edit `c` payload: `c0NN`=cursor at position NN, `c5NN`=cursor advanced right via `0x8A`; field wrapped in `0x06 … 0x14(pad) … 0x0F` — this supersedes the earlier "c0NN = field length" reading.*
- *`T` = APRS received-station popup (callsign + comment), with display-mode `4C`; confirmed on live 144.390 RX.*
- *Still open: `[`, `7`, `X`, `Y` — did NOT move on TNC-enable OR live packet RX; only ever in the boot dump. Now believed to be APRS/TNC config latched at boot (beacon/digipeat/path/etc.), re-sent only when that setting is changed. Next: toggle those config items.*

---

## Appendix A — Complete CTCSS/Tone Table (38 tones, Kenwood standard)

Used for both Tone (T) and CTCSS (CT) modes. Index is the value in `P8 NN`/`Q8 NN` during selection. Note: 69.3 Hz is not supported on this radio.

| Idx | Hz | Idx | Hz | Idx | Hz | Idx | Hz |
|-----|----|-----|----|-----|----|-----|----|
| 1 | 67.0 | 11 | 97.4 | 21 | 136.5 | 31 | 192.8 |
| 2 | 71.9 | 12 | 100.0 | 22 | 141.3 | 32 | 203.5 |
| 3 | 74.4 | 13 | 103.5 | 23 | 146.2 | 33 | 210.7 |
| 4 | 77.0 | 14 | 107.2 | 24 | 151.4 | 34 | 218.1 |
| 5 | 79.7 | 15 | 110.9 | 25 | 156.7 | 35 | 225.7 |
| 6 | 82.5 | 16 | 114.8 | 26 | 162.2 | 36 | 233.6 |
| 7 | 85.4 | 17 | 118.8 | 27 | 167.9 | 37 | 241.8 |
| 8 | 88.5 | 18 | 123.0 | 28 | 173.8 | 38 | 250.3 |
| 9 | 91.5 | 19 | 127.3 | 29 | 179.9 | | |
| 10 | 94.8 | 20 | 131.8 | 30 | 186.2 | | |

---

## Appendix B — Complete DCS Code List (101 codes)

Captured by scrolling through all codes during Scenario 7 Band B. Displayed in `N`/`O` as a 3-digit code during DCS selection mode.

```
023 025 026 031 032 036 043 047 051 053 054 065 071 072 073 074
114 115 116 122 125 131 132 134 143 145 152 155 156 162 165 172
205 212 223 226 243 244 245 246 251 252 255 261 263 265 266 271 274
306 311 315 325 331 332 343 346 351 356 364 365 371
411 412 413 423 432 445 446 452 454 455 462 464 465 466
503 506 516 523 526 532 546 565
606 612 624 627 631 632 654 662 664
703 712 723 731 732 734 743 754
```
