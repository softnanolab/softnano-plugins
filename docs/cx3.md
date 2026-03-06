# PBS Pro Instructions (Imperial HPC)

## Detection

You are on the Imperial College London HPC (CX3/CX3-Phase2) if `qsub` is available and `squeue` is not.
This cluster uses **PBS Pro**, not SLURM.

Documentation: https://icl-rcs-user-guide.readthedocs.io/en/latest/

## Queue Reference

| Queue | Walltime | CPUs | Memory | GPUs | Use case |
|-------|----------|------|--------|------|----------|
| `v1_gpu72` | 72h | 1–64 | up to 920 GB | L40S / A100 | GPU inference/training |
| `v1_medium24` | 24h | 1–64 | up to 450 GB | — | CPU-only, moderate memory |
| `v1_largemem72` | 72h | 1–128 | 921–4000 GB | — | mmseqs2 / large-index jobs |

> Note: 12 GPU limit per user on `v1_gpu72`.

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
| Array jobs | `#PBS -J 0-99` — index available as `$PBS_ARRAY_INDEX` |
| Job name | `#PBS -N <name>` — keep short (15-char limit) |

## Common Commands

```bash
# Submit
qsub script.sh

# Submit with variables
qsub -v "INPUT_FASTA=/path/to/file.fasta,OUTPUT_DIR=/path/to/out/" script.sh

# Check your jobs
qstat -u $USER

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

## Key Differences from SLURM

- No `srun` — run Python directly after activating the venv
- No `%j` job ID expansion in `#PBS -o` — use a fixed log filename
- Resource selector syntax: `select=<N>:ncpus=<C>:mem=<M>gb:ngpus=<G>` instead of `--nodes`/`--gpus`
- Variables passed via `qsub -v "KEY=val"` instead of `--export`
- Queue specified with `#PBS -q` instead of `#SBATCH --partition`

## Other details about CX3
- The `home/` directory (`/rds/general/user/<user>/home`) contains 1TB of storage and should be used to house the code, logs, and outputs.
- The `ephemeral/` directory (`/rds/general/user/<user>/ephemeral`) contains 10TB of storage (that is deleted every 30 days) and should be used for large datasets. Don't worry about the deletion, we will regenerate the datasets as needed.
