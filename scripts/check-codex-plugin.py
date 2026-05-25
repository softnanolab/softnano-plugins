#!/usr/bin/env python3
"""Validate the Codex plugin packaging invariants for CI."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CODEX_PLUGIN_ROOT = REPO_ROOT / "plugins" / "softnano"
CODEX_SKILLS = CODEX_PLUGIN_ROOT / "skills"
ROOT_SKILLS = REPO_ROOT / "skills"


failures: list[str] = []


def display_path(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        failures.append(f"missing JSON file: {display_path(path)}")
        return {}
    except json.JSONDecodeError as exc:
        failures.append(f"invalid JSON in {display_path(path)}: {exc}")
        return {}

    if not isinstance(value, dict):
        failures.append(f"{display_path(path)} must contain a JSON object")
        return {}

    return value


def load_frontmatter(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        failures.append(f"missing skill file: {display_path(path)}")
        return {}

    if not lines or lines[0] != "---":
        failures.append(f"{display_path(path)} must start with YAML frontmatter")
        return {}

    try:
        end = lines.index("---", 1)
    except ValueError:
        failures.append(f"{display_path(path)} frontmatter is not closed")
        return {}

    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()

    return metadata


def immediate_skill_dirs(path: Path) -> set[str]:
    if not path.is_dir():
        failures.append(f"missing skill directory: {display_path(path)}")
        return set()

    return {entry.name for entry in path.iterdir() if entry.is_dir()}


def validate_marketplace() -> None:
    marketplace = load_json(REPO_ROOT / ".agents" / "plugins" / "marketplace.json")
    check(marketplace.get("name") == "softnanolab-plugins", "Codex marketplace name must be softnanolab-plugins")

    plugins = marketplace.get("plugins")
    check(isinstance(plugins, list) and len(plugins) == 1, "Codex marketplace must expose exactly one plugin")
    if not isinstance(plugins, list) or not plugins:
        return

    plugin = plugins[0]
    check(isinstance(plugin, dict), "Codex marketplace plugin entry must be an object")
    if not isinstance(plugin, dict):
        return

    source = plugin.get("source")
    check(isinstance(source, dict), "Codex marketplace plugin source must be an object")
    if isinstance(source, dict):
        check(source.get("source") == "local", "Codex marketplace source must be local")
        check(source.get("path") == "./plugins/softnano", "Codex marketplace path must be ./plugins/softnano")


def validate_manifests() -> None:
    claude = load_json(REPO_ROOT / ".claude-plugin" / "plugin.json")
    codex = load_json(CODEX_PLUGIN_ROOT / ".codex-plugin" / "plugin.json")

    check(claude.get("name") == "softnano", "Claude plugin name must be softnano")
    check(codex.get("name") == "softnano", "Codex plugin name must be softnano")
    check(claude.get("version") == codex.get("version"), "Claude and Codex plugin versions must match")
    check(codex.get("skills") == "./skills/", "Codex manifest skills path must be ./skills/")

    interface = codex.get("interface")
    check(isinstance(interface, dict), "Codex manifest must include interface metadata")
    if isinstance(interface, dict):
        check(bool(interface.get("displayName")), "Codex interface.displayName is required")
        check(bool(interface.get("shortDescription")), "Codex interface.shortDescription is required")
        check(bool(interface.get("defaultPrompt")), "Codex interface.defaultPrompt is required")


def validate_skill_layout() -> None:
    root_dirs = immediate_skill_dirs(ROOT_SKILLS)
    codex_dirs = immediate_skill_dirs(CODEX_SKILLS)

    check("codex" in root_dirs, "root skills tree must contain the Claude-only codex skill")
    check("claude" not in root_dirs, "root skills tree must not contain the Codex-only claude skill")
    check("claude" in codex_dirs, "Codex skill tree must contain the Codex-only claude skill")
    check("codex" not in codex_dirs, "Codex skill tree must not contain the Claude-only codex skill")

    shared_root_dirs = root_dirs - {"codex"}
    shared_codex_dirs = codex_dirs - {"claude"}
    check(
        shared_root_dirs == shared_codex_dirs,
        "shared skill directories differ between skills/ and plugins/softnano/skills/",
    )

    for skill_dir in sorted(CODEX_SKILLS.iterdir()):
        if not skill_dir.is_dir():
            continue

        skill_file = skill_dir / "SKILL.md"
        metadata = load_frontmatter(skill_file)

        check(metadata.get("name") == skill_dir.name, f"{display_path(skill_file)} name must match its directory")
        check(bool(metadata.get("description")), f"{display_path(skill_file)} must have a description")

        forbidden_keys = {"disable-model-invocation", "disable_model_invocation"}
        present_forbidden = forbidden_keys & set(metadata)
        check(
            not present_forbidden,
            f"{display_path(skill_file)} must not use disable-model-invocation; Codex rejects it",
        )


def main() -> int:
    validate_marketplace()
    validate_manifests()
    validate_skill_layout()

    if failures:
        print("Codex plugin validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Codex plugin metadata is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
