# Aurora Invariants - v1.1.0

## Papel

Este documento registra apenas invariantes já provadas pelo repositório da Aurora.

Ele não abre roadmap, não descreve desejo futuro e não substitui leitura do código, dos testes e das docs públicas. Ele existe para conter regressão conceitual.

## Invariantes

### Contrato pequeno e auditável vence promessa ampla

A Aurora só promove frente quando existe contrato explícito, policy, execução real, observabilidade e teste. Amplitude implícita não entra como atalho.

### Superfície explícita vence fallback mágico

`AUR`, `COPR`, `PPA`, `flatpak`, `toolbox`, `distrobox` e `rpm-ostree` só entram por pedido explícito. Observação do host não autoriza inferência frouxa.

### Manutenção do host não vira pacote genérico nem AUR implícita

`host_maintenance.atualizar` abre apenas `atualizar sistema` no host Arch mutável com `pacman` observado. `sudo + pacman` é o backend do recorte; helpers AUR, otimização e bundles de manutenção continuam fora.

### Ferramenta observada não vira suporte

Helper, backend ou comando observado fora do contrato continua sendo apenas observação. A ferramenta presente no host não amplia sozinha a superfície prometida.

### Superfícies diferentes não colapsam num genérico preguiçoso

`host`, `toolbox`, `distrobox` e `rpm-ostree` continuam distintos em request, policy, route, execution e `aurora dev`. A Aurora não apaga fronteira para parecer mais esperta.

### Documentação pública alinhada ao código é patrimônio do produto

`README.md`, `resources/help.txt`, `docs/ARCHITECTURE.md`, `docs/COMPATIBILITY_LINUX.md`, `docs/INSTALLATION_POLICY.md` e `docs/AURY_HERITAGE_MAP.md` já fazem parte da superfície auditável da Aurora.

### Parsing reverso de `trust_signals` não pode ficar implícito

Quando um fato ainda precisa ser reconstituído a partir de `trust_signals`, isso deve ficar explícito, curto e auditado. A Aurora não deve tratar parsing reverso de string como contrato invisível.

### `trust_signals` é evidência, não contrato factual central

Quando um fato central puder nascer diretamente no produtor de policy/route/execution, ele deve nascer ali. `trust_signals` pode explicar, contextualizar e preservar evidência, mas não deve seguir como canal semântico principal do kernel factual.

### Bridge legada precisa ficar explícita

Compatibilidade pode sobreviver por espelhos e bridges pequenas, mas a Aurora não deve esconder bridge legada como se fosse contrato canônico novo.

### Modelo local so entra como camada assistiva sobre kernel deterministico

Desde a `v1.0.0`, o modelo local opera sobre `schema`, `stable_ids`, `facts` e `presentation` ja fechados. Ele pode clarificar, resumir, explicar e desambiguar candidatos ja estruturados, mas nao pode decidir policy, suporte, bloqueio, confirmacao, rota, execucao nem verdade operacional.

### Gate automatizado não substitui revisão humana nem terminal real

Gate curto, checklist humano e terminal real têm papéis diferentes. A Aurora não deve tratar `push`, `tag` ou `release` como seguros só porque o harness passou.

### O centro operacional da Aurora é 100% Python

Fish, stage pública e mecânicas herdadas da Aury não entram como centro do runtime nem do gate da linha da Aurora.
