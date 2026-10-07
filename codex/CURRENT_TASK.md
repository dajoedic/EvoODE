# WP-E2E-A3 — End-to-End: Records aus Worker-Prozessen müssen serialisierbar sein
**Language: Python**

Grundlage: `docs/ODEBENCH_END2END.md` (eingefroren). Code: `experiments/annihilator_odebench_smoke/end2end.py` (Stand
`15bc333`).

## Befund

Der Pilot mit `--run --systems 7 3 --eta 0.0 --workers 6` brach ab, ohne einen Record zu schreiben:

```
AttributeError: Can't get local object '_fit_baseline_arrays.<locals>.fhat'
```

Der Record, den `_compute_record_task_with_seconds` aus dem Worker-Prozess zurückgibt, enthält eine lokale Funktion
(`fhat`, vermutlich über `selected_model` oder `candidate | {"fit": fit}`) und lässt sich nicht picklen. Der Test für
den Worker-Pfad ersetzte `ProcessPoolExecutor` durch einen Inline-Pool und konnte das deshalb nicht finden.

## Zu ändern

1. `fit_record` gibt einen Record zurück, der nur JSON-serialisierbare Werte enthält: dict, list, str, int, float,
   bool, None, dazu inf/nan als float. Funktionen, numpy-Arrays und pysindy-Objekte werden vor der Rückgabe entfernt
   oder in Listen bzw. Zahlen umgewandelt. Inhaltlich gehen keine Felder verloren, die heute in eine Record-Zeile
   geschrieben werden.
2. `run_command`: Scheitert ein einzelner Task im Worker, bricht nicht der ganze Lauf ab. Der Fehler wird mit Task-Key
   und Traceback in `run.log` und `failed_tasks.jsonl` geschrieben, der Lauf geht weiter. Am Ende steht in `DONE` die
   Zahl der gescheiterten Tasks. Ein erneutes `--run` versucht gescheiterte Tasks wieder, denn sie stehen nicht in
   `records.jsonl`.
3. Tests:
   - `run_command` mit **echtem** `ProcessPoolExecutor` (`workers=2`) auf dem synthetischen System, alle drei
     Methoden, ein Protokoll, $\eta = 0$. Records werden geschrieben, und `pickle.dumps(record)` sowie
     `json.dumps(record)` gelingen.
   - Ein Task, der eine Ausnahme wirft (per monkeypatch in einem echten Worker oder gleichwertig), landet in
     `failed_tasks.jsonl`, die übrigen Records werden trotzdem geschrieben.

## Ausführen

Alle Tests (`test_end2end.py`, Smoke-Tests, v3 mit `--basetemp`). **Kein** `--run` auf den Systemen 3, 7, 19, 21.

## Verboten

Andere Änderungen an Methode, Auswahlregel, Kandidaten, Library, Seeds, Toleranzen oder Metriken. Änderungen an v3,
an bestehenden Smoke-Dateien außer `end2end.py` und `test_end2end.py`, an `results*/` und `docs/`. Git-Operationen.
Nichts über 15 Minuten.

## Abnahme

1. Alle Tests grün, kein `skip`, darunter der Test mit echtem Prozess-Pool.
2. Report `codex/reports/REPORT_WP_E2E_A3.md` mit Testausgabe aus diesem Lauf.
