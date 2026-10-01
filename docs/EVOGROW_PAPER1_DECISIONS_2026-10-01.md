# EvoGrow Paper 1 – aktueller Entscheidungsstand
**Stand: 01.10.2026**

> **Datierte Entscheidungsquelle, wird nicht nachgeführt.** Die verbindliche Fassung steht in
> `PAPER_1.md` („Scope Extension (2026-10-01)“) und `docs/paper1_phaseC_benchmark_plan.md` §9.
> **In einem Punkt überholt:** §11 und §14.1 wollten die Grenze `[-10, 10]` nicht in Paper 1
> übernehmen. In der anschließenden Diskussion am selben Tag wurde entschieden, dass Paper 1 genau
> das Phase-C-EvoGrow **mit** `[-10, 10]` ist. Der Grenzen-Pilot ist eine Sensitivitätsdiagnose
> (C-8) und entscheidet nur über die nächste Version. Außerdem fixiert: PySR ist der
> GP-Vertreter, Strukturmetriken gelten nur auf den 30 exakten Systemen, und die Generalisierung
> unter Rauschen wird gegen die saubere Wahrheit gemessen.

## 1. Ziel von Paper 1

Paper 1 soll ein **grundlegendes EvoGrow-Paper** werden.

Ziel ist ausdrücklich **nicht**, jetzt bereits zahlreiche Erweiterungen in die Methode einzubauen. EvoGrow soll zunächst als möglichst einfacher, nachvollziehbarer Basisalgorithmus etabliert und gegen etablierte Verfahren verglichen werden.

Die gewünschte Story ist:

> EvoGrow ist ein einfacher trajectory-based Ansatz zur schrittweisen symbolischen ODE-Discovery.  
> Die Grundversion soll zeigen, dass sie auf relevanten Benchmarks zumindest konkurrenzfähig ist und in einzelnen Regimen Vorteile gegenüber bestehenden Verfahren besitzt.

Wichtig ist dabei:

- keine komplexen Zusatzmechanismen in Paper 1,
- keine Ranking-Heuristiken,
- kein Multiple Shooting,
- keine zusätzlichen Suchstrategien,
- keine aufwendigen Spezialbehandlungen für einzelne Problemklassen.

Solche Erweiterungen sollen bewusst **späteren Papers** vorbehalten bleiben – analog dazu, wie auf der ursprünglichen SINDy-Methode später spezialisierte Varianten wie Weak-SINDy aufgebaut wurden.

---

## 2. Grundidee der Paper-Story

Paper 1 soll vier Dinge sauber zeigen:

1. **Wie EvoGrow funktioniert**
   - progressive Termbibliothek,
   - evolutionäre Struktursuche,
   - Fit auf integrierten Trajektorien,
   - Stufenkappe.

2. **Wie gut EvoGrow auf sauberen Daten funktioniert**
   - Rekonstruktion,
   - Generalisierung,
   - Strukturfindung.

3. **Wie robust EvoGrow gegen schwierigere Beobachtungsbedingungen ist**
   - Messrauschen,
   - reduzierte bzw. unregelmäßige Abtastung.

4. **Wo die einfache Grundversion Grenzen hat**
   - insbesondere die bereits beobachtete Auswahl leicht fitbarer Surrogatstrukturen.

Die Schwächen sollen nicht durch zusätzliche Mechanismen in Paper 1 verdeckt werden, sondern sauber dokumentiert werden und als Motivation für spätere methodische Erweiterungen dienen.

---

## 3. Metriken

Die bisherige alleinige Betrachtung von `R² > 0.9` reicht nicht aus.

Grund: Eine falsche Ersatzstruktur kann eine Trainingstrajektorie sehr gut rekonstruieren und trotzdem den zugrunde liegenden Mechanismus nicht korrekt abbilden.

Deshalb werden **Strukturqualität und dynamische Qualität getrennt bewertet**.

### 3.1 Raw Exact Recovery

Der gefundene Support entspricht exakt dem Ground-Truth-Support.

- keine Schwelle,
- sehr strenge Metrik,
- binär: Treffer / kein Treffer.

Diese Metrik bleibt bestehen.

---

### 3.2 Pruned Exact Recovery

Wie bisher wird eine feste Koeffizientenschwelle verwendet:

