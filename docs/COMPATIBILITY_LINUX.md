# Compatibilidade Linux - Aurora v0.3.1

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
| Arch e derivadas mutáveis com `paru` observado | suportado agora | procurar, instalar com fluxo interativo do helper, remover |
| Arch mutável sem helper aceito | bloqueado por política | sem rota executável |
| Demais famílias Linux | fora do recorte | sem rota executável |
| Atomic / imutáveis | bloqueado por política | sem mutação via AUR |

## Frente `COPR` explícito

| Perfil Linux | Estado | Escopo real |
| --- | --- | --- |
| Fedora mutável com `dnf copr` observado | suportado agora | instalar, remover |
| Fedora mutável sem capacidade `dnf copr` observada | bloqueado por política | sem rota executável |
| Demais famílias Linux | fora do recorte | sem rota executável |
| Atomic / imutáveis | bloqueado por política | sem mutação via COPR |

## `user_software` via `flatpak`

Na `v0.3.1`, `flatpak` continua sendo a frente explícita de software do usuário.

Leitura correta desta frente:

- depende do backend `flatpak` estar presente no host;
- atua em escopo de usuário;
- não herda o bloqueio de mutação de `host_package` em Atomic/imutáveis;
- cobre `procurar`, `instalar` e `remover`;
- exige confirmação explícita para remoção real.

Leitura operacional da frente AUR:

- `aur.instalar` pode entrar no fluxo interativo real do helper aceito;
- `aur.remover` permanece fora do passthrough interativo nesta release;
- ambos continuam auditados com rota explícita e probes coerentes.

Leitura operacional da frente COPR:

- `copr.instalar` habilita explicitamente o repositório pedido antes da instalação;
- `copr.remover` remove o pacote, mas não desabilita o repositório;
- a coordenada `owner/project` é obrigatória;
- o nome do pacote precisa vir de forma exata neste primeiro corte;
- não existe `copr.procurar`, descoberta mágica de repositório ou canonicalização por busca.

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
