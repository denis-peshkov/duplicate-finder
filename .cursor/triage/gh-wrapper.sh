#!/usr/bin/env bash
# GitHub CLI wrapper for triage scripts (consistent entry point for local and CI).
set -euo pipefail

exec gh "$@"
