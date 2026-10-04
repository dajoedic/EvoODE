# WP-G2A2-b — Gate 2A v2: Kalibrierstufe K korrigieren, Laufzeit, Orakel und Stufe K ausführen
**Language: Python**

Fortsetzung von WP-G2A2-a (`codex/reports/REPORT_WP_G2A2_A.md`). Grundlage, **wörtlich verbindlich:**
`docs/GATE_2A_v2.md`. Der Code unter `experiments/annihilator_gate2a_v2/` wird **gezielt korrigiert**, nicht neu
geschrieben.

## Ausgangslage (Claudes Prüfung des Codes)

In Ordnung, nicht anfassen außer für die Laufzeit (Punkt 4): die stabile Leibniz-Auswertung in
`weak_operator.py`, FNS/AML, die Kovarianz erster Ordnung, der Val-Test, A1, A2, A3 und der Gradiententest.

**Akzeptierte Abweichung:** K-a vergleicht $Ac^*$ mit null statt mit einem mpmath-Integral. Das ist exakt
gleichwertig: $\int \varphi\, L^*[f]\,dz = 0$, weil $L^* f \equiv 0$ ist und alle Randterme verschwinden. Ein
hochpräzises Integral würde nur null reproduzieren. Im Report als akzeptierte Abweichung mit dieser Begründung
nennen.

Gemessen von Claude bei $N = 2000$: Der Aufbau des Gewichtstensors dauert 13 s ($\ell_{\max} = 3$), 27 s (4) und
59 s (5). `with_values` dauert 0,02 s. Eine volle Suche mit 5 Bootstrap-Replikaten dauert 27 s.

## Zu korrigieren

1. **K-c wird nicht bewertet, und das Gesamtverdikt ist falsch.** `stage_k_c` sammelt Zahlen, prüft aber keine
   Schwelle. `payload["passed"]` ist „reps == 1000“. Das würde ein falsches Bestanden in Anhang A schreiben.
   Verlangt ist exakt §10 K-c:
   - Punkte 1–3 nur für K1–K6 **und nur für Zellen der Klasse I** aus `ex_ante_k_classes` (breit, $\eta = 0.01$).
     Zellen außerhalb von I werden mit ihrer Klasse als „nicht geprüft“ ausgewiesen, nicht stillschweigend
     übersprungen.
   - (1) Ablehnungsrate $\le 0.03$ und Median $T/\text{dof}$ in $[0.8, 1.25]$.
   - (2) $\|\bar{\hat c} - c^*\| \le 0.5\sqrt{\operatorname{tr}\widehat{\operatorname{Cov}}(\hat c)}$, mit an $c^*$
     ausgerichteten Vorzeichen.
   - (3) Verhältnis empirische Spur zu mittlerer **propagierter** Spur $\operatorname{tr}\Sigma_{\hat c}$ in
     $[0.5, 2]$. Die propagierte Spur wird pro Realisierung erfasst.
   - (4) Clean auf K1–K8, beide Domänen, mit der **vollen Suche aus §6 einschließlich Bootstrap**. Breit muss
     `CORRECT` herauskommen, schmal nie `WRONG`.
   - Jeder Punkt bekommt Zahlen und `passed`. Gesamtverdikt = K-a ∧ K-b ∧ alle K-c-Punkte.
2. **Ergebniszustände in K-c (4)** genau nach §7: `CORRECT`, `AMBIGUOUS` (A1/A2/A3, mit Quelle), `TRUE_NOT_REF`
   (über $n_{\text{exact}}$ der gewählten Klasse aus dem v2-Orakel), `WRONG`, `NONE`. Heute wird ein ambiges
   Ergebnis in der richtigen Klasse als `WRONG` gezählt. Ohne das v2-Orakel lässt sich `TRUE_NOT_REF` nicht
   bestimmen. Dann bricht Stufe K mit einer klaren Meldung ab.
3. **`--part` überschreibt Anhang A.** Jeder Teil schreibt in eine eigene Datei, und ein eigener Merge-Schritt
   setzt die Teile zusammen. Der Merge verweigert ein unvollständiges Set (fehlende Seeds) und schreibt erst dann
   `appendix_A.json` und `.md`. Die Markdown-Datei enthält die Tabellen aller Prüfungen, nicht nur drei Zeilen.
