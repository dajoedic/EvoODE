# Reality-Check Stufe A: direkte Sparse-Regression auf denselben Samples

**Eingefroren am 2026-10-06, vor jedem Lauf.** Auftrag und Entscheidungsregel vom Nutzer (Entwurf im Chat vom
06.10.), Auswahlregel, Kategorie `TRUE_PLUS` und Durchführung trotz absehbarem Ausgang vom Nutzer gewählt. Library,
Zulässigkeitsregel, Gültigkeitsprüfung und Fehlermaße von Claude ausgearbeitet. Änderungen nach dem ersten Lauf
brauchen eine neue Version dieses Dokuments, dieses bleibt mit seinem Ergebnis stehen.

**Was das ist:** eine letzte, begrenzte Diagnose vor dem Abschluss von Idee #1. **Kein Gate 2A v4**, keine Änderung
an Annihilator v3, kein Paper-Benchmark. Code und Ergebnisse von v3 bleiben unverändert.

## 1. Frage

Ist das Surrogatproblem der Annihilator-Methode bei F4, F5 und F8 (`docs/DIAGNOSTIC_AMBIGUITY_RESULT.md`)
außergewöhnlich stark? Oder wählt eine direkte Sparse-Regression auf **denselben** Samples $(x_i, f_i)$ ähnlich oft
eine falsche Struktur?

**Was Stufe A nicht zeigen kann:** Die Baseline bekommt eine Library, die die wahre Funktionsfamilie enthält. Der
Annihilator muss die Familie dagegen selbst über den Operator erschließen. Gewinnt die Baseline, heißt das nur: Das
Surrogatproblem ist nicht unvermeidlich, eine direkte Repräsentation erklärt dieselben Daten strukturell
zuverlässiger. Es heißt **nicht**, dass Sparse-Regression allgemein besser ist. Dieser Vorteil der Baseline wird in
jedem Ergebnisdokument ausdrücklich genannt.

## 2. Daten

- Exakt die Samples der Diagnose: `noisy_sample(key, spec.wide, n = 2000, eta = 0.01, seed)` aus
  `experiments/annihilator_gate2a_v3/functions.py`, Seeds $50000 \ldots 50019$ ($N = 20$).
- Damit ist der Vergleich mit dem Annihilator **gepaart**: dieselben 20 Realisierungen wie Seeds 50000–50019 in
  `results/diagnostic_ambiguity/orion/results/records_merged.jsonl`. Annihilator wird nicht neu gerechnet.
- Rauschniveau für den Test: $\sigma = $ `sigma_eff(values, 0.01, tau)` mit $\tau = 3.386508022297224\cdot10^{-7}$,
  also dasselbe $\sigma$ wie im Annihilator-Test.

| Rolle | Funktionen | entscheidet? |
|---|---|---|
| primär (N1 nach Anhang B) | F4, F5, F8 | ja |
| Kontrolle (I) | F1, F2, F6 | nur Gültigkeitsprüfung (§6) |
| sekundär | F3, F7, F9, F10 | nein, nur berichtet |

Keine Erhöhung von $N$ vor der Auswertung. Ist das Ergebnis knapp, wird ein größeres $N$ als neue Version
spezifiziert.

## 3. Library (eingefroren)

Alle Terme sind feste Funktionen von $x$, ohne freie Parameter:

| Gruppe | Terme |
|---|---|
| Polynome | $1,\ x,\ x^2,\ x^3,\ x^4$ |
| Potenzen | $\sqrt{x},\ x^{1.5}$ |
| Logarithmus | $\log x,\ x\log x$ |
| Exponential | $e^{x},\ e^{-x},\ e^{1.5x},\ e^{-1.5x},\ e^{2x},\ e^{-2x}$ |
| Gauß | $e^{-x^2},\ x\,e^{-x^2}$ |
| Trigonometrisch | $\sin x,\ \cos x,\ \sin 2x,\ \cos 2x$ |
| Rational | $1/(1+x),\ 1/(2+x)$ |

Das sind 23 Terme.

**Zulässigkeitsregel:** Ein Term ist für eine Funktion zugelassen, wenn er auf dem gesamten geschlossenen Intervall
$[a, b]$ der breiten Domäne endlich und reell ist. Auf den positiven Domänen (F3, F4, F5, F8) sind damit alle 23
Terme zugelassen. Auf den Domänen mit $x \le 0$ (F1, F2, F6, F7, F9, F10) fallen $\sqrt{x}$, $x^{1.5}$, $\log x$,
$x\log x$, $1/(1+x)$ und $1/(2+x)$ weg, es bleiben 17.

**Wahre Termmengen** $S^*$:

