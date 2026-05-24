# softnano-plugins

Shared plugin for the SoftNano lab. Provides reusable skills for HPC job management, code review, literature search, and more — usable from either [Claude Code](https://claude.com/claude-code) or [Codex](https://developers.openai.com/codex).

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

Then run `/plugins` inside a Codex session, select **softnano**, and install. Invoke skills with `$softnano <skill-name>` — e.g. `$softnano monitor-jobs`, `$softnano claude "review plan X"` — or pick them from the `/skills` menu.

To update or remove:

```bash
codex plugin marketplace upgrade softnanolab-plugins
codex plugin marketplace remove softnanolab-plugins
```

Codex-specific notes:

- Claude Code reads the root plugin; Codex reads the marketplace entry at `plugins/softnano`.
- Keep `skills/` and `plugins/softnano/skills/` synchronized with `scripts/sync-codex-skills.sh`; verify with `scripts/check-codex-skill-sync.sh` and `python3 scripts/check-codex-plugin.py`. CI runs these checks on pull requests.
- The cross-agent helper intentionally differs: Claude Code exposes `/softnano:codex`; Codex exposes `$softnano claude`.
- Claude-only frontmatter fields (`argument-hint`) are silently ignored by Codex.
- `allowed-tools` and `user-invocable` are recognised by both CLIs. Avoid `disable-model-invocation` in Codex-packaged skills; the Codex plugin validator rejects it.
- The plugin is named `softnano` even though the repo is `softnano-plugins`. Codex resolves the plugin name from `plugins/softnano/.codex-plugin/plugin.json`; the marketplace path must be non-empty.

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

Detect which HPC cluster you are on and load the correct job submission instructions. Covers CX3/HX1 (PBS Pro), Isambard (SLURM), new MMM Young NG (SLURM), and old MMM Young (SGE).

```
/softnano:cluster-instructions [command-to-run]
```

**What it does:**
1. Detects the cluster from host/path and available scheduler commands
2. Checks if you are on a login node or compute node
3. Loads cluster-specific instructions (queues, templates, storage paths)
4. Submits the command via the correct scheduler, or reports the detected environment

Includes full reference docs for CX3/HX1 (PBS Pro), Isambard (SLURM), MMM Young NG (SLURM/A100), and MMM old Young (SGE) with job templates, queue tables, and common commands. `softnanolab-campus` is treated as a workstation/gateway host: it may expose SLURM commands, but it is not the MMM/HPC cluster target, so the skill instructs agents to SSH onward instead of treating campus-local scheduler commands as authoritative.

### `/softnano:codex` (Claude Code)

Get a second opinion from OpenAI Codex CLI. Cross-check reasoning, validate plans, or get an independent code review.

```
/softnano:codex <task or question>
```

**What it does:**
1. Reads relevant files to build context
2. Constructs an unbiased prompt (no leading conclusions)
3. Runs Codex in read-only mode via `codex exec --full-auto`
4. Reports the Codex response and notes agreements/disagreements
5. Lets you decide how to proceed

### `$softnano claude` (Codex)

Get a second opinion from Claude Code while working in Codex. Cross-check reasoning, validate plans, or get an independent code review from Claude.

```
$softnano claude <task or question>
```

**What it does:**
1. Reads relevant files to build context
2. Constructs an unbiased prompt (no leading conclusions)
3. Runs Claude in non-interactive mode via `claude -p`
4. Uses read-only Claude tools by default (`Read`, `Grep`, `Glob`, `LS`)
5. Reports the Claude response and notes agreements/disagreements

### `/softnano:thermo-nuclear-code-quality-review`

An extremely strict maintainability review focused on abstraction quality, giant files, and spaghetti-condition growth. Adapted from Cursor.

**What it does:**
1. Performs a deep code-quality audit of the current branch's changes
2. Hunts for "code judo" moves — restructurings that preserve behavior while making the implementation dramatically simpler
3. Flags PRs that push files past 1000 lines, add ad-hoc branching to unrelated flows, leak feature logic into shared paths, or introduce unnecessary wrappers / casts / optionality
4. Prefers deleting complexity over rearranging it; pushes for canonical helpers and explicit type boundaries
5. Prioritizes a small number of high-conviction structural findings over cosmetic nits

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

**Prerequisites:** `EDISON_PLATFORM_API_KEY` in the agent environment, and `jq` installed. Claude Code users can set it in `~/.claude/settings.json` under `"env"`; Codex users can set it in their shell or project environment.

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

### `/softnano:open-pr`

Open a GitHub pull request with an auto-generated, deeply-reviewed summary.

```
/softnano:open-pr [base-branch] [--draft]
```

**What it does:**
1. Fetches `origin/<base-branch>` (default `main`) and diffs against it
2. Runs `pre-commit` and `pytest` as the quality gate — never on a login node; uses `cluster-instructions` to submit a job when on HPC
3. Spawns 1–2 review subagents in parallel, each with a distinct lens (correctness, API, tests, security, performance)
4. Composes a PR body containing the change summary, gate results, verbatim reviewer notes, and a test plan
5. Pushes the branch and opens the PR via `gh pr create`, returning the URL

Refuses to open the PR if the gate fails or the diff is empty. Uses `--draft` automatically if any reviewer flags a blocker.

### `/softnano:polish-pr`

Follow-up pass on an open PR: address Codex review comments, re-run the thermo-nuclear review, sync with the base branch, and push the updates.

```
/softnano:polish-pr [pr-number] [--base <branch>] [--no-rebase]
```

**What it does:**
1. Resolves the PR for the current branch (or the given number) and pulls open review threads via the GitHub GraphQL API
2. For each unresolved Codex thread: reads the code, applies a minimal fix, replies on the thread, and marks it resolved
3. Re-runs `/softnano:thermo-nuclear-code-quality-review` against the resulting diff and addresses blocker/should-fix findings
4. Fetches the base branch and rebases (or merges, if requested) when new commits have landed
5. Pushes the updated branch (`--force-with-lease` only when a rebase rewrote history) and reports what was resolved, skipped, or escalated

Never auto-resolves human reviewer threads, never force-pushes without `--force-with-lease`, and stops on rebase conflicts so the user can resolve them.

### `/softnano:cleanup`

Post-merge teardown for a feature branch and its worktree.

```
/softnano:cleanup [pr-number]
```

**What it does:**
1. Verifies via `gh pr view` that the PR is actually `MERGED` — refuses otherwise
2. Deletes the remote feature branch (no-ops if GitHub already auto-deleted it; skipped for fork PRs)
3. Removes the current git worktree using `ExitWorktree` (or `git worktree remove` from the main worktree as a fallback) — never `rm -rf`
4. Safely deletes the local feature branch (`-d`; falls back to `-D` only after confirming the PR is merged, e.g. squash-merge cases)
5. Fast-forwards `main` in the main worktree and reports what was deleted

Refuses to delete `main`, refuses to operate on a dirty worktree without confirmation, and refuses to force-delete a branch without a verified-merged PR backing it.

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
│   ├── plugin.json          # Claude Code plugin manifest
│   └── marketplace.json     # Claude Code marketplace manifest
├── .agents/plugins/
│   └── marketplace.json     # Codex marketplace manifest
├── skills/                  # Claude Code skill tree
│   ├── codex/SKILL.md       # Claude Code cross-agent helper
│   ├── monitor-jobs/SKILL.md
│   ├── thermo-nuclear-code-quality-review/SKILL.md
│   ├── edison/
│   │   ├── SKILL.md
│   │   └── scripts/edison_query.sh
│   ├── cluster-instructions/
│   │   ├── SKILL.md
│   │   ├── cx3.md
│   │   ├── isambard.md
│   │   ├── mmm-sge.md
│   │   └── mmm-slurm.md
│   ├── doi2bib/SKILL.md
│   ├── grill-me/SKILL.md
│   ├── cleanup/SKILL.md
│   ├── notion-upload/SKILL.md
│   ├── open-pr/SKILL.md
│   └── polish-pr/SKILL.md
├── plugins/
│   └── softnano/            # Codex plugin root referenced by marketplace.json
│       ├── .codex-plugin/plugin.json
│       └── skills/          # Codex skill tree; uses claude/ instead of codex/
├── scripts/
│   ├── check-codex-skill-sync.sh
│   └── sync-codex-skills.sh
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

Omit `argument-hint` if the skill takes no arguments (see `grill-me`). Then run `scripts/sync-codex-skills.sh`, bump `version` in `.claude-plugin/plugin.json` and `plugins/softnano/.codex-plugin/plugin.json` (keep them in sync), run `scripts/check-codex-skill-sync.sh`, and push. Keep the cross-agent helper intentionally split: root `skills/codex/` is for Claude Code, while `plugins/softnano/skills/claude/` is for Codex.
