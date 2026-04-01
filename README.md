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

### `/softnano:cluster-instructions`

Detect which HPC cluster you are on and load the correct job submission instructions. Covers CX3 (PBS Pro) and Isambard (SLURM).

```
/softnano:cluster-instructions [command-to-run]
```

**What it does:**
1. Detects the cluster from `pwd` and available scheduler commands
2. Checks if you are on a login node or compute node
3. Loads cluster-specific instructions (queues, templates, storage paths)
4. Submits the command via the correct scheduler, or reports the detected environment

Includes full reference docs for CX3 (PBS Pro) and Isambard (SLURM) with job templates, queue tables, and common commands.

### `/softnano:codex`

Get a second opinion from OpenAI Codex CLI (GPT-5.4). Cross-check reasoning, validate plans, or get an independent code review.

```
/softnano:codex <task or question>
```

**What it does:**
1. Reads relevant files to build context
2. Constructs an unbiased prompt (no leading conclusions)
3. Runs Codex in read-only mode via `codex exec --full-auto`
4. Reports the Codex response and notes agreements/disagreements
5. Lets you decide how to proceed

### `/softnano:code-review`

Review Python code against SoftNano style conventions. Checks docstrings, type annotations, tensor shape documentation, and commented-out code.

```
/softnano:code-review [file-or-directory]
```

**What it does:**
1. Identifies files to review (from argument, recent git diff, or staged files)
2. Runs `ruff` lint/format checks if available
3. Manual checks against SoftNano conventions:
   - Google-style docstrings with `Args:`, `Returns:`
   - Tensor shape documentation (`Expected Shape:`)
   - Python 3.12+ type annotations (`x | None`, `list[int]`)
   - Commented-out code has `# TODO: review` + `# ----` markers
4. Reports findings by category and severity
5. Offers to apply style-only fixes (no logic changes)

If no file is given, it reviews staged or recently changed Python files.

### `/softnano:edison`

Conduct scientific literature research using Edison's autonomous search API. Edison searches hundreds of papers with full-text analysis and returns a cited answer.

```
/softnano:edison <research question>
```

**What it does:**
1. Submits the research question to Edison's literature search API
2. Waits for the result (typically 1–5 minutes)
3. Reports the cited answer verbatim

Supports follow-up queries via `--continue-from <task_id>` to build on previous searches.

**Prerequisites:** `EDISON_PLATFORM_API_KEY` in `~/.claude/settings.json` under `"env"`, and `jq` installed.

## Project Structure

```
softnano-plugins/
├── .claude-plugin/
│   ├── plugin.json          # Plugin manifest
│   └── marketplace.json     # Marketplace manifest
├── skills/
│   ├── cluster-instructions/
│   │   ├── SKILL.md         # HPC detection & job submission
│   │   ├── cx3.md           # Imperial PBS Pro reference
│   │   └── isambard.md      # Isambard SLURM reference
│   ├── code-review/
│   │   └── SKILL.md
│   ├── codex/
│   │   └── SKILL.md
│   ├── edison/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── edison_query.sh
│   └── monitor-jobs/
│       └── SKILL.md
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
