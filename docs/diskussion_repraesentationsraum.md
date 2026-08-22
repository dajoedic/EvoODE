# Diskussionsgrundlage — Wie breit darf der Suchraum von EvoODE werden?

**Stand 22.08.2026.** Abschnitte 1–8 sind die Gesprächsvorlage *vor* der Diskussion; die Zahlen sind
gemessen, die Bewertungen waren Vorschläge. **Abschnitt 9 hält das Ergebnis fest** — einschließlich
vier Korrekturen an der Vorlage. Wo sich beide widersprechen, gilt Abschnitt 9.

Zugehörige Dokumente: `docs/phd_thesis_arc.md` §5 (Einordnung in den Dreier-Bogen),
`PAPER_1.md` (Ausführungsplan Paper 1), `analysis/data/paper1_phaseB_v1/system_classification.csv`
(die Rohdaten hinter jeder Zahl unten).

---

## 1. Worum es geht

EvoODE sucht Modellstrukturen als Summe von Termen aus einer festen, gestuften Basis:

```text
du_k/dt  =  Σ  p_i · φ_i(u)
```

Die Basis enthält heute: lineare Terme, Selbstquadrate, paarweise Produkte, Kuben, sowie `sin(u)`
und `cos(u)`. Fünf Stufen, die nacheinander freigeschaltet werden — das ist der Mechanismus, den
Paper 1 untersucht.

**Das Problem:** Von den 63 ODEBench-Systemen kann diese Basis nur **20 exakt darstellen**. Bei den
übrigen 43 enthält die wahre Gleichung Terme, die es in der Basis nicht gibt — die Suche kann sie
prinzipiell nicht finden, egal wie gut sie arbeitet.

Das ist bekannt und wird sauber behandelt: Exakte Systeme werden auf Struktur-Recovery bewertet,
Surrogatsysteme auf Approximationsgüte via R², und beides wird nie vermischt. Die Frage ist nicht,
ob wir korrekt messen. Die Frage ist, ob der Raum, in dem gesucht wird, für eine Dissertation
ausreicht.

---

## 2. Was genau fehlt

Alle 82 nicht abgedeckten Terme aus 117 Gleichungszeilen, nach Familien sortiert und gierig
aufgebaut — welche Familie schließt die meisten Systeme?

| Katalog wächst um | Systeme neu | exakt gesamt |
|---|---|---|
| Ausgangslage | — | 20 / 63 |
| + Konstante | +10 | 30 |
| + rationale Terme (Sättigung, Hill) | +12 | 42 |
| + gemischte Monome Grad ≥ 3 | +9 | 51 |
| + Trigonometrie **mit skaliertem Argument** | +7 | **58** |
| + exp | +1 | 59 |
| + log | +1 | 60 |
| + reelle Potenz | +1 | 61 |
| + hohe Potenz | +1 | 62 |
| + Betrag | +1 | **63** |

**Vier Familien decken 92 Prozent des Benchmarks.** Danach bricht der Ertrag ein: Die letzten fünf
Systeme brauchen fünf verschiedene Sonderfamilien, je eine pro System.

| System | fehlende Familie | Modell |
|---|---|---|
| 7 | log | Gompertz-Tumorwachstum |
| 10 | reelle Potenz | Sprachtod-Modell |
| 16 | hohe Potenz | Landau-Gleichung |
| 21 | exp | reduziertes SIR-Modell |
| 44 | Betrag | getriebenes Pendel, quadratische Dämpfung |

Diese Kante ist selbst ein Ergebnis: Sie sagt, wo ein Katalog aus Evidenz aufhört statt aus
Geschmack.

---

## 3. Die Leiter — und wo der Architektursprung liegt

| Stufe | Was dazukommt | Abdeckung | Architektur |
|---|---|---|---|
| **A** | Konstante, gemischte Monome Grad ≥ 3 | 39 / 63 | **unverändert** |
| **B** | + rationale und skaliert-trigonometrische Terme | 58 / 63 | Terme mit inneren Parametern |
| **C** | + fünf Sonderfamilien | 63 / 63 | wie B |
| **D** | freie Ausdrucksbäume, globale Suche | 63 / 63 | **das wäre GP** |

