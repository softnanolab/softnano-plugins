# softnano-plugins

Shared plugin for the SoftNano lab. Provides reusable skills for HPC job management, code review, literature search, and more — usable from either [Claude Code](https://claude.com/claude-code) or [Codex](https://developers.openai.com/codex). Skills live in a single `skills/` directory that both CLIs read.

## Install

### Claude Code

From within a Claude Code session:

```
/plugin marketplace add softnanolab/softnano-plugins
/plugin install softnano@softnanolab-plugins
```

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

Invoke skills as `/softnano:<skill-name>` — e.g. `/softnano:monitor-jobs`, `/softnano:codex "review plan X"`.

To test locally without installing:

```bash
claude --plugin-dir /path/to/softnano-plugins
```

### Codex

Requires Codex **0.122.0** or newer (`brew upgrade codex` / `npm install -g @openai/codex`).

```bash
codex plugin marketplace add softnanolab/softnano-plugins
```

Then run `/plugins` inside a Codex session, select **softnano**, and install. Invoke skills with `$softnano <skill-name>` — e.g. `$softnano monitor-jobs`, `$softnano codex "review plan X"` — or pick them from the `/skills` menu.

To update or remove:

```bash
codex plugin marketplace upgrade softnanolab-plugins
codex plugin marketplace remove softnanolab-plugins
```

Codex-specific notes:

- The same `skills/` directory is loaded by both CLIs — no duplication.
- Claude-only frontmatter fields (`argument-hint`) are silently ignored by Codex.
- `allowed-tools`, `user-invocable`, and `disable-model-invocation` are recognised by both CLIs.
- The plugin is named `softnano` even though the repo is `softnano-plugins`. Codex resolves the plugin name from `.codex-plugin/plugin.json`, not the directory, so a flat layout at the repo root works correctly.

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
1. Loads the style guide from `docs/code_style.md`
2. Identifies files to review (from argument, recent git diff, or staged files)
3. Runs `ruff` lint/format checks if available
4. Manual checks against SoftNano conventions:
   - Google-style docstrings with `Args:`, `Returns:`
   - Tensor shape documentation (`Expected Shape:`)
   - Python 3.12+ type annotations (`x | None`, `list[int]`)
   - Commented-out code has `# TODO: review` + `# ----` markers
5. Reports findings by category and severity
6. Offers to apply style-only fixes (no logic changes)

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

### `/softnano:doi2bib`

Fetch a BibTeX entry for a given DOI via doi.org content negotiation.

```
/softnano:doi2bib <doi>
```

**What it does:**
1. Accepts a bare DOI or full `https://doi.org/...` URL
2. Runs `curl -LH "Accept: text/bibliography; style=bibtex" https://doi.org/<DOI>`
3. Returns the BibTeX entry verbatim in a code block, ready to paste into a `.bib` file

### `/softnano:grill-me`

Stress-test a plan or design by having the agent interview you relentlessly, walking every branch of the decision tree until there's shared understanding.

```
/softnano:grill-me
```

**What it does:**
1. Asks one focused question at a time
2. Recommends an answer for each question
3. Resolves dependencies between decisions before moving on
4. Explores the codebase itself when a question is answerable that way

## Reference Docs

| File | Description |
|------|-------------|
| `docs/slurm.md` | SLURM reference for Isambard (job templates, commands, key patterns) |
| `docs/cx3.md` | PBS Pro reference for Imperial CX3 (queues, job templates, commands) |
| `docs/code_style.md` | Python code style guide (docstrings, type annotations, tensor shapes) |

These are referenced by the skills for scheduler-specific details.

## Project Structure

```
softnano-plugins/
├── .claude-plugin/
│   ├── plugin.json          # Claude Code plugin manifest
│   └── marketplace.json     # Claude Code marketplace manifest
├── .codex-plugin/
│   └── plugin.json          # Codex plugin manifest
├── .agents/plugins/
│   └── marketplace.json     # Codex marketplace manifest
├── skills/                  # Shared — both CLIs read from here
│   ├── codex/SKILL.md
│   ├── monitor-jobs/SKILL.md
│   ├── code-review/SKILL.md
│   ├── edison/
│   │   ├── SKILL.md
│   │   └── scripts/edison_query.sh
│   ├── doi2bib/SKILL.md
│   └── grill-me/SKILL.md
├── docs/
│   ├── slurm.md             # Isambard SLURM reference
│   ├── cx3.md               # Imperial PBS Pro reference
│   └── code_style.md        # Python code style guide
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

Omit `argument-hint` if the skill takes no arguments (see `grill-me`). Then bump `version` in **both** `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` (keep them in sync) and push.
