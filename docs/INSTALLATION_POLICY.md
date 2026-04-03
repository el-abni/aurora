# Installation Policy - Aurora v0.3.0

## Escopo real da política

Na `v0.3.0`, a política operacional da Aurora governa dois domínios e três fontes reais:

- `host_package` com `source_type=host_package_manager`;
- `host_package` explicitamente marcado com `source_type=aur_repository`;
- `user_software` com `source_type=flatpak_remote`.

A política existe para explicitar contrato, risco e limite da rota. Ela não existe para simular amplitude.

## Campos operacionais

Os campos ativos desta release são:

- `domain_kind`
- `source_type`
- `trust_level`
- `software_criticality`
- `trust_signals`
- `trust_gaps`
- `policy_outcome`
- `requires_confirmation`
- `reversal_level`

## Como a política lê cada frente

### `host_package`

- pedido nu continua em `host_package`;
- `trust_level=distribution_managed`;
- mutação do host em perfil Atomic/imutável continua bloqueada;
- mutações sensíveis pedem confirmação explícita.

### `AUR` explícito

- pedido explicitamente marcado com `aur` continua no escopo de pacote do host, mas com fonte separada;
- `source_type=aur_repository`;
- `trust_level=third_party_build`;
- usa helper AUR aceito de forma explícita e pequena nesta rodada;
- `aur.instalar` e `aur.remover` exigem confirmação explícita;
- `aur.instalar` pode entregar o terminal ao helper para revisão/build interativos e volta para validação por probe quando o helper termina;
- `aur.remover` permanece no caminho não interativo desta release;
- continua bloqueado fora de Arch mutável, sem `pacman` observado ou sem helper aceito.

### `user_software`

- pedido explicitamente marcado como `flatpak` ou `flathub` cai em `user_software`;
- `trust_level=guarded`;
- `flatpak.instalar` usa escopo explícito de usuário e remote default `flathub`;
- `flatpak.remover` usa escopo explícito de usuário e exige confirmação real quando a remoção vai acontecer.

## Como a política afeta o runtime

### `policy_outcome`

Pode resultar, no mínimo, em:

- `allow`
- `block`
- `require_confirmation`

### `requires_confirmation`

Quando verdadeiro, a Aurora pede confirmação explícita com `--confirm` antes de mutações sensíveis.

Na `v0.3.0`, `--confirm` e `--yes` são aceitos como marcadores equivalentes de confirmação explícita, inclusive quando entram inline na frase inspecionada.

### `software_criticality`

Nesta release, a taxonomia continua pequena e pragmática:

- `low`
- `medium`
- `high`
- `sensitive`

Ela sustenta decisão operacional. Não pretende ser modelo universal de software.

### `reversal_level`

Registra o peso de reversão esperado da mutação, por exemplo:

- `informational`
- `host_change`
- `host_change_sensitive`
- `reinstall_required`
- `hard_to_reverse`
- `third_party_host_change`
- `third_party_host_removal`
- `user_scope_change`
- `user_scope_removal`

## Exemplos de comportamento

- `aurora instalar firefox`
  resultado típico: `allow`
- `aurora remover sudo`
  resultado típico: `require_confirmation`
- `aurora instalar firefox` em host Atomic/imutável
  resultado típico: `block`
- `aurora procurar google chrome no aur`
  resultado típico: `allow`
- `aurora instalar google chrome no aur`
  resultado típico: `require_confirmation`
- `aurora procurar firefox no flatpak`
  resultado típico: `allow`
- `aurora instalar firefox no flatpak`
  resultado típico: `allow`
- `aurora remover firefox no flatpak`
  resultado típico: `require_confirmation`

## O que ainda não está aberto

Continuam fora da `v0.3.0`:

- seleção de remote além do default `flathub`;
- COPR, PPA, AppImage e GitHub Releases;
- `rpm-ostree`, toolbox, distrobox e `ujust`.

Se `flatpak` ou helper AUR aparecerem no host sem pedido explícito, isso continua sendo apenas observação e não muda o default de `host_package`.
