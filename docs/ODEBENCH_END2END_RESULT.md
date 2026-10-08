# ODEBench End-to-End: Ergebnis von v1 und v2

**Stand: 2026-10-08.** Bericht nach `docs/ODEBENCH_END2END.md` §9 (v1) und `docs/ODEBENCH_END2END_v2.md`.
**Deskriptiv, ohne Entscheidungsregel.** Über das weitere Vorgehen entscheidet der Nutzer. Vollständig berichtet:
alle Systeme, beide Rauschstufen, alle Methoden und beide Versionen.

## 1. Was gelaufen ist

- **Kette** `run_chain_e2e.ps1`: v2 von 07.10. 16:37 bis 08.10. 02:18, danach die Fortsetzung von v1 bis 03:29. Der
  Laptop stand von 17:02 bis 22:03 im Standby still.
- **Records:** je Version 216 von 216 (4 Systeme × 6 Realisierungen × 3 Fits × 3 Methoden), `DONE`, keine
  gescheiterten Tasks.
- **v2:** Annihilator mit 200 Abschnitten und GCV-Glättungsspline, alle 72 Fits neu gerechnet. Baselines: 78 Records
  aus v1 übernommen, 66 mit demselben Code neu gerechnet.
- **v1:** interpolierender kubischer Spline. Die 113 Records vom 07.10. und die 103 der Fortsetzung bilden zusammen
  den vollständigen Lauf.
- **Systeme:** 3 Logistik, 7 Gompertz, 19 Logistik mit Ernte, 21 SIR. Bei System 19 haben die Baselines keine
  darstellbare wahre Termmenge.
- **Meldungen** „lsoda callback failed“ in `main.err` und `resume.err` gehören zu Integrationen, die bei der Auswahl
  oder Bewertung scheitern. Sie zählen nach v1 §4 und §7 als Fehler $\infty$ bzw. $R^2 = -\infty$. In den Tabellen
  stehen sie in der Spalte „Integr. gescheitert“.

## 2. Technischer Befund: W-SINDy ist nicht reproduzierbar

v2 nahm an, dass die Baselines deterministisch laufen (v2 „Was übernommen wird“). Für SINDy stimmt das: Alle 72
SINDy-Records sind in v1 und v2 bitgleich, auch die neu gerechneten. **Für W-SINDy stimmt es nicht.**

- pysindy 2.1.0 zieht in `WeakPDELibrary` die Zentren der Testfunktionen mit dem globalen `np.random`. Einen Seed
  setzt weder pysindy noch `end2end.py`. Das Ergebnis hängt deshalb davon ab, was der Worker-Prozess vorher gerechnet
  hat.
- Alle 33 W-SINDy-Records, die v2 neu gerechnet hat (System 19 mit 1 %, System 21), weichen von der v1-Fortsetzung
  ab, meist schon in der gewählten Schwelle. Die 39 übernommenen (Systeme 3 und 7, System 19 rauschfrei) sind
  identisch, weil es dieselbe Datei ist.
- Der Test aus WP-E2E-B prüfte die Gleichheit an einem Task. Für W-SINDy ist das kein Beleg.

**Folgen:**

- Jede W-SINDy-Zahl ist **eine** Ziehung der Testfunktionen.
- Für die Systeme 19 und 21 liegen zwei unabhängige Ziehungen vor (§3.3). Sie zeigen, wie stark das Ergebnis
  schwankt: bei 19 mit 1 % etwa Rekonstruktion 16/20 gegen 18/20.
- Unterschiede von ein bis drei Fällen zwischen Methoden liegen damit im Bereich dieser Schwankung.

Die Smoke-Test-Ergebnisse dürften genauso betroffen sein. Das ändert dort nichts am Verdikt, weil es an Bedingung A
(nur Annihilator) hing.

## 3. Funktionsgüte und Struktur

**Lesehilfe:**

- **Rek.:** Anteil $R^2 \ge 0{,}9$ auf den Lern-AB. Je Fit-Satz zählen P1 aus AB1, P1 aus AB2 und P2 mit beiden AB:
  4 Werte bei $\eta = 0$, 20 bei 1 %.
