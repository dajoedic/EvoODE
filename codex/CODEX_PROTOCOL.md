# Dauerauftrag für Codex — Zusammenarbeit mit Claude im 20-Minuten-Takt

Diese Datei ist die stehende Arbeitsanweisung für Codex. Sie ändert sich nicht von Aufgabe zu
Aufgabe. Der jeweils aktuelle Auftrag steht in `codex/CURRENT_TASK.md`.

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

## Ablauf, alle 20 Minuten

1. `codex/CURRENT_TASK.md` lesen und die Kopfzeile prüfen:

   | Claude-Status | Bedeutung |
   |---|---|
   | `waiting for codex` | Neuer Auftrag liegt an. Arbeiten. |
   | `checking results` | Claude prüft gerade. Nichts tun, nichts anfassen. |
   | `idle` oder „Kein aktiver Task" | Nichts zu tun. |

2. Steht dort `waiting for codex` und ist die WP-Kennung (z.B. `WP-C3`) **eine andere** als die
   zuletzt abgeschlossene: `STATUS.md` sofort auf `working` setzen und mit der Umsetzung beginnen.

3. Ist die WP-Kennung dieselbe wie die zuletzt abgeschlossene: nichts tun. Claude prüft noch.

4. Nach Abschluss der Arbeit **als letzte Handlung** `STATUS.md` vollständig überschreiben.

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
