# Compatibilidade Linux - Aurora v0.6.1

## Matriz atual de `host_package`

| Perfil Linux | Estado | Escopo real |
| --- | --- | --- |
| Arch e derivadas mutáveis | suportado agora | procurar, instalar, remover |
| Debian/Ubuntu e derivadas mutáveis | suportado agora | procurar, instalar, remover |
| Fedora mutável | suportado agora | procurar, instalar, remover |
| OpenSUSE mutável | suportado contido | procurar, instalar, remover |
| Atomic / imutáveis | decisão explícita por superfície | `flatpak`, `toolbox`, `distrobox`, `rpm-ostree` ou bloqueio |

## Frente `AUR` explícita

| Perfil Linux | Estado | Escopo real |
| --- | --- | --- |
| Arch e derivadas mutáveis com `paru` ou `yay` observado | suportado agora | procurar, instalar com fluxo interativo do helper, remover |
| Arch mutável sem helper aceito | bloqueado por política | sem rota executável |
| Arch mutável só com helper AUR fora do contrato observado | bloqueado por política | sem rota executável |
| Demais famílias Linux | fora do recorte | sem rota executável |
| Atomic / imutáveis | bloqueado por política | sem mutação via AUR |

Leitura correta desta frente na `v0.6.1`:

- `aur.instalar` continua interativo quando o helper precisa assumir o terminal;
- a Aurora avisa o handoff e deixa explícito que o helper pode pedir Enter, seleção, revisão de build ou senha;
- a confirmação pós-instalação fecha pela presença final do pacote no host, enquanto a honestidade da rota AUR continua ancorada na resolução e no helper explícitos.

## Frente `COPR` explícito

| Perfil Linux | Estado | Escopo real |
| --- | --- | --- |
| Fedora mutável com `dnf copr` observado | suportado agora | procurar, instalar, remover |
| Fedora mutável sem capacidade `dnf copr` observada | bloqueado por política | sem rota executável |
| Demais famílias Linux | fora do recorte | sem rota executável |
| Atomic / imutáveis | bloqueado por política | sem mutação via COPR |

## Frente `PPA` explícito

| Perfil Linux | Estado | Escopo real |
| --- | --- | --- |
| Ubuntu mutável com `add-apt-repository`, `apt-get` e `dpkg` observados | suportado agora | instalar |
| Ubuntu mutável sem uma dessas capacidades | bloqueado por política | sem rota executável |
| Debian puro | fora do recorte | sem rota executável |
| Outras derivadas Debian-like | fora do recorte | sem rota executável |
| Atomic / imutáveis | bloqueado por política | sem mutação via PPA |

## `user_software` via `flatpak`

Na `v0.6.1`, `flatpak` continua sendo a frente explícita de software do usuário.

Leitura correta desta frente:

- depende do backend `flatpak` estar presente no host;
- atua em escopo de usuário;
- não herda o bloqueio de mutação de `host_package` em Atomic/imutáveis;
- em host imutável, a escolha explícita fica auditável como `immutable_selected_surface=flatpak`;
- cobre `procurar`, `instalar` e `remover`;
- preserva `flathub` como default em `procurar` e `instalar` quando nenhum remote é informado;
- aceita remote explícito apenas quando esse remote já é observável via `flatpak remotes`;
- `remover` só usa remote explícito como restrição de `origin`, sem default implícito;
- exige confirmação explícita para remoção real.

## Frente `toolbox` explícita

Na `v0.6.1`, `toolbox` entra como superfície operacional mediada, não como fonte.

| Perfil observado | Estado | Escopo real |
| --- | --- | --- |
| Host com `toolbox` observado e toolbox explícita Arch/Debian/Fedora com backend distro-managed e `sudo` observados | suportado agora | procurar, instalar e remover por nome exato de pacote |
| Host com `toolbox` observado e toolbox explícita OpenSUSE com backend e `sudo` observados | suportado contido | procurar, instalar e remover por nome exato de pacote |
| Host sem `toolbox` observado | bloqueado por política | sem rota executável |
| Toolbox explícita não resolvida, sem backend suportado ou sem `sudo` para mutação | bloqueado por política | sem rota executável |
| Host Atomic / imutável com `toolbox` explícita e válida | suportado agora como ambiente mediado | não abre suporte amplo ao host imutável |