| F1 | F2 | F3 | F4 | F5 | F6 | F7 | F8 | F9 | F10 |
|---|---|---|---|---|---|---|---|---|---|
| $\{x^2\}$ | $\{e^{1.5x}\}$ | $\{x^{1.5}\}$ | $\{\log x\}$ | $\{x\log x\}$ | $\{e^{-x^2}\}$ | $\{\sin 2x, \cos 2x\}$ | $\{1, 1/(2+x)\}$ | $\{x^2, e^x\}$ | $\{\sin x, e^{-x^2}\}$ |

F7: $\sin(2x + 1/2) = \cos(1/2)\sin 2x + \sin(1/2)\cos 2x$. F8: $x/(2+x) = 1 - 2/(2+x)$.

Die Library ist bewusst günstig für die Baseline: Sie enthält alle wahren Familien, sogar die exakte Rate $1.5$ in
$e^{1.5x}$. Die übrigen Terme sind Distraktoren, darunter genau die Familien, aus denen die Annihilator-Surrogate
bestehen (Polynome und Exponentialfunktionen mit konstanten Raten).

## 4. Verfahren

**Entscheidend, BS (Best-Subset mit der Annihilator-Suchregel):**

1. Für $k = 1, 2, 3, 4$: Alle Teilmengen $S$ der zugelassenen Terme mit $|S| = k$ werden per Kleinste-Quadrate
   (ohne Regularisierung) an die verrauschten Werte gefittet.
2. Teststatistik $T = \mathrm{RSS}/\sigma^2$, kritischer Wert $\chi^2_{n-k}(1 - \alpha)$ mit $\alpha = 0{,}01$.
   $S$ ist akzeptiert, wenn $T \le$ kritischer Wert.
3. Gewählt wird beim kleinsten $k$, für das mindestens eine Teilmenge akzeptiert ist, die akzeptierte Teilmenge mit
   kleinstem RSS. Gibt es bis $k = 4$ keine akzeptierte Teilmenge, ist das Ergebnis `FAIL`.

Das ist dieselbe Regel wie beim Annihilator (die einfachste Klasse, die der $\chi^2$-Test bei $\alpha = 1\,\%$ nicht
verwirft). Nur die Repräsentation unterscheidet sich: Termmenge statt Operatorklasse.

**Nur berichtet, STLSQ** (Brunton, Proctor, Kutz 2016): Die Spalten werden auf rms 1 normiert. Startwert ist
Kleinste-Quadrate über alle zugelassenen Terme. Danach werden Koeffizienten mit Betrag unter $0{,}1$ (normiert) auf
null gesetzt, und auf den verbleibenden Termen wird neu gefittet. Das wird höchstens 20-mal wiederholt oder bis sich
die Termmenge nicht mehr ändert. Keine Ridge-Regularisierung. Ein einziger Schwellenwert, kein Pfad, keine Auswahl
nach Ergebnis.

Für beide Verfahren wird, falls die Kleinste-Quadrate-Lösung nicht endlich ist, `FAIL` mit Grund notiert.

## 5. Kategorien

$S$ ist die gewählte Termmenge, $S^*$ die wahre:

| Kategorie | Bedingung |
|---|---|
| `TRUE_STRUCTURE` | $S = S^*$ |
| `TRUE_PLUS` | $S \supsetneq S^*$ (alle wahren Terme und zusätzliche) |
| `SURROGATE` | $S \not\supseteq S^*$ (mindestens ein wahrer Term fehlt), Modell gewählt |
| `FAIL` | kein Modell gewählt (BS: nichts akzeptiert bis $k = 4$) oder numerisches Scheitern |

Die Koeffizienten gehen nicht in die Kategorie ein.

**Pro Realisierung erfasst** (beide Verfahren):
- Funktion, Seed, Verfahren und Kategorie;
- $S$ mit Koeffizienten (in Originaleinheiten), $|S|$, RSS, $T$ und kritischer Wert;
- bei BS die Zahl der akzeptierten Teilmengen beim gewählten $k$ (Mehrdeutigkeit, diagnostisch, ohne Einfluss auf
  die Kategorie);
- relativer Koeffizientenfehler gegenüber den wahren Koeffizienten, falls $S \supseteq S^*$;
- Trainingsresiduum $\sqrt{\mathrm{RSS}/n}/\mathrm{rms}(f)$;
- Fehler auf einem dichten rauschfreien Gitter derselben Domäne (10 000 Punkte):
  $\mathrm{rms}(\hat f - f)/\mathrm{rms}(f)$;
- Fehler auf der Erweiterung $[b,\ b + (b - a)/2]$ (10 000 Punkte), gleiche Normierung mit $\mathrm{rms}(f)$ auf der
  Erweiterung. Nur rechtsseitig, weil alle wahren Funktionen dort definiert sind. Ist ein gewählter Term dort nicht
  endlich, wird `NaN` mit Grund notiert.

