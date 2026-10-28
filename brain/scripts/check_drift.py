#!/usr/bin/env python3
"""
check_drift.py — сверяет обещания brain/claims.yaml с исходным кодом.

Контракт (полная спецификация — в шапке brain/claims.yaml):
  exit 0 — все проверенные клеймы зелёные. Непроверенные (код не выкачан)
           перечислены как SKIPPED и НЕ считаются проверенными.
  exit 1 — хотя бы один FAIL (печатаем «код говорит / в доке нет»)
           или claims.yaml сломан.
  exit 2 — режим --strict (или DRIFT_STRICT=1) и есть SKIPPED. Для CI,
           где код обязан быть на месте.

Где лежит код (первое заданное побеждает):
  1. --code-root DIR
  2. переменная окружения CODE_ROOT
  3. ключ code_root: в brain/claims.yaml
  4. examples/demo-code (демо из коробки)
Относительный путь считается от корня репозитория знаний.

Запуск:
  python3 brain/scripts/check_drift.py
  python3 brain/scripts/check_drift.py --code-root ~/code/acme
  CODE_ROOT=~/code/acme python3 brain/scripts/check_drift.py --strict

Только stdlib, Python 3.11+.
"""
import argparse
import os
import re
import sys

BRAIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(BRAIN)
CLAIMS_PATH = os.path.join(BRAIN, "claims.yaml")
DEFAULT_CODE_ROOT = "examples/demo-code"
# files-in-dir: служебные и базовые файлы — не значения перечисления
EXCLUDED_PREFIXES = ("_", "Abstract", "Base", "base")
KNOWN_TYPES = ("enum-values", "symbol-exists", "pointer-only")


class ConfigError(Exception):
    """claims.yaml не читается или описан неверно."""


def rel(path):
    """Путь для печати: относительно корня репо, если внутри него."""
    try:
        r = os.path.relpath(path, REPO)
    except ValueError:
        return path
    return path if r.startswith("..") else r


def _clean(val):
    """Срезает хвостовой комментарий ' # ...' и кавычки."""
    val = re.sub(r"\s+#.*$", "", val).strip()
    return val.strip("'\"")


def _flow_map(text, lineno):
    """Разбирает { key: value, key: value } — плоский словарь без вложений."""
    text = re.sub(r"\s+#.*$", "", text).strip()
    if not (text.startswith("{") and text.endswith("}")):
        raise ConfigError(
            f"claims.yaml:{lineno}: source пишется одной строкой: "
            "{ path: ..., extract: ... }"
        )
    out = {}
    for part in text[1:-1].split(","):
        if not part.strip():
            continue
        if ":" not in part:
            raise ConfigError(f"claims.yaml:{lineno}: в source нет ':' в {part.strip()!r}")
        key, val = part.split(":", 1)
        out[key.strip()] = val.strip().strip("'\"")
    return out


def parse_claims(path):
    """Минимальный парсер под фиксированную схему claims.yaml (без PyYAML).

    Схема:
      code_root: <путь>          # необязательно
      claims:
        - id: <id>
          doc: <путь к доку от корня репо>
          type: enum-values | symbol-exists | pointer-only
          source: { repo: <подкаталог>, path: <путь>, extract: ..., symbol: ... }
    """
    if not os.path.isfile(path):
        raise ConfigError(f"не найден {rel(path)}")
    settings, claims, cur, item_indent = {}, [], None, None
    with open(path, encoding="utf-8") as fh:
        for n, raw in enumerate(fh, 1):
            line = raw.rstrip("\r\n")
            body = line.strip()
            if not body or body.startswith("#"):
                continue
            indent = len(line) - len(line.lstrip(" "))
            if body.startswith("- id:"):
                cur = {"id": _clean(body.split(":", 1)[1]), "_line": n}
                item_indent = indent
                claims.append(cur)
                continue
            if ":" not in body:
                raise ConfigError(f"claims.yaml:{n}: не понимаю строку {body!r}")
            key, val = body.split(":", 1)
            key = key.strip()
            if indent == 0:
                cur = None
                if key != "claims":
                    settings[key] = _clean(val)
                continue
            if cur is None or indent <= item_indent:
                raise ConfigError(f"claims.yaml:{n}: поле {key!r} вне клейма")
            if key == "source":
                cur["source"] = _flow_map(val, n)
            else:
                cur[key] = _clean(val)
    for c in claims:
        for field in ("doc", "type", "source"):
            if field not in c:
                raise ConfigError(f"claims.yaml:{c['_line']}: у клейма {c['id']!r} нет поля {field!r}")
        if "path" not in c["source"]:
            raise ConfigError(f"claims.yaml:{c['_line']}: у клейма {c['id']!r} в source нет path")
    return settings, claims


