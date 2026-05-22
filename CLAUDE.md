# softnano-plugins

Shared Claude Code / Codex skills for the SoftNano lab.

## Release workflow — required for every new feature

Whenever a PR adds, replaces, or meaningfully changes a skill (anything user-visible — new skill, new behavior, breaking change to an existing skill), it MUST also:

1. **Bump the version** in both plugin manifests, kept in lockstep:
   - `.claude-plugin/plugin.json`
   - `.codex-plugin/plugin.json`

   Use semver against the current value:
   - Patch (`0.x.y` → `0.x.(y+1)`): docs, internal refactors, bug fixes inside an existing skill.
   - Minor (`0.x.y` → `0.(x+1).0`): new skill, new user-facing capability, or replacement of an existing skill.
   - Major (`x.y.z` → `(x+1).0.0`): breaking change to skill names, invocation, or expected inputs.

2. **Cut a GitHub release** matching the new version once the PR is merged to `main`:

   ```
   gh release create vX.Y.Z --target <merge-commit-sha> --title "vX.Y.Z" --generate-notes
   ```

   The release tag must equal the version in `plugin.json` prefixed with `v` (e.g. `0.8.0` → `v0.8.0`). Auto-generated notes are the default — only hand-write notes if there is something the PR list does not convey.

If you open a feature PR without the version bump, add the bump as a follow-up commit on the same branch before merging — do not let `main` drift ahead of the last release tag.
