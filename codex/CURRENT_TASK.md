# WP-G2A2-a — Gate 2A v2: Implementierung, Orakel mit 100 Stellen, Kalibrierstufe K
**Language: Python**

Grundlage, **wörtlich verbindlich:** `docs/GATE_2A_v2.md` (eingefroren am 2026-10-04). Begründung der Änderungen
gegenüber v1: `docs/GATE_2A_v2_RATIONALE.md`. Wo dieser Auftrag und die Spezifikation voneinander abweichen, gilt
die Spezifikation. Melde jede solche Stelle im Report.

Dieser Auftrag umfasst die Stufen **Orakel → Stufe K → Anhang A** aus §14 E9 und endet dort. Die Abnahme auf dem
Gate-Set (§11), Anhang B und der Gate-Lauf sind ein späteres Arbeitspaket. **F1–F10 werden in diesem Auftrag nicht
gerechnet**, außer im Orakel (§3).

## Ort und Verhältnis zu v1

- Neuer Code unter `experiments/annihilator_gate2a_v2/`, gleiche Gliederung wie v1: Konfiguration, Funktionen,
  Orakel, Weak-Matrix, Suche, Transfer, Lauf, Auswertung, `acceptance/`, `tests/`, `results/`, README.
- `experiments/annihilator_gate2a/` (v1) bleibt **verhaltensgleich**. Funktionsdefinitionen und Orakel dürfen
  importiert werden. Wird dort etwas geändert, müssen die v1-Tests unverändert grün bleiben, und der Report nennt die
  Änderung. Die Ergebnisse von v1 unter `experiments/annihilator_gate2a/results/` werden nicht angefasst.

## Umzusetzen

1. **Konfiguration:** alle Konstanten aus §4–§6 und §13 der Spezifikation, das Kalibrier-Set K1–K6 aus §2b mit
   Domänen, und die Varianten S1–S16. $\ell_{\max}$ und $\tau$ sind **keine** Konstanten im Code. Sie werden aus
   Anhang A gelesen, sobald dieser existiert. Vorher wird nur Stufe K gerechnet, die beide Größen erst bestimmt.
2. **Funktionen:** K1–K6 numerisch (SciPy für Ai und $J_0$) und symbolisch (SymPy) wie F1–F10.
3. **Orakel (§3):** 100 Stellen, mindestens 200 Punkte, Schwelle $10^{-60}$, für F1–F10 und K1–K6 auf beiden
   Domänen. Eigener Cache `results/oracle_reference_v2.json` mit Metadaten zu Präzision, Punkten, Schwelle und
   Laufzeit. Die Pflichtprüfungen aus §3 kommen als `acceptance/accept_01_oracle.py` mit JSON. Darin steht auch der
   Vergleich mit dem v1-Cache (`experiments/annihilator_gate2a/results/oracle_reference.json`), mit den drei
   bekannten F10-Einträgen ausdrücklich ausgewiesen. Ai und $J_0$ werden über ihre Definitions-ODE verifiziert.
   Weicht eine K-Referenzklasse von der erwarteten Klasse in §2b ab, wird das berichtet. Das Set wird nicht
   geändert.
4. **Weak-Matrix (§4–§5):** verschränkte Fit/Val-Teilgitter, multiskalige Träger, $M = 8$, $q = 14$.
   **Numerisch stabile Auswertung nach §5**, ausdrücklich keine Monomdarstellung (v1 tut das, und genau das war
   eine Ursache des Scheiterns). Trapezregel pro Teilgitter. Die Gewichtsstruktur $W(c)$ muss für FNS und für die
   Kovarianz zugänglich sein. Achte auf Speicher: Bei $R$ Zeilen, 49 Spalten und 1.000 Samples darf der volle
   Tensor nicht pro Klasse und Replikat neu entstehen.
5. **Suche (§6):** FNS-Kandidat mit SVD-Start, Abbruchregel, Konvergenz-Flag; KCR-Kovarianz; Val-Test; A1 über
   $c_2$ aus $M(\hat c)$; A2 Bootstrap; A3. Der Gradient $\nabla J = 2X(c)c$ wird in einem pytest-Fall gegen finite
   Differenzen geprüft, auf einer kleinen zufälligen Instanz.
