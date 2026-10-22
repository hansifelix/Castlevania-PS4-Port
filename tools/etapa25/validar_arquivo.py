#!/usr/bin/env python3
"""Relatorio da compilacao *real* de liborbis-compat.a, nao compatibilidade NVN."""
import argparse,hashlib,json,subprocess
from pathlib import Path

def inspect_archive(archive:Path,llvm_ar='llvm-ar',llvm_nm='llvm-nm')->dict:
    if not archive.is_file() or archive.stat().st_size<4096:
        raise ValueError('arquivo inexistente ou pequeno demais')
    members=subprocess.run([llvm_ar,'t',str(archive)],capture_output=True,text=True,check=True).stdout.splitlines()
    members=[m for m in members if m.endswith('.o')]
    if len(members)<10 or len(members)!=len(set(members)):
        raise ValueError(f'arquivo com objetos insuficientes/duplicados: {len(members)}')
    names=subprocess.run([llvm_nm,'-g','--defined-only',str(archive)],capture_output=True,text=True,check=True).stdout
    symbols=sum(1 for line in names.splitlines() if line.strip() and len(line.split())>=2 and not line.endswith(':'))
    if symbols<15:
        raise ValueError(f'arquivo sem quantidade suficiente de simbolos definidos: {symbols}')
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    return {'arquivo':str(archive),'tamanho_bytes':archive.stat().st_size,
            'objetos':len(members),'simbolos_definidos_aproximados':symbols,
            'sha256':digest,'compilacao_ps4_executada':True,
            'mesa_radv_compilada':False,'pkg_gerado':False,'ps4_testado':False,
            'runtime_castlevania_executado':False,'port_viavel':'INDETERMINADO'}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();info=inspect_archive(a.archive)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'resultado.json').write_text(json.dumps(info,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (a.out/'RELATORIO.md').write_text(
        '# Kazuma Etapa 25 — build real de orbis-compat (na CI)\n\n'
        f"**Arquivo:** `{info['arquivo'].split('/')[-1]}`\n\n"
        f"**Objetos:** {info['objetos']}; **simbolos aproximados:** {info['simbolos_definidos_aproximados']}; "
        f"**SHA256:** `{info['sha256']}`.\n\n"
        '**Limites:** arquivo compilado nao e driver Vulkan. O Mesa RADV nao foi compilado; '\
        'nenhum ELF/PKG do runtime ou hardware PS4 foi executado. '\
        'A viabilidade de Castlevania permanece INDETERMINADA.\n',encoding='utf-8')
    print(f"Etapa 25: {info['objetos']} objetos, {info['simbolos_definidos_aproximados']} simbolos no overlay. Sem Mesa/PKG/PS4.")
if __name__=='__main__':main()
