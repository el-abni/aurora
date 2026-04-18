# Changelog

## 🌌 Aurora v1.0.0

Fechamento curto de contrato e abertura pública honesta do estado já fechado nas Fases 0–3 da seam `local_model`. Esta release não redesenha o kernel: ela promove o provider real já integrado, mantém `model_off` íntegro por default e fixa `model_on` como camada assistiva opcional, factual e subordinada ao kernel determinístico.

### Alterado

- `VERSION`, `README.md`, `resources/help.txt`, `docs/COMPATIBILITY_LINUX.md`, `docs/INSTALLATION_POLICY.md`, docs centrais, `tests/REVIEW_CHECKLIST.md` e auditorias públicas passam a refletir a `v1.0.0` como release atual;
- a seam em `python/aurora/local_model/` entra publicamente no caminho observável de `aurora dev` / `decision_record`, sem abrir rota nova, sem tocar em `policy`, `support`, `block`, `confirmation`, `route`, `execution` nem em verdade operacional;
- o provider real canônico atual passa a ser `ollama`, com `qwen2.5:3b-instruct` como modelo canônico inicial quando `AURORA_LOCAL_MODEL_MODEL` não é informado;
- `model_off` continua baseline adulto por default; `model_on` continua opcional e apenas assistivo quando `AURORA_MODEL_MODE=model_on` e `AURORA_LOCAL_MODEL_PROVIDER=ollama`;
- `facts.local_model` e o bloco `Local model seam` passam a ser documentados como observabilidade factual mínima, com `stable_ids`, `facts` e `presentation` preservados como espinha pública, `fallback_reason` canônico em snake_case, `output_text` preservado cru como fato e fallback determinístico quando o provider falta, falha ou sai do contrato;
- o endurecimento operacional inicial do provider permanece pequeno e contido: timeout default calibrado por smoke real, piso maior para `explain` no caminho default, `keep_alive` e `num_predict` curto por capability.
- o fechamento da `v1.0.0` passa a incluir `tests/release_gate_canonic_line.sh` no fluxo final de validação antes de push/tag/release.
- a release `v1.0.0` foi fechada com disciplina operacional seguindo `docs/WORKFLOW_DE_TESTES_E_RELEASE.md`, `tests/REVIEW_CHECKLIST.md`, `tests/release_gate_canonic_line.sh`, `tests/release_gate_iteracao.sh`, `tests/release_gate_pre_push.sh`, `tests/release_gate_pre_release.sh` e `tests/audit_workflow_release.py`.

### Continua fora da v1.0.0

- múltiplos providers públicos ou seleção automática entre providers;
- múltiplos modelos canônicos públicos;
- qualquer autoridade do modelo sobre `policy`, suporte, bloqueio, confirmação, rota, execução ou verdade operacional;
- qualquer uso do modelo local como frente genérica de chat ou como muleta para contrato frouxo;
- `host_maintenance`, rede e arquivos;
- parser amplo;
- refactor estrutural grande;
- qualquer abertura lateral de Aury ou backlog futuro como se já estivesse entregue.

## 🌌 Aurora v0.7.0

Release pública pequena em superfície e grande em papel estrutural. Esta rodada não abre a `v1.0.0`: ela promove publicamente a linha já fechada em quatro cortes internos, mantém a superfície pública curta e deixa a Aurora pronta para receber o modelo local depois sobre um kernel determinístico já adulto.

### Alterado

