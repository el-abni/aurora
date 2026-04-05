# 🌌 Aurora

![versão](https://img.shields.io/badge/vers%C3%A3o-v0.5.0-0f766e)
![linguagem](https://img.shields.io/badge/linguagem-Python-3776AB)
![plataforma](https://img.shields.io/badge/plataforma-Linux-orange)
![licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)

**Aurora** é uma assistente de terminal para **Linux**, escrita em **100% Python**, com política explícita, observabilidade própria e execução real sobre um contrato pequeno e auditável.

A release pública atual é a `v0.5.0`. Ela abre `toolbox` como **superfície operacional mediada explícita**, distinta do host e distinta das fontes terceiras já abertas em `AUR`, `COPR`, `PPA` e `flatpak`.

Na `v0.5.0`, a superfície pública continua pequena:

- `host_package` para pacotes do host no `execution_surface=host`;
- `AUR` como fonte explícita de terceiro dentro de `host_package`;
- `COPR` como fonte explícita de terceiro dentro de `host_package`;
- `PPA` como fonte explícita de terceiro dentro de `host_package`;
- `user_software` para software do usuário via `flatpak`;
- `toolbox` como `execution_surface` explícita para operar pacote distro-managed dentro de um ambiente mediado nomeado.

Leitura correta da `v0.5.0`:

- `toolbox` não é fonte de pacote;
- `toolbox` não é `host_package` com outro nome;
- `toolbox` não vira fallback automático quando o host não cabe;
- `toolbox` exige pedido explícito e ambiente explicitamente nomeado;
- `toolbox` usa `source_type=toolbox_host_package_manager` e `trust_level=mediated_environment`;
- `toolbox.instalar` e `toolbox.remover` exigem nome exato de pacote nesta release;
- `toolbox.procurar` existe justamente para descobrir esse nome;
- `host` e `toolbox` aparecem separados em request, policy, route, execution e `aurora dev`.

## O que a Aurora faz

A Aurora funciona como uma camada de decisão e execução sobre Linux. Em vez de esconder escolha de rota atrás de heurística opaca, ela:

- classifica a frase;
- detecta o host Linux;
- observa a superfície mediada quando o pedido explicita `toolbox`;
- aplica política;
- escolhe a rota cabível no contrato atual;
- executa com probe de estado quando a ação muda software;
- expõe um `decision_record` auditável com `aurora dev <frase>`.

## Contrato público da v0.5.0

Rotas reais abertas nesta release:

- `host_package.search`
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

Comportamento garantido:

- pedido nu continua em `host_package` no `execution_surface=host`;
- `AUR`, `COPR`, `PPA`, `flatpak` e `toolbox` só entram por frase explicitamente marcada;
- `toolbox` exige nome explícito de ambiente como `na toolbox <ambiente>`;
- não existe default implícito de toolbox, autoseleção nem descoberta mágica de ambiente;
- `toolbox` observa o ambiente nomeado antes de abrir policy e rota;
- `toolbox` observa qual backend distro-managed está disponível dentro da toolbox e deixa isso visível em `decision_record`;
- `toolbox.instalar` e `toolbox.remover` aceitam apenas nome exato de pacote nesta release;
- `toolbox.remover` exige `--confirm`;
- `toolbox` não se combina com `aur`, `copr`, `ppa` ou remotes `flatpak`;
- `decision_record` e `aurora dev` deixam visíveis `execution_surface`, `environment_target`, `environment_resolution`, `toolbox_profile`, capacidades observadas, gaps e fronteira host vs toolbox;
- host Atomic/imutável continua bloqueado em `host_package`, e isso não muda o default do produto.
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

## Observabilidade

```bash
aurora dev "procurar firefox"
aurora dev "instalar firefox no flatpak"
aurora dev "instalar google chrome no aur --confirm"
aurora dev "procurar obs-studio do copr atim/obs-studio"
aurora dev "instalar obs-studio do ppa ppa:obsproject/obs-studio --confirm"
aurora dev "procurar ripgrep na toolbox devbox"
```

## Compatibilidade Linux

### `host_package`

- suportado agora: Arch/derivadas mutáveis, Debian/Ubuntu/derivadas mutáveis e Fedora mutável;
- suportado contido: OpenSUSE mutável;
- bloqueado por política: hosts Atomic/imutáveis.

### `AUR` explícito

- suportado agora: hosts Arch/derivados mutáveis com `paru` ou `yay` observado;
- usa política própria, `source_type=aur_repository` e `trust_level=third_party_build`;
- `aur.instalar` pode abrir fluxo interativo real do helper;
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
- pode funcionar mesmo quando o host é Atomic/imutável, mas isso não equivale a suporte operacional real a imutáveis;
- não cria toolbox, não administra lifecycle amplo e não vira fallback automático do host.

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

No help público, a versão aparece como:

```text
🌌 Aurora v0.5.0
```

## O que a v0.5.0 não promete

A Aurora ainda não abre:

- fallback automático de pedido nu para AUR;
- fallback automático do host para `toolbox`;
- default implícito de toolbox;
- criação automática de toolbox e administração geral de ambientes;
- mistura de `toolbox` com AUR, COPR, PPA ou remotes `flatpak`;
- canonicalização ampla de alvo para `toolbox.instalar` e `toolbox.remover`;
- descoberta automática de repositório COPR;
- descoberta automática de PPA ou inferência de PPA a partir do nome do pacote;
- `ppa.procurar`, `ppa.remover` real, cleanup automático, `remove-apt-repository` e lifecycle amplo de PPA;
- descoberta automática de remotes `flatpak`;
- add automático de remote arbitrário;
- administração geral de remotes `flatpak`;
- AppImage e GitHub Releases;
- distrobox, `rpm-ostree` e `ujust`;
- suporte operacional real a hosts imutáveis;
- manutenção ampla do host;
- backlog amplo de arquivos e rede.

## Documentação

A documentação complementar desta release fica em:

- [Arquitetura](docs/ARCHITECTURE.md)
- [Compatibilidade Linux](docs/COMPATIBILITY_LINUX.md)
- [Política de Instalação](docs/INSTALLATION_POLICY.md)
- [Mapa de Herança da Aury](docs/AURY_HERITAGE_MAP.md)

## Licença

Este projeto é distribuído sob a licença **MIT**.
