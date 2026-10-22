#!/usr/bin/env python3
"""Classifica resultado da ligacao. Check verde NAO implica ELF valido."""
from pathlib import Path
import json
import re
import sys


def avaliar(log: str, status: str, baseline_ok: bool) -> dict:
    symbols = sorted(set(re.findall(r"(?:^|\n)(?:[^\n]*?)(?:error:\s*)?undefined symbol:\s*([^\n]+)",log)))
    return {
        "etapa": 44,
        "experimento": "link estrito de oito APIs reais + main proprio sem jogo",
        "status_link": status,
        "baseline_minimo_43": bool(baseline_ok),
        "simbolos_nao_resolvidos_no_log": symbols,
        "quantidade_simbolos_no_log": len(symbols),
        "possui_codigo_do_jogo": False,
        "testado_no_ps4": False,
        "gerou_eboot_ou_pkg": False,
        "aviso": "ELF intermediario nao prova execucao em PS4 nem runtime completo; falha estrita nao deve ser ocultada.",
    }


def main():
    if len(sys.argv)!=4:raise SystemExit('Uso: avaliar_link.py PASTA STATUS BASELINE_SIM_OU_NAO')
    out=Path(sys.argv[1]); status=sys.argv[2]; baseline=sys.argv[3]=='SIM'
    texto=(out/'LINK.log').read_text(encoding='utf-8',errors='replace')
    resultado=avaliar(texto,status,baseline)
    (out/'RESULTADO.json').write_text(json.dumps(resultado,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (out/'SIMBOLOS_NAO_RESOLVIDOS.txt').write_text('\n'.join(resultado['simbolos_nao_resolvidos_no_log'])+'\n',encoding='utf-8')
    (out/'LEIA_PRIMEIRO.txt').write_text(
       f"ETAPA44={status}\nBASELINE_ETAPA43={'PASSOU' if baseline else 'NAO_CONFIRMADA'}\n"
       f"SIMBOLOS_NAO_RESOLVIDOS_NO_LOG={resultado['quantidade_simbolos_no_log']}\n"
       "IMPORTANTE: Um check verde valida a auditoria; nao garante ELF, eboot, PKG ou jogo.\n"
       "A Etapa 42 mostrou 33 simbolos no linker completo do runtime: compare com eles separadamente.\n",
       encoding='utf-8'
    )
    print((out/'LEIA_PRIMEIRO.txt').read_text())

if __name__=='__main__':main()