- `VERSION`, `README.md`, `resources/help.txt`, banners públicos, docs centrais e auditorias públicas passam a refletir a `v0.7.0` como release pública atual;
- `tests/release_gate_canonic_line.sh`, `docs/WORKFLOW_DE_TESTES_E_RELEASE.md`, `tests/release_gate_iteracao.sh`, `tests/release_gate_pre_push.sh`, `tests/release_gate_pre_release.sh`, `tests/REVIEW_CHECKLIST.md` e `tests/audit_workflow_release.py` continuam sendo a base do workflow disciplinado da linha também no fechamento público da `v0.7.0`;
- o fechamento dos cortes 1 a 4 passa a ficar explícito na leitura pública da release: baseline factual, observabilidade canônica, seam do modelo local, fallback determinístico e autoridade limitada;
- o `decision_record` público continua em `schema + stable_ids + facts + presentation`, com a seam do modelo local cercada em `facts.local_model` e sem abertura de autoridade operacional nova;
- a seam em `python/aurora/local_model/` continua pequena e auditável, com `model_off` íntegro por default e `model_on` apenas como camada assistiva opcional;
- `aurora dev`, `decision_record`, docs de contrato e auditorias passam a sustentar publicamente a leitura correta da linha: o modelo pode clarificar, resumir, explicar e desambiguar candidatos já estruturados, mas não decide `policy`, suporte, bloqueio, confirmação, rota, execução ou verdade operacional;
- a superfície instalada e o checkout local foram realinhados antes desta promoção pública, para evitar a bridge operacional já detectada no fechamento da candidata final.

### Continua fora da v0.7.0

- provider real de modelo local;
- qualquer abertura pública da `v1.0.0`;
- qualquer nova fonte, nova superfície, nova família ou nova frente de produto;
- `host_maintenance`, rede e arquivos;
- refactor estrutural grande;
- parser amplo;
- qualquer tentativa de usar modelo local para remendar contrato frouxo ou para mandar no kernel.

## 🌌 Aurora v0.6.5

Faixa curta de superfície pública/UX. Esta rodada não abre domínio novo: preserva a espinha canônica fechada na `v0.6.3`, preserva a disciplina operacional consolidada na `v0.6.4` e reorganiza o help para voltar a ser help de uso, não mini documentação embutida.

### Alterado

- `resources/help.txt` foi reorganizado por categoria/superfície, com foco em uso real, exemplos curtos, observabilidade e confirmação;
- o help deixa de repetir blocos longos de contrato, compatibilidade e “fora da release”, e passa a apontar esses detalhes para `README.md`, `docs/COMPATIBILITY_LINUX.md`, `docs/INSTALLATION_POLICY.md` e `docs/WORKFLOW_DE_TESTES_E_RELEASE.md`;
- `README.md`, `docs/ARCHITECTURE.md`, `resources/help.txt` e auditorias públicas passam a refletir a `v0.6.5` como release pública atual;
- `tests/release_gate_canonic_line.sh`, `tests/release_gate_iteracao.sh`, `tests/release_gate_pre_push.sh`, `tests/release_gate_pre_release.sh`, `tests/REVIEW_CHECKLIST.md` e `tests/audit_workflow_release.py` continuam sendo a base disciplinada da linha;
- o contrato público, `stable_ids`, `facts`, `presentation`, workflow, gates e checklist continuam os mesmos da `v0.6.4`; a mudança desta release é utilidade real do help, não expansão de superfície.

### Continua fora da v0.6.5

- qualquer nova fonte, nova superfície, nova família ou nova frente de produto;
- modelo local;
- `host_maintenance`, rede e arquivos;
- refactor estrutural grande;
- expansão de parser;
- qualquer tentativa de empurrar detalhes longos de compatibilidade, limite ou workflow de volta para dentro do help.

## 🌌 Aurora v0.6.4

Faixa curta de workflow, revisão, testes e disciplina de subida. Esta rodada não abre domínio novo: reaproveita a espinha canônica fechada na `v0.6.3` e formaliza o fluxo operacional para coding comum, push, tag e release.

### Adicionado

- `docs/WORKFLOW_DE_TESTES_E_RELEASE.md` como workflow canônico curto da `v0.6.4`;
- `tests/REVIEW_CHECKLIST.md` como checklist humano de revisão antes de subir;
- `tests/release_gate_iteracao.sh` como gate de feedback rápido durante coding;
- `tests/release_gate_pre_push.sh` como gate antes de push;
- `tests/release_gate_pre_release.sh` como gate automatizado antes de tag e release;
- `tests/audit_workflow_release.py` como auditor curto da nova disciplina operacional.