- **Gen. P1:** auf der jeweils anderen ODEBench-AB, 2 bzw. 10 Werte.
- **Gen. P2:** auf den drei neuen Test-AB, 3 bzw. 15 Werte.
- **Median:** Median von $R^2$. Bei zwei Werten ist das der Mittelwert; ein gescheiterter Wert macht ihn deshalb
  $-\infty$.
- **Struktur exakt / Obermenge:** je Fit, 3 bzw. 15 Werte.
  - Annihilator: exakt heißt gewählte Klasse = Referenzklasse, Obermenge heißt eine andere Klasse mit
    $n_{\text{exact}} > 0$.
  - Baselines: exakt heißt Termmenge = wahre Termmenge, Obermenge heißt `TRUE_PLUS`.
  - Bei 19 sind die Baselines nicht darstellbar (–).
- **Integr. gescheitert:** Zahl der Bewertungs-Integrationen mit $R^2 = -\infty$.

### 3.1 Version 2 (Glättungsspline beim Annihilator), vollständig

| Sys. | $\eta$ | Methode | Rek. | Median | Gen. P1 | Median | Gen. P2 | Median | Struktur exakt | Obermenge | Integr. gescheitert |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | 0 | SINDy | 4/4 | 1,000 | 2/2 | 1,000 | 3/3 | 1,000 | 0/3 | 3/3 | 0 |
| 3 | 0 | W-SINDy | 4/4 | 1,000 | 1/2 | 0,947 | 3/3 | 1,000 | 0/3 | 3/3 | 0 |
| 3 | 0 | Annihilator | 4/4 | 1,000 | 2/2 | 1,000 | 3/3 | 1,000 | 2/3 | 1/3 | 0 |
| 3 | 1 % | SINDy | 20/20 | 1,000 | 5/10 | 0,883 | 11/15 | 0,988 | 0/15 | 15/15 | 6 |
| 3 | 1 % | W-SINDy | 14/20 | 0,997 | 5/10 | 0,851 | 12/15 | 0,988 | 0/15 | 15/15 | 11 |
| 3 | 1 % | Annihilator | 17/20 | 1,000 | 8/10 | 0,994 | 10/15 | 0,996 | 4/15 | 11/15 | 8 |
| 7 | 0 | SINDy | 4/4 | 1,000 | 0/2 | $-\infty$ | 3/3 | 0,999 | 0/3 | 3/3 | 1 |
| 7 | 0 | W-SINDy | 4/4 | 1,000 | 0/2 | −14,979 | 3/3 | 0,999 | 0/3 | 3/3 | 0 |
| 7 | 0 | Annihilator | 4/4 | 1,000 | 1/2 | $-\infty$ | 1/3 | $-\infty$ | 0/3 | 0/3 | 3 |
| 7 | 1 % | SINDy | 17/20 | 0,998 | 0/10 | −1765 | 0/15 | $-\infty$ | 0/15 | 12/15 | 12 |
| 7 | 1 % | W-SINDy | 20/20 | 0,999 | 0/10 | −1816 | 5/15 | −12,889 | 0/15 | 15/15 | 7 |
| 7 | 1 % | Annihilator | 14/20 | 0,983 | 0/10 | −174 | 0/15 | $-\infty$ | 0/15 | 2/15 | 14 |
| 19 | 0 | SINDy | 4/4 | 1,000 | 2/2 | 1,000 | 3/3 | 1,000 | – | – | 0 |
| 19 | 0 | W-SINDy | 4/4 | 1,000 | 1/2 | $-\infty$ | 3/3 | 1,000 | – | – | 1 |
| 19 | 0 | Annihilator | 4/4 | 1,000 | 2/2 | 1,000 | 3/3 | 1,000 | 0/3 | 0/3 | 0 |
| 19 | 1 % | SINDy | 16/20 | 0,998 | 6/10 | 0,955 | 11/15 | 0,997 | – | – | 12 |
| 19 | 1 % | W-SINDy | 18/20 | 0,999 | 5/10 | 0,819 | 13/15 | 0,990 | – | – | 6 |
| 19 | 1 % | Annihilator | 20/20 | 0,999 | 10/10 | 0,987 | 13/15 | 0,989 | 0/15 | 0/15 | 1 |
| 21 | 0 | SINDy | 4/4 | 1,000 | 1/2 | $-\infty$ | 3/3 | 1,000 | 0/3 | 3/3 | 1 |
| 21 | 0 | W-SINDy | 4/4 | 1,000 | 1/2 | $-\infty$ | 3/3 | 1,000 | 0/3 | 3/3 | 1 |
| 21 | 0 | Annihilator | 4/4 | 1,000 | 2/2 | 1,000 | 3/3 | 1,000 | 2/3 | 0/3 | 0 |
| 21 | 1 % | SINDy | 20/20 | 1,000 | 4/10 | $-\infty$ | 4/15 | $-\infty$ | 0/15 | 15/15 | 15 |
| 21 | 1 % | W-SINDy | 20/20 | 1,000 | 5/10 | $-\infty$ | 5/15 | −56,591 | 0/15 | 15/15 | 11 |
| 21 | 1 % | Annihilator | 19/20 | 1,000 | 8/10 | 0,992 | 5/15 | −8,075 | 0/15 | 4/15 | 2 |

