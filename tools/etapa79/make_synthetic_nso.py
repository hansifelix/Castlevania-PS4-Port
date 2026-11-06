#!/usr/bin/env python3
"""Etapa 79 — constrói um NSO sintético mínimo com MOD0 real.

Somente 3 instruções AArch64 públicas: mov w0,#42; add w0,w0,#1; ret.
O fixture não usa nem redistribui dados comerciais.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import struct

CODE = struct.pack("<III", 0x52800540, 0x11000400, 0xD65F03C0)
FUNCTION_START = 0x20


def make_fixture(path: Path) -> None:
    # Layout esparso proposital: header/módulo metadata em RO+DATA;
    # executável apenas em 0x20. O loader recomp/nso.py suporta offsets.
    image = bytearray(0x400)
    struct.pack_into("<I", image, 4, 0x220)  # ponteiro MOD0 no início do image
    image[FUNCTION_START:FUNCTION_START + len(CODE)] = CODE
    image[0x220:0x224] = b"MOD0"
    struct.pack_into("<i", image, 0x224, 0x20)  # dynamic: 0x240
    # EH frame é ausente: ponteiro MOD0-relativo resolve para endereço zero.
    struct.pack_into("<i", image, 0x230, -0x220)
    struct.pack_into("<i", image, 0x234, -0x220)
    dynamic = ((6, 0x2e0), (5, 0x310), (11, 24), (0, 0))
    for i, (tag, value) in enumerate(dynamic):
        struct.pack_into("<qQ", image, 0x240 + i * 16, tag, value)
    # Dois símbolos: indefinido nulo e função exportada em +0x20.
    struct.pack_into("<IBBHQQ", image, 0x2f8, 1, 0x12, 0, 1, FUNCTION_START, len(CODE))
    image[0x310:0x310 + len(b"\x00synthetic_entry\x00")] = b"\x00synthetic_entry\x00"
    # Segmentos: text @0x20, ro @0, data @0x200.
    # Arquivo NSO não comprimido, três regiões disjuntas na memória.
    header = bytearray(0x100)
    header[:4] = b"NSO0"
    layout = ((0x100, 0x20, len(CODE)), (0x120, 0, 0x20), (0x140, 0x200, 0x200))
    for i, (off, address, size) in enumerate(layout):
        struct.pack_into("<III", header, 0x10 + i * 0x10, off, address, size)
        struct.pack_into("<I", header, 0x60 + i * 4, size)
    payload = bytearray(0x340)
    payload[:0x100] = header
    payload[0x100:0x100 + len(CODE)] = image[0x20:0x20 + len(CODE)]
    payload[0x120:0x140] = image[:0x20]
    payload[0x140:0x340] = image[0x200:0x400]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    make_fixture(args.out)
    print("NSO sintético gerado; possui 3 instruções e MOD0 — sem ROM, chaves ou assets.")


if __name__ == "__main__":
    main()
