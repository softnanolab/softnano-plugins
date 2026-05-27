# softnano-plugins

Shared Claude Code / Codex skills for the SoftNano lab.

## Release workflow — required for every new feature

Whenever a PR adds, replaces, or meaningfully changes a skill (anything user-visible — new skill, new behavior, polish to an existing skill, breaking change), it MUST also:

1. **Bump the version** in both plugin manifests, kept in lockstep:
   - `.claude-plugin/plugin.json`
   - `plugins/softnano/.codex-plugin/plugin.json`

   Bump rule against the current value `X.Y.Z`. The third component is always `0` — it is never incremented.
   - **Polish to an existing skill** (docs, behavior tweaks, bug fixes, internal refactors, new user-facing capability inside an existing skill): bump the middle component → `X.Y.0` → `X.(Y+1).0`. Example: `1.0.0` → `1.1.0`.
   - **New skill added** (a new skill directory shipped under `skills/`): bump the leading component and reset the middle to `0` → `X.Y.0` → `(X+1).0.0`. Example: `1.3.0` → `2.0.0`.

   Either kind of bump REQUIRES a matching GitHub release (see step 2). There is no "skip the release" path — if you bumped the version, you must tag it.

2. **Cut a GitHub release** matching the new version once the PR is merged to `main`:

   ```
   gh release create vX.Y.Z --target <merge-commit-sha> --title "vX.Y.Z" --generate-notes
   ```

   The release tag must equal the version in `plugin.json` prefixed with `v` (e.g. `0.8.0` → `v0.8.0`). Auto-generated notes are the default — only hand-write notes if there is something the PR list does not convey.

If you open a feature PR without the version bump, add the bump as a follow-up commit on the same branch before merging — do not let `main` drift ahead of the last release tag.

## Codex skill tree sync

Claude Code reads the root `skills/` tree. Codex reads `plugins/softnano/skills/` through `.agents/plugins/marketplace.json`.

When editing a shared skill, run:

```
scripts/sync-codex-skills.sh
scripts/check-codex-skill-sync.sh
python3 scripts/check-codex-plugin.py
```

The Codex tree intentionally keeps `plugins/softnano/skills/claude/` as a Codex-only replacement for root `skills/codex/`.
CI runs the same checks on pull requests and on pushes to `main`.
