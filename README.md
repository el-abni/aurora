# 🌌 Aurora

Evolução da 💜 Aury, com foco em mediação honesta de `host_package` em Linux.

Na `v0.1.0`, o contrato público é pequeno e real:

- launchers oficiais: `aurora` e `auro`;
- domínio realmente suportado: `host_package`;
- ações reais: `procurar`, `instalar` e `remover`;
- observabilidade própria: `aurora dev <frase>`;
- bloqueio explícito para hosts Atomic/imutáveis.

## O que a v0.1.0 faz

A Aurora classifica o pedido, detecta o host Linux, aplica a política e executa a rota de pacote do host quando isso cabe no contrato atual.

Hoje, isso cobre:

- Arch e derivadas mutáveis;
- Debian/Ubuntu e derivadas mutáveis;
- Fedora mutável;
- OpenSUSE mutável, em escopo contido.

Quando a mutação é sensível, a política exige confirmação explícita com `--confirm` no fim do comando.

### Exemplos

```bash
aurora procurar firefox
aurora instalar firefox
aurora instalar firefox --confirm
aurora remover firefox
aurora remover sudo --confirm
aurora dev "instalar firefox"
```

## O que a v0.1.0 não promete

A Aurora `v0.1.0` não abre:

- `flatpak` como rota ativa;
- AUR, COPR, PPA, AppImage e GitHub Releases;
- `rpm-ostree`, toolbox, distrobox e `ujust`;
- arquivos, rede e manutenção ampla do host.

Ferramentas observadas no host não se tornam promessa de suporte automaticamente.

## Instalação

Instalação local padrão:

```bash
./install.sh
```

Isso instala:

- a base da Aurora em `~/.local/share/aurora`;
- os launchers `aurora` e `auro` em `~/.local/bin`.

### Remoção

```bash
./uninstall.sh
```

## Política e honestidade

A Aurora decide com contratos estruturados. Na `v0.1.0`, os campos abaixo já influenciam o runtime:

- `domain_kind`
- `source_type`
- `trust_level`
- `software_criticality`
- `trust_signals`
- `trust_gaps`
- `policy_outcome`
- `requires_confirmation`
- `reversal_level`

Na prática, isso significa:

- instalar não é automaticamente confiar em outras fontes;
- detectar uma ferramenta não é prometer uma rota;
- host imutável continua bloqueado por política;
- mutação sensível pode exigir confirmação.

## Documentação

- [Arquitetura](docs/ARCHITECTURE.md)
- [Compatibilidade Linux](docs/COMPATIBILITY_LINUX.md)
- [Política de Instalação](docs/INSTALLATION_POLICY.md)
- [Mapa de Herança da Aury](docs/AURY_HERITAGE_MAP.md)
