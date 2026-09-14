# WP-N18c — Der Pilotprüfer liest die Heartbeats mit

**Language: Python**

## Ausgangslage

Der Pilot ist **gelaufen**: 16/16 Zellen in 97 Minuten auf dem Cluster, alle Pods `Completed`.
Kriterium 5 ist bereits separat bestanden — `wp_n5_ic_generalization.jl` meldet über alle 16 Zellen
`probe_ok=true`, **0 Rekonstruktionsfehler, 0 divergierte Integrationen**.

Das Go-Kriterium selbst bricht jedoch sofort ab:

```text
Error: criterion 1 failed for pilot: expected 16 records, got 228
```

## Der Defekt

`verify_phasec_p9_pilot.py:109` sammelt die Eingaben mit `records_dir.glob("cell_*.jsonl")`.

Dieses Muster trifft **auch die Heartbeat-Dateien**: eine Pilotzelle schreibt
`cell_000613.jsonl` (ein Ergebnis-Record) **und** `cell_000613.heartbeat.jsonl` (eine Zeile je
abgeschlossenem Level). Nachgezählt im echten Pilotverzeichnis:

- 16 Ergebnisdateien
- 16 Heartbeat-Dateien mit zusammen **212** Zeilen
- 16 + 212 = **228** — genau die Zahl aus der Fehlermeldung

Zu tun: Heartbeat-Dateien sicher ausschließen. Ein Ergebnis-Record je Zelle, sonst nichts.

Erwäge zusätzlich eine defensive Prüfung: eine Ergebnisdatei enthält **genau einen** Record. Kämen
mehrere, wäre das ein Hinweis auf ein anderes Dateiformat, und stillschweigend weiterzuzählen
brächte denselben Fehler in neuer Gestalt zurück.

## Warum das durch die Tests kam

Dieselbe Ursache wie dreimal zuvor, und ich habe sie diesmal mitverschuldet: Für WP-N15 stand die
Heartbeat-Abgrenzung ausdrücklich als geforderter Testfall in der Aufgabe, für WP-N18 habe ich sie
nicht wiederholt — also gab es sie nicht. Die Fixtures enthalten nur Ergebnisdateien, und damit
prüft die Suite eine Verzeichnisform, die auf dem Cluster nicht vorkommt.

`codex/CODEX_PROTOCOL.md` trägt seit `221a3a7` die Regel dazu: **Fixtures werden aus echten Daten
abgeleitet, nicht erfunden.** Hier heißt das konkret: die Fixture bildet ein Pilotverzeichnis so ab,
wie der Cluster es hinterlässt — **mit** Heartbeat-Dateien daneben.

## Abnahmekriterien

1. Ein Testfall mit Heartbeat-Dateien im Eingabeverzeichnis: sie werden nicht eingelesen, die
   Recordzahl bleibt korrekt.
2. Alle Tests grün, Fehlerfälle über **Exit-Codes** geprüft.
3. Kein anderes Verhalten geändert — insbesondere bleibt das Go-Kriterium unverändert scharf.
4. Report nach `codex/reports/REPORT_WP_N18c.md`, kurz.

Den Lauf über die echten Pilotdaten fährt Claude; der Share ist aus deiner Sitzung nicht sichtbar.
