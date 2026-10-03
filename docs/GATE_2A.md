# Gate 2A – eingefrorene Spezifikation

**Status: EINGEFROREN, vom Nutzer abgenommen am 2026-10-04** (E1–E4 in §11 bestätigt, E3 präzisiert). Keine
Regel in diesem Dokument wird nach dem ersten Lauf geändert. Wer eine Regel ändern will, legt eine neue Version an
(`GATE_2A_v2`), die alten Ergebnisse bleiben stehen. Kontext: `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md`.

## 0. Frage und Abgrenzung

Lässt sich aus verrauschten Samples $(x_i, f_i)$ einer unbekannten skalaren Funktion ihr minimaler linearer
Differentialoperator mit polynomialen Koeffizienten rekonstruieren, und erkennt die Methode, wenn die Daten
das nicht hergeben?

Nicht Teil von Gate 2A: ODE-Trajektorien, Schätzung von $\dot x$, ODE-Integration, Symbolic Regression,
genetische Programmierung, nichtlineare Optimierung, Lösungsraum/Basis/symbolisches $f$, Clusterläufe.
Python mit NumPy und SciPy. SymPy und mpmath nur auf der Referenzseite (Abschnitt 3).

## 1. Hypothesenraum und Komplexitätsordnung

Operatorklassen $(r, d)$ mit $1 \le r \le 6$, $0 \le d \le 6$ (42 Klassen). Ein Operator der Klasse ist
$L = \sum_{k=0}^{r} \sum_{j=0}^{d} c_{kj}\, z^j D_z^k$ mit $\|c\|_2 = 1$. Dabei ist $z$ die skalierte Koordinate
aus Abschnitt 4.

Reihenfolge: aufsteigend nach $C(r,d) = (r+1)(d+1)$, bei Gleichstand kleineres $r$, dann kleineres $d$.
$r = 0$ ist ausgeschlossen, denn $p_0 f \equiv 0$ hat für $f \not\equiv 0$ keine Lösung.

## 2. Testfunktionen und Domänen

Zehn Funktionen, jede auf einer breiten und einer schmalen Domäne. Die schmale Domäne ist ein Teilintervall
mit 10 % der Breite der breiten Domäne. Sie ist absichtlich so gelegt, dass verschiedene Familien lokal
ähnlich aussehen.

| # | $f(x)$ | breit | schmal | Referenzklasse | $C$ | Referenzoperator (in $x$) |
|---|---|---|---|---|---|---|
| F1 | $x^2$ | $[-2, 2]$ | $[1.0, 1.4]$ | (1,1) | 4 | $xD - 2$ |
| F2 | $e^{1.5x}$ | $[-2, 2]$ | $[0.0, 0.4]$ | (1,0) | 2 | $D - 3/2$ |
| F3 | $x^{1.5}$ | $[0.2, 4]$ | $[1.0, 1.38]$ | (1,1) | 4 | $2xD - 3$ |
| F4 | $\log x$ | $[0.2, 4]$ | $[1.0, 1.38]$ | (2,1) | 6 | $xD^2 + D$ |
| F5 | $x\log x$ | $[0.2, 4]$ | $[1.0, 1.38]$ | (3,1) | 8 | $xD^3 + D^2$ |
| F6 | $e^{-x^2}$ | $[-2.5, 2.5]$ | $[0.5, 1.0]$ | (1,1) | 4 | $D + 2x$ |
| F7 | $\sin(2x + 1/2)$ | $[-3, 3]$ | $[0.0, 0.6]$ | (2,0) | 3 | $D^2 + 4$ |
| F8 | $x/(2+x)$ | $[0.1, 6]$ | $[1.0, 1.59]$ | (1,2) | 6 | $x(x+2)D - 2$ |
| F9 | $x^2 + e^x$ | $[-2, 2]$ | $[0.0, 0.4]$ | (4,0) | 5 | $D^4 - D^3$ |
| F10 | $\sin x + e^{-x^2}$ | $[-3, 3]$ | $[0.0, 0.6]$ | (5,1) | 12 | vom Orakel |

