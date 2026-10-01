# WP-N36 — Schlankes Kampagnen-Environment (Track I, I-01)
**Language: Julia** (Project/Manifest, Quellcode-Imports, Package Extensions)

Backlog: `CLAUDE.md`, Track I, I-01. Freigegeben und **dringend** (Nutzer, 2026-10-02). Anlass: Am
2026-10-01 sind die Image-Builds auf dem GitLab-Runner gescheitert. Im letzten Log stehen `✗ Makie`
und `✗ BoundaryValueDiffEqFIRK` beim Vorkompilieren, danach ist der Runner abgestürzt. Das Manifest
hat 443 Pakete. Der Rechenpfad braucht einen Bruchteil davon.

## Ziel

Das Environment, das das Kampagnen-Image baut (`Project.toml` und `Manifest.toml` im Repo-Wurzelverzeichnis,
`containers/Dockerfile`), enthält nur noch, was der Rechenpfad braucht. **Die Numerik ändert
sich nicht, kein Bit.**

## Umsetzung

1. **`DifferentialEquations` durch `OrdinaryDiffEq` ersetzen.** Version **5.64.0**, genau die, die
   heute schon im Manifest steht. Jedes `using DifferentialEquations` im Repo (`src/`, `studies/`,
   `benchmarks/`, `experiments/`, `test/`) wird zu `using OrdinaryDiffEq`. Vorher prüfst du, dass jeder
   genutzte Name (`Tsit5`, `ODEProblem`, `solve`, `ReturnCode`, Callbacks, falls vorhanden, …) von
   `OrdinaryDiffEq` bzw. seinen Re-Exports bereitgestellt wird. Ein Name, der fehlt, ist ein Befund
   im Report, nicht still zu umgehen.
2. **Plotten aus dem Kernmodul.** `src/plotting/plot_solution.jl` (`Plots`) und
   `src/plotting/search_animation.jl` (`CairoMakie`) werden als **Package Extensions** umgesetzt:
   `Plots` und `CairoMakie` wandern in `[weakdeps]`, der Plot-Code nach `ext/`, unter `[extensions]`
   registriert. Die öffentlichen Funktionsnamen bleiben, die Methoden existieren nur, wenn das Paket
   geladen ist. `src/EvoODE.jl` inkludiert die beiden Dateien nicht mehr.
3. **Manifest: nur entfernen, nichts aktualisieren.** Jedes Paket, das im neuen Manifest bleibt,
   hat **dieselbe Version und denselben `git-tree-sha1`** wie heute. Der Report enthält dafür einen
   maschinellen Diff (Python reicht): entfernte Pakete, verbleibende Pakete, und **0 Pakete mit
   geänderter Version oder Hash**. Steht dort etwas anderes als 0, ist das `blocked`.
   Vorgehen: `Pkg.rm` bzw. das Bearbeiten von `Project.toml` mit anschließendem Auflösen **ohne
   Update** (`Pkg.resolve()` darf keine Versionen anheben; wenn doch, abbrechen und melden).
   **Das Auflösen braucht Julia**, und Julia läuft in deiner Sandbox nicht. Dann bereitest du die
   `Project.toml`-Änderung und alle Quellcode-Änderungen vor und schreibst die exakten
   Pkg-Kommandos für Claude in den Report. Den Manifest-Diff liefert ein Python-Skript, das Claude
   nach dem Auflösen ausführt.
4. **`[compat]`** entsprechend anpassen: `DifferentialEquations` raus, `OrdinaryDiffEq = "5.64.0"`
   rein, `Plots` und `CairoMakie` bleiben als Compat der weakdeps.
5. **`SpecialFunctions`** wird nur im Screening (`evogrow_screening.jl`, `loggamma`) gebraucht und
   bleibt. Weitere Pakete entfernst du **nicht** in diesem Paket.

## Verboten

Versionen anheben, `Pkg.update`, andere Pakete entfernen oder hinzufügen als oben genannt,
Methoden- oder Runner-Logik ändern, Fingerprints ändern, Git, `docs/`, `codex/CURRENT_TASK.md`
bearbeiten, Push.

## Abnahme (Claude fährt die Julia-Teile auf dem Laptop)

Im Report stehen die Kommandos dafür, jeweils mit erwarteter Dauer:

1. Pkg-Auflösung und der Manifest-Diff aus Punkt 3: **0 geänderte Versionen oder Hashes**.
2. `test/test_wp_n32_data_condition.jl` grün, darunter `phase_c_fingerprint() == "0c9672de35c75a9d"`.
3. **Stufe 0:** System 1, Seed 42, beide IC-Sets, über `run_batch_cell.jl` mit
   `outputs/wp_n32_stage0/manifest.csv`. `compare_phasec_controls.py` gegen C-1: bitgleich.
4. **Orakel bei Grenze 10, System 1:** mit `outputs/wp_n32_b01/history_sys1.jsonl` bitgleich zu C-5.
5. **Eine C-1-Zelle je Dimension 2 und 3, möglichst billig.** System 24, Seed 42, IC 1, Index 277 im
   C-1-Manifest, für dim 2. Für dim 3 das Orakel auf System 52, Seed 42, IC 1, statt einer
   stundenlangen Suche. Jeweils bitgleich zur Referenz.
6. `using EvoODE` lädt ohne `Plots`/`CairoMakie`. Mit `using Plots` erscheint die Plot-Methode.

Report `codex/reports/REPORT_WP_N36.md`, `STATUS.md` nach Protokoll. Weil Julia nicht ausführbar ist,
ist `blocked` mit dem Vermerk *Umgebung, nicht Sache* der erwartete Abschluss.
