#!/usr/bin/env python3
"""Static, read-only Android APK architecture inventory.
No decryption, secret extraction, app execution, or proprietary game packaging.
Usage: python3 tools/audit_apk.py /path/to/port.apk
"""
import hashlib
import json
import struct
import sys
import zipfile
from pathlib import Path

def main(apk):
    path = Path(apk)
    if not path.is_file():
        raise SystemExit(f"APK não encontrado: {path}")
    with zipfile.ZipFile(path) as z:
        libs = []
        for entry in z.infolist():
            if not entry.filename.endswith('.so'):
                continue
            with z.open(entry) as f:
                hdr = f.read(20)
            arch = None
            if hdr.startswith(b'\x7fELF') and len(hdr) >= 20:
                machine = struct.unpack('<H', hdr[18:20])[0]
                arch = {183: 'ARM64/AArch64', 62: 'x86-64', 40: 'ARM32'}.get(machine, f'ELF-machine-{machine}')
            libs.append({'file': entry.filename, 'architecture': arch,
                         'unpacked_bytes': entry.file_size})
        config = z.read('assets/config.txt').decode('utf-8', errors='replace') \
                 if 'assets/config.txt' in z.namelist() else ''
        relevant = [x.filename for x in z.infolist() if x.filename in
                    ('assets/spirv.zip', 'assets/spirv.id', 'assets/variant.txt')]
    print(json.dumps({'apk': path.name, 'size_bytes': path.stat().st_size,
                      'native_libraries': libs, 'renderer_artifacts': relevant,
                      'launcher_config_excerpt': config[:750]},
                      ensure_ascii=False, indent=2))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Uso: python3 tools/audit_apk.py arquivo.apk')
    main(sys.argv[1])
