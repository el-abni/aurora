# tests/

Esta pasta guarda o chão mínimo de regressão auditável que sustenta a espinha canônica da linha da Aurora.

Ela existe para:

- proteger o contrato público já aberto;
- manter alinhados código, docs públicas e gate;
- endurecer a linha sem inflar infraestrutura.

Ela não existe para:

- virar framework de testes;
- prometer cobertura total do projeto;
- justificar abertura de feature nova;
- substituir leitura humana quando a fronteira ainda é conceitual.

## Três camadas da v1.2.0

A `v1.2.0` preserva três camadas distintas:

- teste automático para regressão executável;
- revisão manual para diffs, docs, help, versão e coerência pública;
- teste real no terminal local para o que o harness não enxerga.

Leitura correta:

- gate automatizado não substitui checklist humano;
- checklist humano não substitui terminal real;
- terminal real não substitui a base automática da linha.

## Gate canônico da linha

O gate canônico da linha é:

```bash
bash tests/release_gate_canonic_line.sh
```

Ele reúne:

- a suíte `unittest` pública rastreada pelo Git;
- `tests/audit_public_release.py`;
- `tests/audit_canonic_line.py`;
- `tests/audit_decision_record_contract.py`.
- `tests/audit_factual_hotspots.py`;
- `tests/audit_factual_baseline.py`;
- `tests/audit_observability_canonical_facts.py`;
- `tests/audit_local_model_eval_baseline.py`;
- `tests/audit_workflow_release.py`.

Esse gate é a régua corrente da linha porque protege:

- o chão público já aberto;
- a espinha canônica da v0.6.3;
- o schema curto do `decision_record`;
- a distinção entre canonização de linha e abertura de feature;
- a disciplina operacional preservada na `v1.2.0`.
- a orientação determinística da `v1.2.0` sem execução acidental.

## Gates operacionais por etapa

### Gate de iteração / coding

```bash
bash tests/release_gate_iteracao.sh
```

Uso correto:

- feedback rápido durante coding comum;
- mínimo de smoke público, instalador e contrato;
- não substitui os testes específicos da área tocada.

### Gate pré-push

```bash
bash tests/release_gate_pre_push.sh
```

Uso correto:

- bloquear push com diff ruim;
- reaproveitar o gate canônico atual;
- impedir subida sem coerência pública mínima.

### Gate pré-release / tag

```bash
bash tests/release_gate_pre_release.sh
```

Uso correto:

- candidato automatizado mais duro antes de tag e release;
- reaproveitar o gate pré-push;
- exercitar também o gate histórico `v0.6.2` como patrimônio de fechamento;
- deixar explícito que checklist humano e terminal real continuam obrigatórios.

## Gate histórico de release

O gate histórico da release pública `v0.6.2` continua existindo em:

```bash
bash tests/release_gate_v0_6_2.sh
```

Ele permanece como patrimônio de fechamento da `v0.6.2`. A régua corrente da linha, porém, passa a ser `tests/release_gate_canonic_line.sh`.

## Checklist humano

O checklist operacional curto desta release fica em:

```bash
tests/REVIEW_CHECKLIST.md
```

Ele cobre:

- versão, help, README e changelog;
- `aurora --version`, `aurora --help` e `aurora dev`, quando aplicável;
- revisão de diffs sensíveis;
- bloqueios de push, tag e release;
- validação no terminal real.

Quando a rodada tocar `host_maintenance.atualizar`, a leitura mínima obrigatória inclui:

- `aurora dev "atualizar sistema"`;
- `aurora atualizar sistema`;
- `aurora atualizar sistema --confirm`;
- conferência explícita de que a rota continua em `sudo + pacman`, sem `paru` e sem AUR implícita.

## Guardrail local de integridade canônica

Quando a rodada toca contexto privado, pointers canônicos, classificação viva/histórica ou coerência curta entre `VERSION` e docs centrais, rodar localmente:

```bash
python3 tests/audit_canonic_integrity.py
```

Leitura correta:

- este guardrail detecta quebra objetiva de pointer, marker histórico/transicional ausente e mismatch simples de `VERSION`;
- ele **não** decide roadmap, promoção de versão, prioridade de backlog nem classificação humana final;
- ele existe para endurecer canon vivo local, não para virar nova régua pública automática da linha.

## Leitura correta desta pasta

- `test_*.py` protege o contrato executável já aberto;
- `audit_public_release.py` protege a coerência pública da release atual;
- `audit_canonic_line.py` protege a espinha canônica da linha;
- `audit_canonic_integrity.py` protege pointers e coerência mínima do canon vivo local quando a rodada toca PV/contexto;
- `audit_decision_record_contract.py` protege `schema`, `stable_ids`, `facts` e `presentation`;
- `audit_factual_hotspots.py` congela que serializer e renderer saíram do reparse factual principal no corte 3;
- `audit_factual_baseline.py` congela um baseline factual curto de `aurora dev` e `decision_record`;
- `audit_observability_canonical_facts.py` prova que `render` e `decision_record` continuam expondo fatos promovidos mesmo com `trust_signals` esvaziado;
- `audit_local_model_eval_baseline.py` congela um corpus curto para comparar `model_off` e `model_on` sem deixar o modelo tocar policy, route, execution ou verdade operacional;
- `audit_workflow_release.py` protege o workflow disciplinado da `v1.2.0`;
- `test_conversation_mediation.py` protege tópicos e perguntas fechadas da `v1.2.0`;
- esta base protege auditabilidade e estabilidade de linha, não expansão de produto.

## Limites deliberados

- nada aqui puxa Fish para o centro da Aurora;
- nada aqui depende de stage pública;
- nada aqui abre frente nova de domínio;
- nada aqui tenta transformar checklist humano em framework;
- nada aqui finge que terminal real pode ser totalmente substituído por harness;
- se esta pasta crescer rápido demais, ela provavelmente está tentando resolver arquitetura com volume de teste.
