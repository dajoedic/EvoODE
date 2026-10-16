# Warum wählt die Suche die falschen Terme? Vorschlag für einen Fokuswechsel

**Diskussionspapier, Stand 17.10.2026.** Es wird nicht nachgeführt; Entscheidungen daraus landen in `CLAUDE.md`
und `DIARY.md`. Die Zahlen stammen aus den eingefrorenen Phase-C-Läufen, Quellen am Ende.

## 1. Worum es geht

Bisher haben wir gefragt, **ob** EvoGrow die richtige Gleichung findet, und jede Runde mit einer neuen Variante oder
einem neuen Hebel beantwortet: Stufen-Kappung, Konstante in der Basis, Restarts, zuletzt eine gelenkte
Kandidatenauswahl. Der jüngste Test (Abschnitt 3) zeigt: Selbst wenn wir der Suche die richtigen Terme vorschlagen,
findet sie die richtige Gleichung kaum öfter.

Der Vorschlag ist deshalb, die Frage umzudrehen: **Warum** landet die Suche bei einer falschen Struktur, in welcher
Zelle aus welchem Grund? Erst wenn die Ursachen getrennt und gezählt sind, wird die nächste Methodenversion entworfen,
und zwar gezielt gegen die häufigste Ursache.

## 2. Kurz zum Verfahren

- **Aufgabe:** Aus einer gemessenen Trajektorie x(t) eines ODE-Systems dx/dt = f(x) die rechte Seite f als dünn
  besetzte Summe von Basistermen finden. Die Basis ist `1, u_i, u_i², u_i·u_j, u_i³, sin(u_i), cos(u_i)`.
- **Benchmark:** ODEBench, 63 Systeme in Dimension 1 bis 4. 30 davon sind mit dieser Basis exakt darstellbar; nur dort
  kennen wir die wahre Struktur.
- **Suche (EvoGrow):** eine Population von Kandidatenstrukturen, die von klein nach groß wächst. Terme werden nur
  **hinzugefügt**, nie entfernt. Höhere Basisstufen (Grad 2, 3, trigonometrisch) werden erst freigeschaltet, wenn die
  niedrigeren nicht reichen.
- **Bewertung eines Kandidaten:** Die Koeffizienten werden mit BFGS so gefittet, dass die **integrierte** Trajektorie
  zur gemessenen passt (MSE). Bis zu drei Startpunkte, ein neuer nur nach einem Fehlschlag. Ausgewählt wird nach
  `Objective = MSE + λ · Anzahl Parameter` mit **λ = 1e-3, absolut**, also nicht auf die Datenskala bezogen.
- **Daten:** Je System gibt es zwei Anfangsbedingungen (IC). Trainiert wird auf einer, die andere dient nur als Test
  der Generalisierung und geht nie in die Auswahl ein.
- **Metriken:**
  - Rekonstruktion: Anteil R² > 0,9 auf der Trainingstrajektorie.
  - Generalisierung: dasselbe auf der Test-IC.
  - Struktur: exakter Support, *roh* (gefundene Terme) und *geprunt* (nach einer Schwelle auf kleine Koeffizienten).

## 3. Was wir wissen

**3.1 Die Suche passt die Trajektorie, findet aber nicht den Mechanismus.** C-1, sauber, Seed 42/123/7, beide IC:

| | Rekonstruktion | Generalisierung | Struktur geprunt | Struktur roh |
|---|---|---|---|---|
| EvoGrow, alle Dim. | 88,6 % | 41,4 % | 29,4 % | 13,3 % |
| EvoGrow, dim 2 | 96,4 % | **29,8 %** | 36,7 % | 3 von 60 Zellen |
| Weak-SINDy deg3, alle Dim. | 89,2 % | 61,9 % | 65,0 % | 65,0 % |

Auf dim 2 passt EvoGrow fast jede Trainingskurve, aber nur ein knappes Drittel der Modelle trägt auf die zweite IC.
Wenn die Struktur stimmt, dann meist erst nach dem Pruning: Die Suche landet auf einer **Obermenge** der Wahrheit, und
die Schwelle räumt auf. ODEFormer zeigt dieselbe Lücke (Rekonstruktion 79,9 %, Generalisierung 33,6 %).

