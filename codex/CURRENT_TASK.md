# WP-C4b — Der Trajektorien-Hash auf der Julia-Seite

**Language: Julia**

**Vorbemerkung:** Julia startet in deiner Sitzung nicht (`A specified logon session does not exist`
bzw. `SystemError: longpath`). Das ist bekannt und **kein Grund, den Auftrag zu verwerfen**.
Schreib das Paket fertig, melde `blocked`, schreib ins `note`-Feld ausdrücklich *Umgebung, nicht
Sache*, und halte im Report fest, welche Abnahmepunkte deshalb offen sind. Claude fährt die Abnahme.
Was trotzdem erwartet wird: **lies das Skript vor der Abgabe gegen die Dateien, die es einbindet.**
WP-R1 ist an einem fehlenden `include` gescheitert, also an etwas, das ohne Ausführung sichtbar war.

## Ausgangslage

Claim D verlangt, dass die Trajektorien, auf denen SINDy rechnet, **nachweislich dieselben** sind,
die der EvoGrow-Arm C-1 verbraucht — „**by hash, not by assertion**"
(`docs/paper1_phaseC_benchmark_plan.md` §1b, Zeile **D**).

Der Nachweis ist heute nicht führbar, und der Grund ist ein Befund von gestern: **die Records tragen
keinen Trajektorien-Hash.** `studies/regression/run_regression.jl` schreibt keinen. Der Abgleich muss
deshalb über den **Konstruktionspfad** geführt werden statt über die Records.

Die Python-Seite ist fertig (WP-C4a, `465ef58`). Sie liegt unter
`analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/trajectory_hashes.csv`, 126 Zeilen, je eine
pro (System, IC-Set), und ihr Format ist in `codex/reports/REPORT_WP_C4a.md` unter „Trajectory Hash
Format" beschrieben. **Dieses Format ist bindend** und wird nicht neu erfunden.

## Aufgabe

Ein Julia-Skript unter `studies/regression/`, das für alle 63 Systeme und beide IC-Sets die
Trajektorie erzeugt, sie im vorgegebenen Format hasht und das Ergebnis gegen die Python-Datei
vergleicht.

### Die eine Bedingung, an der alles hängt

**Die Trajektorie wird über `build_trajectory` aus `studies/regression/run_regression.jl` erzeugt
(dort ab Zeile 571), nicht nachgebaut.** Eine Reimplementierung — und sei sie zeichengleich —
entwertet den gesamten Nachweis, weil sie genau die Frage offenlässt, die der Nachweis beantworten
soll. Binde die Datei ein und ruf die Funktion auf. Wenn das Einbinden Nebenwirkungen hat (ein
Skript, das beim Laden losrechnet), ist das ein Befund für den Report und **kein** Anlass, die
Funktion zu kopieren.

Dasselbe gilt für die Systemliste und die IC-Sets: aus derselben Quelle wie die Kampagne, nicht aus
einer zweiten Liste.

### Der Fallstrick, an dem so etwas scheitert

Das Format verlangt die Zustandsmatrix **in C-Reihenfolge mit den Achsen (Zeit, Dimension)**. Julia
speichert spaltenweise. Ein direktes Hashen des Speicherinhalts von `Trajectory.x` liefert deshalb
eine **andere Bytefolge** als NumPy für dieselben Zahlen. Das ist die wahrscheinlichste Ursache eines
Fehlschlags, und sie sieht aus wie ein echter Unterschied. Sorge ausdrücklich für die
zeilenweise Reihenfolge und halte im Report fest, wie du das sichergestellt hast.

Ebenso bindend: Float64, **Little Endian**, Zeitvektor und Zustandsmatrix **getrennt** gehasht,
SHA-256.

### Ausgabe

Eine CSV mit denselben Schlüssel- und Hashspalten wie die Python-Datei, plus Form und Wertebereich je
Achse, damit ein Formfehler nicht als Hash-Unterschied erscheint. Dazu ein Vergleichsschritt, der je
Zeile sagt: beide Hashes gleich, nur Zeit gleich, nur Zustand gleich, oder keiner — und der am Ende
eine Gesamtbilanz zieht.

**Der Vergleich darf nicht schweigen.** Fehlt eine Zeile auf einer Seite, ist das zu melden, nicht zu
überspringen. Unterscheiden sich Hashes, ist die betroffene Zeile mit Form und Wertebereich
auszugeben, damit man Formfehler von Zahlenfehlern trennen kann.

## Was ausdrücklich offenbleibt, und im Report so zu benennen ist

Dieser Nachweis zeigt, dass **derselbe Konstruktionspfad unter derselben Konfiguration** dieselben
Zahlen liefert wie die Python-Seite. Er zeigt **nicht**, dass die laufende Kampagne genau diese
Bytes verbraucht hat — das könnte nur ein Hash im Record. Diese Grenze gehört in den Report und
später ins Paper, nicht wegerklärt. Ob ein Trajektorien-Hash künftig in die Records geschrieben
wird, ist **nicht** Teil dieses Pakets: die Konfiguration ist eingefroren, und der Lauf läuft.

## Abnahme

1. Das Skript ruft `build_trajectory` aus `run_regression.jl` auf; es gibt keine zweite
   Trajektorienkonstruktion im Repo-Pfad dieses Pakets.
2. 126 Zeilen, 63 Systeme, beide IC-Sets.
3. Der Vergleich gegen die Python-Datei läuft und berichtet je Zeile und in Summe.
4. Abweichungen — falls welche auftreten — sind mit Form und Wertebereich ausgewiesen.
5. Laufzeit weit unter 15 Minuten (126 Integrationen bei `abstol = reltol = 1e-9`).

## Verboten

- Keine Reimplementierung von `build_trajectory`, aus keinem Grund.
- Keine Änderung an `run_regression.jl`, an der Kampagnenkonfiguration, an
  `trajectory_hashes.csv` oder an irgendetwas, das den laufenden Lauf berührt.
- **Kein Kampagnen-, Regressions- oder Sondierungslauf**, kein Manifest dafür.
- Keine Anpassung der Python-Seite, damit die Hashes passen. Wenn sie nicht passen, ist das das
  Ergebnis und gehört in den Report.
- Keine neue Planungsdatei. Report nach `codex/reports/REPORT_WP_C4b.md`.

## Ausgaben

- Skript: `studies/regression/`
- Daten: `outputs/phase_c_trajectory_hashes/` — eigener Unterordner, nie direkt in ein
  Sammelverzeichnis
- Report: `codex/reports/REPORT_WP_C4b.md`
