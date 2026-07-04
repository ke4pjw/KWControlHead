# Kenwood TM-D700 Capture Scenarios — Radio Features

**Purpose:** A set of short (≤30 second), self-contained logic-analyzer capture scenarios for systematically identifying more protocol tags. Each is based on a documented TM-D700E radio feature, deliberately excludes anything TNC/APRS/GPS-related, and follows the same format that worked well for the CTCSS/tone test: one continuous capture, narrate each action as you do it, pause 2–3 seconds between discrete steps so activity bursts stay visually separated in the timeline.

**Sourcing note:** scenarios marked **(D700-confirmed)** come directly from TM-D700E manual text already verified in this project. Scenarios marked **(D710-inferred)** are based on the closely related TM-D710 manual, which shares much of the same UI — the D700 very likely behaves the same way, but the exact button name or behavior hasn't been independently confirmed for the D700 specifically. Treat those as "try it and see" rather than "guaranteed to work as described."

**Hardware note:** On the TM-D700, each band has a combined volume/band-select control — rotating it adjusts volume, pushing it selects that band as the active/control band. Throughout this document, **"press VOL A"** means push the left volume knob, and **"press VOL B"** means push the right volume knob. The `[F]`+volume-knob-press combination cycles through available frequency ranges for that band. The manual may refer to these controls as VOL A/VOL B or Band A/Band B depending on context.

For each scenario: **Goal** describes what we're hoping to learn, **Steps** is the button sequence to narrate, and **Watch for** is what to look for in the decode.

---

## 1. Band range cycling (maps full `=` value range)

**Goal:** The `[F]`+volume knob function in VFO mode cycles through *all* available receive/transmit frequency ranges on that band side — not merely a two-state VHF↔UHF swap as originally assumed. This test will map the complete value range of the `=` tag in a single pass, revealing how many distinct states it carries.

**Starting conditions:** both bands in memory mode. When VFO mode is entered, Band A defaults to **144.000 MHz** and Band B defaults to **440.000 MHz** — these are known-plaintext anchors that confirm each VFO-entry step worked correctly before the range cycling begins.

**Steps (D700-confirmed):**
1. Press `[VOL A]` to select Band A, then press `[VFO]` to put Band A in VFO mode — pause 2–3s *(expect `N0144.000  ` and `P`/`R` going blank)*
2. Press `[VOL B]` to select Band B, then press `[VFO]` to put Band B in VFO mode — pause 2–3s *(expect `O0440.000  ` and `Q`/`S` going blank)*
3. Press `[VOL A]` to select Band A, then press `[F]`+`[VOL A]` to cycle to the next frequency range — pause 2–3s after each press; repeat until Band A's ranges wrap back to the start *(watch `=` and `N` on each cycle)*
4. Press `[VOL B]` to select Band B, then press `[F]`+`[VOL B]` to cycle through Band B's frequency ranges — pause 2–3s after each press; repeat until Band B's ranges wrap back to the start *(watch `=` and `O` on each cycle)*

**Note:** steps 1 and 2 are pure setup that will produce the already-understood `P`/`R`/`Q`/`S` blanking messages — that's expected. The interesting data begins at step 3. Each `[F]`+volume knob press should produce a new `=` value; count the distinct values until it cycles back to the start.

