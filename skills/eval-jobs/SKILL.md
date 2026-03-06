---
name: eval-jobs
description: Submit and monitor SLURM/PBS eval jobs for W&B runs, then display interchain metric tables. Use when the user wants to evaluate one or more W&B runs.
argument-hint: "<wandb_run_url(s) or project_url>"
allowed-tools: Bash, Read, Grep, Glob, Write, Agent, Task
---

# Evaluate W&B Runs

You are submitting evaluation jobs for W&B runs on an HPC cluster, monitoring them to completion, and displaying interchain contact prediction metrics.

## Step 0: Resolve the project root

Determine the **invoking project's root directory** — this is the repo from which the user called this skill.

1. Look for `.env` by walking up from `$PWD` (check `$PWD/.env`, `$PWD/../.env`, etc.)
2. The directory containing `.env` is `$PROJECT_ROOT`
3. If no `.env` is found, fall back to `$PWD`

All relative paths below (`.venv`, `scripts/`, `.env`) are relative to `$PROJECT_ROOT`.

## Step 1: Load environment variables

- Read `.env` from `$PROJECT_ROOT` to get `LOGS_DIR`, `JOBS_DIR`, `WANDB_ENTITY`.
- Export them for use in subsequent steps.

## Step 2: Parse arguments

- `$ARGUMENTS` contains one or more W&B run URLs (space or comma separated), OR a W&B project URL to eval all runs in that project.
- Extract `(entity, project, run_id)` from each URL using regex: `wandb\.ai/([^/]+)/([^/]+)/runs/([^/?]+)`
- If a **project URL** is given (no `/runs/`), list all runs in that project by scanning `$LOGS_DIR/<project>/` for run directories that contain checkpoints.

## Step 3: Check for existing results

For each run, check if `$LOGS_DIR/<project>/<run_id>/checkpoints/results.json` already exists.
- If it does: **skip** job submission for that run — use cached results.
- Report which runs are cached vs which need evaluation.
- If ALL runs are cached, skip directly to Step 6.

## Step 4: Generate and submit eval jobs

**First, detect the scheduler:** check if `sbatch` is available (SLURM) or `qsub` is available (PBS Pro). This determines the job template.

### SLURM (Isambard)

For each run needing evaluation, create a batch script at `$JOBS_DIR/<project>/eval_<run_id>.sh`:

```bash
#!/bin/bash
#SBATCH --job-name=eval_<run_id>
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=01:00:00
#SBATCH --output=logs/eval_<run_id>_%j.out

cd $PROJECT_ROOT

# Venv must be synced before submission (uv sync --frozen --extra dev)
# Do NOT run uv sync inside the job — concurrent jobs race on .venv/
PYTHON_EXEC=".venv/bin/python"

srun $PYTHON_EXEC -m scripts.evals.evaluate_from_wandb \
    --wandb_url="https://wandb.ai/<entity>/<project>/runs/<run_id>"
```

Submit with `sbatch` from the `$JOBS_DIR/<project>/` directory. Collect SLURM job IDs.

### PBS Pro (CX3)

For each run needing evaluation, create a batch script at `$JOBS_DIR/<project>/eval_<run_id>.sh`:

```bash
#!/bin/bash
#PBS -N ev_<run_id_short>
#PBS -q v1_gpu72
#PBS -l select=1:ncpus=8:mem=64gb:ngpus=1
#PBS -l walltime=01:00:00
#PBS -o logs/eval_<run_id>.out
#PBS -e logs/eval_<run_id>.err

cd "$PBS_O_WORKDIR"

mkdir -p logs

cd $PROJECT_ROOT

source .venv/bin/activate
PYTHON_EXEC=".venv/bin/python"

$PYTHON_EXEC -m scripts.evals.evaluate_from_wandb \
    --wandb_url="https://wandb.ai/<entity>/<project>/runs/<run_id>"
```

- Note: PBS job names have a 15-char limit, so truncate `run_id` to fit: `ev_<first 12 chars>`.
- Submit with `qsub` from the `$JOBS_DIR/<project>/` directory. Collect PBS job IDs.

## Step 5: Monitor jobs until completion

### SLURM

