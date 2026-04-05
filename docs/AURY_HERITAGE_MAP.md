# Aury Heritage Map - Aurora v0.5.0

## Objetivo

Este mapa registra o que a Aurora herdou da Aury, o que foi refatorado e o que não migrou para o contrato público atual da `v0.5.0`.

## Mapa por área

| Área | Origem principal na Aury | Situação na Aurora | Observação |
| --- | --- | --- | --- |
| Normalização | `python/aury/normalize.py` | herdado com refatoração | vocativos, correções e texto limpo |
| Tokens sensíveis | `python/aury/sensitive_tokens.py` | herdado com refatoração | paths, files e hosts continuam protegidos sem confundir `owner/project` de COPR, `ppa:owner/name` nem `environment_target` de toolbox |
| Pipeline semântico mínimo | `python/aury/pipeline.py` | herdado com refatoração | split simples e preparação de frase |
| Classificação mínima de domínio | partes de `python/aury/analyzer.py` | reescrito no estilo Aurora | `host_package`, `user_software`, fontes explícitas AUR/COPR/PPA e `execution_surface=toolbox` sob contrato próprio |
| Host profile Linux | `python/aury/host.py` | herdado com refatoração | família, mutabilidade, tier, ferramentas observadas e observação contida de toolbox |
| Roteamento de `host_package` | `python/aury/host.py` | herdado com refatoração | busca, instalação, remoção e probes no host |
| Runtime de execução | partes de `python/aury/runtime.py` | reescrito no estilo Aurora | sem dependência mental de Fish e agora com fronteira host vs toolbox explícita |
| Observabilidade | `python/aury/diagnostics.py` | reencarnado | `aurora dev`, `decision_record`, `environment_resolution` e `toolbox_profile` próprios |
| Contratos internos | `python/aury/contracts.py` | reescritos | tipagem focada na Aurora |

## O que não migrou

Não entrou no contrato atual:

- adaptador Fish como centro do produto;
- domínio de arquivos;
- domínio de rede;
- manutenção ampla do host;
- linguagem pública da Aury por inércia;
- qualquer dependência de runtime no checkout da Aury.

## O que continua fora da v0.5.0

- fallback automático de pedido nu para AUR;
- helpers AUR além de `paru` e `yay`;
- passthrough interativo para `aur.remover`;
- descoberta automática de repositório COPR;
- descoberta automática de PPA, `ppa.procurar`, `ppa.remover` real e lifecycle amplo do repositório;
- descoberta automática, add arbitrário e administração ampla de remotes `flatpak`;
- default implícito de toolbox, criação automática de ambiente e administração ampla de lifecycle;
- mistura de toolbox com outras fontes;
- canonicalização ampla de alvo para `toolbox.instalar` e `toolbox.remover`;
- AppImage e GitHub Releases;
- distrobox, `rpm-ostree` e `ujust`;
- suporte operacional real a hosts imutáveis;
- qualquer expansão pública além de `host_package`, AUR explícito, COPR explícito, PPA explícito, `user_software` via `flatpak` e `toolbox` explícita.

## Regra de proveniência

A Aury continua sendo a origem do patrimônio funcional herdado.

A Aurora não é rename da Aury e não é clean room. Ela é uma reencarnação disciplinada desse patrimônio sob contrato próprio, agora com `host_package` e `user_software` como domínios públicos distintos, AUR/COPR/PPA explícitos como fontes separadas e `toolbox` como superfície mediada explícita e auditável.
