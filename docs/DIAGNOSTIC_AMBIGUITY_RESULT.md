# Diagnose `AMBIGUOUS` – Ergebnis und Übergabe

**Stand: 2026-10-06.** Ergebnis des Hauptlaufs zur eingefrorenen Diagnose `docs/DIAGNOSTIC_AMBIGUITY.md`
(N = 100 je Zelle, 600 Realisierungen). Für den Nutzer und jede spätere Sitzung dieser Spur, zur Entscheidung, ob
die Spur endet. Spezifikation und Entscheidungsregel stehen in `docs/DIAGNOSTIC_AMBIGUITY.md` und werden hier nur
so weit wiederholt, wie es zum Lesen nötig ist.

## 1. In einem Satz

**Verdikt nach der eingefrorenen Regel: negativ.** In den identifizierbaren Fällen arbeitet die Methode fast
fehlerfrei (99 % `CORRECT`). Wenn sie in den nicht identifizierbaren Fällen aber eine eindeutige Antwort gibt, ist
diese **in 118 von 118 Fällen falsch**. Ob sie abstainiert oder falsch antwortet, hängt nicht davon ab, ob die Daten
die Antwort tragen, sondern davon, welche falsche Klasse der Test zuerst durchlässt. Für die Abstention-Story
(`PRACTICAL_ANNIHILATOR_BENCHMARK.md`) heißt das nach §5: kein `PRACTICAL_BENCHMARK_v1.md`, kein Hold-out-Set, kein
größerer Benchmark.

## 2. Was geprüft wurde

- **Frage:** Reagiert Gate 2A v3 bei nicht identifizierbaren Fällen (N1 nach Anhang B) überwiegend mit
  `AMBIGUOUS`, und deutlich häufiger als bei identifizierbaren Fällen (I)? Oder wählt sie stabil eine falsche
  Klasse?
- **Zellen:** breite Domäne, $\eta = 0{,}01$.
  N1 = F4 $\log x$ (Referenz (2,1)), F5 $x\log x$ (3,1), F8 $x/(2+x)$ (1,2).
  I = F1 $x^2$ (1,1), F2 $e^{1.5x}$ (1,0), F6 $e^{-x^2}$ (1,1).
- **Methode:** Gate 2A v3 unverändert (`full_search`, AML mit L-BFGS, `boot_reps = 50`, `boot_threshold = 0.8`,
  `a3_trace_threshold = 0.1`, $\ell_{\max} = 4$, $\tau = 3.4\cdot10^{-7}$, $\alpha = 0{,}01$). Klassen werden in der
  festen Ordnung nach $(r+1)(d+1)$ geprüft: (1,0), (2,0), (1,1), (3,0), (4,0), … Die erste nicht verworfene Klasse
  wird gewählt, danach entscheiden A1 bis A3 über `AMBIGUOUS`:
  - **A1:** Der Nullraum in der gewählten Klasse ist mehrdimensional.
  - **A2:** Im Bootstrap wählen weniger als 80 % dieselbe Klasse.
  - **A3:** Die Koeffizientenunsicherheit ist zu groß für die Linearisierung.
- **Seeds:** 50000–50099 je Funktion. Die 12 Pilot-Records (Seeds 50000 und 50001) zählen mit.
- **Entscheidungsregel** (vor dem Lauf eingefroren): Interessant nur, wenn B1–B4 alle erfüllt sind, siehe §4.

## 3. Durchführung und Vollständigkeit

- **Lauf:** Orion, Job `annihilator-diag-amb`, 11 Pods à 1 Kern, Code aus Commit `c71841f`. Gestartet vom Nutzer am
  05.10. um 15:15. Laut Job-Status nach 5 h 30 abgeschlossen (letzter `DONE`-Zeitstempel 05.10., 18:44 Pod-Zeit),
  11/11 Pods `Completed`, **keine Neustarts**. Die Prognose von rund 32 h beruhte auf Pilot-Kosten vom Laptop mit
  6 parallelen Workern. Das ist nur eine Laufzeitbeobachtung, keine Evidenz für irgendetwas.
- **Vollständigkeit:** 5 Teile × 54 + 6 Teile × 53 = 588 Records = die 588 offenen Realisierungen. Zusammen mit den
  12 Pilot-Records sind es 600, je Funktion genau 100 (`complete_equal_n: True`). Die mitgelieferte Pilot-Datei
  `orion/results/records.jsonl` ist byteidentisch mit der committeten `records.jsonl` des Pilots.
