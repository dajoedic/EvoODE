# Idee #3 – Residual-Guided EvoGrow

**Stand:** 2026-10-07  
**Status:** Frühe Forschungsidee / möglicher Neustart von EvoGrow

## 1. Kurzfassung

Die ursprüngliche EvoGrow-Idee wird nicht verworfen, sondern an ihrem schwächsten Punkt neu aufgebaut:

> **Die Wachstumsentscheidung soll nicht mehr primär durch Ausprobieren entstehen, sondern aus der Form des aktuellen Modellfehlers.**

Statt viele neue symbolische Terme oder Strukturen zu erzeugen und anschließend zu prüfen, analysiert der Algorithmus das Residuum des aktuellen Modells und leitet daraus ab, **welche Art von symbolischer Struktur vermutlich fehlt**.

Der zentrale Ablauf lautet:

\[
\text{fit}
\rightarrow
\text{residual fingerprint}
\rightarrow
\text{structural diagnosis}
\rightarrow
\text{targeted growth}
\rightarrow
\text{refit}.
\]

---

## 2. Motivation

Bestehende Ansätze haben charakteristische Schwächen:

- **SINDy:** sehr schnell und interpretierbar, aber abhängig von einer vorgegebenen Library.
- **W-SINDy:** robuster gegen Noise, aber mit demselben Library-Bias.
- **GP / klassische Symbolic Regression:** freie Struktursuche, aber großer kombinatorischer Suchraum und oft hohe Laufzeiten.
- **ODEFormer:** freie symbolische Vorhersage, aber stark abhängig von einem gelernten Prior aus dem Pretraining und weniger transparent.
- **EvoGrow v1:** Struktur wächst inkrementell, aber die Growth-Policy ist zu wenig datengetrieben und probiert zu viel aus.

Die neue Idee versucht die Mitte:

> **Freie bzw. wachsende Struktursuche, aber jeder Wachstumsschritt wird direkt aus dem aktuellen Fehlerbild begründet.**

---

## 3. Kernidee

Angenommen, das aktuelle Modell lautet

\[
\hat f(x)=ax.
\]

Aus den Daten ergibt sich ein Residuum

\[
r(x)=f_{\text{data}}(x)-\hat f(x).
\]

Der Algorithmus fragt nun nicht einfach:

> „Welcher Term aus einer Library korreliert mit \(r\)?“

Sondern:

> **„Welche symbolische Operation oder Funktionsfamilie erklärt die Form von \(r\)?“**

Beispiele für mögliche Residual-Fingerprints:

- **additive Abhängigkeit:** Residuum hängt überwiegend von einer einzelnen Variable ab;
- **multiplikative Interaktion:** \(r/f\) zeigt systematische Abhängigkeit von einer weiteren Variable;
- **rationale / saturierende Struktur:** Transformationen wie \(1/r\) zeigen einfache Beziehungen;
- **exponentielle Struktur:** \(\log |r|\) zeigt annähernd lineares Verhalten;
- **trigonometrische Struktur:** periodisches Residualmuster;
- **Interaktionsstruktur:** Residuum hängt nur von bestimmten Variablenkombinationen ab.

Das Residuum dient damit als **Diagnosesignal für den nächsten Wachstumsschritt**.

---

## 4. Möglicher Basisalgorithmus

### Schritt 1 – Einfaches Startmodell

Mit einer sehr einfachen Struktur beginnen, z. B.

- linear,
- niedriger Polynomgrad,
- oder bewusst minimaler symbolischer Ausdruck.

### Schritt 2 – Parameterfit

Parameter des aktuellen Modells auf den Daten bestimmen.

### Schritt 3 – Residualanalyse

Das Residuum wird nicht nur als Loss verwendet, sondern strukturell analysiert.

Dazu werden wenige vordefinierte diagnostische Transformationen und Tests verwendet.

### Schritt 4 – Structural Diagnosis

Aus den Residual-Fingerprints wird eine kleine Menge plausibler Wachstumsschritte erzeugt.

Beispiel:

\[
ax
\rightarrow
ax+bxy
\]

wenn das Residuum auf eine multiplikative Kopplung mit \(y\) hinweist.

