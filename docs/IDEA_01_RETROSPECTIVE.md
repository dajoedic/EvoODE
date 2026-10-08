# Idee #1 – Annihilator-Guided ODE Discovery: Rückblick

**Stand: 2026-10-08, endgültig. Idee #1 ist gescheitert und abgeschlossen** (Entscheidung des Nutzers, §10).
Zusammenfassung aller Erkenntnisse der Spur, vom Auftauchen der Idee bis zum Abschluss. Für den Nutzer und für die
eigene Akte (PhD-Verlauf). Alle Zahlen stammen aus den verlinkten Dokumenten und Records dieses Branches; der
Endstand trägt den Git-Tag `idea01-annihilator-closed`.

## 1. Kurzfassung

- **Idee:** Statt symbolische Formeln zu erraten, zuerst aus den Daten den einfachsten linearen
  Differentialoperator $L$ bestimmen, der die rechte Seite $f$ einer ODE annihiliert ($L f = 0$). Sein
  Lösungsraum ist dann der datengestützte Hypothesenraum für $f$, inklusive eines statistisch begründeten
  „die Daten reichen nicht“ (`AMBIGUOUS`).
- **Ergebnis:** Die Methode funktioniert sauber für einfache Operatoren erster und zweiter Ordnung mit konstanten
  oder einfachen Koeffizienten, also für Exponentialfunktionen, Potenzen und Gauß-Funktionen. An dem, was sie
  einzigartig machen sollte, scheitert sie: an $x$-abhängigen Koeffizienten (Logarithmen, Gompertz, rationale
  Funktionen) unter realistischem Rauschen.
- **Hauptgründe:**
  1. Die Rauschverstärkung höherer Ableitungen bleibt auch in der schwachen Form.
  2. Die Komplexitätsordnung des Operatorraums bevorzugt falsche Surrogate.
  3. Die Abstention erkennt stabile Fehlwahlen nicht.
  4. Im End-to-End-Fall braucht die Methode die Zeitableitung $\dot x$, die sie nicht vermeiden kann.
- **Sechs Prüfungen** (Gate 2A in drei Versionen, Diagnose `AMBIGUOUS`, Reality-Check, ODEBench-Smoke-Test) zeigen
  dieselbe Grenze.
- **End-to-End-Vergleich** gegen SINDy und W-SINDy (§9): Mit Glättung ist der Annihilator in der Funktionsgüte
  konkurrenzfähig. Ob das am Operator oder an der Glättung liegt, ist offen. Die Struktur trifft er bei 1 % nur bei
  der Logistik.

## 2. Warum wir die Idee hatten

Ausgangspunkt war die Bilanz von EvoGrow (Paper 1, Phase C), dokumentiert in
`docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` §1:

- sehr guter Fit einzelner Trainingstrajektorien, aber schlechte Generalisierung auf neue Anfangsbedingungen;
- geringe rohe Strukturtreue: Ein Modell zeichnet die Trajektorie nach, ohne dass seine Struktur von den Daten
  gestützt wird;
- chaotische Systeme scheitern schon beim Parameterfit der wahren Struktur;
- globale ODE-Integration und nichtlineare Optimierung machen die Methode sehr langsam, und die Effizienzthese
  trägt nicht;
- die feste Polynomstruktur ist für relevante Systeme wie Gompertz zu eng.

Die Leitidee daraus:

> Nicht zuerst symbolische Ausdrücke generieren und testen, sondern aus den Daten zunächst die mathematische
> Struktur des unbekannten Vektorfelds diagnostizieren und daraus erst den zulässigen symbolischen Hypothesenraum
> ableiten.

## 3. Die Idee

**Annihilatoren.** Viele Funktionsfamilien erfüllen eine lineare Differentialgleichung mit polynomialen
Koeffizienten:

$$
L = \sum_{k=0}^{r} p_k(x)\,D^k,\qquad p_k(x) = \sum_{j=0}^{d} c_{kj}\,x^j,\qquad L f = 0 .
$$

| Funktion | Operator |
|---|---|
| $e^{ax}$ | $D - a$ |
| $x^p$ | $xD - p$ |
| $\sin(ax + b)$ | $D^2 + a^2$ |
| $e^{-x^2}$ | $D + 2x$ |
| $\log x$ | $xD^2 + D$ |
| $x\log x$ | $xD^3 + D^2$ |

