#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SOURCE_SKILLS="$REPO_ROOT/skills"
CODEX_SKILLS="$REPO_ROOT/plugins/softnano/skills"

if [ -e "$CODEX_SKILLS/codex" ]; then
    echo "Codex skill tree must not contain skills/codex; use skills/claude instead." >&2
    exit 1
fi

if [ ! -f "$CODEX_SKILLS/claude/SKILL.md" ]; then
    echo "Codex skill tree is missing the Codex-only claude skill." >&2
    exit 1
fi

diff -ru \
    --exclude 'codex' \
    --exclude 'claude' \
    "$SOURCE_SKILLS" \
    "$CODEX_SKILLS"

python3 - "$REPO_ROOT" <<'PY'
import json
import sys
from pathlib import Path

repo = Path(sys.argv[1])
claude = json.loads((repo / ".claude-plugin" / "plugin.json").read_text())
codex = json.loads((repo / "plugins" / "softnano" / ".codex-plugin" / "plugin.json").read_text())

if claude["version"] != codex["version"]:
    raise SystemExit(
        "manifest versions differ: "
        f".claude-plugin={claude['version']} "
        f"plugins/softnano/.codex-plugin={codex['version']}"
    )
PY

echo "Codex skill tree is synchronized."
