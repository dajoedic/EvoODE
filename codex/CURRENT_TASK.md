# WP-N16b — Ein Defekt aus der Abnahme von WP-N16

**Language: Julia** — Codex kann Julia hier nicht ausführen. Schreiben, als `blocked` melden,
Claude fährt die Abnahme.

## Ausgangslage

WP-N16 ist in der Substanz richtig, und die Abnahme hat die schwierigen Teile bestätigt:

- **Phase B ist unberührt:** `phase_b_fingerprint()` steht weiter auf `604e79733b22d64d`, der
  Verhaltens-Fingerprint auf `ffb0266c7913352c`.
- Die parametrisierte Supportherleitung reproduziert die alte Tabelle **datengleich** — einziger
  Unterschied ist das neue, ausdrücklich gewünschte Feld `basis_name`, und der Fingerprint
  überlebt es.
- Die kanonische Tabelle steht: **30 exakte Systeme statt 20**, neu dazu genau
  1, 5, 9, 17, 23, 43, 52, 57, 58, 59 — exakt die zehn Systeme, die `CLAUDE.md` als „scheitern
  allein am konstanten Term" führt. Kein exaktes System verloren, keine `expected_stage` verschoben.
- Das Manifest erzeugt 936 Zeilen (378 + 378 + 180), `phase_c_fingerprint=0c9672de35c75a9d`, mit
  `basis_name` und `max_fit_attempts=3` deklariert.
- Die Indexanordnung ist richtig gelöst: gekappter und ungekappter Arm wechseln sich **zeilenweise**
  ab, ein Abbruch trifft beide gleichmäßig, und C-3 liegt hinten, wo es die Paarung nicht stört.

Ein Defekt bleibt, und er ist total: **keine einzige Phase-C-Zelle läuft.**

## Der Defekt — World Age bei der verzögerten Einbindung

Der Smoke-Test auf Index 1 bricht ab:

```text
WARNING: Detected access to binding `Main.phase_c_fingerprint` in a world prior to its definition world.
ERROR: LoadError: MethodError: no method matching phase_c_fingerprint()
The applicable method may be too new: running in world age 40870, while current world is 40982.
```

Ursache: `_ensure_phase_c_config` (`run_batch_cell.jl:84`) bindet `phase_c_config.jl` **innerhalb
einer Funktion** ein, und `_batch_fingerprint` ruft unmittelbar danach `phase_c_fingerprint()` auf.
Die durch den `include` erzeugten Methoden leben in einem **neueren World Age** als die laufende
Funktion; Julia 1.12 verschärft genau das. Der Aufruf ist damit nicht bloß unsauber, er ist
unmöglich — und die Warnung sagt ausdrücklich, dass es in künftigen Versionen hart fehlschlägt.

Es sind drei Aufrufstellen betroffen (`run_batch_cell.jl:97, 105, 119`), nicht nur eine.

**Tragweite:** `run_batch_cell.jl` ist der Einsprungpunkt jedes Kampagnen-Pods. Der Fehler trifft
**jede** Phase-C-Zelle, sofort, in Pod eins. Wäre er erst auf dem Cluster aufgefallen, hätte ein
mehrwöchiger Lauf 936 Pods in Folge gegen dieselbe Zeile gefahren.

## Was zu tun ist

`phase_b_config.jl` wird auf **oberster Ebene** eingebunden (`run_batch_cell.jl:8`), unbedingt und
neben `run_regression.jl`. Für die Phase-C-Konfiguration gilt dasselbe: die Einbindung gehört
dorthin, wo sie world-age-sicher ist, nicht in eine Funktion.

Falls die verzögerte Einbindung einen Grund hatte, den ich nicht sehe — nenne ihn im Report, statt
ihn stillschweigend zu erhalten. Ich sehe keinen: Phase B macht es seit der Kampagne unbedingt, und
das Laden kostet nichts, was gegen 936 abgestürzte Pods aufwiegt.

Prüfe bei der Gelegenheit, ob dieselbe Bauart noch anderswo vorkommt — ein `include` innerhalb einer
Funktion mit unmittelbar folgendem Aufruf der so erzeugten Namen.

## Abnahmekriterien

1. Der Smoke-Test läuft durch:
   `julia --project=. --startup-file=no studies/regression/run_batch_cell.jl 1 --manifest outputs/studies/regression/phase_c/manifest.csv --output-dir outputs/studies/regression/phase_c/smoke_tasks`
2. Der erzeugte Record trägt `config_fingerprint = 0c9672de35c75a9d`,
   `basis_name = staged_polynomial_basis_with_constant`, `max_fit_attempts = 3` und ein
   **gefülltes** `executed_levels`, das sich von `n_levels` unterscheidet.
3. Eine **Phase-B**-Zelle läuft weiterhin unverändert — die Einbindung darf den bestehenden Pfad
   nicht verschieben.
4. Keine Warnung mehr über den Zugriff auf ein Binding vor seinem Definitions-World.
5. Report nach `codex/reports/REPORT_WP_N16b.md`, knapp: Ursache, Änderung, warum sie
   world-age-sicher ist, und ob die Bauart anderswo vorkommt.

Beide Läufe fährt Claude. Stütze **keine** Aussage auf einen Julia-Lauf, den du nicht selbst
ausgeführt hast.
