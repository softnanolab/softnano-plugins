# SLURM Instructions
Follow this only if you are on a SLURM Machine. You can verify this by checking if the `sbatch` command is available.

- If its a slurm machine, you can assume its on the ISAMBARD cluster. You can read its documentation if you are confused about the cluster, commands, queues, etc. here: https://docs.isambard.ac.uk/user-documentation/guides/

- For Isambard, this is the requirement: You must specify GPU resource in your batch script using either --gpus or one of the --gpus-per-* options. Each GPU requested will also allocate 72 CPU cores and 115 GB of Grace RAM, i.e. one Grace Hopper Superchip. Any job will by default use a unit of one Grace Hopper Superchip. 1 node has 4 GPUs.

## Storage layout — $HOME has a 100 GB quota

The home directory on Isambard is capped at **100 GB**. Anything that is not source code (datasets, model weights, checkpoints, wandb run dirs, large outputs, HuggingFace caches, **and the project venv**) must live under `$PROJECTDIR` instead — that is the shared project space with the real capacity. Keep `$HOME` for the repo checkout and dotfiles only.

Concretely:
- Put data / checkpoints / outputs under `$PROJECTDIR/<project>/...` and reference them from configs via `$PROJECTDIR`.
- Point caches at the project space too: e.g. `export HF_HOME=$PROJECTDIR/.cache/huggingface`, `export WANDB_DIR=$PROJECTDIR/<project>/wandb`.
- Before submitting, sanity-check usage with `quota -s` (works on any quota'd filesystem; on Lustre mounts you can also use `lfs quota -h -u $USER <lustre-mountpoint>`) — a job that fills $HOME mid-run will fail with cryptic write errors.

## One venv per project, hosted on `$PROJECTDIR`

Don't put `.venv` on `$HOME` — even a single PyTorch venv eats a noticeable fraction of the 100 GB quota, and per-worktree venvs blow past it almost immediately. The canonical venv lives on `$PROJECTDIR`; every checkout (the main worktree and each Claude worktree under `.claude/worktrees/<name>/`) reaches it through a `.venv` symlink at the repo root. One venv per project, shared by every worktree.

One-time setup in the main checkout:

```bash
mkdir -p $PROJECTDIR/<project>
rm -rf .venv                                   # remove any stray local venv first; safe if it doesn't exist
ln -sfn $PROJECTDIR/<project>/.venv .venv      # idempotent: -f overwrites, -n replaces an existing symlink-to-dir instead of nesting inside it
uv sync --frozen --extra dev                   # creates the venv at $PROJECTDIR/<project>/.venv
```

For each new Claude worktree, repeat **only** the symlink step (do not re-run `uv sync`):

```bash
# From inside the new worktree:
rm -rf .venv
ln -sfn $PROJECTDIR/<project>/.venv .venv
```

`uv sync` runs **only in the main worktree**; every other worktree picks up updates through the symlink. The job templates below still reference `.venv/bin/python` — that resolves through the symlink to the shared interpreter on `$PROJECTDIR`.

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
| Env sync | Run `uv sync --frozen --extra dev` **from the main worktree only**, before `sbatch` — see "One venv per project" above. Never from a job (concurrent jobs race on `.venv/`) |
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
