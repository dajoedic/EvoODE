# Praktischer Benchmark – Annihilator Discovery als Equation-Discovery-Methode

**Stand:** 2026-10-05  
**Status:** Neue diagnostische Spur nach Gate 2A v3  
**Wichtig:** Dieser Benchmark ersetzt oder überschreibt das Ergebnis von Gate 2A **nicht**.

---

## 1. Ausgangslage

Gate 2A v3 hat eine starke Aussage geprüft:

> Lässt sich aus verrauschten Samples einer unbekannten Funktion der minimale annihilierende Differentialoperator eindeutig und statistisch abgesichert identifizieren?

Diese Aussage ist in der getesteten Form gescheitert.

Insbesondere zeigt Anhang B, dass bei 1 % Rauschen mehrere Funktionen nicht eindeutig gegen einfachere falsche Operatorklassen abgrenzbar sind. Das ist ein Identifizierbarkeitsproblem des Messdesigns und kein bloßer Optimierungsfehler.

Daraus folgt aber **nicht automatisch**, dass Annihilator Discovery als praktisches Equation-Discovery-Verfahren unbrauchbar ist.

Die neue Frage lautet deshalb:

> **Ist Annihilator Discovery praktisch konkurrenzfähig als Equation-Discovery-Methode, auch wenn der wahre minimale Operator nicht in jedem Fall eindeutig identifizierbar ist?**

Das ist eine andere Forschungsfrage als Gate 2A.

---

## 2. Was `AMBIGUOUS` bedeutet

`AMBIGUOUS` ist **kein Fehlerzustand**.

Es bedeutet:

> Die Methode hat nicht genügend stabile Evidenz, um genau eine Operatorhypothese verantwortbar auszuwählen.

Die aktuell vorgesehenen Ursachen sind:

- **A1:** Der Nullraum innerhalb der gewählten Klasse ist mehrdimensional; es existiert also nicht nur eine eindeutige Singulärrichtung.
- **A2:** Die Auswahl ist im Bootstrap / über Wiederholungen instabil; weniger als die festgelegte Mehrheit wählt dieselbe Klasse.
- **A3:** Die Unsicherheit der Koeffizientenschätzung ist so groß, dass die verwendete Linearisierung bzw. Unsicherheitsapproximation nicht mehr vertrauenswürdig ist.

Für den praktischen Benchmark ist `AMBIGUOUS` ausdrücklich interessant:

> Eine Methode, die in schwierigen Fällen korrekt abstainiert, kann wissenschaftlich wertvoller sein als eine Methode, die immer eine Gleichung ausgibt und dabei häufiger falsch liegt.

---

## 3. Abgrenzung zu Gate 2A

Das Ergebnis von Gate 2A bleibt unverändert dokumentiert.

Es wird **keine v4 gebaut**, nur um die bisherigen Kill-Kriterien nachträglich doch noch zu bestehen.

Der praktische Benchmark:

- ändert keine Gate-Kriterien;
- ändert keine Referenzoperatoren;
- ändert keine Komplexitätsordnung;
- repariert nicht nachträglich einzelne F1–F10-Fälle;
- benutzt die bestehende Methode so, wie sie jetzt vorliegt;
- bewertet andere Zielgrößen als das ursprüngliche Gate.

Gate 2A beantwortet:

> Ist der minimale Operator eindeutig identifizierbar?

Der neue Benchmark beantwortet:

> Wie oft liefert die Methode in der Praxis eine richtige, nützliche oder bewusst unsichere strukturelle Aussage?

---

## 4. Hypothese

Die zu prüfende Arbeitshypothese lautet:

> **Auch wenn der minimale Annihilator nicht in jeder verrauschten Situation eindeutig identifizierbar ist, kann Annihilator Discovery häufig eine richtige oder zumindest wahre strukturelle Hypothese liefern und bei unzureichender Evidenz sinnvoll abstainieren.**

Diese Hypothese darf scheitern.

---