Auch rationale Funktionen wie $x/(K+x)$ gehören dazu. Die Frage lautet dann nicht mehr „Welche Formel passt?“,
sondern „Welcher einfachste Operator ist mit den Daten verträglich?“.

**Bausteine der Methode:**

1. **Schwache Form:** Statt $f', f'', f'''$ aus verrauschten Daten zu schätzen, wird $Lf = 0$ mit glatten
   Testfunktionen $\psi(x)$ integriert, und die Ableitungen werden per partieller Integration auf $\psi$
   gewälzt. Die Operatormatrix ist dann linear in den beobachteten Werten $f_i$.
2. **Statistischer Test:** Weil die Matrix linear in $f_i$ ist, ist die Residuenkovarianz für eine feste
   Operatorhypothese analytisch berechenbar. Die Annahme eines Operators wird ein $\chi^2$-Test mit $\alpha = 1\,\%$
   statt eines frei gewählten Schwellwerts. Geschätzt wird auf Fit-Proben, getestet auf disjunkten
   Validierungsproben.
3. **Minimalität:** Gesucht wird die einfachste nicht verworfene Klasse nach der Ordnung $C = (r+1)(d+1)$.
4. **`AMBIGUOUS`** als erlaubtes Ergebnis, ausgelöst durch drei Kriterien:
   - A1: mehrdimensionaler Fast-Nullraum;
   - A2: instabile Auswahl im Bootstrap;
   - A3: zu große Koeffizientenunsicherheit.
5. **Rekonstruktion:** Der Lösungsraum von $L$ liefert die Funktionsfamilie, ein Kleinste-Quadrate-Fit liefert
   $\hat f$.

**Erhoffte Vorteile:**

- keine Expression-Tree-Suche und keine feste Library;
- im Kern lineare Algebra;
- Struktur vor Parametern;
- explizite Aussage über Nicht-Identifizierbarkeit;
- Funktionsfamilien jenseits von Polynomen, etwa Gompertz.

## 4. Wie getestet wurde

Die Spur folgte bewusst harten Regeln (`CLAUDE.md`):

- Erst billig versuchen, die Idee zu zerstören.
- Jede Entscheidungsregel wird vor dem ersten Lauf eingefroren, Änderungen nur als neue Version.
- Keine Kalibrierung am Gate-Set, Kalibrierung nur auf einem disjunkten Set (K1–K8).
- Ein verschlossenes Prüfset (ODEBench 4/49/59/62) wurde nie angesehen.

Gate 2A war bewusst die günstigste denkbare Form: $(x_i, f_i)$-Paare **direkt gegeben**, ohne ODE und ohne
$\dot x$. Erst Gate 2B hätte die volle Kette aus Trajektorien geprüft.

## 5. Wie sich die Idee entwickelt hat

