# Aurora v0.1.0

Aurora e um produto **100% Python** para mediacao honesta de `host_package` em Linux.

Na `v0.1`, o contrato publico e pequeno e real:

- launchers oficiais: `aurora` e `auro`;
- dominio suportado de verdade: `host_package`;
- acoes reais: `procurar`, `instalar` e `remover`;
- observabilidade propria: `aurora dev <frase>`;
- bloqueio explicito para hosts Atomic/imutaveis.

## O que a v0.1 faz

Aurora classifica o pedido, detecta o host Linux, aplica politica e executa a rota do pacote do host quando isso cabe no contrato atual.

Hoje isso cobre:

- Arch e derivadas mutaveis;
- Debian/Ubuntu e derivadas mutaveis;
- Fedora mutavel;
- OpenSUSE mutavel em escopo contido.

Quando a mutacao e sensivel, a politica exige confirmacao explicita com `--confirm` no fim do comando.

Exemplos:

```bash
aurora procurar firefox
aurora instalar firefox
aurora instalar firefox --confirm
aurora remover firefox
aurora remover sudo --confirm
aurora dev "instalar firefox"
```

## O que a v0.1 nao promete

Aurora `v0.1` nao abre:

- `flatpak` como rota ativa;
- AUR, COPR, PPA, AppImage, GitHub Releases;
- `rpm-ostree`, toolbox, distrobox, `ujust`;
- arquivos, rede e manutencao ampla do host.

Ferramentas observadas no host nao viram promessa de suporte automaticamente.

## Instalacao

Instalacao local padrao:

```bash
./install.sh
```

Isso instala:

- base da Aurora em `~/.local/share/aurora`;
- launchers `aurora` e `auro` em `~/.local/bin`.

Remocao:

```bash
./uninstall.sh
```

## Politica e honestidade

Aurora decide com contratos estruturados. Na `v0.1`, os campos relevantes ja influenciam o runtime:

- `domain_kind`
- `source_type`
- `trust_level`
- `software_criticality`
- `trust_signals`
- `trust_gaps`
- `policy_outcome`
- `requires_confirmation`
- `reversal_level`

Isso significa, na pratica:

- instalar nao e automaticamente confiar em outras fontes;
- detectar ferramenta nao e prometer rota;
- host imutavel continua bloqueado por politica;
- mutacao sensivel pode exigir confirmacao.

## Documentacao

- [Arquitetura](docs/ARCHITECTURE.md)
- [Compatibilidade Linux](docs/COMPATIBILITY_LINUX.md)
- [Politica de Instalacao](docs/INSTALLATION_POLICY.md)
- [Mapa de Heranca da Aury](docs/AURY_HERITAGE_MAP.md)
