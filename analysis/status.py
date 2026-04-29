import csv
import glob
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_MD = ROOT / "SCRIPTS.md"

OUTPUT_PATTERNS = {
    "experiments/run_experiment.jl": ["experiments/*/runs/*/status.json"],
    "experiments/generate_manifest.jl": ["experiments/*/manifest.json"],
    "experiments/aggregate.jl": ["experiments/*/run_registry.csv"],
    "benchmarks/benchmark_evogrow.jl": ["benchmarks/results/summary.csv"],
    "benchmarks/run_odebench.jl": ["benchmarks/results/**/*.csv"],
    "profile_init.jl": ["debug_results/profile_init/profile_init_summary.csv"],
    "generalization_study.jl": [
        "debug_results/generalization_study/generalization_summary.csv"
    ],
    "debug_single.jl": ["debug_results/debug_single/debug_lotka.log"],
}

PARENT_CMDLINE_NAMES = {"julialauncher.exe", "bash.exe", "sh.exe"}
ACTIVE_OUTPUT_WINDOW = timedelta(minutes=90)
STUCK_RUN_WINDOW = timedelta(hours=2)


def parse_scripts_md():
    if not SCRIPTS_MD.exists():
        raise FileNotFoundError(f"Missing {SCRIPTS_MD}")

    text = SCRIPTS_MD.read_text(encoding="utf-8")
    code_blocks = re.findall(r"```(?:\w+)?\s*(.*?)```", text, flags=re.DOTALL)
    command_pattern = re.compile(
        r"\bjulia(?:\s+--project(?:=\S+)?)?\s+([^\s`'\"]+\.jl)\b"
    )

    scripts = []
    seen = set()
    for block in code_blocks:
        for match in command_pattern.finditer(block):
            script = match.group(1).replace("\\", "/")
            if script not in seen:
                seen.add(script)
                scripts.append(script)
    return scripts


def get_julia_processes():
    script = r"""
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
"""
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return [], f"PowerShell/WMI konnte nicht ausgefuehrt werden: {exc}"

    if completed.returncode != 0:
        msg = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        return [], f"PowerShell/WMI fehlgeschlagen: {msg}"

    output = completed.stdout.strip()
    if not output:
        return [], None

    try:
        parsed = json.loads(output)
    except json.JSONDecodeError as exc:
        return [], f"PowerShell/WMI JSON konnte nicht gelesen werden: {exc}"

    if isinstance(parsed, dict):
        return [parsed], None
    if isinstance(parsed, list):
        return parsed, None
    return [], f"Unerwartetes PowerShell/WMI JSON-Format: {type(parsed).__name__}"


def parse_datetime(value):
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def localize_for_age(dt):
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone().replace(tzinfo=None)
    return dt


def format_timestamp(dt):
    if dt is None:
        return "?"
    return localize_for_age(dt).strftime("%Y-%m-%d %H:%M")


def format_age(dt, now=None):
    if dt is None:
        return "?"
    now = now or datetime.now()
    delta = now - localize_for_age(dt)
    seconds = max(0, int(delta.total_seconds()))
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24

    if days:
        rem_hours = hours % 24
        return f"{days}d {rem_hours}h" if rem_hours else f"{days}d"
    if hours:
        rem_minutes = minutes % 60
        return f"{hours}h {rem_minutes}m" if rem_minutes else f"{hours}h"
    if minutes:
        return f"{minutes}m"
    return f"{seconds}s"


def format_eta(seconds):
    if seconds is None:
        return "unbekannt"
    minutes = (max(0, int(seconds)) + 59) // 60
    if minutes < 60:
        return f"~{minutes}m"

    hours = minutes // 60
    rem_minutes = minutes % 60
    if hours < 48:
        return f"~{hours}h {rem_minutes}m" if rem_minutes else f"~{hours}h"

    days = hours // 24
    rem_hours = hours % 24
    return f"~{days}d {rem_hours}h" if rem_hours else f"~{days}d"


def format_avg_per_run(seconds):
    if seconds is None:
        return "?"
    if seconds < 60:
        return f"{seconds:.0f} s/Run"
    return f"{seconds / 60:.1f} min/Run"


def normalize_name(value):
    return (value or "").strip().lower()


def effective_cmdline(proc):
    parent_name = normalize_name(proc.get("ParentName"))
    if parent_name in PARENT_CMDLINE_NAMES:
        return proc.get("ParentCmdLine") or ""
    return proc.get("CmdLine") or ""


def classify_process(proc, scripts):
    parent_name = normalize_name(proc.get("ParentName"))
    if parent_name == "code.exe":
        return None, "VS Code / REPL (nicht zuordenbar)", proc.get("CmdLine") or ""

    cmdline = effective_cmdline(proc)
    cmdline_lower = cmdline.lower()
    for script in scripts:
        if Path(script).name.lower() in cmdline_lower:
            return script, None, cmdline

    return None, "unbekanntes Skript", cmdline


