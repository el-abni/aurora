# Architecture - Aurora v0.5.0

## Tese curta

Aurora continua sendo um produto **100% Python** com contratos pequenos e observáveis:

- `host_package` para pacotes oficiais do host em `execution_surface=host`;
- `AUR` como fonte explícita de terceiro para pacote do host em Arch;
- `COPR` como fonte explícita de terceiro para pacote do host em Fedora;
- `PPA` como fonte explícita de terceiro para pacote do host em Ubuntu;
- `user_software` para software do usuário via `flatpak`;
- `toolbox` como `execution_surface` explícita para pacote distro-managed dentro de um ambiente mediado nomeado.

Ela não depende de Fish como centro do runtime, não trata ferramenta observada como promessa de suporte e não colapsa host e ambiente mediado numa rota opaca.

## Fluxo principal

1. `cli.py` recebe o comando público.
2. `semantics/` normaliza a frase e classifica a intenção mínima.
3. `linux/host_profile.py` detecta família, mutabilidade, distro, ferramentas observadas e toolboxes observadas no host.
4. `install/domain_classifier.py` decide entre default de `host_package`, fontes explícitas `AUR`, `COPR`, `PPA`, `user_software` via `flatpak` e `execution_surface=toolbox`.
5. `linux/toolbox.py` resolve o ambiente mediado quando a frase marca `toolbox` e observa a família Linux e o backend dentro desse ambiente.
6. `install/policy_engine.py` produz o juízo de política.
7. `install/candidates.py` e `install/route_selector.py` escolhem a rota executável.
8. `install/execution_handoff.py` executa, faz probes e mantém visível se a ação ocorre no host ou dentro da toolbox.
9. `observability/` registra e renderiza o `decision_record`.

## Módulos principais

### `semantics/`

- normalização;
- proteção de tokens sensíveis;
- split simples de ações;
- classificação mínima de `procurar`, `instalar` e `remover`.

### `linux/`

- `host_profile`;
- detecção de mutabilidade;
- matriz por família;
- rotas concretas de `host_package`;
- observação e roteamento contido de `toolbox`;
- fronteira entre backend oficial do host, fontes terceiras explícitas e ambiente mediado explícito.

### `install/`

- classificação de domínio, fonte e `execution_surface`;
- policy;
- resolução controlada de ambiente;
- resolução controlada de alvo;
- candidatos e seleção de rota;
- handoff de execução;
- separação entre bloqueio, `noop`, confirmação e erro operacional.

### `observability/`

- `decision_record`;
- `environment_resolution`;
- `toolbox_profile`;
- renderização curta e expandida;
- `aurora dev`.

### `presentation/`

- help;
- mensagens de bloqueio;
- mensagens de confirmação;
- mensagens de resultado.

## Rotas abertas na v0.5.0

### `host_package`

Rotas reais:

- `host_package.search`
- `host_package.instalar`
- `host_package.remover`

### `AUR` explícito

Rotas reais:

- `aur.procurar`
- `aur.instalar`
- `aur.remover`

Garantias:

- `AUR` só entra por pedido explícito;
- usa apenas `paru` e `yay`;
- quando ambos estão observados, a ordem do contrato é `paru`, depois `yay`;
- `aur.instalar` usa handoff interativo;
- `aur.remover` continua não interativo;
- helper observado fora do contrato continua visível, mas bloqueado como rota.

### `COPR` explícito

Rotas reais:

- `copr.procurar`
- `copr.instalar`
- `copr.remover`

Garantias:

- `COPR` só entra por pedido explícito;
- a frase precisa carregar `owner/project`;
- a frente só abre em Fedora mutável com `dnf copr` observado;
- `copr.procurar` consulta apenas o repositório explicitamente pedido;
- `copr.instalar` observa se o repositório explícito já estava habilitado e só planeja `enable` quando necessário;
- `copr.remover` exige verificação de proveniência RPM via `from_repo`;
- nenhuma rota COPR faz disable automático, cleanup heurístico ou lifecycle amplo do repositório.

### `PPA` explícito

Rota real:

- `ppa.instalar`

Garantias:

- `PPA` só entra por pedido explícito;
- a frase precisa carregar a coordenada canônica `ppa:owner/name`;
- a frente só abre em Ubuntu mutável com `add-apt-repository`, `apt-get` e `dpkg` observados;
- `ppa.instalar` planeja `add-apt-repository -n`, `apt-get update` e `apt-get install` como passos preparatórios explícitos;
- `ppa.remover` permanece bloqueado por honestidade;
- URL genérica de apt repo não entra como PPA;
- não existe descoberta automática de PPA nem fallback implícito de pedido nu para PPA.

### `user_software`

Rotas reais:

- `flatpak.procurar`
- `flatpak.instalar`
- `flatpak.remover`

Garantias:

- `flatpak` só entra por pedido explícito;
- `flatpak.instalar` e `flatpak.remover` usam escopo explícito de usuário;
- `flatpak.procurar` e `flatpak.instalar` assumem `flathub` apenas quando nenhum remote é informado;
- `flatpak` aceita remote explícito somente quando esse remote já é observável via `flatpak remotes`;
- `flatpak.procurar` usa `flatpak remote-ls` filtrado localmente para respeitar o remote selecionado;
- `flatpak.remover` usa remote explícito apenas como restrição de `origin`, sem default implícito para remoção;
- `flatpak.remover` exige confirmação explícita quando a remoção realmente precisa acontecer.

### `toolbox` explícita

Rotas reais:

- `toolbox.procurar`
- `toolbox.instalar`
- `toolbox.remover`

Garantias:

- `toolbox` entra como `execution_surface`, não como `requested_source`;
- a frase precisa carregar o nome explícito do ambiente em `na toolbox <ambiente>`;
- `toolbox` observa o ambiente antes de abrir policy e route;
- `toolbox` observa `linux_family`, `support_tier`, `package_backends` e `sudo` dentro do ambiente selecionado;
- `toolbox.procurar` pode usar busca humana dentro da toolbox selecionada;
- `toolbox.instalar` e `toolbox.remover` exigem nome exato de pacote nesta release;
- `toolbox.remover` exige confirmação explícita;
- a mutação acontece dentro da toolbox e não toca o host;
- não existe default implícito de toolbox, autocriação, lifecycle amplo, mistura com AUR/COPR/PPA/flatpak nem fallback host -> toolbox.

## Fronteiras deliberadas

A `v0.5.0` continua pequena de propósito:

- pedido nu continua em `host_package` no host;
- `toolbox` não vira escape hatch implícito para Atomic/imutáveis;
- `toolbox` não prepara abstração geral para distrobox;
- `toolbox.instalar` e `toolbox.remover` não fazem canonicalização ampla de alvo;
- `AUR`, `COPR`, `PPA` e `flatpak` continuam separados de `toolbox`;
- hosts imutáveis reais continuam fora da superfície operacional ampla do produto, mesmo com `toolbox` agora aberta de forma explícita.
