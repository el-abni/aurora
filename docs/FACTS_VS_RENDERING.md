# Facts vs Rendering - Aurora v1.3.0

## Papel

Este documento fixa a fronteira entre fato operacional e renderização pública.

Ele reaproveita uma lição já visível no repositório: `messages.py` e `text_polish.py` são boa camada de voz, mas voz não pode virar fonte de verdade operacional.

## Fato operacional decide

- classificação do pedido;
- policy e suporte;
- bloqueio, confirmação ou liberação;
- resolução de ambiente e alvo;
- rota selecionada;
- status final de execução;
- `fallback_reason` e `output_text` da seam `local_model`, quando existirem;
- `action_id`, `route_id` e `event_id`.

Essas decisões vivem em `facts`.

## Renderização decide

- acabamento textual;
- títulos, labels e ordem de leitura;
- polimento de texto público;
- modulação curta de presença e tom;
- marcador discreto de fala na primeira linha da mensagem pública principal;
- resumo público derivado do estado já decidido.

Esses detalhes vivem em `presentation` ou na camada `presentation/`.

Quando existir `facts.local_model`, ele continua sendo camada assistiva e auditavel acima do kernel: pode consumir o payload canonico para sugerir clarificacao, resumo, explicacao ou desambiguacao limitada, mas nao vira fonte de verdade operacional. `fallback_reason` e `output_text` permanecem fatos crus dessa seam, nao wording publico.

## O que renderização nunca decide

- policy;
- suporte;
- bloqueio;
- confirmação;
- resultado;
- rota;
- execução;
- verdade observada pelo probe;
- `fallback_reason` e `output_text` da seam em nome de polimento, “voz” ou conveniência de renderização.

## Choque evitado

Sem essa fronteira, o `decision_record` voltaria a misturar contrato com voz e reabriria um erro já conhecido: usar wording para esconder ou deformar a leitura estrutural da decisão.

## Recorte desta linha

Na `v1.3.0`, o corte continua propositalmente pequeno:

- `facts` concentra o estado operacional;
- `presentation` concentra a voz;
- o payload legado continua espelhado no topo por compatibilidade;
- conversação/mediação de ajuda vive em `presentation/orientation.py`, antes do executor, e não vira fato operacional;
- clarificação controlada de fonte/superfície vive em `presentation/source_clarification.py`, antes do executor, e não vira fato operacional, `source_discovery` nem contrato de recomendação;
- `host_maintenance.atualizar` aparece como fato de request, policy, route e execution, não como frase solta de ajuda;
- a revisão humana ainda lê a renderização no terminal real sem transformar voz em truth layer;
- a presença pública pode ganhar marcador discreto e voz mais composta sem contaminar o `decision_record` técnico;
- o help público continua na camada de renderização e volta a ser curto, enquanto compatibilidade, política e workflow detalhados ficam no README/docs;
- o bloco `Local model seam` do `aurora dev` mostra apenas `mode`, `status` e `requested_capability`, somando `provider_name` + `fallback_reason` em fallback ou `provider_name` + `output_text` em `completed`;
- `output_text` continua cru e não passa por `polish_public_text(...)`;
- não há refactor ornamental amplo do renderer.

## Hotspots explícitos do ponto de partida factual

O estado atual já evita que voz vire verdade e os cortes 2 e 3 fecharam a costura factual principal:

- o corte 2 fez `decision_record_schema.py` passar a consumir fatos explícitos promovidos no produtor de policy, em vez de reconstituir a verdade principal via `trust_signals`;
- o corte 3 fez `render.py` passar a consumir o payload factual canônico e manter `trust_signals` apenas como trilha evidencial exibida;
- o corte 4 passou a cercar o seam do modelo local em `facts.local_model`, com `model_off` por default e `model_on` restrito a ajuda assistiva sobre o payload canonico;
- a observabilidade canônica agora prefere fatos estruturados e deixa explícitas apenas as bridges legadas ainda necessárias.

Por isso, a linha passou a congelar duas coisas pequenas e explícitas:

- `tests/audit_factual_hotspots.py` com `tests/fixtures/factual_hotspots_v0_7_0_cut3.json` para mapear que serializer e renderer saíram do reparse factual principal;
- `tests/audit_factual_baseline.py` com `tests/fixtures/factual_baseline_v0_7_0_cut3.json` para congelar um baseline curto de `decision_record` e `aurora dev` já sobre a observabilidade limpa;
- `tests/audit_observability_canonical_facts.py` para provar que `render` e `decision_record` continuam expondo fatos promovidos mesmo com `trust_signals` esvaziado.
- `tests/audit_local_model_eval_baseline.py` para congelar um corpus curto de comparacao `model_off` vs `model_on`, sem deixar o modelo invadir policy, route, execution ou resultado.
