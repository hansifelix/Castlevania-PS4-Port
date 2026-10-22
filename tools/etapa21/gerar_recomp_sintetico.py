#!/usr/bin/env python3
"""3 instrucoes ARM64 originais -> C++ com o emissor real upstream (sem NSO/jogo)."""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

# Comprovado contra clang --target=aarch64 e llvm-objdump:
# mov w0,#42 ; add w0,w0,#1 ; ret
WORDS = (0x52800540, 0x11000400, 0xD65F03C0)
EXPECTED = 43


def generate(out: Path):
    from recomp import analysis, emit, nso
    out.mkdir(parents=True,exist_ok=True)
    code = struct.pack('<3I', *WORDS)
    m = nso.Module(name='kazuma_synthetic', image=bytearray(code),
                   text=(0,len(code)), ro=(0,0), data=(0,0), bss=(0,0))
    an = analysis.analyze(m, log=lambda *_: None)
    if len(an.functions) != 1 or an.functions[0].start != 0 or an.functions[0].end != 12:
        raise RuntimeError('Recompilador detectou funcao ou intervalo inesperado')
    if sorted(an.insns) != [0,4,8]:
        raise RuntimeError('Disassembly incompleto')
    e = emit.Emitter(an,prefix='kazuma_guest')
    fn = e.function(an.functions[0])
    if e.handled != 3 or e.unhandled:
        raise RuntimeError(f'Instrucao nao suportada: {dict(e.unhandled)}')
    symbol = e.fn(0)
    header = """#pragma once
#include <nx/cpu.h>
#define NXB NX_BASE
void kazuma_guest_00000000(nx::CPU& c);
"""
    if symbol!='kazuma_guest_00000000':
        raise RuntimeError('Nome da funcao gerada mudou no upstream')
    (out/'funcs.h').write_text(header,encoding='utf-8')
    (out/'code.cpp').write_text('#include "funcs.h"\n\n'+fn+'\n',encoding='utf-8')
    (out/'main.cpp').write_text("""#include "funcs.h"
extern "C" int kazuma_recompiled_test() {
    nx::CPU c{};
    kazuma_guest_00000000(c);
    return c.x[0] == 43 ? 0 : 1;
}
int main() { return kazuma_recompiled_test(); }
""",encoding='utf-8')
    report = {
       'etapa':21, 'codigo_arm64_sintetico':True,
       'instrucoes': ['mov w0, #42', 'add w0, w0, #1', 'ret'],
       'bytes_arm64_hex':code.hex(), 'sha256_arm64':hashlib.sha256(code).hexdigest(),
       'recompilador': 'recomp/analysis.py + recomp/emit.py do SuperMarioWonderRecomp upstream',
       'quantidade_instrucoes':e.handled,'funcoes_detectadas':len(an.functions),
       'recompilacao_do_jogo':False, 'pkg_gerado':False,'teste_ps4':False,
       'resultado_esperado':EXPECTED,'observacao':'C++ gerado de ARM64 sintético, sem NSO e sem dados de jogo.'}
    (out/'geracao.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('GERADO: 1 funcao ARM64, 3 instrucoes -> C++ pelo recompilador publico, sem jogo.')
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    generate(args.out)
