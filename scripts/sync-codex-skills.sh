#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SOURCE_SKILLS="$REPO_ROOT/skills"
CODEX_SKILLS="$REPO_ROOT/plugins/softnano/skills"

mkdir -p "$CODEX_SKILLS"

# The cross-agent helper intentionally differs by host:
# - Claude Code root tree: skills/codex/
# - Codex plugin tree: plugins/softnano/skills/claude/
rm -rf "$CODEX_SKILLS/codex"
rsync -a --delete \
    --exclude 'codex/' \
    --exclude 'claude/' \
    "$SOURCE_SKILLS/" \
    "$CODEX_SKILLS/"