def resolve_code_root(cli_value, settings):
    candidates = (
        ("--code-root", cli_value),
        ("env CODE_ROOT", os.environ.get("CODE_ROOT")),
        ("code_root в claims.yaml", settings.get("code_root")),
    )
    origin, value = "по умолчанию", DEFAULT_CODE_ROOT
    for name, val in candidates:
        if val:
            origin, value = name, val
            break
    path = os.path.expanduser(value)
    if not os.path.isabs(path):
        path = os.path.join(REPO, path)
    return os.path.normpath(path), origin


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def extract_values(target, extract):
    """Возвращает список значений, которые определяет код."""
    kind, _, arg = extract.partition(":")
    if kind == "const-prefix":
        # STATUS_X = "x" (Python), const STATUS_X = 'x'; (PHP/JS),
        # STATUS_X: str = "x", STATUS_X: "x" (объект JS/TS)
        if not arg:
            raise ConfigError("extract const-prefix требует префикс: const-prefix:STATUS_")
        pattern = (
            r"\b%s\w*\s*(?::\s*[\w.\[\]]+\s*)?[=:]\s*['\"]([^'\"]*)['\"]"
            % re.escape(arg)
        )
        return sorted(set(re.findall(pattern, read_text(target))))
    if kind == "files-in-dir":
        # имена файлов каталога (без расширения) = значения; arg — расширение
        return sorted(
            os.path.splitext(f)[0]
            for f in os.listdir(target)
            if os.path.isfile(os.path.join(target, f))
            and (not arg or f.endswith(arg))
            and not f.startswith(EXCLUDED_PREFIXES)
        )
    raise ConfigError(f"неизвестный extract: {extract!r} (есть const-prefix:<P>, files-in-dir:<.ext>)")


def doc_section(doc_path, claim_id):
    if not os.path.isfile(doc_path):
        return None
    cid = re.escape(claim_id)
    m = re.search(r"<!--\s*claim:%s\s*-->(.*?)<!--\s*/claim:%s\s*-->" % (cid, cid),
                  read_text(doc_path), re.S)
    return m.group(1) if m else None


def mentions(text, token):
    """Токен встречается целиком (не как часть другого слова)."""
    return re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(token), text) is not None


def section_values(section):
    """Значения из секции-списка: через запятую/перенос, `обратные кавычки` и
    маркеры списка допустимы. Пояснения пишите вне маркеров claim."""
    out = []
    for item in re.split(r"[,\n;|]", section):
        item = item.strip().strip("`*-• ").strip("`")
        if re.fullmatch(r"[\w.-]+", item):
            out.append(item)
    return out


def symbol_problem(target, symbol):
    """Проверка, что symbol упомянут в файле (для каталога не проверяется)."""
    if symbol and os.path.isfile(target) and not mentions(read_text(target), symbol):
        return f"файл есть, но symbol {symbol!r} в нём не найден"
    return None


