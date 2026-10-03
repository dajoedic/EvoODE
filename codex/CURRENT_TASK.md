# WP-G2A — Gate 2A bauen und abnehmen (Annihilator-Discovery), ohne den Gate-Lauf
**Language: Python**

Branch `annihilator-discovery`, Worktree `EvoODE-next`. Grundlage, **wörtlich verbindlich:**
`docs/GATE_2A.md` (eingefroren). Kontext: `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md`. Wo dieser Auftrag und
`GATE_2A.md` sich zu widersprechen scheinen, gilt `GATE_2A.md`. Dann `blocked` melden, nicht auflösen.

## Ziel

Die komplette Gate-2A-Maschinerie implementieren und mit den Abnahmetests unten **beweisen, dass sie
korrekt rechnet**. Den eigentlichen Gate-Lauf (Hauptlauf und Sensitivitätsraster) startet anschließend
Claude. Diese Trennung ist Absicht: Ein Implementierungsfehler darf nie wie ein Kill der Idee aussehen, und
niemand soll die Entscheidungsregeln nach Sichtung von Ergebnissen anfassen.

## Ort und Aufbau

Alles unter `experiments/annihilator_gate2a/`. Die Aufteilung ist ein Vorschlag, die Grenzen sind Pflicht:

- `config.py`: **einzige** Quelle aller Konstanten aus `GATE_2A.md` (§1, §4, §5, §6, §10): Klassengrenzen,
  Ordnung, $N$, $B$, $M$, $q$, $\alpha$, $\sigma_{\text{floor}}$-Faktor, $B_{\text{boot}}$,
  Bootstrap-Schwelle, Noise-Level, Seeds, Funktionen und Domänen aus §2. Dazu die Sensitivitätsvarianten
  S1–S11 als benannte Überschreibungen genau **einer** Konstante.
- `functions.py`: die zehn Funktionen aus §2, numerisch (NumPy) und symbolisch (SymPy, nur fürs Orakel).
- `oracle.py`: Referenzseite nach §3, in der skalierten Koordinate $z$ jeder Domäne. Teilt **keinen** Code
  mit der Weak-Matrix. Cache als JSON unter `results/oracle_reference.json`: pro Funktion × Domäne
  $n_{\text{exact}}$ für alle 42 Klassen, die Referenzklasse und $c^*$ (normiert, Vorzeichen so, dass der
  betragsgrößte Eintrag positiv ist).
- `weak_operator.py`: Gitter, Skalierung, Blöcke, Testfunktionen, Weak-Matrix nach §5. Ableitungen der
  Testfunktionen analytisch: $(z^j\varphi_{b,m})$ ist auf seinem Träger ein Polynom in $z$. Integral per
  Trapezregel auf dem Sample-Gitter in $z$. Pro Domäne und Variante wird ein von $f$ unabhängiger
  Gewichtstensor $K[\text{Zeile}, (k,j), i]$ einmal vorberechnet. Damit gilt $A = K \cdot f$ und
  $W(c) = K \cdot c$ (Kontraktion über die Spalte). Das ist die Grundlage aller Kovarianzen und spart die
  Laufzeit.
- `operator_search.py`: Kandidat, Test, Auswahl, A1, A2 nach §6.
- `transfer.py`: schmal → breit nach §8.
- `run_gate2a.py`: CLI. Filter auf Funktion/Domäne/Noise-Level/Realisierungen, `--variant` (Standard oder
  S1–S11), `--workers` (Parallelisierung über Läufe mit `multiprocessing`, Ergebnis unabhängig von der
  Worker-Zahl), `--smoke`. Schreibt nach `results/<variant>/runs.csv` und skippt nie still.
- `evaluate_gate2a.py`: Zustände nach §7, Zellzusammenfassung, Gate-Verdikt nach §9 inklusive K1–K4,
  K3 über den Vergleich Standard ↔ Varianten. Schreibt `results/<variant>/cells.csv` und
  `results/gate2a_verdict.json`.
- `tests/`: pytest, siehe Abnahme.
- `README.md`: Zweck, Verweis auf `docs/GATE_2A.md`, die exakten Befehle für Hauptlauf, Raster und
  Auswertung.

## Mathematische Präzisierungen (gehören zur Spezifikation, nicht zur Wahl)

1. **Koordinaten.** Methode und Orakel arbeiten in $z = (x-\mu)/s$. Für das Orakel heißt das
   $\tilde f(z) = f(\mu + s z)$, abgeleitet nach $z$. Noise wird in Originalkoordinaten auf $f(x_i)$
   addiert (§4). Da $f$ nicht skaliert wird, ändert die Koordinatenwahl nur $x \to z$.
