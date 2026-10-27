# Idee #4 – Adaptive Persistence-Guided ODE Discovery

**Stand:** 2026-10-07  
**Status:** Frühe Forschungsidee / „Wurm“-Ansatz

## 1. Kurzfassung

Die Grundidee ist, symbolische ODE-Strukturen **nicht nur global auf einer vollständigen Trajektorie** zu fitten, sondern entlang der Trajektorie mit einem adaptiven Fenster zu untersuchen.

Der „Wurm“ bewegt sich durch die Trajektorie. Er besitzt eine Fensterlänge \(L\), innerhalb derer lokal eine symbolische ODE gesucht wird.

Die zentrale Hypothese lautet:

> **Falsche ODE-Strukturen können lokal gut passen. Die wahre Struktur sollte jedoch über unterschiedliche Zustandsbereiche und Fensterskalen hinweg persistent bleiben.**

Damit wird nicht nur der Fit eines Modells bewertet, sondern seine **strukturelle Persistenz**.

---

## 2. Kernidee

Für ein Fenster

\[
[t_i,t_i+L]
\]

wird eine lokale symbolische ODE bestimmt.

Danach wird das Fenster

- weitergeschoben,
- vergrößert,
- verkleinert,
- oder gegebenenfalls geteilt.

Die entscheidende Frage ist nicht nur:

> Welche ODE passt in diesem Fenster am besten?

Sondern:

> **Wie lange und über wie viele unterschiedliche Zustandsbereiche bleibt dieselbe symbolische Struktur gültig?**

Ein lokales Surrogat kann kurzfristig gewinnen. Eine echte globale ODE-Struktur sollte dagegen zunehmend unterschiedliche Teile der Trajektorie überstehen.

---

## 3. Warum adaptive Fenster wichtig sind

Eine feste Fenstergröße ist wahrscheinlich suboptimal.

### Zu kleines Fenster

- wenig Information;
- viele lokal äquivalente Surrogate;
- Noise dominiert;
- Struktur kann stark zwischen benachbarten Fenstern springen.

### Zu großes Fenster

- robuste Fits;
- aber lokale informative Strukturen können verwischt werden;
- dominante Trajektorienbereiche können seltenere Dynamikbereiche überdecken.

### Adaptive Fenstergröße

Die Fensterlänge selbst wird deshalb Teil der Struktursuche.

Der Algorithmus fragt:

> **Wie groß muss das Fenster werden, bis die gefundene Struktur ausreichend stabil und identifizierbar ist?**

---

## 4. Möglicher Algorithmus

### Schritt 1 – Start

An einer Position \(t_i\) wird mit einem kleinen Fenster \(L_0\) begonnen.

### Schritt 2 – Lokale Struktursuche

Innerhalb des aktuellen Fensters wird eine symbolische ODE-Struktur gesucht.

Die konkrete lokale Suchmethode ist zunächst austauschbar.

### Schritt 3 – Stabilität prüfen

Es wird untersucht:

- bleibt dieselbe Struktur bei leicht verändertem Fenster erhalten?
- bleiben die Parameter stabil?
- bleibt die Struktur bei Vergrößerung des Fensters gültig?
- ist der Unterschied zu konkurrierenden Strukturen statistisch belastbar?

### Schritt 4 – Fenster anpassen

Abhängig von der Stabilität:

- **grow:** Fenster vergrößern;
- **shrink:** Fenster verkleinern;
- **move:** Fenster weiterschieben;
- **split:** bei systematisch unterschiedlicher Struktur aufteilen;
- **accept:** Struktur lokal als stabil markieren.

### Schritt 5 – Persistenz sammeln

Für jede symbolische Struktur wird erfasst:

- über welche Fenstergrößen sie überlebt;
- wie viel Zustandsraum sie abdeckt;
- wie oft sie wiederkehrt;
- wie stabil ihre Parameter sind.

### Schritt 6 – Globale Struktur bestimmen

Strukturen mit hoher Persistenz werden bevorzugt.

Ein möglicher abstrakter Score:

\[
P(M)=
\text{state-space coverage}
\times
\text{structural recurrence}
\times
\text{parameter stability}
\times
\text{noise confidence}.
\]

Die final ausgewählte Struktur wird anschließend global auf allen Trainingsdaten refittet.