| Datum | Schritt | Ergebnis | Dokument |
|---|---|---|---|
| 04.10. | Leitdokument, Gate 2A v1 eingefroren | exakte Referenzklassen F1–F10 bestimmt; höhere Klassen enthalten fast immer weitere wahre Annihilatoren, daher keine Ambiguität über „zweite Klasse besteht auch“ | `IDEA_01_…`, `GATE_2A.md` |
| 04.10. | Abnahme v1 | **blockiert:** Matrix ungenau ($3\cdot10^{-3}$ bei F9), Schätzer bei F4 um das 47-Fache seiner Streuung verzerrt, F9 bei 1 % praktisch zufällig | DIARY 04.10. |
| 04./05.10. | Gate 2A v2 | stabile Leibniz-Auswertung, $q = 14$, FNS-Schätzer, A3, Ex-ante-Identifizierbarkeit; **Stufe K scheitert:** FNS landet auf Sattelpunkten; ab Ordnung 4 gibt es Punkte fern von $c^*$ mit kleinerem $J$ als $c^*$ | `GATE_2A_v2*.md` |
| 05.10. | Gate 2A v3 | L-BFGS statt FNS. **Anhang A nicht bestanden:** Ordnung 1–2 kalibriert, Ordnung 3 unterschätzt die Streuung um Faktor 2–7. **Anhang B:** Kill-Kriterium K6 würde auslösen, F4, F5, F8 bei 1 % nicht identifizierbar (N1) | `GATE_2A_v3_STAGE_K_RESULT.md` |
| 05./06.10. | Diagnose `AMBIGUOUS` (N = 100, Orion) | **negativ:** 118 von 118 eindeutigen N1-Antworten falsch; F4 zu 99 % stabil falsch (3,0) mit Bootstrap 1,0 | `DIAGNOSTIC_AMBIGUITY_RESULT.md` |
| 06.10. | Reality-Check A | `STRONG_NEGATIVE`: Best-Subset-Regression auf denselben Samples und mit derselben Suchregel trifft F4/F5/F8 in 60/60 | `REALITY_CHECK_DIRECT_REGRESSION_RESULT.md` |
| 06./07.10. | ODEBench-Smoke-Test (Oracle-$f$) | v1: Aufbaufehler (Trajektoriengitter gegen $\tau$-Boden); v2: **beenden (A)**, rauschfrei 2/4 exakt, bei 1 % 0/4; Gompertz schon rauschfrei verfehlt | `ODEBENCH_SMOKE_TEST_RESULT.md` |
| 07.10. | End-to-End-Vergleich (alle Methoden aus denselben Trajektorien) | v1: Der interpolierende Spline ließ das Ableitungsrauschen explodieren. v2 mit Glättung (08.10.): Funktionsgüte konkurrenzfähig, Struktur bei 1 % nur bei der Logistik | `ODEBENCH_END2END_RESULT.md` |

**Wendepunkte im Verständnis:**

1. **Nach v1:** Die schwache Form löst das Rauschproblem nicht grundsätzlich. Sie verschiebt die Ableitungen auf
   die Testfunktionen, aber die Verstärkung $\sim w^{-k}$ bleibt (wie bei Weak-SINDy). Möglich ist nur noch ein
   quantitativer Vorteil.
2. **Nach v2/v3:** Der statistische Kern funktioniert, wo die Numerik sauber ist (F2: Ablehnung 0,8 % bei Soll
   1 %). Ab Ordnung 3 wird die Unsicherheitsrechnung falsch, ab Ordnung 4 fehlt die Information in den Daten.
3. **Nach Anhang B und der Diagnose:** Das Problem ist nicht nur Rauschen, sondern die **Hypothesenordnung**.
   Falsche Klassen mit konstanten Koeffizienten werden vor den wahren mit $x$-abhängigen Koeffizienten geprüft und
   nicht verworfen.
4. **Nach dem Reality-Check:** Die Daten tragen die Struktur. Eine direkte Regression trifft dieselben Fälle
   immer; das Surrogatproblem kommt aus der Repräsentation.
5. **Nach dem Smoke-Test, Diskussion am 07.10.:** Der Testfehler-Vorsprung des Annihilators kam vom Oracle-$f$.
   Und die schwache Form der Methode integriert in $x$, nicht in $t$: Sie vermeidet die Ableitungen von $f$, aber
   nicht die Zeitableitung $\dot x$, die nötig ist, um $f$ aus Trajektorien zu bekommen.

## 6. Woran die Idee gescheitert ist

### 6.1 Rauschverstärkung höherer Ableitungen

Ein Operator der Ordnung $r$ verlangt Information über $f^{(r)}$. Die schwache Form wälzt die Ableitungen auf die
Testfunktion, aber die Rauschverstärkung $\sim w^{-r}$ bei Testfunktionsbreite $w$ bleibt ein
Bias-Varianz-Konflikt.

- Gemessen ab Ordnung 3: Die Koeffizientenstreuung wird um Faktor 2–7 unterschätzt.
- Ab Ordnung 4: Bei 1 % Rauschen gibt es Punkte fern vom wahren Operator mit besserer Anpassung (K5, K8).

Genau die interessanten Funktionen brauchen höhere Ordnung oder $x$-abhängige Koeffizienten: $\log x$ ist (2,1),
$x\log x$ und Gompertz sind (3,1), die Logistik mit Ernte ist (2,2).

### 6.2 Die Komplexitätsordnung bevorzugt Surrogate

