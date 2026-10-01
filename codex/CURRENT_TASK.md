# WP-S04 (Fortsetzung 2) — falsche Quelle der sauberen Trajektorie
**Language: Julia**

Auftrag und Abnahme von WP-S04 gelten unverändert. Die Dateien liegen uncommittet im Working Tree.
**Weiterarbeiten, nicht neu anfangen.**

## Befund (Claude, voller Lauf, 2026-10-02)

Die eingebaute Kontrolle gegen C-1 hat angeschlagen, und zwar richtig:

```
ERROR: Clean cap mismatch against C-1 record for system 5, IC1: computed=[4], reference=[2]
```

Ursache: `diagnostic_rows()` in `studies/lookahead/wp_s04_stage_cap_noise_thinning.jl` baut die saubere
Trajektorie mit `_phase_c_solution_trajectory(dataset_rows[system_id], ic_set)`. Das ist die **mit
ODEBench ausgelieferte Lösung**. Die Kampagne rechnet mit **`build_trajectory(system, ic_set)`**
(`studies/regression/run_regression.jl`), integriert selbst mit `Tsit5`, `abstol = reltol = 1e-9`,
auf `system[:t_grid]`. Das ist das Phase-B/C-Protokoll (`CLAUDE.md`, „Phase B sampling protocol“).
Gegenprobe von Claude auf dem Kampagnenpfad: System 5 IC 1 ergibt `[2]`, IC 2 `[nothing]`. Das
stimmt mit C-1 überein.

## Umsetzung

1. Die saubere Trajektorie kommt aus `build_trajectory(phase_c_system(system_id), ic_set)`, genau
   derselben Funktion, die der Kampagnenpfad und `apply_phase_c_data_condition` nutzen.
   `_phase_c_solution_trajectory` wird im Skript nicht mehr verwendet.
2. Prüf, ob das Skript an weiteren Stellen die ausgelieferte Lösung nutzt: wahre rechte Seite, F4,
   Zeitraster. Alles muss auf dem selbst integrierten Raster beruhen.
3. Die Kontrolle gegen C-1 bleibt unverändert hart.

## Verboten

`src/` ändern, Policy ändern, die Kontrolle abschwächen, Git, `docs/`, `codex/CURRENT_TASK.md`
bearbeiten.

## Abnahme

Report ergänzt. `STATUS.md` nach Protokoll (`blocked`, *Umgebung, nicht Sache*). Claude fährt den
vollen Lauf.