### Schritt 5 – Targeted Growth

Nur strukturell begründete Erweiterungen werden erzeugt und getestet.

### Schritt 6 – Refit und Validierung

Die neuen Kandidaten werden vollständig neu gefittet und anhand von Rekonstruktion, Generalisierung und Komplexität bewertet.

Danach beginnt der Zyklus erneut.

---

## 5. Unterschied zu EvoGrow v1

Der zentrale Unterschied liegt in der Growth-Policy.

### EvoGrow v1

\[
\text{aktuelle Struktur}
\rightarrow
\text{mögliche Erweiterungen erzeugen}
\rightarrow
\text{fitten}
\rightarrow
\text{beste auswählen}
\]

Die Suche bleibt relativ stark durch Trial-and-Error geprägt.

### Residual-Guided EvoGrow

\[
\text{aktuelle Struktur}
\rightarrow
\text{Fehler diagnostizieren}
\rightarrow
\text{gezielte strukturelle Erweiterung}
\rightarrow
\text{fitten}
\]

Der Fehler wird damit nicht nur bewertet, sondern **als Information über die fehlende Struktur verwendet**.

---

## 6. Abgrenzung zu bestehenden Methoden

Die Idee darf nicht zu einem klassischen „Feature Recovery“-Verfahren werden.

Nicht ausreichend wäre:

> Residuum gegen eine große bestehende Library korrelieren und den besten Term hinzufügen.

Das wäre zu nah an bekannten adaptiven SINDy- bzw. Matching-Pursuit-Ansätzen.

Der mögliche Neuheitskern lautet:

> **Diagnose der fehlenden symbolischen Operation bzw. Funktionsfamilie aus charakteristischen Residualmustern.**

Der Algorithmus soll also möglichst nicht nur entscheiden, **welcher vorhandene Term fehlt**, sondern **wie der Ausdrucksbaum strukturell wachsen sollte**.

---

## 7. Warum die Idee interessant sein könnte

Potenzielle Vorteile:

- echte Struktursuche statt ausschließlich Library-Selektion;
- deutlich kleinerer Suchraum als klassische GP-Verfahren;
- vollständig interpretierbarer Suchprozess;
- keine große Vortrainingsphase wie bei ODEFormer;
- jeder Wachstumsschritt ist datengetrieben begründet;
- natürliche Verbindung von Strukturtreue und Generalisierung;
- potenziell moderate Laufzeiten;
- bestehende EvoGrow-Infrastruktur und Erfahrung könnten teilweise wiederverwendet werden.

---

## 8. Mögliche PhD-Linie

### Paper 1 – Residual-Guided EvoGrow

Ein einfacher Kernalgorithmus mit wenigen diagnostizierbaren Operatorfamilien.

Beispielsweise:

- additive Terme;
- Produkte / Interaktionen;
- Polynome;
- rationale / saturierende Formen;
- Exponentialfunktionen;
- trigonometrische Funktionen.

Benchmark gegen:

- SINDy;
- W-SINDy;
- ODEFormer;
- weitere etablierte ODE-Discovery-Verfahren.

Metriken:

- Strukturtreue;
- Rekonstruktions-\(R^2\);
- Generalisierung;
- Laufzeit;
- Robustheit gegen moderates Noise.

### Paper 2 – Noise-Robust Residual Diagnosis

Die größte Schwäche von Paper 1 wird gezielt adressiert:

- schwache oder integrale Residuen;
- robuste Glättung;
- Unsicherheit der Residual-Fingerprints;
- Multi-Scale-Diagnostik.

Ziel:

> Fehlende Struktur auch dann zuverlässig erkennen, wenn \(\dot x\) oder lokale Residuen stark verrauscht sind.

### Paper 3 – Uncertainty and Multi-Trajectory Structural Growth

Erweiterung um:

- mehrere Initialbedingungen;
- Konfidenz für Growth-Entscheidungen;
- konkurrierende Wachstumspfade;
- explizites `AMBIGUOUS`;
- eventuell automatische Erweiterung der verfügbaren Grammar.

Ziel:

> Nicht nur eine Struktur finden, sondern erkennen, wann die Daten einen Wachstumsschritt eindeutig stützen.

---

## 9. Bewertungsphilosophie

Die Methode wird nicht gegen eine theoretisch optimale Lösung als hartes Kill-Kriterium bewertet.

Entscheidend ist der gepaarte Vergleich gegen reale Konkurrenzverfahren unter identischen Bedingungen:

- gleiche ODEs;
- gleiche Trajektorien;
- gleiche Initialbedingungen;
- gleiche Rauschlevel;
- gleiche Samplingdichte;
- gleiche Train-/Validation-/Test-Splits.

Ein Verfahren muss nicht jede ODE exakt rekonstruieren.

Relevant ist:

> **Ist Residual-Guided EvoGrow hinsichtlich Struktur, Generalisierung und Robustheit konkurrenzfähiger als existierende Verfahren?**

---

## 10. Billigster Kill-Test

Bevor ein vollständiger Algorithmus entwickelt wird, wird nur die zentrale Hypothese geprüft:

> **Trägt das Residuum systematisch genug Information, um die Art der fehlenden Struktur zu erkennen?**

Vorgehen:

1. Kleine Menge bekannter ODE-Terme auswählen.
2. Jeweils absichtlich einen strukturellen Bestandteil aus dem Modell entfernen.
3. Residuum berechnen.
4. Prüfen, ob einfache diagnostische Transformationen die fehlende Operatorfamilie zuverlässig unterscheiden.

Beispiele:

- fehlender \(xy\)-Term;
- fehlendes \(x^2\);
- fehlende Sättigung;
- fehlendes \(e^x\);
- fehlendes \(\sin x\).

Wenn die Residual-Fingerprints bereits rauschfrei nicht unterscheidbar sind, wird die Idee verworfen.

Wenn sie unterscheidbar sind, folgen:

- moderates Noise;
- echte iterative Suche;
- vollständiger ODEBench-Vergleich.

---

## 11. Zentrale Forschungsfrage

Die entscheidende Frage lautet:

> **Kann der systematische Fehler eines unvollständigen ODE-Modells zuverlässig anzeigen, welche symbolische Struktur im Modell fehlt?**

Wenn die Antwort ja ist, könnte daraus ein neuer Typ datengetriebener symbolischer Struktursuche entstehen:

> **Nicht blind suchen, sondern aus jedem Fehler lernen, wie der Ausdruck wachsen muss.**

---

## 12. Einschätzung 2026-10-27 (nach Phase C)

**Bleibt im Ideenpool, Rang 1 von 3.** Am besten abgesichert der drei Ideen.

- Der Kern ist teilweise bestätigt: Im Nebenprojekt Residual Growth (`docs/sideproject_residual_growth_protocol.md`, `DIARY.md` 2026-10-17) erreicht „Term hinzufügen, alle Koeffizienten neu fitten, rückwärts entfernen“ im Weak-Form-Raum bei σ = 0 und vorgegebener Modellgröße die wahre Struktur, sogar aus den falschen Endstrukturen von C-1 heraus.
- Die Residuen-Rangfolge selbst ist FROLS (Billings, Chen & Korenberg 1989). Neu kann nur die Kombination aus inkrementellem Wachstum, Weak-Regression und Simulationsprüfung sein.
- **Schwachstelle: der Fingerabdruck.** WP-R1 zeigt, dass die Polynombasis auch Surrogat-Systeme im Ableitungsraum fast perfekt annähert (Median 0.999993). Fehlt eine sättigende oder transzendente Familie, absorbieren die Polynome auf dem beobachteten Zustandsbereich das meiste davon, und im Residuum bleibt wenig Unterscheidbares. Der Kill-Test aus Abschnitt 10 zielt genau auf diese Stelle und ist der wichtigste der drei Kill-Tests.

**Wann wieder aufnehmen:** wenn Q5 des Nebenprojekts abgeschlossen ist **und** die Fehleranatomie (`docs/diskussion_warum_scheitert_die_suche.md`) überwiegend Klasse B zeigt (Struktur erreicht, schlecht gefittet). Kein paralleler Strang neben dem Nebenprojekt.