1. Poll `squeue -j <comma_separated_job_ids> --noheader --format="%.18i %.8T"` every 30 seconds.
2. Report progress as jobs complete.
3. On failure, find the log file at `$JOBS_DIR/<project>/logs/eval_<run_id>_<job_id>.out` and tail the last 50 lines to report the error.
4. Continue until all jobs finish (COMPLETED or FAILED).

### PBS Pro

1. Poll `qstat <space_separated_job_ids>` every 30 seconds.
2. Jobs disappear from `qstat` output when complete — if a job ID is no longer listed, it has finished.
3. On failure, check `$JOBS_DIR/<project>/logs/eval_<run_id>.err` for errors.
4. Continue until all jobs finish.

Use `sleep 30` with `run_in_background: true` between polls to avoid blocking.

## Step 6: Parse results and display tables

For each completed run, read `$LOGS_DIR/<project>/<run_id>/checkpoints/results.json`.

### Resolve run names

Get the human-readable run name from the W&B config:
- Find `$LOGS_DIR/wandb/run-*-<run_id>/files/config.yaml`
- Parse YAML and extract `wandb.value.name`
- Fall back to `run_id` if not found

### Build three markdown tables

Display **three tables** — one each for `inter_P@K`, `inter_median_P@K`, `inter_AUC`:

```
### Inter-chain P@K
| Run / Split      | seq_id_30 | seq_id_40 | seq_id_50 | seq_id_70 | seq_id_90 | seq_id_100 | sergei |
|------------------|-----------|-----------|-----------|-----------|-----------|------------|--------|
| run_name / val   |      4.2  |      5.1  |      ...  |      ...  |      ...  |       ...  |    —   |
| run_name / test  |      3.9  |      4.8  |      ...  |      ...  |      ...  |       ...  |  12.3  |
```

**Formatting rules:**
- Values are **percentages**: multiply raw values by 100, display with 1 decimal place
- Rows grouped by run: **val** row then **test** row for each run
- Columns: 6 seq_id splits (`30`, `40`, `50`, `70`, `90`, `100`) + `sergei`
- Sergei only has a single eval (no val/test split): show `—` for val rows, the metric value for test rows

**Metric key mapping:**
- PDB splits: `results["pdb_mtm_date_cutoff"]["seq_id_<N>"]["val"|"test"]["summary"]["inter_<metric>"]`
- Sergei: `results["sergei"]["summary"]["<metric>"]` (no `inter_` prefix — sergei is inter-chain only)

| Table | PDB key | Sergei key |
|-------|---------|------------|
| P@K | `inter_P@K` | `P@K` |
| Median P@K | `inter_median_P@K` | `median_P@K` |
| AUC | `inter_AUC` | `AUC` |

## Key paths

| What | Path |
|------|------|
| Eval script | `scripts/evals/evaluate_from_wandb.py` (in `$PROJECT_ROOT`) |
| Results output | `$LOGS_DIR/<project>/<run_id>/checkpoints/results.json` |
| W&B config (run name) | `$LOGS_DIR/wandb/run-*-<run_id>/files/config.yaml` |
| Job scripts | `$JOBS_DIR/<project>/eval_<run_id>.sh` |
| Env vars | `$PROJECT_ROOT/.env` → `LOGS_DIR`, `JOBS_DIR`, `WANDB_ENTITY` |

## Important notes

- Always ensure the `$JOBS_DIR/<project>/logs/` directory exists before submitting (create with `mkdir -p`).
- If a results.json exists but is malformed or empty, re-run the eval for that run.
- When displaying tables with multiple runs, sort rows by run name alphabetically.
- If a metric key is missing from results.json, display `—` in that cell.

## HPC scheduler detection

If you are unsure which scheduler is available, run:
```bash
command -v sbatch && echo "SLURM" || (command -v qsub && echo "PBS" || echo "UNKNOWN")
```
- **SLURM detected:** Follow the SLURM paths in Steps 4–5. See `docs/slurm.md` in this plugin for full SLURM reference.
- **PBS Pro detected:** Follow the PBS Pro paths in Steps 4–5. See `docs/cx3.md` in this plugin for full PBS Pro reference.
