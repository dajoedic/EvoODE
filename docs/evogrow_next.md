# EvoGrow-next: Denkstand vom 03.10.2026

Notiz zum Mitnehmen. Es wurde noch nichts gebaut und nichts gestartet.

## 1. Woran die bisherige Methode krankt (gemessen, Phase C)

- **Nachzeichnen statt Verstehen.** EvoGrow fittet die *eine* Trainingstrajektorie sehr gut (dim 2:
  92 % R² > 0,9), generalisiert aber schlecht auf eine neue Anfangsbedingung (26 %). Die Struktur trifft
  es roh selten (dim 2: 3 von 60). Das Auswahlsignal belohnt nur den Trajektorien-Fit, und eine einzige
  Trajektorie legt die Gleichung nicht fest. ODEFormer und SINDy haben dieselbe Lücke.
- **Der Fit verliert, bevor die Suche gewinnen kann.** Selbst mit der *wahren* Struktur und ohne
  Parametergrenze lassen sich Lorenz, Rössler und Chen-Lee nicht fitten (0/6). Der Fit über die ganze
  Trajektorie hängt in lokalen Optima fest, bei Chaos zwangsläufig.
- **Kein Abbruchkriterium.** Unter Rauschen läuft jede Zelle 20–26 Level, weil die Loss-Toleranz unter
  dem Rauschboden liegt. Teuer, ohne Gewinn.
- **Die Suchraumbegrenzung (Kappe) schaltet sich unter Rauschen ab** oder schneidet in 17 % der
  Gleichungen wahre Terme ab.
- **Effizienz, die ursprüngliche These, trägt nicht.** Gleich gut wie SINDy bei etwa 100-fachem Aufwand.
- **Die Polynom-Basis kann vieles nicht darstellen:** ln, Brüche, sin(a·x). Genau das brauchen schwere
  Systeme wie Gompertz.

## 2. Die neue Idee (Nutzer, 03.10.)

„Random Forest für ODEs“: Die Trajektorie wird in viele Teilstücke zerlegt, mit zufälliger Länge in
einem Bereich, auch überlappend. Je Teilstück wird mit etwas sehr Einfachem und Schnellem gefittet
(SINDy, Polynomregression …). Danach wird aggregiert: über alle Lösungen mitteln oder die Teilmenge
mit der geringsten Varianz nehmen.

Daneben steht als erster Test (Entscheidung des Nutzers) **Multiple Shooting**: Die Trajektorie wird in
Segmente geteilt, die Segment-Anfangszustände werden mitgefittet, ein Stetigkeitsterm verbindet sie.
Das ist das klassische Mittel gegen Chaos und lokale Optima (Bock 1981; Baake et al. 1992, „Fitting ODEs
to chaotic data“).

## 3. Warum sie doch nicht so neu ist

- **Ensemble-SINDy (E-SINDy)**, Fasel, Kutz, Brunton & Brunton, Proc. R. Soc. A 2022: Bagging über
  Teilstichproben, je ein SINDy-Modell, Aggregation über Einschlusswahrscheinlichkeiten der Terme und
  Median der Koeffizienten. Das ist ziemlich genau „Random Forest für SINDy“. https://arxiv.org/abs/2111.10992
- **E-WSINDy** (Ensemble + Weak SINDy, also integrierte statt abgeleitete Form) steht schon im selben
  Paper, eine Anwendung folgte 2024: https://arxiv.org/html/2409.20510v1
- **Stability Selection** (PDE-STRIDE, Maddu et al. 2022) fittet auf vielen Teilstichproben und behält
  nur Terme, die oft gewählt werden. https://arxiv.org/pdf/1907.07810