### Alterado

- `tests/release_gate_canonic_line.sh` continua como régua corrente da linha, mas agora também protege o workflow da `v0.6.4`;
- `README.md`, `docs/ARCHITECTURE.md`, `tests/README.md`, `resources/help.txt` e auditorias públicas passam a refletir a `v0.6.4` como release pública atual;
- `docs/AURORA_INVARIANTS.md` passa a registrar explicitamente que gate automatizado não substitui revisão humana nem terminal real;
- o contrato público, o schema do `decision_record`, `stable_ids`, `facts`, `presentation` e as rotas abertas continuam os mesmos da `v0.6.3`; a mudança desta release é disciplina operacional, não expansão de superfície.

### Continua fora da v0.6.4

- qualquer nova fonte, nova superfície, nova família ou nova frente de produto;
- modelo local;
- `host_maintenance`, rede e arquivos;
- qualquer boundary lateral tratado como implementação antes da hora;
- refactor estrutural grande;
- expansão de parser;
- qualquer tentativa de tratar checklist humano ou terminal real como problema resolvido apenas por gate automático.

## 🌌 Aurora v0.6.3

Faixa curta de canonização da linha. Esta rodada não abre fonte, superfície, parser ou frente nova de produto. Ela fecha o chão contínuo da Aurora com gate canônico, docs curtas, schema versionado do `decision_record`, IDs mínimos estáveis, fronteira explícita entre fato e renderização e dossiê canônico `Aury -> Aurora`.

### Adicionado

- `docs/AURORA_INVARIANTS.md` como registro curto das lições já provadas pelo repositório e já consideradas patrimônio operacional da Aurora;
- `tests/README.md` como papel canônico explícito da pasta `tests/`;
- `tests/audit_canonic_line.py` como auditor pequeno da nova espinha da linha;
- `tests/release_gate_canonic_line.sh` como régua corrente da linha;
- `docs/DECISION_RECORD_SCHEMA.md` como contrato curto e operacional do `decision_record`;
- `docs/FACTS_VS_RENDERING.md` como fronteira explícita entre fato operacional e voz;
- `docs/AURY_TO_AURORA_DOSSIER.md` como dossiê canônico da fronteira `Aury -> Aurora`;
- `python/aurora/contracts/decision_record_schema.py` e `python/aurora/contracts/stable_ids.py` como contrato mínimo executável da nova espinha;
- `tests/audit_decision_record_contract.py` como auditor curto do schema, dos IDs estáveis e da separação `facts` vs `presentation`.

### Alterado

- `README.md`, `docs/ARCHITECTURE.md`, `docs/AURY_HERITAGE_MAP.md`, `resources/help.txt` e auditorias públicas passam a refletir a `v0.6.3` como versão pública única desta entrega;
- `tests/release_gate_v0_6_2.sh` permanece como gate histórico da release `v0.6.2`, mas deixa explícito que a régua corrente da linha agora é `tests/release_gate_canonic_line.sh`;
- o `decision_record` passa a publicar `schema`, `stable_ids`, `facts` e `presentation` sem quebrar os espelhos legados já usados pela base atual;
- `host_package.search` deixa de ser a referência pública da rota de busca do host: o ID canônico passa a ser `host_package.procurar`, preservando o nome antigo apenas como espelho legado de compatibilidade.

### Continua fora da v0.6.3

- qualquer nova fonte, nova superfície, nova família ou nova frente de produto;
- fallback automático, descoberta mágica ou parser amplo;
- manutenção ampla do host, arquivos e rede;
- modelo local;
- qualquer tentativa de empurrar boundaries laterais como implementação antes do fechamento da linha;
- qualquer expansão disfarçada enquanto a linha ainda está sendo canonizada.

## 🌌 Aurora v0.6.2

