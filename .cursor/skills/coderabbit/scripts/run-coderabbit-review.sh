#!/usr/bin/env bash
# Run CodeRabbit CLI on the current branch vs a base (default origin/master).
# Usage:
#   bash .cursor/skills/coderabbit/scripts/run-coderabbit-review.sh \
#     [--base origin/master] [--dir <path>] [--light] [--uncommitted]
#     [--out PATH]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT"

export PATH="${HOME}/.local/bin:${PATH}"

BASE="origin/master"
DIR=""
LIGHT=0
UNCOMMITTED=0
OUT=""

require_value() {
  local flag="$1"
  local value="${2-}"
  if [[ -z "$value" || "$value" == -* ]]; then
    echo "error: $flag requires a non-option value" >&2
    exit 1
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base)
      require_value "$1" "${2-}"
      BASE="$2"
      shift 2
      ;;
    --dir)
      require_value "$1" "${2-}"
      DIR="$2"
      shift 2
      ;;
    --light) LIGHT=1; shift ;;
    --uncommitted) UNCOMMITTED=1; shift ;;
    --out)
      require_value "$1" "${2-}"
      OUT="$2"
      shift 2
      ;;
    -h|--help)
      sed -n '2,7p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 1
      ;;
  esac
done

if ! command -v coderabbit >/dev/null 2>&1; then
  echo "error: coderabbit CLI not found (install and put on PATH, e.g. ~/.local/bin)" >&2
  exit 1
fi

if ! git rev-parse --verify "$BASE" >/dev/null 2>&1; then
  if git rev-parse --verify master >/dev/null 2>&1; then
    echo "warn: '$BASE' missing; falling back to 'master'" >&2
    BASE="master"
  else
    echo "error: base ref '$BASE' not found" >&2
    exit 1
  fi
fi

BRANCH="$(git branch --show-current 2>/dev/null || echo DETACHED)"
SAFE_BRANCH="${BRANCH//\//-}"
STAMP="$(date +%Y%m%d-%H%M%S)"
CACHE_DIR="$ROOT/.cursor/skills/coderabbit/.cache"
mkdir -p "$CACHE_DIR"

SCOPE="all"
if [[ -n "$DIR" ]]; then
  SCOPE="${DIR//\//-}"
fi

if [[ -z "$OUT" ]]; then
  OUT="$CACHE_DIR/cr-${SAFE_BRANCH}-vs-${BASE//\//-}-${SCOPE}-${STAMP}.jsonl"
fi

# Rough file count for Free-plan guidance
if [[ -n "$DIR" ]]; then
  FILE_COUNT="$(git diff --name-only "${BASE}...HEAD" -- "$DIR" 2>/dev/null | wc -l | tr -d ' ')"
else
  FILE_COUNT="$(git diff --name-only "${BASE}...HEAD" 2>/dev/null | wc -l | tr -d ' ')"
fi
FILE_COUNT="${FILE_COUNT:-0}"

echo "branch:  $BRANCH"
echo "base:    $BASE"
echo "files:   $FILE_COUNT (in scope)"
echo "out:     $OUT"
if [[ "$FILE_COUNT" -gt 150 ]]; then
  echo "warn: >150 files — Free CodeRabbit plans often fail; prefer --dir <path> (separate runs) or --light" >&2
fi

ARGS=(review --committed --base "$BASE" --agent)
if [[ "$UNCOMMITTED" -eq 1 ]]; then
  ARGS=(review --uncommitted --base "$BASE" --agent)
fi
if [[ "$LIGHT" -eq 1 ]]; then
  ARGS+=(--light)
fi
if [[ -n "$DIR" ]]; then
  ARGS+=(--dir "$DIR")
fi

echo "cmd:     coderabbit ${ARGS[*]}"
echo

set +e
coderabbit "${ARGS[@]}" 2>&1 | tee "$OUT"
PIPE_STATUSES=("${PIPESTATUS[@]}")
RC=${PIPE_STATUSES[0]}
if [[ ${PIPE_STATUSES[1]} -ne 0 ]]; then
  echo "error: failed to write review log: $OUT" >&2
  RC=${PIPE_STATUSES[1]}
fi
set -e

echo
echo "exit: $RC"
echo "log:  $OUT"

# Compact severity histogram if JSONL findings present
python3 - "$OUT" <<'PY' || true
import json, sys
from collections import Counter
path = sys.argv[1]
findings = []
complete = None
with open(path, encoding="utf-8", errors="replace") as f:
  for line in f:
    line = line.strip()
    if not line.startswith("{"):
      continue
    try:
      o = json.loads(line)
    except json.JSONDecodeError:
      continue
    if o.get("type") == "finding":
      findings.append(o)
    elif o.get("type") == "complete":
      complete = o
print(f"findings: {len(findings)}")
if findings:
  print("severity:", dict(Counter(x.get("severity") for x in findings)))
if complete:
  print("complete:", complete.get("status"), "findings=", complete.get("findings"))
PY

echo "$OUT"
exit "$RC"
