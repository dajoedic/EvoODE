# READ_THIS_FIRST.md — Übergabe der Annihilator-Spur

**Was dieses Dokument ist:** der flüchtige Zustand zwischen zwei Sitzungen dieser Spur: was läuft, was offen ist,
welche Entscheidung ansteht. Wird **immer vollständig überschrieben**. Dauerhaftes gehört in `CLAUDE.md`,
`docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` oder `DIARY.md`. EvoGrow und Paper 1 stehen in `..\EvoODE\READ_THIS_FIRST.md`,
nicht hier.

**Stand: 2026-10-07, 22:15. Auf dem Laptop läuft über Nacht der End-to-End-Vergleich (erst v2, dann die Fortsetzung
von v1). Morgen: Ergebnis prüfen, Bericht schreiben, der Nutzer entscheidet über den Abschluss von Idee #1.**

## 1. Was gerade läuft

- **Kette** `experiments/annihilator_odebench_smoke/run_chain_e2e.ps1` (PowerShell-PID 6120), losgelöst gestartet am
  07.10. um 16:37. Protokoll: `experiments/annihilator_odebench_smoke/results_e2e_v2/chain.log`.
  1. **End-to-End v2** (`docs/ODEBENCH_END2END_v2.md`): 7 Worker, Annihilator mit Abschnitten und
     GCV-Glättungsspline, Baselines aus v1 übernommen (78 Records). Ergebnisordner `results_e2e_v2/`, fertig bei
     `results_e2e_v2/DONE`, bei Fehler `FAILED`. **Erwartet gegen 03:45** (Stand 23:55: 20 von 72 Annihilator-Fits, 12–41 min je Fit nach dem Standby).
  2. Danach automatisch die **Fortsetzung von v1** (`docs/ODEBENCH_END2END.md`, interpolierender Spline): 103
     fehlende Records, Ergebnisordner `results_e2e/`, fertig bei `results_e2e/DONE`. **Erwartet gegen 06:30–07:00.** Der
     v1-Pfad im heutigen Code ist bitgleich zum Stand beim Anhalten (`2bbc6b7`), von Claude geprüft am 07.10.
- **Standby:** Der Laptop war von 17:02 bis 22:03 zugeklappt (Modern Standby), der Lauf stand still. Seit 22:03
  rechnet er wieder. Wachhalte-Skript und Wächter hat der Nutzer abbestellt (00:00); `keep_awake.ps1` liegt nur noch
  im Repository. Geht der Laptop wieder in den Standby, steht der Lauf still und setzt beim Aufwachen fort.
- **Wenn morgen etwas nicht fertig ist:** In `chain.log` steht, welche Stufe läuft, in `run.log` die Records mit
  Sekunden. Gescheiterte Einzel-Fits stehen in `failed_tasks.jsonl` der jeweiligen Stufe. Ein erneutes `--run` mit
  derselben `--spec` setzt fort und überspringt fertige Records:
  - v2: `python -m experiments.annihilator_odebench_smoke.end2end --spec end2end_v2 --run --workers 7 --detach-marker`
  - v1: `python -m experiments.annihilator_odebench_smoke.end2end --spec end2end_v1 --run --workers 7 --detach-marker`

## 2. Nächste Schritte (morgen)

1. **Prüfen:** `DONE` in `results_e2e_v2/` und `results_e2e/`, Zahl der Records (je 216), `failed_tasks.jsonl`.
   Gescheiterte Fits nachrechnen.
2. **Auswerten:** `--summarize --spec end2end_v2` und `--summarize --spec end2end_v1`. Bericht **vollständig und
   deskriptiv** nach v1 §9 (keine Entscheidungsregel, Nutzer entscheidet):
   - je System, $\eta$ und Methode die Anteile $R^2 \ge 0{,}9$ für Rekonstruktion, Generalisierung P1 und
     Generalisierung P2;
   - Strukturtreffer und Obermengen;
   - die gefundenen Gleichungen;
   - Einordnung: v1 mit Spline-Artefakt, v2 mit Glättung.

   Ziel: `docs/ODEBENCH_END2END_RESULT.md`, außerdem §11 in `docs/ODEBENCH_END2END.md` und §Ergebnis in
   `docs/ODEBENCH_END2END_v2.md`.