## 5. Erste Benchmark-Stufe: Operator-Recovery

Zunächst wird **noch keine vollständige ODE-Discovery-Pipeline** gebaut.

Eingabe bleibt:

\[
(x_i, f_i)
\]

Ausgabe bleibt eine Operatorhypothese bzw. ein Unsicherheitszustand.

Ziel ist ausschließlich zu messen, was der bestehende Operator-Discovery-Algorithmus praktisch leistet.

---

## 6. Datensätze

### 6.1 Bestehende Testfunktionen

F1–F10 dürfen verwendet werden, aber **nur noch als bekannte Entwicklungs-/Diagnosefälle**.

Ihre Resultate dürfen nicht als unabhängiger Generalisierungsnachweis dargestellt werden.

### 6.2 Neues Hold-out-Set

Zusätzlich wird ein neues, vorher nicht verwendetes Hold-out-Set erstellt.

Anforderungen:

- Funktionen dürfen nicht zur Entwicklung von v1–v3 verwendet worden sein.
- Referenzoperatoren werden vor dem numerischen Lauf exakt bestimmt.
- Danach wird das Set eingefroren.
- Keine Parameteränderung anhand dieses Sets.
- Möglichst verschiedene:
  - Differentialordnungen;
  - Koeffizientengrade;
  - Funktionsfamilien;
  - Mischformen.

Das Hold-out-Set ist für die spätere wissenschaftliche Bewertung wichtiger als F1–F10.

---

## 7. Noise-Raster

Vorgeschlagenes Raster:

\[
\eta \in
\{0,\;0.001,\;0.005,\;0.01,\;0.02,\;0.05\}
\]

also:

- clean
- 0,1 %
- 0,5 %
- 1 %
- 2 %
- 5 %

Das Noise-Modell bleibt identisch zur bestehenden Gate-Spezifikation.

Keine Anpassung des Rauschmodells nach Sichtung der Ergebnisse.

---

## 8. Ergebniszustände

Jede Realisierung wird in genau einen Zustand eingeordnet:

### `CORRECT`

Die gewählte Klasse entspricht der eingefrorenen Referenzklasse.

### `TRUE_NOT_REF`

Die gefundene Klasse enthält einen **wahren Annihilator**, ist aber nach der eingefrorenen Komplexitätsordnung nicht die Referenzklasse.

Das ist kein Exact-Recovery-Erfolg, aber auch kein strukturell falsches Ergebnis.

### `AMBIGUOUS`

Die Methode gibt bewusst keine eindeutige Klasse aus, weil A1, A2 oder A3 auslöst.

### `WRONG`

Die gewählte Klasse enthält laut exaktem Orakel keinen wahren Annihilator.

### `NONE`

Keine Klasse besteht die vorgesehenen Auswahl-/Validierungsregeln.

---

## 9. Primäre Metriken

### 9.1 Exact-Class Accuracy