Release pequena de polimento operacional, UX pública e endurecimento final sobre a base já revisada na `v0.6.1`. O corte desta rodada não abre frente nova: ele melhora o fluxo percebido pelo usuário, fecha mensagens públicas ainda secas e deixa AUR, toolbox e distrobox mais claros no momento de execução.

### Corrigido

- `aur.instalar` passa a avisar de forma mais clara quando o helper assume o terminal, inclusive em casos de pausa silenciosa durante build e possibilidade de Enter extra ao final;
- mutações mediadas em `toolbox` e `distrobox` agora anunciam início, espera possível, retorno do controle e validação final do estado;
- bloqueios, erros, `noops`, confirmações e sucessos ganham wording mais claro, com melhor caixa, pontuação e acabamento de produto.

### Alterado

- a superfície pública em pt-BR foi revisada com mais agressividade em `messages.py`, `text_polish.py`, help, docs mínimas e `aurora dev`;
- notas e reasons das superfícies mediadas ficaram mais legíveis em `decision_record`, sem mudar o contrato nem a semântica real das rotas;
- help, README e docs públicas passam a refletir a `v0.6.2` como release pública atual.

### Continua fora da v0.6.2

- qualquer nova fonte, nova superfície, nova família ou nova frente de produto;
- passthrough anárquico, fallback automático, descoberta mágica ou parser amplo;
- AppImage, GitHub Releases e `ujust`;
- manutenção ampla do host, arquivos e rede;
- qualquer expansão disfarçada enquanto a linha ainda está sendo endurecida.

## 🌌 Aurora v0.6.1

Release de revisão, correção, polimento e congelamento sobre a base já aberta na `v0.6.0`. O corte desta rodada não abre nova frente: ele endurece a superfície pública existente, melhora a observabilidade do runtime, reduz falso negativo conhecido de confirmação AUR e deixa o produto mais claro antes do próximo ciclo.

### Corrigido

- falhas operacionais de mutação agora tentam expor, de forma curta e segura, o motivo útil informado pelo backend em vez de cair só em “erro operacional” genérico;
- `aur.instalar` deixa de depender exclusivamente de `pacman -Qm` na confirmação pós-instalação e passa a validar a presença real final do pacote no host;
- a UX de handoff interativo para helpers AUR passa a avisar melhor quando o usuário precisa assumir o terminal, inclusive em casos em que o helper pode pedir Enter, seleção, revisão de build ou senha;
- a mensagem de retorno do handoff interativo deixa explícito que a Aurora ainda valida o estado final quando o helper devolve o terminal;
- summaries e mensagens principais deixam de vazar placeholders crus como coordenadas `'-'` em caminhos públicos centrais.

### Alterado

- a rota AUR continua explícita, pequena e contida, mas a confirmação final agora separa melhor “pacote presente no host” de “classificação foreign”, para evitar falso negativo sem relaxar a honestidade da resolução;
- `aurora dev` fica menos ruidoso em casos comuns ao esconder linhas de host imutável quando elas não trazem sinal real para a decisão atual;
- help, README, docs técnicas e wording público passam a refletir a `v0.6.1` como release pública atual;
- o texto público em pt-BR recebeu revisão de acentuação, caixa e acabamento nas mensagens mais visíveis desta rodada.

### Continua fora da v0.6.1

- qualquer nova fonte, nova superfície, nova família ou nova frente de produto;
- fallback automático, descoberta mágica, parser conversacional amplo ou passthrough anárquico;
- `aur.remover` em passthrough interativo;
- AppImage, GitHub Releases e `ujust`;
- manutenção ampla do host, arquivos e rede;
- qualquer expansão disfarçada de backlog enquanto a base ainda estava em revisão.

## 🌌 Aurora v0.6.0

Fechamento contido, mas estrutural, da primeira frente operacional real para hosts imutáveis: `rpm-ostree` entra como superfície explícita, e o host Atomic/imutável deixa de ser apenas um bloqueio genérico para virar uma decisão auditável entre `flatpak`, `toolbox`, `distrobox`, `rpm-ostree` ou bloqueio.

