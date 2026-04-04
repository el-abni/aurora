# 🌌 Aurora

![versão](https://img.shields.io/badge/vers%C3%A3o-v0.3.2-0f766e)
![linguagem](https://img.shields.io/badge/linguagem-Python-3776AB)
![plataforma](https://img.shields.io/badge/plataforma-Linux-orange)
![licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)

**Aurora** é uma assistente de terminal para **Linux**, escrita em **100% Python**, com política explícita, observabilidade própria e execução real sobre um contrato pequeno e auditável.

A release pública atual é a `v0.3.2`. Ela fecha o recorte **AUR contido** com helpers deliberados e observabilidade mais clara, sem reabrir a base já consolidada de `host_package`, `AUR` explícito, `COPR` explícito e `user_software` via `flatpak`.

Na `v0.3.2`, a superfície pública cobre dois domínios reais e duas fontes explícitas adicionais:

- `host_package` para pacotes do host;
- `AUR` como fonte explícita de terceiro dentro do escopo de pacote do host;
- `COPR` como fonte explícita de terceiro dentro do escopo de pacote do host;
- `user_software` para software do usuário via `flatpak`.

Pedidos nus, como `aurora procurar firefox`, continuam no default seguro de `host_package`. Pedidos explicitamente marcados como `aur`, como `aurora instalar google chrome no aur`, entram na frente AUR. Pedidos explicitamente marcados como `copr`, como `aurora instalar yt-dlp do copr atim/ytdlp --confirm`, entram na frente COPR. Pedidos explicitamente marcados como `flatpak` ou `flathub`, como `aurora instalar firefox no flatpak`, entram em `user_software`.

## O que a Aurora faz

A Aurora funciona como uma camada de decisão e execução sobre Linux. Em vez de esconder escolha de rota atrás de heurística opaca, ela:

- classifica a frase;
- detecta o host Linux;
- aplica política;
- escolhe a rota cabível no contrato atual;
- executa com probe de estado quando a ação muda software;
- e expõe um `decision_record` auditável com `aurora dev <frase>`.

## Contrato público da v0.3.2

Rotas reais abertas nesta release:

- `host_package.search`
- `host_package.instalar`
- `host_package.remover`
- `aur.procurar`
- `aur.instalar`
- `aur.remover`
- `copr.instalar`
- `copr.remover`
- `flatpak.procurar`
- `flatpak.instalar`
- `flatpak.remover`

Comportamento garantido:

- `host_package` continua sendo o default para pedidos nus;
- `AUR` só entra quando a frase marca `aur`;
- `AUR` continua separado do backend oficial do host e aceita apenas `paru` e `yay` nesta rodada contida;
- quando ambos estão observados, a Aurora escolhe automaticamente o primeiro helper suportado na ordem do contrato: `paru`, depois `yay`;
- `decision_record` e `aurora dev` expõem helpers AUR observados, helpers suportados nesta rodada e helper selecionado para a rota;
- `aur.instalar` e `aur.remover` exigem confirmação explícita;
- `--confirm` e `--yes` funcionam como confirmação explícita, inclusive quando aparecem inline numa frase passada como texto único ou inspecionada em `aurora dev`;
- `aur.instalar` pode entregar o terminal ao helper para revisão/build interativos;
- `aur.remover` permanece no caminho não interativo desta release;
- helper AUR observado fora do contrato continua bloqueando de forma honesta e não amplia a superfície pública;
- `COPR` só entra quando a frase marca `copr` e traz `owner/project` de forma explícita;
- `copr.instalar` e `copr.remover` exigem confirmação explícita;
- `copr.instalar` habilita explicitamente o repositório pedido antes da instalação;
- `COPR` só abre em Fedora mutável com `dnf copr` observado;
- `COPR` não faz descoberta automática de repositório nem canonicalização de nome de pacote por busca;
- `copr.remover` remove o pacote, mas não desabilita o repositório nem valida a origem RPM nesta rodada;
- `flatpak` só entra quando a frase marca `flatpak` ou `flathub`;
- `flatpak.instalar` e `flatpak.remover` usam escopo explícito de usuário;
- `flatpak.instalar` usa `flathub` como remote default nesta release;
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
aurora instalar yt-dlp do copr atim/ytdlp --confirm
aurora remover yt-dlp do copr atim/ytdlp --confirm
```

### Software do usuário via Flatpak

```bash
aurora procurar firefox no flatpak
aurora instalar firefox no flatpak
aurora remover firefox no flatpak --confirm
```

### Observabilidade

```bash
aurora dev "procurar firefox"
aurora dev "instalar firefox no flatpak"
aurora dev "instalar google chrome no aur --confirm"
aurora dev "instalar yt-dlp do copr atim/ytdlp --confirm"
aurora dev "remover sudo"
```

## Compatibilidade Linux

### `host_package`

- suportado agora: Arch/derivadas mutáveis, Debian/Ubuntu/derivadas mutáveis e Fedora mutável;
- suportado contido: OpenSUSE mutável;
- bloqueado por política: hosts Atomic/imutáveis.

### `AUR` explícito

- suportado agora: hosts Arch/derivados mutáveis com `paru` ou `yay` observado;
- exige marcação explícita de fonte com `aur`;
- usa política própria, `source_type=aur_repository` e `trust_level=third_party_build`;
- se ambos os helpers suportados estiverem observados, a seleção segue a ordem do contrato: `paru`, depois `yay`;
- `aur.instalar` pode abrir o fluxo interativo real do helper e volta para validação por probe quando o helper termina;
- `aur.remover` continua fora do passthrough interativo nesta release;
- helper AUR fora do contrato não vira fallback nem rota executável;
- não herda fallback implícito de `host_package`.

### `COPR` explícito

- suportado agora: Fedora mutável com `dnf` e capacidade `dnf copr` observados;
- exige marcação explícita de fonte com `copr` e coordenada `owner/project`;
- usa política própria, `source_type=copr_repository` e `trust_level=third_party_repository`;
- `copr.instalar` habilita explicitamente o repositório pedido antes da instalação;
- `copr.remover` remove o pacote, mas não gerencia o lifecycle do repositório;
- `COPR` não abre `procurar` nesta release;
- não herda fallback implícito de `host_package`.

### `user_software` via `flatpak`

- depende do backend `flatpak` estar presente no host;
- atua em escopo de usuário, sem mutação do pacote do host;
- vale também em hosts Atomic/imutáveis quando o pedido explicita `flatpak`;
- continua pequeno: não há seleção pública de remote além do default `flathub`.

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
🌌 Aurora v0.3.2
```

## O que a v0.3.2 não promete

A Aurora ainda não abre:

- fallback automático de pedido nu para AUR;
- `copr.procurar`, descoberta automática de repositório COPR ou canonicalização de pacote por busca;
- lifecycle amplo de repositório COPR e validação de origem RPM na remoção;
- helpers AUR além de `paru` e `yay`, e passthrough interativo para `aur.remover`;
- remotes `flatpak` além do default `flathub`;
- PPA, AppImage e GitHub Releases;
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
