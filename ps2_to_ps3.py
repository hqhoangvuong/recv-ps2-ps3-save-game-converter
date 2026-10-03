#!/usr/bin/env python3
"""Convert a Resident Evil Code: Veronica X PS2 save folder (BASLUS-20184) to a
PS3 (NPUB30467x) savedata folder.

    ps2_to_ps3.py PS2/BASLUS-20184-Same-Save-As-PS3 out/NPUB304670
    ps2_to_ps3.py SRC_DIR OUT_DIR [--template PS3/NPUB304670] [--slots 0,1,2]

Format rules (derived by diffing the sample saves, see CLAUDE.md):
  * DATA0.DAT = 8-byte header + 15 x 2104-byte slots + 308-byte tail.
  * Within a slot every 32-bit word is byte-reversed (LE -> BE), except the
    byte-array words at offsets 8 and 2068, which are copied unchanged.
  * The PS2 checksum word (offset 2100) is zeroed: the PS3 sample has none.
  * Header, tail, PARAM.SFO and PNGs are taken from the template PS3 folder.

Unverified: whether a real PS3 accepts the result (PARAM.SFO may carry a
signature); the 0x40 bit that PS3 sets in the word at offset 468 is not
reproduced; the tail (settings) is not converted from the PS2 settings file.
"""
import argparse
import os
import shutil
import struct
import sys

SLOT_SIZE = 2104
SLOT_COUNT = 15
HEADER_SIZE = 8
TAIL_SIZE = 308
UNSWAPPED_WORDS = (8, 2068)
CHECKSUM_OFFSET = 2100


def ps2_checksum(slot: bytes) -> int:
    return sum(slot[:CHECKSUM_OFFSET]) & 0xFFFF


def convert_slot(slot: bytes) -> bytes:
    if len(slot) != SLOT_SIZE:
        raise ValueError(f"slot is {len(slot)} bytes, expected {SLOT_SIZE}")
    out = bytearray(slot)
    for off in range(0, SLOT_SIZE, 4):
        if off not in UNSWAPPED_WORDS:
            out[off:off + 4] = slot[off:off + 4][::-1]
    out[CHECKSUM_OFFSET:CHECKSUM_OFFSET + 4] = bytes(4)
    return bytes(out)


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("src", help="PS2 folder containing SAVEDATA-00..14")
    ap.add_argument("dst", help="output PS3 savedata folder (created)")
    ap.add_argument("--template", default=os.path.join(here, "PS3", "NPUB304670"),
                    help="PS3 folder supplying header/tail/PARAM.SFO/PNGs")
    ap.add_argument("--slots", help="comma-separated slot numbers to convert (default: all present)")
    ap.add_argument("--force-checksum-check", action="store_true",
                    help="abort if a non-empty PS2 slot fails its checksum")
    args = ap.parse_args()

    tmpl = open(os.path.join(args.template, "DATA0.DAT"), "rb").read()
    if len(tmpl) != HEADER_SIZE + SLOT_SIZE * SLOT_COUNT + TAIL_SIZE:
        sys.exit("template DATA0.DAT has unexpected size")
    header = tmpl[:HEADER_SIZE]
    tail = tmpl[HEADER_SIZE + SLOT_SIZE * SLOT_COUNT:]
    wanted = {int(x) for x in args.slots.split(",")} if args.slots else None

    slots = []
    for n in range(SLOT_COUNT):
        path = os.path.join(args.src, f"SAVEDATA-{n:02d}")
        if (wanted is not None and n not in wanted) or not os.path.exists(path):
            slots.append(bytes(SLOT_SIZE))
            continue
        raw = open(path, "rb").read()
        if any(raw) and struct.unpack_from("<I", raw, CHECKSUM_OFFSET)[0] != ps2_checksum(raw):
            msg = f"slot {n}: PS2 checksum mismatch (save may be corrupt/edited)"
            if args.force_checksum_check:
                sys.exit(msg)
            print("warning:", msg, file=sys.stderr)
        slots.append(convert_slot(raw))
        print(f"slot {n:02d}: converted" if any(raw) else f"slot {n:02d}: empty")

    os.makedirs(args.dst, exist_ok=True)
    for name in os.listdir(args.template):
        if name != "DATA0.DAT":
            shutil.copy2(os.path.join(args.template, name), os.path.join(args.dst, name))
    with open(os.path.join(args.dst, "DATA0.DAT"), "wb") as f:
        f.write(header + b"".join(slots) + tail)
    print(f"wrote {os.path.join(args.dst, 'DATA0.DAT')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