### 3.2 Version 1 (interpolierender Spline), Annihilator

Die Baselines von v1 sind mit v2 identisch (SINDy vollständig, W-SINDy für 3, 7 und 19 rauschfrei). Die
abweichenden W-SINDy-Ziehungen für 19 und 21 stehen in §3.3; die Zeile 19 rauschfrei ist dort zur Vollständigkeit
mit aufgeführt und gleich.

| Sys. | $\eta$ | Methode | Rek. | Median | Gen. P1 | Median | Gen. P2 | Median | Struktur exakt | Obermenge | Integr. gescheitert |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 3 | 0 | Annihilator | 4/4 | 1,000 | 2/2 | 1,000 | 3/3 | 1,000 | 2/3 | 1/3 | 0 |
| 3 | 1 % | Annihilator | 4/20 | −1,692 | 1/10 | −3,241 | 0/15 | −11,231 | 0/15 | 3/15 | 11 |
| 7 | 0 | Annihilator | 4/4 | 1,000 | 1/2 | $-\infty$ | 1/3 | −0,592 | 0/3 | 0/3 | 1 |
| 7 | 1 % | Annihilator | 0/20 | $-\infty$ | 0/10 | $-\infty$ | 0/15 | −284 | 0/15 | 0/15 | 26 |
| 19 | 0 | Annihilator | 4/4 | 1,000 | 2/2 | 1,000 | 3/3 | 1,000 | 0/3 | 0/3 | 0 |
| 19 | 1 % | Annihilator | 5/20 | −4,231 | 1/10 | $-\infty$ | 2/15 | −21,552 | 0/15 | 0/15 | 21 |
| 21 | 0 | Annihilator | 4/4 | 1,000 | 2/2 | 1,000 | 3/3 | 1,000 | 2/3 | 1/3 | 0 |
| 21 | 1 % | Annihilator | 4/20 | $-\infty$ | 2/10 | $-\infty$ | 0/15 | $-\infty$ | 1/15 | 5/15 | 26 |

### 3.3 W-SINDy, zweite Ziehung (v1-Fortsetzung)

| Sys. | $\eta$ | Methode | Rek. | Median | Gen. P1 | Median | Gen. P2 | Median | Struktur exakt | Obermenge | Integr. gescheitert |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 19 | 0 | W-SINDy | 4/4 | 1,000 | 1/2 | $-\infty$ | 3/3 | 1,000 | – | – | 1 |
| 19 | 1 % | W-SINDy | 16/20 | 1,000 | 5/10 | 0,810 | 14/15 | 0,994 | – | – | 7 |
| 21 | 0 | W-SINDy | 4/4 | 1,000 | 1/2 | $-\infty$ | 3/3 | 1,000 | 0/3 | 3/3 | 1 |
| 21 | 1 % | W-SINDy | 20/20 | 1,000 | 4/10 | $-\infty$ | 6/15 | −1,059 | 0/15 | 15/15 | 10 |

