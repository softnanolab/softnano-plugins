---
name: edison-research
description: Conduct scientific research using Edison's autonomous literature search API. Use when the user asks to research a scientific question, find papers, or review literature on a topic. Edison searches hundreds of papers and returns a cited answer.
argument-hint: <research question>
user-invocable: true
allowed-tools: Bash
---

# Edison Research

You are delegating a scientific literature search to the Edison API. Edison is an autonomous research agent that searches hundreds of papers and synthesizes a cited answer. Your job is to submit the query, wait for the result, and report it.

## CRITICAL: Do NOT search for the answer yourself

> **Edison takes 1–5 minutes to respond. This is normal. BE PATIENT.**
>
> While waiting for Edison, you MUST NOT:
> - Search the web, PubMed, bioRxiv, or any other source
> - Attempt to answer the research question from your own knowledge
> - Use any other tool to find papers or literature
> - Speculate about what the answer might be
>
> Edison's search is comprehensive (hundreds of papers with full-text analysis). Anything you find on your own would be redundant and inferior. Your role is to **submit and wait**, not to compete with Edison.
>
> The ONLY thing you may do while an Edison query is running is launch additional Edison queries if the user asked for multiple.

## Input

<query>
$ARGUMENTS
</query>

If no query is provided, ask the user what they want to research.

## Step 1: Run the query

Run the script with `run_in_background: true` and `timeout: 600000` (10 minutes):

```bash
${CLAUDE_SKILL_DIR}/scripts/edison_query.sh --query "<the research question>"
```

The script authenticates, submits the query, and polls every 15s until Edison returns an answer (up to 10 minutes). Progress messages appear on stderr. The final result is a JSON object on stdout:

```json
{
  "task_id": "uuid",
  "formatted_answer": "The full cited answer in markdown",
  "answer": "Plain text answer",
  "has_successful_answer": true
}
```

If the script outputs an `error` field, report the error to the user and stop.

### Running multiple queries

If the user asks multiple research questions, launch each as a separate background Bash call. Wait for all to complete before reporting.

## Step 2: Report the answer

Once the script returns:

1. Report `formatted_answer` to the user verbatim — it contains inline citations and is the primary output.
2. Note the `task_id` — the user may want it for follow-up queries.
3. If `has_successful_answer` is `false`, tell the user Edison could not confidently answer and suggest refining the question.

## Follow-up queries

To continue a previous research thread (e.g., ask a follow-up question that builds on prior context), use `--continue-from`:

```bash
${CLAUDE_SKILL_DIR}/scripts/edison_query.sh --query "<follow-up question>" --continue-from <task_id>
```

This reuses the papers and context from the previous task, giving Edison a head start. Use this when the user wants to dig deeper into a topic they already queried.

## Prerequisites

The user must set their Edison API key in `~/.claude/settings.json`:

```json
{
  "env": {
    "EDISON_PLATFORM_API_KEY": "your-key-here"
  }
}
```

Keys are available from [platform.edisonscientific.com/profile](https://platform.edisonscientific.com/profile).

`jq` must be installed (`brew install jq` / `apt install jq`).
