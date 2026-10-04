# Gate 2A v2 – Spezifikation

**Status: EINGEFROREN, vom Nutzer abgenommen am 2026-10-04** („Setz das um“, E5–E9 in §14). Vor dem Einfrieren
ergänzt: die numerisch stabile Auswertung in §5 und die Schwelle $10^{-8}$ in K-a, beides nach einer Messung auf dem
Kalibrier-Set (Begründung: `docs/GATE_2A_v2_RATIONALE.md`). Es gilt dieselbe Regel wie für v1: Keine Regel wird nach dem ersten Lauf geändert. Eine Änderung braucht eine neue Version.
`docs/GATE_2A.md` (v1) bleibt eingefroren und unverändert stehen, ebenso seine Abnahme-JSONs (Branch `9d6a4d0`).
Kontext: `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md`, Diagnose im `DIARY.md` vom 04.10.

## 0. Frage und Abgrenzung

Die Frage bleibt dieselbe wie in v1: Lässt sich aus verrauschten Samples $(x_i, f_i)$ einer unbekannten skalaren
Funktion ihr minimaler linearer Differentialoperator mit polynomialen Koeffizienten rekonstruieren? Und erkennt
die Methode, wenn die Daten das nicht hergeben?

Auch die Abgrenzung ist dieselbe: keine ODE-Trajektorien, keine Schätzung von $\dot x$, keine ODE-Integration,
keine Symbolic Regression, kein GP, keine nichtlineare Optimierung außer der Fixpunkt-Eigenwertiteration in §6.
Python mit NumPy und SciPy. SymPy und mpmath nur auf der Referenzseite.

## 0a. Was v1 gezeigt hat und was v2 deshalb ändert

Die Abnahme von v1 scheiterte an F4 und F9 (Diagnose im DIARY vom 04.10.). Jede Änderung in v2 folgt aus einem
dieser Befunde. **Keine Änderung wird an F1–F10 eingestellt.** Wo eine Einstellung aus Daten festgelegt werden
muss, kommt sie aus dem disjunkten Kalibrier-Set (§2b, §10). F1–F10 werden erst angefasst, wenn die Kalibrierung
eingefroren und vom Nutzer abgenommen ist.

| Befund in v1 | Änderung in v2 | Warum das keine Kalibrierung am Gate-Set ist |
|---|---|---|
| Matrixfehler wächst mit der Ableitungsordnung (F9: $3\cdot10^{-3}$ bei $N = 1000$) | (i) **Numerisch stabile Auswertung** der Testfunktionsableitungen statt Monomdarstellung vom Grad ~40 (§5). (ii) $q = 14$ statt 8: Jeder Integrand ist global $C^7$, auch bei $k = 6$. In v1 war er bei $k = 6$ nur $C^1$ | Gemessen auf K5 (Kalibrier-Set, Ordnung 4). Monomdarstellung: Fehler flach in $N$, also Rundung. Stabil mit $q = 8$: Konvergenz etwa 5. Ordnung, also Quadratur. Stabil mit $q = 14$: $\sim10^{-10}$ bei Blockbreite 0,25 und $\sim10^{-13}$ bei Breite 1. Beide Änderungen sind nötig |
| Konstanter Boden $\sigma_{\text{floor}} = 10^{-8}$ lag unter dem Matrixfehler. F2 clean wurde `AMBIGUOUS` | $\sigma_{\text{floor}}$ wird aus dem gemessenen Quadraturfehler auf dem Kalibrier-Set festgelegt (§10) | Kalibrier-Set, nicht Gate-Set |
| Die SVD ist bei heteroskedastischen, korrelierten Fehlern in $A$ verzerrt (F4: Bias = 47 Streuungen) | Maximum-Likelihood-Schätzer (FNS): Er minimiert genau die Statistik, mit der das Gate testet (§6) | Folgt aus dem eigenen Rauschmodell $A c = W(c)\tilde f$. Es gibt keinen freien Parameter |
| Schmale Testfunktionen verstärken das Rauschen bei hoher Ordnung, Faktor $\sim w^{-k}$ (F9 bei 1 % nicht identifizierbar) | Multiskalige Testfunktionen von domänenbreit bis $2^{-\ell_{\max}}$. Die ML-Gewichtung wertet verrauschte schmale Zeilen selbst ab. Fit/Val werden über verschränkte Samples getrennt statt über Blöcke (§4–5) | Die Breite wird nicht gewählt, alle Skalen sind gleichzeitig drin. Nur $\ell_{\max}$ ist frei, und das wird über ein Genauigkeitskriterium bestimmt, nicht über ein Ergebnis (§10) |
| Die Erste-Ordnung-Kovarianz unterschätzt die Streuung bei F9 um etwa das 15-Fache, weil die Lücke im Spektrum klein ist | Neue Ambiguitätsquelle A3: Ist die propagierte Unsicherheit von $\hat c$ zu groß für eine Linearisierung, lautet das Ergebnis `AMBIGUOUS` (§6) | Feste Schwelle vorab, im Sensitivitätsraster variiert |
| Unklar war, ob ein Scheitern an der Methode liegt oder daran, dass die Daten die Unterscheidung gar nicht tragen | Ex-ante-Identifizierbarkeit pro Zelle, berechnet aus exakten Daten und dem Rauschmodell und vor dem Lauf eingefroren (§9) | Kommt aus exakten Daten, nicht aus Laufergebnissen |
| Orakel F10 schmal: $n_{\text{exact}}$ in (4,6), (5,6), (6,6) um 1 zu hoch | Orakel mit 100 Stellen. Abnahme: identisch zu 60 Stellen bis auf diese drei Einträge, die verschwinden müssen (§3) | Reine Präzision |

