# Current Task

## Task: analysis/status.py — EvoODE Study Status Checker

### Goal

Create `analysis/status.py` — a standalone Python script that shows which scripts
from `SCRIPTS.md` are currently running and what their status is.

---

### Context

**SCRIPTS.md** is the single source of truth for all runnable scripts in this project.
It documents 8 scripts under headings like `### \`experiments/run_experiment.jl\``.

**Windows process limitation:**
Julia on Windows runs via juliaup. The WMI command line of `julia.exe` often does
not contain script arguments. However, the *parent* process (`julialauncher.exe`)
does contain the full command line (`julia profile_init.jl` etc.).
Some Julia processes are "orphans" (started from a shell that has since closed).
Their grandparent no longer exists in WMI. Script name cannot be recovered from
the process tree for these.

**Hybrid approach required:**
1. Try to identify running scripts via the process tree (julialauncher.exe parent's cmdline).
2. For each script in SCRIPTS.md, also check the modification time of its known output files
   to determine if it was recently active (even if process tree gives no result).

---

### Script Location

`analysis/status.py`

---

### Behavior

**Step 1 — Parse SCRIPTS.md**

Extract all `.jl` script paths from SCRIPTS.md using regex on `julia <path>.jl` patterns
in code blocks. Deduplicate. Result: ordered list of script paths relative to project root.

**Step 2 — Get running Julia processes (Windows)**

Use PowerShell + WMI to get all `julia.exe` processes:
- PID, CommandLine, CreationDate
- For each: also fetch parent process (Name, CommandLine)

Use this PowerShell snippet (via subprocess):

```powershell
$procs = @(Get-WmiObject Win32_Process | Where-Object { $_.Name -eq 'julia.exe' })
$procs | ForEach-Object {
    $parent = Get-WmiObject Win32_Process -Filter "ProcessId=$($_.ParentProcessId)" | Select-Object -First 1
    [PSCustomObject]@{
        PID     = $_.ProcessId
        CmdLine = $_.CommandLine
        Created = $_.ConvertToDateTime($_.CreationDate).ToString('o')
        ParentName    = if ($parent) { $parent.Name } else { "?" }
        ParentCmdLine = if ($parent) { $parent.CommandLine } else { "?" }
    }
} | ConvertTo-Json -Depth 1
```

**Step 3 — Match processes to known scripts**

For each julia.exe process:
- Use the parent's CommandLine if ParentName is `julialauncher.exe`, `bash.exe`, or `sh.exe`
- Otherwise use the process's own CommandLine
- Match against known scripts: check if `Path(script).name` appears in the effective cmdline
- If parent is `Code.exe`: mark as "VS Code / REPL (nicht zuordenbar)"
- If no match possible: mark as "unbekanntes Skript"

**Step 4 — Output file status for each known script**

For each script in SCRIPTS.md, derive its known output path(s) from this mapping
(hardcoded, since SCRIPTS.md does not structure outputs in a machine-readable way):

| Script | Output paths to check |
|--------|----------------------|
| `experiments/run_experiment.jl` | `experiments/*/runs/*/status.json` (most recently modified) |
| `experiments/generate_manifest.jl` | `experiments/*/manifest.json` |
| `experiments/aggregate.jl` | `experiments/*/run_registry.csv` |
| `benchmarks/benchmark_evogrow.jl` | `benchmarks/results/summary.csv` |
| `benchmarks/run_odebench.jl` | `benchmarks/results/` (any .csv) |
| `profile_init.jl` | `debug_results/profile_init/profile_init_summary.csv` |
| `generalization_study.jl` | `debug_results/generalization_study/generalization_summary.csv` |
| `debug_single.jl` | `debug_results/debug_single/debug_lotka.log` |

For each output path: find the most recently modified matching file.
Show its modification timestamp and age (e.g., "vor 3d 2h").

**Step 4b — Infer "probably running" from output file activity**

Background: Julia processes started from cmd.exe that has since closed become orphans.
Their script arguments are lost from WMI. These processes show up as "nicht zuordenbar".

To handle this, add an inference step after process matching:

For each script in SCRIPTS.md that is currently `[idle]` (no process match):
- Check the age of its most recently modified output file
- If the output file was modified within the last **90 minutes** AND at least one
  unidentifiable orphan Julia process is running → mark as `[LÄUFT?]`
- The `?` signals that this is inferred from output activity, not confirmed via process tree

The 90-minute threshold is based on this project's output write frequency:
- `benchmark_evogrow.jl` writes to `summary.csv` after every run (typically every few minutes)
- `run_experiment.jl` writes `status.json` after every run

If a script has no output files or output is older than 90 minutes, keep it as `[idle]`.

**Step 5 — Print output**

Print a clean status overview. Example structure:

```
==========================================================
  EvoODE Study Status — 2026-04-29 17:30
==========================================================

  Skripte in SCRIPTS.md : 8
  Julia-Prozesse gesamt : 4  (davon zuordenbar: 1, unbekannt: 2)

  Bekannte Skripte
  --------------------------------------------------------
  [LÄUFT]  profile_init.jl
           PID 73100  |  seit 2026-04-27 22:48  (1d 18h)
           julia profile_init.jl
           Output: debug_results/profile_init/profile_init_summary.csv  (vor 3d 22h)

  [LÄUFT?] benchmarks/benchmark_evogrow.jl
           Output aktiv: benchmarks/results/summary.csv  (vor 34m)
           Fortschritt: 128/300  |  Ø 3.2 min/Run  |  ETA: ~11h 22m
           (Prozess laeuft, aber cmd.exe-Orphan — Script nicht direkt zuordenbar)

  [LÄUFT?] experiments/run_experiment.jl
           Output aktiv: experiments/paper1_phaseA_v1/runs/.../status.json  (vor 1d 9h)
           Fortschritt: 242/300  |  Ø 8.1 min/Run  |  ETA: unbekannt (letzter Run seit >1d aktiv)
           (Prozess laeuft, aber cmd.exe-Orphan — Script nicht direkt zuordenbar)

  [idle]   experiments/generate_manifest.jl
           Output: experiments/paper1_phaseA_v1/manifest.json  (vor 7d 4h)
  ...

  Weitere Julia-Prozesse (nicht zuordenbar)
  --------------------------------------------------------
  PID 42120  |  seit 2026-04-21 22:32  (7d 18h)  |  Elternprozess: cmd.exe
  PID 41456  |  seit 2026-04-23 08:31  (6d 8h)   |  Elternprozess: cmd.exe
```

Note: `[LÄUFT?]` scripts are listed before `[idle]` scripts in the output.
`[LÄUFT]` (confirmed) comes before `[LÄUFT?]` (inferred).

---

### Step 6 — Progress and ETA

For scripts that have countable progress, show: runs done, total, average time per run,
and estimated time remaining.

**Progress tracking per script (hardcoded mapping):**

| Script | Done count | Total | Rate source |
|--------|-----------|-------|-------------|
| `experiments/run_experiment.jl` | count `status.json` files with `"status":"finished"` under `experiments/*/runs/` | count all subdirs in `experiments/*/runs/` | see below |
| `benchmarks/benchmark_evogrow.jl` | row count of `benchmarks/results/summary.csv` minus header | 300 (fixed) | see below |
| `profile_init.jl` | row count of `debug_results/profile_init/profile_init_summary.csv` minus header | 18 (3 systems × 2 modes × 3 seeds) | see below |
| `generalization_study.jl` | row count of `debug_results/generalization_study/generalization_summary.csv` minus header | 18 (3 systems × 2 variants × 3 seeds) | see below |

Scripts without progress tracking (`generate_manifest.jl`, `aggregate.jl`,
`debug_single.jl`, `run_odebench.jl`) show no ETA.

**Rate calculation:**

Do NOT use total elapsed time / total done — this is skewed by stuck runs.

Instead: read timestamps from the output CSV to compute a rolling rate.

For `experiments/run_experiment.jl`:
- Read all `status.json` files that have `"status":"finished"` and a `"finished_at"` timestamp
- Sort by `finished_at`
- Use the last 20 completed runs to compute the average duration:
  `(finished_at[last] - finished_at[first]) / (count - 1)`
- Remaining = total - done (excluding currently `"running"` or `"failed"` runs)
- ETA = remaining * avg_per_run

For `benchmarks/benchmark_evogrow.jl` and other CSV-based scripts:
- Read the `elapsed_s` column from the output CSV (it exists in summary.csv)
- Use the mean of the last 20 rows' `elapsed_s` as avg_per_run
- Remaining = total - done
- ETA = remaining * avg_per_run

If `elapsed_s` column does not exist: fall back to timestamp delta of the
last 20 rows using the CSV's file modification time divided by done count
(coarse fallback).

**Stuck run detection for `experiments/run_experiment.jl`:**

If any `status.json` has `"status":"running"` and its `started_at` is more than
2 hours ago → add a warning line:
```
           ! 1 Run seit >Xh aktiv (vermutlich haengend): 54_evogrow_v1_seed7
```
In this case, still show ETA based on remaining queued runs (excluding the stuck one),
but mark ETA with `(ohne haengenden Run)`.

**ETA formatting:**

- `< 1h`: show minutes only, e.g. `~43m`
- `1h–48h`: show hours and minutes, e.g. `~11h 22m`
- `> 48h`: show days and hours, e.g. `~2d 7h`
- If done = 0 or rate cannot be computed: show `ETA: unbekannt`
- If stuck and no queued runs remain: show `ETA: haengend`

---

### Requirements

- Standard library only: `re`, `json`, `subprocess`, `sys`, `csv`, `glob`, `pathlib`, `datetime`
- No external dependencies
- Works on Windows (PowerShell available)
- If PowerShell/WMI fails: catch exception, print warning, continue with output-file-only mode
- ROOT is derived from `Path(__file__).resolve().parent.parent`

---

### Do NOT

- Add psutil or any non-stdlib dependency
- Hardcode experiment IDs (use glob patterns like `experiments/*/runs/*/status.json`)
- Modify any existing scripts
- Write unit tests
