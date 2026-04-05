# Compatibilidade Linux - Aurora v0.5.0

## Matriz atual de `host_package`

| Perfil Linux | Estado | Escopo real |
| --- | --- | --- |
| Arch e derivadas mutáveis | suportado agora | procurar, instalar, remover |
| Debian/Ubuntu e derivadas mutáveis | suportado agora | procurar, instalar, remover |
| Fedora mutável | suportado agora | procurar, instalar, remover |
| OpenSUSE mutável | suportado contido | procurar, instalar, remover |
| Atomic / imutáveis | bloqueado por política | sem mutação de `host_package` |

## Frente `AUR` explícita

| Perfil Linux | Estado | Escopo real |
| --- | --- | --- |
| Arch e derivadas mutáveis com `paru` ou `yay` observado | suportado agora | procurar, instalar com fluxo interativo do helper, remover |
| Arch mutável sem helper aceito | bloqueado por política | sem rota executável |
| Arch mutável só com helper AUR fora do contrato observado | bloqueado por política | sem rota executável |
| Demais famílias Linux | fora do recorte | sem rota executável |
| Atomic / imutáveis | bloqueado por política | sem mutação via AUR |

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

Na `v0.5.0`, `flatpak` continua sendo a frente explícita de software do usuário.

Leitura correta desta frente:

- depende do backend `flatpak` estar presente no host;
- atua em escopo de usuário;
- não herda o bloqueio de mutação de `host_package` em Atomic/imutáveis;
- cobre `procurar`, `instalar` e `remover`;
- preserva `flathub` como default em `procurar` e `instalar` quando nenhum remote é informado;
- aceita remote explícito apenas quando esse remote já é observável via `flatpak remotes`;
- `remover` só usa remote explícito como restrição de `origin`, sem default implícito;
- exige confirmação explícita para remoção real.

## Frente `toolbox` explícita

Na `v0.5.0`, `toolbox` entra como superfície operacional mediada, não como fonte.

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
- não existe default implícito, criação automática, lifecycle amplo nem fallback host -> toolbox.

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

## Leitura correta da fronteira

- `suportado agora` significa rota real aberta com policy, execução e observabilidade;
- `suportado contido` significa escopo útil e honesto, sem promoção artificial;
- `bloqueado por política` significa bloqueio deliberado, não acidente de backend;
- ferramenta observada sozinha não vira promessa automática de suporte.

## O que observação ainda não significa

Detecção de ferramenta não vira promessa automática de suporte. Isto continua valendo para:

- `toolbox` sem pedido explícito e sem ambiente nomeado;
- PPA fora do recorte Ubuntu mutável;
- `rpm-ostree`;
- distrobox;
- `ujust`.