Die Suche nimmt die erste nicht verworfene Klasse nach $C = (r+1)(d+1)$. Klassen mit konstanten Koeffizienten
beschreiben Exponentialpolynome mit **freien** Raten. Diese Familien sind flexibel und imitieren $\log x$,
$x\log x$ oder $x/(2+x)$ innerhalb von 1 % Rauschen.

- Für $\log x$ kommt (3,0) mit $C = 4$ vor dem wahren (2,1) mit $C = 6$.
- Die Fehlwahlen folgen fast exakt der idealen Teststärke aus Anhang B. Für F8 wird (2,0) mit Güte 0,80 verworfen,
  erwartet sind also 20 % Fehlwahlen; beobachtet wurden 19 %.

Im Funktionsraum ist $\log x$ ein einziger Term. In der Operatorordnung ist es die komplexere Hypothese.

### 6.3 Die Abstention erkennt stabile Fehlwahlen nicht

`AMBIGUOUS` sollte die Antwort auf Nicht-Identifizierbarkeit sein. Tatsächlich:

- A2 (Bootstrap) misst Stabilität. Eine systematisch nicht verwerfbare falsche Klasse ist aber stabil: F4 wird zu
  99 % mit Bootstrap 1,0 falsch beantwortet.
- A1 feuert, wenn die gewählte falsche Klasse zufällig einen mehrdimensionalen Fast-Nullraum hat (F5). Das ist ein
  Nebeneffekt der Klassenstruktur, kein Evidenzsignal.
- Im Smoke-Test feuerten A1 und A3 auch bei **richtigen** Antworten (Logistik und SIR: 10/10 richtige Klasse, alle
  `AMBIGUOUS`).

Ergebnis: In den schweren Fällen falsch oder unentschieden, in den leichten Fällen richtig, aber unentschieden.

### 6.4 Die Zeitableitung lässt sich nicht vermeiden

Aus Trajektorien kennt man nur $x(t)$; $f$ gibt es nur als $\dot x$. Die partielle Integration des Annihilators
läuft in $x$ und beseitigt $f', f'', \dots$, aber nicht $\dot x$. W-SINDy dagegen integriert in $t$ und braucht gar
keine Ableitung. Ein Variablenwechsel holt $\dot x$ zurück: $\int g(x) f(x)\,dx = \int g(x(t))\,\dot x^2\,dt$.
Zeitintegrale liefern zwar ableitungsfreie Information, aber über $1/f$, und $1/f$ hat im Allgemeinen keinen
Annihilator mehr.

Gemessen am 07.10.:

| | Logistik | Gompertz |
|---|---|---|
| Fehler der geschätzten Ableitung bei 1 % Rauschen auf $x$ | 56–63 % | 140–190 % |
| nach bestmöglicher Glättung | etwa 2 % | 10–15 % |

Zum Vergleich: Gate 2A hatte 1 % Rauschen direkt auf $f$, und schon das war ab Ordnung 3 kritisch. Das hatte das
Leitdokument für Gate 2B bereits als „technischen Engpass“ benannt; Gate 2A hatte ihn bewusst übersprungen.

### 6.5 Praktische Hürden

- **Stichprobe:** Die Methode braucht dichte, gleichmäßige $x$-Stichproben. Trajektorien liefern gehäufte Punkte
  am Gleichgewicht und Lücken, wo die Dynamik schnell ist. Ohne neue Kalibrierung verwirft der Test darauf sogar den
  exakten Operator ($T \approx 5\cdot10^{14}$ bei kritischem Wert 250). Bei Gompertz bleibt selbst mit kubischem
  Spline ein Fehler von $5\cdot10^{-4}$, und der kippt den (3,1)-Operator.
- **Konditionierung:** Der Operator (2,2) von System 19 kippt schon bei $5\cdot10^{-6}$ relativem Datenfehler.
- **Kosten:** Ein Annihilator-Fit dauert 15–30 min, ein SINDy-Fit Sekunden. Für einen praktischen Benchmark ist das
  ein Nachteil, auch wenn Laufzeit hier nie als Evidenz galt.

### 6.6 Exakte Struktur ist ein hartes Kriterium, aber nicht der Grund

