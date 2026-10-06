# WP-RC-A — Reality-Check Stufe A: direkte Sparse-Regression (Best-Subset und STLSQ)
**Language: Python**

Grundlage: `docs/REALITY_CHECK_DIRECT_REGRESSION.md` (eingefroren, vollständig lesen). Dort stehen Daten, Library,
Zulässigkeitsregel, wahre Termmengen, Verfahren, Kategorien, erfasste Größen und Entscheidungsregel verbindlich.
Dieser Auftrag sagt nur, wo und wie das gebaut wird. Bei Widerspruch gilt das Dokument; dann `blocked` melden,
nicht selbst entscheiden.

## Zu bauen

1. **Neues Modul** `experiments/annihilator_gate2a_v3/diagnostics/direct_regression_check.py`. Es nutzt aus v3 nur
   lesend `noisy_sample`, `numeric_values`, `rms`, `sigma_eff`, `FUNCTIONS`/`domain_for` und `Settings().n`. Den Wert
   von $\tau$ nimmt es aus derselben Quelle wie `ambiguity_diagnostic.diagnostic_settings()`. Den Zahlenwert nicht
   hart kodieren, aber im Test gegen $3.386508022297224\cdot10^{-7}$ prüfen. Kein anderes v3-Modul wird geändert.
2. **Library** als explizite, geordnete Tabelle (Name, Funktion) mit genau den 23 Termen aus §3, dazu die
   Zulässigkeitsregel (endlich und reell auf dem ganzen geschlossenen $[a, b]$, geprüft an $a$, $b$ und am
   Auswertungsgitter) und die wahren Termmengen $S^*$ für F1–F10 samt wahren Koeffizienten (F7:
   $\cos(1/2)$, $\sin(1/2)$; F8: $1$, $-2$).
3. **BS** genau nach §4: $k = 1 \ldots 4$, erschöpfend, Kleinste-Quadrate ohne Regularisierung,
   $T = \mathrm{RSS}/\sigma^2$, kritischer Wert `scipy.stats.chi2.ppf(0.99, n - k)`. Gewählt wird beim kleinsten $k$
   mit akzeptierter Teilmenge die mit kleinstem RSS. Gezählt werden die Fits insgesamt und die akzeptierten
   Teilmengen beim gewählten $k$.
4. **STLSQ** genau nach §4: Spalten-rms-Normierung, Schwelle 0,1, höchstens 20 Iterationen, keine Ridge-Regularisierung.
   Koeffizienten in Originaleinheiten zurückrechnen. $T$ und der kritische Wert mit $k = |S|$ werden nur berichtet.
5. **Kategorien** nach §5 (`TRUE_STRUCTURE`, `TRUE_PLUS`, `SURROGATE`, `FAIL` mit Grund) und **alle Größen** der
   Liste „Pro Realisierung erfasst“ in §5, inklusive Gitterfehler (10 000 Punkte) und Erweiterungsfehler auf
   $[b,\ b + (b-a)/2]$. `NaN` plus Grund, wenn ein gewählter Term dort nicht endlich ist.
6. **CLI** (`python -m experiments.annihilator_gate2a_v3.diagnostics.direct_regression_check`):
   - `--exact`: Implementierungsprüfung §8.1 für F1–F10 mit $\eta = 0$. Schreibt `exact_check.json`.
   - `--seeds 50000-50001` bzw. `--seeds 50000-50019`, `--functions` (Standard F1–F10): ein Record je
     (Funktion, Seed, Verfahren) als JSON-Zeile nach `records.jsonl`. Fortsetzen ohne Duplikate, wenn die Datei
     schon Records enthält.
   - `--summarize`: berechnet §6 (Gültigkeitsprüfung, $P_{\text{true}}$, $P_{\text{surr}}$, Verdikt `INVALID`,
     `STRONG_NEGATIVE` oder `OPEN`, nur BS, nur F4/F5/F8 bzw. F1/F2/F6) und §7. Für §7 liest es
     `results/diagnostic_ambiguity/orion/results/records_merged.jsonl` (Feld `state`), gepaart über Seeds
     50000–50019 und als Referenz über alle Seeds. Daneben berichtet es STLSQ und die sekundären Funktionen
     getrennt. Schreibt `summary.json` und `summary.md`. Bricht ab, wenn für F4, F5, F8 nicht genau die 20 Seeds
     50000–50019 vorliegen.
   - Ausgabeverzeichnis `experiments/annihilator_gate2a_v3/results/reality_check_direct/`, per `--outdir`
     überschreibbar. `run.log` enthält je Realisierung Funktion, Seed, Verfahren, Zahl der Fits und Sekunden,
     **aber keine Kategorie und keine Termmenge**.