## 6. Entscheidungsregel (eingefroren)

Alle Anteile über die 60 primären Realisierungen (F4, F5, F8 × 20), Verfahren BS:

- $P_{\text{true}} = \#\texttt{TRUE\_STRUCTURE} / 60$
- $P_{\text{surr}} = \#\texttt{SURROGATE} / 60$

**Gültigkeitsprüfung zuerst:** Erreicht BS auf den Kontrollen (F1, F2, F6 × 20) $P_{\text{true}} < 0{,}70$, gilt die
Baseline als nicht funktionsfähig. Das Verdikt heißt dann `INVALID`, es folgt keine Schlussfolgerung über den
Annihilator, und eine neue Version wird mit dem Nutzer besprochen.

| Verdikt | Bedingung | Folge |
|---|---|---|
| `STRONG_NEGATIVE` | $P_{\text{true}} \ge 0{,}70$ **und** $P_{\text{surr}} \le 0{,}20$ | Das Surrogatproblem des Annihilators ist im direkten Vergleich außergewöhnlich stark. **Idee #1 beenden**, kein W-SINDy, kein ODEFormer. |
| `OPEN` | jeder andere Fall | Stufe B (W-SINDy auf Trajektorien) kommt in Frage. Sie braucht eine eigene, vorab eingefrorene Spezifikation, kein automatischer Start. |

`TRUE_PLUS` und `FAIL` zählen weder zu $P_{\text{true}}$ noch zu $P_{\text{surr}}$, werden aber berichtet. STLSQ
und die sekundären Funktionen gehen nicht in das Verdikt ein. Keine Schwellenänderung nach dem Lauf, keine
Library-Änderung nach Sichtung von Ergebnissen.

## 7. Vergleichsgröße Annihilator

Aus den vorhandenen Records, ohne Neuberechnung:
- **gepaart:** Seeds 50000–50019 für F1, F2, F4, F5, F6, F8, Zustände wie gespeichert;
- **Referenz:** alle 100 Seeds je Funktion.

Berichtet werden je Gruppe die Zustandshäufigkeiten und
$P(\text{strukturell falsche eindeutige Ausgabe} \mid N1) = \#\texttt{WRONG} / \#(\texttt{CORRECT} + \texttt{TRUE\_NOT\_REF} + \texttt{WRONG})$.
Bei 100 Seeds ist das $118/118$. Für die Baseline ist die entsprechende Größe
$\#\texttt{SURROGATE} / \#(\texttt{TRUE\_STRUCTURE} + \texttt{TRUE\_PLUS} + \texttt{SURROGATE})$.

## 8. Ablauf

1. **Implementierungsprüfung auf exakten Daten** ($\eta = 0$, $\sigma = $ `sigma_eff(values, 0, tau)`): BS muss für
   alle F1–F10 `TRUE_STRUCTURE` liefern. Das ist ein Code-Test, keine Kalibrierung. Schlägt er fehl, wird der Befund
   gemeldet und nichts an Library oder Regel geändert.
2. **Pilot:** Seeds 50000 und 50001 für alle zehn Funktionen. Erfasst werden nur Zählgrößen (Zahl der Fits). Die
   Pilot-Records zählen im Hauptlauf mit. Ihre Kategorien beeinflussen nichts.
3. **Hauptlauf:** Seeds 50000–50019. Liegt die hochgerechnete Laufzeit unter 1 h, läuft er auf dem Laptop direkt im
   Anschluss an den Pilot.
4. Auswertung nach §6 und §7 in `docs/REALITY_CHECK_DIRECT_REGRESSION.md` §10.

## 9. Erwartung (vorab notiert)

In der Library ist $\log x$ ein Term, $x\log x$ ein Term und $x/(2+x)$ zwei Terme. Das Annihilator-Surrogat (3,0)
entspricht dagegen einer Summe von drei Exponentialfunktionen mit freien Raten. Die feste Library bietet so etwas
nicht, und ihre Polynome und festen Exponentialfunktionen brauchen dafür voraussichtlich mehr Terme. Erwartet wird
deshalb $P_{\text{true}}$ nahe 0,99 bei F4, F5 und F8 und damit `STRONG_NEGATIVE`.

Die inhaltliche Lesart wäre dann: Die Komplexitätsordnung $(r+1)(d+1)$ des Annihilators stuft das Surrogat als
einfacher ein als den wahren Operator. Im Funktionsraum ist es umgekehrt. Das Surrogatproblem liegt an der
Repräsentation, nicht an den Daten allein.

## 10. Ergebnis

*(nach dem Hauptlauf)*
