# WP-N25c — Die Kostenschranke der C-5-Skripte auf die gesamte Zellzeit umstellen
**Language: Julia**

## Ausführung

Julia ist in der Codex-Umgebung nicht ausführbar (`codex/CODEX_PROTOCOL.md`). Code und Tests
schreiben, **nicht ausführen**, und mit `status: blocked` plus dem Vermerk „Julia-Ausführung durch
Claude“ melden. Claude führt die Tests und die Abnahmeläufe aus. Keine Git-Operationen.

## Ausgangslage

`--estimate-cost` in `wp_n3_oracle_refit.jl`, `wp_n4_multistart_refit.jl` und
`wp_n5_ic_generalization.jl` schätzt eine Planungsobergrenze pro Zelle als
Fits pro Zelle × Loss-Evaluations-Budget × Sekunden pro Loss-Evaluation. Die Sekunden pro
Loss-Evaluation kommen aus `wp_n25_loss_eval_seconds` in
`studies/regression/wp_n25_phase_c_c5_common.jl` und werden als
`total_parameter_optimization_time_s / total_loss_evals` berechnet.

Das ist falsch. `total_parameter_optimization_time_s` ist in `src/structure/evogrow.jl`
`total_fit_time_s - total_solve_time_s`, also **ohne** die ODE-Integrationen. Die Integrationen
dominieren auf dim 3 um drei Größenordnungen. Die Schranke war dadurch viel zu niedrig. Richtig
ist die gemessene gesamte Zellzeit: `elapsed_s / total_loss_evals`. Sie enthält alles, was eine
Loss-Evaluation kostet.

Von Hand nachgerechnet, über 175 der 180 exakten C-1-Zellen: Oracle-Refit etwa **92 h**,
Restart-Kurve bei k = 10 etwa **305 h**, davon dim 3 71 h bzw. 238 h. Die teuerste Einzelzelle
liegt bei etwa 17 h. Stand: `docs/paper1_phaseC_benchmark_plan.md`, Absatz unter der Kostentabelle.

## Was zu tun ist

1. `wp_n25_loss_eval_seconds` nimmt `elapsed_s` statt `total_parameter_optimization_time_s`.
   Fehlt `elapsed_s`, ist es nicht endlich oder nicht positiv → Abbruch mit Zell-Schlüssel, wie
   bisher bei `total_loss_evals`.
2. Die Ausgabespalte `campaign_loss_eval_s` bekommt einen Namen, der die Quelle sagt, z. B.
   `campaign_elapsed_s_per_loss_eval`. Die Kopfzeile „Planning cost estimate only; not runtime
   evidence.“ bleibt, und die Ausgabe sagt zusätzlich in einer Zeile, dass die Quelle `elapsed_s`
   ist (Kapazitätsplanung, keine Evidenz, Designprinzip 7).
3. Prüfen, ob `wp_n5_ic_generalization.jl --estimate-cost` dieselbe Funktion oder eine eigene
   Rechnung mit `total_parameter_optimization_time_s` benutzt. Wenn ja: gleich behandeln.
   Sonst unverändert lassen und im Report sagen, was es rechnet.
4. Im gesamten Repository nach weiteren Stellen suchen, an denen
   `total_parameter_optimization_time_s` als Kosten pro Loss-Evaluation oder als Zellkosten
   verwendet wird (außerhalb von `src/`, das das Feld nur schreibt). Nur **auflisten** im Report,
   nicht ändern.
5. `test/test_wp_n25_phase_c_c5.jl`: Test, dass die Schranke aus `elapsed_s` gerechnet wird. Der
   Test-Record hat unterschiedliche Werte für `elapsed_s` und
   `total_parameter_optimization_time_s`, und das Ergebnis muss dem `elapsed_s`-Wert folgen. Dazu
   ein Test für den Abbruch bei fehlendem oder nicht positivem `elapsed_s`.
6. `SCRIPTS.md`, Abschnitt C-5: ein Satz, dass `--estimate-cost` aus `elapsed_s` rechnet und eine
   Obergrenze unter der Annahme ist, dass jeder Fit sein Budget ausschöpft.

## Verboten

- Keine Git-Operationen.
- Nichts an `src/` ändern. Das Feld `total_parameter_optimization_time_s` bleibt, wie es ist.
- Nichts an der Refit-Logik, an den Records oder an den Ausgaben außer dem Kostenmodus ändern.
- Keine Refits starten. Nur `--estimate-cost` ist ein zulässiger Probelauf, und den macht Claude.
- Nichts unter `analysis/data/` oder `analysis/tables/` schreiben.

## Abnahme (führt Claude aus)

1. `julia --project=. --startup-file=no test/test_wp_n25_phase_c_c5.jl` grün.
2. `--estimate-cost` für WP-N3 und WP-N4 (`--starts 10`) auf
   `outputs/phase_c_dryrun_2026-09-25/history.jsonl` liefert Summen in der Größenordnung 92 h bzw.
   305 h (Abweichung durch andere Zellmenge erlaubt, im Report zu erklären).
3. Report `codex/reports/REPORT_WP_N25c.md`: geänderte Dateien, die Liste aus Punkt 4, die Befehle
   für Claude, was nicht verifiziert ist.