7. **Tests** in `experiments/annihilator_gate2a_v3/tests/test_direct_regression_check.py`:
   - Die Library hat genau 23 Terme. Positive Domänen (F3, F4, F5, F8) lassen 23 zu, die übrigen 17, mit genau
     den sechs Ausschlüssen aus §3.
   - Jede wahre Termmenge reproduziert die wahre Funktion auf dem Gitter mit relativem Fehler unter $10^{-12}$.
   - Kategorien: Je ein Beispiel für `TRUE_STRUCTURE`, `TRUE_PLUS`, `SURROGATE` und `FAIL`.
   - BS-Auswahlregel an einem synthetischen Fall: Wenn bei $k = 1$ nichts akzeptiert ist und bei $k = 2$ zwei
     Teilmengen, wird die mit kleinerem RSS gewählt.
   - `--summarize` an einer Fixture: Das Verdikt `STRONG_NEGATIVE` kippt genau an den Schwellen 0,70 und 0,20,
     `INVALID` greift bei Kontrollen unter 0,70. Die §7-Zahl für die 100 Annihilator-Seeds ist 118/118. Die
     Annihilator-Fixture wird aus echten Records von `records_merged.jsonl` abgeleitet, nicht erfunden
     (Protokoll). Records der Baseline werden aus einem echten Record abgeleitet, den der Test mit dem Modul
     erzeugt.
   - $\tau$ entspricht dem Wert aus §2.

## Ausführen

Die neuen Tests und die bestehenden Tests in `experiments/annihilator_gate2a_v3/tests/`, außerdem `--exact`. Wenn
`--exact` nicht für alle F1–F10 `TRUE_STRUCTURE` liefert, den Befund im Report mit Zahlen nennen und **nichts** an
Library, Regel oder Schwellen ändern. **Kein** Lauf mit verrauschten Daten, kein Pilot, kein Hauptlauf. Den
startet Claude. Im Report die Zahl der Fits pro Realisierung aus `--exact` nennen (Kostenabschätzung).

## Verboten

- Jede Änderung an bestehenden v3-Dateien (Code, Tests, Ergebnisse, Records). Jede Änderung an
  `docs/REALITY_CHECK_DIRECT_REGRESSION.md`.
- Library, Schwellen, $\alpha$, $k_{\max}$, STLSQ-Schwelle oder Kategorien anders als im Dokument festlegen, auch
  nicht „zur Robustheit“.
- Neue Abhängigkeiten außer numpy und scipy (kein pysindy).
- Läufe mit $\eta > 0$.
- Git-Operationen.

## Abnahme

1. Alle neuen und alle bestehenden Tests in `experiments/annihilator_gate2a_v3/tests/` grün, kein `skip`.
2. `--exact` ist gelaufen, `exact_check.json` liegt vor, und der Report nennt für jede Funktion Kategorie, $k$,
   $T$ und die Zahl der Fits.
3. Report `codex/reports/REPORT_WP_RC_A.md`: Dateien, Kommandos, Testausgabe aus diesem Lauf und die Feldliste
   eines Records mit Herkunft je Feld.
