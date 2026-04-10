# Facts vs Rendering - Aurora v0.6.3

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

Na `v0.6.3`, o corte é propositalmente pequeno:

- `facts` concentra o estado operacional;
- `presentation` concentra a voz;
- o payload legado continua espelhado no topo por compatibilidade;
- não há refactor ornamental amplo do renderer.