---

## 5. Der eigentliche wissenschaftliche Twist

Sliding-Window Symbolic Regression existiert bereits.

Auch zeitvariable SINDy-Varianten und Ensemble-SINDy untersuchen lokale bzw. resampelte Modelle.

Der mögliche Neuheitskern liegt daher **nicht im Sliding Window selbst**, sondern in:

> **Structural Persistence als eigentliches Discovery-Kriterium und adaptive Fenstergröße als Teil der symbolischen Struktursuche.**

Die Methode geht explizit davon aus, dass das zugrunde liegende autonome ODE-System **nicht zeitlich wechselt**.

Lokale Strukturwechsel werden deshalb zunächst als mögliche Surrogat- oder Noise-Effekte interpretiert.

---

## 6. Abgrenzung zu verwandten Arbeiten

### Sliding-Window Symbolic Regression

Kronberger et al. nutzten Sliding-Window Symbolic Regression zur Detektion echter Änderungen der Systemdynamik.

Hier ist die Grundannahme umgekehrt:

> Die Dynamik bleibt konstant. Deshalb dient strukturelle Stabilität über Fenster hinweg als Evidenz für die richtige ODE.

### Time-Varying SINDy

Time-Varying SINDy sucht explizit nach zeitlich wechselnden Koeffizienten oder Strukturen.

Hier wird dagegen nach einer global persistenten Struktur gesucht.

### Ensemble-SINDy

Ensemble-SINDy nutzt Wiederauftreten einzelner Terme über Resampling als Inclusion Probability.

Adaptive Persistence-Guided Discovery würde stattdessen:

- zusammenhängende Zustandsbereiche untersuchen;
- Fenster aktiv verändern;
- komplette symbolische Strukturen statt einzelner Features verfolgen;
- Persistenz selbst als Such- und Selektionssignal verwenden.

---

## 7. Noise gehört in den Basisalgorithmus

Noise sollte nicht erst eine spätere Erweiterung sein.

Die zentrale Herausforderung ist gerade:

> **Ist ein Strukturwechsel im lokalen Fenster echt oder nur durch Messrauschen verursacht?**

Deshalb muss Paper 1 bereits noise-aware sein.

Mögliche Mechanismen:

- Struktur muss über mehrere überlappende Fenster bestätigt werden;
- Parameteränderungen werden relativ zu ihrer Unsicherheit bewertet;
- Fenster wachsen bei instabilen Ergebnissen weiter;
- Änderungen gelten erst dann als relevant, wenn sie statistisch belastbar sind;
- mehrere Fensterskalen müssen dieselbe Struktur unterstützen.

---

## 8. Mögliche PhD-Linie

### Paper 1 – Adaptive Persistence-Guided Symbolic ODE Discovery

Kernalgorithmus:

- adaptive Sliding-/Growing-Windows;
- lokale symbolische Struktursuche;
- structural persistence;
- noise-aware Stabilitätskriterium;
- globale Rekonstruktion aus persistenten Strukturen.

Benchmark gegen:

- SINDy;
- W-SINDy;
- ODEFormer;
- weitere etablierte ODE-Discovery-Verfahren.

Metriken:

- Strukturtreue;
- Rekonstruktions-\(R^2\);
- Generalisierung;
- Robustheit gegen Noise;
- Laufzeit.

### Paper 2 – Multi-Trajectory Structural Persistence

Die gleiche Idee wird über verschiedene Initialbedingungen erweitert.

Eine echte ODE-Struktur sollte nicht nur entlang einer Trajektorie persistent sein, sondern über mehrere unterschiedliche Trajektorien hinweg.

Mögliche Erweiterungen:

- Persistenz über verschiedene ICs;
- state-space coverage;
- gemeinsame Struktur bei variierenden Parametern;
- Unsicherheitsmodellierung.

### Paper 3 – noch offen

Mögliche Richtungen:

- aktive Auswahl informativer Trajektorienbereiche;
- höherdimensionale Systeme;
- adaptive lokale Suchräume;
- automatische Grammar-Erweiterung;
- explizite Identifizierbarkeit / `AMBIGUOUS`.

Die dritte Erweiterung sollte erst nach Paper 1 und 2 festgelegt werden.

---

## 9. Warum die Idee interessant sein könnte

