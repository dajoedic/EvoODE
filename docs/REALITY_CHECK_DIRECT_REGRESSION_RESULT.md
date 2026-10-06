# Reality-Check Stufe A – Ergebnis und Übergabe

**Stand: 2026-10-06 abends.** Ergebnis des Reality-Checks nach der eingefrorenen Spezifikation
`docs/REALITY_CHECK_DIRECT_REGRESSION.md` (freigegeben vom Nutzer in `084fcfc`, Ergebnis dort in §10). Für den Nutzer
und jede spätere Sitzung dieser Spur, als Grundlage für den Abschluss von Idee #1. Die Vorgeschichte steht in
`docs/DIAGNOSTIC_AMBIGUITY_RESULT.md`.

## 1. In einem Satz

**Verdikt nach der eingefrorenen Regel: `STRONG_NEGATIVE`.** Auf exakt denselben verrauschten Samples und mit
derselben Entscheidungsregel findet eine direkte Best-Subset-Regression F4, F5 und F8 in **60 von 60**
Realisierungen richtig. Der Annihilator liegt auf denselben Samples bei **25 von 25** eindeutigen Antworten falsch.
Die Daten tragen die Struktur also. Das Surrogatproblem entsteht durch die Annihilator-Repräsentation. Folge nach §6
der Spezifikation: **Idee #1 beenden**, kein W-SINDy, kein ODEFormer.

## 2. Warum dieser Check

Die Diagnose `AMBIGUOUS` (06.10.) hatte gezeigt: In den nicht identifizierbaren Fällen F4 $\log x$, F5 $x\log x$
und F8 $x/(2+x)$ (breite Domäne, 1 % Rauschen) bleibt der Annihilator an einfacheren falschen Operatorklassen mit
konstanten Koeffizienten hängen, (3,0) bzw. (2,0). Eindeutige Antworten sind dort immer falsch (118/118).

Offen blieb die Frage des Nutzers: **Ist das normales Equation-Discovery-Elend bei diesen Funktionen und diesem
Rauschen, oder ein zusätzliches Problem der Annihilator-Repräsentation?** Stufe A beantwortet das billig mit einer
direkten Regression von $f(x)$ auf eine feste Library, auf denselben Daten.

## 3. Was geprüft wurde

- **Daten:** exakt die Samples der Diagnose, `noisy_sample(key, wide, n = 2000, eta = 0.01, seed)`, Seeds
  50000–50019. Dasselbe $\sigma$ wie im Annihilator-Test (`sigma_eff` mit $\tau = 3.39\cdot10^{-7}$). Der Vergleich
  ist dadurch **gepaart**, der Annihilator wurde nicht neu gerechnet.
- **Funktionen:**
  - primär F4, F5, F8 (entscheiden);
  - Kontrolle F1, F2, F6 (nur Gültigkeitsprüfung);
  - sekundär F3, F7, F9, F10 (nur berichtet).
- **Library:** 23 feste Terme:
  - Polynome bis $x^4$;
  - $\sqrt x$, $x^{1.5}$, $\log x$, $x\log x$;
  - $e^{\pm x}$, $e^{\pm 1.5x}$, $e^{\pm 2x}$;
  - $e^{-x^2}$, $x e^{-x^2}$;
  - $\sin x$, $\cos x$, $\sin 2x$, $\cos 2x$;
  - $1/(1+x)$, $1/(2+x)$.

  Auf Domänen mit $x \le 0$ fallen die dort undefinierten Terme weg, es bleiben 17. Die Library ist **bewusst
  günstig für die Baseline**: Sie enthält jede wahre Familie, F4 und F5 sind je ein einzelner Term, F8 sind zwei
  ($1 - 2/(2+x)$).
- **Entscheidendes Verfahren, BS (Best-Subset):** Für $k = 1 \ldots 4$ werden alle Teilmengen mit Kleinste-Quadrate
  gefittet, mit $T = \mathrm{RSS}/\sigma^2$ gegen $\chi^2_{n-k}(0{,}99)$. Gewählt wird beim kleinsten $k$ mit einer
  akzeptierten Teilmenge die mit kleinstem RSS. Das ist **dieselbe Entscheidungsphilosophie wie beim Annihilator**
  (die einfachste Hypothese, die der Test bei $\alpha = 1\,\%$ nicht verwirft). Nur die Repräsentation
  unterscheidet sich.
- **Nur berichtet, STLSQ:** normierte Spalten, feste Schwelle 0,1, ohne Ridge-Regularisierung.
- **Kategorien:**
  - `TRUE_STRUCTURE`: exakt die wahre Termmenge;
  - `TRUE_PLUS`: die wahren Terme plus zusätzliche;
  - `SURROGATE`: mindestens ein wahrer Term fehlt;
  - `FAIL`: kein Modell oder numerisches Scheitern.
