---
name: monitor-jobs
description: Monitor SLURM/PBS jobs and their logs. Use when the user asks to monitor, check, or watch a submitted job. Automatically detects running/pending jobs, tails logs, and reports errors.
argument-hint: "[job-id (optional)]"
allowed-tools: Bash, Read, Grep, Glob, Task
---

# Monitor HPC Jobs

You are monitoring HPC jobs on a cluster. Follow this workflow:

## Step 0: Resolve project root and environment

1. Look for `.env` by walking up from `$PWD` (check `$PWD/.env`, `$PWD/../.env`, etc.)
2. The directory containing `.env` is `$PROJECT_ROOT`
3. If no `.env` is found, fall back to `$PWD`
4. Read `.env` to get `JOBS_DIR` (used for locating job scripts and logs).

## Step 1: Detect the scheduler

```bash
command -v sbatch && echo "SLURM" || (command -v qsub && echo "PBS" || echo "UNKNOWN")
```

Follow the **SLURM** or **PBS Pro** paths below depending on the result.

## Step 2: Identify the job

- If `$ARGUMENTS` contains a job ID, use that.

### SLURM
- Run `squeue -u $USER --format="%.18i %.20j %.8T %.10M %.6D %.4C %.20R %o" --sort=-V` to find the user's active jobs.
- If no jobs are running/pending, check recently completed jobs with `sacct -u $USER --starttime=$(date -d '24 hours ago' +%Y-%m-%d) --format=JobID,JobName%30,State,ExitCode,Start,End,Elapsed --noheader`.

### PBS Pro
- Run `qstat -u $USER` to find the user's active jobs.
- If no jobs are running/queued, there is no built-in history command — report that no active jobs were found.

## Step 3: Get job details

### SLURM
- Run `scontrol show job <job_id>` to get full job info (WorkDir, StdOut path, submission script, state, node allocation).
- Extract the **log file path** from the `StdOut` field. Note: `%j` in the path is replaced by the job ID.

### PBS Pro
- Run `qstat -f <job_id>` to get full job info (Output_Path, Error_Path, job state, resources).
- Extract the **log file path** from the `Output_Path` field.

## Step 4: Wait for job to start (if PENDING/QUEUED)

If the job is PENDING (SLURM) or Q (PBS), do NOT just report and stop. Instead, **automatically poll until it starts**:

1. Report the current state: "Job 12345 is PENDING. Waiting for it to start..."
2. Run `sleep 30` in the background using `run_in_background: true`.
3. After each sleep, re-check:
   - **SLURM**: `squeue -j <job_id> --noheader --format="%.18i %.8T"`
   - **PBS**: `qstat <job_id>` (check the state column)
4. If still pending, report briefly ("Still pending, waited Xm so far...") and sleep again.
5. Repeat until the job transitions to RUNNING (R) or FAILED/CANCELLED.
6. Once RUNNING, wait 10 more seconds for the log file to appear, then proceed to Step 5.

This polling loop is the **default behavior** — do not ask the user whether to wait. Just do it.

## Step 5: Monitor the logs

- Check if the log file exists yet. If not, sleep 10 seconds and retry (up to 5 times).
- Once the log file exists, read the **last 100 lines** using `tail -n 100 <log_path>`.
- Look for:
  - **Errors**: Python tracebacks, `Error`, `Exception`, `FAILED`, `CANCELLED`, `OOM`, `CUDA error`, `RuntimeError`
  - **Warnings**: `UserWarning`, `FutureWarning`, deprecation notices
  - **Progress indicators**: epoch numbers, step counts, loss values, W&B run URLs
  - **Training metrics**: `train/loss`, `val/loss`, learning rate, gradient norms

## Step 6: Report status

Provide a concise summary:
1. **Job state** (PENDING / RUNNING / COMPLETED / FAILED / TIMEOUT)
2. **Runtime** so far
3. **Training progress** (current epoch/step, latest loss values)
4. **W&B run URL** if visible in logs
5. **Errors or warnings** if any — include the full traceback

## Step 7: If errors are found

- Analyze the error and identify the root cause.
- Check the relevant source files in the codebase to understand the issue.
- Propose a fix. If the fix is clear and safe:
  1. Apply the fix to the source code.
  2. Cancel the failed job (ask user first):
     - **SLURM**: `scancel <job_id>`
     - **PBS**: `qdel <job_id>`
  3. Resubmit the job with the original script.
- If the fix is ambiguous or risky, present options to the user before acting.

## Step 8: Continuous monitoring (if job is still running)

If the job is running and healthy, offer to keep monitoring. If the user wants continued monitoring:
- Sleep for 60 seconds between checks.
- Re-read the last 100 lines of the log.
- Report any new errors, warnings, or progress updates.
- Stop monitoring when the job completes, fails, or the user asks to stop.

## Key paths

| What | Path |
|------|------|
| Job scripts | `$JOBS_DIR/<project>/` |
| SLURM logs | `$JOBS_DIR/<project>/logs/` (or as specified by `#SBATCH --output`) |
| PBS logs | `$JOBS_DIR/<project>/logs/` (or as specified by `#PBS -o`) |
| Env vars | `$PROJECT_ROOT/.env` → `JOBS_DIR` |

## Important notes

- **SLURM**: Always resolve `%j` in log paths to the actual job ID.
- If the log path is relative, resolve it relative to the job's WorkDir (SLURM: from `scontrol`, PBS: from `PBS_O_WORKDIR`).
- When sleeping/waiting, use `sleep` in Bash with `run_in_background` to avoid blocking.
- Present errors with enough context (surrounding lines) for the user to understand.
- See `docs/slurm.md` or `docs/cx3.md` in this plugin for full HPC reference.
