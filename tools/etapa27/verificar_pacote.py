#!/usr/bin/env python3
"""Valida um candidato a PKG de exemplo público; não afirma execução na GPU."""
import argparse, hashlib, json
from pathlib import Path

EXPECTED = 'IV0000-BREW91240_00-KAZUMAVULKANGPU1.pkg'

def verificar(build:Path, pkg_dir:Path | None = None):
    elf=build/'triangle'
    if not elf.is_file() or elf.stat().st_size < 4096:
        raise ValueError('ELF original ausente/pequeno')
    with elf.open('rb') as fd:
        hdr=fd.read(20)
    if hdr[:4]!=b'\x7fELF' or hdr[4]!=2 or hdr[5]!=1 or int.from_bytes(hdr[18:20],'little')!=62:
        raise ValueError('ELF de triangulo nao e ELF64 little-endian x86-64')
    boots=list(build.rglob('eboot.bin'))
    if len(boots)!=1 or boots[0].stat().st_size<4096:
        raise ValueError('eboot PS4 ausente ou duplicado')
    out={'test':'Triangulo Vulkan publico','title_id':'BREW91240',
         'elf_sha256':hashlib.sha256(elf.read_bytes()).hexdigest(),
         'eboot_sha256':hashlib.sha256(boots[0].read_bytes()).hexdigest(),
         'eboot_size':boots[0].stat().st_size,
         'gpu_ps4_testada':False,'castlevania_executado':False}
    if pkg_dir is not None:
        pkgs=[p for p in pkg_dir.glob('*.pkg') if p.is_file() and not p.is_symlink()]
        if len(pkgs)!=1 or pkgs[0].name!=EXPECTED or pkgs[0].stat().st_size<262144:
            raise ValueError(f'Esperado apenas um PKG ({EXPECTED}) com >256KiB; encontrados: {[p.name for p in pkgs]}')
        out.update(pkg_gerado=True,pkg_size=pkgs[0].stat().st_size,
                   pkg_sha256=hashlib.sha256(pkgs[0].read_bytes()).hexdigest())
    else:
        out['pkg_gerado']=False
    return out

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--build',type=Path,required=True)
    a.add_argument('--pkg-dir',type=Path)
    a.add_argument('--out',type=Path,required=True)
    a.add_argument('--fase',choices=['eboot','pkg'],required=True)
    p=a.parse_args()
    if p.fase=='pkg' and p.pkg_dir is None: raise SystemExit('pkg-dir obrigatorio na fase pkg')
    r=verificar(p.build,p.pkg_dir if p.fase=='pkg' else None)
    p.out.mkdir(parents=True,exist_ok=True)
    (p.out/f'RESULTADO_{p.fase}.json').write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print(f"Etapa 27 ({p.fase}) validada. Teste de GPU PS4 NAO executado.")
if __name__=='__main__': main()
