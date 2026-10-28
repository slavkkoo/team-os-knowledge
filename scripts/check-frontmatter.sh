#!/usr/bin/env bash
# Team OS frontmatter guard.
#
# Каждый .md репозитория знаний открывается блоком frontmatter:
#   ---
#   owner: <роль или ник>                 # кто отвечает за правду в файле
#   tier: stable | evolving | volatile    # как быстро гниёт
#   last_reviewed: YYYY-MM-DD             # ставит ТОЛЬКО человек после ревью
#   bot_updated: YYYY-MM-DD               # необязательно: ставят боты/конвейеры
#   ---
#
# Использование:
#   scripts/check-frontmatter.sh --staged      # то, что лежит в индексе git (pre-commit)
#   scripts/check-frontmatter.sh --all         # все .md репо (кроме исключений)
#   scripts/check-frontmatter.sh a.md b.md     # конкретные файлы (без исключений)
# Exit 0 — всё хорошо, 1 — хотя бы один файл не прошёл.
#
# Совместим с bash 3.2 (macOS).
set -u

# Исключения: публичные доки репо, демо-код и служебные папки скиллов тулкита.
EXEMPT_RE='^(README\.md|INSTALL\.md|CHANGELOG\.md|ROBIN-SPEC\.local\.md)$|^(examples|\.github|\.claude|\.setup-archive|\.team-os-setup|\.decisions-setup|\.robin-setup|brain/\.brain-setup|_toolkit-reference)/'
DATE_RE='^["'"'"']?[0-9]{4}-[0-9]{2}-[0-9]{2}["'"'"']?[[:space:]]*$'

fail=0

# check_content <label> <содержимое файла>
# (содержимое — аргументом, не через пайп: иначе fail=1 потеряется в подоболочке)
check_content() {
  label="$1"
  content="$(printf '%s\n' "$2" | tr -d '\r')"

  if [ "$(printf '%s\n' "$content" | sed -n '1p')" != "---" ]; then
    echo "  FAIL $label — нет frontmatter (первая строка должна быть '---')"
    fail=1
    return
  fi
  closing="$(printf '%s\n' "$content" | awk 'NR>1 && /^---[[:space:]]*$/ {print NR; exit}')"
  if [ -z "$closing" ]; then
    echo "  FAIL $label — frontmatter не закрыт второй строкой '---'"
    fail=1
    return
  fi
  block="$(printf '%s\n' "$content" | awk 'NR==1{next} /^---[[:space:]]*$/{exit} {print}')"

  miss=""
  printf '%s\n' "$block" | grep -qE '^owner:[[:space:]]*[^[:space:]]' || miss="$miss owner"
  printf '%s\n' "$block" | grep -qE '^tier:[[:space:]]*(stable|evolving|volatile)[[:space:]]*$' \
    || miss="$miss tier(stable|evolving|volatile)"
  lr="$(printf '%s\n' "$block" | sed -n 's/^last_reviewed:[[:space:]]*//p' | head -1)"
  printf '%s\n' "$lr" | grep -qE "$DATE_RE" || miss="$miss last_reviewed(YYYY-MM-DD)"
  bu="$(printf '%s\n' "$block" | sed -n 's/^bot_updated:[[:space:]]*//p' | head -1)"
  if [ -n "$bu" ]; then
    printf '%s\n' "$bu" | grep -qE "$DATE_RE" || miss="$miss bot_updated(YYYY-MM-DD)"
  fi

  if [ -n "$miss" ]; then
    echo "  FAIL $label — не хватает или неверно:$miss"
    fail=1
  else
    echo "  ok   $label"
  fi
}

mode="${1:-}"
case "$mode" in
  --staged)
    cd "$(git rev-parse --show-toplevel)" || exit 1
    list="$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.md$' | grep -vE "$EXEMPT_RE" || true)"
    [ -z "$list" ] && exit 0
    while IFS= read -r f; do
      [ -n "$f" ] || continue
      check_content "$f" "$(git show ":$f")"   # проверяем ровно то, что коммитится
    done <<EOF
$list
EOF
    ;;
  --all)
    root="$(cd "$(dirname "$0")/.." && pwd -P)"
    cd "$root" || exit 1
    # git ls-files — только если это корень своего репо (а не подкаталог чужого)
    if [ "$(git rev-parse --show-toplevel 2>/dev/null)" = "$root" ]; then
      list="$(git ls-files --cached --others --exclude-standard '*.md')"
    else
      list="$(find . -name '*.md' -not -path './.git/*' | sed 's|^\./||' | sort)"
    fi
    list="$(printf '%s\n' "$list" | grep -vE "$EXEMPT_RE" || true)"
    [ -z "$list" ] && { echo "  нет .md для проверки"; exit 0; }
    while IFS= read -r f; do
      [ -n "$f" ] && [ -f "$f" ] || continue
      check_content "$f" "$(cat "$f")"
    done <<EOF
$list
EOF
    ;;
  ""|-h|--help)
    sed -n '2,19p' "$0"
    [ -z "$mode" ] && exit 2
    exit 0
    ;;
  *)
    for f in "$@"; do
      case "$f" in *.md) ;; *) continue ;; esac
      [ -f "$f" ] || { echo "  FAIL $f — файл не найден"; fail=1; continue; }
      check_content "$f" "$(cat "$f")"
    done
    ;;
esac

exit $fail
