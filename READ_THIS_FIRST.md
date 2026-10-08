# READ_THIS_FIRST.md — Übergabe der Annihilator-Spur

**Stand: 2026-10-08, endgültig. Die Spur ist abgeschlossen: Idee #1 ist gescheitert.**

- Der Branch ist auf die Akte reduziert: Idee, Code, Ergebnisse und Weg; kein EvoGrow-Bestand mehr.
- Es läuft nichts, es gibt keinen Codex-Auftrag, und auf diesem Branch wird nicht mehr gearbeitet.
- EvoGrow und Paper 1: `..\EvoODE\READ_THIS_FIRST.md` auf `main`.

## Wo nachlesen

| Frage | Dokument |
|---|---|
| Überblick: Idee, Prüfungen, Gründe des Scheiterns | `README.md` |
| Warum gescheitert, mit Belegtabelle | `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` §12 |
| ganze Geschichte, Lehren, was eine Wiederaufnahme bräuchte | `docs/IDEA_01_RETROSPECTIVE.md` |
| letzte Prüfung (End-to-End v1/v2) | `docs/ODEBENCH_END2END_RESULT.md` |
| Chronologie | `DIARY.md` |

## Daten

- **Rohdaten End-to-End:** archiviert auf dem Orion-NFS unter `/bigdata/data-science/joedicke/annihilator_e2e_raw/`.
  Die SHA-256-Prüfsummen stimmen mit `RAW_RECORDS_SHA256.txt` überein (geprüft am 08.10.). Die lokalen Kopien im
  Worktree sind danach überflüssig und dürfen gelöscht werden.
- **Orion:** Der Annihilator-Job `annihilator-diag-amb` ist gelöscht. Von dieser Spur läuft nichts mehr.

## Was noch beim Nutzer liegt

1. **Pushen** (Branch und Tags):
   ```
   git push origin annihilator-discovery
   git push origin idea01-annihilator-archive
   ```
2. **Temp-Ordner** von Codex (`.codex_tmp`, `.pytest-tmp`, `.pytest_cache`, `.pytest_tmp*`): Sie gehören dem Konto
   `CodexSandboxOffline` und lassen sich nur als Administrator löschen. Git ignoriert sie.
3. **Optional:** den Worktree entfernen. Das geht aus `..\EvoODE` mit `git worktree remove ..\EvoODE-next --force`.
   Der Branch bleibt lokal und auf GitHub erhalten.