\[
\tau = \max(10^{-6}, 10^{-3}\cdot \max_i |c_i|)
\]

Ein Term gilt als vorhanden, wenn

\[
|c_i| > \tau.
\]

Danach wird geprüft, ob der verbleibende Support exakt dem Ground Truth entspricht.

Wichtig:

- Die Schwelle wird **vorab festgelegt**.
- Sie wird später nicht abhängig von Noise-Level, Methode oder Ergebnis verändert.
- Es gibt keine nachträgliche Optimierung der Schwelle auf die Benchmark-Ergebnisse.

---

### 3.3 Structural F1

Zusätzlich wird eine kontinuierliche Strukturmetrik eingeführt.

Für Ground-Truth-Terme \(T\) und gefundene Terme \(\hat T\):

\[
Precision = \frac{|T\cap\hat T|}{|\hat T|}
\]

\[
Recall = \frac{|T\cap\hat T|}{|T|}
\]

\[
F1_{structure} =
\frac{2 \cdot Precision \cdot Recall}
{Precision + Recall}
\]

Die Termanwesenheit wird mit derselben festen Pruning-Schwelle bestimmt wie bei `Pruned Exact Recovery`.

Damit kann unterschieden werden zwischen:

- vollständig korrekter Struktur,
- fast korrekter Struktur mit einem Zusatzterm,
- teilweise korrekter Struktur,
- komplett falscher Struktur.

Das ist insbesondere wichtig, weil Exact Recovery allein alle nicht perfekten Lösungen gleich behandelt.

---

## 4. Aggregation der Strukturmetriken

Die Aggregation soll hierarchisch erfolgen:

1. Metrik pro Gleichung,
2. Aggregation auf Systemebene,
3. Aggregation über den Benchmark.

Damit wird verhindert, dass Systeme mit mehreren Gleichungen automatisch stärker gewichtet werden.

---

## 5. Symbolische Äquivalenz

Innerhalb von EvoGrow ist dieses Problem klein, weil EvoGrow aus einer festen Termbibliothek auswählt.

Beispiele der Basis:

- \(1\)
- \(u_i\)
- \(u_i^2\)
- \(u_i u_j\)
- \(u_i^3\)
- \(\sin(u_i)\)
- \(\cos(u_i)\)

EvoGrow erzeugt keine beliebigen symbolischen Ausdrucksbäume, bei denen beispielsweise

\[
x^2
\]

und

\[
x\cdot x
\]

als unterschiedliche Strukturen auftreten könnten.

Für EvoGrow kann Structural F1 deshalb direkt über den Term-Support berechnet werden.

Bei externen Symbolic-Regression-Verfahren wie ODEFormer, PySR oder GP-Verfahren kann vor der Strukturbewertung eine symbolische Vereinfachung bzw. kanonische Darstellung notwendig sein.

---

## 6. Dynamische Metriken

Neben den Strukturmetriken bleiben die dynamischen Metriken bestehen.

### Primär

- **Generalization R²**
- **Reconstruction R²**

Dabei soll Generalisierung stärker gewichtet werden als reine Rekonstruktion, weil eine gut rekonstruierte Trainingstrajektorie auch durch eine falsche Surrogatstruktur entstehen kann.

Die bisherige Schwelle `R² > 0.9` kann weiterhin als leicht interpretierbare Erfolgsrate berichtet werden.

Zusätzlich sollten möglichst auch die zugrunde liegenden kontinuierlichen R²-Werte gespeichert und ausgewertet werden.

---

## 7. Optional: Vector-Field Error

Eine mögliche zusätzliche diagnostische Metrik ist ein Fehler direkt im Vektorfeld:

\[
\frac{\|f_{pred}(x)-f_{true}(x)\|_2}
{\|f_{true}(x)\|_2}
\]

Diese Metrik könnte später helfen, zwischen

- guter Trajektorienrekonstruktion und
- tatsächlich korrektem dynamischem Verhalten

zu unterscheiden.

Für Paper 1 ist sie momentan **optional** und kein Muss.

---

## 8. Wichtig: Metriken sind weitgehend post hoc berechenbar

Die meisten dieser Metriken verursachen praktisch keine zusätzliche Trainings- oder Clusterzeit.

Voraussetzung ist, dass pro Run ausreichend Rohinformation gespeichert wird.

