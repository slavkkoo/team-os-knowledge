---
owner: dev-lead
tier: stable
last_reviewed: 2026-10-28
---

# Скиллы brain

| Скилл | Для кого | Что делает |
|---|---|---|
| [`update-knowledge/`](update-knowledge/SKILL.md) | владелец или агент, еженедельно | Синхронизирует brain с неделей реальности, открывает PR |

Подключение — `scripts/setup.sh` (симлинк в `.claude/skills/`) или вручную:
`ln -s "$(pwd)/brain/skills/update-knowledge" ~/.claude/skills/update-knowledge`.
Копий не делать — иначе правки не доедут.
