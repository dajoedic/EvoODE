# Gate 2A v3 – Ergebnis der Kalibrierstufe K (Anhang A)

**Stand: 2026-10-05, 07:45. Für den Nutzer, zur Entscheidung.** Die Zahlen stammen aus 6 von 8 Teilen
(750 von 1.000 Realisierungen pro Zelle). Zwei Clean-Zellen fehlen noch: K7 breit und K8 breit (Ordnung 5 und 6).
Sie rechnen seit über 1,5 h, der Abschnitt „Nachtrag“ unten wird ergänzt, sobald sie fertig sind. **Das Gesamtverdikt
hängt nicht mehr von ihnen ab** (siehe 2.).

## 1. In einem Satz

Der reparierte Schätzer funktioniert bei Ordnung 1 und 2 einwandfrei. Bei Ordnung 3 trifft er richtig, aber die
Unsicherheitsrechnung stimmt nicht mehr genau. Ab Ordnung 4 tragen die Daten bei 1 % Rauschen die Information schon
auf breiten Domänen nicht. **Nach den vorab festgelegten Regeln besteht Anhang A nicht.** Du entscheidest, wie es
weitergeht.

## 2. Ergebnisse gegen die vorab festgelegten Kriterien (§10 der Spezifikation)

| Prüfung | Was sie prüft | Ergebnis | bestanden? |
|---|---|---|---|
| K-a | Genauigkeit der Matrix | Fehler höchstens $8\cdot10^{-10}$ bei $\ell_{\max} = 4$ (Grenze $10^{-8}$) | **ja** |
| K-b | numerischer Boden | $\tau = 3.4\cdot10^{-7}$ (Grenze $10^{-4}$), bestimmt von K8 | **ja** |
| K-c 1–3, K1 ($\cosh x$, Ordnung 2) | Test kalibriert, Schätzer unverzerrt, Unsicherheit stimmt | Ablehnung 0–2,4 %, $T$/dof 0,98–1,01, Bias $\le 2\cdot10^{-4}$, Spur-Verhältnis 0,74–1,14 | **ja** |
| K-c 1–3, K2 ($x^3$, Ordnung 1) | dito | Ablehnung 0–1,6 %, $T$/dof 0,99–1,01, Spur-Verhältnis 0,94–1,15 | **ja** |
| K-c 1–3, K6 (Ordnung 3) | dito | Ablehnung 0 %, Bias $\le 0.02$ (ok), aber $T$/dof **0,68–0,70** (Soll 0,8–1,25) und Spur-Verhältnis **2,2–7,0** (Soll 0,5–2) | **nein** |
| K-c 4, Clean | breit `CORRECT`, schmal nie `WRONG` | breit: K1, K2, K5, K6 `CORRECT`; schmal: **K7 `WRONG`** ((3,0) statt (5,0)), sonst `CORRECT` oder `AMBIGUOUS` | **nein** |

Die Werte stehen pro Teil (je 125 Realisierungen) in den JSON-Dateien. Sie schwanken zwischen den Teilen kaum. Das
Verdikt ändert sich durch die beiden fehlenden Teile nicht, weil K6 in allen sechs fertigen Teilen durchfällt und
K7 schmal schon `WRONG` ist.

**Vorab-Einstufung, breit, 1 %** (unverändert gegenüber v2):

| | K1 | K2 | K3 Airy | K4 Bessel | K5 | K6 | K7 | K8 |
|---|---|---|---|---|---|---|---|---|
| Ordnung | 2 | 1 | 2 | 2 | 4 | 3 | 5 | 6 |
| Klasse | I | I | **N1** | **N1** | **N2** | I | **N2** | I |

N1 heißt: Eine einfachere, falsche Operatorklasse erklärt die Daten genauso gut. Bei Airy und Bessel ist das ein
Operator 4. Ordnung mit konstanten Koeffizienten. N2 heißt: Die Koeffizienten sind nicht bestimmbar.

## 3. Was das in einfachen Worten bedeutet

1. **Die Reparatur der Nacht hat gewirkt.** Für Ordnung 1 und 2 macht das Verfahren jetzt genau, was es soll: Es
   findet den richtigen Operator, und sein statistischer Test irrt sich mit der vorgesehenen Rate von rund 1 %. Das
   ist der Kern der Idee, und er funktioniert dort.
