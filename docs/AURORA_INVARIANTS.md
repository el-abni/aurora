# Aurora Invariants - v0.6.5

## Papel

Este documento registra apenas invariantes já provadas pelo repositório da Aurora.

Ele não abre roadmap, não descreve desejo futuro e não substitui leitura do código, dos testes e das docs públicas. Ele existe para conter regressão conceitual.

## Invariantes

### Contrato pequeno e auditável vence promessa ampla

A Aurora só promove frente quando existe contrato explícito, policy, execução real, observabilidade e teste. Amplitude implícita não entra como atalho.

### Superfície explícita vence fallback mágico

`AUR`, `COPR`, `PPA`, `flatpak`, `toolbox`, `distrobox` e `rpm-ostree` só entram por pedido explícito. Observação do host não autoriza inferência frouxa.

### Ferramenta observada não vira suporte

Helper, backend ou comando observado fora do contrato continua sendo apenas observação. A ferramenta presente no host não amplia sozinha a superfície prometida.

### Superfícies diferentes não colapsam num genérico preguiçoso

`host`, `toolbox`, `distrobox` e `rpm-ostree` continuam distintos em request, policy, route, execution e `aurora dev`. A Aurora não apaga fronteira para parecer mais esperta.

### Documentação pública alinhada ao código é patrimônio do produto

`README.md`, `resources/help.txt`, `docs/ARCHITECTURE.md`, `docs/COMPATIBILITY_LINUX.md`, `docs/INSTALLATION_POLICY.md` e `docs/AURY_HERITAGE_MAP.md` já fazem parte da superfície auditável da Aurora.

### Gate automatizado não substitui revisão humana nem terminal real

Gate curto, checklist humano e terminal real têm papéis diferentes. A Aurora não deve tratar `push`, `tag` ou `release` como seguros só porque o harness passou.

### O centro operacional da Aurora é 100% Python

Fish, stage pública e mecânicas herdadas da Aury não entram como centro do runtime nem do gate da linha da Aurora.
