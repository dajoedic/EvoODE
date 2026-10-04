# Gate 2A v1 → v2: Was geändert wurde und warum

**Stand 2026-10-04.** Begleitdokument zu `docs/GATE_2A_v2.md`. Es erklärt jede Änderung gegenüber
`docs/GATE_2A.md` (v1): welcher Befund sie ausgelöst hat, warum sie die richtige Antwort ist und welchen Preis sie hat.
Dieses Dokument wird nicht fortgeschrieben. Spätere Befunde gehören ins `DIARY.md`. Die Ergänzungen nach dem
externen Review vom 04.10. sind in §3.11 gesammelt und in den betroffenen Abschnitten eingearbeitet.

## 1. Ausgangslage

v1 wurde am 04.10. eingefroren und implementiert (Branch `9d6a4d0`). Vor dem eigentlichen Gate-Lauf steht eine
Abnahme. Sie prüft, ob die Bausteine korrekt arbeiten. Diese Abnahme scheiterte an F4 ($\log x$, Ordnung 2) und F9
($x^2 + e^x$, Ordnung 4). Der Gate-Lauf wurde deshalb nicht gestartet. **Es gibt kein Gate-Ergebnis von v1**, also
auch keines, das v2 „überschreibt“.

Bestanden haben:

| Prüfung | Ergebnis |
|---|---|
| Orakel, 60 Stellen | alle 20 Referenzklassen korrekt; F1–F9 symbolisch exakt, F10 auf $10^{-58}$ |
| Transfer schmal → breit | Winkel 0 |
| Determinismus | 1 gegen 4 Worker bitgleich |
| Kovarianz-Monte-Carlo F2 | Ablehnungsrate 0,008 (Soll ≤ 0,03), $T/\text{dof}$ 1,00, Spur-Verhältnis 0,99 |

Das letzte Ergebnis ist das wichtigste. Wo die Matrix sauber ist, funktioniert die statistische Kernidee
quantitativ: Der wahre Operator wird mit der vorgesehenen Rate von etwa 1 % verworfen. Ohne die propagierte
Schätzunsicherheit von $\hat c$ läge die Rate bei 30 %.

Gescheitert sind drei Dinge, und alle drei liegen im Aufbau, nicht in der Idee:

1. **Matrixgenauigkeit.** Relatives Residuum des wahren Operators auf exakten Daten bei $N = 1000 / 8000$:
   F2 $3\cdot10^{-10} / 2\cdot10^{-10}$, F4 $2\cdot10^{-8} / 7\cdot10^{-9}$, F9 $3\cdot10^{-3} / 7\cdot10^{-5}$. Der
   Clean-Boden $10^{-8}$ liegt darunter, deshalb wird schon F2 auf exakten Daten `AMBIGUOUS`.
2. **Schätzerbias.** Bei F4 mit 1 % Rauschen ist $\hat c$ um das 47-Fache seiner Streuung verschoben.
3. **Identifizierbarkeit.** Bei F9 mit 1 % ist $\hat c$ praktisch zufällig. Schon clean ist der Abstand der beiden
   kleinsten Singulärwerte nur 22, und die Kovarianz erster Ordnung unterschätzt die Streuung um etwa das 15-Fache.

## 2. Leitregel für alle Änderungen

**Keine Änderung darf an F1–F10 eingestellt werden.** Sonst passt man das Gate an das eigene Testset an, und sein
Bestehen wäre wertlos. Jede Änderung muss deshalb einen von drei Ursprüngen haben:

- (a) eine Herleitung, die von keinem Testergebnis abhängt (Numerik, Statistik des eigenen Rauschmodells);
- (b) eine Messung auf dem **disjunkten Kalibrier-Set** K1–K6, das in v2 neu hinzukommt;
- (c) eine Regel, die vor jedem Lauf feststeht und nur exakte Daten verwendet.

Die Diagnose der v1-Abnahme hat F4 und F9 angesehen, und das lässt sich nicht rückgängig machen. Diese Diagnose hat
aber nur **Mechanismen** benannt (Rundung, Bias, Rauschverstärkung). Sie hat keinen Parameter ausgewählt. Die
Messung, die die Matrixreparatur bestätigt hat (§3.1), lief bewusst auf K5 und nicht auf F9.