**3.2 Die Verlustfunktion erkennt die Wahrheit, wenn der Fit gelingt (WP-T1f).** Für die Wahrheit und alle
Nachbarstrukturen mit einem Term vertauscht oder entfernt wurde jeweils sorgfältig gefittet. Auf 36 Zellen (dim 2 und 3)
schlägt **keine von 2.479 gleich großen Vertauschungen** die Wahrheit, der Abstand beträgt mindestens fünf
Größenordnungen im MSE. Lokal ist die Wahrheit also ein klares Optimum des Kriteriums. Ob weiter entfernte Strukturen
mithalten können, ist damit nicht geprüft.

**3.3 Die Wahrheit ist schwer zu fitten (P-04, Restart-Kurve).** Gibt man dem Optimierer die *wahre* Struktur, erreicht
auf dim 2 ein einzelner Startpunkt R² > 0,9 nur in **25 %** der Zellen, drei Starts in 33 %, zehn in 65 %. Auf dim 1
sind es 73 % / 91 % / 97 %. Die Suche bewertet jede Struktur mit höchstens drei Starts.

**3.4 Bessere Vorschläge helfen kaum (WP-T2a S1, 17.10.).** Der Orakel-Prior zieht die wahren Terme mit erhöhter
Wahrscheinlichkeit (Rang-Gewichtung ∝ 1/Rang, 20 % gleichverteilt beigemischt). dim 2, Seed 42, 20 Zellen; ausgewertet
auf den 13 Zellen, deren Wahrheit nachweislich fittbar ist:

| fittbar, n = 13 | ohne Prior (C-1) | Orakel-Prior |
|---|---|---|
| Struktur geprunt | 3 | 5 |
| Struktur roh | 0 | 2 |
| R² > 0,9 Rekonstruktion | 13 | 13 |

In 8 von 13 Zellen findet die Suche die richtige Struktur nicht, obwohl sie ihr bevorzugt angeboten wird. Die falschen
Strukturen passen die Trainingskurve genauso gut. Nach der vorab festgelegten Regel (≥ 10 pp **und** p < 0,05 über
Systeme) ist der Test nicht bestanden (p = 0,25).

**3.5 Weak-SINDy findet die Struktur doppelt so oft, auf denselben Daten.** Es fittet linear in der schwachen Form,
ohne Integration, ohne Startpunkte, ohne Schranke. Das spricht dagegen, dass die Daten die Struktur grundsätzlich nicht
festlegen. Es spricht eher dafür, dass unser Weg dorthin, der Fit über die integrierte Trajektorie, das Problem ist.
Einschränkung: Bibliothek und Schwelle sind nicht identisch mit unseren.

## 4. Ein Schluss, der aus dem Kriterium folgt

Zwei Annahmen, die noch am Code zu bestätigen sind: Die gemeldete Struktur ist die mit dem kleinsten Objective über
alle ausgewerteten Kandidaten, und λ wirkt pro Koeffizient. Dann gilt:

**Eine Obermenge der Wahrheit kann nur gewinnen, wenn die Wahrheit nie ausgewertet wurde oder schlechter gefittet
wurde, als ihr Optimum hergibt.** Jeder überzählige Term kostet 1e-3 im Objective. Auf den Zellen aus 3.2 liegt der MSE
der gut gefitteten Wahrheit weit darunter. Eine Obermenge müsste den MSE also um mehr als 1e-3 pro Zusatzterm senken,
und das geht nur gegen eine schlecht gefittete Wahrheit.

Daraus folgt umgekehrt ein **eigener möglicher Fehlermechanismus**: Weil λ absolut ist, hängt sein Gewicht an der
Datenskala. Bei Systemen mit kleinem MSE-Niveau dominiert die Strafe, dann kann eine *kleinere falsche* Struktur
gewinnen. Bei großem Niveau ist sie wirkungslos, und Obermengen kosten fast nichts.

## 5. Vier Fehlerklassen (plus eine)

