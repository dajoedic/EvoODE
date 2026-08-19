> **Claude-Status:** `waiting for codex` — WP-E2 übergeben, ich prüfe alle 20 Minuten.
> Melde dich über `codex/STATUS.md`, nicht in dieser Datei. Committe nichts.
> Der Dauerauftrag steht in `codex/CODEX_PROTOCOL.md`.

# WP-E2 — Das eingefrorene Freeze-Memo wird bei jedem Lauf neu datiert
**Language: Python**

## Der Befund

WP-E1 hat den Selbstüberschreib-Fehler in den **Julia**-Studienskripten beseitigt. Die
**Python**-Auswertung hat ihn weiterhin, und dort trifft er das empfindlichste Dokument, das das
Projekt besitzt.

`analysis/scripts/aggregate/evaluate_hypotheses.py` schreibt am Ende
`docs/paper1_freeze_memo_phaseA.md` — ein Dokument, das sich selbst so beschreibt:

```text
# Paper 1 - Freeze Memo: Phase A Results
Generated: 2026-05-17T17:44:03.778186+00:00
Experiment: paper1_phaseA_v1 (300/300 runs, all success=true)

This memo defines what Paper 1 is allowed to claim.
```

Bei der Abnahme von WP-A3 wurde das Skript zur Verifikation ausgeführt — und hat das Datum auf
2026-08-19 gesetzt. Von Hand zurückgesetzt.

**Der Inhalt änderte sich nicht, und genau das ist der Punkt.** Ein eingefrorenes Dokument, das ein
neues Entstehungsdatum bekommt, behauptet, unter dem heutigen Code erzeugt worden zu sein. Wer es
später liest, hat keine Möglichkeit, das zu bemerken. Dasselbe gilt für
`analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json`.

## Umfang

### Teil 1 — Bestandsaufnahme

Welche Skripte unter `analysis/scripts/` schreiben in Pfade, die bereits belegt sind, und welche
davon schreiben in **eingefrorene** Artefakte? Als Tabelle in den Report: Skript, Ziel, eingefroren
ja/nein.

Die Kriterien für „eingefroren" stehen in `CLAUDE.md` und
`docs/paper1_study_protocol.md`; `paper1_phaseA_v1` ist es, ausdrücklich und mit Begründung.

### Teil 2 — Eingefrorene Ziele werden nicht mehr beschrieben

Ein Lauf gegen eingefrorene Daten darf sein Ergebnis nachrechnen und anzeigen, aber das
eingefrorene Artefakt **nicht überschreiben**. Wie du das löst, entscheidest du — es sollte aber
möglich bleiben, die Reproduzierbarkeit zu prüfen, denn genau dafür wurde das Skript bei WP-A3
gebraucht. Ein Weg, der beides erfüllt: nachrechnen, in ein Vergleichsziel schreiben, und melden,
ob es mit dem eingefrorenen Stand übereinstimmt.

Anforderungen:

- Ein Lauf gegen Phase A verändert `docs/paper1_freeze_memo_phaseA.md` und
  `analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json` **nicht**.
- Ob die Reproduktion mit dem eingefrorenen Stand übereinstimmt, muss aus der Ausgabe hervorgehen.
- Der Vergleich muss den **Zeitstempel ausklammern**, sonst meldet er immer eine Abweichung. Sag im
  Report, welche Felder du ausklammerst und warum genau diese.
- Der Neuaufbau von Grund auf muss weiterhin möglich sein — etwa über ein ausdrückliches Flag.
  Es darf nur nicht mehr der Standardfall sein.

### Teil 3 — Nachweis

- Prüfsumme von Memo und Diagnostics-JSON vor und nach einem Phase-A-Lauf: **unverändert**.
- Die Ausgabe zeigt, dass die Reproduktion übereinstimmt.
- Ein Test hält das fest und schlägt gegen den heutigen Stand fehl — beides belegen.

Halte dich an `analysis/CONVENTIONS.md`.

## Verboten

- **Keine Änderung an Julia-Code, an der Cap-Logik oder an irgendetwas Fingerprint-Relevantem.**
  Auf Orion laufen zwei Sondierungszellen; die 120 Regressions-Records liegen unter
  `1d0ccf8d53c6576d` / `61b6548ef0014593`.
- **Keine Cluster-Jobs, keine Kampagne, keine Läufe auf Orion.**
- **Die eingefrorenen Werte nicht „korrigieren".** Stimmt die Reproduktion irgendwo nicht überein,
  ist das ein **Befund für den Report**, keine Einladung, das Memo anzupassen. Ein solcher Fund
  wäre wichtig und gehört ausführlich beschrieben.
- **Nichts committen, nichts stagen, nichts pushen. Kein `git add -A`.**
- Nichts, was länger als 15 Minuten läuft.

## Abnahme

- Die Bestandsaufnahme aus Teil 1 liegt vor.
- Ein Phase-A-Lauf lässt Memo und Diagnostics-JSON unverändert, mit Prüfsummen belegt.
- Die Übereinstimmung der Reproduktion wird gemeldet, die ausgeklammerten Felder sind benannt.
- Der erzwungene Neuaufbau ist weiterhin möglich und dokumentiert.
- Der neue Test schlägt gegen den alten Stand fehl und gegen den neuen nicht.
