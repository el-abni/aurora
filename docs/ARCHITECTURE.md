# Architecture - Aurora v0.3.1

## Tese curta

Aurora continua sendo um produto **100% Python** com contratos pequenos e observáveis:

- `host_package` para pacotes oficiais do host;
- `AUR` como fonte explícita de terceiro para pacote do host em Arch;
- `COPR` como fonte explícita de terceiro para pacote do host em Fedora;
- `user_software` para software do usuário via `flatpak`.

Ela não depende de Fish como centro do runtime, não trata ferramenta observada como promessa de suporte e não colapsa fontes diferentes numa única rota opaca.

## Fluxo principal

1. `cli.py` recebe o comando público.
2. `semantics/` normaliza a frase e classifica a intenção mínima.
3. `linux/host_profile.py` detecta família, mutabilidade e ferramentas observadas.
4. `install/domain_classifier.py` decide entre default de `host_package`, fontes explícitas `AUR` e `COPR`, e `user_software`.
5. `install/policy_engine.py` produz o juízo de política.
6. `install/candidates.py` e `install/route_selector.py` escolhem a rota executável.
7. `install/execution_handoff.py` executa, faz probes, roda passos preparatórios quando a rota exige preparação explícita e entrega o terminal ao helper quando a rota é interativa.
8. `observability/` registra e renderiza o `decision_record`.

## Módulos principais

### `semantics/`

Guarda o patrimônio herdado e refatorado da Aury para:

- normalização;
- proteção de tokens sensíveis;
- split simples de ações;
- classificação mínima de `procurar`, `instalar` e `remover`.

### `linux/`

Guarda a parte Linux real da Aurora:

- `host_profile`;
- detecção de mutabilidade;
- matriz por família;
- rotas concretas de `host_package`;
- fronteira entre backend oficial do host e fontes terceiras explícitas.

### `install/`

Orquestra a decisão:

- classificação de domínio e fonte;
- policy;
- resolução controlada de alvo;
- candidatos e seleção de rota;
- handoff de execução, incluindo preparação explícita de rota quando necessário;
- separação entre bloqueio, `noop`, confirmação e erro operacional.

### `observability/`

Explica o que a Aurora entendeu e fez:

- `decision_record`;
- renderização curta e expandida;
- `aurora dev`.

### `presentation/`

Mantém a superfície pública:

- help;
- mensagens de bloqueio;
- mensagens de confirmação;
- mensagens de resultado.

## Rotas abertas na v0.3.1

### `host_package`

Rotas reais:

- `host_package.search`
- `host_package.instalar`
- `host_package.remover`

Comportamento garantido:

- probe antes/depois para mutação;
- `noop` honesto;
- bloqueio por política em hosts imutáveis;
- confirmação explícita quando a política exigir.

### `AUR` explícito

Primeira fonte terceira real:

- `aur.procurar`
- `aur.instalar`
- `aur.remover`

Comportamento garantido:

- `AUR` só entra por pedido explícito;
- usa helper aceito explicitamente nesta rodada;
- `aur.instalar` e `aur.remover` usam probe via `pacman -Qm`;
- `aur.instalar` usa handoff interativo quando o helper entra em revisão/build;
- depois do helper interativo retornar, a Aurora volta para validar o estado final por probe;
- `aur.remover` permanece no caminho não interativo desta release;
- resolução de alvo separa pacote `foreign` de pacote oficial do host;
- mutação exige confirmação explícita;
- `--confirm` e `--yes` contam como confirmação explícita também quando entram inline na frase;
- não existe fallback implícito de pedido nu para AUR.

### `COPR` explícito

Segunda fonte terceira real:

- `copr.instalar`
- `copr.remover`

Comportamento garantido:

- `COPR` só entra por pedido explícito;
- a frase precisa carregar a coordenada `owner/project`;
- a frente só abre em Fedora mutável com `dnf copr` observado;
- `copr.instalar` executa um passo preparatório explícito para habilitar o repositório pedido e depois instala o pacote;
- `copr.remover` remove o pacote do host, mas não desabilita o repositório;
- mutação exige confirmação explícita;
- o nome do pacote precisa vir de forma exata neste primeiro corte;
- não existe busca global, descoberta mágica de repositório ou fallback implícito de pedido nu para COPR.

### `user_software`

Frente explícita de software do usuário:

- `flatpak.procurar`
- `flatpak.instalar`
- `flatpak.remover`

Comportamento garantido:

- `flatpak` só entra por pedido explícito;
- `flatpak.instalar` e `flatpak.remover` usam escopo explícito de usuário;
- mutação usa probe antes/depois e `noop` honesto;
- `flatpak.remover` exige confirmação explícita quando a remoção realmente precisa acontecer.

## Fronteiras deliberadas

A `v0.3.1` continua pequena de propósito:

- pedido nu continua em `host_package`;
- `AUR` não vira fallback mágico;
- `COPR` não abre `procurar`, não descobre repositório e não canoniza pacote por busca;
- `flatpak` não generaliza seleção de remote além do default `flathub`;
- `user_software` não abre outras fontes além de `flatpak`;
- hosts imutáveis reais continuam fora da superfície operacional.