Für jede Zelle mit falscher Struktur gilt genau eine dieser Klassen. Jede verlangt eine andere Gegenmaßnahme:

| Klasse | Was passiert | Gegenmaßnahme wäre |
|---|---|---|
| **A — nicht erreicht** | Die wahre Struktur wurde nie ausgewertet. | Suchoperatoren: Entfernen/Ersetzen, andere Wachstumsregel |
| **B — schlecht gefittet** | Die Wahrheit wurde ausgewertet, der Fit blieb in einem schlechten lokalen Optimum, eine leichter fittbare Struktur gewann. | Fit: mehr Starts, Warmstarts, Fit in der schwachen Form |
| **C — von Obermenge geschlagen** | Die Wahrheit wurde gut gefittet, eine Obermenge hatte trotzdem ein kleineres Objective. | Komplexitätskontrolle (Skalierung von λ, BIC) |
| **D — nicht identifizierbar** | Eine nicht verschachtelte falsche Struktur ist mindestens so gut wie die gut gefittete Wahrheit. | Kriterium oder Daten: mehrere Trajektorien, Validierung |
| **E — Strafterm** | Die Wahrheit unterliegt einer *kleineren* falschen Struktur, weil λ die MSE-Differenz überwiegt. | λ relativ zur Datenskala |

Nach der Überlegung in Abschnitt 4 sollte C selten sein, und 3.2 macht D in der Nachbarschaft der Wahrheit
unwahrscheinlich. Die Hauptverdächtigen sind **B** und **A**, möglicherweise **E**. Das ist eine Erwartung, kein Befund.

## 6. Die Hypothese „Kombination statt Einzelterm“

Die Vermutung lautet: In einer ODE sagt ein einzelner Term wenig aus, erst die Kombination mehrerer Terme ergibt die
Lösung. Eine Reihenfolge über Einzelterme kann deshalb nicht helfen.

- **Dafür:** S1. Einzelterme bevorzugt anzubieten bringt +2 von 13. Außerdem kann entlang *einer* Trajektorie ein
  falscher Term den Beitrag eines fehlenden wahren nachbilden, etwa ein Polynom ein `sin` oder eine Konstante einen
  Versatz. Basisfunktionen sind auf einer einzelnen Kurve oft fast linear abhängig.
- **Einschränkend:** 3.2. Ist die Kombination *mit passenden Parametern* gefunden, trennt das Kriterium sehr deutlich.
  Schärfer formuliert: **Ein Term ist nur im Verbund und nur mit gut gefitteten Parametern beurteilbar.** Bei einem
  Fit über die integrierte Trajektorie mit wenigen Starts ist genau das unsicher, was zu Klasse B führt.
- **Für den Suchprozess ist die Reihenfolge nicht egal:** Weil nur hinzugefügt wird, bleibt ein früh gewählter falscher
  Term in seiner Linie. S1 hat Einzelterme bevorzugt, nicht die richtige Kombination als Ganzes. Ob die Kombination je
  ausgewertet wurde, ist die offene Frage hinter Klasse A.

## 7. Vorgehen

Der Grundsatz: vorhandene Daten vor neuen Läufen. Die Fragen werden vorher festgelegt. Begonnen wird auf dim 1 und 2,
exakt darstellbare Systeme, weil nur dort die Wahrheit bekannt ist.

1. **Ohne Rechenaufwand (vorhandene Daten).** Für jede C-1-Zelle das Objective der gewählten Struktur gegen das
   Objective der Wahrheit legen, wie sie in P-04 mit k = 3 und k = 10 gefittet wurde. Mögliche Ergebnisse:
   - Wahrheit besser schon bei k = 3 → A (nie erreicht).
   - Nur bei k = 10 besser → B (Fit).
   - Auch bei k = 10 schlechter → C, D oder E. Nach Termzahl getrennt: größere Siegerstruktur heißt C, kleinere E,
     gleich große D.

   Dazu die Skalierung: λ gegen das MSE-Niveau jedes Systems.
