from __future__ import annotations

import re

_WORD_REPLACEMENTS = (
    ("acoes", "ações"),
    ("acao", "ação"),
    ("ambigua", "ambígua"),
    ("ambiguidade", "ambiguidade"),
    ("automatica", "automática"),
    ("automatico", "automático"),
    ("automáticos", "automáticos"),
    ("canonica", "canônica"),
    ("canonico", "canônico"),
    ("confirmacao", "confirmação"),
    ("confianca", "confiança"),
    ("criterio", "critério"),
    ("critica", "crítica"),
    ("critico", "crítico"),
    ("disponivel", "disponível"),
    ("entao", "então"),
    ("execucao", "execução"),
    ("explicita", "explícita"),
    ("explicito", "explícito"),
    ("familia", "família"),
    ("heuristica", "heurística"),
    ("imutavel", "imutável"),
    ("instalacao", "instalação"),
    ("interacao", "interação"),
    ("intermediaria", "intermediária"),
    ("ja", "já"),
    ("logica", "lógica"),
    ("maxima", "máxima"),
    ("medicao", "medição"),
    ("minima", "mínima"),
    ("minimo", "mínimo"),
    ("mutacao", "mutação"),
    ("mutavel", "mutável"),
    ("nao", "não"),
    ("observacao", "observação"),
    ("observavel", "observável"),
    ("operacao", "operação"),
    ("politica", "política"),
    ("possivel", "possível"),
    ("preparacao", "preparação"),
    ("proveniencia", "proveniência"),
    ("proximo", "próximo"),
    ("remocao", "remoção"),
    ("repositorio", "repositório"),
    ("repositorios", "repositórios"),
    ("resolucao", "resolução"),
    ("restricao", "restrição"),
    ("revisao", "revisão"),
    ("ruido", "ruído"),
    ("selecao", "seleção"),
    ("sensivel", "sensível"),
    ("so", "só"),
    ("superficie", "superfície"),
    ("superficies", "superfícies"),
    ("tecnica", "técnica"),
    ("tecnico", "técnico"),
    ("transacao", "transação"),
    ("unica", "única"),
    ("usuario", "usuário"),
    ("usuarios", "usuários"),
    ("util", "útil"),
    ("visivel", "visível"),
)


def polish_public_text(text: str) -> str:
    if not text:
        return text

    polished = text
    for raw, replacement in _WORD_REPLACEMENTS:
        polished = re.sub(rf"\b{raw}\b", replacement, polished)

    match = re.search(r"[A-Za-zÀ-ÿ]", polished)
    if match is not None:
        index = match.start()
        polished = polished[:index] + polished[index].upper() + polished[index + 1 :]
    return polished
