# Decision Record Schema - Aurora v0.6.4

## Papel

Este documento registra o schema canônico e mínimo do `decision_record` nesta linha.

Ele não é manifesto, não é framework genérico e não substitui leitura do código. Ele existe para manter o contrato pequeno, versionado e auditável.

## Schema atual

- `schema.schema_id=aurora.decision_record.v1`
- `schema.schema_version=v1`
- `stable_ids.action_id`: ação mínima estável da rodada (`procurar`, `instalar`, `remover`)
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

## Compatibilidade desta linha

- o payload antigo continua espelhado no topo por compatibilidade;
- o contrato novo a ser consumido daqui em diante é `schema + stable_ids + facts + presentation`.
- a `v0.6.4` não muda esse schema; ela endurece o workflow que protege esse contrato.

## Fica para depois

- novas versões de schema quando houver mudança semântica real;
- expansão de IDs além do mínimo necessário;
- qualquer crescimento de contrato que exija feature nova de domínio.