- **Auswertung:** `ambiguity_diagnostic --merge --reps 100`, dann `--summarize`, lokal am 06.10. Gleiche
  `settings` in allen 600 Records.
- **Kosten** (Zählgrößen je Realisierung): geprüfte Klassen 1 (F2) bis 7, AML-Iterationen 2 bis 74.

## 4. Ergebnis gegen die Kriterien

| Kriterium | Definition | Wert | Schwelle | erfüllt? |
|---|---|---:|---|---|
| B1 | $P(\texttt{WRONG} \mid \text{eindeutige Ausgabe}, N1)$ | **1,000** (118/118) | < 0,20 | **nein** |
| B2 | $P(\texttt{AMBIGUOUS} \mid N1)$ | 0,607 (182/300) | ≥ 0,50 | ja |
| B3 | $P(\texttt{CORRECT} \mid I)$ | 0,990 (297/300) | ≥ 0,70 | ja |
| B4 | $P(\texttt{AMBIGUOUS} \mid N1) - P(\texttt{AMBIGUOUS} \mid I)$ | 0,597 (0,607 − 0,010) | ≥ 0,25 | ja |

**Verdikt: negativ**, weil B1 verfehlt ist. Die Schwellen bleiben unverändert (§5 der Spezifikation).

## 5. Ergebnis je Funktion

| Fkt. | Gruppe | Referenz | Zustände (von 100) | gewählte Klasse | Auslöser `AMBIGUOUS` | Bootstrap-Anteil (Median) | $T$/dof (Median) |
|---|---|---|---|---|---|---:|---:|
| F4 $\log x$ | N1 | (2,1) | 99 `WRONG`, 1 `AMBIGUOUS` | (3,0) bei `WRONG`, (4,0) bei `AMBIGUOUS` | 1× A1+A2+A3 | 1,00 (`WRONG`) | 0,96 |
| F5 $x\log x$ | N1 | (3,1) | 100 `AMBIGUOUS` | (3,0) | 100× nur A1 | 1,00 | 0,59 |
| F8 $x/(2+x)$ | N1 | (1,2) | 81 `AMBIGUOUS`, 19 `WRONG` | (3,0) bei `AMBIGUOUS`, (2,0) bei `WRONG` | 77× A1+A2, 4× A1+A2+A3 | 0,24 (`AMB.`), 0,96 (`WRONG`) | 0,53 / 1,16 |
| F1 $x^2$ | I | (1,1) | 99 `CORRECT`, 1 `AMBIGUOUS` | (1,1); (4,0) bei `AMBIGUOUS` | 1× A1+A2+A3 | 1,00 | 1,01 |
| F2 $e^{1.5x}$ | I | (1,0) | 99 `CORRECT`, 1 `AMBIGUOUS` | (1,0); (2,0) bei `AMBIGUOUS` | 1× A2 | 1,00 | 1,01 |
| F6 $e^{-x^2}$ | I | (1,1) | 99 `CORRECT`, 1 `AMBIGUOUS` | (1,1); (2,1) bei `AMBIGUOUS` | 1× A2 | 1,00 | 1,00 |

In keiner Zelle trat `NONE` oder `TRUE_NOT_REF` auf. In allen 600 Records liegt $T$ unter dem kritischen Wert der
gewählten Klasse; das folgt aus der Suchlogik (gewählt wird die erste nicht verworfene Klasse). $T$/dof in der
letzten Spalte bezieht sich auf die gewählte Klasse; bei F8 steht links der Wert für `AMBIGUOUS`, rechts der für
`WRONG`.

## 6. Was das bedeutet

### 6.1 Die Wahl folgt genau der Teststärke aus Anhang B

Anhang B (`results/appendix_B/appendix_B.json`) hat für jede früher geprüfte, falsche Klasse die Güte $\beta$ des
idealen Tests auf exakten Daten berechnet. Die beobachteten Fehlwahlen passen dazu fast exakt:

| Fkt. | erste falsche Klasse mit kleiner Güte | $\beta$ (Anhang B) | erwartet nicht verworfen | beobachtet gewählt |
|---|---|---:|---:|---:|
| F4 | (3,0) | 0,137 | ≈ 86 % | 99 % |
| F5 | (3,0) | 0,012 | ≈ 99 % | 100 % |
| F8 | (2,0) | 0,799 | ≈ 20 % | 19 % |
| F8 | (3,0), falls (2,0) verworfen | 0,010 | ≈ 99 % | 81 von 81 |