**Stufe A ist geschenkt.** Konstante und gemischte Monome sind gewöhnliche Basisfunktionen. Das
Modell bleibt linear in seinen Koeffizienten, der OLS-Warmstart bleibt unverändert, es wächst nur
der Katalog. Neunzehn Systeme für eine reine Erweiterung.

**Stufe B ist der eigentliche Entwurfsentscheid.** Rationale Terme und skalierte Trigonometrie
tragen **innere** Parameter — das `K` in `u/(u+K)`, das `ω` in `sin(ωu)`. Damit ist das Modell nicht
mehr linear in allen Parametern.

Der übliche Einwand lautet: Dann stirbt das Pretuning. Das stimmt so nicht. Das Pretuning arbeitet
nicht auf dem Simulationsverlust, sondern auf dem algebraischen Ableitungsproblem, und dort bleiben
die **äußeren** Koeffizienten linear, auch wenn jeder Term innere Parameter hat. Man landet bei
separablen kleinsten Quadraten: Für gegebenes `θ` löst OLS die äußeren Koeffizienten geschlossen,
und nur über `θ` — ein bis zwei Dimensionen je Term — muss nichtlinear gesucht werden. Der
Warmstart wird teurer, aber er überlebt.

---

## 4. Warum das kein GP ist

Der Einwand, den man erwarten muss: *Ihr baut euch schrittweise GP nach.*

**GP ist ein Suchverfahren, keine Darstellungsform.** Ausdrucksbäume sind eine Repräsentation;
genetische Programmierung ist die globale Suche darüber — große zufällige Startstrukturen,
Crossover, Mutation. Das eine bedingt das andere nicht.

Drei Eigenschaften machen EvoODE aus, und Stufe B behält alle drei:

1. **Additive Termstruktur** — deshalb ist „ein Term dazu" überhaupt eine sinnvolle
   Wachstumsoperation, und deshalb bleibt das Ergebnis lesbar.
2. **Abzählbarer, staffelbarer Katalog** — nur so hat „Stufe" einen Referenten, und nur so kann ein
   Controller den Raum überhaupt begrenzen.
3. **Minimaler Start, kontrolliertes Wachstum, Promotionskriterium** — der eigentliche Beitrag.

Fällt eine davon weg, ist man bei GP. Es ändert sich die Ausdrucksstärke, nicht die Suchdisziplin.

Und die Aussage wird dadurch **stärker**: „Kontrolliertes inkrementelles Wachstum funktioniert auch
in einem ausdrucksstarken Raum, in dem globale Suche teuer ist" ist ein größerer Beitrag als
dieselbe Aussage in einer Polynombibliothek. In einer schmalen Bibliothek wirkt ein
Wachstumscontroller wie eine SINDy-Variante mit Scheduling-Trick.

---

## 5. Was dagegen spricht, es jetzt zu tun

**Es öffnet Phase 2b erneut.** Eine neue Basis heißt neuer `config_fingerprint`. Der Regressionsblock
vom 20.08. — 120 Records, 25,4 Prozent weniger Suchaufwand bei bitidentischem Ergebnis — wäre
entwertet. Schwerwiegender: Designregel 2 des Papers leitet den Vorausschau-Horizont daraus ab, *wo
die Basis strukturelle Lücken erzeugt*. Mit anderen Termen liegen die Lücken woanders, der Horizont
muss neu hergeleitet und alle Caps neu auditiert werden.

**Das Kostenmodell wäre Makulatur.** Es hängt an der Strukturgröße und an gemessenen Klassenmitteln.

**Und das inhaltlich größte Risiko: Identifizierbarkeit.** Die Zahlen oben messen *Darstellbarkeit*,
nicht *Auffindbarkeit*. `u/(u+K)` geht für großes `K` in einen linearen Term über. Ein reicherer
Katalog erzeugt fast äquivalente Strukturen — und Struktur-Recovery auf gekoppelten Systemen
funktioniert **heute schon nicht** (`pruned_match = false` in jeder gekoppelten Regressionszelle,
auch bei Loss 6,8e-11). Ein breiterer Raum kann das verschlimmern. Stufe B könnte Paper 2 schwerer
machen, bevor sie irgendetwas verbessert.

