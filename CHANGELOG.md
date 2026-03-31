# Changelog

## 🌌 Aurora v0.1.0

Primeiro release público da Aurora.

### Adicionado
- Novo produto, 100% Python, com launchers oficiais `aurora` e `auro`.
- Bootstrap próprio da Aurora com `python -m aurora`, `--help` e `--version`.
- Núcleo inicial de semântica herdada/refatorada da Aury, incluindo normalização conservadora, proteção de tokens sensíveis, split simples de ações e classificação mínima de intenção para `procurar`, `instalar` e `remover`.
- `host_profile` estruturado para Linux, com detecção de família, mutabilidade, tier de suporte e ferramentas observadas.
- `host_package.procurar` com execução real por família:
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
- Mutações reais do host agora contam com probe antes/depois, noop honesto, bloqueio explícito para Atomic/imutáveis e trilha de execução no `decision_record`.
- Confirmação explícita por `--confirm` foi consolidada como parte real da UX para mutações sensíveis.

### Compatibilidade
- Suporte real na v0.1.0 para:
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

### Testes
- Primeira rodada fechou com 20 testes verdes cobrindo bootstrap, semântica mínima, `host_profile`, `host_package.procurar`, bloqueio Atomic e `decision_record`.
- A segunda rodada consolidou a mutação real de `host_package` com 28 testes verdes.
- O fechamento público da release consolidou gates pequenos e fortes para a v0.1.0.
- A validação local em terminal real confirmou instalação da Aurora, `--version`, `--help`, `procurar`, `instalar` e `remover` funcionando na prática.

### Fora da v0.1.0
- `flatpak` como rota ativa.
- AUR, COPR, PPA, AppImage e GitHub Releases.
- `rpm-ostree`, toolbox, distrobox e `ujust`.
- Domínios de arquivos, rede e manutenção ampla do host.