Leitura correta desta frente:

- `toolbox` exige ambiente explicitamente nomeado;
- a Aurora observa o backend dentro da toolbox selecionada antes de abrir a rota;
- `toolbox.procurar` aceita busca humana dentro do ambiente selecionado;
- `toolbox.instalar` e `toolbox.remover` exigem nome exato de pacote;
- `toolbox.remover` exige confirmação explícita;
- a mutação acontece dentro da toolbox e não no host;
- em host imutável, a escolha explícita fica auditável como `immutable_selected_surface=toolbox`;
- não existe default implícito, criação automática, lifecycle amplo nem fallback host -> toolbox.

## Frente `distrobox` explícita

Na `v0.6.1`, `distrobox` entra como segunda superfície operacional mediada, não como fonte.

| Perfil observado | Estado | Escopo real |
| --- | --- | --- |
| Host com `distrobox` observado e distrobox explícita Arch/Debian/Fedora com backend distro-managed e `sudo` observados | suportado agora | procurar, instalar e remover por nome exato de pacote |
| Host com `distrobox` observado e distrobox explícita OpenSUSE com backend e `sudo` observados | suportado contido | procurar, instalar e remover por nome exato de pacote |
| Host sem `distrobox` observado | bloqueado por política | sem rota executável |
| Distrobox explícita não resolvida, sem backend suportado ou sem `sudo` para mutação | bloqueado por política | sem rota executável |
| Host Atomic / imutável com `distrobox` explícita e válida | suportado agora como ambiente mediado | não abre suporte amplo ao host imutável |

Leitura correta desta frente:

- `distrobox` exige ambiente explicitamente nomeado;
- a Aurora observa o backend dentro da distrobox selecionada antes de abrir a rota;
- `distrobox.procurar` aceita busca humana dentro do ambiente selecionado;
- `distrobox.instalar` e `distrobox.remover` exigem nome exato de pacote;
- `distrobox.remover` exige confirmação explícita;
- a mutação acontece dentro da distrobox e não no host;
- em host imutável, a escolha explícita fica auditável como `immutable_selected_surface=distrobox`;
- não existe default implícito, criação automática, lifecycle amplo nem fallback host -> distrobox.

## Frente `rpm-ostree` explícito

Na `v0.6.1`, `rpm-ostree` entra como superfície explícita de host imutável.

| Perfil observado | Estado | Escopo real |
| --- | --- | --- |
| Host Atomic/imutável com `rpm-ostree` observado, `status --json` parseável e sem transação ativa/pending deployment | suportado agora | instalar e remover por nome exato de pacote |
| Host Atomic/imutável com `rpm-ostree` observado, mas com transação ativa | bloqueado por política | sem rota executável |
| Host Atomic/imutável com `rpm-ostree` observado, mas com pending deployment já existente | bloqueado por política | sem rota executável |
| Host Atomic/imutável sem `rpm-ostree` observado | bloqueado por política | sem rota executável |
| Host mutável | fora do recorte | use `host_package` normal |

Leitura correta desta frente:

- `rpm-ostree` exige pedido explícito;
- `rpm_ostree.instalar` e `rpm_ostree.remover` exigem nome exato de pacote;
- `rpm_ostree.procurar` ainda não foi aberta;
- a confirmação de sucesso observa o deployment `default/pending`, não promete `apply-live`;
- uma mutação bem-sucedida pode exigir reboot para aplicar o deployment resultante;
- `rpm-ostree` não equivale a suporte genérico a qualquer host imutável.

## Leitura operacional das frentes explícitas

### `AUR`