## 3. Die Änderungen im Einzelnen

### 3.1 Matrixgenauigkeit: stabile Auswertung und $q = 14$

**Befund.** Der Fehler der Weak-Matrix wächst steil mit der Ableitungsordnung.

**Ursachenanalyse (04.10., auf K5 = $x + \sin x$, Ordnung 4, breite Domäne).** Relatives Residuum
$\|Ac^*\|/\|A\|$ für $N = 1000 / 2000 / 4000 / 8000$, Blockbreite 0,25 wie in v1:

| Auswertung | $q$ | $M$ | Residuum | Lesart |
|---|---|---|---|---|
| Monome (v1) | 8 | 16 | $3\cdot10^{-4}$ → $7\cdot10^{-6}$, ab 4.000 flach | gemischt |
| Monome | 14 | 16 | $5\cdot10^{-3}$ → $3\cdot10^{-3}$, flach | **Rundung dominiert** |
| stabil | 8 | 16 | $3\cdot10^{-4}$ → $7\cdot10^{-9}$, etwa 5. Ordnung in $N$ | **Quadratur dominiert** |
| stabil | 14 | 16 | $2\cdot10^{-10}$ → $8\cdot10^{-11}$ | beides behoben |
| stabil, Breite 1 | 14 | 8 | $\sim10^{-13}$ | Rundungsboden |

Zwei unabhängige Defekte haben sich also überlagert:

- **Rundung.** v1 stellt jede Testfunktion samt Faktor $z^j$ als Monom-Polynom vom Grad ~37 dar und leitet es
  ab. Die Koeffizienten sind groß und haben wechselnde Vorzeichen, deshalb löscht sich bei der Auswertung fast
  alles aus. Ein höheres $q$ allein macht das schlimmer, siehe Zeile 2.
- **Quadratur.** Die Trapezregel ist für einen kompakt getragenen Integranden nur so genau, wie er am Trägerrand
  glatt ist. $(1-u^2)^q$, $k$-mal abgeleitet, verschwindet am Rand nur noch von Ordnung $q - k$. Bei $q = 8$ und
  $k = 6$ ist der Integrand nur noch $C^1$.

**Änderung.** (i) Die Ableitungen werden stabil ausgewertet, über die Leibniz-Regel auf den Faktoren
$(z_c + wu)^j$, $(1-u)^q$, $(1+u)^q$ und $P_m(u)$. Jeder Faktor wird direkt abgeleitet, die Legendre-Ableitungen
mit Clenshaw in der Legendre-Basis. (ii) $q = 14$, damit jeder Integrand bis $k = 6$ global $C^7$ ist.

**Warum das zulässig ist.** Beides ist Numerik nach Lehrbuch. Bestätigt wurde es auf dem Kalibrier-Set.

**Preis.** Ein größeres $q$ konzentriert die Testfunktion zur Trägermitte hin, ihre effektive Breite sinkt
ungefähr wie $1/\sqrt q$. Das verstärkt das Rauschen etwas. Die multiskaligen Träger in §3.4 gleichen das aus.

**Ehrlich zu benennen:** Der erste v2-Entwurf hat nur $q = 14$ enthalten und den Matrixfehler allein der Quadratur
zugeschrieben. Die K5-Messung hat gezeigt, dass das nur die halbe Wahrheit war. Die stabile Auswertung wurde **vor
dem Einfrieren** ergänzt. Den Hinweis auf die Monomdarstellung hatte der WP-G2A-c-Auftrag schon als Vermutung
enthalten.

### 3.2 Numerischer Boden: gemessen statt gesetzt

**Befund.** $\sigma_{\text{floor}} = 10^{-8} \cdot \operatorname{RMS} f$ war eine gesetzte Konstante unterhalb des
tatsächlichen Matrixfehlers. Auf exakten Daten verwarf der Test deshalb sogar den wahren Operator, und F2 wurde
`AMBIGUOUS`. Clean-Ergebnisse wären reine Numerik-Artefakte gewesen.