2. **Bei Ordnung 3 stimmt die Richtung, aber nicht die Fehlerrechnung.** Das Verfahren trifft den Operator (Bias
   winzig). Es unterschätzt aber, wie stark das Ergebnis von Realisierung zu Realisierung schwankt, um Faktor 2 bis 7.
   Der Test ist dadurch zu vorsichtig: Er verwirft nie, ist also nicht kalibriert. Ursache ist wahrscheinlich die
   Näherung erster Ordnung, die bei größerer Unsicherheit nicht mehr trägt.
3. **Auf exakten Daten wählt das Verfahren auf der schmalen Domäne einmal eine falsche Klasse** (K7). Ursache ist der
   numerische Boden $\tau$: Er wird von der Funktion mit der höchsten Ordnung (K8) bestimmt und ist für eine schmale
   Domäne zu großzügig. Eine einfache, falsche Regel passt dann „innerhalb des Bodens“.
4. **Das Grundproblem bleibt sichtbar.** Bei 1 % Rauschen kann das Messdesign schon Operatoren 2. Ordnung mit
   polynomialen Koeffizienten (Airy, Bessel) nicht von einem einfacheren falschen Operator unterscheiden. Ab Ordnung 4
   sind die Koeffizienten unbestimmt. Das ist kein Programmierfehler, sondern die Grenze der Methode in dieser Form.

## 4. Einschätzung

- **Die Idee ist nicht widerlegt, aber stark eingegrenzt.** Sie funktioniert sauber für einfache Operatoren
  (Ordnung 1–2, konstante oder einfache Koeffizienten). Genau dort haben differenzierende Methoden wie SINDy
  allerdings auch keine großen Probleme. Ab Ordnung 3 kommen Kalibrierungsprobleme, ab Ordnung 4 Informationsgrenzen.
- **Wahrscheinlicher Ausgang auf F1–F10:** F4 ($\log x$, (2,1)) und F5 ($x\log x$, (3,1)) sind strukturell
  Airy und Bessel ähnlich, also Ordnung 2–3 mit linearen Koeffizienten. Fallen sie in Anhang B wie diese auf N1, greift
  das Kill-Kriterium **K6**. Meine Schätzung: eher ja als nein.
- **Was ein Weitermachen kosten würde:** eine v4 mit Kovarianz zweiter Ordnung oder Bootstrap-Kovarianz und einem
  Boden pro Zelle statt global. Das wäre die vierte Version in drei Tagen. Jede Version war begründet, aber das Muster
  „Abnahme scheitert, Reparatur, neue Version“ wird selbst zum Risiko. Es ist genau das Nachjustieren, vor dem die
  eigenen Regeln schützen sollen.

## 5. Deine Optionen

| Option | Was passiert | Aufwand |
|---|---|---|
| **A: Anhang B trotz gescheitertem Anhang A rechnen, nur als Diagnose** | Zeigt ohne Gate-Lauf, ob F1–F10 bei 1 % überhaupt identifizierbar sind. Fällt das K6-Kriterium, ist die Frage beantwortet, unabhängig von Kovarianz und Boden. | ~1–2 h Rechnung, keine neue Version |
| B: v4 (Kovarianz und Boden reparieren) | Neue Spezifikation, neue Kalibrierung | 1–2 Tage |
| C: Spur hier beenden | Ergebnis dokumentieren: Die Methode trägt bei 1 % Rauschen nur bis Ordnung 2 | sofort |

**Meine Empfehlung: A.** Anhang B entscheidet die wichtigste offene Frage (ist das Messdesign überhaupt in der Lage?)
billig und ohne neue Version. Fällt K6, ist B überflüssig und C die ehrliche Antwort. Besteht K6 überraschend, lohnt
sich B. Wichtig: Anhang B ist ein Einstufungsschritt aus **exakten** Daten. Er stellt nichts ein und kann das
Gate-Set deshalb nicht „verbrauchen“. Die Gate-Kriterien selbst würden dabei nicht ausgewertet.

