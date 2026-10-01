# WP-S04 — Diagnose: Was macht die Stufenkappe unter Rauschen und Ausdünnung?
**Language: Julia** (Berechnung) **und Python** (Zusammenfassung)

Backlog: `CLAUDE.md`, „Backlog Paper 1“, Track S. Freigegeben vom Nutzer am 2026-10-01. **Reine
Diagnose:** Der Code der Kappe in `src/` wird nicht geändert, keine neue Kappen-Variante,
keine Suche. Paper 1 bleibt eingefroren.

## Anlass

Stufe 2 (`DIARY.md` 2026-10-01): Unter Rauschen wird die endliche C-1-Kappe von System 17 zu
`nothing`. Die Kappe ist unabhängig von der Suche. Sie liest nur Trajektorie und Basis
(`estimate_stage_caps(traj, basis; policy)` in `src/structure/stage_cap.jl`) und lässt sich
deshalb offline in Sekunden prüfen. Vermutung, **vor** der Messung festgehalten: Unter Rauschen
dominiert der Fehler der Ableitungsschätzung das Residuum im Ableitungsraum. Der Verlauf
„deutlicher Abfall, dann Boden“ verschwimmt, positive Evidenz fehlt, und die Kappe fällt auf
`nothing` zurück. Sie wird also vorsichtig, schneidet aber nichts ab.

## Fragen (vorab festgelegt; der Report beantwortet genau diese, mit Zahlen)

- **F1 (Sicherheit):** Schneidet die Kappe unter Rauschen je eine Gleichung ab, deren wahre Terme
  oberhalb der Kappe liegen? Gleiche Definition wie im WP-C1-Prüfstand
  (`studies/lookahead/audit_exact_stage_cap_horizons.jl`, `docs/wp_c1_stage_cap_horizon_audit.md`).
  Zählung je (System, Gleichung, IC, σ, ρ, Realisierung).
- **F2 (Verhalten):** Wie verteilen sich die Kappen gegenüber sauber: gleich, enger, weiter, zu
  `nothing`? Aufgeschlüsselt nach σ, ρ und Dimension.
- **F3 (Mechanismus):** Wie sieht das Residuum im Ableitungsraum je Stufe aus, sauber gegenüber
  verrauscht? Wird der Abfall flacher, steigt der Boden, oder werden Splits unbrauchbar?
- **F4 (Machbarkeit von Ansatz 1):** Das lokale Polynom ist ein linearer Filter. Aus der
  Rauschvarianz folgt die erwartete Fehlervarianz der geschätzten Ableitung, `σ² · Σ w_i²` mit den
  Ableitungsgewichten des Filters. Berechne (a) diese Vorhersage einmal mit dem **wahren** σ²·x²
  und einmal mit einem **aus den Daten geschätzten** σ̂² (Residuen eines lokalen kubischen Fits über
  9 Punkte, Korrektur 9/5, wie in `DIARY.md` 2026-10-01). Vergleiche das (b) mit dem **gemessenen**
  Fehler der Ableitung gegenüber der wahren rechten Seite f(x_sauber) und (c) mit dem gemessenen
  Residuum der **wahren** Stufe. Gesucht ist das Verhältnis Vorhersage zu Messung, als Verteilung.

## Umsetzung

1. **Raster:** alle **21 exakten Systeme mit dim ≤ 2** (`phase_c_support.json`) × IC-Set 1 und 2 ×
   σ ∈ {0; 0,01; 0,02; 0,03; 0,04; 0,05} × ρ ∈ {0; 0,5} × Realisierung 1, 2, 3. Die Daten
   entstehen über `apply_phase_c_data_condition` (`studies/regression/phase_c_data_condition.jl`),
   dieselben Daten wie im Kampagnenpfad. Bei (0, 0) gibt es nur Realisierung 0.
2. **Kappen** mit der eingefrorenen Standard-Policy über `estimate_stage_caps`.
3. **Residuen je Stufe, Split und Gleichung** für F3/F4: über die **bestehenden** internen
   Funktionen der Kappe (`_cap_estimate_derivatives`, `_cap_splits`, `_cap_fit_eval` usw.)
   nachbauen. Dabei nichts in `src/` ändern. **Pflichtkontrolle:** Die aus den nachgebauten
   Residuen abgeleitete Entscheidung muss in jeder Zeile die Kappe von `estimate_stage_caps`
   reproduzieren. Weicht eine Zeile ab, ist der Nachbau falsch, und der Report sagt das.
4. **Kontrolle auf sauberen Daten:** Bei (0, 0) müssen die Kappen den Kappen in den C-1-Records
   (`stage_caps`, `outputs/phase_c_campaign_221a3a7/`) entsprechen, für jedes System, jedes IC-Set
   und Seed 42. Die Kappe ist seed-unabhängig.
5. **Ausgabe:** eine Zeile je (System, Gleichung, IC, σ, ρ, Realisierung) mit Kappe, Kappe sauber,
   Änderungsklasse, Abschneide-Flag, Residuen je Stufe (Median über die Splits) und den Größen aus
   F4. Dazu eine kurze Python-Zusammenfassung mit F1–F4 als Tabellen, **ohne Urteile**. Eigener
   Ausgabeordner unter `outputs/`.

## Verboten

`src/` ändern, Policy-Parameter ändern oder „ausprobieren“, eine neue Kappen-Variante bauen,
Suchen laufen lassen, Cluster, Git, `docs/`, `codex/CURRENT_TASK.md` bearbeiten. Läufe über 15
Minuten in deiner Sitzung.

## Abnahme

1. Das Julia-Skript ist geschrieben und gegen alle Includes geprüft. Im Report stehen ein
   `--limit`-Kommando (2 Systeme) und das volle Kommando für Claude, mit erwarteter Dauer.
2. Die Python-Zusammenfassung läuft in deiner Sitzung auf einer Fixture, die aus einer echten
   Kappenzeile abgeleitet ist. Die Tests sind grün.
3. Die Kontrollen aus Punkt 3 und 4 sind im Code eingebaut und melden Abweichungen laut.
4. Report `codex/reports/REPORT_WP_S04.md`, `STATUS.md` nach Protokoll. Weil Julia nicht
   ausführbar ist, ist `blocked` mit dem Vermerk *Umgebung, nicht Sache* der erwartete Abschluss.
