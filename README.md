# softnano-plugins

Shared [Claude Code](https://claude.com/claude-code) plugin for the SoftNano lab. Provides reusable skills for HPC job management across lab projects.

## Installation

From within a Claude Code session:

```
/plugin marketplace add softnanolab/softnano-plugins
```

Then install the plugin from the **Discover** tab in `/plugin`.

Or add directly to `~/.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "softnanolab-plugins": {
      "source": {
        "source": "github",
        "repo": "softnanolab/softnano-plugins"
      }
    }
  },
  "enabledPlugins": {
    "softnano@softnanolab-plugins": true
  }
}
```

To test locally without installing:

```bash
claude --plugin-dir /path/to/softnano-plugins
```

## Skills

### `/softnano:eval-jobs`

Submit and monitor SLURM/PBS evaluation jobs for W&B runs, then display interchain metric tables.

```
/softnano:eval-jobs <wandb_run_url(s) or project_url>
```

**What it does:**
1. Resolves the invoking project's root directory (via `.env` location)
2. Loads `LOGS_DIR`, `JOBS_DIR`, `WANDB_ENTITY` from `.env`
3. Checks for cached results before submitting
4. Generates and submits batch scripts (SLURM or PBS Pro, auto-detected)
5. Monitors jobs until completion
6. Parses `results.json` and displays inter-chain P@K, median P@K, and AUC tables

**Requirements in each project:**
- `.env` with `LOGS_DIR`, `JOBS_DIR`, `WANDB_ENTITY`
- `scripts/evals/evaluate_from_wandb.py`
- `.venv` with dependencies installed

### `/softnano:monitor-jobs`

Monitor SLURM/PBS jobs and their logs. Automatically detects running/pending jobs, tails logs, and reports errors.

```
/softnano:monitor-jobs [job-id]
```

**What it does:**
1. Auto-detects the HPC scheduler (SLURM or PBS Pro)
2. Lists active jobs or uses a provided job ID
3. Waits for pending jobs to start (polls automatically)
4. Tails logs and identifies errors, warnings, and training progress
5. Reports W&B run URLs, loss values, and training metrics
6. On errors: analyzes root cause and proposes fixes

If no job ID is given, it finds and monitors the user's active jobs.

## Reference Docs

| File | Description |
|------|-------------|
| `docs/slurm.md` | SLURM reference for Isambard (job templates, commands, key patterns) |
| `docs/cx3.md` | PBS Pro reference for Imperial CX3 (queues, job templates, commands) |

These are referenced by the skills for scheduler-specific details.

## Project Structure

```
softnano-plugins/
├── .claude-plugin/
│   ├── plugin.json          # Plugin manifest
│   └── marketplace.json     # Marketplace manifest
├── skills/
│   ├── eval-jobs/
│   │   └── SKILL.md
│   └── monitor-jobs/
│       └── SKILL.md
├── docs/
│   ├── slurm.md             # Isambard SLURM reference
│   └── cx3.md               # Imperial PBS Pro reference
└── .gitignore
```

## Adding New Skills

Create `skills/<skill-name>/SKILL.md` with frontmatter:

```yaml
---
name: my-skill
description: What the skill does
argument-hint: "<expected arguments>"
allowed-tools: Bash, Read, Grep, Glob, Write
---
```

Then bump `version` in `.claude-plugin/plugin.json` and push.
