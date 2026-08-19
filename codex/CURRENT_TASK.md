> **Claude-Status:** `waiting for codex` — WP-V1 übergeben, ich prüfe alle 20 Minuten.
> Melde dich über `codex/STATUS.md`, nicht in dieser Datei. Committe nichts.
> Der Dauerauftrag steht in `codex/CODEX_PROTOCOL.md`.

# WP-V1 — Erkennt der Controller seine eigene Unzuverlässigkeit?
**Language: Julia**

## Warum

Der Stage-Cap funktioniert, aber die Aussage „er schneidet nichts ab" ist derzeit eine Beobachtung
auf denselben Daten, an denen die Entscheidungsregel gewählt wurde. Für Paper 1 fehlen genau zwei
Dinge, und beide sind aus vorhandenen Daten beantwortbar.

**Erstens der Betriebspunkt.** Ein Controller, der sich im Zweifel enthält, hat zwei Fehlerarten mit
völlig verschiedenen Kosten:

|  | Cap gesetzt | Cap enthält sich (`nothing`) |
|---|---|---|
| Cap wäre **korrekt** (>= benötigte Stufe) | richtig festgelegt | **unnötige Enthaltung** — kostet Rechenzeit |
| Cap wäre **falsch** (< benötigte Stufe) | **falsche Festlegung** — kostet die Lösung | **richtig erkannt** |

Die entscheidende Zelle ist die falsche Festlegung. Ist sie leer, lautet die Aussage: *Der Controller
legt sich nie falsch fest, und der Preis dafür sind N unnötige Enthaltungen.* Das ist belastbar. Der
heutige Stand deutet auf 45 korrekte Festlegungen, null falsche und drei bis vier Enthaltungen hin —
zu prüfen, nicht zu übernehmen.

**Zweitens die Wahl der Bandgrenzen.** `0.35`, `0.62` und `0.1` wurden anhand derselben 20 Systeme
festgelegt, gegen die sie validiert werden. Das ist der angreifbarste Punkt der Arbeit. Eine
Leave-one-system-out-Prüfung beantwortet ihn.

## Umfang

Drei Teile. **Teil 3 hängt von Teil 2 ab** — siehe dort.

### Teil 1 — Die Konfusionsmatrix über alle 80 Gleichungszeilen

Für jede der 80 `(System, IC-Set, Gleichung)`-Zeilen der 20 exakten Systeme:

- die benötigte Stufe, aus `phase_b_support.json` abgeleitet wie im WP-C1-Audit — **wiederverwenden,
  nicht neu implementieren**
- den Cap, den der aktuelle Stand liefert
- den Cap, den dieselbe Logik **ohne** Zweifelsband liefern würde, also mit der binären Entscheidung
  wie vor WP-C4

Daraus die Matrix. Die Spalte „wäre falsch" bezieht sich auf den Cap **ohne** Band: Was hätte der
Controller getan, wenn er sich hätte festlegen müssen?

Zusätzlich je Zeile ausgeben, welche Größe die Enthaltung ausgelöst hat, damit die Fälle einzeln
nachvollziehbar bleiben.

**Wichtig:** Es geht nicht darum, eine gute Zahl zu erzeugen. Findet sich eine **falsche
Festlegung**, ist das der wichtigste Befund des Auftrags und gehört an den Anfang des Reports.

### Teil 2 — Sind die Bandkonstanten injizierbar, ohne die Fingerprints zu bewegen?

Die drei Konstanten sind derzeit `const` in `src/structure/stage_cap.jl` und damit weder
konfigurierbar noch in einem Fingerprint enthalten. Für Teil 3 müssen sie von außen setzbar sein.

Prüfe zuerst und berichte, **ob** sich das erreichen lässt, ohne dass sich

- `config_fingerprint()` = `1d0ccf8d53c6576d`,
- `phase_b_fingerprint()` = `e361a2af49366670` und
- `stage_cap_behavior_fingerprint()` = `61b6548ef0014593`

verändern. Alle drei müssen **exakt** stehen bleiben; unter ihnen liegen 120 abgeschlossene
Regressions-Records. Der Weg dahin ist deine Entscheidung.

**Bewegt sich einer der drei Werte, brich Teil 2 ab, führe Teil 3 nicht aus und berichte das.** Dann
entscheidet der Nutzer, ob die Fingerprints bewegt werden dürfen. Das ist ein gültiger Ausgang, kein
Fehlschlag.

### Teil 3 — Leave-one-system-out, nur bei gelungenem Teil 2

Für jedes der 20 exakten Systeme: Bandgrenzen auf den **übrigen 19** Systemen wählen, dann auf dem
ausgelassenen System auswerten und dort die Matrix aus Teil 1 bilden.

Wie „auf 19 Systemen wählen" konkret aussieht, entwirfst du und begründest es im Report — etwa die
Grenzen so legen, dass auf den 19 Systemen keine falsche Festlegung entsteht und die Zahl der
Enthaltungen minimal bleibt. Entscheidend ist allein, dass das ausgelassene System die Wahl **nicht
beeinflusst**.

Ergebnis: die aggregierte Konfusionsmatrix über alle 20 Auslassungen, gegen die In-Sample-Matrix aus
Teil 1 gestellt. Dazu der Wertebereich, den die Grenzen über die 20 Durchläufe annehmen — schwanken
sie stark, sind sie datenabhängig, und das gehört gesagt.

## Verboten

- **Keine Änderung an den Default-Werten** von `0.35`, `0.62`, `0.1`, `tau_rel`, `tau_abs`,
  `lookahead_horizon` oder irgendeiner anderen Policy-Konstante. Teil 2 macht sie setzbar, nicht
  anders.
- **Keine Cluster-Jobs, keine Kampagne, keine Läufe auf Orion.** Dort laufen zwei Sondierungszellen.
- **Kein Anpassen der Bandgrenzen an das Ergebnis.** Zeigt Teil 3, dass die Grenzen out of sample
  schlechter abschneiden, ist das der Befund. Nicht nachbessern.
- **Keine Ground-Truth in `estimate_stage_caps`.** Die benötigte Stufe wird ausschließlich außerhalb
  zur Bewertung verwendet.
- **Nichts committen, nichts stagen, nichts pushen. Kein `git add -A`.**
- Nichts, was länger als 15 Minuten läuft. Alles hier rechnet Ableitungsregressionen, keine Fits.

## Abnahme

- Die Konfusionsmatrix über 80 Zeilen liegt vor, alle vier Zellen beziffert.
- Jede Enthaltung ist einzeln aufgeführt, mit der auslösenden Größe.
- Eine etwaige falsche Festlegung steht am Anfang des Reports.
- Für Teil 2 ist belegt, dass alle drei Fingerprints unverändert sind — oder begründet, dass es
  nicht geht.
- Bei gelungenem Teil 2: die Out-of-Sample-Matrix und der Wertebereich der Grenzen.
