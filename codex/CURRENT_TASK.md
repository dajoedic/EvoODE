# WP-N24b — Wiederholbarkeitsskript: Umgebung trennen, Shards sicher zusammenführen
**Language: Python**

## Ausführung

Lokal umsetzbar und testbar. Kein Docker nötig; den Rauchtest in Docker macht Claude.
Nichts starten, was länger als 15 Minuten läuft.

## Ausgangslage

WP-N24 (`codex/reports/REPORT_WP_N24.md`) ist im Working Tree, uncommittet. Der Harness-Teil ist
abgenommen und bleibt unverändert. Die Abweichung „30 statt 26 Zellen" ist **kein Befund**: Die 26
stammten aus einer Zählung, als das Kandidatenraster erst 427 von 504 Zellen hatte. 30 = 18
Referenz + 12 Kandidat ist richtig. `baselines/run_odeformer_repeatability.py` hat drei Fehler, die
den vollen Lauf unbrauchbar machen würden.

## Was zu tun ist

1. **Umgebung trennen.** Eine Zelle der Referenzumgebung darf nur im Referenz-Image laufen, eine
   Kandidatenzelle nur im Kandidaten-Image. Heute laufen beide gemischt im selben Prozess,
   `run_one_cell` setzt nur das Feld `environment_id`. Neu:
   - Beim Rechnen ist `--environment-id reference|candidate` Pflicht. Es laufen nur Zellen dieser
     Umgebung.
   - Vor der ersten Zelle prüft das Skript, dass die installierte Umgebung zur gewählten passt, und
     zwar über dasselbe Merkmal, das die `_wp_n23`-Records im Feld `environment` tragen (z. B. die
     torch-Version). Stimmt es nicht, bricht das Skript ab, bevor eine Zelle rechnet.
   - Die Konfiguration je Zelle kommt aus derselben Quelle wie im Grid-Lauf der jeweiligen Umgebung.
     Prüfen und im Report belegen, dass sich Referenz- und Kandidatenkonfiguration nur in den
     Feldern unterscheiden, in denen sie sich im Grid-Lauf unterscheiden. Wenn es Abweichungen
     gibt, sie beheben.
2. **Shards sicher zusammenführen.** Heute schreibt jeder Shard-Prozess am Ende `records.jsonl`,
   `records.csv` und `cell_summary.csv` in dasselbe Verzeichnis, und der letzte gewinnt. Neu:
   Shards schreiben nur die Einzelrecords (wie heute unter `records/`) und nicht gelaufene Zellen
   ebenfalls als Einzeldatei. Ein eigener Schritt `--collect` baut `records.jsonl`, `records.csv`
   und `cell_summary.csv` aus **allen** Einzeldateien eines Laufverzeichnisses. Er meldet, wie viele
   Zellen × Wiederholungen erwartet waren, wie viele vorliegen und wie viele wegen der globalen
   Zeitgrenze nicht gelaufen sind.
3. **Kleinkram.**
   - Default für `--expected-changed` auf 30, zusätzlich je Umgebung geprüft (18 / 12).
   - `--compare-modes` liest nur die Laufverzeichnisse, deren Name dem Muster
     `<umgebung>_<modus>_<shards>` folgt. Die heutige Glob-Suche nimmt auch `derive_probe_30` mit.
   - Ein Argument, das den Lauf auf die ersten n Zellen begrenzt, für den Rauchtest.
   - Die Kontrollzellen werden **je Umgebung** gewählt, 4 + 4, damit jede Umgebung eigene
     Kontrollen hat.

## Verboten

- Keine Git-Operationen.
- `baselines/harness.py` nicht verändern, außer ein Test aus Abnahme 3 zwingt dazu. Dann im
  Report begründen.
- Nichts unter `analysis/data/` verändern.

## Abnahme

1. Tests:
   - Falsche Umgebung → Abbruch vor der ersten Zelle.
   - Zwei simulierte Shards schreiben in dasselbe Verzeichnis → `--collect` enthält beide
     vollständig.
   - Nicht gelaufene Zellen erscheinen als solche.
   - Die Zellableitung ergibt 18 / 12 und je 4 Kontrollen.
2. `python -m pytest baselines/tests -q` grün.
3. Report `codex/reports/REPORT_WP_N24b.md` mit den **vollständigen `docker run`-Befehlen** nach dem
   Muster aus `codex/reports/REPORT_WP_N22.md` (Mounts von `baselines/`, `outputs/`, `analysis/`):
   - Rauchtest: 1 Zelle, 2 Wiederholungen, je Modus, je Umgebung.
   - Voller Lauf: je Umgebung `faithful` mit 4 Shards, `faithful` mit 1 Shard und `lifted` mit
     4 Shards, 3 Wiederholungen, `--max-hours 7`. Ausführungsreihenfolge **strikt nacheinander**,
     denn die Last ist die Messgröße und darf zwischen den Läufen nicht vermischt werden.
   - Die `--collect`- und `--compare-modes`-Befehle.
   - Eine Laufzeit-Obergrenze je Lauf aus den Schranken.