Auch die Baselines treffen die exakte Struktur selten. Mit AICc wählten SINDy und W-SINDy dichte Modelle mit 6–9
Termen; im Reality-Check traf Best-Subset dagegen 200/200. Der Smoke-Test scheiterte formal an Bedingung A, die nur
den Annihilator betraf. Der Nutzer hat deshalb zu Recht einen Vergleich verlangt statt einer absoluten Hürde. Der
End-to-End-Vergleich soll genau das liefern.

## 7. Was funktioniert hat und was bleibt

**An der Methode:**

- Für Operatoren erster und zweiter Ordnung mit konstanten oder einfachen Koeffizienten findet sie den richtigen
  Operator. Der statistische Test ist dort kalibriert: F2 0,8 % Ablehnung, I-Fälle 297/300 `CORRECT`, Logistik und
  SIR im Smoke-Test rauschfrei exakt.
- Die Kette $L \to$ Lösungsraum $\to \hat f$ funktioniert bei korrektem Operator numerisch exakt (Fehler
  $\le 2\cdot10^{-11}$).
- Mit Oracle-$f$ ist $\hat f$ auch bei 1 % Rauschen genau ($\mathrm{NRMSE}_f \approx 5\cdot10^{-4}$). Das ist aber
  im Wesentlichen eine geglättete Regression auf exakten Stützstellen.

**Inhaltliche Einsichten:**

1. Ein Sparsamkeitsprinzip ist nur so gut wie die Komplexitätsordnung, in der es angewendet wird. Operatorordnung
   und Funktionsraum-Einfachheit können entgegengesetzt sein.
2. Bootstrap-Stabilität ist kein Identifizierbarkeitstest. Eine robuste Abstention müsste prüfen, ob eine spätere
   Hypothese ebenfalls verträglich ist; das wäre eine neue Methode.
3. Schwache Formen helfen gegen die Ableitungen, über die integriert wird, nicht gegen andere. Wer aus Trajektorien
   lernt, muss die Zeitableitung vermeiden (W-SINDy) oder sauber schätzen.

**Zum Vorgehen** (übertragbar auf jede weitere Spur):

- Entscheidungsregeln vor dem Lauf einfrieren hat mehrfach verhindert, dass Ergebnisse nachträglich umgedeutet
  wurden.
- Gepaarte Vergleiche auf identischen Samples und Gültigkeitsprüfungen der Baseline machen negative Ergebnisse
  belastbar.
- **Plausibilitätsprüfungen müssen den Produktivpfad prüfen.** Mehrere Fehler fielen erst im Pilot auf:
  - die Polstelle in $L \to \hat f$;
  - die Quadratur auf Trajektoriengittern;
  - der nicht serialisierbare Worker-Record;
  - der Spline.

  Pilotläufe vor jedem Hauptlauf haben sich bezahlt gemacht.
- **Eigene Fehler, offen benannt:**
  - lineare Interpolation, danach ein interpolierender Spline für verrauschte Daten;
  - eine AICc-Auswahl, die die Baselines zu dichten Modellen drängte;
  - `STRUCT_OK` mit Obermengen;
  - Empfehlung, Variante B (End-to-End) zunächst wegzulassen.

  Jeder dieser Fehler wurde vor dem jeweiligen Hauptlauf oder in einer neuen Version korrigiert.

## 8. Was eine Wiederaufnahme bräuchte

Keine Reparatur der bisherigen Form, sondern neue Ideen mit eigener, eingefrorener Prüfung:

1. Eine **Komplexitätsordnung im Funktionsraum** statt nach Koeffizientenzahl, etwa nach der Dimension oder
   Flexibilität des Lösungsraums.
2. Eine **eingebaute Identifizierbarkeitsprüfung**: Bleibt eine strukturell andere, spätere Klasse ebenfalls
   verträglich, wird abstainiert.
3. Eine **ableitungsfreie End-to-End-Form**, also eine schwache Form in $t$ und $x$ zugleich. Ob es die gibt, ist
   offen; das $1/f$-Argument (§6.4) spricht dagegen.
4. Neue, versiegelte Testfunktionen. F1–F10 sind Entwicklungsset, das Prüfset 4/49/59/62 ist weiterhin ungesehen.

## 9. End-to-End-Vergleich (v1 und v2)

**Bericht:** `docs/ODEBENCH_END2END_RESULT.md`.

