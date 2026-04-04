# Architecture - Aurora v0.4.1

## Tese curta

Aurora continua sendo um produto **100% Python** com contratos pequenos e observáveis:

- `host_package` para pacotes oficiais do host;
- `AUR` como fonte explícita de terceiro para pacote do host em Arch;
- `COPR` como fonte explícita de terceiro para pacote do host em Fedora;
- `PPA` como fonte explícita de terceiro para pacote do host em Ubuntu;
- `user_software` para software do usuário via `flatpak`.

Ela não depende de Fish como centro do runtime, não trata ferramenta observada como promessa de suporte e não colapsa fontes diferentes numa única rota opaca.

## Fluxo principal

1. `cli.py` recebe o comando público.
2. `semantics/` normaliza a frase e classifica a intenção mínima.
3. `linux/host_profile.py` detecta família, mutabilidade, distro e ferramentas observadas.
4. `install/domain_classifier.py` decide entre default de `host_package`, fontes explícitas `AUR`, `COPR`, `PPA` e `user_software`.
5. `install/policy_engine.py` produz o juízo de política.
6. `install/candidates.py` e `install/route_selector.py` escolhem a rota executável.
7. `install/execution_handoff.py` executa, faz probes, roda passos preparatórios quando a rota exige preparação explícita e entrega o terminal ao helper quando a rota é interativa.
8. `observability/` registra e renderiza o `decision_record`.

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
- fronteira entre backend oficial do host e fontes terceiras explícitas.

### `install/`

- classificação de domínio e fonte;
- policy;
- resolução controlada de alvo;
- candidatos e seleção de rota;
- handoff de execução, incluindo preparação explícita de rota quando necessário;
- separação entre bloqueio, `noop`, confirmação e erro operacional.

### `observability/`

- `decision_record`;
- renderização curta e expandida;
- `aurora dev`.

### `presentation/`

- help;
- mensagens de bloqueio;
- mensagens de confirmação;
- mensagens de resultado.

## Rotas abertas na v0.4.1

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
- `ppa.remover` permanece bloqueado por honestidade, porque a Aurora ainda não demonstra proveniência APT por PPA e não abre lifecycle amplo do repositório;
- URL genérica de apt repo não entra como PPA;
- não existe descoberta automática de PPA, busca global em PPA ou fallback implícito de pedido nu para PPA.

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
- mutação usa probe antes/depois e `noop` honesto;
- `flatpak.remover` exige confirmação explícita quando a remoção realmente precisa acontecer.

## Fronteiras deliberadas

A `v0.4.1` continua pequena de propósito:

- pedido nu continua em `host_package`;
- `AUR` não vira fallback mágico;
- `COPR` continua sem descoberta automática nem busca global;
- `PPA` não vira sinônimo de `apt` externo;
- `PPA` não abre Debian puro nem outras derivadas Debian-like sem sustentação operacional;
- `PPA` não abre `ppa.procurar`, `ppa.remover`, `remove-apt-repository` nem cleanup automático;
- `flatpak` não faz descoberta automática, add arbitrário nem administração geral de remotes;
- hosts imutáveis reais continuam fora da superfície operacional.