- **Entscheidungsregel** (vor dem Lauf eingefroren):
  - Zuerst die Gültigkeitsprüfung: $P_{\text{true}}$ auf den Kontrollen muss mindestens 0,70 sein, sonst
    `INVALID`.
  - Dann `STRONG_NEGATIVE`, wenn auf F4/F5/F8 $P_{\text{true}} \ge 0{,}70$ **und** $P_{\text{surr}} \le 0{,}20$ gilt.
  - In jedem anderen Fall `OPEN`; dann wäre Stufe B (W-SINDy) mit eigener Spezifikation in Frage gekommen.

## 4. Ablauf

| Schritt | Ergebnis |
|---|---|
| Spezifikation eingefroren | `64c295f`. Auswahlregel, `TRUE_PLUS` und Durchführung vom Nutzer gewählt |
| Umsetzung durch Codex | WP-RC-A (`eb77334`). Nachbesserung WP-RC-A2: Der Annihilator-Vergleich fasste N1 und I zusammen (118/415 statt 118/118); der alte Test hatte das umgangen. Danach 54 Tests grün |
| Prüfung auf exakten Daten (§8.1) | bestanden: F1–F10 `TRUE_STRUCTURE`, jeweils mit kleinstem $k$ |
| Freigabe durch den Nutzer | `084fcfc`, zwei Änderungen vor dem ersten Rauschlauf: §8.1 als Implementierungs- und Spezifikationsprüfung mit Stopp, §9 ohne Zahl in der Erwartung |
| Pilot, Seeds 50000–50001 | 17–276 Fits pro Realisierung. Hauptlauf deshalb direkt auf dem Laptop |
| Hauptlauf, Seeds 50000–50019 | 400 Records (10 Funktionen × 20 Seeds × 2 Verfahren), Ergebnis in `69923fc` |

## 5. Ergebnis gegen die Entscheidungsregel

| Größe | Wert | Schwelle | erfüllt? |
|---|---:|---|---|
| Gültigkeit: $P_{\text{true}}$ Kontrollen (F1, F2, F6) | 1,00 (60/60) | ≥ 0,70 | ja |
| $P_{\text{true}}$ primär (F4, F5, F8) | **1,00 (60/60)** | ≥ 0,70 | ja |
| $P_{\text{surr}}$ primär | **0,00 (0/60)** | ≤ 0,20 | ja |

**Verdikt: `STRONG_NEGATIVE`.** Das Ergebnis ist nicht knapp. Beide Schwellen werden mit maximalem Abstand erfüllt.

## 6. Vergleich auf denselben Samples

Strukturell falsche eindeutige Ausgaben / alle eindeutigen Ausgaben:

| Gruppe | Annihilator gepaart (Seeds 50000–50019) | Annihilator Referenz (100 Seeds) | BS | STLSQ |
|---|---:|---:|---:|---:|
| N1 (F4, F5, F8) | **25/25**, dazu 35 `AMBIGUOUS` | 118/118, dazu 182 `AMBIGUOUS` | **0/60** | 0/60 (alle `TRUE_PLUS`) |
| I (F1, F2, F6) | 0/57, dazu 3 `AMBIGUOUS` | 0/297, dazu 3 `AMBIGUOUS` | 0/60 | 2/60 |

In N1 trifft der Annihilator auf diesen 60 Datensätzen **nie** die richtige Klasse. Die direkte Regression trifft
die richtige Struktur auf denselben Datensätzen **immer**.

## 7. Ergebnis je Funktion

| Fkt. | BS `TRUE_STRUCTURE` | BS gewähltes $k$ | STLSQ | STLSQ Termzahl |
|---|---:|---:|---|---:|
| F1 $x^2$ | 20/20 | 1 | 20 `TRUE_PLUS` | 16–17 |
| F2 $e^{1.5x}$ | 20/20 | 1 | 20 `TRUE_PLUS` | 17 |
| F3 $x^{1.5}$ | 20/20 | 1 | 20 `TRUE_PLUS` | 23 |
| F4 $\log x$ | 20/20 | 1 | 20 `TRUE_PLUS` | 23 |
| F5 $x\log x$ | 20/20 | 1 | 20 `TRUE_PLUS` | 23 |
| F6 $e^{-x^2}$ | 20/20 | 1 | 18 `TRUE_PLUS`, 2 `SURROGATE` | 15–17 |
| F7 $\sin(2x + 1/2)$ | 20/20 | 2 | 17 `TRUE_PLUS`, 3 `SURROGATE` | 14–16 |
| F8 $x/(2+x)$ | 20/20 | 2 | 20 `TRUE_PLUS` | 23 |
| F9 $x^2 + e^x$ | 20/20 | 2 | 20 `TRUE_PLUS` | 17 |
| F10 $\sin x + e^{-x^2}$ | 20/20 | 2 | 19 `TRUE_PLUS`, 1 `SURROGATE` | 15–16 |

