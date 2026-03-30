# Aury Heritage Map - Aurora v0.1.0

## Objetivo

Este mapa registra o que a Aurora herdou da Aury, o que foi refatorado e o que nao migrou para a `v0.1`.

## Mapa por area

| Area | Origem principal na Aury | Situacao na Aurora v0.1 | Observacao |
| --- | --- | --- | --- |
| Normalizacao | `python/aury/normalize.py` | herdado com refatoracao | vocativos, correcoes e texto limpo |
| Tokens sensiveis | `python/aury/sensitive_tokens.py` | herdado com refatoracao | paths, files e hosts continuam protegidos |
| Pipeline semantico minimo | `python/aury/pipeline.py` | herdado com refatoracao | split simples e preparacao de frase |
| Classificacao minima de pacote | partes de `python/aury/analyzer.py` | reescrito no estilo Aurora | recorte estreito para `host_package` |
| Host profile Linux | `python/aury/host.py` | herdado com refatoracao | familia, mutabilidade, tier e ferramentas observadas |
| Roteamento de host package | `python/aury/host.py` | herdado com refatoracao | busca, instalacao, remocao e probes |
| Runtime de execucao | partes de `python/aury/runtime.py` | reescrito no estilo Aurora | sem dependencia mental de Fish |
| Observabilidade | `python/aury/diagnostics.py` | reencarnado | `aurora dev` e `decision_record` proprios |
| Contratos internos | `python/aury/contracts.py` | reescritos | tipagem focada na Aurora |

## O que nao migrou

Nao entrou na `v0.1`:

- adaptador Fish como centro do produto;
- dominio de arquivos;
- dominio de rede;
- manutencao ampla do host;
- linguagem publica da Aury por inercia;
- qualquer dependencia de runtime no checkout da Aury.

## O que ficou explicitamente fora da v0.1

- `flatpak` como rota ativa;
- AUR, COPR, PPA, AppImage, GitHub Releases;
- `rpm-ostree`, toolbox, distrobox, `ujust`.

## Regra de proveniencia

A Aury continua sendo a origem do patrimonio funcional herdado.
A Aurora `v0.1` nao e um rename da Aury e nao e clean room.
Ela e uma reencarnacao disciplinada desse patrimonio sob contrato proprio.