2. **Matrix linear in den Daten.** Zeile $(b,m)$, Spalte $(k,j)$:
   $A = \sum_i \omega_i\,(-1)^k (z^j\varphi_{b,m})^{(k)}(z_i)\,\tilde f_i$ mit Trapezgewichten $\omega_i$.
   Für einen Koeffizientenvektor $c$ ist $A c = W(c)\,\tilde f$ mit
   $W(c)_{(b,m),i} = \omega_i \sum_{k,j} c_{kj}(-1)^k (z^j\varphi_{b,m})^{(k)}(z_i)$.
3. **Störung eines rechten Singulärvektors** (erste Ordnung, für A1 auch für den zweitkleinsten). Mit
   $A_{\text{fit}} = U\Sigma V^\top$ und dem Noise-Anteil $E$, wobei $E v = \sigma_{\text{eff}} W_{\text{fit}}(v)\,\varepsilon$:
   $\delta v_i = \sum_{j \ne i} \dfrac{\sigma_j\, u_j^\top E v_i + \sigma_i\, u_i^\top E v_j}{\sigma_i^2 - \sigma_j^2}\, v_j$.
   Das ist linear in $\varepsilon$, also $\delta v_i = G_i \varepsilon$ und
   $\Sigma_{\hat c} = \sigma_{\text{eff}}^2 G_i G_i^\top$. Die Summe läuft über alle übrigen rechten
   Singulärvektoren, mit verrauschtem $A_{\text{fit}}$ als Plug-in. Weil $\|c\| = 1$ gilt, steht $\delta v_i$
   orthogonal zu $v_i$.
4. **Validation-Kovarianz** nach §6 Punkt 3:
   $\Sigma_\rho = \sigma_{\text{eff}}^2 W_{\text{val}}(\hat c)W_{\text{val}}(\hat c)^\top + A_{\text{val}}\Sigma_{\hat c}A_{\text{val}}^\top$.
   Fit- und Validation-Samples sind disjunkt. Proben auf einer gemeinsamen Blockgrenze haben in beiden
   Gewicht 0, weil $\varphi$ dort verschwindet. Dieser Fall wird im Code geprüft, nicht angenommen.
5. **Pseudo-Inverse und Rang.** Eigenzerlegung von $\Sigma_\rho$. Eigenwerte unter
   $10^{-12} \cdot \lambda_{\max}$ zählen als null. Dieser Wert ist eine Implementierungskonstante in
   `config.py`, kein Teil des Sensitivitätsrasters. Er wird im Report genannt.
6. **Bootstrap (A2).** Replikat $b$ des Laufs mit Realisierungs-Seed $s$ bekommt den Seed
   $10000 + 100 s + b$, $b = 0, \dots, 49$ (Clean: $s = 0$). Auf jedem Replikat läuft die vollständige Suche
   (nur Auswahl, ohne A1 und ohne Bootstrap) mit $\sqrt2\,\sigma_{\text{eff}}$ im Test.
7. **Transfer (§8).** Mit $z_n = \alpha z_b + \beta$, $\alpha = s_b/s_n$, $\beta = (\mu_b - \mu_n)/s_n$:
   $\sum c_{kj} z_n^j D_{z_n}^k = \sum c_{kj} (\alpha z_b + \beta)^j \alpha^{-k} D_{z_b}^k$.
   Das ist eine lineare Abbildung $T$ auf den Koeffizienten bei gleichem $(r,d)$. Die Kovarianz wird als
   $T\Sigma_{\hat c}T^\top$ mitgeführt, der Test ist skaleninvariant. Die breite Realisierung bekommt den
   Seed $s + 1000$.
8. **Koeffizientenwinkel:** $\arccos\min(1, |\langle \hat c, c^*\rangle|)$, beide normiert. Nur wenn die
   gewählte Klasse gleich der Referenzklasse ist, sonst leer.

## runs.csv: eine Zeile pro Lauf

Mindestens: Variante, Funktion, Domäne, $\eta$, Seed, gewählte Klasse $(r,d)$ oder leer, $C$, $T$,
Freiheitsgrade, kritischer Wert, die beiden kleinsten Singulärwerte von $A_{\text{fit}}$ der gewählten
Klasse, A1-Ergebnis, Bootstrap-Anteil, Zustand nach §7, Koeffizientenwinkel, Transfer bestanden (nur
schmal), Anzahl geprüfter Klassen, alle Konstanten der Variante, Git-Hash. Zustände exakt als
`CORRECT`, `AMBIGUOUS`, `TRUE_NOT_REF`, `WRONG`, `NONE`. Diese drei dürfen **nie** zusammengefasst werden:
`CORRECT` ≠ `TRUE_NOT_REF` ≠ `WRONG` (§11 E3). `cells.csv` weist pro Zelle die Anzahl jedes Zustands
getrennt aus.

## Verboten

- **Den Gate-Lauf ausführen:** weder den Hauptlauf über alle Zellen noch irgendeine Sensitivitätsvariante
  über mehr als die Smoke-Zellen. Erlaubt sind nur die Tests unten und `--smoke`.