**Änderung.** $\tau$ (Boden relativ zu $\operatorname{RMS} f$) wird auf dem Kalibrier-Set gemessen. Gesucht ist das
kleinste $\tau$, bei dem der wahre Operator den Clean-Test in **jeder** K-Zelle besteht. Darauf kommt der Faktor
10 als Puffer. Liegt $\tau$ über $10^{-4}$, wäre der Boden mit dem 1-%-Rauschen vergleichbar. Dann wird gestoppt.

**Warum das zulässig ist.** Die Messung verwendet den **wahren** Operator, nicht das Suchergebnis, und nur K-Daten.

**Preis.** Clean heißt in v2 „bis auf den gemessenen numerischen Boden“, nicht „exakt“. Das ist ehrlicher als v1,
weil v1 eine Exaktheit behauptet hat, die die Numerik nicht hergab.

### 3.3 Schätzer: approximierte Maximum Likelihood (FNS/AML) statt einfacher SVD

**Befund.** Bei F4 mit 1 % ist $\hat c$ um das 47-Fache seiner Streuung verschoben. Der kleinste Singulärvektor
von $A_{\text{fit}}$ ist der Total-Least-Squares-Schätzer. Er ist nur dann konsistent, wenn die Fehler in $A$
unabhängig und gleich groß sind. Hier sind sie das nicht. Spalten höherer Ableitungsordnung tragen viel mehr
Rauschen ($\sim w^{-k}$), und alle Spalten hängen am selben Rauschvektor, sind also korreliert.

**Änderung.** $\hat c$ minimiert $J(c) = (A_{\text{fit}}c)^\top S(c)^+ (A_{\text{fit}}c)$ mit
$S(c) = W(c)W(c)^\top$. Berechnet wird das mit FNS (Chojnacki et al. 2000), einer Fixpunkt-Eigenwertiteration
mit SVD-Start. Begrifflich genau: $J$ ist die **AML-Kostenfunktion** (approximated maximum likelihood) eines
heteroskedastischen Errors-in-Variables-Modells, eine Näherung erster Ordnung an die volle Likelihood. FNS findet
einen stationären Punkt von $J$, nicht das exakte ML-Optimum. Die Unsicherheit von $\hat c$ ist die
**asymptotische Kovarianz erster Ordnung in KCR-Form** $\sigma^2 (PMP)^+$, also eine Näherung für kleine
Störungen und keine exakte Kovarianz.

**Warum das die richtige Wahl ist.** $J$ ist bis auf $\sigma^{-2}$ dieselbe Statistik, mit der das Gate testet. Das
Rauschmodell $Ac = W(c)\tilde f$ steht schon in v1. v2 zieht daraus nur die Konsequenz für die Schätzung, nicht
erst für den Test. Einen freien Parameter gibt es dabei nicht. Die Diagnose hatte nur einen einfacheren
gewichteten Ansatz (GTLS) probiert: Der senkte den Bias von 47 auf 2,3 Streuungen, beseitigte ihn aber nicht. Der
AML-Schätzer ist die konsequente Version davon. Seine Wirkung ist **noch nicht gemessen**. K-c prüft sie
auf dem Kalibrier-Set mit einer festen Schwelle: Bias höchstens eine halbe Streuung.

**Preis.** Rechenzeit, weil jeder Kandidat jetzt eine Iteration ist. FNS ist streng genommen eine nichtlineare
Optimierung, die v1 ausgeschlossen hat. Sie bleibt aber eine reine Eigenwertiteration ohne Schrittweite oder
Startwertsuche, und die Spezifikation nennt sie ausdrücklich als einzige Ausnahme.

### 3.4 Testfunktionsbreite: alle Skalen gleichzeitig

**Befund.** Bei F9 und 1 % ist der Operator unter v1 nicht identifizierbar. Die Testfunktionen haben eine feste
Blockbreite von 0,25 in $z$. Eine Ableitung der Ordnung $k$ auf der Testfunktion skaliert mit $w^{-k}$, bei
$k = 4$ also mit Faktor ~4.000 gegenüber domänenbreiten Testfunktionen.

