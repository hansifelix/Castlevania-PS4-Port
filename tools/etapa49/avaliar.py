#!/usr/bin/env python3
"""Auditoria de delta de símbolos. CI verde != ELF, não mascara falha do linker."""
from __future__ import annotations
import json
from pathlib import Path
import sys

# API não gráfica/áudio/memória; as de alto risco permanecem PENDENTES.
PREFIXOS = (
    'nx::plat::headless()',
    'nx::plat::memguard_overlap_ns(',
    'nx::plat::profile(',
    'nx::plat::setting(',
    'nx::plat::data_root()',
    'nx::plat::exit_process(int)',
)


def ler_nm(path: Path) -> set[str]:
    ret = set()
    for row in path.read_text(encoding='utf-8').splitlines():
        row = row.strip()
        if row.startswith('U '):
            ret.add(row.removeprefix('U ').strip())
        elif row.startswith('w ') or row.startswith('W '):
            continue
        elif row:
            raise ValueError(f'Formato nm -u inesperado: {row!r}')
    return ret


def avaliar(antes: set[str], depois: set[str], definitions: str) -> dict:
    targets = {}
    for prefix in PREFIXOS:
        expected = sorted(s for s in antes if s.startswith(prefix))
        if len(expected) != 1:
            raise ValueError(f'API esperada deveria estar indefinida UMA vez antes: {prefix}, ocorreu {expected}')
        if any(s.startswith(prefix) for s in depois):
            raise ValueError(f'API AINDA indefinida depois: {prefix}')
        if prefix not in definitions:
            raise ValueError(f'API nao definida no novo objeto: {prefix}')
        targets[prefix] = expected[0]
    resolved = sorted(antes - depois)
    introduced = sorted(depois - antes)
    remaining_plat = sorted(s for s in depois if s.startswith('nx::plat::'))
    return {
        'etapa': 49,
        'natureza': 'link relocavel com seis implementacoes basicas nx::plat, sem jogo e sem PKG',
        'antes': len(antes), 'depois': len(depois),
        'resolvidos': len(resolved), 'introduzidos': len(introduced),
        'apis_basicas_resolvidas': len(targets),
        'apis_resolvidas': sorted(targets.values()),
        'apis_plataforma_pendentes': len(remaining_plat),
        'pendentes_plataforma': remaining_plat,
        'simbolos_resolvidos': resolved,
        'simbolos_introduzidos': introduced,
        'bloqueios_reais': [
            'Modulo AOT do proprio jogo ainda ausente',
            'GPU/Vulkan/NVN para PS4 ainda sem adaptacao',
            'Memoria reservada em enderecos fixos ainda sem adaptacao',
            'Audio, entrada e threads ainda sem adaptacao',
            'Libc++/ABI/link estrito ainda em investigacao',
            'data_root=/app0 e somente provisoria, nao valida escrita nem saves',
        ],
        'gerou_elf_executavel': False,
        'executou_runtime': False,
    }


def main(directory: Path) -> None:
    before = ler_nm(directory/'ANTES.nm')
    after = ler_nm(directory/'DEPOIS.nm')
    defined = (directory/'DEFINIDOS_ADAPTADOR.nm').read_text(encoding='utf-8')
    report = avaliar(before, after, defined)
    status_file = directory/'STATUS_LINK_ESTRITO.txt'
    status = status_file.read_text(encoding='utf-8').strip() if status_file.exists() else 'NAO_TESTADO'
    report['link_estrito'] = status
    report['gerou_elf_executavel'] = status == 'PASSOU_ELF_INTERMEDIARIO'
    (directory/'RELATORIO.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    txt = (
        'KAZUMA ETAPA 49 - SERVICOS BASICOS DO HOST PS4\n'
        '===============================================\n'
        f"APIS_BASICAS_RESOLVIDAS={report['apis_basicas_resolvidas']}\n"
        f"PENDENCIAS_ANTES={report['antes']}\n"
        f"PENDENCIAS_DEPOIS={report['depois']}\n"
        f"RESOLVIDOS_TOTAL={report['resolvidos']}\n"
        f"NOVAS_DEPENDENCIAS={report['introduzidos']}\n"
        f"PLATAFORMA_PENDENTE={report['apis_plataforma_pendentes']}\n"
        f"LINK_ESTRITO={status}\n"
        'AVISO=Este resultado NAO comprova boot de Castlevania. SEM PKG, SEM JOGO.\n'
        'DESBLOQUEIOS DE VERDADE: memoria guest, threads, NVN/Vulkan e AOT privado.\n'
    )
    (directory/'LEIA_PRIMEIRO.txt').write_text(txt, encoding='utf-8')
    (directory/'PLATAFORMA_PENDENTE.txt').write_text('\n'.join(report['pendentes_plataforma'])+'\n',encoding='utf-8')
    print(txt)


if __name__ == '__main__':
    if len(sys.argv)!=2: raise SystemExit('Uso: avaliar.py DIRETORIO_RELATORIOS')
    main(Path(sys.argv[1]))