## 4. Gefundene Gleichungen

**Annihilator: gewählte Klassen** $(r,d)$, mit $\ast$ markiert, wenn $n_{\text{exact}} > 0$ (die Klasse enthält die
wahre Funktion). Referenzklassen: 3 und 21 (3,0), 7 (3,1), 19 (2,2).

| Sys. | $\eta$ | v1 | v2 |
|---|---|---|---|
| 3 | 0 | (3,0)\* ×2, (4,0)\* ×1 | (3,0)\* ×2, (4,0)\* ×1 |
| 3 | 1 % | (2,0) ×7, (1,0) ×5, (2,3)\* ×2, (5,0)\* ×1 | (4,0)\* ×5, (3,0)\* ×4, (6,0)\* ×2, (5,0)\* ×2, (5,1)\* ×1, (1,2)\* ×1 |
| 7 | 0 | (1,1) ×2, (6,0) ×1 | (1,1) ×2, (4,0) ×1 |
| 7 | 1 % | (2,0) ×4, (5,0) ×3, (1,0) ×2, (3,0) ×2, (4,0) ×2, (1,1) ×1, (6,0) ×1 | (1,0) ×4, (2,0) ×3, (4,0) ×3, (3,0) ×1, (1,1) ×1, (5,1)\* ×1, (1,5) ×1, (2,2)\* ×1 |
| 19 | 0 | (3,0) ×2, (4,0) ×1 | (3,0) ×3 |
| 19 | 1 % | (2,0) ×5, (1,1) ×4, (1,0) ×3, (3,0) ×3 | (2,0) ×7, (5,0) ×5, (6,0) ×2, (3,0) ×1 |
| 21 | 0 | (3,0)\* ×2, (3,1)\* ×1 | (3,0)\* ×2, (1,3) ×1 |
| 21 | 1 % | (1,0) ×5, (2,0) ×3, (4,0)\* ×2, (2,1)\* ×1, (3,0)\* ×1, (3,1)\* ×1, (1,3) ×1, (6,0)\* ×1 | (1,1) ×7, (2,0) ×3, (5,0)\* ×2, (6,0)\* ×1, (1,0) ×1, (4,1)\* ×1 |

**Baselines (v2): Zahl der aktiven Terme** von 9 möglichen. Die wahre Termmenge hat 2 Terme (3, 7) bzw. 3 Terme (21).

| Sys. | $\eta$ | SINDy | W-SINDy |
|---|---|---|---|
| 3 | 0 | 9 ×2, 8 ×1 | 9 ×3 |
| 3 | 1 % | 9 ×15 | 9 ×13, 8 ×2 |
| 7 | 0 | 9 ×2, 7 ×1 | 9 ×2, 7 ×1 |
| 7 | 1 % | 9 ×7, 8 ×3, 6 ×2, 3 ×1, 1 ×2 | 9 ×3, 7 ×4, 6 ×2, 5 ×5, 4 ×1 |
| 19 | 0 | 9 ×2, 8 ×1 | 9 ×3 |
| 19 | 1 % | 8 ×1, 4 ×8, 3 ×5, 1 ×1 | 9 ×9, 8 ×3, 5 ×1, 4 ×2 |
| 21 | 0 | 8 ×1, 7 ×2 | 9 ×1, 7 ×1, 6 ×1 |
| 21 | 1 % | 8 ×2, 7 ×3, 6 ×9, 5 ×1 | 9 ×2, 7 ×12, 6 ×1 |

Die vollständigen Termmengen mit Koeffizienten, die Operatorkoeffizienten und die Basisgewichte von $\hat f$
stehen in den Records (§7).

## 5. Weitere Größen

**Median $\mathrm{NRMSE}_f$** auf der Lerndomäne (je 3 bzw. 15 Fits):

