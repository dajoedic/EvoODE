# WP-C4a — Der Phase-C-SINDy-Arm, soweit er ohne C-1 gebaut werden kann

**Language: Python**

## Ausgangslage

Claim D des Phase-C-Plans (`docs/paper1_phaseC_benchmark_plan.md` §1b, Zeile „**D**") vergleicht
EvoGrow gegen SINDy — gepaart je (System, IC-Set) über **alle 63 Systeme**, geschichtet nach
Dimension **und** Dreiwege-Repräsentierbarkeit, mit Kostenachse neben jeder Qualitätszahl.

Der vorhandene Baustein ist `analysis/scripts/aggregate/run_wp_n6_sindy_baseline.py` aus WP-N6. Er
ist lauffähig, konfigurationsgetrieben und dauert Minuten. Er ist aber **auf Phase B gebaut** und
erfüllt drei der Phase-C-Anforderungen nicht:

1. Er schichtet über `data/paper1_phaseB_v1/representational_adequacy.csv`. Das ist die **alte**
   Basis mit 20 exakten / 43 Surrogat-Systemen. Phase C fährt
   `staged_polynomial_basis_with_constant` mit **30 exakt / 33 Surrogat** (WP-N16,
   `phase_c_support.json`). **Jede Schichtung aus WP-N6 ist damit für Phase C ungültig.**
2. Er misst keine Generalisierung. Claim C und Claim D müssen dieselbe Metrik teilen, sonst ist der
   Vergleich auf der Generalisierungsseite nicht paarbar.
3. Er weist die Trajektorien nicht nachprüfbar als dieselben aus, die C-1 verbraucht. WP-N6 hat
   gegen die **ausgelieferten** ODEBench-Lösungen geprüft, nicht gegen unsere eigenen.

**WP-N6 bleibt unangetastet.** Seine Ausgaben unter `analysis/data/wp_n6_sindy_baseline/` und
`analysis/tables/wp_n6_sindy_baseline/` sind Provenienz eines abgeschlossenen Arbeitspakets und
werden weder überschrieben noch verschoben noch „mitgepflegt".

## Was blockiert ist, und was deshalb nicht in diesem Paket steckt

Die C-1-Kampagne läuft (Stand: 18 von 756 Zellen). **Alles, was C-1-Records braucht, ist hier
ausdrücklich nicht zu bauen bzw. nicht auszuführen:**

- die tatsächliche Paarung gegen C-1,
- der Hash-Abgleich gegen die Trajektorien, die C-1 verbraucht hat.

Zum zweiten Punkt ein Befund, der die Aufgabe begrenzt: **die Records tragen keinen
Trajektorien-Hash.** `studies/regression/run_regression.jl` schreibt keinen. Der geforderte Abgleich
„by hash, not by assertion" ist gegen die Records **heute nicht durchführbar** und wird in einem
eigenen Julia-Paket (WP-C4b) nachgezogen, das die Trajektorien über denselben Konstruktionspfad wie
die Kampagne erzeugt und hasht. Dieses Paket hier hat die Aufgabe, die **Python-Seite dieses
Abgleichs vorzubereiten**: ein dokumentiertes, reproduzierbares Hash-Format und die Hashes der
Trajektorien, die SINDy tatsächlich konsumiert hat.

## Aufgabe

### 1. Ein Phase-C-Lauf des SINDy-Baselines

Ein Skript unter `analysis/scripts/aggregate/`, das den SINDy-Arm für Phase C rechnet. Ob das über
einen neuen Einstiegspunkt oder über eine Phase-C-Konfiguration des vorhandenen Skripts geschieht,
entscheidest du — **Bedingung ist nur, dass ein WP-N6-Lauf mit der alten Konfiguration
bit-identische Ausgaben liefert wie heute.** Das ist zu zeigen, nicht zu behaupten.

Anforderungen an den Lauf:

- **alle 63 Systeme, beide IC-Sets**, Trajektorien selbst integriert nach dem eingefrorenen
  Protokoll: 512 Punkte über t ∈ [0,10], `abstol = reltol = 1e-9`.
- **Repräsentierbarkeit aus der kanonischen Quelle**, also aus dem Phase-C-Support-Artefakt
  (`phase_c_support.json`, von WP-N16 erzeugt — Pfad im Repo suchen, nicht raten). Die
  Dreiwege-Klasse ist zu übernehmen, nicht neu herzuleiten. Phase-B-Klassifikationsdateien dürfen in
  diesem Pfad **nicht** gelesen werden.
- **alle Konfigurationen berichten, keine auswählen.** Die zehn Bibliotheks-/Schwellen-Kombinationen
  bleiben vollständig in der Ausgabe. Es gibt keine „beste" Spalte und keinen Maximalwert über
  Konfigurationen in einer Ergebniszahl. Wenn irgendwo ein Maximum gebildet wird, muss die Spalte im
  Namen tragen, dass sie ein Maximum über Konfigurationen ist.
- **Kostenachse.** Je Zelle und Konfiguration die Kostengrößen, die SINDy überhaupt hat (Zahl der
  Regressionen, Zahl der Integrationen für die Auswertung, Laufzeit). Laufzeit ist nach
  Designprinzip 7 **Kontext, keine Evidenz**, und muss im Spaltennamen oder in einer
  Begleitspalte als solche gekennzeichnet sein — so wie es `elapsed_s_evidence_role` in den anderen
  Aggregaten schon tut.

### 2. Generalisierung für SINDy, beide Richtungen

Wie in WP-N5 für EvoODE: das auf IC-Set A gefittete Modell wird von der **ungesehenen**
Anfangsbedingung des jeweils anderen IC-Sets integriert, Koeffizienten unverändert. Beide Richtungen
(1→2 und 2→1) sind **getrennt** zu berichten und nie zu mitteln.

Zwingend mitzuliefern ist die **Rekonstruktionskontrolle** nach dem Vorbild von WP-N5: dasselbe
Modell von der *trainierten* Anfangsbedingung integriert muss die Trainingsvorhersage reproduzieren.
Eine von null verschiedene Kontrolle heißt, dass das Modell aus dem Record nicht rekonstruierbar ist
— dann ist die Zeile ungültig und darf nicht in die Auswertung.

Divergierende Integrationen sind zu **zählen und auszuweisen**, nicht stillschweigend zu verwerfen.

### 3. Trajektorien-Hashes

Je (System, IC-Set) der Hash der Trajektorie, die SINDy tatsächlich konsumiert hat, in einer eigenen
Ausgabedatei. Format explizit und im Report dokumentiert, damit die Julia-Seite es später
nachbilden kann. Vorgabe: **SHA-256 über die rohen little-endian Float64-Bytes**, Zeitvektor und
Zustandsmatrix getrennt gehasht, Zustandsmatrix in C-Reihenfolge mit dokumentierter Achsenordnung
(Zeit × Dimension). Zusätzlich Form und Wertebereich je Achse, damit ein Formfehler nicht als
Hash-Unterschied erscheint.

### 4. Die Paarungsmaschinerie — gebaut, aber nicht gegen C-1 gefahren

Ein Zusammenführungsschritt, der SINDy-Zeilen und EvoGrow-Zellen je (System, IC-Set) paart und
`analysis/data/paper1_phaseC_v1/phasec_sindy_paired.csv` schreibt. Er nimmt den EvoGrow-Teil über
einen Parameter entgegen (Registry oder Record-Verzeichnis), hat **keinen** auf die laufende
Kampagne zeigenden Vorgabewert und bricht ab, wenn die Eingabe unvollständig ist.

Regeln, die der Schritt erzwingen muss:

- **Keine Schlagzeilenzahl über Schichten hinweg.** Jede aggregierte Zahl trägt ihre Schicht
  (Dimension, Dreiwege-Klasse). Ein Gesamtwert über alle 63 Systeme darf nur entstehen, wenn er als
  solcher benannt ist und die Schichtung danebensteht.
- **Beide Metriken immer zusammen** (Designprinzip 9): Strukturtreffer **und** Anteil R² > 0,9, und
  die Strukturtreffer **roh und gepruned** nebeneinander.
- **Die Seed-Behandlung von EvoGrow ist explizit zu deklarieren** — EvoGrow hat drei Seeds je
  (System, IC-Set), SINDy ist deterministisch. Wie die drei Seeds in eine Paarungszeile eingehen,
  muss in einer Spalte und im Report stehen, nicht in einer Konvention.
- Die Identitätsfelder der EvoGrow-Seite (`git_hash`, `config_fingerprint`,
  `stage_cap_behavior_fingerprint`) werden mitgeführt und auf Eindeutigkeit geprüft.

## Tests

**Protokollregel seit `221a3a7`: Fixtures werden aus echten Records abgeleitet, nie erfunden.** Für
die Paarungsmaschinerie stehen echte Phase-C-Records zur Verfügung — der 16-Zellen-Pilot unter
`S:\BigDataOrion\data-science\joedicke\phase_c_p9_pilot_221a3a72f0cb43164a22b09baac2d9ae82681a02\tasks`
(bei fehlendem Laufwerksbuchstaben derselbe Pfad über `\\scch.at\scch\BigDataOrion\...`). Diese
Records tragen die Phase-C-Identität und die von WP-N14 geforderten Spalten.

Zu testen sind mindestens: der Abbruch bei unvollständiger Eingabe, die Ablehnung einer
Nicht-Phase-C-Identität, die Trennung der beiden Generalisierungsrichtungen, die Ungültigkeit einer
Zeile mit von null verschiedener Rekonstruktionskontrolle, und dass keine aggregierte Zahl ohne
Schichtangabe entsteht.

## Abnahmekriterien

1. Ein WP-N6-Lauf mit der alten Konfiguration liefert **bit-identische** Ausgaben wie die
   eingecheckten — gezeigt, nicht behauptet.
2. Der Phase-C-Lauf deckt 63 Systeme × 2 IC-Sets ab, liest die Repräsentierbarkeit aus der
   kanonischen Quelle und liest **keine** Phase-B-Klassifikation.
3. Alle Konfigurationen sind in der Ausgabe; keine Spalte enthält ein Maximum über Konfigurationen,
   ohne das im Namen zu führen.
4. Generalisierung liegt für beide Richtungen getrennt vor, mit Rekonstruktionskontrolle und
   gezählten Divergenzen.
5. Die Trajektorien-Hashes liegen vor, das Format ist im Report so beschrieben, dass eine
   Julia-Implementierung es ohne Rückfrage nachbilden kann.
6. Die Paarungsmaschinerie läuft gegen die 16 Pilot-Records durch und bricht bei unvollständiger
   Eingabe ab. **Sie wird nicht gegen die laufende Kampagne gefahren.**
7. Die Python-Tests laufen grün.

## Ausdrücklich nicht Teil dieses Pakets

- Keine Auswahl einer SINDy-Konfiguration, auch nicht als „Vorschlag".
- Keine Aussage darüber, wer gewinnt. Dieses Paket erzeugt Zahlen, es interpretiert sie nicht.
- Keine Änderung an `run_regression.jl`, an der Kampagnenkonfiguration oder an irgendetwas, das den
  laufenden Lauf berührt. **Die Konfiguration ist eingefroren.**
- Kein Anfassen der WP-N6-Ausgaben.
- Keine neue Planungsdatei. Der Report gehört nach `codex/reports/REPORT_WP_C4a.md`.

## Ausgaben

- Daten: `analysis/data/paper1_phaseC_v1/` (Zellen, Hashes, Paarung)
- Tabellen: `analysis/tables/paper1_phaseC_v1/`
- Konfiguration: `analysis/configs/`
- Report: `codex/reports/REPORT_WP_C4a.md`

Jedes Skript schreibt in seinen **eigenen** Unterordner, nie direkt in ein Sammelverzeichnis.