def match_processes(processes, scripts):
    running_by_script = {script: [] for script in scripts}
    unmatched = []

    for proc in processes:
        script, reason, cmdline = classify_process(proc, scripts)
        enriched = dict(proc)
        enriched["EffectiveCmdLine"] = cmdline
        enriched["Reason"] = reason
        if script is None:
            unmatched.append(enriched)
        else:
            running_by_script[script].append(enriched)

    return running_by_script, unmatched


def newest_matching_file(pattern):
    matches = []
    for path in glob.glob(str(ROOT / pattern), recursive=True):
        candidate = Path(path)
        if candidate.is_file():
            matches.append(candidate)
    return max(matches, key=lambda path: path.stat().st_mtime) if matches else None


def newest_output_for_script(script):
    newest = None
    for pattern in OUTPUT_PATTERNS.get(script, []):
        candidate = newest_matching_file(pattern)
        if candidate is None:
            continue
        if newest is None or candidate.stat().st_mtime > newest.stat().st_mtime:
            newest = candidate
    return newest


def build_output_info(scripts):
    output_info = {}
    for script in scripts:
        path = newest_output_for_script(script)
        modified = datetime.fromtimestamp(path.stat().st_mtime) if path else None
        output_info[script] = {"path": path, "modified": modified}
    return output_info


