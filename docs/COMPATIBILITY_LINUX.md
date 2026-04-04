# Compatibilidade Linux - Aurora v0.3.4

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

## `user_software` via `flatpak`

Na `v0.3.4`, `flatpak` continua sendo a frente explícita de software do usuário.

Leitura correta desta frente:

- depende do backend `flatpak` estar presente no host;
- atua em escopo de usuário;
- não herda o bloqueio de mutação de `host_package` em Atomic/imutáveis;
- cobre `procurar`, `instalar` e `remover`;
- exige confirmação explícita para remoção real.

Leitura operacional da frente AUR:

- `aur.instalar` pode entrar no fluxo interativo real do helper aceito;
- `aur.remover` permanece fora do passthrough interativo nesta release;
- quando `paru` e `yay` aparecem juntos, a Aurora escolhe `paru` por ser o primeiro helper suportado na ordem do contrato;
- helper AUR observado fora do contrato continua visível na observabilidade, mas bloqueado como rota;
- ambos continuam auditados com rota explícita e probes coerentes.

Leitura operacional da frente COPR:

- `copr.procurar` consulta apenas o repositório explicitamente pedido;
- `copr.procurar` pode refinar a consulta humana para forma package-like só dentro desse escopo explícito;
- `copr.instalar` observa se o repositório já estava habilitado e só faz `enable` explícito quando necessário;
- `copr.remover` verifica a origem RPM do pacote instalado via `from_repo` contra o repositório explícito antes de permitir a mutação;
- `copr.remover` bloqueia quando a origem RPM não puder ser demonstrada com honestidade;
- nenhuma rota COPR faz disable automático ou cleanup heurístico do repositório;
- a coordenada `owner/project` é obrigatória;
- o nome do pacote continua precisando ser exato para mutação nesta rodada;
- não existe descoberta mágica de repositório, busca global no universo COPR ou canonicalização por busca fora do repositório explícito.

## Leitura correta da fronteira

- `suportado agora` significa rota real aberta com policy, execução e observabilidade;
- `suportado contido` significa escopo útil e honesto, sem promoção artificial;
- `bloqueado por política` significa bloqueio deliberado, não acidente de backend;
- fonte observada sozinha não vira promessa automática de suporte.

## O que observação ainda não significa

Detecção de ferramenta não vira promessa automática de suporte. Isto continua valendo para:

- PPA;
- `rpm-ostree`;
- toolbox;
- distrobox;
- `ujust`.
