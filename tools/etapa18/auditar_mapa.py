#!/usr/bin/env python3
"""Auditoria ESTATICA do mapa da memoria guest de nx, sem executar nada no PS4.

Nao seleciona enderecos seguros no PS4 e nao reserva memoria.
Lê somente arquivos de cabecalho publicos de um commit fixo do projeto upstream.
"""
import argparse
import ast
import json
import re
from pathlib import Path

UPSTREAM_COMMIT = '4043f21bb4f656d34cd17ba070238c7728d00631'
GIB = 1024 ** 3
MIB = 1024 ** 2
REGIONS = {
    'heap': ('kHeapBase', 'kHeapMax'),
    'alias': ('kAliasBase', 'kAliasSize'),
    'stack': ('kStackBase', 'kStackSize'),
    'kernel_guest': ('kKernelBase', 'kKernelSize'),
    'thunk': ('kThunkBase', 'kThunkSize'),
}


def number_expr(expr: str, vars_: dict) -> int:
    """Aceita apenas constantes aritmeticas basicas do header. Nunca usa eval()."""
    node = ast.parse(expr.strip().removesuffix('ull').removesuffix('UL'), mode='eval').body

    def visit(n):
        if isinstance(n, ast.Constant) and type(n.value) is int:
            return n.value
        if isinstance(n, ast.Name) and n.id in vars_:
            return vars_[n.id]
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub, ast.LShift)):
            a, b = visit(n.left), visit(n.right)
            if isinstance(n.op, ast.Add):
                return a + b
            if isinstance(n.op, ast.Sub):
                return a - b
            if b < 0 or b > 62:
                raise ValueError('deslocamento fora dos limites')
            return a << b
        raise ValueError('expressao desconhecida: ' + expr)

    v = visit(node)
    if not (0 <= v < 2**64):
        raise ValueError('constante fora de uint64')
    return v


def nx_base(cpu: str, platform: str) -> int:
    # O header fixado no upstream usa #ifndef NX_BASE + #if defined(__APPLE__).
    pattern = (r'#if\s+defined\(__APPLE__\)\s*'
               r'#define\s+NX_BASE\s+(0x[0-9a-fA-F]+(?:ull|ULL)?)\s*'
               r'#else\s*#define\s+NX_BASE\s+(0x[0-9a-fA-F]+(?:ull|ULL)?)')
    m = re.search(pattern, cpu)
    if not m:
        raise ValueError('NX_BASE nao reconhecido: revisar cpu.h manualmente')
    return int(m.group(1 if platform == 'macos' else 2).rstrip('uUlL'), 16)


def runtime_constants(runtime: str, cpu: str, platform: str) -> dict:
    if platform not in ('linux', 'android', 'macos'):
        raise ValueError('plataforma invalida')
    begin = runtime.find('constexpr uint64_t kAddressSpaceBase')
    end = runtime.find('void memory_init()', begin)
    if begin < 0 or end < 0:
        raise ValueError('limites das declaracoes nao encontrados no runtime.h')
    block = runtime[begin:end]
    values = {'NX_BASE': nx_base(cpu, platform)}
    stack = []  # (active_parent, branch_condition)
    active = True
    for raw in block.splitlines():
        ln = raw.strip()
        if ln.startswith('#if '):
            expr = ln[4:].strip()
            if expr not in ('defined(__APPLE__)', 'defined(__ANDROID__)'):
                raise ValueError('condicao de compilacao desconhecida: ' + expr)
            cond = (platform == 'macos') if 'APPLE' in expr else (platform == 'android')
            stack.append([active, cond])
            active = active and cond
            continue
        if ln.startswith('#else'):
            if not stack:
                raise ValueError('#else inesperado')
            parent, cond = stack[-1]
            stack[-1][1] = not cond
            active = parent and (not cond)
            continue
        if ln.startswith('#endif'):
            if not stack:
                raise ValueError('#endif inesperado')
            parent, _ = stack.pop()
            active = parent
            continue
        if not active:
            continue
        m = re.match(r'constexpr\s+uint64_t\s+(k\w+)\s*=\s*([^;]+);', ln)
        if m:
            values[m.group(1)] = number_expr(m.group(2), values)
    if stack:
        raise ValueError('preprocessador com condicoes nao encerradas')
    required = {'kAddressSpaceBase', 'kAddressSpaceSize', 'kModuleBase'}
    for a, b in REGIONS.values():
        required.update((a, b))
    missing = required - values.keys()
    if missing:
        raise ValueError('constantes faltando: ' + ', '.join(sorted(missing)))
    return values