**Das ist der Kern des Problems und nicht nur ein Baufehler.** Die schwache Form verschiebt die Ableitungen auf die
Testfunktionen, beseitigt die Rauschverstärkung aber nicht. Breite Testfunktionen verstärken das Rauschen wenig,
mitteln aber lokale Struktur weg. Schmale lösen lokal auf und verstärken das Rauschen stark.

**Änderung, zweiteilig.**
1. **Multiskalige Träger.** Testfunktionen auf den Ebenen $\ell = 0, \dots, \ell_{\max}$, von der ganzen Domäne
   bis $2^{-\ell_{\max}}$, alle zugleich in derselben Matrix. Der AML-Schätzer aus §3.3 wertet jede Zeile nach
   ihrem Rauschen. Verrauschte schmale Zeilen zählen also automatisch wenig. **Damit muss niemand eine Breite
   wählen**, die Gewichtung folgt aus dem Rauschmodell. Frei bleibt nur $\ell_{\max}$, und das wird über ein
   reines Genauigkeitskriterium bestimmt: die feinste Ebene, auf der die Quadratur noch auf $10^{-8}$ genau ist.
   Ob dabei etwas Richtiges gefunden wird, spielt für diese Wahl keine Rolle.
2. **Fit/Val über verschränkte Samples.** In v1 waren Fit und Val abwechselnde Blöcke. Das erzwang schmale
   Träger, denn ein domänenbreiter Träger überdeckt beide Blockarten. In v2 sind Fit die geraden und Val die
   ungeraden Samples. Bei unabhängigem Rauschen pro Sample sind beide Rauschanteile unabhängig, und genau das
   braucht der Test.

**Preis.** (a) Der Val-Test prüft keine Extrapolation in andere Regionen mehr, sondern Rauschkonsistenz in
derselben Region. Extrapolation prüft nur noch der Transfer schmal → breit, und der war schon in v1 eine Diagnose.
(b) Bei korreliertem Rauschen wäre die Trennung ungültig. In Gate 2A gibt es das nicht, in Gate 2B muss es neu
entschieden werden. Beides steht in der Spezifikation als Grenze.

### 3.5 Ambiguität A3: projektive Unsicherheit zu groß

**Befund.** Bei F9 unterschätzte die Kovarianz erster Ordnung die tatsächliche Streuung von $\hat c$ um etwa das
15-Fache. Die Linearisierung setzt voraus, dass die Störung klein ist gegenüber dem Abstand der Singulärwerte. Ist
sie das nicht, ist der Test nicht mehr kalibriert. Er verwirft dann zu oft oder zu selten, ohne dass man es sieht.

**Änderung.** Liegt die projektive Winkelunsicherheit $\theta_{\hat c} = \sqrt{\operatorname{tr}\Sigma_{\hat c}}$
über 0,1 rad, lautet das Ergebnis `AMBIGUOUS`.

**Warum die Größe eindeutig ist (nach dem Review präzisiert).** Ein Operator ist nur bis auf einen Faktor bestimmt,
$c \sim \alpha c$. Eine Unsicherheit „von $c$“ ist deshalb erst dann eindeutig, wenn Repräsentant und Koordinaten
feststehen. v2 legt beides fest:
- Repräsentant ist $\|c\|_2 = 1$ in den Koeffizienten zur Basis $z^j D_z^k$ auf $z \in [-1, 1]$, ohne
  Spaltenskalierung.
- $\Sigma_{\hat c}$ wird durch $P = I - \hat c\hat c^\top$ in den Tangentialraum der Einheitssphäre projiziert.

Dort ist $\theta_{\hat c}$ dimensionslos und für kleine Werte die mittlere quadratische Winkelabweichung in Radiant.
Die Größe bleibt basisabhängig, mit Legendre- statt Monomkoordinaten ergäbe sich ein anderer Wert. Deshalb ist die
Basis festgeschrieben.