---

## 6. Einordnung in den Bogen

Der Dreier-Bogen lautet heute: **#1** den Raum vor der Suche begrenzen, **#2** die Suche innerhalb
eines korrekten Raums reparieren, **#3** Robustheit und externe Vergleiche.

Die Repräsentationsfrage hat darin **keinen Platz**, und das ist der Befund.

- Sie ist **nicht Paper 1** — siehe §5.
- Sie **relativiert** Paper 1 im Bogen: „Der Raum ist nicht die Ursache der gescheiterten Recovery"
  gilt nur für die 20 exakten Systeme. Bei den anderen 43 *ist* der Raum die Ursache. Der Bogen muss
  diese Einschränkung aussprechen statt die allgemeine Aussage zu suggerieren.
- Sie ist **Voraussetzung für Paper 3.** Dort kommen die externen Vergleiche, und PySR, SINDy mit
  reicher Bibliothek und ODEFormer durchsuchen alle Räume, die Sättigung und Oszillation ausdrücken
  können. Fit-Qualität auf Systemen zu vergleichen, die wir nicht darstellen können, misst unseren
  Katalog, nicht unsere Suche.

Daraus folgt eine konkrete Ergänzung, unabhängig von jeder Grammatikentscheidung: Der
Protokoll-Audit braucht eine Spalte, die er heute nicht hat — **ist der Suchraum der
Vergleichsmethode für dieses System überhaupt repräsentationsfähig?** Diese Vergleichsdimension
berichtet meines Wissens niemand.

---

## 7. Was ich zur Diskussion stellen würde

1. **Reicht 39 von 63 ohne Architekturänderung als Zwischenschritt**, oder ist die Halbheit
   schlimmer als der Status quo? Stufe A ist billig, aber sie löst die Kritik nicht — die
   interessanten Motive (Sättigung, Oszillation) liegen in Stufe B.
2. **Wann kommt Stufe B — vor oder nach Paper 2?** Vorher: Paper 2 arbeitet im endgültigen Raum,
   aber unter erschwerter Identifizierbarkeit. Nachher: Paper 2 hat saubere Bedingungen, aber der
   Bogen behält bis Paper 3 einen zu engen Raum.
3. **Ist „Abdeckung über einen deklarierten Motivkatalog" eine tragfähige Formulierung?** Sie ist
   ehrlicher als eine Universalitätsbehauptung und prüfbar — aber sie bindet die Methode an einen
   Benchmark statt an eine Theorie.
4. **Wird der Schwanz bedient?** Fünf Familien für fünf Systeme, um von 58 auf 63 zu kommen. Mein
   Vorschlag ist: nein, und die Kante wird als Ergebnis berichtet.

---

## 8. Vorschlag

Phase B läuft seit dem 22.08. und ist die Vorher-Messung für alles Weitere: Sie etabliert den
Controller auf der heutigen Basis und liefert R² je Surrogatsystem. Damit wird aus „nicht
darstellbar" ein „wird so gut approximiert" — und erst das sagt, welche Familien ihren Preis wert
sind. Ein System, das trotz fehlender Terme R² von 0,99 erreicht, rechtfertigt keine
Architekturänderung; eines bei 0,3 schon.

Bis dahin: Motivkatalog steht (dieses Dokument), Protokoll-Audit um die Repräsentationsspalte
erweitern, entscheiden nach den Daten.

---

## 9. Ergebnis der Diskussion (22.08.2026)

Die Vorlage oben ist der Stand *vor* dem Gespräch. Dieser Abschnitt hält fest, was daraus wurde —
einschließlich der Stellen, an denen die Vorlage korrigiert wurde.

### Entschiedene Reihenfolge

```text
Paper 1  ->  Paper 2  ->  Representation Expansion (Brücke)  ->  Paper 3
```