Potenzielle Vorteile:

- nutzt direkt die lokale versus globale Natur von ODE-Strukturen;
- falsche lokale Surrogate werden systematisch bestraft;
- Noise kann über Persistenz abgefedert werden;
- keine große Vortrainingsphase notwendig;
- vollständig interpretierbarer Entscheidungsprozess;
- flexibel bezüglich der lokalen Symbolic-Regression-Methode;
- natürliche Erweiterung auf mehrere Trajektorien;
- potentiell geringerer Suchraum als globale freie Symbolic Regression.

---

## 10. Zentrales Risiko

Der größte offene Punkt ist:

> **Ist strukturelle Persistenz wirklich ausreichend diskriminierend?**

Es kann passieren, dass mehrere falsche Surrogate ebenfalls über große Bereiche persistent bleiben.

Außerdem hängt die Methode davon ab, dass die lokale symbolische Suche zuverlässig genug ist.

Die Idee darf daher nicht nur zu

> „viele lokale Modelle fitten und das häufigste nehmen“

werden.

Der adaptive Scale-Mechanismus und die Persistenzlogik müssen selbst einen klaren methodischen Beitrag darstellen.

---

## 11. Billigster Kill-Test

Bevor ein vollständiger Algorithmus gebaut wird:

1. Eine kleine Menge ODEBench-Systeme auswählen.
2. Mehrere lokale Fenstergrößen erzeugen.
3. In jedem Fenster eine einfache lokale symbolische Suche durchführen.
4. Strukturen über Fenster und Skalen verfolgen.
5. Prüfen:

> **Hat die wahre Struktur systematisch eine höhere Persistenz als lokal gute falsche Surrogate?**

Zunächst rauschfrei.

Danach mit wenigen realistischen Noise-Leveln.

Wenn die wahre Struktur keine klarere Persistenz zeigt als falsche Modelle, wird die Idee verworfen.

Wenn doch, ist der nächste Schritt:

> **eine adaptive Regel entwickeln, mit der der Wurm selbst entscheidet, wann er wachsen, schrumpfen, weiterkriechen oder stoppen soll.**

---

## 12. Pitch

> **Local fits are easy. True dynamics persist.**

Adaptive Persistence-Guided ODE Discovery sucht deshalb nicht einfach die Gleichung mit dem besten globalen Fit.

Stattdessen beobachtet der Algorithmus, welche symbolische Struktur über zunehmend unterschiedliche Trajektorienabschnitte und Fensterskalen hinweg bestehen bleibt.

Die Fenstergröße wird dabei selbst Teil des Discovery-Prozesses.

Oder bildlich:

> **Ein Wurm kriecht durch die Trajektorie, wird größer oder kleiner und fragt immer wieder: Welche ODE-Struktur überlebt?**

---

## 13. Einschätzung 2026-10-27 (nach Phase C)

**Bleibt im Ideenpool, Rang 2 von 3.** Trifft das in Phase C gemessene Kernproblem am direktesten.

- EvoGrow fittet Trajektorien deutlich besser, als es Mechanismen identifiziert (C-1, dim 2: 91.7 % Rekonstruktion gegen 25.6 % Generalisierung, R² > 0.9); ODEFormer zeigt dieselbe Lücke. Persistenz als Auswahlsignal setzt genau an diesem Trajektorien-Overfitting an.
- Neuheitsrisiko E-SINDy: Abgrenzung nur über zusammenhängende Zustandsbereiche statt Zufallsteilstichproben und über ganze Strukturen statt Einzelterme (Abschnitt 6). Das muss empirisch gegen E-SINDy gezeigt werden, das seit WP-N47 ohnehin als Baseline vorliegt.
- Zum Risiko aus Abschnitt 10 kommt eines hinzu: Eine einzelne Trajektorie überdeckt nur einen kleinen Zustandsbereich. Ein guter Surrogat kann dort in jedem Fenster genauso persistent sein wie die Wahrheit. Fenster über eine Trajektorie ersetzen keine zweite Anfangsbedingung.

**Wann wieder aufnehmen:** wenn die Fehleranatomie (`docs/diskussion_warum_scheitert_die_suche.md`) überwiegend Klasse C/D zeigt (falsche Strukturen, die gleich gut oder besser passen).
