# Changelog

## 🌌 Aurora v0.6.1

Release de revisão, correção, polimento e congelamento sobre a base já aberta na `v0.6.0`. O corte desta rodada não abre nova frente: ele endurece a superfície pública existente, melhora a observabilidade do runtime, reduz falso negativo conhecido de confirmação AUR e deixa o produto mais claro antes do próximo ciclo.

### Corrigido

- falhas operacionais de mutação agora tentam expor, de forma curta e segura, o motivo útil informado pelo backend em vez de cair só em “erro operacional” genérico;
- `aur.instalar` deixa de depender exclusivamente de `pacman -Qm` na confirmação pós-instalação e passa a validar a presença real final do pacote no host;
- a UX de handoff interativo para helpers AUR passa a avisar melhor quando o usuário precisa assumir o terminal, inclusive em casos em que o helper pode pedir Enter, seleção, revisão de build ou senha;
- a mensagem de retorno do handoff interativo deixa explícito que a Aurora ainda valida o estado final quando o helper devolve o terminal;
- summaries e mensagens principais deixam de vazar placeholders crus como coordenadas `'-'` em caminhos públicos centrais.

### Alterado

- a rota AUR continua explícita, pequena e contida, mas a confirmação final agora separa melhor “pacote presente no host” de “classificação foreign”, para evitar falso negativo sem relaxar a honestidade da resolução;
- `aurora dev` fica menos ruidoso em casos comuns ao esconder linhas de host imutável quando elas não trazem sinal real para a decisão atual;
- help, README, docs técnicas e wording público passam a refletir a `v0.6.1` como release pública atual;
- o texto público em pt-BR recebeu revisão de acentuação, caixa e acabamento nas mensagens mais visíveis desta rodada.

### Continua fora da v0.6.1

- qualquer nova fonte, nova superfície, nova família ou nova frente de produto;
- fallback automático, descoberta mágica, parser conversacional amplo ou passthrough anárquico;
- `aur.remover` em passthrough interativo;
- AppImage, GitHub Releases e `ujust`;
- manutenção ampla do host, arquivos e rede;
- qualquer expansão disfarçada de backlog enquanto a base ainda estava em revisão.

## 🌌 Aurora v0.6.0

Fechamento contido, mas estrutural, da primeira frente operacional real para hosts imutáveis: `rpm-ostree` entra como superfície explícita, e o host Atomic/imutável deixa de ser apenas um bloqueio genérico para virar uma decisão auditável entre `flatpak`, `toolbox`, `distrobox`, `rpm-ostree` ou bloqueio.

### Adicionado

- `execution_surface=rpm_ostree` como nova superfície explícita de host imutável.
- `rpm_ostree.instalar` e `rpm_ostree.remover` como primeiro corte real de layering/uninstall via `rpm-ostree`.
- observação estruturada de `rpm-ostree status --json`, incluindo `pending deployment`, transação ativa e pacotes solicitados no deployment booted/default.
- sinais explícitos de host imutável em `policy`, `route`, `decision_record` e `aurora dev`, como `immutable_observed_surfaces` e `immutable_selected_surface`.

### Alterado

- host Atomic/imutável já não responde apenas com bloqueio genérico em `host_package`: o bloqueio de pedido nu agora expõe quais superfícies foram observadas e por que a Aurora não infere entre elas.
- `flatpak`, `toolbox` e `distrobox` continuam explícitos, mas passam a carregar seleção auditável de superfície quando o host é imutável.
- `rpm-ostree` não entra como `requested_source`; entra como superfície operacional distinta do host mutável comum e distinta de ambiente mediado.
- `rpm_ostree.instalar` e `rpm_ostree.remover` exigem nome exato de pacote nesta release.
- `rpm_ostree.procurar` continua fora do corte executável e bloqueia com explicação honesta.
- `rpm_ostree.remover` exige confirmação explícita.
- mutações bem-sucedidas em `rpm-ostree` deixam visível que o efeito foi para o próximo deployment e pode exigir reboot.
- README, help e docs técnicas passam a refletir a `v0.6.0` como release pública atual.

### Continua fora da v0.6.0

- fallback automático do host para `flatpak`, `toolbox`, `distrobox` ou `rpm-ostree`;
- `rpm-ostree.procurar`;
- `apply-live`, `override remove`, reboot automático e chaining amplo de transações `rpm-ostree`;
- `ujust`;
- manutenção ampla do host imutável;
- suporte genérico a qualquer host imutável fora do corte explícito desta release;
- mistura de `rpm-ostree` com AUR, COPR, PPA, `flatpak` remotes, `toolbox` ou `distrobox` na mesma frase.

## 🌌 Aurora v0.5.1

Fechamento pequeno da frente `distrobox` para abrir uma segunda superfície mediada explícita, sem colapsar `toolbox` e `distrobox` numa pseudoentidade única e sem fingir que isso já resolve hosts imutáveis.

### Adicionado

- `execution_surface=distrobox` e `environment_target` explícito no contrato de request, policy, route e `decision_record`.
- `distrobox.procurar`, `distrobox.instalar` e `distrobox.remover` como rotas reais sobre pacote distro-managed dentro de uma distrobox explicitamente nomeada.
- observação explícita de `distrobox` no host, das distroboxes existentes e do backend observado dentro do ambiente selecionado.
- `distrobox_profile` em `aurora dev` para deixar visível a fronteira host vs distrobox.

### Alterado

- `distrobox` não entra como fonte; entra como superfície operacional mediada sobre `host_package`.
- `toolbox` e `distrobox` agora compartilham apenas o miolo de pacote distro-managed dentro do ambiente, mantendo observação, sinais e rotas separados por superfície.
- `distrobox.instalar` e `distrobox.remover` exigem nome exato de pacote nesta release; a descoberta de nome humano fica em `distrobox.procurar`.
- `distrobox.remover` exige confirmação explícita para manter visível a mutação dentro do ambiente mediado.
- README, help e docs técnicas passam a refletir a `v0.5.1` como release pública atual.

### Continua fora da v0.5.1

- fallback automático do host para `distrobox`;
- default implícito de distrobox, autoseleção por ambiguidade ou descoberta mágica de ambiente;
- criação automática de distrobox e administração ampla de lifecycle;
- mistura de `distrobox` com `toolbox`, AUR, COPR, PPA ou remotes `flatpak`;
- canonicalização ampla de alvo para `distrobox.instalar` e `distrobox.remover`;
- `rpm-ostree`, `ujust` e suporte operacional real a hosts imutáveis.

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