6. **Ergebniszustände, Kennzahlen, Transfer (§7, §8)** wie spezifiziert, Lauf-CLI und Auswertung analog zu v1,
   noch ohne Anhang B.
7. **Stufe K (§10)** als `acceptance/stage_k_calibration.py`:
   - **K-a:** Fehlermaß $e$ gegen das hochpräzise Integral (mpmath, 30 Stellen) für alle K-Zellen, beide Teilgitter,
     $\ell \in \{3, 4, 5\}$. Daraus $\ell_{\max}$ nach der Regel aus §10. Erfüllt nicht einmal $\ell = 3$ die
     Regel: Stopp und `blocked`.
   - **K-b:** $\tau$ nach der Formel aus §10. Bei $\tau > 10^{-4}$: Stopp und `blocked`.
   - **Ex-ante-Klassen (§9) nur für die K-Zellen**, weil K-c sie braucht.
   - **K-c 1–4** mit den Schwellen aus §10. 1.000 Realisierungen pro Zelle, Seeds 0–999.
   - Ausgabe `results/calibration/appendix_A.json` und `appendix_A.md`: $\ell_{\max}$, $\tau$, alle Einzelzahlen,
     jede Prüfung mit Bestanden/Nicht bestanden, ein Gesamtverdikt.
8. **Smoke und Laufzeit:** Eine K-Zelle bei 1 %, eine Realisierung, volle Suche mit Bootstrap. Daraus eine
   Hochrechnung für den späteren Gate-Hauptlauf (20 clean + 400 bei 1 % + 400 bei 5 %) und das Raster
   (16 Varianten × (20 clean + 400 bei 1 %)), getrennt nach früh und spät stoppenden Referenzklassen, mit 1 und
   8 Workern. Die Hochrechnung ist eine Projektion, kein Beleg. Sie wird nur so berichtet.

## Verboten

- Keinen Gate-Lauf, kein Raster, **keine Rechnung auf F1–F10 außer dem Orakel**, auch nicht „zur Kontrolle“.
- Keine Konstante, Schwelle oder Regel aus `docs/GATE_2A_v2.md` ändern und keine Toleranz lockern. Scheitert eine
  Prüfung an der Sache, lautet der Status `blocked`, mit den Zahlen. Nicht an der Formel drehen, bis es passt.
- Nichts außerhalb von `experiments/annihilator_gate2a_v2/`, `codex/STATUS.md` und `codex/reports/` schreiben
  (Ausnahme: die oben erlaubte, verhaltensgleiche Änderung an v1). Kein `docs/`, kein Julia, kein `src/`.
- Keine ODE-Integration, keine nichtlineare Optimierung außer der FNS-Iteration, keine SR, kein GP. Nur NumPy,
  SciPy, SymPy, mpmath, pytest, optional pandas.
- Kein Git außer lesend.
- **Kein Einzelkommando über 15 Minuten.** Das Orakel und der K-c-Monte-Carlo dürfen parallelisiert und in Teile
  zerlegt werden (`--part`). Wird etwas nicht fertig, steht der Befehl im Report, und Claude führt ihn aus.

## Abnahme

- Die Punkte 1–8 sind umgesetzt. `pytest experiments/annihilator_gate2a_v2/tests` und
  `pytest experiments/annihilator_gate2a/tests` sind grün.
- `accept_01_oracle` und `stage_k_calibration` sind **ausgeführt**, oder sie haben einen Befehl im Report, falls
  sie länger als 15 Minuten brauchen. Ihre JSONs liegen unter `experiments/annihilator_gate2a_v2/results/`.
- Report `codex/reports/REPORT_WP_G2A2_A.md` mit den Zahlen aus **diesen** Läufen: Orakel, K-a, K-b, ex-ante-Klassen
  der K-Zellen, K-c 1–4, Smoke-Hochrechnung, Abweichungen von der Spezifikation.
- `codex/STATUS.md` mit der Kennung `WP-G2A2-a`. `done` heißt: Anhang A existiert und alle Prüfungen sind bestanden.
  `blocked` heißt: eine Prüfung ist gescheitert oder ein Stopp aus §10 ist eingetreten.
