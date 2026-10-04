# WP-G2A-c — Gate 2A: Abnahmeskripte und vier Code-Stellen auf die Spezifikation bringen
**Language: Python**

Fortsetzung von WP-G2A-b (`codex/reports/REPORT_WP_G2A_B.md`). Grundlage unverändert und **wörtlich
verbindlich:** `docs/GATE_2A.md` und die Abnahmepunkte 1–8 aus dem WP-G2A-Auftrag (der Text steht in
`git show 4b03cb7:codex/CURRENT_TASK.md`, die Punkte sind unten wiederholt). Code unter
`experiments/annihilator_gate2a/` wird **gezielt korrigiert**, nicht neu geschrieben.

## Ausgangslage

Claude hat den Code gegen die Spezifikation gelesen. Die Kernformeln in `operator_search.py` (Kandidat,
Störung des Singulärvektors, Validation-Kovarianz, Test, A1, A2) und die Transfer-Matrix in `transfer.py`
entsprechen der Spezifikation. **Nicht** entsprechen ihr die folgenden Stellen. Das Orakel mit 60 Stellen
hat Claude bereits gebaut, der Cache liegt unter `results/oracle_reference.json` mit gültigen Metadaten.
**Nicht neu bauen**, kein `force=True`.

## Zu korrigieren

1. **`accept_01_oracle.py`:** liest den vorhandenen Cache (kein Neubau) und prüft wörtlich Abnahmepunkt 1:
   - Referenzklassen für alle 20 Funktion × Domäne;
   - $n_{\text{exact}} = 1$ in der Referenzklasse;
   - die $n_{\text{exact}}$-Tabelle über alle 42 Klassen identisch für breit und schmal derselben Funktion;
   - für F1–F9 die **symbolische** Verifikation. Die Koeffizienten des Caches werden über das Verhältnis zum
     betragsgrößten Eintrag rationalisiert (`nsimplify` mit den exakten Funktionsparametern), danach muss
     $L^*[\tilde f]$ mit SymPy exakt zu 0 vereinfachen. Gelingt die Rationalisierung für eine Funktion
     nicht, wird das als solches berichtet, nicht still übersprungen;
   - für F10 die Hochpräzisionsprüfung: $c^*$ mit 30 Stellen neu bestimmt (mpmath-Nullraum der
     Referenzklasse mit 60 Stellen), $|L^*[\tilde f]|$ auf 200 Punkten unter $10^{-25}$ relativ zu
     $\max_k \|c_k \tilde f^{(k)}\|$.

   Alle Einzelergebnisse und ein Gesamt-`passed` gehen ins JSON. Die schwächere Prüfung in
   `oracle._verify_reference` darf bleiben, ersetzt den Abnahmepunkt aber nicht.
2. **`accept_02_weak_strong.py`** prüft bisher nur die Annihilation. Verlangt ist der Vergleich mit der
   **starken Form**: Für F2, F4 und F9 auf der breiten Domäne, mit Standard-Einstellungen ($N = 2000$),
   wird jede Zeile von $A_{\text{val}}c$ verglichen mit $\int \varphi_{b,m}\,L[\tilde f]\,dz$. Dieses
   Integral entsteht aus den analytischen Ableitungen von $\tilde f$ (SymPy → NumPy) und den Werten der
   Testfunktion selbst, ohne partielle Integration, auf einem Gitter mit 200.000 Punkten. Das geschieht
   für zwei Operatoren: (a) $c^*$ aus dem Orakel, (b) ein fester zufälliger Vektor der Referenzklasse
   (Seed 0). Bestanden, wenn der relative Fehler (Zeilennorm der Differenz durch Zeilennorm der starken
   Form) in (b) unter $10^{-6}$ liegt **und** für (a) $\|A c^*\| / (\|A\|\,\|c^*\|) < 10^{-8}$ auf exakten
   Daten gilt. Wird die Grenze $10^{-6}$ verfehlt, ist das ein Befund über die Weak-Matrix (z. B. die
   Monom-Darstellung der Testfunktionen vom Grad ~37). Dann die gemessenen Zahlen berichten und `blocked`
   melden. Die Toleranz bleibt.