## 6. Wo die Daten liegen

- Teilergebnisse: `experiments/annihilator_gate2a_v3/results/calibration/appendix_A_part_*_of_8.json`
- Logs: `experiments/annihilator_gate2a_v3/results/calibration/logs/`
- Abgebrochener Lauf mit dem Vorzeichenfehler: `results/calibration/aborted_2026-10-05_sign_bug/`
- Chronologie: `DIARY.md` vom 04. und 05.10.

## Nachtrag 1: Anhang B (Option A, vom Nutzer gewählt am 05.10.)

**Ergebnis: Das Kill-Kriterium K6 würde auslösen.** Anhang A ist nicht bestanden. Anhang B ist deshalb eine Diagnose
und kein Gate-Ergebnis, die Antwort ist aber eindeutig. Gerechnet wurde am 05.10. von 09:18 bis 09:46 mit
$\ell_{\max} = 4$, $\tau = 3.4\cdot10^{-7}$ und AML (L-BFGS). Daten:
`experiments/annihilator_gate2a_v3/results/appendix_B/appendix_B.{json,md}`.

**Breite Domäne, 1 % Rauschen:**

| | F1 $x^2$ | F2 $e^{1.5x}$ | F3 $x^{1.5}$ | F4 $\log x$ | F5 $x\log x$ | F6 $e^{-x^2}$ | F7 $\sin$ | F8 $x/(2+x)$ | F9 $x^2+e^x$ | F10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Referenz $(r,d)$ | (1,1) | (1,0) | (1,1) | (2,1) | (3,1) | (1,1) | (2,0) | (1,2) | (4,0) | (5,1) |
| Klasse | I | I | I | **N1** | **N1** | I | I | **N1** | **N1** | **N1** |
| konkurrierende falsche Klasse | | | | (4,0) | (6,0) | | | (4,0) | (3,0) | (3,2) |

K6 zählt die breiten Zellen mit $r_{\text{ref}} \le 3$ (F1–F8), die in N1 oder N2 fallen. Das sind **3** (F4, F5, F8),
erlaubt ist höchstens 1.

**Bei 5 %** fällt zusätzlich F3 auf N1. **Schmal** ist fast alles N1, nur F2 bleibt bei 1 % und 5 % I, F7 bei 1 % I.

**Lesart.** In allen N1-Zellen hat die konkurrierende falsche Klasse eine Güte von $\beta \approx 0.01$, also gleich
$\alpha$. Der ideale Test kann sie auf exakten Daten praktisch gar nicht verwerfen. Ein Operator mit **konstanten**
Koeffizienten höherer Ordnung, etwa (4,0), approximiert $\log x$, $x\log x$ und $x/(2+x)$ im Rahmen von 1 % Rauschen
genauso gut wie der wahre Operator mit **polynomialen** Koeffizienten. Bei 1 % Rauschen tragen die Daten keine
Information darüber, ob die Koeffizienten von $x$ abhängen. Genau diese Abhängigkeit war aber der Kern der Idee
(Funktionsfamilien jenseits von Exponentialpolynomen erkennen).

**Was bleibt:** Bei Operatoren erster Ordnung (Potenzen, Exponentialfunktionen, Gauß) und bei Sinus funktioniert das
Verfahren. Dort hat es auch einen kalibrierten Test (K1, K2 in Anhang A). Das ist aber gerade der Bereich, den
bestehende Methoden schon gut abdecken.

**Nach den eigenen, vorab festgelegten Regeln** (v2 §12, K6): Gate 2A ist in dieser Form nicht bestehbar. K6 ist ein
Kill, gemeint als „beendet oder zwingt zur grundsätzlichen Neubewertung“. Die Neubewertung müsste beim
Messdesign ansetzen, also bei mehr Daten, weniger Rauschen oder anderen Testfunktionen, nicht bei einer v4 des
Schätzers. Ob das lohnt, entscheidet der Nutzer.

## Nachtrag 2: Clean-Zellen K7 und K8 breit

K7 breit ist fertig (Teil 4). K8 breit lief um 09:45 seit fast vier Stunden noch. Beide ändern weder das Verdikt
zu Anhang A noch Anhang B.
