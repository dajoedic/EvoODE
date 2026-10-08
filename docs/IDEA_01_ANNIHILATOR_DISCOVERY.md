# Idee #1 – Annihilator-Guided ODE Discovery

> **Abgeschlossen am 2026-10-08: gescheitert** (Entscheidung des Nutzers). Begründung in §12, ausführlicher
> Rückblick in `docs/IDEA_01_RETROSPECTIVE.md`. Der Text ab hier ist der Planungsstand und bleibt als Akte
> unverändert.

Leitdokument der Methodenspur auf dem Branch `annihilator-discovery` (Worktree `..\EvoODE-next`).
Festgehalten am 2026-10-04 aus dem Text des Nutzers. Die in der Abnahmediskussion vom selben Tag vereinbarten
Korrekturen sind eingearbeitet: Referenzoperatoren, Mischformen, Skalierung, statistischer Test, `AMBIGUOUS`
und Branch-Name. Löst `docs/idea_structural_diagnostics.md` ab. Geparkte Ideen (Multiple Shooting,
Invarianztest) stehen weiterhin in `docs/evogrow_next.md`. Der erste Kill-Test: `docs/GATE_2A.md` (v1, an der
Abnahme gescheitert, nie gelaufen) und **`docs/GATE_2A_v2.md` (gültig)**, mit Begründung in
`docs/GATE_2A_v2_RATIONALE.md`.

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
Residuum nicht mehr. Gate 2A fängt das ab: Die Koeffizienten werden auf den Fit-Samples geschätzt und auf
disjunkten Validation-Samples mit unabhängigem Noise getestet. Die Schätzunsicherheit von $\hat c$ wird in die
Residualkovarianz propagiert (`docs/GATE_2A_v2.md` §4–6). In v2 schätzt FNS/AML die Koeffizienten nach genau
der Statistik, mit der getestet wird.

**Was die v1-Abnahme am 04.10. gezeigt hat (Details in `docs/GATE_2A_v2_RATIONALE.md`):**
- *Gestützt:* Der statistische Test ist kalibriert, wo die Numerik sauber ist. Auf F2 verwirft er den wahren
  Operator mit 0,8 % bei Soll 1 %.
- *Abgeschwächt:* Die schwache Form löst das Rauschproblem nicht grundsätzlich. Sie verschiebt die Ableitungen
  auf die Testfunktionen, die Verstärkung $\sim w^{-k}$ bleibt (wie bei Weak-SINDy). Gegenüber differenzierenden
  Methoden ist nur ein quantitativer Vorteil möglich: breite Träger und eine optimale Gewichtung. Das entscheidende
  Risiko der Idee sind Operatoren ab Ordnung 2 unter 1 % Rauschen. Dafür hat v2 eigene Kill-Kriterien (K5, K6).

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
ist `AMBIGUOUS` relevant (in `docs/GATE_2A.md` Kriterium A1). Die zweite Quelle ist eine instabile Auswahl:
Wechselt die gewählte Klasse unter einem parametrischen Bootstrap, stützen die Daten die Wahl nicht
(Kriterium A2). `AMBIGUOUS` ist kein Fehlerzustand.
Seit v2 gibt es eine dritte Quelle: Die projektive Winkelunsicherheit von $\hat c$ ist zu groß (A3).
Die vollständige, operationale Zustandsdefinition steht in `docs/GATE_2A_v2.md`.

## 8. Gate-Folge

- **Gate 2A** (Kill-Test, Python, Laptop): Rekonstruiert man aus verrauschten Samples $(x_i, f_i)$ einer
  unbekannten skalaren Funktion ihren minimalen Operator? Keine ODE, kein $\dot x$, keine Integration, keine
  Symbolic Regression. Spezifikation: `docs/GATE_2A_v2.md`. Die Annahme „Sekunden bis Minuten“ galt für v1. Mit
  FNS und Bootstrap liegt der Hauptlauf in v2 eher bei Stunden, die Hochrechnung steht noch aus.
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
- Experimente liegen unter `experiments/annihilator_gate2a/` (v1) und `experiments/annihilator_gate2a_v2/` (v2).
- Ein neues Repository mit eigenem Namen, eigener Architektur und eigener Paper-Linie entsteht **erst, wenn
  Gate 2A und Gate 2B überzeugend bestanden sind.**

## 11. Regeln dieser Spur

- Erst billig versuchen, die Idee zu zerstören. Entwicklungszeit oder Compute bekommt sie erst, wenn sie
  mehrere harte Gates überlebt.