Die Repräsentationserweiterung wird **kein eigenes Paper**, sondern eine methodische Brücke zwischen
Paper 2 und Paper 3. Damit hat die Frage endlich einen Platz im Bogen, ohne ihn auf vier Arbeiten zu
strecken.

**Begründung für „erst nach Paper 2"** — und sie ist wissenschaftlich, nicht organisatorisch: Paper 2
fragt, warum Recovery scheitert, *obwohl* die Wahrheit im Raum liegt. Wird vorher der Raum
verbreitert, ändern sich Kandidatenraum, Kollinearitäten, Optimierungslandschaft und
Identifizierbarkeit gleichzeitig — dann behandelt Paper 2 mehrere Ursachen auf einmal und kann keine
davon isolieren.

**Gegenmaßnahme, die dazugehört:** Die Operatoren aus Paper 2 müssen **katalogunabhängig** entworfen
werden. Bauen sie auf Polynomstruktur, überträgt sich Paper 2 nicht auf den erweiterten Raum, und
die Reihenfolge kostet genau das, was sie sparen soll.

### Entschieden: keine Stufe A allein

Stufe A ist repräsentationstechnisch billig, aber **experimentell nicht**. Neue Basis heißt neuer
`config_fingerprint`, neue Kandidatenzahl, verschobene Promotionszeitpunkte, anderer Lookahead, neue
Caps, neues Kostenmodell, neuer Regressionsblock — bei A ebenso wie bei B. Der experimentelle Preis
ist derselbe, der methodische Gewinn nicht: 39/63 lässt genau die interessanten Motive draußen
(Sättigung, Hill, skalierte Oszillation). Der Controller wird nicht dadurch interessanter, dass
zusätzlich `u1^2*u2` wählbar ist.

**Also: A und B gemeinsam, einmal bezahlen.**

### Entschieden: der Schwanz wird nicht bedient

58 → 63 kostet fünf Operatorfamilien für fünf Systeme. Marginale Effizienz von eins zu eins — der
Punkt, an dem Benchmark-Vollständigkeit in Benchmark-Overfitting übergeht. Die fünf bleiben als
**out-of-catalog cases** stehen und werden als solche berichtet.

### Korrektur 1 — die GP-Abgrenzung war zu binär

Die Vorlage behauptet: Fällt eine der drei Eigenschaften weg, ist man bei GP. Das ist zu stark.
Zwischen katalogbasierter Strukturentwicklung und GP liegen grammatikgeführte symbolische
Regression, Beam Search, MCTS, enumerative Suche, Programmsynthese und neuronale symbolische Suche.
GP ist **eine** Suchstrategie im kompositionellen Raum, nicht sein Synonym.

Die tragfähige Achse ist deshalb nicht `EvoODE ↔ GP`, sondern:

```text
statisch vorab begrenzter Raum  ↔  kontrolliert wachsender Raum  ↔  frei kompositioneller Raum
```

EvoODE steht in der Mitte, und die Mitte ist dünn besetzt. Das ist die stärkere Positionierung.

### Korrektur 2 — „abzählbarer Katalog" ist bei Stufe B falsch

Sobald `sin(ωx)` mit reellem `ω` zulässig ist, gibt es kontinuierlich viele konkrete
Basisfunktionen. Endlich bleibt die Menge der **Termtypen**. Die Methode ist deshalb künftig zu
definieren über einen

> endlichen, staffelbaren Katalog **parametrisierter Term-Templates**

und nicht über einen abzählbaren Katalog von Basisfunktionen. Jede Instanz trägt wenige innere
Parameter bei linear bleibenden äußeren Koeffizienten.

### Korrektur 3 — der Katalog darf nicht aus dem Benchmark abgeleitet werden

Die Vorlage ist an dieser Stelle zirkulär: Sie leitet die Familien aus ODEBench her und misst den
Katalog dann an ODEBench. Richtig ist die umgekehrte Reihenfolge — den Katalog **semantisch**
definieren (Offsets und Forcing, polynomiale Eigendynamik, polynomiale Interaktion, sättigende
Interaktion, oszillatorische Transformation) und ODEBench anschließend zur *Messung* der
empirischen Reichweite verwenden. Dann ist 58/63 eine Eigenschaft der Modellierungsphilosophie und
nicht ihre Definition. Die Zahl darf sich dabei verschieben.

