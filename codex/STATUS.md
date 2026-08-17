# Codex Status

Diese Datei schreibt **nur Codex**. Claude liest sie und fasst sie nie an.
Das Gegenstück ist `codex/CURRENT_TASK.md` — die schreibt **nur Claude**, Codex liest sie nur.
So hat keine Datei zwei Schreiber und die beiden Seiten können sich nicht gegenseitig überschreiben.

Codex überschreibt diese Datei am Ende eines Arbeitspakets vollständig. Genau drei Felder:

```text
status: working | done | blocked
task:   <WP-Kennung aus CURRENT_TASK.md, z.B. WP-C3>
report: <Pfad zum Report, oder "-" wenn keiner>
note:   <eine Zeile, nur bei blocked: woran es scheitert>
```

`done` heißt: Arbeit abgeschlossen, Dateien liegen im Working Tree, **nicht committet**.
Das Committen macht Claude nach der Prüfung.
`blocked` heißt: Abnahmekriterium nicht erreichbar. Claude hält dann an und wartet auf den Nutzer.

---

status: working
task:   WP-C3
report: -
note:   -
