# Review Checklist - Aurora v1.0.0

Use este checklist antes de `push`, `tag` ou `release`. Se um item não se aplica, a dispensa precisa ser consciente.

## Superfície pública

- [ ] `VERSION`, `README.md`, `CHANGELOG.md` e `resources/help.txt` estão coerentes entre si.
- [ ] `docs/ARCHITECTURE.md`, `docs/DECISION_RECORD_SCHEMA.md`, `docs/FACTS_VS_RENDERING.md`, `docs/WORKFLOW_DE_TESTES_E_RELEASE.md` e `tests/README.md` batem com a release atual.
- [ ] `aurora --version` mostra a versão pública certa.
- [ ] `aurora --help` reflete a superfície pública real.
- [ ] Se contrato, payload ou renderização mudaram, `aurora dev "<caso feliz>"` e `aurora dev "<caso ruim>"` foram lidos.

## Seam `local_model` da v1.0.0

- [ ] `model_off` segue íntegro por default na leitura real de `aurora dev`.
- [ ] `model_on` só entra quando configurado, com `ollama` como provider canônico atual e `qwen2.5:3b-instruct` como modelo canônico inicial.
- [ ] Houve um caso feliz com provider configurado e um caso ruim com provider indisponível, com `status=fallback_deterministic`, ambos lidos no terminal real.
- [ ] Nenhuma doc ou release note sugere autoridade do modelo sobre `policy`, `support`, `block`, `confirmation`, `route`, `execution`, verdade operacional ou polimento de `facts.local_model.output_text`.

## Diffs sensíveis

- [ ] Os diffs em `python/aurora/install/`, `python/aurora/contracts/`, `python/aurora/observability/`, `python/aurora/presentation/`, `bin/`, `install.sh` e `uninstall.sh` foram revisados friamente.
- [ ] Nenhuma doc, help ou mensagem pública promete mais do que o runtime realmente faz.
- [ ] Não ficou deriva de versão entre código, docs, help e changelog.

## Terminal real

- [ ] Se launchers, instalador ou help mudaram, `aurora --version` e `aurora --help` foram testados no terminal real.
- [ ] Se runtime real mudou, a superfície tocada foi validada no terminal local real.
- [ ] Para cada superfície real tocada, houve pelo menos um caso feliz e um caso ruim ou de bloqueio honesto.
- [ ] A validação humana cobriu o que o gate não enxerga: prompt, senha, timing, handoff, ruído visual e sensação da renderização.

## Bloqueios

- [ ] Não fazer `push` se `bash tests/release_gate_pre_push.sh` falhar.
- [ ] Não fazer `tag` nem `release` se `bash tests/release_gate_pre_release.sh` falhar.
- [ ] Não fazer `tag` nem `release` com checklist incompleto.
- [ ] Não fazer `tag` nem `release` sem validação humana real quando a mudança toca runtime, instalador, launcher ou renderização pública.
