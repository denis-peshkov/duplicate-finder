#!/usr/bin/env bash
# Collect branch delta vs a base ref for RELEASE-PLAN drafting.
# Usage:
#   bash .cursor/skills/release-plan/scripts/collect-release-delta.sh \
#     [--base origin/master] [--version 2.2.0] [--out PATH] \
#     [--focus PATH]... [--no-default-focus]
#
# Version defaults from resolve-target-version.sh (GitVersion); optional --version overrides.
# By default appends diff for docs/BREAKING.md. Extra hot paths — repeatable --focus.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
cd "$ROOT"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib/repository-link.sh
source "$SCRIPT_DIR/lib/repository-link.sh"

BASE="origin/master"
VERSION=""
OUT=""
NO_DEFAULT_FOCUS=false
FOCUS=()

require_value() {
  local flag="$1"
  local value="${2-}"
  if [[ -z "$value" || "$value" == -* ]]; then
    echo "error: $flag requires a non-option value" >&2
    exit 1
  fi
}

append_unique() {
  local path="$1"
  local existing
  if ((${#FOCUS[@]} > 0)); then
    for existing in "${FOCUS[@]}"; do
      if [[ "$existing" == "$path" ]]; then
        return 0
      fi
    done
  fi
  FOCUS+=("$path")
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base)
      require_value "$1" "${2-}"
      BASE="$2"
      shift 2
      ;;
    --version)
      require_value "$1" "${2-}"
      VERSION="$2"
      shift 2
      ;;
    --out)
      require_value "$1" "${2-}"
      OUT="$2"
      shift 2
      ;;
    --focus)
      require_value "$1" "${2-}"
      append_unique "$2"
      shift 2
      ;;
    --no-default-focus)
      NO_DEFAULT_FOCUS=true
      shift
      ;;
    -h|--help)
      sed -n '2,9p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 1
      ;;
  esac
done

if [[ "$NO_DEFAULT_FOCUS" != true ]]; then
  append_unique "docs/BREAKING.md"
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
DATE="$(date +%Y-%m-%d)"
REPOSITORY_LINK="$(repository_link "$(git remote get-url origin 2>/dev/null || true)")"
if [[ -z "$VERSION" ]]; then
  VERSION="$("$SCRIPT_DIR/resolve-target-version.sh" --base "$BASE" --json | python3 -c 'import json,sys; print(json.load(sys.stdin).get("target_version") or "")')"
fi
if [[ -z "$VERSION" ]]; then
  echo "error: could not resolve target_version (GitVersion or --version)" >&2
  exit 1
fi
CACHE_DIR="$ROOT/.cursor/skills/release-plan/.cache"
mkdir -p "$CACHE_DIR"
SAFE_BRANCH="${BRANCH//\//-}"
if [[ -z "$OUT" ]]; then
  OUT="$CACHE_DIR/delta-${VERSION}-${SAFE_BRANCH}.md"
fi

MB="$(git merge-base "$BASE" HEAD)"
COMMITS="$(git rev-list --count "${BASE}..HEAD")"
FILES="$(git diff --name-only "${BASE}...HEAD" | wc -l | tr -d ' ')"

{
  echo "# Release delta cache"
  echo
  echo "- **version:** $VERSION"
  echo "- **repository_link:** $REPOSITORY_LINK"
  echo "- **branch:** \`$BRANCH\`"
  echo "- **base:** \`$BASE\`"
  echo "- **merge-base:** \`$MB\`"
  echo "- **date:** $DATE"
  echo "- **commits:** $COMMITS · **files:** $FILES"
  echo
  echo "## Commits (\`${BASE}..HEAD\`)"
  echo
  echo '```'
  git log --oneline "${BASE}..HEAD"
  echo '```'
  echo
  echo "## Diffstat"
  echo
  echo '```'
  git diff --stat "${BASE}...HEAD"
  echo '```'
  echo
  echo "## Name-status"
  echo
  echo '```'
  git diff --name-status "${BASE}...HEAD"
  echo '```'

  if ((${#FOCUS[@]} > 0)); then
    for focus_path in "${FOCUS[@]}"; do
      echo
      echo "## Focus: \`$focus_path\`"
      echo
      echo '```diff'
      git diff "${BASE}...HEAD" -- "$focus_path" 2>/dev/null || true
      echo '```'
    done
  fi
} > "$OUT"

echo "$OUT"
