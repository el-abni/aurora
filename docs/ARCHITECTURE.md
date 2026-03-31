# Architecture - Aurora v0.2.0

## Tese curta

Aurora `v0.2.0` é um produto **100% Python** com duas frentes reais e contidas:

- `host_package` para pacotes do host;
- `user_software` para software do usuário via `flatpak`.

Ela não depende de Fish como centro do runtime, não trata ferramenta observada como promessa de suporte e não colapsa espécies diferentes de ação numa única rota opaca.

## Fluxo principal

1. `cli.py` recebe o comando público;
2. `semantics/` normaliza a frase e classifica a intenção mínima;
3. `linux/host_profile.py` detecta família, mutabilidade e backends observados;
4. `install/domain_classifier.py` decide entre `host_package` e `user_software`;
5. `install/policy_engine.py` produz o juízo de política;
6. `install/candidates.py` e `install/route_selector.py` escolhem a rota executável;
7. `install/execution_handoff.py` executa, faz probes e produz o resultado final;
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
- bloqueio explícito de mutação do host em perfis Atomic/imutáveis.

### `install/`

Orquestra a decisão:

- classificação de domínio;
- policy;
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

## Rotas abertas na v0.2.0

### `host_package`

Rotas reais:

- `host_package.search`
- `host_package.install`
- `host_package.remove`

Comportamento garantido:

- probe antes/depois para mutação;
- `noop` honesto;
- bloqueio por política em hosts imutáveis;
- confirmação explícita quando a política exigir.

### `user_software`

Primeira frente real:

- `flatpak.procurar`
- `flatpak.instalar`
- `flatpak.remover`

Comportamento garantido:

- `flatpak` só entra por pedido explícito;
- `flatpak.instalar` e `flatpak.remover` usam escopo explícito de usuário;
- mutação usa probe antes/depois e `noop` honesto;
- `flatpak.remover` exige confirmação explícita quando a remoção realmente precisa acontecer.

## Fronteiras deliberadas

Esta release continua pequena de propósito:

- pedido nu continua em `host_package`;
- `flatpak` não generaliza seleção de remote além do default `flathub`;
- `user_software` não abre outras fontes além de `flatpak`;
- hosts imutáveis reais continuam fora da superfície operacional.