Die Spalten „Referenzklasse“ und „Referenzoperator“ sind die **Vorab-Kontrolle vom 04.10.** Sie stammen aus
einer unabhängigen Rechnung (Nullraum mit 60 Stellen Präzision auf 120 Punkten, alle 42 Klassen). Das Orakel
aus Abschnitt 3 muss sie reproduzieren, sonst ist das Orakel fehlerhaft und der Lauf startet nicht.

Bekannte Gleichstände, aufgelöst durch die Tie-Regel und nicht als Ambiguität zu werten: F1 hat bei $C = 4$
auch $D^3$ (3,0). F8 hat bei $C = 6$ auch $(x+2)D^2 + 2D$ (2,1). In vielen höheren Klassen existieren weitere
**wahre**, nicht-äquivalente Annihilatoren, z. B. $(xD-1)^2$ für F5 in (2,2) und ein Operator 2. Ordnung für F9
in (2,2). Deshalb darf `AMBIGUOUS` nie aus „eine andere Klasse besteht auch“ abgeleitet werden.

## 3. Referenzseite (Orakel)

Das Orakel bestimmt pro Funktion und Domäne in der skalierten Koordinate $z$ (Abschnitt 4):

1. für **jede** der 42 Klassen die exakte Nullraumdimension $n_{\text{exact}}(r,d)$;
2. die Referenzklasse = erste Klasse in der Ordnung mit $n_{\text{exact}} > 0$, und deren normierten
   Koeffizientenvektor $c^*$.

Verfahren: exakte symbolische Ableitungen von $f$ (SymPy). Daraus die Kollokationsmatrix
$M_{i,(k,j)} = z_i^j f^{(k)}(z_i)$ in mpmath mit 60 Stellen auf mindestens 120 Punkten. Nullraumdimension =
Anzahl der Singulärwerte unter $10^{-35}$ mal dem größten. Pflicht: In der Referenzklasse ist
$n_{\text{exact}} = 1$, sonst ist die Testfunktion ungeeignet und wird gemeldet. Für die Referenzklasse wird
$c^*$ zusätzlich symbolisch verifiziert: $L^*[f]$ vereinfacht exakt zu 0, nach Rationalisierung der
Koeffizienten bzw. mit den exakten Parametern. Das Orakel teilt die Ordnung mit der Methode, aber **keinen
Code der Weak-Matrix.** Ergebnis wird als JSON gecacht.

## 4. Daten, Skalierung und Noise

- Pro Domäne $[a, b]$: $N = 2000$ äquidistante Punkte $x_i$ einschließlich der Ränder.
- Skalierung von $x$ (fest, nur aus der Domäne, nie aus den Daten): $z = (x - \mu)/s$ mit $\mu = (a+b)/2$,
  $s = (b-a)/2$, also $z \in [-1, 1]$. Diese affine Transformation erhält $(r, d)$.
- $f$ wird **nicht** skaliert, denn $L[f] = 0$ ist homogen.
- Noise wird **auf die exakten Funktionswerte am Gitter in Originalkoordinaten** addiert, vor jeder weiteren
  Verarbeitung: $\tilde f_i = f(x_i) + \sigma\,\varepsilon_i$, $\varepsilon_i \sim \mathcal N(0,1)$ i.i.d.,
  $\sigma = \eta \cdot \operatorname{RMS}_i f(x_i)$, $\eta \in \{0, 0.01, 0.05\}$.
- Realisierungen: $\eta = 0$ eine (deterministisch), $\eta > 0$ jeweils 20 mit Seeds $0, \dots, 19$.
- **Der Methode ist $\eta$ bekannt** (siehe Abschnitt 11, Entscheidung E1). Sie rechnet mit
  $\sigma_{\text{eff}} = \sqrt{(\eta \cdot \operatorname{RMS}_i \tilde f_i)^2 + \sigma_{\text{floor}}^2}$
  und dem numerischen Boden $\sigma_{\text{floor}} = 10^{-8} \cdot \operatorname{RMS}_i \tilde f_i$.

## 5. Weak-Matrix

