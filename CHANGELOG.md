# Changelog

## 🌌 Aurora v0.3.0

Fechamento público da release que abre AUR como fonte explícita de terceiro sobre a base já consolidada da `v0.2.0`, sem recontaminar `host_package`.

### Adicionado
- marcação pública inicial de AUR por frase explícita, como `aurora procurar <pacote> no aur`.
- `aur.procurar`, `aur.instalar` e `aur.remover` como primeira fonte terceira real da Aurora.
- `source_type=aur_repository` e `trust_level=third_party_build` como leitura própria da nova frente.
- resolução de alvo com separação entre pacote `foreign` e pacote oficial do host.

### Alterado
- `decision_record` e `aurora dev` agora expõem `requested_source`, helper selecionado e `source_mismatch`.
- a política de AUR nasce com confirmação explícita para mutações e bloqueio honesto quando `paru` não está observado.
- `--confirm` e `--yes` passam a contar como confirmação explícita também quando entram inline na frase inspecionada.
- `aur.instalar` anuncia a entrega e o retorno do helper interativo antes da validação final por probe.
- README, help e docs técnicas passam a refletir a `v0.3.0` como release pública atual.

### Higiene da release
- `VERSION` promovido para `v0.3.0`.
- `tests/audit_public_release.py` e `tests/release_gate_v0_3.sh` passam a congelar o contrato público final da release.
- `.gitignore` passa a ignorar `.codex` como artefato transitório local da ferramenta de desenvolvimento.

### Continua fora da v0.3.0
- fallback automático de pedido nu para AUR;
- helpers AUR além de `paru`;
- passthrough interativo para `aur.remover`;
- seleção de remote além do default `flathub`;
- COPR, PPA, AppImage e GitHub Releases;
- `rpm-ostree`, toolbox, distrobox e `ujust`;
- hosts imutáveis reais como superfície operacional.

## 🌌 Aurora v0.2.0

Fechamento público da release que abre `user_software` como segundo domínio real da Aurora, preservando `host_package` como base íntegra da `v0.1.0`.

### Adicionado
- `domain_kind=user_software` como parte real do contrato público.
- arbitragem inicial entre `host_package` e `user_software`, com default seguro para pedidos nus.
- `flatpak.procurar`, `flatpak.instalar` e `flatpak.remover` como primeira rota ativa de software do usuário.
- probes antes e depois para mutações `flatpak`, com `noop` honesto quando o estado já está satisfeito.
- gate final da `v0.2.0` com auditoria pública alinhada ao contrato real da release.

### Alterado
- `README.md`, `resources/help.txt` e docs principais agora descrevem a `v0.2.0` como release pública legítima.
- `aurora dev <frase>` e o `decision_record` passaram a expor melhor a leitura de domínio, escopo e rota.
- a política operacional agora governa `host_package` e `user_software`, incluindo `source_type=flatpak_remote`.
- `flatpak.remover` continua exigindo confirmação explícita quando a remoção realmente vai acontecer.

### Higiene da release
- `VERSION` promovido para `v0.2.0`.
- `.gitignore` passou a ignorar `__pycache__/` e `*.pyc`.
- artefatos Python compilados deixaram de fazer parte do rastreamento do repositório.

### Continua fora da v0.2.0
- seleção de remote além do default `flathub`;
- AUR, COPR, PPA, AppImage e GitHub Releases;
- `rpm-ostree`, toolbox, distrobox e `ujust`;
- suporte operacional real a hosts imutáveis;
- backlog amplo de arquivos, rede e manutenção de host.

## 🌌 Aurora v0.1.0

Primeiro release público da Aurora.

### Adicionado
- Novo produto, 100% Python, com launchers oficiais `aurora` e `auro`.
- Bootstrap próprio da Aurora com `python -m aurora`, `--help` e `--version`.
- Núcleo inicial de semântica herdada/refatorada da Aury, incluindo normalização conservadora, proteção de tokens sensíveis, split simples de ações e classificação mínima de intenção para `procurar`, `instalar` e `remover`.
- `host_profile` estruturado para Linux, com detecção de família, mutabilidade, tier de suporte e ferramentas observadas.
- `host_package.search` com execução real por família:
  - Arch/derivadas
  - Debian/Ubuntu/derivadas
  - Fedora
  - OpenSUSE mutável contido
- `decision_record` próprio da Aurora e comando `aurora dev <frase>` para observabilidade de decisão.
- Modelo inicial e operacional de política com `domain_kind`, `source_type`, `trust_level`, `software_criticality`, `trust_signals`, `trust_gaps`, `policy_outcome`, `requires_confirmation` e `reversal_level`.
- Estrutura modular inicial da Aurora em `semantics/`, `linux/`, `install/`, `observability/` e `presentation/`.

### Alterado
- A Aurora nasce com identidade própria e deixa de depender de Fish como centro do produto.
- O runtime foi organizado com separação mais clara entre planejamento, política, execução e apresentação.
- A instalação da própria ferramenta passou a seguir a direção de launcher fino + base própria da Aurora, em vez de repetir a casca histórica da Aury.

### Endurecimento da release
- `host_package.instalar` e `host_package.remover` passaram a executar de verdade em hosts mutáveis suportados.
- Mutações reais do host agora contam com probe antes/depois, `noop` honesto, bloqueio explícito para Atomic/imutáveis e trilha de execução no `decision_record`.
- Confirmação explícita por `--confirm` foi consolidada como parte real da UX para mutações sensíveis.

### Compatibilidade
- Suporte real na `v0.1.0` para:
  - Arch/derivadas mutáveis
  - Debian/Ubuntu/derivadas mutáveis
  - Fedora mutável
  - OpenSUSE mutável em escopo contido
- Hosts Atomic/imutáveis permanecem bloqueados por política, de forma explícita e honesta.

### Documentação
- Documentação pública mínima da release consolidada em:
  - `README.md`
  - `docs/ARCHITECTURE.md`
  - `docs/COMPATIBILITY_LINUX.md`
  - `docs/INSTALLATION_POLICY.md`
  - `docs/AURY_HERITAGE_MAP.md`
- `resources/help.txt` alinhado ao comportamento real da Aurora e ao uso de `--confirm`.

### Fora da v0.1.0
- `flatpak` como rota ativa.
- AUR, COPR, PPA, AppImage e GitHub Releases.
- `rpm-ostree`, toolbox, distrobox e `ujust`.
- Domínios de arquivos, rede e manutenção ampla do host.
