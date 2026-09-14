# WP-C4c — SINDy rechnet auf den Trajektorien der Kampagne, nicht auf eigenen

**Language: Python**

## Ausgangslage

WP-C4b hat den Hash-Abgleich gebaut und gefahren (`a1b8297`). Ergebnis über alle 63 Systeme und
beide IC-Sets:

| | |
|---|---|
| Zeitgitter bit-identisch | **126 / 126** |
| Zustandsmatrix identisch | **0 / 126** |
| Formfehler, fehlende Zeilen | 0 |

Die Ursache ist kein Fehler auf einer der beiden Seiten: die Kampagne integriert mit **`Tsit5`**
(`studies/regression/run_regression.jl:578`), das SINDy-Skript mit **`DOP853`**
(`scipy.integrate.solve_ivp`), beide bei `1e-9`. Zwei Verfahren verschiedener Ordnung stimmen bei
dieser Toleranz auf etwa **1e-10** überein — mehr nicht.

Claim D verlangt aber „trajectories **verified byte-identical** to those C-1 consumed, **by hash,
not by assertion**". Mit zwei Integratoren ist das grundsätzlich unerreichbar, egal wie die
Toleranzen gesetzt werden.

## Die Aufgabe, und der Weg, der nicht gegangen wird

**Nicht gegangen wird:** den Python-Integrator auf `Tsit5` umstellen oder die Toleranzen so lange
drehen, bis die Hashes zufällig passen. Das wäre eine Reimplementierung des Konstruktionspfads und
ließe genau die Frage offen, die der Nachweis beantworten soll — derselbe Fehler, den WP-C4b auf der
Julia-Seite ausdrücklich vermeiden musste.

**Gegangen wird:** SINDy **konsumiert die Trajektorien der Kampagne als Bytes**, statt eigene zu
erzeugen. Dann ist Byte-Identität nicht hergestellt, sondern trivial wahr.

Dazu zwei Teile:

### 1. Export auf der Julia-Seite

`studies/regression/phase_c_trajectory_hashes.jl` erzeugt die Trajektorien bereits über
`build_trajectory`. Es soll sie zusätzlich **exportieren** — dieselben Zahlen, die es hasht, in einem
Format, das die Python-Seite verlustfrei liest. Bindend: Float64, Little Endian, Zustandsmatrix in
C-Reihenfolge mit Achsen (Zeit, Dimension), Zeitvektor getrennt — also exakt das Format, das der
Hash schon beschreibt, damit Export und Hash **dieselbe** Bytefolge sind.

Neben den Daten gehört je (System, IC-Set) der Hash in eine Begleitdatei, damit die Python-Seite
beim Laden prüfen kann, dass sie bekommen hat, was sie erwartet.

**Julia läuft in deiner Sitzung nicht.** Schreib den Teil fertig, melde ihn als offen, Claude fährt
ihn. Lies ihn vorher gegen die Datei, die er einbindet.

### 2. Die Python-Seite lädt statt zu integrieren

`run_phasec_sindy_baseline.py` bekommt den Export als **kanonische** Quelle der Trajektorien. Das
eigene `solve_ivp` für die Wahrheits-Trajektorie entfällt in diesem Pfad.

Regeln:

- **Beim Laden wird der Hash neu berechnet und gegen die Begleitdatei geprüft.** Stimmt er nicht,
  **Abbruch** — nicht warnen, nicht weiterrechnen.
- Fehlt der Export, **Abbruch mit klarer Meldung**. Kein stilles Zurückfallen auf eigene Integration:
  genau dieses Zurückfallen würde den Nachweis später unbemerkt entwerten.
- Der Pfad zum Export ist ein Parameter ohne Vorgabewert, der auf etwas Laufendes zeigt.
- `solve_ivp` bleibt dort erlaubt, wo es **nicht** um die Wahrheits-Trajektorie geht, sondern um die
  Integration des **gefitteten** Modells (Rekonstruktion und Generalisierung). Das ist unsere eigene
  Auswertung, keine gemeinsame Eingabe. Halte die beiden Verwendungen im Code und im Report
  auseinander.

### 3. Neu rechnen, und den Unterschied ausweisen

Der Phase-C-SINDy-Lauf wird auf den geladenen Trajektorien wiederholt. **Die Ergebnisse werden sich
ändern** — das ist erwartet und kein Fehler.

Der Report muss den Unterschied beziffern, mindestens: wie viele der 2.520 Zeilen ihren
`r2_gt_0_9`-Wert ändern, wie viele ihren Strukturtreffer ändern, und wie groß die
`r2`-Abweichungen sind (Quantile, keine Mittelwerte). **Keine Deutung, keine Bewertung** — nur die
Zahlen. Wenn sich nichts ändert, ist auch das ein Ergebnis und gehört so berichtet.

**Das darf nicht dazu führen, dass eine Konfiguration ausgewählt oder eine Schwelle angepasst wird.**
Beides bleibt verboten wie bisher.

## Abnahme

1. Der Export existiert und ist bytegleich mit dem, was `phase_c_trajectory_hashes.jl` hasht.
2. Der Hash-Abgleich meldet **126 / 126 in beiden Hashes gleich**. Das ist das eigentliche Ziel
   dieses Pakets.
3. Die Python-Seite bricht ab, wenn der Export fehlt oder ein Hash nicht stimmt — beides getestet.
4. Der neue SINDy-Lauf liegt vor, und der Unterschied zum bisherigen ist beziffert.
5. Alle Python-Tests grün.

## Verboten

- Den Python-Integrator auf ein anderes Verfahren umstellen, um Hashes zu erzwingen.
- Toleranzen verändern.
- Stilles Zurückfallen auf eigene Integration, wenn der Export fehlt.
- Eine SINDy-Konfiguration auswählen; die Schwelle 0,9 anfassen; eine Pruning-Regel ändern.
- Irgendetwas, das den laufenden Kampagnenlauf berührt. Die Konfiguration ist eingefroren.
- Keine neue Planungsdatei. Report nach `codex/reports/REPORT_WP_C4c.md`.