**Warum das zulässig ist.** **Die Schwelle 0,1 rad ist eine vorab festgelegte operative Heuristik.** Sie ist keine
allgemeine mathematische Grenze dafür, ab wann die Linearisierung gilt. Eine solche Grenze hängt vom Abstand im
Spektrum und von der Krümmung ab, und eine einzelne Zahl gibt sie nicht her. Die Wirkung der Schwelle wird im
Sensitivitätsraster mit 0,05 und 0,2 geprüft (K3-Kill bei Instabilität). Sie entspricht der Kernforderung der Idee: Die Methode soll sagen, wenn die Daten nicht
reichen, statt zwanghaft eine Gleichung auszugeben.

### 3.6 Ex-ante-Identifizierbarkeit (Anhang B)

**Problem.** v1 konnte nicht unterscheiden, ob ein Scheitern an der Methode liegt oder daran, dass die Daten die
Unterscheidung gar nicht tragen. Auf schmalen Domänen sehen verschiedene Funktionsfamilien absichtlich lokal
ähnlich aus, so war das Gate gebaut. Wählt die Methode dort bei 1 % eine einfachere Klasse, die im Rahmen des
Rauschens genauso passt, zählte v1 das als `WRONG`. Im Extremfall löste es Kill K2 aus.

**Änderung.** Vor dem Gate-Lauf wird jede Zelle aus **exakten** Daten und dem Rauschmodell eingestuft. Für jede
einfachere Klasse wird berechnet, mit welcher Wahrscheinlichkeit der ideale Test sie verwirft (Güte aus der
Nichtzentralität). Für die Referenzklasse wird berechnet, ob A3 schon im Idealfall auslösen würde. Daraus folgen
drei Klassen: I (identifizierbar), N1 (eine einfachere Klasse ist datenkonsistent) und N2 (Koeffizienten
unbestimmt). `WRONG` in N-Zellen wird berichtet, entscheidet aber nicht.

**Warum das die folgenreichste Änderung ist und warum sie trotzdem vertretbar ist.** Sie nimmt Zellen aus der
Wertung. Gefährlich wäre das, wenn die Einstufung aus Laufergebnissen käme. Sie kommt aber aus exakten Daten und
steht vor dem Lauf fest. Zwei Sicherungen verhindern, dass sich das Gate auf diesem Weg leert:

- **K6:** Fällt mehr als eine breite Zelle mit Ordnung ≤ 3 bei 1 % in N1 oder N2, ist das ein Kill. Dann kann
  schon der *ideale* Test dieses Designs moderate Operatoren nicht unterscheiden.
- Die fünf einfachen Funktionen müssen weiterhin breit in 11 von 20 Realisierungen `CORRECT` sein, egal wie sie
  eingestuft sind.

**Grenze.** Das ist Identifizierbarkeit **unter diesem Messdesign**, keine designfreie Informationsschranke.

### 3.7 Kalibrier-Set K1–K8 und Stufe K

**Warum es das Set braucht.** Zwei Größen ($\ell_{\max}$, $\tau$) müssen aus Daten bestimmt werden, und die
statistischen Prüfungen (Kovarianz, Bias) brauchen Funktionen, an denen man sie messen darf. Täte man das auf
F1–F10, wäre es eine Kalibrierung am Gate-Set.

**Zusammensetzung.** $\cosh x$ (2,0), $x^3$ (1,1), Airy $\operatorname{Ai}(x)$ (2,1), Bessel $J_0(x)$ (2,1),
$x + \sin x$ (4,0), $x e^x + e^{-x}$ (3,0), **nach dem Review ergänzt** $1 + \sin x + \cos 2x$ (5,0) und
$\sin x + \sin 2x + \sin 3x$ (6,0). Das deckt die Ordnungen 1 bis 6 und die Koeffizientengrade 0 und 1 ab, mit
Spezialfunktionen, die in F1–F10 nicht vorkommen. Die Klassen von K1–K6 stammen aus einer Handrechnung, das Orakel
bestätigt sie. Weicht es ab, wird das berichtet, das Set aber nicht geändert. K7 und K8 hat Claude vor der Aufnahme
mit einem Hochpräzisions-Nullraum bestätigt (50 Stellen, beide Domänen, Dimension 1).

