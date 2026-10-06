# READ_THIS_FIRST.md — Übergabe der Annihilator-Spur

**Was dieses Dokument ist:** der flüchtige Zustand zwischen zwei Sitzungen dieser Spur: was läuft, was offen ist,
welche Entscheidung ansteht. Wird **immer vollständig überschrieben**. Dauerhaftes gehört in `CLAUDE.md`,
`docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` oder `DIARY.md`. EvoGrow und Paper 1 stehen in `..\EvoODE\READ_THIS_FIRST.md`,
nicht hier.

**Stand: 2026-10-06 abends. Der Reality-Check Stufe A ergibt `STRONG_NEGATIVE`. Nach der eingefrorenen Regel wird
Idee #1 beendet. Der Nutzer hatte vorab zugesagt, die Spur in diesem Fall zu schließen. Offen ist nur noch das
Abschlussdokument. Nichts läuft.**

## 1. Wo wir stehen

- **Ausführlich:** `docs/REALITY_CHECK_DIRECT_REGRESSION_RESULT.md` (Ergebnis, Lesart, Gesamtbild, Datenablage).
- **Reality-Check Stufe A** (`docs/REALITY_CHECK_DIRECT_REGRESSION.md` §10): Auf exakt denselben Samples und mit
  derselben Auswahlregel (kleinstes Modell, das der $\chi^2$-Test bei 1 % nicht verwirft) findet eine direkte
  Best-Subset-Regression F4, F5 und F8 in 60 von 60 Realisierungen richtig, eindeutig und mit Fehler
  ≈ $2\cdot10^{-4}$. Der Annihilator ist auf denselben Samples bei 25 von 25 eindeutigen Ausgaben falsch.
  STLSQ ist in der eingefrorenen Form entartet; das wird nur berichtet.
- **Vorbehalt:** Die Library der Baseline enthält die wahren Familien. Das Ergebnis zeigt, dass das Surrogatproblem
  nicht unvermeidlich ist. Es zeigt nicht, dass Sparse-Regression allgemein überlegen ist.
- **Diagnose `AMBIGUOUS`** (`docs/DIAGNOSTIC_AMBIGUITY_RESULT.md`): negativ, B1 = 118/118.
- **Gesamtbild:** Gate 2A v1 nie gelaufen. v2 in Stufe K gescheitert. v3: Anhang A nicht bestanden, Anhang B löst K6
  aus. Diagnose `AMBIGUOUS` negativ, Reality-Check `STRONG_NEGATIVE`. Funktionieren tut nur der Bereich Ordnung 1–2
  mit einfachen Koeffizienten. Das Surrogatproblem stammt aus der Repräsentation und ihrer Komplexitätsordnung
  $(r+1)(d+1)$.

## 2. Nächste Schritte

1. **Abschluss schreiben** (nach Bestätigung durch den Nutzer): Abschlussabschnitt in
   `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` mit Ergebnis, Gate-Folge, Lesart und dem, was übertragbar bleibt.
   Danach in `CLAUDE.md` die Spur als abgeschlossen markieren. Kein W-SINDy, kein ODEFormer, kein eigenes Repository.
2. Aufräumen (§3).

## 3. Was noch liegt

- Kein Job, kein Pod, kein Codex-Auftrag aktiv. Die Originaldaten der Diagnose bleiben auf dem NFS unter
  `/bigdata/data-science/joedicke/annihilator_diag_amb/`. Eine lokale Kopie ist committet.
- Auf Orion stehen noch der abgeschlossene Job `annihilator-diag-amb` und seine Pods (`Completed`, ohne
  Ressourcen). Löschen mit `oc delete job annihilator-diag-amb`.
- `.pytest_tmp/` und `.codex_tmp/` im Wurzelverzeichnis: Temp-Ordner aus Codex' Testläufen. Nicht committen,
  löschen.
- `PRACTICAL_ANNIHILATOR_BENCHMARK.md` ist uncommittet (Entwurf des Nutzers). Committen als Teil der Akte oder
  verwerfen, entscheidet der Nutzer.
- Uncommittet liegen noch Orakel-Teil 12/18 und Worker-Caches der v2-Abnahme
  (`experiments/annihilator_gate2a_v2/results/acceptance/`). Committen oder löschen, entscheidet der Nutzer.
