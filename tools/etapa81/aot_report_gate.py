"""Etapa 81: qualidade da geração AOT — NÃO significa port jogável.

No relatório público do recompilador, 'unhandled N' > 0 exige análise humana
antes de ligar o resultado. Não substitui instruções por NOP sem semântica.
"""
from __future__ import annotations
import re

_PAT = re.compile(r"^functions\s+(\d+),\s*handled\s+(\d+),\s*unhandled\s+(\d+)\s*$")


def parse_report(report_text: str) -> dict:
    first = report_text.splitlines()[0].strip() if report_text.splitlines() else ""
    match = _PAT.fullmatch(first)
    if not match:
        raise ValueError("Relatório AOT sem primeira linha reconhecível; não marcar completo")
    functions, handled, unhandled = map(int, match.groups())
    if functions < 1 or handled < 1 or handled + unhandled < functions:
        raise ValueError("Contagens AOT inconsistentes; não marcar completo")
    details = []
    for line in report_text.splitlines()[1:]:
        m = re.fullmatch(r"\s*(\d+)\s+([A-Za-z][\w.]*)\s*", line)
        if m:
            details.append({"quantidade": int(m.group(1)), "mnemonico": m.group(2).lower()})
    return {
        "functions_detected": functions,
        "instructions_handled": handled,
        "instructions_unhandled": unhandled,
        "unhandled_mnemonics": details,
        "all_instructions_supported": unhandled == 0,
        "ready_for_ps4_link": False,
        "reason": "AOT ainda não foi compilado ou ligado com o runtime PS4",
    }