**Warum K7 und K8 (Review).** Der Suchraum reicht bis Ordnung 6, und gerade hohe Ableitungsordnungen sind numerisch
kritisch. Ohne Kalibrierfälle dort ließe sich ein späteres Scheitern bei F10 (Ordnung 5) wieder nicht eindeutig der
Methode oder der Numerik zuordnen, also genau die Lage, in der v1 gescheitert ist. **K7 und K8 prüfen
ausschließlich die numerische Infrastruktur:** Matrixgenauigkeit (K-a), Boden (K-b) und die Clean-Suche
(K-c Punkt 4). In die statistischen Prüfungen K-c 1–3 gehen sie nicht ein, und sie optimieren keine Recovery-Regel.
Sie wirken auf $\ell_{\max}$ und $\tau$, weil beide als Maximum bzw. Minimum über alle K-Zellen definiert sind. Das
ist gewollt: Die Numerik muss auch für die höchsten Ordnungen des Suchraums tragen.

**Wichtigste Verfahrensänderung.** Die statistischen Prüfungen, an denen v1 gescheitert ist (Monte-Carlo, Bias),
laufen in v2 **nur noch auf dem Kalibrier-Set**. Auf F1–F10 wird nur noch Numerik und Infrastruktur geprüft. Der
Grund: Scheitert eine statistische Prüfung auf dem Gate-Set, verführt das genau zu dem Nachjustieren, das die
Leitregel verbietet. Scheitert sie auf dem Kalibrier-Set, wird berichtet, und es gibt v3 oder einen Abbruch. Ein
stilles Nachstellen gibt es nicht.

**Ablauf.** Orakel → Stufe K → Anhang A → **Abnahme durch den Nutzer** → Abnahme auf dem Gate-Set → Anhang B →
Gate-Lauf → Raster.

### 3.8 Neue Kill-Kriterien K5 und K6

- **K5:** Unter den breiten I-Zellen mit Ordnung ≥ 2 erreicht bei 1 % weniger als die Hälfte 11 von 20 `CORRECT`.
  Damit wird die Warnung aus der v1-Abnahme prüfbar: „Die Methode scheitert schon bei 1 % an Operatoren ab
  Ordnung 2.“ Bestätigt sie sich trotz aller Reparaturen, trägt die Idee nicht.
- **K6:** siehe §3.6.

v2 enthält damit **in mehreren Richtungen strengere Kill-Kriterien**. v1 hätte F4 und F9 nur über „höchstens 2 von 20
`WRONG`“ bewertet und ein flächiges `NONE` oder `AMBIGUOUS` bei höherer Ordnung toleriert. **Insgesamt ist v2 aber
nicht monoton strenger:** Die N-Zellen aus §3.6 nehmen Fälle aus der Entscheidung, die v1 gewertet hätte. v2 ist
anders strukturiert und gezielter, nicht einfach härter.

### 3.9 Orakel mit 100 Stellen

**Befund.** Bei F10 schmal war die Nullraumdimension in drei hohen Klassen um 1 zu hoch, verglichen mit breit.
Mathematisch ist sie identisch (Restriktion analytischer Funktionen), also war das ein Präzisionsartefakt.

**Änderung.** 100 Stellen, mindestens 200 Punkte, Schwelle $10^{-60}$. Abnahme: Die drei Einträge verschwinden, und
sonst ist alles identisch zum 60-Stellen-Cache. Kostet nur Rechenzeit.

### 3.10 Sensitivitätsraster

Angepasst an die neuen Parameter. $B$ entfällt, dafür kommen $\ell_{\max} \pm 1$, $\tau \cdot 10^{\pm1}$ und die
A3-Schwelle dazu. Es sind jetzt 16 statt 11 Varianten. K3 ist unverändert: Ändert eine Variante das Clean-Ergebnis
oder die 1-%-Mehrheiten um mehr als 2 Zellen, folgt ein Kill.

### 3.11 Externes Review vom 04.10. und was daraus folgte