- Jede Entscheidungsregel wird **vor** dem ersten Lauf eingefroren und nicht nach Sichtung der Ergebnisse
  angepasst.
- Von einfach zu komplex. Kein GP. Nichts mit Gabriel Kronberger (Autorenschaft prüfen).
- Kein HPC, solange ein Gate auf dem Laptop in Minuten läuft.

## 12. Abschluss (2026-10-08)

**Entscheidung des Nutzers am 08.10.: Idee #1 ist gescheitert und wird beendet.** Grundlage ist der
End-to-End-Vergleich (`docs/ODEBENCH_END2END_RESULT.md`) zusammen mit allen vorherigen Prüfungen.

**Warum:** Das Kernversprechen ist in allen sieben Prüfungen verfehlt.

| Versprechen (§2, §4) | Befund |
|---|---|
| Struktur vor Parametern | Bei 1 % Rauschen nur bei der Logistik getroffen; sonst wählt die Komplexitätsordnung Surrogate mit konstanten Koeffizienten |
| Funktionsfamilien jenseits fester Libraries, Gompertz als zentraler Fall (§8) | Gompertz schon rauschfrei verfehlt, end-to-end das schwächste System |
| begründetes `AMBIGUOUS` | 118/118 eindeutige N1-Antworten falsch; die Abstention erkennt stabile Fehlwahlen nicht |
| lineare Algebra statt Suche | AML ist nichtlinear und teuer; end-to-end ist zusätzlich eine Ableitungsschätzung nötig, die schwache Form in $x$ vermeidet $\dot x$ nicht |

**Positiv, aber nicht das Ziel:** Mit Glättung ist der Annihilator end-to-end in der Funktionsgüte konkurrenzfähig.
Ob das am Operator oder an der Glättung liegt, ist ungeklärt. Diese Frage hätte am Scheitern des Kernversprechens
nichts geändert und wird deshalb nicht weiter verfolgt.

**Gate-Stand:** Gate 2A wurde in keiner Version bestanden, Gate 2B nie formal eröffnet. Der End-to-End-Vergleich
war deskriptiv, ohne Entscheidungsregel. Ein eigenes Repository entsteht nicht (§10).

**Prüfset:** ODEBench 4/49/59/62 wurde nie angesehen und bleibt für künftige Ideen verschlossen.

### Belege im Repository

| Prüfung | Spezifikation und Ergebnis | Code und Records |
|---|---|---|
| Gate 2A v1 | `GATE_2A.md` | `experiments/annihilator_gate2a/` |
| Gate 2A v2 | `GATE_2A_v2.md`, `GATE_2A_v2_RATIONALE.md` | `experiments/annihilator_gate2a_v2/` |
| Gate 2A v3, Stufe K | `GATE_2A_v3.md`, `GATE_2A_v3_STAGE_K_RESULT.md` | `experiments/annihilator_gate2a_v3/` |
| Diagnose `AMBIGUOUS` | `DIAGNOSTIC_AMBIGUITY.md`, `…_RESULT.md` | `experiments/annihilator_gate2a_v3/diagnostics/ambiguity_diagnostic.py`, Orion-Runbook unter `…_v3/orion/` |
| Reality-Check A | `REALITY_CHECK_DIRECT_REGRESSION.md`, `…_RESULT.md` | `experiments/annihilator_gate2a_v3/diagnostics/direct_regression_check.py` |
| ODEBench-Smoke-Test | `ODEBENCH_SMOKE_TEST.md`, `…_v2.md`, `…_RESULT.md` | `experiments/annihilator_odebench_smoke/` |
| End-to-End v1/v2 | `ODEBENCH_END2END.md`, `…_v2.md`, `…_RESULT.md` | `experiments/annihilator_odebench_smoke/end2end.py`, `results_e2e*/records_compact.jsonl` |

- **Rohdaten:** Die End-to-End-Rohdaten (2 × 910 MB) liegen nicht in Git. Sie werden auf dem Orion-NFS
  archiviert, Prüfsummen in `experiments/annihilator_odebench_smoke/RAW_RECORDS_SHA256.txt`. Die Originaldaten der
  Diagnose liegen unter `/bigdata/data-science/joedicke/annihilator_diag_amb/`.
- **Endstand im Git:** Tag `idea01-annihilator-closed` auf dem Branch `annihilator-discovery`.
- **Was eine Wiederaufnahme bräuchte:** `docs/IDEA_01_RETROSPECTIVE.md` §8. Das wäre eine neue Idee mit eigener
  Gate-Folge, keine Fortsetzung.