def display_path(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def output_status(script, output_info, now, active=False):
    info = output_info.get(script, {})
    path = info.get("path")
    if path is None:
        return "(kein Output gefunden)"
    label = "Output aktiv" if active else "Output"
    modified = info.get("modified")
    return (
        f"{label}: {display_path(path)}"
        f"  ({format_timestamp(modified)}; vor {format_age(modified, now)})"
    )


def is_unidentifiable_orphan(proc):
    if proc.get("Reason") != "unbekanntes Skript":
        return False
    parent = normalize_name(proc.get("ParentName"))
    return parent in {"?", "", "cmd.exe", "powershell.exe", "pwsh.exe"}


def infer_active_scripts(scripts, running_by_script, unmatched, output_info, now):
    has_orphan = any(is_unidentifiable_orphan(proc) for proc in unmatched)
    inferred = set()
    if not has_orphan:
        return inferred

    for script in scripts:
        if running_by_script.get(script):
            continue
        modified = output_info.get(script, {}).get("modified")
        if modified is not None and now - localize_for_age(modified) <= ACTIVE_OUTPUT_WINDOW:
            inferred.add(script)
    return inferred


def read_json_file(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def experiment_progress(now):
    run_dirs = [
        Path(path)
        for path in glob.glob(str(ROOT / "experiments/*/runs/*"))
        if Path(path).is_dir()
    ]
    total = len(run_dirs)
    done = 0
    failed = 0
    running = []
    finished_times = []

    for run_dir in run_dirs:
        status = read_json_file(run_dir / "status.json")
        if not isinstance(status, dict):
            continue

        state = status.get("status")
        if state == "finished":
            done += 1
            finished_at = parse_datetime(status.get("finished_at"))
            if finished_at is not None:
                finished_times.append(localize_for_age(finished_at))
        elif state == "failed":
            failed += 1
        elif state == "running":
            started_at = parse_datetime(status.get("started_at"))
            running.append({"run_id": run_dir.name, "started_at": localize_for_age(started_at)})

    finished_times.sort()
    avg_seconds = None
    if len(finished_times) >= 2:
        window = finished_times[-20:]
        span = (window[-1] - window[0]).total_seconds()
        if span >= 0 and len(window) > 1:
            avg_seconds = span / (len(window) - 1)

    stuck = [
        item
        for item in running
        if item["started_at"] is not None and now - item["started_at"] > STUCK_RUN_WINDOW
    ]
    remaining = max(total - done - failed - len(running), 0)

    if stuck and remaining == 0:
        eta = "haengend"
    elif avg_seconds is None:
        eta = "unbekannt"
    else:
        eta = format_eta(remaining * avg_seconds)
        if stuck:
            eta = f"{eta} (ohne haengenden Run)"

    warnings = []
    if stuck:
        oldest = min(stuck, key=lambda item: item["started_at"])
        warnings.append(
            f"! {len(stuck)} Run seit >{format_age(oldest['started_at'], now)} aktiv "
            f"(vermutlich haengend): {oldest['run_id']}"
        )

    return {
        "done": done,
        "total": total,
        "avg_seconds": avg_seconds,
        "eta": eta,
        "warnings": warnings,
    }


def read_csv_rows(path):
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            sample = handle.read(4096)
            handle.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=";,")
            except csv.Error:
                dialect = csv.excel
            return list(csv.DictReader(handle, dialect=dialect))
    except OSError:
        return []


def csv_progress(path, total):
    if path is None or not path.exists():
        return {
            "done": 0,
            "total": total,
            "avg_seconds": None,
            "eta": "unbekannt",
            "warnings": [],
        }

    rows = read_csv_rows(path)
    done = len(rows)
    avg_seconds = None
    elapsed_values = []

    if rows and "elapsed_s" in rows[0]:
        for row in rows[-20:]:
            try:
                elapsed_values.append(float(row.get("elapsed_s", "")))
            except (TypeError, ValueError):
                pass

    if elapsed_values:
        avg_seconds = sum(elapsed_values) / len(elapsed_values)
    elif done > 0:
        # Coarse fallback when no per-row timing exists.
        avg_seconds = max(0.0, datetime.now().timestamp() - path.stat().st_mtime) / done

    remaining = max(total - done, 0)
    eta = "unbekannt" if avg_seconds is None else format_eta(remaining * avg_seconds)
    return {
        "done": done,
        "total": total,
        "avg_seconds": avg_seconds,
        "eta": eta,
        "warnings": [],
    }


def build_progress_info(scripts, output_info, now):
    progress = {}
    for script in scripts:
        path = output_info.get(script, {}).get("path")
        if script == "experiments/run_experiment.jl":
            progress[script] = experiment_progress(now)
        elif script == "benchmarks/benchmark_evogrow.jl":
            progress[script] = csv_progress(path, 300)
        elif script == "profile_init.jl":
            progress[script] = csv_progress(path, 18)
        elif script == "generalization_study.jl":
            progress[script] = csv_progress(path, 18)
    return progress


def progress_lines(script, progress_info):
    info = progress_info.get(script)
    if not info:
        return []

    lines = [
        f"Fortschritt: {info['done']}/{info['total']}  |  "
        f"avg {format_avg_per_run(info.get('avg_seconds'))}  |  ETA: {info['eta']}"
    ]
    lines.extend(info.get("warnings", []))
    return lines


def print_header(now, scripts, processes, running_by_script, unmatched):
    matched_processes = sum(len(items) for items in running_by_script.values())
    unknown_processes = len(unmatched)
    print("=" * 58)
    print(f"  EvoODE Study Status - {now.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 58)
    print()
    print(f"  Skripte in SCRIPTS.md : {len(scripts)}")
    print(
        f"  Julia-Prozesse gesamt : {len(processes)}"
        f"  (davon zuordenbar: {matched_processes}, unbekannt: {unknown_processes})"
    )
    print()


def script_sort_key(script, running_by_script, inferred):
    if running_by_script.get(script):
        return 0
    if script in inferred:
        return 1
    return 2


def print_known_scripts(scripts, running_by_script, inferred, output_info, progress_info, now):
    print("  Bekannte Skripte")
    print("  " + "-" * 54)
    ordered_scripts = sorted(
        enumerate(scripts),
        key=lambda item: (script_sort_key(item[1], running_by_script, inferred), item[0]),
    )

    for _, script in ordered_scripts:
        processes = running_by_script.get(script, [])
        if processes:
            print(f"  [LAEUFT]  {script}")
            for proc in processes:
                created = parse_datetime(proc.get("Created"))
                print(
                    f"           PID {proc.get('PID', '?')}  |  seit "
                    f"{format_timestamp(created)}  ({format_age(created, now)})"
                )
                cmdline = (proc.get("EffectiveCmdLine") or "").strip()
                if cmdline:
                    print(f"           {cmdline}")
            print(f"           {output_status(script, output_info, now)}")
        elif script in inferred:
            print(f"  [LAEUFT?] {script}")
            print(f"           {output_status(script, output_info, now, active=True)}")
        else:
            print(f"  [idle]    {script}")
            print(f"           {output_status(script, output_info, now)}")

        for line in progress_lines(script, progress_info):
            print(f"           {line}")

        if script in inferred and not processes:
            print(
                "           (Prozess laeuft, aber cmd.exe-Orphan - "
                "Script nicht direkt zuordenbar)"
            )
        print()


def print_unmatched(unmatched, now):
    if not unmatched:
        return
    print("  Weitere Julia-Prozesse (nicht zuordenbar)")
    print("  " + "-" * 54)
    for proc in unmatched:
        created = parse_datetime(proc.get("Created"))
        parent = proc.get("ParentName") or "?"
        reason = proc.get("Reason") or "unbekanntes Skript"
        print(
            f"  PID {proc.get('PID', '?')}  |  seit {format_timestamp(created)}"
            f"  ({format_age(created, now)})  |  Elternprozess: {parent}"
        )
        print(f"      {reason}")
    print()


def main():
    now = datetime.now()
    try:
        scripts = parse_scripts_md()
    except OSError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1

    processes, warning = get_julia_processes()
    running_by_script, unmatched = match_processes(processes, scripts)
    output_info = build_output_info(scripts)
    inferred = infer_active_scripts(scripts, running_by_script, unmatched, output_info, now)
    progress_info = build_progress_info(scripts, output_info, now)

    if warning:
        print(f"Warnung: {warning}", file=sys.stderr)
        print("Fahre im Output-Datei-Modus fort.", file=sys.stderr)
        print(file=sys.stderr)

    print_header(now, scripts, processes, running_by_script, unmatched)
    print_known_scripts(scripts, running_by_script, inferred, output_info, progress_info, now)
    print_unmatched(unmatched, now)
    return 0


if __name__ == "__main__":
    sys.exit(main())
