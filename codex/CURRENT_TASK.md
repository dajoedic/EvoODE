# WP-N18b — Ein Defekt aus der Abnahme von WP-N18

**Language: Python**

## Ausgangslage

WP-N18 ist im Kern richtig, und die Abnahme hat das Wesentliche bestätigt:

- **Die Pilotauswahl stimmt exakt**: 16 Zellen, Systeme 2, 24, 52, 63, Seed 42, vier Dimensionen zu
  je vier Zellen, acht gepaarte Zellen — **alle acht benachbart** in der Indexliste. Die
  Empfehlung „Regel behalten, 16 statt 12" ist umgesetzt.
- `phase_c_fingerprint` bleibt `0c9672de35c75a9d`.
- 43 Python-Tests grün.
- Die Feldherkunftsprüfung hat geliefert, was sie sollte: „Duplikatzähler" und „Restart-Zähler"
  sind **keine** echten Spaltennamen, und der Report nennt die tatsächlichen.

Ein Defekt bleibt, und er ist blockierend.

## Der Defekt — Kriterium 1 kann auf echten Daten nicht bestehen

Der Prüfer liest die rohen `cell_*.jsonl` und verlangt je Record `success is True` sowie ein leeres
`failure_reason` (`verify_phasec_p9_pilot.py:129-132`).

**Beide Felder existieren im Record nicht.** Gegen den echten Phase-C-Smoke-Record geprüft
(`outputs/studies/regression/phase_c/smoke_tasks/cell_000001.jsonl`): `success` fehlt,
`failure_reason` fehlt, vorhanden ist allein `error` (Wert `null`). Mit sechzehn Kopien dieses
echten Records ausgeführt, meldet der Prüfer:

```text
Error: criterion 1 failed for .../cell_000001.jsonl: success is None, expected true
```

Das heißt: **der Pilot fällt durch, egal wie gut er läuft.** Und das ist die gefährlichere Hälfte —
ein Go-Kriterium, das grundlos „nein" sagt, lädt dazu ein, es abzuschwächen, statt den Fehler zu
suchen. Genau das darf bei einem eingefrorenen Kriterium nie passieren.

## Woher die beiden Namen stammen — und was daran die Lösung sein könnte

`success` und `failure_reason` sind **Registry-Spalten**, keine Recordfelder. Sie entstehen in
`convert_campaign_history_to_run_registry.py`; die WP-A8-Auswertung hat sie für Phase B genau dort
geprüft („756 Zellen mit `success == True`"). Das Go-Kriterium im Plan ist also auf der **Registry**
formuliert, nicht auf den rohen Records.

Daraus folgt eine Beobachtung, die ich dir mitgebe, ohne sie vorzuschreiben: prüfte der Pilot die
**konvertierte Registry** statt der rohen Records, dann existierten `success` und `failure_reason`
wie gemeint — **und** die Erweiterung der WP-N14-Erlaubnisliste um `manifest_index` und
`batch_output_file` würde überflüssig, weil die Registry ohnehin `campaign_manifest_index` führt,
das bereits erlaubt ist. Zwei Probleme, eine Ursache.

Entscheide den Weg selbst und **begründe ihn**. Bedingungen, die unabhängig vom Weg gelten:

- Das Kriterium wird **nicht abgeschwächt**. „`success` fehlt, also überspringen wir das" ist keine
  Lösung. Wenn die Herkunft der Spalte wechselt, muss der Prüfer sie dort auch wirklich prüfen.
- Wird weiter roh gelesen, muss der Prüfer den **tatsächlichen** Erfolgsindikator des Records
  benennen und im Report festhalten, dass `error` die Recordseite von `success` ist — eine
  Übersetzung, die dokumentiert gehört, nicht stillschweigend passiert.
- Jede verbleibende Erweiterung der Erlaubnisliste bleibt begründungspflichtig.

## Warum das dreimal hintereinander passiert ist — und was daraus folgt

Dies ist der **dritte** Fall in dieser Sitzung, in dem Tests grün sind und echte Daten den Code
sofort umwerfen:

- WP-N15: die Fixture gab jeder Zelle eine Termliste, auch Surrogaten — echte Surrogate haben dort
  `null`.
- WP-N16: der Smoke-Test auf einer echten Zelle fand einen World-Age-Fehler, der jeden Pod getötet
  hätte.
- WP-N18: die Fixture gibt jedem Record ein `success`, das echte Records nicht haben.

Das Muster ist immer dasselbe: **die Fixture wurde erfunden statt abgeleitet.** Sie bildet ab, was
der Plan beschreibt, nicht was die Pipeline erzeugt — und prüft damit die Annahme gegen sich selbst.

Zu tun: Die Fixtures dieses Pakets werden **aus einem echten Record abgeleitet** — ausgehend vom
Smoke-Record, gekürzt und angepasst, aber mit dessen Feldbestand als Grundlage. Wo ein Feld für
einen Fehlerfall verändert wird, ist die Änderung sichtbar, nicht die Grundlage.

## Abnahmekriterien

1. Der Prüfer besteht gegen **echte** Records: mit sechzehn Kopien des Smoke-Records darf
   Kriterium 1 nicht mehr an `success` scheitern. (Andere Kriterien dürfen dabei fallen — die
   Kopien sind keine echte Pilotmenge; entscheidend ist, dass **Kriterium 1 die Zelle akzeptiert**.)
2. Der gewählte Weg ist im Report begründet, und das Kriterium ist **nicht** abgeschwächt.
3. Die Fixtures stammen aus dem echten Record, nicht aus der Planbeschreibung.
4. Alle Tests grün, Fehlerfälle je Kriterium über **Exit-Codes** geprüft.
5. Report nach `codex/reports/REPORT_WP_N18b.md`, knapp, mit aktualisierter Ablaufanleitung, falls
   sich die Eingaben des Prüfers geändert haben.