| Sys. | $\eta$ | SINDy | W-SINDy | Annihilator v1 | Annihilator v2 |
|---|---|---|---|---|---|
| 3 | 0 | $2{,}9\cdot10^{-5}$ | $2{,}5\cdot10^{-4}$ | $3{,}1\cdot10^{-5}$ | $3{,}4\cdot10^{-5}$ |
| 3 | 1 % | 0,029 | 0,083 | 1,0 | 0,036 |
| 7 | 0 | 0,013 | 0,010 | $9{,}9\cdot10^{-4}$ | $9{,}9\cdot10^{-4}$ |
| 7 | 1 % | 44 | 262 | $\infty$ | 0,13 |
| 19 | 0 | $3{,}7\cdot10^{-5}$ | $5{,}7\cdot10^{-5}$ | $4{,}1\cdot10^{-5}$ | $3{,}9\cdot10^{-5}$ |
| 19 | 1 % | 0,090 | 0,013 | 1,6 | 0,022 |
| 21 | 0 | $1{,}9\cdot10^{-5}$ | $2{,}1\cdot10^{-5}$ | $1{,}5\cdot10^{-5}$ | $1{,}0\cdot10^{-4}$ |
| 21 | 1 % | 0,098 | 0,059 | $\infty$ | 0,042 |

W-SINDy aus v2. In der v1-Ziehung liegen die Werte für 19 und 21 bei 1 % bei 0,011 und 0,051, rauschfrei bei 21
bei $2{,}7\cdot10^{-5}$.

**Zählgrößen** (Summe über alle 72 Fits je Methode):

| | Kandidaten gefittet | davon verworfen | Integrationen für die Auswahl |
|---|---|---|---|
| SINDy | 1440 | 237 | 1920 |
| W-SINDy (v2) | 1440 | 226 | 1920 |
| Annihilator v1 | 1296 | 989 | 456 |
| Annihilator v2 | 1296 | 711 | 812 |

Beim Annihilator heißt „verworfen“: Die Kette $L \to \hat f$ ist gescheitert, etwa weil die Nullstelle des
Leitkoeffizienten im Datenbereich lag. In v2 fallen so 55 % der Kandidaten weg, in v1 76 %.

**Laufzeit** (nur berichtet, keine Evidenz): Median je Fit für den Annihilator 20 min in v2 und 15 min in v1, für
SINDy 5 s, für W-SINDy 21 s.

## 6. Einordnung

Das ist Claudes Lesart. Sie ist keine Entscheidungsregel; der Nutzer entscheidet.

1. **v1 und v2.** Der Einbruch des Annihilators bei 1 % in v1 war im Wesentlichen das Spline-Artefakt. Mit Glättung
   (v2) steigen die Rekonstruktionen von 4/20 auf 17/20 (3), von 0/20 auf 14/20 (7), von 5/20 auf 20/20 (19) und
   von 4/20 auf 19/20 (21). Rauschfrei sind v1 und v2 fast gleich.
2. **Funktionsgüte in v2: im Feld der Baselines, teils darüber.**
   - Rekonstruktion: Bei 1 % liegen alle drei Methoden auf 3, 19 und 21 zwischen 14/20 und 20/20, ohne klare
     Ordnung. Bei Gompertz (7) liegt der Annihilator mit 14/20 unter SINDy (17/20) und W-SINDy (20/20).
   - Generalisierung P1: Der Annihilator liegt vorn, 8/10, 10/10 und 8/10 auf 3, 19 und 21 gegen 4–6/10 bei den
     Baselines. Bei diesen 1D-Systemen liegt die andere ODEBench-AB oft auf derselben Bahn. P1 misst deshalb
     überwiegend Genauigkeit innerhalb des gesehenen Bereichs.
   - Generalisierung P2 (Extrapolation): etwa gleichauf (3: 10 gegen 11–12 von 15; 19: 13 gegen 11–14; 21: 5 gegen
     4–6). Bei 21 scheitern alle Methoden überwiegend.
   - Gompertz generalisiert keine Methode bei 1 %. P2 schafft nur W-SINDy in 5/15 Fällen, der Annihilator in 0/15.