\[
\text{Exact Accuracy}
=
\frac{\#\texttt{CORRECT}}{N}
\]

Frage:

> Wie oft wird exakt die Referenzklasse getroffen?

---

### 9.2 True-Annihilator Accuracy

\[
\text{True Accuracy}
=
\frac{\#(\texttt{CORRECT}+\texttt{TRUE\_NOT\_REF})}{N}
\]

Frage:

> Wie oft liefert die Methode zumindest einen mathematisch wahren Annihilator?

---

### 9.3 Wrong Rate

\[
\text{Wrong Rate}
=
\frac{\#\texttt{WRONG}}{N}
\]

Diese Größe ist besonders wichtig.

Eine Methode mit etwas geringerer Coverage, aber sehr niedriger Wrong Rate kann praktisch interessanter sein als eine Methode, die immer entscheidet.

---

### 9.4 Abstention Rate

\[
\text{Abstention Rate}
=
\frac{\#(\texttt{AMBIGUOUS}+\texttt{NONE})}{N}
\]

`AMBIGUOUS` und `NONE` sollen zusätzlich getrennt berichtet werden.

---

### 9.5 Coverage

Definition für eine eindeutige strukturelle Aussage:

\[
\text{Coverage}
=
\frac{\#(\texttt{CORRECT}+\texttt{TRUE\_NOT\_REF}+\texttt{WRONG})}{N}
\]

`AMBIGUOUS` und `NONE` zählen nicht zur Coverage.

---

### 9.6 Conditional Structural Accuracy

Unter den Fällen, in denen die Methode tatsächlich eine Operatorhypothese ausgibt:

\[
\text{Conditional Accuracy}
=
\frac{
\#(\texttt{CORRECT}+\texttt{TRUE\_NOT\_REF})
}{
\#(\texttt{CORRECT}+\texttt{TRUE\_NOT\_REF}+\texttt{WRONG})
}
\]

Diese Metrik ist zentral für die Frage, ob `AMBIGUOUS` als sinnvolle Abstention funktioniert.

Beispiel:

- 68 `CORRECT`
- 12 `TRUE_NOT_REF`
- 17 `AMBIGUOUS`
- 3 `WRONG`

Dann gilt:

\[
\text{Coverage}=83\%
\]

und

\[
\text{Conditional Accuracy}
=
\frac{80}{83}
\approx 96.4\%.
\]

Ein solches Ergebnis wäre trotz nur 68 % Exact-Class Accuracy wissenschaftlich interessant.

---

## 10. Risk–Coverage

Der Benchmark soll ausdrücklich als **Selective-Prediction-Problem** ausgewertet werden.

Risk:

\[
\text{Risk}
=
1-\text{Conditional Accuracy}
\]

Für jedes Noise-Level werden mindestens berichtet:

- Coverage;
- Risk;
- Exact Accuracy;
- True Accuracy;
- Wrong Rate;
- AMBIGUOUS Rate.

Falls sich aus vorhandenen Unsicherheitsgrößen ein kontinuierlicher Confidence Score ableiten lässt, kann zusätzlich eine Risk–Coverage-Kurve erstellt werden.

**Wichtig:** Dafür keine neue Confidence-Heuristik anhand der Benchmark-Ergebnisse erfinden. Nur bereits vorhandene, vorab definierte Größen verwenden.

---

## 11. Weitere Diagnostik

Zusätzlich berichten:

- Ergebnis nach Referenzordnung \(r\);
- Ergebnis nach Koeffizientengrad \(d\);
- Ergebnis nach Funktionsfamilie;
- breite vs. schmale Domäne;
- Runtime;
- Anzahl geprüfter Klassen;
- gegebenenfalls Top-2 / Top-3-Kandidaten.

Top-k ist nur eine Diagnose und ersetzt nicht die primären Ergebniszustände.

---

## 12. Was ein interessantes Ergebnis wäre

Es gibt **keine nachträglich gesetzte Pass/Fail-Grenze**.

Stattdessen wird zunächst deskriptiv bewertet.

Interessant wäre insbesondere ein Muster wie:

- hohe `CORRECT`- oder `TRUE_NOT_REF`-Rate bei niedrigem/moderatem Noise;
- sehr niedrige `WRONG`-Rate;
- steigende `AMBIGUOUS`-Rate mit zunehmendem Noise;
- sinnvolle Risk–Coverage-Beziehung;
- klare Bereiche, in denen die Methode zuverlässig ist;
- keine extreme Laufzeit.

Eine Methode muss nicht 10/10 Fälle lösen, um wissenschaftlich interessant zu sein.

Die relevante Frage lautet:

> **Wie gut ist sie relativ zu etablierten Equation-Discovery-Verfahren und welche Information benötigt sie dafür?**

---

## 13. Noch kein direkter WSINDy-Vergleich in Stufe 1

Ein unmittelbarer Vergleich von Gate-2A-Operator-Recovery mit WSINDy wäre derzeit unfair.

Unsere aktuelle Methode erhält direkt

\[
(x_i,f_i),
\]

während ein vollständiges Equation-Discovery-Verfahren typischerweise aus Trajektorien

\[
x(t)
\]

eine Dynamik rekonstruiert.

Außerdem liefert Gate 2A zunächst einen Operator \(L\), aber noch keine vollständige rekonstruierte Funktion \(\hat f\).

Deshalb dient Stufe 1 ausschließlich der Frage:

> Hat der Annihilator-Ansatz als Strukturdiagnose genügend praktische Signalqualität, um den nächsten Entwicklungsschritt zu rechtfertigen?

---

## 14. Entscheidung nach Stufe 1

### Fall A – klar schlecht

Beispielsweise:

- hohe `WRONG`-Rate;
- kaum brauchbare Ergebnisse schon bei 0,5–1 % Noise;
- `AMBIGUOUS` trennt gute und schlechte Fälle nicht;
- keinerlei Vorteil gegenüber trivialen Baselines.

Dann wird Idee #1 beendet.

### Fall B – interessant

Beispielsweise:

- relevante Exact-/True-Accuracy;
- niedrige Wrong Rate;
- sinnvolle Abstention;
- gute Risk–Coverage-Eigenschaften;
- stabile Resultate auf dem neuen Hold-out-Set.

Dann wird Gate 2B bzw. die vollständige Rekonstruktionskette angegangen.

---

## 15. Zweite Benchmark-Stufe: echte Equation Discovery

Nur bei positivem Ergebnis von Stufe 1.

Dann muss die vollständige Kette gebaut werden:

\[
x(t)
\rightarrow
\text{vector-field evidence}
\rightarrow
L
\rightarrow
\text{solution space}
\rightarrow
\hat f(x)
\]

Erst dann ist ein fairer Vergleich mit vollständigen Equation-Discovery-Verfahren sinnvoll.

Mögliche Baselines:

- SINDy;
- WSINDy / Weak-SINDy;
- symbolische Regression / GP;
- ggf. ODEFormer;
- Oracle/Library-basierte Referenz, sofern methodisch sinnvoll.

---

## 16. Vergleichskriterien in Stufe 2

Dann mindestens:

### Strukturtreue

Findet die Methode die richtige symbolische Struktur?

### Generalisierung

Neue Anfangsbedingungen:

\[
x_0^{\text{test}}
\neq
x_0^{\text{train}}
\]

### Trajectory Fit

Wie gut werden beobachtete und neue Trajektorien reproduziert?

### Robustheit gegen Noise

Gleiches Noise-Raster über alle Methoden, soweit fair möglich.

### Runtime

Training / Discovery / Optimierung getrennt berichten.

### Vorwissen / Hypothesenraum

Explizit dokumentieren:

- Welche Funktionslibrary bekommt jede Methode?
- Welche Operatorordnung bekommt unsere Methode?
- Welche Funktionsfamilien sind vorgegeben?
- Welche Information wird aus den Daten induziert?

Dieser Punkt ist entscheidend für einen fairen Vergleich.

---

## 17. Möglicher wissenschaftlicher Claim

Der ursprüngliche starke Claim

> „Der minimale Annihilator wird aus verrauschten Daten eindeutig identifiziert.“

ist nach Gate 2A nicht haltbar.

Ein möglicher neuer Claim wäre:

> **Annihilator-guided discovery provides a data-driven structural hypothesis for unknown dynamics and explicitly abstains when the available evidence does not support a reliable operator choice.**

Ein stärkerer Claim ist erst zulässig, wenn der praktische Benchmark ihn trägt.

---

## 18. Wichtigste Regel

**Keine Reparatur des alten Gates durch neue Erfolgskriterien.**

Gate 2A bleibt ein negatives Ergebnis bezüglich eindeutiger Minimal-Operator-Identifikation.

Der neue Benchmark ist eine eigenständige Frage:

> **Kann eine methodisch unvollkommene, aber strukturinformative Annihilator-Discovery praktisch konkurrenzfähig sein?**

Genau das soll jetzt gemessen werden.
