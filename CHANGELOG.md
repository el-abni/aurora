# Changelog

## 🌌 Aurora v0.5.0

Fechamento pequeno da frente `toolbox` para abrir um ambiente mediado explícito e distinto do host, sem fingir que isso já resolve suporte operacional real a hosts imutáveis.

### Adicionado

- `execution_surface=toolbox` e `environment_target` explícito no contrato de request, policy, route e `decision_record`.
- `toolbox.procurar`, `toolbox.instalar` e `toolbox.remover` como rotas reais sobre pacote distro-managed dentro de uma toolbox explicitamente nomeada.
- observação explícita de `toolbox` no host, das toolboxes existentes e do backend observado dentro do ambiente selecionado.
- `environment_resolution` e `toolbox_profile` em `aurora dev` para deixar visível a fronteira host vs toolbox.

### Alterado

- `toolbox` não entra como fonte; entra como superfície operacional mediada sobre `host_package`.
- `toolbox.instalar` e `toolbox.remover` exigem nome exato de pacote nesta release; a descoberta de nome humano fica em `toolbox.procurar`.
- `toolbox.remover` exige confirmação explícita para manter visível a mutação dentro do ambiente mediado.
- host Atomic/imutável continua bloqueado em `host_package`, mas um pedido explicitamente marcado para `toolbox` pode seguir quando `toolbox` e o ambiente nomeado foram observados.
- README, help e docs técnicas passam a refletir a `v0.5.0` como release pública atual.

### Continua fora da v0.5.0

- fallback automático do host para `toolbox`;
- default implícito de toolbox, autoseleção por ambiguidade ou descoberta mágica de ambiente;
- criação automática de toolbox e administração ampla de lifecycle;
- mistura de `toolbox` com AUR, COPR, PPA ou remotes `flatpak`;
- canonicalização ampla de alvo para `toolbox.instalar` e `toolbox.remover`;
- distrobox, `rpm-ostree`, `ujust` e suporte operacional real a hosts imutáveis.

## 🌌 Aurora v0.4.1

Fechamento pequeno da frente `flatpak` para abrir `remote` explícito além de `flathub`, sem transformar a Aurora em gerenciador amplo de remotes.

### Adicionado

- `flatpak` agora aceita `remote` explícito via coordenada simples já observável no host, como `no flatpak <remote>` ou `no flathub`.
- `flatpak.procurar`, `flatpak.instalar` e `flatpak.remover` carregam o `remote` para policy, route, execution e `decision_record`.
- observação explícita de `flatpak remotes` e uso controlado de `flatpak remote-ls` para respeitar o `remote` selecionado sem descoberta ampla.

### Alterado

- `flathub` continua sendo o default apenas para `flatpak.procurar` e `flatpak.instalar` quando nenhum `remote` é informado.
- `flatpak.remover` deixa explícito que `remote` só entra como restrição honesta de `origin`, sem assumir default para remoção.
- README, help e docs técnicas passam a refletir a `v0.4.1` como release pública atual.

### Continua fora da v0.4.1

- descoberta automática de remotes `flatpak`;
- add automático de remote arbitrário;
- administração geral de remotes `flatpak`;
- sincronização ampla de remotes;
- PPA, COPR e AUR fora do que já estava aberto;
- toolbox, distrobox, `rpm-ostree` e hosts imutáveis como superfície operacional.

## 🌌 Aurora v0.4.0

Fechamento pequeno da frente PPA para abrir uma nova família explícita de repositório terceiro sem transformar `apt` genérico em promessa ampla de Debian-like.

### Adicionado

- `requested_source=ppa` com coordenada canônica obrigatória `ppa:owner/name`.
- `source_type=ppa_repository` e `trust_level=third_party_repository` como leitura própria da nova frente.
- `ppa.instalar` como rota real com passos preparatórios explícitos: `add-apt-repository`, `apt-get update` e `apt-get install`.
- observabilidade dedicada para `PPA` em `decision_record` e `aurora dev`, incluindo capacidades observadas, distro compatível, coordenada e preparação planejada.

### Alterado

- a política passa a distinguir Ubuntu mutável suportado de Debian puro e outras derivadas Debian-like bloqueadas na frente PPA.
- `ppa.remover` deixa de ser ambíguo: continua bloqueado por honestidade porque a Aurora ainda não demonstra proveniência APT por PPA nem lifecycle amplo de repositório.
- README, help e docs técnicas passam a refletir a `v0.4.0` como release pública atual.

### Continua fora da v0.4.0

- descoberta automática de PPA;
- busca global em PPA;
- tratamento de apt repo genérico como se fosse PPA;
- `ppa.procurar`, `ppa.remover` real, `remove-apt-repository` e cleanup/lifecycle amplo;
- promessa ampla para Debian-like fora de Ubuntu mutável;
- AppImage e GitHub Releases;
- `rpm-ostree`, toolbox, distrobox e `ujust`;
- hosts imutáveis reais como superfície operacional.

## 🌌 Aurora v0.3.4

Fechamento pequeno da honestidade operacional de COPR em mutação, adicionando proveniência RPM na remoção e lifecycle limitado de repositório sem abrir descoberta automática, cleanup heurístico ou disable mágico.

### Adicionado

- verificação de proveniência RPM em `copr.remover`, comparando `from_repo` do pacote instalado com os `repoids` observados no repo file do COPR explícito.
- observação explícita do estado habilitado do repositório COPR informado para expor se ele já estava ativo ou se precisou de `enable`.

### Alterado

- `copr.instalar` agora trata `enable` de forma idempotente.
- `copr.remover` passa a bloquear cedo quando a origem RPM não fecha com o repositório explícito.

## 🌌 Aurora v0.3.3

Fechamento contido da frente COPR para abrir `copr.procurar` por repositório explícito, sem descoberta automática de fonte nem busca global no universo COPR.

### Adicionado

- `copr.procurar` como rota real de leitura dentro da família COPR já aberta.
- consulta restrita ao `owner/project` explicitamente pedido.

## 🌌 Aurora v0.3.2

Fechamento contido da frente AUR sobre a base já aberta da `v0.3.1`.

### Adicionado

- `yay` como segundo helper AUR deliberadamente suportado ao lado de `paru`.
- observabilidade dedicada para helpers AUR observados, suportados e selecionados.

## 🌌 Aurora v0.3.1

Fechamento público da release que abre COPR como fonte explícita de terceiro em Fedora mutável.

### Adicionado

- marcação pública inicial de COPR por frase explícita com coordenada `owner/project`.
- `copr.instalar` e `copr.remover` como segunda frente real de terceiro dentro de `host_package`.

## 🌌 Aurora v0.3.0

Fechamento público da release que abre AUR como fonte explícita de terceiro.

### Adicionado

- marcação pública inicial de AUR por frase explícita, como `aurora procurar <pacote> no aur`.
- `aur.procurar`, `aur.instalar` e `aur.remover` como primeira fonte terceira real da Aurora.

## 🌌 Aurora v0.2.0

Fechamento público da release que abre `user_software` como segundo domínio real da Aurora.

### Adicionado

- `domain_kind=user_software` como parte real do contrato público.
- `flatpak.procurar`, `flatpak.instalar` e `flatpak.remover` como primeira rota ativa de software do usuário.

## 🌌 Aurora v0.1.0

Primeiro release público da Aurora.

### Adicionado

- produto 100% Python, com launchers oficiais `aurora` e `auro`;
- bootstrap próprio da Aurora com `python -m aurora`, `--help` e `--version`;
- núcleo inicial de semântica, `host_profile`, `decision_record` e rotas reais de `host_package`.
