# WP-S04 (Fortsetzung) — Laufzeitfehler beheben
**Language: Julia**

Der Auftrag und die Abnahme von WP-S04 gelten unverändert (Fragen F1–F4, Kontrollen, Report
`codex/reports/REPORT_WP_S04.md`). Die Dateien liegen uncommittet im Working Tree. **Weiterarbeiten,
nicht neu anfangen.**

## Befund (Claude, erster Lauf, 2026-10-02)

```
julia --project=. --startup-file=no studies/lookahead/wp_s04_stage_cap_noise_thinning.jl --limit 2
ERROR: LoadError: UndefVarError: `_cap_estimate_derivatives` not defined in `Main`
in expression starting at studies/lookahead/wp_s04_stage_cap_noise_thinning.jl:447 (Aufruf aus Zeile 448)
```

Die internen Funktionen der Kappe (`_cap_estimate_derivatives`, `_cap_splits`, `_cap_fit_eval`,
`_cap_richardson_error_estimate`, `_cap_cumulative_stage_idxs` usw.) sind nicht exportiert. Sie müssen
als `EvoODE.<name>` aufgerufen werden, so wie andere Skripte unter `studies/lookahead/` das tun (dort
nachsehen und dieselbe Form verwenden).

**Hinweis zum Environment:** Seit WP-N36 (`dc17a46`) gibt es `DifferentialEquations` nicht mehr, sondern
`OrdinaryDiffEq`. Prüf, dass das Skript kein `using DifferentialEquations` enthält.

## Umsetzung

Geh das **ganze Skript** auf diese Fehlerklasse durch: jeder Aufruf eines nicht exportierten Namens aus
`EvoODE`, jedes fehlende `include`, jeder Zugriff auf Felder, die fehlen können (siehe
`codex/CODEX_PROTOCOL.md`, „Julia kann in dieser Umgebung nicht ausgeführt werden“). Korrigieren und im
Report auflisten.

## Verboten

`src/` ändern, Policy-Parameter ändern, Git, `docs/`, `codex/CURRENT_TASK.md` bearbeiten.

## Abnahme

Report ergänzt um die Liste der korrigierten Stellen. `STATUS.md` nach Protokoll (`blocked`,
*Umgebung, nicht Sache*). Claude fährt danach `--limit 2` und den vollen Lauf.