**Ehrliche Grenze dieser Änderungen:** Die schwache Form verschiebt die Ableitungen auf die Testfunktionen,
beseitigt die Rauschverstärkung aber nicht. Sie bleibt ein Bias-Varianz-Konflikt in der Testfunktionsbreite. v2
macht diesen Konflikt so gut wie möglich handhabbar. Wenn das bei Operatoren ab Ordnung 2 auf breiten Domänen
nicht reicht, ist das ein Kill (K5, K6), keine Einladung zu v3.

## 1. Hypothesenraum und Komplexitätsordnung

Unverändert gegenüber v1. Klassen $(r, d)$ mit $1 \le r \le 6$, $0 \le d \le 6$ (42 Klassen). Ein Operator ist
$L = \sum_{k=0}^{r}\sum_{j=0}^{d} c_{kj}\, z^j D_z^k$ mit $\|c\|_2 = 1$. Die Ordnung läuft aufsteigend nach
$C(r,d) = (r+1)(d+1)$, bei Gleichstand kleineres $r$, dann kleineres $d$.

## 2. Gate-Set F1–F10

Unverändert gegenüber v1 §2: dieselbe Tabelle, dieselben Domänen, dieselben Referenzklassen, dieselben bekannten
Gleichstände (E4 gilt weiter).

| # | $f(x)$ | breit | schmal | Referenzklasse | $C$ |
|---|---|---|---|---|---|
| F1 | $x^2$ | $[-2, 2]$ | $[1.0, 1.4]$ | (1,1) | 4 |
| F2 | $e^{1.5x}$ | $[-2, 2]$ | $[0.0, 0.4]$ | (1,0) | 2 |
| F3 | $x^{1.5}$ | $[0.2, 4]$ | $[1.0, 1.38]$ | (1,1) | 4 |
| F4 | $\log x$ | $[0.2, 4]$ | $[1.0, 1.38]$ | (2,1) | 6 |
| F5 | $x\log x$ | $[0.2, 4]$ | $[1.0, 1.38]$ | (3,1) | 8 |
| F6 | $e^{-x^2}$ | $[-2.5, 2.5]$ | $[0.5, 1.0]$ | (1,1) | 4 |
| F7 | $\sin(2x + 1/2)$ | $[-3, 3]$ | $[0.0, 0.6]$ | (2,0) | 3 |
| F8 | $x/(2+x)$ | $[0.1, 6]$ | $[1.0, 1.59]$ | (1,2) | 6 |
| F9 | $x^2 + e^x$ | $[-2, 2]$ | $[0.0, 0.4]$ | (4,0) | 5 |
| F10 | $\sin x + e^{-x^2}$ | $[-3, 3]$ | $[0.0, 0.6]$ | (5,1) | 12 |

