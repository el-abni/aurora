# Architecture - Aurora v0.6.4

## Tese curta

Aurora continua sendo um produto **100% Python** com contratos pequenos e observáveis:

- `host_package` para pacotes oficiais do host em `execution_surface=host`;
- `AUR` como fonte explícita de terceiro para pacote do host em Arch;
- `COPR` como fonte explícita de terceiro para pacote do host em Fedora;
- `PPA` como fonte explícita de terceiro para pacote do host em Ubuntu;
- `user_software` para software do usuário via `flatpak`;
- `toolbox` como `execution_surface` explícita para pacote distro-managed dentro de um ambiente mediado nomeado;
- `distrobox` como `execution_surface` explícita para pacote distro-managed dentro de um ambiente mediado nomeado.
- `rpm-ostree` como `execution_surface` explícita para layering/uninstall no host imutável.

Ela não depende de Fish como centro do runtime, não trata ferramenta observada como promessa de suporte e não colapsa host e ambiente mediado numa rota opaca.

## Espinha canônica da linha

A `v0.6.4` não abre rota nova. Ela preserva a espinha canônica fechada na `v0.6.3` com oito peças pequenas e explícitas:

- `tests/release_gate_canonic_line.sh` como régua corrente da linha;
- `tests/release_gate_v0_6_2.sh` preservado como gate histórico da release `v0.6.2`;
- `tests/README.md` como papel canônico da pasta `tests/`;
- `docs/AURORA_INVARIANTS.md` como registro curto das lições já provadas pelo repositório;
- `docs/DECISION_RECORD_SCHEMA.md` como contrato curto do `decision_record`;
- `docs/FACTS_VS_RENDERING.md` como fronteira entre fato operacional e renderização;
- `docs/AURY_TO_AURORA_DOSSIER.md` como dossiê canônico da fronteira `Aury -> Aurora`;
- `tests/audit_decision_record_contract.py` como auditor curto do novo chão contratual.

Essa espinha reaproveita uma lição já aprendida pela Aurora: a linha endurece melhor com contrato pequeno, docs auditáveis e gate curto do que com feature nova. Ela também evita um choque já conhecido com o patrimônio do repo: Fish e stage pública não entram como centro do gate da Aurora.

## Disciplina operacional da v0.6.4

A `v0.6.4` formaliza o workflow que faltava em volta dessa espinha:

- `docs/WORKFLOW_DE_TESTES_E_RELEASE.md` define as três camadas de validação;
- `tests/REVIEW_CHECKLIST.md` fixa a revisão humana curta;
- `tests/release_gate_iteracao.sh` cobre coding comum;
- `tests/release_gate_pre_push.sh` reaproveita a régua corrente da linha antes de push;
- `tests/release_gate_pre_release.sh` fecha o lado automatizado antes de tag e release;
- `tests/release_gate_v0_6_2.sh` continua histórico, exercitado sem voltar a ser a régua corrente;
- gate automatizado não substitui checklist humano nem terminal real.

## Fluxo principal

1. `cli.py` recebe o comando público.
2. `semantics/` normaliza a frase e classifica a intenção mínima.
3. `linux/host_profile.py` detecta família, mutabilidade, distro, ferramentas observadas, toolboxes observadas e distroboxes observadas no host.
4. `install/domain_classifier.py` decide entre default de `host_package`, fontes explícitas `AUR`, `COPR`, `PPA`, `user_software` via `flatpak`, `execution_surface=toolbox`, `execution_surface=distrobox` e `execution_surface=rpm_ostree`.
5. `linux/toolbox.py` e `linux/distrobox.py` resolvem o ambiente mediado quando a frase marca a superfície e observam a família Linux e o backend dentro desse ambiente.
6. `linux/rpm_ostree.py` observa `rpm-ostree status --json` quando a frase marca a superfície imutável do host.
7. `install/policy_engine.py` produz o juízo de política.
8. `install/candidates.py` e `install/route_selector.py` escolhem a rota executável.
9. `install/execution_handoff.py` executa, faz probes e mantém visível se a ação ocorre no host mutável, no host imutável via `rpm-ostree`, dentro da toolbox ou dentro da distrobox.
10. `contracts/decision_record_schema.py` e `contracts/stable_ids.py` fixam o schema versionado e os IDs mínimos estáveis do `decision_record`.
11. `observability/` registra `facts`, preserva compatibilidade por espelhos legados e renderiza a camada pública.

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
- observação e roteamento contido de `toolbox` e `distrobox`;
- observação e roteamento contido de `rpm-ostree` como superfície de host imutável;
- compartilhamento mínimo do miolo de pacote distro-managed dentro de ambiente mediado, sem apagar a distinção entre as superfícies;
- fronteira entre backend oficial do host mutável, fontes terceiras explícitas, ambiente mediado explícito e host imutável explícito.

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
- `schema=aurora.decision_record.v1`;
- `stable_ids`;
- `facts`;
- `presentation`;
- `environment_resolution`;
- `toolbox_profile`;
- `distrobox_profile`;
- `rpm_ostree_status`;
- `immutable_selected_surface`;
- renderização curta e expandida;
- `aurora dev`.

