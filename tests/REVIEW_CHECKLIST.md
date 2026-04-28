# Review Checklist - Aurora v1.2.0

Use este checklist antes de `push`, `tag` ou `release`. Se um item não se aplica, a dispensa precisa ser consciente.

## Superfície pública

- [ ] `VERSION`, `README.md`, `CHANGELOG.md` e `resources/help.txt` estão coerentes entre si.
- [ ] `docs/ARCHITECTURE.md`, `docs/DECISION_RECORD_SCHEMA.md`, `docs/FACTS_VS_RENDERING.md`, `docs/WORKFLOW_DE_TESTES_E_RELEASE.md` e `tests/README.md` batem com a release atual.
- [ ] `aurora --version` mostra a versão pública certa.
- [ ] `aurora --help` reflete a superfície pública real.
- [ ] `aurora versão`, `auro versão`, tópicos de orientação e perguntas fechadas foram testados sem execução.
- [ ] Se contrato, payload ou renderização mudaram, `aurora dev "<caso feliz>"` e `aurora dev "<caso ruim>"` foram lidos.

## Seam `local_model` herdada da v1.0.0

- [ ] `model_off` segue íntegro por default na leitura real de `aurora dev`.
- [ ] `model_on` só entra quando configurado, com `ollama` como provider canônico atual e `qwen2.5:3b-instruct` como modelo canônico inicial.
- [ ] Houve um caso feliz com provider configurado e um caso ruim com provider indisponível, com `status=fallback_deterministic`, ambos lidos no terminal real.
- [ ] Nenhuma doc ou release note sugere autoridade do modelo sobre `policy`, `support`, `block`, `confirmation`, `route`, `execution`, verdade operacional ou polimento de `facts.local_model.output_text`.

## Diffs sensíveis

- [ ] Os diffs em `python/aurora/install/`, `python/aurora/contracts/`, `python/aurora/observability/`, `python/aurora/presentation/`, `bin/`, `install.sh` e `uninstall.sh` foram revisados friamente.
- [ ] Nenhuma doc, help ou mensagem pública promete mais do que o runtime realmente faz.
- [ ] Não ficou deriva de versão entre código, docs, help e changelog.

## Canon vivo local

- [ ] Se a rodada tocou PV/contexto ou roadmap privado, `python3 tests/audit_canonic_integrity.py` passou.
- [ ] Pointers canônicos centrais agora apontam para arquivos reais.
- [ ] Material pré-`v1.2.0` ou de preparação pós-`v1.0.0` que continuou útil foi marcado como histórico/transicional.
- [ ] A promoção de versão, a classificação final de roadmap e a decisão de canon continuam tratadas como decisão humana de mantenedor/revisor, não do guardrail local.

## Terminal real

- [ ] Se launchers, instalador ou help mudaram, `aurora --version` e `aurora --help` foram testados no terminal real.
- [ ] Se runtime real mudou, a superfície tocada foi validada no terminal local real.
- [ ] Se a rodada tocou `host_maintenance.atualizar`, foram lidos `aurora dev "atualizar sistema"`, `aurora atualizar sistema` e `aurora atualizar sistema --confirm`, com conferência explícita de `sudo + pacman`, sem `paru` e sem AUR implícita.
- [ ] Para cada superfície real tocada, houve pelo menos um caso feliz e um caso ruim ou de bloqueio honesto.
- [ ] A validação humana cobriu o que o gate não enxerga: prompt, senha, timing, handoff, ruído visual e sensação da renderização.

## Bloqueios

- [ ] Não fazer `push` se `bash tests/release_gate_pre_push.sh` falhar.
- [ ] Não fazer `tag` nem `release` se `bash tests/release_gate_pre_release.sh` falhar.
- [ ] Não fazer `tag` nem `release` com checklist incompleto.
- [ ] Não fazer `tag` nem `release` sem validação humana real quando a mudança toca runtime, instalador, launcher ou renderização pública.
