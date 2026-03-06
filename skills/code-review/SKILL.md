---
name: code-review
description: Review Python code against SoftNano style conventions. Use when the user asks to review, lint, or check code style. Checks docstrings, type annotations, tensor shape docs, and commented-out code.
argument-hint: "[file-or-directory (optional)]"
allowed-tools: Bash, Read, Grep, Glob, Write, Edit
---

# Code Review

You are reviewing Python code against the SoftNano code style guide. Follow this workflow:

## Step 1: Load the style guide

Read `docs/code_style.md` from this plugin's directory to get the authoritative style rules. The key conventions are:

- **Docstrings**: Google-style with `Args:`, `Returns:`, multi-line description
- **Tensor shapes**: `Expected Shape:` sub-lines in `Args:`
- **Type annotations**: Python 3.12+ style — `x | None` not `Optional[x]`, lowercase `list`/`dict`/`tuple` not `List`/`Dict`/`Tuple`, all arguments annotated
- **Commented-out code**: Must have `# TODO: review this code later` + `# ----` markers, or be deleted
- **Return types**: Always specified in both annotation and `Returns:` docstring section

## Step 2: Identify files to review

Determine which files to check, in priority order:

1. If `$ARGUMENTS` specifies a file or directory, use that.
2. If no argument, check for staged changes: `git diff --cached --name-only -- '*.py'`
3. If nothing staged, check recent unstaged changes: `git diff --name-only -- '*.py'`
4. If no changes, ask the user which files to review.

For directories, find all Python files recursively.

## Step 3: Run automated checks

If `ruff` is available (`command -v ruff`), run it first for quick wins:

```bash
ruff check --select E,W,F,I <files>
ruff format --check <files>
```

Report ruff findings separately. If ruff is not installed, skip this step and note it in the report.

## Step 4: Manual style checks

For each Python file, check the following categories:

### 4a. Docstrings
- Every public function/method/class has a docstring.
- Docstring uses Google style: summary line, blank line, `Args:`, `Returns:`.
- `Args:` lists all parameters with descriptions.
- `Returns:` specifies the return type and meaning.

### 4b. Tensor / array shape documentation
- Functions that accept array-like arguments (numpy, torch, jax) document `Expected Shape:` for each array parameter in the docstring.

### 4c. Type annotations
- All function parameters have type annotations.
- Return types are annotated.
- Uses `x | None` instead of `Optional[x]`.
- Uses lowercase builtins (`list`, `dict`, `tuple`) instead of `typing.List`, `typing.Dict`, `typing.Tuple`.
- No unnecessary imports from `typing` for types available as builtins.

### 4d. Commented-out code
- Any commented-out code block (2+ consecutive commented lines that look like code) must be wrapped with `# TODO: review this code later` and `# ----` markers.
- Stale commented-out code without markers should be flagged for deletion.

## Step 5: Report findings

Organize the report by category and severity:

```
## Code Review: <filename>

### Errors (must fix)
- [type-annotations] line 42: Missing type annotation for parameter `data`
- [docstring] line 58: Missing `Returns:` section

### Warnings (should fix)
- [commented-code] lines 70-75: Commented-out code without TODO marker
- [tensor-shape] line 42: Parameter `features` is array-like but missing Expected Shape

### Style (nice to have)
- [docstring] line 12: Summary line should use imperative mood

### Passed
- ruff: no issues found
- type-annotations: 15/17 functions fully annotated
```

## Step 6: Offer to apply fixes

After reporting, offer to apply **style-only** fixes:

- Add missing docstring templates (skeleton with `Args:` and `Returns:`)
- Replace `Optional[X]` with `X | None`
- Replace `typing.List` / `typing.Dict` / `typing.Tuple` with lowercase builtins
- Add `# TODO: review this code later` + `# ----` markers around commented-out code
- Remove unused `typing` imports

**Never** change logic, rename variables, or refactor code. Style fixes only.

## Important notes

- When in doubt about a convention, defer to `docs/code_style.md` in this plugin.
- Do not flag test files for missing docstrings on test functions (functions starting with `test_`).
- Private functions (starting with `_`) should still have type annotations but docstrings are optional.
- Be pragmatic: focus on actionable findings, not nitpicks.
