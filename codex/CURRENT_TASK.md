# WP-G2A3-b — Gate 2A v3: Vorzeichenfehler im AML-Gradienten
**Language: Python**

Fortsetzung von WP-G2A3-a. Grundlage unverändert: `docs/GATE_2A_v3.md` mit `docs/GATE_2A_v2.md`.

## Befund (Claude, 05.10. nachts)

Stufe K v3 lief und wurde von Claude abgebrochen. Bei K1 breit, 1 %, landet `aml_candidate` in 10 von 12 geprüften
Seeds (2, 10, …, 90) bei etwa 35° und $J \approx 290$, obwohl $J(c^*) \approx 0.09$ ist. In den übrigen Seeds
liegt sie bei 0,02–0,05°. Ursache: `aml_cost` und `aml_projected_gradient` rufen `normalize_coeffs(coeffs)` auf.
Diese Funktion dreht das Vorzeichen so, dass der betragsgrößte Eintrag positiv ist. $J$ ist gerade in $c$ und bleibt
davon unberührt. Der Gradient ist dagegen ungerade und kehrt sich um, sobald der betragsgrößte Eintrag von $x$
negativ ist. L-BFGS bekommt dann einen falschen Gradienten, und die Liniensuche bricht ab.

## Zu tun

1. `_aml_objective` und alles, was es aufruft, rechnen mit $c = x/\|x\|$ **ohne** Vorzeichennormierung. Eine
   Normierung des Vorzeichens ist nur für Ausgabe und Vergleich erlaubt, nach der Optimierung.
2. **pytest:** Der Gradient aus `_aml_objective` stimmt mit zentralen finiten Differenzen von $J(x/\|x\|)$ überein,
   und zwar an mindestens einem $x$ mit **negativem** betragsgrößtem Eintrag und an einem mit positivem.
   Zusätzlich gilt für K1 breit, 1 %, die Seeds 2, 10, 18, 26: Winkel zu $c^*$ unter 1°, $J(\hat c) \le J(c^*)
   \cdot 1.01$, `converged` gleich True.
3. Prüfe, ob dieselbe Vorzeichennormierung noch an anderer Stelle einen Gradienten oder eine Iteration verfälscht,
   etwa in der Kovarianz, bei A1 oder in der Ausrichtung im Monte-Carlo. Jede gefundene Stelle kommt mit Begründung
   in den Report. Ändere sie nur, wenn sie ebenfalls falsch rechnet.
4. Die Ausgaben des abgebrochenen Laufs unter
   `experiments/annihilator_gate2a_v3/results/calibration/` (`appendix_A_part_*`, `logs/`) werden nach
   `results/calibration/aborted_2026-10-05_sign_bug/` verschoben, nicht gelöscht.
5. Smoke: Stufe K mit `--limit`, und pytest für v3, v2 und v1.

## Verboten

Wie in WP-G2A3-a. Insbesondere: Stufe K nicht voll ausführen, keine Konstante, Schwelle oder Regel ändern, nichts
auf F1–F10 rechnen, kein Git außer lesend.

## Abnahme

Die Tests sind grün, auch die neuen Fälle aus Punkt 2. Report `codex/reports/REPORT_WP_G2A3_B.md` mit den Zahlen
der vier Seeds und den Befehlen für Stufe K. `codex/STATUS.md` mit `WP-G2A3-b`.
