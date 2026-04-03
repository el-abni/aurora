# Aury Heritage Map - Aurora v0.3.1

## Objetivo

Este mapa registra o que a Aurora herdou da Aury, o que foi refatorado e o que não migrou para o contrato público atual da `v0.3.1`.

## Mapa por área

| Área | Origem principal na Aury | Situação na Aurora | Observação |
| --- | --- | --- | --- |
| Normalização | `python/aury/normalize.py` | herdado com refatoração | vocativos, correções e texto limpo |
| Tokens sensíveis | `python/aury/sensitive_tokens.py` | herdado com refatoração | paths, files e hosts continuam protegidos sem confundir `owner/project` de COPR com caminho |
| Pipeline semântico mínimo | `python/aury/pipeline.py` | herdado com refatoração | split simples e preparação de frase |
| Classificação mínima de domínio | partes de `python/aury/analyzer.py` | reescrito no estilo Aurora | `host_package`, `user_software` e fontes explícitas AUR/COPR sob contrato próprio |
| Host profile Linux | `python/aury/host.py` | herdado com refatoração | família, mutabilidade, tier e ferramentas observadas |
| Roteamento de `host_package` | `python/aury/host.py` | herdado com refatoração | busca, instalação, remoção e probes |
| Runtime de execução | partes de `python/aury/runtime.py` | reescrito no estilo Aurora | sem dependência mental de Fish |
| Observabilidade | `python/aury/diagnostics.py` | reencarnado | `aurora dev` e `decision_record` próprios |
| Contratos internos | `python/aury/contracts.py` | reescritos | tipagem focada na Aurora |

## O que não migrou

Não entrou no contrato atual:

- adaptador Fish como centro do produto;
- domínio de arquivos;
- domínio de rede;
- manutenção ampla do host;
- linguagem pública da Aury por inércia;
- qualquer dependência de runtime no checkout da Aury.

## O que continua fora da v0.3.1

- fallback automático de pedido nu para AUR;
- helpers AUR além de `paru`;
- `copr.procurar`, descoberta automática de repositório COPR e lifecycle amplo do repositório;
- PPA, AppImage e GitHub Releases;
- `rpm-ostree`, toolbox, distrobox e `ujust`;
- suporte operacional real a hosts imutáveis;
- qualquer expansão pública além de `host_package`, AUR explícito, COPR explícito e `user_software` via `flatpak`.

## Regra de proveniência

A Aury continua sendo a origem do patrimônio funcional herdado.

A Aurora não é rename da Aury e não é clean room. Ela é uma reencarnação disciplinada desse patrimônio sob contrato próprio, agora com `host_package` e `user_software` como domínios públicos distintos e AUR/COPR explícitos como fontes separadas dentro do escopo do host.