3. **Rückblick ergänzen:** §9 in `docs/IDEA_01_RETROSPECTIVE.md` (bisher vorläufig).
4. **Entscheidung des Nutzers:** Idee #1 abschließen oder nicht. Bei Abschluss: Abschlussabschnitt in
   `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md`, `CLAUDE.md` als abgeschlossen markieren, aufräumen (§4).

## 3. Wo wir stehen

**Ausführlich:** `docs/IDEA_01_RETROSPECTIVE.md` (Motivation, Idee, Entwicklung, Gründe des Scheiterns, Lehren;
vorläufig).

| Prüfung | Ergebnis | Dokument |
|---|---|---|
| Gate 2A v1–v3 | v1 nie gelaufen, v2 Stufe K gescheitert, v3 Anhang A nicht bestanden, Anhang B löst K6 aus | `GATE_2A_v3_STAGE_K_RESULT.md` |
| Diagnose `AMBIGUOUS` | negativ, 118/118 eindeutige N1-Antworten falsch | `DIAGNOSTIC_AMBIGUITY_RESULT.md` |
| Reality-Check A | `STRONG_NEGATIVE`, direkte Regression trifft F4/F5/F8 in 60/60 | `REALITY_CHECK_DIRECT_REGRESSION_RESULT.md` |
| ODEBench-Smoke-Test (Oracle-$f$) | Verdikt „beenden“ (A): rauschfrei 2/4, bei 1 % 0/4 exakt; der Testfehler-Vorsprung kam vom Oracle-$f$ | `ODEBENCH_SMOKE_TEST_RESULT.md` |
| End-to-End v1 | angehalten bei 113/216 (läuft jetzt weiter) | `ODEBENCH_END2END.md` |
| End-to-End v2 | läuft | `ODEBENCH_END2END_v2.md` |

**Zwischenstand End-to-End v1** (Systeme 3 und 7):

- Rauschfrei liegen alle drei Methoden etwa gleichauf.
- Bei 1 % bricht der Annihilator ein, Logistik-Rekonstruktion 4/20 gegen SINDy 20/20.
- Ursache sind die stark verrauschte Ableitungsschätzung (Fehler 56–190 %) und der interpolierende Spline, der das
  Rauschen vervielfacht (Aufbaufehler, in v2 behoben).
- Kernpunkt aus der Diskussion vom 07.10.: Die schwache Form des Annihilators integriert in $x$ und beseitigt
  Ableitungen von $f$, nicht die Zeitableitung $\dot x$. End-to-End ist die Methode deshalb auf eine
  Ableitungsschätzung angewiesen wie SINDy, während W-SINDy sie vermeidet.

## 4. Was noch liegt

- **Kein Codex-Auftrag aktiv.**
- **Orion:** Der abgeschlossene Job `annihilator-diag-amb` steht noch (Pods `Completed`, keine Ressourcen). Löschen
  mit `oc delete job annihilator-diag-amb`. Die Originaldaten der Diagnose bleiben auf dem NFS unter
  `/bigdata/data-science/joedicke/annihilator_diag_amb/`; eine lokale Kopie ist committet.
- **⚠ Große Datei im Git-Verlauf, vor dem nächsten Push lösen:** `results_e2e/records.jsonl` (v1, 113 Records,
  etwa 490 MB) wurde in Commit `2dfd44b` committet. GitHub lehnt Dateien über 100 MB ab; der Push schlägt dann fehl.
  Optionen:
  - die Commits seit `2dfd44b` lokal umschreiben und die Datei durch eine verkleinerte Fassung ersetzen (zum
    Beispiel ohne `candidate_validations`, gzip-komprimiert);
  - Git LFS.

  Die Datei ist so groß, weil jeder Record alle Kandidaten-Validierungen mit Koeffizienten speichert.
  `results_e2e_v2/records.jsonl` wird genauso groß. Vor dem Commit beider Endstände entscheiden.
- **Temp-Ordner** aus Codex' Testläufen (`.pytest_tmp*`, `.pytest-tmp`, `.codex_tmp/`): nicht committen, löschen.
- **Entscheidungen des Nutzers:**
  - `PRACTICAL_ANNIHILATOR_BENCHMARK.md` (uncommittet, Entwurf des Nutzers): zur Akte oder verwerfen;
  - Orakel-Teil 12/18 und Worker-Caches der v2-Abnahme (`experiments/annihilator_gate2a_v2/results/acceptance/`):
    committen oder löschen.