Mindestens speichern:

- gefundene Terme,
- alle Koeffizienten,
- ungeprunte Struktur,
- Ground-Truth-Struktur,
- Trainings-/Rekonstruktionsvorhersagen,
- Generalisierungsvorhersagen,
- Initial Condition,
- Seed,
- Noise-Level,
- Sampling/Subsampling-Bedingung,
- Methodenkonfiguration.

Grundsatz:

> Lieber zu viele Rohoutputs speichern als später teure Experimente wiederholen, weil eine nachträgliche Metrik nicht mehr berechnet werden kann.

Die **primären Metriken** sollten vor den neuen Experimenten festgelegt werden. Zusätzliche diagnostische Metriken dürfen später ergänzt werden.

---

# 9. Robustheitsbenchmark: Noise + Sampling

Paper 1 soll nicht nur saubere Daten untersuchen.

Es werden zwei Robustheitsachsen verwendet:

1. **Messrauschen**
2. **reduzierte / unregelmäßige Beobachtung**

Das Experiment soll möglichst nah am ODEFormer-/ODEBench-Protokoll bleiben.

---

## 9.1 Noise

Vorgesehen sind die Noise-Level

\[
\sigma \in
\{0,\ 0.01,\ 0.02,\ 0.03,\ 0.04,\ 0.05\}.
\]

Verwendet wird multiplikatives gaußsches Rauschen entsprechend dem ODEFormer-Protokoll.

Das Rauschen wird bei uns **geseedet**, damit die Experimente reproduzierbar bleiben.

---

## 9.2 Sampling / Subsampling

Analog zum großen ODEFormer-Benchmark:

\[
\rho \in \{0,\ 0.5\}.
\]

Das bedeutet:

- vollständige Beobachtung,
- zufälliges Entfernen von 50 % der Beobachtungspunkte.

Wichtig für die Formulierung im Paper:

Das ist **nicht** einfach eine halbierte reguläre Sampling-Frequenz.

Die verbleibenden Punkte sind zufällig verteilt.

Deshalb sollte das korrekt bezeichnet werden als beispielsweise:

- `irregular subsampling`
- `random subsampling`
- `missing observations`

und nicht pauschal als regulär halbierte Sampling Rate.

---

## 9.3 Kombination

Damit ergibt sich zunächst ein überschaubares Raster aus

\[
6 \text{ Noise-Level} \times 2 \text{ Sampling-Bedingungen}
= 12 \text{ Bedingungen}.
\]

Das ist deutlich überschaubarer als ein eigenes großes Raster und hat den Vorteil, dass die Versuchsanordnung direkt an einen etablierten Vergleich anschließt.

---

# 10. Baselines

Die Baselines sollen **nah am ODEFormer-Paper**, aber bewusst kompakt gewählt werden.

Ziel ist nicht, Dutzende existierende Verfahren neu zu implementieren.

Aktuell sinnvoll:

- **SINDy**
- **ODEFormer**
- **ein klassisches Symbolic-Regression-/GP-Verfahren**
- eventuell ein weiterer etablierter Vertreter wie **ProGED oder PySR**

Für den Noise-Vergleich kann zusätzlich **Weak-SINDy** relevant sein, da es explizit für robustere Systemidentifikation unter schwierigeren Datenbedingungen entwickelt wurde.

Die endgültige Auswahl wird bewusst klein gehalten.

---

# 11. Parametergrenze: [-10, 10]

Die bisherige feste Parametergrenze

\[
[-10,10]
\]

ist problematisch.

Sie gehört nicht zur konzeptionellen Kernidee von EvoGrow und macht einige Ground-Truth-Systeme bereits konstruktiv unerreichbar.

Deshalb soll sie **nicht einfach aus historischen Gründen in Paper 1 übernommen werden**.

Gleichzeitig soll die Entscheidung nicht durch nachträgliches Benchmark-Tuning getroffen werden.

---

## 11.1 Geplanter kleiner Bound-Pilot

Verglichen werden drei Varianten:

### A – bisherige kleine Grenze

\[
[-10,10]
\]

### B – große numerische Grenze

Eine deutlich größere feste Grenze, die Ground-Truth-Parameter des Benchmarks nicht konstruktiv ausschließt.

### C – unbounded

