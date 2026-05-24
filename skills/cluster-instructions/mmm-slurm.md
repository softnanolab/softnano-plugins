# MMM Young NG SLURM Instructions

Use these instructions on the new MMM Young cluster reached as `ssh mmm` from machines that have Jakub's SSH aliases. Direct SSH target is `mmm1486@young-ng.rc.ucl.ac.uk`.

## Detection

You are on MMM Young NG when:

- `pwd` is under `/lustre/home/<user>`
- hostname looks like `login*.young.ucl.ac.uk`
- `sbatch`, `squeue`, `srun`, and `scontrol` are available
- `qsub` / `qconf` are not available

This is **SLURM**, not SGE and not Isambard. Do not use Isambard GPU assumptions here.

## Login-node rule

Treat `login*.young.ucl.ac.uk` as submit-and-inspect only. Do not run Python workloads, tests, GPU commands, or heavy CPU jobs directly on the login node. Use `sbatch` for normal work and `srun` only for short interactive debugging allocations.

## Observed Partitions

| Partition | Typical QoS | Notes |
|---|---|---|
| `cpu` | `freecpu`, `test`, `nolimit` | Default CPU partition |
| `highmem` | `highmem`, `test`, `nolimit` | High-memory CPU nodes |
| `hbm` | `hbmcpu`, `test`, `nolimit` | HBM/tmpfs-heavy CPU nodes |
| `gpu` | `freegpu`, `test`, `nolimit` | A100 GPU partition |
| `intergpu` | `intergpu`, `test`, `nolimit` | Interactive GPU partition |

The observed GPU node is `node-x12t-002` with A100 GRES. Before relying on an exact GPU request string, verify with:

```bash
scontrol show partition gpu -o
scontrol show node node-x12t-002 | grep -E 'Gres=|CfgTRES='
```

## Modules

The new MMM module stack is separate from `mmm-old`. Modules observed on the new SLURM login include:

- `python/3.11.9` and `python/3.13.0`
- `openblas/0.3.28-omp`
- `cuda/12.6.2`

Prefer loading explicit modern modules in job scripts. If a project has a checked-in lockfile, create/sync the virtualenv before submission when that is lightweight. If dependency setup starts compiling large packages, move it into a CPU batch job.

## Single-GPU Job Template

```bash
#!/bin/bash
#SBATCH --job-name=<descriptive_name>
#SBATCH --partition=gpu
#SBATCH --qos=freegpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --gres=gpu:a100:1
#SBATCH --time=24:00:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

cd "$SLURM_SUBMIT_DIR"
mkdir -p logs

module load python/3.11.9
module load openblas/0.3.28-omp
module load cuda/12.6.2

PYTHON_EXEC=".venv/bin/python"

srun "$PYTHON_EXEC" -m scripts.<script_name> \
    <args>
```

If `--gres=gpu:a100:1` is rejected, inspect the node GRES and retry with the exact local syntax, commonly `--gres=gpu:1` or `--gpus=1`.

## CPU Job Template

```bash
#!/bin/bash
#SBATCH --job-name=<descriptive_name>
#SBATCH --partition=cpu
#SBATCH --qos=freecpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err

set -euo pipefail

cd "$SLURM_SUBMIT_DIR"
mkdir -p logs

module load python/3.11.9
module load openblas/0.3.28-omp

PYTHON_EXEC=".venv/bin/python"

srun "$PYTHON_EXEC" -m scripts.<script_name> \
    <args>
```

## Interactive Debugging

Use short interactive allocations for quick checks only:

```bash
# CPU
srun --partition=cpu --qos=test --cpus-per-task=4 --mem=16G --time=00:30:00 --pty bash -l

# GPU
srun --partition=intergpu --qos=intergpu --gres=gpu:a100:1 --cpus-per-task=4 --mem=32G --time=01:00:00 --pty bash -l
```

If the GPU interactive request is rejected, fall back to the `gpu` partition with `--qos=test` and the exact GRES syntax shown by `scontrol`.

## Common Commands

```bash
# Partitions and node state
sinfo -o "%P %a %D %c %m %G %N"

# Submit
sbatch job.slurm

# Check your jobs
squeue -u "$USER" --format="%.18i %.20j %.8T %.10M %.6D %.4C %.20R"

# Job details
scontrol show job <job_id>

# Recent history
sacct -u "$USER" --starttime=$(date -d '24 hours ago' +%Y-%m-%d) \
    --format=JobID,JobName%30,State,ExitCode,Elapsed --noheader

# Cancel
scancel <job_id>
```

## Key Differences from `mmm-old`

- Use `sbatch` / `srun` / `squeue`, not `qsub` / `qstat`.
- Use SLURM partitions/QoS rather than SGE queues.
- New MMM module names differ from old MMM. Do not copy `python/3.11.4-gnu-10.2.0` or old CUDA module names unless `module avail` confirms them on the new login.
- Do not assume Isambard's Grace Hopper resource mapping; MMM's GPU partition is A100-based.
