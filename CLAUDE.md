# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## State of the repo

This repository contains **no source code, build system, tests, or README** — only sample save-game data (single commit, "first commit"). Its stated purpose (from the name) is converting Resident Evil Code: Veronica X saves between PS2 and PS3 formats. There are no build/lint/test commands; any converter must be written from scratch. No `xxd` is installed; use `od -A d -t x1 <file>` or Python for binary inspection.

## Sample data (reference inputs for the converter)

- `PS2/BASLUS-20184/` — a PS2 memory-card save folder (BASLUS-20184 = US game ID):
  - `SAVEDATA-00` … `SAVEDATA-14`: 15 slot files, each exactly 2104 bytes (15 × 2104 = 31560 bytes total). Little-endian; begins `0a 00 00 00 01 00 00 00 …`.
  - `BASLUS-20184` (52 bytes): small game-level settings/flags file, mostly zeros.
  - `icon.sys` (PS2 icon descriptor, title "RESIDENT EVIL CODE: Veronica X") and `bio_cv.ico` (3D icon) are memory-card metadata, not game data.
- `PS3/NPUB304670/` — a PS3 savedata folder (NPUB304670 = PSN title ID, RPCS3-style):
  - `DATA0.DAT` (31876 bytes): 8-byte header (`00 8e d8 c8 ff ff ff ff`, purpose unknown — not a CRC32/Adler/byte-sum of the body) + 15 × 2104-byte slots + 308-byte tail. See the verified mapping below.
  - `PARAM.SFO`: PS3 save metadata (title, `SAVEDATA_DIRECTORY`, `PARAMS`/`PARAMS2`, and an `RPCS3_BLIST` key). Its `PARAMS` may contain a hash/signature that must be handled for a real PS3 to accept a converted save (RPCS3 is more lenient).
  - `ICON0.PNG`, `PIC1.PNG`: display assets only.

## Verified PS2 ↔ PS3 mapping (derived by diffing the samples; no public format docs were found online)

- **Slot layout is identical.** `DATA0.DAT[8:]` is 15 consecutive 2104-byte slots followed by a 308-byte tail; PS2 `SAVEDATA-NN` is slot NN. The PS3 sample has only slot 0 populated (others all zero); the PS2 sample has slots 0–7 populated, 8–14 empty.
- **Endianness:** multi-byte integers are little-endian on PS2 and big-endian on PS3, so converting is a per-field byte reversal. In slot 0, 28 of the 37 non-zero 32-bit words are exactly the reversed PS2 word, and the u16 pairs inside words swap order too (a full 4-byte reversal of the word — e.g. PS2 `01 00 37 00` → PS3 `00 37 00 01`).
- **Not swapped:** word at offset 8 is four u8 fields (`00 00 01 00` is identical on both; across PS2 slots byte 9 and 10 vary, e.g. `00 04 08 00`, `00 03 0b 00`). Any u8 arrays/strings must be left as-is, so a blanket word swap is wrong — a per-field map is needed.
- **Slot header:** u32 @0 = `0x0a` in every slot (version/magic); u32 @4 = slot id (PS2 slots hold 1,2,4,5,6,7,8,9 — slot 0 → 1, and ids are not contiguous at slot 3).
- **Checksum (PS2, verified on all 8 populated slots):** u32 LE at offset 2100 = sum of bytes `[0, 2100)` & 0xFFFF. The PS3 sample's slot 0 has **0** there (its byte sum is 0x147b), so PS3 does not store this checksum at the same place — don't assume it is needed or absent without testing in RPCS3/hardware.
- **Caveat:** the PS3 and PS2 slot 0 are different game states, not the same save, so 7 words (offsets 468, 2036, 2052, 2060, 2064, 2084, 2100) differ in value and cannot be told apart from layout differences. The last ~68 bytes of a slot (2036–2103) are where they cluster. A same-state pair (export the same save from PS2 and PS3) is needed to resolve this.
- **Tail / `BASLUS-20184` file:** the 52-byte PS2 settings file corresponds to the first 52 bytes of the PS3 308-byte tail (the rest is zero); byte 15 is `01` in both (not swapped), while the word at 48 is `1` on PS2 and `6` on PS3 (likely different settings, not just endianness).
- The PS3 side adds `PARAM.SFO`/PNGs and (on real hardware) likely a signature/hash; PS2 adds `icon.sys`/`.ico`.
