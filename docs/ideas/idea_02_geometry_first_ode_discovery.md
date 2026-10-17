# Idee #2 – Geometry-First ODE Discovery

**Stand:** 2026-10-07  
**Status:** Frühe, aber pitchbare Forschungsidee

## 1. Kurzfassung

Die Grundidee ist, die Struktur einer ODE **nicht zuerst über eine Schätzung von \(\dot x\)** zu identifizieren, sondern zunächst nur aus der **Geometrie beobachteter Trajektorien**.

Für zwei nahe Punkte einer Trajektorie gilt

\[
\Delta x = x(t+h)-x(t).
\]

Für kleines \(h\) muss das wahre Vektorfeld \(f(x)\) ungefähr parallel zu dieser lokalen Bewegungsrichtung sein.

In 2D ergibt sich daraus beispielsweise die Bedingung

\[
\Delta x_1 f_2(x)-\Delta x_2 f_1(x)\approx 0.
\]

Damit lässt sich die **Richtung bzw. Struktur des Vektorfeldes** untersuchen, ohne zunächst explizit

\[
\dot x \approx \frac{\Delta x}{h}
\]

zu berechnen.

Der zentrale Pitch lautet:

> **Geometry tells us what the dynamics are. Time tells us how fast they run.**

---

## 2. Motivation

Klassische Verfahren wie SINDy lösen im Kern

\[
\dot X = \Theta(X)\Xi.
\]

Damit hängt die Strukturidentifikation direkt von einer guten Schätzung von \(\dot X\) ab. Unter Messrauschen kann genau diese Ableitungsschätzung problematisch werden.

Geometry-First ODE Discovery trennt dagegen zwei Informationsquellen:

1. **Trajektoriengeometrie:** Welche Richtung hat das Vektorfeld?
2. **Zeitinformation:** Wie schnell bewegt sich das System entlang dieser Richtung?

Die Hoffnung ist, dass insbesondere die **Struktur** robuster aus der Trajektoriengeometrie bestimmt werden kann.

---

## 3. Möglicher Basisalgorithmus

### Stufe 1 – Geometry-based structure discovery

Aus einer interpretierbaren Kandidatenbibliothek, z. B.

\[
1,\ x_1,\ x_2,\ x_1^2,\ x_1x_2,\ldots
\]

wird ein sparsames Vektorfeld

\[
f_\Xi(x)
\]

gesucht, dessen Richtung möglichst gut mit den lokal beobachteten Trajektorienrichtungen übereinstimmt.

Anders als bei Standard-SINDy werden die einzelnen Komponenten des Vektorfeldes dabei nicht unabhängig gegen \(\dot x_i\) regressiert. Die Gleichungen werden über die gemeinsame Richtungsbedingung gekoppelt.

### Stufe 2 – Time-based magnitude identification

Nach Bestimmung einer plausiblen Struktur wird die Zeitinformation genutzt, um die Geschwindigkeit entlang des gefundenen Vektorfeldes bzw. die verbleibenden Koeffizienten zu bestimmen.

Damit wird die Struktur zunächst möglichst unabhängig von einer expliziten Ableitungsschätzung identifiziert.

---

## 4. Zentrales mathematisches Problem

Die reine Trajektoriengeometrie bestimmt ein Vektorfeld nicht eindeutig.

Falls

\[
f(x)
\]

eine Trajektoriengeometrie erzeugt, dann erzeugt auch

\[
a(x)f(x)
\]

für geeignetes positives \(a(x)\) dieselben geometrischen Bahnen, allerdings mit anderer Zeitparametrisierung.

Das ist kein Randproblem, sondern die zentrale Identifizierbarkeitsfrage des Ansatzes.

Ein möglicher Lösungsweg:

1. Bestimme alle sparsamen Strukturen, die geometrisch mit den Daten verträglich sind.
2. Nutze anschließend die Zeitinformation, um zwischen diesen Kandidaten zu unterscheiden.
3. Bleiben mehrere strukturell unterschiedliche Modelle kompatibel, wird explizit **AMBIGUOUS** ausgegeben.

Damit könnte Identifizierbarkeit direkt Bestandteil des Algorithmus werden.

---

## 5. Warum die Idee interessant sein könnte

Potenzielle Vorteile:

- explizit **interpretierbare ODE-Struktur**;
- Strukturfindung zunächst ohne direkte \(\dot x\)-Regression;
- mögliche Robustheit gegenüber Messrauschen;
- gemeinsame Identifikation aller Zustandskomponenten;
- sehr einfache mathematische Grundidee;
- potenziell schnelle Optimierung über Sparse Regression / lineare Algebra;
- klare Erweiterungspunkte;
- explizite Behandlung von Nicht-Identifizierbarkeit.

---

## 6. Abgrenzung

Die Idee darf nicht lediglich zu