## 2b. Kalibrier-Set K1–K6 (neu, disjunkt zum Gate-Set)

Das Set dient nur der Festlegung von $\ell_{\max}$ und $\sigma_{\text{floor}}$ und den Prüfungen in §10. Es deckt
die Ordnungen 1 bis 4 und die Koeffizientengrade 0 und 1 ab. Die schmale Domäne folgt derselben Regel wie im
Gate-Set: 10 % der Breite der breiten Domäne. Die erwarteten Referenzklassen stammen aus einer Handrechnung. Es
gilt die Klasse, die das Orakel liefert. Weicht es ab, wird das berichtet. Das Set wird deshalb **nicht**
geändert.

| # | $f(x)$ | breit | schmal | erwartete Referenzklasse | Referenzoperator (in $x$) |
|---|---|---|---|---|---|
| K1 | $\cosh x$ | $[-2, 2]$ | $[0.5, 0.9]$ | (2,0) | $D^2 - 1$ |
| K2 | $x^3$ | $[-2, 2]$ | $[0.8, 1.2]$ | (1,1) | $xD - 3$ |
| K3 | $\operatorname{Ai}(x)$ | $[-4, 2]$ | $[-1.0, -0.4]$ | (2,1) | $D^2 - x$ |
| K4 | $J_0(x)$ | $[0.5, 8]$ | $[2.0, 2.75]$ | (2,1) | $xD^2 + D + x$ |
| K5 | $x + \sin x$ | $[-3, 3]$ | $[0.5, 1.1]$ | (4,0) | $D^4 + D^2$ |
| K6 | $x e^{x} + e^{-x}$ | $[-2, 2]$ | $[-0.2, 0.2]$ | (3,0) | $(D-1)^2(D+1)$ |

## 3. Orakel

Das Verfahren ist dasselbe wie in v1 §3, mit drei Änderungen: **100 Stellen** statt 60, **mindestens 200 Punkte**
statt 120, Nullraumschwelle $10^{-60}$ relativ zum größten Singulärwert statt $10^{-35}$. Es läuft für F1–F10
und K1–K6, beide Domänen. Pflichtprüfungen:

- Die Referenzklassen von F1–F10 stimmen mit v1 überein, und $n_{\text{exact}} = 1$ in der Referenzklasse.
- Die $n_{\text{exact}}$-Tabelle über alle 42 Klassen ist für breit und schmal derselben Funktion identisch,
  **auch für F10.** Damit ist das Präzisionsartefakt von v1 erledigt. Bleibt es bestehen, ist das Orakel nicht
  abgenommen, und der Nutzer entscheidet.
- Die $n_{\text{exact}}$-Tabelle stimmt mit dem 60-Stellen-Cache von v1 überein, ausgenommen genau die drei
  bekannten F10-Einträge.
- Die symbolische bzw. hochpräzise Verifikation von $c^*$ erfolgt wie in v1, für K1–K6 analog. Ai und $J_0$
  gelten als symbolisch verifiziert, wenn SymPy $L^*[f]$ über die Definitions-ODE zu 0 vereinfacht.

## 4. Daten, Skalierung, Noise und Fit/Val-Trennung

- Gitter, Skalierung auf $z \in [-1, 1]$ und Noise sind identisch zu v1 §4: $N = 2000$, $\eta \in \{0, 0.01,
  0.05\}$, 20 Realisierungen mit Seeds $0, \dots, 19$, $\eta$ der Methode bekannt (E1).
- $\sigma_{\text{eff}} = \sqrt{(\eta \cdot \operatorname{RMS}_i \tilde f_i)^2 + \sigma_{\text{floor}}^2}$ mit
  $\sigma_{\text{floor}} = \tau \cdot \operatorname{RMS}_i \tilde f_i$. Der Faktor $\tau$ wird in §10 festgelegt
  und in Anhang A eingefroren.
