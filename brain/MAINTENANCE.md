---
owner: dev-lead
tier: stable
last_reviewed: 2026-10-28
---

# Обслуживание brain

> Что сюда писать: кто, когда и как обновляет каждый файл brain. Замените
> роли на свои.

| Что | Кто | Когда | Как |
|---|---|---|---|
| `now.md` | pm | еженедельно | из дайджестов и трекера; новая дата снапшота, bump `last_reviewed` |
| `product/object-model.md` | dev-lead | чекер красный | `git pull` в `CODE_ROOT`, дописать новые значения в claim-секцию |
| `product/glossary.md` | dev-lead | новый термин | строка: термин + имя в коде + источник |
| `claims.yaml` | dev-lead | новое обещание дока о коде | claim-секция в доке + запись в `claims.yaml` |
| Клон кода | любой | перед проверкой и выводами | `git -C "$CODE_ROOT" pull` |
| Eval | pm | ежемесячно | `evals/knowledge-impact.md`: перестал brain выигрывать — доки сгнили |

Еженедельный прогон — скилл `skills/update-knowledge/` (читает неделю,
обновляет volatile-доки, открывает PR; напрямую не пушит).

Чекер: `python3 brain/scripts/check_drift.py` — зелёный обязателен перед
коммитом (хук это форсит). Код не выкачан → SKIPPED, не провал; в CI
используйте `--strict`, чтобы SKIPPED ронял сборку.

Новый клейм за 3 шага:
1. В доке оберните список значений: `<!-- claim:my-id -->` … `<!-- /claim:my-id -->`.
2. В `claims.yaml` добавьте запись с `type` и `source` (форматы — в шапке).
3. `python3 brain/scripts/check_drift.py` → `ok my-id`. Затем проверьте, что
   клейм умеет краснеть: временно уберите значение из дока — должен быть FAIL.