**BS im Einzelnen:**
- Kein `FAIL`, kein `TRUE_PLUS`, kein `SURROGATE` in allen 200 Realisierungen.
- **Keine Mehrdeutigkeit:** Beim gewählten $k$ ist in jeder Realisierung genau eine Teilmenge akzeptiert.
- **Genauigkeit:**
  - Relativer Fehler auf einem dichten rauschfreien Gitter der Domäne: im Median $1{,}4$–$2{,}9\cdot10^{-4}$ je
    Funktion, höchstens $5{,}5\cdot10^{-4}$.
  - Auf der rechten Erweiterung $[b,\ b + (b-a)/2]$: im Median $1{,}3$–$2{,}9\cdot10^{-4}$, höchstens
    $6{,}5\cdot10^{-4}$.
  - Relativer Koeffizientenfehler: im Median $1{,}4$–$5{,}3\cdot10^{-4}$, höchstens $1{,}2\cdot10^{-3}$ (F8).
- **Kosten:** 17 bis 276 Fits pro Realisierung, insgesamt Sekunden auf dem Laptop.

**STLSQ ist in der eingefrorenen Form entartet** (geht nicht ins Verdikt ein):
- Die Library ist auf diesen Domänen stark kollinear. Schon die erste Kleinste-Quadrate-Lösung über alle Terme hat
  normierte Koeffizienten weit über der Schwelle 0,1. Nach 1–3 Iterationen wird nichts mehr entfernt, und es bleiben
  14–23 Terme.
- Auf der Domäne passt das Modell im Rauschen (Fehler ≈ $10^{-3}$). Die Koeffizienten weichen aber um
  Größenordnungen ab (relativer Fehler bis $2\cdot10^7$), auf der Erweiterung liegt der Fehler zwischen 15 und
  $7\cdot10^7$.
- `TRUE_STRUCTURE` kommt nie vor. Die 6 `SURROGATE`-Fälle sind Modelle, in denen ein wahrer Term unter die Schwelle
  gefallen ist.
- Das zeigt nur, dass ein ungetuntes STLSQ mit fester Schwelle bei einer kollinearen Library keine brauchbare
  Vergleichsmethode ist. Eine Schwellenwahl nach Sichtung wäre Kalibrierung am Ergebnis und ist nach §4 der
  Spezifikation ausgeschlossen. Für die Frage dieses Checks spielt es keine Rolle, weil BS sie eindeutig beantwortet.

## 8. Was das bedeutet

### 8.1 Die Daten tragen die Struktur

Bei 1 % Rauschen und 2000 Punkten lässt sich $\log x$ von jedem anderen Modell mit höchstens einem Library-Term klar
unterscheiden. Der Test verwirft jede falsche Einzelterm-Hypothese, und die wahre besteht. Das Gleiche gilt für
$x\log x$ und für $x/(2+x)$ mit zwei Termen. Die Nicht-Identifizierbarkeit aus Anhang B ist also **keine
Eigenschaft der Daten**, sondern eine der Hypothesenmenge, in der der Annihilator sucht.

### 8.2 Die Ursache liegt in der Komplexitätsordnung des Annihilators

Der Annihilator ordnet Hypothesen nach $(r+1)(d+1)$, also nach der Zahl der Operatorkoeffizienten. In dieser
Ordnung kommt (3,0) mit vier Koeffizienten vor dem wahren Operator (2,1) für $\log x$ mit sechs. (3,0) beschreibt
aber eine dreidimensionale Familie von Exponentialpolynomen mit **freien** Raten (Summen von $e^{\lambda x}$,
gegebenenfalls mit Faktor $x$ oder oszillierend). Dieser Familie ist es leicht, $\log x$
im Rahmen von 1 % zu imitieren. Im Funktionsraum ist $\log x$ die einfachere Hypothese, in der Operatorordnung die
komplexere. Die Suchregel „einfachste nicht verworfene Hypothese“ führt deshalb bei gleicher Testlogik in der einen
Repräsentation immer zum Ziel und in der anderen nie.

### 8.3 Was dieser Check nicht zeigt