### Adicionado

- `execution_surface=rpm_ostree` como nova superfície explícita de host imutável.
- `rpm_ostree.instalar` e `rpm_ostree.remover` como primeiro corte real de layering/uninstall via `rpm-ostree`.
- observação estruturada de `rpm-ostree status --json`, incluindo `pending deployment`, transação ativa e pacotes solicitados no deployment booted/default.
- sinais explícitos de host imutável em `policy`, `route`, `decision_record` e `aurora dev`, como `immutable_observed_surfaces` e `immutable_selected_surface`.

### Alterado

- host Atomic/imutável já não responde apenas com bloqueio genérico em `host_package`: o bloqueio de pedido nu agora expõe quais superfícies foram observadas e por que a Aurora não infere entre elas.
- `flatpak`, `toolbox` e `distrobox` continuam explícitos, mas passam a carregar seleção auditável de superfície quando o host é imutável.
- `rpm-ostree` não entra como `requested_source`; entra como superfície operacional distinta do host mutável comum e distinta de ambiente mediado.
- `rpm_ostree.instalar` e `rpm_ostree.remover` exigem nome exato de pacote nesta release.
- `rpm_ostree.procurar` continua fora do corte executável e bloqueia com explicação honesta.
- `rpm_ostree.remover` exige confirmação explícita.
- mutações bem-sucedidas em `rpm-ostree` deixam visível que o efeito foi para o próximo deployment e pode exigir reboot.
- README, help e docs técnicas passam a refletir a `v0.6.0` como release pública atual.

### Continua fora da v0.6.0

- fallback automático do host para `flatpak`, `toolbox`, `distrobox` ou `rpm-ostree`;
- `rpm-ostree.procurar`;
- `apply-live`, `override remove`, reboot automático e chaining amplo de transações `rpm-ostree`;
- `ujust`;
- manutenção ampla do host imutável;
- suporte genérico a qualquer host imutável fora do corte explícito desta release;
- mistura de `rpm-ostree` com AUR, COPR, PPA, `flatpak` remotes, `toolbox` ou `distrobox` na mesma frase.

## 🌌 Aurora v0.5.1

Fechamento pequeno da frente `distrobox` para abrir uma segunda superfície mediada explícita, sem colapsar `toolbox` e `distrobox` numa pseudoentidade única e sem fingir que isso já resolve hosts imutáveis.

### Adicionado

- `execution_surface=distrobox` e `environment_target` explícito no contrato de request, policy, route e `decision_record`.
- `distrobox.procurar`, `distrobox.instalar` e `distrobox.remover` como rotas reais sobre pacote distro-managed dentro de uma distrobox explicitamente nomeada.
- observação explícita de `distrobox` no host, das distroboxes existentes e do backend observado dentro do ambiente selecionado.
- `distrobox_profile` em `aurora dev` para deixar visível a fronteira host vs distrobox.

### Alterado

- `distrobox` não entra como fonte; entra como superfície operacional mediada sobre `host_package`.
- `toolbox` e `distrobox` agora compartilham apenas o miolo de pacote distro-managed dentro do ambiente, mantendo observação, sinais e rotas separados por superfície.
- `distrobox.instalar` e `distrobox.remover` exigem nome exato de pacote nesta release; a descoberta de nome humano fica em `distrobox.procurar`.
- `distrobox.remover` exige confirmação explícita para manter visível a mutação dentro do ambiente mediado.
- README, help e docs técnicas passam a refletir a `v0.5.1` como release pública atual.

### Continua fora da v0.5.1