- `aur.instalar` pode entrar no fluxo interativo real do helper aceito;
- `aur.remover` permanece fora do passthrough interativo nesta release;
- quando `paru` e `yay` aparecem juntos, a Aurora escolhe `paru`;
- helper AUR observado fora do contrato continua visível, mas bloqueado como rota.

### `COPR`

- `copr.procurar` consulta apenas o repositório explicitamente pedido;
- `copr.instalar` observa se o repositório já estava habilitado e só faz `enable` explícito quando necessário;
- `copr.remover` verifica a origem RPM do pacote instalado via `from_repo` contra o repositório explícito antes de permitir a mutação;
- nenhuma rota COPR faz disable automático ou cleanup heurístico do repositório;
- a coordenada `owner/project` é obrigatória.

### `PPA`

- `ppa.instalar` exige coordenada canônica `ppa:owner/name`;
- `ppa.instalar` planeja `add-apt-repository`, `apt-get update` e `apt-get install` como passos explícitos;
- `ppa.remover` continua bloqueado por honestidade;
- `PPA` não equivale a `apt` genérico nem a qualquer repo externo;
- URL genérica de apt repo continua fora do contrato.

### `flatpak`

- `flatpak.procurar` usa `flatpak remote-ls` no remote selecionado, sem descoberta ampla;
- `flatpak.instalar` bloqueia cedo quando o remote default `flathub` ou o remote explícito não está observado;
- `flatpak.remover` respeita remote explícito só como restrição de `origin`;
- não existe add automático, sincronização ampla nem administração geral de remotes.

### `toolbox`

- `toolbox.procurar` deixa visível em `decision_record` qual ambiente foi selecionado;
- `toolbox.instalar` e `toolbox.remover` deixam visíveis `execution_surface=toolbox`, `environment_target`, `toolbox_profile` e `toolbox_package_backends`;
- `toolbox.instalar` e `toolbox.remover` não fazem fallback para host, não criam toolbox e não misturam outras fontes;
- `toolbox` não é promessa ampla para `rpm-ostree`, distrobox ou hosts imutáveis como um todo.

### `distrobox`

- `distrobox.procurar` deixa visível em `decision_record` qual ambiente foi selecionado;
- `distrobox.instalar` e `distrobox.remover` deixam visíveis `execution_surface=distrobox`, `environment_target`, `distrobox_profile` e `distrobox_package_backends`;
- `distrobox.instalar` e `distrobox.remover` não fazem fallback para host, não criam distrobox e não misturam outras fontes;
- `distrobox` não é alias de `toolbox` e não é promessa ampla para `rpm-ostree` ou hosts imutáveis como um todo.

### `rpm-ostree`

- `rpm_ostree.instalar` e `rpm_ostree.remover` deixam visíveis `execution_surface=rpm_ostree`, `rpm_ostree_status`, `immutable_observed_surfaces` e `immutable_selected_surface`;
- a rota bloqueia cedo quando já existe `pending deployment` ou transação ativa;
- a rota não abre `apply-live`, `override remove`, reboot automático ou manutenção ampla do host;
- `rpm-ostree` não mistura `owner/project`, `from_repo`, `ppa:owner/name`, `toolbox` ou `distrobox` na mesma frase.

## Leitura correta da fronteira

- `suportado agora` significa rota real aberta com policy, execução e observabilidade;
- `suportado contido` significa escopo útil e honesto, sem promoção artificial;
- `bloqueado por política` significa bloqueio deliberado, não acidente de backend;
- ferramenta observada sozinha não vira promessa automática de suporte.

## O que observação ainda não significa

Detecção de ferramenta não vira promessa automática de suporte. Isto continua valendo para:

- `toolbox` sem pedido explícito e sem ambiente nomeado;
- `distrobox` sem pedido explícito e sem ambiente nomeado;
- PPA fora do recorte Ubuntu mutável;
- `rpm-ostree` sem pedido explícito;
- `ujust`.
