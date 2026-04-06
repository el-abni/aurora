from __future__ import annotations

import re

_WORD_REPLACEMENTS = (
    ("acoes", "ações"),
    ("acao", "ação"),
    ("ambigua", "ambígua"),
    ("ambiguidade", "ambiguidade"),
    ("analitico", "analítico"),
    ("automatica", "automática"),
    ("automatico", "automático"),
    ("automáticos", "automáticos"),
    ("auditavel", "auditável"),
    ("basicos", "básicos"),
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
    ("implicita", "implícita"),
    ("implicito", "implícito"),
    ("instalacao", "instalação"),
    ("interacao", "interação"),
    ("intermediaria", "intermediária"),
    ("ja", "já"),
    ("logica", "lógica"),
    ("magica", "mágica"),
    ("maxima", "máxima"),
    ("medicao", "medição"),
    ("minima", "mínima"),
    ("minimo", "mínimo"),
    ("multiplos", "múltiplos"),
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
    ("publica", "pública"),
    ("publico", "público"),
    ("remocao", "remoção"),
    ("repositorio", "repositório"),
    ("repositorios", "repositórios"),
    ("resolucao", "resolução"),
    ("restricao", "restrição"),
    ("revisao", "revisão"),
    ("ruido", "ruído"),
    ("seletiva", "seletiva"),
    ("semantica", "semântica"),
    ("sintese", "síntese"),
    ("sozinha", "sozinha"),
    ("selecao", "seleção"),
    ("sensivel", "sensível"),
    ("so", "só"),
    ("superficie", "superfície"),
    ("superficies", "superfícies"),
    ("tecnica", "técnica"),
    ("tecnico", "técnico"),
    ("transacao", "transação"),
    ("transicao", "transição"),
    ("unica", "única"),
    ("unico", "único"),
    ("usuario", "usuário"),
    ("usuarios", "usuários"),
    ("util", "útil"),
    ("visivel", "visível"),
    ("autoselecao", "autosseleção"),
    ("parseavel", "parseável"),
    ("previo", "prévio"),
    ("rapida", "rápida"),
    ("rapido", "rápido"),
)


def polish_public_text(text: str) -> str:
    if not text:
        return text

    polished = text
    for raw, replacement in _WORD_REPLACEMENTS:
        polished = re.sub(rf"\b{raw}\b", replacement, polished)

    chars = list(polished)
    capitalize_next = True
    for index, char in enumerate(chars):
        if capitalize_next and re.match(r"[A-Za-zÀ-ÿ]", char):
            chars[index] = char.upper()
            capitalize_next = False
            continue
        if char in ".!?;":
            capitalize_next = True
        elif not char.isspace() and char not in "\"'([{":
            capitalize_next = False
    return "".join(chars)