4. **Laufzeit, verhaltensneutral.** Der Gewichtstensor hängt nur vom $z$-Gitter, $N$, $\ell_{\max}$, $q$ und $M$
   ab. Er hängt **nicht** von der Funktion oder Domäne ab, weil jede Domäne auf dasselbe $z \in [-1, 1]$ skaliert
   wird. Er wird pro Prozess **einmal je Konfiguration** gebaut und wiederverwendet (für K-a, K-b, ex-ante, K-c
   und `run_gate2a`). Ein Festplatten-Cache ist erlaubt, wenn sein Schlüssel alle diese Größen enthält. Ebenso
   werden die spaltenindizierten Kopien in `WeightContext.split` pro Klasse höchstens einmal angelegt und nicht pro
   Aufruf. Danach wird die volle Suche profiliert und der größte verbleibende Posten benannt. Zulässig sind nur
   Optimierungen, die das Ergebnis **bitgleich** lassen. Nachweis: Auf einer K-Zelle bei 1 %, Seed 0, mit 5
   Bootstrap-Replikaten sind alle Felder vor und nach der Optimierung bitgleich (ohne Laufzeit). Der Nachweis kommt
   als pytest-Fall oder Abnahmeskript, mit Zahlen im Report.
5. **Orakel lauffähig machen.** `accept_01_oracle` ohne `--limit` muss sich parallelisieren (`--workers`) und in
   Teile zerlegen lassen (`--part`, mit Merge wie in Punkt 3). Zusätzlich prüft es für K1–K8: Die
   Referenzkoeffizienten in `config.calibration_reference_coeffs` stimmen mit $c^*$ aus dem Orakel überein
   (Winkel $< 10^{-20}$). Stufe K liest $n_{\text{exact}}$ für `TRUE_NOT_REF` aus dem v2-Orakel-Cache.
6. **Aufräumen:** Aus `experiments/annihilator_gate2a_v2/` entfernen, was aus v1 kopiert wurde und nicht zu v2
   gehört: `acceptance/accept_02` bis `accept_06` (die Abnahme auf dem Gate-Set nach §11 ist ein späteres
   Arbeitspaket), `results/acceptance/accept_02` bis `06*.json`, das kopierte `results/oracle_reference.json` und
   das leere `results/standard/`.

## Ausführen

Erst `pytest` für v2 und v1. Dann, jeweils unter 15 Minuten pro Einzelkommando:
- Orakel voll, in Teilen und mit Workern, danach Merge;
- Stufe K: K-a, K-b, ex-ante und K-c (4) voll; K-c (1–3) in Teilen über die Seeds, danach Merge.

Was nicht in 15 Minuten pro Kommando passt, steht als exakter Befehl im Report. Claude führt es aus.
**Hochrechnung** aus gemessenen Zeiten, nach der Optimierung, für den späteren Gate-Hauptlauf (20 clean +
400 × 1 % + 400 × 5 %, je 50 Bootstrap-Replikate) und das Raster (16 Varianten × (20 + 400)), mit 1 und 8
Workern. Das ist eine Projektion, kein Beleg.

## Verboten

Wie in WP-G2A2-a. Insbesondere: keine Rechnung auf F1–F10 außer im Orakel, keine Konstante, Schwelle oder Regel
aus der Spezifikation ändern, keine Toleranz lockern, kein Git außer lesend, nichts außerhalb von
`experiments/annihilator_gate2a_v2/`, `codex/STATUS.md` und `codex/reports/`.

## Abnahme

- Die Punkte 1–6 sind umgesetzt, und `pytest` für v2 und v1 ist grün.
- Bitgleichheitsnachweis aus Punkt 4 mit Zahlen.
- Orakel-JSON und Anhang A existieren, oder der Report nennt die exakten Befehle für die fehlenden Teile.
- Report `codex/reports/REPORT_WP_G2A2_B.md` mit allen Zahlen aus **diesen** Läufen, je Prüfpunkt bestanden oder
  nicht, plus Hochrechnung.
- `codex/STATUS.md` mit der Kennung `WP-G2A2-b`. `done` = Anhang A vollständig erzeugt (egal ob er besteht oder
  scheitert; ein Scheitern ist ein Ergebnis und kein Blocker). `blocked` = etwas ließ sich nicht ausführen, oder
  die Implementierung kommt nicht weiter.
