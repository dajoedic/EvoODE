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
- Reports nach `codex/reports/`, benannt `REPORT_WP_<Kennung>.md`. **Niemals nach `docs/`** — dort
  liegen nur Reports, die Claude bewusst befördert hat, weil eine Entscheidung an ihnen hängt.
- Bestehende Ableitungen und Hilfsfunktionen wiederverwenden statt neu implementieren — doppelte
  Implementierungen derselben Größe laufen auseinander.
- Im Report Zahlen nennen, keine Einschätzungen. Claude prüft jede Kausalaussage gegen die
  Rohdaten; eine Behauptung, die die CSV nicht trägt, fällt auf.

## Julia kann in dieser Umgebung nicht ausgeführt werden

Codex' Sandbox startet `julia.exe` nicht — der Aufruf scheitert reproduzierbar mit
`Program 'julia.exe' failed to run: A specified logon session does not exist`. Beobachtet in WP-N1,
WP-N3 und WP-N5. **Python läuft dagegen normal**, inklusive Ausführung und Fehlerpfad-Tests
(WP-N2, WP-N6).

Folgen für Julia-Aufträge:

- Code schreiben, statisch so sorgfältig wie möglich prüfen, dann `status: blocked` melden. Das ist
  kein Scheitern, sondern der vorgesehene Weg.
- **Niemals Ergebnisse erfinden**, die einen Lauf voraussetzen. Der Report enthält die Kommandos,
  nicht deren Ausgabe.
- Zwei Kommandos in den Report: einen kurzen Testlauf über wenige Zellen (`--limit`) und den vollen
  Lauf. Der `--limit`-Pfad hat sich bewährt und spart Claude eine volle Runde.
- Weil jede Runde einen kompletten Durchlauf bei Claude kostet, gehört bei Julia-Code das **ganze
  Skript** auf Laufzeitfehlerklassen durchgesehen, die ein statischer Blick übersieht: Operationen
  auf `Set` statt `Vector`, fehlende `collect`-Aufrufe, `JSON3.Object` wo ein `Dict` erwartet wird,
  Indizierung mit `nothing`, Zugriffe auf Record-Felder, die fehlen können.

Claude führt Julia-Läufe aus und meldet Fehler mit vollständigem Stacktrace zurück.

## Fixtures werden abgeleitet, nicht erfunden

Am 2026-09-14 sind in einer Sitzung **drei** Arbeitspakete mit grünen Tests an echten Daten sofort
umgefallen — immer aus derselben Ursache:

- **WP-N15:** die Fixture gab jeder Zelle eine Liste erwarteter Terme, auch den als Surrogat
  markierten. Echte Surrogatzellen haben dort `null` — 221 von 335 Records. Das Skript erklärte
  zwei Drittel des Datensatzes für kaputt und konnte die Literaturkennzahl gar nicht berechnen.
- **WP-N16:** ein `include` innerhalb einer Funktion lief statisch sauber, scheiterte aber an Julias
  World-Age-Regeln. Der Einsprungpunkt jedes Kampagnen-Pods war betroffen.
- **WP-N18:** die Fixture gab jedem Record ein Feld `success`, das kein echter Record trägt — es ist
  eine Registry-Spalte. Das eingefrorene Go-Kriterium hätte für **jede** Zelle „nein" gesagt.

Das Muster ist immer dasselbe: die Fixture bildet ab, was der **Plan beschreibt**, nicht was die
**Pipeline erzeugt**, und prüft damit die eigene Annahme gegen sich selbst. Grüne Tests sind dann
kein Beleg, sondern eine Bestätigung des Irrtums.

Daher gilt:

- **Fixtures werden aus einem echten Record abgeleitet.** Ausgangspunkt ist eine reale Datei —
  gekürzt und angepasst, aber mit deren Feldbestand als Grundlage. Wo ein Feld für einen Fehlerfall
  verändert wird, ist die Änderung sichtbar, nicht die Grundlage.
- **Vor der Feldliste steht die Feldprüfung.** Verlangt ein Auftrag Spalten, wird jeder Name
  einzeln gegen einen echten Record geprüft und im Report mit seiner Herkunft genannt: bestehendes
  Recordfeld, neues Recordfeld, oder Analysepipeline. Die Namen im Plan sind oft keine echten
  Spaltennamen — bei WP-N16 und WP-N18 war jeweils die Hälfte anders benannt oder stammte aus einer
  anderen Schicht.
- **Ein Testergebnis wird nur berichtet, wenn es aus dem Lauf stammt**, den der Report beschreibt.
  Eine Zahl aus einem früheren Zwischenstand ist keine Abnahme.

## Der Start von Codex braucht eine Berechtigungsregel (seit 2026-09-18)

Läuft Claude Code im **Auto-Modus**, entscheidet ein Klassifizierer ohne Rückfrage über jeden
Werkzeugaufruf. `codex exec` fällt dort ohne Freigabe unter „Create Unsafe Agents" und wird
abgewiesen — der Auftrag ist dann zwar in `codex/CURRENT_TASK.md` geschrieben, aber **nie
übergeben**. Das ist ein stiller Fehler: die Übergabe sieht getan aus und ist es nicht.

Nötig ist ein Eintrag in `permissions.allow` von `.claude/settings.json`:

```json
"Bash(codex exec *)"
```

**Claude darf diese Regel nicht selbst setzen.** Der Auto-Modus blockt das Bearbeiten der eigenen
Berechtigungsdatei als „Self-Modification", und das ist richtig so — die Freigabe trägt der Nutzer
ein, über die Datei oder über `/permissions`.

**`.claude/` steht in der `.gitignore`, die Regel lebt also nur auf dem Rechner, auf dem sie
eingetragen wurde.** Auf einem frischen Klon oder einem zweiten Arbeitsplatz fehlt sie und der
stille Abbruch kehrt zurück. Deshalb steht die Anforderung hier, in einer versionierten Datei.

Der Aufruf selbst, aus dem Repository-Wurzelverzeichnis:

```
codex exec -s workspace-write "Bearbeite codex/CURRENT_TASK.md nach codex/CODEX_PROTOCOL.md."
```

Nicht `--full-auto` im Hintergrund verwenden — diese Form hat den Klassifizierer am 2026-09-18
zusätzlich ausgelöst. Ob die Regel ohne sie überhaupt nötig gewesen wäre, ist ungeprüft; mit Regel
und der obigen Form läuft der Start zuverlässig.

**Lebendprüfung nach dem Start:** CPU-Zeit des Prozesses, nicht Laufzeit. Ein hängender Start sieht
wie ein laufender aus.