def analyze(values: dict, platform: str) -> dict:
    envelope_start = values['kAddressSpaceBase']
    envelope_end = envelope_start + values['kAddressSpaceSize']
    entries = []
    findings = []
    for name, (base_const, size_const) in REGIONS.items():
        start = values[base_const]
        size = values[size_const]
        end = start + size
        entries.append({'nome': name, 'inicio_hex': f'0x{start:012X}',
                        'fim_exclusivo_hex': f'0x{end:012X}', 'inicio': start,
                        'fim_exclusivo': end, 'tamanho_gib': round(size / GIB, 6)})
        if start < envelope_start or end > envelope_end or size == 0:
            findings.append({'nivel': 'ALERTA', 'tipo': 'fora_envelope', 'regiao': name})
    for i in range(len(entries)):
        for j in range(i+1, len(entries)):
            a, b = entries[i], entries[j]
            if max(a['inicio'], b['inicio']) < min(a['fim_exclusivo'], b['fim_exclusivo']):
                findings.append({'nivel': 'ALERTA', 'tipo': 'sobreposicao',
                                 'regioes': [a['nome'], b['nome']]})
    module_base = values['kModuleBase']
    if module_base < envelope_start or module_base >= envelope_end:
        findings.append({'nivel': 'ALERTA', 'tipo': 'module_base_fora_envelope'})
    for entry in entries:
        if entry['inicio'] <= module_base < entry['fim_exclusivo']:
            findings.append({'nivel': 'ATENCAO', 'tipo': 'base_modulo_em_regiao', 'regiao': entry['nome']})
    return {
        'etapa': 18,
        'plataforma_original': platform,
        'fonte_publica_commit': UPSTREAM_COMMIT,
        'modelo': 'enderecos e tamanhos NOMINAIS do runtime; nao sao mapeamentos PS4',
        'envelope_guest': {'inicio_hex': f'0x{envelope_start:012X}',
                           'fim_exclusivo_hex': f'0x{envelope_end:012X}',
                           'tamanho_gib': round(values['kAddressSpaceSize'] / GIB, 6)},
        'module_base_hex': f'0x{module_base:012X}',
        'regioes': entries,
        'achados_estaticos': findings,
        'sobreposicoes_nominais': any(x['tipo'] == 'sobreposicao' for x in findings),
        'ps4_mapa_real_verificado': False,
        'enderecos_seguros_ps4_identificados': False,
        'nx_plat_reserve_commit_decommit_testados_ps4': False,
        'instrucao_operacional': 'NAO usar MAP_FIXED; NAO reservar essas faixas no PS4; auditoria apenas.',
    }


def generate(runtime_file: Path, cpu_file: Path, output: Path):
    runtime = runtime_file.read_text(encoding='utf-8')
    cpu = cpu_file.read_text(encoding='utf-8')
    output.mkdir(parents=True, exist_ok=True)
    reports = []
    for platform in ('linux', 'android', 'macos'):
        data = analyze(runtime_constants(runtime, cpu, platform), platform)
        (output / f'mapa_{platform}.json').write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        reports.append(data)
    lines = [
        '# Kazuma — Etapa 18: auditoria estatica de memoria', '',
        f'Referencia upstream: `{UPSTREAM_COMMIT}`.', '',
        '**Isto NAO e um mapa real da memoria do PS4.** As faixas representam apenas',
        'enderecos nominais empregados pelo runtime em outros sistemas. Nao executar',
        'mmap fixo, nao instalar PKG, nao modificar kernel, firmware ou GoldHEN.', '',
        '| Plataforma | Envelope guest nominal | Inicio modulo | Colisoes nominais |',
        '|---|---|---|---|',
    ]
    for data in reports:
        lines.append(f"| {data['plataforma_original']} | {data['envelope_guest']['inicio_hex']}–{data['envelope_guest']['fim_exclusivo_hex']} | {data['module_base_hex']} | " +
                     ('Sim' if data['sobreposicoes_nominais'] else 'Nao') + ' |')
    lines += ['', '## Implicacoes e pendencias', '',
        '- Um endereco livre em Linux, Android ou macOS **nao esta comprovado livre no PS4**.',
        '- Sem evidencias do mapa de memoria real de um processo homebrew PS4, nenhuma',
        '  faixa pode ser considerada adequada para a memoria guest do jogo.',
        '- As funcoes `nx::plat::reserve/commit/decommit` nao foram implementadas nem testadas.',
        '- O Test 06 de 64 KiB usava endereco escolhido pelo SO; nao exercitou mapa fixo.',
        '- O runtime exige mais do que memoria: codigo recompilado, loader, threads e NVN.',
        '- Proxima decisao: estudar viabilidade sem reservar grandes faixas ou enderecos fixos.',
        '', '## Regioes (intervalos [inicio, fim), fim exclusivo)', '']
    for data in reports:
        lines.append(f"### {data['plataforma_original']}")
        lines += ['| Regiao | Inicio | Fim exclusivo | GiB |', '|---|---|---|---:|']
        for e in data['regioes']:
            lines.append(f"| {e['nome']} | {e['inicio_hex']} | {e['fim_exclusivo_hex']} | {e['tamanho_gib']:.6f} |")
        lines.append('')
    (output / 'AUDITORIA_MAPA.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('ETAPA 18: relatorios estaticos criados em', output)
    for d in reports:
        print(f"{d['plataforma_original']}: colisoes nominais = {d['sobreposicoes_nominais']}; PS4 validado = NAO")
    return reports


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--cpu', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    generate(args.runtime, args.cpu, args.out)


if __name__ == '__main__':
    main()
