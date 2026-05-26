#!/usr/bin/env python3
"""Validate the Claude and Codex plugin packaging invariants for CI."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CODEX_PLUGIN_ROOT = REPO_ROOT / "plugins" / "softnano"
CODEX_SKILLS = CODEX_PLUGIN_ROOT / "skills"
ROOT_SKILLS = REPO_ROOT / "skills"


failures: list[str] = []
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
CODEX_INSTALLATION_POLICIES = {"AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"}
CODEX_AUTHENTICATION_POLICIES = {"ON_INSTALL", "ON_USE"}
CODEX_COMPONENT_PATH_FIELDS = {"skills", "mcpServers", "apps", "hooks"}
FORBIDDEN_COMPATIBILITY_KEYS = {"disable-model-invocation", "disable_model_invocation"}


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
        # Intentional minimal parser: this validator only needs simple key/value frontmatter.
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()

    return metadata


def immediate_skill_dirs(path: Path) -> set[str]:
    if not path.is_dir():
        failures.append(f"missing skill directory: {display_path(path)}")
        return set()

    return {entry.name for entry in path.iterdir() if entry.is_dir()}


def check_component_path(manifest: dict[str, Any], field: str, manifest_path: Path, plugin_root: Path) -> None:
    value = manifest.get(field)
    if value is None:
        return

    check(isinstance(value, str), f"{display_path(manifest_path)} {field} path must be a string")
    if not isinstance(value, str):
        return

    check(value.startswith("./"), f"{display_path(manifest_path)} {field} path must start with ./")

    resolved = (plugin_root / value).resolve()
    plugin_root = plugin_root.resolve()
    check(
        resolved == plugin_root or plugin_root in resolved.parents,
        f"{display_path(manifest_path)} {field} path must stay inside the plugin root",
    )


def validate_marketplaces() -> None:
    claude_marketplace = load_json(REPO_ROOT / ".claude-plugin" / "marketplace.json")
    check(
        claude_marketplace.get("name") == "softnanolab-plugins",
        "Claude marketplace name must be softnanolab-plugins",
    )
    check(bool(claude_marketplace.get("description")), "Claude marketplace description is required")

    claude_plugins = claude_marketplace.get("plugins")
    check(
        isinstance(claude_plugins, list) and len(claude_plugins) == 1,
        "Claude marketplace must expose exactly one plugin",
    )
    if isinstance(claude_plugins, list) and claude_plugins:
        claude_plugin = claude_plugins[0]
        check(isinstance(claude_plugin, dict), "Claude marketplace plugin entry must be an object")
        if isinstance(claude_plugin, dict):
            check(claude_plugin.get("name") == "softnano", "Claude marketplace plugin name must be softnano")
            check(claude_plugin.get("source") == "./", "Claude marketplace source must be ./")
            check(bool(claude_plugin.get("description")), "Claude marketplace plugin description is required")

    codex_marketplace = load_json(REPO_ROOT / ".agents" / "plugins" / "marketplace.json")
    check(
        codex_marketplace.get("name") == "softnanolab-plugins",
        "Codex marketplace name must be softnanolab-plugins",
    )

    plugins = codex_marketplace.get("plugins")
    check(isinstance(plugins, list) and len(plugins) == 1, "Codex marketplace must expose exactly one plugin")
    if not isinstance(plugins, list) or not plugins:
        return

    plugin = plugins[0]
    check(isinstance(plugin, dict), "Codex marketplace plugin entry must be an object")
    if not isinstance(plugin, dict):
        return

    check(plugin.get("name") == "softnano", "Codex marketplace plugin name must be softnano")

    source = plugin.get("source")
    check(isinstance(source, dict), "Codex marketplace plugin source must be an object")
    if isinstance(source, dict):
        check(source.get("source") == "local", "Codex marketplace source must be local")
        check(source.get("path") == "./plugins/softnano", "Codex marketplace path must be ./plugins/softnano")

    policy = plugin.get("policy")
    check(isinstance(policy, dict), "Codex marketplace plugin policy must be an object")
    if isinstance(policy, dict):
        check(
            policy.get("installation") in CODEX_INSTALLATION_POLICIES,
            f"Codex marketplace installation policy must be one of {sorted(CODEX_INSTALLATION_POLICIES)}",
        )
        check(
            policy.get("authentication") in CODEX_AUTHENTICATION_POLICIES,
            f"Codex marketplace authentication policy must be one of {sorted(CODEX_AUTHENTICATION_POLICIES)}",
        )

    check(bool(plugin.get("category")), "Codex marketplace plugin category is required")


def validate_manifests() -> None:
    claude_path = REPO_ROOT / ".claude-plugin" / "plugin.json"
    codex_path = CODEX_PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
    claude = load_json(claude_path)
    codex = load_json(codex_path)

    check(claude.get("name") == "softnano", "Claude plugin name must be softnano")
    check(codex.get("name") == "softnano", "Codex plugin name must be softnano")
    check(bool(claude.get("description")), "Claude plugin description is required")
    check(bool(codex.get("description")), "Codex plugin description is required")
    check(SEMVER_RE.fullmatch(str(claude.get("version", ""))) is not None, "Claude plugin version must be semver")
    check(SEMVER_RE.fullmatch(str(codex.get("version", ""))) is not None, "Codex plugin version must be semver")
    check(claude.get("version") == codex.get("version"), "Claude and Codex plugin versions must match")

    check("authors" not in claude, "Claude plugin manifest must use author, not ignored authors")
    claude_author = claude.get("author")
    check(isinstance(claude_author, dict) and bool(claude_author.get("name")), "Claude plugin author.name is required")

    codex_author = codex.get("author")
    check(isinstance(codex_author, dict) and bool(codex_author.get("name")), "Codex plugin author.name is required")

    check(codex.get("skills") == "./skills/", "Codex manifest skills path must be ./skills/")
    for field in CODEX_COMPONENT_PATH_FIELDS:
        check_component_path(codex, field, codex_path, CODEX_PLUGIN_ROOT)

    interface = codex.get("interface")
    check(isinstance(interface, dict), "Codex manifest must include interface metadata")
    if isinstance(interface, dict):
        check(bool(interface.get("displayName")), "Codex interface.displayName is required")
        check(bool(interface.get("shortDescription")), "Codex interface.shortDescription is required")
        check(bool(interface.get("longDescription")), "Codex interface.longDescription is required")
        check(interface.get("category") == "Productivity", "Codex interface.category must be Productivity")
        capabilities = interface.get("capabilities")
        check(
            isinstance(capabilities, list)
            and bool(capabilities)
            and all(isinstance(item, str) and item for item in capabilities),
            "Codex interface.capabilities must be a non-empty string list",
        )
        check(bool(interface.get("defaultPrompt")), "Codex interface.defaultPrompt is required")


def validate_skill_metadata(skill_dirs: set[str], skill_root: Path) -> None:
    for skill_name in sorted(skill_dirs):
        skill_file = skill_root / skill_name / "SKILL.md"
        metadata = load_frontmatter(skill_file)

        check(metadata.get("name") == skill_name, f"{display_path(skill_file)} name must match its directory")
        check(bool(metadata.get("description")), f"{display_path(skill_file)} must have a description")

        if "allowed-tools" in metadata:
            allowed_tools = metadata["allowed-tools"]
            check(bool(allowed_tools), f"{display_path(skill_file)} allowed-tools must not be empty")
            check(
                "," not in allowed_tools,
                f"{display_path(skill_file)} allowed-tools must use documented space-separated syntax",
            )

        present_forbidden = FORBIDDEN_COMPATIBILITY_KEYS & set(metadata)
        check(
            not present_forbidden,
            f"{display_path(skill_file)} must not use {sorted(present_forbidden)}; "
            "these keys break cross-agent compatibility",
        )


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

    validate_skill_metadata(root_dirs, ROOT_SKILLS)
    validate_skill_metadata(codex_dirs, CODEX_SKILLS)


def main() -> int:
    validate_marketplaces()
    validate_manifests()
    validate_skill_layout()

    if failures:
        print("Plugin validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print("Claude and Codex plugin metadata is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
