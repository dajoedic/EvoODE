# WP-E2E-A2 — End-to-End: kubischer Spline beim Resampling, Plausibilitätsprüfung 2 nach Spezifikation
**Language: Python**

Grundlage: `docs/ODEBENCH_END2END.md` (Entwurf, §5 Punkt 2 und §8 am 07.10. geändert, **neu lesen**) und
`codex/reports/REPORT_WP_E2E_A.md`. Die Arbeit aus WP-E2E-A liegt uncommittet im Working Tree. Der Status `blocked`
war richtig. Die Diagnose von Claude (`experiments/annihilator_odebench_smoke/results_e2e/diag/`) zeigt: Die lineare
Interpolation war die Ursache bei System 19, und bei System 7 bleibt mit Spline ein Fehler, der als Befund gilt.

## Zu ändern

1. `resample_state_derivative` in `end2end.py`: Statt `np.interp` wird `scipy.interpolate.CubicSpline` (Randbedingung
   not-a-knot, Standard) auf den nach $x$ sortierten, bei gleichem $x$ gemittelten Paaren verwendet. Sonst bleibt
   alles gleich (2000 Punkte, Domäne, $z$-Normierung).
2. `sanity_command`: Prüfung 2 entscheidet `passed` nur über die Systeme 3, 19 und 21. System 7 wird mit allen
   Zahlen weiter berechnet und gespeichert, mit dem Vermerk `"documented_exception": true`, und geht nicht in
   `passed` ein. Prüfung 1 bleibt unverändert.
3. Tests:
   - Resampling mit Spline reproduziert eine glatte synthetische Funktion auf ungleichmäßigen Punkten mit relativem
     Fehler $< 10^{-8}$; Mitteln gleicher $x$ bleibt.
   - Die Ausnahmeregel in der Plausibilitätsprüfung.
   - Bestehende Tests anpassen, wo sie lineare Interpolation voraussetzen.

## Ausführen

Alle Tests (`test_end2end.py`, Smoke-Tests, v3 mit `--basetemp`), dann `--sanity`. **Kein** `--run` auf den
Systemen.

## Verboten

Andere Änderungen an Methode, Auswahlregel, Kandidaten, Library, Seeds oder Toleranzen. Änderungen an bestehenden
Smoke-Dateien, an v3, an `results/`, `results_v2/`, `docs/`. Git-Operationen. Nichts über 15 Minuten.

## Abnahme

1. Alle Tests grün, kein `skip`.
2. `results_e2e/sanity.json`: Prüfung 1 bestanden. Prüfung 2 für 3, 19 und 21 bestanden, System 7 mit Zahlen und
   Ausnahmevermerk, insgesamt `passed: true`. Wenn nicht: `blocked` mit Zahlen.
3. Report `codex/reports/REPORT_WP_E2E_A2.md` mit Testausgabe und Zahlen aus diesem Lauf.