- fallback automático do host para `distrobox`;
- default implícito de distrobox, autoseleção por ambiguidade ou descoberta mágica de ambiente;
- criação automática de distrobox e administração ampla de lifecycle;
- mistura de `distrobox` com `toolbox`, AUR, COPR, PPA ou remotes `flatpak`;
- canonicalização ampla de alvo para `distrobox.instalar` e `distrobox.remover`;
- `rpm-ostree`, `ujust` e suporte operacional real a hosts imutáveis.

## 🌌 Aurora v0.5.0

Fechamento pequeno da frente `toolbox` para abrir um ambiente mediado explícito e distinto do host, sem fingir que isso já resolve suporte operacional real a hosts imutáveis.

### Adicionado

- `execution_surface=toolbox` e `environment_target` explícito no contrato de request, policy, route e `decision_record`.
- `toolbox.procurar`, `toolbox.instalar` e `toolbox.remover` como rotas reais sobre pacote distro-managed dentro de uma toolbox explicitamente nomeada.
- observação explícita de `toolbox` no host, das toolboxes existentes e do backend observado dentro do ambiente selecionado.
- `environment_resolution` e `toolbox_profile` em `aurora dev` para deixar visível a fronteira host vs toolbox.

### Alterado

- `toolbox` não entra como fonte; entra como superfície operacional mediada sobre `host_package`.
- `toolbox.instalar` e `toolbox.remover` exigem nome exato de pacote nesta release; a descoberta de nome humano fica em `toolbox.procurar`.
- `toolbox.remover` exige confirmação explícita para manter visível a mutação dentro do ambiente mediado.
- host Atomic/imutável continua bloqueado em `host_package`, mas um pedido explicitamente marcado para `toolbox` pode seguir quando `toolbox` e o ambiente nomeado foram observados.
- README, help e docs técnicas passam a refletir a `v0.5.0` como release pública atual.

### Continua fora da v0.5.0

- fallback automático do host para `toolbox`;
- default implícito de toolbox, autoseleção por ambiguidade ou descoberta mágica de ambiente;
- criação automática de toolbox e administração ampla de lifecycle;
- mistura de `toolbox` com AUR, COPR, PPA ou remotes `flatpak`;
- canonicalização ampla de alvo para `toolbox.instalar` e `toolbox.remover`;
- distrobox, `rpm-ostree`, `ujust` e suporte operacional real a hosts imutáveis.

## 🌌 Aurora v0.4.1

Fechamento pequeno da frente `flatpak` para abrir `remote` explícito além de `flathub`, sem transformar a Aurora em gerenciador amplo de remotes.

### Adicionado

- `flatpak` agora aceita `remote` explícito via coordenada simples já observável no host, como `no flatpak <remote>` ou `no flathub`.
- `flatpak.procurar`, `flatpak.instalar` e `flatpak.remover` carregam o `remote` para policy, route, execution e `decision_record`.
- observação explícita de `flatpak remotes` e uso controlado de `flatpak remote-ls` para respeitar o `remote` selecionado sem descoberta ampla.

### Alterado

- `flathub` continua sendo o default apenas para `flatpak.procurar` e `flatpak.instalar` quando nenhum `remote` é informado.
- `flatpak.remover` deixa explícito que `remote` só entra como restrição honesta de `origin`, sem assumir default para remoção.
- README, help e docs técnicas passam a refletir a `v0.4.1` como release pública atual.

### Continua fora da v0.4.1

- descoberta automática de remotes `flatpak`;
- add automático de remote arbitrário;
- administração geral de remotes `flatpak`;
- sincronização ampla de remotes;
- PPA, COPR e AUR fora do que já estava aberto;
- toolbox, distrobox, `rpm-ostree` e hosts imutáveis como superfície operacional.

## 🌌 Aurora v0.4.0

Fechamento pequeno da frente PPA para abrir uma nova família explícita de repositório terceiro sem transformar `apt` genérico em promessa ampla de Debian-like.

### Adicionado

