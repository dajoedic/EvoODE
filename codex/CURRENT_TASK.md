> **Claude-Status:** `waiting for codex` — WP-B1 übergeben. Melde dich über `codex/STATUS.md`,
> nicht in dieser Datei. Committe nichts.
> Der Dauerauftrag steht in `codex/CODEX_PROTOCOL.md`.

# WP-B1 — Wie viele Suchlevel sind verschwendet? Messen, nicht reparieren
**Language: Julia**

## Warum

System 59 steht ab Level 21 unverändert bei Loss 4,082 und läuft trotzdem bis Level 30. Neun von
dreißig Leveln verbessern nichts, und weil die Levelkosten mit der Strukturgröße stark wachsen, ist
der verschwendete Anteil an der Rechenzeit deutlich größer als der an der Levelzahl.

Das ist eine Beobachtung an **einer** Zelle. Bevor irgendeine Abbruchregel entworfen wird, muss die
Verteilung über alle vorliegenden Läufe bekannt sein.

**Dieser Auftrag baut ausdrücklich keine Abbruchregel.** Er misst nur. Die Lehre aus WP-C4 und
WP-V1: Ein Mechanismus, der entworfen wird, bevor man weiß, was er leisten muss, bekommt
Konstanten, die zu den gerade betrachteten Fällen passen und sonst nichts.

## Datenlage

Die Heartbeat-Dateien enthalten je Level ein Ereignis mit `level`, `stage` und `best_loss`. Daraus
lässt sich rekonstruieren, wann der finale Loss zum ersten Mal erreicht wurde.

Verfügbare Quellen auf dem Netzlaufwerk `S:` unter
`S:\BigDataOrion\data-science\joedicke\`:

| Ordner | Inhalt |
|---|---|
| `pilot_sweep_tasks`, `pilot_sweep3_tasks`, `pilot_e20af80` | 42 Pilotzellen, `pretune_on`, Systeme 24–62 |
| `campaign_88eaeb6f…\tasks_pretune_off_probe` | 3 Sondierungszellen, `pretune_off`, Systeme 56, 59, 61 |
| `regression_88eaeb6f…\tasks`, `regression2_f6143eb…\tasks` | je 120 Regressionszellen, alle vier Varianten |

**Der Share hängt gelegentlich.** Jeden Zugriff mit Zeitlimit absichern und bei Nichterreichbarkeit
abbrechen und berichten, statt eine leere Liste als „keine Daten" zu deuten. Ein leeres Ergebnis von
`S:` ist **kein** Beleg für Abwesenheit — das ist in diesem Projekt schon zweimal passiert.

## Umfang

### Teil 1 — Je Zelle: wann war Schluss?

Für jede Zelle mit Heartbeat-Daten:

- die Levelzahl, bei der `best_loss` **zuletzt** verbessert wurde
- die Gesamtzahl gelaufener Level
- daraus die Zahl der Level ohne jede Verbesserung am Ende
- der Zeitanteil dieser Level an der Gesamtlaufzeit der Zelle, aus den Heartbeat-Zeitstempeln

„Verbessert" heißt: `best_loss` sinkt überhaupt. Ob eine Absenkung um 1e-12 auf einem Loss von 4
noch als Verbesserung zählen soll, ist genau die Frage, die eine spätere Regel beantworten muss —
**hier nicht entscheiden**. Stattdessen die Größe so berichten, dass beide Lesarten ablesbar sind:
etwa zusätzlich die letzte Levelzahl, ab der sich der Loss um weniger als ein Promille geändert hat.

### Teil 2 — Die Verteilung, aufgeschlüsselt

Nicht nur Mittelwerte. Gefragt ist, ob sich die Verschwendung vorhersagen lässt, und zwar
aufgeschlüsselt nach:

- Dimensionsklasse
- exakt gegen surrogat
- `pretune_on` gegen `pretune_off`
- Variante
- Zellen, die eine brauchbare Lösung finden, gegen solche, die es nicht tun

Der letzte Punkt ist der interessanteste: Verschwenden gerade die Zellen die meisten Level, die
ohnehin scheitern? Wenn ja, wäre eine Abbruchregel doppelt wertvoll; wenn nein, würde sie auch
erfolgreichen Zellen etwas wegnehmen.

### Teil 3 — Was eine Regel kosten würde

Rein hypothetisch und ohne Implementierung: Wie viele Level und wie viel Zeit hätte ein Abbruch
nach **k** Leveln ohne Verbesserung gespart, für `k = 3, 5, 8`? Und, die entscheidende Gegenfrage:
**Wie viele Zellen hätten dabei eine Verbesserung verpasst**, die erst nach einer längeren Pause
kam?

Diese Gegenfrage ist der Kern des Auftrags. Eine Abbruchregel ist genau dann vertretbar, wenn
Verbesserungen nach langer Pause selten oder klein sind. Berichte jeden Fall einzeln, in dem der
Loss nach mehr als **k** stillen Leveln noch einmal deutlich gesunken ist — mit System, Level und
Größe des Sprungs.

## Verboten

- **Keine Abbruchregel implementieren**, keine Änderung an `n_levels`, an der Suchschleife oder an
  irgendetwas Fingerprint-Relevantem. Dieser Auftrag ändert **keinen** Produktivcode.
- **Keine Cluster-Jobs, keine Kampagne, keine Läufe auf Orion.** Der Namespace ist leer und bleibt es.
- **Keine Empfehlung für ein bestimmtes k** im Report. Zahlen liefern, Entscheidung dem Nutzer.
- **Nichts committen, nichts stagen, nichts pushen. Kein `git add -A`.**
- Nichts, was länger als 15 Minuten läuft.

## Abnahme

- Tabelle je Zelle mit letzter Verbesserung, Gesamtleveln, stillen Leveln am Ende und deren
  Zeitanteil.
- Die Aufschlüsselungen aus Teil 2, jeweils mit Fallzahl.
- Die drei hypothetischen Ersparnisse aus Teil 3, jeweils mit der Zahl verpasster Verbesserungen.
- Jede späte Verbesserung einzeln aufgeführt.
- Wenn Daten fehlen oder `S:` nicht erreichbar war, steht das im Report statt einer stillen Lücke.
