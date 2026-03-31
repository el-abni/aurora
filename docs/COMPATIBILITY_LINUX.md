# Compatibilidade Linux - Aurora v0.2.0

## Matriz atual de `host_package`

| Perfil Linux | Estado | Escopo real |
| --- | --- | --- |
| Arch e derivadas mutáveis | suportado agora | procurar, instalar, remover |
| Debian/Ubuntu e derivadas mutáveis | suportado agora | procurar, instalar, remover |
| Fedora mutável | suportado agora | procurar, instalar, remover |
| OpenSUSE mutável | suportado contido | procurar, instalar, remover |
| Atomic / imutáveis | bloqueado por política | sem mutação de `host_package` |

## Leitura correta da fronteira

- `suportado agora` significa rota real aberta para `host_package`;
- `suportado contido` significa escopo útil e honesto, sem promoção artificial;
- `bloqueado por política` significa bloqueio deliberado, não acidente de backend.

## `user_software` via `flatpak`

Na `v0.2.0`, `flatpak` deixa de ser apenas ferramenta observada quando o pedido explicita `flatpak` ou `flathub`.

Leitura correta desta frente:

- depende do backend `flatpak` estar presente no host;
- atua em escopo de usuário;
- não herda o bloqueio de mutação de `host_package` em Atomic/imutáveis;
- cobre `procurar`, `instalar` e `remover`;
- exige confirmação explícita para remoção real.

## O que observação ainda não significa

Detecção de ferramenta não vira promessa automática de suporte. Isto continua valendo para:

- AUR;
- COPR;
- PPA;
- `rpm-ostree`;
- toolbox;
- distrobox;
- `ujust`.
