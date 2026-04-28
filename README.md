# 🌌 Aurora

![versão](https://img.shields.io/badge/vers%C3%A3o-v1.2.0-0f766e)
![linguagem](https://img.shields.io/badge/linguagem-Python-3776AB)
![plataforma](https://img.shields.io/badge/plataforma-Linux-orange)
![licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)

**Aurora** é uma assistente de terminal para **Linux**, escrita em **100% Python**, com contrato pequeno, política explícita, execução real e observabilidade própria.

A release pública atual é a `v1.2.0`. Ela adiciona uma camada pequena de conversação/mediação determinística em PT-BR para ajuda e orientação. A absorção `host_maintenance.atualizar` fechada na `v1.1.0` continua igual: `aurora atualizar sistema --confirm` em host Arch mutável com `pacman` observado, confirmação explícita obrigatória e backend `sudo + pacman`.

## O que é

A Aurora recebe uma frase curta em português, enquadra a ação, observa o host ou a superfície explicitamente pedida, aplica política e então executa, bloqueia ou mostra uma leitura técnica. Ela não é um chat genérico e não promete entender qualquer frase.

O centro da linha continua determinístico. O `decision_record` é o contrato canônico de inspeção, e a seam `local_model` continua apenas assistiva e observável quando habilitada por opt-in.

## Uso rápido

```bash
aurora ajuda
auro ajuda
aurora --version
aurora versão
aurora exemplos
aurora como instalar firefox?
aurora dev "procurar firefox"
```

`auro` é o launcher curto de `aurora`. Use `aurora dev <frase>` quando quiser ver a decisão antes de confiar numa frase ou numa superfície.

## Conversação e orientação

A `v1.2.0` aceita tópicos fechados como `aurora exemplos`, `aurora limites`, `aurora comandos`, `aurora fontes`, `aurora modelo local`, `aurora decision record`, `aurora o que você faz` e `aurora como eu uso`.

Perguntas fechadas como `aurora como instalar firefox?`, `aurora como procurar firefox?`, `aurora como remover firefox?` e `aurora como atualizar sistema?` retornam orientação e exit 0. Elas não executam backend, não escolhem fonte, não fazem busca real, não pedem confirmação e não alteram o sistema.

## Exemplos

Pacotes do host:

```bash
aurora procurar firefox
aurora instalar firefox
aurora remover firefox --confirm
```

Manutenção explícita do host:

```bash
aurora atualizar sistema
aurora atualizar sistema --confirm
aurora dev "atualizar sistema"
```

Sem `--confirm`, `atualizar sistema` deve bloquear e pedir confirmação. Com `--confirm`, a rota real suportada hoje é `host_maintenance.atualizar` no Arch mutável observado, usando `sudo + pacman`.

Fontes explícitas:

```bash
aurora procurar google chrome no aur
aurora instalar google chrome no aur --confirm
aurora procurar obs-studio do copr atim/obs-studio
aurora instalar obs-studio do ppa ppa:obsproject/obs-studio --confirm
```

Software do usuário, ambientes e host imutável explícito:

```bash
aurora procurar firefox no flatpak
aurora instalar firefox no flatpak
aurora procurar ripgrep na toolbox devbox
aurora procurar ripgrep na distrobox devbox
aurora instalar htop no rpm-ostree
```

Esses exemplos existem porque a linha já tem rotas, política e observabilidade para essas superfícies. Eles não significam fallback automático entre host, AUR, COPR, PPA, Flatpak, toolbox, distrobox e rpm-ostree.

## Modelo local

Por padrão, `aurora dev` roda em `model_off`. Esse modo é completo para inspeção técnica e não depende de provedor local.

`model_on` só entra quando configurado explicitamente:

```bash
AURORA_MODEL_MODE=model_on AURORA_LOCAL_MODEL_PROVIDER=ollama aurora dev "procurar firefox"
```

O provider público atual é `ollama`; quando `AURORA_LOCAL_MODEL_MODEL` não é informado, o modelo canônico inicial é `qwen2.5:3b-instruct`. Se o provider faltar, falhar, expirar ou devolver saída fora do contrato, a Aurora registra fallback determinístico e mantém o kernel suficiente sozinho.

O modelo local pode ajudar a explicar, resumir, clarificar ou desambiguar candidatos já estruturados. Ele não decide policy, suporte, bloqueio, confirmação, rota, execução nem verdade operacional.

## Decision record

A leitura técnica pública fica em:

```bash
aurora dev "procurar firefox"
aurora dev "atualizar sistema"
```

O contrato canônico atual é `aurora.decision_record.v1`, com:

- `stable_ids` para ação, rota e evento;
- `facts` como chão operacional;
- `presentation` como voz e renderização.

Texto de ajuda, polimento e renderização não viram contrato. Quando um consumidor precisa de verdade operacional, deve ler `schema + stable_ids + facts + presentation`.

## Recorte atual

Na `v1.2.0`, a superfície pública continua pequena:

- `host_package` para pacotes do host;
- `host_maintenance.atualizar` para `atualizar sistema` no Arch mutável com `pacman`;
- orientação determinística de ajuda antes do executor, sem novo domínio operacional;
- AUR, COPR e PPA apenas quando a frase marca a fonte explicitamente;
- `user_software` via Flatpak;
- toolbox e distrobox apenas quando a frase nomeia o ambiente;
- rpm-ostree apenas quando a frase marca essa superfície.

Limites honestos:

- sem `otimizar`, cache, órfãos ou bundles amplos de manutenção do host;
- sem `paru`, `yay` ou helper AUR como backend de `host_maintenance`;
- sem AUR implícita em `atualizar sistema`;
- sem equivalência multi-distro para `host_maintenance.atualizar` nesta primeira absorção;
- sem fallback automático do host para toolbox, distrobox, rpm-ostree, Flatpak ou AUR;
- sem default implícito de toolbox ou distrobox;
- sem criação ou lifecycle amplo de ambientes;
- sem autoridade do modelo local sobre policy, suporte, bloqueio, confirmação, rota, execução ou resultado.

## Instalação

```bash
git clone https://github.com/el-abni/aurora.git
cd aurora
./install.sh
```

O script instala:

- `~/.local/share/aurora`
- `~/.local/bin/aurora`
- `~/.local/bin/auro`

Depois de instalar, valide:

```bash
aurora --version
aurora --help
```

Remoção:

```bash
./uninstall.sh
```

## Mais detalhes

- [Arquitetura](docs/ARCHITECTURE.md): módulos, superfícies e fronteira do kernel determinístico.
- [Compatibilidade Linux](docs/COMPATIBILITY_LINUX.md): matriz real de suporte, incluindo host mutável, Flatpak, toolbox, distrobox e rpm-ostree.
- [Política de Instalação](docs/INSTALLATION_POLICY.md): `policy`, confirmação, gaps e riscos por frente.
- [Schema do Decision Record](docs/DECISION_RECORD_SCHEMA.md): `aurora.decision_record.v1`, `stable_ids`, `facts` e `presentation`.
- [Facts vs Rendering](docs/FACTS_VS_RENDERING.md): separação entre fato operacional e apresentação.
- [Invariantes da Aurora](docs/AURORA_INVARIANTS.md): regras que a linha já provou e não deve reabrir sem motivo.
- [Dossiê Aury -> Aurora](docs/AURY_TO_AURORA_DOSSIER.md): herança disciplinar e limites entre as linhas.
- [Workflow de Testes e Release](docs/WORKFLOW_DE_TESTES_E_RELEASE.md): gates, revisão humana, terminal real e `tests/release_gate_canonic_line.sh`.
- [Papel Canônico de tests/](tests/README.md): base pública de audits, fixtures e regressões.
- [Checklist de Revisão](tests/REVIEW_CHECKLIST.md): revisão manual antes de push, tag ou release.
- [Changelog](CHANGELOG.md): histórico das releases públicas.

Ordem de leitura pública: `README.md` -> `docs/COMPATIBILITY_LINUX.md` -> `docs/INSTALLATION_POLICY.md` -> `docs/ARCHITECTURE.md` -> `docs/WORKFLOW_DE_TESTES_E_RELEASE.md` -> `tests/README.md` -> `CHANGELOG.md`.

## Licença

Este projeto é distribuído sob a licença **MIT**.
