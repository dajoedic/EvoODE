# Dauerauftrag für Codex — Zusammenarbeit mit Claude

Diese Datei ist die stehende Arbeitsanweisung für Codex. Sie ändert sich nicht von Aufgabe zu
Aufgabe. Der jeweils aktuelle Auftrag steht in `codex/CURRENT_TASK.md`.

**Seit 2026-08-21 wird Codex direkt gestartet.** Claude ruft nach dem Schreiben eines Auftrags
selbst `codex exec` auf und übergibt darin den Verweis auf `codex/CURRENT_TASK.md`. Es gibt
**keinen Polling-Takt mehr**: Eine Sitzung beginnt mit einem Auftrag und endet mit dem
`STATUS.md`-Eintrag. Wer diese Datei in einer laufenden Sitzung liest, hat seinen Auftrag bereits.

## Rollen

Claude ist Architekt und schreibt die Arbeitspakete. Codex ist Umsetzer und schreibt Code.
Claude prüft, committet und dokumentiert. **Codex committet nie.**

## Die beiden Dateien

| Datei | Schreibt | Liest |
|---|---|---|
| `codex/CURRENT_TASK.md` | nur Claude | nur Codex |
| `codex/STATUS.md` | nur Codex | nur Claude |

Keine Datei hat zwei Schreiber. **Codex bearbeitet `CURRENT_TASK.md` niemals** — auch nicht, um
eine Fertigmeldung hineinzuschreiben. Rückmeldungen laufen ausschließlich über `STATUS.md`.

## Ablauf je Sitzung

1. `codex/CURRENT_TASK.md` lesen. Steht dort „Kein aktiver Task", ist nichts zu tun — dann
   `STATUS.md` nicht anfassen und die Sitzung beenden.

2. Als **erste** Handlung `STATUS.md` auf `working` mit der WP-Kennung des Auftrags setzen. Das ist
   das Signal, dass die Sitzung läuft; ohne es kann Claude eine abgestürzte Sitzung nicht von einer
   arbeitenden unterscheiden.

3. Den Auftrag umsetzen. Die Abschnitte **Verboten** und **Abnahme** gelten wörtlich.

4. Als **letzte** Handlung `STATUS.md` vollständig überschreiben — `done` oder `blocked`.

`CURRENT_TASK.md` wird dabei niemals bearbeitet, auch nicht für eine Fertigmeldung. Rückmeldungen
laufen ausschließlich über `STATUS.md`.

## STATUS.md — genau vier Felder

```text
status: working | done | blocked
task:   <WP-Kennung, z.B. WP-C3>
report: <Pfad zum Report, oder ->
note:   <eine Zeile; bei blocked: woran es scheitert>
```

- `done` — Arbeit fertig, alle Dateien liegen **uncommittet** im Working Tree.
- `blocked` — das Abnahmekriterium des Auftrags ist nicht erreichbar. Das ist ein **gültiges
  Ergebnis**, kein Fehler. Nicht erzwingen, nicht umdeuten, nicht die Anforderung aufweichen.
  In `note` in einem Satz sagen, woran es liegt, und im Report ausführlich.

## Harte Regeln

- **Nicht committen, nicht stagen, nicht pushen.** Claude erkennt fertige Arbeit am Working Tree;
  committete Arbeit ist für ihn unsichtbar. Fertige Dateien bleiben liegen.
- **Kein `git add -A`** und keine Git-Operationen überhaupt.
- **Keine Cluster-Jobs, keine Kampagne, keine Regressionsläufe, keine Sondierungsläufe** — weder
  starten noch Manifeste dafür erzeugen. Auch dann nicht, wenn es naheliegt.
- **Nichts, was länger als 15 Minuten läuft.** Wenn doch: abbrechen, `blocked` melden, im Report
  sagen warum.
- Der Auftrag hat immer einen Abschnitt **Verboten** und einen Abschnitt **Abnahme**. Beide gelten
  wörtlich. Abnahmekriterien sind nicht verhandelbar und werden nicht sinngemäß ausgelegt.

## Julia-Läufe in der Codex-Sitzung

Zweimal blockiert (WP-H7, WP-R1): Julia startet in der Sandbox nicht, Meldung
`SystemError: longpath: Access is denied` beim Laden von `Pkg`. Ursache ist mit hoher
Wahrscheinlichkeit das Julia-Depot unter `~/.julia` — es liegt **außerhalb** des beschreibbaren
Workspace. Claude startet Julia-Pakete deshalb künftig mit einem zusätzlichen Verzeichnis:

```text
codex exec -s workspace-write --add-dir <Julia-Depot> ...
```

Falls Julia trotzdem nicht startet: **Das ist kein Grund, den Auftrag zu verwerfen.** Umsetzung
fertigstellen, `blocked` melden, im `note`-Feld ausdrücklich *Umgebung, nicht Sache* schreiben und
im Report festhalten, welche Abnahmepunkte deshalb offen sind. Claude fährt die Abnahme dann selbst.
Nicht mit anderen Julia-Versionen ausweichen — das Projekt ist auf 1.12.6 gepinnt, und ein Lauf
unter 1.11.5 wäre keine gültige Abnahme.

**Was dabei trotzdem von dir erwartet wird:** Ein Skript, das nie gelaufen ist, ist ungeprüft.
Lies es vor der Abgabe gegen die Dateien, die es einbindet — WP-R1 scheiterte an einem fehlenden
`include`, also an etwas, das ohne Ausführung sichtbar gewesen wäre.

## Handwerkliches

- Die zweite Zeile jedes Auftrags nennt die Sprache: `**Language: Julia**` oder
  `**Language: Python**`.
- Code, Kommentare und Docstrings auf **Englisch**. Reports dürfen englisch sein.
- Jedes Skript schreibt in seinen **eigenen** Unterordner unter `outputs/`, nie direkt hinein.
- Reports nach `docs/`, benannt nach der WP-Kennung.
- Bestehende Ableitungen und Hilfsfunktionen wiederverwenden statt neu implementieren — doppelte
  Implementierungen derselben Größe laufen auseinander.
- Im Report Zahlen nennen, keine Einschätzungen. Claude prüft jede Kausalaussage gegen die
  Rohdaten; eine Behauptung, die die CSV nicht trägt, fällt auf.