3. **Der P1-Vorsprung ist nicht eindeutig dem Operator zuzuordnen.**
   - In v2 bekommt der Annihilator vor dem Fit eine eigens entworfene Glättung von $(\tilde x, \hat{\dot x})$:
     Abschnitte plus GCV-Spline. Der Fehler auf $f$ sinkt dadurch auf 2–3 % (Gompertz 10–15 %).
   - SINDy fittet auf die ungeglätteten Einzelpaare mit 56–190 % Fehler je Punkt und mittelt erst in der
     Regression.
   - Die Klassen mit konstanten Koeffizienten, die der Annihilator meist wählt, sind Exponentialpolynome mit freien
     Raten, also flexible glatte Approximatoren.
   - Ob der Vorsprung vom Operatoransatz oder von der Vorverarbeitung kommt, trennt dieser Vergleich nicht. Trennen
     würde ihn SINDy auf denselben geglätteten Paaren; das ist nicht gelaufen.
4. **Strukturtreffer bleiben die Schwäche, auf die die Idee eigentlich zielte.**
   - Exakt trifft der Annihilator bei 1 % nur die Logistik, in 4/15 Fällen. Dort enthalten aber alle 15 gewählten
     Klassen die wahre Funktion.
   - Bei SIR (21), rauschfrei 2/3 exakt, wählt er bei 1 % in 7/15 Fällen (1,1) ohne die wahre Funktion. Exakt
     trifft er 0/15.
   - Bei 19 und 7 landet er auf Surrogaten; nur 2/15 Gompertz-Klassen enthalten die wahre Funktion.
   - Das entspricht dem Muster aus Gate 2A und dem Smoke-Test (Rückblick §6.2).
   - Die Baselines treffen die exakte Struktur nie. Sie wählen meist dichte Modelle mit 6–9 von 9 Termen. Das liegt
     an der Auswahlregel: Der kleinste Validierungsfehler belohnt dichte Modelle.
   - Ein Strukturvergleich zwischen den Methoden sagt deshalb wenig. Absolut ist das Ergebnis des Annihilators
     schwach, außer bei der Logistik.
5. **Kleine Fallzahlen.** Je Zelle gibt es 10–20 Werte aus 5 Rauschrealisierungen, und die Werte innerhalb einer
   Realisierung hängen zusammen. Dazu kommt die W-SINDy-Streuung (§2). Unterschiede von wenigen Fällen tragen keine
   Aussage.
6. **Kosten.** Ein Annihilator-Fit kostet in Zählgrößen 18 Klassen mit AML und Kette, von denen gut die Hälfte
   scheitert. Die Baselines brauchen 20 lineare STLSQ-Fits. In der Laufzeit sind das Minuten gegen Sekunden.

**Kurz:** Mit sauberer Glättung ist der Annihilator end-to-end in der Funktionsgüte konkurrenzfähig und auf
P1-Generalisierung sogar vorn. Woher dieser Vorsprung kommt, ist offen. Die Struktur, also das eigentliche
Versprechen der Idee, findet er bei 1 % nur bei der Logistik.

## 7. Daten

- **Rohdaten:** `experiments/annihilator_odebench_smoke/results_e2e/records.jsonl` (v1) und
  `results_e2e_v2/records.jsonl` (v2), je etwa 910 MB. Der größte Teil sind die pysindy-Parameter in jeder
  Kandidaten-Validierung.
- **Kompaktfassung:** `records_compact.jsonl` in beiden Ordnern, je etwa 3 MB. Entfernt sind nur die Schlüssel
  `parameters`, `pysindy_parameters` und `training_trajectories`. Alle Metriken, Koeffizienten und
  Kandidaten-Validierungsfehler bleiben erhalten; die Trajektorien lassen sich aus den Seeds neu erzeugen.
- **Auswertung:** Die Tabellen in §3–5 sind aus den Kompaktfassungen gerechnet.
- Die eingebaute Funktion `--summarize` wertet nur die Smoke-Test-Entscheidungsregel aus, die hier nicht gilt. Sie
  wurde nicht verwendet.
