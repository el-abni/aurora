# Installation Policy - Aurora v1.2.0

## Escopo real da política

Na `v1.2.0`, a política operacional da Aurora governa três domínios, três superfícies explícitas fora do host mutável comum e nove leituras reais de rota. A nova orientação conversacional roda antes dessa política e não altera essas rotas:

- `host_package` com `execution_surface=host` e `source_type=host_package_manager`;
- `host_maintenance` com `execution_surface=host` e `source_type=host_maintenance`;
- `host_package` explicitamente marcado com `source_type=aur_repository`;
- `host_package` explicitamente marcado com `source_type=copr_repository`;
- `host_package` explicitamente marcado com `source_type=ppa_repository`;
- `host_package` explicitamente marcado com `execution_surface=toolbox` e `source_type=toolbox_host_package_manager`;
- `host_package` explicitamente marcado com `execution_surface=distrobox` e `source_type=distrobox_host_package_manager`;
- `host_package` explicitamente marcado com `execution_surface=rpm_ostree` e `source_type=rpm_ostree_layering`;
- `user_software` com `source_type=flatpak_remote`.

O recorte de `host_maintenance` é mínimo e formalmente fechado nesta release: apenas `atualizar sistema` no host Arch mutável com `pacman` observado.

A política existe para explicitar contrato, risco e limite da rota. Ela não existe para simular amplitude.

## Campos operacionais

Os campos ativos desta release são:

- `domain_kind`
- `source_type`
- `execution_surface`
- `trust_level`
- `software_criticality`
- `trust_signals`
- `trust_gaps`
- `policy_outcome`
- `requires_confirmation`
- `reversal_level`

## Como a política lê cada frente

### `host_package`

- pedido nu continua em `host_package` no host;
- `execution_surface=host`;
- `trust_level=distribution_managed`;
- mutação do host em perfil Atomic/imutável continua bloqueada quando a frase não escolhe uma superfície;
- em host imutável, a política expõe `immutable_observed_surfaces` e `immutable_selected_surface=block` quando a inferência seria frouxa demais;
- mutações sensíveis pedem confirmação explícita.

### `host_maintenance`

- `host_maintenance` não substitui `host_package`; ele abre apenas a atualização explícita do sistema;
- `execution_surface=host`;
- `source_type=host_maintenance`;
- `trust_level=host_operational_change`;
- a frente continua restrita ao host Arch mutável com `pacman` observado;
- a política exige confirmação explícita antes de qualquer execução;
- a rota usa apenas o backend oficial `sudo + pacman`;
- `paru`, `yay` e qualquer helper AUR observado continuam apenas como observação fora do contrato;
- Fedora, Debian/Ubuntu e OpenSUSE mutáveis ficam fora do recorte equivalente nesta primeira absorção;
- hosts Atomic/imutáveis continuam bloqueados por política e não ganham equivalência automática com `rpm-ostree`, `flatpak`, `toolbox` ou `distrobox`.

### `AUR` explícito

- pedido explicitamente marcado com `aur` continua no escopo de pacote do host, mas com fonte separada;
- `execution_surface=host`;
- `source_type=aur_repository`;
- `trust_level=third_party_build`;
- usa apenas `paru` e `yay`;
- `aur.instalar` e `aur.remover` exigem confirmação explícita;
- `aur.instalar` pode entregar o terminal ao helper para revisão/build interativos e avisa explicitamente que o helper pode pedir Enter, seleção, revisão ou senha;
- o fluxo AUR também avisa quando pode haver pausa silenciosa durante build e, em alguns terminais, Enter extra ao final;
- a confirmação pós-instalação AUR valida a presença final no host e não trata `pacman -Qm` como único critério de sucesso;
- `aur.remover` permanece no caminho não interativo desta release;
- continua bloqueado fora de Arch mutável, sem `pacman` observado, sem helper aceito ou com helper fora do contrato como único helper disponível.

### `COPR` explícito

- pedido explicitamente marcado com `copr` continua no escopo de pacote do host, mas com fonte separada;
- `execution_surface=host`;
- a frase precisa trazer `owner/project` de forma explícita;
- `source_type=copr_repository`;
- `trust_level=third_party_repository`;
- `copr.procurar` não exige confirmação, mas só consulta o repositório explicitamente pedido;
- `copr.instalar` e `copr.remover` exigem confirmação explícita;
- a frente só abre em Fedora mutável com `dnf` e capacidade `dnf copr` observados;
- `copr.remover` só permite mutação quando a origem RPM do pacote instalado fecha com o repositório explícito;
- a proveniência RPM em `copr.remover` usa `dnf repoquery --installed` com `from_repo`;
- não existe disable automático, cleanup heurístico nem lifecycle amplo do repositório.

### `PPA` explícito