- **Die Baseline ist bevorteilt.** Sie bekommt die wahre Funktionsfamilie in der Library, teilweise mit exakter Rate
  ($e^{1.5x}$). Der Annihilator muss die Familie selbst über den Operator erschließen, und das war gerade sein
  Versprechen.
- Das Ergebnis zeigt also, dass das Surrogatproblem **nicht unvermeidlich** ist. Es zeigt nicht, dass
  Sparse-Regression allgemein überlegen wäre, und auch nicht, wie eine Baseline ohne die wahre Familie in der
  Library abschneiden würde.
- Für die Go/No-Go-Frage reicht das: Das Versprechen der Methode, Familien jenseits einer vorgegebenen Library zu
  erkennen, scheitert genau an den $x$-abhängigen Koeffizienten, auf die es ankäme.

## 9. Gesamtbild der Spur

| Schritt | Ergebnis |
|---|---|
| Gate 2A v1 | eingefroren, an der Abnahme gescheitert, nie gelaufen |
| Gate 2A v2 | Stufe K gescheitert (FNS-Fehler) |
| Gate 2A v3, Anhang A | nicht bestanden: Ordnung 3 unkalibriert, Clean K7/K8 durchgefallen |
| Gate 2A v3, Anhang B | Kill-Kriterium K6 würde auslösen (F4, F5, F8 bei 1 % N1) |
| Diagnose `AMBIGUOUS` | negativ: B1 = 118/118, die Abstention fängt stabile Fehlwahlen nicht ab |
| Reality-Check Stufe A | **`STRONG_NEGATIVE`**: Die direkte Repräsentation löst dieselben Fälle in 60/60 |

**Was bleibt:**
- Für Operatoren erster und zweiter Ordnung mit konstanten oder einfachen Koeffizienten findet der Annihilator den
  richtigen Operator, mit kalibriertem Test (K1, K2 aus Anhang A; I-Fälle mit 297/300 `CORRECT`).
- Übertragbar ist die Prüfdisziplin: Entscheidungsregeln vor jedem Lauf einfrieren, Gültigkeitsprüfung,
  gepaarte Vergleiche auf identischen Samples, Implementierungsprüfung auf exakten Daten.
- Inhaltlich übertragbar ist eine Einsicht: Ein Sparsamkeitsprinzip ist nur so gut wie die Komplexitätsordnung, in
  der es angewendet wird.

## 10. Nächste Schritte

1. **Abschluss schreiben** (nach Bestätigung durch den Nutzer, der den Abschluss bei `STRONG_NEGATIVE` vorab
   zugesagt hat): Abschlussabschnitt in `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` und in `CLAUDE.md` die Spur als
   abgeschlossen markieren. Kein W-SINDy, kein ODEFormer, kein eigenes Repository.
2. **Aufräumen** (Entscheidungen des Nutzers):
   - `PRACTICAL_ANNIHILATOR_BENCHMARK.md` (uncommittet): zur Akte committen oder verwerfen;
   - Reste der v2-Abnahme unter `experiments/annihilator_gate2a_v2/results/acceptance/` (uncommittet): committen
     oder löschen;
   - der abgeschlossene Orion-Job `annihilator-diag-amb`: löschen mit `oc delete job annihilator-diag-amb`;
   - die Temp-Ordner `.pytest_tmp/` und `.codex_tmp/`: löschen.

## 11. Wo die Daten liegen

| Pfad | Inhalt |
|---|---|
| `docs/REALITY_CHECK_DIRECT_REGRESSION.md` | eingefrorene Spezifikation, Ergebnis in §10 |
| `experiments/annihilator_gate2a_v3/diagnostics/direct_regression_check.py` | Code (BS, STLSQ, Kategorien, Auswertung) |
| `experiments/annihilator_gate2a_v3/tests/test_direct_regression_check.py` | 16 Tests |
| `experiments/annihilator_gate2a_v3/results/reality_check_direct/exact_check.json` | Prüfung auf exakten Daten (§8.1) |
| `experiments/annihilator_gate2a_v3/results/reality_check_direct/records.jsonl` | **400 Records**, Grundlage des Verdikts |
| `experiments/annihilator_gate2a_v3/results/reality_check_direct/summary.json`, `summary.md` | Verdikt und Vergleichstabellen |
| `experiments/annihilator_gate2a_v3/results/reality_check_direct/run.log` | Fortschritt ohne Kategorien |
| `codex/reports/REPORT_WP_RC_A.md`, `REPORT_WP_RC_A2.md` | Umsetzungs- und Nachbesserungsbericht |
| `experiments/annihilator_gate2a_v3/results/diagnostic_ambiguity/orion/results/records_merged.jsonl` | Annihilator-Records für den Vergleich |