**Watch for:** a new `=` value on every press, the total number of distinct states the tag takes (could be more than 4 given the D700's wide receive coverage), and whether `N` (the displayed frequency) jumps to a range-appropriate default on each press — which would cross-confirm that `=` really is tracking the active frequency range.

---

## 2. Direct frequency change (tuning knob — both bands)

**Goal:** Confirm how `N` and `O` update during real-time tuning — does the body send one message per detent click, or batch into a single update after you stop turning? Also cross-checks that the step size between consecutive `N`/`O` values matches whatever step size is currently set (see scenario 6). Covers both bands in one pass.

**Starting conditions:** both bands in memory mode.

**Steps (D700-confirmed):**
1. Press `[VOL A]` to select Band A, then press `[VFO]` to enter VFO mode — pause 2–3s *(expect `N0144.000  `, `P`/`R` going blank)*
2. Turn the tuning control 3–4 clicks in one direction — pause 2–3s
3. Turn the tuning control back the same number of clicks — pause 2–3s
4. Press `[VOL B]` to select Band B, then press `[VFO]` to enter VFO mode — pause 2–3s *(expect `O0440.000  `, `Q`/`S` going blank)*
5. Turn the tuning control 3–4 clicks in one direction — pause 2–3s
6. Turn the tuning control back the same number of clicks

**Watch for:** how many `N` (Band A) and `O` (Band B) messages appear per click — one per detent vs. one batched message after stopping. Also note whether any other tag fires alongside the frequency update (a "tuning active" indicator, for example).

---

## 3. Control band vs. TX band (PTT/Ctrl indicator distinction — both bands)

**Goal:** `[CTRL]` separates "which band has PTT" from "which band the controls currently affect." Complete the full CTRL test on Band A first, then repeat identically on Band B.

**Starting conditions:** both bands in memory mode.

**Steps (D700-confirmed):**

*Band A block:*
1. Press `[VOL A]`, then press `[VFO]` — pause 2–3s *(PTT on Band A, Band A in VFO mode)*
2. Turn tuning control 1–2 clicks — pause 2–3s *(Band A has control: watch `N` update)*
3. Press `[CTRL]` — pause 2–3s *("CTRL" appears on Band B row; control shifts to Band B, PTT stays on Band A)*
4. Turn tuning control 1–2 clicks — pause 2–3s *(Band B now has control: watch `O` update)*
5. Press `[CTRL]` again — pause 2–3s *(control returns to Band A)*
6. Turn tuning control 1–2 clicks — pause 2–3s *(Band A has control again: watch `N` update)*

*Band B block:*
7. Press `[VOL B]`, then press `[VFO]` — pause 2–3s *(PTT on Band B, Band B in VFO mode)*
8. Turn tuning control 1–2 clicks — pause 2–3s *(Band B has control: watch `O` update)*
9. Press `[CTRL]` — pause 2–3s *("CTRL" appears on Band A row; control shifts to Band A, PTT stays on Band B)*
10. Turn tuning control 1–2 clicks — pause 2–3s *(Band A now has control: watch `N` update)*
11. Press `[CTRL]` again — pause 2–3s *(control returns to Band B)*
12. Turn tuning control 1–2 clicks — pause 2–3s *(Band B has control again: watch `O` update)*

**Watch for:** a tag that changes at each CTRL press (steps 3, 5, 9, 11) but not at the tuning steps — that's the control-band indicator. Also watch for the literal ASCII strings "CTRL" and "PTT" in any tag payload at the CTRL press moments, since those words appear literally on the display at the affected band's row indicator position.

---

## 4. Squelch — full range sweep, both bands

**Goal:** Identify the squelch level tags for both bands and confirm the full numeric range encoded in each. The TM-D700 has a dedicated SQL knob for each band (SQL A and SQL B) — independent physical controls that don't require pressing VOL A/B to switch bands first. A full sweep from minimum to maximum and back will reveal the complete value range and encoding.

**Starting conditions:** any — SQL controls are band-dedicated and operate independently regardless of which band has PTT.

**Steps (D700-confirmed):**
1. Turn SQL A (Band A squelch) from its current position all the way to minimum (fully open/no squelch) — pause 2–3s
2. Turn SQL A all the way to maximum (fully closed) — pause 2–3s
3. Return SQL A to a sensible mid-range position — pause 2–3s
4. Turn SQL B (Band B squelch) from its current position all the way to minimum — pause 2–3s
5. Turn SQL B all the way to maximum — pause 2–3s
6. Return SQL B to a sensible mid-range position

**Watch for:** a tag whose value sweeps continuously from one extreme to the other, updating on every SQL knob detent (similar to how `0x8F` encoder pulses work in scenario 2). Expect separate tags or separate payloads for SQL A vs SQL B — they may share a tag with a band-selector field in the payload, or use completely distinct tags. Also note the numeric range of the value — confirms how many squelch levels the protocol encodes.

---

## 5. Volume — full range sweep, both bands

**Goal:** Same idea as scenario 4 for the VOL controls. The TM-D700 has a dedicated VOL knob for each band — VOL A (left) and VOL B (right). Rotating each knob adjusts that band's audio level independently; pressing it selects the band (already documented as keycodes 0x8D/0x8E). A full sweep confirms whether volume level is reported to the body at all, or handled purely locally in the head's own audio amp with no protocol message sent.

**Starting conditions:** any — VOL rotation is band-dedicated and independent.

**Note:** take care to only *rotate* each knob for this scenario, not press it — pressing VOL A or VOL B generates a 0x8D/0x8E band-select keycode which would add noise to the capture.

**Steps (D700-confirmed):**
1. Rotate VOL A from its current position all the way to minimum (zero volume) — pause 2–3s
2. Rotate VOL A all the way to maximum — pause 2–3s
3. Return VOL A to a comfortable listening level — pause 2–3s
4. Rotate VOL B from its current position all the way to minimum — pause 2–3s
5. Rotate VOL B all the way to maximum — pause 2–3s
6. Return VOL B to a comfortable listening level

**Watch for:** a tag tracking each knob's position — or complete silence, which would confirm volume is handled entirely within the head (a purely local audio-amp control with no protocol involvement). Either result is informative. If a tag does appear, note whether SQL A and VOL A share any tag structure, or use completely distinct encodings.

---

## 6. Frequency step size

**Goal:** Identify the step-size tag.

**Steps (D700-confirmed):**
1. Press `[VFO]` to ensure you're in VFO mode
2. Press `[F]`, then `[STEP]`
3. Use the tuning control or arrow keys to cycle through 2–3 step sizes (e.g. 5 → 10 → 12.5 kHz)
4. Press `[STEP]` (or equivalent) again to confirm/exit

**Watch for:** a tag whose value changes with each step-size selection.

---

## 7. Tone/CTCSS frequency and DCS code selection

**Goal:** We've confirmed `@` tracks tone *mode* (off/Tone/CTCSS/DCS) — this scenario looks for the separate field(s) tracking *which* tone frequency or DCS code is selected within each mode, in one combined pass to keep it under 30 seconds.

**Steps (D700-confirmed):**
1. Press the tone-cycle button to reach Tone mode (`@1`)
2. Turn the tuning control one click to step to the next tone frequency
3. Press the tone-cycle button again to reach CTCSS mode (`@2`)
4. Turn the tuning control one click to step to the next CTCSS frequency
5. Press the tone-cycle button again to reach DCS mode (`@3`)
6. Turn the tuning control one click to step to the next DCS code

**Watch for:** a numeric tag changing at each tuning step. Pay attention to whether the *same* tag carries the value across all three modes (suggesting Kenwood uses one shared "sub-tone index" field) or whether Tone/CTCSS frequency and DCS code use distinct tags — that's a real open question, not an assumption.

---

## 8. Repeater shift direction

**Goal:** Identify the shift-direction tag (simplex / + shift / − shift, and possibly the special "=" *display glyph* the manual uses for odd-split offsets — note this is a coincidental reuse of the "=" character as a screen icon, completely unrelated to our protocol's `=` tag, and worth being careful not to conflate the two).

**Steps (D700-confirmed):**
1. Press `[F]`, then `[SHIFT]` repeatedly to cycle through the available shift directions
2. Pause between each press

**Watch for:** a tag whose value cycles through 2–4 states in step with each `[SHIFT]` press.

---

## 9. Reverse function

**Goal:** Clean on/off toggle, likely related to the same area as repeater shift.

**Steps (D700-confirmed):**
1. Press `[REV]` to turn Reverse ON
2. Pause
3. Press `[REV]` again to turn it OFF

**Watch for:** a boolean-looking tag flipping between two values.

---

## 10. Automatic Simplex Checker (ASC)

**Goal:** A related but distinct function from plain Reverse — worth distinguishing from scenario 9's tag.

**Steps (D710-inferred, likely same on D700):**
1. Press and hold `[REV]` for about 1 second to activate ASC
2. Pause
3. Press `[REV]` again briefly to cancel

**Watch for:** whether this produces the *same* tag as scenario 9 (meaning Reverse and ASC share a field) or a different one (meaning they're tracked separately).

---

## 11. FM/AM mode switching (menu-based, Band A only)

**Goal:** AM mode is only available on Band A and is accessed via the menu system at L1=3, L2=4 — there is no direct [F]+[MHz] shortcut for FM/AM. Note: [F]+[MHz] (0x86) is the Transceiver Lock function (scenario 15), not FM/AM. This scenario confirmed AM mode sets the 0x15 separator byte in `N`'s frequency payload (displays as underscore `_`), and FM restore returns to the 0x2E dot separator.

**Steps (D700-confirmed — performed in Scenario11_V1.csv):**
1. Press `[VOL A]` to select Band A
2. Press `[MNU]` to open the menu
3. Navigate to menu L1=3, L2=4 (FM/AM setting) and select AM — press `[OK]`
4. Press `[F]`/ESC to exit menu — pause 2–3s
5. Return to menu and restore FM — press `[OK]` then `[F]`/ESC

**Watch for:** `N` tag frequency updating its separator byte on exit from menu — `0x15` (underscore `_`) for AM mode, `0x2E` (dot `.`) for FM mode. The `b` and `c` tags track the menu path and current value respectively.

---

## 12. Power output level

**Goal:** Identify the TX power level tag (High/Mid/Low).

**Steps (D710-inferred — D700 may use a dedicated `[LOW]` key or a menu/PF-key combo instead; try the most direct method available on your unit):**
1. Cycle through power levels once or twice
2. Pause between each

**Watch for:** a 2–3 state tag.

---

## 13. Single-band vs. dual-band display mode

**Goal:** A long-press function distinct from a normal Band A/B select press — worth testing since it changes the overall display layout, which likely means a noticeably different message burst from the body.

**Steps (D710-inferred — confirm this long-press behavior exists on the D700 before relying on it):**
1. Press and hold volume knob for about 1 second to toggle between single-band and dual-band display
2. Pause
3. Repeat to toggle back

**Watch for:** since this changes which VFO rows are shown at all, expect a larger burst than the simple band-select test — potentially several tags changing at once (display-layout-related fields, not just the `=` active-band tag).

---

## 14. Key beep on/off

**Goal:** Simple boolean toggle, useful as another easy confirmed data point.

**Steps (D700-confirmed, exact key combo may require checking your unit's menu structure if not directly bound to a key):**
1. Toggle key beep off
2. Pause
3. Toggle it back on

**Watch for:** a boolean tag — note that this is a setting more than a live status field, so it may only transmit once on change rather than appearing in the normal idle/heartbeat traffic.

---

## 15. Transceiver Lock

**Goal:** Identify the lock-status tag — useful since lock state likely also gates whether button-press messages get sent at all (worth noting if pressing buttons while locked produces *no* HEAD→BODY messages, which would itself be informative).

**Steps (D700-confirmed — exact lock activation method TBD on your unit, commonly a held key combo):**
1. Engage Transceiver Lock
2. Try pressing one of the already-confirmed buttons (e.g. VFO) — note whether it still produces a keycode message
3. Disengage Lock

**Watch for:** both a lock-status tag and (if the button press during lock produces no message) confirmation that locked buttons are suppressed entirely rather than sent-and-ignored.

---

## Explicitly excluded from this set

Per your request, nothing here touches TNC, APRS, or GPS configuration — those involve a much larger, separate set of tags (the `X`, `H`, `6`, `m` cluster from the original boot capture, and the whole "TNC APRS Δ16 BCON GPS 1200" status row) and deserve their own dedicated session.

## Also worth avoiding for now

Scenario candidates that involve actually keying the transmitter (the 1750 Hz `[CALL]` tone, live PTT transmission) are intentionally left out of this list. Capturing those is possible and would likely reveal PTT-related tags, but it requires actually transmitting RF — make sure you're using a dummy load or operating within your license privileges on a clear frequency before attempting that as a follow-up.

---

## 16. Tuning encoder in memory mode (channel scrolling — both bands)

**Goal:** Confirms that `0x8F` is a universal encoder tag used in all contexts. In memory mode, the body sends a full per-channel state update on every encoder click: channel label (`R`/`S`), frequency (`N`/`O`), channel number (`P`/`Q`), tone mode (`@`/`A`), and shift direction (`D`/`E`) — all channel-specific values stored in each memory slot.

**Starting conditions:** both bands in memory mode. Press `[VOL A]` then `[MR]` to enter memory mode on Band A; similarly for Band B.

**Steps (D700-confirmed — performed in Scenario16_V1.csv):**
1. Press `[VOL A]` to select Band A, then press `[MR]` to enter memory mode — pause 2–3s *(Band A now in memory mode, showing current channel)*
2. Turn the tuning control 3–4 clicks in one direction to scroll through memory channels — pause 2–3s
3. Turn the tuning control back the same number of clicks — pause 2–3s
4. Press `[VOL B]` to select Band B, then press `[MR]` to enter memory mode — pause 2–3s
5. Turn the tuning control 3–4 clicks in one direction — pause 2–3s
6. Turn the tuning control back the same number of clicks — pause 2–3s
7. Press `[VFO]` to return Band B to VFO mode — pause 2–3s
8. Press `[VOL A]`, then press `[VFO]` to return Band A to VFO mode

**Confirmed from Scenario16_V1.csv:**
- `0x8F` encoder (0x01=up, 0xFF=down) operates identically in memory mode — universal
- Body sends `R`/`N`/`P`/`@`/`D` (Band A) or `S`/`O`/`Q`/`A`/`E` (Band B) on every click — full per-channel state
- `D`/`E` (shift direction) and `@`/`A` (tone mode) are channel-specific — update per click
- Channel number encoding in `P`/`Q`: prefix `0` + right-justified 3-char number for channels 1–199; prefix `1` for channels 200+ (e.g. `P1200` = channel 200)
- Memory channels appear to be numbered 1–200 (not 0–199); wraps 199→200→1

**Watch for:** whether `@`/`A` omits the tag entirely when unchanged (only sends it when different from the previous channel's value) — this was seen in the Band A scroll where some channels didn't send `@`.

---

## 17. Illumination level / DIM (resolves 0x80 boot value and `;` tag)

**Goal:** The DIM function is accessed via `[F]`+`[OK/CTRL]` (0x87 then 0x8C) — there is no separate DIM button keycode. The encoder then scrolls through 5 levels: DIM 1, 2, 3, 4, and OFF. This confirmed tag `;` as the illumination indicator and resolved the last boot burst mystery (`0x80` payload `'1'` = DIM level 1 at startup).

**Steps (D700-confirmed — performed in Scenario17_V1.csv):**
1. Press `[F]`, then press `[OK/CTRL]` to enter DIM adjustment mode — pause 2–3s *(expect `45`, `H070`, `;1`, `N0DIM   1`)*
2. Turn encoder clockwise through DIM 2 → 3 → 4 → OFF — pause 2–3s between each *(watch `;` and `N` update each click)*
3. Press `[OK/CTRL]` to save DIM OFF — pause 2–3s
4. Press `[F]`, then `[OK/CTRL]` to re-enter DIM adjustment — pause 2–3s *(reopens showing current level)*
5. Turn encoder counter-clockwise: DIM 4 → 3 → 2 → 1 — pause 2–3s between each
6. Press `[OK/CTRL]` to save DIM 1

**Confirmed from Scenario17_V1.csv:**
- DIM entered via `[F]`+`[OK/CTRL]` (0x87 → 0x8C) — no separate button code
- Tag `;` = DIM/illumination level: `;0`=OFF, `;1`=DIM 1 (boot default), `;2`=DIM 2, `;3`=DIM 3, `;4`=DIM 4
- `N` repurposed: shows `N0DIM   1` through `N0DIM OFF` in DIM adjustment mode
- `45` display mode (same as step-size selection) — confirms `45` = generic encoder-driven list selection
- `H070` in DIM adjustment mode (differs from `H?30` in tone/step selection); `H000` on exit
- Boot burst `0x80` payload `'1'` = DIM level 1 at startup — **boot burst now fully decoded**
- Forward cycle: 1→2→3→4→OFF→1; reverse: OFF→4→3→2→1→OFF

---

## 18. Long-hold [F] key

**Goal:** A short press of `[F]` is confirmed as keycode `0x87`. A long hold of `[F]` on many Kenwood radios opens the main menu (which may be the `MNU` function), or triggers a different behavior entirely. This will either confirm `0x87` is reused with a different timing interpretation by the body, or reveal a distinct keycode for the long-hold event — potentially resolving one of the two unknown button codes (PM and MNU).

**Starting conditions:** any — radio in normal operating state.

**Steps:**
1. Press and hold `[F]` for approximately 1–2 seconds until a menu or different display appears — pause 2–3s
2. Note what appears on the display
3. Press `[F]` briefly (or `[ESC]`) to exit — pause 2–3s

**Watch for:** whether a second `0x87` message appears during the hold (indicating the body detects hold duration from repeated messages or a timeout), or whether a completely new keycode appears on key-down or key-up that differs from `0x87`. Also watch the body's response — if a menu opens, expect tag `4` to change value and possibly `V` or `H`/`I` to carry menu title text.

---

## 19. CALL channel toggle (both bands)

**Goal:** The `[CALL]` button (confirmed as keycode `0x85`) toggles each band between its configured CALL channel frequency and the current VFO frequency. Pressing once jumps to the CALL frequency (displaying "CALL" as the channel label in `R`/`S`); pressing again returns to the previous VFO frequency. The CALL channel also carries its own stored shift direction, so `D`/`E` may update on toggle.

**Steps (D700-confirmed — performed in ScenarioCALL_V1.csv):**
1. Press `[VOL A]` to select Band A — pause 2–3s
2. Press `[CALL]` to jump to Band A's CALL channel — pause 2–3s *(expect `R0CALL`, new `N` frequency)*
3. Press `[CALL]` again to return to previous VFO — pause 2–3s *(expect `R0` blank, `N` restored)*
4. Press `[VOL B]` to select Band B — pause 2–3s
5. Press `[CALL]` to jump to Band B's CALL channel — pause 2–3s *(expect `S0CALL`, new `O` freq, possible `E` change)*
6. Press `[CALL]` again to return — pause 2–3s *(expect `S0` blank, `O` and `E` restored)*

**Confirmed from ScenarioCALL_V1.csv:**
- Band A CALL = 144.390 MHz (same as APRS ch.199); label `R0CALL`
- Band B CALL = 446.000 MHz; label `S0CALL`; `E1` (+shift) activates on enter, `E0` restores on exit
- CALL channel carries its own stored shift direction independent of VFO shift setting

**Watch for:** any additional tags changing alongside `R`/`S`/`N`/`O`/`D`/`E` — power level (`B`/`C`), tone mode (`@`/`A`), or offset frequency could also be CALL-channel-specific.

---

## 20. PM (Programmable Memory) — select PM1 then PM OFF

**Goal:** The `[PM]` button (keycode `0x81`) enters a PM selection UI. Within that UI, other buttons select which PM bank to recall (the Tone/mode button `0x88` selects PM1), and `[F]` either cancels (if no PM is currently active) or selects PM OFF (if a PM bank is currently loaded). Recalling a PM bank or selecting PM OFF triggers a full state dump comparable in scope to the power-on boot sequence.

**Starting conditions:** PM not active (radio in normal VFO/MR state).

**Steps (D700-confirmed — performed in ScenarioPM_V1.csv):**
1. Press `[PM]` — pause 2–3s *(expect `48` — PM selection UI active)*
2. Press `[F]` to cancel — pause 2–3s *(expect `40` — simple cancel, no state change)*
3. Press `[PM]` again — pause 2–3s *(expect `48`)*
4. Press `[Tone]` to select PM1 — pause 2–3s *(triggers full PM1 state dump; expect `32`, `48`, complete state restoration including both bands)*
5. Press `[PM]` to re-enter PM UI — pause 2–3s *(expect `48`)*
6. Press `[F]` to select PM OFF — pause 2–3s *(triggers full PM OFF restore + TNC reinitialization; expect `31`, Z1, "OPENING TNC")*

**Confirmed from ScenarioPM_V1.csv:**
- `0x81` = PM button keycode
- `48` = tag `4` value `'8'` = PM selection mode active
- `32` = tag `3` value `'2'` = PM bank active; `31` = tag `3` value `'1'` = no PM active
- PM1 recall sets `=0` (Band A), `B0`/`C0` (High power) — stored from when PM1 was saved
- PM OFF sets `=3` (Band B), `B1`/`C1` (Medium) — restores pre-PM state
- PM OFF triggers TNC reinitialization (`Z1`, `V` shows "OPENING TNC") same as single-band-B to dual-band transition
- `[F]` in PM UI means PM OFF only when a PM bank is currently active; it means simple cancel otherwise
- `0x13` and `0x11` sent by head after PM OFF selection — meaning unknown

**Watch for in future PM captures:** whether other Tone button presses (different `0x88` variants) select PM2, PM3 etc., or whether PM bank selection uses a different button mapping.