- pedido explicitamente marcado com `ppa` continua no escopo de pacote do host, mas com fonte separada;
- `execution_surface=host`;
- a frase precisa trazer a coordenada canônica `ppa:owner/name`;
- `source_type=ppa_repository`;
- `trust_level=third_party_repository`;
- `ppa.instalar` exige confirmação explícita;
- a frente só abre em Ubuntu mutável com `add-apt-repository`, `apt-get` e `dpkg` observados;
- `ppa.instalar` planeja `add-apt-repository`, `apt-get update` e `apt-get install` como passos preparatórios explícitos;
- a política mantém o gap `ppa_repository_state_not_observed_by_design`;
- `ppa.remover` continua em `block`, porque a Aurora ainda não demonstra proveniência APT suficiente por PPA.

### `user_software`

- pedido explicitamente marcado como `flatpak` ou `flathub` cai em `user_software`;
- `execution_surface=host`;
- `trust_level=guarded`;
- `flatpak.procurar` e `flatpak.instalar` assumem `flathub` apenas quando nenhum remote é informado;
- `flatpak` aceita remote explícito apenas como nome simples já observável via `flatpak remotes`;
- a política expõe `flatpak_effective_remote`, `flatpak_remote_origin` e `flatpak_observed_remotes`;
- `flatpak.procurar` usa `flatpak remote-ls` dentro do remote selecionado;
- `flatpak.instalar` bloqueia cedo quando o remote default ou explícito não está observado;
- `flatpak.remover` usa escopo explícito de usuário e exige confirmação real quando a remoção vai acontecer.
- em host imutável, a política deixa explícito `immutable_selected_surface=flatpak`.

### `toolbox` explícita

- pedido explicitamente marcado como `toolbox` continua no domínio `host_package`, mas troca a superfície para `execution_surface=toolbox`;
- `toolbox` não vira `requested_source`;
- `source_type=toolbox_host_package_manager`;
- `trust_level=mediated_environment`;
- a frase precisa trazer `na toolbox <ambiente>`;
- a política expõe `toolbox_requested_environment`, `toolbox_environment_status`, `toolbox_resolved_environment`, `toolbox_linux_family`, `toolbox_package_backends` e `toolbox_sudo_observed`;
- `toolbox.procurar` não exige confirmação;
- `toolbox.instalar` não exige confirmação, mas depende de backend distro-managed e `sudo` observados dentro do ambiente selecionado;
- `toolbox.remover` exige confirmação explícita;
- `toolbox.instalar` e `toolbox.remover` exigem nome exato de pacote;
- o runtime avisa início da execução mediada, espera possível, retorno do controle e validação final nas mutações em toolbox;
- a política mantém gaps estruturais visíveis: `toolbox_default_selection_not_opened`, `toolbox_create_not_opened`, `toolbox_lifecycle_not_opened`, `toolbox_host_fallback_not_opened` e `toolbox_mutation_requires_exact_package_name`;
- host Atomic/imutável não bloqueia `toolbox` por si só, mas também não abre suporte amplo a imutáveis;
- em host imutável, a política deixa explícito `immutable_selected_surface=toolbox`.

### `distrobox` explícita

- pedido explicitamente marcado como `distrobox` continua no domínio `host_package`, mas troca a superfície para `execution_surface=distrobox`;
- `distrobox` não vira `requested_source`;
- `source_type=distrobox_host_package_manager`;
- `trust_level=mediated_environment`;
- a frase precisa trazer `na distrobox <ambiente>`;
- a política expõe `distrobox_requested_environment`, `distrobox_environment_status`, `distrobox_resolved_environment`, `distrobox_linux_family`, `distrobox_package_backends` e `distrobox_sudo_observed`;
- `distrobox.procurar` não exige confirmação;
- `distrobox.instalar` não exige confirmação, mas depende de backend distro-managed e `sudo` observados dentro do ambiente selecionado;
- `distrobox.remover` exige confirmação explícita;
- `distrobox.instalar` e `distrobox.remover` exigem nome exato de pacote;
- o runtime avisa início da execução mediada, espera possível, retorno do controle e validação final nas mutações em distrobox;
- a política mantém gaps estruturais visíveis: `distrobox_default_selection_not_opened`, `distrobox_create_not_opened`, `distrobox_lifecycle_not_opened`, `distrobox_host_fallback_not_opened` e `distrobox_mutation_requires_exact_package_name`;
- host Atomic/imutável não bloqueia `distrobox` por si só, mas também não abre suporte amplo a imutáveis;
- em host imutável, a política deixa explícito `immutable_selected_surface=distrobox`.

### `rpm-ostree` explícito

