#!/usr/bin/env python3
"""Non-destructive structural check of an NSP or ZIP containing NSPs.

No decryption, keys, copyrighted content extraction, or game execution.
Works with Python 3 (e.g., Termux). Printed filenames may include title IDs.

Usage: python tools/audit_switch.py /path/to/Game.nsp
       python tools/audit_switch.py /path/to/Castlevania.zip
"""
import re
import struct
import sys
import zipfile
from pathlib import Path

MAX_FILES = 4096
MAX_TABLE = 2 * 1024 * 1024
TITLE_RE = re.compile(r'\[([0-9a-fA-F]{16})\]', re.I)
VERSION_RE = re.compile(r'\[v(\d+)\]', re.I)
SKIP_EXT = ('.keys', '.key', '.tik', '.cert')


def label(name):
    if name.lower().endswith(SKIP_EXT):
        return None
    title_match = TITLE_RE.search(name)
    ver_match = VERSION_RE.search(name)
    title_id = title_match.group(1).upper() if title_match else None
    role = ('atualização (ID + 0x800)' if title_id and int(title_id, 16) & 0xFFF == 0x800 else
            'base (ID termina em 000)' if title_id and int(title_id, 16) & 0xFFF == 0 else
            'DLC/outro (ID não identifica base/update)' if title_id else 'tipo não identificável só pelo nome')
    return title_id, int(ver_match.group(1)) if ver_match else None, role


def read_pfs0(f, total_size):
    header = f.read(16)
    if len(header) < 16:
        return 'cabeçalho curto (arquivo incompleto?)'
    if header[:4] != b'PFS0':
        return f'cabeçalho {header[:4]!r}: NÃO é PFS0 reconhecível (pode estar corrompido/ser outro formato)'
    n, strings_size, _ = struct.unpack_from('<III', header, 4)
    if n > MAX_FILES or strings_size > MAX_TABLE:
        return 'metadados PFS0 fora dos limites seguros; leitura interrompida'
    need = n * 24 + strings_size
    blob = f.read(need)
    if len(blob) < need:
        return 'tabela PFS0 incompleta'
    strings = blob[n * 24:]
    payload_start = 16 + need
    valid = 0
    problems = []
    for idx in range(n):
        offset, size, str_offset, _ = struct.unpack_from('<QQII', blob, idx * 24)
        if str_offset >= strings_size or payload_start + offset + size > total_size:
            problems.append(idx)
        else:
            valid += 1
    return (f'PFS0 OK: {n} entradas, {valid} com limites coerentes'
            + (f'; {len(problems)} entrada(s) inconsistente(s)' if problems else ''))


def check(path):
    path = Path(path)
    if not path.is_file():
        raise ValueError(f'Arquivo não encontrado: {path}')
    print('Auditoria estrutural somente-leitura; não precisa de chaves de Switch.')
    suffix = path.suffix.lower()
    candidates = []
    if suffix == '.nsp':
        candidates.append((path.name, path.stat().st_size, lambda: path.open('rb')))
    elif suffix == '.zip':
        with zipfile.ZipFile(path) as z:
            print(f'ZIP válido: {len(z.infolist())} entradas. Não extrai arquivos.')
            for item in z.infolist():
                if not item.filename.lower().endswith('.nsp'):
                    continue
                name = Path(item.filename).name
                print(f'\n{name}\n  tamanho declarado: {item.file_size:,} bytes')
                details = label(name)
                if details:
                    print(f'  Title ID: {details[0] or "indisponível"}; versão: {details[1]}; classificação: {details[2]}')
                with z.open(item) as f:
                    print('  ' + read_pfs0(f, item.file_size))
            print('\nChaves .keys no ZIP foram ignoradas. Não as compartilhe.')
        return
    else:
        raise ValueError('Formato aceito: arquivo .nsp ou .zip com .nsp')
    for name, size, opener in candidates:
        print(f'\n{name}\n  tamanho: {size:,} bytes')
        details = label(name)
        if details:
            print(f'  Title ID: {details[0] or "indisponível"}; versão: {details[1]}; classificação: {details[2]}')
        with opener() as f:
            print('  ' + read_pfs0(f, size))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Uso: python3 tools/audit_switch.py arquivo.nsp | Castlevania.zip')
    try:
        check(sys.argv[1])
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as exc:
        raise SystemExit(f'Erro: {exc}') from exc