Keine künstliche Parametergrenze.

---

## 11.2 Ziel des Piloten

Der Pilot soll **nicht** beantworten:

> Welche Variante liefert die höchsten Benchmark-Scores?

Sondern:

> Kann die künstliche Parametergrenze entfernt werden, ohne dass der Optimierer numerisch instabil wird?

Das verhindert nachträgliches Tuning auf den Benchmark.

---

## 11.3 Testfälle

Der Pilot soll klein bleiben und gezielt schwierige sowie Kontrollfälle enthalten.

Sinnvoll sind insbesondere:

- dim-3-Systeme, die durch `[-10,10]` bisher konstruktiv ausgeschlossen sind,
- System 52 als Fall, bei dem die wahre Struktur nachweislich fitbar ist,
- System 61 als schwieriger Optimierungsfall,
- einige dim-1-/dim-2-Systeme als Kontrollgruppe.

---

## 11.4 Entscheidungsregel

Wenn `unbounded` numerisch stabil funktioniert:

> **unbounded verwenden.**

Wenn unbounded zu systematischen numerischen Problemen führt:

> große feste Grenze ausschließlich als numerischen Guard verwenden.

Die Grenze soll dann so gewählt werden, dass sie keine bekannten Ground-Truth-Systeme konstruktiv ausschließt.

Nicht vorgesehen für Paper 1:

- adaptive Bounds,
- systemabhängige Bounds,
- aufwendige Normalisierungsmechanismen,
- spezielle parameterabhängige Skalierungen.

---

# 12. Was explizit NICHT in Paper 1 kommt

Die folgenden Ideen bleiben bewusst spätere Erweiterungen:

- Ranking im Ableitungsraum,
- Struktur-Vorsortierung,
- Pretuning als Bewertungssignal,
- Multiple Shooting,
- komplexe Warmstart-Strategien,
- Noise-spezifische Suchregeln,
- adaptive Stopping-Regeln,
- zusätzliche Metaheuristiken.

Diese Punkte sind potentielle Inhalte späterer EvoGrow-Versionen bzw. Folgepapers.

---

# 13. Aktuelles Paper-1-Metrikset

Der aktuelle Kern wäre:

\[
\boxed{
\text{Raw Exact Recovery}
+
\text{Pruned Exact Recovery}
+
\text{Structural F1}
+
\text{Generalization R²}
+
\text{Reconstruction R²}
}
\]

Optional:

\[
\text{Vector-Field Error}
\]

Damit werden Strukturqualität und dynamische Qualität klar getrennt.

---

# 14. Derzeit noch offene Punkte

Die konzeptionellen Grundfragen sind weitgehend geklärt.

Offen bleiben hauptsächlich:

### 1. Ergebnis des Parameter-Bound-Piloten

Danach wird die endgültige EvoGrow-v1-Konfiguration eingefroren.

### 2. Umfang des teuren EvoGrow-Robustheitsbenchmarks

Zu entscheiden ist noch, ob Noise/Subsampling für EvoGrow nur auf

- dim 1 und dim 2

oder auch auf

- dim 3 und dim 4

gerechnet wird.

Aufgrund der aktuellen Ergebnisse und Kosten spricht momentan viel dafür, den teuren Robustheitsbenchmark zunächst auf dim 1/2 zu konzentrieren.

### 3. Finale kleine Baseline-Liste

Voraussichtlich:

- SINDy,
- ODEFormer,
- ein klassischer Symbolic-Regression-/GP-Vertreter,
- eventuell ProGED/PySR,
- optional Weak-SINDy im Noise-Teil.

---

# 15. Aktuelles Zielbild

Paper 1 soll bewusst **kein maximal optimierter EvoGrow** sein.

Es soll zeigen:

> Hier ist die einfache Grundmethode.  
> So funktioniert sie.  
> Hier ist sie konkurrenzfähig.  
> Hier besitzt sie interessante Vorteile.  
> Hier liegen ihre Grenzen.  
> Und genau aus diesen Grenzen ergeben sich die nächsten methodischen Erweiterungen.

Damit entsteht ein sauberes Fundament für eine EvoGrow-Paper-Serie, statt bereits im ersten Paper sämtliche Verbesserungen in einen schwer interpretierbaren Gesamtalgorithmus zu integrieren.