> „SINDy mit einem anderen Residuum“

werden.

Derivative-free ODE Discovery existiert bereits, etwa über Weak-SINDy, Integral-SINDy oder Runge-Kutta-basierte Verfahren.

Der mögliche Neuheitskern wäre daher nicht allein das Vermeiden von \(\dot x\), sondern:

> **Strukturidentifikation primär aus der Trajektorienrichtung, gefolgt von separater Identifikation der Zeitparametrisierung.**

Auch geometrisch eingeschränkte SINDy-Verfahren existieren. Diese nutzen Geometrie typischerweise als bekannte oder gelernte Nebenbedingung für das Vektorfeld. Geometry-First Discovery würde dagegen die beobachtete Trajektoriengeometrie selbst als primäres Struktur-Signal verwenden.

Eine gründliche Novelty-Prüfung ist vor einer Implementierung notwendig.

---

## 7. Mögliche PhD-Linie

### Paper 1 – Geometry-First Sparse ODE Discovery

Ein einfacher Basisalgorithmus:

- polynomialer bzw. fester interpretierbarer Funktionsraum;
- Strukturidentifikation aus Trajektorienrichtungen;
- anschließende Magnituden-/Koeffizientenschätzung;
- Vergleich gegen SINDy, W-SINDy, ODEFormer und weitere etablierte Methoden.

Ziel: zeigen, dass Geometry-First Discovery eine konkurrenzfähige Alternative zur direkten Ableitungsregression darstellt.

### Paper 2 – Noise-Robust Geometry Discovery

Erweiterung für verrauschte Daten:

- robuste lokale Tangentenschätzung;
- Multi-Scale-Tangenten;
- adaptive Fenster;
- Unsicherheitsmodellierung der Richtungsinformation.

Ziel: bessere Strukturidentifikation unter realistischem Messrauschen.

### Paper 3 – Identifiability and Multi-Trajectory Discovery

Systematische Behandlung geometrisch äquivalenter Vektorfelder:

- mehrere Anfangsbedingungen;
- explizite Kandidatenmengen;
- Identifizierbarkeitstest;
- AMBIGUOUS als zulässiges Ergebnis;
- eventuell aktive Auswahl informativer Trajektorien.

Ziel: erkennen, wann die beobachteten Daten eine eindeutige ODE-Struktur tatsächlich tragen.

---

## 8. Bewertungsphilosophie

Die Methode soll **nicht primär gegen eine theoretisch optimale Lösung** bewertet werden.

Entscheidend ist der gepaarte Vergleich gegen real existierende Verfahren unter denselben Bedingungen:

- gleiche ODEs;
- gleiche Trajektorien;
- gleiche Initialbedingungen;
- gleiche Rauschlevel;
- gleiche Samplingdichten;
- gleiche Train-/Validation-/Test-Splits.

Wichtige Metriken:

- Strukturtreue;
- Rekonstruktions-\(R^2\);
- Generalisierung auf neue Anfangsbedingungen;
- Robustheit gegenüber Rauschen;
- Laufzeit.

Ein Ergebnis von beispielsweise 7/10 korrekt identifizierten Systemen kann wissenschaftlich stark sein, wenn relevante Baselines nur 4–5/10 erreichen.

---

## 9. Billigster Kill-Test

Bevor ein vollständiger Algorithmus entwickelt wird:

1. 5–10 kleine, zweidimensionale ODE-Systeme auswählen.
2. Zunächst rauschfreie Trajektorien verwenden.
3. Nur Stufe 1 testen.
4. Prüfen, ob die beobachteten Trajektorienrichtungen ausreichend Information liefern, um die wahre Sparse-Struktur gegenüber konkurrierenden Sparse-Strukturen zu bevorzugen.

Die Kernfrage lautet:

> **Trägt die lokale Trajektorienrichtung überhaupt genug Information für zuverlässige Strukturidentifikation?**

Falls nein, wird die Idee früh verworfen.

Falls ja, folgen:

- Zeitparametrisierung;
- Rauschen;
- Generalisierung;
- Vergleich gegen Baselines.

---

## 10. Aktuelle Einschätzung

Die Idee ist interessant, weil Problem, Mechanismus und Erweiterungspfad zusammenpassen.

Sie kombiniert:

- eine sehr einfache Grundidee;
- direkten Bezug zu erklärbarer ODE Discovery;
- potenziell geringere Abhängigkeit von verrauschten Ableitungsschätzungen;
- eine klare Identifizierbarkeitsfrage;
- natürliche Erweiterungen für mehrere Papers.

Der wichtigste offene Punkt ist derzeit nicht die Implementierung, sondern:

> **Ist die Richtung des beobachteten Flusses informationsreich genug, um ODE-Strukturen zuverlässig voneinander zu unterscheiden?**

Genau das sollte als erstes getestet werden.
