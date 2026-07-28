# CURRENT TASK: WP-T2b — Live-Beobachtbarkeit für den WP-T2-Lauf

**Language: Julia**

## Context

Das WP-T2-Skript `studies/numerics/system26_tolerance_screening.jl` ist inhaltlich fertig und
korrekt: drei Bedingungen (D8, R8, R6), Anker gegen Baseline v0, inkrementelles Flush. Ein
einziger Mangel bleibt vor dem externen Lauf: Es hat **keine Live-Ausgabe**. `verbose = 0`, kein
`level_callback`, kein `run.log`. Während der teuersten Bedingung (R6, rund 3 Stunden) sieht der
Betreiber im Terminal nichts, bis die Bedingung fertig ist.

Der Lauf dauert 5–8 Stunden und wird extern verfolgt. Ohne Live-Fortschritt ist ein Hänger nicht
von normalem Rechnen zu unterscheiden. Genau dafür wurde im Regression-Runner der
`level_callback` mit Fortschrittsanzeige gebaut; dieselbe Beobachtbarkeit fehlt hier.

Dies ist ein **rein additiver** Beobachtbarkeits-Fix. Er darf am Experiment nichts ändern: nicht an
den Bedingungen, Toleranzen, Hyperparametern, Ankerwerten, an der RNG-Nutzung, den Metriken oder
den Ausgabedateien-Inhalten. Nur zusätzliche Ausgabe zur Laufzeit kommt hinzu.

## Goal

Der WP-T2-Lauf gibt pro Level eine kompakte Live-Zeile aus, sodass der Fortschritt im Terminal
sichtbar ist, und schreibt zusätzlich ein persistentes `run.log`. Die Ergebnisse bleiben
bit-identisch zu einem Lauf ohne diesen Fix.

## Files

- **Nur ändern:** `studies/numerics/system26_tolerance_screening.jl`.
- **Nicht anfassen:** `src/`, alle anderen Skripte, die Regression-Konfiguration.

## Required Content

### 1. `level_callback` für beide Bedingungstypen

Beide Bedingungen konstruieren ihre Strategie in `build_strategy(kind)` derzeit mit
`level_callback = nothing`. Statt `nothing` wird eine Callback-Funktion übergeben, die pro Level
**eine** kompakte, sofort geflushte Zeile ausgibt. Sie erhält den Level-Snapshot (das
`level_log`-NamedTuple mit u. a. `level`, `stage`, `best_loss`, `best_objective`, `n_params`,
`elapsed_s`).

Die Zeile muss enthalten: Bedingungslabel, `level`/Gesamtzahl, `stage`, `best_loss`, Level-Laufzeit.
Beispiel-Format (Wortlaut frei, Inhalt verbindlich):
`[R6] level 14/30 stage=2 best_loss=3.51e-03 level_elapsed=224.9s`

Der Callback ist **nebenwirkungsfrei bezüglich der Suche**: Er liest nur den Snapshot und gibt aus.
Er darf den RNG nicht berühren und keine Zustandsvariable der Suche verändern. Das ist die
Bedingung dafür, dass die Ergebnisse unverändert bleiben.

### 2. `run.log` je Lauf

Zu Beginn von `main()` ein `run.log` im Ausgabeordner öffnen (`set_log_file`), am Ende schließen
(`close_log_file`). Damit landet die Level-Ausgabe zusätzlich persistent auf der Platte, nicht nur
flüchtig im Terminal. Falls die Live-Zeile aus Punkt 1 über den regulären Logger läuft, erfüllt das
beide Zwecke zugleich; andernfalls die Zeile zusätzlich in das Log schreiben.

### 3. Bedingungswechsel sichtbar machen

Beim Start jeder Bedingung eine Zeile ausgeben, welche Bedingung mit welcher Toleranz nun läuft
(die vorhandene `println("Running condition ...")` genügt, sofern sie geflusht wird). Nach jeder
Bedingung eine Abschlusszeile mit Gesamtlaufzeit der Bedingung.

### 4. Keine semantische Änderung

`verbose` in `build_options` darf angehoben werden, **falls** das nötig ist, damit der
`level_callback` feuert — aber nur, wenn das die numerischen Ergebnisse nachweislich nicht
verändert. Falls eine `verbose`-Anhebung die interne Logmenge oder das Verhalten beeinflusst, statt
dessen den `level_callback` unabhängig von `verbose` wirken lassen. Im Zweifel: `verbose` so
lassen, wie es ist, und die Sichtbarkeit allein über den `level_callback` herstellen.

Anker, Bedingungen, Toleranzen (1e-6 / 1e-8), Hyperparameter, RNG-Seed und alle Ausgabedatei-
Schemata bleiben unverändert.

## Verification

**Den System-26-Lauf NICHT starten.** Er dauert Stunden und wird ausschließlich extern gestartet.

Erlaubt ist nur der billige Smoke-Test auf **System 3** mit reduziertem Budget:

```
EVO_T2_SYSTEM_ID=3 EVO_T2_N_LEVELS=4 julia studies/numerics/system26_tolerance_screening.jl
```

Damit bestätigen:
1. Pro Level erscheint eine Live-Zeile im Terminal, für alle drei Bedingungen.
2. `run.log` wird geschrieben und enthält die Level-Zeilen.
3. Die numerischen Ergebnisse des Smoke-Tests (Loss, `final_stage`, `pruned_match` je Bedingung)
   sind **identisch** zu einem Lauf ohne den Fix. Prüfe das, indem du vor und nach der Änderung
   denselben Smoke-Test rechnest und die Werte vergleichst — sie müssen übereinstimmen, sonst ist
   der Fix nicht rein additiv.

Der Smoke-Test läuft auf System 3 in Sekunden. Nach dem Smoke-Test die Ausgabedateien im
Zielordner nicht als Ergebnis missverstehen; sie stammen vom Testsystem.

Im Abschlussbericht: dass der Fix rein additiv ist (Ergebnisvergleich bestanden), wie die
Live-Zeile aussieht, und der Startbefehl für den externen System-26-Lauf.

## Constraints

- Reiner Beobachtbarkeits-Fix. Keine Änderung an Bedingungen, Toleranzen, Hyperparametern,
  Ankerwerten, RNG-Nutzung, Metriken oder Ausgabedatei-Inhalten.
- Der `level_callback` ist nebenwirkungsfrei bezüglich der Suche.
- `src/` bleibt unangetastet.
- Den System-26-Lauf nicht ausführen; nur der System-3-Smoke-Test ist erlaubt.
- Keine neuen Abhängigkeiten (`ProgressMeter` ist bereits vorhanden, falls ein Balken statt einer
  Zeile gewünscht ist — beides ist akzeptabel).
