# Idee #1 – Annihilator-Guided ODE Discovery

Leitdokument der Methodenspur auf dem Branch `annihilator-discovery` (Worktree `..\EvoODE-next`).
Festgehalten am 2026-10-04 aus dem Text des Nutzers. Die in der Abnahmediskussion vom selben Tag vereinbarten
Korrekturen sind eingearbeitet: Referenzoperatoren, Mischformen, Skalierung, statistischer Test, `AMBIGUOUS`
und Branch-Name. Löst `docs/idea_structural_diagnostics.md` ab. Geparkte Ideen (Multiple Shooting,
Invarianztest) stehen weiterhin in `docs/evogrow_next.md`. Die eingefrorene Spezifikation des ersten Kill-Tests
steht in `docs/GATE_2A.md`.

**Namensregel:** Das laufende EvoGrow-Paper bleibt Paper 1 des bisherigen PhD-Pfads. Diese Linie heißt intern
„Idee #1“ und **nicht** ebenfalls „Paper 1“.

## 1. Motivation

EvoGrow wird voraussichtlich nicht als Kernmethode weiterverfolgt. Die zentralen Probleme aus Phase C:

- sehr guter Fit einzelner Trainingstrajektorien, aber schlechte Generalisierung auf neue Anfangsbedingungen;
- geringe rohe Strukturtreue;
- chaotische Systeme scheitern bereits beim Parameterfit der **wahren** Struktur;
- globale ODE-Integration und nichtlineare Optimierung machen die Methode extrem langsam;
- die ursprüngliche Effizienzthese trägt nicht;
- die feste Polynomstruktur ist für relevante Systeme wie Gompertz zu eingeschränkt.

Leitidee:

> Nicht zuerst symbolische Ausdrücke generieren und testen, sondern aus den Daten zunächst die mathematische
> Struktur des unbekannten Vektorfelds diagnostizieren und daraus erst den zulässigen symbolischen
> Hypothesenraum ableiten.

Langfristiges Ziel bleibt $\mathbf x(t) \rightarrow \dot{\mathbf x} = \mathbf f(\mathbf x)$, rein datenbasiert,
mit expliziter symbolischer und interpretierbarer ODE.

## 2. Kernidee

Viele relevante Funktionsklassen werden durch lineare Differentialoperatoren mit polynomialen Koeffizienten
annihiliert. Gesucht wird

$$
L = \sum_{k=0}^{r} p_k(x)\,D^k, \qquad D = \frac{d}{dx}, \qquad p_k(x) = \sum_{j=0}^{d} c_{kj}\,x^j,
$$

mit $L[f] = 0$. Beispiele: $e^{ax}$ wird von $D - a$ annihiliert, $x^p$ von $xD - p$, $\sin(ax+b)$ von
$D^2 + a^2$, $e^{-x^2}$ von $D + 2x$. Auch $\log x$, $x\log x$ und $x/(K+x)$ besitzen solche Relationen.

Die Frage lautet also nicht mehr „Welche Expression passt?“, sondern:

> Welcher möglichst einfache Differentialoperator ist mit den Daten kompatibel?

Der gefundene Operator definiert einen Funktionsraum, aus dem die symbolische Gleichung rekonstruiert wird.

## 3. Langfristige Pipeline

trajectory data → vector-field evidence → weak operator matrix → minimal annihilator →
operator classification / factorization → solution space / admissible functional family → symbolic $f$

Die symbolische Struktur entsteht **aus dem gefundenen Operator**, nicht aus einer vorab festgelegten
universellen Library.

## 4. Warum das interessant sein könnte

- keine breite Expression-Tree-Suche;
- keine globale ODE-Integration im inneren Suchloop;
- keine zwingend feste Polynomialbibliothek;
- Strukturdiagnose vor Parameterschätzung;
- im Kern potenziell reine lineare Algebra;
- natürliche Möglichkeit, Unsicherheit und Nicht-Identifizierbarkeit explizit auszugeben.

`AMBIGUOUS` ist ein erlaubtes Ergebnis. Lassen die Daten mehrere gleich plausible Operatoren zu, wählt die
Methode **nicht zwanghaft** eine Gleichung. Das adressiert direkt ein EvoGrow-Problem: Ein Modell kann eine
Trajektorie hervorragend nachzeichnen, ohne dass seine Struktur eindeutig durch die Daten gestützt wird.

