# Decision Record Schema - Aurora v1.3.0

## Papel

Este documento registra o schema canônico e mínimo do `decision_record` nesta linha.

Ele não é manifesto, não é framework genérico e não substitui leitura do código. Ele existe para manter o contrato pequeno, versionado e auditável.

## Schema atual

- `schema.schema_id=aurora.decision_record.v1`
- `schema.schema_version=v1`
- `stable_ids.action_id`: ação mínima estável da rodada (`procurar`, `instalar`, `remover`, `atualizar`)
- `stable_ids.route_id`: rota canônica estável da rodada
- `stable_ids.event_id`: evento estável de decisão ou execução
- `facts`: estado operacional canônico
- `presentation`: resumo e voz pública

## O que é canônico

Em `facts` ficam os dados que descrevem estado operacional:

- `request`
- `policy`
- `environment_resolution`
- `target_resolution`
- `execution_route`
- `execution`
- `local_model`
- `host_profile`, `toolbox_profile`, `distrobox_profile`, `rpm_ostree_status`
- `outcome`

Esses campos são o chão parseável da linha.

## O que é apresentação

Em `presentation` ficam apenas elementos de voz:

- `summary`
- `execution.summary`
- `execution.pre_probe_summary`
- `execution.post_probe_summary`

Renderização pode formatar, polir texto e escolher labels de leitura. Ela não escolhe policy, suporte, bloqueio, confirmação ou resultado.

## IDs mínimos estáveis

Os IDs mínimos desta linha são:

- `action_id`
- `route_id`
- `event_id`

Eles reaproveitam uma lição já aprendida pela Aurora: nome pequeno e explícito endurece melhor a linha do que taxonomia ampla demais.

Detalhe importante desta release:

- `host_package.search` continua apenas como `route_name` legado para compatibilidade;
- o ID canônico da rota de busca do host passa a ser `host_package.procurar`.
- `host_maintenance.atualizar` entra como ID canônico da atualização explícita e contida do sistema.

## Compatibilidade desta linha

- o payload antigo continua espelhado no topo por compatibilidade;
- o contrato novo a ser consumido daqui em diante é `schema + stable_ids + facts + presentation`.
- a `v1.3.0` não entrega schema novo nem motor novo; ela adiciona `source_clarification` determinística fora do `decision_record`, preserva a orientação da `v1.2.0`, herda da `v1.0.0` a seam limitada em `facts.local_model` com provider real canônico e preserva `host_maintenance.atualizar` sem relaxar o contrato central.

## Seam local do modelo

Quando `facts.local_model` estiver presente, a leitura correta e minima e:

- `mode`: `model_off` ou `model_on`;
- `status`: `disabled`, `completed` ou `fallback_deterministic`;
- `requested_capability`: `clarify`, `summarize`, `explain` ou `disambiguate_limited`;
- invariantes contratuais: `authority_profile=aurora.local_model.limited_assist.v1`, `advisory_only=true`, `input_schema_id=aurora.local_model.input.v1`;
- guardrails contratuais adicionais: `allowed_capabilities`, `forbidden_authorities` e `consumed_sections`;
- campos por estado: `provider_name`, `fallback_reason` e `output_text`.

Leitura factual desses campos por estado:

- `provider_name` fica vazio em `model_off` e registra o provider efetivamente usado quando a seam entra;
- `fallback_reason` só e significativo em `fallback_deterministic` e usa um dialeto canonico curto: `provider_not_configured`, `provider_connection_error`, `provider_timeout`, `provider_invalid_response`, `provider_unavailable`, `provider_returned_empty_output`;
- `output_text` so e significativo em `completed` e preserva o texto cru devolvido pelo provider, sem polimento;
- o bloco tecnico `Local model seam` do `aurora dev` projeta esses fatos de forma minima por estado, sem reescrever esses valores.

Entrada atual do provider real:

- o provider publico suportado hoje e `ollama`;
- ele so e resolvido quando `mode=model_on` e `AURORA_LOCAL_MODEL_PROVIDER=ollama`;
- o modelo canonico inicial e `qwen2.5:3b-instruct` quando `AURORA_LOCAL_MODEL_MODEL` nao e informado.

Limites do bloco:

- pode resumir, explicar, clarificar e desambiguar entre candidatos ja estruturados;
- nao pode decidir policy, suporte, bloqueio, confirmacao, rota, execucao ou verdade operacional;
- se o provider faltar, falhar ou sair do contrato, a linha cai para fallback deterministico e o kernel permanece suficiente sozinho.

## Ponto de partida factual da fase seguinte

O schema atual já separa `facts` e `presentation`, e os cortes 2 e 3 fecharam a maior parte da dívida factual imediata:

- `decision_record_schema.py` deixou de depender primariamente de parsing reverso de `trust_signals` para contexto de `COPR`, `PPA`, `flatpak`, `toolbox`, `distrobox`, host imutável e `rpm-ostree`;
- esses fatos agora nascem no produtor de policy como estruturas explícitas pequenas e continuam espelhados em campos legados por compatibilidade da linha;
- `trust_signals` permanece como trilha evidencial e explicativa, não mais como canal semântico central do serializer nem do render canônico;
- `decision_record` e `aurora dev` agora preferem os fatos promovidos, mantendo bridges legadas explícitas só onde a linha ainda precisa sobreviver;
- o estado real do corte 3 fica congelado em `tests/audit_factual_hotspots.py` com `tests/fixtures/factual_hotspots_v0_7_0_cut3.json`, em `tests/audit_factual_baseline.py` com `tests/fixtures/factual_baseline_v0_7_0_cut3.json` e em `tests/audit_observability_canonical_facts.py`.
- o baseline factual herdado do corte 4 continua cercando `facts.local_model` em `tests/audit_local_model_eval_baseline.py` com `tests/fixtures/local_model_eval_baseline_v0_7_0_cut4.json`.

## Fica para depois

- novas versões de schema quando houver mudança semântica real;
- expansão de IDs além do mínimo necessário;
- qualquer crescimento de contrato que exija feature nova de domínio.
