# Установка

С нуля до первого ответа из репо — около часа, большая часть — на наполнение.

## 0. Что нужно

- git, bash, Python 3.11+ (drift-чекер — только stdlib);
- агент для чтения репо: Claude Code (`claude`) или любой, который читает
  `CLAUDE.md` / `AGENTS.md`;
- доступ на чтение к коду продукта — для brain (можно позже).

## 1. Создать свой репо

1. На GitHub: **Use this template → Create a new repository**. Сделайте его
   **приватным** — это база знаний вашей команды.
2. Клонировать:

   ```bash
   git clone git@github.com:<you>/<team>-knowledge.git
   cd <team>-knowledge
   ```

## 2. Подключить хуки

```bash
./scripts/setup.sh --dry-run   # показать, что будет сделано
./scripts/setup.sh             # сделать
```

`setup.sh` проверяет python3, выполняет `git config core.hooksPath .githooks`,
ставит права на скрипты, делает симлинки скиллов в `.claude/skills/` и
прогоняет проверки. Повторный запуск безопасен.

Вручную то же самое — одна команда:

```bash
git config core.hooksPath .githooks
```

Проверка: `python3 brain/scripts/check_drift.py` → `3 ok`. Затем красное демо
из README: поменяйте `"no_show"` в `examples/demo-code/booking/status.py` и
попробуйте закоммитить — коммит должен упасть. Верните: `git checkout examples/demo-code`.

## 3. Наполнить — в этом порядке

Примеры про Acme найти так: `grep -rn "Acme" --include=*.md .` — заменяйте или
удаляйте по мере наполнения.

1. **`CLAUDE.md`** — название команды и продукта, **главный повторяющийся
   вопрос**, граница доверия (допишите свои пункты).
2. **`product/features.md`** — ответ на этот вопрос: реестр фич с
   источниками и указатели, где живут статусы.
3. **Проверка M0:** откройте свежую сессию (`claude` в корне репо) и задайте
   реальный вопрос команды. Ответ должен прийти из репо с цитатой файла. Не
   пришёл — допишите файл, а не промпт.
4. **Покажите ответ одному тиммейту** там, где он его увидит (M1).
5. **`product/team.md`, `product/overview.md`, `brain/product/glossary.md`** —
   роли, продукт, словарь.
6. **Brain на своём коде:**
   ```bash
   cp .env.example .env          # .env в .gitignore
   # в .env: CODE_ROOT=~/code/<ваш-репо>
   ```
   Замените клеймы в `brain/claims.yaml` (форматы — в его шапке), перенесите
   реальные статусы в claim-секции `brain/product/object-model.md`, удалите
   `examples/` и уберите `code_root: examples/demo-code`. Убедитесь, что
   клейм умеет краснеть (`brain/MAINTENANCE.md`, «Новый клейм за 3 шага»).
7. **`decisions.md`** — 5–10 принципов из реальных эпизодов, авторитет
   калибровки, встреча для вердиктов. Примеры D-01/D-02 удалите.
8. **`soul.md`, `robin/duties.md`** — имя и голос агента, расписание duty.

Каждый шаг — отдельный коммит или PR; хук проверит frontmatter
(`owner / tier / last_reviewed`) у каждого `.md`.

## 4. Опционально: скиллы Team OS Toolkit

Тулкит умеет майнить наполнение из того, что уже есть на вашей машине: история
сессий агента, MCP-конфиг, существующие доки и код. Установка и описание — https://github.com/BayramAnnakov/team-os-toolkit

| Скилл | Что даёт |
|---|---|
| `/init-team-os` | Майнит главный вопрос и первые файлы, задаёт не больше 5 вопросов |
| `/init-team-brain` | Глоссарий и объектную модель из кода, клеймы для drift-чекера |
| `/init-team-decisions` | Принципы из встреч и чатов в `decisions.md` + скилл-подмастерье |
| `/robin-init` | Черновики `soul.md` и duty roster, спеку агента под ваш стек |

Скиллы создают служебные папки (`.team-os-setup/`, `.decisions-setup/`,
`.robin-setup/`, `brain/.brain-setup/`) и `ROBIN-SPEC.local.md` — хук их не
проверяет. Сгенерированное сверьте с конвенциями этого шаблона: хук ждёт во
frontmatter ключ `tier` — если скилл написал `stability`, переименуйте.

## 5. Подключить агента

Агент живёт в отдельном репо
[`team-os-agent`](https://github.com/slavkkoo/team-os-agent): Telegram-бот +
duty по systemd-таймерам. В его `.env` укажите:

- `KNOWLEDGE_REPO_URL` — URL этого репо (агенту — read-only deploy key или
  токен с правом создавать ветки/PR для brain-sync);
- `KNOWLEDGE_BRANCH` — основная ветка (обычно `main`);
- `CODE_REPOS` — репо кода для сверки (тот же код, что в `CODE_ROOT`).

Агент читает `CLAUDE.md`, `soul.md` и `robin/duties.md` из этого репо; правки
поведения — PR сюда, а не в конфиг агента.
