# WP-N25b — C-5-Skripte laden wieder: Doppel-Include auflösen
**Language: Julia**

## Ausführung

Codex kann kein Julia ausführen. Code schreiben, `blocked` mit Grund "Julia-Ausführung" melden;
Claude führt die Abnahme aus. Nichts starten, was länger als 15 Minuten läuft.

## Ausgangslage

WP-N25 liegt uncommittet im Working Tree (`codex/reports/REPORT_WP_N25.md`). Claudes Abnahme 1
(WP-N1-Bitgleichheit) ist gescheitert: **Alle drei Skripte brechen schon beim Laden ab**, auch ohne
`--campaign`.

```
ERROR: LoadError: UndefVarError: `AbstractBasis` not defined in `Main`
Hint: It looks like two or more modules export different bindings with this name ...
in expression starting at studies/regression/diagnostic_systems.jl:160
in expression starting at studies/regression/run_regression.jl:13
in expression starting at studies/regression/phase_c_trajectory_hashes.jl:7
in expression starting at studies/regression/wp_n25_phase_c_c5_common.jl:1
in expression starting at studies/regression/wp_n5_ic_generalization.jl:11
```

Ursache: `wp_n25_phase_c_c5_common.jl` bindet `phase_c_trajectory_hashes.jl` ein. Das ist ein
eigenständiges Skript mit eigenem `Pkg.activate` und eigenem `include` von `run_regression.jl` und
`phase_c_config.jl`. Die C-5-Skripte haben `run_regression.jl` aber schon selbst eingebunden. Das
zweite Einbinden erzeugt die Mehrdeutigkeit.

WP-N26 ist inzwischen committet (`408f1cd`) und berührt diese Dateien nicht. Nur `SCRIPTS.md`
enthält Abschnitte aus beiden Paketen; die WP-N26-Teile dort bleiben unverändert.

## Was zu tun ist

1. Jede Datei wird genau einmal eingebunden. Was der Helfer aus `phase_c_trajectory_hashes.jl`
   braucht (Hash-Format und Hash-Funktion), wandert in eine Bibliotheksdatei **ohne**
   `Pkg.activate` und ohne eigene `include`s von `run_regression.jl` / `phase_c_config.jl`. Sowohl
   `phase_c_trajectory_hashes.jl` als auch `wp_n25_phase_c_c5_common.jl` nutzen dann diese Datei.
   **Das Verhalten und die Ausgaben von `phase_c_trajectory_hashes.jl` bleiben unverändert**,
   gleiche Hashes für dieselbe Eingabe.
2. Die Reihenfolge der Includes in den drei C-5-Skripten und im Helfer so ordnen, dass
   `phase_c_config.jl` nur einmal geladen wird und keine Definition aus `phase_b_config.jl`
   überschattet oder von ihr überschattet wird. Falls beide Konfigurationen denselben Namen
   definieren, das im Report benennen.
3. Der Test `test/test_wp_n25_phase_c_c5.jl` bindet die Dateien auf dieselbe Weise ein wie die
   Skripte, sodass ein Ladefehler dieser Art im Test auffällt.
4. Report `REPORT_WP_N25.md` um einen Abschnitt "WP-N25b" ergänzen.

## Verboten

- Keine Git-Operationen.
- `phase_c_config.jl`, `run_regression.jl`, `run_k8s_indexed_cell.jl`, `diagnostic_systems.jl`,
  `src/`: nicht ändern. Die Kampagne läuft noch.
- Nichts an der Logik von WP-N25 ändern, was über das Laden hinausgeht.

## Abnahme (Claude führt aus)

Die Abnahme 1–5 aus WP-N25 unverändert, zusätzlich: `phase_c_trajectory_hashes.jl --limit 6`
liefert vor und nach der Änderung byte-identische Hash-Dateien.
