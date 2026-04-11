# Workflow de Testes e Release - Aurora v0.7.0

## Papel

Este documento formaliza a disciplina operacional preservada pela `v0.7.0`.

Ele não abre domínio novo, não cria framework de CI e não substitui leitura do código. Ele existe para separar claramente:

- teste automático;
- revisão/teste manual;
- teste real no terminal local.

## Três camadas de validação

### Teste automático

Teste automático é o que a Aurora consegue validar de forma mecânica e repetível:

- `unittest`;
- auditorias em `tests/`;
- gates shell por etapa.

Ele existe para proteger regressão executável, coerência pública e contrato pequeno. Ele não substitui revisão humana nem terminal real.

### Revisão e teste manual

Revisão manual é a leitura humana curta que confere:

- `VERSION`, `README.md`, `CHANGELOG.md` e `resources/help.txt`;
- coerência entre docs centrais e superfície pública;
- `aurora --version`, `aurora --help` e `aurora dev`, quando a mudança toca contrato, payload ou renderização;
- diffs sensíveis em `install/`, `contracts/`, `observability/`, `presentation/`, launchers e instaladores.

O artefato curto dessa camada é `tests/REVIEW_CHECKLIST.md`.

### Teste real no terminal local

Teste real no terminal local é o que só o ambiente real do Abni valida com honestidade:

- launchers instalados;
- handoff interativo do helper AUR;
- prompts, senha e timing real;
- `toolbox`, `distrobox` e `rpm-ostree` reais;
- sensação de renderização pública;
- comportamento final de `aurora` fora do harness de teste.

Essa validação é obrigatória quando a mudança toca runtime, instalador, launcher, handoff, mensagens públicas visíveis ou qualquer superfície cujo comportamento dependa do terminal real.

## Gates por etapa

### Coding comum

Rodar:

```bash
bash tests/release_gate_iteracao.sh
```

Esse gate dá feedback rápido sobre o chão público mínimo. Ele não substitui os testes específicos da área tocada.

### Antes de commit

Rodar:

```bash
bash tests/release_gate_iteracao.sh
```

Também é obrigatório:

- revisar os diffs sensíveis tocados;
- conferir `aurora --version` e `aurora --help` se a superfície pública mudou;
- conferir `aurora dev "<frase>"` se contrato, payload ou renderização mudaram.

### Antes de push

Rodar:

```bash
bash tests/release_gate_pre_push.sh
```

Esse gate bloqueia push quando:

- há whitespace/error de diff;
- a linha canônica falha;
- a coerência pública deixa de fechar.

Se a mudança tocou runtime real, o push também fica bloqueado até haver validação humana mínima no terminal local.

### Antes de tag

Rodar:

```bash
bash tests/release_gate_pre_release.sh
```

Também é obrigatório:

- checklist humano completo;
- versão, help e changelog coerentes;
- terminal real validado para a superfície tocada;
- worktree final já revisada para o corte de release.

### Antes de release

Repetir o gate pré-release no candidato final e só então:

- gerar relatório;
- gerar manifesto de empacotamento;
- gerar ZIP limpo;
- conferir a cópia final do artefato.

## O que nunca sobe sem validação humana real

Nunca devem subir por gate automático sozinho:

- mudanças em `VERSION`, `README.md`, `CHANGELOG.md`, `resources/help.txt` e docs centrais;
- mudanças em `install.sh`, `uninstall.sh`, `bin/`, `python/aurora/install/`, `python/aurora/contracts/`, `python/aurora/observability/` e `python/aurora/presentation/`;
- mudanças em handoff interativo, prompts, senha, `toolbox`, `distrobox`, `rpm-ostree` ou AUR;
- qualquer alteração cuja honestidade só apareça no terminal real.

## Leitura correta da v0.7.0

- `tests/release_gate_canonic_line.sh` continua sendo a régua corrente da linha;
- `tests/release_gate_v0_6_2.sh` continua como gate histórico;
- `tests/release_gate_iteracao.sh`, `tests/release_gate_pre_push.sh` e `tests/release_gate_pre_release.sh` organizam a rotina operacional por etapa;
- gate automatizado não substitui checklist humano;
- checklist humano não substitui terminal real;
- a `v0.7.0` preserva disciplina de subida, promove a superfície pública final pré-`v1.0.0` e não abre frente nova de domínio.
