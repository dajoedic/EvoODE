# WP-E2E-B — End-to-End v2: Glättungsspline beim Annihilator, Übernahme der Baseline-Records
**Language: Python**

Grundlage: `docs/ODEBENCH_END2END_v2.md` (eingefroren, vollständig lesen) und `docs/ODEBENCH_END2END.md` (v1, gilt,
soweit v2 nichts ändert). Code: `experiments/annihilator_odebench_smoke/end2end.py` (Stand `2bbc6b7`). Eilig, aber
sorgfältig: Der Nutzer wartet auf die Ergebnisse.

## Zu ändern

1. **Resampling als Version:** Eine Spec-Konstante bzw. ein CLI-Schalter `--spec end2end_v2` (Standard bleibt v1, damit
   v1 fortsetzbar bleibt). In v2 nutzt das Annihilator-Resampling genau das Verfahren aus `docs/ODEBENCH_END2END_v2.md`:
   200 gleich breite Abschnitte über $[\min x, \max x]$, je nicht leerem Abschnitt Mittelwert von $x$ und $\dot x$ und
   Punktzahl; dann `scipy.interpolate.make_smoothing_spline(xb, fb, w=counts, lam=None)`, ausgewertet auf 2000
   gleichmäßigen Punkten. Vorlage: `experiments/annihilator_odebench_smoke/results_e2e/diag/diag_smooth2.py`
   (`binned_smooth`). Scheitert der Spline numerisch, ist der Kandidat bzw. Fit gescheitert (Grund im Record),
   kein Ersatzverfahren.
   Domäne und $z$-Normierung bleiben. Records tragen `spec: "end2end_v2"` und den gewählten `lam` (falls zugänglich,
   sonst den Hinweis, dass GCV verwendet wurde).
2. **Ergebnisordner** für v2: `experiments/annihilator_odebench_smoke/results_e2e_v2/` (Kopie von `setup.json` und
   `reference.json` wie bisher).
3. **Übernahme der Baselines:** Mit `--reuse-baselines-from experiments/annihilator_odebench_smoke/results_e2e` werden
   vor dem Lauf alle gültigen SINDy- und W-SINDy-Records aus v1 nach `results_e2e_v2/records.jsonl` kopiert, mit dem
   Zusatzfeld `reused_from: "end2end_v1"`. Der Lauf rechnet dann nur fehlende Tasks: alle Annihilator-Tasks und die
   fehlenden Baseline-Tasks. Baselines werden mit unverändertem Code gerechnet.
4. **Plausibilitätsprüfung 2 in v2** (`--sanity --spec end2end_v2`, schreibt `results_e2e_v2/sanity.json`): wie in v1
   (exaktes $\dot x$, Referenzklasse vorgegeben), aber: 3 und 21 müssen $< 10^{-4}$ bestehen, 7 **und 19** werden mit
   Zahlen und Ausnahmevermerk gespeichert und gehen nicht in `passed` ein. Prüfung 1
   (synthetisch) ebenfalls wiederholen.
5. **Auswertung** (`--summarize --spec end2end_v2`): wie bisher, auf `results_e2e_v2/records.jsonl`.
6. **Tests:**
   - Abschnitte + Glättungsspline: Auf einer glatten Funktion plus Rauschen ist der Fehler nach dem Resampling
     deutlich kleiner als bei linearer Interpolation; viele fast gleiche $x$-Werte (Häufung) führen nicht zum Absturz.
   - Die Übernahme kopiert nur SINDy/W-SINDy, keine Annihilator-Records, und keine Duplikate.
   - Ein Baseline-Task, neu berechnet, ergibt bitgleich (bis auf `reused_from` und Laufzeitfelder) denselben Record
     wie der übernommene. Synthetisches System; kein Fit auf den Systemen 3/7/19/21.
   - v1-Verhalten unverändert, wenn `--spec` nicht angegeben ist.

## Ausführen

Alle Tests (`test_end2end.py` und die Smoke-Tests; die v3-Tests nur, wenn Code unter v3 berührt wurde, was nicht sein
darf), dann `--sanity --spec end2end_v2`. **Kein** `--run` auf den Systemen.

## Verboten

Jede andere Änderung an Methode, Auswahlregel, Kandidaten, Library, Seeds, Toleranzen oder Metriken. Änderungen an
v3, an `results_e2e/` (v1), `results/`, `results_v2/`, `docs/`. Git-Operationen. Nichts über 15 Minuten.

## Abnahme

1. Alle Tests grün, kein `skip`.
2. `results_e2e_v2/sanity.json` mit beiden Prüfungen; 3 und 21 bestanden, 7 und 19 mit Zahlen. Wenn nicht: `blocked` mit Zahlen.
3. Report `codex/reports/REPORT_WP_E2E_B.md` mit Testausgabe und den Zahlen der Prüfungen.