- $[-1, 1]$ wird in $B = 8$ gleich breite Blöcke geteilt. Blöcke mit ungeradem Index (1, 3, 5, 7) bilden
  $\Phi_{\text{fit}}$, gerade (2, 4, 6, 8) $\Phi_{\text{val}}$. Damit verwenden Fit und Validation disjunkte
  Samples, und ihr Noise ist unabhängig.
- Pro Block mit Mittelpunkt $z_b$ und Halbbreite $w$: $u = (z - z_b)/w$,
  $\varphi_{b,m}(z) = (1 - u^2)^q P_m(u)$ auf $|u| \le 1$, sonst 0. Dabei ist $P_m$ das Legendre-Polynom,
  $m = 0, \dots, M-1$, $M = 16$, $q = 8$. $\varphi$ ist $C^{q-1}$, Randterme verschwinden für alle $k \le 6$.
  Zeilen: $\Phi_{\text{fit}}$ und $\Phi_{\text{val}}$ je $4 \cdot 16 = 64$, mehr als die maximal 49 Unbekannten.
- Matrixeintrag für Zeile $(b,m)$, Spalte $(k,j)$:
  $A_{(b,m),(k,j)} = (-1)^k \int (z^j \varphi_{b,m})^{(k)}(z)\, \tilde f(z)\, dz$. Die Ableitungen der
  Testfunktion werden analytisch berechnet (Polynom). Das Integral wird mit der Trapezregel auf dem
  Sample-Gitter gebildet.
- Jede Zeile ist linear in $\tilde f$: $A c = W(c)\,\tilde f$. $W(c)$ ist eine bekannte Gewichtsmatrix, das
  Fundament der Kovarianz in Abschnitt 6.

## 6. Kandidat, Test und Entscheidung

Für jede Klasse in der Ordnung von Abschnitt 1:

1. **Kandidat:** SVD von $A_{\text{fit}}$. $\hat c$ = rechter Singulärvektor zum kleinsten Singulärwert.
2. **Residuum auf Validation:** $\rho = A_{\text{val}}\, \hat c$.
3. **Kovarianz:** $\Sigma_\rho = \sigma_{\text{eff}}^2\, W_{\text{val}}(\hat c) W_{\text{val}}(\hat c)^\top + A_{\text{val}} \Sigma_{\hat c} A_{\text{val}}^\top$.
   Der zweite Term ist die Schätzunsicherheit von $\hat c$ aus den Fit-Daten, in erster Ordnung propagiert
   (Störung des Singulärvektors durch $E_{\text{fit}}$, Plug-in mit der verrauschten Matrix). Ohne ihn würde
   der wahre Operator systematisch zu oft verworfen, weil $\hat c$ selbst geschätzt ist.
4. **Test:** $T = \rho^\top \Sigma_\rho^{+} \rho$, Freiheitsgrade = $\operatorname{rank}(\Sigma_\rho)$.
   Bestanden, wenn $T \le \chi^2_{\text{dof},\,1-\alpha}$ mit $\alpha = 0.01$.
5. Die **erste** bestandene Klasse ist die ausgewählte Klasse $(r_{\text{sel}}, d_{\text{sel}})$. Danach endet
   die Suche. Besteht keine Klasse bis (6,6), lautet das Ergebnis `NONE`.

**Ambiguität (nur zwei Quellen, beide vorab fest):**

- **A1, mehrdimensionaler Nullraum:** In der ausgewählten Klasse besteht auch der zweitkleinste rechte
  Singulärvektor von $A_{\text{fit}}$ den Test aus Schritt 2–4, mit seiner eigenen Störungspropagation.
- **A2, instabile Auswahl:** parametrischer Bootstrap mit $B_{\text{boot}} = 50$ Replikaten
  $\tilde f^{*} = \tilde f + \sigma_{\text{eff}}\,\varepsilon^{*}$, getestet mit $\sqrt 2\,\sigma_{\text{eff}}$
  („noise on noise“, bewusst konservativ). Die vollständige Suche läuft auf jedem Replikat. Wählt weniger als
  80 % der Replikate dieselbe Klasse, ist das Ergebnis `AMBIGUOUS`.

