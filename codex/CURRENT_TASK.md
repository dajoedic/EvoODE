> **Claude-Status:** `waiting for codex` — WP-C5 übergeben, ich prüfe alle 20 Minuten.
> Melde dich über `codex/STATUS.md`, nicht in dieser Datei. Committe nichts.
> Der Dauerauftrag steht in `codex/CODEX_PROTOCOL.md`.

# WP-C5 — Das Zweifelsband wird entfernt
**Language: Julia**

## Warum

WP-V1 (`docs/WP-V1.md`, Commit `55a12f8`) hat gezeigt, dass das in WP-C4 eingeführte Zweifelsband
seinen Zweck nicht erfüllt. Über alle 80 Gleichungszeilen der 20 exakten Systeme:

| | |
|---|---|
| Cap gesetzt, korrekt | 77 |
| Cap gesetzt, falsch | 0 |
| Band **verhindert** einen falschen Cap | **0** |
| Band **nimmt einen korrekten Cap weg** | **3** |

Und der Lorenz-Fix, um dessentwillen das Band gebaut wurde, kommt nachweislich **nicht** vom Band:
Alle vier Lorenz-Zeilen liefern auch mit der binären Entscheidung Cap 3. Repariert hat es der
**Wiederaufnahme-Zweig** — die Regel, die bei einer Floor-Unterschreitung weitersucht, wenn spätere
Stufen das Residuum noch deutlich senken. Den enthält die binäre Variante ebenso.

**Entscheidung des Nutzers:** Das Band wird entfernt, der Wiederaufnahme-Zweig bleibt.

## Umfang

### Teil 1 — Zurück auf zwei Ausgänge

Die Entscheidung nach einer Floor-Unterschreitung hat wieder **zwei** Ausgänge statt drei:

- eine spätere Stufe senkt das Residuum deutlich → weitersuchen, höher deckeln
- sonst → hier deckeln

Der dritte Ausgang, die Enthaltung im Zwischenbereich, entfällt. Damit entfällt auch die zweite
Bandgrenze; es bleibt **eine** Schwelle für „deutlich".

Was mit den drei Policy-Feldern geschieht, die WP-V1 eingeführt hat
(`post_floor_clear_drop_ratio`, `post_floor_clear_no_drop_ratio`, `post_floor_min_floor_ratio`),
entscheidest du und begründest es im Report. Die verbleibende Schwelle sollte konfigurierbar bleiben
— sie ist die tragende Größe des Mechanismus, und WP-V1 hat gezeigt, dass ihre Wahl eine
wissenschaftliche Frage ist und keine Implementierungsdetail.

**Nicht betroffen und unverändert zu lassen:** die Ablehnung bei fehlender Anregung
(`_cap_residuals_uninformative_without_gain`). Sie ist ein anderer Mechanismus, war nicht Gegenstand
des Befundes und betrifft System 31 / IC 2.

### Teil 2 — Zielbild, zeilenweise

Nach der Änderung, gegen den heutigen Stand geprüft:

| Zeilen | Soll |
|---|---|
| 55 Gl. 3 und 56 Gl. 3, beide IC-Sets | Cap **3**, unverändert |
| 12 / IC 1 Gl. 1 | Cap **2** — kommt zurück |
| 31 / IC 1 Gl. 1 | Cap **3** — kommt zurück |
| 55 / IC 2 Gl. 2 | Cap **4** — kommt zurück |
| 31 / IC 2 Gl. 1 | **`nothing`**, unverändert (fehlende Anregung) |
| alle übrigen Zeilen | **unverändert**, Cap-Wert für Cap-Wert |

Erwartung: **48 endliche Caps statt 45**, weiterhin **null abgeschnittene Zeilen**. Weicht etwas
davon ab, ist das zu berichten und nicht zu erzwingen.

### Teil 3 — Fingerprints, bewusst bewegt

Die Änderung bewegt `stage_cap_behavior_fingerprint()`, und das ist beabsichtigt: Die Sonde prüft
genau die drei Ausgänge, von denen einer entfällt. Ob sich auch `config_fingerprint()` und
`phase_b_fingerprint()` bewegen, hängt von deiner Wahl in Teil 1 ab.

Alle drei alten und neuen Werte im Report festhalten. Alt:

- `config_fingerprint()` = `1d0ccf8d53c6576d`
- `phase_b_fingerprint()` = `e361a2af49366670`
- `stage_cap_behavior_fingerprint()` = `61b6548ef0014593`

Die Sonde in `src/structure/stage_cap_fingerprint.jl` enthält einen Probe-Fall
`late_floor_doubt_abstains`, der auf den entfallenden Ausgang zielt. Passe die Sonde an und erhöhe
`STAGE_CAP_BEHAVIOR_FINGERPRINT_VERSION`, damit der Wechsel als eigene Ära erkennbar ist.

### Teil 4 — Tests und Nachweis

- Die Tests aus WP-C4 zu den drei Ausgängen auf zwei Ausgänge anpassen.
- `test/test_stage_cap.jl` und `test/test_regression_runner_gate2.jl` müssen grün sein.
- Das WP-C1-Audit erneut laufen lassen, zeilenweise gegen den heutigen Stand stellen, und die
  Zeilenzahl endlicher Caps vorher und nachher berichten.

## Verboten

- **Keine Cluster-Jobs, keine Kampagne, keine Läufe auf Orion.** Dort laufen zwei
  Sondierungszellen.
- **Den Wiederaufnahme-Zweig nicht verändern** und seine Schwelle nicht auf einen anderen Wert
  setzen. Entfernt wird das Band, nicht die Regel, die Lorenz repariert.
- **`docs/wp_c1_stage_cap_horizon_audit.md` und `docs/wp_c4_stage_cap_horizon_audit.md` nicht
  anfassen** — historische Belege mit Regenerierverbot.
- **Nichts committen, nichts stagen, nichts pushen. Kein `git add -A`.**
- Nichts, was länger als 15 Minuten läuft.

## Abnahme

- Zielbild aus Teil 2 zeilenweise erfüllt, insbesondere: Lorenz bleibt bei 3, die drei Caps kommen
  zurück, keine Zeile wird abgeschnitten.
- Endliche Caps von 45 auf 48.
- Alte und neue Werte aller drei Fingerprints im Report, Sondenversion erhöht.
- Beide Testsuiten grün.
