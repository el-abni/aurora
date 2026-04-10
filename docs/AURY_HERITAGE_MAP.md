# Aury Heritage Map - Aurora v0.6.4

## Objetivo

Este mapa registra o que a Aurora herdou da Aury, o que foi refatorado e o que não migrou para o contrato público atual da `v0.6.4`.

Leitura canônica de fronteira: `docs/AURY_TO_AURORA_DOSSIER.md`.

## Mapa por área

| Área | Origem principal na Aury | Situação na Aurora | Observação |
| --- | --- | --- | --- |
| Normalização | `python/aury/normalize.py` | herdado com refatoração | vocativos, correções e texto limpo |
| Tokens sensíveis | `python/aury/sensitive_tokens.py` | herdado com refatoração | paths, files e hosts continuam protegidos sem confundir `owner/project` de COPR, `ppa:owner/name` nem `environment_target` de toolbox ou distrobox |
| Pipeline semântico mínimo | `python/aury/pipeline.py` | herdado com refatoração | split simples e preparação de frase |
| Classificação mínima de domínio | partes de `python/aury/analyzer.py` | reescrito no estilo Aurora | `host_package`, `user_software`, fontes explícitas AUR/COPR/PPA e `execution_surface=toolbox`/`execution_surface=distrobox`/`execution_surface=rpm_ostree` sob contrato próprio |
| Host profile Linux | `python/aury/host.py` | herdado com refatoração | família, mutabilidade, tier, ferramentas observadas e observação contida de toolbox, distrobox e superfícies úteis em host imutável |
| Roteamento de `host_package` | `python/aury/host.py` | herdado com refatoração | busca, instalação, remoção e probes no host |
| Runtime de execução | partes de `python/aury/runtime.py` | reescrito no estilo Aurora | sem dependência mental de Fish e agora com fronteira explícita entre host mutável, host imutável via `rpm-ostree` e ambientes mediatos |
| Observabilidade | `python/aury/diagnostics.py` | reencarnado | `aurora dev`, `decision_record`, `environment_resolution`, `toolbox_profile`, `distrobox_profile` e `rpm_ostree_status` próprios |
| Contratos internos | `python/aury/contracts.py` | reescritos | tipagem focada na Aurora |

## O que não migrou

Não entrou no contrato atual:

- adaptador Fish como centro do produto;
- domínio de arquivos;
- domínio de rede;
- manutenção ampla do host;
- linguagem pública da Aury por inércia;
- qualquer dependência de runtime no checkout da Aury.

## O que continua fora da v0.6.4

- fallback automático de pedido nu para AUR;
- helpers AUR além de `paru` e `yay`;
- passthrough interativo para `aur.remover`;
- descoberta automática de repositório COPR;
- descoberta automática de PPA, `ppa.procurar`, `ppa.remover` real e lifecycle amplo do repositório;
- descoberta automática, add arbitrário e administração ampla de remotes `flatpak`;
- default implícito de toolbox, default implícito de distrobox, criação automática de ambiente e administração ampla de lifecycle;
- mistura de toolbox ou distrobox com outras fontes;
- mistura de `rpm-ostree` com outras fontes ou superfícies;
- canonicalização ampla de alvo para `toolbox.instalar` e `toolbox.remover`;
- canonicalização ampla de alvo para `distrobox.instalar` e `distrobox.remover`;
- `rpm_ostree.procurar`, `apply-live`, `override remove`, reboot automático e chaining amplo de transações;
- AppImage e GitHub Releases;
- `ujust`;
- suporte genérico a hosts imutáveis além do corte explícito `flatpak`/`toolbox`/`distrobox`/`rpm-ostree`;
- qualquer expansão pública além de `host_package`, AUR explícito, COPR explícito, PPA explícito, `user_software` via `flatpak`, `toolbox` explícita, `distrobox` explícita e `rpm-ostree` explícito.

## Regra de proveniência

A Aury continua sendo a origem do patrimônio funcional herdado.

A Aurora não é rename da Aury e não é clean room. Ela é uma reencarnação disciplinada desse patrimônio sob contrato próprio, agora com `host_package` e `user_software` como domínios públicos distintos, AUR/COPR/PPA explícitos como fontes separadas e `toolbox`/`distrobox`/`rpm-ostree` como superfícies explícitas e auditáveis.
