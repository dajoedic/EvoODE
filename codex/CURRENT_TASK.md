# WP-N38 (Fortsetzung 3) — Strukturmetriken im ODEFormer-Rauschlauf sind leer
**Language: Python**

**Zuerst dieses Paket, danach WP-N39.** WP-N39 (PySR) ist am Nutzungslimit abgebrochen. Die
Teiländerung an `baselines/harness.py` liegt uncommittet im Tree. **Nicht verwerfen, nicht
anfassen**, außer diese Aufgabe braucht es zwingend. Dann im Report vermerken. Die Spezifikation
von WP-N39 kommt danach wieder in diese Datei.

## Befund (Claude, voller Stufenlauf, 2026-10-02)

`outputs/wp_n38_noise_odeformer/stages/details.csv`: 240/240 `success`, alle 20 Hashes verifiziert,
R²-Werte plausibel. Aber **in allen Records sind `active_terms_raw`, `active_terms_pruned` und
`true_terms` leer (`[]`)**. Damit sind `structure_hit_*` und `odeformer_structure_hit_*` überall
`False`. Beispiel: System 1, σ 0,01, `beam10_noopt` liefert `0.2812 - 0.3557*x_0`. Das ist die wahre
Struktur `[1, u1]`, gemeldet wird aber „kein Treffer“. System 17 liefert `x_0*(0.3965 -
0.0041*x_0)`, ebenfalls die wahre Struktur `[u1, u1^2]`. Auch die Records des Referenzrasters
(`reference_orion_55e9c75/records.jsonl`) haben `active_terms_raw = []`. Strukturtreffer für
ODEFormer wurden also bisher anderswo berechnet (WP-N31-Paarung, `codex/reports/REPORT_WP_N31.md`)
oder gar nicht.

## Umsetzung

1. Finde heraus, wo und wie WP-N31 die ODEFormer-Strukturtreffer berechnet hat (Code, nicht nur der
   Report). Gibt es dort eine kanonische Expansion von ODEFormer-Ausdrücken auf Basisterme, wird sie
   **wiederverwendet**. Gibt es keine: In `baselines/harness.py` existieren
   `canonicalize_odeformer_expression` und die PySR-Funktionen `pysr_canonical_term` /
   `pysr_active_terms_by_equation`. Daraus eine gemeinsame Expansion bauen (sympy `expand`,
   Abbildung auf die Termnamen von `phase_c_support.json`, Terme außerhalb der Basis als eigener
   Zähler), sodass ODEFormer und später PySR **dieselbe** Funktion nutzen.
2. `true_terms` kommt aus `phase_c_support.json` (wie bei WP-N34/SINDy). Roh = alle Terme mit
   Koeffizient ≠ 0. Gepruned = mit derselben Pruning-Regel wie im Rest von Phase C
   (`max(1e-6, 1e-3·max_abs)` je Gleichung, Quelle zitieren). Treffer nur für exakte Systeme.
3. `run_odeformer_noise.py` füllt die Felder damit. Dazu ein **Nachberechnungsmodus**, der die
   Strukturfelder aus vorhandenen `records.jsonl` neu berechnet und `details.csv`, `summary.csv`
   und die Vergleichstabelle neu schreibt, **ohne ODEFormer erneut zu rufen**. Der Stufenlauf ist
   fertig und wird nicht wiederholt.
4. Tests: System 1 `0.2812 - 0.3557*x_0` → `[1, u1]`, Treffer roh und gepruned. System 17
   `x_0*(0.3965 - 0.0041*x_0)` → `[u1, u1^2]`, Treffer. Ein Ausdruck mit einem Bruch (System 24
   liefert z. B. `(-7.64*x_0**2 + 2.02*x_0 - 0.0284)/(…)`) → außerhalb der Basis, kein Treffer,
   kein Absturz. `sin`/`cos`-Terme werden richtig erkannt.

## Verboten

ODEFormer neu laufen lassen. Pruning-Regel erfinden oder anpassen. Ergebnisdateien des
Referenzrasters ändern. Git, `oc`, `codex/CURRENT_TASK.md` bearbeiten.

## Abnahme

Nachberechnung auf `outputs/wp_n38_noise_odeformer/stages/` ausgeführt (Python, das kannst du
selbst). Im Report: Strukturtreffer roh/gepruned je System, Bedingung und Konfiguration (n von 3),
und welche WP-N31-Zahlen von derselben Expansion abhängen. Tests grün. `STATUS.md` nach Protokoll.
