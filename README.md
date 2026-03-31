# 🌌 Aurora

![versão](https://img.shields.io/badge/vers%C3%A3o-v0.2.0-0f766e)
![linguagem](https://img.shields.io/badge/linguagem-Python-3776AB)
![plataforma](https://img.shields.io/badge/plataforma-Linux-orange)
![licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)

**Aurora** é uma assistente de terminal para **Linux**, escrita em **100% Python**, com política explícita, observabilidade própria e execução real sobre um contrato pequeno e auditável.

Na `v0.2.0`, a superfície pública passa a cobrir dois domínios reais:

- `host_package` para pacotes do host;
- `user_software` para software do usuário via `flatpak`.

Pedidos nus, como `aurora procurar firefox`, continuam no default seguro de `host_package`. Pedidos explicitamente marcados como `flatpak` ou `flathub`, como `aurora instalar firefox no flatpak`, entram em `user_software`.

## O que a Aurora faz

A Aurora funciona como uma camada de decisão e execução sobre Linux. Em vez de esconder escolha de rota atrás de heurística opaca, ela:

- classifica a frase;
- detecta o host Linux;
- aplica política;
- escolhe a rota cabível no contrato atual;
- executa com probe de estado quando a ação muda software;
- e expõe um `decision_record` auditável com `aurora dev <frase>`.

## Contrato público da v0.2.0

Rotas reais abertas nesta release:

- `host_package.procurar`
- `host_package.instalar`
- `host_package.remover`
- `flatpak.procurar`
- `flatpak.instalar`
- `flatpak.remover`

Comportamento garantido:

- `host_package` continua sendo o default para pedidos nus;
- `flatpak` só entra quando a frase marca `flatpak` ou `flathub`;
- `flatpak.instalar` e `flatpak.remover` usam escopo explícito de usuário;
- `flatpak.instalar` usa `flathub` como remote default nesta release;
- mutações usam probe antes e depois, com `noop` honesto quando nada precisa mudar;
- `--confirm` continua fazendo parte real da UX para mutações sensíveis.

## Exemplos rápidos

### Pacotes do host

```bash
aurora procurar firefox
aurora instalar firefox
aurora instalar sudo --confirm
aurora remover firefox
aurora remover sudo --confirm
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
aurora dev "remover sudo"
```

## Compatibilidade Linux

### `host_package`

- suportado agora: Arch/derivadas mutáveis, Debian/Ubuntu/derivadas mutáveis e Fedora mutável;
- suportado contido: OpenSUSE mutável;
- bloqueado por política: hosts Atomic/imutáveis.

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
aurora --help
auro --help
```

A identidade pública da ferramenta é:

```text
🌌 Aurora
```

Nesta release, a versão pública aparece como:

```text
🌌 Aurora v0.2.0
```

## O que a v0.2.0 não promete

A Aurora `v0.2.0` ainda não abre:

- remotes `flatpak` além do default `flathub`;
- AUR, COPR, PPA, AppImage e GitHub Releases;
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