**Ein Strukturvorteil, der sich in der Diskussion am 04.10. gezeigt hat:** Die schwache Operatormatrix ist
linear in den beobachteten $f_i$. Unter einem festen additiven Rauschmodell ist die Kovarianz des Residuums
**für eine feste Operatorhypothese** deshalb analytisch berechenbar. Die Annahme eines Operators wird so zu
einem vorab festgelegten statistischen Test statt zu einem frei gewählten Schwellwert. Werden die
Operator-Koeffizienten aus denselben Daten geschätzt, gilt diese Nullverteilung für das anschließend minimierte
Residuum nicht mehr. `docs/GATE_2A.md` fängt das ab: Koeffizienten aus den Fit-Blöcken, Test auf disjunkten
Validation-Blöcken mit unabhängigem Noise, und die Schätzunsicherheit von $\hat c$ wird in die
Residualkovarianz propagiert (§5–6 dort).

## 5. Novelty-Abgrenzung

Bekannt sind: D-finite/holonome Funktionen, Differentialalgebra, Annihilator-Operatoren, Guessing von
Differentialoperatoren aus Reihen bzw. exakten Funktionsdaten, AI-Feynman-artige Property Detection vor der
Symbolic Regression, Weak-SINDy und andere schwache Formulierungen, Differentialalgebra zur
Identifizierbarkeit bzw. Modelldiskriminierung. Die mögliche Innovation liegt **nicht** in einem dieser
Bausteine. Der mögliche neue Kern:

> **Recover the symbolic vector field of an unknown dynamical system by discovering its minimal state-space
> annihilating operator directly from data and using the operator's solution space as the data-induced
> symbolic hypothesis space.**

Gate 2A prüft zunächst ausschließlich, ob dieser Kern numerisch überhaupt funktioniert.

## 6. „Minimal“ ist relativ zu einer festgelegten Ordnung

Aus $L[f] = 0$ folgt $QL[f] = 0$. Es gibt also trivial unendlich viele nicht-minimale Annihilatoren.
Darüber hinaus existieren oft **mehrere nicht-äquivalente** Annihilatoren in verschiedenen Klassen $(r,d)$.
Die exakte Vorab-Rechnung vom 04.10. zeigt das für $x^2$ ($xD - 2$ und $D^3$), $x\log x$, $x/(K+x)$ und beide
Mischformen. „Minimal“ bedeutet deshalb **minimal bezüglich einer explizit definierten, vorab eingefrorenen
Komplexitätsordnung**, nicht zwingend minimale Differentialordnung:

$$
C(r,d) = (r+1)(d+1), \qquad \text{Tie-Break: erst kleineres } r, \text{ dann kleineres } d.
$$

Der Referenzoperator jeder Testfunktion wird mit **genau dieser Ordnung** exakt symbolisch bestimmt und nie
von Hand vorgegeben. Die Referenz verwendet dieselbe Ordnung, aber **nicht** die numerische Weak-Matrix des
getesteten Algorithmus. Sonst würden wir gegen uns selbst testen. Ein gefundener Operator ist zunächst ein
Lösungsraum, keine fertige symbolische Basis. Den Schritt $L \rightarrow$ Klassifikation/Faktorisierung
$\rightarrow$ Basis $\rightarrow f$ braucht Gate 2A noch nicht.

## 7. Ergebniszustände

`AMBIGUOUS` heißt nicht einfach „kleiner Singulärwert“. Es heißt: Nach Komplexität, Validation und
statistischem Test bleiben mindestens zwei nicht-äquivalente Operatorhypothesen bestehen, ohne dass die Daten
eine davon bevorzugen können. Operatoren, die sich nur um einen Skalar unterscheiden ($L \sim aL$), sind
dieselbe Hypothese. Mehrere **wahre** Annihilatoren mit gleichem $C$, aber unterschiedlichem $(r,d)$
(z. B. $xD - 2$ und $D^3$ für $x^2$, beide $C = 4$) sind keine Ambiguität der Daten. Sie werden durch die
vorab festgelegte Tie-Regel geordnet, hier zugunsten von $xD - 2$. Bleiben dagegen zwei nicht-proportionale
Operatoren mit **identischem** $(r,d)$ nach allen Tests bestehen, kann die Tie-Regel nicht helfen. Genau dann
ist `AMBIGUOUS` relevant (in `docs/GATE_2A.md` Kriterium A1). `AMBIGUOUS` ist kein Fehlerzustand.
Die vollständige, operationale Zustandsdefinition steht in `docs/GATE_2A.md`.

