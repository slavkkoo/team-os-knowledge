---
owner: pm
tier: stable
last_reviewed: 2026-10-28
---

# skills/ — скиллы команды

> Что сюда класть: сохранённые инструкции, которые агенты применяют
> повторяемо (решения, ответы поддержки, разбор задач). Одна папка — один
> скилл: `SKILL.md` с frontmatter (`name`, `description` — *когда* применять,
> плюс `owner / tier / last_reviewed`). Новые скиллы — через PR.

| Скилл | Для кого | Что делает |
|---|---|---|
| [`decide-like-team/`](decide-like-team/SKILL.md) | вся команда | Подмастерье для решений: рекомендация → принципы → gap-анализ → лог |
| [`../brain/skills/update-knowledge/`](../brain/skills/update-knowledge/SKILL.md) | владелец / агент, еженедельно | Синхронизирует brain с неделей, открывает PR |

## Как подключить

- **Claude Code в этом репо:** `scripts/setup.sh` делает симлинки в
  `.claude/skills/` — скиллы доступны как `/decide-like-team`, `/update-knowledge`.
- **Глобально** (во всех проектах): симлинк, не копия — правки доезжают сами:
  `ln -s "$(pwd)/skills/decide-like-team" ~/.claude/skills/decide-like-team`

## Контракт для агента команды

Реестр скиллов агента (`team-os-agent`) держит **тонкие указатели**:
frontmatter с триггером + строка «прочитай канонический SKILL.md по пути X в
репо знаний». Никаких копий: правки доезжают при синхронизации репо.
