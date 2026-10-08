# READ_THIS_FIRST.md — Übergabe der Annihilator-Spur

**Was dieses Dokument ist:** der flüchtige Zustand zwischen zwei Sitzungen dieser Spur. Wird **immer vollständig
überschrieben**. EvoGrow und Paper 1 stehen in `..\EvoODE\READ_THIS_FIRST.md`, nicht hier.

**Stand: 2026-10-08. Die Spur ist abgeschlossen: Idee #1 ist gescheitert** (Entscheidung des Nutzers nach dem
End-to-End-Vergleich). Es läuft nichts, es gibt keinen Codex-Auftrag, und auf diesem Branch wird nicht mehr
gearbeitet.

## 1. Wo nachlesen

| Frage | Dokument |
|---|---|
| Warum gescheitert, kurz und mit Belegtabelle | `docs/IDEA_01_ANNIHILATOR_DISCOVERY.md` §12 |
| Ganze Geschichte, Gründe, Lehren, was eine Wiederaufnahme bräuchte | `docs/IDEA_01_RETROSPECTIVE.md` |
| letzte Prüfung (End-to-End v1/v2) | `docs/ODEBENCH_END2END_RESULT.md` |
| Chronologie | `DIARY.md`, Einträge ab 2026-10-04 |

Endstand im Git: Tag `idea01-annihilator-closed`.

## 2. Was noch beim Nutzer liegt (ohne Einfluss auf den Branch)

1. **Tag pushen:** `git push origin idea01-annihilator-closed`.
2. **Rohdaten aufs Orion-NFS** (2 × 910 MB, nicht in Git). Mit VPN, sobald `S:` erreichbar ist, in PowerShell aus
   dem Repository-Ordner:
   ```
   $src = "experiments\annihilator_odebench_smoke"
   $dst = "S:\BigDataOrion\data-science\joedicke\annihilator_e2e_raw"
   New-Item -ItemType Directory -Force "$dst\results_e2e", "$dst\results_e2e_v2" | Out-Null
   Copy-Item "$src\results_e2e\records.jsonl" "$dst\results_e2e\"
   Copy-Item "$src\results_e2e_v2\records.jsonl" "$dst\results_e2e_v2\"
   Copy-Item "$src\RAW_RECORDS_SHA256.txt" "$dst\"
   Get-FileHash "$dst\results_e2e\records.jsonl", "$dst\results_e2e_v2\records.jsonl" -Algorithm SHA256
   ```
   Die beiden Hashes müssen mit `RAW_RECORDS_SHA256.txt` übereinstimmen (`2f1023fb…` und `afe2c6d7…`). Erst danach
   die lokalen Rohdateien löschen.
3. **Orion:** Der abgeschlossene Job `annihilator-diag-amb` steht noch. Löschen mit
   `oc delete job annihilator-diag-amb`.
4. **Temp-Ordner** von Codex (`.codex_tmp`, `.pytest-tmp`, `.pytest_cache`, `.pytest_tmp*`) gehören dem Konto
   `CodexSandboxOffline` und lassen sich nur als Administrator löschen. Git ignoriert sie.