**Aufbau:** SINDy, W-SINDy und Annihilator auf denselben verrauschten Trajektorien der Systeme 3, 7, 19 und 21.

- Auswahl: gemeinsam über den Validierungsfehler.
- Gemessen: R² ≥ 0,9 für Rekonstruktion und Generalisierung (ODEBench-Standard P1, Extrapolation P2), dazu die
  Strukturtreffer.
- Keine Entscheidungsregel. Beide Läufe sind vollständig (je 216 Records).

**Ergebnis bei 1 % Rauschen:**

| | Logistik (3) | Gompertz (7) | Ernte (19) | SIR (21) |
|---|---|---|---|---|
| Rekonstruktion, Annihilator v1 / v2 | 4 / 17 von 20 | 0 / 14 | 5 / 20 | 4 / 19 |
| Rekonstruktion, SINDy / W-SINDy | 20 / 14 | 17 / 20 | 16 / 18 | 20 / 20 |
| Gen. P1, Annihilator v2 / bester Baseline | 8 / 5 von 10 | 0 / 0 | 10 / 6 | 8 / 5 |
| Gen. P2, Annihilator v2 / bester Baseline | 10 / 12 von 15 | 0 / 5 | 13 / 13 | 5 / 5 |
| Struktur exakt, Annihilator v2 | 4/15 | 0/15 | 0/15 | 0/15 |

**Lesart:**

1. **Der Einbruch in v1 war ein Aufbaufehler.** Mit Glättung (v2) ist der Annihilator in der Funktionsgüte
   konkurrenzfähig und bei P1-Generalisierung vorn.
2. **Woher der P1-Vorsprung kommt, ist offen.**
   - Nur der Annihilator bekommt eine eigens entworfene Glättung von $(x, \dot x)$.
   - Die meist gewählten Klassen mit konstanten Koeffizienten sind flexible Exponentialpolynome, also glatte
     Approximatoren.
   - Ein Vorteil des Operatoransatzes ist damit nicht belegt. Belegen könnte ihn SINDy auf denselben geglätteten
     Daten; das ist nicht gelaufen.
3. **Die Struktur, also das eigentliche Versprechen, bleibt aus.**
   - Exakt trifft der Annihilator nur die Logistik.
   - Bei SIR wählt er bei 1 % meist (1,1) ohne die wahre Funktion.
   - Bei Gompertz und Ernte landet er auf Surrogaten.
   - Das ist dasselbe Muster wie in §6.2.
   - Die Baselines treffen die exakte Struktur nie, weil die Auswahl über den Validierungsfehler dichte Modelle
     bevorzugt.
4. **Gompertz** generalisiert bei 1 % keine Methode. Der Annihilator ist dort am schwächsten (P2 0/15, W-SINDy 5/15).

**Eigener Fehler, offen benannt:** Die Annahme „Baselines deterministisch“ in v2 stimmte für W-SINDy nicht, weil
pysindy die Testfunktionen ohne Seed zieht. Die beiden vorhandenen Ziehungen schwanken um bis zu drei Fälle je
Zelle.

## 10. Abschluss

Am 2026-10-08 hat der Nutzer nach Sichtung des End-to-End-Ergebnisses entschieden: **Idee #1 ist gescheitert.**

- **Ausschlaggebend:** Das Kernversprechen, also Struktur vor Parametern, Familien jenseits fester Libraries mit
  Gompertz als zentralem Fall und eine begründete Abstention, ist in keiner der sieben Prüfungen eingelöst.
- **Nicht weiterverfolgt:** die offene Frage aus §9, ob die konkurrenzfähige Funktionsgüte vom Operator oder von
  der Glättung kommt. Sie hätte am Scheitern des Kernversprechens nichts geändert.
- **Abschlussabschnitt:** `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` §12, mit Belegtabelle (Dokumente, Code und
  Records je Prüfung).
- **Prüfset:** ODEBench 4/49/59/62 bleibt ungesehen und steht künftigen Ideen zur Verfügung.
- **Verworfen:** Der Entwurf `PRACTICAL_ANNIHILATOR_BENCHMARK.md` (Nutzer, Selective Prediction) wird mit dem
  Abschluss gegenstandslos. Er liegt als Akte im Repository.
