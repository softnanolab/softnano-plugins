# PBS Pro Instructions (Imperial HPC)

## Detection

You are on the Imperial College London HPC (CX3/CX3-Phase2) if `qsub` is available and `squeue` is not.
This cluster uses **PBS Pro**, not SLURM.

Documentation: https://icl-rcs-user-guide.readthedocs.io/en/latest/

## Queue Reference

Verified against `qstat -Qf` (2026-09-15). Pick the smallest tier that fits — the
small/medium/large tiers are sized by CPU and memory, and a smaller request waits less.

| Queue | Walltime | Max CPUs | Max memory | GPUs | Use case |
|-------|----------|----------|------------|------|----------|
| `v1_small24` / `v1_small24a` | 24h | 16 | 128 GB | — | Default for CPU work: scripts, parsing, small pipelines |
| `v1_small72` / `v1_small72a` | 72h | 16 | 128 GB | — | Same, when it needs longer than a day |
| `v1_medium24` / `v1_medium24a` | 24h | 64 | 450 GB | — | CPU-only, moderate memory |
| `v1_medium72` / `v1_medium72a` | 72h | 64 | 450 GB | — | Same, longer walltime |
| `v1_large24` / `v1_large24a` | 24h | 128 | 920 GB | — | Large CPU jobs |
| `v1_large72` / `v1_large72a` | 72h | 128 | 920 GB | — | Same, longer walltime |
| `v1_largemem72` | 72h | 128 | **min 921 GB**, max 4000 GB | — | mmseqs2 / large-index jobs. Has a memory *floor* — a smaller request is rejected |
| `v1_gpu72` | 72h | 128 | 920 GB | up to 8 (L40S / A100) | GPU inference/training |
| `v1_capability24` | 24h | 256 | 2048 GB | — | Very wide CPU work |
| `v1_capability48` | 48h | 256 | 2048 GB | — | Same, 48h |
| `v1_interactive` | 8h | 8 | 64 GB | 1 | `qsub -I` sessions |
| `v1_jupyter` / `v1_jupytergpu` | 8h | 8 / 4 | 64 / 32 GB | — / 1 | Jupyter via OnDemand |

> **The `a` suffix means array jobs.** Every `*a` queue has `max_array_size = 10000`;
> every non-`a` queue has `max_array_size = 0` and rejects a `#PBS -J` submission. So
> `#PBS -J 0-99` must go to `v1_small24a`, `v1_medium72a` and so on — never the plain
> name. Resource limits are otherwise identical within a pair.

> Note: 12 GPU limit per user on `v1_gpu72`.

> Contention varies and is worth checking before choosing: `qstat -Q` shows queued vs
> running counts per queue. `v1_small24` is usually the busiest on the cluster, and its
> `a` twin is often much emptier.

## Job Script Templates

### Single-GPU Job

```bash
#!/bin/bash
#PBS -N <descriptive_name>
#PBS -q v1_gpu72
#PBS -l select=1:ncpus=8:mem=64gb:ngpus=1
#PBS -l walltime=24:00:00
#PBS -o logs/<descriptive_name>.out
#PBS -e logs/<descriptive_name>.err

cd "$PBS_O_WORKDIR"

mkdir -p logs

cd $PROJECT_ROOT

source .venv/bin/activate
PYTHON_EXEC=".venv/bin/python"

$PYTHON_EXEC -m scripts.<script_name> \
    <args>
```

### CPU-Only Large-Memory Job (colabfold_search / mmseqs2)

```bash
#!/bin/bash
#PBS -N <descriptive_name>
#PBS -q v1_largemem72
#PBS -l select=1:ncpus=16:mem=921gb
#PBS -l walltime=72:00:00
#PBS -o logs/<descriptive_name>.out
#PBS -e logs/<descriptive_name>.err

cd "$PBS_O_WORKDIR"

mkdir -p logs

source "$HOME/miniforge3/etc/profile.d/conda.sh"
conda activate colabfold

<command>
```

## Key Patterns

| Pattern | Details |
|---------|---------|
| Log path | `#PBS -o logs/<name>.out` — relative to `PBS_O_WORKDIR` (submission dir) |
| Working dir | PBS does NOT cd automatically — always `cd "$PBS_O_WORKDIR"` first |
| Python exec | `source .venv/bin/activate` then use `.venv/bin/python` directly (no `srun`) |
| Passing vars | `qsub -v "KEY=val,KEY2=val2" script.sh`; read as `${KEY}` in the script |
| Array jobs | `#PBS -J 0-99` — index available as `$PBS_ARRAY_INDEX`. **Requires an `a`-suffixed queue** (`v1_small24a`, …); the plain queues reject arrays |
| Job name | `#PBS -N <name>` — keep short (15-char limit) |

## Common Commands

```bash
# Submit
qsub script.sh

# Submit with variables
qsub -v "INPUT_FASTA=/path/to/file.fasta,OUTPUT_DIR=/path/to/out/" script.sh

# Check your jobs
qstat -u $USER

# Job state after it finishes (plain qstat forgets it; -x keeps history)
qstat -x <job_id>

# Queue contention — queued vs running per queue, before picking one
qstat -Q

# Job details (nodes, state, logs)
qstat -f <job_id>

# Tail output (log path is relative to submission dir)
tail -f logs/<name>.out

# Cancel
qdel <job_id>

# Interactive GPU session (quick debugging)
qsub -I -q v1_gpu72 -l select=1:ncpus=4:mem=32gb:ngpus=1 -l walltime=01:00:00
```

> For quick debugging (mypy, ruff, pytest, short scripts under 5 min), use an interactive session via `qsub -I`. For anything longer, use a batch script.

> **PBS copies the log back only when the job ends.** While a job runs, the path in
> `#PBS -o` still holds the *previous* run's output if the filename is reused — output is
> buffered on the execution node until exit. So `tail`ing it mid-run shows stale content
> that looks like a completed run. Check `qstat -x <job_id>` for state, and check the
> log's mtime before believing it. Use a unique log name per run to avoid the trap
> entirely.

## Key Differences from SLURM

- No `srun` — run Python directly after activating the venv
- No `%j` job ID expansion in `#PBS -o` — use a fixed log filename
- Resource selector syntax: `select=<N>:ncpus=<C>:mem=<M>gb:ngpus=<G>` instead of `--nodes`/`--gpus`
- Variables passed via `qsub -v "KEY=val"` instead of `--export`
- Queue specified with `#PBS -q` instead of `#SBATCH --partition`

## Other details about CX3
- The `home/` directory (`/rds/general/user/<user>/home`) contains 1TB of storage and should be used to house the code, logs, and outputs.
- The `ephemeral/` directory (`/rds/general/user/<user>/ephemeral`) contains 10TB of storage (that is deleted every 30 days) and should be used for large datasets. Don't worry about the deletion, we will regenerate the datasets as needed.
- The agent might be run from within a login node. Once you know that you are on CX3, find the machine name and if it doesn't have the word `login` in it, then you are not on a login node and can run python commands directly.
