#!/usr/bin/env bash
# scripts/setup.sh [--dry-run] — подготовка репо знаний после clone.
#
# Что делает (идемпотентно, повторный запуск ничего не ломает):
#   1. проверяет git и python3 >= 3.11;
#   2. включает хуки: git config core.hooksPath .githooks;
#   3. ставит права на исполнение хукам и скриптам;
#   4. подключает скиллы репо в .claude/skills/ симлинками (Claude Code
#      подхватит /decide-like-team и /update-knowledge в этом каталоге);
#   5. прогоняет проверки (read-only): frontmatter всех .md и drift-чекер.
#
# --dry-run — показать шаги 2–4, ничего не меняя (проверки 1 и 5 только читают).
set -u

DRY=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY=1 ;;
    -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
    *) echo "Неизвестный аргумент: $arg (есть --dry-run, --help)"; exit 2 ;;
  esac
done

root="$(cd "$(dirname "$0")/.." && pwd -P)"
cd "$root" || exit 1
problems=0

say()  { printf '%s\n' "$*"; }
run()  {
  if [ "$DRY" -eq 1 ]; then say "  [dry-run] $*"; else say "  + $*"; "$@"; fi
}

say "== Team OS knowledge: setup ($root)"
[ "$DRY" -eq 1 ] && say "   режим --dry-run: ничего не меняю"

# 1. Окружение
say "== 1. Окружение"
if command -v git >/dev/null 2>&1; then
  say "  ok   git: $(git --version)"
else
  say "  FAIL git не найден — установите git"; exit 1
fi
if command -v python3 >/dev/null 2>&1 \
   && python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
  say "  ok   python3: $(python3 --version 2>&1)"
else
  say "  FAIL нужен python3 >= 3.11 (drift-чекер). Сейчас: $(python3 --version 2>&1 || echo 'нет')"
  problems=1
fi
is_repo=0
if [ "$(git rev-parse --show-toplevel 2>/dev/null)" = "$root" ]; then
  is_repo=1
  say "  ok   git-репозиторий: $root"
else
  say "  WARN $root — не корень git-репо. Сначала git clone (или git init)."
fi

# 2. Хуки
say "== 2. Git-хуки"
if [ "$is_repo" -eq 1 ]; then
  current="$(git config --get core.hooksPath || true)"
  if [ "$current" = ".githooks" ]; then
    say "  ok   core.hooksPath уже .githooks"
  else
    [ -n "$current" ] && say "  WARN core.hooksPath был '$current' — заменяю"
    run git config core.hooksPath .githooks
  fi
else
  say "  пропуск: не git-репо (после clone выполните: git config core.hooksPath .githooks)"
  [ "$DRY" -eq 1 ] || problems=1
fi

# 3. Права
say "== 3. Права на исполнение"
for f in .githooks/pre-commit scripts/*.sh brain/scripts/*.py; do
  [ -f "$f" ] || continue
  if [ -x "$f" ]; then say "  ok   $f"; else run chmod +x "$f"; fi
done

# 4. Скиллы для Claude Code
say "== 4. Скиллы -> .claude/skills/"
made_dir=0
for dir in skills/*/ brain/skills/*/; do
  [ -f "${dir}SKILL.md" ] || continue
  name="$(basename "$dir")"
  link=".claude/skills/$name"
  target="../../${dir%/}"
  if [ -L "$link" ] && [ "$(readlink "$link")" = "$target" ]; then
    say "  ok   $link"
  elif [ -e "$link" ]; then
    say "  WARN $link уже существует и это не наш симлинк — не трогаю"
  else
    if [ ! -d .claude/skills ] && [ "$made_dir" -eq 0 ]; then
      run mkdir -p .claude/skills; made_dir=1
    fi
    run ln -s "$target" "$link"
  fi
done

# 5. Проверки (только чтение)
say "== 5. Проверки"
# те же настройки, что видит pre-commit хук
if [ -f .env ]; then set -a; . ./.env; set +a; say "  (настройки из .env)"; fi
fm_out="$(bash scripts/check-frontmatter.sh --all 2>&1)"
if [ $? -eq 0 ]; then
  say "  ok   frontmatter: $(printf '%s\n' "$fm_out" | grep -c '^  ok') файлов"
else
  printf '%s\n' "$fm_out" | grep 'FAIL' | sed 's/^/  /'
  problems=1
fi
if command -v python3 >/dev/null 2>&1; then
  python3 brain/scripts/check_drift.py | sed 's/^/  /'
  [ "${PIPESTATUS[0]}" -eq 0 ] || problems=1
fi

say ""
if [ "$problems" -ne 0 ]; then
  say "Есть проблемы (см. FAIL/WARN выше)."
else
  say "Готово."
fi
cat <<'EOF'

Дальше (подробно — INSTALL.md):
  1. Красное демо: поменяйте "no_show" в examples/demo-code/booking/status.py
     и сделайте git commit -am test — коммит должен упасть. Затем
     git checkout examples/demo-code
  2. Заполните CLAUDE.md (главный вопрос + граница доверия), затем product/features.md.
  3. Подключите свой код: CODE_ROOT в .env (шаблон .env.example) и клеймы в brain/claims.yaml.
EOF
[ "$problems" -eq 0 ] || exit 1
exit 0