- `requested_source=ppa` com coordenada canônica obrigatória `ppa:owner/name`.
- `source_type=ppa_repository` e `trust_level=third_party_repository` como leitura própria da nova frente.
- `ppa.instalar` como rota real com passos preparatórios explícitos: `add-apt-repository`, `apt-get update` e `apt-get install`.
- observabilidade dedicada para `PPA` em `decision_record` e `aurora dev`, incluindo capacidades observadas, distro compatível, coordenada e preparação planejada.

### Alterado

- a política passa a distinguir Ubuntu mutável suportado de Debian puro e outras derivadas Debian-like bloqueadas na frente PPA.
- `ppa.remover` deixa de ser ambíguo: continua bloqueado por honestidade porque a Aurora ainda não demonstra proveniência APT por PPA nem lifecycle amplo de repositório.
- README, help e docs técnicas passam a refletir a `v0.4.0` como release pública atual.

### Continua fora da v0.4.0

- descoberta automática de PPA;
- busca global em PPA;
- tratamento de apt repo genérico como se fosse PPA;
- `ppa.procurar`, `ppa.remover` real, `remove-apt-repository` e cleanup/lifecycle amplo;
- promessa ampla para Debian-like fora de Ubuntu mutável;
- AppImage e GitHub Releases;
- `rpm-ostree`, toolbox, distrobox e `ujust`;
- hosts imutáveis reais como superfície operacional.

## 🌌 Aurora v0.3.4

Fechamento pequeno da honestidade operacional de COPR em mutação, adicionando proveniência RPM na remoção e lifecycle limitado de repositório sem abrir descoberta automática, cleanup heurístico ou disable mágico.

### Adicionado

- verificação de proveniência RPM em `copr.remover`, comparando `from_repo` do pacote instalado com os `repoids` observados no repo file do COPR explícito.
- observação explícita do estado habilitado do repositório COPR informado para expor se ele já estava ativo ou se precisou de `enable`.

### Alterado

- `copr.instalar` agora trata `enable` de forma idempotente.
- `copr.remover` passa a bloquear cedo quando a origem RPM não fecha com o repositório explícito.

## 🌌 Aurora v0.3.3

Fechamento contido da frente COPR para abrir `copr.procurar` por repositório explícito, sem descoberta automática de fonte nem busca global no universo COPR.

### Adicionado

- `copr.procurar` como rota real de leitura dentro da família COPR já aberta.
- consulta restrita ao `owner/project` explicitamente pedido.

## 🌌 Aurora v0.3.2

Fechamento contido da frente AUR sobre a base já aberta da `v0.3.1`.

### Adicionado

- `yay` como segundo helper AUR deliberadamente suportado ao lado de `paru`.
- observabilidade dedicada para helpers AUR observados, suportados e selecionados.

## 🌌 Aurora v0.3.1

Fechamento público da release que abre COPR como fonte explícita de terceiro em Fedora mutável.

### Adicionado

- marcação pública inicial de COPR por frase explícita com coordenada `owner/project`.
- `copr.instalar` e `copr.remover` como segunda frente real de terceiro dentro de `host_package`.

## 🌌 Aurora v0.3.0

Fechamento público da release que abre AUR como fonte explícita de terceiro.

### Adicionado

- marcação pública inicial de AUR por frase explícita, como `aurora procurar <pacote> no aur`.
- `aur.procurar`, `aur.instalar` e `aur.remover` como primeira fonte terceira real da Aurora.

## 🌌 Aurora v0.2.0

Fechamento público da release que abre `user_software` como segundo domínio real da Aurora.

### Adicionado

- `domain_kind=user_software` como parte real do contrato público.
- `flatpak.procurar`, `flatpak.instalar` e `flatpak.remover` como primeira rota ativa de software do usuário.

## 🌌 Aurora v0.1.0

Primeiro release público da Aurora.

### Adicionado

- produto 100% Python, com launchers oficiais `aurora` e `auro`;
- bootstrap próprio da Aurora com `python -m aurora`, `--help` e `--version`;
- núcleo inicial de semântica, `host_profile`, `decision_record` e rotas reais de `host_package`.
