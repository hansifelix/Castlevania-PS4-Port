#!/usr/bin/env python3
"""Kazuma etapa 9: auditoria reproduzivel de lacunas de simbolos.

Nao gera nem modifica binarios. Referencias textuais sao pistas, nao prova
nem de definicao, nem de compatibilidade com o PS4.
"""
import argparse
import collections
import csv
import json
import re
import subprocess
from pathlib import Path

SUFFIXES = {'.c', '.cc', '.cpp', '.cxx', '.h', '.hh', '.hpp', '.hxx', '.S'}


def desmangle(symbol):
    proc = subprocess.run(['c++filt', symbol], capture_output=True, text=True, check=True)
    return proc.stdout.strip()


def categoria(symbol):
    if symbol.startswith('_ZN2nx4plat'):
        return 'API de plataforma nx::plat'
    if symbol.startswith('_ZN2nx'):
        return 'Funcoes do runtime nx (outras unidades possiveis)'
    if symbol.startswith('_ZTH'):
        return 'Inicializacao TLS C++'
    if symbol == '__dso_handle':
        return 'Suporte de inicializacao C++'
    if symbol == 'rename':
        return 'Biblioteca C / importacao possivel'
    return 'Outros simbolos sem correspondencia'


def nome_para_busca(symbol, human):
    if symbol == '__dso_handle':
        return '__dso_handle'
    if symbol == 'rename':
        return 'rename'
    # Remove parametros; busca apenas o identificador terminal, sem inferir definicoes.
    before = human.split('(', 1)[0]
    name = before.rsplit('::', 1)[-1].strip()
    if not re.fullmatch(r'[a-zA-Z_]\w*', name):
        name = symbol  # Falha segura, evita falsa identificacao.
    return name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--resumo', required=True, type=Path)
    ap.add_argument('--upstream', required=True, type=Path)
    ap.add_argument('--saida', required=True, type=Path)
    args = ap.parse_args()
    d = json.loads(args.resumo.read_text(encoding='utf-8'))
    after = set(d['indefinidos_restantes'])
    providers = set(d['possiveis_bibliotecas_por_simbolo'])
    faltantes = sorted(after - providers)
    if len(after) != d['combinado7_indefinidos']:
        raise SystemExit('ERRO: quantidade de referencias diverge da etapa 8')
    if not args.upstream.is_dir():
        raise SystemExit('ERRO: arvore upstream nao encontrada')
    args.saida.mkdir(parents=True, exist_ok=True)
    files = []
    for path in args.upstream.rglob('*'):
        if path.is_file() and path.suffix in SUFFIXES and path.stat().st_size <= 2_000_000:
            files.append(path)
    files.sort()
    searchable = []
    for path in files:
        try:
            content = path.read_text(encoding='utf-8', errors='replace')
            searchable.append((str(path.relative_to(args.upstream)), content))
        except OSError:
            pass
    counts = collections.Counter()
    rows = []
    for symbol in faltantes:
        human = desmangle(symbol)
        category = categoria(symbol)
        counts[category] += 1
        term = nome_para_busca(symbol, human)
        pattern = re.compile(r'(?<!\w)' + re.escape(term) + r'(?!\w)')
        paths = [filename for filename, content in searchable if pattern.search(content)]
        rows.append({
            'simbolo_manglado': symbol,
            'nome_legivel': human,
            'classe': category,
            'termo_pesquisado': term,
            'arquivos_com_ocorrencia_textual': '; '.join(paths[:30]),
            'total_arquivos_encontrados': len(paths),
            'observacao': 'Coincidencia de texto, nao e definicao comprovada'
        })
    with (args.saida / 'simbolos_sem_provedor.tsv').open('w', encoding='utf-8', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else [
            'simbolo_manglado', 'nome_legivel', 'classe', 'termo_pesquisado',
            'arquivos_com_ocorrencia_textual', 'total_arquivos_encontrados', 'observacao'], delimiter='\t')
        wr.writeheader()
        wr.writerows(rows)
    report = {
        'etapa': 9,
        'fonte_relatorio_etapa8': str(args.resumo),
        'referencias_indefinidas_nos_sete_objetos': len(after),
        'com_pista_em_arquivos_estaticos_openorbis': len(providers),
        'sem_pista_nos_arquivos_estaticos_openorbis': len(faltantes),
        'agrupamento_dos_sem_pista': dict(sorted(counts.items())),
        'arquivos_fonte_upstream_consultados': len(searchable),
        'referencias_com_ocorrencia_textual_em_codigo_upstream': sum(bool(r['total_arquivos_encontrados']) for r in rows),
        'escopo': 'classificacao e busca textual de candidatos; NAO comprovacao de provedor ou definicao',
        'comprovacao_de_link_final': False,
        'comprovacao_de_execucao_no_ps4': False,
        'comprovacao_de_jogo': False,
    }
    (args.saida / 'resumo.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lines = [
        '# Kazuma — Etapa 9: lacunas de simbolos (diagnostico)',
        '',
        f'- Referencias nos 7 objetos: {len(after)}',
        f'- Referencias com nome correspondente no OpenOrbis (.a): {len(providers)}',
        f'- Referencias sem correspondencia no .a do OpenOrbis: {len(faltantes)}',
        f'- Arquivos publicos de codigo consultados: {len(searchable)}',
        '',
        '## Tipos de lacuna observados',
    ]
    for category, n in sorted(counts.items()):
        lines.append(f'- {category}: {n}')
    lines += [
        '', '## Interpretacao',
        '- Uma referencia sem nome correspondente em arquivos .a do SDK nao implica impossibilidade de port.',
        '- Uma correspondencia textual no codigo original pode ser so uma declaracao ou chamada.',
        '- Correspondencia de nome em SDK tambem NAO prova ligacao valida nem compatibilidade de ABI.',
        '- Ainda falta projeto de plataforma, ponto de entrada, event loop, grafico, audio e testes reais.',
        '- Nenhum eboot.bin, PKG, NSP, NCA, APK ou jogo foi produzido nem utilizado nesta etapa.',
    ]
    (args.saida / 'LEIA_ME.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print('ETAPA 9: relatorio de lacunas criado.')
    print(f'7 objetos: {len(after)} refs | {len(providers)} com pista SDK | {len(faltantes)} sem pista SDK')
    for category, n in sorted(counts.items()):
        print(f'  {category}: {n}')
    print('SEM link final, executavel ou teste no PS4.')


if __name__ == '__main__':
    main()