In den N1-Zellen erreicht die Suche die Referenzklasse also praktisch nie. Sie bleibt vorher an einer falschen
Klasse mit konstanten Koeffizienten hängen, die der Test nicht verwerfen kann. Das ist dieselbe
Informationsgrenze wie in Anhang B, jetzt auf verrauschten Daten bestätigt. Die in Anhang B als „konkurrierende
falsche Klasse“ genannten Klassen (4,0) und (6,0) sind nur die schwächsten; die Suche stoppt schon bei der
früheren Klasse (3,0) bzw. (2,0).

### 6.2 Die Abstention misst die gewählte Klasse, nicht die Identifizierbarkeit

Ob am Ende `AMBIGUOUS` oder `WRONG` herauskommt, entscheidet allein, **welche** falsche Klasse gewählt wurde:

- **(3,0) bei F5 und F8:** Diese Klasse hat für $x\log x$ und $x/(2+x)$ einen mehrdimensionalen Fast-Nullraum, also
  feuert A1. Die Abstention ist hier ein Nebeneffekt der Klassenstruktur, kein Signal „die Daten reichen nicht“.
  Bei F5 kommt sie **nur** von A1, der Bootstrap wählt in 100 % der Fälle stabil (3,0).
- **(3,0) bei F4:** eindimensionaler Nullraum, A1 feuert nicht. Der Bootstrap wählt in 100 % der Wiederholungen
  wieder (3,0), A2 feuert also auch nicht. Ergebnis: **stabil falsch, mit voller Zuversicht.** Das war das
  Warnsignal aus dem Pilot, jetzt mit N = 100 bestätigt.
- **(2,0) bei F8:** gleiches Muster in 19 % der Fälle, Bootstrap-Anteil 0,90–1,00.

Der strukturelle Grund: A2 misst, ob die Auswahl unter Resampling **stabil** ist. Eine falsche Klasse, die der Test
systematisch nicht verwerfen kann, ist aber stabil. Kein Ambiguitätskriterium der Methode prüft, ob eine spätere,
komplexere Klasse die Daten genauso gut erklären würde. Genau das wäre die Frage der Identifizierbarkeit.

### 6.3 Die identifizierbaren Fälle sind sauber

- F1, F2 und F6: 297 von 300 `CORRECT`. Die Referenzklasse wird in 3 von 300 Fällen verworfen, das ist genau die
  nominale Rate $\alpha = 1\,\%$. Danach wählt die Suche eine spätere Klasse ((4,0), (2,0), (2,1)), und A2 (bei F1
  zusätzlich A1 und A3) macht daraus `AMBIGUOUS` statt `TRUE_NOT_REF`. $T$/dof liegt in den `CORRECT`-Fällen im
  Median bei 1,00–1,01 (Spanne 0,79–1,23), der Test ist dort also kalibriert. Der Bootstrap-Anteil liegt bei
  0,90–1,00.
- Alle drei Verwerfungen stammen aus **Seed 50000**, also aus dem Pilot. In den 294 Orion-Realisierungen der
  Gruppe I gab es kein einziges `AMBIGUOUS`. Das zweite Warnsignal aus dem Pilot (Referenz in 3 von 6 Fällen
  verworfen) war eine Häufung bei diesem einen Seed und hat sich **nicht** bestätigt.
- Zum Feld `n_exact` in den Records: Es bezieht sich auf die **gewählte** Klasse, nicht auf die Referenz. Deshalb
  steht bei den drei Seed-50000-Fällen 2, sonst 1. Das ist keine Inkonsistenz zwischen Pilot und Orion.

### 6.4 Einordnung

Die Methode hat damit zwei saubere Eigenschaften und eine, die die Abstention-Story trägt oder bricht:

1. **Identifizierbare Fälle erster Ordnung:** richtig und kalibriert (bestätigt K1/K2 aus Anhang A und I aus
   Anhang B).
2. **Unterscheidung von N1 und I über die Abstention-Rate:** im Aggregat deutlich (B2, B4 erfüllt).
3. **Verlässlichkeit einer eindeutigen Antwort:** In N1 ist jede eindeutige Antwort falsch. Ein Nutzer könnte also
   einer eindeutigen Ausgabe nicht ansehen, ob sie aus einem I-Fall (99 % richtig) oder einem N1-Fall (0 % richtig)
   stammt. Für Selective Prediction ist genau das das entscheidende Kriterium, deshalb ist B1 zu Recht hart.