„Eine andere Klasse besteht ebenfalls“ ist ausdrücklich **kein** Ambiguitätskriterium (Abschnitt 2).

## 7. Ergebniszustände pro Lauf (gegen das Orakel)

| Zustand | Definition |
|---|---|
| `CORRECT` | ausgewählte Klasse = Referenzklasse, nicht ambig |
| `AMBIGUOUS` | A1 oder A2 trifft zu |
| `TRUE_NOT_REF` | nicht ambig, ausgewählte Klasse ≠ Referenz, aber $n_{\text{exact}}(r_{\text{sel}}, d_{\text{sel}}) > 0$: ein wahrer, nicht minimaler Annihilator. Kein falscher Operator |
| `WRONG` | nicht ambig, $n_{\text{exact}}(r_{\text{sel}}, d_{\text{sel}}) = 0$: Die Klasse enthält gar keinen Annihilator von $f$ |
| `NONE` | keine Klasse besteht |

Zusätzlich pro Lauf, als Kennzahlen und nicht für Zustände: Koeffizientenwinkel
$\arccos |\langle \hat c, c^* \rangle|$, falls die Klasse der Referenz entspricht; $T$ und Freiheitsgrade der
ausgewählten Klasse; die beiden kleinsten Singulärwerte von $A_{\text{fit}}$; der Bootstrap-Anteil.

## 8. Generalisierung schmal → breit (Diagnose, nicht entscheidend)

Der auf der schmalen Domäne ausgewählte Operator wird exakt in die $z$-Koordinate der breiten Domäne
transformiert. Die Transformation ist affin, $(r, d)$ bleibt erhalten, die Kovarianz wird linear mitgeführt.
Getestet wird mit dem Test aus Abschnitt 6 auf den Validation-Zeilen einer **unabhängigen** Realisierung der
breiten Domäne (Seed + 1000). Berichtet wird der Anteil bestandener Transfers pro Zelle.

## 9. Gate-Kriterien

Zelle = Funktion × Domäne × Noise-Level (20 Zellen pro Level).

**0 % (Clean):**
- *bestanden:* alle 10 breiten Zellen `CORRECT` mit Koeffizientenwinkel $< 10^{-6}$, und 0 schmale Zellen
  `WRONG`.

**1 %:**
- *bestanden:* In keiner Zelle sind mehr als 2 von 20 Realisierungen `WRONG` (das deckt die erwartete
  Fehlerrate bei $\alpha = 0.01$ mit Puffer ab), und alle fünf einfachen Funktionen mit $C \le 4$ (F1, F2,
  F3, F6, F7) sind auf der breiten Domäne in mindestens 11 von 20 Realisierungen `CORRECT`.

**5 %:** nur Belastungstest, wird berichtet und entscheidet nicht.

**Kill-Kriterien** (jedes einzelne beendet oder zwingt zur grundsätzlichen Neubewertung):

- **K1** (systematisch falsch unter exakten Daten): mindestens 2 der 20 Clean-Zellen `WRONG`, oder
  irgendeine breite Clean-Zelle `WRONG`.
- **K2** (stabil und selbstbewusst falsch bei 1 %): In irgendeiner Zelle wählen mindestens 10 von 20
  Realisierungen dieselbe falsche Klasse und sind dabei nicht `AMBIGUOUS`.
- **K3** (abhängig von willkürlichen Einstellungen): Sensitivitätsraster aus Abschnitt 10. Eine Variante
  ändert ein Clean-Ergebnis von `CORRECT` weg, **oder** sie ändert bei 1 % die Zahl der Zellen mit
  `WRONG`-Mehrheit oder mit `CORRECT`-Mehrheit um mehr als 2.
- **K4** (Nullraum praktisch nicht identifizierbar): Eine der fünf einfachen Funktionen ist bei 1 % auf der
  breiten Domäne in weniger als 11 von 20 Realisierungen `CORRECT`, **und** die Mehrheit ihrer übrigen
  Realisierungen ist `NONE` oder `WRONG`.

Weder bestanden noch Kill (z. B. eine schmale Clean-Zelle ambig): Bericht an den Nutzer, der Nutzer
entscheidet.

