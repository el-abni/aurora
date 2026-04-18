# 🌌 Aurora

![versão](https://img.shields.io/badge/vers%C3%A3o-v1.0.0-0f766e)
![linguagem](https://img.shields.io/badge/linguagem-Python-3776AB)
![plataforma](https://img.shields.io/badge/plataforma-Linux-orange)
![licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)

**Aurora** é uma assistente de terminal para **Linux**, escrita em **100% Python**, com política explícita, observabilidade própria e execução real sobre um contrato pequeno e auditável.

A release pública atual é a `v1.0.0`. Ela não redesenha o produto nem abre frente lateral: promove com honestidade o estado já fechado nas Fases `0` a `3` da seam `local_model` sobre a espinha canônica fechada na `v0.6.3` e a disciplina operacional fechada na `v0.6.4`. O provider real entra hoje apenas pela seam observável de `aurora dev` / `decision_record`, com `model_off` íntegro por default, `model_on` opcional e assistivo e fallback determinístico quando a borda falha. Os detalhes longos continuam em `README/docs`, não no help.

Na `v1.0.0`, a superfície pública continua pequena e deliberadamente próxima da `v0.7.0`:

- `host_package` para pacotes do host no `execution_surface=host`;
- `AUR` como fonte explícita de terceiro dentro de `host_package`;
- `COPR` como fonte explícita de terceiro dentro de `host_package`;
- `PPA` como fonte explícita de terceiro dentro de `host_package`;
- `user_software` para software do usuário via `flatpak`;
- `toolbox` como `execution_surface` explícita para operar pacote distro-managed dentro de um ambiente mediado nomeado;
- `distrobox` como `execution_surface` explícita para operar pacote distro-managed dentro de um ambiente mediado nomeado.
- `rpm-ostree` como `execution_surface` explícita para layering/uninstall no host imutável.

## Espinha canônica da linha

A `v1.0.0` reaproveita uma lição já aprendida pela Aurora: endurecimento de linha pede regra executável e docs canônicas curtas, não feature nova. Por isso, a espinha fechada na `v0.6.3` continua amarrada por:

- `tests/release_gate_canonic_line.sh` como régua corrente da linha;
- `tests/release_gate_v0_6_2.sh` como gate histórico da release `v0.6.2`;
- `tests/README.md` como papel canônico da pasta `tests/`;
- `docs/AURORA_INVARIANTS.md` como registro curto das lições já provadas pela Aurora;
- `docs/DECISION_RECORD_SCHEMA.md` como contrato curto do `decision_record`;
- `docs/FACTS_VS_RENDERING.md` como fronteira explícita entre fato operacional e voz;
- `docs/AURY_TO_AURORA_DOSSIER.md` como dossiê canônico de herança e limite entre Aury e Aurora.

Leitura correta da `v1.0.0`:

- `toolbox` não é fonte de pacote;
- `toolbox` não é `host_package` com outro nome;
- `toolbox` não vira fallback automático quando o host não cabe;
- `toolbox` exige pedido explícito e ambiente explicitamente nomeado;
- `toolbox` usa `source_type=toolbox_host_package_manager` e `trust_level=mediated_environment`;
- `toolbox.instalar` e `toolbox.remover` exigem nome exato de pacote nesta release;
- `toolbox.procurar` existe justamente para descobrir esse nome;
- `distrobox` também não é fonte, não é alias de `toolbox`, não vira fallback automático e exige ambiente explicitamente nomeado;
- `distrobox` usa `source_type=distrobox_host_package_manager` e `trust_level=mediated_environment`;
- `distrobox.instalar` e `distrobox.remover` exigem nome exato de pacote nesta release;
- `distrobox.procurar` existe justamente para descobrir esse nome;
- `toolbox` e `distrobox` compartilham apenas o miolo de pacote distro-managed dentro do ambiente; observação, seleção, semântica e auditabilidade continuam explícitas por superfície;
- `rpm-ostree` não é backend mágico para qualquer mutação no host;
- `rpm-ostree` usa `execution_surface=rpm_ostree`, `source_type=rpm_ostree_layering` e `trust_level=immutable_host_surface`;
- `rpm_ostree.instalar` e `rpm_ostree.remover` exigem nome exato de pacote;
- `rpm_ostree.procurar` ainda não foi aberta;
- `rpm-ostree` observa `status --json`, bloqueia quando já existe `pending deployment` ou transação ativa e deixa explícito quando a mudança vai para o próximo deployment;
- pedido nu em host imutável não sofre fallback mágico: a Aurora mostra as superfícies observadas e bloqueia quando a frase não escolhe uma delas;
- `host`, `toolbox`, `distrobox` e `rpm_ostree` aparecem separados em request, policy, route, execution e `aurora dev`.

## Workflow operacional da v1.0.0

A `v1.0.0` preserva uma lição que o repositório já vinha ensinando: gate automatizado sozinho não segura release honesta quando a superfície pública ainda depende de docs, help, renderização, launchers e terminal real.

Por isso, esta release amarra:

- `docs/WORKFLOW_DE_TESTES_E_RELEASE.md` como workflow canônico curto;
- `tests/REVIEW_CHECKLIST.md` como checklist humano de revisão;
- `tests/release_gate_iteracao.sh` como gate de coding comum;
- `tests/release_gate_pre_push.sh` como gate antes de push;
- `tests/release_gate_pre_release.sh` como gate automatizado antes de tag e release;
- separação explícita entre teste automático, revisão manual e teste real no terminal local;
- `tests/release_gate_v0_6_2.sh` preservado como gate histórico exercitado no fechamento mais duro, sem virar régua corrente da linha.

O foco da `v1.0.0` é superfície pública curta sobre a espinha já canonizada:

- `tests/release_gate_canonic_line.sh` continua como régua corrente da linha;
- `tests/README.md` passa a explicar o papel dos gates por etapa;
- `docs/AURORA_INVARIANTS.md` passa a registrar que gate automatizado não substitui revisão humana nem terminal real;
- o `decision_record` continua em `schema=aurora.decision_record.v1`, com `stable_ids`, `facts` e `presentation` sem abertura de contrato novo;
- a espinha da linha continua 100% Python, sem puxar Fish ou stage pública para o centro da Aurora;
- o help público volta a priorizar uso rápido, enquanto compatibilidade, limites e workflow detalhado continuam neste README e nos docs centrais.

## O que a v1.0.0 fecha estruturalmente

A `v1.0.0` torna pública uma leitura que já estava fechada no checkout:

- o baseline factual dos cortes `1` e `2` sai da zona de hotspot principal;
- a observabilidade canônica do corte `3` passa a ser parte assumida da linha pública;
- `local_model/` entra como seam pequena e explícita, com `model_off` como modo íntegro por default;
- o provider real canônico `ollama` entra apenas nessa seam observável, com `qwen2.5:3b-instruct` como modelo canônico inicial;
- `model_on` continua apenas como camada assistiva opcional, com fallback determinístico e autoridade limitada;
- `fallback_reason` permanece factual em dialeto canônico curto e `output_text` permanece preservado cru como fato;
- essa seam pode clarificar, resumir, explicar e desambiguar candidatos já estruturados, mas não pode decidir `policy`, bloqueio, confirmação, rota, execução ou verdade operacional.

## Seam `local_model`

A leitura correta desta abertura é curta:

- sem variável de ambiente, `aurora dev` continua em `model_off`;
- `model_on` só entra quando `AURORA_MODEL_MODE=model_on` e `AURORA_LOCAL_MODEL_PROVIDER=ollama`;
- o provider canônico atual é `ollama`, com `qwen2.5:3b-instruct` como modelo canônico inicial quando `AURORA_LOCAL_MODEL_MODEL` não é informado;
- a seam consome `schema + stable_ids + facts + presentation`, mas não decide `policy`, suporte, bloqueio, confirmação, rota, execução ou verdade operacional;
- se o provider faltar, falhar, expirar ou sair do contrato, a linha cai em fallback determinístico e o kernel permanece suficiente;
- `aurora dev` mostra um bloco técnico curto `Local model seam`; `fallback_reason` e `output_text` permanecem fatos crus, sem polimento textual.

## O que a Aurora faz

A Aurora funciona como uma camada de decisão e execução sobre Linux. Em vez de esconder escolha de rota atrás de heurística opaca, ela:

- classifica a frase;
- detecta o host Linux;
- observa a superfície mediada quando o pedido explicita `toolbox` ou `distrobox`;
- observa `rpm-ostree` quando o pedido explicita a superfície imutável do host;
- aplica política;
- escolhe a rota cabível no contrato atual;
- executa com probe de estado quando a ação muda software;
- expõe um `decision_record` auditável com `aurora dev <frase>`, incluindo `immutable_observed_surfaces`, `immutable_selected_surface` e `rpm_ostree_status` quando cabível.

## Decision Record Canônico

Na `v1.0.0`, a leitura parseável do `decision_record` continua sendo:

- `schema.schema_id=aurora.decision_record.v1`;
- `stable_ids.action_id`, `stable_ids.route_id` e `stable_ids.event_id` como IDs mínimos estáveis;
- `facts` como seção canônica do estado operacional;
- `presentation` como seção de voz e renderização.
- `facts.local_model` como seam factual assistiva, com `mode`, `status`, `requested_capability`, `provider_name`, `fallback_reason` e `output_text` quando couber.

Compatibilidade desta linha:

- o payload antigo continua espelhado no topo por compatibilidade com a base já aberta;
- `host_package.search` continua existindo apenas como `route_name` legado; o ID canônico da rota é `host_package.procurar`.

## Contrato público da v1.0.0

Rotas reais abertas nesta release:

- `host_package.procurar`
- `host_package.instalar`
- `host_package.remover`
- `aur.procurar`
- `aur.instalar`
- `aur.remover`
- `copr.procurar`
- `copr.instalar`
- `copr.remover`
- `ppa.instalar`
- `flatpak.procurar`
- `flatpak.instalar`
- `flatpak.remover`
- `toolbox.procurar`
- `toolbox.instalar`
- `toolbox.remover`
- `distrobox.procurar`
- `distrobox.instalar`
- `distrobox.remover`
- `rpm_ostree.instalar`
- `rpm_ostree.remover`

Comportamento garantido:

- pedido nu continua em `host_package` no `execution_surface=host`;
- `AUR`, `COPR`, `PPA`, `flatpak` e `toolbox` só entram por frase explicitamente marcada;
- `toolbox` exige nome explícito de ambiente como `na toolbox <ambiente>`;
- não existe default implícito de toolbox, autoseleção nem descoberta mágica de ambiente;
- `toolbox` observa o ambiente nomeado antes de abrir policy e rota;
- `toolbox` observa qual backend distro-managed está disponível dentro da toolbox e deixa isso visível em `decision_record`;
- `toolbox.instalar` e `toolbox.remover` aceitam apenas nome exato de pacote nesta release;
- `toolbox.remover` exige `--confirm`;
- mutações em `toolbox` avisam quando a execução mediada começa, quando pode haver espera silenciosa ou senha e quando a Aurora ainda vai validar o estado final;
- `distrobox` exige nome explícito de ambiente como `na distrobox <ambiente>`;
- não existe default implícito de distrobox, autoseleção nem descoberta mágica de ambiente;
- `distrobox` observa o ambiente nomeado antes de abrir policy e rota;
- `distrobox` observa qual backend distro-managed está disponível dentro da distrobox e deixa isso visível em `decision_record`;
- `distrobox.instalar` e `distrobox.remover` aceitam apenas nome exato de pacote nesta release;
- `distrobox.remover` exige `--confirm`;
- mutações em `distrobox` avisam quando a execução mediada começa, quando pode haver espera silenciosa ou senha e quando a Aurora ainda vai validar o estado final;
- `rpm-ostree` entra apenas por frase marcada como `no rpm-ostree`;
- `rpm_ostree.instalar` e `rpm_ostree.remover` aceitam apenas nome exato de pacote nesta release;
- `rpm_ostree.remover` exige `--confirm`;
- `rpm-ostree` observa `status --json` antes de liberar mutação e bloqueia se houver `pending deployment` ou transação ativa;
- `toolbox`, `distrobox` e `rpm-ostree` não se combinam entre si nem com `aur`, `copr`, `ppa` ou remotes `flatpak`;
- `decision_record` e `aurora dev` deixam visíveis `execution_surface`, `environment_target`, `environment_resolution`, `toolbox_profile`, `distrobox_profile`, `rpm_ostree_status`, `immutable_observed_surfaces`, `immutable_selected_surface`, capacidades observadas, gaps e fronteira host vs ambiente mediado ou host imutável;
- host Atomic/imutável já não é apenas bloqueio genérico: `flatpak`, `toolbox`, `distrobox` e `rpm-ostree` podem ser escolhidos explicitamente, e pedido nu bloqueia com inventário das superfícies observadas.
- `--confirm` e `--yes` funcionam como marcadores equivalentes de confirmação explícita quando a política exigir.

## Exemplos rápidos

### Pacotes do host

```bash
aurora procurar firefox
aurora instalar firefox
aurora instalar sudo --confirm
aurora remover firefox
aurora remover sudo --confirm
```

### Pacotes AUR explícitos

```bash
aurora procurar google chrome no aur
aurora instalar google chrome no aur --confirm
aurora remover google chrome no aur --confirm
```

### Pacotes COPR explícitos

```bash
aurora procurar obs-studio do copr atim/obs-studio
aurora instalar yt-dlp do copr atim/ytdlp --confirm
aurora remover yt-dlp do copr atim/ytdlp --confirm
```

### Pacotes PPA explícitos

```bash
aurora instalar obs-studio do ppa ppa:obsproject/obs-studio --confirm
aurora dev "remover obs-studio do ppa ppa:obsproject/obs-studio"
```

### Software do usuário via Flatpak

```bash
aurora procurar firefox no flatpak
aurora instalar firefox no flatpak
aurora procurar firefox no flatpak flathub-beta
aurora remover firefox no flatpak --confirm
```

### Pacotes dentro de toolbox explícita

```bash
aurora procurar ripgrep na toolbox devbox
aurora instalar ripgrep na toolbox devbox
aurora remover ripgrep na toolbox devbox --confirm
aurora dev "instalar obs-studio na toolbox devbox"
```

### Pacotes dentro de distrobox explícita

```bash
aurora procurar ripgrep na distrobox devbox
aurora instalar ripgrep na distrobox devbox
aurora remover ripgrep na distrobox devbox --confirm
aurora dev "instalar obs-studio na distrobox devbox"
```

### Host imutável via `rpm-ostree`

```bash
aurora instalar htop no rpm-ostree
aurora remover htop no rpm-ostree --confirm
aurora dev "instalar htop no rpm-ostree"
```

## Observabilidade

```bash
aurora dev "procurar firefox"
aurora dev "instalar firefox no flatpak"
aurora dev "instalar google chrome no aur --confirm"
aurora dev "procurar obs-studio do copr atim/obs-studio"
aurora dev "instalar obs-studio do ppa ppa:obsproject/obs-studio --confirm"
aurora dev "procurar ripgrep na toolbox devbox"
aurora dev "procurar ripgrep na distrobox devbox"
aurora dev "instalar htop no rpm-ostree"
AURORA_MODEL_MODE=model_on AURORA_LOCAL_MODEL_PROVIDER=ollama aurora dev "procurar firefox"
AURORA_MODEL_MODE=model_on AURORA_LOCAL_MODEL_PROVIDER=ollama AURORA_LOCAL_MODEL_URL=http://127.0.0.1:11434/indisponivel aurora dev "procurar firefox"
```

## Compatibilidade Linux

### `host_package`

- suportado agora: Arch/derivadas mutáveis, Debian/Ubuntu/derivadas mutáveis e Fedora mutável;
- suportado contido: OpenSUSE mutável;
- em hosts Atomic/imutáveis, pedido nu bloqueia cedo e exige escolha explícita entre `flatpak`, `toolbox`, `distrobox`, `rpm-ostree` ou bloqueio.

### `AUR` explícito

- suportado agora: hosts Arch/derivados mutáveis com `paru` ou `yay` observado;
- usa política própria, `source_type=aur_repository` e `trust_level=third_party_build`;
- `aur.instalar` pode abrir fluxo interativo real do helper e prepara explicitamente o usuário para prompts e retorno do terminal;
- o fluxo AUR também avisa sobre pausa silenciosa de build e possibilidade de Enter extra ao final em alguns terminais;
- a confirmação pós-instalação AUR valida a presença final no host, sem depender apenas de `pacman -Qm`;
- `aur.remover` continua fora do passthrough interativo desta release;
- helper AUR fora do contrato não vira fallback nem rota executável.

### `COPR` explícito

- suportado agora: Fedora mutável com `dnf` e capacidade `dnf copr` observados;
- exige marcação explícita de fonte com `copr` e coordenada `owner/project`;
- usa política própria, `source_type=copr_repository` e `trust_level=third_party_repository`;
- `copr.procurar` consulta apenas o repositório explicitamente pedido;
- `copr.remover` verifica `from_repo` antes da mutação.

### `PPA` explícito

- suportado agora: **Ubuntu mutável** com `apt-get`, `dpkg` e `add-apt-repository` observados;
- exige marcação explícita de fonte com `ppa` e coordenada canônica `ppa:owner/name`;
- usa política própria, `source_type=ppa_repository` e `trust_level=third_party_repository`;
- `ppa.instalar` planeja `add-apt-repository -n`, `apt-get update` e `apt-get install` como passos preparatórios explícitos;
- `ppa.remover` continua bloqueado por honestidade.

### `user_software` via `flatpak`

- depende do backend `flatpak` estar presente no host;
- atua em escopo de usuário, sem mutação do pacote do host;
- vale também em hosts Atomic/imutáveis quando o pedido explicita `flatpak`;
- em host imutável, `decision_record` marca `immutable_selected_surface=flatpak`;
- preserva `flathub` como default para `flatpak.procurar` e `flatpak.instalar`;
- aceita remote explícito apenas quando ele já é observável via `flatpak remotes`.
- `flatpak.procurar` usa `flatpak remote-ls` no remote selecionado.

### `toolbox` explícita

- depende do comando `toolbox` estar presente no host;
- exige ambiente explicitamente nomeado;
- opera apenas dentro da toolbox selecionada, nunca no host;
- observa a família Linux e os `package_backends` dentro da toolbox antes de liberar a rota;
- cobre `procurar`, `instalar` e `remover`;
- `toolbox.instalar` e `toolbox.remover` exigem nome exato de pacote nesta release;
- `toolbox.remover` exige confirmação explícita;
- pode funcionar mesmo quando o host é Atomic/imutável, e nesse caso o `decision_record` marca `immutable_selected_surface=toolbox`;
- não cria toolbox, não administra lifecycle amplo e não vira fallback automático do host.

### `distrobox` explícita

- depende do comando `distrobox` estar presente no host;
- exige ambiente explicitamente nomeado;
- opera apenas dentro da distrobox selecionada, nunca no host;
- observa a família Linux e os `package_backends` dentro da distrobox antes de liberar a rota;
- cobre `procurar`, `instalar` e `remover`;
- `distrobox.instalar` e `distrobox.remover` exigem nome exato de pacote nesta release;
- `distrobox.remover` exige confirmação explícita;
- pode funcionar mesmo quando o host é Atomic/imutável, e nesse caso o `decision_record` marca `immutable_selected_surface=distrobox`;
- não cria distrobox, não administra lifecycle amplo e não vira fallback automático do host;
- não apaga a diferença para `toolbox`: a Aurora observa e roteia `distrobox` como superfície própria.

### `rpm-ostree` explícito

- depende do comando `rpm-ostree` estar presente no host;
- só abre como superfície explícita de host imutável;
- cobre `rpm_ostree.instalar` e `rpm_ostree.remover`;
- `rpm_ostree.procurar` continua fora do corte;
- exige nome exato de pacote;
- observa `rpm-ostree status --json` antes da mutação;
- bloqueia quando já existe `pending deployment` ou transação ativa;
- `rpm_ostree.remover` exige confirmação explícita;
- uma execução bem-sucedida pode exigir reboot para aplicar o deployment resultante.

Ferramenta observada no host não vira promessa de suporte automaticamente. A Aurora só abre rota onde já existe policy, execução real e auditoria.

## Instalação

Instalação pública padrão:

```bash
git clone https://github.com/el-abni/aurora.git
cd aurora
./install.sh
```

O script instala a superfície pública em:

- `~/.local/share/aurora`
- `~/.local/bin/aurora`
- `~/.local/bin/auro`

Depois da instalação, valide com:

```bash
aurora --version
aurora --help
```

Remoção:

```bash
./uninstall.sh
```

## Como usar

Para ver o help público:

```bash
auro --help
aurora --help
```

A identidade pública da ferramenta é:

```text
🌌 Aurora
```

Na `v1.0.0`, o help público continua sendo superfície curta de uso. Compatibilidade detalhada, limites e workflow continuam no README e nos docs.

No help público, a versão aparece como:

```text
🌌 Aurora v1.0.0
```

## O que a v1.0.0 não promete

A Aurora ainda não abre:

- fallback automático de pedido nu para AUR;
- fallback automático do host para `toolbox`;
- fallback automático do host para `distrobox`;
- fallback automático do host para `rpm-ostree`;
- default implícito de toolbox;
- default implícito de distrobox;
- criação automática de toolbox, criação automática de distrobox e administração geral de ambientes;
- mistura de `toolbox`, `distrobox` ou `rpm-ostree` com AUR, COPR, PPA ou remotes `flatpak`;
- canonicalização ampla de alvo para `toolbox.instalar` e `toolbox.remover`;
- canonicalização ampla de alvo para `distrobox.instalar` e `distrobox.remover`;
- `rpm_ostree.procurar`, `apply-live`, `override remove`, reboot automático e chaining amplo de transações;
- descoberta automática de repositório COPR;
- descoberta automática de PPA ou inferência de PPA a partir do nome do pacote;
- `ppa.procurar`, `ppa.remover` real, cleanup automático, `remove-apt-repository` e lifecycle amplo de PPA;
- descoberta automática de remotes `flatpak`;
- add automático de remote arbitrário;
- administração geral de remotes `flatpak`;
- múltiplos providers públicos ou seleção automática entre providers;
- múltiplos modelos canônicos públicos;
- uso do modelo local fora da seam assistiva observável de `aurora dev` / `decision_record`;
- qualquer autoridade do modelo sobre policy, suporte, bloqueio, confirmação, rota, execução ou resultado operacional;
- AppImage e GitHub Releases;
- `ujust`;
- suporte genérico a hosts imutáveis fora do recorte `flatpak`/`toolbox`/`distrobox`/`rpm-ostree`;
- manutenção ampla do host;
- backlog amplo de arquivos e rede.

## Documentação

A documentação complementar desta release fica em:

- [Arquitetura](docs/ARCHITECTURE.md)
- [Compatibilidade Linux](docs/COMPATIBILITY_LINUX.md)
- [Política de Instalação](docs/INSTALLATION_POLICY.md)
- [Mapa de Herança da Aury](docs/AURY_HERITAGE_MAP.md)
- [Invariantes da Aurora](docs/AURORA_INVARIANTS.md)
- [Schema do Decision Record](docs/DECISION_RECORD_SCHEMA.md)
- [Facts vs Rendering](docs/FACTS_VS_RENDERING.md)
- [Dossiê Aury -> Aurora](docs/AURY_TO_AURORA_DOSSIER.md)
- [Workflow de Testes e Release](docs/WORKFLOW_DE_TESTES_E_RELEASE.md)
- [Papel Canônico de tests/](tests/README.md)
- [Checklist de Revisão](tests/REVIEW_CHECKLIST.md)

## Licença

Este projeto é distribuído sob a licença **MIT**.
