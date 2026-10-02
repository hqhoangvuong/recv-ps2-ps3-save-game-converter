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
  - `DATA0.DAT` (31876 bytes): the actual save payload. It starts with an 8-byte header (`00 8e d8 c8 ff ff ff ff`) followed by what looks like the same record layout as the PS2 slots but **big-endian** (`00 00 00 0a 00 00 00 01 …` vs PS2 `0a 00 00 00 01 00 00 00 …`). The 31560-byte PS2 payload plus remaining trailing bytes accounts for its size; the exact mapping is not yet verified.
  - `PARAM.SFO`: PS3 save metadata (title, `SAVEDATA_DIRECTORY`, `PARAMS`/`PARAMS2`, and an `RPCS3_BLIST` key). Its `PARAMS` may contain a hash/signature that must be handled for a real PS3 to accept a converted save (RPCS3 is more lenient).
  - `ICON0.PNG`, `PIC1.PNG`: display assets only.

When working on a converter, treat the PS2 and PS3 folders as paired known-good samples of the same game state and diff them to derive the byte-order/layout transformation rather than assuming it.