## 10. Sensitivitätsraster für K3 (vorab fest, eine Einstellung pro Variante)

Standard: $N = 2000$, $B = 8$, $M = 16$, $q = 8$, $\alpha = 0.01$, $\sigma_{\text{floor}} = 10^{-8}$,
$B_{\text{boot}} = 50$, Bootstrap-Schwelle 0.8.

| Variante | geändert |
|---|---|
| S1 / S2 | $N = 1000$ / $4000$ |
| S3 | $B = 12$ (6 Fit- + 6 Val-Blöcke) |
| S4 | $M = 24$ |
| S5 | $q = 10$ |
| S6 / S7 | $\alpha = 0.05$ / $0.001$ |
| S8 / S9 | $\sigma_{\text{floor}} = 10^{-10}$ / $10^{-6}$ |
| S10 / S11 | Bootstrap-Schwelle 0.7 / 0.9 |

Das Raster läuft auf 0 % und 1 %, beide Domänen, mit 20 Realisierungen bei 1 %.

## 11. Bei der Abnahme bestätigte Entscheidungen (Nutzer, 2026-10-04)

- **E1, Noise-Level bekannt: bestätigt.** Gate 2A gibt der Methode $\eta$ vor, denn es testet die
  Operatorrekonstruktion isoliert. Eine $\sigma$-Schätzung würde einen zweiten Fehlermechanismus
  hineinziehen. Sie wird erst in Gate 2B Teil der Pipeline. **Kein** zweiter Arm mit geschätztem $\sigma$ in
  Gate 2A.
- **E2, Clean-Kriterium auf der schmalen Domäne: bestätigt.** Dort gilt „kein `WRONG`“ statt „alles
  `CORRECT`“. Die schmale Domäne testet gerade Konditionierung und Identifizierbarkeit. `AMBIGUOUS`,
  `TRUE_NOT_REF` und `NONE` dürfen dort diagnostisch auftreten.
- **E3, `TRUE_NOT_REF`: bestätigt, mit Präzisierung.** `CORRECT` ≠ `TRUE_NOT_REF` ≠ `WRONG`, und die drei
  werden nie zusammengefasst. `TRUE_NOT_REF` ist kein falscher Operator und geht **nicht** in K2 ein. Es ist
  aber auch **kein** `CORRECT` und **keine** erfolgreiche Rekonstruktion des minimalen Operators. Es zählt
  nie für ein Bestehens-Kriterium: Eine breite Clean-Zelle mit `TRUE_NOT_REF` heißt „nicht bestanden“ (nicht
  Kill). Der Report weist den Anteil `TRUE_NOT_REF` pro Zelle und Noise-Level eigens aus. Häufiges
  `TRUE_NOT_REF` auf breiten Daten wäre ein Befund gegen die Kernthese, auch ohne ein Kill-Kriterium
  auszulösen.
- **E4, Domänen und Parameter in Abschnitt 2: bestätigt.** Die schmale Domäne hat exakt 10 % der Breite der
  breiten Domäne. Werte wie in der Tabelle.

## 12. Umsetzung und Aufwand

- Ort: `experiments/annihilator_gate2a/` auf dem Branch `annihilator-discovery`. Ergebnisse unter
  `experiments/annihilator_gate2a/results/` als CSV (eine Zeile pro Lauf) plus Zusammenfassung pro Zelle plus
  Gate-Verdikt. Seeds und alle Einstellungen stehen in jeder Zeile.
- Tests vor dem Lauf: Orakel reproduziert die Tabelle in Abschnitt 2. Die Weak-Matrix stimmt auf exakten
  Daten mit dem stark aufgelösten Integral überein. Die Kovarianzformel wird auf F2 mit 1.000
  Monte-Carlo-Realisierungen geprüft: empirische gegen analytische Verteilung von $T$ für den wahren Operator.
- Aufwand: Hauptlauf (60 Zellen, davon 40 × 20 Realisierungen × 50 Bootstrap-Replikate, kleine SVDs) in
  wenigen Minuten. Raster etwa 10-mal so viel. Gesamt unter 1 h auf dem Laptop, kein HPC.
