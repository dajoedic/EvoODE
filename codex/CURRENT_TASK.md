# WP-G2A3-c — Gate 2A v3: Anhang B (ex-ante-Identifizierbarkeit F1–F10) als Diagnose
**Language: Python**

Grundlage: `docs/GATE_2A_v3.md` mit `docs/GATE_2A_v2.md` §9 (ex-ante-Identifizierbarkeit) und §12 (K6).
Kontext: `docs/GATE_2A_v3_STAGE_K_RESULT.md`. Anhang A ist **nicht** bestanden. Der Nutzer hat am 05.10.
entschieden (Option A), Anhang B trotzdem zu berechnen, **ausschließlich als Diagnose**. Kein Gate-Lauf, keine
Gate-Kriterien außer der K6-Diagnose unten.

## Zu bauen

`experiments/annihilator_gate2a_v3/acceptance/appendix_b.py`:

1. **Parameter:** $\ell_{\max}$ und $\tau$ aus der Stufe K von v3 (`results/calibration/appendix_A_part_0_of_8.json`,
   Felder `K_a.ell_max` und `K_b.tau`). Prüfe, dass alle vorhandenen Teildateien dieselben Werte tragen, sonst Abbruch.
   Schreibe die Werte und ihre Herkunft in die Ausgabe.
2. **Rechnung genau nach v2 §9 mit dem v3-Schätzer (AML, L-BFGS):** für F1–F10, beide Domänen,
   $\eta \in \{0.01, 0.05\}$, exakte Funktionswerte, $\sigma_{\text{eff}}$ für das jeweilige $\eta$. Für jede Klasse
   **vor** der Referenzklasse: $\hat c$ auf den exakten Fit-Daten, Nichtzentralität $\lambda = T$ des Val-Tests,
   Güte $\beta$. Für die Referenzklasse: $\theta_{\hat c}$. Daraus folgt die Klasse I, N1 oder N2. Die Logik ist
   dieselbe wie bei `ex_ante_k_classes`. Teile sie, statt sie zu kopieren, sofern das ohne Verhaltensänderung für K
   geht.
3. **Ausgabe** `results/appendix_B/appendix_B.json` und `.md`, pro Zelle: Klasse, $\theta_{\hat c}$, alle früheren
   Klassen mit $\beta$, die schwächste frühere Klasse.
4. **K6-Diagnose** (v2 §12): Zähle bei $\eta = 0.01$ die breiten Zellen mit $r_{\text{ref}} \le 3$ (F1–F8), die
   in N1 oder N2 fallen. Liegt die Zahl über 1, ist „K6 würde auslösen“ = ja. Dazu die Liste der betroffenen Zellen.
   Die Markdown-Datei sagt oben in einem Satz, dass Anhang A nicht bestanden ist und dies eine Diagnose ist, kein
   Gate-Ergebnis.
5. `--workers N` (parallel über Zellen) und eine Fortschrittszeile mit Zeitstempel pro fertiger Zelle.
6. pytest: ein kleiner Fall (eine F-Zelle, eine frühere Klasse) prüft, dass die Ausgabe die Felder enthält und dass
   eine I-Zelle der K-Rechnung (K2 breit) mit der neuen Funktion dasselbe Ergebnis liefert wie in Stufe K.

## Ausführen

Wenn die Hochrechnung aus einer Zelle unter 15 Minuten mit 4 Workern liegt, führe das Skript selbst voll aus.
Sonst schreib den exakten Befehl in den Report. **Achtung:** Auf dem Laptop laufen noch zwei Stufe-K-Teile, beide
nicht anfassen. Mehr als 6 Worker sind nicht erlaubt.

## Verboten

Kein Gate-Lauf, keine Suche auf verrauschten F-Daten, keine Konstante, Schwelle oder Regel ändern, nichts außerhalb
von `experiments/annihilator_gate2a_v3/`, `codex/STATUS.md` und `codex/reports/`, kein Git außer lesend.

## Abnahme

Tests grün. Anhang B erzeugt, oder der Befehl steht im Report. Report `codex/reports/REPORT_WP_G2A3_C.md` mit der
Klassentabelle und der K6-Diagnose. `codex/STATUS.md` mit `WP-G2A3-c`.
