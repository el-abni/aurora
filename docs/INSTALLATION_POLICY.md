# Installation Policy - Aurora v0.1.0

## Escopo real da politica

Na `v0.1`, a politica operacional da Aurora governa apenas o dominio `host_package`.

Isto significa:

- `source_type=host_package_manager`
- `trust_level=distribution_managed`

Nao existe, nesta release, selecao entre multiplas fontes de software.

## Campos operacionais

Os campos ja ativos nesta release sao:

- `domain_kind`
- `source_type`
- `trust_level`
- `software_criticality`
- `trust_signals`
- `trust_gaps`
- `policy_outcome`
- `requires_confirmation`
- `reversal_level`

## Como a politica afeta o runtime

### `policy_outcome`

Pode resultar, no minimo, em:

- `allow`
- `block`
- `require_confirmation`

### `requires_confirmation`

Quando verdadeiro, a Aurora pede confirmacao explicita com `--confirm` antes de mutacoes sensiveis.

### `software_criticality`

Nesta release, a taxonomia e pequena e pragmatica:

- `low`
- `medium`
- `high`
- `sensitive`

Ela nao pretende ser modelo universal de software.
Ela existe para sustentar a decisao da `v0.1`.

### `reversal_level`

Registra o peso de reversao esperado da mutacao, por exemplo:

- `informational`
- `host_change`
- `host_change_sensitive`
- `reinstall_required`
- `hard_to_reverse`

## Exemplos de comportamento

- `aurora instalar firefox`
  resultado tipico: `allow`
- `aurora remover firefox`
  resultado tipico: `allow`
- `aurora remover sudo`
  resultado tipico: `require_confirmation`
- `aurora instalar firefox` em host Atomic/imutavel
  resultado tipico: `block`

## O que nao esta aberto na v0.1

Ficam fora desta release:

- `flatpak` como fonte ativa;
- AUR, COPR, PPA, AppImage, GitHub Releases;
- `rpm-ostree`, toolbox, distrobox, `ujust`.

Se `flatpak` aparecer no host, isso continua sendo observacao, nao promessa de rota.