Das Review hielt die Revision für überzeugend und nicht für nachträgliches Schönrechnen, weil v1 schon in der Abnahme
scheiterte und kein Gate-Lauf stattfand. Es verlangte vor dem Freeze drei Änderungen und zwei kleinere. Alle sind
umgesetzt, bevor irgendetwas aus Stufe K gerechnet wurde. Eine laufende Codex-Implementierung wurde dafür
angehalten.

| Punkt | Umsetzung |
|---|---|
| FNS nicht „Maximum Likelihood“ nennen, KCR nicht als exakt darstellen | FNS/AML, heteroskedastischer EIV-Schätzer, asymptotische Kovarianz erster Ordnung (§3.3; Spezifikation §0a, §6) |
| A3 eindeutig definieren | projektive Winkelunsicherheit mit festgelegtem Repräsentanten, festgelegter Basis und Tangentialraum; 0,1 rad als operative Heuristik (§3.5; Spezifikation §6) |
| Kalibrier-Set bis Ordnung 6 | K7 (5,0) und K8 (6,0), nur für die numerische Infrastruktur (§3.7; Spezifikation §2b, §10) |
| „strenger als v1“ abschwächen | „in mehreren Richtungen strengere Kill-Kriterien, insgesamt nicht monoton strenger“ (§3.8; Spezifikation §0a) |
| F1–F10 nicht mehr unberührt | offen benannt; eine Erfolgsbehauptung braucht später ein neues, versiegeltes Funktions-Hold-out-Set (§6 unten; Spezifikation §0a) |

## 4. Was unverändert bleibt

Die Fragestellung, der Hypothesenraum (42 Klassen), die Komplexitätsordnung, F1–F10 mit Domänen und Referenzklassen,
das Rauschmodell, $\eta$ bekannt (E1), der Val-Test selbst, A1 und A2, die Ergebniszustände einschließlich der
Trennung `TRUE_NOT_REF` (E3), das Clean-Kriterium, die 1-%-Kriterien für die fünf einfachen Funktionen, sowie K1,
K3 und K4.

## 5. Was das für die Idee heißt

- **Unberührt:** der Kern. Gesucht wird der minimale Annihilator als Strukturdiagnose, und eine statistisch
  begründete Entscheidung darf auch „die Daten reichen nicht“ lauten.
- **Gestützt:** Der statistische Teil funktioniert quantitativ, wo die Numerik sauber ist (F2).
- **Abgeschwächt:** die Erwartung, dass die schwache Form das Rauschproblem *grundsätzlich* löst. Die
  Rauschverstärkung $\sim w^{-k}$ bleibt ein Bias-Varianz-Konflikt, wie bei Weak-SINDy. Ein Vorteil gegenüber
  differenzierenden Methoden kann nur noch quantitativ sein: breite Träger und eine optimale Gewichtung. Grundsätzlich
  anders ist die schwache Form nicht.
- **Wo das Risiko jetzt liegt:** bei Operatoren ab Ordnung 2 unter 1 % Rauschen auf breiten Domänen. Genau dafür
  gibt es K5 und K6. v2 ist so gebaut, dass ein Scheitern dort eindeutig ist und nicht in eine v3 ausweicht.

## 6. Grenze der Aussagekraft

F1–F10 sind seit der v1-Diagnose nicht mehr vollständig unberührt, weil F4 und F9 angesehen wurden. Für einen
internen Kill-Test ist das vertretbar: Daraus wurden nur Mechanismen benannt, alle Parameter kommen aus dem
Kalibrier-Set, und alles ist dokumentiert. **Besteht Gate 2A v2 und soll daraus eine wissenschaftliche
Erfolgsbehauptung werden, wird sie auf einem neuen, versiegelten Funktions-Hold-out-Set bestätigt.** Dieses Set wird
vor diesem Schritt festgelegt und bleibt bis dahin ungesehen. Für die späteren Gates mit ODE-Systemen gibt es ein
solches verschlossenes Prüfset bereits (Systeme 4/49/59/62). Für Gate 2A muss es noch entstehen.
