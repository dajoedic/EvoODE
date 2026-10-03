# WP-G2A-b — Gate 2A fertigstellen: Orakel nach §3, Laufzeit, Transfer, K2/K3, Abnahme ausführen
**Language: Python**

Fortsetzung von WP-G2A (`codex/reports/REPORT_WP_G2A.md`, Status `blocked`). Der Code unter
`experiments/annihilator_gate2a/` bleibt die Basis und wird ergänzt, nicht neu geschrieben. Grundlage
unverändert und **wörtlich verbindlich:** `docs/GATE_2A.md`. Alle Regeln, Präzisierungen 1–8, die Spalten
und die Abschnitte **Verboten** und **Abnahme** aus dem WP-G2A-Auftrag gelten weiter. Der Text steht in
`git show 4b03cb7:codex/CURRENT_TASK.md`. Kannst du Git nicht aufrufen, gilt die Zusammenfassung unten.
Dieser Auftrag nennt nur, was offen ist.

## Diagnose durch Claude (gemessen)

Ein einziger Lauf (F2 breit, clean) wird nicht in 5 Minuten fertig. Ursache: `weight_tensor` wird in jeder
Klasse und in jedem der 50 Bootstrap-Replikate neu aufgebaut. Jede Zeile wird dabei über alle $N$ Punkte
ausgewertet, obwohl die Testfunktion nur auf ihrem Block lebt. Zusätzlich werden Polynome vom Grad bis
etwa 37 in der Monombasis neu zusammengesetzt. Das Orakel-JSON stammt aus der Doppelpräzisions-Variante und
erfüllt §3 nicht.

## Offene Punkte

1. **Orakel nach §3, ohne Abkürzung.** SymPy-Ableitungen, Kollokation in mpmath mit 60 Stellen auf
   mindestens 120 Punkten, Nullraum-Schwelle $10^{-35}$ relativ zum größten Singulärwert, symbolische
   Verifikation nach Abnahmepunkt 1 aus WP-G2A. Das Orakel wird **einmal** gebaut und als JSON gecacht.
   Der Cache trägt Metadaten (Verfahren, Präzision, Punktzahl, Schwelle). `run_gate2a.py` verweigert einen
   Cache ohne diese Metadaten oder mit anderen Werten. Der bestehende Doppelpräzisions-Cache wird gelöscht.
   Eine Vergleichsrechnung von Claude brauchte für zehn Funktionen auf einer Domäne mit $(r,d) \le (6,6)$
   etwa 4 Minuten. Für 20 Funktion × Domäne ist etwa das Doppelte zu erwarten. Das ist erlaubt, und der Bau
   gehört zur Abnahme.
2. **Laufzeit.** Der Gewichtstensor wird pro Gitter × Variante × {fit, val} **einmal** für die größte
   Klasse (6,6) gebaut. Jede Klasse $(r,d)$ ist eine Spaltenauswahl daraus. Jede Zeile wird nur auf den
   Samples ihres Blocks gespeichert und ausgewertet (blocklokale Slices statt voller $N$). Die Ableitungen
   von $z^j\varphi_{b,m}$ werden numerisch stabil gebildet, z. B. per Leibniz-Regel aus den Ableitungen von
   Hülle × Legendre in $u$ und von $z^j$, statt aus einem hochgradigen Monom-Polynom. Die Wahl der
   Darstellung ist frei, Abnahmepunkt 2 aus WP-G2A entscheidet. **Zielmarken, gemessen und berichtet:** ein
   vollständiger Lauf inklusive 50 Bootstrap-Replikaten für F2 breit clean unter 5 s, für F10 breit clean
   unter 30 s, auf einem Kern. Wird eine Marke verfehlt, ist das kein `blocked`. Die gemessene Zeit und die
   Hochrechnung stehen im Report.
3. **Transfer (§8)** in den Läufen der schmalen Domäne verdrahtet, Spalte `transfer_passed` gefüllt.
4. **Auswertung (§9) vollständig:** Clean- und 1-%-Bestehenskriterien, K1, K2, K3 (Standard gegen jede
   Variante S1–S11, nach der Regel in §9) und K4. E3 wird umgesetzt: `TRUE_NOT_REF` zählt nie als Bestehen
   und nie in K2. Ausgabe `results/gate2a_verdict.json` mit jedem Kriterium einzeln (Wert, Schwelle,
   Ergebnis) und dem Gesamtverdikt `PASS`, `KILL` oder `USER_DECISION`. Fehlen Varianten-Ergebnisse, lautet
   K3 `NOT_EVALUATED` statt `PASS`.
5. **Git-Hash:** Wie bisher aus `GIT_COMMIT`. Läufe ohne `--smoke` brechen ab, wenn `GIT_COMMIT` fehlt.
   Claude setzt die Variable.
6. **Abnahmetests 1–6 aus WP-G2A** als eigene Skripte unter `experiments/annihilator_gate2a/acceptance/`,
   je eines pro Punkt, jedes schreibt seine Zahlen nach `results/acceptance/<name>.json`. **Führe sie alle
   aus.** Dauert eines länger als 15 Minuten, brich es ab und gib Claude im Report den exakten Befehl. Das
   ist dann kein `blocked` für den Rest. Die Toleranzen stehen wörtlich im WP-G2A-Auftrag und werden nicht
   gelockert: starke Form $< 10^{-6}$ auf 200.000 Punkten, Annihilation $< 10^{-8}$, Monte-Carlo mit
   Ablehnungsrate in $[0, 0.03]$, $T/\text{dof}$ in $[0.85, 1.15]$ und Spur-Verhältnis in $[0.8, 1.25]$,
   Transfer-Winkel $< 10^{-10}$, Determinismus mit 1 gegen 4 Worker.
7. Danach `--smoke` mit gemessenen Zeiten und der Hochrechnung für Hauptlauf und Raster (1 und 8 Worker).

## Zusammenfassung der weiter geltenden Verbote

Kein Hauptlauf, keine Sensitivitätsvariante über die Smoke-Zellen hinaus. Keine Änderung an Konstanten
oder Regeln aus `docs/GATE_2A.md`. Nichts außerhalb von `experiments/annihilator_gate2a/` (und
`codex/STATUS.md`, `codex/reports/`). Kein `docs/`, kein Julia, kein `src/`. Keine ODE-Integration,
keine nichtlineare Optimierung, kein SR/GP. Nur NumPy, SciPy, SymPy, mpmath, pytest, optional pandas in
der Auswertung. Kein Git-Schreibzugriff. Kein Einzelkommando über 15 Minuten.

## Abnahme

Alle Punkte 1–7 erfüllt, mit Zahlen aus den Läufen dieser Sitzung im Report
`codex/reports/REPORT_WP_G2A_B.md`. Ein Abnahmetest, der an der **Sache** scheitert, besonders der
Monte-Carlo-Test der Kovarianz, heißt `blocked`, mit den gemessenen Zahlen. Die Formel wird nicht
angepasst, bis es passt. `pytest experiments/annihilator_gate2a/tests` ist grün. `STATUS.md` mit der
Kennung `WP-G2A-b`.