def check_claim(c, code_root):
    """-> (status, details). status: ok | fail | skip."""
    cid, ctype, src = c["id"], c["type"], c["source"]
    if ctype not in KNOWN_TYPES:
        return "fail", {"reason": f"неизвестный type {ctype!r} (есть: {', '.join(KNOWN_TYPES)})"}

    repo_dir = os.path.join(code_root, src["repo"]) if src.get("repo") else code_root
    if not os.path.isdir(repo_dir):
        what = f"репо {src['repo']!r} не выкачан в {rel(code_root)}" if src.get("repo") \
            else f"CODE_ROOT не найден: {rel(code_root)}"
        return "skip", {"reason": what}

    target = os.path.join(repo_dir, src["path"])
    doc_path = os.path.join(REPO, c["doc"])
    # код на месте, а пути нет — это дрейф (код переехал), а не «не проверено»
    if not os.path.exists(target):
        return "fail", {"reason": f"путь исчез из кода: {src['path']} (код переехал или клейм устарел)"}

    if ctype == "symbol-exists":
        problem = symbol_problem(target, src.get("symbol"))
        return ("fail", {"reason": problem}) if problem else ("ok", {})

    section = doc_section(doc_path, cid)
    if section is None:
        return "fail", {"reason": f"в {c['doc']} нет секции <!-- claim:{cid} --> ... <!-- /claim:{cid} -->"}

    if ctype == "pointer-only":
        problems = []
        sym = src.get("symbol")
        if not sym:
            problems.append("в source нет symbol")
        else:
            p = symbol_problem(target, sym)
            if p:
                problems.append(p)
            if not mentions(section, sym):
                problems.append(f"секция не упоминает symbol {sym!r}")
        if src["path"] not in section:
            problems.append(f"секция не упоминает path {src['path']!r}")
        return ("fail", {"reason": "; ".join(problems)}) if problems else ("ok", {})

    # enum-values
    extract = src.get("extract", "")
    if extract.startswith("files-in-dir") and not os.path.isdir(target):
        return "fail", {"reason": f"files-in-dir ждёт каталог, а {src['path']} — файл"}
    if extract.startswith("const-prefix") and not os.path.isfile(target):
        return "fail", {"reason": f"const-prefix ждёт файл, а {src['path']} — каталог"}
    values = extract_values(target, extract)
    if not values:
        return "fail", {"reason": f"в коде не найдено ни одного значения по {extract!r} — проверь extract"}
    missing = [v for v in values if not mentions(section, v)]
    extra = [v for v in section_values(section) if v not in values]
    if missing:
        return "fail", {"reason": "в доке нет значений, которые есть в коде",
                        "values": values, "missing": missing, "extra": extra}
    return "ok", {"extra": extra}


def main():
    ap = argparse.ArgumentParser(description="Drift-чекер: доки brain против кода.")
    ap.add_argument("--code-root", help="каталог с кодом (иначе env CODE_ROOT / code_root / демо)")
    ap.add_argument("--strict", action="store_true",
                    default=os.environ.get("DRIFT_STRICT", "") in ("1", "true", "yes"),
                    help="SKIPPED считать ошибкой (exit 2) — для CI")
    args = ap.parse_args()

    try:
        settings, claims = parse_claims(CLAIMS_PATH)
    except ConfigError as e:
        print(f"ОШИБКА КОНФИГА: {e}")
        sys.exit(1)

    code_root, origin = resolve_code_root(args.code_root, settings)
    print(f"Код: {rel(code_root)} ({origin})")
    if not os.path.isdir(code_root):
        print(f"SKIPPED: каталог кода не найден — ни один клейм не проверен."
              f" Задай CODE_ROOT или code_root в brain/claims.yaml.")

    passed, failed, skipped, warned = [], [], [], []
    for c in claims:
        try:
            status, info = check_claim(c, code_root)
        except ConfigError as e:
            status, info = "fail", {"reason": f"конфиг: {e}"}
        except OSError as e:
            status, info = "fail", {"reason": f"ошибка чтения: {e}"}
        {"ok": passed, "fail": failed, "skip": skipped}[status].append((c, info))
        if info.get("extra"):
            warned.append((c, info["extra"]))

    for c, info in failed:
        print(f"FAIL     {c['id']}: {info['reason']}")
        if info.get("missing"):
            print(f"         код говорит: {', '.join(info['values'])}")
            print(f"         в доке НЕТ:  {', '.join(info['missing'])}  -> допиши в {c['doc']}")
    for c, extra in warned:
        print(f"WARN     {c['id']}: в доке есть значения, которых нет в коде: "
              f"{', '.join(extra)} (удалить из {c['doc']}?)")
    for c, info in skipped:
        print(f"SKIPPED  {c['id']}: {info['reason']}")
    for c, _ in passed:
        print(f"ok       {c['id']}")

    total = len(claims)
    tail = " Skipped-клеймы НЕ проверены." if skipped else ""
    print(f"\nИтог: {len(passed)} ok, {len(failed)} failed, {len(skipped)} skipped из {total}.{tail}")
    if failed:
        sys.exit(1)
    if skipped and args.strict:
        print("--strict: skipped считается ошибкой.")
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
