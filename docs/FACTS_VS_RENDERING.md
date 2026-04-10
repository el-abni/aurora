# Facts vs Rendering - Aurora v0.6.4

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

## O que renderização nunca decide

- policy;
- suporte;
- bloqueio;
- confirmação;
- resultado;
- rota;
- verdade observada pelo probe.

## Choque evitado

Sem essa fronteira, o `decision_record` voltaria a misturar contrato com voz e reabriria um erro já conhecido: usar wording para esconder ou deformar a leitura estrutural da decisão.

## Recorte desta linha

Na `v0.6.4`, o corte continua propositalmente pequeno:

- `facts` concentra o estado operacional;
- `presentation` concentra a voz;
- o payload legado continua espelhado no topo por compatibilidade;
- a revisão humana ainda lê a renderização no terminal real sem transformar voz em truth layer;
- a presença pública pode ganhar marcador discreto e voz mais composta sem contaminar o `decision_record` técnico;
- não há refactor ornamental amplo do renderer.
