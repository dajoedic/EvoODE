# ODEBench End-to-End, Version 2: Glättung statt Interpolation beim Annihilator

**Eingefroren am 2026-10-07, vor dem ersten Lauf von v2.** Auf Wunsch des Nutzers nach der Zwischenauswertung von v1.
Grundlage ist `docs/ODEBENCH_END2END.md` (v1). **Alles, was hier nicht geändert wird, gilt aus v1 unverändert:**

- Systeme, Daten, Rauschen und Seeds;
- die Protokolle P1/P2 und die gemeinsame Auswahlregel;
- die Kandidaten, die Baselines und die Metriken;
- keine Entscheidungsregel, Bericht vollständig (v1 §9).

## Warum eine Version 2

Zwischenstand von v1: Bei $\eta = 0{,}01$ bricht der Annihilator ein, auf der Logistik etwa 4/20 Rekonstruktionen mit
$R^2 \ge 0{,}9$ gegen 20/20 bei SINDy. Die Diagnose vom 07.10. (`results_e2e/diag/diag_noise.{py,out}`) findet zwei
Ursachen:

1. **Die geschätzte Ableitung ist stark verrauscht.** Ihr relativer Fehler gegenüber $f$ liegt bei 56–63 % für die
   Logistik und 140–190 % für Gompertz. Das gehört zur Aufgabe und gilt für SINDy genauso.
2. **Der interpolierende kubische Spline aus v1 §5 lässt dieses Rauschen explodieren.** Nach dem Resampling liegt
   der Fehler bei 350–24 000 %, mit Ausschlägen bis zum 3400-Fachen des wahren Maximums. Lineare Interpolation läge
   bei 32–145 %. Der Spline war für exakte Daten eingeführt worden (Prüfung 2); für verrauschte Daten ist ein
   interpolierendes Verfahren ungeeignet. Das ist ein Aufbaufehler von Claude.

## Die einzige Änderung (ersetzt v1 §5 Punkt 2, nur Annihilator)

- Die Paare $(\tilde x_i, \hat{\dot x}_i)$ werden nach $\tilde x$ sortiert, Paare mit gleichem $\tilde x$ gemittelt.
- Durch diese Punkte wird ein **Glättungsspline** gelegt: `scipy.interpolate.make_smoothing_spline`, kubisch.
  Die Glättungsstärke `lam=None` wählt das Verfahren selbst über GCV, also rein aus den Daten und ohne
  Tuning-Parameter.
- Er wird auf 2000 gleichmäßigen Punkten über $[\min \tilde x, \max \tilde x]$ ausgewertet.
- Domäne und $z$-Normierung bleiben wie in v1.

Bei exakten Daten wählt GCV eine sehr kleine Glättung; die Prüfung 2 (v1 §8) wird mit dieser Änderung wiederholt
und muss für 3, 19 und 21 wieder bestehen (7 bleibt dokumentierte Ausnahme).

## Was übernommen wird

- **Baselines:** SINDy und W-SINDy sind von der Änderung nicht betroffen und laufen deterministisch (gleiche Seeds,
  gleicher Code). Ihre fertigen Records aus v1 (`results_e2e/records.jsonl`) werden übernommen; fehlende rechnet
  der Lauf von v2 mit demselben Code. Ein Test zeigt an einem Task, dass Neuberechnung und übernommener Record
  identisch sind.
- **Annihilator:** wird in v2 vollständig neu gerechnet, auch bei $\eta = 0$, Seeds und Protokolle wie in v1.

## Status von v1

Der Lauf von v1 wurde am 07.10. gegen 16:40 bei 113 von 216 Records angehalten (35 Annihilator, 39 SINDy,
39 W-SINDy), um Rechenzeit für v2 freizumachen. Er lässt sich mit `--run` jederzeit fortsetzen. Seine
Annihilator-Ergebnisse bei $\eta = 0{,}01$ gelten nach der Diagnose als Artefakt des Splines und werden so berichtet.

## Ablauf

1. Codex (WP-E2E-B): Resampling umstellen, Übernahme der Baselines, Prüfung 2 erneut, Tests.
2. Hauptlauf von v2 auf dem Laptop, losgelöst, 7 Worker (etwa 1 GB je Worker).
3. Bericht nach v1 §9 für v2, zusammen mit dem Zwischenstand von v1, in `docs/ODEBENCH_END2END_RESULT.md`.

## Ergebnis

*(nach dem Lauf)*