## 8. Gate-Folge

- **Gate 2A** (Kill-Test, Python, Laptop, Sekunden bis Minuten): Rekonstruiert man aus verrauschten Samples
  $(x_i, f_i)$ einer unbekannten skalaren Funktion ihren minimalen Operator? Keine ODE, kein $\dot x$, keine
  Integration, keine Symbolic Regression. Spezifikation: `docs/GATE_2A.md`.
- **Gate 2B** (erst nach bestandenem 2A): die vollständige 1D-Kette
  $x(t) \rightarrow f(x) = \dot x \rightarrow L \rightarrow$ Funktionsraum $\rightarrow \hat f(x) \rightarrow$
  Generalisierung auf neue Anfangsbedingungen. Zentraler Testfall Gompertz (System 7). Der technische
  Engpass ist dann die robuste Rekonstruktion der State-Space-Information aus verrauschten Zeitreihen.
- **Mehrdimensionale Systeme** gehören nicht zu Gate 2A. Eine einzelne Trajektorie auf einem Attraktor liefert
  keine Information über das Vektorfeld transversal zum Attraktor, auch bei Chaos nicht. Für partielle
  Ableitungen und Interaktionsstruktur braucht es mehrere gezielt gewählte Anfangsbedingungen bzw. ausreichende
  Zustandsraumabdeckung. Das wird später explizit als Identifizierbarkeitsproblem behandelt.

Systeme für spätere Gates: Entwicklung 7 / 40 / 56 / 63, verschlossenes Prüfset 4 / 49 / 59 / 62.

## 9. Mögliche langfristige Paper-Struktur (nur falls die Gates überlebt werden)

1. Erstes Methodenpaper der Linie: D-finite / annihilator-guided discovery für einfache Funktionsfamilien:
   minimaler Operator, dateninduzierter Funktionsraum, keine breite Expression Search.
2. Erweiterung: komplexere Kompositionen, größere differential-algebraische Klassen (D-algebraisch,
   kompositionell).
3. Robustheit: Noise, sparse sampling, Weak Form, mehrere Anfangsbedingungen, Identifizierbarkeit,
   `AMBIGUOUS`, Unsicherheitsquantifizierung.

## 10. Repository-Organisation

- Vorerst **kein neues Repository.** Die Arbeit bleibt isoliert im `EvoODE`-Repo, Branch
  `annihilator-discovery`, Worktree `..\EvoODE-next` mit eigenem VS-Code-Fenster. Der Branch heißt bewusst
  nicht `evogrow-next`, weil es methodisch nicht um eine Weiterentwicklung von EvoGrow geht.
- Bestehender EvoGrow-Code wird nicht verändert, Paper-1-Ergebnisse auf `main` bleiben unangetastet, keine
  Refactorings alten Codes ohne zwingenden Grund.
- Experimente liegen unter `experiments/annihilator_gate2a/`.
- Ein neues Repository mit eigenem Namen, eigener Architektur und eigener Paper-Linie entsteht **erst, wenn
  Gate 2A und Gate 2B überzeugend bestanden sind.**

## 11. Regeln dieser Spur

- Erst billig versuchen, die Idee zu zerstören. Entwicklungszeit oder Compute bekommt sie erst, wenn sie
  mehrere harte Gates überlebt.
- Jede Entscheidungsregel wird **vor** dem ersten Lauf eingefroren und nicht nach Sichtung der Ergebnisse
  angepasst.
- Von einfach zu komplex. Kein GP. Nichts mit Gabriel Kronberger (Autorenschaft prüfen).
- Kein HPC, solange ein Gate auf dem Laptop in Minuten läuft.