2. **Zweite IC als Diagnose, nicht als Auswahl.** Auf derselben Zellmenge Wahrheit und gewählte Struktur auf der
   Test-IC vergleichen. Schlägt die Wahrheit dort deutlich, enthielte eine zweite Trajektorie die nötige Information.
   Das wäre ein Argument für Validierung innerhalb der Trainingsdaten, nicht für die Nutzung der Test-IC.
3. **Kolinearität ohne Suche.** Korrelation und Konditionszahl der Basisterme entlang jeder Trainingstrajektorie,
   gegen den Fehlerklassen-Befund gelegt. Das prüft die Hypothese aus Abschnitt 6 direkt.
4. **Nur falls 1 bis 3 Klasse A nicht entscheiden: Instrumentierung.** Die Records zählen heute nur, *wie viele*
   verschiedene Strukturen ausgewertet wurden, nicht *welche*. Die Heartbeats enthalten nur die beste Struktur pro
   Level. Nötig wäre ein verhaltensneutrales Protokoll aller ausgewerteten Strukturen mit Loss, Objective und
   Fitversuchen, abgesichert durch eine bitgleiche Kontrolle. Danach ein Nachlauf der 20 S1-Zellen ohne Prior auf
   Orion, ~200 Kernstunden.

**Ergebnis** wäre eine Tabelle Fehlerklasse × Dimension × System, mit beiden Metriken daneben. Daraus folgt, welcher
Hebel die nächste Version trägt: Fit, Suchoperatoren, Komplexitätskontrolle oder Kriterium.

## 8. Risiken

- **Diagnose ohne Ende.** Dagegen: Fragen und Klassen vorher einfrieren, mit Schritt 1 anfangen, nach Schritt 1
  entscheiden.
- **Kleine Fallzahlen.** dim 2 hat 10 exakte Systeme. Aussagen pro Klasse sind zählend, nicht inferenzstatistisch.
- **Die Klassen hängen am Fit.** „Gut gefittet“ heißt immer: bestes von k Starts. Unendlich viele Starts gibt es nicht,
  deshalb ist die Grenze zwischen B und C/D unscharf und muss mit k berichtet werden.
- **Pruning-Schwelle.** Roh und geprunt immer beide berichten, die Schwelle nicht nachträglich anpassen.

## 9. Fragen für die Diskussion

1. Ist die Umstellung von „ob“ auf „warum“ als Beitrag tragfähig, als Paper-Teil oder eigene Arbeit? Oder ist sie nur
   ein Zwischenschritt zur nächsten Version?
2. Sind die fünf Klassen vollständig und trennscharf? Fehlt ein Mechanismus?
3. Ist der Fit über die integrierte Trajektorie (Simulationsfehler) grundsätzlich der falsche Ort für die
   Strukturauswahl? Wie steht das zur Literatur zum Simulations- gegen Prädiktionsfehler bei der Termauswahl in
   NARX-Modellen (Piroddi & Spinelli 2003; Piroddi & Lovera 2008)?
4. Wie misst man „nicht identifizierbar auf einer Trajektorie“ sauber? Reicht die Kolinearität der Basis, oder braucht
   es eine Größe, die die Parameter einbezieht?
5. Absolutes λ: Bug, Konfigurationsfehler oder vertretbare Wahl, wenn man es offen berichtet?

## Quellen im Repository

- C-1 und Vergleichstabelle: `analysis/data/paper1_phaseC_v1/hierarchy_n47_e935c37/`; EvoGrow-Zahlen unverändert seit
  `hierarchy_n46` (DIARY 13.10.).
- WP-T1f: `analysis/data/wp_t1d_neighbourhood/wp_t1f_campaign_1db1193…/` (DIARY 12.10.).
- P-04: `analysis/data/paper1_phaseC_v1/restart_curve/` (DIARY 13.10.).
- WP-T2a S1: `outputs/paper2_t2a_s1_e483f83/`, vorläufig inline ausgewertet (DIARY 17.10.).
- Objective und λ: `src/structure/evogrow.jl` (`ind.objective = lval + λ * length(params)`),
  `studies/regression/run_regression.jl` (`LAMBDA = 1e-3`).
