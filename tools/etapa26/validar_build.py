#!/usr/bin/env python3
"""Confirma evidencias de build/link sem confundi-las com execucao grafica no console."""
import argparse, hashlib, json
from pathlib import Path

def analisar(build:Path):
    if not build.is_dir():
        raise ValueError('Diretorio de build nao encontrado')
    elf = build / 'triangle'
    if not elf.is_file() or elf.stat().st_size < 4096:
        raise ValueError('ELF triangle nao encontrado ou pequeno')
    with elf.open('rb') as fd:
        hdr=fd.read(20)
    if hdr[:4] != b'\x7fELF' or hdr[4] != 2 or int.from_bytes(hdr[18:20],'little') != 62:
        raise ValueError('O arquivo nao e ELF64 x86-64')
    boots=list(build.rglob('eboot.bin'))
    if len(boots) != 1 or boots[0].stat().st_size < 4096:
        raise ValueError('Esperado exatamente um eboot.bin PS4 nao vazio')
    return {
      'etapa':26,
      'target_elf':'ELF64 x86-64',
      'elf_bytes':elf.stat().st_size,
      'elf_sha256':hashlib.sha256(elf.read_bytes()).hexdigest(),
      'eboot_bytes':boots[0].stat().st_size,
      'eboot_sha256':hashlib.sha256(boots[0].read_bytes()).hexdigest(),
      'mesa_radv_compilado_nesta_ci':False,
      'mesa_radv_precompilado_do_bundle':True,
      'exemplo_vulkan_linkado':True,
      'pkg_gerado':False,
      'ps4_testado':False,
      'runtime_castlevania_executado':False,
      'viabilidade_port':'INDETERMINADA',
    }
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--build',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();r=analisar(a.build)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'RESULTADO.json').write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    (a.out/'RELATORIO.md').write_text(
        '# Kazuma Etapa 26 — Link publico Mesa/Vulkan PS4\n\n'
        'O exemplo publico `orbis-porting-kit/examples/triangle` foi compilado e ligado para ELF64 x86-64 com o bundle Mesa/RADV precompilado e vkloader.\n\n'
        f"ELF: {r['elf_bytes']} bytes, SHA256 {r['elf_sha256']}\n\n"
        f"eboot: {r['eboot_bytes']} bytes, SHA256 {r['eboot_sha256']}\n\n"
        '**NAO valida** GPU no console, dynamic rendering, shaders do jogo, carregador do runtime ou menu do Castlevania. Nao gera PKG nem instala nada.\n',
        encoding='utf8')
    print('ETAPA 26: ELF e eboot preparados no runner. SEM PKG. SEM PS4. Port indeterminado.')
if __name__=='__main__':main()