- pedido explicitamente marcado como `rpm-ostree` continua no domínio `host_package`, mas troca a superfície para `execution_surface=rpm_ostree`;
- `rpm-ostree` não vira `requested_source`;
- `source_type=rpm_ostree_layering`;
- `trust_level=immutable_host_surface`;
- a política expõe `rpm_ostree_status`, `rpm_ostree_pending_deployment`, `rpm_ostree_transaction_active`, `rpm_ostree_booted_requested_packages` e `rpm_ostree_pending_requested_packages`;
- `rpm_ostree.instalar` não exige confirmação, mas depende de `rpm-ostree` observado, `status --json` parseável e host imutável real;
- `rpm_ostree.remover` exige confirmação explícita;
- `rpm_ostree.instalar` e `rpm_ostree.remover` exigem nome exato de pacote;
- a política bloqueia quando já existe `pending deployment` ou transação ativa;
- a política mantém gaps estruturais visíveis: `rpm_ostree_search_not_opened`, `rpm_ostree_apply_live_not_opened`, `rpm_ostree_override_remove_not_opened`, `rpm_ostree_reboot_not_performed_by_aurora`, `rpm_ostree_transaction_chaining_not_opened` e `rpm_ostree_mutation_requires_exact_package_name`.

## Como a política afeta o runtime

### `policy_outcome`

Pode resultar, no mínimo, em:

- `allow`
- `block`
- `require_confirmation`

### `requires_confirmation`

Quando verdadeiro, a Aurora pede confirmação explícita com `--confirm` antes de mutações sensíveis.

Na `v1.2.0`, `--confirm` e `--yes` são aceitos como marcadores equivalentes de confirmação explícita, inclusive quando entram inline na frase inspecionada.

### `software_criticality`

Nesta release, a taxonomia continua pequena e pragmática:

- `low`
- `medium`
- `high`
- `sensitive`

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
- `mediated_environment_change`
- `mediated_environment_removal`
- `deployment_change`
- `deployment_change_sensitive`

## Exemplos de comportamento

- `aurora instalar firefox`
  resultado típico: `allow`
- `aurora remover sudo`
  resultado típico: `require_confirmation`
- `aurora instalar firefox` em host Atomic/imutável
  resultado típico: `block`
- `aurora instalar firefox no rpm-ostree`
  resultado típico: `allow`
- `aurora remover firefox no rpm-ostree`
  resultado típico: `require_confirmation`
- `aurora procurar google chrome no aur`
  resultado típico: `allow`
- `aurora procurar obs-studio do copr atim/obs-studio`
  resultado típico: `allow`
- `aurora instalar obs-studio do ppa ppa:obsproject/obs-studio`
  resultado típico: `require_confirmation`
- `aurora procurar firefox no flatpak`
  resultado típico: `allow`
- `aurora instalar ripgrep na toolbox devbox`
  resultado típico: `allow`
- `aurora remover ripgrep na toolbox devbox`
  resultado típico: `require_confirmation`
- `aurora instalar ripgrep na distrobox devbox`
  resultado típico: `allow`
- `aurora remover ripgrep na distrobox devbox`
  resultado típico: `require_confirmation`
- `aurora procurar htop no rpm-ostree`
  resultado típico: `block`

## O que ainda não está aberto

Continuam fora da `v1.2.0`:

- `otimizar`, cache, órfãos e bundles amplos de manutenção;
- `paru`, `yay` ou qualquer helper AUR como backend de `host_maintenance`;
- AUR implícita em `atualizar sistema`;
- suporte equivalente de `host_maintenance.atualizar` em Debian/Ubuntu, Fedora ou OpenSUSE nesta primeira absorção;
- fallback automático do host para `toolbox`;
- fallback automático do host para `distrobox`;
- fallback automático do host para `rpm-ostree`;
- default implícito de toolbox, autoseleção e descoberta mágica de ambiente;
- default implícito de distrobox, autoseleção e descoberta mágica de ambiente;
- criação automática de toolbox, criação automática de distrobox e administração ampla de lifecycle;
- mistura de `toolbox`, `distrobox` ou `rpm-ostree` com `aur`, `copr`, `ppa` ou `flatpak`;
- canonicalização ampla de alvo para `toolbox.instalar` e `toolbox.remover`;
- canonicalização ampla de alvo para `distrobox.instalar` e `distrobox.remover`;
- `rpm_ostree.procurar`, `apply-live`, `override remove`, reboot automático e chaining amplo de transações;
- descoberta automática de repositório COPR;
- descoberta automática de PPA ou inferência por nome do pacote;
- `ppa.procurar`, `ppa.remover` real, `remove-apt-repository` e cleanup/lifecycle amplo;
- descoberta automática de remotes `flatpak`;
- add automático de remote arbitrário;
- administração geral de remotes `flatpak`;
- helpers AUR além de `paru` e `yay`, e passthrough interativo para `aur.remover`;
- AppImage e GitHub Releases;
- toolbox default implícita, distrobox default implícita e `ujust`;
- suporte genérico a hosts imutáveis fora do corte explícito de `flatpak`, `toolbox`, `distrobox` e `rpm-ostree`.

Se `flatpak`, helper AUR, capacidade COPR, `add-apt-repository`, `toolbox`, `distrobox` ou `rpm-ostree` aparecerem no host sem pedido explícito, isso continua sendo apenas observação e não muda o default seguro de `host_package` no host.
