# Architecture - Aurora v0.3.0

## Tese curta

Aurora continua sendo um produto **100% Python** com contratos pequenos e observáveis:

- `host_package` para pacotes oficiais do host;
- `AUR` como fonte explícita de terceiro para pacote do host em Arch;
- `user_software` para software do usuário via `flatpak`.

Ela não depende de Fish como centro do runtime, não trata ferramenta observada como promessa de suporte e não colapsa fontes diferentes numa única rota opaca.

## Fluxo principal

1. `cli.py` recebe o comando público.
2. `semantics/` normaliza a frase e classifica a intenção mínima.
3. `linux/host_profile.py` detecta família, mutabilidade e ferramentas observadas.
4. `install/domain_classifier.py` decide entre default de `host_package`, fonte explícita `AUR` e `user_software`.
5. `install/policy_engine.py` produz o juízo de política.
6. `install/candidates.py` e `install/route_selector.py` escolhem a rota executável.
7. `install/execution_handoff.py` executa, faz probes, entrega o terminal ao helper quando a rota é interativa e produz o resultado final.
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
- fronteira entre backend oficial do host e helper de fonte terceira em Arch.

### `install/`

Orquestra a decisão:

- classificação de domínio e fonte;
- policy;
- resolução controlada de alvo;
- candidatos e seleção de rota;
- handoff de execução;
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

## Rotas abertas na v0.3.0

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

A `v0.3.0` continua pequena de propósito:

- pedido nu continua em `host_package`;
- `AUR` não vira fallback mágico;
- `flatpak` não generaliza seleção de remote além do default `flathub`;
- `user_software` não abre outras fontes além de `flatpak`;
- hosts imutáveis reais continuam fora da superfície operacional.
