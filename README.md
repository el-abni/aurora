# 🌌 Aurora

![versão](https://img.shields.io/badge/vers%C3%A3o-v0.4.1-0f766e)
![linguagem](https://img.shields.io/badge/linguagem-Python-3776AB)
![plataforma](https://img.shields.io/badge/plataforma-Linux-orange)
![licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)

**Aurora** é uma assistente de terminal para **Linux**, escrita em **100% Python**, com política explícita, observabilidade própria e execução real sobre um contrato pequeno e auditável.

A release pública atual é a `v0.4.1`. Ela amplia `flatpak` com **remote explícito e contido**, preservando `flathub` como default quando nada é informado e sem abrir descoberta, add automático ou administração geral de remotes.

Na `v0.4.1`, a superfície pública cobre dois domínios reais, três famílias explícitas de fonte terceira no host e uma frente `flatpak` com seleção explícita de remote:

- `host_package` para pacotes do host;
- `AUR` como fonte explícita de terceiro dentro de `host_package`;
- `COPR` como fonte explícita de terceiro dentro de `host_package`;
- `PPA` como fonte explícita de terceiro dentro de `host_package`;
- `user_software` para software do usuário via `flatpak`.

Pedidos nus, como `aurora procurar firefox`, continuam no default seguro de `host_package`. Pedidos explicitamente marcados como `aur`, `copr`, `ppa` ou `flatpak` entram apenas nessas frentes explícitas.

## O que a Aurora faz

A Aurora funciona como uma camada de decisão e execução sobre Linux. Em vez de esconder escolha de rota atrás de heurística opaca, ela:

- classifica a frase;
- detecta o host Linux;
- aplica política;
- escolhe a rota cabível no contrato atual;
- executa com probe de estado quando a ação muda software;
- expõe um `decision_record` auditável com `aurora dev <frase>`.

## Contrato público da v0.4.1

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

Comportamento garantido:

- `host_package` continua sendo o default para pedidos nus;
- `AUR` só entra quando a frase marca `aur`;
- `COPR` só entra quando a frase marca `copr` e traz `owner/project`;
- `PPA` só entra quando a frase marca `ppa` e traz a coordenada canônica `ppa:owner/name`;
- `flatpak` só entra quando a frase marca `flatpak` ou `flathub`;
- `flatpak.procurar` e `flatpak.instalar` usam `flathub` como default quando nenhum remote é informado;
- `flatpak` aceita remote explícito no formato `no flatpak <remote>` ou `no flathub`, mas só quando esse remote já foi observado no host;
- `decision_record` e `aurora dev` deixam visíveis `requested_source`, `source_coordinate`, capacidades observadas, gaps e passos preparatórios;
- `aur.instalar`, `aur.remover`, `copr.instalar`, `copr.remover` e `ppa.instalar` exigem confirmação explícita;
- `--confirm` e `--yes` funcionam como confirmação explícita, inclusive quando aparecem inline numa frase passada como texto único ou inspecionada em `aurora dev`;
- `aur.instalar` pode entregar o terminal ao helper para revisão/build interativos;
- `copr.procurar` consulta apenas o repositório explicitamente pedido;
- `copr.remover` só executa quando a origem RPM do pacote instalado fecha com o repositório explícito informado via `from_repo`;
- `ppa.instalar` planeja `add-apt-repository`, `apt-get update` e `apt-get install` de forma explícita e auditável;
- `ppa.remover` permanece bloqueado por honestidade, porque a Aurora ainda não demonstra proveniência APT por PPA nem lifecycle amplo do repositório;
- mutações usam probe antes e depois, com `noop` honesto quando nada precisa mudar.

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

## Observabilidade

```bash
aurora dev "procurar firefox"
aurora dev "instalar firefox no flatpak"
aurora dev "instalar google chrome no aur --confirm"
aurora dev "procurar obs-studio do copr atim/obs-studio"
aurora dev "instalar obs-studio do ppa ppa:obsproject/obs-studio --confirm"
aurora dev "remover obs-studio do ppa ppa:obsproject/obs-studio"
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
- `copr.instalar` observa o estado do repositório e só planeja `enable` quando necessário;
- `copr.remover` verifica `from_repo` antes da mutação;
- nenhuma rota COPR faz disable automático ou cleanup heurístico do repositório.

### `PPA` explícito

- suportado agora: **Ubuntu mutável** com `apt-get`, `dpkg` e `add-apt-repository` observados;
- exige marcação explícita de fonte com `ppa` e coordenada canônica `ppa:owner/name`;
- usa política própria, `source_type=ppa_repository` e `trust_level=third_party_repository`;
- `ppa.instalar` planeja `add-apt-repository -n`, `apt-get update` e `apt-get install` como passos preparatórios explícitos;
- `ppa.remover` continua bloqueado por honestidade nesta release;
- Debian puro e outras derivadas Debian-like continuam bloqueados nesta frente;
- URL genérica de apt repo não entra como PPA.

### `user_software` via `flatpak`

- depende do backend `flatpak` estar presente no host;
- atua em escopo de usuário, sem mutação do pacote do host;
- vale também em hosts Atomic/imutáveis quando o pedido explicita `flatpak`;
- preserva `flathub` como default para `flatpak.procurar` e `flatpak.instalar` quando nenhum remote é informado;
- aceita remote explícito apenas quando ele já é observável via `flatpak remotes` no host;
- `flatpak.procurar` respeita o remote selecionado via `flatpak remote-ls` filtrado localmente;
- `flatpak.remover` só usa remote explícito como restrição honesta de `origin`, sem assumir default para remoção;
- continua pequeno: não há add automático, descoberta ampla nem administração geral de remotes.

Ferramenta observada no host não vira promessa de suporte automaticamente. A Aurora só abre rota onde já existe política, execução real e auditoria.

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
🌌 Aurora v0.4.1
```

## O que a v0.4.1 não promete

A Aurora ainda não abre:

- fallback automático de pedido nu para AUR;
- descoberta automática de repositório COPR;
- descoberta automática de PPA ou inferência de PPA a partir do nome do pacote;
- `ppa.procurar`, `ppa.remover` real, cleanup automático, `remove-apt-repository` e lifecycle amplo de PPA;
- tratamento de URL genérica de apt repo como se fosse PPA;
- promessa ampla para qualquer Debian-like fora de Ubuntu mutável;
- descoberta automática de remotes `flatpak`;
- add automático de remote arbitrário;
- administração geral de remotes `flatpak`;
- AppImage e GitHub Releases;
- `rpm-ostree`, toolbox, distrobox e `ujust`;
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
