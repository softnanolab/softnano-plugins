# softnano-plugins

Shared plugin for the SoftNano lab. Provides reusable skills for HPC job management, code review, literature search, and more — usable from either [Claude Code](https://claude.com/claude-code) or [Codex](https://developers.openai.com/codex). The shared plugin payload lives under `plugins/softnano/`, and both CLIs read the same `plugins/softnano/skills/` directory.

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
claude --plugin-dir /path/to/softnano-plugins/plugins/softnano
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

- The same `plugins/softnano/skills/` directory is loaded by both CLIs — no duplication.
- Claude-only frontmatter fields (`argument-hint`) are silently ignored by Codex.
- `allowed-tools`, `user-invocable`, and `disable-model-invocation` are recognised by both CLIs.
- The plugin is named `softnano` even though the repo is `softnano-plugins`. Both marketplace manifests point at `./plugins/softnano`, where the Claude and Codex plugin manifests live.

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

### `/softnano:notion-upload`

Upload local image files to a Notion page. Uses the Notion File Upload REST API to embed PNGs, JPGs, and other images directly into a page.

```
/softnano:notion-upload <notion_page_url_or_id> <file_path(s) or glob pattern>
```

**What it does:**
1. Resolves file paths (supports glob patterns like `figures/*.png`)
2. Uploads each image via the Notion File Upload API (3-step process)
3. Appends all images as blocks to the Notion page with auto-generated captions
4. Reports upload results and any failures

**Prerequisites:** `NOTION_API_TOKEN` in your project `.env` file or as an environment variable. Create an integration at https://www.notion.so/profile/integrations and share the target page with it.

## Reference Docs

## Project Structure

```
softnano-plugins/
├── .claude-plugin/
│   └── marketplace.json     # Claude Code marketplace manifest
├── .agents/plugins/
│   └── marketplace.json     # Codex marketplace manifest
├── plugins/
│   └── softnano/
│       ├── .claude-plugin/
│       │   └── plugin.json  # Claude Code plugin manifest
│       ├── .codex-plugin/
│       │   └── plugin.json  # Codex plugin manifest
│       └── skills/          # Shared — both CLIs read from here
│           ├── codex/SKILL.md
│           ├── monitor-jobs/SKILL.md
│           ├── code-review/SKILL.md
│           ├── edison/
│           │   ├── SKILL.md
│           │   └── scripts/edison_query.sh
│           ├── cluster-instructions/
│           │   ├── SKILL.md
│           │   ├── cx3.md
│           │   └── isambard.md
│           ├── doi2bib/SKILL.md
│           ├── grill-me/SKILL.md
│           └── notion-upload/SKILL.md
└── .gitignore
```

## Adding New Skills

Create `plugins/softnano/skills/<skill-name>/SKILL.md` with frontmatter:

```yaml
---
name: my-skill
description: What the skill does
argument-hint: "<expected arguments>"
allowed-tools: Bash, Read, Grep, Glob, Write
---
```

Omit `argument-hint` if the skill takes no arguments (see `grill-me`). Then bump `version` in **both** `plugins/softnano/.claude-plugin/plugin.json` and `plugins/softnano/.codex-plugin/plugin.json` (keep them in sync) and push.
