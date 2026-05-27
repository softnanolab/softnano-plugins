# SLURM Instructions
Follow this only if you are on a SLURM Machine. You can verify this by checking if the `sbatch` command is available.

- If its a slurm machine, you can assume its on the ISAMBARD cluster. You can read its documentation if you are confused about the cluster, commands, queues, etc. here: https://docs.isambard.ac.uk/user-documentation/guides/

- For Isambard, this is the requirement: You must specify GPU resource in your batch script using either --gpus or one of the --gpus-per-* options. Each GPU requested will also allocate 72 CPU cores and 115 GB of Grace RAM, i.e. one Grace Hopper Superchip. Any job will by default use a unit of one Grace Hopper Superchip. 1 node has 4 GPUs.

## Storage layout — $HOME has a 100 GB quota

The home directory on Isambard is capped at **100 GB**. Anything that is not source code (datasets, model weights, checkpoints, wandb run dirs, large outputs, HuggingFace caches, etc.) must live under `$PROJECTDIR` instead — that is the shared project space with the real capacity. Keep `$HOME` for the repo checkout, dotfiles, and the venv only.

Concretely:
- Put data / checkpoints / outputs under `$PROJECTDIR/<project>/...` and reference them from configs via `$PROJECTDIR`.
- Point caches at the project space too: e.g. `export HF_HOME=$PROJECTDIR/.cache/huggingface`, `export WANDB_DIR=$PROJECTDIR/<project>/wandb`.
- Before submitting, sanity-check with `quota -s` (or `du -sh ~ 2>/dev/null`) — a job that fills $HOME mid-run will fail with cryptic write errors.

## Worktrees share the main checkout's `.venv`

When working across multiple Claude worktrees in `.claude/worktrees/<name>/`, **do not** run `uv sync` inside each worktree — that would create a separate `.venv/` per worktree and quickly burn through the $HOME quota. Instead, symlink the main worktree's `.venv` into each new worktree once at creation time:

```bash
# From inside the new worktree (one-time):
ln -s <main-worktree-path>/.venv .venv
```

Run `uv sync --frozen --extra dev` only in the main worktree; all sibling worktrees see the update through the symlink. The job templates below still reference `.venv/bin/python` — that resolves through the symlink to the shared interpreter.

## Single-GPU Job Template

```bash
#!/bin/bash

#SBATCH --job-name=<descriptive_name>
#SBATCH --nodes=1
#SBATCH --gpus-per-node=1
#SBATCH --ntasks-per-node=1
#SBATCH --time=24:00:00
#SBATCH --output=logs/<descriptive_name>_%j.out

cd $PROJECT_ROOT

# Venv must be synced before submission (uv sync --frozen --extra dev)
# Do NOT run uv sync inside the job — concurrent jobs race on .venv/
PYTHON_EXEC=".venv/bin/python"

srun $PYTHON_EXEC -m scripts.<script_name> \
    <args>
```

## Multi-Node Multi-GPU (DDP)

```bash
#SBATCH --nodes=4
#SBATCH --gpus-per-node=4
#SBATCH --ntasks-per-node=4

# ...same setup...

srun $PYTHON_EXEC -m scripts.<script_name> \
    trainer.devices=4 \
    trainer.num_nodes=4
```
- Note that for 16 GPUs, you will need 4 nodes with gpus-per-node=4 and ntasks-per-node=4


## Key Patterns

| Pattern | Details |
|---|---|
| Log path | `#SBATCH --output=logs/<name>_%j.out` — `%j` expands to SLURM job ID |
| Env sync | Run `uv sync --frozen --extra dev` **before** `sbatch`, not inside the job (concurrent jobs race on `.venv/`) |
| Python exec | Set `PYTHON_EXEC=".venv/bin/python"` and use `srun $PYTHON_EXEC` — never `uv run` inside srun (race conditions on multi-node) |
| Script invocation | Always `python -m scripts.module.name` (not `python scripts/path/file.py`) |
| Hydra overrides | Passed as positional args after the script: `key=value key2=value2` if that script uses hydra|
| Working dir | `cd` to `$PROJECT_ROOT` first; `#SBATCH --output` is relative to the submission dir (the `$JOBS_DIR/<project>/` folder) |

## Common Commands

```bash
# Submit
sbatch baseline.batch

# Check your jobs
squeue -u $USER --format="%.18i %.20j %.8T %.10M %.6D %.4C %.20R"

# Job details (node, log path, state)
scontrol show job <job_id>

# Recent job history (last 24h)
sacct -u $USER --starttime=$(date -d '24 hours ago' +%Y-%m-%d) \
    --format=JobID,JobName%30,State,ExitCode,Elapsed --noheader

# Tail logs (resolve %j → actual job ID)
tail -f logs/<name>_<job_id>.out

# Cancel
scancel <job_id>
```

- For simple debugging jobs or to run mypy, ruff, pre-commits, pytest, simply use srun. For anything that would take more than 5 minutes, create a job script and submit it using sbatch.
