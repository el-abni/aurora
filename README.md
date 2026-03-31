# 🌌 Aurora

![versão](https://img.shields.io/badge/vers%C3%A3o-v0.1.0-6a5acd)
![linguagem](https://img.shields.io/badge/linguagem-Python-3776AB)
![plataforma](https://img.shields.io/badge/plataforma-Linux-orange)
![licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green)

**Aurora** é uma assistente de terminal para **Linux**, focada em mediação honesta de `host_package` com política explícita, observabilidade própria e execução real no recorte público da `v0.1.0`.

Ela nasce como um produto **100% Python**, com launchers oficiais `aurora` e `auro`, e abre sua primeira release pública com um contrato pequeno, real e auditável.

---

> Estado público real da **v0.1.0**: a Aurora abre com suporte operacional explícito para `host_package` em Arch/derivadas mutáveis, Debian/Ubuntu/derivadas mutáveis, Fedora mutável e OpenSUSE mutável em escopo contido. `procurar`, `instalar` e `remover` significam **pacote do host**, não software do usuário, múltiplas rotas, app store, política ampla de origem nem instalação cross-source. Hosts Atomic/imutáveis permanecem **bloqueados por política**. `flatpak` e `rpm-ostree` podem ser observados no ambiente, mas ficam fora do contrato ativo desta release.

## O que é a Aurora

A Aurora funciona como uma camada de decisão e execução sobre o domínio de `host_package`.

Em vez de tratar o terminal como uma coleção de comandos isolados, ela:

- classifica o pedido;
- detecta o host Linux;
- aplica política;
- escolhe a rota cabível no contrato atual;
- e expõe um `decision record` auditável com `aurora dev <frase>`.

A ideia não é fingir suporte onde ele não existe, e sim abrir a Aurora com uma base pequena, forte e honesta.

---

## Exemplos rápidos

### Pacotes do host

```bash
aurora procurar firefox
aurora instalar firefox
aurora instalar firefox --confirm
aurora remover firefox
aurora remover sudo --confirm
```

### Observabilidade

```bash
aurora dev "procurar firefox"
aurora dev "instalar obs-studio"
aurora dev "remover obs-studio"
```

---

## Funcionalidades da v0.1.0

A versão atual da **🌌 Aurora** já oferece:

- produto 100% Python;
- launchers oficiais `aurora` e `auro`;
- interpretação inicial de frases para `procurar`, `instalar` e `remover`;
- normalização conservadora e proteção de tokens sensíveis;
- `host_profile` estruturado para Linux;
- suporte real de `host_package.procurar`, `host_package.instalar` e `host_package.remover`;
- política operacional com `domain_kind`, `source_type`, `trust_level`, `software_criticality`, `trust_signals`, `trust_gaps`, `policy_outcome`, `requires_confirmation` e `reversal_level`;
- `decision_record` próprio com `aurora dev <frase>`;
- noop honesto, bloqueio explícito por política e confirmação real com `--confirm` quando necessário.

---

## Compatibilidade Linux da v0.1.0

A matriz pública atual fica assim:

- **suportado agora**: Arch/derivadas mutáveis, Debian/Ubuntu/derivadas mutáveis e Fedora mutável;
- **suportado contido**: OpenSUSE mutável;
- **bloqueado por política**: hosts Atomic/imutáveis.

Ferramentas observadas no host **não** viram promessa de suporte automaticamente.

---

## Instalação

Instalação pública padrão:

```bash
git clone https://github.com/el-abni/aurora.git
cd aurora
./install.sh
```

O script instala a superfície pública em:

- `~/.local/share/aurora`
- `~/.local/bin/aurora`
- `~/.local/bin/auro`

Depois da instalação, valide com:

```bash
aurora --version
aurora --help
```

Remoção:

```bash
./uninstall.sh
```

---

## Como usar

Para ver o help público:

```bash
aurora --help
auro --help
```

A identidade pública da assistente é:

```text
🌌 Aurora
```

No help, a versão aparece como:

```text
🌌 Aurora v0.1.0
```

---

## Contrato público mínimo da v0.1.0

- `aurora --help` e `auro --help` renderizam o help público da base ativa.
- `aurora --version` e `auro --version` imprimem `Aurora v0.1.0`.
- `aurora dev <frase>` expõe um `decision record` próprio com request, host profile, policy, rota e resultado planejado/executado.
- na `v0.1.0`, `procurar`, `instalar` e `remover` significam explicitamente **pacote do host**.
- na `v0.1.0`, esse trio não significa software do usuário, app store, múltiplas origens nem política ampla de instalação cross-source.
- na `v0.1.0`, hosts Atomic/imutáveis continuam bloqueados por política de forma explícita.
- na `v0.1.0`, `flatpak` e `rpm-ostree` podem aparecer apenas como ferramentas observadas, fora do contrato ativo.
- na `v0.1.0`, `--confirm` faz parte real da UX para mutações sensíveis.

## O que a v0.1.0 não promete

A Aurora `v0.1.0` não abre:

- `flatpak` como rota ativa;
- AUR, COPR, PPA, AppImage e GitHub Releases;
- `rpm-ostree`, toolbox, distrobox e `ujust`;
- arquivos, rede e manutenção ampla do host;
- software do usuário como domínio público desta primeira release.

---

## Filosofia do projeto

A Aurora não tenta simular amplitude vazia.

Ela existe para:

- abrir uma base Python própria e auditável;
- tratar Linux com honestidade;
- expor política em vez de esconder decisão;
- mediar mutações do host com mais clareza;
- crescer por contrato, não por improviso.

---

## Documentação

A documentação complementar da release fica em:

- [Arquitetura](docs/ARCHITECTURE.md)
- [Compatibilidade Linux](docs/COMPATIBILITY_LINUX.md)
- [Política de Instalação](docs/INSTALLATION_POLICY.md)
- [Mapa de Herança da Aury](docs/AURY_HERITAGE_MAP.md)

---

## Licença

Este projeto é distribuído sob a licença **MIT**.
