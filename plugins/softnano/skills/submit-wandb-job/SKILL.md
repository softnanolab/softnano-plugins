---
name: submit-wandb-job
description: Submit one or more wandb-logged training/finetuning runs to the HPC scheduler. `WANDB_PROJECT` is fixed per repo (snake_case basename); `WANDB_RUN_GROUP` is picked per invocation. The training script must take the experiment/group name as a config key (e.g. Hydra `meta.experiment_name=<group>`); the skill passes it on the command line. The working tree is committed first so each run pins to a real SHA. Delegates SLURM/PBS templating to `cluster-instructions`. Use when the user asks to submit, queue, launch, or kick off a wandb training/finetuning job.
argument-hint: "[N (jobs, default 1)] [--group <name>] [--one-off] [--skip-commit-check]"
allowed-tools: Bash, Read, Grep, Glob, Write, Edit, Skill, AskUserQuestion
---

# Submit wandb Job

Enforces a wandb/commit contract on top of `cluster-instructions`. For training/finetuning runs that log to wandb — not eval-only jobs.

## Contract

| Env var | Value | Scope |
|---|---|---|
| `WANDB_PROJECT` | `.env: WANDB_PROJECT` or snake_case repo basename | constant per repo |
| `WANDB_RUN_GROUP` | user, per invocation (`tmp` for one-offs) | one per invocation |
| `WANDB_NAME` | `<group>__<tag>` | one per job |
| `WANDB_NOTES` | `commit: <SHA>` (+ `(dirty)` if not pinned) | one per invocation |

The skill exports these env vars in the job script. **The experiment/group name must be a config key in the training script** (e.g. Hydra `meta.experiment_name`, or whatever the project's equivalent is) — the user's command should include the override (e.g. `... meta.experiment_name=<group>`) so the training code receives the same value the skill sets in `WANDB_RUN_GROUP`. If the training script hardcodes the experiment name or the wandb project, that's a real bug in the project — surface it and ask the user to fix it; don't paper over it from this skill.

## Step 0 — Pre-flight

```bash
git rev-parse --show-toplevel    # → REPO_ROOT; bail if not a git repo
git status --porcelain           # → DIRTY (string)
```

Refuse on: not a git repo, or detached HEAD without explicit consent.

## Step 1 — Project (constant)

`.env: WANDB_PROJECT` if set, else snake_case of `basename $REPO_ROOT` (lowercase, `-` → `_`, strip non-`[a-z0-9_]`, collapse `_`). Show it to the user. If they override, write the override into `.env` so it stays constant next time.

## Step 2 — Group

In order:

1. **One-off** — if `--one-off` was passed, or the user said "one-off / throwaway / quick test / scratch / ad hoc": set `group = tmp`, no questions asked.
2. **Explicit** — `--group <name>` or a name in the conversation: use it.
3. **Suggest, then ask** — gather candidates from:
   - `$JOBS_DIR/*/` directories (prior groups from this skill).
   - Recent `LOGS_DIR/wandb/run-*/files/config.yaml` — grep `group:`, dedupe, cap at 10.
   - A fresh slug derived from a salient piece of the user's command (only if it actually hints at one).

   Present via `AskUserQuestion` with up to 3 existing groups + Other. If one is a strong semantic match for what the user is running ("another seed for the dropout sweep" + an existing `mlm_tune_dropout`), recommend it explicitly and ask whether that's where this belongs. If no candidates exist, ask freeform with a `tmp`-for-throwaway nudge.

Validate: `[A-Za-z0-9_.-]+`, non-empty, no whitespace. `tmp` is fine — don't gate it behind a "are you sure" prompt.

## Step 3 — Commit gate

If `DIRTY` is empty: capture `HEAD_SHA`, continue.

If `DIRTY` non-empty and `--skip-commit-check`: capture `HEAD_SHA`, set `commit_pinned=false`, continue (warn in the final report).

Otherwise show `git status --short` + `git diff --stat`, then ask **once** via `AskUserQuestion`:

- **Commit (recommended)** — `git add -u`, propose a one-liner from the diff, `git commit` (let hooks run; never `--no-verify`). Re-stage and retry once if hooks rewrite. Verify clean, then capture new `HEAD_SHA`.
- **Bypass** — `commit_pinned=false`. Report will flag it.
- **Cancel** — abort.

Don't include untracked files unless the user says so.

## Step 4 — Per-job details

Ask for `N` if not in `$ARGUMENTS` (default 1). For each job collect:

- **Command** — full invocation (user usually states it; ask if not). Skill is agnostic to Hydra/argparse/CLI shape — don't parse it, but do check that the command sets the experiment/group name as a config key (e.g. `meta.experiment_name=<group>`). If it doesn't, ask the user to add it before continuing — the `WANDB_RUN_GROUP` env var alone won't reach a Hydra config.
- **Tag** — short, used in `WANDB_NAME` and the script filename (`lr1e-3`, `seed42`). Default to `j<i>` or a salient `=value` from the command if the user omits one.

If `N > 1` and the user hasn't said how the jobs differ, ask — don't invent ablations.

## Step 5 — Cluster + paths

Invoke `cluster-instructions` (Skill tool) for scheduler detection and templates. Don't submit from this skill directly. Pick up `JOBS_DIR` from `.env` (fall back to `$REPO_ROOT/jobs`), `mkdir -p $JOBS_DIR/<project>/<group>/logs`. The `<project>` outer level matches `monitor-jobs`' documented `$JOBS_DIR/<project>/` layout; `<group>` nests inside so related runs cluster on disk too.

## Step 6 — Generate scripts

One script per job at `$JOBS_DIR/<project>/<group>/<group>__<tag>.{sh,batch}`. Use the scheduler header from `cluster-instructions`. Before the user's command:

```bash
export WANDB_PROJECT="<project>"
export WANDB_RUN_GROUP="<group>"
export WANDB_NAME="<group>__<tag>"
export WANDB_NOTES="commit: <HEAD_SHA>"   # append " (dirty)" if commit_pinned=false
cd "$REPO_ROOT"
```

Logs to `logs/<group>__<tag>.out` (PBS) or `logs/<group>__<tag>_%j.out` (SLURM), relative to the submission dir — matches `monitor-jobs` expectations.

Show the scripts (`cat`) and pause for confirmation if any of: `N > 3`, `commit_pinned=false`, or the command contains obviously destructive tokens (`rm `, `--force`). Otherwise just submit.

## Step 7 — Submit

`sbatch` / `qsub` per script. On any failure, stop — don't retry, don't continue to the next job. Capture job IDs.

## Step 8 — Report

```markdown
## Submitted <N> job(s) to <cluster>

- **project**: `<project>`   **group**: `<group>`
- **commit**: `<short-SHA>` — `<subject>`    <!-- or "dirty submit — not pinned" if commit_pinned=false -->
- **logs**: `<absolute path>`

| # | Job ID | Tag | Script | Log |
|---|---|---|---|---|

Monitor: `/softnano:monitor-jobs`.
```

Repeat the dirty-submit warning at the bottom if applicable.

## Hard rules

- Never auto-commit, never `--no-verify`, never edit the user's training code to fit the env contract.
- Never submit from a login node — `cluster-instructions` enforces this; don't work around it.
- Wandb auth is not this skill's problem — let the job fail at runtime if `WANDB_API_KEY` / `~/.netrc` is missing.
