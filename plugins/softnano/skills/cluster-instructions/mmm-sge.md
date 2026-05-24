# MMM Old Young SGE Instructions

Use these instructions on the old MMM Young cluster reached as `ssh mmm-old` from the SoftNano campus workstation. If the alias is not defined locally, use `ssh mmm1486@young.rc.ucl.ac.uk`.

## Detection

You are on MMM old Young when:

- `pwd` is under `/lustre/home/<user>`
- hostname looks like `login*.ib.young.ucl.ac.uk`
- `qsub`, `qstat`, `qacct`, `qconf`, and `qhost` are available under `/opt/sge/bin/lx-amd64/`
- `sbatch` / `squeue` are not available

This is **SGE / Grid Engine**, not PBS. The command is named `qsub`, but PBS directives such as `#PBS` and PBS resource selectors are wrong here.

## Login-node rule

Treat `login*.ib.young.ucl.ac.uk` as submit-and-inspect only. Do not run Python workloads, tests, GPU commands, or heavy CPU jobs directly on the login node. Submit via `qsub` and inspect with `qstat`, `qacct`, and log files.

## Required Project Flags

Include these directives unless the user gives a different account/project:

```bash
#$ -A Imperial_Mat
#$ -P Free
```

Missing account/project flags are a common reason for rejection.

## Modules

The old MMM module stack is separate from the new SLURM login. Modules observed on old Young include:

- `python/3.11.4-gnu-10.2.0`
- `openblas/0.3.13-openmp/gnu-10.2.0`
- `cuda/12.2.2/gnu-10.2.0` and older CUDA modules

The old login may print startup warnings about missing newer `cmake` or `git` modulefiles. Do not treat those warnings as job-submission failures; load the old module names explicitly in the job script.

## Queues and Resources

Common queue names include `Arya` and `Bran`. `Bran` is the GPU-oriented queue historically used for SoftNano GPU jobs. Lowercase queue names may appear in `qconf -sql` but can be unavailable or disabled; prefer the uppercase queue names shown as available by `qstat -g c`.

Observed requestable complexes include:

| Complex | Alias | Use |
|---|---|---|
| `gpu` | | GPU count, for example `-l gpu=1` |
| `h_rt` | | Runtime limit |
| `memory` | `mem` | Memory request |
| `slots` | `s` | Slot count |
| `tmpfs` | `scratch` | Local scratch/tmpfs request |

Parallel environments are queue/hostgroup-specific. Do not invent `-pe smp 8`; check `qconf -spl` and `qconf -sq <queue>` before using a PE. For single-process GPU work, a single slot plus `-l gpu=1` is the conservative default.

## Single-GPU Job Template

```bash
#!/bin/bash -l
#$ -N <descriptive_name>
#$ -cwd
#$ -V
#$ -A Imperial_Mat
#$ -P Free
#$ -q Bran
#$ -l h_rt=48:00:00
#$ -l gpu=1
#$ -l memory=64G
#$ -l tmpfs=10G
#$ -j y
#$ -o logs/

set -euo pipefail

mkdir -p logs

module load python/3.11.4-gnu-10.2.0
module load openblas/0.3.13-openmp/gnu-10.2.0
module load cuda/12.2.2/gnu-10.2.0

PYTHON_EXEC=".venv-mmm/bin/python"

"$PYTHON_EXEC" -m scripts.<script_name> \
    <args>
```

## CPU Job Template

```bash
#!/bin/bash -l
#$ -N <descriptive_name>
#$ -cwd
#$ -V
#$ -A Imperial_Mat
#$ -P Free
#$ -q Arya
#$ -l h_rt=12:00:00
#$ -l memory=32G
#$ -l tmpfs=10G
#$ -j y
#$ -o logs/

set -euo pipefail

mkdir -p logs

module load python/3.11.4-gnu-10.2.0
module load openblas/0.3.13-openmp/gnu-10.2.0

PYTHON_EXEC=".venv-mmm/bin/python"

"$PYTHON_EXEC" -m scripts.<script_name> \
    <args>
```

## Common Commands

```bash
# Queues and capacity
qstat -g c

# Queue details
qconf -sq Bran
qconf -sq Arya

# Requestable resources
qconf -sc

# Parallel environments
qconf -spl

# Submit
qsub job.sge

# Submit and wait for completion
qsub -sync y job.sge

# Check your jobs
qstat -u "$USER"

# Job details
qstat -j <job_id>

# Accounting after completion
qacct -j <job_id>

# Cancel
qdel <job_id>
```

## Key Differences from New `mmm`

- Use `qsub` / `qstat` / `qacct`, not `sbatch` / `squeue` / `sacct`.
- Use SGE directives (`#$`), not PBS directives (`#PBS`) and not SLURM directives (`#SBATCH`).
- Include `#$ -A Imperial_Mat` and `#$ -P Free`.
- Keep GPU jobs within `48:00:00` unless the user explicitly provides a different cluster policy.
- Old and new MMM have incompatible module stacks; do not copy module names between them without checking `module avail`.