### `presentation/`

- help;
- mensagens de bloqueio;
- mensagens de confirmação;
- mensagens de resultado;
- indicador discreto de fala na mensagem pública principal;
- polimento de texto e voz pública sem decidir policy, suporte, bloqueio, confirmação ou resultado.

## Decision Record Canônico

Na `v0.6.4`, o `decision_record` continua com uma leitura canônica curta:

- `schema.schema_id=aurora.decision_record.v1`;
- `stable_ids.action_id`, `stable_ids.route_id` e `stable_ids.event_id` como IDs mínimos estáveis;
- `facts` como camada factual de request, policy, route, execution e observações;
- `presentation` como camada de voz.

Compatibilidade:

- o payload antigo continua espelhado no topo nesta linha;
- `host_package.search` continua apenas como `route_name` legado;
- o ID canônico da rota de busca do host passa a ser `host_package.procurar`.

## Rotas abertas na v0.6.4

### `host_package`

Rotas reais:

- `host_package.procurar`
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
- `aur.instalar` usa handoff interativo e avisa explicitamente quando o usuário precisa assumir o terminal;
- o handoff AUR também deixa explícitos pausa silenciosa de build e Enter extra em alguns terminais;
- a confirmação pós-instalação AUR valida a presença final no host sem depender só de `pacman -Qm`;
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
- as mutações em `toolbox` avisam início da execução, espera possível, retorno do controle e validação final;
- a mutação acontece dentro da toolbox e não toca o host;
- não existe default implícito de toolbox, autocriação, lifecycle amplo, mistura com AUR/COPR/PPA/flatpak nem fallback host -> toolbox.

### `distrobox` explícita

Rotas reais:

- `distrobox.procurar`
- `distrobox.instalar`
- `distrobox.remover`

Garantias:

- `distrobox` entra como `execution_surface`, não como `requested_source`;
- a frase precisa carregar o nome explícito do ambiente em `na distrobox <ambiente>`;
- `distrobox` observa o ambiente antes de abrir policy e route;
- `distrobox` observa `linux_family`, `support_tier`, `package_backends` e `sudo` dentro do ambiente selecionado;
- `distrobox.procurar` pode usar busca humana dentro da distrobox selecionada;
- `distrobox.instalar` e `distrobox.remover` exigem nome exato de pacote nesta release;
- `distrobox.remover` exige confirmação explícita;
- as mutações em `distrobox` avisam início da execução, espera possível, retorno do controle e validação final;
- a mutação acontece dentro da distrobox e não toca o host;
- `toolbox` e `distrobox` compartilham apenas o miolo de pacote distro-managed dentro do ambiente; a observação, a resolução de ambiente e os sinais de policy continuam separados;
- não existe default implícito de distrobox, autocriação, lifecycle amplo, mistura com AUR/COPR/PPA/flatpak nem fallback host -> distrobox.

### `rpm-ostree` explícito

Rotas reais:

- `rpm_ostree.instalar`
- `rpm_ostree.remover`

Garantias:

- `rpm-ostree` entra como `execution_surface`, não como `requested_source`;
- a frase precisa marcar a superfície explicitamente, por exemplo `no rpm-ostree`;
- a frente observa `rpm-ostree status --json` antes de liberar mutação;
- `rpm_ostree.instalar` e `rpm_ostree.remover` exigem nome exato de pacote;
- `rpm_ostree.remover` exige confirmação explícita;
- a rota deixa visível se já existe `pending deployment` ou transação ativa;
- a confirmação de sucesso observa o deployment `default/pending`, não promete `apply-live`;
- `rpm_ostree.procurar` ainda não entra como rota executável nesta release.

## Fronteiras deliberadas

A `v0.6.4` continua pequena de propósito:

- pedido nu continua em `host_package` no host;
- em host imutável, pedido nu bloqueia com `immutable_observed_surfaces` e `immutable_selected_surface=block`;
- `toolbox` não vira escape hatch implícito para Atomic/imutáveis;
- `distrobox` também não vira escape hatch implícito para Atomic/imutáveis;
- `rpm-ostree` também não vira backend mágico para qualquer limitação do host;
- `toolbox.instalar` e `toolbox.remover` não fazem canonicalização ampla de alvo;
- `distrobox.instalar` e `distrobox.remover` não fazem canonicalização ampla de alvo;
- `rpm_ostree.instalar` e `rpm_ostree.remover` não abrem `apply-live`, reboot automático, `override remove` nem chaining amplo;
- `AUR`, `COPR`, `PPA` e `flatpak` continuam separados de `toolbox` e de `distrobox`;
- hosts imutáveis reais continuam fora da superfície operacional ampla do produto, mesmo com `flatpak`, `toolbox`, `distrobox` e `rpm-ostree` já amarrados de forma explícita.