- Irgendeine Konstante oder Regel aus `docs/GATE_2A.md` ändern, „verbessern“ oder umgehen, auch wenn ein
  Smoke- oder Testergebnis schlecht aussieht. Ein Abnahmetest, der an der Spezifikation scheitert, heißt
  `blocked` mit Begründung. Die Spezifikation wird nicht angepasst.
- `docs/` bearbeiten, Code außerhalb von `experiments/annihilator_gate2a/` anlegen oder ändern, `src/`,
  Julia, `benchmarks/`, `studies/` oder andere Experimente anfassen.
- ODE-Integration, nichtlineare Optimierung, Symbolic Regression, GP.
- Abhängigkeiten außer NumPy, SciPy, SymPy, mpmath, pytest. pandas nur in `evaluate_gate2a.py`, falls
  installiert. Nichts installieren.
- Git in jeder Form. Nichts, was länger als 15 Minuten läuft.

## Abnahme (wörtlich)

1. **Orakel:** reproduziert für alle 20 Funktion × Domäne die Referenzklassen der Tabelle in §2 von
   `GATE_2A.md`. In der Referenzklasse gilt $n_{\text{exact}} = 1$. Die symbolische Verifikation
   $L^*[f] \equiv 0$ ist für F1–F9 bestanden. Für F10 wird gerundet: $c^*$ mit 30 Stellen einsetzen, der
   Betrag von $L^*[\tilde f]$ liegt auf 200 Punkten unter $10^{-25}$ relativ. Die $n_{\text{exact}}$-Tabelle
   über alle 42 Klassen ist für die breite und die schmale Domäne derselben Funktion identisch
   (Identitätssatz). Laufzeit des Orakels im Report.
2. **Weak-Matrix gegen starke Form:** Für F2, F4 und F9 auf der breiten Domäne stimmt jede Zeile
   $A_{\text{val}} c$ für den Orakel-Operator und für einen zufälligen Operator der Referenzklasse mit
   $\int \varphi\,L[f]\,dz$ überein, gebildet aus analytischen Ableitungen auf einem Gitter mit 200.000
   Punkten. Relativer Fehler unter $10^{-6}$. Für den Orakel-Operator ist
   $\|A c^*\|/(\|A\|\,\|c^*\|) < 10^{-8}$ auf exakten Daten.
3. **Kovarianz per Monte-Carlo, der wichtigste Test:** F2, F4 und F9 auf der breiten Domäne,
   $\eta = 0.01$, je 1.000 Realisierungen, **mit dem vollen Verfahren**: $\hat c$ aus Fit geschätzt, getestet
   wird nur die Referenzklasse. Bestanden, wenn die Ablehnungsrate des wahren Operators bei $\alpha = 0.01$
   in $[0, 0.03]$ liegt und der Mittelwert von $T/\text{dof}$ in $[0.85, 1.15]$. Zusätzlich die empirische
   Kovarianz von $\hat c$ gegen $\sigma_{\text{eff}}^2 G G^\top$: Spur-Verhältnis in $[0.8, 1.25]$. Zahlen
   im Report. Scheitert das, ist das `blocked`. Nicht die Formel anpassen, bis es passt, sondern melden.
4. **Transfer:** Die exakte Referenz $c^*$ der schmalen Domäne, mit $T$ transformiert, ist parallel zur
   exakten Referenz der breiten Domäne (Winkel $< 10^{-10}$), für alle zehn Funktionen.
5. **Determinismus:** Zweimal derselbe Lauf, einmal mit `--workers 1` und einmal mit `--workers 4`, ergibt
   identische `runs.csv`-Zeilen.
6. **Smoke** (`--smoke`, sonst nichts): F2 breit clean, F2 breit $\eta = 0.01$ mit 2 Realisierungen,
   F10 breit clean. Jeweils Laufzeit pro Lauf messen. Daraus die **Hochrechnung** für Hauptlauf und
   Raster mit 1 und mit 8 Workern (Zahl der Läufe × gemessene Zeit, getrennt nach früh und spät stoppenden
   Funktionen). Die Smoke-Zustände stehen im Report, werden aber nicht bewertet.
7. `pytest experiments/annihilator_gate2a/tests` ist grün. Die Ausgabe gehört in den Report.
8. Report `codex/reports/REPORT_WP_G2A.md`: Testergebnisse mit Zahlen; je Regel aus `GATE_2A.md` §1–§9 die
   Code-Stelle, die sie umsetzt; die Spalten von `runs.csv` und `cells.csv`; die exakten Befehle für
   Hauptlauf, Raster und Auswertung; Abweichungen von der Spezifikation (erwartet: keine. Falls doch: einzeln
   begründet, und dann `blocked`).

`STATUS.md` nach `codex/CODEX_PROTOCOL.md`, Kennung `WP-G2A`.
