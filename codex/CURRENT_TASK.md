# WP-T1f-c — WP-T1f ohne Parameter-Kappung
**Language: Julia**

## Ausführung

Codex kann in dieser Umgebung kein Julia ausführen (`codex/CODEX_PROTOCOL.md`). Umsetzen, Befehle für
Claude im Report auflisten, Status `blocked` melden. Keine Git-Operationen, kein `oc`/`kubectl`,
kein Lauf der Probe.

## Ausgangslage

WP-T1f und WP-T1f-b sind umgesetzt und liegen uncommittet im Working Tree
(`codex/reports/REPORT_WP_T1f.md`, `REPORT_WP_T1f_b.md`). Claude hat `--control-only` über alle 36
Zellen laufen lassen: **12 dim-3-Zellen liegen über der Grenze 1e-4**, bis zu 2.800 (Lorenz 55).

**Ursache:** Der Phase-C-Referenzoptimierer (`build_reference_optimizer` in
`studies/regression/run_regression.jl`) setzt `clamp_val = BFGS_CLAMP_VAL = 10.0`, und die
Simulation kappt jeden Parameter vorher auf [−10, 10] (`src/optimize/bfgs.jl`, `src/simulate/solve.jl`).
Die Systeme 54, 55, 56, 57, 58 und 59 brauchen Koeffizienten mit |c| > 10 (12, 99,96, 28, −28,5).
Die Koeffizienten-Zuordnung ist korrekt; sie wurde gegen die ODEBench-Gleichungen geprüft.

**Entscheidung des Nutzers (2026-09-28):** WP-T1f fragt, ob der **Loss** die Wahrheit identifiziert.
Die Kappung ist eine Schranke des **Optimierers**. WP-T1f läuft deshalb **für alle 36 Zellen und alle
Fit-Rollen ohne Kappung** (`clamp_val = Inf`), sonst identisch zum Phase-C-Optimierer. Ein Arm, kein
Vergleichsarm mit Kappung.

## Was zu tun ist

1. **Optimierer:** WP-T1f baut seinen Optimierer als Kopie des Phase-C-Referenzoptimierers, bei der
   **nur** `clamp_val` auf `Inf` gesetzt ist. Alle anderen Felder (Iterationen, Toleranzen,
   `max_loss_evals`, `reject_nonfinite`, `divergence_limit`, `max_fit_attempts`) werden vom
   Referenzoptimierer übernommen, nicht neu hingeschrieben, damit sie nicht auseinanderlaufen können.
   Das gilt für Kontrolle, Boden, warme Nachbarn und `truth_cold`.
2. **Durchreichen:** `fit_fixed_structure_phase_c` in `wp_t1d_neighbourhood_loss.jl` bekommt dafür
   höchstens einen weiteren optionalen Parameter mit einem Default, der das bisherige Verhalten exakt
   erhält (wie `p0` und `max_fit_attempts` in WP-T1f). Die Simulation für R² und Koeffizienten in
   dieser Funktion muss denselben Optimierer und damit dieselbe Kappung verwenden wie der Fit.
3. **Identität sichtbar machen:** Jede WP-T1f-Rohzeile trägt `clamp_val` (als Zahl bzw. `"Inf"`)
   und ein Feld `optimizer_variant = "phase_c_reference_unclamped"`. Das bisherige Feld
   `config_fingerprint` heißt in WP-T1f-Zeilen `phase_c_config_fingerprint` (derselbe Wert wie
   bisher); dazu kommt `wp_t1f_config_fingerprint`, ein Hash über den Phase-C-Fingerprint, die
   Optimierervariante, `clamp_val`, m, die Margins und die Schwellen. Die Aggregation liest beide
   Namen, damit die alten `cold_reference`-Zeilen (Feld `config_fingerprint`) weiter funktionieren.
4. **Kontrollmodus:** `--control-only` und die Kontrolle in jeder Zelle rechnen ebenfalls ohne
   Kappung. Die Grenze 1e-4 bleibt.
5. **Self-Test:** ein Fall, der prüft, dass der WP-T1f-Optimierer `clamp_val = Inf` hat und in allen
   übrigen Feldern dem Referenzoptimierer gleicht.
6. **`SCRIPTS.md`** und der Kommentar im Kampagnen-Manifest: ein Satz, dass WP-T1f ohne Kappung
   läuft und warum.

## Verboten

- Keine Änderung an `src/`, an `run_regression.jl`, an `phase_c_config.jl` oder an
  `BFGS_CLAMP_VAL`. Der Phase-C-Pfad bleibt bitgleich.
- Keine Änderung an Schwellen, m, Margins, Budget, Retry-Regel, Toleranzen.
- Das Verhalten von `wp_t1d_neighbourhood_loss.jl` bei Default-Aufruf bleibt unverändert.

## Abnahme

1. `test/test_wp_t1f_warm_neighbourhood.jl` erweitert: Optimierer-Gleichheit bis auf `clamp_val`;
   eine Rohzeile trägt `clamp_val`, `optimizer_variant` und beide Fingerprints; die Aggregation
   verarbeitet alte und neue Feldnamen.
2. Report `codex/reports/REPORT_WP_T1f_c.md` mit den Julia-Befehlen für Claude: WP-T1d-Test,
   WP-T1f-Test, `--self-test`, `--control-only` (Erwartung: alle 36 Zellen unter 1e-4),
   `--smoke --fresh`.
3. `codex/STATUS.md`: `status: blocked`, WP-T1f-c, Report-Pfad.