- **Neu: Die Trennung in Fit und Val läuft über verschränkte Samples statt über Blöcke.** Fit sind die Samples mit
  geradem Index ($i = 0, 2, \dots$, 1.000 Punkte), Val die mit ungeradem Index (1.000 Punkte). Unter i.i.d.-Noise
  sind beide Rauschanteile unabhängig, und genau das braucht der Test. Fit und Val sehen jetzt dieselbe Region.
  Der Test prüft also Rauschkonsistenz und keine Extrapolation in andere Regionen. Die Extrapolation prüft
  weiterhin der Transfer in §8. *Grenze:* Bei korreliertem Noise wäre diese Trennung ungültig. In Gate 2A tritt
  korreliertes Noise nicht auf, in Gate 2B muss die Frage neu gestellt werden.

## 5. Weak-Matrix (multiskalig)

- Träger auf den Ebenen $\ell = 0, \dots, \ell_{\max}$: $I_{\ell,k} = [-1 + 2k/2^\ell,\; -1 + 2(k+1)/2^\ell]$ mit
  $k = 0, \dots, 2^\ell - 1$. Ebene 0 ist die ganze Domäne.
- Testfunktion auf $I_{\ell,k}$ mit Mittelpunkt $z_c$ und Halbbreite $w = 2^{-\ell}$: $u = (z - z_c)/w$ und
  $\varphi(z) = (1 - u^2)^q P_m(u)$ für $|u| \le 1$, sonst 0. Dabei ist $m = 0, \dots, M-1$, $M = 8$, $q = 14$.
- Zeilen pro Teilgitter: $R = M\,(2^{\ell_{\max}+1} - 1)$. **Bedingung:** $R \ge 2 \cdot 49$, also
  $\ell_{\max} \ge 3$ (120 Zeilen).