## 7. Folgen nach der eingefrorenen Regel

- **Kein** `docs/PRACTICAL_BENCHMARK_v1.md`, **kein** Hold-out-Set, **kein** größerer Benchmark.
- **Keine Nachjustierung** von A1, A2, A3, $\alpha$, Klassenordnung oder Bootstrap-Schwelle auf Basis dieses
  Ergebnisses (§5 der Spezifikation). Eine Regel wie „zusätzlich prüfen, ob eine spätere Klasse ebenfalls nicht
  verworfen wird“ wäre genau so eine nachträgliche Reparatur. Sie bräuchte eine neue, vorab eingefrorene Version
  und neue Testfunktionen.
- **F1–F10 sind ab jetzt Entwicklungsset**, kein unberührtes Gate-Set mehr. Das verschlossene Prüfset
  (4 / 49 / 59 / 62) bleibt unangetastet.

## 8. Stand der Spur und Entscheidung

| Schritt | Ergebnis |
|---|---|
| Gate 2A v1 | eingefroren, an der Abnahme gescheitert, nie gelaufen |
| Gate 2A v2 | Stufe K gescheitert (FNS-Fehler) |
| Gate 2A v3, Anhang A | nicht bestanden (Ordnung 3 unkalibriert, Clean K7/K8 durchgefallen) |
| Gate 2A v3, Anhang B | Kill-Kriterium K6 würde auslösen (F4, F5, F8 bei 1 % N1) |
| Diagnose `AMBIGUOUS` | **negativ** (B1: 118/118 eindeutige N1-Antworten falsch) |

**Was bleibt:** Bei Operatoren erster Ordnung mit konstanten oder linearen Koeffizienten (Potenzen,
Exponentialfunktionen, Gauß) findet das Verfahren den richtigen Annihilator mit kalibriertem Test. Das ist aber der
Bereich, den bestehende Methoden schon abdecken. Die Kernidee, $x$-abhängige Koeffizienten zu erkennen, scheitert
bei 1 % Rauschen an der Information in den Daten. Die Abstention fängt das nicht verlässlich ab.

**Offene Entscheidung (Nutzer):**

- **A: Spur beenden.** Ergebnis in `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` als Abschluss festhalten. Kein
  weiterer Compute.
- **B: Grundsätzliche Neubewertung** beim Messdesign (mehr Punkte, weniger Rauschen, andere Funktionsklassen) oder
  bei einer Identifizierbarkeitsprüfung als Teil der Methode. Das wäre eine neue Idee mit eigener, vorab
  eingefrorener Spezifikation und neuen Testfunktionen, keine Fortsetzung von Gate 2A.

**Empfehlung: A.** Vier Schritte hintereinander zeigen dieselbe Grenze. Variante B würde die Methode auf genau die
Bedingungen zuschneiden, unter denen sie schon funktioniert, oder ein neues Kriterium einführen, das erst nach
diesem Ergebnis motiviert ist.

## 9. Wo die Daten liegen

Alles unter `experiments/annihilator_gate2a_v3/results/diagnostic_ambiguity/`:

| Pfad | Inhalt |
|---|---|
| `records.jsonl`, `run.log`, `summary.*`, `pilot.*` | Pilot (12 Records, 05.10.) |
| `orion/results/parts/part_*_of_11/` | Orion-Teile: `records.jsonl`, `run.log` (ohne Zustände), `DONE`, Nullraum-Cache |
| `orion/results/records.jsonl` | Pilot-Kopie, die mit auf Orion lag (byteidentisch) |
| `orion/results/records_merged.jsonl` | **600 zusammengeführte Records**, Grundlage des Verdikts |
| `orion/results/summary.json`, `summary.md` | B1–B4 und Zustände je Gruppe |

Weitere Quellen: Code `experiments/annihilator_gate2a_v3/diagnostics/ambiguity_diagnostic.py`, Runbook
`experiments/annihilator_gate2a_v3/orion/RUNBOOK.md`, Teststärken `results/appendix_B/appendix_B.json`. Auf dem
Orion-NFS bleibt die Originalablage unter `/bigdata/data-science/joedicke/annihilator_diag_amb/` liegen.
