---
name: cluster-instructions
description: Detect which HPC cluster you are on and load the correct job submission instructions. Use when the user asks to submit, run, or schedule a job, or when you need to know which cluster environment you are in.
argument-hint: "[command-to-run (optional)]"
allowed-tools: Bash, Read, Grep, Glob, Write, Edit
---

# Cluster Instructions

You are on an HPC cluster. Before submitting any jobs or running heavy commands, detect which cluster you are on and follow the correct instructions.

**IMPORTANT**: Never run Python, heavy CPU, or GPU commands directly on a login node. Always submit via the scheduler unless you have confirmed you are on a compute node.

## Step 1: Detect the cluster

Run these checks in order:

```bash
# Check working directory path
pwd

# Check available scheduler
command -v sbatch && echo "SLURM" || (command -v qsub && echo "PBS" || echo "UNKNOWN")
```

| Path pattern | Cluster | Scheduler | Instructions |
|---|---|---|---|
| `/rds/general/user/<user>/home/` | Imperial CX3 | PBS Pro | `cx3.md` in this skill |
| `/gpfs/home/<user>` | Imperial HX1 | PBS Pro | Use CX3 instructions (`cx3.md`) |
| `/home/<project>/<user>.<project>/` + `/projects/<project>/` exists | Isambard AI | SLURM | `isambard.md` in this skill |

If none match, ask the user which cluster they are on.

## Step 2: Check if you are on a login node

- **CX3**: Run `hostname`. If it contains `login`, you are on a login node — do not run compute commands directly. If it does NOT contain `login`, you are on a compute node and can run short Python commands directly.
- **Isambard**: Assume login node unless inside an `srun` session or a batch job.

## Step 3: Load cluster-specific instructions

Read the appropriate file from this skill's directory:

- **CX3 / HX1**: Read `cx3.md` — covers PBS Pro queues, job templates, key patterns, common commands, and storage paths.
- **Isambard**: Read `isambard.md` — covers SLURM job templates, GPU allocation (Grace Hopper Superchips), DDP setup, and common commands.

Follow those instructions for all job submission, script creation, and resource allocation decisions.

## Step 4: Submit or run the command

If `$ARGUMENTS` contains a command or script to run:

1. Determine if it needs a batch job (long-running, GPU, heavy CPU) or can run directly (quick debugging, <5 min).
2. For batch jobs: create a job script using the templates from the cluster-specific instructions, then submit it.
3. For quick commands on a compute node: run directly.
4. For quick commands on a login node:
   - **CX3**: Use `qsub -I` for an interactive session.
   - **Isambard**: Use `srun` for an interactive session.

If no arguments are provided, just report which cluster and node type you detected.
