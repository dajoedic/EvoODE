# WP-A1: `analysis/` directory structure

## Context

Before writing any analysis scripts, the full directory structure for `analysis/`
must exist and be correctly ignored by git.

Architecture and conventions are defined in `analysis/CONVENTIONS.md`.
Read that file before doing anything.

---

## Task

### 1. Create missing subdirectories

The following directories must be created with a `.gitkeep` file each:

```
analysis/scripts/aggregate/
analysis/scripts/plot/
analysis/utils/
analysis/data/
analysis/figures/
analysis/tables/
analysis/notebooks/
analysis/configs/
```

`analysis/exploratory/` and `analysis/paper1/` already exist from a previous task.
Do not touch them — leave them as-is.

### 2. Extend `.gitignore`

Append the following lines to the existing `.gitignore` in the repo root.
Do not remove or reorder existing entries.

```
analysis/data/
analysis/figures/
analysis/tables/
analysis/notebooks/.ipynb_checkpoints/
```

### 3. Do not touch anything else

- No Python files
- No Julia files
- No changes to `analysis/CONVENTIONS.md`
- No changes to `CLAUDE.md`
- No changes to `requirements.txt`

---

## Completion condition

- All eight directories listed above exist and contain a `.gitkeep`
- `.gitignore` contains the four new entries
- `git status` shows only new `.gitkeep` files and the modified `.gitignore`

## Verification step

Run `git status` and confirm no unexpected files are staged or modified.

---

## Commit

Single commit after both steps are complete:

```
Add analysis/ directory structure and extend .gitignore
```

No other files in this commit.
