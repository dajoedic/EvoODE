# READ_THIS_FIRST.md — Übergabe der Annihilator-Spur

**Was dieses Dokument ist:** der flüchtige Zustand zwischen zwei Sitzungen dieser Spur: was läuft, was offen ist,
welche Entscheidung ansteht. Wird **immer vollständig überschrieben**. Dauerhaftes gehört in `CLAUDE.md`,
`docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` oder `DIARY.md`. EvoGrow und Paper 1 stehen in `..\EvoODE\READ_THIS_FIRST.md`,
nicht hier.

**Stand: 2026-10-05 nachmittags. Gate 2A v3: Anhang A nicht bestanden, Anhang B (Diagnose) löst Kill-Kriterium K6 aus.
Grundsatzentscheidung beim Nutzer offen.**

## 1. Wo wir stehen

**Zuerst lesen: `docs/GATE_2A_v3_STAGE_K_RESULT.md`**, vor allem „Nachtrag 1“.

- **v1** (04.10.): an der Abnahme gescheitert. Ursachen: Matrixnumerik, SVD-Bias, schmale Testfunktionen. Nie
  gelaufen.
- **v2:** Stufe K scheiterte, weil FNS Sattelpunkte statt Minima fand.
- **v3:** AML mit L-BFGS. Zwei Implementierungsfehler von Codex wurden behoben (Vorzeichen im Gradienten). Stufe K:
  - Ordnung 1–2 kalibriert (K1, K2 bestanden);
  - K6 (Ordnung 3): Kovarianz unterschätzt die Streuung um das 2- bis 7-Fache;
  - Clean K7 schmal ist `WRONG`, K7 und K8 breit sind `AMBIGUOUS` statt `CORRECT`. **Anhang A besteht nicht.**
  - Alle 8 Teile sind fertig (11:15), `appendix_A.{json,md}` ist zusammengeführt (1.000 Realisierungen).
- **Anhang B** als Diagnose (Nutzer: Option A): Bei 1 % Rauschen auf der breiten Domäne sind F4, F5, F8, F9 und F10
  nicht identifizierbar (N1). Eine Klasse mit **konstanten** Koeffizienten passt jeweils so gut wie der wahre
  Operator mit **polynomialen** Koeffizienten, Güte $\beta \approx \alpha$. **K6 würde auslösen** (3 Zellen > 1).
  Identifizierbar bleiben nur Operatoren erster Ordnung und der Sinus.

## 2. Offene Entscheidung des Nutzers (in dieser Sitzung zu treffen)

Spur **beenden** (Ergebnis dokumentieren) oder das **Messdesign grundsätzlich neu denken**. Im zweiten Fall muss
der Nutzer festlegen, welche Annahme sich ändern darf:
- weniger Rauschen als Zielbereich (etwa 0,1 %);
- mehr Daten (größeres N, mehrere Trajektorien);
- eine schmalere Fragestellung (Ordnung und Koeffizientenstruktur, ohne polynomiale von konstanten Koeffizienten
  zu unterscheiden).

Jede Variante ändert das Versprechen der Idee. Das ist eine inhaltliche Entscheidung, keine technische. Eine v4 des
Schätzers allein ändert an K6 nichts.

## 3. Was noch läuft oder liegt

- **Es läuft nichts.** Stufe K v3 ist vollständig, Anhang A, die Logs und die Lauf-Hilfsdateien von Anhang B sind
  committet.
- `codex/CURRENT_TASK.md` enthält noch den erledigten WP-G2A3-c (`STATUS.md`: `done`). Kein aktiver Auftrag.
- Uncommittet liegen noch Orakel-Teil 12/18 und Worker-Caches der v2-Abnahme
  (`experiments/annihilator_gate2a_v2/results/acceptance/`). v2 ist abgelöst. Ob sie committet oder gelöscht werden, entscheidet der Nutzer.