**Was davon wirklich offen bleibt** (vor dem Bauen gezielt prüfen):
1. **Invarianz als Auswahlkriterium.** Die wahre Gleichung muss in *jedem* Zeitfenster **dieselben
   Koeffizienten** haben, denn der Mechanismus ändert sich nicht. Eine Gleichung, die nur nachzeichnet,
   braucht je Fenster andere. Die Koeffizientenstreuung über die Fenster (oder: Modell aus Fenster i sagt
   Fenster j vorher) wird damit zum Auswahlsignal. E-SINDy zählt nur, *wie oft* ein Term gewählt wird.
   Das Prinzip entspricht Invariant Causal Prediction (Peters et al. 2016), mit Zeitfenstern als
   Umgebungen. Es zielt direkt auf die Hauptschwäche aus Punkt 1.
2. **Kurze Fenster integrieren statt ableiten**, auch für Terme, die nichtlinear in den Parametern
   sind (ln, Brüche). SINDy ist linear in einer festen Bibliothek und kommt dort grundsätzlich nicht hin.

E-SINDy und E-WSINDy gehören als stärkste Gegner auf die Vergleichsliste.

## 4. Was der Nutzer will

Etwas **genial Einfaches, schnell und genau**. Symbolische Regression im weitesten Sinn, alles erlaubt.
**Nicht** in Richtung genetische Programmierung, **nichts** mit Gabriel Kronberger. Von einfach zu
komplex. Zuerst auf wenigen, **bekannt schweren** Systemen gut werden:

| Rolle | dim 1 | dim 2 | dim 3 | dim 4 |
|---|---|---|---|---|
| Entwicklung | 7 Gompertz | 40 Duffing | 56 Lorenz (chaotisch) | 63 SEIR |
| verschlossenes Prüfset | 4 RC nichtlinear | 49 Brusselator | 59 Rössler (chaotisch) | 62 Binok. Rivalität |

Erfolg: exakte Struktur roh **und** R² > 0,9 in Rekonstruktion und Generalisierung, sauber und bei
(σ 0,05; ρ 0,5).

**Denkanstoß:** „Genial einfach“ hieß in diesem Feld fast immer, eine Eigenschaft der Wahrheit zu
nutzen, die die anderen ignorieren. SINDy nutzt die dünne Besetzung, die schwache Form die
Integralgültigkeit, die Fenster-Idee die zeitliche Invarianz. Weitere Kandidaten:
- **Zeitumkehr:** Rückwärts integriert muss die wahre Gleichung zum Anfang zurückführen.
- **Konsistenz zwischen den Komponenten** gekoppelter Systeme.
- **Kürzeste Beschreibung** (MDL): Was erklärt die Daten bis aufs Rauschen am knappsten?

## 5. Billige nächste Tests, wenn es losgehen soll (je Minuten bis wenige Stunden, Laptop)

1. **Multiple-Shooting-Orakel:** Die wahre Struktur von Lorenz 56 (und 55, 59, 61, 63) wird mit
   Segmenten statt mit einem Schuss gefittet, K ∈ {1, 8, 16, 32}. Bestanden, wenn Systeme mit heute 0/6
   R² > 0,9 bei einer einzigen Ganztrajektorien-Integration erreichen.
2. **Invarianztest:** Auf den vier Entwicklungssystemen werden die wahre Struktur und die typischen
   falschen Strukturen (aus C-1) auf vielen zufälligen, überlappenden Fenstern gefittet. Bestanden, wenn
   die wahre Struktur überall die kleinste Koeffizientenstreuung hat, sauber und unter Rauschen.

Organisation: ein Git-Worktree `..\EvoODE-next` (Branch `evogrow-next`, eigenes VS-Code-Fenster).
`main` bleibt im alten Ordner für die Paper-1-Ergebnisse.

## 6. Weitere Idee (Nutzer, 04.10.): strukturelle Diagnostik über Differentialrelationen

Festgehalten in **`docs/idea_structural_diagnostics.md`**: Funktionsklassen haben charakteristische
Differentialrelationen (z. B. exp: g·g'' − g'² = 0). Diese werden aus den Daten getestet, bevor gesucht
wird. Ergebnis kann auch `AMBIGUOUS` sein (Identifizierbarkeit als Teil der Discovery). Noch nicht bewertet.