3. **`accept_03_covariance_mc.py`** testet bisher $c^*$ mit Koeffizienten-Kovarianz null. Damit ist genau
   der Teil ungetestet, auf den es ankommt. Verlangt ist das **volle Verfahren**: Je Realisierung wird
   $\hat c$ aus $A_{\text{fit}}$ geschätzt (kleinster rechter Singulärvektor der Referenzklasse), dann mit
   `coefficient_covariance` und `test_operator` getestet, also exakt der Code-Pfad von `search_once`
   (`forced_class` benutzen oder denselben Funktionen folgen, nichts duplizieren). F2, F4, F9 breit,
   $\eta = 0.01$, Seeds 0–999. Berichtet und geprüft:
   - Ablehnungsrate bei $\alpha = 0.01$ in $[0, 0.03]$;
   - Mittelwert $T/\text{dof}$ in $[0.85, 1.15]$;
   - **Spur-Verhältnis** = Spur der empirischen Kovarianz der 1.000 Vektoren $\hat c$ (Vorzeichen an $c^*$
     ausgerichtet) durch den Mittelwert der Spur von $\Sigma_{\hat c}$ aus `coefficient_covariance`, in
     $[0.8, 1.25]$.

   Zusätzlich, nur berichtet: dieselben drei Zahlen **ohne** den $\Sigma_{\hat c}$-Term im Test, um zu
   sehen, was der Term bewirkt. Darf parallelisiert werden. Läuft der volle Test länger als 15 Minuten, gibt
   es `--part F2|F4|F9`. Läufe, die nicht fertig werden, nennt der Report mit Befehl.
4. **`accept_05_determinism.py`** muss **`--workers 1` gegen `--workers 4`** vergleichen (über den
   `run_gate2a`-Pfad mit `multiprocessing`), nicht zwei sequentielle Läufe. Aufgaben: F2 breit clean, F2
   breit $\eta = 0.01$ Seed 0, F7 schmal $\eta = 0.01$ Seed 0 (prüft auch den Transfer-Pfad).
   `runtime_seconds` wird ausgenommen, sonst bitgleich.
5. **`evaluate_gate2a.py`, K2:** zählt bisher alle Noise-Level. Laut §9 gilt K2 nur für **1-%-Zellen**.
   Die 5-%-Zellen sind Belastungstest und lösen nie einen Kill aus. Korrigieren und einen pytest-Fall dafür
   ergänzen: zehn gleiche `WRONG` bei 5 % ergeben kein K2.
6. **`run_gate2a.py`, Transfer:** übergibt bisher Kovarianz null. §8 und Präzisierung 7 verlangen
   $T\Sigma_{\hat c}T^\top$ mit $\Sigma_{\hat c}$ aus der Auswahl auf der schmalen Domäne. Dafür
   `Selection` um $\Sigma_{\hat c}$ der gewählten Klasse erweitern. $T$ ist `transfer_matrix`. Die
   Normierung nach der Transformation muss die Kovarianz konsistent mitskalieren.
7. **`accept_06_smoke.py`:** Die Hochrechnung nimmt bisher eine mittlere Zeit mal 820. Verlangt ist die
   Trennung nach früh und spät stoppenden Funktionen: Messung auf F2 (früh) und F10 (spät), Hochrechnung
   je Funktion nach der Referenz-Komplexität, für Hauptlauf (20 clean + 400 bei 1 % + 400 bei 5 %) und
   Raster (11 Varianten × (20 clean + 400 bei 1 %)), mit 1 und 8 Workern. Sonst wie Abnahmepunkt 6.

## Verboten

Unverändert aus WP-G2A und WP-G2A-b: kein Hauptlauf, keine Sensitivitätsvariante über die Smoke-Zellen
hinaus, keine Änderung an Konstanten oder Regeln aus `docs/GATE_2A.md`, keine Toleranz lockern. Nichts
außerhalb von `experiments/annihilator_gate2a/`, `codex/STATUS.md`, `codex/reports/`. Kein `docs/`, kein
Julia, kein `src/`. Das Orakel nicht neu bauen. Keine ODE-Integration, keine nichtlineare Optimierung,
kein SR/GP. Nur NumPy, SciPy, SymPy, mpmath, pytest, optional pandas in der Auswertung. Kein Git außer
lesend. Kein Einzelkommando über 15 Minuten.

## Abnahme

- Die Punkte 1–7 sind umgesetzt.
- `accept_01` bis `accept_06` sind **ausgeführt**, jedes mit seinem JSON unter `results/acceptance/`.
  Ausnahme: ein Lauf über 15 Minuten, dann mit Befehl im Report.
- `pytest experiments/annihilator_gate2a/tests` ist grün.
- Report `codex/reports/REPORT_WP_G2A_C.md` mit den Zahlen aus **diesen** Läufen, je Abnahmepunkt
  bestanden oder nicht.
- Ein Abnahmetest, der an der Sache scheitert, besonders 2 oder 3, heißt `blocked`, mit den Zahlen. Nicht
  die Formel drehen, bis es passt.
- `STATUS.md` mit der Kennung `WP-G2A-c`.
