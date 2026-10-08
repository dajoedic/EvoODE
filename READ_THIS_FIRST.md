# READ_THIS_FIRST.md — Übergabe der Annihilator-Spur

**Was dieses Dokument ist:** der flüchtige Zustand zwischen zwei Sitzungen dieser Spur: was läuft, was offen ist,
welche Entscheidung ansteht. Wird **immer vollständig überschrieben**. Dauerhaftes gehört in `CLAUDE.md`,
`docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` oder `DIARY.md`. EvoGrow und Paper 1 stehen in `..\EvoODE\READ_THIS_FIRST.md`,
nicht hier.

**Stand: 2026-10-08, vormittags.**

- Der End-to-End-Vergleich ist fertig und ausgewertet.
- Es läuft nichts.
- Die Git-Historie ist bereinigt und pushbereit (§2).
- **Offen:** die Entscheidung des Nutzers über den Abschluss von Idee #1 (§3).

## 1. Ergebnis End-to-End (v1 und v2)

**Bericht:** `docs/ODEBENCH_END2END_RESULT.md`. Kurzfassung in `docs/IDEA_01_RETROSPECTIVE.md` §9.

- **Läufe:** Beide sind vollständig (je 216/216 Records, keine gescheiterten Tasks). v2 endete um 02:18, v1 um 03:29.
- **Rekonstruktion bei 1 %:** Mit Glättung (v2) liegt der Annihilator im Feld der Baselines, mit 17/14/20/19 von 20
  auf den Systemen 3/7/19/21. In v1 waren es 4/0/5/4, ein Spline-Artefakt.
- **Generalisierung P1:** Der Annihilator ist vorn (8/10, 10/10 und 8/10 auf 3, 19 und 21, Baselines 4–6/10).
- **Generalisierung P2:** etwa gleichauf. Gompertz generalisiert keine Methode.
- **Offen:** ob der P1-Vorsprung vom Operator oder von der Glättung kommt, die nur der Annihilator bekommt. Klären
  würde das SINDy auf denselben geglätteten Paaren; das ist nicht gelaufen.
- **Struktur bei 1 %:** Exakt trifft der Annihilator nur die Logistik (4/15). Sonst wählt er Surrogate. Die Baselines
  wählen dichte Modelle und treffen nie exakt.
- **Befund:** W-SINDy ist nicht reproduzierbar, weil pysindy 2.1.0 die Testfunktionen über das globale `np.random`
  ohne Seed zieht. Zwei Ziehungen liegen für 19 und 21 vor.

## 2. Große Datei: erledigt, Push möglich

- Die v1-Rohdatei ist aus der lokalen Historie entfernt (08.10., manueller Modus). Die Commits ab dem alten
  `2dfd44b` haben neue Hashes (`04a927e` …).
- Sicherung des alten Stands: `refs/backup/pre-bigfile-rewrite-20261008`. Nach einem erfolgreichen Push löschen
  mit `git update-ref -d refs/backup/pre-bigfile-rewrite-20261008`.
- Die Rohdateien (je etwa 910 MB) bleiben lokal und stehen in `.gitignore`. Committet sind die Kompaktfassungen
  `records_compact.jsonl` in `results_e2e/` und `results_e2e_v2/`.
- Der Branch ist **pushbereit** (GitHub, nur durch den Nutzer).

## 3. Nächste Schritte

1. **Push** durch den Nutzer: `git push origin annihilator-discovery`.
2. **Entscheidung des Nutzers:** Idee #1 abschließen oder nicht.
   - Bei Abschluss: Abschlussabschnitt in `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md`, `CLAUDE.md` als abgeschlossen
     markieren, aufräumen (§4).
   - Falls die offene Frage aus §1 noch geklärt werden soll: neue eingefrorene Version mit SINDy auf den geglätteten
     Paaren. Sie ist billig, weil Baselines nur Sekunden je Fit brauchen.

## 4. Was noch liegt

- **Kein Codex-Auftrag aktiv.**
- **Orion:** Der abgeschlossene Job `annihilator-diag-amb` steht noch (Pods `Completed`). Löschen mit
  `oc delete job annihilator-diag-amb`. Die Originaldaten bleiben auf dem NFS unter
  `/bigdata/data-science/joedicke/annihilator_diag_amb/`, eine lokale Kopie ist committet.
- **Nicht committete Laufdateien** der Kette (`*.err`, `*.out`) in `results_e2e/` und `results_e2e_v2/`.
  `main.err` und `resume.err` sind je etwa 340 KB groß und enthalten vor allem lsoda-Meldungen. Beim Aufräumen
  committen oder löschen. `DONE`, `chain.log` und `run.log` sind committet.
- **Temp-Ordner** aus Codex' Testläufen (`.pytest_tmp*`, `.pytest-tmp`, `.codex_tmp/`): nicht committen, löschen.
- **Entscheidungen des Nutzers:**
  - `PRACTICAL_ANNIHILATOR_BENCHMARK.md` (uncommittet, Entwurf des Nutzers): zur Akte oder verwerfen;
  - Orakel-Teil 12/18 und Worker-Caches der v2-Abnahme (`experiments/annihilator_gate2a_v2/results/acceptance/`):
    committen oder löschen.