### Korrektur 4 — „rational" ist keine zulässige Operatorfamilie

`P(x)/Q(x)` als Familie würde den Raum sprengen. Zugelassen werden **benannte mechanistische
Motive**: `x/(K+x)`, gegebenenfalls `x^n/(K^n+x^n)`, analog `sin(ωx)` und `cos(ωx)`. EvoODE
erweitert nicht die Grammatik, sondern ergänzt wenige semantisch definierte dynamische Motive.

### Neu: drei Ebenen statt zwei

Die Vorlage unterscheidet Darstellbarkeit und Auffindbarkeit. Die tragfähige Trennung hat drei
Ebenen, und sie ist für den gesamten Bogen wertvoll:

| Ebene | Frage | Bei Scheitern |
|---|---|---|
| **Representability** | Liegt `f*` überhaupt in `H`? | keine Suche kann helfen |
| **Identifiability** | Unterscheiden die Daten `f*` von Alternativen? | Informationsproblem, kein Suchproblem |
| **Search recoverability** | Findet der Algorithmus `f*` im Budget? | erst hier ist es ein Suchproblem |

Erst wenn die ersten beiden Ebenen geklärt sind, ist ein Fehlschlag eindeutig als Suchproblem
interpretierbar. Das ist die Präzisierung, die Paper 2 seinen Geltungsbereich gibt.

### Neu: der Protokoll-Audit braucht zwei Spalten, nicht eine

Eine boolesche Spalte „repräsentationsfähig" reicht nicht. Zu trennen sind:

- **in principle representable** — die Methode könnte die Struktur ausdrücken
- **representable under the evaluated protocol** — sie ist unter den tatsächlich verwendeten
  Operatoren, Limits und Restriktionen erreichbar

Der Unterschied ist der ganze Punkt: SINDy kann beliebige Bibliotheken tragen, aber wenn im
publizierten Experiment Polynome bis Grad 3 verwendet wurden, ist ein Sättigungsterm dort nicht
erreichbar. PySR kann einen Operator erlauben und ihn durch Komplexitätsgrenzen dennoch unerreichbar
machen. ODEFormer hängt zusätzlich an seiner Trainingsverteilung.

Diese Dimension wird in Symbolic-Regression-Vergleichen üblicherweise nicht sichtbar gemacht — sie
ist ein eigener methodischer Beitrag von Paper 3.

### Offen, und von mir ergänzt: die R²-Auswertung braucht eine Referenz

Der Plan ist, aus Phase B je fehlender Motivfamilie das mittlere Surrogat-R² zu lesen und daran zu
entscheiden, welche Familien ihren Preis wert sind. Das hat eine Verwechslungsgefahr: **Ein R² von
0,3 belegt nicht, dass die Familie fehlt** — es kann auch die Suche gewesen sein, die das beste
Modell innerhalb der aktuellen Klasse nicht gefunden hat. In den Records sieht beides gleich aus.

Nötig ist deshalb eine Referenz: die **beste erreichbare Anpassung innerhalb der aktuellen Basis**,
algebraisch auf dem Ableitungsproblem gerechnet, ohne Suche. Erst die Differenz zwischen dieser
Referenz und dem tatsächlich gefundenen Modell trennt „die Klasse kann es nicht" von „die Suche fand
es nicht". Billig zu rechnen und ohne sie ist die Auswahlregel nicht belastbar.

### Was jetzt gilt

- Phase B läuft **unverändert** weiter. Keine Basisänderung, keine Fingerprint-Änderung, kein neuer
  Regressionsblock.
- Die Surrogat-R² werden nach fehlender Motivfamilie ausgewertet — mit der Referenz oben.
- Der Protokoll-Audit bekommt die zwei Repräsentationsspalten.
- Die Repräsentationserweiterung wird nach Paper 2 als Brücke umgesetzt, A und B gemeinsam.
