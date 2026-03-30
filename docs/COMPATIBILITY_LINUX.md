# Compatibilidade Linux - Aurora v0.1.0

## Contrato da v0.1

O contrato publico atual da Aurora cobre apenas o dominio `host_package`.

Accoes reais:

- `procurar`
- `instalar`
- `remover`

## Matriz atual

| Perfil Linux | Estado | Escopo real |
| --- | --- | --- |
| Arch e derivadas mutaveis | suportado agora | procurar, instalar, remover |
| Debian/Ubuntu e derivadas mutaveis | suportado agora | procurar, instalar, remover |
| Fedora mutavel | suportado agora | procurar, instalar, remover |
| OpenSUSE mutavel | suportado contido | procurar, instalar, remover |
| Atomic / imutaveis | bloqueado por politica | sem mutacao do host |

## Leitura correta da fronteira

- `suportado agora` significa rota real de `host_package` aberta;
- `suportado contido` significa escopo util e honesto, sem promocao artificial;
- `bloqueado por politica` significa bloqueio deliberado, nao acidente de backend.

## Atomic / imutaveis

Aurora `v0.1` bloqueia mutacao de `host_package` em perfis Atomic/imutaveis.

Isso inclui a leitura honesta de perfis equivalentes a:

- Universal Blue e derivados equivalentes;
- `opensuse-microos` e `microos`;
- outros perfis detectados como imutaveis pela heuristica atual.

## Ferramentas observadas que nao entram no contrato ativo

A deteccao de ferramenta nao vira promessa de suporte. Na `v0.1`, isto vale especialmente para:

- `flatpak`;
- `rpm-ostree`.
