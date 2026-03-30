# Architecture - Aurora v0.1.0

## Tese curta

Aurora `v0.1` e um produto **100% Python** com foco estreito em `host_package`.

Ela nao depende de Fish como centro arquitetural, nao abre multiplas fontes e nao trata hosts imutaveis como se fossem mutaveis.

## Fluxo principal

1. `cli.py` recebe o comando publico;
2. `semantics/` normaliza a frase e classifica a intencao minima;
3. `linux/host_profile.py` detecta familia, mutabilidade e backends observados;
4. `install/policy_engine.py` produz o juizo de politica;
5. `install/candidates.py` e `install/route_selector.py` escolhem a rota;
6. `install/execution_handoff.py` executa a rota, faz probe antes/depois e produz o resultado final;
7. `observability/` registra e renderiza o `decision_record`.

## Modulos principais

### `semantics/`

Guarda o patrimonio herdado e refatorado da Aury para:

- normalizacao;
- protecao de tokens sensiveis;
- split simples de acoes;
- classificacao minima de `procurar`, `instalar` e `remover`.

### `linux/`

Guarda a parte Linux real da `v0.1`:

- `host_profile`;
- deteccao de mutabilidade;
- matriz por familia;
- rotas concretas de `host_package`;
- bloqueio de hosts Atomic/imutaveis.

### `install/`

Orquestra a decisao:

- classificacao de dominio;
- candidatos de rota;
- policy;
- selecao;
- handoff de execucao.

### `observability/`

Explica o que a Aurora entendeu e fez:

- `decision_record`;
- renderizacao curta e expandida;
- `aurora dev`.

### `presentation/`

Mantem a superficie publica:

- help;
- mensagens de bloqueio;
- mensagens de confirmacao;
- mensagens de resultado.

## Contrato de execucao da v0.1

Rotas realmente abertas:

- `host_package.search`
- `host_package.install`
- `host_package.remove`

Comportamentos garantidos:

- probe antes/depois para mutacao;
- `noop` honesto;
- bloqueio por politica em hosts imutaveis;
- confirmacao explicita quando a politica exigir;
- separacao entre bloqueio, `noop`, execucao e erro operacional.

## O que esta deliberadamente fora

- `flatpak` como rota ativa;
- qualquer fonte alem de `host_package_manager`;
- manutencao ampla do host;
- dominios de arquivos e rede;
- multi-acao real como superficie publica.