- Für den Eintrag gilt dieselbe Formel wie in v1:
  $A_{(\ell,k,m),(k',j)} = (-1)^{k'} \int (z^j\varphi)^{(k')}(z)\, \tilde f(z)\,dz$. Die Ableitungen sind
  analytisch und **numerisch stabil**: keine Darstellung als Monom-Polynom in $u$ oder $z$. Stattdessen
  Leibniz-Regel über die Faktoren $(z_c + w u)^j$, $(1-u)^q$, $(1+u)^q$ und $P_m(u)$. Jeder Faktor wird direkt
  abgeleitet (Potenzen über fallende Fakultäten, Legendre-Ableitungen in der Legendre-Basis mit Clenshaw-Auswertung).
  Das Integral ist die Trapezregel auf dem **jeweiligen Teilgitter** (Fit: gerade Indizes, Val:
  ungerade), mit dem außerhalb des Trägers durch 0 fortgesetzten Integranden. Die Trägerränder müssen nicht auf
  Gitterpunkten liegen, weil der Integrand dort von Ordnung $q - k' \ge 8$ verschwindet.
- Wie in v1 gilt $A c = W(c)\,\tilde f$ mit bekannter Gewichtsmatrix $W(c) = \sum_{kj} c_{kj} W_{kj}$, getrennt
  für Fit ($W_{\text{fit}}$) und Val ($W_{\text{val}}$).

## 6. Kandidat, Test und Entscheidung

Für jede Klasse in der Ordnung von §1, mit $S(c) = W_{\text{fit}}(c)\,W_{\text{fit}}(c)^\top$:

1. **Kandidat, Maximum Likelihood.** $\hat c$ minimiert
   $J(c) = (A_{\text{fit}}c)^\top S(c)^{+} (A_{\text{fit}}c)$ auf $\|c\| = 1$. Das ist genau die
   Teststatistik bis auf den Faktor $\sigma_{\text{eff}}^{-2}$. Der Kandidat wird also nach demselben Kriterium
   gewählt, nach dem er getestet wird. Berechnet wird er mit FNS (fundamental numerical scheme, Chojnacki et al.
   2000):
   - $\eta(c) = S(c)^{+} A_{\text{fit}}\, c$ und $Q(c) = [\,W_{1}^\top \eta,\ \dots,\ W_{n}^\top \eta\,]$, also
     eine Spalte pro Koeffizient;
   - $X(c) = A_{\text{fit}}^\top S(c)^{+} A_{\text{fit}} - Q(c)^\top Q(c)$. Es gilt $\nabla J = 2\,X(c)\,c$;
   - Start: SVD-Kandidat wie in v1. Iteration: $c_{t+1}$ = Eigenvektor von $X(c_t)$ zum betragskleinsten
     Eigenwert, Vorzeichen an $c_t$ ausgerichtet. Abbruch, wenn der Winkel zwischen aufeinanderfolgenden Iteraten
     unter $10^{-12}$ liegt, spätestens nach 100 Iterationen. Nicht-Konvergenz wird pro Lauf protokolliert, und
     das letzte Iterat wird verwendet;
   - Pseudoinverse von $S$ mit fester relativer Schwelle $10^{-12}$.
2. **Schätzunsicherheit** (KCR-Schranke, erste Ordnung):
   $\Sigma_{\hat c} = \sigma_{\text{eff}}^2\,\big(P\,M(\hat c)\,P\big)^{+}$ mit
   $M(c) = A_{\text{fit}}^\top S(c)^{+} A_{\text{fit}}$ und $P = I - \hat c\hat c^\top$.
3. **Residuum, Kovarianz und Test auf Val** wie in v1 §6, Schritte 2–4:
   $\rho = A_{\text{val}}\hat c$ und
   $\Sigma_\rho = \sigma_{\text{eff}}^2 W_{\text{val}}(\hat c)W_{\text{val}}(\hat c)^\top + A_{\text{val}}\Sigma_{\hat c}A_{\text{val}}^\top$.
   Die Statistik ist $T = \rho^\top\Sigma_\rho^{+}\rho$ mit $\text{dof} = \operatorname{rank}\Sigma_\rho$. Der Test
   besteht bei $T \le \chi^2_{\text{dof},\,1-\alpha}$ mit $\alpha = 0.01$.
4. Die **erste** bestandene Klasse ist die ausgewählte. Besteht keine Klasse, lautet das Ergebnis `NONE`.

**Ambiguität, jetzt drei Quellen, alle vorab fest:**

- **A1, mehrdimensionaler Nullraum:** In der ausgewählten Klasse besteht auch $c_2$ den Test aus Schritt 3, mit
  eigener Propagation nach Schritt 2. $c_2$ ist der Eigenvektor von $M(\hat c)$ zum zweitkleinsten Eigenwert,
  orthogonal zu $\hat c$.
- **A2, instabile Auswahl:** parametrischer Bootstrap wie in v1 ($B_{\text{boot}} = 50$, $\sqrt2\,\sigma_{\text{eff}}$,
  Schwelle 80 %). Die vollständige Suche einschließlich FNS läuft auf jedem Replikat.
- **A3, Linearisierung ungültig (neu):** $\sqrt{\operatorname{tr}\Sigma_{\hat c}} > 0.1$ in der ausgewählten
  Klasse. Dann ist die Erste-Ordnung-Kovarianz nicht vertrauenswürdig, und der Test kann nicht kalibriert sein.

## 7. Ergebniszustände

Unverändert gegenüber v1 §7 und E3: `CORRECT`, `AMBIGUOUS` (A1, A2 oder A3, die auslösende Quelle wird
protokolliert), `TRUE_NOT_REF`, `WRONG`, `NONE`. Die Kennzahlen pro Lauf sind dieselben wie in v1, ergänzt um die
FNS-Iterationen, ein Konvergenz-Flag und $\sqrt{\operatorname{tr}\Sigma_{\hat c}}$.

## 8. Transfer schmal → breit

Wie in v1 §8 (Diagnose, nicht entscheidend), mit der Val-Hälfte der breiten Realisierung mit Seed + 1000.

## 9. Ex-ante-Identifizierbarkeit (neu, vor dem Lauf eingefroren)

Diese Rechnung trennt „die Methode scheitert“ von „die Daten tragen die Unterscheidung unter diesem Messdesign
nicht“. Sie nutzt nur exakte Funktionswerte und das Rauschmodell, niemals Laufergebnisse. Sie wird vor dem
Gate-Lauf berechnet und als Anhang B eingefroren.

Für jede Zelle (Funktion × Domäne) und jedes $\eta \in \{0.01, 0.05\}$, mit exakten Daten und $\sigma_{\text{eff}}$
für dieses $\eta$:

- Für jede Klasse vor der Referenzklasse wird $\hat c$ per FNS auf den exakten Fit-Daten berechnet. Daraus folgt
  die Nichtzentralität $\lambda = T$ des Val-Tests auf exakten Val-Daten. Die Güte ist
  $\beta = P\big(\chi^2_{\text{dof}}(\lambda) > \chi^2_{\text{dof},\,0.99}\big)$.
- Für die Referenzklasse wird $\sqrt{\operatorname{tr}\Sigma_{\hat c}}$ aus exakten Daten berechnet.
- **Klasse der Zelle:**
  - **I** (identifizierbar): $\beta \ge 0.9$ für alle früheren Klassen und $\sqrt{\operatorname{tr}\Sigma_{\hat c}} \le 0.1$.
  - **N1** (eine einfachere Klasse ist datenkonsistent): Eine frühere Klasse hat $\beta < 0.9$.
  - **N2** (Koeffizienten unbestimmt): nicht N1, aber $\sqrt{\operatorname{tr}\Sigma_{\hat c}} > 0.1$.

**Grenze:** Das ist die Identifizierbarkeit **unter diesem Messdesign** (diese Testfunktionen, dieses $N$, dieser
Test), keine designfreie Informationsschranke. Eine N-Zelle sagt deshalb: „Mit diesem Aufbau nicht unterscheidbar“.
Ob irgendein Verfahren es könnte, sagt sie nicht.

## 10. Kalibrierung (Stufe K, nur K1–K6, vor jedem Kontakt mit F1–F10)

Die Kalibrierung legt genau zwei Größen fest, beide über Kriterien, die nicht von Suchergebnissen abhängen.
Danach folgen Prüfungen, die nur bestehen oder scheitern. Bei einem Scheitern wird nichts nachgestellt.

**K-a: $\ell_{\max}$ über die Matrixgenauigkeit.** Für jede K-Zelle (beide Domänen, beide Teilgitter) wird jede
Zeile von $A c^*$ mit exakten Daten berechnet und mit dem hochpräzisen Integral (mpmath-Quadratur der exakten
Funktion, 30 Stellen) verglichen. Fehlermaß: $e = \max_{\text{Zeilen}} |\,(Ac^*)_{\text{Trapez}} -
(Ac^*)_{\text{exakt}}\,| \,/\, (\|W(c^*)\|_{\text{Zeile}} \cdot \operatorname{RMS} f)$, also der Fehler in Einheiten
der Rauschwirkung eines Rauschens der Größe 1·RMS f. Festgelegt wird
$\ell_{\max}$ = das größte $\ell \in \{3, 4, 5\}$, für das $e \le 10^{-8}$ in allen K-Zellen gilt. Das ist sechs
Größenordnungen unter der Rauschwirkung bei 1 %. Den Clean-Fall deckt $\tau$ aus K-b ab. Erfüllt
nicht einmal $\ell = 3$ das Kriterium: Stopp, Bericht an den Nutzer.

**K-b: $\tau$ (numerischer Boden).** Clean, mit dem gewählten $\ell_{\max}$ und dem wahren $c^*$: Pro K-Zelle wird
$\tau_{\text{cell}} = \sqrt{T_1 / \chi^2_{\text{dof},\,0.99}}$ berechnet. Dabei ist $T_1$ die Val-Statistik von
$c^*$ mit $\sigma_{\text{eff}} = 1 \cdot \operatorname{RMS} f$, ohne den $\Sigma_{\hat c}$-Term. Festgelegt wird
$\tau = \max(10 \cdot \max_{\text{cells}} \tau_{\text{cell}},\; 10^{-12})$. Damit besteht der wahre Operator den
Clean-Test in jeder K-Zelle mit dem Faktor 10 Puffer in $\sigma$. Gilt $\tau > 10^{-4}$, wäre der Boden mit 1 %
Rauschen vergleichbar. Dann folgt Stopp und Bericht.

**K-c: Prüfungen (bestehen oder scheitern, ohne Nachstellen).** Breite Domäne, $\eta = 0.01$, nur K-Zellen, die
nach §9 in Klasse I fallen:

1. Kovarianz-Monte-Carlo mit 1.000 Realisierungen pro Zelle, wahrer Operator fest, getestet wie in §6 Schritt 3
   (mit $\hat c$ aus FNS). Die Ablehnungsrate muss $\le 0.03$ sein, und der Median von $T/\text{dof}$ muss in
   $[0.8, 1.25]$ liegen.
2. Bias des Schätzers über dieselben Realisierungen: $\|\bar{\hat c} - c^*\| \le 0.5 \cdot \sqrt{\operatorname{tr}
   \widehat{\operatorname{Cov}}(\hat c)}$, mit Vorzeichen ausgerichtet an $c^*$.
3. Kalibrierte Unsicherheit: Das Verhältnis empirische zu propagierter Spur liegt in $[0.5, 2]$.
4. Clean, alle K-Zellen: Die volle Suche aus §6 liefert auf der breiten Domäne `CORRECT` und auf der schmalen nie
   `WRONG`.

**Ergebnis:** Anhang A mit $\ell_{\max}$, $\tau$, allen Zahlen aus K-a bis K-c und einem Gesamtverdikt. Gegen
diesen Anhang **nimmt der Nutzer ab, bevor F1–F10 laufen.** Scheitert K-c, wird das berichtet, und der Nutzer
entscheidet (v3 oder Abbruch). An v2 wird nichts nachgestellt.

## 11. Abnahme auf dem Gate-Set (nach Anhang A, vor dem Gate-Lauf)

Hier wird nur noch Numerik und Infrastruktur geprüft. Die statistischen Prüfungen sind in K-c abgeschlossen, damit
F1–F10 nicht noch einmal zum Nachjustieren einladen.

1. Orakel nach §3.
2. Weak gegen stark: Kriterium K-a ($e \le 10^{-8}$) für alle 20 F-Zellen. Ein Scheitern wird berichtet, die
   betroffene Zelle bekommt keinen anderen Parameter.
3. Transfer (Winkel unter $10^{-10}$ bei exakter Transformation) und Determinismus (1 gegen 4 Worker bitgleich),
   wie in v1.
4. Anhang B (§9) berechnet und eingefroren.
5. Smoke-Test: eine Realisierung pro Zelle bei 1 %, nur zur Laufzeitmessung und Hochrechnung.

## 12. Gate-Kriterien

Zelle = Funktion × Domäne × Noise-Level.

**0 % (Clean):** wie in v1. Alle 10 breiten Zellen `CORRECT` mit Koeffizientenwinkel $< 10^{-6}$, und 0 schmale
Zellen `WRONG`.

**1 %, bestanden, wenn alle drei Bedingungen gelten:**
- In keiner I-Zelle sind mehr als 2 von 20 Realisierungen `WRONG`.
- Die fünf einfachen Funktionen F1, F2, F3, F6, F7 sind auf der breiten Domäne in mindestens 11 von 20
  Realisierungen `CORRECT`.
- Unter den breiten I-Zellen mit $r_{\text{ref}} \ge 2$ (Kandidaten F4, F5, F7, F9, F10) erreicht mindestens die
  Hälfte mindestens 11 von 20 `CORRECT`.

**N-Zellen:** `WRONG` wird dort berichtet, entscheidet aber nicht. In N1 ist eine einfachere Klasse datenkonsistent,
ihre Wahl ist Sparsamkeit unter Unterbestimmtheit und kein Methodenfehler. Wünschenswert ist dort `AMBIGUOUS`. Der
Anteil wird pro N-Zelle ausgewiesen.

**5 %:** Belastungstest, wird berichtet, entscheidet nicht.

**Kill-Kriterien:**
- **K1, K3 und K4:** wie in v1, mit dem Raster aus §13.
- **K2:** wie in v1, aber nur in I-Zellen.
- **K5 (neu, Ordnung ≥ 2):** Unter den breiten I-Zellen mit $r_{\text{ref}} \ge 2$ erreicht bei 1 % weniger als
  die Hälfte 11 von 20 `CORRECT`. Das ist genau die Warnung aus der v1-Abnahme: Die Methode könnte bei 1 % an
  Operatoren höherer Ordnung scheitern. Bestätigt sie sich mit den Reparaturen von v2, trägt die Idee nicht.
- **K6 (neu, das Messdesign selbst):** Mehr als eine breite Zelle mit $r_{\text{ref}} \le 3$ (F1–F8) fällt bei 1 %
  in Anhang B in N1 oder N2. Dann kann schon der ideale Test dieses Designs moderate Operatoren nicht
  unterscheiden.

Weder bestanden noch Kill: Bericht, der Nutzer entscheidet.

## 13. Sensitivitätsraster für K3

Standard: $N = 2000$, $M = 8$, $q = 14$, $\ell_{\max}$ und $\tau$ aus Anhang A, $\alpha = 0.01$,
$B_{\text{boot}} = 50$, Bootstrap-Schwelle 0.8, A3-Schwelle 0.1.

| Variante | geändert |
|---|---|
| S1 / S2 | $N = 1000$ / $4000$ |
| S3 / S4 | $M = 6$ / $12$ |
| S5 / S6 | $q = 12$ / $16$ |
| S7 / S8 | $\ell_{\max} - 1$ / $\ell_{\max} + 1$ (nicht unter 3) |
| S9 / S10 | $\alpha = 0.05$ / $0.001$ |
| S11 / S12 | $\tau / 10$ / $\tau \cdot 10$ |
| S13 / S14 | Bootstrap-Schwelle 0.7 / 0.9 |
| S15 / S16 | A3-Schwelle 0.05 / 0.2 |

Das Raster läuft auf 0 % und 1 %, beide Domänen, mit 20 Realisierungen bei 1 %. Die Klassen I/N aus Anhang B gelten
für alle Varianten unverändert.

## 14. Zur Abnahme: Entscheidungen des Nutzers

- **E5, Kalibrier-Set K1–K6 und seine Domänen.** Das Set muss vor dem ersten Lauf fest sein.
- **E6, Fit/Val-Trennung über verschränkte Samples statt über Blöcke.** Damit sind breite Testfunktionen möglich.
  Der Preis: Der Test prüft keine Extrapolation mehr zwischen Regionen, das macht nur noch der Transfer.
- **E7, Ex-ante-Klassen I/N** und die Regel, dass `WRONG` in N-Zellen nicht entscheidet. Das ist die
  folgenreichste Änderung gegenüber v1. Sie ist nur vertretbar, weil die Klassen vor dem Lauf aus exakten Daten
  entstehen. K6 verhindert, dass sich das Gate über viele N-Zellen selbst leert.
- **E8, die neuen Kill-Kriterien K5 und K6.**
- **E9, Ablauf:** Orakel → Stufe K → Anhang A → **Abnahme durch den Nutzer** → Abnahme auf dem Gate-Set (§11) →
  Gate-Lauf → Raster. Scheitert eine Stufe, wird berichtet und nicht nachgestellt.

## 15. Umsetzung und Aufwand

- Code unter `experiments/annihilator_gate2a_v2/` auf dem Branch `annihilator-discovery`. Der v1-Code unter
  `experiments/annihilator_gate2a/` bleibt **verhaltensgleich**: Gemeinsam genutzte Teile (Funktionsdefinitionen,
  Orakel) werden importiert oder kopiert, nicht verändert.
- Ergebnisse wie in v1 als CSV pro Lauf, Zusammenfassung pro Zelle und Verdikt. Anhang A und B als JSON plus
  Markdown-Tabelle, mit allen Einstellungen in jeder Zeile.
- **Aufwand: unbekannt, wird im Smoke-Test gemessen.** FNS mit 50 Bootstrap-Replikaten ist teurer als die SVD in
  v1 (v1-Hochrechnung: Hauptlauf ~49 min, Raster ~4,6 h). Bis zu einer Projektion unter 1 h läuft der Hauptlauf
  auf dem Laptop. Liegt sie darüber, wird vor dem Start gesprochen (Laufort-Regel in `CLAUDE.md`).
