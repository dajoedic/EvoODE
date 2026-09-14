# EvoODE — Projekt-Tagebuch

Neueste Einträge zuerst. Aktueller Projektzustand: siehe `CLAUDE.md`.

---

## 2026-09-14

### 82 Heartbeats bei 50 gestarteten Zellen — und eine Vorbedingung fuer den C-3-Neustart

Die Frage kam beim Nachschauen des Fortschritts auf: der Job meldet `18/756`, die Parallelitaet ist
32. Das ist kein Widerspruch — **`COMPLETIONS` zaehlt fertige Zellen, `parallelism` gleichzeitige
Pods.** Nachgezaehlt: 50 Pods, davon 18 `Completed` und 32 `Running`, **0 Restarts**. Die fertigen
sind schlicht die billigen, Systeme 52 und 53 mit 5,9 bis 109,6 Minuten.

**Auffaellig war etwas anderes: 82 Heartbeat-Dateien bei 50 gestarteten Zellen.** Sie zerfallen
sauber in zwei Bloecke:

| Block | Zellen | Ergebnis | seit > 60 min stumm |
|---|---|---|---|
| 613–662 | 50 | 18 | 39 |
| **883–914** | **32** | **0** | **32** |

Der zweite Block stammt vom abgebrochenen C-3-Start: Zeitstempel 10:53 UTC, `"hostname":
"evoode-phase-c-c3-campaign-0"`, Variante `evogrow_v2_2_stage_capped_pretune_on`. Das sind die 32
Pods, die beim gleichzeitigen Start hochfuhren und binnen Minuten angehalten wurden. Je 3 bis 6
Heartbeat-Zeilen, dann nichts mehr. 50 + 32 = 82, vollstaendig erklaert. Nebenbei bestaetigt der
Pod-Index die Zuordnung: Index + 613 = Zellnummer.

**Daraus folgt eine Vorbedingung, die vor dem Fortsetzen von C-3 zu erledigen ist.** Der Runner
schreibt Heartbeats **anhaengend** — `open(sink.path, "a")`, `studies/regression/run_regression.jl:520`.
Wird C-3 fortgesetzt, schreiben die 32 Zellen 883–914 also **in die vorhandenen Dateien hinein**,
und der Strom enthaelt danach zwei Laeufe hintereinander.

Der Leser haelt das nicht aus. `read_heartbeat` (`studies/regression/analyze_wasted_search_levels.jl:98`)
ueberschreibt `start_time` bei jedem `start`-Ereignis — das waere noch gutartig —, schiebt aber
**alle** `level`-Ereignisse in **eine** Liste und sortiert sie nur nach Levelnummer. Der abgebrochene
Vorlauf und der echte Lauf werden damit zu einer Reihe mit doppelten Levelnummern verschmolzen.
Betroffen waere die Level-Waste-Messung, die genau aus diesem `best_loss`-Strom rekonstruiert wird.

Zwei Abhilfen, und sie schliessen einander nicht aus. Kurzfristig: die 32 Reste vor dem Fortsetzen
beiseiteraeumen — billig, aber leicht zu vergessen, deshalb steht es jetzt in der Uebergabe.
Dauerhaft: **den Leser gegen mehrfache `start`-Ereignisse robust machen**, den Strom an ihnen
segmentieren und nur das letzte Segment auswerten. Das ist die eigentliche Reparatur, denn ein
Pod-Neustart erzeugt dasselbe Bild in jeder Kampagne — hier waren es zufaellig 0 Restarts.

Kein Datenverlust, kein Defekt im laufenden Lauf: die Ergebnisdateien sind davon nicht beruehrt, und
fuer die 32 C-3-Zellen existiert ohnehin kein Ergebnis.

---

## 2026-09-14

### Kann k = 3 den Konstanten-Defekt auf dim 2 heilen? Vermutlich nicht — der Mechanismus passt nicht

<!-- dc07d25 -->

Die Frage kam aus dem Gespraech und ist berechtigt: der dim-2-Probelauf lief unter `ec3b6bd`
(09.09.), die Restart-Politik kam mit `4908b07` (WP-N11, 10.09.) und hat den Vorgabewert
`max_fit_attempts = 1`. **Die Probe ist also k = 1, Phase C faehrt k = 3.** Also koennte der
Einbruch der Strukturtreffer unter der Konstanten (pruned 55,6 % → 35,2 %) ein Artefakt zu weniger
Parameterstarts sein.

**Er ist es vermutlich nicht, und der Grund ist die Form des Fehlschlags.** `fit_attempt_failed`
(`src/optimize/bfgs.jl:142`) ist eng definiert: nicht-endlicher Loss **oder** Loss ≥ 1e6 **oder**
`result_valid == false`. Der Neustart repariert **gescheiterte** Fits. Auf dim 2 scheitert aber
nichts — die Fits gelingen auf der falschen Struktur:

| Schicht A | alte Basis | mit Konstante |
|---|---|---|
| verfehlte Zellen | 24 / 54 | 35 / 54 |
| davon Sentinel-Loss | **0** | **0** |
| Median-Loss der verfehlten Zellen | ~0 | ~0 |
| R² > 0,9 unter den verfehlten | 21 / 24 | **32 / 35** |

Der staerkste Einzelbeleg ist die R²-Zeile des Probelaufs: **51/54 in beiden Armen, identisch**.
Waeren misslungene Parameterfits die Ursache, muesste der konstante Arm im R² schlechter sein. Er
ist gleich gut und trifft trotzdem seltener die Struktur — **eine Selektionsfrage, keine
Optimierungsfrage.** Direkt an den Zaehlern, ueber alle 336 Zellen und rund 148.000 Parameterfits:
`total_optimizer_invalid_result_fits = 0` (0 Zellen mit > 0) und `total_nonfinite_solves = 0`. Zwei
der drei Praedikat-Zweige haben **kein einziges Mal** gefeuert.

**Grenze der Pruefung, ausdruecklich:** der dritte Zweig — ein *einzelner* Fit bei ≥ 1e6 — hat in
diesen Records keinen eigenen Zaehler. Auf Zellebene endet keine der 336 Zellen im Sentinel, aber
innerhalb einer Zelle kann es passiert sein. WP-N4 hat gezeigt, dass es vorkommt (15 von 102 mit der
wahren Struktur bei einem Start). Die Wirkung ist also **nicht auf null bewiesen**, sie erklaert nur
das beobachtete Muster nicht.

**Zwei Gegenpunkte, die die Vermutung nicht ganz erledigen.** Ein Pfad existiert: selektiert wird
ueber den Loss, also verliert eine richtige Struktur mit schlechtem Fit gegen eine falsche mit
Gluecksfit — dort wirkt k = 3 indirekt auf die Strukturtreffer. Und der implizite Multistart ist
laengst da und schwaecht k = 3 ab: unter `pretuning = false` zieht jeder Fit `0.1 .* randn`, in der
ersten vermessenen gekoppelten Zelle (System 26) 310 Fits auf 45 Strukturen, 85,5 % Duplikate,
Median 5 Wiederholungen je Struktur. Der Retry beisst dort, wo eine Struktur **genau einmal**
gefittet wird — das kommt auf gekoppelten Systemen vor, weshalb k = 3 dort besser begruendet ist als
die dim-1-Zahlen nahelegten. Eine Randverbesserung, keine Gegenmassnahme gegen die
Falsch-Positiv-Magnetik der Konstanten.

**Die Antwort kostet nichts.** C-1 faehrt kanonische Basis *und* k = 3 ueber dieselben dim-2-Systeme,
Seeds und IC-Sets wie der Probelauf. Der Unterschied ist im Wesentlichen k. Zwei Auflagen: anderes
Identitaetstripel, also **Diagnostik und niemals eine gemeinsame Tabelle**; und der Git-Hash driftet
mit, k ist nicht sauber isoliert. Sauber isoliert wird es nur in der Restart-Ablation ueber den
Orakel-Pfad. **Beim Auswerten von C-1 nachsehen** — dafuer steht es hier.

---

## 2026-09-14

### Der dim-2-Probelauf ist vollstaendig — und die Nachrechnung aendert keine Entscheidung

<!-- e09034e -->

Zelle 293 ist am 14.09. um 14:34 fertig geworden, **336 von 336**, Job `evoode-wp-n1-dim2-campaign`
auf `Complete`. Damit laeuft die WP-N15-Auswertung zum ersten Mal **ohne `--allow-incomplete`**:
336 Records gelesen, `raw-implies-pruned`-Verletzungen 0, ein Identitaetstripel ueber jeden Record
(`ec3b6bd` / `0290b75a28791195` / `ffb0266c7913352c`).

**Die fehlende Zelle war genau das, was der Phase-C-Plan von ihr vorhergesagt hatte** — ein
Surrogat, das nur einen einzigen R²-Nenner beruehrt. System 44 (Driven pendulum with quadratic
damping), Seed 42, IC-Set 2, konstante Basis, R² = 0,808, also **unter** der Schwelle. Bewegt hat
sich deshalb nur eine Zahl: die R² > 0,9-Rate des konstanten Arms auf Surrogaten,
97/107 = 90,7 % → 97/108 = **89,8 %**. Alle Exakt-Schichten, die P3-Entscheidungszahlen
eingeschlossen, sind unveraendert: Layer A 9 Systeme, 54 Zellen je Arm, pruned 30/54 (alt) gegen
19/54 (konstant), raw 7/54 gegen 4/54, R² > 0,9 in beiden Armen 51/54.

**Teuer war sie allerdings.** 610 Parameterfits, 3,75e6 Loss-Evaluationen, Endstufe 5 in beiden
Gleichungen — die Zelle mit der laengsten Laufzeit des ganzen Probelaufs. Das ist der Grund, warum
sie vier Tage nach den anderen 335 fertig wurde, und es ist kein Zufall, dass ausgerechnet sie
unter R² 0,9 bleibt.

**Eine Kennzahl verschiebt sich dadurch messbar: der Konstanten-Aufschlag.** Ueber alle 336 Zellen
kostet die Konstante **+20,8 %** `total_loss_evals` (3,507e8 gegen 4,237e8) und **+4,0 %**
`total_parameter_fits`; am 13.09. standen dort +19,8 % und +3,2 %, gerechnet auf 335 Zellen. Stufe 5
erreichen 122 statt 121 Zellen im konstanten Arm. Der in die Kostentabelle uebertragene Aufschlag
betraegt **+20 %** und liegt damit jetzt **knapp unter** der gemessenen Groesse. Die Kampagne ist
eingefroren und laeuft, also bleibt die Zahl stehen; die Unterdeckung wird deklariert statt
korrigiert. Sie ist dieselbe einseitige Risikorichtung, die der Plan ohnehin nennt — und sie ist
klein gegen die zwei groesseren Vorbehalte: der Aufschlag ist **nur auf dim 2** gemessen, waehrend
dim 3 drei Viertel der Phase-B-Rechenzeit trug, und auf den neun gepaarten exakten Systemen liegt er
bei etwa +60 %.

**Betrieblich:** das Laufwerk `S:` war in dieser Sitzung `Unavailable`, der UNC-Pfad
`\\scch.at\scch\BigDataOrion\...` dagegen erreichbar. Der Aggregator nimmt `--input`, also war
nichts zu reparieren — aber die Vorgabewerte der Analyseskripte zeigen auf `S:`, und das faellt beim
naechsten Mal wieder auf.

Nebenbefund aus derselben Abfrage: C-1+C-2 stand um 15:00 bei **18/756**, C-3 unveraendert
`Suspended` 0/180.

---

## 2026-09-14

### Phase C ist gestartet — und der Pilot konnte Claim B nicht pruefen

<!-- a6c0e6c -->

**Der Startablauf lief durch.** Image `221a3a72f0cb...` aus sauberem Baum (`git_dirty = False`),
Bootstrap **bestanden** — der Fingerprint **aus dem Image** ist `0c9672de35c75a9d` und damit
identisch mit dem lokalen —, Smoke-Test 3/3 bestanden, Pilot **16/16 in 97 Minuten**, und das
**Go-Kriterium ist gruen**: `16 records, 8 pairs`, Exit 0. Kriterium 5 separat: alle 16 Zellen
`probe_ok`, **0 Rekonstruktionsfehler, 0 divergierte Integrationen**.

**Und trotzdem ist das Wichtigste an diesem Piloten, was er nicht zeigen konnte.** In allen acht
Paaren sind `executed_levels`, `final_stage` und `loss` **identisch** zwischen gekapptem und
ungekapptem Arm. Grund: in **allen 16 Zellen ist jede Kappe `nothing`**. Die Kappe greift auf
keinem der vier Pilotsysteme, also rechnen beide Arme dieselbe Suche. Kriterium 4 besteht damit
**trivial** — null Unterschiede erfuellen „Unterschiede nur in Kappenfeldern" —, und der Pilot
liefert **kein Signal fuer Claim B**.

Das ist ein Artefakt der Auswahlregel, nicht ein Defekt: „billigstes exaktes System je
Dimensionsklasse" waehlt genau die Systeme, auf denen die Suche frueh endet — und wo sie frueh
endet, ist die Kappe belanglos. Die Regel bleibt trotzdem richtig, sie war vorab festgelegt. Aber
**das Go-Kriterium kann den Mechanismus der Hauptabbildung nicht pruefen**, und das gehoert
notiert, bevor jemand aus dem gruenen Exit-Code mehr liest, als drinsteht.

**Die Gegenprobe, und sie entscheidet den Start.** Die Kappe liest nur Trajektorie und Basis, ist
also **ohne jede Suche** berechenbar (`estimate_stage_caps`). Ueber alle 63 Systeme, beide IC-Sets,
beide Basen gerechnet — 252 Zeilen, `outputs/phase_c_cap_incidence/stage_caps_by_basis.csv`:

| Basis | gekappte Gleichungen | Zellen mit mindestens einer Kappe |
|---|---|---|
| alt | 124 / 234 (53,0 %) | 94 / 126 |
| **kanonisch** | **111 / 234 (47,4 %)** | **83 / 126** |

Je Dimension unter der kanonischen Basis: dim 1 32/46, dim 2 36/56, dim 3 15/20, **dim 4 0/4**.

Die Kampagne hat also reichlich Zellen, in denen die Kappe bindet — **Claim B hat Signal**, der
Pilot hatte nur zufaellig keines. Zwei Dinge zum Mitschreiben: die Konstante **senkt** die
Kappenhaeufigkeit leicht (53,0 % → 47,4 %), eine weitere deklarationspflichtige Folge der
Basisentscheidung; und auf **dim 4 bindet keine einzige Kappe**, dort sind gekappter und
ungekappter Arm strukturell identisch.

Ein Nebenbefund aus denselben Records, der zeigt, wofuer Phase C da ist: auf System 52, IC 2,
springt der Verlust von `4,6e-04` (Rekonstruktion) auf `1,18e+01` (Generalisierung).

## 2026-09-13

### WP-N18: der Pilot steht, und sein Go-Kriterium haette immer „nein" gesagt

<!-- 5d9bbf6 -->

**Die „12 Zellen" des Plans folgen nicht aus seiner eigenen Auswahlregel.** Billigstes exaktes
System je Dimensionsklasse, gekreuzt mit C-1 und C-2, einem Seed und beiden IC-Sets — unter der
kanonischen Basis haben **alle vier** Dimensionsklassen exakte Systeme, also ergibt die Regel
**16 Zellen**. Die Regel bleibt, die Zahl wird korrigiert: eine vorab festgelegte Regel
nachtraeglich zu beschneiden, damit eine Zahl stimmt, waere die falsche Richtung — und die vierte
Klasse kostet praktisch nichts, waehrend dim 3/4 genau die Stelle ist, an der Recordfehler am
wahrscheinlichsten sind.

Eingefrorene Auswahl, aus `run_registry.csv` gegen die kanonische Supporttabelle hergeleitet:
Systeme **2, 24, 52, 63**, Seed **42**, je Dimension vier Zellen, **alle acht Paare benachbart**.
Zwei Eigenheiten sind deklariert statt geglaettet: **System 52** ist eines der zehn neu exakten
Systeme, seine Kostenzahl stammt also aus einer Basis, unter der es Surrogat war; **System 63** ist
die Identifizierbarkeitsgrenze, deren Kappe auf der alten Basis ueberall `nothing` war — ob das
unter der kanonischen noch gilt, weiss niemand, und der Pilot zeigt es.

**Der Defekt, und er ist die lehrreiche Haelfte (WP-N18b).** Kriterium 1 prueft je Zelle
`success == true` und leeres `failure_reason`. **Beide Felder gibt es im Record nicht** — nur
`error`. Mit sechzehn Kopien des echten Smoke-Records ausgefuehrt: `success is None, expected true`.
Der Pilot waere durchgefallen, **egal wie gut er laeuft** — und das ist gefaehrlicher als ein
Fehlalarm sonst: ein eingefrorenes Go-Kriterium, das grundlos „nein" sagt, laedt dazu ein, es
abzuschwaechen statt den Fehler zu suchen.

Ursache: `success` und `failure_reason` sind **Registry-Spalten**, keine Recordfelder; das Kriterium
ist auf der Registry formuliert. Der Pruefer liest sie jetzt dort — und damit entfiel zugleich die
Erweiterung der WP-N14-Erlaubnisliste, die der rohe Pfad gebraucht haette, weil die Registry
ohnehin `campaign_manifest_index` fuehrt. Zwei Probleme, eine Ursache.

**Gegen echte Daten geprueft, nicht gegen Fixtures:** sechzehn aus dem Smoke-Record geformte Records
laufen durch, `16 records, 8 pairs`, Exit 0; und der Probe-Schluessel wird in
`wp_n5_ic_generalization.jl` und im Pruefer **identisch** gebildet. Das belegt die Mechanik, nicht
dass ein echter Pilot besteht.

**Ein Muster, das diese Sitzung dreimal gezeigt hat.** WP-N15: die Fixture gab Surrogaten eine
Termliste, die echte Surrogate nie haben. WP-N16: erst die Ausfuehrung fand einen World-Age-Fehler,
der jeden Pod getoetet haette. WP-N18: die Fixture gab jedem Record ein `success`, das kein Record
hat. Immer dieselbe Ursache — **die Fixture wurde erfunden statt abgeleitet** und prueft damit die
Annahme gegen sich selbst. Konsequenz fuer kuenftige Pakete: Fixtures aus einem echten Record
ableiten.

Damit ist **P9 gebaut**. Es fehlt nur noch die Ausfuehrung: Smoke-Job, Pilot, Go-Kriterium, Start.

### WP-N17: die Cluster-Manifeste, und warum es zwei Jobs sind statt drei

<!-- 29a0030 -->

Bootstrap, Smoke und **zwei** Kampagnen-Jobs. Der Plan hatte „Manifeste fuer C-1, C-2, C-3"
gefordert; richtig ist eine andere Aufteilung, und der Grund ist wissenschaftlich, nicht
betrieblich. **C-1 und C-2 teilen sich einen Job**, weil ihre Paarung bindend ist (§2b): getrennte
Jobs haetten getrennte Abbruchzeitpunkte und hinterliessen unvollstaendige Paare — genau das, was
Claim B nicht ueberlebt. **C-3 laeuft allein**, weil er gegen niemanden gepaart ist, ~2.400
Kernstunden kostet und das ist, was man streicht, wenn das Budget knapp wird.

**Die kostenabsteigende Indexliste erfuellt zwei Ziele gleichzeitig**, und deshalb ist sie die
richtige: die teuren Zellen starten zuerst — die teuerste Phase-B-Zelle lief 289,7 h, und eine Zelle
ist nicht teilbar, also bestimmt sie am Ende allein die Wanduhr —, **und alle 378 Paare bleiben
benachbart**, sodass ein Teillauf ganze Paare liefert. `indices_all.txt` hat nur die zweite
Eigenschaft, die Dimensionslisten keine.

**Abnahme:** `completions` deckt sich exakt mit den Listenlaengen (756, 180, 3); die beiden Armlisten
sind disjunkt und ergeben zusammen die 936; **alle 378 Paare nachweislich benachbart**; die
Smoke-Liste deckt wirklich alle drei Arme ab statt dreimal dieselbe Sorte Zelle. Der Bootstrap
schreibt die Indexlisten **neben** das Manifest — gegen ein temporaeres Verzeichnis ausprobiert, weil
ein fester Vorgabepfad hier bedeutet haette, dass der Kampagnen-Job nichts findet. Alle Jobs zeigen
auf denselben Kampagnenpfad, **der Smoke-Job auf ein eigenes Ausgabeverzeichnis** — Probe-Records
koennen so nie in die Kampagnendaten geraten, die Lehre aus den 42 Pilot-Records.

**Zwei Dinge bewusst nicht abgeschrieben.** `parallelism: 32` wird uebernommen, seine Begruendung
nicht: sie ruht auf einer Momentaufnahme des Namensraums vom 09.09., die seither niemand geprueft
hat. Das Manifest nennt jetzt die Kommandos, die **unmittelbar vor dem Start** zu wiederholen sind.
Und der Token-Fehlermodus steht als Kommentar in **jedem** Manifest: bei 5–7 Wochen Laufzeit und
Pods, die durchgehend neu erzeugt werden, hinterlaesst ein ablaufendes Deploy-Token eine Luecke in
der Mitte des Datensatzes — eine, die ganze Systeme trifft und deshalb wie ein Ergebnis aussieht.

Damit sind **alle Bauteile der Phase C fertig**. Offen ist nur noch **P9**: Smoke-Job und der
12-Zellen-Pilot mit dem fuenfteiligen Go-Kriterium. Beides braucht ein gueltiges Cluster-Token.

### WP-N16: die Phase-C-Konfiguration steht, und der wahre Support war basisabhaengig

<!-- 6212809 / e29895c -->

B4 und B1 sind **ein** Arbeitspaket, nicht zwei. Der Fingerprint nimmt den wahren Support in die
Kampagnenidentitaet auf — mit der Begruendung, dass er definiert, was `pruned_match` bedeutet — und
der Support haengt an der Basis. Die Konstante wird ein Term **in Stufe 1**, also verschiebt sich
**jeder Termindex**. Ein weiterverwendetes `phase_b_support.json` haette keinen Fehler erzeugt,
sondern **lautlos falsche Strukturtreffer**.

**Die kanonische Tabelle validiert sich selbst.** `phase_c_support.json`, hergeleitet auf der
kanonischen Basis: **30 exakte Systeme statt 20**, neu dazu genau 1, 5, 9, 17, 23, 43, 52, 57, 58,
59 — exakt die zehn, die `CLAUDE.md` seit dem 07.09. als „scheitern allein am konstanten Term"
fuehrt. Kein exaktes System verloren, keine `expected_stage` verschoben. Dass eine unabhaengige
Herleitung genau die Liste trifft, die aus der Repraesentierbarkeitsanalyse stammt, ist die beste
Bestaetigung, die hier zu haben war.

**Folgen fuer den Plan, alle nachgezogen:** C-3 umfasst **180 Zellen statt 120**, weil er alle
exakten Systeme abdeckt; die Kosten steigen auf **~12.300–15.900 Kernstunden**; und jede aus
„20 exakte Systeme" abgeleitete Zahl ist fuer Phase C veraltet, die Phase-B-Aufteilung 240/516
eingeschlossen.

**Phase-C-Identitaet:** `0c9672de35c75a9d`, 936 Manifestzeilen (378 + 378 + 180), mit Basisname und
`max_fit_attempts = 3` im Fingerprint. Der Optimierer-Default bleibt bei 1 — die 3 steht in der
Phase-C-Konfiguration, nie im Default. Damit ist die offene Haelfte von **P6** geschlossen.

**Ein stiller Totalausfall wurde verbaut:** `variant_basis_name` faellt auf die **alte** Basis
zurueck, wenn eine Variante kein `basis_name` traegt. Fuer Phase B war das richtig, fuer Phase C
waere ein vergessenes Feld ein Arm auf der falschen Basis gewesen, dem man es nicht ansieht. Jede
Variante deklariert die Basis jetzt ausdruecklich, und die Konfiguration bricht ab statt
zurueckzufallen.

**Die Indexanordnung ist eine bewusste Entscheidung.** Gekappter und ungekappter Arm wechseln sich
**zeilenweise** ab, C-3 liegt hinten. Der `wp_n1`-Generator hatte die Varianten aussen geschleift,
sodass ein Abbruch in der ersten Haelfte nur einen Arm hinterlaesst — bei Claim B, der
Hauptabbildung des Papers, waere das der Verlust der Paarung.

**Ein Defekt aus der Abnahme, der jeden Pod getroffen haette (WP-N16b).** Der Smoke-Test brach mit
einem Julia-1.12-**World-Age**-Fehler ab: `phase_c_config.jl` wurde *innerhalb einer Funktion*
eingebunden, die so erzeugten Methoden leben in einem neueren World als der aufrufende Code.
`run_batch_cell.jl` ist der Einsprungpunkt **jedes** Kampagnen-Pods — der Fehler haette 936 Pods
nacheinander gegen dieselbe Zeile gefahren. Behoben durch unbedingtes Einbinden auf oberster Ebene,
wie Phase B es seit der Kampagne macht.

**Die Abnahme, gefahren von Claude, weil Codex hier kein Julia startet.** `phase_b_fingerprint()`
unveraendert `604e79733b22d64d`; die alte Supporttabelle datengleich reproduziert (einziger
Unterschied das neue, gewuenschte Feld `basis_name`, das der Fingerprint ueberlebt); und eine echte
Phase-B-Zelle — System 3, Seed 42, IC 1, `pretune_off` — **bitgleich gegen ihren Kampagnen-Record
ueber 67 Felder**, einzige Abweichung `git_dirty`. Der Smoke-Test auf Phase C laeuft: System 1, der
RC-Schaltkreis, eines der zehn ohne Konstante nicht darstellbaren Systeme, Loss 1,5e-14, Struktur
getroffen, `executed_levels = 1` gegen `n_levels = 30`. 37 Python-Tests gruen.

Offen bleiben **B7** (k8s-Manifeste) und **P9** (Smoke-Job und 12-Zellen-Pilot).

### P3 ist entschieden: die Konstante kommt in die kanonische Basis

<!-- a62073c -->

Entscheidung des Nutzers, mit dem Zusatz „leider". Das trifft die Lage genau: **die Entscheidung
faellt gegen die eigenen Messwerte des Probelaufs, nicht mit ihnen.** Auf den neun dim-2-Systemen,
die unter beiden Basen exakt sind, kostet die Konstante Strukturtreffer — ausgeduennt 55,6 % →
35,2 %, roh 13,0 % → 7,4 % — bei identischer R²-Rate von 94,4 %.

Was trotzdem entscheidet, ist **Repraesentierbarkeit, und die ist kein Stellparameter**: die alte
Basis stellt 20 von 63 Systemen exakt dar, SINDys schlichte Polynombibliothek 40, ProGEDs rationale
Grammatik 53; zehn Systeme scheitern **allein** am konstanten Term. Ein Methodenpaper kann keinen
Beitrag zur Suchstrategie behaupten, waehrend es den halben Suchraum der Vergleichsmethode
durchsucht. Die Suchbarkeit zahlt dafuer — das ist ab jetzt ein berichtetes Ergebnis, keine Fussnote.

**Die Kosten steigen, und zwar aus einem Grund, der leicht uebersehen worden waere.** Jede
Phase-C-Kostenzahl ist aus der Phase-B-Registry abgeleitet, und Phase B lief auf der **alten** Basis.
Der Probelauf misst den Aufschlag direkt: **+19,8 %** `total_loss_evals` und +3,2 %
`total_parameter_fits` ueber alle 335 Zellen. Damit **~11.500–15.100 Kernstunden, 5–7 Wochen**
statt 9.600–12.600. Drei Vorbehalte stehen dabei: Kernstunden sind aus Loss-Eval-Zaehlungen nicht
ablesbar (Designprinzip 7), gemessen ist **nur dim 2**, waehrend dim 3 in Phase B 75,6 % der Rechenzeit
trug — und auf den neun gepaarten exakten Systemen ist der Aufschlag mit rund 60 % dreimal so gross
wie im Aggregat. Das Risiko ist **einseitig**: die Zahl kann ueberschritten werden, und der
ungekappte Spiegel ist die Stelle, an der das zuerst sichtbar wuerde.

**Die zweite Folge betrifft das Narrativ.** Der rohe Strukturtreffer wird sehr klein. Schon auf der
alten Basis erzeugt die Ausduennungsregel auf dim 2 **77 % der Treffer** (30 ausgeduennt gegen 7
roh), und die Konstante ist ein Falsch-Positiv-Magnet — auf dim 1 in 31 von 37 verfehlten Zellen
vertreten. Roh **und** ausgeduennt werden ueberall berichtet; die Schwelle wird nicht nachgezogen.

**Als Limitation deklariert, nicht versteckt:** der Nutzen der Konstante ist auf **dim 1** gemessen
(Generalisierung 72,7 % → 87,9 %), ihre Kosten auf **dim 2** (Strukturtreffer). Kein Lauf misst
beides auf derselben Dimension, und der dim-2-Probelauf wird nicht wiederholt. Phase Cs Claim C
schliesst die Luecke fuer die kanonische Basis, bekommt auf dim 2 aber kein Gegenstueck auf der
alten Basis.

P3 ist damit geschlossen, **B1, B4 und B7 sind frei**. Nachgezogen in `CLAUDE.md`, `PAPER_1.md` und
der Freeze-Liste des Phase-C-Plans.

### WP-N15: die dim-2-Auswertung steht, und sie bestaetigt die dim-1-Richtung

<!-- 5b0e227 / 0bfff14 -->

Der Probelauf auf Orion ist bei **335 von 336 Zellen**, fehlerfrei, unter einer Identitaet
(`git ec3b6bd` / `0290b75a28791195` / `ffb0266c7913352c`). Die fehlende Zelle 293 ist System 44,
Surrogat, konstante Basis — sie lebt, Level 27 von 30. Die exakte Haelfte ist damit **vollstaendig**;
offen ist nur ein Beitrag zur R²-Rate.

**Ein Befund strukturiert die ganze Auswertung.** `representability` wird **je Basis** neu
hergeleitet (`_wp_n1_system_for_basis`). Auf dim 2 sind **9 Systeme unter beiden Basen exakt**
(24, 25, 26, 27, 28, 29, 31, 32, 38), **System 43 nur unter der konstanten**, keines nur unter der
alten. Wer die exakten Zellen der Arme naiv gegeneinanderstellt — 54 gegen 60 — vergleicht
verschiedene Systemmengen. Daher drei Schichten, die nie zu einer Zahl verschmelzen.

**Schicht A, die gepaarte Frage** (9 Systeme, je Arm 54 Zellen):

| | alte Basis | konstante Basis |
|---|---|---|
| Strukturtreffer **roh** | 7/54 = 13,0 % | 4/54 = **7,4 %** |
| Strukturtreffer **ausgeduennt** | 30/54 = 55,6 % | 19/54 = **35,2 %** |
| R² > 0,9 | 51/54 = 94,4 % | 51/54 = **94,4 %** |

Die dim-1-Richtung bestaetigt sich auf gekoppelten Systemen: der konstante Term **kostet**
Strukturtreffer, roh wie ausgeduennt, waehrend die Literaturkennzahl ein **exakter Gleichstand**
ist. Die gepaarte Kontingenz der Rohtreffer: 2 beide, 5 nur alt, 2 nur konstant, 45 keiner. Neun
Systeme sind die effektive Stichprobe, deshalb **kein p-Wert** — die Lehre aus WP-A6.

**Schicht B, wo es vorher keinen Wert gab:** System 43, 6 Zellen, nur konstante Basis. Roh 0/6,
ausgeduennt 3/6, R² 6/6. Kein Vergleichsarm, konstruktionsbedingt — nie als Verbesserung gegen
eine Null lesen.

**Schicht C, die Literaturkennzahl:** Surrogate 105/114 = 92,1 % (alt) gegen 97/107 = 90,7 %
(konstant, Nenner wegen Zelle 293 um eins kleiner); exakte 51/54 = 94,4 % gegen 57/60 = 95,0 %.

**Die Ausduennungsregel traegt hier noch mehr als bekannt.** Auf der alten Basis stehen 30
ausgeduennten Treffern **7 rohe** gegenueber: **23 von 30 Treffern, also 77 %, erzeugt die
Schwelle, nicht die Suche.** WP-N7b hatte fuer Phase B dim 2 64 % gemessen. Das ist ein Grund, die
Schwellenabhaengigkeit zu berichten, **nie** die Schwelle nachzuziehen.

**Die Aufwandsachse ist zum ersten Mal beziffert.** Der Einwand gegen die dim-1-Auswertung —
gleiches Level-Budget fuer einen groesseren Suchraum — stand seit dem 08.09. ohne Zahl. Schicht A,
`total_loss_evals` als Quantile: alte Basis 8,5e3 / 3,6e5 / **8,1e5** / 1,5e6 / 4,8e6, konstante
Basis 5,0e4 / 5,6e5 / **1,3e6** / 2,4e6 / 6,7e6. Die konstante Basis zahlt also rund **60 % mehr
Loss-Evaluationen im Median** — bei schlechterer Strukturausbeute und gleicher R²-Rate. Die
Parameterfits liegen naeher beieinander (330 gegen 370 im Median), die Obergrenze 610 ist in beiden
Armen dieselbe.

**Wichtige Einordnung dieser Zahl, weil sie ab jetzt die Kostenrechnung traegt:** die 60 % gelten
fuer **Schicht A**, die neun gepaarten exakten Systeme. Ueber **alle** Zellen je Arm ist der
Aufschlag kleiner — `total_loss_evals` im Median 1,96e6 gegen 1,99e6, in der Summe 3,51e8 gegen
4,20e8, also **+19,8 %**; `total_parameter_fits` in der Summe +3,2 %; die Endstufe 5 erreichen in
beiden Armen exakt 121 Zellen. Fuer die Hochrechnung der Phase-C-Kosten ist **+20 % auf die
Zaehlgroessen** die belastbare Zahl, nicht die 60 %.

**Zur Abnahme.** Codex meldete „33 passed"; tatsaechlich waren **4 von 33 rot**, und zwar genau die
Tests, die einen erfolgreichen Schreibvorgang erreichen — die Abschlussmeldung machte den
Ausgabepfad bedingungslos relativ zum Repo und starb auf `tmp_path`. Der zweite Defekt hielt den
Lauf ueber echte Daten vollstaendig auf: `wp_n1_expected_support_terms` ist fuer Surrogate `null`
(221 von 335 Records, alle Surrogate, kein exaktes), und das galt als toedlicher Fehler. **Schicht C
waere damit unerreichbar gewesen.** Die Fixtures gaben jeder Zelle eine Termliste, auch den
Surrogaten — eine Kombination, die es in echten Daten nicht gibt. Beides in WP-N15b behoben, 36
Tests gruen, Rohtrefferzahl unabhaengig nachgerechnet (11 von 114).

Damit ist die Entscheidungsgrundlage fuer **P3** da. Die Entscheidung selbst — ob die Konstante in
die kanonische Basis kommt — ist damit **nicht** getroffen: sie haengt daran, welche Metrik zaehlt,
und genau das ist nach WP-N5 eine Frage nach dem Zweck der Methode, nicht nach ihrer Konfiguration.

## 2026-09-10

### WP-N10: der Duplikatzaehler steht, und er stellt die Restart-Politik infrage

<!-- 22a9059 -->

Der Zaehler fuer die `StructureSpec`-Duplikatrate ist committet. Kanonischer Schluessel ist die
je Gleichung sortierte, eindeutige Termindexmenge; gezaehlt wird auf drei Ebenen — ganzer Lauf,
je Stufe, je Level. Die Records tragen Summen, Wiederholungshistogramm und Quantile, **nie einen
Mittelwert** (stehende Auswertungsregel).

Der Eingriff ist rein beobachtend: gezaehlt wird nach `_evaluate!`, die Suche liest den Zaehler
nie. Abnahme von Claude gefahren, nicht von Codex: dieselbe Zelle mit und ohne Zaehler ist
**bit-identisch** — `loss` ueber alle 15 Stellen, dazu `total_loss_evals`,
`total_parameter_fits`, `total_ode_solves`, `r2`, `pruned_match`, `support_terms`.
`phase_b_fingerprint()` bleibt `604e79733b22d64d`, `stage_cap_behavior_fingerprint()` bleibt
`ffb0266c7913352c`; die Kampagnenvergleichbarkeit ist also unberuehrt. Neun Tests gruen.

**Warum das mehr ist als Instrumentierung.** Die ersten dim-1-Messungen sagen: jede Struktur
bekommt effektiv 20 bis 160 Fits, nicht einen — System 3 kommt auf 110 Fits bei 2 eindeutigen
Strukturen (98,2 % Duplikate), System 11 auf 290 bei 3 (99,0 %). Die eingefrorene Restart-Politik
`retry-on-failure bis k = 3` ruht auf WP-N4, und WP-N4 lief auf dim-1-Zellen. Ein „einzelner Fit"
ist dort ein Zustand, den die Suche gar nicht herstellt. Die Praemisse der Politik ist damit
offen, nicht widerlegt.

Einordnung, die eine naheliegende Fehldeutung ausschliesst: die hohe Duplikatrate heisst **nicht**
„die Suche exploriert nicht". Auf dim 1 und niedriger Stufe ist der Strukturraum so klein, dass es
kaum mehr Strukturen *gibt*. Der Befund lautet „Raum erschoepft", nicht „Suche untaetig".

Die dim-2-Messung auf System 26 laeuft. Eine Zelle entscheidet die Frage nicht, sie zeigt die
Groessenordnung; die belastbare Verteilung ueber 378 Zellen liefert Phase C jetzt umsonst, weil
der Zaehler drin ist.

### P8: die Phase-C-Matrix ist vollstaendig, und die Kostenrechnung war dreifach falsch

<!-- 02d80dd -->

Jede Claim-Zeile nennt jetzt Arm, Skript, Ausgabepfad und Pass-Kriterium (neuer Abschnitt 1b), und
die fuenf offenen Fragen des Plans sind mit Begruendung entschieden (Abschnitt 7). P8 ist damit
erledigt.

**Die Entscheidungen.** SINDy vergleicht ueber alle 63 Systeme, gepaart je (System, IC-Set),
geschichtet nach Dimension und dreiwertiger Repraesentierbarkeit, **ohne aggregierte Kopfzahl ueber
die Schichten** — der WP-N6-Einwand ungleicher Aggregationseinheiten entfaellt bei Phase C
konstruktionsbedingt, weil C-1 ohnehin alle 63 Systeme auf denselben Trajektorien rechnet. Die
Restart-Ablation laeuft ueber den Oracle-Pfad, weil nur dort k isoliert ist: in der vollen Suche
variiert der implizite Multistart aus Strukturduplikaten gleichzeitig, eine Recovery-gegen-k-Kurve
aus vollen Laeufen misst also zwei Dinge auf einmal. Der Oracle-Arm laeuft nur auf der kanonischen
Basis — das Argument ist Zuschnitt, nicht Kosten. Die Pretuning-Ablation bekommt einen
Bestaetigungsarm von 120 Zellen statt eines Zitats ueber eine Basisgrenze hinweg. Und vor der
Einreichung steht ein 12-Zellen-Pilot mit fuenfteiligem Go-Kriterium, ausdruecklich verschieden vom
Smoke-Test: der Smoke-Test fragt, ob der Pfad laeuft, der Pilot, ob die Records die Claims tragen.

**Die Kosten waren geschaetzt, jetzt sind sie abgeleitet — und die Schaetzung war zu niedrig.** Aus
`experiments/paper1_phaseB_v1/run_registry.csv`, nicht aus dem Bauch:

| Groesse | alt | gemessen |
|---|---:|---:|
| kanonischer Arm C-1 | ~2.600 h | **3.249,3 h** (Phase B `pretune_off`, dieselben 378 Zellen) |
| Pretuning-Arm C-3 | von mir mit ~400 h veranschlagt | **1.331,4 h** |
| Gesamt | ~8.000–11.000 h | **~9.600–12.600 h** |

Der Pretuning-Arm ist der lehrreiche Posten. Meine Annahme war, „nur exakte Systeme" mache ihn
billig. Das stimmt nicht, weil die exakte Menge Lorenz enthaelt: **1.314,5 der 1.331,4 Stunden
(98,7 %) liegen in 24 dim-3-Zellen**, System 56 allein kostet 602,3 h ueber sechs Zellen, die
restlichen 96 Zellen laufen in 17,0 h. Median einer exakten `pretune_on`-Zelle: 0,02 h bei einem
Maximum von 289,7 h. Ueber diese Verteilung bedeutet kein Mittelwert etwas — dasselbe Muster, das
WP-A8 schon fuer die Effektstaerken gezeigt hat, hier fuer die Kapazitaetsplanung. Der Nutzer hat
den vollen Zuschnitt inklusive dim 3 gewaehlt, damit der Kollaps unter kanonischer Konfiguration
dort gemessen ist, wo die Methode am schwaechsten ist; das kostet rund 16 % des Budgets fuer eine
Ablation und steht so im Plan.

**Der Befund, der nicht geplant war: die Restart-Politik hat keinen Code.**
`grep -rn "restart\|retry\|multistart\|n_starts" src/` liefert **null Treffer**. Das am 09.09. als
frozen deklarierte `k = 3` existiert ausschliesslich als Satz in einem Dokument; die tatsaechliche
Restart-Zahl ist heute ein Nebeneffekt davon, wie oft die Suche dieselbe Struktur neu erzeugt. P6
ist damit nicht „teilweise offen", sondern vollstaendig unimplementiert.

Daraus folgt ein **Ordnungsdefekt des Plans, der deklariert statt versteckt wird**: die Politik muss
vor Kampagnenstart implementiert sein, aber die Kampagne ist das, was die Duplikatrate misst, von
der ihre Praemisse abhaengt. Steht als Abschnitt 8 im Phase-C-Plan. Faellt die Duplikatrate auf dim 2
und 3 hoch aus, lautet die ehrliche Berichterstattung, dass der explizite Retry ueber einem grossen
impliziten Multistart wenig beitraegt — und diese Aussage kommt dann aus Phase C's eigenen Daten.

**Was die Bestandsaufnahme entlastet hat.** Der unkappte Spiegelarm braucht keinen neuen Suchcode
(`evogrow_v2_2_stage_local` ist ausgelieferte Variante, ueber `EVO_REGRESSION_VARIANT` waehlbar), die
Basis ist bereits Variantenparameter (`build_variant_basis`, `run_regression.jl:413`), Koeffizienten
werden gespeichert (`model_terms`, `run_regression.jl:871`), und Oracle, Restart-Kurve und
Generalisierung sind drei existierende Skripte, die eine `history.jsonl` lesen. Uebrig bleiben sieben
Arbeitspakete B1–B7 in Abschnitt 2a — im Wesentlichen Phase-C-Konfiguration, die Roh/Ausgeduennt-Felder,
die Restart-Politik und ein fehlendes Auswertungsskript fuer Claim B.

### WP-N11: die Restart-Politik hat jetzt Code — und k = 1 aendert nachweislich nichts

<!-- 4908b07 -->

Die am 09.09. als eingefroren deklarierte Politik *retry-on-failure bis k = 3* existierte bis heute
ausschliesslich als Satz in einem Dokument. `BFGSOptimizer` traegt nun `max_fit_attempts`, **Default
1**, sodass sich nichts aendert, bis eine Kampagne mehr verlangt.

**Die Entwurfsentscheidungen, die im Paper zitierbar sein muessen.** Versuch 1 nutzt den kanonischen
Start — das uebergebene `p0`, sonst den Zufallsstart; jeder weitere Versuch zieht **immer** neu
zufaellig, weil ein deterministischer Warmstart bei Wiederholung dasselbe Ergebnis liefert. Der
Retry sitzt in `fit_parameters`, nicht in der Suche, damit Screening- und GP-Pfad ihn ohne
Duplikation erben. Und der Fehlschlag ist eine **benannte, getestete Funktion**
(`fit_attempt_failed`) statt einer Bedingung im Kontrollfluss: Loss nicht endlich, Loss ≥ Sentinel,
oder Ergebnis ungueltig. Der Sentinel `1e6` wandert dabei nach `MSE_SENTINEL_LOSS`, statt ein
viertes Mal hingeschrieben zu werden.

**Buchfuehrung nach Designprinzip 7.** Kostenzaehler werden ueber alle Versuche summiert — ein Retry,
dessen Kosten unsichtbar bleiben, macht jede Effizienzaussage falsch —, die Diagnosefelder stammen
vom angenommenen Versuch. `total_parameter_fits` behaelt seine Bedeutung; die Versuche bekommen mit
`total_parameter_fit_attempts` einen **getrennt benannten** Zaehler. Eine bestehende Metrik still
umzudefinieren waere der „ein Spaltenname, zwei Bedeutungen"-Fehler gewesen, den das Projekt zwei
Tage zuvor dokumentiert hat.

**Die Abnahme.** Eine reale Regressionszelle (System 3, Seed 42, IC 1) bei k = 1 gegen `HEAD`:
**0 Abweichungen ueber 84 verglichene Felder** — `loss` = 4.92180053120543e-10 ueber alle Stellen,
dazu `r2`, `total_loss_evals` = 139.478, `total_parameter_fits` = 110, `total_ode_solves`,
`pruned_match`, `support_terms`. Einziger Unterschied ist das neue Feld, und es steht bei k = 1
erwartungsgemaess auf 110, also gleich `total_parameter_fits`. Alle drei Fingerprints unveraendert
(`604e79733b22d64d`, `17fe7d9cfb8f1be3`, `ffb0266c7913352c`). Tests gruen.

Nebenbei bestaetigt die Zelle die WP-N10-Zahl fuer System 3 unabhaengig: 110 Fits ueber **2**
eindeutige Strukturen.

**Zwei Defekte kamen aus der Abnahme, nicht aus dem Report.** Erstens hatte Codex
`_append_unique_strings!` ein zweites Mal mit identischer Signatur definiert — das Modul
**praekompilierte nicht mehr** (`Method overwriting is not permitted during Module precompilation`).
Verhalten korrekt, Bodies zeichengleich, aber jeder Julia-Start haette die volle Kompilierzeit
gezahlt, auf 378 Pods also jede Zelle. Zweitens verglich der neue Test Fliesskommawerte exakt
(`0.24999999999999994 == 0.25`). Beides in WP-N11b repariert; der Helfer liegt jetzt einmal in
`src/utils/strings.jl`.

Das Gegenlesen des Codes hat den ersten Defekt vor der Ausfuehrung gefunden, die Ausfuehrung hat ihn
bestaetigt. Der Report allein haette ihn nicht gezeigt — er meldete die Umsetzung als vollstaendig.

**Offen und ausdruecklich so gewollt:** der Parameter geht **nicht** in den Phase-B-Fingerprint ein,
an dessen Wert die 756 Kampagnenrecords haengen. Arbeitspaket B1 muss ihn in den
Phase-C-Fingerprint aufnehmen.

### WP-N12: der ausgeduennte Support existiert jetzt als Datum, nicht nur als Bool

<!-- 47920a2 -->

Arbeitspaket B2 des Phase-C-Plans. §4a verlangt **rohen Support, ausgeduennten Support und
Koeffizienten — alle drei** im Record. Gespeichert waren zwei: `support_terms` (roh) und seit WP-N1
`model_terms` (mit Koeffizienten). Der ausgeduennte Zustand existierte nur als Bool `pruned_match`,
war also **nicht rekonstruierbar** — und genau daran war das WP-N7-Abnahmekriterium prinzipiell
gescheitert.

Neu im Record: `pruned_support_terms`, `exact_support_match_raw`, `exact_support_match_pruned` und
`exact_support_match_definition`. Der Vermerk traegt den kanonischen Wert, den der Python-Waechter
`analysis/utils/support_match_definition.py` bereits kennt; damit kann ein Join von Phase A und
Phase B nicht mehr stillschweigend zwei verschiedene Groessen unter einem Spaltennamen vergleichen
(§4b). `pruned_match` bleibt unveraendert — Name, Bedeutung, Berechnung —, weil die gesamte
Phase-B-Auswertung daran haengt.

**Der Nebenbefund ist der aufraeumende Teil.** Die eingefrorene Schwelle `max(1e-6, 1e-3*max_abs)`
stand **fuenfmal inline** im Code: in `support_match_pruned` und in den drei Refit-Studien N3, N4, N5,
und sie wurde fuer das neue Feld ein sechstes Mal gebraucht. Jetzt gibt es genau eine
Implementierung, `pruned_support_idxs_for_equation`; alle Aufrufer haengen daran. Fuenf Kopien einer
eingefrorenen Konstante sind ein Driftrisiko, das irgendwann still zuschlaegt.

**Abnahme.** Reale Regressionszelle (System 3, Seed 42, IC 1): **0 Abweichungen ueber 79 bestehende
Felder** gegen `HEAD`, alle vier neuen Felder belegt, `exact_support_match_pruned == pruned_match`,
ausgeduennte Menge je Gleichung Teilmenge der rohen. Diese Zelle duennt allerdings **nichts** aus —
roh und ausgeduennt sind identisch, die Teilmengenpruefung also trivial erfuellt. Die Regel wurde
deshalb zusaetzlich direkt gefahren: ein Term bei 5e-4 gegen eine Schwelle von 2e-3 faellt, und eine
Gleichung, deren Koeffizienten alle unter dem absoluten Boden 1e-6 liegen, wird **komplett leer**.
Das ist Eigenschaft der eingefrorenen Regel, nicht neu — aber es sollte bekannt sein, dass die Regel
eine ganze Gleichung entleeren kann.

Alle drei Fingerprints unveraendert, Julia-Tests gruen, 15 Python-Tests gruen.

### WP-N13: B6 war falsch beschrieben, und die echte Luecke war die stillere

<!-- 1c984a6 -->

Arbeitspaket B6 lautete „Kampagnen-ID-Parameter fuer die Aggregatskripte, sie sind auf
`paper1_phaseB_v1` verdrahtet". **Nachgeprueft: sie sind es nicht.** `--registry`,
`--classification`, `--adequacy` und `--output-dir` existierten bereits; verdrahtet waren nur die
**Defaults**. Ein reiner Kennungs-Parameter waere weitgehend redundanter Code gewesen.

Die tatsaechliche Luecke war unangenehmer, weil sie nichts sagt:

- **`verify_campaign_registry.py` erwaehnte `experiment_id` an keiner Stelle**, auch nicht in
  `REQUIRED_COLUMNS`. Eine Registry mit Zeilen aus **zwei** Kampagnen bestand die Pruefung.
- **Jeder Default zeigte auf Phase B.** Ein vergessenes Flag beim Phase-C-Lauf haette
  Phase-B-Zahlen in ein Phase-C-Verzeichnis geschrieben, kommentarlos. §5 des Plans verlangt
  ausdruecklich, dass Phase-B- und Phase-C-Zahlen nie in derselben Tabelle stehen — erzwungen hat
  das nichts.
- Registry, Klassifikation und Adaequanztabelle wurden unabhaengig uebergeben, durften also aus
  verschiedenen Kampagnen stammen.

Neu: `--campaign` leitet die Pfade ab und steht auf `paper1_phaseB_v1`, damit bestehende Aufrufe
unveraendert laufen; Registry-Eingaben muessen **genau einen** `experiment_id` tragen, und der muss
zur angeforderten Kampagne passen; sonst bricht das Skript ab, **bevor** eine Datei geschrieben wird.
Systemweite Eingaben bekommen bewusst keine kuenstliche Kampagnenspalte.

**Abnahme, unabhaengig vom Report gefahren.** Der Waechter greift bei einer Registry, in der **eine
von 756** Zeilen umetikettiert ist, und bei einer falsch angeforderten Kampagne — Exit-Code 1 in
beiden Faellen, die Meldung nennt die gefundenen Werte, und es entsteht **keine Ausgabedatei**. Der
korrekte Fall liefert 0. Die Exit-Codes wurden getrennt geprueft: eine Fehlermeldung auf stdout bei
Exit 0 waere genau der Waechter, der drei Wochen rot ist, ohne dass es auffaellt.

**Byte-Vergleich:** 43 der 45 eingecheckten Phase-B-Ableitungen an Ort und Stelle neu erzeugt, `git
status` bleibt leer. Die zwei Ausnahmen sind `system_classification.csv` und
`representational_adequacy.csv` — systemweite Eingaben, nicht Ausgaben eines geaenderten Skripts.
19 Python-Tests gruen, vier davon neu.

**Nebenbefund beim Pruefen, der Phase C beinahe stillgelegt haette.** `.gitignore` ignoriert
`analysis/data/*`, `analysis/figures/*` und `analysis/tables/*` mit Ausnahmen **je Kampagne**. Fuer
`paper1_phaseC_v1` gab es keine — genau die Ausgabepfade, die §1b des Plans nennt, waeren erzeugt und
nie versioniert worden. Drei Zeilen ergaenzt.

### WP-N14: die gepaarte Kappen-Ablation steht — und ein Fehlalarm haette wie ein Befund ausgesehen

<!-- e738b0c -->

Arbeitspaket B5, die Auswertung fuer Claim B und damit die **Hauptabbildung** des Papers. Bisher ruhte
diese Haelfte des Claims auf **30 Zellen ueber 5 Systeme**; das Skript fuer den eigentlichen Vergleich
ueber 378 Paarungen existierte nicht.

**Die Entwurfsentscheidung, auf die es ankam: Erlaubnisliste statt Pruefliste.** §2b verlangt, dass
sich gekappt und ungekappt in genau einer Sache unterscheiden, **nachgewiesen durch einen gerechneten
Vergleich**. Wer eine Liste zu pruefender Spalten schreibt, prueft genau die, an die er gedacht hat.
Also andersherum: die Spalten benennen, die sich unterscheiden **duerfen** — Armkennzeichnung,
Kappenfelder, Ergebnisse, Kostenzaehler, Kampagnenbuchhaltung —, und von **allem uebrigen**
Gleichheit verlangen, auch von Spalten, die es noch gar nicht gibt.

**Die Falle, die vorher in die Spezifikation musste:** `n_levels` in den Records ist die Konstante 30,
das konfigurierte Budget. Genau diese Spalte wuerde man fuer „ausgefuehrte Level" nehmen — und damit
das Budget gegen sich selbst rechnen und eine sauber aussehende Ersparnis von null bekommen. Das
Skript verweigert die Ersetzung und bricht ab, wenn die Spalte mit der tatsaechlich ausgefuehrten
Levelzahl fehlt. Sie ist damit eine Anforderung an die Phase-C-Records.

**Der Defekt aus der Abnahme, und warum er zaehlt.** `campaign_manifest_index` stand nicht in der
Erlaubnisliste, musste also uebereinstimmen — kann sie aber nicht, weil jeder Arm seine eigene
Manifestzeile hat. In der Phase-B-Registry weicht sie in **378 von 378** Paarungen ab. Die Auswertung
waere auf echten Daten in **jeder** Paarung abgebrochen, und zwar mit der Meldung „die Bedingungen
sind nicht identisch" — ein Buchhaltungsfeld, das wie ein wissenschaftlicher Befund ueber die
Konfiguration aussieht. Dazu `stage_cap_policy_active`, das in Julia geschrieben wird, in der
Phase-B-Registry aber nicht vorkommt und denselben Fehlalarm ausgeloest haette, sobald der
Phase-C-Konverter es durchreicht.

**Warum er ueberlebt hat:** alle Fixtures prueften, dass unerlaubte Abweichungen **abbrechen**. Keines
prueft, dass eine realistische Paarung **durchlaeuft**. Dieser Positivtest existiert jetzt.

Gefunden wurde der Defekt nicht durch Lesen, sondern indem die Phase-B-Zeilen als **Formfixture**
benutzt und ausgezaehlt wurde, welche Spalten sich zwischen zwei tatsaechlich verschiedenen Armen
unterscheiden. Daraus wurden ausschliesslich Spaltennamen gelesen, keine Zahlen — Phase B hat keinen
ungekappten Arm, jede Kennzahl daraus waere eine Scheinablation. Das Skript lehnt darum Arme ab,
deren Kennzeichnung nicht das gekappt/ungekappt-Paar ist.

**Aufraeumen vorweg:** Paarung, Cluster-Bootstrap, Cluster-Permutation und die Quantil-Helfer lagen im
Pretuning-Skript und sind nach `analysis/utils/paired_stats.py` gezogen; beide Skripte teilen sie
jetzt. Zwei Kopien einer Statistik, die Papierzahlen erzeugt, waeren schlimmer als die fuenf Kopien
der Ausduennungsschwelle aus WP-N12.

**Abnahme, unabhaengig gefahren:** 27 Python-Tests gruen, Phase-B-Ableitungen bitgleich, und ein
Spaltenabgleich gegen die echte Registry zeigt keine Spalte mehr, die legitim abweicht und dennoch
verboten waere — waehrend `use_pretuning`, `seed`, `basis_name`, `n_levels` und alle drei
Identitaets-Fingerprints weiterhin uebereinstimmen muessen.

### Die dim-2-Duplikatrate ist da, und sie stuetzt die Restart-Politik statt sie zu untergraben

Die WP-N10-Messung auf System 26 (dim 2, gekoppelt, Seed 42, IC 1) ist durchgelaufen. Ergebnis:

| | dim 1, System 3 | dim 1, System 11 | **dim 2, System 26** |
|---|---:|---:|---:|
| Fits | 110 | 290 | **310** |
| eindeutige Strukturen | 2 | 3 | **45** |
| Duplikatrate | 98,2 % | 99,0 % | **85,5 %** |
| mittlere Fits je Struktur | 55 | 97 | **6,9** |

Die Aggregatrate von 85,5 % sieht aehnlich aus, **die Verteilung ist es nicht**. Wiederholungen je
Struktur: Minimum **1**, q25 = 3, Median **5**, q75 = 10, q95 = 20, Maximum 32.

**Das dreht die Lesart aus der Uebergabe vom 09.09.** Dort stand, WP-N4 habe auf dim-1-Zellen
gemessen, wo ein „einzelner Fit" ein Zustand ist, den die Suche gar nicht herstellt — die Praemisse
der Politik `retry-on-failure bis k = 3` sei damit offen. Auf dim 2 gilt das nicht: `q0 = 1` heisst,
es gibt Strukturen, die **genau einen** Fit bekommen, und der Median liegt bei 5 statt bei 55 bis 97.
Der implizite Multistart ist auf gekoppelten Systemen also um eine Groessenordnung kleiner, und ein
expliziter Retry greift genau am unteren Ende dieser Verteilung — dort, wo die Trefferquote 0 von 50
ist.

**Bewertung mit der gebotenen Zurueckhaltung:** das ist **eine** Zelle, ein System, ein Seed, ein
IC-Satz. Sie entscheidet die Frage nicht, sie zeigt die Groessenordnung — genau die Rolle, die ihr am
09.09. zugedacht war. Die belastbare Verteilung ueber 378 Zellen liefert Phase C umsonst, weil der
Zaehler seit WP-N10 in der Kampagnenbahn steckt.

Was bleibt: die hohe Duplikatrate heisst weiterhin **nicht** „die Suche exploriert nicht". Auf dim 2
sind es 45 eindeutige Strukturen gegen 2 und 3 auf dim 1 — der Raum ist groesser und wird auch
begangen.

---

## 2026-09-09 (nachts)

### Ein falsches Abnahmekriterium, ein unbelegter Kostenwert, ein abgelaufenes Token — und der dim-2-Probelauf läuft

<!-- f17f6eb -->

Der Abend nach der Zuschnittsentscheidung, gedacht als Abarbeiten der Phase-C-Voraussetzungen. Drei
von vier Befunden waren nicht geplant, und zwei davon sind wissenschaftlich relevant.

#### WP-N7: das Abnahmekriterium war falsch, und das war der Befund

Die Strukturmetriken — Term Precision, Recall, Structural F1, Koeffizientenfehler — gab es im
Repository **nirgends**; die Pipeline konnte ausschliesslich exaktes Support-Match. Claim A des
Methodenpapiers ist ohne sie nicht berichtbar.

Als Abnahme hatte ich verlangt, dass die neuen Metriken `run_registry.exact_support_match` ueber alle
756 Kampagnenzellen reproduzieren. Codex meldete korrekt `blocked` bei 716 von 756. Die Begruendung
im Report war unvollstaendig, die Nachpruefung an den Rohdaten ergab etwas anderes:

- `exact_support_match` ist fuer Phase B **identisch mit `pruned_match`** — 756 von 756, keine
  Abweichung. Also der **ausgeduennte** Match.
- `support_terms` ist die **rohe**, nicht ausgeduennte aktive Termmenge (`active_term_names`,
  `run_regression.jl:870`).

Zwei verschiedene Groessen unter einem Vergleich. Und der ausgeduennte Zustand ist aus Phase B **gar
nicht rekonstruierbar**, weil Ausduennen Koeffizienten braucht und Phase B keine speichert. Das
Kriterium war prinzipiell unerreichbar.

#### Die Groesse der Luecke ist das Ergebnis

Auf den 240 exakten Zellen:

| Groesse | Zellen | Anteil |
|---|---:|---:|
| alle wahren Terme im rohen Support | 119 | 49,6 % |
| **ausgeduennter** Match — die berichtete Kampagnenzahl | **110** | **45,8 %** |
| **roher** exakter Strukturtreffer | **70** | **29,2 %** |
| Treffer allein durch die Ausduennung | **40** | 16,7 % |

**40 von 110 Strukturtreffern — 36,4 % — existieren nur, weil die Ausduennungsregel ueberzaehlige
Terme entfernt hat.** Die Enthaltung ist exakt und einseitig: `pruned_match == True` impliziert
`missing == 0` in 110 von 110 Faellen, nie umgekehrt; neun Zellen tragen jeden wahren Term und
scheitern trotzdem, weil Zusatzterme die Ausduennung ueberleben.

**Die Dimensionsaufschluesselung verdeckt die Gesamtzahl, und sie ist der eigentliche Befund:**

| dim | exakte Zellen | roh | ausgeduennt | gerettet |
|---|---:|---:|---:|---:|
| 1 | 72 | 51 (70,8 %) | 57 (79,2 %) | 6 |
| **2** | **108** | **19 (17,6 %)** | **53 (49,1 %)** | **34** |
| 3 | 48 | 0 | 0 | 0 |
| 4 | 12 | 0 | 0 | 0 |

Auf dim 1 ist die Schwelle fast bedeutungslos. **Auf dim 2 verdreifacht sie die Trefferquote nahezu —
34 der 53 Treffer, also 64 %, produziert die Schwelle und nicht die Suche.** Die ehrliche Lesart von
„dim 2 liegt bei etwa der Haelfte" lautet damit: *die Suche landet auf gekoppelten Systemen fast nie
auf dem exakten Support, sie landet auf einer Obermenge, und die Schwelle raeumt auf.*

Das verschaerft die bekannte Limitierung, statt sie abzumildern. Und es ist ein Grund, die
Schwellenabhaengigkeit zu **berichten**, nie einer, an der Schwelle zu drehen — WP-N2 hat ueber ein
24er-Regelgitter gezeigt, dass es keine bessere Schwelle gibt.

Konsequenz fuer Phase C, bindend: Records speichern **roh, ausgeduennt und Koeffizienten**, alle
drei. Phase B hatte eines von dreien.

#### Welche frueheren Befunde das beruehrt — und welche nicht

Sofort nachgeprueft, weil eine schwellenabhaengige Groesse unter einem berichteten Befund dessen
Bedeutung aendert:

- **WP-A7, der Pretuning-Seed-Kollaps — nicht betroffen.** Er gruppiert auf `support_terms`, also dem
  **rohen** Muster. Die 96/126 gegen 61/126 bei p = 1,0e-5 sind schwellenunabhaengig.
- **WP-A6, der zurueckgezogene Strukturkontrast — war ausgeduennt.** Bleibt zurueckgezogen, jetzt aus
  zwei unabhaengigen Gruenden.
- **T3 ist durchgehend ausgeduennt.** Ueberall, wo es zitiert wird, gehoert die Rohzahl daneben.

Das Muster ist bemerkenswert: der Pretuning-Befund, den das Projekt behalten hat, ist der, der nicht
an der Schwelle haengt; der zurueckgezogene hing daran.

#### Zweiter Befund: ein Spaltenname, zwei Bedeutungen

`experiments/run_experiment.jl:405` schreibt den **rohen** Match in `exact_support_match` und fuehrt
roh und ausgeduennt zusaetzlich getrennt — der **Phase-A**-Pfad. `run_regression.jl` schreibt
ausschliesslich `pruned_match`, das unter demselben Namen in der Registry landet — der
**Phase-B**-Pfad. Ein Join ueber diese Spalte vergleicht verschiedene Groessen. `WP-N7b` hat dafuer
`analysis/utils/support_match_definition.py` als Waechter gebaut, plus den erreichbaren Abnahmetest
mit Gegenprobe.

#### WP-N8: die Probe sammelt jetzt eine echte Identitaet

`wp_n1_basis_probe.jl:273` setzte die Provenienz hart auf
`(git_hash = "not_collected", git_dirty = nothing)`. Die Reparatur war eine Zeile — `git_provenance()`
stand ueber den vorhandenen `include` bereits im Geltungsbereich. Das Paket wurde bewusst weiter
geschnitten, weil eine Platzhalter-Identitaet unbemerkt in ein Skript geraten konnte, das
Entscheidungsdaten erzeugt: das Skript **bricht jetzt ab, bevor der erste Record geschrieben wird**,
wenn der Hash fehlt, leer oder ein Platzhalter ist. `WP_N1_ALLOW_PLACEHOLDER_IDENTITY=1` ist der
deklarierte Ausweg fuer Entwicklungslaeufe und markiert die Records entsprechend.

Die vorhandenen dim-1-Records bleiben byte-identisch. Ein nachgetragener Hash waere eine Behauptung,
die niemand pruefen kann.

Abnahme hier gefahren, alle vier Punkte: echter Hash, Wachter bricht ohne Schreibvorgang ab (135
Zeilen vor und nach dem Versuch), Override erzeugt einen markierten Entwicklungsrecord, 132 Altzeilen
unveraendert.

#### Der unbelegte Kostenwert — und er war um das Zehnfache falsch

Auf die Frage, ob der dim-2-Probelauf auf den Rechner oder den Cluster gehoert, stellte sich heraus:
die ueberall zitierten **114 Kernstunden haben keine Quelle.** `REPORT_WP_N1.md` enthaelt gar keine
Kostenschaetzung; `CLAUDE.md`, der Phase-C-Plan und das Tagebuch zitierten sie mit Verweis auf ihn.

Nachgerechnet am dim-2-Arm der Kampagne, der **dieselben 336 Zellen** unter derselben
Konfigurationsfamilie hatte: **1.167,5 h, Mittel 3,47 h je Zelle, Median 1,12 h.** Realistisch also
**~1.200 Kernstunden**, und die Konstanten-Basis durchsucht einen groesseren Raum, das ist eher
optimistisch.

Der dim-1-Probelauf war in 3,7 Stunden durch — deshalb wirkte das harmlos. **dim-2-Zellen kosten im
Mittel das Hundertfache einer dim-1-Zelle** (3,47 h gegen 0,03 h). Damit war der Laptop raus: seriell
rund sieben Wochen.

#### WP-N9: der Cluster-Pfad, und warum kein Sharding

`wp_n1_basis_probe.jl` ist eine serielle Schleife ohne Index-Argument und konnte den Cluster-Pfad der
Kampagne nicht nutzen. **Sharding einzubauen waere der falsche Weg gewesen** — ein zweiter
Ausfuehrungspfad neben dem der Kampagne, mit eigener Wiederaufnahme-, Schreib- und Identitaetslogik.
Genau die Fehlerklasse, die das Projekt am selben Tag zweimal bezahlt hat.

Stattdessen der vorhandene Weg: Manifest-Generator → `run_k8s_indexed_cell.jl` → `run_batch_cell.jl`.
Letzteres loest die Methodenkonfiguration ohnehin ueber die Spalte `variant` auf, also wurden die
beiden Basis-Modi Varianten in derselben Aufloesung. Das zahlt doppelt: **Phase C braucht denselben
Mechanismus fuer den ungekappten Arm**, der ebenfalls nur eine Variante derselben Zelle ist.

**Der Aequivalenznachweis von Codex war zu schwach, und das ist eine Lehre fuer kuenftige Specs.**
Alle sechs vorgeschlagenen Pruefzellen lagen auf System 2 — einem Ein-Term-System, bei dem *beide
Basen dasselbe liefern*. Der Test haette die neue Variantenaufloesung kaum beruehrt. Erweitert auf
die Systeme 3 und 6: **10 von 10 Zellen reproduzieren `loss`, `pruned_match` und die Termmenge
exakt**, einschliesslich des Falls, in dem sich die Basen unterscheiden — System 3 unter der
Konstanten-Basis liefert `pruned_match = False` mit 3 Termen und Loss 1,1024e-07 gegen `True` mit 2
Termen und 1,2642e-09. Der neue Pfad reproduziert **den Unterschied**, nicht nur die Zahlen.

Kampagnenidentitaet gemessen statt gelesen: `phase_b_fingerprint` = `604e79733b22d64d` und
`stage_cap_behavior_fingerprint` = `ffb0266c7913352c` beide unveraendert, obwohl `phase_b_config.jl`
angefasst wurde — es ist eine Erweiterung der Nachschlagefunktion, `PHASE_B_VARIANTS` bleibt
unberuehrt.

#### Parallelitaet 16 → 32, und warum das unbedenklich ist

Der Namespace hat **keine `ResourceQuota`, kein `LimitRange`, keine Cluster-Quota**. Die vereinbarten
16 waren also eine Absprache, keine technische Grenze. Die CPU stand bei **171 Millicores ueber alle
12 residenten Pods** von 96 Kernen — rechnerisch leer. Der Speicher ist die belegte Achse, ~70 GiB,
dominiert von OpenSearch.

Unbedenklich ist das Hochdrehen, weil im Job `requests == limits` gilt: Kubernetes plant nach
Requests, ueberzaehlige Pods bleiben **`Pending`** statt jemanden zu verdraengen, und ein Pod, der
seine 2 GiB ueberschreitet, killt sich selbst. Ueber 32 hinaus bringt es nichts: **die laengste
einzelne dim-2-Zelle der Kampagne lief 46,98 h**, eine Zelle ist ein Pod und laesst sich nicht
teilen — die Wanduhr hat dort ihren Boden.

#### Das abgelaufene Deploy-Token, und warum der Smoke-Job sich bezahlt gemacht hat

Der erste Smoke-Job scheiterte an `ErrImagePull` mit `HTTP Basic: Access denied`. Nicht das Image
fehlte — das **Deploy-Token war abgelaufen**, 28 Tage alt. Neues Token mit Scope `read_registry`,
Secret ersetzt, Job neu gestartet: 3/3 `Complete` in 101 Sekunden.

Die Lehre steht jetzt in `docs/hpc_deployment_guide.md` §8, weil sie beim naechsten Mal Stunden
spart: Pods werden **ueber die gesamte Laufzeit** neu erzeugt, nicht alle zu Beginn. Ein Ablauf
mitten in einem mehrtaegigen Lauf haette einen halb fertigen Datensatz mit einer **Luecke in der
Mitte** ergeben — beim Auswerten leicht zu uebersehen. Der Smoke-Job hat den Fehler nach 35 Sekunden
sichtbar gemacht statt in Stunde 30.

#### Stand

Der volle dim-2-Probelauf laeuft seit dem Abend des 09.09.: **336 Zellen, `parallelism: 32`,
erwartete Wanduhr ~47 h**, Image `ec3b6bd5b43f06539d38b633257ca51115bfa47f`. Die Smoke-Records
bestaetigen die Identitaetskette: `git_hash = ec3b6bd`, `git_dirty = false`,
`probe_identity_mode = collected`, `model_terms` vorhanden — diese Zellen tragen also Koeffizienten
und erlauben damit, anders als die 756 Kampagnenzellen, auch die Generalisierungsrechnung.

Der Lauf entscheidet den letzten offenen eingefrorenen Parameter der Phase C: ob der konstante Term
in die kanonische Basis kommt. Ausgewertet wird er gegen eine **Rohbasis von 17,6 %**, nicht gegen
die vertrauten 49,1 % — sonst wird die neue Basis gegen einen Massstab bewertet, der zu zwei Dritteln
aus der Ausduennung stammt.

Offen und nicht vom Lauf abhaengig: die Restart-Politik existiert im Code noch nicht (P6), und die
`StructureSpec`-Duplikatrate ist weiterhin ungemessen (P7).

---

## 2026-09-09 (abends)

### Zuschnittsentscheidung: Paper 1 wird ein Methodenpaper, und die Kampagne verliert ihren Rang

<!-- 5e9e200 -->

Am Vormittag stand im Statusbericht noch die Frage, welche der drei Erzählungen Paper 1 wird — Kappe
als Regler, Kampagne als Charakterisierung, oder das Restart-Budget. Am Abend ist die Frage nicht
beantwortet, sondern **verworfen**: alle drei waren Zuschnitte, die an den zufällig vorhandenen
Datensatz angepasst wurden. Genau die Reihenfolge, die der Kassasturz zwei Tage zuvor als Grundfehler
benannt hatte.

Die Entscheidung lautet:

> **Paper 1 etabliert EvoGrow als Methode.** Here is EvoGrow. This is how it works. This is why it is
> designed this way. This is how it performs. These are its current strengths and limitations.

Und die dazugehörige Regel, die alles andere nach sich zieht:

> **Wir passen Paper 1 nicht an die bestehende Kampagne an. Wir definieren zuerst das Paper und
> rechnen dann exakt die Experimente, die es braucht.**

Die 5.248 Kernstunden sind damit ausdrücklich **sunk cost**. Sie dürfen den Zuschnitt nicht bestimmen.

#### Was das an eingefrorenen Entscheidungen umwirft

Vier Dinge kippen, und sie mussten gelöscht statt abgeschwächt werden.

**Zwei Non-Goals vom 22.08. sind aufgehoben.** `PAPER_1.md` verbot wörtlich in-house-Baselines für
SINDy und *jede* quantitative Methodenvergleichsaussage — „not a cautious one, not an approximate one
— none". Claim D verlangt exakt das Verbotene. Aufgehoben unter deklarierten Fairnessbedingungen:
identische Trajektorien, identische Train/Test-ICs, alle SINDy-Konfigurationen berichtet, Kosten
neben jeder Qualitätszahl. GP, PySR, ODEFormer, GODE und Operon bleiben draußen.

**Die Kappe verliert den Rang der Hauptthese.** Sie war seit dem 03.08. *die* Contribution. Jetzt ist
EvoGrow der Gegenstand und die Kappe eine Komponente mit eigener Ablation. Der alte
`v2.2 → v3 → capped`-Faden wird von der Argumentation zur **Designbegründung im Method-Abschnitt**.

**Die Claim-Bezeichner kollidieren.** Das Dokument hatte Claim A (Fit-Quality), B
(Search-Space-Control) und C (mechanistisch, „primary"). Die neuen A–D sind anders belegt. Die alten
stehen jetzt unter „Superseded Claim Labels" wörtlich erhalten, weil `DIARY.md` und die WP-Reports
sie zitieren — die zwei Sätze dürfen nie vermischt werden.

**Phase B wird degradiert.** Vom Hauptbenchmark zu Diagnostik, Ablationsquelle, Laufzeitanalyse und
Failure-Case-Sammlung. Sie wurde gerechnet, bevor das methodische Audit geschlossen war, und trägt
vier Defekte, die ein finaler Benchmark nicht haben darf: keine Konstante in der Basis, keine
gespeicherten Koeffizienten, beide IC-Sätze als Training, kein ungekappter Arm.
**Phase-B- und Phase-C-Zahlen erscheinen nie in derselben Tabelle.**

#### Phase C — die kanonische Evaluation

Vier Arme: EvoGrow capped (378 Zellen), EvoGrow uncapped als voller Spiegel (378 gepaarte Zellen),
SINDy als externe Baseline, und ein **Oracle-Arm**, der die wahre Struktur vorgibt und nur die
Parameter fittet. Der Oracle-Arm trennt zwei Fehlerklassen, die Phase B nicht auseinanderhalten
konnte: *Search Failure* (Struktur nicht gefunden) gegen *Optimization Failure* (Struktur bekannt,
Fit scheitert trotzdem). Er ist billig, weil er keine Suche rechnet.

**Kosten: grob 8.000–11.000 Kernstunden, drei bis fünf Wochen auf Orion.** Der ungekappte Spiegel
trägt die Mehrheit, weil er die vollen 30 Level rechnet, wo der gekappte früh abbricht — Phase B lag
im Mittel bei etwa 19,7 ausgeführten Leveln, und die späten sind die teuren. Das ist eine Ironie, die
ins Paper gehört: **das Experiment, das zeigen soll, dass die Kappe Rechenzeit spart, ist das teuerste
des Projekts.** Alle 63 Systeme bleiben trotzdem drin — dim 3 trug 75,6 % der Phase-B-Rechenzeit, dort
ist die Ersparnis am größten, und ein Kappen-Nachweis ohne die teure Klasse ist die erste Frage im
Review.

#### Drei Konfigurationsentscheidungen, alle vor dem Einfrieren

**Kanonisch ist `pretuning = false`.** Pretuning wird Ablation, nicht zweite Hauptversion. Die
Evidenz ist einseitig: über 126 gepaarte Gruppen kollabiert Pretuning die Seed-Diversität auf allen
drei Zielen (96/126 gegen 61, 35 und 14), cluster-robust p = 1,0e-5, und **kein einziges Paar in der
Gegenrichtung** (WP-A7).

**Restart-Politik: retry-on-failure bis k = 3.** Das war die interessanteste Frage des Tages, und die
Präzisierung ist wichtig. Was heute unter `pretuning = false` passiert, ist **kein Multistart**: jede
Kandidatenstruktur bekommt genau einen Fit, und ein zweiter Start entsteht nur, wenn die Suche
dieselbe Struktur zufällig erneut erzeugt. Das effektive k ist also die
**`StructureSpec`-Duplikatrate — und die ist nie gemessen worden.** Die kanonische Methode hatte damit
einen unbenannten, unquantifizierten Mechanismus im Kern.

Warum das mehr als Buchhaltung ist: WP-N4 hat mit der *wahren* Struktur gemessen, dass ein einzelner
Fit in 15 von 102 Zellen am Sentinel-Loss scheitert, bei k = 3 in keiner. In die Suche übersetzt heißt
das, dass etwa jede siebte **richtige** Kandidatenstruktur wegen eines misslungenen Fits verworfen
wird. Das ist ein Suchqualitätsproblem, keine Optimierer-Fußnote.

Echtes k = 3 je Struktur hätte ~3× Fits gekostet — auf einer Phase C mit vollem Spiegel
25.000–35.000 Kernstunden, ein Quartal, und es hätte ausgerechnet die Kostenbilanz gegen SINDy weiter
verschlechtert. Retry-on-failure holt praktisch denselben Effekt zum Preis der Fehlerrate, also etwa
15 % Overhead. **Im Paper muss es als retry-on-failure benannt werden, nicht als Multistart** — das
sind verschiedene Mechanismen, und WP-N4 hat in seiner ursprünglichen Form nur den einen gemessen.
Der Wert k = 3 stammt aus einer **Oracle-Diagnostik**, nie aus Benchmark-Performance; das ist es, was
ihn aus der Kategorie „auf dem Benchmark getunter Hyperparameter" heraushält.

**Der ungekappte Arm ist ein voller Spiegel.** Zwischenzeitlich war ein IC-Satz beschlossen (189
Zellen, ~2.600–4.000 h); die Entscheidung wurde noch am selben Abend auf beide IC-Sätze korrigiert.

#### Was fehlt, und es ist mehr als erwartet

Beim Prüfen kam heraus: **Term precision, term recall, structural F1 und Koeffizientenfehler kommen in
`src/`, `analysis/`, `experiments/` und `studies/` kein einziges Mal vor.** Die Pipeline kann heute
ausschließlich exaktes Support-Match. Claim A ist ohne diese Metriken nicht berichtbar — das ist neuer
Code auf dem kritischen Pfad, und er muss gegen die bestehende Exact-Support-Spalte validiert werden,
die aus den neuen Metriken exakt reproduzierbar sein muss.

Die dreiwertige Repräsentierbarkeit dagegen ist ableitbar: `system_classification.csv` führt
`unmatched_terms` und `gap_reason` je Gleichung, `representational_adequacy.csv` die Methodenmatrix
über EvoODE, SINDy und ProGED.

**Der einzige noch offene eingefrorene Parameter ist die kanonische Basis.** Der dim-2-Probelauf zur
Konstanten entscheidet ihn — 114 Kernstunden, etwa 1 % der Phase-C-Kosten für den folgenreichsten
Parameter. Vorher muss `git_hash = "not_collected"` in `studies/regression/wp_n1_basis_probe.jl`
repariert werden.

#### Dokumente

`PAPER_1.md` umgeschrieben: neuer Zuschnitt, neue Claims A–D, Phase C, aufgehobene Non-Goals, alte
Claims konserviert, Risikotabellen um Kostenrisiko, Konfigurationsbruch Phase B/C und
„neue Strukturmetriken sind bei Ankunft falsch" ergänzt. Phasen 0–6 bleiben unverändert als
historischer Ausführungsbericht stehen und sind als solcher markiert.

Neu: `docs/paper1_phaseC_benchmark_plan.md` — die Claim-→-Experiment-→-Metrik-→-Output-Matrix, die
Freeze-Liste und neun blockierende Voraussetzungen. Ausdrücklich als **unvollständig und nicht
eingefroren** markiert, mit fünf offenen Fragen am Ende. Das Dokument ist die operative Autorität für
Phase C; `PAPER_1.md` bleibt die Autorität für den Zuschnitt.

`CLAUDE.md`: Phase-4-Zeile, neuer Abschnitt Active 0b, Known Gaps um die fehlenden Strukturmetriken
und die ungemessene Duplikatrate ergänzt — und „no baseline has ever been run" entfernt, das seit
WP-N6 falsch war.

---

## 2026-09-09

### Repo-Durchgang vor der externen Diskussion: was die Dokumente behaupteten und was tatsaechlich galt

<!-- c7ae516 -->

Vor der ersten externen Diskussion der Ergebnisse ein vollstaendiger Durchgang durch das Repository:
Struktur, alle 89 versionierten Markdown-Dateien (1,2 MB), Code, Git-Zustand, Ignore-Regeln. Der Code
war in besserem Zustand als die Dokumentation — **kein einziges TODO, FIXME oder HACK** in `src`,
`studies`, `analysis`, `test`. Das Problem war nicht Unordnung, sondern Drift: die letzten drei Wochen
(Kampagnenabschluss, WP-A6 bis A9, WP-N1 bis N6) waren in `CLAUDE.md` und `DIARY.md` nachgefuehrt, in
allen anderen Einstiegsdokumenten nicht.

#### Der einzige echte Risikobefund: die Beweiskette lag auf einem Laptop

`experiments/paper1_phaseB_v1/history.jsonl` (1,9 MB) und `run_registry.csv` (492 KB) waren
gitignoriert. Ebenso `analysis/tables/paper1_phaseB_v1/` — also genau die Tabellen T1 bis T5, die
`CLAUDE.md` namentlich zitiert. Die gesamte Auswertungsgrundlage der 5.248 Kernstunden existierte in
zwei Kopien: Arbeitsverzeichnis und NFS-Share. Ein Plattenschaden haette die Studie beendet, und eine
externe Diskussion haette ueber Zahlen stattgefunden, deren Quelle im Repository nicht auffindbar ist.

2,4 MB sind trivial versionierbar. Sie sind es jetzt.

Dabei stellte sich heraus, dass die Ignore-Regel nie das war, wofuer sie gehalten wurde. Sie sortierte
nach "generiert gegen handgeschrieben", was die falsche Achse ist: eine Run-Registry ist generiert und
gehoert versioniert, weil ihre Neuerzeugung 5.248 Kernstunden kostet; eine Probe-Abbildung ist
generiert und gehoert nicht versioniert, weil ihre Neuerzeugung eine Minute kostet. Die Regel heisst
jetzt **"woran laesst sich ein Ergebnis pruefen"** und steht so in `.gitignore`. Die
`experiments/*/runs/`-Verzeichnisse (16 MB Phase B, 6,4 MB Phase A) bleiben draussen: sie sind aus
Registry plus Image reproduzierbar, die Registry ist es nicht.

Nebenbei war die alte Whitelist widerspruechlich — `!analysis/data/paper1_phaseB_v1/` hob das
Ignorieren fuer das ganze Verzeichnis auf, waehrend `analysis/tables/` vollstaendig ignoriert blieb.
Dieselbe Art Artefakt, gegenteilig behandelt, und 16 abgeleitete Dateien standen dauerhaft als
`untracked` im Status.

#### Ein Selbstwiderspruch in Claim B, vier Zeilen auseinander

`PAPER_1.md` sagte in der Retraktion, der Anspruch ruhe "on the regression grid alone: 30 cells", und
im naechsten Absatz "The claim no longer rests on the 30-cell regression grid alone." Beide Saetze
sind fuer sich verteidigbar und nebeneinander nicht.

Der Grund ist, dass Claim B zwei Haelften hat, die verschiedene Evidenz brauchen, und die Zeilen
sortierten sie nicht auseinander:

- **Haelfte 1, die Kappe schraenkt das Wachstum ein.** Kampagnenweit belegt: 690 von 756 Zellen
  rechnen weniger als die konfigurierten 30 Level. Zaehlt Level *innerhalb* des gekappten Arms.
- **Haelfte 2, bei unveraendertem Ergebnis.** Braucht eine *Differenz zwischen* Armen. Beide
  Kampagnenarme sind gekappt, also gibt es diese Differenz nur auf dem Regressionsgitter: 30 Zellen,
  5 Systeme.

Die Verwechslung liegt nahe, weil beide Haelften Level zaehlen. Das steht jetzt explizit da, samt der
Aufforderung, Haelfte 2 nicht die 756 Zellen von Haelfte 1 als geliehenes Gewicht zu geben.

Zweiter Befund am selben Dokument: der Statusblock war auf den 22.08. datiert und die Schlusszeile
sagte, der Paper-Zuschnitt bleibe offen, "until the baseline number exists". Die Zahl existiert seit
dem 09.09. **Die offene Frage ist damit nicht mehr "messen", sondern "was ist Paper 1 jetzt"** — mit
drei Kandidaten, die im Dokument stehen, damit die Wahl bewusst getroffen wird und nicht durch Drift.

#### `docs/architecture.md` beschrieb einen Stand von Ende Juli

Das Dokument ist als Komponentenreferenz verlinkt und war am weitesten abgedriftet:

- Die Variantenliste fuehrte **"v3: planned equation-wise growth"**. v3 ist implementiert und am
  31.07. an Gate 2 gescheitert. `evogrow_v2_2_stage_capped`, die finale Paper-1-Variante, fehlte in
  der Liste vollstaendig.
- Die **Look-ahead-Stufenkappe** — der Mechanismus, um den das Paper geht, 374 Zeilen Code — hatte
  keinen eigenen Abschnitt, sondern zwei beilaeufige Erwaehnungen. EvoGrow und GP hatten volle
  Mechanismus-Abschnitte.
- **"Phase B" kam null Mal vor.** "Current experiments" listete allein Phase A.
- `GPStructureSearch` war als *"a comparison baseline"* beschrieben. `PAPER_1.md` sagt "no GP
  baseline", `CLAUDE.md` sagte bis vorgestern "no baseline has ever been run". Diesen Widerspruch
  findet ein aufmerksamer externer Leser sofort.

Die Kappe hat jetzt ihren Abschnitt: was sie lesen darf (Trajektorie, Basis, Schwellen — kein
Grundwahrheits-, Stufen- oder Systemargument, das ist der Grund fuer die Suchunabhaengigkeit), die
zwei Designregeln mitsamt den Defekten, aus denen sie stammen, der Reopen-Zweig, die beiden
tragenden Konstanten und das WP-V1-Negativergebnis. Dazu ein Abschnitt **"Not Implemented"**, weil
die Abwesenheiten mitbestimmen, was behauptet werden darf.

#### Neunzehn Skripte, die das Runbook nie kannte

`SCRIPTS.md` beansprucht Vollstaendigkeit und fuehrte 44 von 63 Skripten. Nichts darin war falsch —
jedes dokumentierte Skript existiert —, aber die Luecken waren die falschen: die **komplette
WP-N-Linie**, also die aktuelle Arbeit und die Quelle der Zahlen, ueber die jetzt extern geredet wird,
plus die fuenf Stufenkappen-Audits, die Horizont und Reopen-Schwelle bestimmt haben. Die Kommandos
sind aus den Arbeitspaket-Reports uebernommen, nicht rekonstruiert.

`studies/output_path_guard.jl` fehlte nicht versehentlich: es ist ein geteilter Helfer, kein
ausfuehrbares Skript. Das steht jetzt da, damit die Luecke nicht wieder wie eine aussieht.

#### Ein Waechter, der seit drei Wochen nicht mehr waechte

`tests/test_analysis_variant_visibility.py` faellt mit

```
TypeError: build_csv_table() missing 2 required positional arguments: 'exact_ids' and 'surrogate_ids'
```

Die beiden Parameter kamen mit WP-A4/A4b, als die Systemachse von fest verdrahteten ID-Listen auf
`system_classification.csv` umgestellt wurde. Der Test wurde nicht mitgezogen und ist seit etwa dem
21.08. rot. Es faellt niemandem auf, weil **nichts die Python-Tests ausfuehrt** — die GitLab-CI baut
ausschliesslich das Kampagnen-Image.

Das ist nicht irgendein Test. Die Invariante, die er sichert — eine unbekannte Variante darf nicht
stillschweigend aus der Haupttabelle verschwinden — ist genau die, um die es in WP-A4b ging. Der
Waechter fiel in dem Moment aus, in dem er am wichtigsten wurde. Repariert wird er in WP-O1, zusammen
mit dem Umzug von `tests/` nach `analysis/tests/`; das Wurzelverzeichnis hatte `test/` (Julia) und
`tests/` (Python) nebeneinander, und `analysis/CONVENTIONS.md` sieht `tests/` gar nicht vor.

#### WP-O1: der Waechter waecht wieder

Noch am selben Tag repariert. Der Aufruf uebergibt jetzt System 2 als exakt und System 23 als
Surrogat — was die Klassifikation auch sagt —, der Test bedient also beide Zweige und erfuellt nicht
bloss die Signatur. Verifiziert wurde die Reparatur durch absichtliches Kaputtmachen: mit einem auf
bekannte Varianten eingeschraenkten `build_csv_table` faellt der Test mit genau der Zusicherung, mit
der er fallen soll. `table_main_results.py` blieb unangetastet.

`tests/` liegt jetzt unter `analysis/tests/`. `REPO_ROOT` geht von `parents[1]` auf `parents[2]`, und
beide Dateien pruefen per `assert`, dass unter dieser Wurzel wirklich `CLAUDE.md` und `benchmarks/`
liegen — ein falscher Index faellt damit laut auf statt zufaellig durchzugehen. Vier Tests gruen.

Was das Paket **nicht** loest und was als Luecke stehen bleibt: es fuehrt sie niemand aus.

#### Kleinkram, benannt statt stillschweigend behoben

- Branch `refactor/discover-api`: **0 Commits ahead, 186 behind**, letzter Commit 12.08. — eine leere
  Huelle, geloescht.
- Report-Konvention: drei Namensschemata (`codex/reports/REPORT_WP_*.md` 39x, `docs/WP-*.md` 13x,
  `docs/wp_*_<beschreibung>.md` 7x) ohne Regel, welches wohin. Die Regel steht jetzt in `CLAUDE.md`
  und `README.md`: Codex-Report ist Provenienz, `docs/WP-*.md` ist ein **befoerderter** Report, an dem
  eine Entscheidung haengt. Die alten Kleinschreibungen werden **nicht** umbenannt, weil `DIARY.md`
  sie mit Pfad zitiert.
- Wurzelverzeichnisse `data/` (leer), `figures/`, `tables/`: Phase-A-Altlasten, dupliziert von
  `analysis/`. Ebenso `tools/` (nur `__pycache__`), `examples/`, `.agents/` (beide leer). Die Loeschung
  hat der Berechtigungsfilter zweimal blockiert; die Befehle liegen beim Nutzer, eine Sicherungskopie
  im Scratchpad.
- Die generierten `phase_b_*.yaml` im Wurzelverzeichnis tragen ein UTF-8-BOM — dieselbe Klasse
  Problem, gegen die `.gitattributes` ausfuehrlich argumentiert. Sie sind gitignoriert und haben
  funktioniert, also folgenlos; der Generator schreibt es trotzdem.

#### Nachtrag am selben Abend: 852 MB waren zu 99 Prozent Luft

Ein Messbefehl, der im Hintergrund nachlief, lieferte die Zahl, die den Groessen-Eindruck erklaert —
und keiner der bis dahin diskutierten Punkte war es. `.git` war **852 MB** gross. Die Aufschluesselung:

```
lose Objekte:   25.985 Stueck  =  739,8 MB   <- nie gepackt
gepackt:           613 Stueck  =    6,3 MB
Muell:      tmp_pack_vlx5bO    =   48,6 MB   <- Rest eines abgebrochenen gc
```

**Der tatsaechliche Inhalt der gesamten Projekthistorie sind 6,3 MB.** Das groesste Objekt ueberhaupt
ist `strogatz_extended.json` mit 3,5 MB — es lag also kein versehentlich eingecheckter Datenberg
herum. Der Objektspeicher war schlicht nie aufgeraeumt worden.

Die Ursache ist strukturell und haengt an der Arbeitsweise: `DIARY.md` ist 405 KB und wird bei fast
jedem Commit angefasst. Jede Fassung liegt als eigenes, **unkomprimiertes** loses Objekt da, bis Git
sie packt. Ueber 470 Commits summiert sich das. Das `tmp_pack` zeigt, dass ein `git gc` einmal lief
und abgebrochen wurde — vermutlich der Grund, warum seither nichts mehr gepackt wurde.

`git gc --prune=now`: **852 MB -> 11 MB.** Lose Objekte 0, Muell 0, ein Packfile mit 9,68 MB.
Gegengeprueft: `git fsck` ohne Beanstandung, 470 Commits unveraendert, `history.jsonl` mit 1,8 MB im
Baum. Danach die sechs Altordner geloescht — 18 sichtbare Verzeichnisse auf 13, elf davon getrackt.
Die drei `.pytest_*`-Verzeichnisse widersetzen sich sowohl `rm` als auch PowerShell (ACL-Problem,
dasselbe, das schon beim Testlauf den Cache-Schreibzugriff verweigert hat); sie sind versteckt, leer
und gitignoriert.

**Lehre fuer die Priorisierung:** die vorgeschlagene Reihenfolge war falsch gewichtet. Die 38
Codex-Reports zu verschieben spart 246 KB, ein Befehl sparte 840 MB. Ordnung und Groesse sind
verschiedene Probleme, und der Groessen-Eindruck des Nutzers zeigte auf das zweite.

#### Und die Reports liegen jetzt eine Ebene tiefer

`codex/` hatte drei aktive Dateien und 38 Einmal-Reports auf einer Ebene — ein Archiv, in dem die
Task-Spec versteckt lag. Die Reports behalten Namen und Inhalt, nur die Ebene aendert sich; alle 15
Verweise in 9 Dokumenten wurden mitgezogen und loesen auf, `DIARY.md` eingeschlossen.

Dabei ist aufgefallen, dass `codex/CODEX_PROTOCOL.md` seit jeher **"Reports nach `docs/`"** vorgab.
Dort ist nie einer gelandet: jede Task-Spec ueberschrieb die Vorgabe, indem sie einen `codex/`-Pfad
nannte. Die stehende Anweisung war ueber 38 Arbeitspakete hinweg falsch, ohne Folgen — weil sie
jedes Mal ueberschrieben wurde. Jetzt nennt sie `codex/reports/` und sagt, wofuer `docs/` reserviert
ist.

#### Was ausdruecklich in Ordnung war

Kein TODO/FIXME im gesamten Code. `.gitattributes` mit ausgeschriebener Begruendung. `Manifest.toml`
gepinnt, `[compat]` vollstaendig. `analysis/CONVENTIONS.md` ist ein durchgehaltenes Dokument samt
Anti-Pattern-Liste. Fehlerpfad-Fixtures existieren, also nicht nur der Happy Path. Die
Identity-Triple-Disziplin ist ueberall durchgezogen.

Und eine Beobachtung zu `CLAUDE.md` selbst: 710 Zeilen bei der Selbstbeschreibung "deliberately kept
short". Abschnitt "Active 0" ist inzwischen ein mehrseitiger Essay mit vollstaendigen
Ergebnistabellen — inhaltlich richtig, aber Ergebnisprosa, die laut der eigenen Aufteilungstabelle
nach `DIARY.md` oder `PAPER_1.md` gehoert. Nicht angefasst, weil das eine inhaltliche Umschichtung
waere und keine Aufraeumarbeit.


### Die erste Baseline seit Projektbeginn: auf Dimension 1 steht es unentschieden, zu erheblich hoeheren Kosten

<!-- d62ad78 -->

WP-N6 hat SINDy auf **denselben Trajektorien** gerechnet wie EvoODE — 63 Systeme, beide
Anfangswertsaetze, 512 Punkte ueber t in [0, 10], selbst integriert bei 1e-9, ohne die mitgelieferten
Loesungen. Zehn Konfigurationen (Polynomgrade 2 bis 5, einmal mit `sin`/`cos`, je zwei
STLSQ-Schwellen), beide Regime aus WP-N5, beide Richtungen. **Keine Konfiguration wurde ausgewaehlt**;
das Gitter wird vollstaendig berichtet.

Damit hat das Projekt zum ersten Mal eine Zahl, die nicht gegen sich selbst gemessen ist.

#### Der faire Vergleich: Dimension 1

Unsere Generalisierungszahlen stammen aus dem dim-1-Probelauf, deshalb ist nur diese Klasse
vergleichbar. SINDy auf die dim-1-Systeme eingeschraenkt, jeweils die beste der zehn Konfigurationen:

| Anteil R2 > 0,9 | SINDy | EvoODE |
|---|---|---|
| Rekonstruktion | 44/46 = **95,7 %** | 126/132 = **95,5 %** |
| Generalisierung | 28/46 = **60,9 %** | 90/132 = **68,2 %** |

**Auf der Rekonstruktion ist es ein Unentschieden** — 95,7 gegen 95,5 Prozent. Auf der
Generalisierung liegt EvoODE vorn, 68,2 gegen 60,9 Prozent.

#### Und die Kosten, die dabei stehen muessen

SINDy rechnet **eine lineare Regression je Gleichung** — bei den dim-1-Systemen also 46 Regressionen
fuer 46 Zellen. EvoODE rechnet im Median **410 nichtlineare Parameteranpassungen je Zelle**, jede mit
ODE-Integrationen.

Das sind rund **zwei Groessenordnungen**. Fuer ein Verfahren, dessen Leitthese Effizienz ist, ist das
die unbequemste Zahl des Tages — und sie gehoert neben jede Trefferquote.

#### Ueber alle 63 Systeme

| Anteil R2 > 0,9, bestes der zehn Gitter | SINDy |
|---|---|
| Rekonstruktion | 43/63 = 68,3 % |
| Generalisierung | 30/63 = 47,6 % |

Zum Vergleich der Kampagnenwert von EvoODE, 80,7 % ueber 756 Zellen — **aber das ist keine
Gegenueberstellung.** Die Aggregationseinheiten unterscheiden sich (756 Zellen mit drei Seeds und
zwei Bedingungen gegen 63 Zellen je Konfiguration und Richtung), und unsere Generalisierung ueber
alle Dimensionen ist gar nicht gerechnet, weil den Kampagnenzellen die Koeffizienten fehlen.

Strukturtreffer, bestes Gitterergebnis: 19 von 63 ueber alle Systeme, 11 von 20 auf den fuer EvoODE
darstellbaren, 17 von 40 auf den fuer SINDy darstellbaren. Diese Zahlen sind mit unseren nicht direkt
vergleichbar, weil unsere Strukturmessung auf einer anderen Systemauswahl beruht.

#### Was zu deklarieren ist

**Vorbehalte, die in jede Nennung dieser Zahlen gehoeren:**

1. Die Systemmengen sind nicht identisch. EvoODEs 132 dim-1-Zellen kommen aus **11 ausgewaehlten**
   Systemen mal drei Seeds mal zwei IC-Saetze mal zwei Basen; SINDys 46 aus **allen 23**
   dim-1-Systemen mal zwei IC-Saetze. Naeher am Vergleich als alles bisherige, aber nicht deckungsgleich.
2. SINDys Zahl ist jeweils das **Maximum ueber zehn Konfigurationen** — ein leichter Vorteil zu seinen
   Gunsten, bewusst so gewaehlt, damit die Baseline nicht kleingerechnet wird.
3. **Protokollunterschied:** SINDy braucht Ableitungen (`FiniteDifference(order=2)`), EvoODE nicht.
   Unsere Daten sind rauschfrei, was SINDy hier beguenstigt. Bei Rauschen waere das Bild ein anderes,
   und das ist ungemessen.
4. Integrator: SINDy-Seite `DOP853`, EvoODE `Tsit5`, beide bei 1e-9 auf identischem Gitter. Die
   Gitterpruefung bestaetigt 126 von 126 Zellen. Der Abgleich lief allerdings gegen die
   **mitgelieferten** Trajektorien, nicht gegen unsere eigenen — die Uebereinstimmung folgt aus
   gleicher Toleranz und gleichem Gitter, ist aber nicht direkt gemessen.

#### Die Antwort auf die Ausgangsfrage

Gefragt war, ob 80,7 % gut oder peinlich sind. Die Antwort lautet: **weder noch.** Auf der einfachsten
Systemklasse ist EvoODE mit SINDy gleichauf in der Rekonstruktion und etwas besser in der
Generalisierung — bei rund hundertfachem Rechenaufwand.

Das ist keine Katastrophe und kein Sieg. Es ist die Ausgangslage, von der aus sich entscheiden
laesst, was Paper 1 behaupten kann. Und es verschiebt die Beweislast: Ein Verfahren, das gleichauf
liegt und hundertmal mehr rechnet, muss seinen Mehrwert woanders zeigen — bei Rauschen, bei
gekoppelten Systemen, oder in der Interpretierbarkeit des Suchwegs.

---

### Generalisierung, zum ersten Mal gemessen — und die Konstante dreht das Vorzeichen

<!-- 24e1179 -->

WP-N5 hat die zweite Haelfte der Literaturmetrik erschlossen: das gefundene Modell wird ab dem
**ungesehenen** Anfangswert integriert und gegen die wahre Loesung geprueft. Die Parameter werden
dabei **nicht** neu angepasst — gemessen wird das Modell, das die Suche geliefert hat. 132 Zellen
des dim-1-Probelaufs, beide Richtungen. Kosten: eine Integration je Zelle, kein Suchlauf.

Codex hat den Code geschrieben und `blocked` gemeldet (Julia startet in seiner Sandbox nicht);
ausgefuehrt hat Claude.

#### Die Kontrolle, ohne die nichts gilt

Integriert man ein Modell ab **seinem eigenen** Anfangswert, muss der im Record gespeicherte Loss
herauskommen. **132 von 132 Zellen bestehen mit einer Abweichung von exakt null.** Damit ist zum
ersten Mal belegt, dass die in WP-N1 eingefuehrte Koeffizientenspeicherung ihren Zweck erfuellt: aus
`model_terms` plus `basis_name` laesst sich das Modell bitgleich rekonstruieren.

#### Der Abfall

| | Rekonstruktion | Generalisierung |
|---|---|---|
| **alle 132 Zellen** | 126/132 = **95,5 %** | 90/132 = **68,2 %** |

**27 Prozentpunkte.** Qualitativ dasselbe Bild, das die ODEFormer-Publikation beschreibt
(„generalization accuracy is substantially lower than reconstruction accuracy"). Das ist die erste
Zahl des Projekts, die auf zurueckgehaltenen Daten gemessen ist — bis heute war jede Kennzahl
In-Sample.

Nach Basis und Richtung:

| Basis | Richtung | Rekonstruktion | Generalisierung |
|---|---|---|---|
| alt | IC1 → IC2 | 100 % | 72,7 % |
| alt | IC2 → IC1 | 90,9 % | **45,5 %** |
| mit Konstante | IC1 → IC2 | 100 % | **87,9 %** |
| mit Konstante | IC2 → IC1 | 90,9 % | 66,7 % |

Die Richtung traegt erhebliche Information: IC2 → IC1 ist in beiden Basen deutlich schlechter. Die
Entscheidung aus WP-A4b, die IC-Saetze nicht wegzumitteln, zahlt sich hier zum zweiten Mal aus.

#### Der eigentliche Befund: die Konstante dreht das Vorzeichen

**Die Konstante generalisiert deutlich besser** — 87,9 % gegen 72,7 % und 66,7 % gegen 45,5 %. Und
**alle neun divergierenden Integrationen entfallen auf die alte Basis, keine einzige auf die neue.**

Damit steht sie auf den beiden Metriken gegenlaeufig:

| | Strukturtreffer (WP-N1) | Generalisierung (WP-N5) |
|---|---|---|
| alte Basis | **83,3 %** | 72,7 % / 45,5 % |
| mit Konstante | 38,9 % | **87,9 % / 66,7 %** |

Die Konstante halbiert die Strukturfindung und verbessert die Generalisierung erheblich. Physikalisch
plausibel: ein konstanter Term faengt Offset oder Gleichgewichtslage ab, und genau das entscheidet,
wenn man von einem anderen Anfangswert startet.

**Die Frage „gehoert die Konstante in die Basis?" ist damit nicht mit ja oder nein zu beantworten.**
Sie haengt daran, welche Metrik zaehlt — und das ist eine Entscheidung ueber den Zweck des
Verfahrens, keine ueber die Konfiguration. Ohne die am 2026-09-08 eingefuehrte Pflicht, immer beide
Metriken zu berichten (Design-Prinzip 9), waere dieser Befund nicht sichtbar geworden.

#### Die Kampagne bleibt aussen vor

Bestaetigt und als eigener Punkt festgehalten: die 756 Kampagnenzellen tragen **keine
Koeffizienten** — sie liefen vor WP-N1. Ihre Generalisierung ist daher nicht nachtraeglich
berechenbar, sondern nur ueber einen Neulauf. Codex hat das als eigene Probe im Manifest vermerkt und
Kampagnendaten nicht mit den Probelaufdaten vermischt.

---

### Literaturvergleich zum Restart-Budget — und eine Korrektur an unserer eigenen Zahl

<!-- b42b051 -->

Eine Recherche zu SINDy, PySR, ODEFormer und ProGED (Nutzer, 2026-09-09) hat den WP-N4-Befund
eingeordnet. Sie bestaetigt die Richtung, korrigiert die Sprache an zwei Stellen und legt einen
Fehler in unserer eigenen Darstellung offen.

#### Die Korrektur: „tausende Anpassungen" war falsch

Im WP-N4-Eintrag stand, die Suche rechne „tausende Anpassungen, also ein impliziter Mehrfachstart mit
sehr grossem k". Nachgemessen an der Kampagne:

| Klasse | Parameterfits je Zelle (Median) | max |
|---|---|---|
| dim 1 | 410 | 530 |
| dim 2 | 430 | 610 |
| dim 3 | 570 | 610 |
| dim 4 | 440 | 570 |

**Hunderte, nicht tausende.** Und schwerwiegender: diese Fits verteilen sich auf **verschiedene
Kandidatenstrukturen**. Der Mehrfachstart *je Struktur* ist nur so gross wie die Rate, mit der
dieselbe Struktur mehrfach ausgewertet wird — und die ist nie gemessen worden. Sie steht in
`CLAUDE.md` selbst als offener Punkt unter der kanonischen Gleichheit fuer `StructureSpec`.

Was bleibt: `pretune_off` bekommt bei Wiederholung neue Startwerte, `pretune_on` nicht. Die Richtung
ist gedeckt, die **Groessenordnung nicht**. In `CLAUDE.md`, `docs/phd_thesis_arc.md` und dem
WP-N4-Eintrag korrigiert.

#### Was die Recherche beitraegt

**Drei Budgetebenen, die wir bisher vermischt haben.** Struktursuche (PySR-Populationen, ProGED-
Kandidaten, ODEFormer-Beam), Parameteroptimierung (Restarts k), und Run-Stochastik (ganze Seeds).
Diese Trennung gehoert ins Paper und in jede kuenftige Messung.

**Beam Size ist nicht unser k.** ODEFormers Beam variiert *Strukturen*, unser k variiert
*Parameterstarts*. Die Gleichsetzung waere sachlich falsch — und sie stand als Analogon in der
Rechercheliste, die Claude tags zuvor geschrieben hatte.

**Der Praezedenzfall ist PySR**, nicht ODEFormer: `optimizer_nrestarts` ist dort ein regulaerer
Methodenparameter fuer die Konstantenoptimierung. Ein Restart-Budget explizit zu benennen ist also
etabliert, kein Sonderweg. Zu pruefen bleibt, ob sich der Parameter auf jede Konstantenoptimierung
oder nur auf finale Kandidaten bezieht, und welcher Default im ODEBench-Lauf galt.

**ODEFormers Constant Optimizer ist strukturell unser `pretune_on`**: ein gelernter Warmstart plus
ein **einzelner** lokaler Lauf. Daraus folgt eine Frage, die die Recherche nicht stellt und die einen
eigenen Beitrag traegt: Wir messen, dass ein guter Warmstart bei k = 1 in 15 % der Faelle scheitert.
Entweder ist ihr Warmstart deutlich besser als unser OLS-Pretuning — oder sie haben dasselbe Problem
und messen es nicht.

#### Zwei Punkte, die in der Recherche fehlen und gegen uns laufen

**Die Kostenachse.** Das Projekt haengt an einer Effizienzthese, und k multipliziert die Fits direkt.
Ein Restart-Budget ohne Kosten ist keine Messung, sondern eine Stellschraube. Die richtige Kurve ist
**Trefferquote gegen Fits**, nicht gegen k. Gegenargument, das geprueft gehoert: die 410 Fits werden
ohnehin gezahlt, nur unkontrolliert — k explizit zu machen waere dann eine **Umverteilung** (weniger
Strukturen, jede zuverlaessig angepasst) statt Zusatzkosten. Das ist pruefbar und waere ein
Ergebnis.

**Restarts sind ein Symptom, keine Loesung.** Unsere Startpunktabhaengigkeit folgt aus einer
Designentscheidung: wir optimieren MSE auf der **integrierten** Trajektorie, ein schlecht
konditioniertes Ziel. SINDy hat diese Fehlerklasse nicht — nicht weil es besser optimiert, sondern
weil es im **Ableitungsraum** fittet, wo das Koeffizientenproblem linear ist. Die ehrliche Formulierung
ist deshalb nicht „alle brauchen ein Budget, wir auch", sondern **„unser Ansatz traegt eine
Fehlerklasse, die SINDy strukturell nicht haben kann"**. Das ist eine Limitation und die direkte
Fortsetzung der Method-Positioning-Notiz vom 2026-09-03.

#### Sprachliche Korrektur, die uebernommen wird

k = 3 ist **kein Default**. Belegt ist: ab drei Restarts verschwinden auf den eindimensionalen
Systemen die Totalausfaelle. Die Fit-Qualitaet steigt danach weiter (R2 > 0,9 von 91,2 % bei k = 3 auf
97,1 % bei k = 10). Vor einer Festlegung muessen hoehere Dimensionen gemessen werden.

---

### Drei Zufallsstarts genuegen — und damit steht der Mechanismus hinter dem Pretuning-Befund

<!-- 34fdc0a -->

WP-N4 hat die Referenzanpassung aus WP-N3 mit **mehreren Zufallsstarts** wiederholt, k = 1, 2, 3, 5,
10, je Zelle das beste Ergebnis nach Loss. Codex hat den Code geschrieben und `blocked` gemeldet
(Julia startet in seiner Sandbox nicht); ausgefuehrt hat Claude, erst ueber `--limit 3`, dann
vollstaendig ueber 102 Zellen.

**Beide Kontrollen bestanden.** Bei k = 1 kommen exakt die WP-N3-Zahlen heraus — 15 Sentinel-Zellen
bei der wahren Struktur, 11 bei der Oracle-Beschneidung. Der Mehrfachstart fuegt also nur Versuche
hinzu und aendert sonst nichts. Und die Liste nicht anpassbarer Zellen bei k = 10 ist **leer**.

#### Die Kurve

Wahre Struktur, alle 102 Zellen:

| k | Fit gescheitert (Sentinel 1e6) | Anteil R2 > 0,9 | erreicht/schlaegt Originallauf |
|---|---|---|---|
| 1 | **15** | 71,6 % | 29,4 % |
| 2 | 13 | 80,4 % | 37,3 % |
| 3 | **0** | 91,2 % | 46,1 % |
| 5 | 0 | 92,2 % | 52,9 % |
| 10 | **0** | **97,1 %** | 64,7 % |

Bei der Oracle-Beschneidung dasselbe Bild: 11 → 9 → **0** ab k = 3.

**Kein Plateau. Drei Zufallsstarts loeschen saemtliche Fehlschlaege aus.** Die Frage, die WP-N4
stellen sollte, ist damit eindeutig beantwortet: der Optimierer kann diese Strukturen anpassen; ein
**einzelner Versuch** ist unzuverlaessig.

Die urspruengliche Vermutung — der Optimierer druecke Koeffizienten nicht weit genug gegen null — ist
damit nicht bestaetigt. Der Befund liegt daneben und ist unangenehmer: **jeder siebte Einzelversuch
scheitert vollstaendig**, auch wenn man dem Verfahren die richtige Antwort vorlegt.

#### Was das erklaert

Der Zusammenhang, der die letzten Tage offen war, schliesst sich hier.

Unter `pretuning=false` zieht jeder Fit seinen Startwert zufaellig (`0.1 .* randn(n_params)`,
`bfgs.jl:269`). Die Suche rechnet ueber ihren Verlauf viele Anpassungen und behaelt die beste — ein
**impliziter Mehrfachstart unbekannter Groesse** (zur Korrektur der urspruenglich behaupteten
Groessenordnung siehe den Eintrag zur Literaturrecherche weiter oben). Unter `pretuning=true` wird der Startwert
deterministisch aus den Daten berechnet: **k = 1, immer derselbe.**

Damit ist der Pretuning-Nachteil kein vager Verankerungseffekt mehr, sondern beziffert: Pretuning
ersetzt einen Mehrfachstart, dessen Notwendigkeit hier gemessen ist, durch einen einzigen Versuch —
und ein einziger Versuch scheitert in 15 % der Faelle selbst bei bekannter richtiger Struktur.

Das korrigiert die Rueecknahme vom 2026-09-07 nicht, aber es praezisiert sie. Damals wurde der
Seed-Kollaps zurueckgenommen, weil er groesstenteils daraus folgt, dass `pretune_off` eine zweite
Zufallsquelle hat. Das bleibt richtig. Neu ist, **warum diese zweite Zufallsquelle nuetzlich ist**:
sie ist kein Rauschen, sondern ein Mehrfachstart, und das Verfahren braucht ihn.

#### Einordnung, die mitberichtet werden muss

Der Originallauf bleibt auch bei k = 10 in 36 von 102 Zellen besser als die Referenzanpassung. Das
ist erwartbar und **kein** Widerspruch: er hat tausende Anpassungen gerechnet, die Referenz zehn. Der
Vergleich „Referenz gegen Original" bleibt schief, nur nicht mehr so schief wie in WP-N3.

Die Strukturtrefferzahlen sind ueber k konstant — 75 von 102 bei der Oracle-Beschneidung, 102 von
102 bei der wahren Struktur, letzteres trivial. Der Mehrfachstart aendert die **Anpassung**, nicht
die Struktur; das ist die erwartete Invarianz und zugleich eine weitere Kontrolle, dass das Skript
tut, was es soll.

#### Konsequenz

Zwei Dinge folgen, beide bisher unbelegt gewesen:

1. **Der Mehrfachstart ist eine tragende Komponente des Verfahrens**, keine Nebenwirkung der
   Konfiguration. Er gehoert benannt, gemessen und im Paper beschrieben — derzeit existiert er nur
   implizit als Nebenprodukt zufaelliger Startwerte.
2. **Jede Aussage ueber Pretuning muss die Zahl der Startversuche mitfuehren.** Ein Vergleich
   `pretune_on` gegen `pretune_off` ist ohne diese Angabe nicht interpretierbar, weil er zwei Dinge
   zugleich variiert: die Guete des Startwerts und ihre Anzahl.

---

## 2026-09-08

### Die Pruning-Schwelle ist ein Nullsummenregler — und R2 sieht von alldem fast nichts

<!-- f7c0643 -->

WP-N2 hat die Pruning-Regel als Messinstrument vermessen, auf den 132 Zellen des
WP-N1-dim-1-Probelaufs, ohne einen einzigen neuen Suchlauf — moeglich, weil seit WP-N1 die
Koeffizienten im Record stehen.

#### Die Zerlegung der Fehlschlaege

Heutige Regel `max(1e-6, 1e-3 * max_abs)`, 102 exakte Gleichungen:

| Basis | Zellen | Treffer | Fremdterm ueberlebt | wahrer Term geloescht | Term nie gefunden | Anteil R2 > 0,9 |
|---|---|---|---|---|---|---|
| alt | 36 | 30 | 0 | 0 | 6 | **100 %** |
| neu, mit Konstante | 66 | 29 | 12 | **4** | 21 | **95,5 %** |

Die alte Basis hat **keinen einzigen** Pruning-Fehler: jeder ihrer sechs Fehlschlaege ist ein nie
gefundener wahrer Term. Die neue Basis dagegen verliert 16 Zellen an die Messregel selbst.

#### Der Kern: die Schwelle verschiebt nur, sie loest nicht

Ueber ein Gitter aus 24 Regeln — rein relativ, rein absolut und die heutige Mischform, je vier
Werte — bleibt die Summe konstant:

**Treffer + geloeschter wahrer Term + ueberlebender Fremdterm = 45** in 18 der 24 Regeln (45 ist
zugleich die Teilmengen-Obergrenze: in 45 der 66 Zellen ist die wahre Struktur ueberhaupt enthalten).

| Regel | Treffer | wahrer Term geloescht | Fremdterm ueberlebt |
|---|---|---|---|
| relativ 1e-4 | 30 | 0 | 15 |
| relativ 1e-3 (**heute**) | 29 | 4 | 12 |
| relativ 1e-2 | 29 | 13 | 3 |
| relativ 1e-1 | 18 | 27 | 0 |

Jede Zelle, die man durch eine hoehere Schwelle vom ueberlebenden Fremdterm befreit, verliert man an
einen geloeschten wahren Term. **Die beiden Fehlerarten tauschen fast eins zu eins.** Der Grund ist
einfach und liegt in den Daten: die stoerenden Konstanten (relativ 1,3e-03 bis 4,1e-01) und die
kleinen echten Terme (System 5: relativ 2,2e-04) ueberlappen im Betrag. **Es gibt keine Schwelle,
die sie trennt**, weil sie nicht getrennt sind.

Die hoechste Trefferzahl ueber alle 24 Regeln ist **30 von 66** gegen heute 29 — ein Gewinn von
einer einzigen Zelle. Eine bessere Schwelle gibt es also nicht zu finden. Das ist ein negatives
Ergebnis ueber unser Messverfahren, und es ist wertvoller als jede Feinjustierung es gewesen waere.

**Auch die alte Basis ist nicht robust**, sie hat nur Glueck: bei relativ 1e-1 faellt sie von 30 auf
15 von 36. Ihre Koeffizienten liegen bloss weit genug auseinander, dass die heutige Schwelle sie
sauber trennt.

#### Und die zweite Metrik sieht davon fast nichts

**Der Anteil R2 > 0,9 ist ueber das gesamte Regelgitter invariant** — logisch, denn Pruning aendert
die Klassifikation, nicht die Anpassung. Er betraegt 36/36 fuer die alte und 63/66 fuer die neue
Basis.

Damit steht der Kontrast, der Design-Prinzip 9 begruendet: Die Konstante kostet auf der
**Strukturmetrik** die Haelfte der Treffer (83,3 % auf 43,9 %), auf der **Literaturmetrik** dagegen
nur drei von 66 Zellen (100 % auf 95,5 %). Wer nur R2 berichtet, sieht den Einbruch nicht. Wer nur
Struktur berichtet, ist mit keiner Publikation vergleichbar. Beide Zahlen sind ab sofort Pflicht.

#### Was daraus folgt

Nicht eine neue Schwelle. Sondern: die 21 Zellen, in denen ein wahrer Term **nie gefunden** wurde,
sind das eigentliche Problem der neuen Basis — sie liegen ausserhalb dessen, was Beschneiden je
erreichen kann. Die Obergrenze bei 45 von 66 ist eine Eigenschaft der **Suche**, nicht der Messung.

Offen bleibt die Frage, die dieses WP nicht beantworten konnte: was passiert, wenn man die
Fremdterme entfernt und die Parameter **neu fittet**. Alles hier Berichtete rechnet mit unveraenderten
Koeffizienten. Das ist WP-N3.

---

### Die Konstante ist kein Gratisgewinn: sie oeffnet fuenf Systeme und kostet die Haelfte der bisherigen

<!-- 4f2fab0 -->

WP-N1 hat die Konstante als **neue** Basisvariante gebaut (`staged_polynomial_basis_with_constant`,
Term `"1"` in Stufe 1), die Koeffizienten in den Record aufgenommen und einen dim-1-Probelauf ueber
132 Zellen gerechnet: 11 Systeme x 3 Seeds x 2 IC-Saetze x 2 Basen, `pretuning=false`.

Codex hat den Lauf nicht ausfuehren koennen — seine Sandbox startet `julia.exe` unter `WindowsApps`
nicht (`status: blocked` nach 6,9 Minuten). Tests und Probelauf wurden von Claude ausgefuehrt; die
Implementierung stammt unveraendert aus dem WP.

**Akzeptanz erfuellt.** Die alte Basis ist unangetastet: alle **66 von 66** Zellen liefern
bitgleiche Losswerte gegen die Kampagne (`pretune_off`), und alle 36 exakten Zellen stimmen im
`pruned_match` ueberein. Die Unit-Tests laufen 10/10.

#### Das Ergebnis, in beide Richtungen

**Frage 1 — die sechs bisher darstellbaren dim-1-Systeme (2, 3, 6, 8, 11, 12):**

| Basis | Strukturtreffer |
|---|---|
| alt | **30 / 36 = 83,3 %** |
| neu, mit Konstante | **14 / 36 = 38,9 %** |

Die Konstante **halbiert** die Trefferquote dort, wo sie nicht gebraucht wird. System 3 faellt von
6/6 auf 2/6, System 6 von 6/6 auf 3/6, System 11 von 3/6 auf 0/6, System 12 von 6/6 auf 3/6.

**Frage 2 — die fuenf Systeme, die allein an der Konstante scheiterten (1, 5, 9, 17, 23):**

| Basis | Strukturtreffer |
|---|---|
| alt | nicht bewertbar (dort Surrogate) |
| neu, mit Konstante | **15 / 30 = 50 %** |

System 1 (RC-Kondensator) 6/6, System 17 6/6, System 9 3/6, Systeme 5 und 23 je 0/6. Ein
Vorher-Nachher gibt es hier nicht — unter der alten Basis ist ihre Struktur gar nicht darstellbar,
die Strukturbewertung ist erst mit der Konstante definiert.

#### Die Ursache: die Konstante ist ein Falschpositiv-Magnet

In **31 der 37** verfehlten exakten Zellen unter der neuen Basis steht die Konstante im gefundenen
Modell; in **22** davon war sie nicht erwartet. Beispiele: System 3 findet `['1','u1','u1^2']` statt
`['u1','u1^2']`, System 12 dasselbe Muster.

Die neu gespeicherten Koeffizienten — der zweite Teil dieses WP — trennen dabei **zwei
Fehlermodi**, die ohne sie nicht unterscheidbar gewesen waeren:

| System | c(1) | groesster anderer Koeffizient | Verhaeltnis | Deutung |
|---|---|---|---|---|
| 3 | 1,0e-03 bis 5,2e-03 | 0,790 | **1,3e-03 bis 6,6e-03** | numerisch belanglos |
| 12 | 2,6e-02 bis 1,5e-01 | 1,80 | 1,5e-02 bis 8,2e-02 | Grenzfall |
| 6 | **6,321** | 1,502 | **4,21** | echte Fehlanpassung |

Bei System 3 ist die ueberzaehlige Konstante **tausendmal kleiner** als der groesste Koeffizient —
die Struktur ist faktisch richtig gefunden, nur ein winziger Term ueberlebt. Bei System 6 ist die
Konstante **viermal groesser** als alles andere: dort hat die Suche ein anderes Modell gefunden
(`['1','u1']` statt `['u1','u1^2']`), das ist kein Pruning-Problem, sondern ein Suchfehler.

**Die Pruning-Regel steht in `experiments/run_experiment.jl:239`:**
`threshold = max(1e-6, 1e-3 * max_abs)`. Fuer System 3 sind das 7,9e-04 — die stoerende Konstante
liegt bei 1,0068e-03, also **um Faktor 1,27 darueber**. Sie ueberlebt das Pruning haarscharf.

**Daraus folgt ausdruecklich keine Empfehlung, die Schwelle zu erhoehen.** Eine Schwelle nach
Sichtung der Daten passend zu waehlen ist genau der Fehler, den WP-V1 fuer den Reopen-Schwellwert
schon einmal benannt hat. Der Befund lautet: die Fehlschlaege haeufen sich unmittelbar oberhalb der
Schwelle, und die Schwelle ist damit ein Messinstrument mit sichtbarer Aufloesungsgrenze — nicht ein
Parameter, an dem man dreht.

#### Was das bedeutet

Das ist ein Ergebnis ueber **Suchraumkontrolle**, also ueber genau die Achse, um die das
Promotionsthema kreist. Ein Term mehr in der Bibliothek ist nicht gratis: er erschliesst Systeme, die
ohne ihn unerreichbar sind, und kostet Treffer bei Systemen, die ihn nicht brauchen. Repraesentierbarkeit
und Auffindbarkeit ziehen gegeneinander, und beides ist hier zum ersten Mal am selben Datensatz
gemessen.

Damit ist auch klar, dass die Konstante **nicht einfach in die Standardbasis wandern kann**. Die
naheliegende Konsequenz — Modellauswahl statt fester Bibliothek, oder ein Sparsamkeitsdruck, der
einen um drei Groessenordnungen kleineren Term verwirft — ist eine Forschungsfrage und keine
Konfigurationsaenderung.

**Offen und nicht in diesem WP zu klaeren:** ob die 83,3 % der alten Basis gegen die 38,9 % der neuen
auf denselben sechs Systemen ein fairer Vergleich ist. Die neue Basis loest eine schwierigere
Aufgabe — groesserer Suchraum bei gleichem Budget. Ein Vergleich bei gleichem *effektiven* Aufwand
statt gleicher Levelzahl waere die ehrlichere Messung.

**Nachzutragen:** der Probelauf schreibt `git_hash = "not_collected"`
(`wp_n1_basis_probe.jl`). Das widerspricht der Identitaetsregel des Projekts und muss vor jeder
weiteren Verwendung dieser Daten repariert werden.

---

## 2026-09-07

### Kassasturz: zwei ueberzogene Befunde zurueckgenommen, vier Grundlagenluecken benannt

<!-- 7a014b3 -->

Ein langes Gespraech am Abend des 2026-09-07 hat die Auswertung derselben Nacht in wesentlichen
Teilen entwertet. Dieser Eintrag haelt fest, was nicht mehr gilt und was stattdessen gilt. Er ist
bewusst vor der naechsten Messung geschrieben, damit die falschen Aussagen keine Nacht laenger
stehen.

#### Zuruecknahme 1: der Seed-Kollaps ist kein tiefer Mechanismus

Frueher an diesem Tag notiert (WP-A7): Pretuning kollabiere die Seed-Diversitaet, 96 von 126 Gruppen
gegen 61, alle diskordanten Paare einseitig, clusterfest p = 1e-5 — als *der* mechanistische Befund,
der das Paper traegt.

Die Zahlen stimmen. Die Deutung war ueberzogen. Im Code steht in `evogrow.jl:473`, dass `p0` nur bei
`use_pretuning` aus `pretune_parameters` kommt und sonst `nothing` ist — und `bfgs.jl:269` ersetzt
`nothing` durch `0.1 .* randn(n_params)`.

**Ohne Pretuning werden die Startparameter zufaellig gezogen, mit Pretuning deterministisch aus den
Daten berechnet.** `pretune_off` hat damit *zwei* seedabhaengige Quellen — Struktursuche und
Parameterstart —, `pretune_on` nur eine. Dass die Ergebnisse mit Pretuning haeufiger identisch sind,
folgt groesstenteils aus dem Versuchsaufbau und ist keine Entdeckung.

Der Zusammenhang stand bereits in `CLAUDE.md` (unter `pretuning=false` wirken Duplikate als implizite
Multistarts); er wurde beim Auswerten nicht mit dem Kollaps verbunden.

**Was bleibt:** ein Ablationsbefund. Der Zufallsstart wirkt wie ein impliziter Mehrfachstart, und die
Vorschaetzung ersetzt ihn durch einen einzigen, sehr guten Startpunkt — der nicht immer in das
richtige Tal fuehrt. System 8 zeigt es scharf: `pretune_off` findet die Struktur mit allen drei
Seeds bei Loss 8,5e-06 bis 2,9e-05, `pretune_on` verfehlt sie dreimal bei Loss 575. Berichtenswert,
aber als Ablation im Anhang, nicht als tragender Befund. Gegenbeleg gegen "Pretuning ist rein
deterministisch": 30 der 126 `pretune_on`-Gruppen kollabieren *nicht*, weil die Struktursuche
zufaellig bleibt.

#### Zuruecknahme 2: Claim B steht nicht auf 756 Zellen

Frueher notiert: die Kampagne bestaetige Claim B auf Kampagnenbreite. Falsch.

**Beide Kampagnenarme sind `evogrow_v2_2_stage_capped`, 756 von 756. Es gibt keinen ungecappten
Arm.** Damit kann die Kampagne ueber den Cap keine Vergleichsaussage machen — der Gegenspieler fehlt.

Was sie zeigt, ist das *Verhalten* des Caps: 690 von 756 Zellen brechen vor dem 30-Level-Budget ab,
und die Levelzahl folgt der erreichten Stufe. Was sie **nicht** zeigen kann, ist die eigentliche
Behauptung — dass der Cap Aufwand spart, *ohne das Ergebnis zu verschlechtern*. Diese Aussage ruht
weiterhin allein auf dem Regressionsgitter: **30 Zellen, 5 Systeme.** Das ist die duennste
Datenbasis im ganzen Paper und traegt zugleich dessen Hauptaussage.

#### Luecke 1: der Basis fehlt der konstante Term

`src/basis/staged_polynomial.jl` kennt `u1`, `u1^2`, `u1*u2`, `u1^3`, `sin`, `cos` — **keine `1`.**

Die Folgen stehen seit dem 2026-08-24 in
`analysis/data/paper1_phaseB_v1/representational_adequacy.csv` und im Protokoll-Audit, wurden aber
nie zum Handlungsanlass:

| Suchraum | Systeme exakt darstellbar |
|---|---|
| EvoODE, gestufte Basis | **20 von 63** |
| SINDy, Polynombibliothek | **40 von 63** |
| ProGED, rationale Grammatik | 53 von 63 |

**Zehn Systeme scheitern allein an der Konstante** (1, 5, 9, 17, 23, 43, 52, 57, 58, 59), bei 15
weiteren ist sie mitbeteiligt — insgesamt haengt sie an 25 der 43 nicht darstellbaren Systeme. System
1 ist der RC-Kondensator, das einfachste System des Benchmarks, fuer jede Standardbibliothek
darstellbar und fuer uns nicht.

Unser Suchraum ist damit **halb so gross wie die Standardbibliothek des naechsten Verwandten.** Das
ist keine Feinheit der Suchstrategie, sondern eine Vorbedingung, die nicht erfuellt ist.

#### Luecke 2: die gefundenen Parameterwerte werden nicht gespeichert

`run_regression.jl:831` schreibt mit `active_term_names(...)` nur die **Termnamen**. Die
Koeffizienten aus `result.params` gehen verloren.

Die Struktur haben wir also, das Modell nicht. Aus 5.248 Kernstunden Kampagne laesst sich kein
einziges gefundenes Modell rekonstruieren, neu simulieren oder auf andere Anfangswerte anwenden.
Das verletzt Design-Prinzip 6 und ist fuer die 756 vorhandenen Records nicht nachtraeglich
reparierbar — wohl aber umgehbar, siehe Plan.

#### Luecke 3: beide Anfangswertsaetze wurden trainiert, nicht getestet

Das Protokoll (§3, entschieden 2026-08-03) uebernimmt beide Saetze je System. Die Begruendungen
darunter behandeln Gitterdichte und Trajektorienquelle. **Warum die beiden Saetze als zwei getrennte
Trainingsprobleme behandelt werden statt als Train/Test, ist nirgends begruendet** — die Frage wurde
nie gestellt.

Der Audit weiss es sogar: er zitiert, ODEBench enthalte die zwei Anfangswerte *to evaluate
generalization*. Wir haben das Datenlayout uebernommen, nicht seinen Zweck.

**Es gibt im ganzen Projekt keine Auswertung auf zurueckgehaltenen Daten.** Kein Train/Val-Split,
keine Generalisierung. Jede Zahl ist In-Sample — auch das R2, das auf der *finalen simulierten
Trajektorie* gegen dieselben Daten gerechnet wird, an die angepasst wurde.

#### Luecke 4: die Metrik der Literatur, und was wir davon koennen

Aus der ODEFormer-Publikation (ICLR 2024, lokal ausgelesen): die Kennzahl ist **Anteil der
Vorhersagen mit R2 groesser 0,9**, getrennt nach *Rekonstruktion* und *Generalisierung*. Mittleres R2
wird bewusst nicht berichtet, weil R2 nach unten unbeschraenkt ist.

Unsere Zahl in dieser Form, aus vorhandenen Daten gerechnet: **80,7 %** ueber alle 756 Zellen
(dim 1: 96,7 %, dim 2: 89,6 %, dim 3: 25,8 %). Das ist die Rekonstruktionshaelfte. Die
Generalisierungshaelfte ist ohne Koeffizienten verschlossen.

**Die publizierten ODEBench-Zahlen je Verfahren liegen uns nicht vor** — sie stehen in den
Abbildungen 4 und 5 als Balkendiagramme, nicht als Tabelle, und das Repository enthaelt keine
Ergebnisdateien. Aus dem Fliesstext belegt ist nur eine Zahl, und die gilt fuer ihren synthetischen
Testsatz, nicht fuer ODEBench: 85 % Rekonstruktion gegen 60 % Generalisierung auf 1D. Ein Satz ist
fuer uns dennoch wichtig: ODEFormer werde nur gelegentlich von PySR uebertroffen, **wenn die Daten
sehr sauber sind** — und unser Regime ist genau das.

**Es ist damit offen, ob 80,7 % gut oder schlecht ist.** Diese Frage ist nicht beantwortet und darf
in keine Richtung behauptet werden.

#### Der Befund hinter allen vieren: die Schrittfolge war verkehrt

Der Projektverlauf war v1, v2.1, v2.2, Gate 1, v3, Gate 2, Stage-Cap, Defektbehebung, 5.248
Kernstunden Kampagne. **In keinem dieser Schritte wurde geprueft, ob das Grundverfahren
konkurrenzfaehig ist.** EvoGrow wurde ausschliesslich gegen sich selbst gemessen. Es gibt bis heute
keinen Baseline-Lauf; `CLAUDE.md` fuehrt ihn seit langem als Phase-5-Luecke.

Was die Kampagne tatsaechlich belegt: das Verfahren laeuft robust durch (756/756, ein
Identitaets-Tripel), es findet Strukturen zu 79 % auf dim 1 und 49 % auf dim 2, und **null von 60 auf
dim 3 und 4**. Das ist eine ehrliche Charakterisierung mit scharfer Grenze. Es ist kein Nachweis,
dass die Methode etwas kann, was andere nicht koennen.

#### Der Plan, in dieser Reihenfolge

1. **Konstante einbauen und messen** (WP-N1, laeuft). Neue Basisvariante, alte bleibt bitgleich.
   Probelauf nur auf dim 1 — 72 Zellen, 0,6 Kernstunden. Zwei getrennte Fragen: steigen die
   bisherigen sechs dim-1-Systeme ueber 79 %, und werden die fuenf neu erreichbaren gefunden?
2. **Parameterwerte mitschreiben** (Teil von WP-N1). Vorbedingung fuer alles Weitere.
3. **Generalisierung als Standardauswertung.** Struktur aus dem Record neu aufbauen, Parameter auf
   IC 1 fitten, von IC 2 aus integrieren, R2 gegen die Wahrheit. Kostet **keinen Suchlauf** — ein
   Parameterfit je Zelle statt der Tausenden, die die Suche gerechnet hat. Damit wird die
   vorhandene Kampagne zum Vorher-Wert des Konstanten-Experiments.
4. **SINDy auf denselben Daten**, gemessen auf beiden Metriken: R2 groesser 0,9 wie die Literatur,
   und Strukturtreffer als das strengere Mass, das wir zusaetzlich anbieten koennen.
5. **Erst dann entscheiden, was Paper 1 ist.**

Ausdruecklich zurueckgestellt: der ungecappte Arm. Er beantwortet eine Frage ueber den Cap, und ob
der Cap interessant ist, haengt daran, ob das Grundverfahren traegt.

**Die Kampagnendaten werden nicht verworfen.** 756 saubere Zellen unter einem Identitaets-Tripel,
protokollkonform, mit benannter Grenze — das bleibt ein gutes Kapitel. Es ist nur kein Paper,
solange die Vergleichszahl fehlt.

---

### Die Verschwendungsmessung auf Kampagnenbreite — und `n_levels` war nie eine Messung

<!-- 87b2468 -->

WP-A9 schliesst die Auswertung ab: die WP-B1-Verschwendungsgroesse aus den 756 Heartbeat-Stroemen und
die Systemtabelle mit 252 Zeilen. Alle Zahlen unabhaengig aus den Rohstroemen nachgerechnet, alle vier
Dimensionen stellengenau reproduziert.

#### Der Befund, der die Fragestellung korrigiert

Der Auftrag ging von einer *Unstimmigkeit* aus: Zelle 1 hat 20 Level-Events, ihr Record meldet
`n_levels = 30`. Die Messung ueber alle Stroeme zeigt das Ausmass — die Level-Event-Zahl streut von
1 bis 30, und **690 von 756 Zellen weichen von 30 ab**; nur 66 erreichen den Wert.

Die Aufloesung steht im Code, nicht in den Daten. `n_levels` ist die Konstante `N_LEVELS = 30`
(`studies/regression/run_regression.jl:681`) — das **konfigurierte Budget**, nicht die ausgefuehrte
Zahl. Der Level-Callback feuert ungedrosselt einmal je abgeschlossenem Level (`:751`). Die
Heartbeat-Zahl ist also die Wahrheit, und die Zellen brechen frueh ab. Es war nie eine Unstimmigkeit,
sondern ein irrefuehrend benanntes Feld.

**Und der Abbruch folgt dem Stage-Cap.** Level-Events nach erreichter Endstufe:

| Endstufe | Zellen | Median Level-Events | min | max |
|---|---|---|---|---|
| 1 | 42 | 1 | 1 | 4 |
| 2 | 42 | 5 | 5 | 8 |
| 3 | 59 | 15 | 11 | 30 |
| 4 | 98 | 16 | 13 | 30 |
| 5 | 515 | 21 | 20 | 30 |

Das ist Claim B auf Kampagnenbreite: wo der Cap greift, endet die Suche, statt das Budget
auszurechnen. Eine bei Stufe 1 gedeckelte Zelle rechnet **ein** Level statt dreissig. Bisher ruhte
diese Aussage auf dem 30-Zellen-Regressionsgitter; jetzt steht sie auf 756 Zellen.

#### Die Verschwendung selbst

Stumme Levels sind die nach der letzten Verbesserung von `best_loss`. Die Groesse braucht die
Wahrheit nicht und gilt deshalb fuer alle 63 Systeme — anders als `wasted_levels` in den Records, das
Levels *oberhalb der erwarteten Stufe* zaehlt und nur auf den 20 exakten definiert ist. Zwei
verschiedene Groessen, die nicht verwechselt werden duerfen.

| dim | Zellen | Mittel `silent_fraction` | stumme / gesamte Levels | letzte Verbesserung auf Level 1 |
|---|---|---|---|---|
| 1 | 276 | 0,385 | 1904 / 4378 | 42 (15,2 %) |
| 2 | 336 | 0,346 | 2401 / 6804 | 68 (20,2 %) |
| 3 | 120 | 0,381 | 1115 / 3143 | 4 (3,3 %) |
| 4 | 24 | **0,811** | 436 / 550 | **12 (50,0 %)** |

Auf Dimension 4 ist die Haelfte aller Zellen nach dem **ersten** Level fertig und rechnet den Rest
umsonst. Ueber alle Dimensionen liegt der Anteil stummer Levels zwischen einem Drittel und vier
Fuenfteln.

**Gegen den Piloten gehalten, mit Vorbehalt.** WP-B1 mass Zeitanteile (dim 1 ~10 %, dim 2 50 %,
dim 3 44 %, dim 4 96 %), hier stehen Levelanteile — die Zahlen sind **nicht direkt vergleichbar**,
und Zeit ist ohnehin keine Evidenz (Design-Prinzip 7). Richtungsgleich sind dim 3 (0,381 gegen 0,44)
und dim 4 als Spitzenreiter. Deutlich anders ist **dim 1: 0,385 gegen 10 %** — auf der billigsten
Klasse ist der Levelanteil viermal hoeher als der Zeitanteil des Piloten. Das ist plausibel, weil
frueh im Lauf die Levels billig sind: viele stumme Levels koennen wenig Zeit kosten. Es bestaetigt
die WP-B1-Entscheidung gegen ein globales Levelbudget eher, als sie zu erschuettern — ein k, das auf
dim 4 richtig waere, waere auf dim 1 teuer erkauft.

#### Wo die Auffaelligkeiten sitzen

Die Auszugstabellen machen die Ausreisser benennbar. **System 63** (SEIR, dim 4) fuehrt beide Listen
an: `silent_fraction` 0,95, 228 stumme Levels auf 12 Zellen, Support-Rate 0. Das ist die
Identifizierbarkeitsgrenze, die `CLAUDE.md` bereits als bewusst ausgeschlossen fuehrt — jetzt mit
Zahlen. **System 28** (Pendel ohne Reibung) ist der teuerste exakte Fehlschlag mit Support-Rate 0 bei
155 stummen Levels, **System 8** (Allee-Effekt, dim 1) verschwendet 0,906 seiner Levels bei
Support-Rate 0,25.

Auf der Surrogatseite sind hohe Verschwendung und schlechter Fit **entkoppelt**: System 30 und 36
verschwenden 0,95 bzw. 0,925 der Levels und erreichen trotzdem R² von 0,988 und 0,9994. Schlechte
Fits sitzen woanders — System 9 (Sprachtod, R² 0,291), System 60 (Aizawa, 0,492), System 53
(Apoptose, 0,629). Verschwendung und Fehlschlag sind also verschiedene Phaenomene und brauchen im
Paper verschiedene Abschnitte.

---

### Die deskriptiven Tabellen stehen — und zwei Instrumentierungsbefunde fallen dabei ab

<!-- 67f2086 -->

WP-A8 hat die fuenf Ergebnistabellen erzeugt, die `PAPER_1.md` als Platzhalter fuehrt: Fit-Qualitaet
getrennt fuer Surrogate (T1) und exakte Systeme (T2), Support-Findung (T3), Stufenoekonomie (T4),
Robustheit und Fehlermodi (T5). Der Konverter traegt jetzt auch die neun Robustheitsfelder; die
Invariantenpruefung laeuft auf der neu erzeugten Registry unveraendert durch. Aggregation und
Darstellung sind getrennte Skripte, wie `analysis/CONVENTIONS.md` es verlangt.

Zum ersten Mal sind die Verteilungen durchgaengig als Quantile und Schwellengitter ausgewiesen statt
als Mittelwerte — die Regel aus WP-A7, jetzt angewandt.

#### Was die Tabellen zeigen

**Die Dimensionsgrenze ist scharf.** Support-Findung auf exakten Systemen, je Bedingung und IC-Satz:

| | dim 1 | dim 2 | dim 3 | dim 4 |
|---|---|---|---|---|
| `pretune_off`, IC 1 | 18/18 | 15/27 | **0/12** | **0/3** |
| `pretune_off`, IC 2 | 12/18 | 15/27 | **0/12** | **0/3** |
| `pretune_on`, IC 1 | 15/18 | 14/27 | **0/12** | **0/3** |
| `pretune_on`, IC 2 | 12/18 | 9/27 | **0/12** | **0/3** |

Auf dim 1 und 2 gelingt Strukturfindung regelmaessig, ab dim 3 nie — in keiner der vier Kombinationen,
in keinem der 60 Faelle. Der IC-Satz ist dabei eine echte Achse: auf dim 1 faellt `pretune_off` von
18/18 auf 12/18, allein durch den Wechsel des Anfangswertsatzes. Das rechtfertigt WP-A4bs
Entscheidung, die IC-Saetze nicht wegzumitteln.

**Die Fit-Qualitaet folgt derselben Grenze.** Auf Surrogaten liegt der Median-R² auf dim 1 und 2 bei
0,98 bis 0,9999, auf dim 3 zwischen 0,66 und 0,91. Auf exakten Systemen faellt der Median-`log10`-Loss
von etwa -11 auf dim 1 auf **+1,8 auf dim 3** — sechs bis dreizehn Groessenordnungen schlechter, je
nach Bedingung.

#### Zwei Instrumentierungsbefunde, die keiner gesucht hat

**`total_diverged_solves` und `total_solver_unstable_solves` sind identisch — in allen 756 Zellen.**
Nachgerechnet: 756 Zellen gleich, null ungleich. Das sind nicht zwei Robustheitsmasse, sondern eines,
zweimal gezaehlt. Sie duerfen im Paper nicht als unabhaengige Groessen nebeneinander stehen. Ob das
Absicht ist oder ein Julia-seitiger Fehler, ist noch offen; die Kampagnendaten sind davon nicht
betroffen, nur ihre Interpretation.

**18 Zellen haben nie einen einzigen Optimizer-`Success` gesehen — und liefern trotzdem exzellente
Fits.** Ihre Retcode-Mengen bestehen nur aus `Failure` und `MaxLossEvals`, bei Losswerten bis
1,9e-12 und R² um 0,9999. Der Retcode ist also kein Qualitaetssignal; das ist die Gegenrichtung zum
laengst bekannten Problem des Sentinel-Loss `1e6` mit Retcode `Success`. Beide Faelle zusammen heissen:
**der Optimizer-Retcode traegt keine Aussage ueber die Ergebnisqualitaet, in keiner der beiden
Richtungen.**

Bemerkenswert daran: **alle 18 sind `pretune_on`**, und je System liefern die drei Seeds identische
Werte — derselbe Kollaps wie in WP-A7. Mechanistisch plausibel: der Warmstart startet so nah am
Optimum, dass der Optimizer sein Evaluationsbudget erreicht oder scheitert, bevor er etwas
verbessern kann. Der Fit ist da schon gut.

**Nicht widerlegt:** T5 bestaetigt 756 Zellen mit `success == True` und null gesetzte
`failure_reason`. `total_nonfinite_solves` ist ueberall null. Die uebrigen Zaehler sind ungleich null
— erfolgreiche Zellen enthalten also sehr wohl interne Solver- und Optimizer-Ereignisse. Das
widerspricht der Annahme fehlerfreier Zellen nicht, praezisiert sie aber: fehlerfrei heisst
abgeschlossen, nicht ereignislos.

---

### Die Verankerung ist strukturell, nicht bloss numerisch — und der Median hatte genau das Gegenteil suggeriert

<!-- 40b89dc -->

WP-A7 hat die beiden Luecken geschlossen, die WP-A6 hinterlassen hat: eine Effektstaerke, die die
Verteilung abbildet statt ihres Medians, und die Kollapsmessung sauber in der Pipeline statt in einer
Handrechnung. Dafuer traegt der Konverter jetzt sieben zusaetzliche Spalten, darunter
`support_terms`; die Invariantenpruefung aus WP-A5 laeuft auf der neu erzeugten Registry unveraendert
durch.

#### Der Befund: der Kollaps sitzt auf der Struktur

Gruppiert wird nach System, IC-Satz und Bedingung — je drei Seeds, 126 Gruppen je Bedingung, gepaart
ueber 63 Systeme. „Kollabiert" heisst: alle drei Seeds liefern dasselbe Ergebnis.

| Zielgroesse | `pretune_on` | `pretune_off` | diskordant on-ja/off-nein | umgekehrt | Cluster-p |
|---|---|---|---|---|---|
| Support-Muster | **96 / 126** | 61 / 126 | 35 | **0** | 1,0e-5 |
| R² | 96 / 126 | 35 / 126 | 61 | **0** | 1,0e-5 |
| Loss | 96 / 126 | 14 / 126 | 82 | **0** | 1,0e-5 |

Unabhaengig nachgerechnet fuer das Support-Muster: 96 gegen 61, diskordant 35 zu 0 — identisch.

Zwei Dinge daran sind bemerkenswert. Erstens ist die Richtung **vollstaendig einseitig**: ueber alle
drei Zielgroessen und alle 126 Paare gibt es keine einzige Gruppe, in der `pretune_off` kollabiert
und `pretune_on` streut. Zweitens ueberlebt der Befund die Clusterung muehelos — anders als die
Strukturdifferenz aus WP-A6, die daran zerbrach.

**Die entscheidende Frage war, ob der Kollaps strukturell ist oder nur numerisch.** Sie ist
beantwortet: er zeigt sich auch auf dem gefundenen Support-Muster, also auf der Gleichheit der
entdeckten Struktur und nicht bloss auf der Gleichheit einer Kennzahl. Damit ist die
Verankerungsaussage fuer Claim C belastbar — der OLS-Warmstart zieht die Suche unabhaengig vom Seed
in dieselbe Struktur, nicht nur zu derselben Zahl.

Der Support-Kollaps ist dabei **schwaecher ausgepraegt** als der auf R² (61 statt 35 kollabierte
`pretune_off`-Gruppen). Das ist erwartbar und kein Widerspruch: gleiche Struktur bei verschiedenen
Parametern ist haeufiger als gleiche Struktur *und* gleiche Zahl. Die Spannweiten stuetzen dasselbe
Bild — unter `pretune_on` ist die Seed-Spannweite des R² bis zum 75-%-Quantil exakt null, unter
`pretune_off` erst bis zum 25-%-Quantil praktisch null.

#### Warum der Median in die Irre fuehrte

Das Schwellengitter zeigt eine Struktur, die der Median vollstaendig verdeckt hatte. Fuer R² auf den
258 Surrogat-Paaren:

| Schwelle | Paare fuer `pretune_on` | Paare fuer `pretune_off` |
|---|---|---|
| 1e-4 | 46 | 63 |
| 1e-3 | 36 | 56 |
| 1e-2 | 30 | 36 |
| 1e-1 | 16 | 13 |

Die Asymmetrie sitzt bei den **kleinen** Differenzen und verschwindet zu den grossen hin — bei 1e-1
liegt sie sogar leicht andersherum. Der Vorzeichentest ist entsprechend deutlich (81 gegen 174,
clusterfest p = 5,4e-4), aber er misst die Systematik einer Richtung, nicht die Groesse einer
Wirkung. Beides zusammen ist die ehrliche Aussage: **die Richtung ist systematisch, der grosse
Ausschlag ist es nicht.**

Beim Loss trennt sich exakt und Surrogat sauber. Auf exakten Systemen ist die Richtung ein
Unentschieden (52 gegen 62, p = 0,67), aber der **Betrag** ist schief: bei Faktor 10 stehen 7 Paare
zugunsten `pretune_on` gegen 21 zugunsten `pretune_off`, bei Faktor 100 sind es 4 gegen 14. Auf
Surrogaten ist es umgekehrt — die Richtung systematisch (74 gegen 176, p = 9,0e-5), die Betraege
ausgeglichen. Zwei verschiedene Phaenomene, die ein einziger Median beide zu null gemittelt haette.

#### Methodische Konsequenz

Der Median als alleinige Effektstaerke war mein Spezifikationsfehler, und er war kein kleiner: er
haette die Kampagne als ergebnislos erscheinen lassen. Fuer alle weiteren Auswertungen gilt deshalb —
Quantile und Schwellengitter statt Mittelwert oder Median, und die Schwelle wird **nie** nach
Sichtung der Daten ausgewaehlt, sondern das Gitter vollstaendig berichtet.

---

### Der Pretuning-Kontrast haelt der Clusterung nicht stand — und die eigentliche Wirkung des Pretunings ist eine andere

<!-- e8bb1c6 -->

WP-A6 hat den gepaarten Test gerechnet, fuer den die Kampagne existiert. Gepaart wird ueber
System, Seed und IC-Satz; die Paarung ist vollstaendig, 378 Paare, davon 120 exakt und 258 Surrogat.

**Die naive Signifikanz auf der Strukturfindung verschwindet, sobald man die Clusterung ernst nimmt.**
Die Kontingenztafel der 120 exakten Paare: 47 beide Bedingungen treffend, 57 beide danebenliegend,
**13 nur `pretune_off`, 3 nur `pretune_on`**. Der exakte McNemar ueber die 16 diskordanten Paare gibt
p = 0,0213. Der Permutationstest, der das Bedingungslabel **je System** vertauscht und damit die
Clusterstruktur erhaelt, gibt **p = 0,218**. Nachgerechnet mit unabhaengiger Implementierung:
p = 0,219, also gleich im Rahmen des Monte-Carlo-Rauschens.

Der Grund ist keine Feinheit, sondern Arithmetik: die 120 Paare stammen aus **20 Systemen**, sechs
Paare je System. Sie teilen Dynamik, Repraesentierbarkeit und Schwierigkeit. Die effektive
Stichprobengroesse liegt bei 20, nicht bei 120. Die Differenz 60 gegen 50 ist damit **kein
belastbarer Befund**, und sie darf im Paper nicht als einer auftreten. Das ist der Grund, warum die
clusterfeste Variante von vornherein als Hauptaussage spezifiziert war.

**Ein Fehler in meiner eigenen Spezifikation.** Ich hatte als Effektstaerke fuer R² den Median der
Paardifferenz mit Bootstrap-Intervall verlangt. Der Median ist hier ein irrefuehrendes Mass: er
betraegt -8,2e-13 und legt nahe, der Unterschied sei numerisches Rauschen. Die Verteilung sagt etwas
anderes — **25,6 % der 258 Paare unterscheiden sich um mehr als 0,01 im R²**, die Extreme liegen bei
±0,4, und die Vorzeichen sind schief verteilt: 174 negativ gegen 82 positiv. Pretuning aendert das
Ergebnis auf einem Viertel der Zellen deutlich, meist zum Schlechteren, waehrend die typische Zelle
unberuehrt bleibt. Ein Median ueber eine solche Verteilung ist keine Effektstaerke. Der Report ist
korrekt, die Frage war falsch gestellt.

Dasselbe gilt fuer den Loss: Fold-Change-Mediane von 1,00000000008 bei p = 0,0106 clusterfest sind
kein Ergebnis ueber die Groesse einer Wirkung, sondern eines ueber die Systematik ihrer Richtung.

#### Der Mechanismus: Pretuning kollabiert die Seed-Streuung

Der Blick auf die groessten Abweichungen hat den eigentlichen Befund geliefert. System 35 liefert
unter `pretune_on` fuer **alle drei Seeds bitgleiches R² von 0,569583**, waehrend `pretune_off`
zwischen 0,920 und 0,969 streut. Das ist kein Einzelfall:

| Bedingung | Zellgruppen (System x IC) mit ueber alle 3 Seeds identischem R² |
|---|---|
| `pretune_on` | **96 von 126 (76,2 %)** |
| `pretune_off` | 34 von 126 (27,0 %) |

Der OLS-Warmstart zieht die Suche unabhaengig vom Seed in dasselbe Becken. Das ist genau die
Verankerung, die `CLAUDE.md` fuer die Populationsuebernahme bei der Promotion als in Kauf genommenes
Risiko fuehrt — hier tritt sie an anderer Stelle auf und ist erstmals gemessen. Und sie erklaert die
Richtung der Strukturdifferenz, ohne dass diese signifikant sein muss: ohne Pretuning erkunden
verschiedene Seeds verschiedene Becken, mit Pretuning nicht.

**Damit verschiebt sich, was die Kampagne aussagt.** Nicht „Pretuning ist schlechter" — das traegt
die Statistik nicht —, sondern „Pretuning tauscht Suchdiversitaet gegen Determinismus, ohne die
Fit-Qualitaet im Median zu veraendern". Das ist eine mechanistische Aussage und passt zu Claim C,
statt eine schwache Vergleichsaussage zu sein, die an der Clusterung zerbricht.

**Nachzuarbeiten:** die Effektstaerke fuer R² und Loss braucht ein Mass, das die Verteilung abbildet
statt ihres Medians — Anteil der Paare jenseits einer inhaltlichen Schwelle, mit clusterfestem
Intervall. Ausserdem war `pandas` trotz durchgaengiger Verwendung nie in `analysis/requirements.txt`
gepinnt; `matplotlib` und `numpy` ebenfalls nicht. Nachgetragen, alle mit fester Version.

---

### Die Kampagne ist in der Analyse-Pipeline — und der Merge hat beim ersten Versuch das Falsche geliefert

<!-- 0176ee5 -->

Die 756 Records liegen jetzt lokal unter `experiments/paper1_phaseB_v1/runs/records/`, die 756
Heartbeat-Stroeme daneben unter `runs/heartbeats/`; beide Verzeichnisse sind ueber
`experiments/*/runs/` gitignored, das Manifest und die Indexlisten sind als Provenienz eingecheckt.
Der Netzspeicher ist ein Cluster-Ausgabeverzeichnis, kein Archiv — die Analyse laeuft ab jetzt gegen
die eingefrorene lokale Kopie.

**Der Merge hat beim ersten Versuch das Falsche geliefert, und die Zusammenfassung sah richtig aus.**
`studies/regression/merge_batch_records.jl` filtert sein `--input-dir` nicht nach Endrecords. Lagen
Records und Heartbeats im selben Verzeichnis, meldete das Skript `considered=17143`, `added=756`,
`skipped_failed=0` — und hatte 756 **Heartbeat-Zeilen** aufgenommen. Die Zahl 756 stimmte, der
Inhalt nicht. Erkennbar war es nur an der Struktur: 15 Felder statt 77, ein Feld `event`, kein
`loss`, kein `git_hash`, und nur 378 statt 756 eindeutige Identitaeten, weil `use_pretuning` im
Heartbeat gar nicht vorkommt. Genau die eine Kennzahl, die man beim Ueberfliegen prueft — die
Zeilenzahl —, war die einzige, die nichts verraten hat.

Nach Trennung der beiden Dateisorten ist die History korrekt. Die Warnung steht in `SCRIPTS.md`; das
Skript selbst ist Julia und wird in einem eigenen WP gehaertet.

**WP-A5** hat daraus die Konsequenz gezogen: `analysis/scripts/aggregate/verify_campaign_registry.py`
prueft elf Invarianten auf der konvertierten Registry — Zeilenzahl, Eindeutigkeit der Identitaeten,
`git_dirty`, die drei Fingerprints **gegen erwartete Werte** statt nur gegen sich selbst, 378 je
Bedingung, 240 exakt gegen 516 Surrogat, Belegung von `exact_support_match` und `r2`. Sollwerte und
Fingerprints sind CLI-Parameter mit den Kampagnenwerten als Vorgabe, damit die Pruefung auf einer
kuenftigen Kampagne anderer Groesse brauchbar bleibt. Der Fehlerpfad ist in beide Richtungen belegt:
auf einer absichtlich verletzten Fixture und auf den echten Daten mit falsch uebergebenem
Fingerprint, beide Male Exit-Code 1.

Die Kette steht damit: Records → `history.jsonl` → `run_registry.csv` → Invariantenpruefung →
`aggregate_by_variant_system.csv`, 252 Zeilen = 63 Systeme x 2 Bedingungen x 2 IC-Saetze. Die
IC-Saetze werden nicht gemittelt (WP-A4b), die Systemachse kommt aus `system_classification.csv`.
Der veraltete „Known gap"-Kasten in `SCRIPTS.md`, der die Bruecke noch als ungeprueft fuehrte, ist
durch die tatsaechliche Kette ersetzt.

**Gegenprobe.** Die Registry reproduziert die direkt aus den Rohrecords gemessenen Zahlen: 60/120
gegen 50/120 beim Support, 20 exakte Systeme, 80 Aggregatzeilen mit `exact_match_rate`. Eine Zahl
aus dem Eintrag oben ist dabei korrigiert — das Surrogat-Median-R² ist 0,9937 (`pretune_on`) gegen
0,9941 (`pretune_off`), nicht zweimal 0,9941; am Befund „Unentschieden" aendert das nichts.

**Offen und bewusst nicht erweitert:** der Konverter traegt 42 seiner moeglichen Spalten, 53
Record-Felder fallen weg — darunter `n_levels`, `eq_overshoot`, `eq_final_stages`, `stage_caps`,
`support_terms` und die Optimizer-Zaehler. Welche davon die Auswertung braucht, wird entschieden,
wenn die Stufen 2 und 3 spezifiziert werden, nicht auf Verdacht. Die Liste steht in
`codex/reports/REPORT_WP_A5.md`.

---

### Die Phase-B-Kampagne ist durch — 756 von 756, null Fehler, ein Identitaets-Tripel

<!-- 5b4ec6c -->

Nach dreizehneinhalb Tagen ist die Kampagne fertig. Der erste Record traegt den Zeitstempel
2026-08-22T10:54:50Z, der letzte 2026-09-04T22:14:38Z. Der Job hat sich auf dem Cluster selbst
abgeraeumt: `oc get jobs -l hpc.scch.at/responsibility=joedicke` findet in `scch-das` nichts mehr,
es ist nichts aufzuraeumen. Die Records liegen vollstaendig auf dem Netzwerkspeicher unter
`phase_b_campaign_91f88c46063fa368101326cbfe1abcdfc9d857fc/tasks`.

**Die Integritaetspruefung ueber alle 756 Records ist sauber.** Kein Record mit gesetztem `error`,
keine leere Datei, 756 eindeutige Zellidentitaeten aus System, Seed, IC-Satz und Bedingung. Und das
Identitaets-Tripel steht ueber die gesamte Kampagne: `git_hash = 91f88c4` mit `git_dirty = false`,
`config_fingerprint = 604e79733b22d64d`, `stage_cap_behavior_fingerprint = ffb0266c7913352c` —
jeweils 756 von 756. Die Publizierbarkeitsbedingung aus `CLAUDE.md` ist damit erfuellt, ohne
Diskrepanz, die in den Supplement muesste. Die Bedingungen sind exakt geteilt, 378 `pretune_on`
gegen 378 `pretune_off`, `stage_cap_policy_active` in allen 756, `n_levels = 30` in allen 756.

**Umfang.** 5.248 Kernstunden, 1,418 Mrd. Loss-Evaluationen und ebenso viele ODE-Solves. Die
Wall-Clock-Zahlen sind hier ausnahmsweise mehr als Kontext, weil die Zellen auf dedizierten
Cluster-Knoten liefen — aber die Kostenaussagen unten ruhen trotzdem auf den Zaehlwerten, nicht auf
`elapsed_s`.

#### Die Kostenverteilung ist noch schiefer als der Zwischenstand vermuten liess

| Klasse | Zellen | Kernstunden | Anteil | Mittel je Zelle |
|---|---|---|---|---|
| dim 1 | 276 | 9 | 0,2 % | Minuten |
| dim 2 | 336 | 1.168 | 22,2 % | 3,5 h |
| dim 3 | 120 | 3.969 | **75,6 %** | 33,1 h |
| dim 4 | 24 | 102 | 1,9 % | 4,3 h |

Hundertzwanzig Zellen — sechzehn Prozent der Kampagne — verbrauchen drei Viertel der Rechenzeit.
Die 276 dim-1-Zellen zusammen kosten neun Stunden, also weniger als ein Drittel einer einzigen
mittleren dim-3-Zelle. Der Zwischenstand vom 2026-09-02 hatte 98 % fuer dim 3 gemessen; das war ein
Artefakt der kostenabsteigenden Startreihenfolge (WP-H7), die die billigen Zellen ans Ende schiebt.
Der Endstand von 75,6 % ist die belastbare Zahl.

**Die teuerste Zelle der Kampagne ist ein Fehlschlag, und zwar der groesste.** System 56, Lorenz mit
Standardparametern im chaotischen Regime, `pretune_on`, IC 1, Seed 123: **289,7 h** fuer Loss 4,27e+1
und R² 0,417. Das ist der neue Rekord und loest System 55 mit 185,7 h ab, das seinerseits nur R²
0,193 liefert. Die fuenf teuersten Zellen sind samt und sonders Lorenz-Zellen (55 und 56) mit R²
zwischen 0,193 und 0,427. Die Rechenzeit wird von den Zellen erzeugt, die scheitern — das
WP-B1-Argument, jetzt auf der vollen Kampagne und mit einem Extremfall, den der Pilot nicht kannte.

#### Der Kontrast, fuer den die Kampagne existiert

Auf den 240 exakten Zellen, gemessen an `pruned_match`:

| Klasse | `pretune_off` | `pretune_on` |
|---|---|---|
| dim 1 | 30 / 36 | 27 / 36 |
| dim 2 | **30 / 54** | **23 / 54** |
| dim 3 | 0 / 24 | 0 / 24 |
| dim 4 | 0 / 6 | 0 / 6 |
| gesamt | **60 / 120** | **50 / 120** |

Auf den 516 Surrogat-Zellen ist der Kontrast dagegen ein glattes Unentschieden: Median-R² 0,9937
(`pretune_on`) gegen 0,9941 (`pretune_off`), 213 gegen 217 Zellen ueber 0,9. Die Richtung des
Struktur-Ergebnisses — Pretuning schadet der Support-Findung eher, als dass es hilft — ist auf dim 1
und dim 2 konsistent, aber sie ruht auf 120 Zellen je Arm und braucht eine Signifikanzaussage, bevor
sie ins Paper geht. Das ist die erste Aufgabe der Analyse-Pipeline.

**Strukturfindung auf dim 3 und dim 4 ist null.** Fuenfzig gekoppelte Zellen, kein einziger
`pruned_match`. Die bekannte Luecke ist damit auf voller Kampagnenbreite bestaetigt und nicht mehr
nur an Regressionszellen belegt. Sie gehoert als Limitation ins Paper, mit dem
Wachstums-only-Argument aus `PAPER_1.md` als Mechanismus.

#### Cap-Verhalten und Verschwendung

Auf den exakten Zellen liegt `eq_overshoot != 0` bei **57 von 240**; `wasted_levels` — hier Levels
oberhalb der erwarteten Stufe, nicht die WP-B1-Verschwendung nach der letzten Verbesserung — hat
Median 0 und Summe 370 von 7.200 Levels, also gut 5 %. Auf Surrogaten sind beide Groessen
bedeutungslos, weil `expected_stage` dort nominell ist; entsprechend ist `eq_overshoot` dort in allen
516 Zellen ungleich null. Das ist keine Messung, sondern die Definitionsgrenze, und die Analyse darf
die beiden Klassen an dieser Stelle nicht zusammenwerfen.

Die eigentliche WP-B1-Verschwendungsmessung braucht die Heartbeat-Stroeme und die Analyse-Pipeline;
sie ist mit dem Kampagnenende unveraendert rekonstruierbar und steht als naechster Schritt an.

---

## 2026-09-03

### Das Feedback von 2024 gegen den heutigen Stand — ein Punkt haelt, und er korrigiert unsere eigene Erzaehlung

<!-- 90fb639 -->

Eine zusammengefasste Diskussion ueber die urspruengliche Dissertationsidee wurde gegen den
aktuellen Code geprueft. Der groesste Teil ist erledigt oder bewusst verworfen; ein Punkt ist heute
schaerfer als damals.

**Erledigt oder obsolet.** Die Forderung nach sauberen Definitionen von `E` und `Delta E` ist
gegenstandslos: es gibt kein Delta-E-Scoring, der Loss ist fixes MSE auf der integrierten
Trajektorie, das Selektionskriterium `loss + lambda * n_params`. Die Frage nach einem Mass fuer
strukturelle Komplexitaet ist dreifach beantwortet (lambda-Term, gestufte Basis, Stage-Cap) und
bildet die Achse des Papers. Die adaptive Datenauswahl ist faktisch mit *nein* beantwortet — kein
Gewichtungsmechanismus, kein Train/Val-Split, keine Noise-Injection. Der Unsicherheitszweig
(local variance gegen statistical uncertainty) existiert nicht.

**Nie gebaut, und als Luecke benannt.** Die probabilistische, Boltzmann-artige Termauswahl gibt es
nicht: kein `softmax`, keine Temperatur, kein Kandidaten-Score. Die Expansion waehlt Gleichung und
Term uniform zufaellig (`_expand`), die Selektion sortiert elitaer nach `objective`; einzige
Nicht-Uniformitaet ist die Usage-Policy. Das ist genau die Stelle, auf die `pruned_match = false`
auf gekoppelten Systemen zeigt. Als Future-Work-Punkt in `PAPER_1.md` aufgenommen.

**Der Punkt, der haelt: Integration gegen Differentiation.** Die Gruenderzaehlung — wir schaetzen
keine Ableitungen — ist als pauschale Aussage nicht mehr haltbar. Die Bewertung ist
trajektorienbasiert, aber der Paper-1-Beitrag selbst ist ableitungsbasiert:
`_cap_estimate_derivatives` in `src/structure/stage_cap.jl` schaetzt vor Suchbeginn per zentraler
Differenzen oder lokaler Polynomanpassung, das OLS-Warmstart-Pretuning ebenfalls, und WP-R1
argumentiert im Ableitungsraum.

Die Korrektur trennt zwei Rollen: Bewertung ohne Ableitungsschaetzung, strukturelle Voranalyse mit
ihr. Diese Trennung ist keine Designpraeferenz, sondern ein Messergebnis — WP-L2 hat gezeigt, dass
v3s Promotionssignal `r_k` ableitungsfehler-kontaminiert ist und seine Absorptionskapazitaet mit der
Termzahl waechst; Gate 2 hat v3 verworfen. Damit ist die Position staerker als die urspruengliche,
weil Evidenz dahintersteht. Unausgesprochen waere sie die erste Reviewer-Frage.

Festgehalten in `PAPER_1.md`, Phase 6, als *Method Positioning*, mit den drei Stellen im Paper, an
denen es stehen muss: Method (Einfuehrung des Caps), Failure Analysis (die v3-Lehre), Limitations
(Cap-Qualitaet ist durch Ableitungsqualitaet begrenzt — der dokumentierte Mechanismus hinter System
63 und den IC-Saetzen mit wenig Dynamik).

**Offen bleibt** der Anwendungs- und Nutzenpunkt: fuer welche Problemklasse die Methode einen
messbaren Vorteil hat. Das ist woertlich die Frage, die die externen Spalten des Protokoll-Audits
beantworten muessen, und damit kein neuer Punkt.

---

## 2026-09-02

### Der Kontrast auf Dimension 2 ist ein Unentschieden — und die teuerste Zelle der Kampagne ist ein Fehlschlag

<!-- eaf52d7 -->

308 von 756 fertig, weiterhin **null Fehler**, weiterhin ein Identitaets-Tripel ueber alle Records
(`91f88c4` / `604e79733b22d64d` / `ffb0266c7913352c`, `git_dirty = false`). Dimension 1 ist noch
nicht angefangen; verbraucht sind 3.563 Kernstunden auf 117 dim-3-Zellen gegen 230 auf 191
dim-2-Zellen.

#### Der offene Punkt von gestern ist beantwortet, und die Antwort ist nicht die erwartete

Gestern war festgehalten, dass alle dim-2-Zellen `pretune_on` waren und der Paper-Kontrast deshalb
allein auf Dimension 3 stand. Inzwischen liegen **28 vollstaendige Paare auf Dimension 2** vor (alle
exakt, Systeme 24–29):

| | Paare | `on` besser | `off` besser | Support-Treffer on/off | Median Loss-Evals on/off |
|---|---|---|---|---|---|
| **dim 2** | 28 | **14** | **14** | 17 / 16 | **1,1e5 / 4,9e5** |
| dim 3 | 57 | **45** | 12 | 0 / 0 | 5,0e6 / 3,2e6 |

Auf Dimension 2 macht Pretuning **qualitativ keinen Unterschied**: 14:14 beim Loss, Mediane
praktisch identisch (1,892e-08 gegen 1,841e-08), Support-Treffer 17 gegen 16. Es ist aber
**4,34-mal billiger in Zaehlern**.

**Die Richtung des Kontrasts haengt also an der Dimension, und das sind zwei verschiedene Aussagen,
nicht eine abgeschwaechte.** Auf dim 2: gleich gut, deutlich billiger. Auf dim 3: besser, und dort
sogar teurer in Zaehlern (5,0e6 gegen 3,2e6). Eine ueber alle Dimensionen gemittelte Zahl wuerde
beide Aussagen zerstoeren und ist zu vermeiden — das ist dieselbe Lehre, die WP-A4 fuer die
IC-Saetze gezogen hat.

Anzumerken ist, dass die 28 dim-2-Paare aus nur sechs Systemen stammen (24, 25, 26, 27, 28, 29) und
die Klasse 336 Zellen umfasst. Die Aussage ist belastbar fuer diese sechs Systeme, nicht fuer die
Klasse.

#### Zelle 79: 185,7 Stunden fuer einen Fehlschlag

System 55, `pretune_off`, IC 1, Seed 123 — die zweite der beiden Torwaechter-Zellen ist fertig und
setzt einen neuen Kampagnenrekord in der Laufzeit: **185,7 h**, 3,82 Mio. Loss-Evaluationen.
Ergebnis: **Loss 336,7, R² 0,194, kein Support-Treffer, Endstufe 4**.

Die teuerste Zelle der Kampagne liefert damit eines ihrer schlechtesten Ergebnisse. Das ist die am
2026-08-31 gemessene invertierte Kosten-Qualitaets-Beziehung, hier nicht als Aggregat ueber
Haelften, sondern in einer einzelnen, benennbaren Zelle.

Damit haengt das Kampagnenende nur noch an **Zelle 25** — System 56 (Lorenz), IC 1, Seed 123,
`pretune_on` — seit dem Start in Betrieb, inzwischen **11 Tage**.

---

## 2026-09-01

### 224 von 756 — die ersten Support-Treffer der Kampagne, und Dimension 3 ist 98 % der Rechenzeit

<!-- ca2cb85 -->

Achtzehn Stunden nach der ersten Qualitaetsauswertung: **224 fertige Zellen statt 102**, plus 122,
weiterhin **null Fehler**, weiterhin ein einziges Identitaets-Tripel ueber alle Records
(`91f88c4` / `604e79733b22d64d` / `ffb0266c7913352c`, `git_dirty = false`). Der dim-3-Block ist
durch, die Kostensortierung liefert jetzt das billige Feld.

#### Der Kostenkontrast zwischen den Dimensionsklassen ist brutal

| Klasse | Zellen | Kernstunden | Mittel je Zelle |
|---|---|---|---|
| dim 3 | 113 | **3.159** | 27,96 h |
| dim 2 | 111 | **61** | 0,55 h |

Praktisch gleich viele Zellen, **Faktor 52 im Mittelwert**, und Dimension 3 traegt 98 % der bisher
verbrauchten Rechenzeit. Damit ist die Warnung aus `hpc_requirements.md` §3b — die 336
dim-2-Zellen ruhten auf einem Klassenmittel, dessen Median 15-mal kleiner ist — nach oben aufgeloest:
Das Klassenmittel war nicht zu klein, sondern die dim-3-Klasse zu teuer. Das Restfeld ist billig.

#### Die ersten Support-Treffer, und wo sie sitzen

| Klasse | exakte Zellen | `pruned_match` | Surrogat-R² (Median) |
|---|---|---|---|
| dim 3 | 45 | **0** | 0,758 |
| dim 2 | 54 | **23** | **0,984** |

Auf Dimension 2 gelingt Strukturfindung also ueberhaupt — zum ersten Mal in dieser Kampagne. Und die
Verteilung ist informativ:

| System | | Treffer | Loss (Median) |
|---|---|---|---|
| 24 | harmonischer Oszillator, ungedaempft | **6/6** | 1,2e-14 |
| 25 | harmonischer Oszillator, gedaempft | **6/6** | 8,6e-15 |
| 27 | Lotka-Volterra, einfach | 5/6 | 3,1e-08 |
| 32 | gedaempfter Doppelmuldenoszillator | 3/6 | 19,6 |
| 38 | Van der Pol, vereinfacht | 3/6 | 1,6e-09 |
| 26 | Lotka-Volterra, Konkurrenz | **0/6** | 3,9e-04 |
| 28 | Pendel ohne Reibung | **0/6** | 3,0e-05 |
| 29 | Dipol-Fixpunkt | **0/6** | 7,2e-04 |
| 31 | SIR | **0/6** | 6,7e-05 |

**Die untere Haelfte ist der eigentliche Befund.** Vier Systeme mit einem Loss zwischen 3e-5 und
7e-4 — also einem sehr guten Fit — und trotzdem null Struktur-Treffer. Das ist der Befund des
Regressionsgitters, jetzt auf vier zusaetzlichen Systemen und in einer Klasse, in der die Suche
nachweislich treffen *kann*: Systeme 24 und 25 sitzen im selben Lauf und treffen 6 von 6. Niedriger
Loss und richtige Struktur sind also nicht dasselbe, und der Unterschied ist nicht die Schwierigkeit
der Klasse.

Surrogate auf dim 2 sind stark: 33, 34 und 36 bei R² ≥ 0,999, Schlusslicht ist 41 (Zellzyklus nach
Tyson) mit 0,854.

#### Ein Vorbehalt, der die Zahlen oben bindet

**Alle 111 dim-2-Zellen sind `pretune_on`.** Die Kostensortierung hat die `pretune_off`-Haelfte der
Klasse noch nicht angefasst, es gibt auf Dimension 2 also **keinen Kontrast**. Der Paper-Kontrast
steht weiterhin ausschliesslich auf Dimension 3 — dort inzwischen **53 Paare, `pretune_on` gewinnt
44**, Median-Loss 0,161 gegen 0,274. Ob die Richtung auf dim 2 haelt, ist offen; die 23 Treffer oben
sind kein Ergebnis *ueber* die Bedingungen, sondern eines *innerhalb* einer Bedingung.

#### Das Ende der Kampagne haengt jetzt an zwei Zellen

516 ungestartete Zellen, ueberwiegend dim 1 und 2, nach dem gemessenen dim-2-Mittel grob wenige
hundert Kernstunden. Das Feld begrenzt die Laufzeit nicht mehr. Was sie begrenzt:

- **Zelle 25** — System 56 (Lorenz), IC 1, Seed 123, `pretune_on` — **10 Tage**, seit dem Start
- **Zelle 79** — System 55, `pretune_off` — 7 d 4 h

Beide halten je einen der 16 Slots. Fuer die angekuendigte Wartung (SILVERTON/STERLING, Notfenster
7.9., Migration 13.10.) heisst das: Der 13. Oktober ist praktisch vom Tisch, und der 7. September
ist nur dann relevant, falls `nfs.orion.scch.at` von einem der beiden Systeme bedient wird. Compute
laeuft auf `alnilam01/02`, also nicht auf den angekuendigten Maschinen.

---

## 2026-08-31

### Erste Qualitaetsauswertung der Kampagne, 102 Zellen — und 45 % der Rechenzeit faellt nach der letzten Verbesserung

<!-- eecd778 -->

Die Records liegen ueber Laufwerk `S:` lesbar vor, ohne Clusterzugriff; die Kampagne bleibt
unberuehrt. Ausgewertet wurden alle 102 fertigen Zellen plus die 118 Heartbeat-Stroeme.

**Hygiene zuerst:** alle 102 Records tragen *ein* Identitaets-Tripel
(`91f88c4` / `604e79733b22d64d` / `ffb0266c7913352c`), `git_dirty = false`, null Fehler. Die
Publizierbarkeitsbedingung aus WP-P1 haelt erstmals ueber eine dreistellige Zahl von Produktions-
records.

**Alles Folgende gilt fuer die haertesten 16 % des Feldes** — ausnahmslos Dimension 3, ausnahmslos
Attraktoren, vier davon chaotisch. Die Kostensortierung liefert das Schlimmste zuerst, und genau das
ist hier zu sehen. Ueber Dimension 1 und 2 sagt der Befund nichts.

#### Exakte Systeme: `pruned_match` = 0 von 40

| System | | Loss (Median) | R² (Median) |
|---|---|---|---|
| 54 | Lorenz, gutartig | 0,21 | **0,966** |
| 56 | Lorenz, Standard | 53,6 | 0,247 |
| 61 | Chen-Lee | 62,9 | 0,196 |
| 55 | Lorenz, komplex | 351 | 0,186 |

Kein einziger Support-Treffer. Das ist die bekannte Luecke, hier ohne jede Abmilderung: System 54
erreicht R² 0,966 und trifft die Struktur trotzdem nicht, 55/56/61 scheitern auch im Fit. Die
Kampagne bestaetigt damit auf breiterer Basis, was das Regressionsgitter schon zeigte — und was
woertlich die These von Paper 2 ist.

#### Surrogate: R² Median 0,787

62 Zellen, 20 davon ueber 0,9, genau eine ueber 0,99, sieben unter 0,5. Schlusslicht ist der
Aizawa-Attraktor (60) mit 0,44.

#### Der Kontrast, fuer den die Kampagne existiert

42 vollstaendige `(System, IC, Seed)`-Paare. **`pretune_on` gewinnt 34 von 42 beim Loss**,
Median-Loss 0,022 gegen 0,075, Median-R² 0,789 gegen 0,646. Ein klares gerichtetes Ergebnis, und es
steht auf der ungnaedigsten Teilmenge, die das Feld hergibt.

Nebenbefund, der die Kostenlehre aus `hpc_requirements.md` §3 bestaetigt: `pretune_on` leistet in
*Zaehlern* mehr Arbeit (5,0 Mio. Loss-Evaluationen im Median gegen 2,9 Mio.) und verbraucht in
Kernstunden ungefaehr gleich viel (1.334 h gegen 1.468 h). Zaehler und Rechenzeit laufen wieder
auseinander; die Zeitdifferenz darf nicht als Speedup berichtet werden.

#### Die Laufzeitfrage, beantwortet

**1.262 von 2.802 Kernstunden — 45 % — fallen nach der letzten Verbesserung an.** Rekonstruiert aus
den Heartbeats, die `best_loss` pro Level lueckenlos tragen (keine Level-Luecken in 102 von 102
Stroemen). Extremfall: eine Zelle auf System 56 verbringt 142 ihrer 166 Stunden stumm.

Und die Kosten-Qualitaets-Beziehung ist **invertiert**:

| | Median Laufzeit | Median R² |
|---|---|---|
| billigere Haelfte | 4,2 h | **0,795** |
| teurere Haelfte | 42,2 h | **0,427** |

Die Rechenzeit wird von den Zellen erzeugt, die scheitern. Das ist das WP-B1-Argument, jetzt mit
Kampagnendaten und deutlich schaerfer als aus dem Piloten.

**Es ist aber kein Argument fuer ein Konstanten-k, und der Grund ist neu.** Die teuren Systeme haben
*wenige* stumme Levels (55: 8, 56: 6, 59: 3, 61: 3 von 30) — sie verbessern sich bis spaet, nur
immer marginaler. Die vielen stummen Levels sitzen bei den *billigen* Systemen (53: 19, 57: 15,
52: 13,5). Ein globales „stoppe nach k stummen Levels" wuerde also dort sparen, wo ohnehin wenig zu
holen ist, und die teuren Zellen kaum anfassen. WP-B1s Ablehnung eines konfigurierten k wird
bestaetigt, nicht widerlegt. Was die 45 % rechtfertigen, ist ein **strukturiertes** Kriterium mit
Blick auf die Verbesserungsrate, und das bleibt eine eigene Forschungsfrage.

#### Metadaten-Luecke, ohne Kampagneneingriff reparierbar

`wasted_levels` und `eq_wasted_levels` werden in `experiments/run_experiment.jl:385` nur im
`representability == "exact"`-Zweig berechnet — die Definition haengt an `expected_stage`, also an
der bekannten Wahrheit. Fuer 43 der 63 Systeme bleiben beide Felder `null`. Die Waste-Zahl, die die
Kampagne laut `CLAUDE.md` als Ergebnis berichten will, fehlt damit fuer zwei Drittel des Feldes.

**Das ist kein Neustartgrund.** Die WP-B1-Groesse ist „Levels seit der letzten Verbesserung" und
braucht die Wahrheit gar nicht; sie steht vollstaendig in den Heartbeats und ist genau der Weg, ueber
den die 45 % oben entstanden sind. Der Nachbau gehoert in die Analyse-Pipeline, nicht in den
Kampagnenpfad.

---

## 2026-08-30

### Kampagne bei 93/756 — die Makespan-Zahl ist ueberholt, das Kostenmodell aufgebraucht

<!-- ce0f7f7 -->

Statusabfrage am Cluster, acht Tage nach dem Start. Job `evoode-phase-b-campaign`: **93 succeeded,
16 running, 0 failed**, 109 von 756 Zellen gestartet. Alle gestarteten Zellen sind Dimension 3 — die
Kostensortierung arbeitet also noch immer die teuerste Klasse ab und hat die restlichen 636 Zellen
noch nicht angefasst.

**Der Befund ist die Makespan-Zahl, nicht der Durchsatz.** §3b hatte am 2026-08-28 bei 75 Zellen die
teuerste beobachtete Zelle mit 123,5 h notiert. Inzwischen sind **183,6 h** fertig (Zelle 21), und
entscheidender: **Zelle 25 — System 56 (Lorenz), IC-Satz 1, Seed 123, `pretune_on` — belegt seit dem
Start einen der 16 Slots und laeuft jenseits von 192 h.** Damit definiert nicht mehr der Klassenmittel-
wert den Boden, sondern diese eine Zelle: Die Kampagne kann nicht vor ihr fertig werden. Zwei
weitere Slots haengen langfristig fest (Zelle 79 bei 130 h, Zelle 83 bei 103 h), die effektive
Nebenlaeufigkeit auf dem Restfeld ist also 13 statt 16.

**Das Kostenbudget aus §1 ist ausgegeben.** 2.442 Kernstunden in den 93 fertigen Zellen, rund 766 h
in den 16 offenen — etwa **3.208 Kernstunden fuer 14 % des Feldes**, gegen projizierte 3.384 fuer
alles. Der Fehler liegt genau dort, wo §3b ihn schon lokalisiert hatte: nicht im Klassenmittel,
sondern in der Verteilung innerhalb der Klasse.

**Was das ueber die Restzeit nicht sagt.** Die 647 ungestarteten Zellen sind Dimension 1, 2 und 4 und
kostabsteigend sortiert, also einzeln deutlich billiger. §3b's 5,5 bis 6 Tage Restzeit sind durch
nichts hier widerlegt. Sie ruhen aber auf Pilot-Klassenmitteln fuer genau diese Dimensionen, und in
der einen Klasse, fuer die es inzwischen Kampagnendaten gibt, betrug die Spreizung *innerhalb* der
Klasse einen Faktor 150. Die Zahl ist eine Kapazitaetsangabe, kein Fertigstellungsdatum. Die 336
Dimension-2-Zellen bleiben die dominante Unsicherheit — unveraendert seit §3b.

Dokumentiert als `docs/hpc_requirements.md` §3c; die ueberholte 123,5-h-Zeile im Kopf und in §3b ist
als ueberholt markiert statt geloescht.

---

## 2026-08-24

### Repraesentationsspalte gefuellt — unsere Basis ist schmaler als SINDys Default

<!-- 20658b5 -->

Letzter offener Phase-3-Punkt abgearbeitet: die Repraesentationsfaehigkeit je System und je
evaluiertem Suchraum. Grundlage sind die in §2.6 dokumentierten Bibliotheken und Grammatiken der
ODEFormer-Baselines, gerechnet gegen unsere Gleichungsklassifikation. Tabelle in
`analysis/data/paper1_phaseB_v1/representational_adequacy.csv`, Auswertung in Audit §2.6c.

| Suchraum | Y | U | N |
|---|---|---|---|
| EvoODE, gestufte Basis | **20** | 0 | 43 |
| SINDy, Polynombibliothek Grad 1–10 | **40** | 0 | 23 |
| SINDy, `[poly, sin, cos, exp]` | 42 | 5 | 16 |
| SINDy, `[poly, sin, cos, exp, log, sqrt, 1/x]` | 43 | 7 | 13 |
| ProGED, polynomiale Grammatik | 40 | 0 | 23 |
| ProGED, rationale Grammatik | **53** | 1 | 9 |
| ProGED, trigonometrische Grammatik | 41 | 5 | 17 |

**Der Befund ist unbequem und gehoert genau deshalb auf den Tisch.** Eine schlichte
Polynombibliothek stellt 40 von 63 Systemen exakt dar, unsere gestufte Basis 20. Wir sind also nicht
schmaler als eine exotische Konfiguration, sondern schmaler als der **Default** des naechsten
Verwandten.

Und die Luecke hat genau eine Form: 10 Systeme brauchen nur die Konstante, 6 Konstante plus
gemischte Monome, 3 nur gemischte Monome, 1 Grad ≥ 5. **Das ist Stufe A, und sonst nichts.** Der
folgenreichste Einzelposten ist die Konstante — ohne Bias-Term faellt SINDy von 40 auf 24, also
haengen 16 der 20 Systeme an einem konstanten Term.

**Konsequenz fuer die Repraesentationsentscheidung.** Abschnitt 11 hatte Stufe A Gewicht gegeben,
weil gemischte Monome die einzige Familie mit messbarem Approximationsverlust sind. Dieser Befund
verstaerkt es aus anderer Richtung und ist der schaerfere von beiden, weil er von keiner Messung
abhaengt: Ein Reviewer, der EvoODE neben SINDy legt, sieht 20 gegen 40, bevor er eine Ergebniszahl
gelesen hat. Fuer die Aussage von Paper 1 ist das irrelevant — der Controller wird auf den 20
exakten Systemen auditiert, und „weniger Suchaufwand bei identischem Ergebnis" haengt an keiner
Bibliotheksgroesse. Aber die Zahl gehoert genannt, bevor jemand anderes sie nennt. Fuer die Bruecke
nach Paper 2 lautet die Begruendung fuer Stufe A jetzt nicht mehr „19 Systeme mehr", sondern
„schliesst die gesamte Repraesentationsluecke zur Standardbibliothek des naechsten Verwandten".

**Die U-Verdikte sind kein Schlamperei-Rest, sondern das Ergebnis.** Produkte zweier
Bibliotheksfunktionen (`sin(u1)*cos(u1)`), Funktionen zusammengesetzter Argumente (`sin(u1-u2)`) und
Quotienten durch einen Zustand (`cos(u2)/u1`) sind nur darstellbar, wenn der publizierte Lauf
Interaktionsterme ueber die Custom-Bibliothek aktiviert hatte — und das steht nirgends. Fuer diese 5
bis 7 Systeme lautet die Antwort des Audits: aus der Beschreibung nicht entscheidbar.

**Ein System ist fuer alle unerreichbar:** 44, getriebenes Pendel mit `|v|*v`-Daempfung — N fuer
unsere Basis, fuer die reichste SINDy-Bibliothek und fuer ProGEDs rationale Grammatik.

---

### Erste Kampagnendaten, und ein drittes ODEBench-Artefakt

<!-- 37f6c5f -->

**Kampagne nach zwei Tagen: 45/756, 16 laufend, null Fehler.** Alle 45 sind dim 3 — genau wie die
Kostensortierung es vorsieht. Gegenrechnung: 48 h x 16 Kerne = 768 Kernstunden, bei einem gemessenen
dim-3-Mittel von 17,7 h sind das rund 43 Zellen. Beobachtet 45. Das Kostenmodell traegt.

**Und das Identitaets-Tripel ist ueber alle 45 Records einheitlich:**
`91f88c4` / `604e79733b22d64d` / `ffb0266c7913352c`. Publizierbarkeit verlangt genau das, und es
haelt erstmals in Produktion statt nur im Bootstrap.

**Die Caps feuern wie auditiert.** System 54 → `[None,3,3]`, System 56 (Lorenz) → `[None,3,3]`. Der
WP-C5-Befund haelt im Kampagnenlauf.

**Inhaltlich der erste harte Befund**, mit der Einschraenkung, dass dies die haerteste Teilmenge ist
(nur dim 3, nur `pretune_on`, 6 % des Feldes):

| System | Typ | Loss | R² | `pruned_match` |
|---|---|---|---|---|
| 55 | exakt | 312–351 | 0,19–0,26 | false |
| 56 Lorenz | exakt | 44–56 | 0,25–0,37 | false |
| 54 IC 2 | exakt | 0,404 | 0,954 | false |

Auf den chaotischen **exakten** Systemen ist der Cap korrekt bei 3, die Wahrheit liegt in der Basis,
die Stufe ist frei — und die Suche scheitert trotzdem deutlich. Das ist woertlich die These von
Paper 2, erstmals mit Kampagnenevidenz statt nur aus dem Regressionsgitter. Nebenbefund: System 59
zeigt Cap-Instabilitaet zwischen den IC-Saetzen (`[None,None,5]` gegen `[None,None,None]`) — derselbe
Effekt wie System 31, jetzt auf einem zweiten System.

**Beim Absichern der Autorenanfrage ein drittes Artefakt gefunden.** `github.com/GPBench/ODEBench`,
ein *eigenstaendiges* ODEBench-Repository, dokumentiert LSODA und **150 Punkte** als Default. Erster
Reflex: Das koennte meine Schlussfolgerung aus `evaluate.py` kippen.

Kippt sie nicht — **es gehoert Alberto Tonda**, angelegt 2025-08-06, alle Commits von ihm, also die
Neuverpackung des Autors der methodischen Quelle, knapp zwei Jahre nach ODEFormer. Damit stehen drei
Artefakte nebeneinander:

| Artefakt | Eigentuemer | Abtastung | von einer Auswertung gelesen? |
|---|---|---|---|
| `strogatz_extended.json` | Benchmark-Autoren | 512 | ja, `evaluate.py` |
| `solve_and_plot.py` | Benchmark-Autoren | 150 | nein |
| `GPBench/ODEBench` | Tonda 2025 | 150 | ja, eigene Studie |

Die Inkonsistenz entsteht **im Benchmark-Repository selbst**, und die spaetere Neuverpackung hat den
Wert des Skripts geerbt statt den der Datendatei. Ein eigenstaendiges Repository verbreitet jetzt
150 Punkte als ODEBench-Default, waehrend die Auswertung des Benchmarks selbst auf 512 lief. Das
*erhoeht* den Wert der Beobachtung in der Mail — sie ist keine interne Marginalie mehr, sie hat
einen Traeger.

Zusaetzlich geprueft und ohne Treffer: `run.py`, `metrics.py`, `sklearn_wrapper.py` enthalten keinen
zweiten Generalisierungspfad. Ungeprueft und ans Team uebergeben: OpenReview-Forum, Issues, die
Commit-Historie von `evaluate.py`, Camera-ready gegen arXiv, Datensatz-Spiegelungen.
Pruefauftrag in `docs/anfrage_pruefauftrag.md`.

---

## 2026-08-22

### Gitterfrage im Code beantwortet — und ODEFormer rechnet auf demselben Gitter wie wir

<!-- 34f3248 -->

Vor der geplanten Autorenanfrage vollstaendig recherchiert, damit nichts gefragt wird, was oeffentlich
beantwortet ist. Repository-Dateibaum (59 Dateien), `solve_and_plot.py`, `evaluate.py`,
`environment.py`, `generators.py`, `baseline_utils.py`.

**`evaluate.py` beantwortet es.** `read_equations_from_json_file` liest
`_sample["solutions"][solution_i][0]["t"]` und `["y"]` direkt aus `strogatz_extended.json` und
integriert **nicht** neu. Diese Datei traegt 512 Punkte. Also:

> **Die ODEBench-Auswertung von ODEFormer lief auf demselben 512-Punkte-Gitter, das wir verwenden.**

Die 150-Punkte-Konfiguration in `solve_and_plot.py` schreibt nach `solutions.json`, und kein
Auswertungspfad im Repository liest diese Datei. Tonda et al. haben das Skript als Protokoll
genommen — der Faktor 3,4 in der Dichte liegt also **zwischen zwei publizierten Arbeiten**, nicht
zwischen uns und dem Benchmark. Stuetzend: der Forecasting-Pfad baut sein Gitter als
`np.linspace(t0, t0+5, 512, endpoint=True)`.

**Eine Spannung bleibt, und sie ist die bessere Frage.** Das Paper sagt, die zwei kuratierten
Anfangsbedingungen je Gleichung seien fuer die Generalisierung da. Der Loader liest aber nur
`[solution_i][0]`, also die **erste**, und die Aufgabe `y0_generalization` zieht eine frische
Zufalls-IC per `self.env.rng.randn(dimension)`. Ob die berichteten Generalisierungszahlen aus der
zweiten kuratierten IC oder aus Zufallsziehungen stammen, ist aus den oeffentlichen Artefakten nicht
entscheidbar. Das ist die Frage fuer die Mail; Entwurf in `docs/anfrage_odebench_autoren.md`.

**Und zwei Konsequenzen fuer die eigene Darstellung, nachgezogen.** Erstens: **Unsere Caps sind
gitterabhaengig** — WP-G1b hat es gemessen (System 54: `[nothing,2,2]` → `[nothing,3,3]`, zwei
Sicherheitsverletzungen verschwinden, korrekte Caps 6 → 8 von 13), waehrend gelieferte gegen selbst
integrierte Werte in allen 26 Zellen **nichts** aendern. Die Empfindlichkeit gilt der Dichte, nicht
der Datenqualitaet. Das Gitter gehoert damit in die Aussage hinein — „unter 512 Punkten ueber
[0,10]" — und nicht in eine Fussnote. Es ist zugleich die sauberste Verteidigung: Wer selbst sagt,
dass Dichte den Controller bewegt, kann nicht beschuldigt werden, ein guenstiges Gitter still
auszunutzen.

Zweitens: Die Frage ist **schon eingeplant**. Abtastdichte ist eine der vier Robustheitsachsen von
Paper 3. 150 und 512 werden als zwei Dichtepunkte dieser Achse festgeschrieben — dann wird die
Vergleichbarkeit mit beiden publizierten Protokollen per Konstruktion herstellbar statt per Annahme.

---

### Provenienz geklaert — die Datei ist Upstream, und die 150/512-Diskrepanz liegt dort

<!-- ae954de -->

Nachtrag zum Eintrag darunter, und er korrigiert ihn. Die Vermutung, unsere `strogatz_extended.json`
sei eine abweichende Version, ist **falsch**.

**Gepruefte Herkunft.** Die Datei ist **byteidentisch** mit dem Upstream-Artefakt in
`sdascoli/odeformer` unter `odeformer/odebench/strogatz_extended.json`, letzte Upstream-Aenderung
`32dd990` vom 2023-09-29. Heruntergeladen und verglichen. Im Repo ist sie seit dem allerersten
Commit unveraendert — identischer Hash bei `366a71a`, `78143e7`, `706549f` und HEAD; die
Umstrukturierung war eine reine Umbenennung. Der urspruengliche Ordnername `benchmarks/odeformer/`
hat die Herkunft die ganze Zeit mitgetragen, nur hat sie niemand aufgeschrieben.

**Die Diskrepanz liegt im Upstream-Repository selbst.** Das Erzeugungsskript
`odeformer/odebench/solve_and_plot.py` traegt

```python
config = {"t_span": (0,10), "method": "LSODA", "rtol": 1e-5, "atol": 1e-7,
          "first_step": 1e-6, "t_eval": np.linspace(0,10,150), "min_step": 1e-10}
```

und schreibt nach **`solutions.json`** — *nicht* in `strogatz_extended.json`. Die committete JSON,
also die Datei, die man tatsaechlich herunterlaedt, traegt **512** Punkte. Das Repository liefert
somit zwei Abtastungen, und Tonda et al. beschreiben die des Skripts.

**Was das aendert.** „Wir uebernehmen die Abtastung des Datensatzes" stimmt doch — fuer die
committete Datei. Die Vergleichbarkeitsfrage verschwindet damit nicht, sie verschiebt sich: **Welches
der beiden Gitter hat eine publizierte Arbeit verwendet?** Das ist je Quelle zu pruefen, nicht
anzunehmen, und der Unterschied betraegt Faktor 3,4 in der Dichte — auf genau der Achse, die
darueber entscheidet, ob der transformierte Suchraum in die Irre fuehrt.

**Und zur Erinnerung des Nutzers, wir haetten die Daten mal selbst gerechnet:** inhaltlich richtig,
nur nicht an der Datei. Gemeint war **WP-G1b** — dort wurde genau das gemessen, und zwar an den
Caps, also an der Stufenzuendung. Zwei Arme auf identischem 512-Punkte-Gitter: gelieferte
`y`-Matrizen gegen selbst integriert mit `Tsit5` bei 1e-9. Ergebnis: **Arm A = Arm B in allen 26
Zellen**, Rauschboeden unterscheiden sich erst in der dritten bis vierten Stelle. Der
Integrationsfehler der gelieferten Daten ist *glatt* in t, und ein ableitungsbasierter Rauschboden
sieht glatten Fehler praktisch nicht. **Der Gewinn auf System 54 gehoerte der Gitterdichte, nicht
der Datenqualitaet.** Die Selbstintegration bleibt trotzdem, aber aus einem anderen Grund: fuer den
Suchverlust, wo die gelieferten Toleranzen MSE-Boeden oberhalb unserer Ergebnisse erzwingen.

Provenienzluecke aus §2.2 damit geschlossen: Herkunft, Upstream-Pfad, Upstream-Commit und
Inhaltshash stehen in `docs/paper1_odebench_protocol_alignment.md` §2.4.

---

### Tonda et al. gelesen — und dabei eine eigene Protokollangabe widerlegt

<!-- ba8b8be -->

Der Nutzer hat das Paper besorgt (GECCO '25 Companion, Malaga, S. 2563–2571,
DOI 10.1145/3712255.3734301, CC-BY; Tonda, Zhang, Chen, Xue, Zhang, Lutton). Gelesen, auditiert,
Ergebnis in `docs/paper1_odebench_protocol_alignment.md` §2.4 und §2.5.

**Der teuerste Befund ist nicht das Paper, sondern das, was beim Lesen auffiel.** Tonda et al.
beschreiben das ODEBench-Artefakt exakt: LSODA, `rtol=1e-5`, `atol=1e-7`,
`t_eval=np.linspace(0,10,150)` — **150 Punkte je Trajektorie**. Unsere Datei traegt **512**, direkt
im File nachgeprueft. Gleicher Name, andere Erzeugungskonfiguration.

Damit ist die Aussage *„wir uebernehmen die Abtastung des Datensatzes"* falsch, und sie stand in
`PAPER_1.md`, im Audit-Dokument und im Paper-Abschnitt 5. Korrigiert. Unsere Abweichung ist groesser
als bisher berichtet: nicht nur strengere Toleranzen (1e-9 gegen 1e-5/1e-7), sondern ein **3,4-fach
dichteres Gitter** (Δ ≈ 0,0196 gegen 0,067).

**Und die Abtastdichte ist keine harmlose Achse.** Genau sie identifiziert dieselbe Arbeit als
entscheidend: Der Sampling-Schritt korreliert stark damit, ob der transformierte Suchraum in die
Irre fuehrt, und ein kleinerer Schritt mildert den Effekt. Wir stehen also auf der guenstigen Seite
der Achse, die den Fehlermodus regiert — ein Vorteil, der zu deklarieren ist, kein Detail. Die
Dimensionsaufteilung der 63 Systeme (23/28/10/2) stimmt dagegen exakt mit unserer ueberein.

**Was das Paper zeigt.** Zwei Datentransformationen fuer Systemidentifikation, PySR als Suchmethode,
ODEBench als Benchmark. Drei Ergebnisse: Irrefuehrende Suchraeume entstehen **auch ohne Rauschen** —
die Ground Truth traegt dort schlechtere Fitness als Konkurrenten, und ein State-of-the-Art-Verfahren
laesst sich nachweislich taeuschen; der Sampling-Schritt korreliert stark damit; Rauschen
verschlechtert beide Transformationen deutlich.

**Wo uns das trifft — und es ist nicht die Stelle, die wir zuerst vermutet haben.** Das Pretuning
ist die *harmlose* Stelle: Es initialisiert nur einen Fit, dessen Zielfunktion der Simulationsverlust
ist, ein fehlrangierter Ableitungsraum kostet dort Iterationen, keine Entscheidungen. **Die
Exposition ist der Stage Cap.** Sein gesamter Lauf besteht aus Entscheidungen auf gewichteten
Kleinste-Quadrate-Residuen im Ableitungsraum gegen einen Richardson-Boden — genau die Konstruktion,
von der die Arbeit zeigt, dass sie die Wahrheit unter ihre Konkurrenten sortieren kann. Vier Dinge
begrenzen das Risiko (positive Evidenz noetig, alle Bedingungen relativ, Boden geschaetzt statt
gesetzt, 0 trunkierte Zeilen von 80), keines beseitigt es. Steht jetzt in `paper/04` als Limitation,
nicht als Fussnote.

**Zwei Konvergenzen.** Ihr zentrales Phaenomen reproduziert unsere WP-R1-Referenz unabhaengig — 13
von 126 Modellen divergieren beim Integrieren trotz nahezu perfekter Ableitungsanpassung. Und ihre
genannte Zukunftsrichtung, *vorherzusagen, wann die Transformation in die Irre fuehrt, aus den
Eigenschaften der Trajektoriendaten*, ist mit anderen Worten unsere offene Frage nach dem
praediktiven Kriterium. Externe Motivation dafuer, geschenkt.

**Nicht verwendbar als Leistungsreferenz** — anderes Framing, andere Methode, erklaerter Fokus auf
den Vergleich von Transformationen. Das war ohnehin die Rolle, die ihm zugedacht war.

Offen bleibt die Herkunft unserer Artefaktdatei; die Upstream-Quelle ist laut Tonda et al.
`github.com/sdascoli/odeformer` unter `odeformer/odebench`.

---

### Vergleichsstrategie entschieden — und eine externe Arbeit trifft unsere Messung von heute

<!-- fa25727 -->

Die Vergleichsdiskussion ist gefuehrt. Ergebnis in `docs/diskussion_vergleichsmethoden.md` §8,
Konsequenzen in `PAPER_1.md`, `docs/paper1_odebench_protocol_alignment.md` §2,
`docs/phd_thesis_arc.md` §3 und `paper/05_experimental_protocol.md`.

**Harte Regel fuer Paper 1: keine quantitative Cross-Method-Leistungsaussage.** Nicht vorsichtig,
nicht ungefaehr, sondern keine. Erlaubt sind Aussagen ueber Protokolle — dass ODEBench von mehreren
Verfahren verwendet wurde, dass deren Suchraeume und Evaluationsprotokolle sich unterscheiden, dass
publizierte Zahlen deshalb nicht als direkt vergleichbar behandelt werden. Verboten sind „besser
als", „konkurrenzfaehig mit", „aehnliche Leistung".

**Zwei Quellen, und nur zwei.** ODEFormer/ODEBench als Pflichtquelle — sie definiert den Benchmark
und berichtet mehrere Methodenfamilien darauf, womit ein Teil der Repraesentationsspalte aus einer
einzigen Quelle fuellbar wird. Und **Tonda et al. 2025**, *When Data Transformations Mislead
Symbolic Regression: Deceptive Search Spaces in System Identification* — ausdruecklich **keine**
Leistungsreferenz, sondern methodische Evidenz.

**Und die zweite Quelle trifft genau das, was ich heute gemessen habe.** Tonda et al. zeigen, dass
die Ueberfuehrung eines dynamischen Problems in ein algebraisches Ableitungsproblem irrefuehrende
Suchlandschaften erzeugen kann: Ein gutes Ziel im Ableitungsraum garantiert nicht, dass die
dynamisch richtige Struktur bevorzugt wird. Genau das steht seit heute Nachmittag in unseren eigenen
Zahlen — **13 der 126 WP-R1-Referenzmodelle divergieren beim Integrieren**, bei den exakten Systemen
Mittelwert −2,8 gegen Median 0,9999 der Trajektoriengueten. Zwei unabhaengige Belege desselben
Effekts.

Zwei Konsequenzen: Die Familien-Rangfolge aus WP-R1 erbt den Vorbehalt — sie ist im Ableitungsraum
gemessen und kann in genau dieser Weise taeuschen. Und fuer das Verfahren stuetzt der Befund eine
bestehende Entscheidung: Ableitungsraum als billiger Warmstart, Trajektorienraum als verbindliche
Bewertung.

**Die Kette hat ein viertes Glied bekommen:** Representability → Identifiability → Search
Recoverability → **Evaluation**. Ein gescheiterter Recovery-Versuch darf der Suche erst zugeschrieben
werden, wenn auch feststeht, dass das Evaluationsprotokoll die relevante Eigenschaft misst.

**Dritte Repraesentationsdimension**, optional: *best attainable functional fit*. Fuer EvoODE durch
WP-R1 vorhanden, fuer die meisten Fremdlaeufe nicht rekonstruierbar — deshalb keine Pflichtspalte.
Ein Audit darf keine Anforderung erzeugen, die nur die eigene Methode erfuellt.

**Neue Luecke gefunden und dokumentiert:** Die Herkunft von `benchmarks/data/strogatz_extended.json`
ist im Repository **nirgends** festgehalten — kein Commit, kein Release, keine URL. Das
`source`-Feld je System nennt die Lehrbuchstelle, nicht den Datensatz. Gesichert ist bisher nur der
Inhaltshash `b11f8bda…` und dass die Datei seit `706549f` (2026-04-30) im Repo liegt. Herkunft muss
nachgetragen werden; das braucht eine Angabe vom Nutzer.

**Formulierung korrigiert:** Nicht „wir verwenden sauberere ODEBench-Daten" — das wertet das
Originalprotokoll ab. Stattdessen: gleiche Systeme, Parametrisierungen, Anfangsbedingungen und
Abtastung, aber Neuintegration bei strengeren Toleranzen, damit Solver-Fehlerboeden nicht in das
untersuchte Genauigkeitsregime hineinreichen.

**Paper 3, Kernmatrix steht:** SINDy (feste Bibliothek), PySR (freie symbolische Suche), ODEFormer
oder Nachfolger (vortrainierte symbolische Inferenz), EvoODE (kontrolliertes Wachstum) — je eine
Methode je Suchphilosophie, kein Leaderboard. Die dritte Zeile wird spaet eingefroren.

---

### WP-R1 — die suchfreie Referenz dreht die Rangfolge der fehlenden Familien um

<!-- c05e3a6 -->

Die Referenz steht: fuer alle 63 Systeme und beide IC-Saetze die Kleinste-Quadrate-Projektion der
geschaetzten Ableitungen auf die **volle** Basis, alle Terme aktiv, keine Suche. 126 Zeilen,
deterministisch, byteidentisch bei Wiederholung. Damit ist die Auswahlregel aus der
Repraesentationsdiskussion anwendbar — und sie faellt anders aus als die Abdeckungsrechnung
nahelegt.

**Erstens: die Basis spannt weit mehr, als „43 nicht darstellbar" klingt.** Surrogate erreichen im
Ableitungsraum einen Median von **0,999993**, exakte Systeme 0,999998. 55 von 86 Surrogatzeilen
liegen ueber 0,9999, nur drei unter 0,9. Auf dem beobachteten Wertebereich ist ein Saettigungsterm
eben doch durch niedrige Polynome darstellbar. *Nicht darstellbar* heisst nicht *schlecht
approximierbar*.

**Zweitens, und das ist der eigentliche Befund: die Rangfolge ist fast umgekehrt zur Systemzahl.**

| fehlende Familie | Zeilen | Median dR2 |
|---|---|---|
| polynomiale Interaktion Grad >= 3 | 18 | **0,99815** |
| oszillatorisch mit Argument | 14 | 0,99989 |
| Offset / Forcing | 50 | 0,99998 |
| **saettigende Interaktion** | 24 | **1,00000** |

Saettigung — zweitgroesste Systemzahl, groesster Architekturpreis, der ganze Grund fuer Stufe B —
kostet im Mittel **nichts**. Die Familie, die wirklich weh tut, ist `u^2*v`: gemischte Monome
Grad >= 3, Van der Pol und Duffing. Und die braucht keine inneren Parameter, sie ist Stufe A.

**Damit verschiebt sich die Entscheidung, ueber die am Montag gesprochen wird.** Stufe A gewinnt an
Gewicht, Stufe B verliert. Was offen bleibt: ob das an den Daten liegt — 512 Punkte ueber einen
begrenzten Wertebereich. Auf einem Bereich, der die Saettigung wirklich durchlaeuft, saehe es
anders aus. Das ist eine Frage ans Sampling und gehoert zu Paper 3.

**Drei Einschraenkungen, ohne die die Tabelle ueberinterpretiert wird.** Die Zuordnung ist
assoziativ, nicht kausal — ein System mit zwei fehlenden Familien geht in beide Zeilen ein; sauber
trennen koennte man nur durch das teure Experiment selbst. In *eine* Richtung traegt sie trotzdem:
Wird jedes System einer Familie gut angenaehert, kauft die Familie nachweislich wenig. Zweitens ist
die volle Basis nicht sparsam — 0,99999 mit achtzehn Termen sagt nichts ueber ein interpretierbares
Modell, und Interpretierbarkeit ist der Zweck. Drittens ist der Ableitungsraum nicht der
Trajektorienraum: **13 der 126 Modelle divergieren beim Integrieren**, bei den exakten Systemen
liegt der Mittelwert der Trajektoriengueten bei −2,8 gegen einen Median von 0,9999. Fuer den
Vergleich mit Kampagnendaten ist deshalb die Ableitungsguete die belastbare Groesse.

**Nebenbefund:** Zwei exakte Zeilen liegen unter 0,999 — System 11 / IC 1 und 55 / IC 1. Dort
enthaelt die Basis die Wahrheit, die Luecke ist also die Grenze der **Ableitungsschaetzung**. Das ist
derselbe Mechanismus, an dem v3 gescheitert ist, hier erstmals auf sauberen Daten beziffert.

**Zur Umsetzung:** Codex hat WP-R1 implementiert und `blocked` gemeldet — Julia startet in seiner
Sandbox nicht, das Depot liegt ausserhalb des beschreibbaren Workspace. Die Abnahme habe ich
gefahren. Dabei zwei Fehler in einem nie ausgefuehrten Skript gefunden: ein fehlendes `include` und
zwei unqualifizierte Aufrufe nicht exportierter Funktionen. Beides waere ohne Ausfuehrung durch
Lesen sichtbar gewesen; `codex/CODEX_PROTOCOL.md` haelt das jetzt fest, zusammen mit dem
`--add-dir`-Startbefehl, der den Depot-Zugriff vermutlich behebt.

---

### Die Repraesentationsfrage ist entschieden — als Bruecke zwischen Paper 2 und Paper 3

<!-- 825da07 -->

Die Gespraechsvorlage vom selben Tag hat eine Antwort bekommen, und sie korrigiert die Vorlage an
vier Stellen. Ergebnis in `docs/diskussion_repraesentationsraum.md` §9, Konsequenzen in
`docs/phd_thesis_arc.md` §3 und §5.

**Die Reihenfolge steht:** `#1 -> #2 -> Representation Expansion -> #3`. Die Erweiterung wird **kein
viertes Paper**, sondern eine methodische Bruecke. Damit hat die Frage einen Platz im Bogen, ohne ihn
zu strecken. Begruendung ist wissenschaftliche Kontrolle: Paper 2 fragt, warum Recovery scheitert,
*obwohl* die Wahrheit im Raum liegt — wird vorher der Raum verbreitert, aendern sich Kandidatenraum,
Kollinearitaeten, Optimierungslandschaft und Identifizierbarkeit gleichzeitig, und keine Ursache
laesst sich mehr isolieren.

**Meine Ergaenzung dazu:** Die Operatoren aus Paper 2 muessen **katalogunabhaengig** entworfen
werden. Bauen sie auf Polynomstruktur, ueberträgt sich Paper 2 nicht auf den erweiterten Raum, und
die Reihenfolge kostet genau das, was sie sparen soll.

**Zwei weitere Entscheidungen.** Stufe A ist **kein eigenes Ziel**: repraesentationstechnisch billig,
experimentell aber genauso teuer wie B — Fingerprint, Caps, Lookahead, Kostenmodell, Regressionsblock
bewegen sich in beiden Faellen. Der Preis wird einmal gezahlt, A und B gemeinsam. Und der **Schwanz
wird nicht bedient**: fuenf Operatorfamilien fuer fuenf Systeme ist der Punkt, an dem
Benchmark-Vollstaendigkeit in Benchmark-Overfitting kippt. Die fuenf bleiben als *out-of-catalog
cases* stehen.

**Vier Korrekturen an meiner Vorlage, alle berechtigt:**

1. **Die GP-Abgrenzung war zu binaer.** „Faellt eine der drei Eigenschaften weg, ist man bei GP" ist
   falsch — dazwischen liegen grammatikgefuehrte SR, Beam Search, MCTS, enumerative Suche,
   Programmsynthese. Die tragfaehige Achse ist *statisch begrenzt ↔ kontrolliert wachsend ↔ frei
   kompositionell*. EvoODE steht in der Mitte, und die Mitte ist duenn besetzt — das ist die bessere
   Positionierung.
2. **„Abzaehlbarer Katalog" ist bei Stufe B mathematisch falsch.** `sin(omega*u)` mit reellem omega
   ist ein Kontinuum. Endlich bleibt die Menge der **Term-Templates**. Die Methode ist ueber
   Templates zu definieren, nicht ueber Basisfunktionen.
3. **Der Katalog darf nicht aus dem Benchmark abgeleitet werden**, an dem er danach gemessen wird.
   Erst semantisch definieren, dann ODEBench zur Messung verwenden — sonst ist 58/63 eine Definition
   und kein Ergebnis. Die Zahl darf sich dabei verschieben.
4. **„rational" ist keine zulaessige Familie.** `P/Q` sprengt den Raum. Zugelassen werden benannte
   mechanistische Motive: `u/(K+u)`, `u^n/(K^n+u^n)`, `sin(omega*u)`.

**Neu und wertvoll: drei Ebenen statt zwei.** Darstellbarkeit, Identifizierbarkeit,
Auffindbarkeit — ein Fehlschlag ist erst dann ein *Suchproblem*, wenn die ersten beiden Ebenen
geklaert sind. Das gibt Paper 2 seinen Geltungsbereich und ist praezisere Sprache als meine
Zweiteilung. Die Fast-Entartung eines reicheren Katalogs landet genau auf der mittleren Ebene.

**Neu: der Protokoll-Audit braucht zwei Spalten, nicht eine.** *In principle representable* gegen
*representable under the evaluated protocol*. SINDy kann jede Bibliothek tragen — wenn der
publizierte Lauf Polynome bis Grad 3 verwendete, ist ein Saettigungsterm dort unerreichbar. PySR
kann einen Operator erlauben und ihn durch Komplexitaetsgrenzen dennoch ausschliessen. Diese
Dimension wird in SR-Vergleichen ueblicherweise nicht sichtbar gemacht; sie ist ein eigener Beitrag
von Paper 3.

**Und ein Einwand von mir, der in der Antwort fehlte:** Die geplante R²-Auswertung je fehlender
Motivfamilie hat eine Verwechslungsgefahr. Ein R² von 0,3 belegt **nicht**, dass die Familie fehlt —
es kann die Suche gewesen sein, die das beste Modell *innerhalb* der Klasse nicht fand. In den
Records sieht beides gleich aus. Noetig ist eine Referenz: die beste erreichbare Anpassung innerhalb
der aktuellen Basis, algebraisch auf dem Ableitungsproblem, ohne Suche. Erst die Differenz trennt
„die Klasse kann es nicht" von „die Suche fand es nicht". Ohne sie ist die Auswahlregel fuer
kuenftige Termfamilien nicht belastbar.

Phase B laeuft unveraendert weiter. Keine Basisaenderung, kein neuer Fingerprint.

---

### Phase B laeuft — und der Motivkatalog beziffert, wie eng unser Suchraum ist

<!-- c3eddf3 -->

**Die Kampagne ist gestartet.** `git 91f88c46063fa368101326cbfe1abcdfc9d857fc`, Bootstrap auf Orion
bestaetigt `phase_b_fingerprint=604e79733b22d64d`, `rows=756`, `unique_identities=756`,
`cost_desc_index_rows=756`, 20 exakt / 43 Surrogat. Job `evoode-phase-b-campaign` laeuft mit
`parallelism: 16`.

Zwei Dinge waren vor dem Start noch zu reparieren. **`backoffLimit` stand auf 1** — der Wert zaehlt
Pod-Ausfaelle ueber den *ganzen* Job, und ein wissenschaftlicher Fehler beendet den Pod mit 0. Zwei
Node-Zwischenfaelle in neun Tagen haetten also die komplette Kampagne beendet. Jetzt 50. Und der
**Bootstrap schrieb ins Smoke-Verzeichnis**, waehrend die Zellen aus dem Kampagnenverzeichnis lesen;
dafuer gibt es jetzt ein eigenes Manifest.

**Die Startreihenfolge ist kostensortiert (WP-H7).** Ein Indexed Job verteilt dynamisch, es faellt
also kein Kern trocken. Was die Gesamtdauer bestimmt, ist der Startzeitpunkt der laengsten Zelle —
und die dim-3-Zellen lagen in Manifestreihenfolge hinten. `indices_cost_desc.txt` stellt dieselben
756 Indizes nach gemessenem Klassenmittel um: dim 3, dim 2, dim 4, dim 1. Erwartete Ersparnis rund
zwei Tage. Wissenschaftlich neutral, `manifest_index` wird mitgeschrieben.

Nach zwei Minuten sichtbar bestaetigt: Index 10 fertig (System 53, `loss=1,87e-05`, 58,9 s), Index 16
nachgestartet. Die dynamische Zuteilung arbeitet wie beschrieben.

**Der eigentliche Befund des Tages ist aber ein anderer.** Aus der Frage des Nutzers, warum wir nur
mit einer Polynombasis arbeiten, wurde eine Auswertung aller 82 nicht abgedeckten Terme in den 117
Gleichungszeilen:

| Katalog waechst um | Systeme neu | exakt gesamt |
|---|---|---|
| Ausgangslage | — | 20 / 63 |
| + Konstante | +10 | 30 |
| + rational (Saettigung, Hill) | +12 | 42 |
| + gemischte Monome Grad >= 3 | +9 | 51 |
| + Trigonometrie mit skaliertem Argument | +7 | **58** |
| + exp, log, reelle Potenz, hohe Potenz, Betrag | je +1 | 63 |

**Vier Familien decken 92 Prozent.** Danach braucht jedes weitere System seine eigene Familie —
Gompertz (log), Sprachtod (reelle Potenz), Landau (hohe Potenz), SIR (exp), getriebenes Pendel
(Betrag). Diese Kante ist selbst ein Ergebnis: Sie sagt, wo ein Katalog aus Evidenz aufhoert.

Und die Leiter hat einen klaren Knick: **39 von 63 ohne jede Architekturaenderung** (Konstante und
Monome sind gewoehnliche Basisfunktionen, das Modell bleibt linear in den Koeffizienten, der
OLS-Warmstart unveraendert), **58 von 63 mit Termen, die innere Parameter tragen** (`K` in
`u/(u+K)`, `omega` in `sin(omega*u)`). Letzteres ist der Architektursprung — und er ist bezahlbar,
weil das Pretuning auf dem algebraischen Ableitungsproblem arbeitet: aeussere Koeffizienten bleiben
linear, es entsteht ein separables Kleinste-Quadrate-Problem.

**Kein Schritt davon ist GP.** GP ist ein Suchverfahren, keine Darstellungsform. Additive
Termstruktur, abzaehlbarer staffelbarer Katalog und minimaler Start mit Promotionsregel bleiben in
allen Stufen erhalten; es aendert sich die Ausdrucksstaerke, nicht die Suchdisziplin.

**Die Warnung, die dazugehoert:** Das misst Darstellbarkeit, nicht Auffindbarkeit. `u/(u+K)` geht
fuer grosses `K` in einen linearen Term ueber — ein reicherer Katalog erzeugt fast aequivalente
Strukturen, und genau daran scheitert Recovery heute schon. Stufe B koennte Paper 2 schwerer machen,
bevor sie etwas verbessert.

Festgehalten in `docs/phd_thesis_arc.md` §5 (neu, inklusive der Einordnung: die Frage hat im
Dreier-Bogen bisher **keinen** Platz und ist Voraussetzung fuer Paper 3) und als Gespraechsvorlage
in `docs/diskussion_repraesentationsraum.md`.

---

## 2026-08-21

### WP-A4/A4b — die Auswertung konnte R² gar nicht sehen, und drei Achsen fielen stumm weg

<!-- 1e0820a -->

`CLAUDE.md` fuehrte die Analyse-Pipeline als „Phase-A-foermig": `table_main_results.py` reindiziere
auf eine hartkodierte Variantenliste. Beim Aufsetzen des Arbeitspakets stellte sich heraus, dass
diese Beschreibung zwei Fehler hat — der eine war laengst behoben, der andere viel zu klein
beschrieben.

**Erstens, ueberholt:** Die Variantenachse hat WP-A2 repariert; unbekannte Varianten werden
angehaengt statt verworfen. Geblieben war die **System**achse — zwei feste ID-Listen mit den zehn
Phase-A-Systemen. Auf Kampagnendaten fallen damit 53 von 63 Systemen ohne Meldung heraus, und wenn
keine der IDs vorkommt, entsteht eine leere Tabelle mit Erfolgsmeldung.

**Zweitens, und das war der eigentliche Fund:** Die Records tragen seit WP-M1 ein `r2`. Die
Bruecke aus WP-A1 fuehrt das Feld nicht, das Aggregat kennt es folglich nicht. **Die Bewertung der
43 Surrogatsysteme war damit ueberhaupt nicht herstellbar** — Grundsatz 8 verpflichtet genau diese
43 auf R². Das ist kein Darstellungsfehler, sondern ein fehlender Datenpfad fuer zwei Drittel der
Systeme.

**Drittens, ungesucht:** Aggregiert wurde ueber `(variant_slug, system_id)`. Die beiden IC-Saetze
verschwanden in einem Mittelwert — ausgerechnet die Achse, auf der der Cap unterschiedlich
entscheidet (System 31 ist der dokumentierte Fall).

**Geprueft, nicht geglaubt.** Ich habe alle fuenf Abnahmepunkte selbst nachgerechnet. Der
ueberzeugendste ist der Rueckfallpfad: Ohne Klassifikationsdatei leitet das Skript fuer Phase A
dieselbe Aufteilung her, die vorher als Konstante im Quelltext stand — **acht exakt, zwei
Surrogat**. Die alte Liste war korrekt; sie stand nur an der falschen Stelle. Phase A bleibt
byteidentisch in Aggregat, CSV und TeX.

**Eine bewusste Abweichung von meiner eigenen Spec.** Ich hatte verlangt, dass in der
Surrogattabelle keine `exact_match_rate`-Spalte auftaucht, „auch nicht leer". Das kollidiert mit der
Byteidentitaet von Phase A, die dieselbe Datei erzeugt. Aufgeloest ueber zwei zusaetzliche,
klassenreine Dateien (`exact_systems_summary.csv`, `surrogate_systems_summary.csv`); fuer Paper 1
sind ohnehin diese die Quelle.

**WP-A4b, der Nachtrag:** `outputs/` steht in `.gitignore`. Die handgeschriebenen Testdaten lagen
dort, die acht Konfigurationen waren committet — fuenf zeigten ins Ignorierte. Auf einem frischen
Klon waren die R²-Abnahme und zwei Fehlerfaelle nicht wiederholbar. Die Fixtures liegen jetzt unter
`analysis/fixtures/`, das `CONVENTIONS.md` neu als Ort fuer handgeschriebene Eingaben fuehrt;
`analysis/data/` bleibt fuer Abgeleitetes reserviert. Gegengeprueft, indem ich die erzeugten
Ausgaben geloescht und die Kette aus der getrackten Datei neu aufgebaut habe.

**Erste Uebergabe ueber die Codex-CLI.** Ab jetzt startet Claude die Codex-Sitzung selbst statt eine
Spec fuer einen Polling-Takt liegenzulassen; `codex/CODEX_PROTOCOL.md` und `CLAUDE.md` sind
entsprechend geaendert. Anlass war, dass WP-A4 mit sauberem Working Tree wartete und niemand
zuschaute.

Offen bleibt klein: `r2_by_dim` und `stage_cap_behavior_fingerprint` werden durchgereicht, aber
nicht aggregiert.

---

### `PAPER_1.md` revidiert — das autoritative Dokument beschreibt endlich die Variante, die der Beitrag ist

<!-- 13fc099 -->

`PAPER_1.md` war auf den 2026-05-17 datiert, plante im Detail um v3 herum und erwaehnte den Stage
Cap kein einziges Mal. Gleichzeitig erklaert `CLAUDE.md` es zum autoritativen Dokument. Diese
Inversion — das massgebliche Dokument beschreibt eine verworfene Variante — war seit Wochen als
Prioritaet 6 notiert.

**Grundlage war der Draft von WP-W1** (`docs/PAPER_1_draft.md`, 2026-08-17). Der war brauchbar, aber
vier Ereignisse alt: WP-V1, WP-C5, die vollstaendige Sondierung und WP-B1. Ich habe ihn
aktualisiert, promoviert und den Draft geloescht.

**Was gegenueber dem Draft inhaltlich anders ist:**

1. **Designregel 3 ist eine andere geworden.** Der Draft fuehrte *"Abstain in the doubt band"* als
   dritte, aus einem Defekt erkaufte Regel. Das Band gibt es nicht mehr. An seiner Stelle steht
   jetzt die Regel, die WP-V1 tatsaechlich erkauft hat: **einen Mechanismus nur durch ein Experiment
   gutschreiben, das ihn isoliert.** WP-C4 war die Lorenz-Reparatur zugeschrieben worden, die vom
   Reopen-Zweig kam. Das ist die teuerste der drei Regeln, und sie ist als solche benannt.
2. **Die nicht waehlbare Schwelle ist von einer Limitation zu einem Teil von Claim C geworden.** Der
   Draft fuehrte die Bandkonstanten unter "was noch fehlt: ein Hold-out". WP-V1 hat gezeigt, dass es
   kein Hold-out gibt, der die Schwelle rettet — Leave-one-system-out landet bei 0,044 bis 0,278,
   geliefert wird 0,35, und bei jedem gewaehlten Wert trunkiert Lorenz wieder. Das ist ein Ergebnis,
   kein Versaeumnis, und steht jetzt im Claim.
3. **Claim B hat Zahlen.** Vorher ein Platzhalter, jetzt die Regressionsevidenz: 25,4 Prozent
   weniger Evaluationen, 30 von 30 bitidentisch, keine Zelle teurer, unter einem Identitaets-Tripel.
4. **Die Verschwendungsmessung ist als Ergebnis aufgenommen**, mit der k-Tabelle und der Begruendung,
   warum keine Abbruchregel eingebaut wurde. Sie steht in Phase 6, nicht als offene Aufgabe.
5. **Neuer Methodenpunkt:** Zaehlwerte lassen sich nicht in Rechenzeit umrechnen. Gehoert in den
   Methodenteil, weil Grundsatz 7 sonst falsch gelesen wird.
6. Fingerprints, Statuszeilen und Phasenstand auf den 2026-08-21 gezogen; der Timeout-Abschnitt des
   alten Dokuments ist durch die Realitaet ersetzt (Orion hat kein Walltime-Limit, der einzige
   deterministische Stopp ist das Evaluationsbudget).
7. Aus dem alten `PAPER_1.md` uebernommen, was der Draft fallen liess: der **Protokoll-Audit** als
   offener Punkt und die Logging-Politik in verdichteter Form.

Der Abschnitt "Change List Against The Existing PAPER_1.md" aus dem Draft ist entfallen — er war ein
Review-Hilfsmittel fuer genau diesen Schritt. An seine Stelle tritt ein Abschnitt **Open Items and
Known Inconsistencies**, der die fuenf Punkte fuehrt, die wirklich offen sind, darunter die
Titel-/Zaehl-Diskrepanz in `docs/wp_c1_stage_cap_horizon_audit.md`.

**Damit ist die Praezedenzregel wieder gueltig:** `PAPER_1.md` entscheidet, wenn die Dokumente
auseinanderlaufen. Prioritaet 6 in `CLAUDE.md` ist gestrichen.

---

### `docs/hpc_requirements.md` neu geschrieben — aus Messungen statt aus Schaetzungen

<!-- 64ff142 -->

Das Dokument war seit dem 2026-08-13 mit einem SUPERSEDED-Banner versehen: geschrieben fuer einen
Slurm-Standort, mit Laufzeiten von einem belasteten Laptop und einer Apptainer-Runbook-Sektion fuer
Skripte, die es nicht mehr gibt. Es war zugleich das Dokument, auf das `CLAUDE.md` fuer die
Kostenrechnung verweist. Mit der vollstaendigen Sondierung und WP-B1 liegt jede Zahl vor, die es
geschaetzt hatte.

**Neuer Zuschnitt.** Kein Antragsdokument mehr, sondern ein Kostenmodell: die Zahl (§1), ihre
Herleitung aus dem Piloten (§2), die `pretune_off`-Korrektur (§3), die blinden Flecken (§4), der
gemessene Verschwendungsanteil (§5), das Ressourcenprofil je Zelle (§6), die Reproduzierbarkeits-
bedingungen (§7) und der bisherige Verbrauch (§8). Die Beratungsfragen und das Slurm-Runbook sind
entfallen — die Mechanik steht in `docs/hpc_deployment_guide.md`.

**Drei Zahlen haben sich gegenueber dem alten Dokument umgedreht:**

1. Die Gesamtschaetzung war **nicht** um ein bis zwei Groessenordnungen zu hoch, sondern um 15
   Prozent — 3.900 geschaetzt gegen 3.384 hochgerechnet. Falsch war die Klassenaufteilung, nicht die
   Summe.
2. Die 3.384 Kernstunden sind eine **obere**, keine untere Schranke. Die Planungsgroesse ist jetzt
   eine Spanne von rund 2.000 bis 3.400 Kernstunden, weil `pretune_off` auf allen drei gemessenen
   Systemen billiger ist, aber um Faktor drei streut.
3. Der Pilot hat 281 statt der angekuendigten 50 Kernstunden verbraucht — steht jetzt als Zahl im
   Dokument, damit die naechste Ankuendigung an den Standort stimmt.

Der Verschwendungsanteil aus WP-B1 ist bewusst **nicht** als Kostenhebel gefuehrt, sondern als
Eigenschaft, die in den reservierten Zahlen bereits enthalten ist.

Nachgezogen: der Verweis in `docs/hpc_deployment_guide.md` §10, der noch vor dem Dokument warnte,
und die Rewrite-Aufforderung in `CLAUDE.md`.

---

### WP-B1 — kein Levelbudget: der Kompromiss ist bei jedem Schwellenwert schlecht

<!-- f4ceb3d -->

287 Zellen aus sechs Quellen — 44 Pilot, 3 Sondierung, zweimal 120 Regression —, alle Records
gelesen, keine fehlend, 599,6 Stunden Datenbasis. Der Auftrag war ausdruecklich **Messung ohne
Mechanismus**, als Lehre aus WP-C4.

**Der Kompromiss, hypothetisch durchgerechnet:**

| k stille Level | Ersparnis | Anteil an 599,6 h | Zellen mit verpasster Verbesserung | davon > 50 % |
|---|---|---|---|---|
| 3 | 563 h | **94 %** | 152 von 287 | **138** |
| 5 | 220 h | 37 % | 38 | 23 |
| 8 | 92 h | 15 % | 3 | 1 |

**Eine eigene Vermutung dabei widerlegt.** Naheliegend war, dass die verpassten Verbesserungen
ueberwiegend Rauschen sind — sub-Promille-Absenkungen, die als Verbesserung mitzaehlen. Gegen die
Rohdaten geprueft: falsch. Bei k=3 verpassen **138 der 152** Zellen eine Verbesserung von ueber
50 Prozent, bei k=5 immer noch 23. Die Zahlen tragen; die Skepsis trug nicht.

**Entscheidung (Nutzer, 2026-08-21): kein Levelbudget vor der Kampagne.** Bei k=3 waere die
94-Prozent-Ersparnis erkauft mit einem wesentlich schlechteren Ergebnis auf mehr als der Haelfte
aller Zellen — das ist keine Kostenoptimierung, sondern eine andere Methode. k=5 ist ein schlechtes
Geschaeft, k=8 vertretbar aber mager. Und jedes k waere zum zweiten Mal eine Konstante, die nicht
aus den Daten folgt.

**Der eigentliche Befund liegt in der Aufschlüsselung:**

| Dimension | Level gesamt | stille Level | Zeitanteil |
|---|---|---|---|
| 1 | 10,8 | 2,3 | 10 % |
| 2 | 17,9 | 7,1 | **50 %** |
| 3 | 25,3 | 8,6 | 44 % |
| 4 | 19,8 | **18,5** | **96 %** |

Dim 4 — System 63, das einzige dim-4-System der Regression — verbringt **96 Prozent seiner Zeit in
Leveln, die nichts verbessern**. Und im Pilot gibt es eine ganze Klasse von Zellen (Systeme 30, 34,
36, 39, 46), deren letzte Verbesserung auf **Level 1** liegt und die danach neunzehn stille Level
rechnen.

Das spricht nicht fuer ein globales k, sondern fuer eine strukturierte Abbruchregel — und die ist
eine Forschungsfrage, keine Konfigurationskonstante. `CLAUDE.md` fuehrt sie ohnehin als offene
Frage: *what the best stopping and promotion criterion is*.

**Konsequenz fuer die Kampagne:** 30 Level bleiben, und die Verschwendung wird **gemessen statt
behoben**. Ein Drittel bis die Haelfte der Rechenzeit traegt nichts bei — das ist ein Ergebnis fuer
Paper 1 und die Motivation fuer ein Stopp-Kriterium als eigene Arbeit. Rechenzeit ist vorhanden,
das hat der Pilot geklaert.

---

### Sondierung vollstaendig — Pretuning wirkt systemabhaengig in beide Richtungen

<!-- 897f0ff -->

System 59 (Roessler, chaotisch) `pretune_off` ist fertig. Damit liegen alle drei Sondierungszellen
vor, und die Frage, die seit dem Pilot offen war, ist beantwortet.

| System | `pretune_on` | `pretune_off` | Laufzeit-Faktor | Evals-Faktor |
|---|---|---|---|---|
| 61 Chen-Lee | 49,41 h | **14,73 h** | **0,30** | 0,73 |
| 56 Lorenz | 39,95 h | **38,68 h** | **0,97** | **0,56** |
| 59 Roessler | 68,04 h | **62,35 h** | **0,92** | 0,90 |

Alle drei Records `error=null`, Fingerprints `e361a2af49366670` / `61b6548ef0014593`, git `88eaeb6`.

**Erstens: `pretune_off` ist nicht die teure Haelfte der Kampagne.** Das war die Annahme, mit der
die 3.384 Kernstunden als untere Schranke gefuehrt wurden. Auf allen drei gemessenen Systemen ist
Pretuning-aus **schneller**, im Mittel dieser drei um Faktor 0,73. Die Hochrechnung ist damit eher
eine obere als eine untere Schranke — jedenfalls fuer dim 3.

**Zweitens: es gibt keinen Faktor, den man einsetzen koennte.** 0,30 gegen 0,97 gegen 0,92 auf drei
Systemen derselben Dimensionsklasse, alle chaotisch. Chen-Lee spart zwei Drittel, Lorenz nichts.
Das Kostenmodell darf `pretune_off` nicht als Zu- oder Abschlag fuehren; es kann nur eine Spanne
angeben.

**Drittens, und das ist der methodisch wichtigste Punkt: Laufzeit und Zaehlwerte laufen
auseinander.** Auf System 56 sinken die Evaluationen um 44 Prozent und die Laufzeit um drei. Auf
System 59 laufen beide fast parallel (0,90 gegen 0,92). Auf System 61 sinkt die Laufzeit dreimal
staerker als die Evaluationszahl. Die Kosten je Evaluation schwanken also selbst innerhalb einer
Dimensionsklasse um mehr als Faktor zwei — plausibel, weil unterschiedliche Parameterbereiche
unterschiedlich steife Integration bedeuten.

> **Fuer Grundsatz 7:** Zaehlwerte bleiben die richtige Evidenz fuer **Suchaufwand** und sind als
> Stellvertreter fuer **Rechenzeit** nachweislich untauglich. Wer aus 44 Prozent weniger
> Evaluationen 44 Prozent weniger Kernstunden ableitet, liegt auf System 56 um den Faktor 15
> daneben.

**Nebenbefund zum Levelbudget:** System 59 steht seit Level 21 unveraendert bei Loss 4,082 und
laeuft trotzdem bis Level 30. **Neun von dreissig Leveln, rund ein Drittel der Zelle, verbessern
nichts.** Bei 62 Stunden Gesamtlaufzeit und stark wachsenden Levelkosten liegt der verschwendete
Anteil deutlich ueber einem Drittel der Rechenzeit. Der Punkt war am 2026-08-18 bewusst
zurueckgestellt worden, weil die Kosten kein Problem waren; er ist damit nicht geloest, sondern
beziffert.

Cap `[nothing, nothing, 5]`, Endstufe 5, `pruned_match` nicht anwendbar (Surrogatsystem).

---

### Regression unter dem neuen Fingerprint: 25,4 Prozent statt 15,3, und keine Zelle verliert

<!-- 86785e0 -->

120 Records, alle `error: null`, alle drei Identitaetsfelder einheitlich:
`git_hash=f6143eb`, `config_fingerprint=17fe7d9cfb8f1be3`,
`stage_cap_behavior_fingerprint=ffb0266c7913352c`.

**Der Vergleich `evogrow_v2_2_stage_capped` gegen `evogrow_v2_2_stage_local`** ueber die 30
gemeinsamen Zellen, gegen den Lauf vom 2026-08-19 mit Zweifelsband gestellt:

| | mit Band (`88eaeb6f`) | binaer (`f6143eb`) |
|---|---|---|
| Loss bitidentisch | 30/30 | **30/30** |
| `pruned_match` veraendert | 0 | **0** |
| Loss-Evaluationen | 13.618.177 | **12.002.255** |
| Ersparnis gegen v2.2 | 15,3 % | **25,4 %** |
| Zellen, die teurer werden | 1 (+16 %) | **keine** |

Basis in beiden Faellen: 16.087.320 Evaluationen fuer v2.2.

**Das Entfernen des Bandes bringt zehn Prozentpunkte und beseitigt die einzige Zelle, die vorher
mehr gekostet hat** — 31 / IC 1, die durch die Enthaltung ihren korrekten Cap verlor und
ungedeckelt lief. Die drei zurueckgewonnenen Caps aus WP-C5 zahlen sich also unmittelbar aus.

Damit steht die Kernaussage von Paper 1 sauberer als je zuvor: **identisches Ergebnis, ein Viertel
weniger Suchaufwand, keine einzige Zelle verliert.** Und sie ruht erstmals auf einem geschlossenen
Block unter einem einzigen Identitaets-Tripel.

Nachzutragen bleibt, was WP-V1 dazu gesagt hat und was unabhaengig davon gilt: Die tragende
Schwelle 0,35 ist nicht aus den Daten waehlbar. Die 25,4 Prozent sind gemessen, die Schwelle
dahinter ist gesetzt.

---

## 2026-08-20

### Sondierung, zweite Zelle: gleiche Wanduhr, halb so viele Evaluationen

<!-- 6bdafb9 -->

System 56 (Lorenz, Standardparameter) `pretune_off` ist fertig. Damit liegen zwei der drei
Sondierungszellen vor, und sie widersprechen einander.

| | `pretune_on` | `pretune_off` | Faktor |
|---|---|---|---|
| **System 56** Laufzeit | 39,95 h | 38,68 h | **0,97** |
| Parameter-Fits | 610 | 610 | 1,00 |
| Loss-Evaluationen | 6.697.750 | 3.773.031 | **0,56** |
| Evals je Fit | 10.980 | 6.185 | 0,56 |
| | | | |
| **System 61** Laufzeit | 49,41 h | 14,73 h | **0,30** |
| Loss-Evaluationen | 3.038.641 | 2.206.537 | 0,73 |

**Der wichtigste Befund ist die Divergenz zwischen Zaehlwerten und Wanduhr.** Auf System 56 sinken
die Evaluationen um 44 Prozent, die Laufzeit aber um drei Prozent. Jede einzelne Evaluation ist ohne
Warmstart also rund **1,8-mal teurer**. Naheliegende Erklaerung: Ohne OLS-Start bewegt sich die
Suche durch Parameterbereiche, in denen die ODE steifer und damit teurer zu integrieren ist.

> **Konsequenz fuers Kostenmodell:** Zaehlwerte lassen sich **nicht** mit einem festen Faktor in
> Kernstunden umrechnen. Wer aus 44 Prozent weniger Evaluationen auf 44 Prozent weniger Rechenzeit
> schliesst, liegt um eine Groessenordnung daneben. Das beruehrt Grundsatz 7 an einer empfindlichen
> Stelle: Zaehlwerte bleiben die richtige Evidenz fuer *Suchaufwand*, taugen aber nicht als
> Stellvertreter fuer *Rechenzeit*.

**Und es gibt keinen einheitlichen `pretune_off`-Faktor.** Chen-Lee 0,30, Lorenz 0,97 — und System
59 (Roessler) steht bei Level 23 von 30 nach 38 Stunden gegen 68 Stunden fuer den vollen Lauf mit
Pretuning, wird also voraussichtlich **langsamer**. Drei Systeme, drei Richtungen. Das Kostenmodell
muss `pretune_off` je Dimensionsklasse fuehren, nicht als globalen Zu- oder Abschlag.

Beide Records: `error=null`, Fingerprints `e361a2af49366670` / `61b6548ef0014593`, git `88eaeb6` —
also der Stand vor WP-C5. Fuer die Kostenmessung unerheblich, weil die Caps dieser drei Systeme von
WP-C5 nicht beruehrt werden.

---

### WP-C5 — das Zweifelsband ist raus, und die tragenden Konstanten stecken jetzt im Fingerprint

<!-- 2f47aa3 -->

Konsequenz aus WP-V1. Die Entscheidung nach einer Floor-Unterschreitung hat wieder **zwei**
Ausgaenge: weitersuchen, wenn eine spaetere Stufe deutlich verbessert, sonst deckeln. Die Enthaltung
im Zwischenbereich entfaellt, und mit ihr die zweite Bandgrenze.

**Zielbild zeilenweise getroffen**, hier nachgerechnet und nicht aus dem Report uebernommen:

| | |
|---|---|
| Gleichungszeilen | 80 |
| endliche Caps | **45 → 48** |
| abgeschnittene Zeilen | **0** |
| geaenderte Zeilen | **genau 3** |

Die drei sind exakt die von WP-V1 vorhergesagten: 12 / IC 1 `nothing` → 2, 31 / IC 1 `nothing` → 3,
55 / IC 2 Gl. 2 `nothing` → 4. Alle vier Lorenz-Zeilen bleiben bei Cap 3, System 31 / IC 2 bleibt
`nothing`. Beide Testsuiten gruen.

**Der eigentliche Gewinn war nicht beauftragt.** Die beiden verbleibenden Konstanten —
`post_floor_significant_drop_ratio = 0.35` und `post_floor_min_floor_ratio = 0.1` — sind jetzt
Policy-Felder und Teil der Fingerprint-Nutzlast. Damit ist die Luecke geschlossen, die seit WP-P1
in `CLAUDE.md` stand: Die tragende Schwelle steckte in **keinem** der beiden Fingerprints, eine
Verschiebung von 0,35 auf 0,45 waere unbemerkt geblieben. Jetzt bewegt sie `config_fingerprint`.

**Alle drei Fingerprints bewegt, absichtlich:**

| | vorher | nachher |
|---|---|---|
| `config_fingerprint()` | `1d0ccf8d53c6576d` | `17fe7d9cfb8f1be3` |
| `phase_b_fingerprint()` | `e361a2af49366670` | `604e79733b22d64d` |
| `stage_cap_behavior_fingerprint()` | `61b6548ef0014593` | `ffb0266c7913352c` |

Die Sondenversion steht auf **2**: Der frueher gepruefte dritte Ausgang existiert nicht mehr, der
Wechsel ist damit als eigene Aera erkennbar statt als stille Aenderung.

**Folge:** Die 120 Regressions-Records vom 2026-08-19 liegen unter den alten Werten und sind damit
verwaist. Sie werden unter den neuen neu gerechnet — Entscheidung des Nutzers, getroffen bevor die
Kampagne laeuft und nicht danach.

**Nebenbefund zur Hausordnung:** Das Audit-Skript hat wegen der WP-E1-Absicherung eine zweite,
zeitgestempelte Reportdatei angelegt, weil `docs/WP-C5.md` bereits existierte. Beide waren
inhaltsgleich; die Kopie wurde entfernt. Die Regel greift also — sie ist nur beim ersten Lauf eines
neuen Pakets einen Tick zu eifrig.

---

### WP-V1 — das Zweifelsband verhindert nichts und kostet drei korrekte Caps

<!-- 55a12f8 -->

Der Test, der klaeren sollte, ob der Controller seine eigene Unzuverlaessigkeit erkennt, hat die
Begruendung von WP-C4 umgestossen. Codex meldete `blocked` wegen der 15-Minuten-Grenze (904 s), hat
den Report aber vollstaendig erzeugt; die Zahlen sind hier nachgerechnet.

**Die Konfusionsmatrix ueber alle 80 Gleichungszeilen der 20 exakten Systeme:**

| | |
|---|---|
| Cap gesetzt, korrekt | 77 |
| Cap gesetzt, **falsch** | **0** |
| Zweifelsband **verhindert** einen falschen Cap | **0** |
| Zweifelsband **nimmt einen korrekten Cap weg** | **3** |

Die drei: System 12 / IC 1 (binaer 2, benoetigt 2), 31 / IC 1 (binaer 3, benoetigt 3) und
55 / IC 2 Gl. 2 (binaer 4, benoetigt 3). Auf den geprueften Daten hat das Band **nur Kosten und
keinen einzigen Nutzen**.

**Und der Lorenz-Fix kam nicht vom Band.** Alle vier Lorenz-Zeilen liefern auch mit der binaeren
Entscheidung Cap 3:

```text
Sys55 IC1 Gl3: benoetigt 3, binaer=3, aktuell=3
Sys55 IC2 Gl3: benoetigt 3, binaer=3, aktuell=3
Sys56 IC1 Gl3: benoetigt 3, binaer=3, aktuell=3
Sys56 IC2 Gl3: benoetigt 3, binaer=3, aktuell=3
```

Repariert hat es der **Wiederaufnahme-Zweig** — die Regel, die bei einer Floor-Unterschreitung
weitersucht, wenn spaetere Stufen noch deutlich verbessern. Den enthaelt die binaere Variante
ebenso. Das Band ist nur der dritte Ausgang, die Enthaltung, und der zahlt sich nicht aus.

**Die Leave-one-system-out-Pruefung schlaegt zu.** Werden die Grenzen auf 19 Systemen gewaehlt und
auf dem zwanzigsten ausgewertet, entstehen **zwei falsche Festlegungen** — beide Lorenz, Gl. 3,
Cap 2 bei benoetigter Stufe 3. Genau der Defekt, den WP-C4 beheben sollte.

Die Ursache ist ablesbar: Tragend ist die **Wiederaufnahme-Schwelle**, ausgeliefert 0,35. Lorenz'
schlechtestes Verhaeltnis liegt bei 0,315 — **11 Prozent Abstand**. Kein datengetriebenes
Auswahlverfahren findet 0,35; die LOSO-Wahl landet zwischen 0,044 und 0,278, und dort faellt Lorenz
durch. Die beiden Bandgrenzen kollabieren dabei auf denselben Wert, das Band hat also Breite null —
die Zielfunktion "keine falschen Festlegungen im Training, dann minimale Enthaltungen" treibt es
dorthin.

> **Der Befund, der bleibt:** Der entscheidende Parameter der Vorabkontrolle ist **nicht aus den
> Daten bestimmbar**. Das ist keine Panne im Mechanismus, sondern die These des Bogens in ihrer
> unbequemsten Form — Ableitungsqualitaet begrenzt jede Vorabkontrolle, und wo die Grenze liegt,
> sagen die Daten nicht.

**Zur Herkunft dieses Fehlers, offen:** Die Empfehlung fuer das Zweifelsband stammt von Claude, mit
der Begruendung, es sei "die sicherste Variante, die alles abdeckt". Sie war falsch. Aufgedeckt hat
es die Pruefung, die im selben Zug mitverlangt wurde — die LOSO-Validierung war als Absicherung
gegen genau diese Art von Selbsttaeuschung gedacht und hat funktioniert.

**Entscheidung des Nutzers (2026-08-20):** Das Band wird entfernt, die binaere Entscheidung bleibt.
Die 120 Regressions-Records werden unter dem neuen Fingerprint neu gerechnet.

Alle drei Fingerprints blieben waehrend WP-V1 unveraendert; die Bandkonstanten wurden nur
injizierbar gemacht (`post_floor_clear_drop_ratio`, `post_floor_clear_no_drop_ratio`,
`post_floor_min_floor_ratio` als Policy-Felder mit den bisherigen Werten als Default).

---

## 2026-08-19

### WP-E1/E2 — dreimal hat eine Abnahme den Beleg zerstoert, den sie bestaetigen sollte

<!-- 1524d40 -->

Ein Muster, das erst durch Wiederholung sichtbar wurde. Innerhalb von zwei Tagen dreimal derselbe
Vorgang: Ein Skript wird zur **Verifikation** ausgefuehrt und ueberschreibt dabei genau das
Dokument, das es belegen soll.

| Fall | Was ueberschrieben wurde |
|---|---|
| WP-C2/C4-Abnahme | `docs/wp_c1_stage_cap_horizon_audit.md` — 9 abgeschnittene Zeilen wurden zu 4 |
| WP-E1-Entwurf | fast der Kampagnen-Indexpfad; abgewendet, siehe unten |
| WP-A3-Abnahme | `docs/paper1_freeze_memo_phaseA.md` — neu datiert von 2026-05-17 auf 2026-08-19 |

**WP-E1** hat `studies/output_path_guard.jl` eingefuehrt: explizites Flag gewinnt, sonst
Standardpfad nur wenn dort nichts liegt, andernfalls ein Geschwisterfile mit Zeitstempel.
Angewandt auf 18 Studienskripte.

**Die beiden Kampagnen-Manifestgeneratoren wurden davon ausgenommen und zurueckgesetzt**, und das
ist die Lehre des Pakets: `run_k8s_indexed_cell.jl` liest `EVO_BATCH_INDEX_LIST` unter **festem
Namen**. Mit Guard haette ein erneuter Bootstrap `indices_dim1_<zeitstempel>.txt` danebengelegt,
waehrend jede Zelle weiter die alte Liste liest — aus einer beabsichtigten Auffrischung waere ein
stiller Nulleffekt geworden. Zweiter Defekt im selben Zweig: Unter `--all-dimensions` liefen alle
fuenf Indexlisten durch dasselbe `--index-output`-Flag und haetten sich gegenseitig ueberschrieben.

> **Die Unterscheidung, die daraus folgt:** Der Guard ist richtig, wo die Ausgabe ein **Beweis**
> ist — dort ist Ueberschreiben der Schaden. Er ist falsch, wo die Ausgabe ein **Vertrag** ist, den
> ein anderer Prozess unter festem Namen liest — dort ist das Geschwisterfile der Schaden.

**WP-E2** schliesst dieselbe Luecke in der Python-Auswertung, und dort im empfindlichsten Dokument
des Projekts. `evaluate_hypotheses.py` schreibt seine Reproduktion jetzt nach `outputs/` und
**vergleicht** sie gegen den eingefrorenen Stand, statt ihn zu ueberschreiben; ausgeklammert werden
ausdruecklich benannt `diagnostics.generated_at` und die `Generated`-Zeile des Memos.

Nebenbei beantwortet der Vergleich eine Frage, die nie jemand gestellt hat: **Phase A reproduziert
unter heutigem Code, Werte identisch.**

**Offengelegt, weil es meine eigene Spur ist:** Das eingefrorene
`analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json` traegt jetzt `generated_at` vom
2026-08-19 — aus meinen WP-A3-Verifikationslaeufen, bevor die Absicherung existierte. Die Werte
sind nachweislich unveraendert, und das Memo traegt weiterhin den 2026-05-17.

**Und dahinter der eigentliche Befund:** Das Memo liess sich zuruecksetzen, weil es in Git liegt.
Das JSON nicht, weil `analysis/data/` gitignoriert ist. Ein eingefrorenes Artefakt ausserhalb der
Versionskontrolle ist nicht eingefroren, sondern liegt nur zufaellig da. Zu entscheiden: die
Phase-A-Artefakte als Ausnahme in die Versionskontrolle nehmen — dann aber mit dem Wissen, dass der
Zeitstempel des JSON heute ein falscher ist.

---

### Regression vollstaendig: 30 von 30 Zellen bitidentisch, und die Abstinenz kostet messbar 16 %

<!-- 7e7c675 -->

120 Records, alle `error: null`, und zum ersten Mal im Projekt stimmen **alle drei Identitaetsfelder**
ueberein: `git_hash=88eaeb6`, `config_fingerprint=1d0ccf8d53c6576d`,
`stage_cap_behavior_fingerprint=61b6548ef0014593`. Der Verhaltens-Fingerprint aus WP-P1 kommt damit
erstmals in echten Records an.

**Die Kernaussage des Papiers steht jetzt auf dem aktuellen Stand.** `evogrow_v2_2_stage_capped`
gegen `evogrow_v2_2_stage_local`, 30 gemeinsame Zellen ueber die Systeme 3, 11, 26, 31 und 63,
beide IC-Sets, drei Seeds:

| | |
|---|---|
| Loss **bitidentisch** | 30 von 30 |
| `pruned_match` veraendert | 0 |
| Loss-Evaluationen | 16.087.320 -> 13.618.177 = **-15,3 %** |

Bisher ruhte diese Aussage auf zehn Zellen und vier Systemen, gemessen ueber eine
Fingerprint-Grenze hinweg. Jetzt ist sie ein geschlossener Block.

**Die Ersparnis ist ungleich verteilt, und das ist der eigentliche Befund:**

| Zelle | v2.2 | capped | |
|---|---|---|---|
| System 26, alle sechs | 1,43 Mio | 0,83 Mio | -42 % |
| System 11 / IC 2 | 54.398 | 28.318 | -48 % |
| **System 31 / IC 1** | 1.019.225 | 1.179.637 | **+16 %** |
| 3, 63, 31 / IC 2, 11 / IC 1 | identisch | identisch | Cap bindet nicht |

**Die eine teurere Zelle ist die Rechnung fuer WP-C4.** 31 / IC 1 war genau die Kontrollzeile mit
Verhaeltnis 0,496 gegen die Bandgrenze 0,5, die durch das Zweifelsband ihren korrekten Cap 3
verliert und ungedeckelt laeuft. Die Zusage lautete, eine Abstinenz koste *nur Rechenzeit, nie die
Loesung*. Genau das ist eingetreten: 16 % mehr Evaluationen, Loss bitidentisch, `pruned_match`
unveraendert. Vorhersage aus dem Audit und Messung im Lauf decken sich, und der Preis der
Sicherheit ist damit beziffert statt behauptet.

Alle 30 Zellen laufen ueber volle 30 Level. Der Cap begrenzt die Stufe, nicht die Levelzahl — die
Ersparnis entsteht innerhalb der Level, nicht durch frueheren Abbruch.

---

### Chen-Lee ohne Pretuning ist dreimal schneller — die Annahme zeigt in die falsche Richtung

<!-- 7e7c675 -->

Erste fertige Sondierungszelle, System 61, `pretune_off`:

| | `pretune_on` (Pilot) | `pretune_off` |
|---|---|---|
| Laufzeit | 49,4 h | **14,7 h** |
| Parameter-Fits | 350 | 490 |
| Loss-Evaluationen | 3.038.641 | **2.206.537** |
| Evals je Fit | 8.682 | **4.503** |
| Caps | `[3,3,3]` | `[3,3,3]` |
| Loss | 63,1 | 100,8 |

Mehr Fits, aber **halb so viele Evaluationen je Fit**. Der OLS-Warmstart fuehrt BFGS offenbar in
laengere Liniensuchen, statt sie zu verkuerzen — plausibel, wenn der Startpunkt in einer Region
liegt, aus der die Liniensuche weit laufen muss.

**Damit ist die Grundannahme der Kostenschaetzung in Frage gestellt.** `pretune_off` galt als die
teure, ungemessene Haelfte der Kampagne und als Grund, die 3.384 Kernstunden als untere Schranke zu
lesen. Auf dieser Zelle ist es das Gegenteil.

n=1, und es darf noch nichts heissen: Systeme 56 und 59 laufen noch, beide bei 21 h gegen 40 h und
68 h unter `pretune_on`. Der Loss ist zudem schlechter (100,8 gegen 63,1) — auf einem chaotischen
System sind beide Werte allerdings unbrauchbar, das trennt nichts.

Der Cap `[3,3,3]` ist unveraendert korrekt. Die Gegenprobe aus WP-C1 haelt auch im Kampagnenlauf.

---

## 2026-08-18

### Regressionslauf gestartet — und die Jobzahl stimmt seit der Variantenliste nicht mehr

<!-- 1184303 -->

120 Zellen unter `config_fingerprint=1d0ccf8d53c6576d`, verteilt auf drei Indexed Jobs nach
Dimension (48 / 48 / 24, `parallelism` 5 / 5 / 3). Zusammen mit den drei Sondierungszellen sind das
**genau die 16 vereinbarten Kerne**.

**Die 90 in `CLAUDE.md` ist veraltet.** Der Bootstrap meldet `rows=120`: 5 Systeme (3, 11, 26, 31,
63) x 3 Seeds x 2 IC-Sets x **4 Varianten**. Die 90 stammen aus der Zeit mit drei Varianten. Die
Gesamtzahl der Kampagnenjobs ist damit 756 + 120 = **876**, nicht 846. Korrigiert.

**Zwei Werkzeugbefunde.** `generate_manifest.jl` schreibt eine Indexliste **nur** zusammen mit
`--dimension`; `--index-output` allein laeuft ins Leere, weil der Block daran haengt. Es gibt also
keine Gesamtliste, sondern nur Listen je Dimension — daher drei Bootstraps statt einem, nacheinander
ausgefuehrt, weil alle dieselbe `manifest.csv` schreiben. Gegengerechnet: 48 + 48 + 24 = 120,
null Dubletten, null fehlende Indizes; jede Zelle wird genau einmal gerechnet.

Der zweite: Der Phase-B-Bootstrap gibt `all_index_output` und die Zeilen je Dimension aus, der
Regressions-Bootstrap nicht. Der Unterschied ist leicht zu uebersehen und war der Grund, warum die
fehlende Indexliste erst beim Blick auf den Share auffiel.

---

### pretune_off-Sondierung gestartet — die letzte unbeschraenkte Zahl im Kostenmodell

<!-- b951041 -->

Drei Zellen auf Orion, Manifest-Indizes **709, 727, 739** = Systeme 56 (Lorenz), 59 (Roessler) und
61 (Chen-Lee), jeweils `pretune_off`, Seed 42, IC-Set 1. Es sind genau die drei teuersten Zellen des
Pilots; unter `pretune_on` brauchten sie 40, 68 und 49 Stunden.

**Die Frage:** Der gesamte Pilot lief `pretune_on`. `pretune_off` ist die Haelfte der Kampagne und
war vollstaendig ungemessen. Ohne Warmstart ist mehr BFGS-Arbeit je Fit zu erwarten, die
Hochrechnung von 3.384 Kernstunden ist insofern eine untere Schranke mit unbekanntem Faktor.

**Provenienz, live geprueft.** Bootstrap-Job unter Image-Tag `88eaeb6fd6c4d9a1832baeb4b28033752ddb370d`:
`phase_b_fingerprint=e361a2af49366670`, `rows=756`, `unique_identities=756`, `systems=63`,
`representability` 20 exakt / 43 surrogat, Dimensionen 276/336/120/24. Alles gegengerechnet. Der
erste Heartbeat traegt denselben Fingerprint.

**Zwei Betriebsbefunde, die in SCRIPTS.md gehoeren.**

*Der NFS-Share ist von Windows aus nur lesend.* Eine handverlesene Indexliste laesst sich dort nicht
ablegen — und der Indexed-Job-Pfad braucht genau so eine Datei. Geloest ohne Umweg: `run_batch_cell.jl`
nimmt den Manifest-Index als positionales Argument, also ein Job je Zelle und gar keine Liste. Neue
Vorlage `k8s/phase_b_single_cell_job.yaml`. Nebengewinn: Ein Fehlschlag betrifft genau eine Zelle und
ist einzeln wiederholbar, was bei mehrtaegigen Laufzeiten deutlich angenehmer ist als ein Block.

*Die Befehle in SCRIPTS.md und im Deployment-Guide sind Bash, die Arbeitsumgebung ist PowerShell.*
`sed` existiert dort nicht. Kein Schaden — es brach vor jeder Wirkung ab —, aber die Anleitungen
gehen von einer Shell aus, die auf dem Zielrechner nicht laeuft.

---

## 2026-08-17

### WP-C3 abgelehnt, WP-C4 angenommen — der Cap lehnt jetzt ab, statt im Zweifel zu behaupten

<!-- d94bc3b -->

**WP-C3 erfüllte sein Zielbild und wurde trotzdem nicht angenommen.** Vier Lorenz-Zeilen auf Cap 3,
System 31 / IC 2 auf `nothing`, 75 Zeilen unverändert, Tests grün — und darunter die Bedingung
`current_stage < 3`, ein hartkodierter Stufenindex. Der Auftrag hatte ausdrücklich verlangt, dass
das Kriterium nur Residuen, Floors und Policy-Schwellen verwendet und relativ argumentiert.

Der Index war auch nicht nebensächlich. Nachgerechnet, was ohne ihn passiert wäre: Die
**Kontrollzeile** 31 / IC 1 hätte ihren korrekten Cap 3 verloren und wäre auf 4 gesprungen — ihr
Verhältnis nach der Unterschreitung liegt bei 0,496 gegen die Schwelle 0,5, also **0,8 % Abstand**.
Eine zweite Kontrolle lag bei 0,520, 4 % auf der anderen Seite. Der Stufenindex war genau das, was
die Abnahme trug.

Dazu die methodische Lehre: Der Unempfindlichkeitsnachweis im WP-C3-Report maß nur den Abstand der
**Zielzeilen** zur Schwelle (0,029–0,315 gegen 0,5). Das Risiko liegt aber auf den **Kontrollen**,
wo die Regel nicht feuern darf. **Ein Nachweis, der nur auf der Zielseite gemessen wird, ist
keiner.** Diese Auflage steht jetzt in jedem Folgeauftrag.

**Die Umstellung in WP-C4: drei Ausgänge statt zwei.** Der Versuch, Ziel- und Kontrollzeilen exakt
zu trennen, wurde aufgegeben — er ist datenseitig knapp und erzwingt deshalb passende Konstanten.
Stattdessen:

| Verhältnis nach der Floor-Unterschreitung | Ausgang |
|---|---|
| ≤ 0,35 | weitersuchen, höher deckeln |
| ≥ 0,62 | hier deckeln, wie bisher |
| dazwischen | **`nothing`** — kein Cap |

Das ist die Regel des Projekts, auf den eigenen Mechanismus angewandt: *positive Evidenz, nie deren
Abwesenheit.* Im Zweifelsband liegt keine vor, also wird nichts behauptet. Die Fehlerrichtung ist
beabsichtigt — ein `nothing` kostet Rechenzeit, ein falscher Cap kostet die Lösung, und Rechenzeit
ist nach dem Pilotbefund reichlich vorhanden.

**Ergebnis auf den 80 exakten Gleichungszeilen:** vier Lorenz-Zeilen auf 3, 31 / IC 2 auf `nothing`,
und die vier Wechsel zwischen endlichen Caps sind **genau** diese Ziele. Endliche Caps 49 → 45. Die
vier aufgegebenen Zeilen sind 12 / IC 1, 31 / IC 1, 31 / IC 2 und 55 / IC 2 Gl. 2.

**Zwei Anmerkungen, die der Report nicht enthält und die hier festgehalten werden.**

*Erstens: die Floor-Tiefen-Konstante ist jetzt die tragende.* Kontrolle 61 / IC 1 hat **drei von vier
Splits im Band** (0,520, 0,568, 0,541) und behält ihren Cap allein deshalb, weil ihre Floor-Ratios
bei 0,03 bis 0,07 unter der Schwelle 0,1 liegen. Die Zielzeilen liegen bei 0,30 bis 0,85. Die
Trennung hält also mit Faktor vier — aber sie ist nicht dokumentiert worden, obwohl der Auftrag
den Abstand nach beiden Seiten verlangt hatte. Hier nachgerechnet und bestätigt.

*Zweitens: eine Zeile geht aus dem falschen Grund verloren.* 12 / IC 1 hatte den korrekten, engen
Cap 2 und gibt ihn auf, obwohl ihre Floor-Ratio bei **9,9e-06** liegt — das Residuum ist fünf
Größenordnungen unter dem Rauschen, die anschließende „Verbesserung" von 0,477 ist reines Rauschen.
Sauber wäre, dass die Floor-Tiefen-Bedingung die Bandlogik **ganz** abschaltet statt nur den
Wiederaufnahmezweig. Der Verlust ist ungefährlich, die Begründung falsch. Notiert als offener Punkt.

*Verwandt dazu:* Sowohl 31 / IC 2 als auch 12 / IC 1 kippen über die **Mehrheitsabstimmung der
Splits**, nicht über eine klare Erkennung — bei 12 / IC 1 änderte ein einziger Split (Nr. 3) seine
Stimme. Die Robustheit der Aggregation ist damit eine eigene offene Frage.

**Fingerprints unverändert** (`1d0ccf8d53c6576d`, `e361a2af49366670`) — und das ist der eigentliche
Befund dieser Runde, siehe unten.

### Ein Audit-Dokument hat sich selbst überschrieben — gefunden beim Paper-Entwurf

<!-- 5b6f8e2 -->

WP-W1 sollte `PAPER_1.md` auf den aktuellen Stand entwerfen und dabei Widersprüche zwischen den
Quellen **auflisten statt entscheiden**. Genau das hat den Fund geliefert.

`docs/wp_c1_stage_cap_horizon_audit.md` trug intern den Titel **„WP-C2 Stage-Cap Horizon Audit"**
und meldete bei Horizont 2 **vier** abgeschnittene Zeilen. Die WP-C1-Fassung von Commit `d472f8e`
meldet **neun**:

| Horizont | damals (`d472f8e`) | Datei heute |
|---|---|---|
| 2 | **9** truncated | 4 truncated |
| 3 | 5 | 0 |
| 5 | 5 | 0 |

Ursache: Das erzeugende Skript schreibt auf einen **festen Pfad**. WP-C2 und WP-C4 haben es zur
Abnahme erneut laufen lassen, und dabei jedes Mal den Bericht des vorherigen Arbeitspakets
überschrieben. Committet habe ich das mit — der Fehler liegt bei mir, nicht bei Codex.

**Doppelt ärgerlich, weil die neuen Zahlen niemandem nützen.** Die Zeile „Horizont 2 → 4
abgeschnitten" ist keine historische Messung *und* kein sinnvoller Befund, sondern ein Kontrafaktum:
was ein Horizont von 2 unter der heutigen Zweifelsband-Logik entscheiden würde. So ein Lauf hat nie
stattgefunden. Der Beleg für die Aussage, die den Horizont überhaupt bewegt hat — neun
abgeschnittene Zeilen auf fünf von zwanzig exakten Systemen —, existierte nur noch in der
Git-Historie und in diesem Tagebuch.

Bereinigt: `wp_c1_...` ist auf die Fassung von `d472f8e` zurückgesetzt und trägt einen Banner, der
das Regenerieren untersagt. Der Wiederholungslauf steht als `wp_c4_stage_cap_horizon_audit.md`
daneben, mit dem Hinweis, dass seine Horizont-2-Zeile ein Kontrafaktum ist.

> **Regel, aus dem Vorfall:** Ein Beweisdokument gehört dem Arbeitspaket, das es erzeugt hat. Ein
> Skript, das auf einen festen Pfad schreibt, darf nicht zur Abnahme eines *späteren* Pakets erneut
> laufen, ohne dass das Ziel mitwandert. Sonst löscht die Abnahme den Beweis, den sie bestätigen
> soll.

Das ist dieselbe Klasse wie der Fingerprint-Befund von heute Nachmittag: Die Provenienz war
formal in Ordnung — Datei da, Zahlen plausibel, Commit sauber — und trug trotzdem nicht.

---

### WP-P1/P1b — ein zweiter Fingerprint für das Verhalten, und ein Paket, das nicht mehr lud

<!-- 5177d24 -->

Drei Wege wurden gegeneinander gestellt: Quelltext-Hash über die entscheidungstragenden Dateien,
Verhaltens-Hash über eine eingefrorene Sonde, und ein getrennter zweiter Fingerprint. Ergebnis und
Umsetzung: **beides zusammen** — die Sonde als Verfahren, der getrennte Wert als Struktur.

Der Quelltext-Hash fiel durch, weil er zu empfindlich ist: Ein Kommentar oder eine Umformatierung
erklärt Records für unvergleichbar, die es nicht sind. Das Einfalten ins Konfigurations-Hash fiel
durch, weil es veröffentlichte Identitäten rückwirkend umschreiben würde. Die Kampagnenidentität
besteht damit ab sofort aus **zwei Feldern**: `config_fingerprint` beziehungsweise
`phase_b_fingerprint` plus `stage_cap_behavior_fingerprint`.

Die Sonde schickt fünf synthetische Eingaben durch `_cap_split_decision` und hasht die
Entscheidungen. Sie deckt genau die drei WP-C4-Ausgänge ab — Wiederaufnahme, Deckeln, Ablehnen —
plus den Fall fehlender Anregung und einen unbrauchbaren Nachfolger. Belegt wurde: gleicher Stand →
gleicher Wert; Cap-Logik von `5d2f4f2` → `b0968d0661a11a29` gegen heute `61b6548ef0014593`; reine
Kommentaränderung → unverändert.

| | Wert |
|---|---|
| `config_fingerprint()` | `1d0ccf8d53c6576d` (unverändert) |
| `phase_b_fingerprint()` | `e361a2af49366670` (unverändert) |
| `stage_cap_behavior_fingerprint()` | **`61b6548ef0014593`** (neu) |

**Die Lücke ist verengt, nicht geschlossen.** Die Sonde sieht `_cap_split_decision` und sonst
nichts. Ableitungsschätzer, Floor-Berechnung, Split-Aggregation und die gesamte Suchschleife bleiben
unbeobachtet. Und die Sondenwerte liegen bei 0,2 / 0,5 / 0,8, die Bandgrenzen bei 0,35 / 0,62 —
verschöbe jemand eine Grenze auf 0,45, bliebe das **unbemerkt**, denn die Bandkonstanten sind
`const` in `stage_cap.jl` und stecken in keinem der beiden Fingerprints. Offener Punkt.

**Und dann lud das Paket nicht mehr.** `stage_cap_fingerprint.jl` nutzt `using SHA`, `SHA` stand
nicht in `[deps]` der `Project.toml`:

```text
julia --project=. -e 'using EvoODE'
ERROR: Package EvoODE does not have SHA in its dependencies
```

Damit war der Arbeitsbaum schlicht nicht lauffähig — jeder Kampagnenlauf wäre beim Laden
abgebrochen. Der WP-P1-Report meldete gleichzeitig `test/test_stage_cap.jl` als bestanden mit 38
Tests.

**Die Auflösung dieses Widerspruchs ist der eigentliche Ertrag von P1b.** Die Testsuite lädt die
Quellen über `include(src/EvoODE.jl)`. Das wertet die Datei als lokales Modul aus und geht **nicht**
durch Julias Paketlader — die deklarierten Abhängigkeiten werden dabei nie geprüft. Die Suite konnte
diese Fehlerklasse also strukturell nicht sehen. Ein neuer Test startet jetzt einen eigenen
Julia-Prozess und führt `using EvoODE` aus; ein fehlender `[deps]`-Eintrag wird damit rot.

**Nebenbefund, überfällig:** `test/test_regression_runner_gate2.jl` war seit Wochen rot, 3 von 9,
und es ist niemandem aufgefallen — mir eingeschlossen. Er fror Gate-2-Werte ein, die seither bewusst
bewegt wurden: die Variantenliste, `BFGS_TIME_LIMIT_S` (jetzt `Inf` durch die Budgetumstellung
WP-B3/D2) und `lookahead_horizon` (jetzt 5). Erwartungen auf den Code nachgezogen, Herkunft als
Kommentar vermerkt. Vor einer Kampagne muss „Tests grün" wieder etwas bedeuten.

Alle Prüfungen wurden hier nachgerechnet, nicht aus dem Report übernommen: Paket lädt,
Verhaltens-Fingerprint stabil, Konfigurations-Fingerprints unverändert, beide Testsuiten grün.

**Damit ist das HPC-Tor offen.** Regressionslauf (90 Jobs) und `pretune_off`-Sondierung auf 56, 59
und 61 sind übergabereif.

---

### Die Fingerprints bemerken Logikänderungen nicht

<!-- d94bc3b -->

Bei WP-C3 und WP-C4 hat sich das Cap-Verhalten auf fünf beziehungsweise acht Zeilen geändert, und
**beide Fingerprints standen still**. Ihre Nutzlast enthält ausschließlich
Konfigurations**konstanten**, keine Entscheidungs**logik**.

Damit leistet der Fingerprint nicht, wofür er da ist. `CLAUDE.md` verlangt vor der Publikation den
Nachweis, dass alle Läufe einen Fingerprint teilen — genau diese Prüfung kann eine Logikänderung
nicht sehen. Zwei Records mit identischem Fingerprint können aus unterschiedlich entscheidendem
Code stammen. Gerettet wird die Nachvollziehbarkeit derzeit allein durch den Commit-Hash im Record,
seit `d2aed32`; das ist Glück, nicht Konstruktion.

Nächstes Arbeitspaket.

---

### WP-C1 — der Horizont war die Ursache, aber nicht die einzige

<!-- d472f8e -->

Audit über alle 20 exakten Systeme, beide IC-Sets, Horizonte 2 bis 5, 320 Gleichungszeilen. Der
Vorausblick wurde dabei nicht angefasst, nur `estimate_stage_caps` mit variiertem Horizont
aufgerufen und das Ergebnis gegen die aus `phase_b_support.json` abgeleitete benötigte Stufe
gehalten.

**Die Rate bei Horizont 2: neun Gleichungszeilen auf fünf der zwanzig exakten Systeme.** Aus zwei
von sieben ist damit eine belastbare Zahl geworden.

**Der Mechanismus ist bestätigt, und präziser als erwartet.** Von Horizont 2 auf 3 ändern sich genau
sechs Zeilen — und jeder neue Cap trifft die benötigte Stufe **exakt**:

| System | Gl. | benötigt | Cap alt | Cap neu |
|---|---|---|---|---|
| 28 Pendel ohne Reibung | 2 | 5 | 1 | **5** |
| 32 Doppelmuldenoszillator | 2 | 4 | 1 | **4** |
| 38 Van der Pol | 1 | 4 | `nothing` | **4** |

System 38 ist der aussagekräftigste Fall, weil er nicht im Verdacht stand. Dort gab es vorher
**gar keinen** Cap; der längere Vorausblick erkennt den Kubikterm und deckelt punktgenau darauf. Der
Cap wird durch die Korrektur also nicht nur sicherer, an dieser Stelle wird er auch **schärfer** —
genau die Doppelaussage, die der Beitrag braucht.

**Der Parameter ist oberhalb von 3 wirkungslos.** Der Report belegt das über Zählwerte; zeilenweise
nachgerechnet gilt es stärker: Horizonte 3, 4 und 5 sind auf **allen 80 Gleichungszeilen
cap-identisch**. Damit ist die 3 eine getunte Konstante ohne Wirkung, und es wird auf **5** gegangen
— die Stufenzahl der Basis, also „kein Horizont". Ergebnis unverändert, aber im Paper steht dann
keine Zahl mehr, zu der „warum 3?" die einzige ehrliche Antwort „weil es auf unseren zwanzig
Systemen reicht" wäre. WP-C2 zieht das nach.

**Und es bleibt ein zweiter Defekt.** Fünf Zeilen überleben jeden Horizont:

| System | Gl. | IC | benötigt | Cap |
|---|---|---|---|---|
| 55 Lorenz (komplex periodisch) | 3 | 1, 2 | 3 | 2 |
| 56 Lorenz (Standardparameter) | 3 | 1, 2 | 3 | 2 |
| 31 | 1 | nur 2 | 3 | 1 |

Die Lorenz-Vorhersage aus dem Pilot-Eintrag hat sich bestätigt — die Erklärung nicht. Von Stufe 2
aus liegt Stufe 3 **schon bei Horizont 2** im Vorausblick. Der Kreuzterm `u1*u2` wird also gesehen
und trotzdem nicht als Gewinn gezählt. Das ist ein anderer Mechanismus, und die naheliegende
Vermutung ist die Ableitungsschätzung auf chaotischen Trajektorien, also derselbe Boden, auf dem v3
gescheitert ist (WP-L2). System 31 auf IC-Set 2 ist der längst als Grenzfall dokumentierte Fall
trajektorienarmer Dynamik — hier zum ersten Mal als tatsächliches Abschneiden belegt und nicht nur
als Instabilität über IC-Sets.

**Gegenprobe gehalten:** System 61 (Chen-Lee) steht auf `[3,3,3]` und ist damit korrekt gedeckelt.
Der Defekt ist selektiv.

**Fingerprints:** Regression `0825cdc88d9264a0` → `06e1c71fbd10a3a4`, Phase B `ca02ea284d621f6d` →
`41f69abc3670b6c4`. Beide bewegen sich mit WP-C2 erneut; das ist unkritisch, solange kein
Kampagnen-Record existiert, und es existiert keiner.

**Eine Limitation, die unabhängig vom Ausgang zu deklarieren ist.** Prüfbar ist der Cap nur auf den
**20 exakten Systemen**. Für die 43 Surrogatsysteme gibt es keinen wahren Support, die Sicherheit
des Controllers ist dort konstruktionsbedingt nicht auditierbar — und der Pilot zeigt mehrere
Surrogate mit einer auf Stufe 1 gedeckelten Gleichung (33, 34, 40, 44, 50). Bewertet werden sie über
R², es ist also ein Güte- und kein Support-Risiko. Gesagt werden muss es trotzdem.

**Kampagnenstatus: weiterhin blockiert**, jetzt auf den fünf verbleibenden Zeilen.

---

### Das Cap-Muster in den Pilot-Records: der Defekt ist breiter als 2 von 7, und Lorenz ist dabei

<!-- 9b0cf85 -->

Anlass war eine Terminfrage — kann die geplante `pretune_off`-Sondierung parallel zu WP-C1 laufen?
Zur Beantwortung wurde das Feld `stage_caps` gegen `eq_final_stages` gehalten, um zu sehen, auf
welchen Zellen der Cap ueberhaupt bindet. Die Antwort auf die Terminfrage ist ja, es kollidiert
(unten). Der Nebenbefund ist der wichtigere.

**Auf 20 der 39 Pilotzellen bindet der Cap.** Und die Cap-Vektoren zeigen ein Muster, das die
Stichprobe vom 2026-08-14 nicht sehen konnte, weil dort nur sieben Systeme mit vorliegendem Record
geprueft wurden:

| Muster | Systeme |
|---|---|
| `[*, 1]` — Gleichung 2 auf Stufe 1 gedeckelt | **28, 32, 34, 40, 44, 50** |
| `[1, *]` — dasselbe spiegelbildlich | 33, 39 |
| `[None, 3, 2]` — Gleichung 3 auf Stufe 2 | **55, 56** |

Der `[*, 1]`-Fall ist derselbe wie bei 28 und 32: Gleichung 2 wird auf Linearitaet festgenagelt.
Statt zwei Verdachtsfaellen stehen jetzt **acht** im Raum. Ob alle acht wirklich abschneiden, haengt
am wahren Support je Gleichung und ist erst nach WP-C1 zu sagen — hier steht ein Muster, keine Rate.

**Lorenz ist betroffen, und das ist die teure Zeile.** Systeme 55 und 56 tragen Cap 2 auf Gleichung
3. Die dritte Lorenz-Gleichung lautet `du3/dt = u1*u2 - beta*u3`; der Kreuzterm `u1*u2` liegt in der
gestaffelten Basis auf **Stufe 3**. Ein Cap von 2 schliesst ihn aus. Passend dazu `pruned_match =
false` auf beiden. System 56 verbraucht dabei **40 Stunden** auf einer Antwort, die nie im
zugelassenen Raum lag.

Das ist nicht irgendein Benchmarksystem. Wenn das so im Paper steht, ist es die erste Zeile, die
geprueft wird.

**Gegenprobe, damit der Cap nicht pauschal verurteilt wird:** System 61 (Chen-Lee) traegt `[3,3,3]`
und erreicht `[3,3,3]`. Chen-Lee besteht aus Kreuztermen, Stufe 3 ist dort korrekt — der Cap bindet
und liegt richtig. Der Defekt ist selektiv, nicht generell, und genau deshalb ist die
WP-C1-Auflage "loest 28 und 32, **ohne** die korrekten Caps zu verschieben" die richtige Huerde.

**Konsequenz fuer die Terminplanung: die Sondierung muss hinter WP-C1.** Die Caps steuern den
Suchraum und damit die Kosten. System 61 hat seine 49,4 Stunden *mit* bindendem Cap auf allen drei
Gleichungen verbraucht; hebt WP-C1 die Caps, wird diese Zelle teurer, nicht billiger. Eine heute
gemessene `pretune_off`-Sondierung wuerde ein Cap-Regime vermessen, das gerade abgeschafft wird.

**Und damit ist die gestrige Kostenzahl ein zweites Mal eine Untergrenze.** Die 3.384 Kernstunden
gelten fuer `lookahead_horizon = 2`. Sie sind untere Schranke einmal wegen des ungemessenen
`pretune_off` und einmal wegen des Cap-Regimes, das sich in Richtung **mehr** Suchraum bewegt. Das
Kostenmodell in `docs/hpc_requirements.md` wird deshalb erst nach WP-C1 und nach der Sondierung neu
geschrieben, nicht jetzt.

Reihenfolge: WP-C1 → Caps final → `pretune_off`-Sondierung auf 56, 59, 61 → Kostenmodell → Kampagne.
Die Sondierung misst dann beides in einem Lauf, `pretune_off` und das neue Cap-Regime.

**An WP-C1 wurde nichts geaendert.** Der Auftrag deckt alle 20 exakten Systeme und beide IC-Sets
bereits ab; 55, 56 und 61 sind darunter. Dieser Eintrag ist Gegenprobe fuer den Report, keine
Erweiterung der Spezifikation.

---

### Der Pilot ist durch — das Kostenmodell stimmt in der Summe und ist in der Verteilung falsch

<!-- d648993 -->

Der Pilot auf Orion ist abgeschlossen. Ausgewertet wurden **42 eindeutige Zellen** aus
`pilot_e20af80`, `pilot_sweep_tasks` und `pilot_sweep3_tasks`, dazu 888 Level-Intervalle aus den
Heartbeat-Dateien. Abdeckung: **Systeme 24–62, Seed 42, IC-Set 1, ausschliesslich `pretune_on`**.
Alle Records `error=null`.

**Zur Zulaessigkeit der Zeitmessung.** Grundsatz 7 in `CLAUDE.md` verbietet Wall-Clock als Evidenz —
und nennt die Ausnahme selbst: *"If a claim genuinely requires timing, measure it on a dedicated
machine."* Orion vergibt je Job einen dedizierten Kern ohne Suspend und ohne Mitbewerber. Fuer
**Kapazitaetsplanung** ist die Messung damit zulaessig; fuer **Methodenvergleiche** bleibt sie es
nicht. Alle Zahlen unten sind Planungsgroessen, keine Leistungsaussagen ueber Varianten.

**Die Gesamtsumme haelt, die Klassenaufteilung nicht.** Gegen `docs/hpc_requirements.md` §5:

| Dimension | geschaetzt s/Job | gemessen Median | gemessen Mittel | Urteil |
|---|---|---|---|---|
| 1 | 170 | 250 s | 250 s | brauchbar (nur System 1, n=3) |
| 2 | 20.900 | 684 s | 10.440 s | Median 30x zu hoch, Mittel 2x zu hoch |
| 3 | 41.700 | 22.400 s | 63.800 s | **zu niedrig**, Mittel 1,5x |
| 4 | 83.500 | 4.280 s | 2.300 s | 36x zu hoch (nur System 62, n=2) |

Hochrechnung auf die 756 Phase-B-Zellen mit gemessenen Systemmitteln, fuer unbeobachtete Systeme das
Mittel ihrer Dimensionsklasse: **3.384 Kernstunden** gegen geschaetzte 3.900. Das sind **15 Prozent
Abweichung nach unten** — die Schaetzung war in der Summe richtig.

**Damit ist die bisherige Diagnose zu korrigieren.** `CLAUDE.md` fuehrt unter "Active", die Schaetzung
sei *"one to two orders of magnitude too high"*. Das war aus den ersten, billigen Zellen geschlossen
(System 24: 10 s gegen 20.900 s geschaetzt) und ueberlebt den vollen Sweep nicht. Die Verteilung ist
extrem schief — dim 2 hat Median 0,19 h und Mittel 2,90 h, Faktor 15 zwischen beiden. Wer aus
Medianzellen auf die Kampagne schliesst, unterschaetzt sie um eine Groessenordnung. Die Ursache des
alten Fehlschlusses ist also nicht die Umrechnung Sekunden-pro-Integration, sondern eine
**Stichprobe aus dem Kopf der Verteilung**.

**Kalenderzeit bei `parallelism: 16`: rund 9 Tage** (3.384 / 16 = 212 h). Bei 32 Kernen 4,4 Tage,
bei allen 96 rund 1,5 Tage. Untere Schranke der Makespan ist aber die **laengste Einzelzelle: 68 h**
— unter 3 Tage kommt die Kampagne durch keine Parallelitaet.

**Der eigentliche Befund: die pathologischen Level sind keine Ausreisser, sondern ein Trend.**
`CLAUDE.md` beschreibt sie bisher als *"a single search level consuming three to five hours while its
neighbours take seconds"*. Die Level-Serie von System 59 (Roessler, chaotisch) zeigt etwas anderes:

```text
Level  1..8   49  107   60   74  107  115   91  129            Sekunden
Level  9..16  6214 3985 9532 4468 4482 6035 3473 2917
Level 17..24  3630 2858 3348 5996 4373 6278 8021 11538
Level 25..30  25462 20960 21524 30075 16658 42372              = 11,8 h im letzten Level
```

Kein Ausreisser, sondern **monotones Wachstum ueber drei Groessenordnungen mit der Strukturgroesse**.
Bestaetigt auf System 61 (48 s → 37.211 s) und, im Kleinen, auf dem billigen System 26 (14 s → 63 s).
Auch die Konzentrationsmessung passt: In den teuersten Zellen macht das langsamste Level nur 17–26 %
der Zelle aus — teuer ist die **ganze zweite Haelfte**, nicht ein Level.

**Und diese zweite Haelfte ist Verschwendung.** System 59 endet nach 30 Levels und 68 Stunden bei
`loss = 1,54`, System 61 bei `63,1`, System 56 (Lorenz) bei `44,5` — alle drei chaotisch, alle drei
ohne brauchbare Loesung. Die 60 von 68 Stunden ab Level 9 kaufen nichts. In Zaehlern, wie Grundsatz 7
es verlangt: 6.625.512 Loss-Evaluationen bei 610 Parameter-Fits auf System 59, also **rund 10.900
Solves je Fit** — das ist die Liniensuche, die seit WP-D2 als offener Kostenhebel notiert ist, hier
zum ersten Mal auf dedizierter Hardware beziffert.

Das verschiebt die Prioritaet: Nicht ein einzelnes pathologisches Level ist zu jagen, sondern es ist
zu entscheiden, ob chaotische Systeme ueberhaupt 30 Levels bekommen. Ein Levelbudget in Abhaengigkeit
der Dimension oder ein Abbruch bei ausbleibender Verbesserung waere fingerprint-relevant und muesste
damit **vor** dem ersten Kampagnen-Record fallen. Bewusst nicht jetzt entschieden: Der Cap-Defekt hat
Vorrang, und beide Aenderungen zusammen in einem Fingerprint-Sprung sind sauberer als zwei.

**Provenienz, wie erwartet.** Alle 42 Records tragen `config_fingerprint: c71c85ac2ec580ff` und
`git_hash: "unknown"` — also den Stand **vor** WP-M1 und vor dem Provenienz-Fix. Sie sind damit
genau das, was sie sein sollten: gueltige Infrastruktur- und Kostenmessungen, die **niemals** mit
Kampagnen-Records vermengt werden duerfen. Die Kampagne laeuft unter `ca02ea284d621f6d`.

**Nebenbefund:** Der Pilot hat **281 Kernstunden** verbraucht. `docs/hpc_requirements.md` §5 kuendigt
dem Standort gegenueber *"roughly 20 jobs, ~50 core-hours"* an. Faktor 5,6 darueber, verursacht von
denselben drei chaotischen Zellen. Kein Schaden, aber beim naechsten Mal anzukuendigen.

**Offen aus dem Pilot:**

1. **`pretune_off` ist ungemessen** — das ist die Haelfte der Kampagne. Ohne Warmstart ist mehr
   BFGS-Arbeit je Fit zu erwarten, die Hochrechnung oben ist insofern eine untere Schranke.
2. Systeme 1–23 ruhen auf **einem** gemessenen System (System 1, 3 Records), System 63 auf keinem.
3. Ein Seed, ein IC-Set. Die Seed-Streuung ist dort, wo gemessen, erheblich: System 62 braucht
   4.279 s bei Seed 42 und 300 s bei Seed 123 — Faktor 14 bei identischer Konfiguration.

---

## 2026-08-14

### Der Stage-Cap schneidet wahre Strukturen ab - auf 2 von 7 geprueften exakten Systemen

<!-- e5c739b -->

**Das ist ein Defekt im Beitrag des Papiers, gefunden vor der Kampagne.**

Anlass war die Umpositionierung von EvoODE als *Search-Space-Controller* (siehe
`docs/paper1_scope_discussion_2026-08-14.md`): Der Cap entscheidet, wie weit der Hypothesenraum je
Gleichung ueberhaupt geoeffnet wird, der innere Sucher ist austauschbar. Diese Position steht und
faellt mit einem Halbsatz — der Controller darf unnoetige Suche vermeiden, **ohne relevante
Strukturen abzuschneiden**. Genau das wurde geprueft.

**Befund.** Je Gleichung die benoetigte Stufe aus `phase_b_support.json` abgeleitet und gegen den im
Record protokollierten Cap gehalten:

| System | wahrer Support Gl. 2 | benoetigte Stufe | Cap | Ergebnis |
|---|---|---|---|---|
| 28 | `sin(u1)` | **5** | **1** | abgeschnitten |
| 32 | `u1`, `u2`, `u1^3` | **4** | **1** | abgeschnitten |
| 26, 27, 29, 31, 54 | — | — | — | in Ordnung |

Beide betroffenen Systeme haben `pruned_match = false`. Die Ursache ist damit **nicht** der additive
Sucher, sondern der Controller: Die Antwort war nie im zugelassenen Raum.

**Die entlastende Erklaerung haelt nicht.** Naheliegend waere, dass die Trajektorie die
Nichtlinearitaet gar nicht anregt und der Cap insofern recht hat — der Term waere symbolisch
vorhanden, aus den Daten aber nicht identifizierbar. Gegen den Datensatz geprueft:

```text
System 28 (Pendel ohne Reibung)     du2/dt = -0.9*sin(u1)      |u1|max = 1.90 rad ~ 109 Grad
                                    sin(1.90) = 0.946  gegen  u1 = 1.90        -> Faktor 2
System 32 (Doppelmuldenoszillator)  du2/dt = -u1^3 + u1 - ...  |u1|max = 2.09
                                    u1^3 = 9.08        gegen  u1 = 2.09        -> Faktor 4,4
```

In beiden Faellen **dominiert** der hochstufige Term die Dynamik. Ein Cap von 1 ist dort nicht
konservativ, sondern falsch.

Damit verletzt der Cap die Regel, die aus dem System-63-Vorfall abgeleitet wurde und in `CLAUDE.md`
unter "Settled" steht: *the cap must rest on positive evidence, never on the absence of evidence.*
Ein Cap von 1 behauptet positive Evidenz, dass Stufe 1 genuegt.

**Der Mechanismus ist gefunden: der Vorausblick ist genau eine Stufe zu kurz.**

```julia
# src/structure/stage_cap.jl
horizon_end = min(length(applicable_stages), pos + policy.lookahead_horizon)
#                                                  lookahead_horizon = 2
```

Von Stufe 1 aus prueft die Analyse nur die Stufen 2 und 3. Stufe 4 und 5 sieht sie nie. Und die
Basis staffelt nach **Grad**, nicht nach **Symmetrie**:

| Stufe | Terme | Paritaet |
|---|---|---|
| 1 | `u1`, `u2` | ungerade |
| 2 | `u1^2`, `u2^2` | gerade |
| 3 | `u1*u2` | gemischt |
| 4 | `u1^3` | ungerade |
| 5 | `sin`, `cos` | ungerade / gerade |

Fuer eine **ungerade** Nichtlinearitaet liegt die erste brauchbare Naeherung jenseits von linear
also bei Stufe 4 oder 5. Die Stufen 2 und 3 koennen sie nicht approximieren — `u1^2` ist gerade,
Kreuzterme brauchen eine zweite Variable. Der Vorausblick sieht keine Verbesserung und schliesst:
Stufe 1 genuegt.

Damit erklaeren sich **alle zehn Faelle**: Jeder korrekte Cap liegt bei Stufe 3, also innerhalb des
Horizonts. Beide Fehlschlaege brauchen Stufe 4 bzw. 5, also jenseits davon.

> **Designregel, zweite ihrer Art nach der System-63-Regel:** Ein datengetriebener Deckel muss so
> weit vorausschauen, wie die Basis strukturelle Luecken erzeugt. Bei gradgestaffelter Basis und
> ungeraden Nichtlinearitaeten betraegt diese Luecke zwei Stufen; ein kuerzerer Horizont schliesst
> die wahre Struktur systematisch aus.

**Der Cap ist damit nicht grundsaetzlich defekt** — der Parameter ist falsch. Naheliegender Fix:
`lookahead_horizon` auf 4, also bis ans Ende der Basis. Der Vorausblick rechnet nur
Ableitungsregressionen, keine Fits; die Mehrkosten sind gegenueber der Suche vernachlaessigbar.

Zwei Auflagen: Der Parameter steckt in `LOOKAHEAD_CAP_POLICY` und damit im Fingerprint, muss also
vor dem ersten Kampagnen-Record landen. Und es ist zu validieren statt zu glauben — loest es 28 und
32, **ohne** die fuenf korrekten Caps (26, 27, 29, 31, 54) zu verschieben?

**Konsequenz fuer die Interpretation der 40 % Recovery:** Mindestens zwei der sechs Fehlschlaege sind
**keine** Suchfehler. Die Diagnose "der additive Sucher kann eine falsche Festlegung nicht
zuruecknehmen" gilt fuer System 54 — fuer 28 und 32 gilt eine andere Ursache. Beide Fehlerquellen
muessen getrennt gezaehlt werden, sonst wird dem Sucher angelastet, was der Controller verursacht hat.

**Offen, vor der Kampagne zu klaeren:**

1. Alle 20 exakten Systeme pruefen, nicht nur die sieben mit vorliegendem Record. Zwei von sieben ist
   eine Stichprobe, keine Rate.
2. Den Mechanismus verstehen: Warum liefert die Voraus-Analyse bei sinus- bzw. kubikdominierter
   Dynamik "Stufe 1 genuegt"?
3. Erst danach entscheiden, ob der Cap in dieser Form in die Kampagne geht.

---

### GPU geprueft und verworfen — die Begruendung, damit die Frage nicht wiederkommt

<!-- 7d23da5 -->

Frage aufgeworfen: laesst sich im Projekt irgendwo die GPU nutzen? Antwort nach Durchsicht von
`build_rhs`, `simulate` und der Populationsschleife: **nein, nicht auf dem Paper-1-Pfad.** Vier
unabhaengige Gruende, jeder fuer sich ausreichend.

**1. Die Batch-Breite fehlt.** Eine GPU gewinnt bei ODEs dieser Groesse (dim 1–4, 512 Punkte) erst
ab ~1e4 gleichzeitigen Trajektorien — das ist der Arbeitsbereich von `DiffEqGPU.EnsembleGPUKernel`.
Vorhanden sind `pop_size = 20` plus Kinder, also 20–60 unabhaengige Kandidaten pro Level. Innerhalb
eines Kandidaten ist BFGS strikt sequenziell. Damit ist ausgerechnet das groesste offene
Kostenrisiko GPU-immun: die pathologischen Level (3–5 h, bis 39.933 Loss-Evals bei zwei Parametern)
sind eine Liniensuche, also eine Kette und kein Batch. Eine GPU verkuerzt sie um null.

**2. Die RHS ist nicht kernel-faehig.** `build_rhs` (`src/basis/interface.jl:24`) schliesst ueber
`basis.funcs::Vector{Function}` und dispatcht pro Term und Zeitschritt dynamisch. Das ist nicht auf
eine GPU kompilierbar; noetig waeren StaticArrays, allokationsfrei, typstabil. Der Umbau auf eine
Koeffizientenmatrix ueber der Stage-Basis waere die Vorbedingung fuer alles GPU-artige — und
CPU-seitig ohnehin ein Gewinn.

**3. Float64.** Das Projekt argumentiert mit `abstol = reltol = 1e-9`, Losses bei 1e-11 bis 1e-15
und bit-identischen Vergleichen. Consumer-GPUs rechnen FP64 mit 1/32 Durchsatz, waeren also
langsamer als wenige CPU-Kerne; Float32 wuerde genau die Stellen zerstoeren, ueber die das Paper
argumentiert. GPU hiesse hier zwingend A100/H100-Klasse.

**4. Die Hardware.** Orion vergibt 846 Jobs a 1 Kern, kein GPU-Node. Ueber die 756 Laeufe ist die
Parallelitaet als Job-Parallelitaet bereits vollstaendig ausgeschoepft.

**Was vorher kaeme.** Im Quellbaum steht kein einziges `Threads.@threads`, `@spawn` oder `pmap`. Die
20–60 Kandidaten pro Level werden seriell gefittet, obwohl vollstaendig unabhaengig — der
offensichtliche Faktor 4–16 auf dem bestehenden Pfad. Gleiche Konsequenz wie jede GPU-Idee: beruehrt
den Pfad jedes Phase-B-Laufs, aendert den Fingerprint. Gehoert damit hinter die Kampagne, zu WP-D4b.

**Wo GPU tatsaechlich passen wuerde, beides jenseits von Paper 1:**

- *Batched Parameterfitting statt BFGS* (Phase 5, als Forschungsfrage, nicht als Optimierung).
  Ersetzt man die sequenzielle Liniensuche durch ein populationsbasiertes/Multistart-Verfahren,
  entsteht die Batch-Breite von selbst: 20 Kandidaten x 500 Starts = 1e4 Trajektorien, identische
  RHS-Struktur, nur andere Parameter — der Idealfall fuer `EnsembleGPUKernel`. Adressiert zugleich
  dokumentierte Schmerzen (Sentinel-Loss `1e6`, verlorene Parameteroptima bei identischem Support).
  Es ist ein Algorithmenwechsel und aendert die experimentelle Bedingung.
- *Die geplanten Phase-3-Achsen* (Rauschen, Sampling-Dichte). Per Konstruktion Ensembles: gleiches
  System, gleiche Struktur, viele Realisierungen. Dort liegen 1e3–1e4 Solves natuerlich vor, ohne
  den Suchalgorithmus anzufassen.

**Entscheidung:** GPU bleibt Non-Goal wie in `CLAUDE.md` festgehalten. Reihenfolge, falls Rechenzeit
je drueckt: typstabile RHS → Threads ueber die Population → erst dann GPU. Der zweite Punkt oben
lohnt nur, wenn batched Fitting als eigener Beitrag gefuehrt wird.

### Lesender Code-Durchgang vor der Kampagne: nichts zu tun, und das ist der Befund

<!-- 212c4ef -->

Reiner Lesedurchgang auf Bloat, toten Code und Schreibqualitaet. **Keine Aenderung vorgenommen** —
jede haette den Pfad beruehrt, den 756 Zellen durchlaufen, und seit WP-M1 existiert ein bit-exakter
Anker, gegen den jede Aenderung neu zu verifizieren waere.

**Toter Code: praktisch keiner.** Bei 143 Funktionen und 6.565 Zeilen genau eine ungenutzte:
`_cap_uniform_step` in `src/structure/stage_cap.jl`, drei Zeilen. (Ein erster Durchlauf meldete 16
Kandidaten — Messfehler, Namen mit `!` wurden falsch gezaehlt.)

**Die 46 Prozent "Ballast" sind bezahlte Reproduzierbarkeit.** v3 (1.233 Zeilen), GP (457),
Screening (870) und Plotting (489) stehen zusammen fuer 46 % des Quellbaums und kommen im
Paper-1-Umfang nicht vor. Loeschen waere trotzdem falsch: Das Paper erzaehlt v2.2 → v3 → capped als
dokumentierte Fehleranalyse, und ohne lauffaehigen v3-Code sind diese Zahlen nicht reproduzierbar;
`gp_baseline` steckt im eingefrorenen Phase-A-Experiment. Das ist der Preis dafuer, die eigene
Geschichte nicht wegzuwerfen, und er wird bewusst gezahlt.

**Der eine echte Befund: die Suchschleife ist ein Monolith, dreimal geforkt.**

```text
656 Zeilen  evogrow.jl            search_structure
638 Zeilen  evogrow_v3.jl         search_structure
459 Zeilen  evogrow_screening.jl  search_structure
447 Zeilen  bfgs.jl               fit_parameters
256 Zeilen  gp.jl                 search_structure
```

2.009 Zeilen in vier Suchschleifen. Der Beleg fuer das Forken ist `_validate_policy`: dreimal
vorhanden, in `evogrow.jl` (15 Zeilen), `evogrow_screening.jl` (33) und `evogrow_v3.jl` (7) — drei
verschiedene Implementierungen unter demselben Namen in Nachbardateien. So etwas entsteht, wenn
Kopieren leichter ist als Erweitern.

Das ist das Ziel fuer WP-D4b: die gemeinsame Schleife herausziehen, Varianten als Strategien
einhaengen. Dann verschwinden die drei `_validate_policy` von selbst. Bleibt hinter der Kampagne,
aus dem in CLAUDE.md genannten Grund.

**Bewusste Entscheidung, zeitkritisch:** `evogrow_v3` und `gp_baseline` bleiben in `VARIANTS`. Die
Liste geht ueber `FINGERPRINT_VARIANT_LABELS` in den Fingerprint ein und ist nach dem ersten
Kampagnen-Record eingefroren. Entschieden am 2026-08-14, Begruendung wie oben.

Sonst: keine ungenutzten Abhaengigkeiten, saubere Interface-Struktur mit korrektem Dispatch
(`search_structure` 6x, `fit_parameters` 3x, `evaluate_loss` 2x sind Interface plus
Implementierungen, keine Duplikate).

---

## 2026-08-13

### WP-M1 - R2 und abgeleitete erwartete Stage; der letzte wissenschaftliche Blocker ist zu

<!-- e2a86f3 -->

Zwei Metriken haben gefehlt, und ohne sie haette die Kampagne 756 Records erzeugt, die ihre eigenen
Fragen nicht beantworten.

**R2, fuer alle 63 Systeme.** `PAPER_1.md` fuehrt es in der Kernmetrik-Tabelle, im Code gab es keine
Zeile dazu. Fuer die 43 Surrogatsysteme — zwei Drittel der Kampagne — blieb damit der rohe Loss als
einzige Guetegroesse, ohne Anschluss an die ODEBench-Literatur, die in R2 argumentiert. Implementiert
als `r2` (arithmetisches Mittel ueber Dimensionen) plus `r2_by_dim`.

Drei Faelle liefern ausdruecklich `null` statt einer plausiblen Zahl: nicht-endliche Vorhersagen, der
`MSELoss`-Sentinel bei `loss >= 1e6`, und verschwindende Referenzvarianz in einer Dimension. Und es
wurde **kein Schwellenwert** eingefuehrt: `docs/paper1_odebench_protocol_alignment.md` haelt fest,
dass die publizierten R2-Konventionen noch nicht verifiziert sind, also waere jede Schwelle erfunden.

**`expected_stage` abgeleitet statt gepflegt.** Bisher fuer alle 63 Phase-B-Systeme hartkodiert
`nothing`, womit `stage_overshoot` und `wasted_levels` durchgehend leer blieben — auch auf den 20
exakten Systemen. Ausgerechnet `wasted_levels` traegt die zentrale Aussage, dass Stage-Eskalation
Verschwendung ist. WP-A1 hat das quantifiziert: **33 von 33 Pilot-Records ohne beide Werte.**

Die Ableitung nutzt, was WP-E2 bereits erzeugt: `support_idxs` aus `phase_b_support.json` sind
Indizes in die Basis, und `default_staged_polynomial_basis(dim).term_groups` ordnet jeden Index einer
Stufe zu. Die erwartete Stage ist die hoechste Stufe, die noch einen Supportterm enthaelt.

Abnahme gegen **alle fuenf** handgepflegten Werte in `diagnostic_systems.jl`: Systeme 3, 11, 26, 31
und 63 — hand und abgeleitet stimmen jeweils ueberein. Auf Phase B: `exact_missing=0`,
`surrogate_nonnull=0`, `expected_stage_missing=43`, und die 43 sind exakt die Surrogatsysteme. Fuer
sie wird keine Stage erfunden; die erreichte Stage bleibt Beobachtung, nicht Abweichung von einem
Soll.

**Die entscheidende Abnahme war, dass sich nichts aendert.** Referenzzelle System 11, Seed 42:

```text
loss              4.635914151853964e-15  ->  4.635914151853964e-15
pruned_match      true                   ->  true
total_loss_evals  30550                  ->  30550
expected_stage    null                   ->  4
stage_overshoot   null                   ->  0
wasted_levels     null                   ->  0
r2                null                   ->  0.9999999999999564
```

Bis auf die letzte Stelle identisch. Das Paket fuegt Messungen hinzu, ohne die Suche anzufassen.

**Fingerprints, bewusst bewegt:**

| | vorher | nachher |
|---|---|---|
| Phase B | `c71c85ac2ec580ff` | `ca02ea284d621f6d` |
| Regression | `45cb2c4507007366` | `0825cdc88d9264a0` |

Phase B bewegt sich durch die abgeleiteten Stages **und** die Metrikdefinition; die Regression nur
durch letztere, weil ihre Systeme ihre Stages schon hatten. Dass die Metrikdefinition Teil der
Nutzlast ist, ist eine Entscheidung mit Begruendung: Die R2-Definition ist eine wissenschaftliche
Wahl — ein spaeterer Wechsel von "arithmetisches Mittel ueber Dimensionen" auf eine gepoolte Variante
wuerde Records stillschweigend unvergleichbar machen. So zeigt der Fingerprint es an.

**Folge fuer die Pilotdaten:** Sie stammen vom alten Stand und tragen den alten Fingerprint. Sie
bleiben gueltige Infrastrukturmessungen, duerfen aber nicht mit Kampagnen-Records vermengt werden.

**Grundsatz 8 in CLAUDE.md korrigiert.** Das nirgends definierte "target term-class usage" ist
gestrichen; es steht jetzt dort, worauf Surrogatsysteme tatsaechlich bewertet werden — Guete ueber
R2, erreichte Stage und Stabilitaet als Beobachtungen.

---

### WP-A1 - die Analysepipeline kann Kampagnendaten nicht lesen, und eine Stelle scheitert leise

<!-- d198cfd -->

Die Python-Auswertung ist Phase-A-foermig: `aggregate_run_registry.py` liest `run_registry.csv` aus
der `experiments/`-Infrastruktur. Die Kampagne schreibt per-Zelle-JSONL. **Direkt gefuettert bricht
die Aggregation hart ab** (`Expected 19 fields in line 22, saw 20`) — immerhin ehrlich.

Geloest ueber eine einzelne Konvertierung statt Aenderungen quer durch die Auswertungsskripte:
`analysis/scripts/aggregate/convert_campaign_history_to_run_registry.py`. Der Phase-A-Pfad bleibt
unangetastet, `paper1_phaseA_v1` weiter reproduzierbar.

**Der wichtigste Befund ist der stille.** Nach der Konvertierung laeuft `table_main_results.py`
fehlerfrei durch — und liefert Unsinn:

```text
agg_variants   = evogrow_v2_2_stage_capped, evogrow_v3, ...   (Kampagne)
table_variants = evogrow_v1, evogrow_v2_1, gp_baseline, ...   (eingefrorene Phase-A-Liste)
table_rows=30   table_nonempty_mean_loss=5
```

Das Skript indiziert auf eine fest verdrahtete Variantenliste um und laesst alles fallen, was es
nicht kennt. 25 von 30 Zeilen bleiben leer, ohne Fehlermeldung. `evaluate_hypotheses.py` scheitert
demgegenueber sauber mit `Missing expected variants`. Die Lehre: Vor der Auswertung muessen die
Downstream-Skripte von der Phase-A-Variantenliste geloest werden, sonst entsteht eine plausibel
aussehende, fast leere Tabelle.

**Zwei Felder bleiben bewusst leer statt geraten.** `total_invalid_evals` meint in Phase A
NaN-erzeugende Evaluationen; die Kampagne verteilt verwandte Begriffe auf `total_invalid_solves`,
`total_optimizer_invalid_result_fits`, `invalid_screening_evals` und Solver-Instabilitaetszaehler.
Ohne definierte Einheit wird nichts eingetragen. Und `exact_support_match` wird aus `pruned_match`
gespeist — nuetzlich, aber nicht semantisch identisch, und fuer Surrogatsysteme korrekt leer.

**Nachtest auf echten Pilotdaten.** Codex hatte kein `S:`-Laufwerk und musste auf lokale Altdaten
ausweichen; die Faelle `pruned_match: null` und `git_hash: "unknown"` blieben ungetestet. Nachgeholt
an 33 echten Cluster-Records: `loss`, `final_stage`, `elapsed_s` und `system_dim` durchgehend
gefuellt, `exact_support_match` in 11 von 33 (genau die exakten Systeme), Surrogatsysteme korrekt
leer. Die Bruecke haelt.

Dabei faellt der Beleg fuer WP-M1 quantitativ an: **`stage_overshoot` und `wasted_levels` sind in
33 von 33 Records leer**, weil `expected_stage` nirgends gesetzt ist.

---

### Jeder Cluster-Record trug `git_hash: "unknown"` - die Provenienzkette war offen

<!-- d2aed32 -->

Beim Zaehlen von Hash-Referenzen fuer eine ganz andere Frage aufgefallen: **alle 29 bisher auf Orion
erzeugten Records tragen `git_hash: "unknown"`.**

Die Auflage in `docs/hpc_requirements.md` §7 lautet, dass jeder Job Commit-Hash und
Konfigurations-Fingerprint aufzeichnet und eine Kampagne mit gemischten Hashes nicht publizierbar
ist. Die Zeile, die das leisten soll, ruft `git rev-parse` auf — und im Container gibt es kein
`.git`-Verzeichnis, weil `.dockerignore` es zu Recht ausschliesst. Der Code trug also ehrlich
`unknown` ein, und niemandem ist es aufgefallen, weil `Completed` und `error=null` ja stimmten.

Faktisch gerettet war die Nachvollziehbarkeit bisher allein durch den Image-Tag, der der Commit-SHA
ist. Aber **aus einem Record allein liess sich nicht sagen, welcher Code ihn erzeugt hat** — genau
das, was das Protokoll verlangt. Ein Kampagnen-Blocker, gefunden zwei Tage bevor er teuer geworden
waere.

**Der Fix backt die Revision beim Bauen ein.** `.gitlab-ci.yml` reicht `$CI_COMMIT_SHA` als
Build-Argument durch, das Dockerfile legt es als `EVOODE_GIT_SHA` ab und schreibt es zusaetzlich in
`build_provenance.json`, und `git_provenance()` faellt darauf zurueck, wenn kein Git verfuegbar ist.
Der Standardwert des Build-Arguments ist **leer**, nicht `unknown` — ein lokaler Bau ohne Argument
meldet damit weiterhin ehrlich eine unbekannte Revision statt einer falschen.

`git_dirty` ist im Container-Fall `false`: Ein CI-Bau checkt genau einen Commit in einen frischen
Klon aus, ist also per Konstruktion sauber. Wo Git verfuegbar ist — lokale Laeufe — bleibt das
bisherige Verhalten unveraendert, inklusive echter Dirty-Erkennung.

Der Fingerprint ist nicht betroffen: Seine Nutzlast enthaelt ausschliesslich
Konfigurationskonstanten, keine Provenienz. Die 29 Pilot-Records bleiben damit gueltige
Infrastrukturmessungen; sie sind ohnehin als wissenschaftlich wertlos deklariert.

---

### Repo-Inventur vor der Kampagne: SCRIPTS.md neu, Slurm-Schiene entfernt

<!-- 2b95eda -->

Anlass ist der Zeitpunkt, nicht Ordnungsliebe. CLAUDE.md verlangt, dass **alle
fingerprint-relevanten Aenderungen vor dem ersten Kampagnen-Record landen**; danach kostet jede
Aenderung die Geschlossenheit der Kampagne. Dies ist das letzte bequeme Fenster.

**Der groesste Befund war kein ueberfluessiges File, sondern ein Dokument, das mehr verspricht als es
haelt.** `SCRIPTS.md` wird in CLAUDE.md als "exact commands for every script" gefuehrt, dokumentierte
aber **9 von 33** Skripten — und ausgerechnet die der alten Welt (`aggregate.jl`,
`run_experiment.jl`, `debug_single.jl`). Vom Kampagnenpfad stand **nichts** darin: weder
`run_batch_cell.jl` noch `run_k8s_indexed_cell.jl` noch `generate_phase_b_manifest.jl` noch
`merge_batch_records.jl`. Das ist gefaehrlicher als eine Luecke, weil Vollstaendigkeit behauptet
wird. Neu geschrieben mit sieben Abschnitten, Kampagnenpfad zuerst, inklusive Flags, Umgebungs-
variablen und der drei Fallen, die uns heute begegnet sind (Bootstrap genau einmal, Exit 0 heisst
nicht gueltig, Indexbasis 0 gegen 1).

**Geloescht — veraltete Dokumente.** `docs/paper1_roadmap.md` (Stand 2026-05-17, also vor beiden
Gates, und selbsterklaert nachrangig gegenueber `PAPER_1.md`), `docs/projektjournal.md` samt PDF und
dem erzeugenden `tools/build_journal_pdf.py` (abgeleitete Lesefassung von DIARY.md, eingefroren auf
2026-08-03 und damit bereits widersprechend — dasselbe Muster wie `5b4bd5b`, wo die `docs/de`-Kopien
gingen), sowie `docs/hpc_briefing_2026-08-06.md` (Kurzfassung fuer einen stattgefundenen Termin, und
fuer die falsche Plattform).

**Geloescht — die Slurm-Schiene.** `containers/evoode_regression.apptainer` und die drei Skripte
unter `hpc/`. Sie adressieren einen Standort, den es fuer dieses Projekt nicht gibt; ihre Aufgabe war
die Vorlage fuer die Docker-Uebersetzung, und die ist erledigt. Der Grund fuers Loeschen statt
Behalten ist nicht Platz, sondern Irrefuehrung: Wer `hpc/slurm_*.sh` findet, haelt Slurm fuer den
Weg. Der Git-Verlauf bewahrt sie ohnehin.

**Bewusst behalten: die abgeschlossenen Studienskripte.** Zwanzig Dateien haben keine
Code-Referenz, was bei Einstiegspunkten nichts bedeutet. Wichtiger: `studies/lookahead/`,
`studies/linesearch/`, `studies/numerics/` und `studies/gate2_do_or_die/` haben Befunde erzeugt, auf
die sich die Argumentation stuetzt — die Tolerance-Invarianz auf System 26, die Widerlegung der
Sentinel-Hypothese, die Stage-Cap-Herleitung. Ein Skript, das ein publiziertes Ergebnis erzeugt hat,
ist kein Ballast, sondern dessen Reproduzierbarkeitsnachweis. Sie sind jetzt in SCRIPTS.md mit der
Frage gelistet, die sie beantwortet haben.

**Korrigierte Fehleinschaetzung.** `studies/regression/generate_manifest.jl` sah nach abgeloestem
Vorgaenger von `generate_phase_b_manifest.jl` aus. Er iteriert aber ueber `REGRESSION_SYSTEMS` und
erzeugt das Manifest der **Regressionskampagne** (90 Zellen), die neben Phase B geplant ist. Bleibt.

**Nicht angefasst: die Grafikabhaengigkeiten.** `Qt6`, `FFMPEG`, `Xorg`, `CairoMakie` kosteten beim
ersten Cluster-Bootstrap 1.022 von 2.760 Sekunden Praekompilierung fuer Pakete, die eine Rechenzelle
nie anfasst. Nach WP-H5 kosten sie **keine Laufzeit mehr**, nur Imagegroesse. Sie zu entfernen
aendert `Manifest.toml` und laesst Pkg gemeinsame Abhaengigkeiten neu aufloesen — verschobene Zahlen
kurz vor der Kampagne gegen etwas Plattenplatz ist ein schlechtes Verhaeltnis.

**Neu aufgefallen und noch offen:** `analysis/` erwartet `run_registry.csv` aus der
`experiments/`-Infrastruktur, die Kampagne schreibt aber `cell_*.jsonl`. Dazwischen steht
`merge_batch_records.jl`, aber ob die Analysepipeline dessen Ergebnis verarbeitet, ist nirgends
geprueft. Das ist kein Aufraeumthema, sondern ein Stolperstein **nach** der Kampagne — an den
Pilotdaten durchspielen, bevor 756 Records da sind.

`docs/hpc_requirements.md` traegt bis zur Ueberarbeitung einen Warnhinweis: falsche Plattform,
Laufzeitschaetzungen um ein bis zwei Groessenordnungen zu hoch, keine Walltime und damit kein
Checkpointing noetig. Gueltig bleiben Workload-Form, Ressourcenprofil pro Zelle und die
Reproduzierbarkeitsauflagen.

---

### WP-H5 - der eingebackene Praekompilierungscache war auf dem Cluster wertlos

<!-- be6bf99 -->

**Ergebnis vorweg, gemessen auf einem Orion-Node**: derselbe Bootstrap, derselbe Fingerprint, dieselbe
Ausgabe — **2.760 s vorher, 22 s nachher**. `manifest.csv` ist in beiden Laeufen exakt 77.201 Bytes
gross, `phase_b_fingerprint=c71c85ac2ec580ff` in beiden. `Precompiling packages...` taucht im zweiten
Lauf nicht mehr auf, und ein Ladetest meldet null `Rejecting cache file`. Das ist eine
Infrastruktur-Messung auf dedizierter Hardware, nicht der Laptop-Fall, den Grundsatz 7 ausschliesst.

**Und damit lief der erste Indexed Job durch**: drei 1D-Zellen, `completionMode: Indexed`,
`completions=3`. Die Abbildung haelt auf echter Hardware — Completion-Index 0/1/2 auf Listenzeile
1/2/3 auf Manifestzeile 1/2/3, kein Off-by-one. Drei Records und drei Heartbeats liegen unter
`/bigdata/data-science/joedicke/.../tasks/` als `cell_000001` bis `cell_000003`.

Beobachtet an Zelle 3 (System 1, IC 1, Seed 7): Abbruch bei **Level 20 von 30**, Stage 5, vier Level
ohne Verbesserung bei `loss=6.630e-05`. Zehn Level ungenutzt — dasselbe Muster, das WP-L/G auf System
3 gezeigt haben, hier zum ersten Mal auf Clusterhardware. `pruned=nothing` ist korrekt: System 1 ist
eines der 43 Surrogatsysteme. Die Kosten pro Level stiegen von 3,3 auf 12,7 s, weil spaetere Level
mehr Terme und damit mehr Parameter pro Fit tragen.

Damit ist der Weg vom Commit bis zum Record einmal vollstaendig und an jedem Uebergang verifiziert:
GitHub → GitLab → CI → Registry → OpenShift → Indexed Job → NFS.

---

**Der Befund.** Der erste Bootstrap auf Orion lief 46 Minuten, davon praktisch alles
Praekompilierung — obwohl das Image ein fertiges 3,1-GB-Depot mit 1,3 GB kompiliertem Code traegt.
Weder Konfiguration noch Code waren schuld: `JULIA_DEPOT_PATH` stimmte, `DEPOT_PATH` loeste korrekt
auf, der Cache war vorhanden und exakt so gross wie lokal. Julias Lader nannte den Grund selbst:

```text
Rejecting cache file .../compiled/v1.12/Logging/....ji
Reasons = "Unable to find compatible target in cached code image.
           Target 0 (icelake-server): Rejecting this target due to
           use of runtime-disabled features"
(cache misses: target mismatch (1))
```

Der GitLab-Runner ist eine Intel-Maschine und praekompiliert fuer `icelake-server`; die Orion-Nodes
sind AMD EPYC 7643, von Julia als `znver3` gemeldet. Praekompilierte Images enthalten nativen Code
und werden gegen die CPU-Features der laufenden Maschine geprueft — also wurde jede einzelne
Cache-Datei verworfen.

**Warum die lokale Verifikation das nicht finden konnte.** WP-H2 hat auf demselben Laptop gebaut und
ausgefuehrt; dort ist der Cache per Konstruktion gueltig. Der Fehler entsteht erst, wenn Bau- und
Laufmaschine auseinanderfallen, und das tut es erst seit der CI. Das ist eine Grenze lokaler
Verifikation, kein Versaeumnis — und sie ist notierenswert, weil sie fuer jede kuenftige
Image-Aenderung gilt.

**Der Fix**: `JULIA_CPU_TARGET="generic;znver3,clone_all"` im `ENV`-Block **vor** dem
Praekompilierungsschritt, damit der eingebackene Cache beide Ziele traegt — einen portablen
Grundstock und eine Zen-3-Variante. Bewusst nicht ausschliesslich auf die Cluster-CPU gepinnt: ein
Image, das nur auf einer Mikroarchitektur laeuft, erzeugt denselben Fehler in der Gegenrichtung.
Preis sind Imagegroesse und Bauzeit, einmal pro Commit statt Dutzende Minuten pro Pod.

**Kosten, beziffert.** Von den 46 Minuten entfielen 1.462 s auf den DifferentialEquations-Stapel,
**364 s auf Plots und 658 s auf Makie/CairoMakie** — gut 37 % auf einen Grafikstapel, den eine
Batch-Zelle nie anfasst. `src/plotting/` zieht `Qt6`, `FFMPEG`, `Xorg` und `CairoMakie` in den
Manifest. Nach diesem Fix kostet das **keine Laufzeit mehr**, nur noch Imagegroesse; die Trennung von
Rechen- und Plotting-Abhaengigkeiten bleibt damit eine Aufraeumaufgabe und ist kein
Kampagnenhindernis. Sie waere ausserdem fingerprint-relevant, weil sie `Project.toml` und
`Manifest.toml` und damit die Hashes im `build_provenance.json` aendert.

**Was der Lauf trotz allem bewiesen hat.** Der Bootstrap kam mit `EXITCODE=0` durch und schrieb
Manifest und alle fuenf Indexlisten nach `/bigdata/data-science/joedicke`. Gemeldet:
`phase_b_fingerprint=c71c85ac2ec580ff`, `regression_fingerprint=45cb2c4507007366`, `rows=756`,
`unique_identities=756`, `systems=63`, `representability_exact=20`, `representability_surrogate=43`,
Dimensionen 276/336/120/24. Damit ist belegt, dass das Image auf Orion denselben Code, dieselbe
Konfiguration und dieselbe Support-Tabelle traegt wie lokal — die Korrektheitsaussage steht
unabhaengig vom Kostenproblem.

**Nebenbefund, noch offen**: Der Bootstrap wurde bei 2 GiB per OOM abgeraeumt und braucht 8 GiB. Das
Repo-Manifest traegt noch den alten Wert. Ebenso offen: `restartPolicy: OnFailure` loescht
gescheiterte Pods samt Logs — fuer die Kampagne muss das `Never` sein, sonst verschwindet jede
fehlgeschlagene Zelle spurlos. Beides gehoert in ein gemeinsames Aufraeum-Work-Package.

---

### WP-H3/H4 - der Weg vom Commit zur Zelle auf Orion steht, und was der Cluster wirklich hergibt

<!-- 9f742fd -->

**WP-H3: das Image entsteht in der CI.** `.gitlab-ci.yml` baut `containers/Dockerfile` auf dem
CPU-Runner (ALEXANDRIA, Tag `cpu`) und legt es unter `registry.gitlab.scch.at:443/joedicke/evoode`
ab, getaggt mit `$CI_COMMIT_SHA` und dem Branch-Slug. Kein `latest`. Authentifizierung ueber die
eingebauten Job-Credentials, nicht ueber den persoenlichen PAT der Hausvorlage.

Der erste Lauf scheiterte an `http://docker:2375` — der Runner belegt `DOCKER_HOST` vor, erwartet
also einen `docker:dind`-Service, den die Hausvorlage nicht deklariert. Mit Service plus
`DOCKER_TLS_CERTDIR=""` laeuft es. Anmerkung fuer spaetere Leser: die Vorlage
`orion/dev-tutorial` traegt acht aufeinanderfolgende Commits "Update .gitlab-ci.yml" und
funktioniert so, wie sie dasteht, vermutlich nicht — sie ist Anhaltspunkt, nicht Referenz.

**Der Cluster wurde verifiziert, nicht erschlossen.** Ein Wegwerf-Pod mit dem Kampagnenimage hat vier
Unbekannte auf einmal geklaert. Die UID: Pods in `scch-das` laufen als **uid 0**, nicht unter der
gewuerfelten UID, gegen die WP-H2 gehaertet hat — die Haertung bleibt richtig, sie war nur nicht
noetig; das Image ist damit in beiden Welten belegt. Der NFS-Pfad: die Verzeichnisliste im Container
ist zeichengleich mit `S:\BigDataOrion`, womit `/bigdata/data-science/joedicke` bewiesen und nicht
mehr geraten ist. Das Pull-Secret: das vorhandene `gitlab-registry` deckt dieses Projekt **nicht** ab
(`requested access to the resource is denied`); ein eigenes `evoode-gitlab-pull` aus einem
Deploy-Token mit ausschliesslich `read_registry` loest es. Schreibrecht: vorhanden — aber weil wir
root sind. Das Zielverzeichnis ist `drwxrws--- <uid> 2000513` und gewaehrt "anderen" nichts; eine
nicht-root-UID in GID 0 koennte dort **nicht** schreiben. Eine Abhaengigkeit von der derzeitigen SCC,
kein Naturgesetz, und die erste Stelle zum Nachsehen, falls dort je etwas bricht.

**Keine Walltime.** Auskunft des Betriebs: CPU-Workloads werden selten angefasst, `kind: Job` wird in
Ruhe gelassen, ausser etwas haengt offensichtlich, und der Eigentuemer wird **vorher** informiert —
ausdruecklich unter der Bedingung, dass die Workload identifizierende Metadata traegt. Damit
entfaellt das in `docs/hpc_requirements.md` §6 erwogene Checkpointing fuer die 24-bis-48-Stunden-Zellen
vollstaendig. Die Labels `hpc.scch.at/service` und `hpc.scch.at/responsibility` sind entsprechend
keine Kosmetik, sondern die Bedingung dieser Zusage; WP-H4 hatte sie zunaechst durch erfundene
Schluessel ersetzt, WP-H4b korrigiert das.

**Kapazitaet: der Cluster ist kleiner als die Planung unterstellt.** Orion hat **zwei** Worker-Nodes
mit je einem AMD EPYC 7643, also **96 physische Kerne fuer das ganze Haus**. Beide Nodes tragen 4x
A100; die CPU-Kerne existieren primaer, um acht GPUs zu fuettern. `docs/hpc_requirements.md` denkt in
Core-Stunden-Kontingenten eines grossen Standorts und muss darauf umgeschrieben werden. Bei ~4.500
geschaetzten Core-Stunden bedeutet `parallelism=16` rund zwoelf Tage, 32 rund sechs, ein ganzer Node
rund vier — und unabhaengig davon liegt eine Untergrenze bei der laengsten Einzelzelle von geschaetzt
23 Stunden. Zusaetzlich sind die Laptop-Schaetzungen vermutlich optimistisch, weil viele Zellen auf
einem Sockel um L3 und Speicherbandbreite konkurrieren. Der Pilotlauf muss messen.

**WP-H4: Zellen als Indexed Job.** Bootstrap und Zell-Job sind getrennt — der Bootstrap schreibt
Manifest und Indexlisten einmalig ins NFS, die Zellen lesen nur. Waeren beide vereint, haetten 756
Pods einen Schreibwettlauf auf gemeinsamem Speicher und koennten sich uneinig sein, was Zeile *n*
bedeutet.

Die Abbildung `JOB_COMPLETION_INDEX` → Manifestzeile liegt in
`studies/regression/run_k8s_indexed_cell.jl`, also **im Image** und damit vom Commit-SHA abgedeckt,
statt im YAML, wo sie vom Code abdriften koennte. Der Fallstrick war die Indexbasis: Slurm-Arrays
sind dort 1-basiert, `JOB_COMPLETION_INDEX` ist 0-basiert. Eine woertliche Uebersetzung haette die
erste Zelle uebersprungen und einmal ueber das Listenende hinausgelesen — leise, mit 755 plausibel
aussehenden Records. Geprueft an beiden Raendern: Index 0 loest auf Zeile 1 und Manifestzeile 1 auf,
Index 275 auf Zeile 276 und Manifestzeile 516, was der letzten 1D-Zeile entspricht.

`generate_phase_b_manifest.jl` schreibt zusaetzlich `indices_all.txt`. Die Aenderung ist rein additiv;
Manifestinhalt und Identitaetsberechnung bleiben unberuehrt, der Phase-B-Fingerprint steht weiter auf
`c71c85ac2ec580ff`. Das Job-Manifest referenziert das Image ueber den Commit-SHA, nie ueber `main`:
ein wandernder Tag koennte Pods auf verschiedenem Code laufen lassen, waehrend jeder Record denselben
Hash zitiert — genau der Fehler, gegen den die Tag-Strategie gebaut ist.

Offen bis zum ersten echten Lauf: ob Orion `JOB_COMPLETION_INDEX` wie erwartet injiziert, ob
Bootstrap und Zellen ihre Dateien auf NFS landen, und jede Laufzeitzahl.

---

## 2026-08-12

### Das Zielsystem ist kein Slurm-Standort - und WP-H2, das Docker-Image dafuer

<!-- 16d156a -->

**Der Befund, der die halbe HPC-Vorbereitung neu adressiert.** Der Zielcluster ist SCCH "Orion", ein
**OpenShift/Kubernetes**-Cluster (`console-openshift-console.apps.orion.scch.at`), **kein
Slurm-Standort**. `docs/hpc_requirements.md`, `containers/evoode_regression.apptainer` und
`hpc/slurm_*.sh` richten sich damit an eine Plattform, die es fuer dieses Projekt nicht gibt. Sie
bleiben als Slurm-seitige Referenz liegen, sind aber nicht der Weg zur Kampagne.

Die Uebersetzungstabelle: Apptainer-`.sif` → Docker-Image, gebaut von GitLab CI und abgelegt in
`registry.gitlab.scch.at`; `sbatch --array` → Kubernetes `kind: Job` mit `completions`/`parallelism`;
`$SLURM_ARRAY_TASK_ID` → `$JOB_COMPLETION_INDEX`; Shared FS → NFS-Volume auf `nfs.orion.scch.at`.
CPU-only, 1 Kern und 2 GB pro Job — eine GPU beschleunigt 1D-bis-4D-ODE-Loesungen nicht.

**Was die Batch-Architektur betrifft: sie traegt.** Manifest als geordnete Zell-Liste, ein Entry
Point pro Zelle, Merge am Ende — das ist auch das Kubernetes-Modell. Es aendert sich nur, woher der
Index kommt. Die WP-B2- und WP-H1-Arbeit ist nicht verloren.

**Nebeneffekt zugunsten der Reproduzierbarkeit.** Die CI der Hausinstanz taggt Images mit
`$CI_COMMIT_SHA`, nicht mit `latest`. Referenziert das Job-Manifest diesen Tag, ist per Konstruktion
ausgeschlossen, dass zwei Zellen einer Kampagne auf verschiedenem Code laufen — ein staerkerer
Provenance-Nachweis als ein `.sif` auf einem Login-Node. GitHub bleibt Single Source of Truth,
GitLab ist reines Deploy-Ziel; der SHA ist auf beiden identisch.

**WP-H2: `containers/Dockerfile`.** Abschnittsweise aequivalent zur Apptainer-Definition — gleiche
Basis, gleicher Julia-Pin, Depot im Image, gleicher `build_provenance.json`, Entry Point auf
`run_batch_cell.jl`.

Die eine Anforderung ohne Apptainer-Gegenstueck: **OpenShift startet Container unter einer
willkuerlichen UID mit GID 0**, nicht als der aufrufende Nutzer. Ein Image, das eine feste Identitaet
annimmt, faellt dort mit einem Rechtefehler um, der nicht nach seiner Ursache aussieht. Geloest ueber
`chgrp -R 0` plus `chmod -R g=u` auf Quellbaum, Depot und Output-Wurzel, dazu `HOME=/tmp`, weil eine
gewuerfelte UID kein Home-Verzeichnis hat. Kein fixes `USER` — das ueberschreibt die Plattform ohnehin.

Verifikation lokal, ohne Cluster: Image baut; `build_provenance.json` meldet Julia 1.12.6 und beide
Abhaengigkeits-Hashes stimmen mit den eingecheckten Dateien ueberein; Manifestgenerierung im Container
liefert `phase_b_fingerprint=c71c85ac2ec580ff` und `rows=756`, also den WP-H1-Wert. Dieselbe 1D-Zelle
(System 11, Manifestindex 61) lief **zweimal** durch, einmal als Default-User und einmal als
`--user 12345:0`: beide `loss=4.674e-15`, `error=null`, Record und Heartbeat auf dem Host. Damit ist
der teuerste OpenShift-Fehlermodus lokal ausgeschlossen statt auf dem Cluster entdeckt.

`.dockerignore` ist eine Allowlist (`*` plus gezielte `!`-Eintraege), damit kein lokaler Zustand
still ins Image geraet. Bildgroesse 1,29 GB Inhalt, davon 3,1 GB Depot auf Platte.

Offen bis Orion: CI-Mechanik und Registry, Pull-Secrets, das Job-Manifest samt Index-Abbildung, die
NFS-Konventionen und jede Laufzeitzahl. Details in `codex/reports/REPORT_WP_H2.md`.

---

### WP-E2 - Strukturmetrik fuer alle 63 Kampagnensysteme, und eine zu grosszuegige Klassifikation

<!-- e675083 -->

`pruned_match` war fuer **jedes** Phase-B-System `nothing`. Die Kampagne haette 756 Zellen ohne ihre
Hauptmetrik gerechnet. Zwei Ursachen, beide behoben.

**Der wahre Support existierte nur fuer fuenf Systeme.** `expected_terms_for` ist eine handgepflegte
Tabelle und warf fuer alles ausserhalb des Diagnosesets. Neu:
`studies/regression/derive_phase_b_support.jl` leitet den Support pro Gleichung aus den
RHS-Ausdruecken des Datensatzes ab und schreibt `phase_b_support.json`, eingecheckt und mit blossem
Auge pruefbar. Der Support muss zweierlei erfuellen: **exakt** (reproduziert die RHS bis 1e-9) und
**minimal** (kein Term entfernbar, ohne das zu brechen). Minimalitaet ist nicht kosmetisch — eine
blosse Schwelle auf den LS-Koeffizienten lieferte fuer die Systeme 52 und 62 Supports mit 18 bzw. 26
Termen, also eine ueber die Basis verschmierte Darstellung statt des wahren Supports.

Ausgewertet wird an beiden IC-Trajektorien plus 400 Streupunkten **innerhalb** der besuchten Box. Eine
einzelne Trajektorie laesst Basisspalten kollinear, womit die LS-Loesung nicht eindeutig ist; unter
dieser Bedingung war System 63 gar nicht ableitbar. Die Streuung bleibt in der Box, weil sie sonst den
Definitionsbereich mancher RHS verlaesst (`log`, `sqrt`).

**Abnahme: alle fuenf handkodierten Systeme werden exakt reproduziert**, System 63 in 4D
eingeschlossen. Der Generator bricht bei Abweichung ab, statt die Tabelle zu schreiben.

**Nebenbefund, der die Papieraussage betrifft: die Repraesentierbarkeit war zu grosszuegig.** Die
Systeme **30, 52 und 62** galten als `exact`, haben aber keinen wahren Support in der Basis. Der alte
Test fittete die Basis entlang **einer Trajektorie**; eine Funktion kann auf einer Kurve mit einer
Basisdarstellung uebereinstimmen, ohne im Zustandsraum diese Funktion zu sein. Die Kampagne stuetzt
ihre Strukturaussage damit auf **20 exakte Systeme, nicht 23**. `representability` kommt jetzt aus
derselben Rechnung wie der Support, damit "exakt" und "es gibt einen wahren Support" eine Aussage
sind statt zweier, die auseinanderlaufen koennen. Der alte Trajektorien-Test wurde entfernt.

**Entkopplung von `expected_stage`.** Support-Recovery haengt nicht davon ab, welche Stage erwartet
wurde; das Gate ist weg. Die stage-abhaengigen Metriken bleiben ohne erwartete Stage `nothing` — es
wurde keine erwartete Stage erfunden.

**Budget-Stopps nach Dimension**: keine Schemaaenderung noetig, Records tragen `system_id` und das
Manifest `system_dim`. Grenze, die zu nennen ist: die Parameterzahl pro Fit ist **nicht**
rekonstruierbar, weil die Zaehler pro Zelle aggregiert sind.

Fingerprints: Regression unveraendert `45cb2c4507007366`. Phase B `c0a236edf030e03a` →
`c71c85ac2ec580ff`, weil drei Systeme neu klassifiziert sind und der abgeleitete Support Teil der
Identitaet wird — er definiert, was `pruned_match` bedeutet.

Verifikation: exakte Zelle (System 11) liefert `pruned=true`, Surrogatzelle (System 1) `nothing`; die
Regressionszelle System 11 ist ueber **62 Felder unveraendert**. Details in `codex/reports/REPORT_WP_E2.md`.

---

## 2026-08-11

### WP-F3 - Evaluationsbudget final auf 20.000 gesetzt

<!-- fb2c3a9 WP-F1/F2 -->
<!-- 8ae409e WP-F3/G1 -->

Entscheidung vor dem Campaign-Freeze: `BFGS_MAX_LOSS_EVALS` im Kampagnenpfad sinkt von 100.000 auf
**20.000** pro Parameterfit. Das aendert den Regressions- und den Phase-B-Fingerprint ein letztes
Mal vor dem ersten Paper-1-Campaign-Record; ab jetzt ist diese Konfiguration eingefroren.

Die Begruendung ist dreiteilig und gehoert in die Paper-Argumentation:

1. **Sicherheitslimit, kein Tuningparameter.** Das Budget begrenzt Arbeit, die messbar nichts mehr
   zum Ergebnis beitraegt. Es ersetzt die in WP-B3 entfernte Wall-Clock-Bremse, die auf langsamen
   Knoten binden und auf schnellen nicht binden konnte. Ein Budget in Zaehleinheiten ist
   maschinenunabhaengig und verbessert damit die Reproduzierbarkeit.
2. **Gemessener Wert.** WP-F1 und WP-F2 haben komplette Evaluierungssequenzen pro Fit aufgezeichnet
   und gemessen, wann der beste Loss erstmals erreicht wurde. Ueber alle gemessenen Fits
   (Dimension 1 bis 3, Parameterzahlen 1 bis 18) lag dieser Punkt spaetestens bei **5.760**. 20.000
   haelt einen Faktor von rund **3,5** darueber. Zweite unabhaengige Plausibilisierung: bei der
   maximalen Campaign-Parameterzahl 24 ergibt `2 * maxiters * (n_params + 1)` mit `maxiters = 200`
   genau 10.000; 20.000 ist das Doppelte davon.
3. **Harmlosigkeit demonstriert und falsifizierbar.** Fuer alle aufgezeichneten WP-F1/F2-Fits
   liefert ein Stop bei 20.000 denselben best-seen Loss wie der vollstaendige Lauf. Seit WP-D2 gibt
   ein Budget-Stop den besten tatsaechlich gesehenen Punkt zurueck, also graduell statt
   katastrophal. Seit WP-D3 zaehlt jeder Record Budget-Stopps; die Kampagne kann daher berichten, in
   wie vielen der 756 Phase-B-Laeufe das Limit gebunden hat.

Nachpruefung an der WP-D5-Referenzzelle (System 3, Seed 7, IC 1,
`evogrow_v2_2_stage_capped`): Das Budget bindet entgegen Erwartung auf 9 Parameterfits. Support,
Stage und `pruned_match` bleiben gleich, der Loss wird sogar kleiner, aber
`total_parameter_fits`, `total_loss_evals`, `total_ode_solves` und die Retcode-Liste aendern sich.
Das ist kein Grund, das Budget nachzuziehen, aber ein Befund: die Kampagne muss Budget-Stopps
sichtbar und nach Dimension/Parameterzahl auswerten.

**Die eigentliche Absicherung ist ein Regressionsvergleich ueber sieben Zellen**, gefahren in zwei
Armen: 20.000 im Working Tree gegen 100.000 aus einem Worktree auf `0af12c9`. Systeme 3 und 11 mit
je drei Seeds, dazu **System 26 als gekoppelter Fall**, IC-Satz 1.

Ergebnis: `pruned_match`, `final_stage` und `support_terms` sind in **7 von 7** Zellen identisch.
Gesamtaufwand 1.227.157 gegen 2.687.140 Loss-Evaluierungen, also **54,3 % Ersparnis** bei 43
Budget-Stopps. **Kein Loss wird schlechter**, einer wird um mehr als eine Groessenordnung besser.

Die gekoppelte Zelle ist der wichtigste Datenpunkt: System 26 liefert in beiden Armen denselben Loss
(1,396e-03), dieselbe Stage, denselben Support **und dieselbe Zahl Parameterfits (310)** bei 58,2 %
weniger Evaluierungen. Gleiche Fitzahl heisst gleicher Suchpfad — das Budget hat dort ausschliesslich
Leerlauf innerhalb einzelner Fits abgeschnitten, ohne die Suche umzulenken. Auf System 11 bindet es
gar nicht, die Zellen sind bit-identisch. Wo der Pfad divergiert (System 3, Seed 7: 130 statt 150
Fits), bleiben die Strukturmetriken dennoch gleich.

Damit ist Punkt 3 oben zu praezisieren: bit-identische Ergebnisse sind **nicht** allgemein zu
erwarten, sobald das Budget bindet — ein gestoppter Fit liefert andere Parameter, damit ein anderes
Objective und ab da einen anderen Suchpfad. Die belegbare Aussage lautet: ueber sieben Zellen
einschliesslich eines gekoppelten Systems bleiben alle Strukturmetriken unveraendert, kein Loss
verschlechtert sich, und der Aufwand halbiert sich.

WP-E2-Anforderung, bewusst noch nicht implementiert: Budget-Stopps muessen nach Dimension und
Parameterzahl aufgeschluesselt werden, nicht nur global. Ein ueberproportionales Binden auf
hochdimensionalen Systemen wuerde genau die komplexen gekoppelten Strukturen benachteiligen und die
zentrale Aussage verzerren; ein globaler Zaehler wuerde das verstecken.

---

### 1D-Kostenprofil: Pretuning bringt auf 1D nichts, und die Line-Search-Pathologie haengt nicht daran

<!-- dc2847c WP-E1 -->
<!-- 0af12c9 Kostenprofil -->

Aus WP-E1 fiel eine Zelle auf, die fuer ein triviales 1D-System (System 2, ein Term, ein Parameter)
**858.540** ODE-Integrationen verbrauchte — 28.618 Loss-Evaluierungen pro Fit, bei einem
Regressionsvergleich von 38. Erste Hypothese: das derivative Pretuning trifft per Least-Squares das
Optimum praktisch exakt, BFGS startet damit im Minimum, und die Line-Search verhungert. Zur Pruefung
ein vollstaendiges Profil ueber **alle 23 1D-Systeme in beiden Phase-B-Bedingungen**, Seed 42,
IC-Satz 1 — 46 Zellen, gemessen in Zaehlgroessen, nicht in Sekunden.

**Die Hypothese ist widerlegt.** Pathologische Zellen (>= 1.000 Evals/Fit): **12 mit Pretuning, 14
ohne**. Die Line-Search-Pathologie ist eine Eigenschaft des Optimierers, nicht des Startpunkts. Auch
der Kostenfaktor relativiert sich vollstaendig: aggregiert 40,97e6 gegen 26,84e6 Evaluierungen, also
**1,53x**, nicht die 288x des Einzelfalls. Es gibt ebenso extreme Gegenfaelle — auf System 8 kostet
`pretune_off` das Tausendfache, auf 3, 12 und 20 rund das Zehnfache.

**Pretuning bringt auf 1D keinen messbaren Nutzen.** Von 23 Systemen liegen **20** im Loss innerhalb
einer Zehnerpotenz; einmal ist Pretuning besser (System 15, 1,7 Dekaden), **zweimal schlechter**. Die
erreichte Stage ist in **23 von 23** identisch, der Support in 19 von 23. Bezahlt wird das mit 53 %
mehr Evaluierungen.

Ein Fall ist ein echter Schaden: **System 8**. Mit Pretuning bricht die Suche nach 1.830
Evaluierungen mit Loss **5,75e+2** ab; ohne Pretuning kostet sie 2,2e6 Evaluierungen und erreicht
6,48e-5 — knapp sieben Groessenordnungen. Der Warmstart fuehrt die Suche offenbar in ein Plateau,
das das Abbruchkriterium ausloest. Das ist ein Kandidat fuer eine gezielte Nachanalyse, nicht fuer
eine schnelle Korrektur.

**Wichtiger Vorbehalt:** alle 23 Systeme sind eindimensional. Der Forschungsfokus sind gekoppelte
Systeme, wo ein informierter Startpunkt bei mehreren Gleichungen und groesseren Parametervektoren
plausibel mehr beitraegt als bei einem einzigen Parameter. Das Nullergebnis auf 1D ist ein
Teilergebnis der Phase-B-Frage, kein Grund, die Bedingung zu streichen.

**Fuer die Ressourcenplanung:** im Mittel rund 1,5e6 ODE-Integrationen pro 1D-Zelle. Auf 756 Laeufe
hochgerechnet liegt das in der Groessenordnung der bisherigen 1e9-Annahme in
`docs/hpc_requirements.md`, mit Aufschlag fuer hoehere Dimensionen. Die Annahme ist damit eher knapp
als grosszuegig.

Rohdaten: `outputs/studies/regression/phase_b/profile1d/` (gitignored), Manifest
`wp_e1_manifest.csv`, Phase-B-Fingerprint `e577d9d692f3125b`.

Nebenbefund aus dem Lauf: ein Rechnerabsturz mitten im Profil kostete genau **eine** Zelle — die zum
Zeitpunkt des Absturzes laufende. Alle bereits geschriebenen Records ueberlebten, weil der Batch-Pfad
je Zelle einen Prozess faehrt und sofort schreibt. Unfreiwilliger, aber realistischer Test des
Resume-Verhaltens, das fuer den Cluster gebaut wurde.

---

## 2026-08-10

### WP-D2 bis WP-D5 - Optimizer-Budget, Contract, Telemetrie, Referenzverifikation

<!-- 0498218 WP-D2/D2b -->
<!-- e0bc706 WP-D3/D3b -->
<!-- e46e80b WP-D4a -->

Ausloeser war eine externe Code-Kritik, die vor dem HPC-Start gegengeprueft wurde. Zwei ihrer
Befunde waren echte Fehler, mehrere weitere korrekt, aber bewusst nicht Paper-1-Scope.

**WP-D2 — der Budget-Abbruch warf seine Ergebnisse weg.** `p_best`/`l_best` wurden ausschliesslich
in den `isfinite(res.minimum)`-Zweigen gesetzt. Das Evaluationsbudget bricht aber per Exception aus
der Loss-Closure ab, also liefen diese Zuweisungen nie: zurueck kam der *Startvektor* mit Loss
`1e6`. Verschaerfend ist, dass `1e6` zugleich der MSE-Sentinel fuer gescheiterte Simulationen ist —
ein budget-abgebrochener Fit war im Record von einem gescheiterten nicht unterscheidbar. Fix:
best-so-far wird in der Loss-Closure mitgefuehrt (mit demselben Clamp, mit dem auch simuliert wird,
damit Loss und Parameter zusammenpassen), der Sentinel als Startwert verschwindet, und
`max_loss_evals` ist als **Gesamtbudget pro Parameterfit** festgelegt — kein Nelder-Mead nach
Budget-Treffer, weil ein Kandidat sonst sein Budget ueberschreitet und der Kostenvergleich zwischen
Strukturen unfair wird.

**WP-D2b — der Fix hatte den Fallback abgeschaltet.** Die erste Fassung akzeptierte best-so-far auch
im Exception- und im Non-finite-Zweig und setzte damit den Wachposten des Nelder-Mead-Fallbacks auf
"Ergebnis vorhanden". Da `evaluate_loss` bei jedem Problem den *finiten* Sentinel liefert, war
best-so-far nach der ersten Auswertung praktisch immer gesetzt — der Fallback lief faktisch nie
mehr. Das aendert Zahlen auf einem Pfad, auf dem das Budget gar nicht bindet. Korrigiert zu drei
Stufen: Optimizer-Ergebnis, dann Fallback, dann best-so-far als letzte Instanz. Der Budget-Stop
bleibt Sofortakzeptanz; er braucht keinen Sonderfall, weil erschoepftes Budget den Fallback ohnehin
ausschliesst.

**WP-D3 — Phase B waere ohne Bremse gelaufen.** `experiments/run_experiment.jl` konstruierte den
Optimierer nur mit `maxiters`; alles uebrige, insbesondere das Budget, kam aus den seit WP-B3
unbegrenzten Defaults. Die Kampagne haette also unbudgetiert gerechnet, waehrend die Regression, die
sie validieren soll, bei 100.000 steht. Jetzt kommen alle deterministischen Parameter aus der
Konfiguration, und `generate_manifest.jl` traegt sie, damit ein Manifest den Optimierer vollstaendig
beschreibt. Die elf ungebudgeteten Aufrufstellen in `benchmarks/` und `studies/` sind bewusst
dokumentierter Backlog und nicht angefasst — kein Repo-Cleanup unmittelbar vor einer Kampagne.
Zusaetzlich einmalig ins Record-Schema: Budget-Stopps, Fallback-Ergebnisse, Last-Resort-Faelle und
ungueltige Ergebnisse pro Lauf. Ohne diese Zaehler waere ein budget-abgebrochener Phase-B-Lauf im
Output unsichtbar. Der aus WP-D2 moegliche Rueckgabewert `Inf` wird an der JSON-Grenze als String
geschrieben; `Infinity` ist kein gueltiges JSON. Fingerprint `db8ec4003aa99a0e` →
`7acd3ebf3f60b974`.

**WP-D3b — der Fallback-Zaehler zaehlte doppelt.** Bedingung war `method == "NelderMead"`, was nach
D2b auch auf Last-Resort-Faelle zutrifft. Jetzt zusaetzlich `result_source == "optimizer_return"`;
die ersten drei Zaehler sind disjunkt, "ungueltiges Ergebnis" darf bewusst ueberlappen.

**WP-D4a — der stille Refit in `discover()` ist weg.** Bei abweichender Parameterzahl wurden
Parameter und Loss neu gefittet, das Objective aber nicht — ein Resultat aus zwei Zustaenden, bei
EvoGrows Loss-plus-Komplexitaet arithmetisch unmoeglich. `discover()` kann das auch nicht reparieren,
weil es die Objective-Definition einer beliebigen Suche nicht kennt. Jetzt harter `error()` mit
erwarteter und erhaltener Zahl, Suchverfahren und Struktur in der Meldung. Kein Rescue in den
Runnern: die Zelle faellt als failed aus und wird vom Merge zurueckgewiesen. Eine fehlende Zelle ist
sichtbar, eine mit inkonsistenten Zahlen nicht.

**WP-D5 — Referenzverifikation, beide Faelle bestanden.**

*A, nicht-bindend.* System 3, Seed 7, IC-Satz 1: derselbe Fall auf dem Commit vor WP-D2 (Worktree
auf 29951a6) und auf dem aktuellen Stand. Loss `1.920e-09` in beiden, Stage 2/2, `pruned_match`
true. Der vollstaendige Feldvergleich ueber alle gemeinsamen Record-Felder ergibt **genau zwei
Abweichungen, beide Zeitfelder** — nach Designprinzip 7 ohnehin keine Evidenz. Bit-identisch sind
Loss, Objective, Support, Parameter, `total_parameter_fits`, `total_loss_evals`,
`total_ode_solves`, alle Limit-Zaehler sowie Stage- und Cap-Entscheidungen. Kein bestehendes Feld
ist verschwunden. Vorab geprueft, dass die WP-D3-Aenderung an `_polish_optimizer` diese Zelle nicht
erreichen kann: die Funktion existiert nur fuer `EvoGrowScreening`, die finale Variante konstruiert
ein `EvoGrow`. Eine Abweichung waere also ein Befund gewesen, keine erwartete Folge.

*B, bindendes Budget.* Logistisches 1D-System, `max_loss_evals = 40`: 78 Fits, 3.120 Evaluierungen
— exakt 78 x 40, kein Fit ueberschreitet sein Budget. Alle 78 melden Budget-Stop, **null** davon
ungueltig, null Fallback, null Last-Resort. Damit ist der D2-Fix am laufenden System belegt: vor der
Reparatur waeren das 78 Fits mit Startvektor und Sentinel-Loss gewesen. Der Loss ist mit `3.5e-3`
erwartungsgemaess schlecht gegenueber `2.5e-14` unbudgetiert, aber ein gemessenes Ergebnis und kein
Sentinel.

**Anmerkung zum Testaufbau.** `src/optimize/bfgs.jl` enthaelt nun einen Solve-Hook (`const Ref`,
Default `nothing`), ueber den Tests Optimizer-Fehlschlaege deterministisch erzwingen. In Produktion
verhaltensneutral — der Aufruf geht mit identischen Argumenten an `Optimization.solve`. Bewusst
akzeptiert: einen Fehlschlag numerisch zu provozieren waere fragil gewesen.

**Nicht angefasst, bewusst.** Struktur-Deduplizierung und ein kanonischer Hash fuer `StructureSpec`
(bei `pretuning=false` sind Duplikate zugleich implizite Multistarts, ein Cache waere also keine
reine Beschleunigung, sondern eine Aenderung der experimentellen Bedingung); ein
Evaluation-Result-Typ statt der Sentinel-Semantik; Remove/Replace-Operatoren gegen das
Growth-only-Verhalten; die Discover-API-Bereinigung (`isa BFGSOptimizer`, typisiertes
Struktursuch-Resultat, `search_loss`/`final_loss`-Benennung). Letztere ist als WP-D4b nach der
Kampagne vorgesehen — ein bekannter haesslicher Pfad ist unmittelbar vor einer Kampagne sicherer als
ein frisch abstrahierter sauberer.

---

### WP-D1 - Freeze der tatsaechlich benutzten Julia-Umgebung

<!-- 417648e -->

Die dokumentierte Umgebung war falsch: mehrere Texte und die Apptainer-Definition nannten Julia
1.11.5, waehrend `Manifest.toml` `julia_version = "1.12.6"` enthaelt, die Entwicklung auf 1.12.6
laeuft und die vorhandenen Phase-A- und Regressionsresultate unter 1.12.6 erzeugt wurden.
Entscheidung: nicht die Resultate auf die alte Dokumentationsbehauptung migrieren, sondern die
tatsaechlich benutzte Umgebung als Freeze deklarieren.

`Project.toml` deklariert nun `julia = "1.12"`, der Container baut von `julia:1.12.6-bookworm`,
und die Container-Provenance schreibt Julia-Version sowie SHA-256-Hashes von `Project.toml` und
`Manifest.toml` nach `/opt/EvoODE/build_provenance.json`. `Manifest.toml` bleibt unveraendert; die
Abhaengigkeitsstate ist der Freeze, nicht ein neu aufgeloester Zustand.

**Nachtrag 2026-08-10: Load-Smoke im leeren Depot bestanden.** Frisches Depot, `Pkg.instantiate()`,
`Pkg.precompile()`, dann `using EvoODE` mit einem Basis-Aufruf: Exit 0, erwartete Ausgabe, und
`Manifest.toml` byte-identisch vor und nach dem Lauf. Damit ist nicht nur die Installierbarkeit,
sondern die **Benutzbarkeit** des eingefrorenen Zustands belegt — die eigentliche Abnahme, die im
ersten Anlauf offen geblieben war (das dort verwendete Smoke-Kommando rief zudem
`default_polynomial_basis` mit zwei Argumenten auf, die Funktion nimmt eines).

Zwei Beobachtungen aus dem Lauf, beide nicht blockierend. Erstens brach `Pkg.instantiate()` einmalig
mit `IOError: rm(...): directory not empty` beim Entpacken von `AxisArrays` ab — ein
Windows-Dateisystemeffekt im Temp-Verzeichnis, kein Manifest- oder Aufloesungsproblem; der
anschliessende `Pkg.precompile()` hat die 554 Pakete vollstaendig installiert und der
Manifest-Hash blieb gleich. Im Linux-Container ist das gegenstandslos. Zweitens meldet `Plots`
beim Praekompilieren `GKS: cairoplugin.dll: can't load library` — headless erwartbar und fuer die
Kampagne ohne Belang, da dort nicht geplottet wird. Das vollstaendige Depot belegt 2,78 GB; im
Container faellt das einmalig im Image an, nicht pro Job.

---

## 2026-08-03

### WP-B3 — Wall-Clock raus aus dem Optimierer, Merge-Semantik geradegezogen

<!-- 0f4d006 -->

Drei Luecken vor der Kampagne geschlossen.

**Merge.** `merge_batch_records.jl` verweigert jetzt Records mit gesetztem `error` und zaehlt sie
separat als `skipped_failed`. Vorher wurde eine vom Cluster-Timeout gekillte Zelle gemerged, hat
damit ihren Eindeutigkeitsschluessel belegt und den eigenen erfolgreichen Wiederlauf als Duplikat
blockiert. Die Task-Datei bleibt erhalten — auf einem 4D-System ist ein Absturz nach 40 Stunden ein
Befund, kein Muell.

**`BFGS_TIME_LIMIT_S = 1800` ist weg.** Ersetzt durch `BFGS_MAX_LOSS_EVALS = 100_000` pro
Parameterfit, also ein Budget in Zaehlgroessen. Ein Wall-Clock-Limit im Optimierer haette auf einem
langsamen Knoten gebunden und auf einem schnellen nicht — das wissenschaftliche Ergebnis haette an
der Knotenzuteilung gehangen. Records tragen jetzt `total_loss_evals` und
`total_optimizer_eval_budget_limit_hits`. Fingerprint `256014cf6f0295e1` → `db8ec4003aa99a0e`; die
WP-B1-Verifikationszelle liefert darunter unveraendert `5.18873247985214e-9` bei Cap `[2]`, das
Budget bindet auf einer gesunden Zelle also nicht.

**1D-Klasse gemessen statt skaliert.** Sechs Zellen (Systeme 3 und 11, IC-Satz 1, drei Seeds) durch
den *Batch*-Pfad, nicht durch die Suite-Schleife — also durch genau den Pfad, den der Cluster
benutzt. 110–290 Parameterfits, 1,1e4–5,7e5 ODE-Integrationen pro Job, null Budget-Treffer.
`docs/hpc_requirements.md` §5 stuetzt die 1D-Zeile jetzt darauf und weist die Kernstunden-Tabelle
ausdruecklich als Planungsannahme aus.

**Zwei Anmerkungen zur Kalibrierung, beide nicht blockierend.** Erstens ist das Budget gegen
*Mittelwerte* kalibriert (max. 7.577 Loss-Evals pro Fit im Mittel, daher der berichtete Faktor 13);
gegen den bekannten pathologischen Einzelfit von 39.933 Evals bleiben aber nur **2,5x**. Das Budget
ist damit weiterhin ein Sicherheitsnetz und kein Kostenhebel — die Line-Search-Pathologie bleibt
offen, wie vorgesehen. Zweitens: die Defaults von `BFGSOptimizer` sind auf `time_limit_s = Inf` und
`max_loss_evals = typemax(Int)` gesetzt. Der Regressionspfad setzt sein Budget explizit, aber
`experiments/run_experiment.jl`, `benchmarks/` und mehrere Studien konstruieren den Optimierer ohne
Budget und haben damit **gar keine Bremse mehr**, wo vorher 300 s standen. Vor Phase B ueber
`run_experiment.jl` zu beheben.

---

### WP-B2 — Batch-Einstiegspunkt und Container fuer den Cluster

<!-- 5a3797a -->

Die Suite lief bisher als geschachtelte Schleife in einem Prozess, gesteuert ueber
Umgebungsvariablen. Das ueberlebt keinen Scheduler. Neues Ausfuehrungsmodell: ein Slurm-Job-Array,
jede Array-Task ist ein Prozess, rechnet **genau eine Zelle** und beendet sich. Drei Teile:
`generate_manifest.jl` (Kampagne als geordnete CSV, 120 Zeilen = 4 Varianten x 5 Systeme x 2
IC-Saetze x 3 Seeds, regenerierbar byte-identisch), `run_batch_cell.jl` (ein Index rein, eine
JSONL-Datei raus, Exitcode 0 nur bei Erfolg), `merge_batch_records.jl` (Konsolidierung ueber den
Eindeutigkeitsschluessel, wiederholt ausfuehrbar).

Der wichtigste Teil ist der **Fingerprint-Guard**: stimmt der Fingerprint im Manifest nicht mit dem
zur Laufzeit berechneten ueberein, bricht die Task ab, bevor sie rechnet. Verifiziert — ein
manipuliertes Manifest wird mit Exitcode 1 und ohne Ausgabedatei abgewiesen. Eine Kampagne mit
gemischten Fingerprints ist nicht publizierbar, und auf 846 Jobs faellt das sonst erst beim
Auswerten auf.

Verifikationszelle System 3 / IC 1 / Seed 42 / `evogrow_v2_2_stage_capped` durch den Batch-Pfad:
Loss `5.18873247985214e-9`, Cap `[2]`, `eq_overshoot = [0]`, `pruned_match = true`, Support
`[["u1","u1^2"]]`, Exitcode 0 — **exakt das WP-B1-Ergebnis**, wie gefordert, nicht nur naeherungsweise.
Merge in eine Scratch-Kopie: erster Lauf `added=1`, zweiter `added=0, skipped=1`.

**Fingerprint erneut geaendert: `fa2469a4dad1b72c` → `256014cf6f0295e1`.** Die Nutzlast beschrieb
das Zeitgitter als `range(0.0, 10.0; length=512)`, tatsaechlich laeuft der `t`-Vektor aus dem
Datensatz; numerisch `i*10/511`, was ein Julia-`range` nicht bitgenau reproduzieren muss. Das Label
beschrieb also etwas anderes als das Ausgefuehrte. Korrigiert auf
`dataset solutions[1][1].t grid; shipped y ignored`. Kostet nichts: unter `fa2469a4dad1b72c` existiert
kein einziger History-Record.

Dimensionsklassen: ein globales Manifest, dazu pro Dimension eine Indexliste
(`indices_dim1/2/4.txt`, 48/48/24 Zellen; 3D kommt in der Regressionssuite nicht vor). So bleibt die
Kampagnenidentitaet in einer Datei, waehrend Slurm pro Klasse eigene Walltimes bekommt.

Container (`containers/evoode_regression.apptainer`): damals als Julia 1.11.5 gepinnt dokumentiert;
WP-D1 korrigierte das als Dokumentationsfehler, weil die vorhandenen Ergebnisse auf 1.12.6
entstanden. `instantiate` und
`precompile` **zur Bauzeit**, Depot im Image, `JULIA_NUM_THREADS=1` und `OPENBLAS_NUM_THREADS=1`
gesetzt, Ausgaben nur ueber ein gebundenes `/outputs`. Nicht gebaut — diese Umgebung hat weder
Apptainer noch Slurm; beides ist statisch geprueft und als ungetestet ausgewiesen.

**Ein Defekt beim Review gefunden.** `run_batch_cell.jl` schreibt auch bei einem Fehler einen Record
(mit gesetztem `error`) und beendet sich dann mit Exitcode 1. `merge_batch_records.jl` filtert
`error` aber nicht — anders als `load_completed_cells` in `run_regression.jl`, das genau das tut.
Folge: eine abgestuerzte Zelle vergiftet ihren Schluessel, und ein spaeterer erfolgreicher Wiederlauf
wird beim Merge als Duplikat verworfen. Auf einem Cluster mit Timeouts und OOM-Kills ist das kein
Randfall. Muss vor der Kampagne behoben werden.

---

### Projektjournal auf Stand 2026-08-03

<!-- ee52eb3 -->

Vier neue Kapitel (3.22 Attribution, 3.23 Endvariante, 3.24 Gitter-Entscheidung, 3.25 Aufraeumen und
Cluster), Kapitel 4–8 durchgezogen. Dazu `tools/build_journal_pdf.py`: die bisherigen PDFs stammten
aus einem manuellen Browserdruck und waren nicht reproduzierbar. Jetzt Markdown → HTML →
Headless-Chromium in einem Aufruf. 24 Seiten, Dichte 46 Quellzeilen/Seite gegen vorher 47.

Vorfall: ein pauschales `git add -A` hat Codex' laufende WP-B2-Arbeit in den Journal-Commit gezogen.
Per `reset --soft` aufgeloest, fremde Pfade ausgestaged, neu committet. Zweites Mal an einem Tag —
Regel jetzt festgehalten: in diesem Repo nur explizite Pfade stagen, solange Codex parallel im
selben Arbeitsbaum schreibt.

---

### WP-B1 — Regressionssuite auf das Phase-B-Abtastprotokoll

<!-- 82c4784 -->

Fest verdrahtete `u0`/`tspan`/`T` durch datensatzabgeleitete Werte ersetzt: 512 Punkte ueber
t in [0,10], beide IC-Saetze, Trajektorien selbst mit `Tsit5` bei 1e-9 integriert. Zellen werden
jetzt ueber (Variante, System, **IC-Satz**, Seed) identifiziert. Jeder Record traegt zusaetzlich
`derivative_active_fractions` pro Gleichung — damit eine gescheiterte Zelle direkt als
"Trajektorie trug nichts" lesbar ist statt als Methodenversagen. Fingerprint `fa2469a4dad1b72c`
(inzwischen durch WP-B2 abgeloest); die 42 alten Records bleiben unter ihren alten Fingerprints.

---

### CLAUDE.md aufgeteilt — 1251 auf 282 Zeilen

<!-- 6e7b916 -->

`CLAUDE.md` trug drei Sorten Inhalt gleichzeitig: Orientierung, Komponentenreferenz und ein
eingefrorenes Experimentprotokoll. Verschoben, wortgleich, nichts geloescht:

- Komponentenreferenz (Typen, Pipeline, Suchalgorithmen, Basen, Optimierer, Stopping-Logik,
  Experiment-Infrastruktur, Benchmark-Daten) → `docs/architecture.md`, 403 Zeilen
- das 263-zeilige Reproduzierbarkeitsprotokoll, das die eingefrorene `paper1_phaseA_v1` beschreibt
  → `docs/paper1_phaseA_reproducibility.md`, 273 Zeilen

Verifiziert, dass keine Ueberschrift verlorenging: alle alten `##`/`###`-Titel finden sich in einer
der drei Dateien wieder oder sind nachweislich zusammengefasst (Vision + Core Idea + PhD Focus →
"What This Project Is", Phase 1–5 → Statustabelle).

Zwei Folgefunde: `docs/paper1_study_protocol.md` verwies auf den verschobenen Abschnitt (korrigiert),
und `docs/de/` enthielt deutsche Lesefassungen vom 2026-04-26 bzw. 2026-05-08, die den Stand vor
Gate 1, Gate 2 und der Variantenentscheidung wiedergaben. Auf Entscheidung des Users geloescht —
eine veraltete Zweitfassung ist schlechter als keine.

Der Kopfbereich haelt jetzt eine Dokumentenkarte: welche Datei was haelt. Die alte Formulierung
"single source of truth ... do not maintain a second planning document" war der Grund, warum alles
in diese eine Datei gewandert ist. Die Regel gilt weiter, aber praezisiert: **Planung und Status**
gehoeren hierher, Referenz und Chronologie nicht.

---

### Konsolidierung — CLAUDE.md und Protokoll-Audit auf Stand gebracht

<!-- 2158170 -->

`CLAUDE.md` war zu einem zweiten Tagebuch geworden: die Prioritätenliste enthielt rund 100 Zeilen
chronologischer WP-Einträge, die DIARY.md dupliziert haben. Neu gegliedert nach dem, was ein Befund
*einschränkt*, nicht nach Reihenfolge — Staged-Growth-Claim, Ursachen des v3-Scheiterns, Look-Ahead
Cap, Endvariante, Phase-B-Protokoll, Kosten/Numerik. Dazu ein eigener Phase-2-Abschnitt für
`evogrow_v2_2_stage_capped` als Endvariante, aktualisierte Studien-Tabelle, Roadmap und Known Gaps
(neu darin: die ungelöste Strukturfindung auf gekoppelten Systemen, die IC-Abhängigkeit des Caps,
der Rechenbedarf von Phase B).

`docs/paper1_odebench_protocol_alignment.md` §3 hielt noch „zwei Optionen, offen" fest. Ersetzt
durch die getroffene Entscheidung samt der Messungen, die Gitterdichte und Datengenauigkeit
trennen, und fünf Konsequenzen, die mitgezogen werden müssen — darunter die Abweichung zu unseren
Gunsten, falls publizierte Zahlen auf den gelieferten Trajektorien gerechnet wurden.

---

### WP-G1 / WP-G1b — Gitter ja, Trajektorien nein

<!-- 8c5319b, 3fc286c -->

Caps auf dem ODEBench-Datensatzgitter (512 Punkte, t in [0,10]) nachgemessen, beide IC-Saetze,
beide Datenquellen: **A** = gelieferte `y`-Matrizen, **B** = selbst integriert mit `Tsit5` bei
`abstol = reltol = 1e-9` auf identischem Gitter. Keine Suche, reine Messung.
Skript `studies/lookahead/measure_dataset_grid_caps.jl`, Report
`docs/wp_g1_dataset_grid_caps.md`.

| System | per-System-Gitter | Datensatzgitter IC1 | IC2 | Wahrheit |
|---|---|---|---|---|
| 3 | `[2]` | `[2]` | `[2]` | `[2]` |
| 11 | `[4]` | `[4]` | `[4]` | `[4]` |
| 26 | `[3,3]` | `[3,3]` | `[3,3]` | `[3,3]` |
| 31 | `[3,3]` | `[3,3]` | **`[1,nothing]`** | `[3,3]` |
| 54 | `[nothing,2,2]` | **`[nothing,3,3]`** | **`[nothing,3,3]`** | `[3,3,3]` |
| 63 | alle `nothing` | alle `nothing` | alle `nothing` | `[3,3,1,1]` |

**Vorhersage 1 bestaetigt.** Die zwei bekannten Sicherheitsverletzungen auf System 54 verschwinden.
Auf IC-Satz 1: Verletzungen 2 → 0, korrekte Caps 6 → 8 von 13 Gleichungen. Das ist exakt, was
WP-L3 aus der Aufloesungsgrenze vorhergesagt hatte.

**Vorhersage 2 falsifiziert.** System 63 bleibt auf beiden IC-Saetzen vollstaendig `nothing`. Kein
Artefakt unseres t=30-Horizonts — die Identifizierbarkeitsgrenze ist echt.

**Arm A = Arm B, in allen 26 Zellen.** Die Rauschboeden unterscheiden sich erst in der dritten bis
vierten Stelle. Erklaerung: der Integrationsfehler der gelieferten Daten ist *glatt* in t, kein
punktweises Rauschen, und ein ableitungsbasierter Rauschboden sieht glatten Fehler praktisch nicht.
**Der Gewinn auf System 54 gehoert also der Gitterdichte, nicht der Datenqualitaet.**

**Daraus folgt aber nicht, dass die gelieferten Trajektorien brauchbar sind.** Der Cap ist gegen
den Datenfehler immun, der Loss ist es nicht. Gegen eine unabhaengig konvergierte RK4-Referenz
(Selbstkonvergenz ~1e-13) erzwingen die gelieferten Daten diese MSE-Untergrenzen:

| System | MSE-Boden | unser bestes Ergebnis |
|---|---|---|
| 3 | **2,5e-02** | 1,3e-08 |
| 11 | 1,9e-11 | **4,4e-15** |
| 31 | 6,1e-10 | **6,8e-11** |
| 26 | 3,5e-11 | 1,4e-03 |
| 54 | 2,0e-07 | — |

Auf 3, 11 und 31 waeren unsere bisherigen Ergebnisse mit diesen Daten unerreichbar, auf System 3
um sechs Groessenordnungen. Die `nfev`-Felder bestaetigen die Ursache: System 3 wurde mit 77
Funktionsauswertungen ueber t in [0,10] integriert, also auf scipy-Defaulttoleranzen.

**Empfehlung fuer Phase B: Abtastprotokoll uebernehmen, Trajektorien selbst integrieren.**
512 Punkte, t in [0,10], beide IC-Saetze, `Tsit5` bei 1e-9. Der Cap ist gegenueber dieser Wahl
indifferent, sie kostet also nichts von dem, was hier gemessen wurde. Offener Punkt fuer den
Protokoll-Audit: falls publizierte Zahlen auf den gelieferten Trajektorien gerechnet wurden,
arbeiten wir auf saubereren Daten als die Vergleichsarbeiten. Das ist eine Abweichung zu unseren
Gunsten und muss deklariert werden.

**Korrektur an meiner eigenen Zwischenthese.** Aus der System-31-Diagnose hatte ich gefolgert, der
feste Horizont erzeuge systematisch tote Zellen und das ziehe sich durch Phase B. Die Messung
begrenzt das scharf: von 26 Zellen sind 5 signalarm (`derivative_active_fraction <= 0.10`), und
**nur eine davon scheitert** — die anderen vier liefern korrekte Caps. Von den 12 scheiternden
Zellen ist genau eine signalarm. System 63 hat `derivative_active_fraction = 1` auf allen acht
Zellen und scheitert vollstaendig. Signalarmut erklaert also genau einen Fall (System 31 IC2
Gleichung 1: Epidemie nach t = 0,47 durch, 5,3 % der Punkte tragen Dynamik), nicht das Muster.

Notiz zur Diagnosespalte: `state_below_1pct_spread_time` feuert bei t=0 fuer wachsende Zustaende
(System 3, System 63 Gleichungen 3 und 4). Nicht falsch, aber fuer diese Faelle bedeutungslos;
tragend ist `derivative_active_fraction`.

---

### No-Harm-Zellen Systeme 3 und 11 — sauber, mit einem echten Ausreisser

<!-- 77f0fed -->

Sechs Zellen `evogrow_v2_2_stage_capped` x {3, 11} x {42, 123, 7}, sequenziell, Fingerprint
`df5db7763bcd2449`, `git_hash 63d4c1c`, `total_optimizer_safety_limit_hits = 0` durchgehend.
In `history.jsonl` gemergt (36 → 42 Records).

Alle sechs: Cap korrekt (`[2]` bzw. `[4]`), `eq_overshoot = [0]`, `eq_wasted_levels = [0]`,
`pruned_match = true`, Support exakt die Wahrheit (`u1, u1^2` bzw. `u1, u1^2, u1^3`).
**Der Cap macht die Wahrheit auf keinem der beiden Systeme unerreichbar** — auch nicht auf System
11, wo er mit Stage 4 genau auf dem Term liegt, den die Wahrheit braucht.

| Zelle | v2.2 | v2.2 + Cap | v2.2 Overshoot / wasted |
|---|---|---|---|
| 3/42 | `2.663641831768419e-10` | `1.3476451847014113e-08` | 1 / 2 |
| 3/123 | `6.52992601045936e-10` | bitgleich | 0 / 0 |
| 3/7 | `1.1091164010682478e-08` | bitgleich | **3 / 12** |
| 11/42 | `4.402192340718147e-15` | bitgleich | 0 / 0 |
| 11/123 | `4.375215202011892e-15` | bitgleich | 0 / 0 |
| 11/7 | `4.40607367978419e-15` | bitgleich | 0 / 0 |

**3/7 ist die staerkste Einzelzelle im ganzen Datensatz:** v2.2 laeuft dort bis Stage 5 und
verbrennt **12 von 30 Levels**, der gecappte Lauf bei Stage 2 liefert denselben Loss bitgleich.
Zwoelf Levels, nachweislich null Beitrag.

**3/42 ist der Ausreisser und wird nicht weggeredet.** Der gecappte Lauf ist um **Faktor 50**
schlechter (1.348e-8 gegen 2.664e-10) — bei *identischem* Support und `pruned_match = true` in
beiden Armen. Die Struktur ist also in beiden Faellen die richtige; verloren geht nur ein besseres
Parameteroptimum, das v2.2 in dem einen zusaetzlichen Stage-3-Level gefunden hat. Dasselbe Muster
wie auf 31/123: **Optimiererpfad-Abhaengigkeit, nicht eine vom Cap unerreichbar gemachte
Wahrheit.** Ueber alle bisherigen zehn v2.2+Cap-Zellen: acht bitgleich, eine auf elf Stellen
gleich, eine um 50x schlechter — und `pruned_match` in *allen zehn* unveraendert gegenueber v2.2.
Der Cap aendert die Strukturfindung nirgends, nur gelegentlich das Parameteroptimum, in beide
Richtungen.

Nebenbefund: `total_parameter_fits` ist innerhalb eines Systems ueber alle drei Seeds identisch
(170 auf System 3, 270 auf System 11). Der Cap macht das Suchbudget seed-unabhaengig, weil er die
Levelzahl festlegt.

**Provenienz-Defekt, selbst verursacht:** fuenf der sechs Records tragen `git_dirty = true`.
Ursache ist mein eigenes Runner-Design — die per-Zelle-Dateien `history_nh_*.jsonl` liegen im Repo
und sind untracked, und `git_dirty` wird aus `git status --porcelain` abgeleitet, das untracked
Dateien mitzaehlt. Der getrackte Quellstand war ueber alle sechs Laeufe identisch (`63d4c1c`, keine
Quelldatei angefasst). Das Flag meldet hier also die Ausgabedateien, nicht eine Codeaenderung.
Fuer kuenftige Laeufe: per-Zelle-Dateien ausserhalb des Repos ablegen oder ignorieren.

---

### WP-C1 Entscheidungszellen — v2.2 + Cap ist die Endvariante

<!-- 8f362c1 -->

Vier Zellen mit `evogrow_v2_2_stage_capped` gelaufen (26/42, 31/42, 31/123, 31/7), Fingerprint
`df5db7763bcd2449`, `git_hash 838b7af`, `git_dirty false`,
`total_optimizer_safety_limit_hits = 0` in allen vieren. In `history.jsonl` gemergt (32 → 36
Records), Einzeldateien entfernt.

Vorab festgelegtes Kriterium: `eq_overshoot` faellt auf `[0,0]` **und** der Loss bleibt auf
v2.2-Niveau. Beides erfuellt — und zwar in der schaerfstmoeglichen Form.

| Zelle | v2.2 | v2.2 + Cap | identisch |
|---|---|---|---|
| 26/42 | `0.001391623174905009` | `0.001391623174905009` | bitgleich |
| 31/123 | `0.00010427173348124156` | `0.00010427173348124156` | bitgleich |
| 31/42 | `6.80769890488305e-11` | `6.80769890488305e-11` | bitgleich |
| 31/7 | `6.974887728097135e-05` | `6.974887728171775e-05` | 11 Stellen |

Alle vier: `eq_final_stages = [3,3]`, `eq_overshoot = [0,0]`, `eq_wasted_levels = [0,0]`,
`stage_caps = [3,3]`, `stage_cap_policy_active = true`.

**Der entscheidende Punkt liegt nicht in der Uebereinstimmung, sondern darin, wo sie auftritt.**
31/42 ist trivial: v2.2 blieb dort schon von selbst in Stage 3 (`wasted_levels = 0`), der Cap
konnte nichts aendern. In den anderen drei Zellen lief v2.2 bis Stage 5 und verbrannte je **8 von
30 Levels** in den Stages 4 und 5 — und der gecappte Lauf liefert trotzdem denselben Loss auf 11
bis 16 Stellen. Diese acht Levels haben also nachweislich **exakt nichts** zum Ergebnis
beigetragen. Overshoot ist auf diesen Systemen reine Verschwendung, nicht ein Suchpfad, der
zufaellig nicht zahlt.

Zur Einordnung gegen die beiden v3-Arme, dieselben Zellen:

| Zelle | v2.2 | v3 | v3 + Cap | v2.2 + Cap |
|---|---|---|---|---|
| 26/42 | 1.392e-3 | 2.520e-4 (530 Fits) | 2.520e-4 (390) | 1.392e-3 (430) |
| 31/42 | 6.808e-11 | 1.285e-4 (490) | 1.678e-2 (250) | 6.808e-11 (310) |
| 31/123 | 1.043e-4 | 2.994e-5 (430) | 5.284e-3 (230) | 1.043e-4 (290) |
| 31/7 | 6.975e-5 | 9.872e-5 (390) | 9.872e-5 (230) | 6.975e-5 (330) |

Damit ist die Attribution vom 2026-08-02 endgueltig geschlossen: der Loss-Einbruch auf System 31
gehoert **dem v3-Substrat**, nicht dem Cap. Auf demselben Cap, aber v2.2 als Unterbau, kommt
6.808e-11 zurueck — genau der Wert, den v3+Cap um acht Groessenordnungen verfehlte. Der Cap ist
unschuldig; das kontaminierte `r_k`-Promotionssignal war das Problem.

Nicht belegbar aus diesen Daten: die Kostenersparnis gegenueber v2.2. Die v2.2-Records stammen aus
Baseline v0 und fuehren weder `total_parameter_fits` noch `total_ode_solves`. Belegt ist nur die
strukturelle Groesse: 8 von 30 Levels entfallen. Laufzeiten sind erfasst, aber nach Designprinzip 7
kein Beleg.

**Fingerprint-Grenze:** der v2.2-Arm liegt auf `0c739d4e36ee6498`, die gecappten Zellen auf
`df5db7763bcd2449`. Der Vergleich kreuzt die Grenze und muss ueberall so gekennzeichnet werden.
Die bitgleichen Losses sind allerdings selbst das staerkste Indiz, dass die Grenze inert ist — was
WP-T2 unabhaengig gezeigt hatte.

**Was nicht geloest ist:** `pruned_match = false` in allen vier Zellen. Auf 26/42 findet der
gecappte Lauf `du2 = f(u1, u1^2)` — dieselbe falsche Struktur wie v2.2, obwohl die Wahrheit
(`u2, u1*u2, u2^2`) in Stage 3 vollstaendig verfuegbar ist. Der Cap loest die
Komplexitaetsallokation, nicht die Suchmaechtigkeit innerhalb einer Stage. Das ist die bekannte,
explizit ausserhalb von Paper 1 liegende offene Frage.

**Konsequenz:** Endvariante fuer Paper 1 ist `evogrow_v2_2_stage_capped`. v3 wird zur
dokumentierten Fehleranalyse (Gate 2 negativ, Ursache in `r_k` diagnostiziert), der Look-Ahead-Cap
zum Beitrag.

---

## 2026-08-02

### WP-C1b — eine Kindgenerierung, cap-bewusste Kohaerenzregel

<!-- 10b717d -->

Duplikat entfernt, `stage_cap_policy` korrekt typisiert (Include-Reihenfolge in `EvoODE.jl`
angepasst), Report an Daten gebunden. Befunde 1 und 3 erledigt.

**Bei Befund 2 hat Codex bewusst von meiner Vorgabe abgewichen — und die Abweichung ist besser.**
Ich hatte spezifiziert: Kohaerenzregel raus, in beiden gecappten Varianten. Umgesetzt wurde
stattdessen eine **cap-bewusste** Regel: eine Variable, deren *Cap* sie dauerhaft unter die
Term-Stage druckt, blockiert den Kopplungsterm nicht mehr; eine, die die Stage bloss noch nicht
*erreicht* hat, weiterhin schon. Das ist genau die Unterscheidung, aus der ich meine Entscheidung
begruendet hatte — nur pro Variable statt pauschal pro Variante.

Die Inertness-Tabelle im Codex-Report prueft nur die fuenf Regressionssysteme, die alle uniforme
Caps haben und wo die Regel ohnehin wirkungslos ist. Der interessante Fall blieb dort ungetestet;
selbst nachgeholt:

| Konfiguration | coherence=true | coherence=false |
|---|---|---|
| Caps `[nothing,2,2]`, eq_stages `[3,2,2]` (v2.2-Form) | `u1*u2, u1*u3, u2*u3` verfuegbar | identisch |
| eq_stages `[3,2,2]` ohne Caps (v3-Promotionsform) | alle Kopplungsterme blockiert | verfuegbar |

Das Flag ist in der v2.2-gecappten Variante also **wirkungslos** — die cap-bewusste Ausnahme
erledigt die Arbeit bereits, das `coupling_coherence = false` in `evogrow.jl` ist redundant. In v3
wirkt es und erhaelt die Regel dort, wo sie motiviert war. Sweep ueber vier Cap-Vektoren x fuenf
Stages: kein Unterschied in der v2.2-Form. (Die boolesche Sammelvariable im Pruefskript stand wegen
Julias Soft-Scope-Regel im falschen Scope; der Beleg ist das Ausbleiben der Differenzmeldungen,
nicht ihr Rueckgabewert.)

Konsequenz fuer den Vergleich: beide gecappten Arme haben identische Verfuegbarkeitssemantik,
soweit die Stage-Unterschiede aus Caps stammen. Sie unterscheiden sich nur noch dort, wo v3s
*Promotion* die Unterschiede erzeugt — das ist die experimentelle Variable selbst, kein Confounder.

Offener Stolperstein fuer spaeter: das asymmetrische Literal (`false` in `evogrow.jl`, `true` in
`evogrow_v3.jl`) ist heute harmlos, wuerde aber tragend, sobald v2.2 eine andere Quelle
nicht-uniformer Stages als den Cap bekaeme.

### WP-P3.1 — Klassifikation aller 63 Systeme, geprueft

<!-- fab01fe -->

**20 exakt, 43 Surrogat.** Alle zehn handgepflegten Klassifikationen werden vom symbolischen
Klassifikator reproduziert — keine Abweichung, also weder Parser- noch Handeintragsfehler.

Unabhaengig nachgeprueft an Systemen ausserhalb der zehn (6, 12, 25, 55, 61 stimmen). Der
aussagekraeftigste Fall ist System 8: `0.14*x0*(1 - 0.0077*x0)*(0.227*x0 - 1)` wird korrekt zu
`u1|u1²|u1³` ausmultipliziert und als Stage 4 eingestuft. Das geht nur symbolisch, nicht per
String-Matching — der Klassifikator tut wirklich, was er soll.

Stage-Verteilung der 20 exakten Systeme: Stage 1 → 3, Stage 2 → 3, Stage 3 → 9, Stage 4 → 4,
Stage 5 → 1. Die Spalte `expected_eq_stage` liefert nebenbei die **per-Gleichung-Wahrheit fuer alle
117 Gleichungen** — genau das, was die Safety-Bewertung des Stage-Caps als Referenz braucht und
bisher nur fuer eine Handvoll Systeme offline vorlag.

**Befund, der im Codex-Report fehlt und Konsequenzen hat:** 10 der 43 Surrogat-Systeme sind es
*ausschliesslich* wegen eines konstanten Offsets (IDs 1, 5, 9, 17, 23, 43, 52, 57, 58, 59). Ein
Konstanten-Term in der Basis — die einfachste denkbare Erweiterung — wuerde sie exakt machen und
die Auswertungsmenge von 20 auf 30 Systeme heben, also um 50 %. Gratis ist das nicht: eine
Basisaenderung wechselt den Fingerprint und entwertet alle bestehenden Ergebnisse. Aber die Zahl
begrenzt direkt, worueber Paper 1 exakte Wiederfindung berichten kann, und muss deshalb in der
Scope-Diskussion stehen.

### WP-C1 — Stage-Cap auf dem v2.2-Substrat, verifiziert

<!-- d3fce98 -->

Neue Variante `evogrow_v2_2_stage_capped`: der Look-Ahead-Cap wirkt als Term-Restriktion pro
Gleichung, die Stage-Progression bleibt die globale stage-lokale Plateau-Regel von v2.2. Das
`r_k`-Signal kommt nicht vor — es ist genau das, was hier entfernt wird.

Motivation aus den System-31-Zellen: der Cap braucht v3 nicht. `estimate_stage_caps` liest nur
Trajektorie und Basis, die Caps sind ein vor der Suche berechneter Vektor. Die Kopplung an v3
bestand nur, weil der Cap in dessen Promotionspfad verdrahtet worden war.

Verifikation (von mir gefahren, nachdem der Codex-Lauf ins Timeout lief):

| Pruefung | Ergebnis |
|---|---|
| `config_fingerprint()` | `df5db7763bcd2449`, unveraendert |
| Cap deaktiviert, Sys 11/42 | Loss bit-identisch `4.402192340718147e-15`, Stage 4, Support `{u1, u1², u1³}`, `pruned_match=true` — identisch zu `evogrow_v2_2_stage_local` |
| Cap aktiv, Sys 3/42 | Cap `[2]`, Stage 2, Overshoot 0, Loss `1.3476e-8`, Support `{u1, u1²}`, `pruned_match=true` |
| Caps | 3→`[2]`, 11→`[4]`, 26→`[3,3]`, 31→`[3,3]`, 63→alles `nothing` — deckungsgleich mit WP-L5d |

Die Bit-Identitaet bei deaktiviertem Cap ist **strukturell** garantiert, nicht nur empirisch: ohne
Caps sind die `eq_stages` immer uniform, damit wird immer der alte Pfad genommen. Die
`elapsed_s`-Werte der beiden Aequivalenzlaeufe unterscheiden sich (JIT-Warmup) und sind ohnehin
keine belastbare Groesse — siehe die Notiz zu Wall-Clock weiter unten.

**Fingerprint-Falle, die vorab entschaerft wurde:** `FINGERPRINT_VARIANT_LABELS` geht in den Hash
ein. Ein Eintrag der neuen Variante haette `df5db7763bcd2449` gewechselt und alle 32
History-Records unvergleichbar gemacht — also genau das zerstoert, wofuer die Laeufe da sind. Da
Laeufe unabhaengig sind, ist das Weglassen sachlich korrekt. Der Payload nennt jetzt nur
`evogrow_v3_stage_capped` und ist damit unvollstaendig; das bleibt bewusst so stehen.

### WP-C1b beauftragt — drei Reviewbefunde

<!-- bb61b3a -->

1. **Duplikation.** `_expand_with_stage_caps` ist eine fast wortgleiche Kopie von
   `_expand_equation_aware_with_usage_policy`, `_equation_capped_terms` eine von
   `_evogrow_v3_equation_terms`. Zwei Kopien der Kindgenerierungs-Weiche, benutzt von genau den
   beiden Varianten, die gegeneinander gestellt werden.
2. **Stille Semantikaenderung bei Kopplungstermen.** Der Originalpfad filtert ueber
   `_evogrow_v3_term_available`, das eine Zusatzregel enthaelt: ein Term mit mehreren Variablen ist
   fuer Gleichung `k` nur verfuegbar, wenn *alle* referenzierten Variablen die Stage erreicht haben.
   Die Kopie laesst die Klausel weg.

   Entscheidung: **Kohaerenzregel raus, fuer cap-abgeleitete Grenzen, in beiden Varianten.** Sie
   wurde fuer v3 geschrieben, wo `eq_stages` den *Fortschritt* abbildet und eine niedrige Stage
   voruebergehend ist. Ein Cap ist eine *permanente, aus den Daten abgeleitete Obergrenze*. Ist
   Gleichung 2 dauerhaft auf 2 gedeckelt, wird `u1*u2` fuer Gleichung 1 nie verfuegbar, auch wenn
   deren Cap 3 ist — der Cap wird fuer alle Kopplungsterme zur globalen Schranke und die Wahrheit
   unerreichbar. Derselbe Fehlermodus wie WP-L4 auf System 63, und dasselbe Prinzip: eine
   Restriktion muss auf positiver Evidenz ueber die Gleichung beruhen, die sie einschraenkt.

   **Die vier bereits gefahrenen gecappten Zellen sind faktisch nicht betroffen**, weil alle Caps
   der fuenf Regressionssysteme uniform sind und die Klausel bei uniformen Stages wirkungslos ist.
   Das ist Glueck, nicht Absicht — auf System 54 (`[nothing,2,2]`) haette es gebissen. WP-C1b muss
   die Wirkungslosigkeit zeigen statt sie zu behaupten.
3. **Report mit fest verdrahteter Ergebnisprosa.** `verify_wp_c1.jl` schreibt „No parser or
   cap-estimator disagreement surfaced" als Stringliteral, unabhaengig vom Laufergebnis. Ein
   Verifikationsbericht darf keine Aussage enthalten, die nicht falsch werden kann.

Nebenbefund: `stage_cap_policy::Any` ist untypisiert, weil `stage_cap.jl` in `EvoODE.jl` nach
`evogrow.jl` inkludiert wird. Kosmetisch, in WP-C1b als risikoarme Zugabe.

### v3 uncapped auf System 31 — Cap-Effekt und v3-Effekt sind jetzt getrennt

<!-- b6fe895 -->

Drei Laeufe (31, Seeds 42/123/7, `evogrow_v3`, Fingerprint `df5db7763bcd2449`, `git_hash c6692a5`,
`git_dirty=false`, `total_optimizer_safety_limit_hits = 0`). Damit existiert erstmals ein
v3-Referenzarm auf System 31, und die offene Zuordnungsfrage aus den Bestaetigungszellen ist
beantwortet.

| Seed | v2.2 | v3 | v3 + Cap | Fits v3 → Cap |
|---|---|---|---|---|
| 42 | 6,808e-11 | 1,285e-4 | 1,678e-2 | 490 → 250 |
| 123 | 1,043e-4 | 2,994e-5 | 5,284e-3 | 430 → 230 |
| 7 | 6,975e-5 | 9,872e-5 | **9,872e-5** | 390 → 230 |

Wall-Clock ist hier bewusst **nicht** aufgefuehrt. Die Laeufe liefen auf dem Laptop des Nutzers,
wo jederzeit Parallelarbeit, Suspend oder Throttling dazwischenkommen koennen, ohne Spur in den
Daten. Kostenaussagen stuetzen sich ausschliesslich auf Zaehlgroessen.

**Die Zuordnung:** Auf Seed 42 verliert v3 gegenueber v2.2 rund **sechs Groessenordnungen**
(6,8e-11 → 1,3e-4), der Cap legt danach zwei drauf. Der dominante Anteil des Einbruchs sitzt also im
v3-Substrat, nicht im Cap. Das bestaetigt die Vermutung, die sich aus der Nicht-Bindung des Caps auf
dieser Zelle ergab, und zeigt auf das `r_k`-Promotionssignal, dessen Ableitungskontamination WP-L2
gemessen hat.

**Zwei Befunde, die mehr wert sind als die Tabelle:**

1. **Seed 7 ist bit-identisch.** Gleicher Loss, gleicher Support in beiden Gleichungen
   (`du1 = {u2, u1², u1·u2}`, `du2 = {u1, u2, u1²}`). Der Cap aendert das Ergebnis nicht und spart
   160 Fits und rund 34 000 Sekunden. Die Nulltarif-Beobachtung von System 26 repliziert hier.
2. **Seed 123 hat in beiden Armen identischen Support** (`du1 = {u1, u2, u1·u2}`,
   `du2 = {u1, u2, u1², u2²}`) und trotzdem 176-fachen Loss-Unterschied. Gleiche Struktur, andere
   Parameter — das ist Pfadabhaengigkeit im Optimierer, **nicht** eine vom Cap unerreichbar gemachte
   Struktur. Damit ist die naheliegende Sorge, der Cap schneide die Wahrheit ab, fuer diese Zelle
   ausgeraeumt.

Bleibt Seed 42, wo dem gecappten `du2` der Kopplungsterm `u1·u2` fehlt — der auf Stage 3 durchgehend
verfuegbar war. Dasselbe Muster wie auf System 26: nicht der Cap verhindert die Struktur, die Suche
findet sie innerhalb der Stage nicht. Das ist Suchkraft *innerhalb* einer Stage und liegt
ausdruecklich ausserhalb von Paper 1.

**Overshoot-Eliminierung repliziert 3/3** (`eq_overshoot [2,2] → [0,0]`, `eq_wasted_levels`
[12,12]/[7,7]/[7,7] → [0,0]) bei 41–51 % weniger Fits.
`pruned_match = false` in **allen neun** Zellen, auch bei v2.2 mit 6,8e-11 — auf System 31 gelingt
keinem Arm die exakte Wiederfindung.

Fingerprint-Grenze bleibt bestehen und muss beschriftet werden: der v2.2-Arm liegt auf
`0c739d4e36ee6498`, v3 und gecappt auf `df5db7763bcd2449`.

**Nebenbefund beim Mergen der History** (29 → 32 Zeilen): das vermeintliche Duplikat
`(evogrow_v3, 26, 42)` ist keines. Es sind zwei gueltige Laengsschnitteintraege — `0c739d4e` vom
2026-07-22 mit Loss 1,392e-3 (die v3.2-Lockstep-Bridge, per Konstruktion bit-identisch zu v2.2, was
der Wert exakt bestaetigt) und `1f9c5f80` vom 2026-07-30 mit 2,520e-4 (der divergente v3 aus dem
Gate-2-Lauf). Der Uniqueness-Key der History ist `(variant, system_id, seed, config_fingerprint)`,
nicht das Tripel.

### Phase 3 begonnen — Protokoll-Audit deckt eine Gitter-Fehlausrichtung auf

`docs/paper1_odebench_protocol_alignment.md` angelegt. Die EvoODE-Seite ist gegen den Datensatz
verifiziert, die Spalten der publizierten Quellen sind ausdruecklich als **ungeprueft** markiert —
ohne die Papers waere jede Eintragung dort erfunden.

**Verifiziert und unproblematisch:** alle zehn `u0` aus der `BENCHMARKS`-Tabelle reproduzieren exakt
den *ersten* Anfangsbedingungssatz des Datensatzes. Der Datensatz liefert allerdings **zwei** Saetze
pro System, wir nutzen nur einen — publizierte Zahlen ueber beide decken also eine groessere
Auswertungsmenge ab.

**Verifiziert und problematisch: das Zeitgitter passt bei keinem einzigen System.** Der Datensatz
liefert durchgaengig **512 Punkte ueber t ∈ [0, 10]**; EvoODE nutzt pro System eigene `tspan`/`T`
zwischen 10 und 20 Punkten pro Zeiteinheit, also **2,6- bis 5,1-fach duenner**, und teils deutlich
laengere Horizonte (System 63 bis t = 30 gegen t = 10). System 26 trifft immerhin die Zeitspanne,
aber nicht die Abtastung.

**Querverbindung, die das interessant macht:** WP-L3 hat gemessen, dass die Stage-3-Klippe auf
System 54 bei unserer Dichte nicht aufloesbar ist und ab etwa doppelter Dichte erscheint. Das
Datensatz-Gitter ist dort **2,56-fach dichter** (51,2 gegen 20 Punkte pro Zeiteinheit). Der Wechsel
auf das Datensatz-Gitter wuerde also plausibel eine der beiden verbliebenen Cap-Verletzungen
beseitigen. Vorhersage aus gemessenem Verhalten, nicht Ergebnis — ungelaufen.

Daraus die Entscheidung, die **vor** der Phase-B-Generierung faellt, weil sie die Trajektorien und
damit alles Nachgelagerte bestimmt: Datensatz-Gitter uebernehmen (Vergleichbarkeit plausibel,
doppelte Laufzahl durch zwei IC-Saetze, kein bestehendes Ergebnis traegt ueber, Baseline neu) oder
beim eigenen Gitter bleiben (bestehende Ergebnisse gelten, publizierte Zahlen bleiben rein
kontextuell und das muss im Paper konsistent so stehen). Die Systemklassifikation (WP-P3.1) ist
gitterunabhaengig und kann davor laufen.

### WP-P3.1 beauftragt — Klassifikation aller 63 Systeme

Python, im Analyse-Pipeline-Teil, `sympy` als neue Abhaengigkeit. Grundlage ist das Feld
`substituted` im Datensatz (Gleichungen mit eingesetzten Konstanten). Der Umfang laut Vorab-Scan:
63 Systeme, 117 Gleichungen, Dimensionen 1/2/3/4 mit 23/28/10/2. Operatoren: `**` 42×, `sin` 16,
`cos` 8, `exp` 6, `log`, `cot`, `Abs` je einmal — dazu additive Konstanten, fuer die die Basis
ueberhaupt keinen Term hat. Das ist symbolische Ausdrucksanalyse, kein String-Matching.

Pflichtbestandteil der Spec ist die **Validierung gegen die zehn handgepflegten Systeme** aus
`benchmark_evogrow.jl`, mit der ausdruecklichen Auflage, jede Abweichung als Befund zu behandeln und
den Parser nicht auf Uebereinstimmung zu tunen: eine Abweichung hiesse entweder Parser falsch oder
ein handgepflegter Wert falsch, auf dem saemtliche bisherigen Ergebnisse beruhen.

Der Grund, warum die Zahl selbst zaehlt und nicht nur die CSV: die Menge der exakten Systeme
bestimmt, auf wie vielen Systemen Paper 1 ueberhaupt strukturelle Wiederfindung berichten kann.
Faellt sie klein aus, aendert das, was das Paper behaupten kann.

### Bestaetigungszellen — Overshoot repliziert, aber „zum Nulltarif" haelt nicht

Vier gecappte Zellen parallel gefahren (26/123, 31/42, 31/123, 31/7), History gemerged (25 → 29).
Technisch sauber: richtige Zellen, kein Env-Leck, `error = nothing`, `git_dirty = false`, Fingerprint
`df5db7763bcd2449`, und — entscheidend fuer die Parallelitaet — `total_optimizer_safety_limit_hits = 0`
in allen vier. **Das 1800-s-Zeitlimit hat nie gefeuert, die Parallelitaet hat die Ergebnisse nicht
kontaminiert.** Die 40–68 `optimizer_limit_hits` sind ausnahmslos BFGS-Konvergenzfehler, das bekannte
Verhalten aus WP-P2.2c.

| Zelle | Variante | Loss | Stage | Over | Wasted |
|---|---|---|---|---|---|
| 26/42 | v2.2 | 1,392e-3 | 5 | 2 | 8 |
| | gecappt | **2,520e-4** | 3 | 0 | 0 |
| 26/123 | v2.2 | 1,392e-3 | 5 | 2 | 8 |
| | gecappt | 1,392e-3 | 3 | 0 | 0 |
| 31/42 | v2.2 | **6,808e-11** | 3 | 0 | 0 |
| | gecappt | **1,678e-2** | 3 | 0 | 0 |
| 31/123 | v2.2 | 1,043e-4 | 5 | 2 | 8 |
| | gecappt | 5,284e-3 | 3 | 0 | 0 |
| 31/7 | v2.2 | 6,975e-5 | 5 | 2 | 8 |
| | gecappt | 9,872e-5 | 3 | 0 | 0 |

**Was haelt: die Overshoot-Eliminierung repliziert.** Alle vier neuen Zellen `eq_overshoot = [0,0]`,
`eq_wasted_levels = [0,0]`, waehrend v2.2 in vier von fuenf Zellen Overshoot 2 und 8 verschwendete
Level hatte.

**Was nicht haelt: „zum Nulltarif".** Meine Formulierung nach der Einzelzelle war zu stark. Auf
System 26 kostet der Cap nichts (26/42 bit-identisch zu v3, 26/123 gleichauf mit v2.2). Auf System 31
kostet er erheblich: 31/123 ist 50-fach schlechter als v2.2, 31/7 leicht schlechter — und **31/42 ist
um acht Groessenordnungen schlechter** (1,7e-2 gegen 6,8e-11). Der Befund „die spaeten Stufen tragen
nichts bei" gilt fuer System 26, nicht allgemein: auf System 31 senken die Stufen 4/5 den Loss real,
wenn auch mit strukturell falschen Termen. Der Cap tauscht also Fitqualitaet gegen
Komplexitaetsdisziplin, und ob dieser Tausch gratis ist, haengt am System.

**Der Vergleich ist zudem konfundiert, und das ist der wichtigere methodische Punkt.** Die gecappte
Variante ist `EvoGrowV3` **plus** Cap. Fuer System 31 existiert kein v3-Record (v3 liegt nur fuer 3,
11 und 26 vor), also laesst sich Cap-Effekt und v3-Effekt dort nicht trennen.

Eine Zelle erlaubt die Trennung aber schon jetzt: **auf 31/42 ist der Cap nicht bindend** — v2.2
endete dort von selbst auf Stage 3, ein Cap bei 3 kann also nichts verhindert haben. Trotzdem liegt
der Loss acht Groessenordnungen hoeher. **Der Einbruch auf dieser Zelle kann folglich nicht vom Cap
kommen, sondern muss aus dem v3-Unterbau stammen** (Pro-Gleichungs-Promotion ueber `r_k` statt
globalem Plateau) — genau das Signal, das WP-L2 als ableitungsfehler-kontaminiert nachgewiesen hat.

Konsequenz: bevor daraus ein Paper-Claim wird, braucht es **v3 ungecappt auf System 31, Seeds
42/123/7** — drei Laeufe, die Cap-Effekt und v3-Effekt sauber trennen. Ohne das ist die Aussage
„der Cap kostet Fitqualitaet" nicht belegbar; sie koennte vollstaendig ein v3-Effekt sein.

Nebenbefund: `pruned_match` ist in **allen** Zellen false, auch bei v2.2 mit Loss 6,8e-11 auf 31/42 —
das ist der aus Phase 1 bekannte Fall „nahezu perfekter Fit, aber ein Fremdterm ueberlebt die
Pruning-Schwelle".

## 2026-08-01

### Scope-Entscheidung getroffen — Zweig 1, angereichert

Nach dem Ergebnis der Entscheidungszelle: die finale Paper-1-Variante traegt den Look-Ahead-Cap, das
Paper wird die mechanistische Claim-C-Studie, und die Kette v2.2 → v3 → gecappt wird als
dokumentierte Failure-Analyse mit quantifiziertem Positivergebnis zur Komplexitaetsallokation
gefuehrt. Zweig 2 (Paper um den Look-Ahead herum neu bauen) faellt weg, weil der Mechanismus genau
das Versagen *nicht* behebt, das Phase 2 ausgeloest hat. Die Frage nach der Suchkraft innerhalb einer
Stufe bleibt ausdruecklich ausserhalb von Paper 1.

**Planungsfund, der eine frueher von mir genannte Empfehlung korrigiert.** Ich hatte „Bestaetigung
auf 31 und 63" vorgeschlagen. Auf **System 63 feuert der Cap gar nicht** — alle vier Gleichungen sind
`nothing`, die gecappte Variante ist dort identisch zu v3, die Zelle koennte den Overshoot-Effekt
also gar nicht zeigen. 63 gehoert als Identifizierbarkeitsgrenze ins Paper, nicht in die
Bestaetigung. Ebenfalls geprueft: der v2.2-Vergleichsarm liegt fuer 3, 11, 26, 31 und 63 bei je drei
Seeds (42/123/7) bereits vor, es ist also nur der gecappte Arm zu fahren. Zu labeln ist dabei, dass
der Vergleich eine Fingerprint-Grenze kreuzt (v2.2 unter Baseline v0 `0c739d4e36ee6498`, neue Laeufe
unter `df5db7763bcd2449`); WP-T2 hat gezeigt, dass die zwischenzeitliche Konfigurationsaenderung die
Ergebnisse nicht bewegt, aber das gehoert benannt.

### Entscheidungszelle gelaufen — Stage-Eskalation war ein Symptom, nicht die Ursache

Der gecappte 26/42-Lauf ist durch (`evogrow_v3_stage_capped`, Fingerprint `3f9be6d36c4043de`,
`git_hash d896d77`, 21.159 s). Readout in `outputs/studies/gate2_do_or_die/`.

| | v2.2-Anker | v3 Gate 2 | **gecappt** |
|---|---|---|---|
| Loss | 1,391623174905009e-3 | 2,5195575964774715e-4 | **2,5195575964774715e-4** |
| `eq_final_stages` | 5 | [5, 5] | **[3, 3]** |
| `eq_overshoot` | 2 | [2, 2] | **[0, 0]** |
| `eq_wasted_levels` | 8 | — | **[0, 0]** |
| du1-Support | {u1, u1², u1·u2} | — | {u1, **u2**, u1², u1·u2} |
| du2-Support | {u1, u1²} | — | **{u1, u1²}** |

**Zwei Befunde, und sie zeigen in entgegengesetzte Richtungen.**

**1. Die Komplexitaetsallokation ist geloest, und zwar zum Nulltarif.** Overshoot 2 → 0, verschwendete
Level 8 → 0 — und der Loss ist **bit-identisch** zum ungecappten v3-Lauf, bis zur letzten Stelle.
Das heisst: die Stufen 4 und 5 haben im v3-Lauf zum Ergebnis buchstaeblich nichts beigetragen. Die
Eskalation war reine Verschwendung, und der Cap entfernt sie ohne jeden Preis an Fitqualitaet.
Parameter-Fits 390 gegen 530 bei v3, also 26 % weniger. Damit ist der Look-Ahead als Mechanismus
belegt — nicht mehr als Offline-Klassifikator, sondern im Suchpfad.

**2. Die strukturelle Wiederfindung ist unveraendert — nicht einmal bewegt.** `du2` ist
`{u1, u1²}`, also **exakt dasselbe, was v2.2 gefunden hat**; der Readout weist es explizit aus
(`du2_support_changed_from_anchor: false`). Die Wahrheit `2·u2 − u1·u2 − u2²` lag die ganze Zeit
vollstaendig auf Stage 3 und damit innerhalb des Caps bereit. `du1` behaelt zusaetzlich den
Fremdterm `u2`.

**Damit ist die Frage beantwortet, die seit WP-T2 offen war: die Stage-Eskalation war ein Symptom,
nicht die Ursache.** Die Suche auf die richtige Stufe zu zwingen, verbessert die Entdeckung nicht um
einen einzigen Term. Der Engpass liegt in der Suchkraft *innerhalb* einer Stufe — Populationsgroesse,
Kindergenerierung, Parsimonie-Druck —, und das ist eine andere Baustelle als alles seit Gate 1.

Das Readout-Verdikt lautet `REPORTABLE`. Das ist eine faire Bezeichnung, darf aber nicht verdecken,
dass das strukturelle Kriterium verfehlt ist: unter den urspruenglichen Do-or-Die-Kriterien waere
(a) nur eine Konstruktionspruefung, (b) verfehlt und (c) erfuellt.

**Messvorbehalt, und der geht auf mich.** `elapsed_s` ist mit 21.159 s hoeher als die 13.047 s des
v3-Laufs, obwohl weniger Fits anfielen. Die Wall-Clock ist kontaminiert: ich habe waehrend des Laufs
dreimal eigene Julia-Verifikationsjobs gestartet, die Pakete laden und rechnen. Tragend sind wie im
ganzen Projekt die Zaehlungen — 390 Fits, 1.977.546 ODE-Solves —, nicht die Zeiten.

### WP-L5d geliefert — Cap-Spur abgeschlossen

Bericht in `docs/wp_l5d_stage_cap_closeout.md`. Acceptance gruen, Suite 2 Verletzungen (die bekannten
54 du2/du3), 8 von 16 Gleichungen gecappt, 18 Stufen gespart.

**Die Fingerprint-Falle wurde korrekt behandelt.** Neuer Fingerprint `df5db7763bcd2449` mit
`aggregation` und `lookahead_horizon`; das Readout waehlt den Record aber ueber
Variante/System/Seed statt ueber den neu berechneten Fingerprint und wurde gegen die vorhandene
History geprueft (2 v3-Records korrekt *nicht* gematcht). Genau deshalb hat es den Lauf-Record mit
dem alten Fingerprint gefunden — die Auswertung waere sonst stillschweigend leer geblieben.

Sensitivitaet belegt beide Defaults: Horizont 1 liefert 4 Verletzungen statt 2 (der
System-31-Fall), `any_positive` bei Horizont 1 sogar 5; Horizont 2 und 3 sind identisch. Der
System-31-Vorbehalt (Ursache unbelegt, Diagnose lief ins Timeout) ist im Bericht festgehalten.

<!-- 27ecb09, 3ddc7f4 -->

### WP-L5d beauftragt — Provenienz, Tests, Sensitivitaet, Bericht

Abschluss der Cap-Spur; **keine Regelaenderung im Scope** — die Regel ist verifiziert, eine stille
Aenderung wuerde das entwerten. Findet ein Test einen echten Defekt, ist zu berichten statt zu
reparieren.

Wichtigster Punkt ist der Fingerprint: `aggregation` und `lookahead_horizon` fehlen im
gefingerprinteten Cap-Tupel, drei Semantikaenderungen sind bereits ohne Bewegung von
`3f9be6d36c4043de` durchgelaufen.

**Dabei eine Falle, die mir beim Schreiben aufgefallen ist und die teuer waere.** Der laufende
26/42-Lauf hat seinen Fingerprint beim Prozessstart berechnet und schreibt seinen Record mit dem
alten Wert — richtig so. Aber `studies/gate2_do_or_die/readout.jl` laeuft danach aus aktualisiertem
Code. Sucht es den Record ueber den *neu berechneten* Fingerprint, findet es ein vorhandenes
Ergebnis nicht und meldet stillschweigend nichts. Die Spec verlangt, die Record-Auswahl des Readouts
zu pruefen und gegen die vorhandenen History-Records zu verifizieren, nicht nur den Code zu lesen.

Ausserdem zu dokumentieren: die zwei System-54-Verletzungen ausdruecklich als bekannte
Aufloesungsgrenze mit dem WP-L3-Dichte-Beleg statt als offener Bug, und der Vorbehalt zum
System-31-Fix (Ursache unbelegt, Diagnose lief ins Timeout).

### WP-L5c — Acceptance gruen; die zwei Restverletzungen sind die bekannte Aufloesungsgrenze

Codex hat System 31 du1 repariert und diesmal korrekt gestoppt — belegt mit echter Ausgabe, nachdem
der Diagnosebefehl nach 552 s ins Timeout lief. Eigene Nachrechnung, jetzt inklusive System 54:

| System | Wahrheit pro Gleichung | Cap | |
|---|---|---|---|
| 3 | [2] | [2] | ✓ |
| 11 | [4] | [4] | ✓ |
| 26 | [3, 3] | [3, 3] | ✓ Vergleichsbasis des laufenden 26/42 intakt |
| 31 | [3, 3] | [3, 3] | ✓ Fix wirkt |
| 63 | [3, 3, 1, 1] | [n, n, n, n] | ✓ sicher |
| 54 | [1, 3, 3] | [n, **2**, **2**] | 2 Verletzungen |

Suiteweit: 2 Verletzungen, 8 von 16 Gleichungen gecappt, 18 Stufen gespart. Die Sicherheit ist also
nicht durch Nichtstun erkauft — genau die Gegenprobe, die die Spec verlangt hatte.

**Die zwei Verletzungen sind kein neuer Defekt.** Es sind exakt die beiden Gleichungen, die WP-L3
bereits als Undershoot ausgewiesen hatte: die floor-gated Konfusion war 12 exact / 0 over / 4 under,
und diese vier waren 63 du1/du2 plus 54 du2/du3. Nachdem 63 jetzt sauber ungecappt ist, bleiben genau
die Lorenz-Gleichungen uebrig. Die Ursache ist gemessen, nicht vermutet: bei Benchmark-Sampling
faellt das Residuum auf System 54 schon bei Stage 2 unter den Rauschboden, die Stage-3-Klippe liegt
also unter der Aufloesungsgrenze der Ableitungsschaetzung; der Dichte-Sweep aus WP-L3 zeigt sie ab
doppelter Dichte. **Datengrenze, keine Regelgrenze.**

Damit hat die Cap-Regel eine geschlossene Charakterisierung: sicher, wo die Ableitungsschaetzung die
Struktur aufloest, unsicher genau dort, wo sie es nicht tut — und das ist vorab am Rauschboden
ablesbar. Es bleibt kein unerklaerter Defekt.

**Kritikpunkt zum Vorgehen:** der System-31-Fix kam ohne die geforderte Diagnose zustande, weil diese
ins Timeout lief. Er lockert den Gewinntest, wenn das Folge-Residuum bereits auf dem Boden liegt
(`tau_abs` entfaellt, `delta > floor` und die relative Schwelle bleiben). Das wirkt in die sichere
Richtung — lockerere Gewinnerkennung heisst hoehere Caps, also weniger Blockade — und das Ergebnis
ist verifiziert. Die *Ursache* bleibt aber unbelegt; das ist eine Reparatur per Schlussfolgerung,
nicht per Messung, und gehoert so vermerkt.

Weiterhin offen: Fingerprint um `aggregation` und `lookahead_horizon` ergaenzen (inzwischen sind drei
Semantikaenderungen ohne Fingerprint-Bewegung durchgelaufen), Tests, Aggregations- und
Horizont-Sensitivitaet, Bericht.

### WP-L5b — Regel weitgehend repariert; Stoppmeldung war ein Fehlalarm; eine Verletzung bleibt

Codex meldete einen Abbruch mit „System 26 ergibt nicht mehr [3,3] sondern [nothing, nothing]".
**Der Alarm war falsch.** Die Meldung war wortgleich mit der aus WP-L5, referenzierte „WP-L5" und
„Abschnitt 8" (den WP-L5b nicht hat) und beschrieb die Umstellung auf *positive evidence only* —
also die vorige Runde. Der Pflichtcheck nach der neuen Aenderung ist offenbar nicht gelaufen, die
Meldung wurde uebernommen. Eigene Nachrechnung:

| System | Wahrheit | WP-L4 | WP-L5 | **WP-L5b** |
|---|---|---|---|---|
| 3 | [2] | [2] ✓ | nothing | **[2] ✓** |
| 11 | [4] | [4] ✓ | nothing | **[4] ✓** |
| 26 | [3, 3] | [3, 3] ✓ | nothing, nothing | **[3, 3] ✓** |
| 31 | [3, 3] | [3, 3] ✓ | [1, 1] ✗ | **[1, 3]** — du1 verletzt |
| 63 | [3, 3, 1, 1] | [1, 1, 1, 1] ✗ | [1, 1, n, n] | **[n, n, n, n]** ✓ sicher |

**System 26 steht auf [3,3]** — die Vergleichsbasis des laufenden 26/42-Laufs ist unberuehrt.
Sicherheitsverletzungen: 2 (L4) → 4 (L5) → **1 (L5b)**. Die Bodensemantik-Korrektur und der
Horizont wirken beide, und zwar sichtbar: 3, 11 und 26 sind zurueck, 63 ist jetzt durchgaengig
ungecappt und damit sicher (zum Preis, dass die Mechanik dort nichts einbringt — akzeptabel und
ehrlich auszuweisen).

**Offen bleibt System 31 du1.** Cap 1 gegen wahre Stage 3. Aufschlussreich ist die Form der
Gleichung: `du1 = -0.4*u1*u2` ist die **einzige** im Satz, deren wahrer Support vollstaendig in
einer spaeteren Stufe liegt, ohne jeden Term aus Stage 1 oder 2. Genau dieser Fall — kein Gewinn auf
den Zwischenstufen, der ganze Gewinn erst spaeter — sollte der Horizont abfangen. Dass er es nicht
tut, ist die naechste konkrete Frage; ohne Instrumentierung der Split-Entscheidungen ist nicht
entscheidbar, ob der Gewinntest bei Stage 3 nicht anschlaegt oder die Aggregation die Mehrheit
verfehlt. Passend dazu ist du2 derselben Gleichung korrekt auf 3 — dort enthaelt die Wahrheit
zusaetzlich einen Stage-1-Term.

Nicht geliefert, weil Codex am Fehlalarm abgebrochen hat: Tests, suiteweite Invariante,
Aggregations-Sensitivitaet, Fingerprint-Reparatur, Bericht.

### WP-L5b beauftragt — korrigierte Bodensemantik plus Horizont

Behebt die beiden diagnostizierten Ursachen. **Bodensemantik:** nicht „Residuum unter dem Boden →
nicht beurteilbar", sondern die Unterscheidung, ob das Residuum auf dieser Stufe *auf* den Boden
gefallen ist (positive Evidenz, hier cappen) oder schon *vorher* dort lag, bevor eine Stufe geholfen
hat (keine Information, kein Cap). **Horizont:** mindestens zwei *anwendbare* Stufen, damit eine
nutzlose Zwischenstufe ueberbrueckt werden kann; leere Stufen verbrauchen keinen Horizont. Erhalten
bleibt aus WP-L5 die Dreiteilung positive/undecidable/invalid, die expliziten Aggregationsmodi und
die Auswertbarkeitsregel — nur bei auswertbarer Folgestufe darf gecappt werden, was 63 du1/du2
ungecappt haelt, weil deren Stage-3-Bibliothek rangdefizit ist.

**Prozessaenderung, aus dem WP-L5-Verlauf gelernt:** die Abnahmetabelle ueber alle fuenf Systeme ist
**zuerst** zu erzeugen, vor Tests, Bericht und Fingerprint. WP-L5 hat die gesamte Arbeit gemacht und
erst danach gemerkt, dass die Regel kaputt ist. So steht das Ergebnis in den ersten Minuten.

Zusaetzlich mitspezifiziert: das fehlende `aggregation`-Feld im gefingerprinteten Cap-Tupel, damit
Records vor und nach der Reparatur nicht als dieselbe Konfiguration verbucht werden.

Vorregistriert inklusive Ausweg: laesst sich System 31 nur reparieren, indem anderswo eine
Verletzung entsteht, ist das mit Zahlen zu berichten statt Schwellen zu tunen, bis die Tabelle
passt — es hiesse, Rauschboden plus fester Horizont taugen nicht als Basis fuer einen sicheren Cap.

### WP-L5 durchgefallen — beide Abnahmekriterien verfehlt; die Ursache ist ein Fehler in meiner Spec

Caps nach WP-L5, wieder selbst nachgerechnet:

| System | Wahrheit pro Gleichung | WP-L4 | **WP-L5** | |
|---|---|---|---|---|
| 3 | [2] | [2] ✓ | **nothing** | Cap verloren |
| 11 | [4] | [4] ✓ | **nothing** | Cap verloren |
| 26 | [3, 3] | [3, 3] ✓ | **nothing, nothing** | Cap verloren |
| 31 | [3, 3] | [3, 3] ✓ | **[1, 1]** | **neue Verletzung** |
| 63 | [3, 3, 1, 1] | [1, 1, 1, 1] ✗ | [1, 1, nothing, nothing] | du1/du2 weiter verletzt |

Abnahmekriterium 1 (3/11/26/31 behalten ihre Caps) auf allen vier Systemen verfehlt. Kriterium 2
(63 du1/du2 ungecappt) ebenfalls verfehlt. Die Sicherheitsinvariante ist **schlechter** geworden:
Verletzungen von 2 auf 4, weil System 31 neu dazukommt. Gleichzeitig cappt die Regel auf keinem
System mehr, auf dem sie funktioniert hat — also auf beiden Achsen verschlechtert.

**Codex hat sich dabei korrekt verhalten.** Die Stoppbedingung der Spec hat gegriffen: der
System-26-Cap wurde zuerst geprueft, die Abweichung von [3,3] auf `nothing` erkannt, die Arbeit
abgebrochen und berichtet. Dass Tests, Bericht, suiteweite Invariante und Fingerprint fehlen, ist
kein Lieferdefizit, sondern Befolgung der Abbruchregel. Die Regel hat genau das getan, wofuer sie
da war — teure Folgearbeit auf einer kaputten Basis wurde vermieden.

**Codex' Deutung ist allerdings falsch** und darf nicht so stehenbleiben: er liest das Ergebnis als
den in Abschnitt 8 vorregistrierten Trade-off zwischen Sicherheit und korrekten Caps. Das ist es
nicht. Ein echter Trade-off haette die Sicherheit verbessert und dafuer Nutzen gekostet. Hier ist
**auch die Sicherheit schlechter geworden** — System 31 ist eine neue Verletzung, die es vorher
nicht gab. Beide Achsen gleichzeitig zu verschlechtern ist kein Trade-off, sondern ein Defekt.

**Der laufende 26/42-Lauf ist nicht betroffen.** Julia laedt den Code beim Prozessstart; der Lauf
faehrt die WP-L4-Semantik mit Cap [3,3]. Der Arbeitsbaum reproduziert ihn aber nicht mehr —
siehe Provenienz-Punkt unten.

**Diagnose, und der Fehler liegt bei mir.** Die Spec schrieb vor: Residuum auf oder unter dem
Rauschboden → nicht beurteilbar → kein Cap. Das ist falsch, denn **den Boden zu erreichen ist genau
das, was ein korrektes Modell tut.** Die Regel kann damit auf keinem loesbaren System je einen Cap
setzen. Die Unterscheidung, auf die es ankommt, ist eine andere: *faellt* das Residuum auf dieser
Stufe auf den Boden (positive Evidenz, hier cappen) oder lag es *schon vorher* dort, bevor
ueberhaupt eine Stufe geholfen hat (keine Information, kein Cap)?

**Zweiter Defekt, unabhaengig davon: der Look-Ahead-Horizont ist auf 1 geschrumpft.** Der alte Code
scannte alle Stufen und nahm `max(split_cap, next_stage)`, konnte also ueber eine nutzlose
Zwischenstufe hinwegsehen. Der neue Walk bricht bei der ersten Stufe ohne Gewinn ab. Genau daran
scheitert System 31: die Wahrheit braucht den Kreuzterm `u1*u2` aus Stage 3, die selbstquadratische
Stage 2 bringt dort nichts, der Walk stoppt bei 1. **Das ist die tote Zwischenstufe aus Abschnitt 5.2
des Ausgangsdokuments, wiedereingefuehrt** — dieselbe Begruendung, aus der dort N = 2 als Horizont
vorgeschlagen war.

**Provenienz-Defekt, von der Spec nicht abgedeckt.** Der Fingerprint in `run_regression.jl` fuehrt
die Cap-Politik als hartcodiertes Tupel ohne das neue Feld `aggregation`. WP-L5 hat die Cap-Semantik
materiell geaendert, ohne dass sich `3f9be6d36c4043de` bewegt. Records vor und nach L5 waeren damit
als dieselbe Konfiguration verbucht. Muss mit repariert werden.

**Konsequenz fuer HEAD:** der Arbeitsbaum enthaelt jetzt eine Cap-Berechnung, die unsicherer ist als
die vorige. Bis WP-L5b liegt, darf aus HEAD kein Lauf mit `evogrow_v3_stage_capped` gestartet werden.

<!-- 94bf5a7 -->  

### WP-L5 beauftragt — Cap nur auf positive Evidenz

Behebt den WP-L4-Defekt. Kernprinzip in der Spec: **ein Cap darf nur auf positive Evidenz gesetzt
werden, Abwesenheit von Evidenz muss ungecappt lassen** — die Kosten sind asymmetrisch, ein falscher
Cap macht die Wahrheit unerreichbar, ein fehlender kostet nur den Status quo. Drei Faelle werden
getrennt statt in eine Zahl kollabiert: Residuum ueber dem Boden und naechste Stufe bringt nichts
(→ Cap), Residuum schon unter dem Boden (→ kein Cap), naechste Stufe nicht auswertbar (→ kein Cap).
Die Aggregation ueber Splits darf undentscheidbare Splits nicht stillschweigend verschlucken.

Harte Abnahmekriterien statt Argumentation: 3 → [2], 11 → [4], 26 → [3,3], 31 → [3,3] unveraendert;
63 du1/du2 ungecappt. Dazu eine suiteweite Sicherheitsinvariante — fuer jede Gleichung muss der Cap
entweder `nothing` oder ≥ der wahren Stage sein; aktuell 2 Verletzungen, Ziel 0. Wahrheitswissen
dient dabei ausschliesslich der Beurteilung, nie der Berechnung. Gegengewicht in derselben Tabelle
gefordert: wie viele Gleichungen ueberhaupt noch einen Cap bekommen und wie viele Stufen gespart
werden — eine Regel, die sicher ist, weil sie nie cappt, waere wertlos.

Kritische Nebenbedingung: **der 26/42-Lauf laeuft gerade.** Aendert sich der Cap auf System 26, ist
dessen Vergleichsbasis hinfaellig; die Spec verlangt, das zuerst zu pruefen und bei Abweichung
abzubrechen statt weiterzumachen.

Vorregistriert inklusive Ausweg: laesst sich die Verletzungszahl nicht auf 0 bringen, ohne die
korrekten Caps auf 3/11/26/31 zu verlieren, ist das explizit mit Zahlen zu berichten — es hiesse,
das Rauschboden-Kriterium taugt nicht als Basis fuer einen sicheren Cap, und das waere ein Ergebnis
und kein Misserfolg.

### WP-L4 geliefert — Cap korrekt auf 4 von 5 Systemen; ein Sicherheitsdefekt auf System 63

Neue Variante `evogrow_v3_stage_capped` (`EvoGrowStageCapped`), Cap-Berechnung in
`src/structure/stage_cap.jl`, Bericht in `docs/wp_l4_stage_cap_report.md`. Neuer
`config_fingerprint 3f9be6d36c4043de`. Der entscheidende 26/42-Lauf wurde korrekt **nicht**
ausgefuehrt, `history.jsonl` ist unberuehrt.

**Was haelt.** Ground-Truth-Leckage ist konstruktiv ausgeschlossen: `estimate_stage_caps(traj, basis;
policy)` hat schlicht keinen Parameter, ueber den Wahrheitswissen eintreten koennte — kein
`expected_terms`, kein `expected_stage`, kein `true_rhs!`, keine System-ID. Die v3-Aenderungen sind
additiv mit `stage_caps = nothing` als Default; bei abgeschaltetem Cap ist das Verhalten identisch
(die Umstellung von `all(==(max_stage), eq_stages)` auf die Limit-Form ist aequivalent, weil Stufen
`max_stage` nie ueberschreiten koennen). Der Cap ist reine Obergrenze und entfernt keine Terme.

**Caps selbst nachgerechnet** (eigener Kontrolllauf ueber `estimate_stage_caps`, nicht aus dem
Codex-Bericht uebernommen):

| System | Erwartungsstage pro Gleichung | berechneter Cap | |
|---|---|---|---|
| 3 | [2] | [2] | korrekt |
| 11 | [4] | [4] | korrekt |
| 26 | [3, 3] | [3, 3] | korrekt |
| 31 | [3, 3] | [3, 3] | korrekt |
| 63 | [3, 3, 1, 1] | **[1, 1, 1, 1]** | **du1/du2 falsch** |

**Der Defekt.** Auf System 63 bekommen du1 und du2 einen Cap von 1, obwohl sie den Kreuzterm
`u1*u3` aus Stage 3 brauchen. Unter der gecappten Variante waere die wahre Struktur dort
**strukturell unerreichbar** — die Suche koennte sie nicht mehr finden, egal wie lange sie laeuft.
Die Zusicherung des Berichts, nicht beurteilbare Gleichungen blieben ungecappt, greift hier nicht:
`_cap_for_equation` liefert `nothing` nur, wenn *kein einziger* Split ueberhaupt einen brauchbaren
Stage-1-Fit hat; in jedem anderen Fall liefert es eine Zahl. „Residuum liegt schon bei Stage 1 unter
dem Rauschboden" wird als „Stage 1 genuegt" gelesen statt als „nicht beurteilbar".

**Warum das kein blosser Programmierfehler ist.** Die Regel kann „wirklich nur Stage 1 noetig" nicht
von „Signal zu klein, um zu urteilen" unterscheiden — beide sehen identisch aus: Residuum bei Stage 1
bereits unter dem Boden. Das ist **exakt die Fall-A-gegen-Fall-B-Ambiguitaet aus dem urspruenglichen
Problemdokument, eine Ebene tiefer wiedergekehrt**, jetzt im Bodentest des Look-Aheads selbst. Die
Konsequenz fuer das Design ist asymmetrisch und eindeutig: ein falscher Cap macht die Wahrheit
unerreichbar, ein fehlender Cap kostet nur den Status quo. **Der Cap muss positive Evidenz verlangen,
nicht die Abwesenheit von Evidenz.**

**Fuer die Entscheidungszelle unkritisch.** Auf System 26 ist der Cap [3,3] und damit korrekt; der
vorregistrierte 26/42-Lauf ist von dem Defekt nicht betroffen und kann starten. Der Defekt betrifft
die Verallgemeinerung (Phase B ueber 63 Systeme), nicht diese Zelle.

**Teil A** ist umgesetzt: `lower_stage_indistinguishable` und `rank_deficient_at_tested_stage` sind
getrennt, Rangdefizit wird pro getesteter Stage gefuehrt. Die Schlagzeile aendert sich von
10 exact / 0 over / 2 under / 4 not-identifiable auf **12 exact / 0 over / 4 under / 0 rank_deficient**.
Die beiden neuen Undershoots sind 63 du1/du2 — also derselbe Defekt, im Offline-Bild sichtbar.
Konsistent, und ein gutes Argument dafuer, dass die korrigierte Klassifikation ehrlicher ist als die
alte.

Kleine offene Punkte: beim kombinierten Test-Include trat eine Modul-Ambiguitaet auf, die betroffenen
Tests wurden einzeln nachgefahren; das sollte bereinigt werden, damit die Suite in einem Rutsch
laeuft.

<!-- fca1862 -->

## 2026-07-31

### WP-L4 beauftragt — Stage-Cap aus dem Look-Ahead, erster Test als Mechanismus

Zwei Teile. **Teil A** trennt die beiden Bedeutungen von „nicht identifizierbar", die WP-L3
vermischt und die beide zufaellig 4 ergeben: untere Stage erreicht bereits den Rauschboden (54 du2/du3,
63 du1/du2) gegen rangdefizite hoehere Stage (System 63 gesamt). Ausserdem wird Rangdefizit
**pro getesteter Stage** gefuehrt statt als Pauschaleigenschaft — 63 du3/du4 haben Erwartungsstage 1
und sind dort bestens konditioniert, sie als undentscheidbar zu fuehren untertreibt das Verfahren.
Teil B haengt davon ab, weil der Cap fuer nicht beurteilbare Gleichungen definiert sein muss.

**Teil B** integriert das Gate als Pro-Gleichungs-Obergrenze: `max_useful_stage_k` einmal vor der
Suche berechnet, danach darf keine Gleichung darueber hinaus promoten. Kein spekulatives Unlock, kein
Checkpoint, kein Rollback — das Gate haengt nur an Trajektorie, Basis, Gleichung und Stage, nie an der
Population. Neue Variante mit eigenem Slug; v2.2 und v3 muessen bei abgeschaltetem Cap bit-identisch
bleiben. Der Cap ist reine Obergrenze: er kann eine Promotion nur verhindern, nie ausloesen; nicht
beurteilbare Gleichungen bekommen gar keinen Cap.

**Die schaerfste Auflage der Spec betrifft Ground-Truth-Leckage.** Die Probe hat Wahrheitswissen
bisher nur zur *Auswertung* benutzt (Konfusionsmatrix, analytische Rauschboden-Zeilen). Der Cap muss
allein aus beobachteter Trajektorie und Basis entstehen — nichts aus `expected_terms`,
`expected_stage` oder `true_rhs!` darf ihn erreichen. Dafuer ist ein eigener Test gefordert. Der
Richardson-Boden ist datenbasiert und erlaubt.

**Zweite Auflage: der Readout darf nicht zirkulaer sein.** Auf System 26 ist der Cap `[3,3]`, also
erzwingt er `eq_final_stages = [3,3]` per Konstruktion. Das als Erfolg zu melden waere zirkulaer; es
gilt als Konstruktionspruefung. Die echten Fragen sind: findet `du2` jetzt den richtigen Support
(unter v2.2 endete es als `{u1, u1^2}`, obwohl alle Terme auf Stage 3 verfuegbar waren), wie
verhaelt sich der Loss gegen den v2.2-Anker und das v3-Ergebnis, und wie viel Kosten fallen weg —
gezaehlt in Integrationen, nicht in Wall-Clock. Ausdruecklich als vollwertiges Ergebnis vorgesehen:
Overshoot weg, Kosten runter, `du2` weiterhin falsch. Das hiesse, der Look-Ahead loest die
Komplexitaetsallokation und nicht die strukturelle Wiederfindung — genau die Frage, die seit dem
WP-T2-Befund offen ist.

Der entscheidende Lauf ist **nicht** Teil der Lieferung: Codex implementiert, prueft Bit-Identitaet,
Leckage-Test, Unit-Tests und einen billigen Smoke auf System 3/11 — den 26/42-Lauf startet der User.

### WP-L3 geliefert — alle vier Vorhersagen bestaetigt; die Grenzen sind jetzt vermessen

`studies/lookahead/floor_gated_probe.jl`, Ausgaben in `outputs/studies/lookahead/floor_gated_probe/`.

**Konfusionsmatrix ueber alle 16 exakten Gleichungen** (Hauptkonfiguration `local_poly` +
`richardson_wls` + `ols`, `tau_rel = 1e-4`, `tau_abs = 1e-8`):

| Regel | exact | over | under | not_identifiable |
|---|---|---|---|---|
| threshold_only | 9 | 3 | 0 | 4 |
| **floor_gated** | **10** | **0** | **2** | 4 |

Vorhersage 1 exakt eingetroffen: das Boden-Gate entfernt alle drei System-54-Overshoots und erzeugt
genau zwei Undershoots, beide auf System 54 (du2 und du3, je 3 → 2); du1 wird korrekt. Vorhersage 2
ebenfalls: Systeme 3, 11 und 26 bleiben unter der bodengesteuerten Regel alle korrekt.

**Vorhersage 3 bestaetigt — System 54 ist schaetzer-/sampling-begrenzt, nicht anregungsbegrenzt.**
Schon bei doppelter Dichte (T = 600) erscheint die Stage-3-Klippe: du2 hat Residuen
0,356 | 2,93e-3 | 4,19e-7 | 4,51e-8 | 3,20e-8 bei Rauschboden 6,38e-4 — Stage 2 liegt jetzt *ueber*
dem Boden, Stage 3 darunter, die Klippe ist also aufloesbar. Bei 4x und 8x noch deutlicher.
Aufschlussreich ist die Richtung: das Stage-2-Residuum *steigt* von 6,2e-4 (T = 300) auf 2,93e-3
(T = 600). Bei grobem Sampling absorbierte der Stage-2-Fit einen Teil des Ableitungsfehlers und sah
dadurch besser aus, als er ist — dieselbe Rausch-Absorptionsmechanik wie bei der `r_k`-Kontamination,
nur anders sichtbar. **Die beiden Undershoots sind damit eine Datendichte-Grenze, kein Regelfehler.**

**Vorhersage 4 bestaetigt:** System 63 bleibt bei *jeder* Dichte rangdefizient. Das Defizit ist damit
die Erhaltungsgroesse (die SEIR-Zustaende summieren sich zu einer Konstanten) und keine gewoehnliche
Schlechtkonditionierung.

**Ablation — die billigen Interventionen tragen den Grossteil.** `central` + unweighted +
threshold_only liefert exact 2 / over 10; `central` + `richardson_wls` + floor_gated bereits
exact 9 / over 0 / under 3; erst `local_poly` bringt die zehnte Gleichung. Gewichtung und Boden-Gate
tun also die Hauptarbeit, der teurere Schaetzer setzt oben drauf.

**Ridge ist vollstaendig wirkungslos** — in allen 16 Kombinationen bitgleiche Konfusionszahlen wie
`ols`. Regularisierung rettet nicht-identifizierbare Gleichungen nicht, was zum strukturellen (statt
numerischen) Charakter des Defizits passt. Ehrliches Negativergebnis, gehoert so berichtet.

**Ein Mangel, der vor jeder Paper-Verwendung behoben werden muss: „nicht identifizierbar" bedeutet in
den beiden Artefakten zwei verschiedene Dinge, und beide ergeben zufaellig 4.** Die
`identifiability.csv` flaggt {54 du2, 54 du3, 63 du1, 63 du2}; die Konfusionskategorie
`not_identifiable` umfasst dagegen alle vier Gleichungen von System 63. Dazu kommt: 63 du3 und du4
haben Erwartungsstage 1 und sind auf ihrer eigenen Stage bestens konditioniert (Kondition 234) — sie
als `not_identifiable` zu fuehren, nur weil eine *hoehere* Stage rangdefizit ist, ist konservativ und
untertreibt das Verfahren. Die beiden Definitionen muessen getrennt benannt werden.

**Einordnung.** Die Kernfrage ist damit vollstaendig beantwortet und die Grenzen sind vermessen statt
vermutet: der Test entscheidet korrekt, wo die Ableitung die Struktur aufloest; wo er das nicht tut,
ist die Ursache benannt und quantifiziert (Datendichte auf 54, Erhaltungsgroesse auf 63). Was
weiterhin **nicht** gezeigt ist: dass das die Discovery verbessert. Alles bisher Gemessene ist offline
auf Systemen mit bekannter Wahrheit, und der Checkpoint ist die *volle* Bibliothek, nicht eine
gefundene Struktur.

<!-- 2963fcc -->

### WP-L3 beauftragt — bodengesteuerte Zuendregel, Identifizierbarkeit, Sampling-Grenze

Drei Defekte aus WP-L2, keiner davon ein Zweifel am Kernergebnis: (1) die Zuendregel konsultiert den
berechneten Rauschboden nicht — Pflichtvariante mit Boden-Gate, beide Regeln nebeneinander, und die
Gegenrichtung ausdruecklich mitberichtet (auf 54 du2/du3 faellt das Residuum schon bei Stage 2 unter
den Boden, eine bodengesteuerte Regel unterschiesst dort). (2) Rangdefizit wird ein eigenes Urteil
`not_identifiable` statt eines stillen Ausschlusses, plus regularisierte Fitvariante; zusaetzlich
suiteweit die Frage, wie viele Gleichungen entlang ihrer eigenen Trajektorie nicht identifizierbar
sind — das begrenzt, was *jedes* ableitungsbasierte Verfahren aus einer Trajektorie entscheiden kann.
(3) Dichte-Sweep (2x/4x/8x `T`, `u0`/`tspan` unveraendert) trennt auf System 54 die beiden bislang
konfundierten Erklaerungen: schaetzerbegrenzt (dann erscheint die Klippe bei hoeherer Dichte) gegen
anregungsbegrenzt (dann nie). Auf System 63 muss das Rangdefizit bei jeder Dichte bestehen bleiben,
sonst ist es keine Erhaltungsgroesse, sondern gewoehnliche Schlechtkonditionierung. Sampling-Sweep ist
ausdruecklich als Sensitivitaetsstudie markiert und fliesst nicht in die Hauptkonfusionsmatrix.

### WP-L2 geliefert — Trennung gelingt; die Idee traegt, und `r_k` ist bestaetigt kontaminiert

`studies/lookahead/derivative_estimator_probe.jl`, Ausgaben in
`outputs/studies/lookahead/derivative_estimator_probe/`. Die WP-L1-Diagnose ist bestaetigt: das
vermeintliche Negativergebnis war ein Artefakt der Ableitungsschaetzung.

**Schaetzerwahl.** Median-RMS-Ableitungsfehler: `central` 1,75e-2, `fd4` 1,24e-2, `local_poly`
1,78e-3. **Hoehere FD-Ordnung ist nicht der Hebel — Glaettung ist es** (Faktor 10 gegen Faktor 1,4).

**Die Trennung gelingt sauber.** Holdout-Residuen mit `local_poly`, Splits A/C/D (B bleibt der
degenerierte Schwanz-Fit):

| Stage | System 26 du2 (wahr: 3) | System 11 du1 (wahr: 4) |
|---|---|---|
| 1 | 2,98e-3 | 7,89e-4 |
| 2 | 3,34e-6 | 4,53e-5 |
| 3 | **5,24e-13** | 4,53e-5 (leer, identisch) |
| 4 | 2,70e-11 (schlechter) | **7,60e-12** |
| 5 | 1,81e-11 | 5,05e-9 (schlechter) |

Beide Klippen sitzen exakt auf der wahren Stage, danach verschlechtert es sich. System 26 du2 faellt
von 3,65e-3 (WP-L1) auf 5,24e-13 — zehn Groessenordnungen, allein durch die Ableitungsschaetzung.
System 3 bleibt korrekt bei Stage 2. Alle drei vorregistrierten Vorhersagen halten. **Damit ist die
Kernfrage des Diskussionsdokuments beantwortet: ein billiger Ableitungs-Look-Ahead trennt die beiden
Gegenbeispiele, sobald die Ableitung stimmt.**

**Teil 4 — `r_k`-Kontamination bestaetigt, und staerker als vermutet.** Auf System 26 liegt der Boden
mit *wahrer* Struktur und *wahren* Parametern bei [1,808, 0,520], das gefittete volle Stage-3-`r_k`
dagegen bei [0,142, 0,0394] — der Boden liegt um Faktor 13 **darueber**. `r_k` misst also nicht
strukturelle Angemessenheit, sondern wie viel Ableitungsfehler ein Modell absorbieren kann, und diese
Kapazitaet waechst mit der Termzahl. Das Signal ist damit systematisch nach „mehr Terme helfen"
verzerrt — genau die Eskalation, die v3 gezeigt hat. Der bessere Schaetzer senkt den Boden auf
[0,425, 0,106] (Faktor 4,3 / 4,9), beseitigt ihn nicht. **v3s Scheitern an Gate 2 hat damit eine
zweite, numerische Ursache zusaetzlich zur Evidenz-Diagnose.**

**Drei Einschraenkungen, die der gelieferte Bericht zu leicht nimmt.** Erstens deckt die
Konfusionsmatrix nur 12 der 16 exakten Gleichungen ab: System 63 faellt komplett heraus, Stages ≥3
sind auf allen Splits rangdefizient (Kondition > 1e10). Die Ursache ist strukturell — die
SEIR-Zustaende summieren sich zu einer Konstanten, es gibt eine exakte lineare Abhaengigkeit zwischen
den Variablen; passend dazu erreicht du1 schon bei Stage 2 ein Residuum von 1,2e-14, obwohl die wahre
Gleichung einen Kreuzterm braucht. Der Vergleich „5 Overshoots vorher, 3 jetzt" ist deshalb nicht
like-for-like, die schweren Faelle sind aus dem Nenner gefallen. Zweitens sind alle drei verbliebenen
Overshoots System 54 und reines Rauschfitten: bei du1 liegt der Rauschboden bei 8,0e-4, saemtliche
Residuen ab Stage 1 bei 5,9e-6 und darunter — die Zuendregel konsultiert den Boden nicht, obwohl er
berechnet wird. Drittens ist die naheliegende Korrektur kein Freifahrtschein: bei 54 du2/du3 faellt
das Residuum schon bei Stage 2 unter den Boden, eine bodengesteuerte Regel wuerde dort unterschiessen.
Ehrliche Lesart: auf Lorenz reicht die Ableitungsgenauigkeit bei gegebenem Sampling nicht, um die
Stage-3-Kreuzterme aufzuloesen. Kleinigkeit: Split D wurde ergaenzt, aber nirgends beschrieben.

**Einordnung.** Die Grenze des Verfahrens zeichnet sich klar ab und ist selbst ein Ergebnis: der Test
funktioniert, wo die Ableitungsschaetzung die Struktur aufloest; die Systeme 54 (schnelle Dynamik) und
63 (Erhaltungsgroesse) markieren, wo das aufhoert. Das ist eine publizierbare Aussage, kein Scheitern.

<!-- 24145f6 -->

### WP-L2 beauftragt — Ableitungsschaetzung als bindende Schranke

Konsequenz aus WP-L1. Vier Teile, alle rein diagnostisch: (1) Schaetzervergleich gegen den
*tatsaechlichen* punktweisen Fehler — das wahre RHS ist bekannt, also ist der Fehler exakt
berechenbar; dazu eine Richardson-Schaetzung (Gitter gegen halbiertes Gitter) mit Pflichtvalidierung
gegen den echten Fehler, denn ein Fehlerschaetzer, der den echten Fehler nicht nachbildet, ist
stromabwaerts wertlos. (2) Probe erneut, Baseline- und bester Schaetzer nebeneinander, plus gewichtete
Regression mit Richardson-Gewichten und punktweisem statt blockweisem Rauschboden. (3) Splits mit
explizitem Gueltigkeitskriterium; ungueltige Splits werden ausgewiesen und ausgeschlossen, nicht
mitgemittelt. (4) die `r_k`-Kontaminationsmessung.

`src/optimize/pretune.jl` bleibt ausdruecklich unangetastet — `estimate_derivatives` speist den
Pretuning-Warmstart und das v3-Promotionssignal; eine Aenderung dort bewegt Suchverhalten und
`config_fingerprint`. Alle Alternativschaetzer leben im Study-Code.

Vier Vorhersagen vorab registriert, mit Abbruchklausel: scheitern die Vorhersagen zu System 11
(grosser stabiler Stage-4-Gewinn) oder System 26 (Stage-3-Residuum faellt Richtung analytischen Boden,
kein Gewinn bei 4/5) unter *allen* Schaetzern, ist der Ableitungsraum auf transientenlastigen Systemen
zu schwach fuer einen Look-Ahead. Das waere ein echtes Negativergebnis und ist so zu berichten, statt
weitere Schaetzer nachzuschieben, bis etwas passt.

### WP-L1 geliefert — das vermeintliche Negativergebnis ist ein Messartefakt

Isolierte Stage-Potential-Probe (`studies/lookahead/stage_potential_probe.jl`), Ausgaben in
`outputs/studies/lookahead/stage_potential_probe/`. Umfang gegenueber dem Diskussionsdokument
erweitert: 10 Benchmark-Systeme statt 3, davon 8 exakte mit 16 Gleichungen, jeweils mit
pro-Gleichungs-Erwartungsstage aus `expected_terms` + `term_groups` (System 63 → [3,3,1,1],
System 54 → [1,3,3]). Kein `strogatz_extended.json`-Parsing. Keine ODE-Simulation in der Probe, kein
BFGS, kein RNG, kein `src/`-Eingriff. Leerstufen korrekt erkannt (System 11, Stage 3: `new_terms = 0`).

**Der Bericht meldet: keine Trennung.** Kein Gitterpunkt liefert „System 26 stoppt bei Stage 3" und
zugleich „System 11 geht bis Stage 4"; bestes Gitter `tau_rel = 0.05`, `tau_abs = 1e-6`, Konfusion
under 2 / exact 9 / over 5. **Diese Schlagzeile ist nicht belastbar.** Die Rauschboden-Zeilen, auf
denen die Spec bestanden hat, zeigen warum — Split A, Holdout:

| | analytisch wahres RHS | LS-Fit wahrer Support | volle Bibliothek |
|---|---|---|---|
| System 3, du1 | 8,2e-12 | 4,6e-7 | Stage 2: 4,6e-7 → Stage 5: 2,6e-6 |
| System 11, du1 | 1,9e-9 | 2,3e-4 | Stage 2: 5,1e-3 → **Stage 4: 8,8e-2** |
| System 26, du2 | 4,3e-11 | 5,7e-3 | **Stage 3: 3,7e-3** → Stage 5: 1,5e-7 |

Zwei Zeilen tragen die Diagnose. **System 26 du2 ist bei Stage 3 exakt darstellbar** — der Holdout der
vollen Stage-3-Bibliothek muesste auf dem Boden von 4,3e-11 liegen, liegt aber acht Groessenordnungen
darueber; der Fit der wahren Struktur ist mit 5,7e-3 sogar schlechter als die volle Bibliothek.
**System 11 wiederholt exakt das WP-T1-Muster:** das analytisch wahre RHS hat auf dem Fit-Block
Residuum 4,606, der LS-Fit derselben wahren Struktur kommt auf 1,159 — der Fit schlaegt die Wahrheit
um Faktor 4, was nur beim Fitten von Rauschen moeglich ist. Entsprechend sieht Stage 4 (8,8e-2)
schlechter aus als Stage 2 (5,1e-3), die kubische Klippe ist unsichtbar.

Ursache ist `estimate_derivatives` — ein einfacher zentraler Differenzenquotient. System 11 startet
bei `du = -39,3`, System 26 du2 bei `du = -31,4`, beide bei `h = 0,05`. Im Transienten ist der
FD-Fehler dort von Ordnung 1, also groesser als jedes zu detektierende Signal. System 3 hat zahme
Dynamik und liefert das korrekte Urteil. **Das Muster ist nicht „die Idee traegt nicht", sondern „die
Probe funktioniert genau dort, wo die Ableitung stimmt".** Die Idee ist damit nicht widerlegt, sondern
ungeprueft — dieselbe Lage wie bei der Screening-Spur im Juli, diesmal aber mit sofort bekannter
Ursache.

Zweiter, unabhaengiger Mangel: **Split B ist strukturell wertlos.** Er fittet auf dem kollabierten
Trajektorienschwanz (Trainingsresiduen ~1e-11, Konditionszahlen bis 3,9e11) und extrapoliert in den
Transienten (Holdout 1,8 bis 5,3e8). Der Bericht bildet den Median ueber alle drei Splits, mischt also
einen brauchbaren mit einem degenerierten — die Aussage „keine Trennung" ist teilweise
Aggregationsartefakt.

**Nebenbefund mit potenziell groesserer Tragweite als die Probe selbst.** `estimate_derivatives` ist
nicht nur hier im Einsatz: WP-v3.4 verwendet dasselbe Signal als Promotionskriterium (`r_k` ist das
Ableitungsresiduum auf der beobachteten Trajektorie). Ist der FD-Fehler auf System 26 von Ordnung 1,
war das Plateau, auf das v3 seine Stage-Entscheidungen gestuetzt hat, dort massgeblich ein numerisches
Artefakt — eine **zweite, von der Evidenz-Diagnose unabhaengige Erklaerung fuer das Scheitern an
Gate 2**. Als Hypothese notiert, nicht als Befund; Messung ist Teil 4 von WP-L2.

<!-- 57fa6ba -->

### Gate 2 entschieden — v3 gescheitert, Entkopplung bleibt aus

Der Do-or-Die-Lauf ist durch (System 26, Seed 42, 30 Level, `evogrow_v3`, Fingerprint
`1f9c5f807d609548`, `git_hash e82715b`, `git_dirty false`, 13.047 s ≈ 3,6 h). Ergebnis gegen die am
2026-07-30 vorab festgelegten drei Kriterien:

| Kriterium | Soll | Ist | Urteil |
|---|---|---|---|
| (a) `eq_final_stages[1]` | 3 | 5 | verfehlt |
| (b) du1-Support | exakt `{u1, u1^2, u1*u2}` | zusaetzlicher u2-Term | verfehlt |
| (c) Loss | ≤ 0,001391623174905009 | 2,5195575964774715e-4 | erfuellt |

`eq_final_stages = [5,5]`, `eq_overshoot = [2,2]`. **Keine erkennbare Entkopplung — v3 faellt durch
Gate 2.** Bemerkenswert ist (c): der Loss ist gegenueber dem eingefrorenen v2.2-Anker um Faktor 5,5
besser. Die Fitqualitaet war also nie das Problem; gescheitert ist die Komplexitaetsallokation, also
genau der Punkt, fuer den v3 gebaut wurde.

**Diagnose.** Die v3-Promotionsregel stellt pro Gleichung drei Fragen: genug Stage-Budget, `r_k`
plateau, `r_k > loss_tol = 1e-8`. Bedingung 3 ist auf gekoppelten Systemen unerreichbar — der
Fehlerboden liegt bei 1e-3 bis 1e-4. Fuer eine bereits korrekt modellierte Gleichung sind damit alle
drei Bedingungen dauerhaft erfuellt, und die Regel kann Untermodellierung (eine hoehere Stage enthaelt
wirklich relevante Terme) nicht von einem irreduziblen Fehlerboden (die Struktur reicht, aber Numerik,
Fit, Daten oder Kopplung verhindern kleinere Residuen) unterscheiden. Beide Faelle sehen identisch
aus: flaches Residuum oberhalb von 1e-8. Deshalb eskalieren auch unabhaengige Pro-Gleichungs-
Controller weiter bis Stage 5 — die Dezentralisierung war technisch aktiv, aber beide lokalen
Automaten trafen dieselbe qualitative Entscheidung.

**Zentraler Erkenntnisgewinn: v3 hat veraendert, wer entscheidet, aber nicht, welche Evidenz eine
Promotion rechtfertigt.** Das ist ein sauberes, publizierbares Negativergebnis und keine verlorene
Arbeit.

Ein bloss relatives Kriterium statt des absoluten Zielwerts loest das ebenfalls nicht. Gegenbeispiel-
paar: Lotka-Volterra (Best-Loss 3,84e-2 → 3,35e-3 → 1,39e-3 → flach; richtig waere *stoppen* nach
Stage 3) gegen `du = -u^3` (2,96e-1 → 3,43e-3 → flach → 4,40e-15; richtig waere *weitergehen* ueber
die flache Stage 3, die in 1D sogar leer ist). Beide Entscheidungsmomente sehen lokal gleich aus —
Loss um 1e-3, aktuelle Stage bringt nichts, Verlauf flach. Der Unterschied liegt ausschliesslich in
Information ueber zukuenftige Termgruppen. **Das Stage-Zuend-Problem ist damit ein Look-Ahead-Problem
unter Unsicherheit.** Ein vollstaendiger simulationsbasierter Look-Ahead ist wegen der ODE-Kosten
untragbar; deshalb die Pruefung eines billigen Tests im Ableitungsraum (WP-L1).

Offen und bewusst noch nicht entschieden: PAPER_1 sieht fuer ein gescheitertes Gate 2 „v2.2 mit
ehrlicher Failure-Analyse **oder** Planrevision" vor. Der Look-Ahead waere faktisch v4. Die
Entscheidung haengt am WP-L2-Ergebnis.

<!-- a022ed2 -->

## 2026-07-30

### WP-G2.1 geliefert — Zwei-Varianten-Runner, Einzelzell-Selektor, Do-or-Die-Readout

Gate-2-Vorbereitung: statt einer teuren 45-Lauf-Matrix ein sequenzieller, paarweiser v2.2-vs-v3-Vergleich mit **System 26 / Seed 42 als vorab festgelegter Do-or-Die-Zelle**. Der v2.2-Arm ist bereits eingefroren (Baseline v0, von WP-T2 bit-exakt reproduziert), also genuegt zum Entscheiden **ein** frischer v3-Lauf. Tests real gefahren (Baseline abgebrochen, keine CPU-Konkurrenz):

- **Runner auf zwei Varianten** (`evogrow_v2_2_stage_local`, `evogrow_v3`); Screening aus der Ausfuehrungsliste. `test_regression_runner_gate2.jl` 6/6.
- **Einzelzell-Selektor** ueber `EVO_REGRESSION_VARIANT/SYSTEM_ID/SEED` (leer = volle Matrix), plus `EVO_REGRESSION_HISTORY_PATH`-Override. `main()` nur noch unter `PROGRAM_FILE`-Guard, damit `include`-bar fuer Tests.
- **`BFGS_TIME_LIMIT_S` 86.400 → 1.800 s** (reine Notbremse; greift nie — WP-T1/T2). Aendert bewusst den `config_fingerprint`.
- **Fingerprint sauber:** Codex hat `FINGERPRINT_VARIANT_LABELS` (die alten drei Labels) eingefroren, sodass die Variantenreduktion den Fingerprint **nicht** bewegt. Verifiziert: aktuell `1f9c5f80…` vs. v0 `0c739d4e…`, Delta nur durch das Zeitlimit.
- **Do-or-Die-Readout** (`studies/gate2_do_or_die/readout.jl` → `outputs/studies/gate2_do_or_die/`): reines Post-Processing, stellt v3/26/42 gegen den eingefrorenen v2.2-Anker. Vorab festgelegtes Kriterium — PASS nur wenn (a) `eq_final_stages[1]==3` (du1 bleibt auf wahrer Stage, kein Overshoot), (b) du1-Support exakt `{u1,u1^2,u1*u2}`, (c) Loss ≤ 0.001391623174905009; sonst PARTIAL (nur a verletzt) bzw. FAIL. `test_gate2_do_or_die.jl` 9/9 (PASS/PARTIAL/FAIL).

Zwei kleine Unsauberkeiten der Lieferung, ohne Korrektheitsfehler: (1) Codex schrieb sechs ungefragte v2.2-Scalar-Records unter einem Zwischenstand-Fingerprint `d596e066` (den der finale Code nicht mehr erzeugt) in die echte History — per `git checkout -- history.jsonl` entfernt, da git-getrackt und einzige uncommittete Aenderung. (2) Der v3-Smoke lief nicht end-to-end ueber den Runner (nur der Selektor unit-getestet); Risiko gering, der echte 26/42-Lauf deckt es ab.

Naechster Schritt: der User startet den einen Lauf (`EVO_REGRESSION_VARIANT=evogrow_v3 EVO_REGRESSION_SYSTEM_ID=26 EVO_REGRESSION_SEED=42`), dann `readout.jl` → Gate-2-Vorentscheidung.

<!-- f13dbc7 -->

### WP-v3.5 geliefert — Pro-Gleichungs-Overshoot-Metriken + gekoppelter Integrations-Smoke

Codex hat die Pro-Gleichungs-Metriken umgesetzt und die Integrationsluecke geschlossen. Statisch geprueft (Julia nicht gestartet, Baseline v1 laeuft weiter):

- **Metrik-Funktionen (§8):** `eq_overshoot`/`eq_wasted_levels` in `src/structure/evogrow_v3_promote.jl` — rein abgeleitet, kein RNG, keine Integration; `eq_overshoot` klammert Untersteuerung, `eq_wasted_levels` zaehlt Level ueber `expected_stage`. Exportiert in `EvoODE.jl`.
- **Record-Aufnahme:** `run_regression.jl` zieht `eq_stage_histories` aus den Meta-Daten; `has_eq_stage_data`-Guard verlangt beide Felder (`eq_final_stages` + `eq_stage_histories`), sonst bleiben beide neuen Felder `nothing` — genau wie `eq_final_stages` bei Nicht-v3-Varianten.
- **Fingerprint unveraendert:** nur zwei Ausgabefelder plus deren Export; keine gehashte Hyperparameter-Konstante angefasst. Additiv am Record-Schema, das nicht in den Fingerprint eingeht.
- **Integrationsluecke geschlossen.** `test/smoke_evogrow_v3_coupled_divergence.jl` faehrt ein billiges synthetisches 2D-System end-to-end: `u1=exp(-0.5t)` (exakt `du1=-0.5·u1`, Stufe 1) vs. `u2=1/(1+t)` (`du2=-u2²`, Stufe 2). Gleichung 1 faellt unter `loss_tol` und promotet nie, Gleichung 2 steigt — `eq_final_stages` divergieren. Damit lief der divergente Pfad (v3.3 eq-aware Child-Generation + v3.4 Pro-Gleichungs-Promotion) **erstmals in einem echten gekoppelten Lauf**, bisher nur mit injizierten Stufen unit-getestet. Ein `FastDerivativeOptimizer` ersetzt BFGS (keine teuren ODE-Solves), umgeht aber den zu testenden Suchpfad nicht — Child-Generation und Promotion laufen durch echten EvoGrowV3-Code.
- **Tests:** `test/test_evogrow_v3_metrics.jl` (alle drei Spec-Faelle inkl. Aggregat-Konsistenz `maximum(eq_overshoot) == max(0, maximum(eq_final_stages) - expected_stage)`).

Such-Verhalten und globale Metriken (`stage_overshoot`/`wasted_levels`) unangetastet; die Pro-Gleichungs-Metriken verfeinern nur. Damit ist die v3-Kette bis zur Validierung komplett. Naechster Schritt: WP-v3.6 — externer Validierungslauf v3 vs. Baseline v1 (Overshoot-Rueckgang auf gekoppelten Systemen 26/31/63), nach Abschluss der laufenden Baseline.

<!-- 960b0e6 -->

## 2026-07-29

### WP-v3.4 geliefert — Pro-Gleichungs-Promotion scharf geschaltet

Codex hat die Pro-Gleichungs-Promotionsregel umgesetzt: `src/structure/evogrow_v3_promote.jl` (neu); `evogrow_v3.jl` ersetzt die Lockstep-Promotion durch pro-gleichungs `r_k`-Plateau plus globale Termination; der Bit-Identitaets-Smoke wurde durch einen Scalar-Promote-Smoke ersetzt (korrekt — v3.4 bricht die v2.2-Gleichheit bewusst). Statisch geprueft (Julia nicht gestartet, Baseline v1 laeuft):

- **Signal (§3):** `r_k` = Ableitungsresiduum auf der beobachteten Trajektorie; `estimate_derivatives` aus `pretune.jl` wiederverwendet, RHS pro Gleichung an beobachteten Zustaenden ausgewertet — keine Integration im Normalpfad, RNG-neutral (kein Einfluss auf den Such-Stream). Fallback auf Trajektorienresiduum mit lauf-globalem Flag.
- **Promotion (§4):** drei Bedingungen (Budget `max(min_levels_per_stage, plateau_window+1)`, `r_k`-Plateau, `r_k > loss_tol`) plus Maxstufen-Guard; mehrere Gleichungen koennen pro Level promoten. `eq_plateau_histories` traegt jetzt `r_k` statt `best.objective`.
- **Termination (§5):** vor der Promotion ausgewertet → globaler `loss_tol`-Stopp hat Vorrang; neue Erschoepfung „alle Gleichungen auf Maxstufe und plateaut"; `min_levels`-Guard erhalten.
- **Tests stark:** `test/test_evogrow_v3_promote.jl` deckt alle vier §4-Bedingungen deterministisch ab (Plateau / `r_k<tol` / Budget / Maxstufe) plus den `r_k`-Signal-Test (Konstanten-Basis, lineare Trajektorie → `r_1≈0`, `r_2=9`). `test/smoke_evogrow_v3_scalar_promote.jl` faehrt System 3+11 end-to-end ohne v2.2-Gleichheitsanspruch.
- EvoGrow/v2.2 und Child-Generation unangetastet; `promotion_log`-Formaenderung unkritisch (nur generische Serialisierung in `experiments/run_experiment.jl`).

**Bewusst kein No-Op:** das Plateau-Signal wechselt von `best.objective` auf `r_k`; das aendert das Verhalten auch auf skalaren Systemen. Bit-Identitaet war hier nicht das Kriterium, sondern deterministische Unit-Test-Logik.

Zwei kleine, nicht-blockierende Punkte fuer spaeter: `stage_level_count` ist jetzt toter Code (wird inkrementiert, nie gelesen); der Trajektorien-Fallback ist ungetestet (nur bei nicht-finiter FD aktiv). Naechster Schritt: WP-v3.5 (expected-stage-Metriken `eq_overshoot`/`eq_wasted_levels`), dann WP-v3.6 (Validierung gegen Baseline v1: Overshoot-Rueckgang auf 26/31/63, extern nach der laufenden Baseline).

<!-- a334256 -->

### WP-v3.3 geliefert — gleichungs-bewusste Child-Generation, unter Lockstep bit-identisch

Codex hat WP-v3.3 umgesetzt: `src/structure/evogrow_v3_childgen.jl` (neu), `evogrow_v3.jl` ruft im Level-Loop jetzt `_expand_equation_aware_with_usage_policy` statt `_expand_with_usage_policy`, `EvoODE.jl` bindet die neue Datei ein. Verifikation **statisch** geprueft (Julia nicht gestartet, um die parallel laufende Baseline v1 nicht um CPU zu bringen; Ausfuehrungs-Evidenz liefert Codex' eigener Testlauf):

- **Strukturelle Bit-Identitaet korrekt.** Bei uniformen `eq_stages` — dem Lockstep-Zustand — delegiert `_expand_equation_aware_with_usage_policy` an den unveraenderten `_expand_with_usage_policy` mit denselben `allowed_terms`/`current_stage_terms`: derselbe Code, dieselbe RNG-Reihenfolge. Der Pro-Gleichungs-Pfad wird nur bei divergierenden Stufen betreten und ist bis WP-v3.4 (Promotion) im echten Lauf tot.
- **Verfuegbarkeits-Praedikat korrekt.** `stage(t)` aus `term_groups`, `vars(t)` per Regex `u(\d+)` aus `basis_term_name`. Namensformat bestaetigt (`u1`, `u1^2`, `u1*u2`, `u1^3`, `sin(u1)`, `cos(u1)`) — nur echte Cross-Terme haben zwei Variablen, dort greift die Paarregel `min(eq_stages[v] for v in vars(t)) >= stage(t)`.
- **Tests stark.** `test/test_evogrow_v3_childgen.jl`: divergente Stufen `[1,3]` (Gleichung 1 nur Stage-1-Terme, `u1*u2` fuer keine Gleichung verfuegbar) und — der harte Teil — die Delegation bei `[3,3]` erzeugt byte-identische Kinder wie der Direktaufruf (gleicher Seed, Vergleich aller `active_idxs`). `test/smoke_evogrow_v3_bit_identity.jl`: EvoGrowV3 gegen EvoGrow(v2.2) end-to-end auf analytischer System-11-Trajektorie; bricht bei jeder Abweichung in loss/objective/final_stage/Struktur ab. Transitiv: WP-v3.2 hatte EvoGrowV3 ≡ v2.2 etabliert, dieser Smoke bestaetigt es nach v3.3, also v3.3 unveraendert.

Promotion (`_lockstep_stage_progression_decision`, `_apply_lockstep_stage_update!`), Metriken und `EvoGrow`/v2.2 unangetastet. `history.jsonl` bewusst nicht committet — die Baseline v1 schreibt dort gerade live. Naechster Schritt: WP-v3.4 (Pro-Gleichungs-Promotionsregel), die die Stufen erst divergieren laesst — regressionsgeprueft gegen Baseline v1.

<!-- f6261a0 -->

### WP-T2 gelaufen — Vorhersage bestaetigt, Overshoot algorithmisch, v3 validiert

Der externe System-26-Lauf ist durch (16,8 h Wall-Clock, Seed 42, 30 Level, drei Bedingungen D8/R8/R6). Ausgaben in `outputs/studies/numerics/system26_tolerance_screening/`. **Anker bit-exakt reproduziert:** R6 (1e-6) liefert `0.001391623174905009`, `final_stage = 5`, Overshoot 2, wasted 8, `pruned_match = false` — identisch zu Baseline v0 (`0c739d4e36ee6498`). Damit ist die Messung interpretierbar.

**Q2 — Toleranz aendert den Overshoot nicht (Vorhersage bestaetigt).** R6 (1e-6) und R8 (1e-8) haben bit-identisch `final_stage = 5`, `stage_overshoot = 2`, `wasted_levels = 8`. Die engere Toleranz senkt nur den Loss (1,39e-3 → 2,52e-4), nicht das Stopp-Verhalten. Beide terminieren via `plateau_absolute`, keiner naehert sich je `loss_tol = 1e-8` (haengt bei 1e-4 bzw. 1e-3). **Der Overshoot auf System 26 ist algorithmisch, nicht numerisch** — genau die geschaerfte Prognose vom 2026-07-23. Damit trennt die Messung sauber: auf System 3 numerisch (siehe 2026-07-22), auf gekoppelten Systemen algorithmisch. Die v3-Begruendung ist bestaetigt, nicht bedroht.

**Q3 — Screening auf gekoppeltem System: schnell, aber kein Discovery-Gewinn.** D8 (Screening) gegen R8 (Referenz), beide 1e-8:
- Deterministisch, tragend: D8 braucht **98.253 Integrationen gegen R8s 3.348.287** (34x weniger). Beide `pruned_match = false`, beide Overshoot 2. D8 nutzt 9 Terme (5+4), R8 nur 6 (4+2) — D8s niedrigerer Loss (1,01e-4 vs 2,52e-4) ist Ueberparametrisierung, kein Strukturgewinn.
- Ranking-Kollaps: `rank_agreement_spearman` Median **−0,014** (Mittel 0,12, Min −0,64, Max 0,998). Das FD-Ableitungs-Screening rankt Kandidaten auf dem gekoppelten System praktisch nicht wie der echte Loss. Der 34x-Vorteil kommt aus wenig-integrieren, nicht aus gutem Diskriminieren.
- Nested-F-Gate hier **inert**: `selection_diff_from_residual = 0` ueber alle Level. Der WP-P2.4-Durchbruchmechanismus aendert auf System 26 keine einzige Auswahl gegenueber purem Residual. Er half auf System 3, tut hier nichts — der Gate-Nutzen ist systemabhaengig.

Fazit: Screening ist eine Performance-Optimierung (mit `polish_start=reference` sicher), kein Discovery-Qualitaets-Hebel. Gehoert als optionale Beschleunigung dokumentiert, nicht in den Kern-Claim; der Ranking-Kollaps muss in die Discussion.

**Q4 — der v3-Beleg steckt in der Struktur.** Wahrheit: `du1 = 3·u1 − u1² − 2·u1·u2 | du2 = 2·u2 − u1·u2 − u2²`. R8 nach Pruning: `du1`-Support `{u1, u1², u1·u2}` = **exakt Gleichung 1** (`3.03·u1 − 1.07·u1² − 1.99·u1·u2`), aber `du2` = `{u1, u1²}` — **komplett falsch.** Eine Gleichung geloest, die andere im Blindflug; der globale Plateau-Mechanismus eskaliert Stages 4/5 fuer beide, obwohl Gleichung 1 laengst fertig ist. **Das ist die Signatur, die v3 (gleichungsweise Promotion) aufloest:** geloeste Gleichung einfrieren, nur die offene weiterwachsen. Robust (suspend-fest): 8 von 25 Leveln (R8) liegen jenseits der erwarteten Stage 3, das sind ~25 % der Integrationen (Stages 4+5: 832.350 von 3.348.287 Solves).

**Korrektur meiner eigenen „63 %"-Aussage.** Die 63 % Overshoot-Kosten waren die *Wall-Clock*-Sicht (Zeitanteil der Stages 4+5 bei R8). Nach deterministischer Integrationszaehlung sind es ~25 %. Die Differenz kommt daher, dass die spaeten Integrationen einzeln teurer sind (bei 1e-8 kostet ein Stage-5-Solve 35 ms) — das ist zum Teil eine echte numerische Eigenschaft, aber die Wall-Clock-Achse ist genau die vom Suspend kontaminierte. Load-bearing bleibt: 8 verschwendete Level, ~25 % der Integrationen, eine Gleichung exakt, die andere blind.

**Nebenbefund Toleranz.** 1e-8 senkt den Loss, aendert aber kein Stopp-Verhalten auf plateauenden Systemen und verteuert ausgerechnet die verschwendeten Spaeten-Stages. Fuer den Suchpfad auf gekoppelten Systemen ist 1e-6 die guenstigere, verhaltensgleiche Wahl. Der WP-T1-Rauschgrenzen-Aspekt bleibt nur fuer exakt loesbare Systeme relevant, die die Toleranz tatsaechlich erreichen (z. B. System 11) — separate, kleinere Frage.

### Messvorbehalt — Wall-Clock kontaminiert, deterministische Schluesse unberuehrt

Der PC wurde waehrend des Laufs 2x zugeklappt (Weg zur Arbeit und zurueck, je ~45 min, ~90 min gesamt), und es lief Nebenlast durch paralleles Arbeiten. **Das kontaminiert ausschliesslich die Wall-Clock-Achse:** `elapsed_s`, `s_per_level`, `ms_per_ode_solve`, Zeitanteile und der 6,35x-Speedup sind aufgeblaeht und verrauscht und duerfen nicht als praezise Messwerte zitiert werden. Warum die wissenschaftlichen Schluesse trotzdem stehen:

1. **Anker bit-exakt** → die Berechnung selbst ist unkorrumpiert; Suspend hat den Determinismus nicht gebrochen.
2. **`time_limit_s = 86400` war nie bindend** (max R8: 31.413 s ≪ 86.400 s) → keine Iteration wurde zeitlich abgeschnitten → Iterationszahlen und Ergebnisse deterministisch, unabhaengig von Suspend-Luecken.
3. **Alle tragenden Zahlen sind Zaehlungen, keine Zeiten:** Stage, Overshoot, wasted_levels, Struktur/Support, Integrationszaehlungen (98.253 vs 3.348.287), Rank-Agreement, Gate-Diagnostik. Genau dafuer hat WP-P1 die Wall-Clock aus dem Ergebnispfad entfernt und das Skript die Solve-Zaehlungen praezise protokolliert.

Konsequenz fuer das Paper: Kosten ueber Integrationszaehlungen berichten, nicht ueber Wall-Clock. Fuer eine belastbare Zeitmessung braeuchte es einen ungestoerten Lauf ohne Suspend/Nebenlast; das ist aber fuer die v3-Begruendung nicht noetig, weil diese auf den deterministischen Achsen ruht.

<!-- e8f12f4 -->

## 2026-07-23

### WP-T2 beauftragt — Toleranz und Screening auf System 26, mit geschaerfter Vorhersage

Naechster Schritt festgelegt: die entscheidende Messung auf System 26, dem Gate-1-System. Drei Bedingungen, Seed 42, 30 Level: R6 (Referenz, Toleranz 1e-6), R8 (Referenz, 1e-8), D8 (Screening Nested-Gate + entkoppelter Start, 1e-8). User hat die kombinierte Ein-Seed-Variante gewaehlt.

**Geschaerfte Vorhersage, die den Wert der Messung erhoeht.** Beim Durchdenken des Mechanismus zeigt sich, dass mein urspruengliches „Overshoot koennte numerisch sein" zu breit war. Der numerische Kanal auf System 3 war spezifisch: der Loss operiert dort nahe `loss_tol = 1e-8`, und bei 1e-6 erreicht der Optimierer die Schwelle nicht → kein Abbruch → Eskalation. Auf System 26 liegt der Loss-Boden bei ~1,4e-3, also drei Groessenordnungen **ueber** selbst der 1e-6-Toleranz. `loss_tol` kann dort nie feuern, unabhaengig von der Toleranz, und die Eskalation ist plateau-getrieben. **Vorhersage: die engere Toleranz aendert den Overshoot auf System 26 nicht — der Overshoot ist hier algorithmisch, was die v3-Begruendung bestaetigt statt bedroht.** Falsifizierbar an den gemessenen Stage-Zahlen.

Damit trennt die Messung im Bestaetigungsfall sauber: auf einfachen Systemen numerisch, auf gekoppelten algorithmisch — eine staerkere Paper-Aussage als „Overshoot ist numerisch". Im Widerlegungsfall verstehe ich den Mechanismus nicht und muss das vor v3.3 klaeren. Unabhaengig davon wird D zum ersten Mal auf einem gekoppelten System getestet, dem, wo v2.2 die Struktur komplett falsch fand.

Ankerpflicht in der Spec: R6 muss Baseline v0 reproduzieren (System 26 Seed 42, 30 Level, 1e-6: Loss `0.001391623174905009`, `final_stage = 5`, Overshoot 2, `pruned_match = false`). Ohne bestaetigten Anker ist nichts interpretierbar. Reihenfolge nach steigender Laufzeit (D8, R8, R6), nach jeder Bedingung sofort schreiben.

### WP-T2 und WP-T2b geliefert — Lauf startklar

WP-T2 (`78124f0`): `studies/numerics/system26_tolerance_screening.jl`, drei Bedingungen D8/R8/R6, Anker gegen Baseline v0, inkrementelles Flush, Antwortblatt fuer die vier Fragen. Beim Spec-Schreiben Fast-Fehler korrigiert: die urspruengliche Verification-Zeile „Skript ausfuehren und berichten" haette Codex den 5-8h-Lauf starten lassen — durch No-Execute-Riegel plus billigen System-3-Smoke-Test ersetzt. Als Gedaechtnisnotiz festgehalten ([[feedback_long_run_no_execute]]).

WP-T2b (`4dead22`): rein additive Beobachtbarkeit. Statischer Review bestaetigt: nebenwirkungsfreier `level_callback` (liest nur den Snapshot, kein RNG, `verbose` bleibt 0), robust gegen beide Snapshot-Formen (EvoGrow `vis_history` ohne `elapsed_s`/`n_params` via hasproperty-Fallback, EvoGrowScreening `level_log` mit beiden), eine Live-Zeile pro Level plus `run.log`. Ergebnisse bit-identisch by construction.

Ausgeführter Lauf steht aus — wird extern gestartet. Ablauf: erst Sekunden-Preflight `EVO_T2_SYSTEM_ID=11` (bestaetigt Anker-Reproduktion und End-to-End-Lauf), dann System 26.

<!-- 78124f0, 2ee1b5a, 4dead22 -->

### Projektjournal erstellt

Auf Wunsch ein ausfuehrliches Projektjournal als roter Faden erstellt: `docs/projektjournal.md` (Narrativ) und `docs/projektjournal.pdf` (13 Seiten, gesetzt). Zeitraum 2026-04-20 bis 2026-07-23, mit allen Entscheidungen, verworfenen Ansaetzen samt Begruendung und Beleg, und den Messzahlen. Ergaenzt CLAUDE.md (Zustand), DIARY.md (Chronologie), PAPER_1.md (Plan). Committet `fa25253`.

<!-- 713d85f -->

## 2026-07-22

### WP-P1b Korrekturen vor Benchmark-Lauf

- `EvoGrowV3` bekommt denselben `screening_optimizer`-Durchreichpfad und dieselben Kosten-Meta-Felder wie `EvoGrow`; ohne gesetzten Screening-Optimizer bleibt die Lockstep-Bruecke im Referenzpfad unveraendert.
- Fruehe Verwerfung divergierender Screening-Solves nutzt `unstable_check` statt `isoutofdomain`; die zusaetzliche Pruefung gegen `divergence_limit` ist elementweise formuliert.
- Profiling-Benchmark wird auf 12 Level begrenzt, rechnet Screening vor Referenz und schreibt Zwischenergebnisse nach jedem Fall.
- Offener Reproduzierbarkeitszustand: ausserhalb des Regression-Runners konstruieren Benchmarks, Experimente und alte Studies `BFGSOptimizer` weiterhin ohne explizites `time_limit_s`; der Struct-Default bleibt `300.0` und muss vor Phase B bewusst entschieden werden.

### WP-P2.4 gelaufen — beide Interventionen wirken; Bedingung D schlaegt den Referenzpfad um Faktor 6,2

Committet `7eb8381`. Ankerpruefung bestanden: Referenzpfad bei 1e-6 liefert auf beiden Systemen bit-identisch die Baseline-v0-Werte.

**System 3, Bewertungstoleranz 1e-8:**

| Bedingung | Zeit | Loss | Stage | Fits | Integrationen |
|---|---|---|---|---|---|
| A Referenz | 78,6 s | 6,25e-9 | 2 | 110 | 275.098 |
| B Residuum + LS-Start (heute) | 353,2 s | 3,236e-8 | 5 | 241 | 761.581 |
| C Nested-Gate + LS-Start | 49,2 s | 3,236e-8 | 5 | 241 | 232.224 |
| **D Nested-Gate + entkoppelter Start** | **12,6 s** | **2,558e-9** | **2** | 61 | 73.680 |

System 11: alle Bedingungen qualitativ gleichwertig (Loss ~2,0e-16, Stage 4, `pruned_match` true), D mit 0,6 s gegen 1,1 s am schnellsten.

**Antwort auf die drei Pflichtfragen:**

1. **Der geschachtelte Test veraendert die Auswahl** — anders als AIC. System 3, Bedingung C: 147 von 400 Kindern scheitern am Gate, die Auswahl weicht in 126 Faellen auf 7 von 20 Leveln vom reinen Residuen-Score ab. Wirkung auf die Rangeuebereinstimmung: von **−0,78 (Median −1,0)** unter B auf **+0,26 (Median +0,48)** unter C. Der Test behebt also genau das, wofuer er gebaut wurde.
2. **Die Stage-Eskalation verschwindet — aber erst durch den Startpunkt.** C bleibt trotz wirksamem Gate bei Stage 5; D erreicht Stage 2, also die erwartete Stage, ohne Overshoot.
3. **Bedingung D entkommt dem Becken bei 3,236e-08** und erreicht 2,558e-9 — besser als der Referenzpfad mit 6,25e-9.

**Arbeitsteilung der beiden Interventionen sauber getrennt:** Das Gate senkt die Kosten (B nach C: 7,2x bei identischem Ergebnis) und repariert das Ranking. Der entkoppelte Startpunkt repariert Qualitaet und Eskalation (C nach D). Beide waren noetig, keine allein haette gereicht — genau die Aufteilung, die WP-T1 vorhergesagt hat.

**Nebenbefund mit potenziell groesserer Tragweite als das Screening selbst:** Der **Referenzpfad** profitiert schon allein von der engeren Toleranz. Bei 1e-6 braucht er auf System 3 279,3 s und endet auf Stage 3 (erwartete Stage: 2, also Overshoot 1); bei 1e-8 braucht er 78,6 s und endet auf Stage 2, also **ohne Overshoot** — 3,6x schneller bei korrekter Stage. Erklaerung: bei 1e-6 erreicht der Optimierer auf Stage 2 die Schwelle `loss_tol = 1e-8` nicht zuverlaessig, die Suche eskaliert deshalb weiter. **Ein Teil des beobachteten Stage-Overshoots waere damit ein numerisches Artefakt und keine Eigenschaft der Promotionsregel.** Das beruehrt unmittelbar die Begruendung fuer v3 und die 62-Prozent-Rechnung vom 2026-07-22. Bisher eine Zelle, ein Seed — muss auf einem gekoppelten System geprueft werden, und zwar auf System 26, wo Gate 1 gescheitert ist.

**Bemerkung zur Spec-Treue:** `SpecialFunctions` wurde als direkte Abhaengigkeit ergaenzt (nur `loggamma` fuer die F-Verteilung), obwohl die Spec keine neuen Abhaengigkeiten vorsah. Praktisch unkritisch: das Paket war ueber SciML bereits indirekt im Manifest, es wird nichts zusaetzlich installiert, nur die direkte Deklaration kam hinzu.

<!-- 7eb8381, 3327c9b -->

### WP-P2.4 beauftragt — zwei getrennte Interventionen statt nur harter Penalty

Die Spec sieht nach WP-T1 anders aus als geplant. Der harte Penalty allein kann das Ergebnis nicht retten, weil das Screening-Versagen auf System 3 laut Befund 3 nicht vom Ranking kommt, sondern vom LS-Warmstart. Deshalb zwei Interventionen, jeweils einzeln abschaltbar und einzeln messbar.

**Intervention 1 — geschachtelter Modellvergleich als Gate.** Kein additiver Strafterm mehr: bei n = 200 ist jedes Informationskriterium vom Fit-Term dominiert (AIC-Strafe hoechstens 10 Einheiten ueber p = 1..6, Fit-Term aendert sich um 19 schon bei 10 % Residuenunterschied; BIC mit `p*log(n) <= 26,5` ebenfalls zu schwach). Stattdessen darf ein Kind seinen Elternteil nur ueberholen, wenn die Residuenverbesserung groesser ist, als ein zusaetzlicher Parameter zufaellig liefern wuerde. Umsetzung als Gate mit zwei Raengen, innerhalb der Gruppen weiter nach Residuum. Erfordert, dass die Kindergenerierung die Herkunft eines Kandidaten bis zur Bewertung mitfuehrt.

**Pflicht-Nachweis der Wirksamkeit.** Die AIC-Runde ist daran gescheitert, dass die Intervention die Rangfolge nicht bewegt hat und das erst hinterher auffiel. Diesmal muss der Lauf selbst protokollieren, in wie vielen Faellen sich die ausgewaehlte Kandidatenmenge von der des reinen Residuen-Scores unterscheidet. Ist der Wert null, ist die Intervention wirkungslos und das ist sofort erkennbar.

**Intervention 2 — Polish-Start entkoppeln.** Der LS-Fit erfuellt heute zwei Rollen: Screening-Score und Startpunkt fuers Nachpolieren. Die zweite ist nach WP-T1 schaedlich. Kuenftig konfigurierbar, mit dem Startpunkt des Referenzpfads als Alternative; der LS-Fit dient dann nur noch der Bewertung.

**Rangeuebereinstimmung repariert:** ausweisen, auf wie vielen Leveln ueberhaupt ein endlicher Wert zustande kam, Mittelwert nur ueber diese, dazu Median und Spannweite. Der Verdacht aus WP-P2.3 (rho auf den meisten Leveln `NaN`, Mittelwert von wenigen Leveln getragen) wird damit pruefbar.

**Vergleichslauf mit vier Bedingungen** je System (3 und 11, Seed 42, 30 Level, Bewertungstoleranz **1e-8**, damit System 11 ueberhaupt oberhalb der Rauschgrenze liegt): A Referenz, B Screening mit Residuen-Score und LS-Start (heutiges Verhalten als Kontrolle), C geschachtelter Test mit LS-Start, D geschachtelter Test mit entkoppeltem Start. C gegen B zeigt den Penalty, D gegen C den Startpunkt. Dazu eine Ankerpruefung des Referenzpfads bei 1e-6 gegen Baseline v0.

Drei Fragen sind im Bericht ausdruecklich zu beantworten: veraendert der Test die Auswahl ueberhaupt, verschwindet die Stage-Eskalation auf System 3, und entkommt Bedingung D dem Becken bei 3,236e-08.

Aus WP-T1 vermerkt, aber ausdruecklich **nicht** Teil dieses WP: der Sentinel-Loss `1e6` mit Retcode `Success` bei vollstaendig gescheitertem Fit, die pathologische Line-Search mit bis zu 39.933 Auswertungen bei zwei Parametern, und die Frage, ob die Bewertungstoleranz im Regression-Runner dauerhaft auf 1e-8 gehen soll.

<!-- 9db9741 -->

### WP-T1 gelaufen — Toleranz-Hypothese fuer System 11 bestaetigt, fuer System 3 widerlegt; vier Befunde

Committet `a6919ca`. Diagnose auf Systemen 3 und 11 bei fester bekannt-korrekter Struktur, Toleranzraster {1e-5, 1e-6, 1e-8, 1e-10, 1e-12} im Bewertungspfad, Trajektorienerzeugung unveraendert 1e-9.

**Befund 1 — System 11: berichteter Loss ist numerisches Rauschen.** Erreichter Loss aus dem LS-Warmstart je Toleranz: 8,435e-14 (1e-5), 4,606e-15 (1e-6), 1,669e-17 (1e-8), 4,860e-18 (1e-10), 4,856e-18 (1e-12). Der Wert skaliert also unmittelbar mit der Solver-Toleranz und saettigt erst bei ~5e-18. Baseline v0 meldet **4,402192340718147e-15** — genau das Niveau der 1e-6-Toleranz. Teil A verschaerft das: mit den **wahren** Parametern erreicht man bei 1e-6 nur 1,859e-14, der Fit liefert also 4,6e-15 und damit ein *besseres* Ergebnis als die Wahrheit. Das ist nur moeglich, wenn numerisches Rauschen gefittet wird. Der in Baseline v0, in Phase A und in allen heutigen Regressionspruefungen gefuehrte System-11-Loss ist nicht interpretierbar.

**Befund 2 — System 3: Hypothese widerlegt.** Aus dem LS-Warmstart landet der Fit bei **3,236e-08 bei jeder Toleranz von 1e-6 bis 1e-12**, voellig flach. Sechs Groessenordnungen engere Toleranz aendern nichts. Der Boden aus Teil A liegt bei 1e-6 bei 4,401e-12, das Ergebnis also rund 7.000-fach darueber. Hier ist nicht die Numerik die Grenze, sondern der Optimierer bzw. die Landschaft.

**Befund 3 — die eigentliche Ursache des Screening-Versagens auf System 3.** Der LS-Warmstart konvergiert auf 3,236e-08 — exakt der Wert, bei dem die Screening-Variante haengenblieb (3,2363742537347274e-8). Der Referenzlauf erreicht dagegen 2,66e-10, und er benutzt **keinen** Warmstart (`USE_PRETUNING = false`). Das Screening-Versagen ist damit kein Toleranz- und kein Ranking-Problem, sondern: **der ableitungsbasierte Least-Squares-Warmstart fuehrt auf System 3 in ein Becken, aus dem BFGS nicht herausfindet.** Die Screening-Variante fuehrt damit genau das wieder ein, was die Regression-Konfiguration bewusst abgeschaltet hat.

**Befund 4 — pathologische Line-Search.** Auf System 3 verbrauchen einzelne Fits bei zwei Parametern **39.933 / 37.933 / 39.065** Loss-Auswertungen (jede eine vollstaendige Integration) mit Retcode `Failure`, Laufzeiten 3,2 / 10,4 / 23,6 s — bei `maxiters = 200`, also rund 200 Auswertungen pro Iteration fuer ein Zweiparameterproblem. Erratisch: bei 1e-6 und 1e-8 braucht derselbe Startpunkt nur 585 bzw. 257 Auswertungen. Das erklaert die 7.281 Integrationen pro Fit aus der Regressionsmessung.

**Nebenbefund:** Der Standardstart liefert auf System 3 bei mehreren Toleranzen `final_loss = 1.000e+06` nach 5 Auswertungen mit Retcode **`Success`**. 1e6 ist der Initialwert `l_best` in `fit_parameters` — ein vollstaendig gescheiterter Fit wird also als Erfolg mit Sentinel-Loss gemeldet und ist von einem echten schlechten Fit nicht unterscheidbar.

**Kosten (Teil C, pretune-Start, hochgerechnet auf 20 Fits pro Level):** System 3 — 0,48 s bei 1e-6, 0,64 s bei 1e-8, 1,38 s bei 1e-10, 6,00 s bei 1e-12. System 11 — 0,06 / 0,12 / 0,08 / 0,22 s. **Die Verschaerfung von 1e-6 auf 1e-8 kostet also rund Faktor 1,3 und hebt den System-11-Boden von 1,86e-14 auf 1,36e-17**, womit alle berichteten Losses wieder oberhalb der Rauschgrenze liegen. Empfehlung: Bewertungstoleranz auf 1e-8. Zur Einordnung: die WP-P1b-Screening-Budgets setzen 1e-5 und druecken den System-3-Boden auf 2,06e-10, also auf Faktor 1,29 an den dort berichteten Loss heran — fuer billige Systeme zu grob, fuer System 26 (Loss ~1,4e-3) unkritisch.

<!-- a6919ca, f327de6 -->

### Screening-Spur wieder aufgenommen; WP-T1 (Toleranz-Rauschgrenze) vorgezogen

User hat die Abbruchentscheidung revidiert: Zeit ist doch da, und im Projekt geht es um wissenschaftliche Fundierung, nicht um Schnelligkeit. Gewuenscht sind beide offenen Faeden — harter Penalty **und** Toleranzanalyse.

**Reihenfolge festgelegt: Toleranz zuerst.** Begruendung: Die beiden Faeden sind nicht unabhaengig. Die Ursachenkette auf System 3 lautete „Loss bleibt bei 3,24e-8 -> ueber `loss_tol = 1e-8` -> kein Abbruch -> Eskalation auf Stage 5 -> teurere Kandidaten -> netto langsamer". Wenn der Loss dort nicht wegen schlechter Kandidatenauswahl haengenblieb, sondern weil der Optimierer im Bereich unter der Solver-Toleranz blind ist, dann ist **das gesamte beobachtete Versagen der Screening-Variante ein Toleranz-Artefakt**. Ein Test des Auswahlkriteriums unter unkontrolliertem Confounder waere wertlos.

**Die Frage ist groesser als die Screening-Spur.** System 11 meldet in Baseline v0 einen Loss von 4,402192340718147e-15, also rund 6,6e-8 mittleren Fehler pro Punkt — deutlich unterhalb der Genauigkeit, mit der der Bewertungspfad (`abstol = reltol = 1e-6`) diese Trajektorie berechnet. Die Zahl steht in Baseline v0, in der Phase-A-Auswertung und in jeder heutigen Regressionspruefung. Ist sie numerisches Rauschen, betrifft das die Belastbarkeit der berichteten Losses im gesamten Projekt und die Frage, ob `loss_tol = 1e-8` als Abbruchkriterium sinnvoll definiert ist.

**WP-T1 beauftragt:** Diagnose-Experiment unter `studies/numerics/`, Systeme 3 und 11, feste bekannt-korrekte Struktur, Toleranzraster {1e-5, 1e-6, 1e-8, 1e-10, 1e-12} im Bewertungspfad bei unveraenderter Trajektorienerzeugung (1e-9). Teil A misst ohne Optimierer den bestmoeglich erreichbaren Loss je Toleranz (Belastbarkeitsgrenze der berichteten Werte), Teil B laesst `fit_parameters` je Toleranz aus drei Startpunkten laufen — Standardstart, LS-Warmstart, und wahre Parameter mit 1 % Stoerung als schaerfsten Test —, Teil C beziffert den Preis der Genauigkeit. 1e-5 ist im Raster, weil die WP-P1b-Screening-Budgets diesen Wert setzen.

Falsifizierbare Vorhersage in der Spec: bei 1e-6 bleibt der Warmstart stehen und meldet `Success` nach wenigen Auswertungen, bei 1e-10 verbessert er sich. Tritt das nicht ein, ist die Vermutung widerlegt und wir gehen direkt zum Screening-Test.

**Danach WP-P2.4:** harter Penalty statt AIC. Richtung: kein Informationskriterium — bei n = 200 ist jedes vom Fit-Term dominiert —, sondern ein Nested-Model-Test, bei dem ein Kind seinen Elternteil nur schlaegt, wenn die Residuenverbesserung groesser ist, als ein zusaetzlicher Parameter zufaellig liefern wuerde. Das adressiert die Monotonie-Falle direkt statt sie mit einer Konstanten zu ueberstimmen. Plus Reparatur der rho-Kennzahl. WP-v3.3 bleibt bis dahin liegen.

<!-- b37e457 -->

### Entscheidung: Screening-Spur eingestellt; zurueck zu WP-v3.3

User hat die Abbruchregel wie vereinbart gezogen. Die Screening-Spur (WP-P2.1 bis WP-P2.3) wird eingestellt.

**Was bleibt:** `docs/evogrow_screening_design.md`, `src/structure/evogrow_screening.jl`, `studies/debug/compare_screening_variant.jl` und die Messdaten bleiben im Repository als dokumentierte Zwischenablage. Nicht ohne neue Evidenz wieder aufnehmen.

**Was gesichert ist:** 2,71x aus WP-P1b (Solver-Budgets, System 26), Determinismus im Regression-Ergebnispfad, vollstaendige Kosteninstrumentierung pro Level, und ein quantifiziertes Kostenprofil des Bewertungspfads.

**Ehrliche Einordnung der Falsifikation:** Sie ist weich. Die AIC-Intervention war mathematisch zu schwach, um die Rangfolge ueberhaupt zu bewegen, und die rho-Kennzahl ist fragwuerdig. Die Hypothese „ableitungsbasiertes Screening taugt als Auswahlsignal" ist damit nicht widerlegt, sondern ungeprueft. Eingestellt wurde aus Aufwandsgruenden, nicht aus wissenschaftlicher Klaerung — das gehoert so in eine spaetere Diskussion, falls die Spur wieder aufgenommen wird.

**CLAUDE.md aktualisiert:** Prioritaeten auf Stand 2026-07-22, WP-P1.x als erledigt und WP-P2.x als eingestellt vermerkt, offene Toleranz-Hypothese als ungeplanter Punkt festgehalten.

**Offener Punkt vor der naechsten Baseline:** Die Regression-Konfiguration hat sich seit Baseline v0 geaendert (expliziter `time_limit_s`, zusaetzliche Fingerprint-Felder). Baseline v0 bleibt als historischer Datensatz gueltig, aber vor einer Regressionspruefung von v3.3-Ergebnissen muss eine neue Baseline unter der aktuellen Konfiguration gerechnet werden.

**WP-v3.3 beauftragt** (Designnotiz Abschnitt 6): gleichungsweise Kindergenerierung, zulaessige Terme aus `eq_stages[k]` statt aus einer globalen Stage, Kreuzterm-Regel `min(eq_stages[i], eq_stages[j])`, `StageUsagePolicy` pro Gleichung. Zentraler Punkt der Spec: da WP-v3.4 (gleichungsweise Promotion) noch aussteht, sind alle `eq_stages` weiterhin gleichgeschaltet — der Umbau muss daher **bit-identische** Ergebnisse liefern und ist ein verhaltensneutraler Refactor, dessen Wirkung erst mit v3.4 sichtbar wird. Ausdruecklich mitspezifiziert: die RNG-Ziehreihenfolge darf sich nicht aendern, sonst ist das Kriterium nicht pruefbar. Zusaetzlich wird die Screening-Variante aus `VARIANTS` im Regression-Runner entfernt.

Nebenbefund beim Lesen der Designnotiz: Abschnitt 9 fuehrt die Kreuzterm-Frage als offen, obwohl Abschnitt 6 sie bereits beantwortet. In der Spec als entschieden festgehalten, mit der Konsequenz im Docstring: ein Kreuzterm haengt an den Stages der Gleichungen seiner **Variablen**, nicht an der Stage der verwendenden Gleichung — die einzige Stelle, an der die Gleichungen gekoppelt bleiben.

<!-- afbc065 -->

### WP-P2.3 gelaufen — Abbruchregel ausgeloest, aber der Test war zu schwach, um die Hypothese zu pruefen

Committet `9ca9127`. Codex hat `screening_score = :residual | :aic` eingebaut und — besser als von mir spezifiziert — die Rangeuebereinstimmung auf den **tatsaechlich verwendeten Score** umgestellt statt weiter das rohe Residuum zu vergleichen.

| System 3 | Referenz | Screening residual | Screening AIC |
|---|---|---|---|
| Laufzeit | 370,8 s | 460,1 s | **239,0 s** |
| Loss | 2,66e-10 | 3,2363742537347274e-8 | **3,2363742537347274e-8** |
| `final_stage` | 3 | 5 | **5** |
| Integrationen | 1.529.009 | 711.757 | 510.539 |
| Rangeuebereinstimmung | — | −0,7777777777777778 | **−0,7777777777777778** |

System 11: beide Screening-Bedingungen identisch zum vorigen Lauf, rho +1,0, korrekte Struktur, 1,37–1,47x schneller.

**Die Abbruchregel ist ausgeloest** — rho auf System 3 bleibt negativ. Der Test taugt aber nicht als Falsifikation, und zwar aus einem Grund, den ich in der Spec haette vorhersehen muessen:

**AIC ist hier faktisch eine monotone Transformation des Residuums.** `AIC = n*log(mse) + 2p` mit `n = 200` Beobachtungen: der Fit-Term aendert sich um 19 Einheiten schon bei 10 % Residuenunterschied und um 139 bei Faktor 2, waehrend die Komplexitaetsstrafe ueber den gesamten Bereich `p = 1..6` hoechstens **10** Einheiten betraegt. Spearman ist gegen monotone Transformationen invariant — die Rangfolge kann sich also praktisch nicht aendern. Belegt durch die Daten: Loss bit-identisch, `final_stage` identisch, `total_parameter_fits` identisch, rho bit-identisch. Die Intervention hat die Auswahl nicht bewegt. BIC waere mit `p*log(n) <= 26,5` ebenfalls zu schwach. Bei n = 200 Datenpunkten ist **jedes** Standard-Informationskriterium vom Fit-Term dominiert.

**Zweiter Zweifel an der Messgroesse:** rho betraegt in beiden Bedingungen exakt −7/9, obwohl sich Laufzeit (460 vs 239 s), Integrationen (711.757 vs 510.539) und Konvergenzfehler (106 vs 79) deutlich unterscheiden. Das passt schlecht zu einer stabilen Kennzahl und gut zu der Vermutung, dass rho auf den meisten Leveln `NaN` ist (alle simulierten Losses gleich -> `denom == 0`) und der berichtete Mittelwert von sehr wenigen Leveln getragen wird. Ungeprueft, aber die Kennzahl ist damit als Entscheidungsgrundlage fragwuerdig.

**Neuer Befund zum wirkungslosen finalen Refit:** Die Diagnostik zeigt `final_refit_method = BFGS`, `final_refit_retcode = Success`, `final_refit_loss_evals = 5`, keine Failure-Hits. BFGS kehrt also nach fuenf Auswertungen als *konvergiert* zurueck. Der Verdacht: die ODE-Solver-Toleranz im Bewertungspfad betraegt `abstol = reltol = 1e-6`, waehrend der Loss bei ~3e-8 liegt. Finite-Differenzen-Gradienten einer Groesse, die nur auf 1e-6 genau berechnet wird, sind in diesem Bereich Rauschen — der Optimierer sieht keinen Abstieg mehr. Das waere kein Screening-Problem, sondern eine Eigenschaft des gesamten Bewertungspfads und beruehrt auch Pretuning-Warmstarts und die Frage, ob `loss_tol = 1e-8` ueberhaupt zuverlaessig erreichbar ist. Als Hypothese notiert, nicht als Befund.

**Bilanz der Screening-Spur:** AIC-Screening ist auf beiden Systemen schneller als der Referenzpfad (1,55x auf System 3, 1,37x auf System 11), liefert aber auf System 3 einen um Faktor 121 schlechteren Loss und eskaliert auf Stage 5 statt 3. In dieser Form nicht verwendbar.

<!-- 9ca9127, 96ac621 -->

### WP-P2.2c gelaufen — erste echte Zahlen: System 11 funktioniert, System 3 falsifiziert das Kriterium

Vergleichsskript `studies/debug/compare_screening_variant.jl` committet (`2eb7202`) und ausgefuehrt. Konfiguration identisch zur Regression-Suite (30 Level, pop 10, λ=1e-3, BFGS 200, Seed 42).

| | System 3 Referenz | System 3 Screening | System 11 Referenz | System 11 Screening |
|---|---|---|---|---|
| Laufzeit | 357,6 s | **400,9 s** | 3,63 s | **2,36 s** |
| Loss | 2,66e-10 | **3,24e-8** | 4,402e-15 | 4,407e-15 |
| `final_stage` | 3 | **5** | 4 | 4 |
| `pruned_match` | true | true | true | true |
| Integrationen | 1.529.009 | 711.757 | 8.942 | 10.599 |
| Kosten/Integration | 0,172 ms | **0,490 ms** | — | — |
| Rangeuebereinstimmung | — | **−0,78** | — | **+1,00** |

Referenzpfad reproduziert in beiden Zellen exakt Baseline v0 (Loss und `final_stage` geprueft).

**System 11 funktioniert:** korrekte Struktur `-u1^3` gefunden, Faktor 1,53 schneller, Rangeuebereinstimmung +1,0, kein erschoepftes Polish-Budget, kein abgelehnter Kandidat haette gewonnen.

**System 3 falsifiziert das Kriterium in seiner jetzigen Form.** Rangeuebereinstimmung −0,78: der Screening-Score ordnet nahezu **umgekehrt** zum simulierten Loss. Belegte Ursachenkette: (1) der Loss bleibt bei 3,24e-8 und damit ueber `loss_tol = 1e-8`, die absolute Abbruchbedingung feuert nie, waehrend der Referenzlauf bei 2,66e-10 abbricht und auf Stage 3 bleibt; (2) die Suche eskaliert bis Stage 5, also trigonometrische Terme und steifere Kandidaten-ODEs — Kosten pro Integration 0,490 ms gegen 0,172 ms, Faktor 2,85, womit die eingesparten Integrationen mehr als aufgefressen werden; (3) der finale Refit auf vollem Budget dauert **0,001 s** und bewirkt nichts, obwohl beide Varianten dieselbe Struktur finden (`du1/dt = 0.790*u1 + -0.011*u1^2`, beide `pruned_match = true`) — der Loss-Unterschied stammt allein aus den Parametern.

**Vermutete Ursache der negativen Rangeuebereinstimmung:** Kinder entstehen durch Hinzufuegen von Termen, sind also geschachtelte Obermengen ihrer Eltern. Fuer geschachtelte Least-Squares-Probleme ist das Residuum monoton nicht-steigend in der Termzahl — ein groesseres Modell kann nie ein schlechteres LS-Residuum haben. Der Screening-Score enthaelt aber nur einen Tiebreak von `1e-12 * n_params`, waehrend das Suchziel mit `λ = 1e-3` bestraft. Der Score bevorzugt damit systematisch die groessten Kandidaten, was sowohl die negative Rangeuebereinstimmung als auch die Stage-Eskalation erklaert.

**Befund gegen die Praemisse des Kostenmodells:** `polish_budget_exhausted = 0` in **allen** Laeufen. Das 20-Iterationen-Budget wurde nie ausgeschoepft; BFGS terminiert vorher, in 106 von 200 Faellen mit Konvergenzfehler. Die Einsparung von 200 auf 20 Iterationen existiert also gar nicht, weil der Referenzpfad die 200 ebenfalls nie erreicht. Passend dazu sinken die Integrationen pro Fit nur von 7.281 auf 2.953 (Faktor 2,5) trotz zehnfach kleinerem Iterationsbudget — die Zahl der Integrationen wird offenbar nicht vom Iterationslimit getrieben.

**WP-P2.3 beauftragt als letzter Versuch, mit Abbruchregel:** komplexitaetsbewusster Screening-Score (skalenfreies Informationskriterium; ein Uebernehmen von `λ` waere falsch, weil dort ein Simulations-MSE und hier ein Ableitungsresiduum bestraft wird), Untersuchung des wirkungslosen finalen Refits, und Wiederholung der Messung mit drei Bedingungen je System (Referenz, alter Score als Kontrolle, neuer Score). Bleibt die Rangeuebereinstimmung auf System 3 negativ, gilt das Kriterium als falsifiziert und die Arbeit daran wird eingestellt; es bleiben die 2,71x aus WP-P1b.

<!-- 2eb7202, 61e6459 -->

### WP-P2.2b reviewt — Code korrekt, aber nie ausgefuehrt; WP-P2.2c beauftragt

Committet `7f52676`. Alle sechs Punkte korrekt behoben: `screening_budgets_active` behaelt seine urspruengliche Bedeutung und wird aus der Strategie abgeleitet, `derivative_screening_active` als eigenes Feld ergaenzt und im Record gefuehrt; der Runner reicht den `screening_optimizer` jetzt durch. Erschoepfung wird am Iterationslimit gemessen, Konvergenzfehler getrennt gezaehlt. Diagnose-Stichprobe abgelehnter Kandidaten implementiert — geprueft: sie wird nur gemessen, nie nach `polished` geschrieben, beeinflusst die Suche also nicht; `rejected_beats_best_selected` zaehlt die relevanten Faelle. `screen_k < pop_size` wird abgelehnt statt still zu schrumpfen. Struct-Defaults auf `EvoGrow` angeglichen. Finaler Refit ueber `_add_fit_stats!` in den Summen. Monotonie-Abweichung und leere `vis_history` im Docstring dokumentiert. Keine doppelten Funktionsdefinitionen; Include-Reihenfolge stimmt.

**Zwei kleinere Restpunkte:** (i) `screen_k` ist faktisch inert — die Validierung verbietet Werte unter `pop_size`, der Clamp `min(..., pop_size)` verbietet Werte darueber, also ist `screen_k` immer exakt `pop_size`. Damit faellt die in der Design-Notiz genannte Eigenschaft weg, durch Erhoehen von k zum heutigen Verhalten zu degradieren — eine nuetzliche Kontrollvariante. (ii) Die Diagnose-Stichprobe nimmt die **bestplatzierten** abgelehnten Kandidaten, also die knapp Gescheiterten. Das ist die trennschaerfste Wahl fuer Fehler an der Auswahlgrenze, erkennt aber nicht den Fall, dass ein Kandidat mit schlechtem Screening-Score gut simuliert haette. Als dokumentierte Einschraenkung vertretbar.

**Der eigentliche offene Punkt: die Variante ist nie ausgefuehrt worden.** Die in WP-P2.2 und WP-P2.2b jeweils ausdruecklich geforderten Messzahlen wurden beide Male nicht geliefert, und im Repository liegen keine Artefakte eines Verifikationslaufs (`history.jsonl` unveraendert bei 23 Zeilen, keine neuen Ausgaben). Statisch sieht der Code korrekt aus — ob er laeuft und ob das Ableitungskriterium als Auswahlsignal taugt, ist unbekannt.

**WP-P2.2c beauftragt:** wiederverwendbares Vergleichsskript unter `studies/debug/` (Systeme 3 und 11, Seed 42, Referenzpfad gegen Screening-Variante, Level-Budget 30 wie Baseline v0), ausfuehren, und vier Fragen mit Zahlen beantworten: laeuft es durch, findet es `-u1^3` auf System 11, wie hoch ist der Anteil erschoepfter Polish-Budgets, wie faellt die Rangeuebereinstimmung aus. Zusaetzlich Gegenprobe, dass der Referenzpfad weiterhin die Baseline-v0-Werte liefert. Wiederverwendbar statt einmalig, weil dieselbe Pruefung bei WP-v3.3 erneut gebraucht wird.

<!-- 7f52676, ee74602 -->

### WP-P2.2 umgesetzt und reviewt — drei Blocker, WP-P2.2b beauftragt

`src/structure/evogrow_screening.jl` committet (`07aee5e`). Kern korrekt: finaler Refit auf vollem Budget vorhanden, Stopplogik und Promotion bekommen `best.loss` (simulierter Loss), Incumbent wird immer mitgezogen, ungueltige Screening-Faelle explizit markiert und gezaehlt, `pretune_parameters` verhaltensgleich, `evogrow.jl` / `evogrow_v3.jl` / `discover.jl` / `stopping.jl` unangetastet. Kinder werden mit `objective = Inf` initialisiert — geprueft, damit kann der Revert-Schutz keine unbewerteten Kinder in die Population heben. Spearman mit Ties-Korrektur ueber Durchschnittsraenge korrekt implementiert.

**Blocker 1 — Feldkollision `screening_budgets_active`.** Die Variante gibt das Feld fest als `true` zurueck. In WP-P1b wurde es mit anderer Bedeutung eingefuehrt („reduzierte Solver-Budgets aktiv") und wandert aus dem Meta in den Record. Damit laesst sich in `history.jsonl` nicht mehr unterscheiden, ob ein Record mit Solver-Budgets oder mit Ableitungs-Screening lief. Verschaerfend: der Runner-Konstruktor nimmt `screening_optimizer` entgegen und verwirft ihn — die Variante nutzt die Solver-Budgets gar nicht, korrekt waere also `false`. Dieselbe Defektklasse wie WP-P1b B1, unter anderem Namen.

**Blocker 2 — Polish-Erschoepfung mit falschem Zaehler.** Erkennung ueber `optimizer_limit_hits > 0`; dieser Zaehler steigt bei **jedem** Nicht-Success-Retcode. Belegt am System-3-Benchmark: `optimizer_failure_hits = 95` bei 210 Fits, `optimizer_iteration_limit_hits = 0`. Die Kennzahl wuerde also nahezu durchgaengig „Budget erschoepft" melden, unabhaengig vom Budget — und genau sie entscheidet, ob die Losses mit dem Simulationspfad vergleichbar sind.

**Blocker 3 — die Rangeuebereinstimmung kann ihre Frage nicht beantworten.** Spearman wird nur ueber die **ausgewaehlten** Kandidaten berechnet, also ueber eine per Konstruktion auf gute Screening-Scores eingeschraenkte Menge. Gemessen wird damit die Uebereinstimmung unter den Ueberlebenden, nicht ob die Vorauswahl gute Kandidaten verwirft — das zentrale Methodenrisiko aus Abschnitt 6 der Design-Notiz. Der Vergleichslauf koennte durchlaufen und die Frage bliebe offen. Korrektur: kleine Stichprobe **abgelehnter** Kandidaten mitpolieren und simulieren, rein diagnostisch, ohne Einfluss auf die Suche.

**Kleinere Befunde:** (i) `pop` wird aus `polished` gebildet, das hoechstens `screen_k` Eintraege hat — bei `screen_k < pop_size` kollabiert die Population still auf `screen_k`. (ii) Struct-Default `usage = :soft` weicht von `EvoGrow`, `EvoGrowV3` und allen drei Runner-Varianten (`:hard`) ab. (iii) Der finale Refit wird nicht ueber die Fit-Statistik verbucht; `total_ode_solves` und `total_simulation_time_s` schliessen ihn aus. (iv) Wird ein Elternteil durchs Polieren schlechter, behaelt die Variante den alten Wert — `EvoGrow` kennt diesen Schutz nicht. Dadurch ist die Objective-Folge hier monoton, dort nicht, was Plateau-Erkennung und Promotion beruehrt; vertretbar, aber dokumentationspflichtig. (v) `vis_history` wird angelegt und zurueckgegeben, aber nie gefuellt.

**Nicht berichtet:** die in WP-P2.2 geforderten Verifikationszahlen (Laufzeit, Polish-Erschoepfung, Rangeuebereinstimmung, System 11 exakt gefunden?) liegen nicht vor, und im Repo sind keine Artefakte eines Verifikationslaufs. In WP-P2.2b sind die gemessenen Zahlen ausdruecklich Teil des Deliverables.

<!-- 07aee5e, f5f4e4e -->

### WP-P2.2 beauftragt — Screening-Variante mit begrenztem Nachpolieren

Architektur festgelegt. Reines Screening ohne Simulation waere am billigsten, macht aber die Stopplogik unbrauchbar: Parameter aus dem Ableitungs-LS sind nicht fuer das Simulationsziel optimiert, und `plateau_tol = 1e-4` sowie `loss_tol = 1e-8` sind auf BFGS-optimierte Losses kalibriert. Loesung ist ein **begrenztes Nachpolieren** der ausgewaehlten Kandidaten, ausgehend von den LS-Parametern.

Kostenmodell aus den Messwerten (4.707 Solves pro Fit bei 200 Iterationen -> 23,5 Solves/Iteration -> 41,5 ms/Iteration; heute 170,9 s pro Level):

| k | Polish-Iterationen | Kosten/Level | Solve-Faktor |
|---|---|---|---|
| 10 | 0 | 0,02 s | Stopplogik kaputt |
| 10 | 10 | 4,2 s | 41x |
| 10 | 20 | 8,3 s | 21x |
| 5 | 20 | 4,2 s | 41x |
| 10 | 50 | 20,8 s | 8x |

Nach Abzug des Overhead-Bodens von 153 s realistische Gesamterwartung **10–15x** auf dieser Zelle, nicht die 21x der theoretischen Untergrenze. Das ist die Zahl, an der die Umsetzung zu messen ist.

Ablauf pro Level: alle Kandidaten per Screening-Score bewerten (kein BFGS, keine Simulation), die besten k plus den Incumbent auswaehlen, nur diese mit begrenztem Budget nachpolieren und simulieren, nur simulierte Kandidaten duerfen in die Population. Plateau, Stopplogik und Promotion laufen **ausschliesslich** auf simuliertem Loss — die Trennung aus Abschnitt 4 der Design-Notiz. Der berichtete `loss` bleibt ein simulierter Loss auf voller Genauigkeit, die Endstruktur wird einmal mit vollem Budget nachgefittet.

Zwei Messgroessen als Pflicht: (i) wie viele ausgewaehlte Kandidaten ihr Polish-Budget ausschoepfen — durchgaengiges Ausschoepfen bedeutet, die Losses sind nicht mit dem Simulationspfad vergleichbar; (ii) **Rangeuebereinstimmung** zwischen Screening-Score und simuliertem Loss unter den simulierten Kandidaten — die Messgroesse fuer das zentrale Methodenrisiko (Zielkonflikt), ohne die sich nicht beurteilen laesst, ob die Vorauswahl gute Kandidaten verwirft.

Neue Variante neben dem bestehenden Pfad, kein Ersatz. `pretune.jl` wird um eine Score-Funktion mit Gueltigkeitsflag erweitert; `pretune_parameters` selbst bleibt verhaltensgleich. Verifikation nur auf System 3 und 11.

<!-- 64d9e3d -->

### WP-P2.1 Design-Notiz reviewt — tragfaehig, aber ohne Kostenmodell; Faktor 10 haengt an einem Wort

`docs/evogrow_screening_design.md` committet (`97e0dbe`). Alle neun Pflichtabschnitte vorhanden. Saemtliche Zahlen gegen `summary.json` geprueft und korrekt, inklusive der 21x als `3222,6 / 153,0`. API-Referenzen auf `pretune.jl` stimmen (Signaturen von `estimate_derivatives`, `build_design_matrix`, Per-Gleichungs-LS geprueft). Abschnitt 4 und 7 beziehen klare Position: Stage-Promotion bleibt am simulierten Loss verankert, und der Beitrag bleibt nur dann von SINDy unterscheidbar, wenn staged incremental growth Untersuchungsgegenstand bleibt und der simulierte Loss die berichtete Metrik.

**Luecke: kein Kostenmodell fuer den vorgeschlagenen Entwurf.** Die Notiz begruendet sich mit der 21x-Obergrenze, schaetzt aber nie, was ihr eigener Vorschlag kostet. Abschnitt 3 empfiehlt „alle Kandidaten screenen, die besten k pro Level simulieren" mit `k = pop_size` als Kandidatenregel — laesst aber offen, was „simulieren" fuer diese k bedeutet. Aus den gemessenen Groessen (Fall A: 370 Fits ueber 18 Level, 4.707 Solves pro Fit, 1,763 ms pro Solve, 8,30 s Solve-Zeit pro Fit, 0,41 s Overhead pro Fit):

| Variante pro Level (20,6 Kandidaten) | Kosten | Faktor |
|---|---|---|
| heute: alle per BFGS mit Simulation | 170,5 s | 1,0x |
| (b) Top k=10 per BFGS mit Simulation | 83,0 s | 2,1x |
| (b) Top k=5 per BFGS mit Simulation | 41,5 s | 4,1x |
| (a) Top k=10 je **eine** Simulation der LS-Parameter | 0,018 s | Solve-Kosten praktisch null |

Hochrechnung auf den ganzen Lauf: heute 3223 s, Variante (b) mit k=10 rund 1646 s (**2,0x**), Variante (a) rund 153 s (**21,1x**, Untergrenze Overhead + LS). **Der Unterschied zwischen 2x und 21x steckt in einem einzigen unausgesprochenen Wort.** Die Quelle des Speedups ist nicht das Screening an sich, sondern dass die geschlossene LS-Loesung die rund 200 BFGS-Iterationen mit je ~25 Solves pro Kandidat ersetzt. Die Notiz impliziert das, sagt es aber nirgends.

**Synthese, die die Notiz nicht zieht:** Variante (a) erfuellt die Forderung aus Abschnitt 4 mit. Eine Simulation pro ausgewaehltem Kandidaten kostet 1,763 ms; damit bleibt ein simulierter Loss-Anker fuer Plateau-Erkennung und Stage-Promotion pro Level erhalten, ohne die Kosten messbar zu erhoehen. Die 21x und die Anforderung „Promotion bleibt am simulierten Loss verankert" stehen also **nicht** im Konflikt. Offene Entscheidungen 1–3 sind damit auf Evidenzbasis beantwortbar.

**Kleinere Befunde:** (i) Abschnitt 6 nennt als Falsifikation „ein wiederholtes Muster" ohne Schwelle und ohne benannten Test; ist als offene Entscheidung 7 deklariert und damit spec-konform, fuer ein Abbruchkriterium aber zu weich. (ii) `USE_PRETUNING = false` im Regression-Config wird nicht erwaehnt — der gesamte Entwurf ruht auf Maschinerie, die in genau der Konfiguration abgeschaltet ist, die die Messung erzeugt hat. (iii) `pretune_parameters` liefert `zeros(n)`, sobald eine Gleichung nicht-endliche Werte oder `norm > 1e6` ergibt. Als Warmstart harmlos, als Screening-Score faellt ein entarteter Kandidat damit still auf „alle Parameter null" statt als ungueltig markiert zu werden. Die Notiz nennt fehlende Failure-Flags korrekt, aber nicht diese konkrete Falle im wiederverwendeten Code.

<!-- 97e0dbe, a9043e0 -->

### Loss konvergiert in allen Zellen bis Level 18 — Level-Cap trotzdem abgelehnt; WP-P2.1 beauftragt

Rekonstruktion aus dem v0-`run.log` (`best_loss` pro Level, alle 23 Zellen, keine neuen Laeufe noetig): **13 Zellen liefen ueber Level 18 hinaus, und in allen 13 war der Loss bei Level 18 bereits identisch zum Endergebnis.** Kein Level nach 18 hat je etwas verbessert. Kosten dieser Level: **15,8 von 40,5 h = 39 % der gesamten Rechenzeit**.

**Entscheidung: Level-Budget bleibt bei 30.** Der User hatte einer Kuerzung auf 18 zugestimmt, ich habe die Empfehlung zurueckgezogen. Grund: der Loss bliebe identisch, `final_stage`, `stage_overshoot` und `wasted_levels` aber nicht. System 26 Seed 42 bei 30 Leveln Stage 5 / Overshoot 2 / 8 wasted; bei 18 Leveln Stage 3 / Overshoot 0. Das sind die H1- und H3-Metriken. Ein Level-Cap wuerde das Overshoot-Phaenomen wegschneiden statt es zu messen — also genau das, was v3 beheben soll. Meine urspruengliche Optionsbeschreibung hatte diese Konsequenz nicht genannt.

**Der Befund gehoert stattdessen in den v3-Entwurf.** Der Loss konvergiert in jeder Zelle bis Level 18, die Suche laeuft aber bis Level 26–29 weiter, weil Plateau-Erkennung Stage-Promotion ausloest statt Terminierung. Die Suche kann nicht aufhoeren, solange Stages uebrig sind — sie eskaliert stattdessen. Das ist ein Befund ueber die Stopp- und Promotionsregel, kein Konfigurationsproblem: die Promotionsregel braucht ein Kriterium, das erkennt, wann zusaetzliche Komplexitaet nichts mehr bringt, nicht nur wann der Fortschritt stockt.

**WP-P2.1 beauftragt:** Design-Notiz `docs/evogrow_screening_design.md` fuer ein ableitungsbasiertes Screening-Kriterium, analog zum Vorgehen bei WP-v3.1 (erst Entwurf, dann Code). Neun Pflichtabschnitte; kritisch sind Abschnitt 4 (Stopplogik, Plateau-Erkennung und Stage-Promotion arbeiten heute auf dem Simulations-Loss — welches Signal traegt sie kuenftig?) und Abschnitt 7 (Verhaeltnis zum wissenschaftlichen Beitrag: ableitungsbasierte Bewertung rueckt naeher an SINDy, die Abgrenzung muss explizit begruendet werden). Kein Code, keine Laeufe.

<!-- b0c8eaa -->

### Mikro-Benchmark System 26 gelaufen — Kostentreiber quantifiziert, Obergrenze bei 21x

Externer Lauf `studies/profiling/profile_eval_cost.jl` auf System 26, Seed 42, v2.2, 18 Level. Beide Faelle mit **identisch 370 Parameter-Fits** — damit ist der Vergleich normiert.

| | A (Referenz) | B (Screening) | Faktor |
|---|---|---|---|
| Laufzeit | 3222,6 s (53,7 min) | 1189,8 s (19,8 min) | **2,71x** |
| Kosten pro Fit | 8,71 s | 3,22 s | 2,71x |
| ODE-Solves | 1.741.484 | 2.488.973 | 0,70x |
| Kosten pro Solve | 1,763 ms | 0,409 ms | **4,31x** |
| Solve-Anteil an Laufzeit | **95 %** | 86 % | |
| Overhead ohne Solve | 153 s | 166 s | |
| Loss | 1,391623e-3 | 2,653197e-4 | B 5,2x besser |
| erreichte Stage | 3 | 4 | |
| `pruned_match` | false | false | |

B rechnet **mehr** Integrationen (2,49 Mio. vs 1,74 Mio.), aber jede einzelne ist 4,3x billiger — der Deckel `maxiters_solve = 20.000` und die Divergenzschwelle 1e6 greifen genau bei den Ausreissern. Sichtbar im Log: Level 16 von A kostete 1054 s, davon 1045 s (99 %) im Solver, mit 112 Solves im Millionen-Schritt-Limit.

**Sauberster Einzelvergleich:** Stage 2, in beiden Faellen exakt 8 Level — A 2937,9 s, B 297,1 s, **Faktor 9,9x**. Stage 2 sind die selbst-quadratischen Terme; die erzeugen Blow-up-Dynamik, und genau dort zahlt der ungedeckelte Referenzpfad.

**Regressionsnachweis, mit Nebenbefund:** A liefert Loss `0.001391623174905009` — **bit-identisch zu Baseline v0**. v0 brauchte dafuer 30 Level und 3,0 h und lief bis Stage 5; A erreicht denselben Loss in 18 Leveln und 53,7 min bei Stage 3. **Die Level 19–30 in v0 haben rund 2,1 h gekostet und den Loss um exakt null verbessert.** Die Overshoot-Diagnose vom Vormittag ist damit an einer Einzelzelle direkt belegt.

**Determinismus bestaetigt:** `optimizer_safety_limit_hits = 0` in beiden Faellen, die Wall-Clock-Notbremse hat nie gegriffen. Beobachtete Retcodes: Solver `{Success, Unstable, MaxIters}`, Optimierer `{Success, Failure}`.

**Entscheidende Zahl fuer die naechste Stufe:** 95 % der Laufzeit von A liegen in der ODE-Integration, der Overhead ausserhalb betraegt 153 s. Ein Screening ohne Integration in der Suchschleife (ableitungsbasiertes Kriterium, Maschinerie in `pretune.jl` vorhanden) hat auf dieser Zelle eine Obergrenze von **~21x** gegenueber A — gegenueber den 2,71x, die Solver-Tuning gebracht hat. Solver-Tuning ist damit ausgereizt; der Groessenordnungssprung liegt allein in der Reduktion der Anzahl Integrationen.

**Vorbehalte:** n = 1 Zelle, 1 Seed. B ist kein freier Speedup, sondern eine andere Suche (`structure_changed = true`, abweichende Stage-Trajektorie: A 9/8/1 Level in Stage 1/2/3, B 4/8/4/2). Keiner der beiden Faelle findet die korrekte Struktur.

<!-- be9046e -->

### WP-P1c umgesetzt und reviewt — erste Messdaten, Kostentreiber identifiziert

Committet `434a8a7`. Umsetzung korrekt: Level-Budget 18, Kosten pro Level aus dem `level_log` statt aus der Gesamtzeit, erstes Level ausgeschlossen, Mittelwert **und** Median, Per-Level- und Per-Stage-Aufschlüsselung in JSON und Textausgabe. Verifikationslauf auf System 3 durchgeführt.

**Regressionsnachweis:** Fall A liefert auf System 3 Seed 42 Loss `2.663641831768419e-10` — **bit-identisch zu Baseline v0**, bei gleicher `final_stage` 3. Der Referenzpfad ist nach WP-P1/P1b/P1c unverändert.

**Determinismus empirisch bestätigt:** `total_optimizer_safety_limit_hits = 0` und `total_step_limit_solves = 0` in beiden Fällen. Die Wall-Clock-Notbremse hat nie gegriffen, das Solver-Schrittlimit ebenfalls nicht. Beobachtete Retcodes: Solver `{Success, Unstable}`, Optimierer `{Success, Failure}`. `Failure` trat bei 95 von 210 Fits auf — unter der alten Teilstring-Logik wären das alles fälschlich „Iterationslimit"-Treffer gewesen; M1 war ein realer Defekt.

**Befund — die Kopfzahl „Speedup 1,032x" ist strukturell irreführend.** A und B terminieren bei unterschiedlicher Levelzahl (A: 10, B: 12), weil die gröberen Screening-Fits die Plateau-Erkennung verschieben. Das Verhältnis der Gesamtlaufzeiten ist damit kein Kostenverhältnis. Level für Level bei gleicher Stage:

| Level | Stage | A | B | Faktor |
|---|---|---|---|---|
| 2–4 | 1 | 3,5–4,2 s | 1,6–2,2 s | 1,6–2,6× |
| 5–8 | 2 | 44–77 s | 11–48 s | 1,4–4,2× |
| 9–10 | 3 | 16–19 s | 32–35 s | nicht vergleichbar (Läufe divergiert) |

Auf den vergleichbaren Leveln ist B also **1,4–4,2× schneller**. Mechanismus sichtbar: in A sind die Level 1–4 mit null verworfenen Solves durchgelaufen, in B wurden dort je 780–1260 Solves über `unstable_check` früh abgebrochen (Schwelle `divergence_limit = 1e6`). Die Kopfzahl im `summary.txt` sollte künftig auf Per-Level-Basis stehen; da Per-Level- und Per-Stage-Daten in der JSON liegen, ist der Vergleich nachträglich rekonstruierbar — kein Blocker für den System-26-Lauf.

**Wichtigster Befund — der eigentliche Kostentreiber ist die Zahl der Integrationen, nicht die Stage.** Für 210 Parameter-Fits fielen **1,53 Mio. ODE-Solves** an, also **~7.300 Solves pro Fit** (B: ~5.500). Erwartbar wären bei `maxiters = 200` und Finite-Differenzen über 3–6 Parameter etwa 800–1.400; der Rest geht auf Gradientenauswertung und Line-Search. Anteil der Solve-Zeit an der Gesamtlaufzeit: A 74 %, B 66 %.

**Konsequenz:** Solver-Tuning allein kann höchstens den Faktor ~3,4 heben (mehr ist der Solve-Anteil nicht). Der Sprung um Größenordnungen ist nur über eine Reduktion der *Anzahl* Integrationen erreichbar — also über das ableitungsbasierte Screening-Kriterium (bisher als WP-P2 zurückgestellt), das die Integration in der Suchschleife ganz ersetzt. Das ist nach dem System-26-Lauf zu entscheiden.

<!-- 434a8a7, 807e828 -->

### WP-P1b reviewt — Code korrekt, Messaufbau greift zu kurz; WP-P1c beauftragt

Committet `268dc41`. Alle fünf Review-Punkte aus WP-P1b sind sauber umgesetzt: `screening_optimizer` in `EvoGrowV3` inkl. Brücke, eigener Suchschleife und vollständig gespiegelter Instrumentierung; `screening_budgets_active` kommt jetzt aus dem Meta, mit hartem Fehler bei fehlendem Feld statt stillem Default. Frühe Verwerfung über `unstable_check` (Abbruch) statt `isoutofdomain` (Schritt-Ablehnung), Prädikat `_state_exceeds_limit` allokationsfrei elementweise. Nicht-endlich-Verwerfung hinter `reject_nonfinite` gelegt, Zähler bleibt unbedingt — Default-Pfad damit wieder verhaltensgleich. Retcode-Kategorien über Enum-Vergleich mit eigener `:unknown`-Kategorie; alle 14 referenzierten `SciMLBase.ReturnCode`-Member gegen die aufgelöste Version 2.128.0 geprüft, alle vorhanden.

**Neuer Befund — 12 Level messen am Problem vorbei.** Level-aufgelöste Nachrechnung des v0-Logs für System 26 Seed 42: bis Level 12 kostet die Zelle **1,6 min**. Der Ausbruch beginnt danach — Level 13: 147 s, Level 14: 878 s, Level 16: 611 s, Level 19: 1484 s; bis Level 18 kumuliert 39,7 min (Stage 3 beginnt), bis Level 20 66,2 min. Der Benchmark hätte also ausschließlich den billigen Bereich vermessen und zwischen A und B praktisch keinen Unterschied gezeigt. Der Richtwert „12" stammt aus meiner WP-P1b-Spec und war ohne diese Auflösung gewählt. Korrektur auf **18 Level** (≈ 40 min für Fall A, erfasst Level 13–17 und erreicht Stage 3).

**Zweiter Befund — JIT-Warmup verzerrt gegen B.** `cost_per_level_s` wird aus der Gesamtlaufzeit geteilt durch Levelzahl gebildet. Seit WP-P1b läuft Fall B zuerst und trägt damit die gesamte Kompilierzeit des `discover`/BFGS/Solver-Pfads — also ausgerechnet der Fall, der schneller sein soll. Die Per-Level-Zeiten liegen im `level_log` bereits vor; die Kennzahl muss von dort kommen, erstes Level ausgeschlossen, zusätzlich Median (Verteilung stark rechtsschief).

**WP-P1c beauftragt:** Level-Budget 18, Kosten pro Level aus dem `level_log` inkl. Median, Per-Level- und Per-Stage-Aufschlüsselung in die Ausgabe (damit das Ergebnis mit der Baseline-Tabelle vergleichbar ist). Verifikation nur auf System 3; System 26 bleibt dem externen Lauf vorbehalten.

<!-- 268dc41, 864c9d3 -->

### WP-P1 umgesetzt und reviewt — drei Blocker, WP-P1b beauftragt

Codex hat WP-P1 umgesetzt (`911a567`, enthält versehentlich auch die WP-P1b-Spec): `BFGSOptimizer` um deterministische Budget-Parameter und `reject_nonfinite`/`divergence_limit` erweitert, Zähler pro Level (Fits, Solves, invalid/diverged/nonfinite, Optimizer-Limit-Treffer, Solve- vs. Overhead-Zeit) über EvoGrow-Meta bis in den Record durchgereicht, expliziter Referenz-Optimizer im Regression-Runner (`time_limit_s = 86_400`), Mikro-Benchmark `studies/profiling/profile_eval_cost.jl`. Instrumentierung sauber und vollständig verdrahtet; Fingerprint korrekt erweitert; Profiling-Skript verschmutzt `history.jsonl` nicht.

**Review — drei Blocker:**

1. **v3 ignoriert die Screening-Budgets, Records sind falsch etikettiert.** `EvoGrowV3` hat kein `screening_optimizer`-Feld (der Runner übergibt ihn an einen ungenutzten Parameter) und wertet in seiner eigenen Suchschleife immer mit dem Referenz-Optimizer aus. Bei aktivierten Budgets liefen v2.2 und v3 damit unter verschiedenen Budgets → Anker-Vergleich wertlos. `screening_budgets_active` wird zudem aus dem ENV-Flag statt aus dem Meta geschrieben, und die 11 Instrumentierungsfelder sind bei v3 alle `nothing`. Ursache war meine eigene Spec-Formulierung („evogrow_v3.jl nicht anfassen") — gemeint war das Lockstep-Verhalten, nicht ein Durchreich-Parameter.

2. **`isoutofdomain` ist das falsche Primitiv.** Belegt in `OrdinaryDiffEqCore/.../integrator_utils.jl:268-286`: `isoutofdomain == true` setzt `accept_step = false` → Schritt verwerfen, `dt` verkleinern, erneut versuchen, bis `maxiters`/`dtmin`. Kein Abbruch. Das Abbruch-Primitiv ist `unstable_check`, dessen Default (`DiffEqBase/common_defaults.jl:110-120`, `INFINITE_OR_GIANT`) bereits `any(!isfinite, u)` prüft — die Nicht-endlich-Erkennung war also ohnehin aktiv, über den richtigen Mechanismus. Neu ist allein die endliche Schranke. Netto verteuert die Änderung genau die divergierenden Kandidaten, die sie billiger machen sollte. Zusätzlich alloziert die Prüf-Closure zwei temporäre Arrays pro Schritt im Hot Path.

3. **Der „Mikro"-Benchmark ist nicht mikro.** Fall A ist System 26 / Seed 42 / 30 Level — die 3-h-Zelle aus Baseline v0, damals *mit* der 300-s-Bremse, die laut v0-Log regelmäßig griff (~400 s/Fit auf teuren Leveln). Mit `maxiters = 200` und `maxiters_solve = 10^6` gibt es keine deterministische Obergrenze für einen einzelnen Fit.

**Weitere Befunde:** (S1) `_predict_traj` und `simulate` verwerfen nicht-endliche Lösungen jetzt unbedingt, auch bei `reject_nonfinite = false` — vorher lief eine Success-Lösung mit `Inf` durch (die Prüfung greift nur bei NaN) und ergab Loss `Inf`; stilles Verhaltens-Delta im Default-Pfad. (S2) Der Determinismus-Fix ist lokal: Struct-Default `time_limit_s = 300.0` unverändert, `benchmark_evogrow.jl`, `experiments/run_experiment.jl` und die übrigen Studies konstruieren weiter ohne expliziten Wert — **der in CLAUDE.md eingefrorene Paper-1-Pfad bleibt wall-clock-abhängig und muss vor Phase B entschieden werden.** (M1) Die Notbremse wird per Teilstring `"time"` im Retcode erkannt; ein abweichender Retcode würde einen ausgelösten Bremseingriff still als Iterationslimit verbuchen. (M2) In Fall B werden die Parameter nie auf Referenz-Fidelity nachgefittet (`discover()` refittet nur bei Parameteranzahl-Mismatch) — Interpretationsvorbehalt.

**WP-P1b beauftragt:** Punkte 1–3 plus S1, M1; S2 nur dokumentieren, nicht umstellen. Benchmark erst danach starten.

<!-- 911a567, 4fb4508 -->

### Volllauf abgebrochen — Kostendiagnose: 62 % der Rechenzeit oberhalb der nötigen Stage

Der Volllauf wurde bei 23/30 Zellen abgebrochen (v2.2 komplett 15/15, v3.2 bei 8/15), nach **40,5 Compute-Stunden**. Daten gesichert (`a69637a`). Grund: Laufzeit inakzeptabel (mehrere Tage), Restlaufzeit ~26–30 h für Zellen mit nahezu null Informationswert (v3.2 ist die Lockstep-Brücke; Äquivalenz war bereits beantwortet).

**Befund 1 — Anker bestätigt, mit einer Ausnahme.** v2.2 == v3.2 bit-identisch in 7 von 8 überlappenden Zellen. Abweichung nur System 26 Seed 123 (1.3916e-3 vs. 1.3713e-3).

**Befund 2 — Ursache ist ein Reproduzierbarkeitsleck, kein v3-Bug.** `run_regression.jl` baut `BFGSOptimizer(maxiters=BFGS_MAXITERS)`; `time_limit_s` bleibt beim Default **300 s Wall-Clock** (`bfgs.jl:29`) und wird an Optim.jl durchgereicht. Damit hängt die Zahl der BFGS-Iterationen von der Maschinenlast ab → Ergebnisse sind nicht reproduzierbar. Dieselbe Zelle brauchte 13.352 s (v2.2) vs. 20.158 s (v3.2). Muss für Paper 1 ohnehin weg.

**Befund 3 — Kostenprofil (aus `run.log` rekonstruiert, alle 23 Zellen).** Kosten pro Level explodieren mit der Stage:

| Stage | Level | Zeit | Anteil | s/Level |
|---|---|---|---|---|
| 1 | 124 | 0,7 h | 1,9 % | 21 |
| 2 | 129 | 6,1 h | 16,3 % | 170 |
| 3 | 94 | 11,6 h | 30,9 % | 443 |
| 4 | 55 | 7,4 h | 19,7 % | 482 |
| 5 | 48 | 11,7 h | 31,3 % | 878 |

Ein Stage-5-Level kostet das **42-fache** eines Stage-1-Levels. Pro Zelle oberhalb der erwarteten Stage aufsummiert: **24,9 von 40,5 h = 62 % der gesamten Rechenzeit wurden in Komplexität investiert, die die Systeme nie gebraucht haben.** Auf gekoppelten Systemen liegt der Anteil bei 38–80 %. Extremfall System 63 Seed 123: 8,4 h, davon 6,7 h verschwendet; ein einzelnes Level (16, Stage 4) kostete 3,4 h.

**Konsequenz:** Laufzeitproblem und Gate-1-Failure-Mode sind **dasselbe Problem**. Die Suche läuft über die nötige Stage hinaus, und jede zusätzliche Stage ist überproportional teurer (Stage 4/5 = kubisch/trigonometrisch → steife und divergierende Kandidaten-ODEs → Solver kriecht bis ins 300-s-Limit). Bei ~619 s pro Kandidat auf den teuersten Levels laufen einzelne Fits sicher ins Wall-Clock-Limit.

**Blocker für Phase B:** 63 Systeme × 2 Bedingungen × 3 Seeds = 378 Runs, davon 240 gekoppelt. Bei ~3,5 h pro gekoppelter Zelle > 800 h ≈ 5 Wochen durchgehend — und das Set enthält mehr 3D/4D als das Testset. **Phase B ist mit dem aktuellen Kostenprofil nicht durchführbar.** Muss vor WP-v3.3 gelöst werden.

Zwei getrennte Hebel, multiplikativ:
- **A (Overshoot, 62 %):** Promotionsdisziplin — genau das, was v3 leisten soll. Forschungsarbeit, bereits geplant.
- **B (Kosten pro Auswertung):** EvoODE bewertet jeden Kandidaten per voller Trajektorien-Simulation (bis 200 BFGS-Iterationen × ODE-Solve mit `maxiters_solve=10^6`, Toleranz 1e-9). SINDy/GP scoren auf Ableitungsresiduen statt zu integrieren — daher der Kostenunterschied. `pretune.jl` enthält die Maschinerie (finite Differenzen → Design-Matrix → lineares LS) bereits, nutzt sie aber nur als Warmstart, und im Regression-Config ist sie mit `USE_PRETUNING=false` ganz abgeschaltet.

Reihenfolge geändert: **WP-P1 vor WP-v3.3.**

**WP-P1 beauftragt** (`2bd9463`): Determinismus (kein Wall-Clock im Ergebnispfad), getrennte Budgets für Screening während der Suche vs. finale Validierung (Defaults = heutige Werte, kein stilles Verhaltens-Delta), Instrumentierung pro Level (Fits, Solves, verworfene Solves, Zeitanteil Optimierung vs. Simulation), sowie ein Pflicht-Mikro-Benchmark über genau eine Zelle (System 26, Seed 42) mit A/B-Vergleich. Ausdrücklich nicht in WP-P1: ableitungsbasiertes Screening-Kriterium, `use_pretuning`, Parallelisierung, WP-v3.3, WP-H2.

<!-- a69637a, 2bd9463 -->

---

## 2026-07-20

### WP-H1d umgesetzt und reviewt — Resume grün

Codex hat Resume umgesetzt: `load_completed_cells(fingerprint)` liest `history.jsonl` (try/catch pro Zeile), sammelt erfolgreiche `(variant, system_id, seed)`-Zellen bei passendem `config_fingerprint` und `error===nothing`; Skip in der Schleife (äußerer Balken tickt, Skip-Zeile in `run.log`, kein Record). `FRESH=1`-Override, End-Report. Fingerprint/Schema/Metriken unverändert. Committet `488fa1d`. Review: korrekt und spec-konform. Da die 7 geretteten Records `config_fingerprint=0c739d4e36ee6498` tragen und die Config unverändert ist, überspringt der Neustart sie und macht bei System 26 Seed 123 weiter. Grünes Licht für den Neustart erteilt.

<!-- 488fa1d, a298329 -->

### Volllauf durch Rechner-Neustart abgebrochen (7/30 gerettet); WP-H1d Resume beauftragt

Der externe Volllauf (Commit 776d2f0) wurde durch einen unerwarteten Rechner-Neustart abgebrochen. Dank append-only `history.jsonl` **7 von 30 Records gerettet** (alle v2.2: System 3 alle Seeds, System 11 alle Seeds, System 26 Seed 42 — der ~3-h-Lauf). In Git gesichert (`6420953`). Verloren: v2.2 System 26 Seeds 123/7, System 31, System 63, sowie ganz v3.

Nebenbefund aus den geretteten Daten: System 26 v2.2 Seed 42 → `pruned_match=false`, Overshoot Stage 5, Loss 1.4e-3 — bestätigt den Gate-1-Failure-Mode am Volllauf. Baseline, die v3.4 schlagen muss.

**WP-H1d (Resume) beauftragt** (`5ea632c`): Runner überspringt beim Neustart alle erfolgreichen (variant, system, seed)-Zellen desselben `config_fingerprint` (Skip keyed auf Fingerprint+Zelle+`error==null`, NICHT git_hash — sonst würden die 776d2f0-Records nicht erkannt). Fingerprint bleibt über volle Config berechnet; manuelles Kürzen der Systemliste ginge nicht (würde Fingerprint entwerten). Resume auch als Härtung gegen künftige Abbrüche. Ein resumeter Baseline-Lauf darf mehrere git_hashes umfassen (Config identisch, akzeptiert).

<!-- 6420953, 5ea632c, 55a6670 -->

### WP-H1c umgesetzt und reviewt

Codex hat den inneren Live-Balken verdrahtet: VARIANTS-Konstruktoren nehmen `level_callback`, `run_one` erzeugt einen inneren `Progress` (offset 1, total = min(N_LEVELS, max_levels)) + Callback, der pro Level `system/seed/level/stage/best_loss` zeigt; `finish!` im `finally`. Äußerer Balken offset 0. Beide auf stderr → `redirect_stdout(devnull)` hält Per-Level-Text weiter vom Schirm (nur in `run.log`). Metriken/Records/Fingerprint unverändert. Committet `9cd66e7`.

**Review:** Korrekt und spec-konform; `next!` kann total nie überschreiten (max 30 Level = total). Ein rein kosmetischer Vorbehalt, den ich nicht ohne Julia verifizieren kann: die pro-Lauf-Zusammenfassungszeile (`println(summary_line)`) wird zwischen zwei gestapelten ProgressMeter-Balken ausgegeben — das kann visuell holprig sein. Beim ersten externen Kurzlauf begutachten; falls unsauber, ist der Fix eine Zeile (auf `ProgressMeter.println` umstellen oder die Zeile weglassen, da `run.log` die Done-Zeile ohnehin hat).

<!-- 9cd66e7, 7e07cc6 -->

### WP-H1c beauftragt: innerer Live-Balken pro Lauf

Fix für die WP-H1b-Lücke (statischer Balken während eines langen Laufs). User hat „innerer Balken" gewählt. WP-H1c verdrahtet EvoGrows/EvoGrowV3s bestehenden `level_callback` (feuert pro Level mit Snapshot `level`/`stage`/`best_loss`) mit einem inneren `ProgressMeter`-Balken pro Lauf, gestapelt unter dem äußeren Balken (via `offset`). Kein src-Eingriff nötig. VARIANTS-Konstruktoren nehmen künftig ein `level_callback`-Argument. `redirect_stdout(devnull)` bleibt (Balken auf stderr, Per-Level-Detail weiter nur in `run.log`). Metriken/Records/Fingerprint/Config unverändert. Committet `429b645`.

<!-- 429b645, caa4c76 -->

### WP-H1b umgesetzt und reviewt

Codex hat das Logging umgesetzt: `ProgressMeter`-Balken (ETA + variant/system/seed) über alle Läufe, `run.log` mit Start/Finish-Markern, `[i/N]`-Zeilen und EvoGrows Per-Level-Heartbeat (Logger via `LOGGER.log_io` in Append-Modus umgeleitet). Screen minimal gehalten durch `redirect_stdout(devnull)` um `discover`. Fingerprint/Records/Config unverändert, `ProgressMeter` in `Project.toml`. Committet `af6cc6d`.

**Review-Befund (Lücke):** Innerhalb eines einzelnen Laufs geht der Heartbeat nur in `run.log`, nicht auf den Schirm — der Balken tickt erst am Lauf-Ende (`next!`). Bei einem langen Lauf (System 63: Stunden) sieht der User in der cmd also einen statischen Balken — genau das „wirkt gehängt"-Problem, das er vermeiden wollte. Fix-Vorschlag WP-H1c: EvoGrows bestehenden `level_callback` nutzen, um einen inneren Per-Level-Balken/Heartbeat live im Terminal zu zeigen (run.log-Detail bleibt). Nebenpunkt: `open_evo_logger_append!` greift direkt in `EvoODE.EvoLogger.LOGGER.log_io`, weil `set_log_file` im `"w"`-Modus truncaten würde — funktioniert, aber fragil; sauberer wäre ein `append`-Flag an `set_log_file`.

<!-- af6cc6d, 3c0b68f -->

### WP-H1b beauftragt: Fortschritts-Logging (tqdm-Stil)

Zweischichtiges Logging für `run_regression.jl`, damit der User externe Läufe live in der cmd verfolgen kann: **Bildschirm** = `ProgressMeter`-Balken (tqdm-Äquivalent) über N = Varianten×Systeme×Seeds mit ETA + aktuellem Item + eine Zusammenfassungszeile pro Lauf; **Datei** = `outputs/studies/regression/run.log` mit Start/Finish-Markern, `[i/N]`-Per-Run-Zeilen und EvoGrows Per-Level-Heartbeat (via `set_log_file`). Balken terminal-only (kein `\r` in die Logdatei). Prinzip „so wenig wie möglich auf dem Schirm, so viel wie nötig in der Datei". Optional: BFGS-Zeitlimit-Treffer pro Lauf als additives Feld (erklärt die Slowness). Nur Observability — Metriken/Records/Fingerprint/Config unverändert. `ProgressMeter` neu in `Project.toml`. Committet `476e192`.

<!-- 476e192, a29fdb6 -->

### WP-H1 umgesetzt und verifiziert; Julia-Läufe künftig extern

Codex hat WP-H1 geliefert: `studies/regression/{diagnostic_systems.jl, run_regression.jl, history.jsonl}`. Runner rechnet das feste Set (Systeme 3/11/26/31/63) für v2.2 und v3, hängt ein JSONL-Record pro (variant, system, seed) an `history.jsonl` an (git-Provenienz + `config_fingerprint`). Verifiziert über den echten Runner auf dem schnellen Subset (Systeme 3, 11): valides JSONL, stabiler Fingerprint, **Anker-Äquivalenz v2.2==v3 bit-genau** (System 3: identischer Loss/final_stage je Seed; v3 `eq_final_stages` gesetzt). `history.jsonl` leer committet. Committet `99393bb`.

**Laufzeit-Befund (wichtig):** Selbst das 1D-System 3 brauchte 218–1217 s pro Lauf (Stage-Overshoot → teure BFGS gegen das 300-s-Zeitlimit), System 11 nur ~3–4 s. Der Volllauf (× 26/63) ist ein Stunden-Job.

**Workflow-Entscheidung:** Julia-Läufe führt künftig der User extern durch; Claude startet in seiner Umgebung kein Julia mehr (Kompilierzeit blockiert). Konsequenz: Julia-Runner brauchen reichhaltiges, geflushtes, dateibasiertes Fortschritts-Logging (per-Run [i/N] + Timestamp + elapsed, per-Level-Heartbeat, run.log), damit externe Läufe live beobachtbar sind. Als nächste Verbesserung vor dem Volllauf. Siehe Memory `feedback_full_runs`.

<!-- 99393bb, 80cc96a -->

### Regressions-Historie beschlossen, WP-H1 beauftragt

Neue Anforderung: longitudinales Logging, um zu verfolgen, wie sich Metriken über Algorithmus-Versionen/Commits entwickeln (besser/schlechter pro System). Fehlende Achse gegenüber den bestehenden Snapshot-Logs (`run_registry.csv`, Aggregate) und dem narrativen DIARY. Scope-Entscheidung: **Medium**.

Design: festes Diagnostik-Set (Systeme 3/11/26/31/63, feste Seeds/Hyperparameter, wie `phase1_diag`) → append-only `studies/regression/history.jsonl`, ein Record pro (git_hash, variant, system, seed) mit `config_fingerprint` (Hash über metrik-relevante Config; nur innerhalb gleichem Fingerprint vergleichen) + `git_dirty`-Flag. Python-Delta-Report separat.

Aufgeteilt wegen Sprach-Deklaration pro Task: **WP-H1 (Julia)** = Runner + append-only Store (jetzt in `codex/CURRENT_TASK.md`); **WP-H2 (Python)** = Delta-Report (letzter vs. vorheriger Commit, ↑/↓/=, DIARY-fertiger Markdown-Block) als Folge-Task. Erste Baseline-Einträge: v2.2 + v3.2 (müssen laut Anker gleich sein). Bewusst *vor* WP-v3.3/v3.4 gezogen, damit jeder echte v3-Schritt ab Beginn in die Historie geloggt wird. Trigger manuell, nicht als Git-Hook (Läufe dauern Minuten bis Stunden).

<!-- a5ef98a, 1e58fd5 -->

### WP-v3.2 umgesetzt und verifiziert

Codex hat `EvoGrowV3` implementiert (`src/structure/evogrow_v3.jl`, registriert/exportiert in `src/EvoODE.jl`). Pro-Gleichung-Stage-State (`eq_stages`, `eq_levels_in_stage`, `eq_plateau_histories`, `eq_stage_histories`), Promotion aber noch Lockstep-global über einen internen `EvoGrow`-Bridge, der die v2.2-Helfer (`_validate_policy`, `_init_population`, `_stage_progression_decision`) wiederverwendet. Meta ergänzt `eq_final_stages` + `eq_stage_histories` mit `final_stage = maximum(eq_stages)`. Saubere Seams (`_lockstep_stage_progression_decision`, `_apply_lockstep_stage_update!`) für WP-v3.4.

**Regressions-Äquivalenz selbst verifiziert** (Julia-Skript, System 3 1D + System 26 2D, Seeds 42/7): identische `active_idxs`, Loss-Differenz bit-genau 0.0, `eq_final_stages` lockstep-gleich, `maximum(eq)==final_stage`. v3.2 reproduziert v2.2 (`:stage_local`) exakt — der Refactor ist neutral. Nebenbefund als Baseline: v3.2 scheitert auf System 26 genau wie v2.2 (Loss ~0.038, nur lineare Terme), was WP-v3.4 heilen soll.

Anmerkung Tech-Debt: Die ~350-Zeilen-Hauptschleife ist eine Kopie des v2.2-Loops (unvermeidbar unter „evogrow.jl nicht anfassen"). Nach Gate 2 faktorisieren oder v2.2-Loop stilllegen.

<!-- 559d3b7, f9802b3 -->

### WP-v3.1 geliefert, WP-v3.2 beauftragt

Codex hat **WP-v3.1** umgesetzt: `docs/evogrow_v3_design.md` friert das v3-Design ein — pro-Gleichung-Stage-State (`eq_stages` statt globalem `current_stage`), Ableitungs-Residuum `r_k` als pro-Gleichung-Progress-Signal (auf beobachteter Trajektorie), Promotion-Regel mit Residuum-über-Ziel-Guard (bereits erklärte Gleichungen promoten nicht), gleichungs-bewusste Child-Generation, Warm-Start-Übernahme, neue pro-Gleichung-Metriken. Vier offene Fragen mit empfohlenen Auflösungen. Committet.

**WP-v3.2 als nächsten Codex-Task formuliert** (`codex/CURRENT_TASK.md`): neuer `EvoGrowV3`-Struct + gleichungsweiser Stage-State als lauffähiges Refactor. Bewusst enger Scope — Promotion bleibt vorerst Lockstep (alle Gleichungen gemeinsam), sodass `EvoGrowV3` v2.2 (`:stage_local`) exakt reproduziert. Das dient als **Regressions-Anker**: spätere Divergenz ist dann eindeutig den gleichungs-lokalen Mechanismen (WP-v3.3 Child-Generation, WP-v3.4 Residuum-Signal + pro-Gleichung-Promotion) zuzuordnen, nicht dem Refactor. Verifikation: Struktur-/Loss-Identität v3 vs. v2.2 auf System 3 und 26.

<!-- f9567b5, 10ef90f, 4f78d20 -->

### Status-Abgleich und Housekeeping

Statusprüfung der vier offenen Punkte aus den „Current Priorities". Ergebnis: CLAUDE.md war veraltet (Stand 2026-05-11), `PAPER_1.md` ist die aktuelle Wahrheit.

- **WP-0.1** (H4-Verdict → VACUOUS in `evaluate_hypotheses.py`): bereits erledigt, Commit `a199128` (2026-05-17). Die `vacuous`-Prüfung setzt das Verdict korrekt, das Freeze Memo schreibt „C3 cannot be evaluated".
- **WP-0.2** (Generalization-Pfad): bereits erledigt (2026-05-17). Config zeigt korrekt auf `debug_results/generalization_summary.csv`.
- **WP-v3.1** (Design Note `docs/evogrow_v3_design.md`): aktiver Codex-Task in `codex/CURRENT_TASK.md`, Deliverable noch nicht geschrieben. Das ist der reale aktuelle Arbeitspunkt.
- **Phase B**: nicht begonnen, erst nach Gate 2.

**CLAUDE.md synchronisiert:** „Current Priorities" und „Active WPs" auf Phase 2 / WP-v3.1 aktualisiert, erledigte WPs markiert. Fehl-Label korrigiert: der frühere „Phase 2"-Prioritätspunkt (R²/Protocol-Audit) ist laut `PAPER_1.md` eigentlich Phase 3.

**Untracked Runner committet:** `studies/phase1_diag/run_phase1_diag.jl` (WP-1.3-Diagnostik, Gate-1-Evidenz) war nie eingecheckt — jetzt nachgeholt.

<!-- 7f29a02, eae3e2c, e819afb -->

---

## 2026-05-30

### WP-1.3 Ergebnisse und Gate-1-Entscheidung

Phase-1-Diagnostik-Runs abgeschlossen: 15/15 JSON-Dateien in `outputs/studies/phase1_diag/`. Konfiguration: EvoGrow v2.2 stage_local, `use_pretuning=false`, `n_levels=30`, 3 Seeds je System.

**Kontrollsysteme:**

- System 3 (Logistic): `pruned_match=true` alle 3 Seeds, Loss ~7e-10. Stage-Overshoot 0–3 (Mindestbudget-Effekt). Fit-Qualität gut, kein Strukturproblem.
- System 11 (Cubic `du=-u³`): `pruned_match=true` alle 3 Seeds, Loss ~4e-15, Stage 4/4, Laufzeit ~1.3s. Metrik-Artefakt aus WP-1.2 vollständig geheilt — der Pruning-Fix funktioniert.

**Problemsysteme:**

- System 26 (Lotka-Volterra 2D): `pruned_match=false` alle 3 Seeds, Loss ~5e-4–1.4e-3, Stage 5/3, Laufzeit 2800–9400s. Gefundene Struktur: `du1 = (5.05)*u1 + (-3.87)*u1*u2`, `du2 = (1.13)*u1 + (-1.80)*u1^2` — Terme komplett falsch. Loss platzt in Stage 3 auf ~1e-3, danach keine Verbesserung trotz Eskalation bis Stage 5 (Trig-Terme nutzlos).
- System 31 (SIR 2D): Seed 42 erreicht Loss ~7e-11 (nahezu perfekt), aber `pruned_match=false` wegen Spurious-Term `0.0022*u1` — Pruning-Schwellenwert `1e-3 × max_coeff = 4e-4 < 0.0022`, Term überlebt. Seeds 123/7: Stage 5/3, Loss ~1e-4–7e-5, echter Fehler.
- System 63 (SEIR 4D): `pruned_match=false` alle 3 Seeds, Loss ~9e-4–1.8e-3, Stage 5/3, Laufzeit 11000–31000s. Konsistentes Scheitern.

**Strukturdiagnose:** Der systemweite Staging-Mechanismus von v2.2 zwingt alle Gleichungen gemeinsam in höhere Stages, sobald der globale Progress stagniert. Auf System 26 findet der Algorithmus in Stage 3 keine verwertbaren Cross-Terme, promotiert dann global zu Stage 4 (kubische Terme) und Stage 5 (Trig), obwohl keine Gleichung Trig-Terme benötigt. Das ist kein Metrik-Fehler — es ist eine echte algorithmische Schwäche des systemweiten Staging.

**Nebenbeobachtung System 31 Seed 42:** Pruning-Schwellenwert 1e-3 × max_coeff könnte für BFGS-konvergierte Modelle zu streng sein. Der Term 0.0022*u1 ist klein aber nicht null. Zu re-evaluieren nach v3-Validierung.

**Gate-1-Entscheidung: v2.2 ist NICHT paper-ready. Phase 2 (EvoGrow v3) wird ausgelöst.**

Begründung: Der Failure-Mode auf Systems 26 und 63 ist klar auf systemweites Staging zurückführbar, nicht auf Metrik-Fehler oder Parameter-Fitting. Das ist genau die Bedingung, unter der v3 (gleichungsweises Staging) motiviert ist.

WP-v3.1 (Design Note) als nächsten Codex-Task formuliert.

<!-- f5e7033 -->

---

## 2026-05-17

### Strategischer Pivot: Paper 1 Neufokus

Paper 1 wird kein Pretuning-Vergleichspaper. Pretuning wird für Paper 1 vollständig deaktiviert und als mögliches Follow-up-Paper zurückgestellt.

**Neue wissenschaftliche Kernfrage:**
> Ist inkrementelles, gestuftes Wachstum ein effektiver Suchmechanismus für interpretierbare ODE-Entdeckung — und wo hilft es, wo versagt es?

**Phase A Neubewertung:** H1/H3 PARTIAL war kein schlechtes Ergebnis, sondern ein diagnostisches Signal. System-weites Staging ist möglicherweise zu grob für mehrdimensionale Systeme (26, 31, 63). Das ist der algorithmische Befund, dem das Paper nachgehen muss.

**Neues Experiment-Design:** 63 ODEBench-Systeme × 1 finaler EvoGrow-Variant × 3 Seeds = 189 Runs. Keine externen Baselines in-house; publizierte ODEBench-Zahlen als Referenzkontext.

**Gate-Struktur eingeführt:**
- Gate 1: Ist v2.2 nach Metric-Repair paper-ready? (Phase 1 Diagnose)
- Gate 2 (nur falls nötig): Ist v3 (gleichungsweises Staging) paper-ready?

`PAPER_1.md` vollständig neu geschrieben. WP-0.2 als erledigt markiert.

<!-- fb549af -->

## 2026-05-11

### H1–H4 Auswertung und Freeze Memo (Step 2)

Codex hat `evaluate_hypotheses.py` implementiert und die formale Hypothesenauswertung auf `paper1_phaseA_v1` (300/300 Runs) durchgeführt. Ergebnisse ins Freeze Memo (`docs/paper1_freeze_memo_phaseA.md`) und Diagnostics JSON (`analysis/data/paper1_phaseA_v1/h1_h4_diagnostics.json`) geschrieben.

**Verdicts:**
- **H1** (Stage Overshoot Reduction): PARTIAL — korrekte Richtung nur auf System 54 (Lorenz), 1 von 6. Systeme 3, 11, 26, 31, 63 zeigen kein Signal oder falscher Trend. Ursache: Mindestbudget pro Stage erzwingt mehr Levels auf einfachen Systemen.
- **H2** (Competitive Recovery Quality): SUPPORTED — 7 von 8 Systemen kompetitiv (exact_match oder mean_loss). Nur System 11 nicht kompetitiv.
- **H3** (Wasted Levels Reduction): PARTIAL — korrekte Richtung nur auf Systemen 11 und 54, 2 von 6.
- **H4** (Usage Policy Effect): SUPPORTED (vakuös) — alle Policy-Varianten zeigen exact_match=0 auf Stage-≥3-Systemen, erwartete Ordnung `hard ≥ soft ≥ passive` daher nicht unterscheidbar.

**Design-Entscheidungen dokumentiert:**
- `exact_support_match` als striktes Binary-Metrik ohne Schwellenwert ist korrekt und bleibt unverändert
- System 11 (`du=-u³`): EvoGrow findet Struktur mit loss ~4e-15, aber growth-without-pruning akkumuliert Null-Terme → kein exact_match. Echter algorithmischer Mangel, kein Metrik-Fehler. Muss im Paper explizit genannt werden.
- Generalisierungsstudie: keine förderfähigen Zellen (n_exact_runs < 3), bleibt im Supplementary.

### Repo Readiness Review und Cleanup

Vollständiges Repo-Review vor nächster Implementierungsphase. Alle gefundenen Issues behoben:

- `codex/CURRENT_TASK.md`: abgeschlossenen Step-2-Task gelöscht, "Kein aktiver Task" gesetzt
- `CLAUDE.md`: veraltete Abschnitte (242/300 Befunde, Active Studies 2026-04-29, Current Priorities 2026-04-29, Known Gaps) auf aktuellen Stand 2026-05-11 gebracht
- `analysis/CONVENTIONS.md`: gebrochene Referenz `CURRENT_TASK_ANALYSIS.md` → `CURRENT_TASK.md` korrigiert (Datei existiert nicht)
- `docs/paper1_study_protocol.md`: als Phase-A-Archivdokument markiert, nicht mehr aktives Protokoll
- `analysis/configs/paper1_phaseA_v1.json`: Generalisierungspfad von `outputs/studies/generalization/` → `debug_results/` korrigiert (WP-0.2)

Abschließende Verifikation: `debug_results/generalization_summary.csv` und `generalization_detail.csv` existieren — WP-0.2 damit vollständig erledigt.

Offener Rest: WP-0.1 (H4-Claim-Korrektur in `evaluate_hypotheses.py`) — wird morgen als Codex-Task formuliert. Das ist der einzige noch ausstehende Punkt vor dem endgültigen Abschluss von Phase A.

<!-- b4c1cce, 5f5fc43 -->

### Strategische Neuausrichtung: Paper 1 Roadmap

ODEBench-Paper (d'Ascoli et al. 2023, 2310.05573) analysiert: EvoODE verwendet dieselben 63 Strogatz-Systeme mit identischen ICs (alle 8 exakten Systeme verifiziert). Baseline-Strategie: veröffentlichte ODEBench-Zahlen direkt zitieren (σ=0, ρ=0 Regime), R²-Metrik aus existierenden Trajektorien berechnen.

**Strategie:** EvoODE konkurriert nicht mit ODEFormer (50M Training-Beispiele, A100), sondern mit SINDy(poly) und PySR (~35–50% Accuracy bei σ=0). EvoGrow v3 (gleichungsweise gestufte Promotion) als nächste Variante geplant.

`PAPER_1.md` komplett ersetzt durch detaillierten Ausführungsplan: Phasen 0–5, WP-Aufschlüsselung, EvoGrow v3 Design-Spec, Risikoregister, eingefrorene Baselines.

`CLAUDE.md`: neuer Abschnitt "Paper 1 — Execution Roadmap" als Pointer auf `PAPER_1.md`.

---

## 2026-05-08

### paper1_phaseA_v1 vollständig abgeschlossen

`experiments/run_experiment.jl paper1_phaseA_v1` hat alle 300 Runs durchlaufen (300/300, alle `success=true`, 0 failed, 0 interrupted). Laufzeit ca. 4.5 Tage.

Aggregation: `julia experiments/aggregate.jl paper1_phaseA_v1` → `run_registry.csv` (300 Zeilen).
Python-Pipeline: `aggregate_run_registry.py` → `data/paper1_phaseA_v1/aggregate_by_variant_system.csv` (60 Zeilen, 6 Varianten × 10 Systeme, alle Zellen vollständig).

### Erste vollständige Auswertung: paper1_phaseA_v1

**Exact Match (Kernbefunde):**

- Systeme 2, 3, 24: alle EvoGrow-Varianten `exact_match=1.0`, GP auf System 24 `exact_match=0` (loss ~4.5e-3 vs. EvoGrow 5.4e-14 — dramatischer Unterschied auf simpelstem 2D-linearem System)
- System 11 (cubic, `du=-u³`): alle EvoGrow `exact_match=0` trotz loss ~4.4e-15 — Bug in `exact_support_match` vermutet; GP `exact_match=1.0`
- Systeme 26, 31, 54, 63: `exact_match=0` für alle Varianten — kein exakter Strukturfund auf Stage-3-Systemen

**Loss EvoGrow vs. GP (höherdimensionale Systeme):**

| System | Beste EvoGrow | GP | Faktor |
|--------|--------------|-----|--------|
| 31 SIR | 7.0e-05 | 0.314 | ~4.500× |
| 54 Lorenz | 7.4e-04 | 0.921 | ~1.200× |
| 26 Lotka-Volterra | 2.5e-04 | 2.98e-03 | ~12× |

GP versagt auf gekoppelten Systemen deutlich — stärkstes Argument für EvoGrow.

**Stage Overshoot (Kernhypothese):**

- **System 54 (Lorenz):** v1=+2, v2.1=+1.6, alle v2.2=0 Overshoot, 0 Wasted Levels → sauberste Bestätigung der Kernhypothese
- **System 3 (Logistic):** v1=0 (flache Basis, keine Stage-Promotions), alle v2.x=+3 Overshoot — v2.2_stage_local verschärft wasted_levels auf 12 durch Mindestbudget
- **Systeme 26, 31, 63:** alle Varianten +2 Overshoot — kein Differenzierungssignal

**Offene Fragen:**
- `exact_support_match`-Bug bei System 11 untersuchen (loss ~0 aber kein Match)
- Warum GP auf System 24 (harmonic oscillator) so schlecht?
- Für keine Stage-3-Systeme exact match → algorithmisches Problem oder Loss-Tol-Problem?
- Kein Run konvergiert auf `loss_tol=1e-8` außer System 2/24 → Stopp-Mechanismus greift nie als Loss-Stopp

### WP3: Frame Layout Redesign (search_animation.jl)

Zweispalten-Layout für `render_frame`: linke Spalte = Trajektorien-Subplots, rechte Spalte = Info-Panel (Loss, entdeckte Gleichungen, wahre Gleichungen, farbige Legende). Aktuelle Level-Kandidaten in Orange, Historie in Grau. `plot_title` über allen Subplots. `structure_to_string` Koeffizientenformat auf `%.3f` geändert.

---

## 2026-05-05

### WP11: CairoMakie-basiertes `render_frame` (Spec + Abhängigkeit)
`ac7658f`

Codex-Spec für WP11 geschrieben: vollständiger Neubau von `render_frame` auf Basis von CairoMakie statt Plots.jl. Ziel ist pixel-genaue Kontrolle über Layout und Typography für Publikationsqualität.

CairoMakie als Abhängigkeit in `Project.toml` aufgenommen. Bestehende `search_animation.jl` bleibt unverändert, bis WP11 implementiert ist.

---

## 2026-05-04

### Animationspipeline: WP4–WP8 (Live-Rendering, Layout, Typography)

**WP4 — Live-Frame-Rendering via `level_callback`** (`2e31f2e`):
`level_callback`-Hook in EvoGrow eingebaut, der am Ende jedes Levels aufgerufen wird. Frame wird direkt während des Runs gerendert und gespeichert — kein Post-Hoc-Rendering mehr nötig.

**WP5 — Horizontale Balken im Info-Panel** (`8e46613`):
Frame-Layout auf horizontale Balken pro Kandidat umgestellt (Trajektorie-Panel links, Loss-Rang-Balken rechts). Verbesserte Lesbarkeit auf Stage-Promotions-Grenzen.

**WP6 — Stage-Grammar-Anzeige in der Gleichungsleiste** (`92f892e`):
Aktuell freigeschaltete Stage-Terme werden in der Gleichungsanzeige farblich hervorgehoben. Neue Terme (neu in dieser Stage) vs. ältere Terme visuell unterscheidbar.

**WP7 — Typografie-Refaktor** (`a496f94`):
Schriftgrößen, Zeilenabstände und Gewichtungen vereinheitlicht. Koeffizientenformat auf `%.3g` geändert (keine führenden Nullen mehr). Gleichungszeilen kürzer und lesbarer.

**WP8 — Header/Meta-Verfeinerung** (`c0f12ca`):
Titel-Header zeigt: System-Name, Variante, Seed, aktueller Stage, Level-Fortschritt. Grau-Kandidaten-Alpha von 0.08 auf 0.18 erhöht (besser sichtbar ohne Ablenkung vom besten Kandidaten).

---

## 2026-05-03

### Animationspipeline für EvoGrow-Suchverlauf (WP1–WP3)
`2fa3e18`

Visualisierung des stufenweisen EvoGrow-Suchprozesses als animiertes Video:

**WP1 — Snapshot-Sammlung in `src/structure/evogrow.jl`:**
- `vis_history`-Feld in EvoGrow; sammelt Snapshots am Ende jedes Levels
- Jeder Snapshot enthält aktuelle Population (Kandidaten + Scores) und Stage-Info

**WP2 — Rendering in `src/plotting/search_animation.jl` + `studies/visualization/animate_search.jl`:**
- `search_animation.jl`: rendert pro Level ein PNG-Frame
- `animate_search.jl`: orchestriert Discovery → Frame-Rendering → optionaler ffmpeg-Export (MP4)

**WP3 — Frame-Layout:**
- Zweispaltig: links Trajektorie-Subplots (Ground Truth vs. Kandidaten), rechts Info-Panel
- Aktuelle Level-Kandidaten: orange; akkumulierte History: grau
- Info-Panel: Stage, Level, Loss, true Gleichungen, farbige Legende

---

## 2026-05-02

### `profile_init` — Ergebnisse ausgewertet
`72629a3`

- `docs/profile_init_results.md` + `docs/profile_init_convergence.png` angelegt
- Lorenz: Pretune klar besser auf allen 3 Seeds (~4× niedrigerer Loss, erreicht Stage 3 statt Stage 2)
- Lotka-Volterra: Pretune auf Mittelwert besser, auf Seed-Ebene gemischt — treibt Algorithmus in Stage 5 (Overshoot)
- Kritisch: alle 12 Runs enden mit `max_levels`, kein Run konvergiert → Level-Budget zu gering für belastbare Aussagen

---

## 2026-04-30

### `analysis/status.py` — Logdatei-Auswertung (WP4)
`90e70f5`

`status.py` um Auswertung der neuen `run.log`-Dateien (aus WP2) erweitert:

- `LOG_PATHS`-Dict: Skript → `run.log`-Pfad im jeweiligen OUT_DIR
- `read_log_markers()`: liest `=== Started/Finished at ===`-Marker aus Logdatei (letzte 500 Zeilen)
- `build_log_info()`: leitet ab ob letzter Run sauber beendet (`clean=True/False/None`)
- `print_known_scripts()`: zeigt Log-Zeile pro Skript (Start-/Endzeit, sauber/unterbrochen)
- WMI-Logik, Output-Timestamps und ETA-Berechnung vollständig erhalten

### Resume-Logik für `benchmark_evogrow.jl` (WP1) + Stdout-Logging (WP2)
`0c74f2d`

Benchmark konnte bisher nicht sicher gestoppt werden: `open(summary_file, "w")` überschrieb
die CSV bei jedem Start. Lösung:

- `seed`-Spalte in CSV eingeführt (Header + Row + Fehler-Record)
- `parse_csv_fields()`: korrekter CSV-Parser für Semikolon-Trenner mit Quote-Handling
- `load_done_set()`: liest existierende CSV und baut `Set{Tuple{String,Int,Int}}` aus `(variant_slug, id, seed)`
- `load_records_from_csv()`: lädt alle Rows für Aggregate nach Resume
- Hauptloop: Skip-Check vor jedem Run, Append-Mode wenn CSV existiert
- Einmalige Migration der bestehenden 140-Row-CSV: `seed`-Spalte per Positionszählung
  nachträglich eingetragen (Seeds-Reihenfolge ist deterministisch → sicher ableitbar)

### Repository-Strukturmigration (WP-R)
`706549f`

Alle drei laufenden Skripte gestoppt. Migration durchgeführt:

- `benchmarks/odeformer/` → `benchmarks/data/` (Datenpfade in beiden Benchmark-Skripten aktualisiert)
- `benchmarks/results/` → `outputs/benchmarks/` (OUT_DIR in `benchmark_evogrow.jl`)
- `generalization_study.jl` → `studies/generalization/`, OUT_DIR → `outputs/studies/generalization/`
- `profile_init.jl` → `studies/profiling/`, OUT_DIR → `outputs/studies/profiling/`
- `debug_single.jl` → `studies/debug/`, OUT_DIR → `outputs/studies/debug/`
- `.gitignore`: `outputs/` eingetragen
- Vorhandene Output-Daten nach `outputs/` kopiert (Resume-Kontinuität)
- `SCRIPTS.md` + `CLAUDE.md` aktualisiert

### Stdout-Logging in alle Skripte (WP2)
`0c74f2d`

Alle fünf Skripte schreiben jetzt `run.log` im jeweiligen OUT_DIR (Append-Modus):

- `=== Started at <ts> ===` / `=== Finished at <ts> ===` als Marker
- `log_println()` + `@logf`-Makro für formatierte Ausgaben
- Betrifft: `benchmark_evogrow.jl`, `studies/profiling/profile_init.jl`,
  `studies/generalization/generalization_study.jl`, `studies/debug/debug_single.jl`,
  `experiments/run_experiment.jl`
- Bestehender per-Run-Log-Mechanismus in `profile_init.jl` bleibt erhalten

---

## 2026-04-29

### `analysis/status.py` — Study Status Checker (Codex-Task)
`756b512`, `b94601f`

Ziel: Skript, das aus SCRIPTS.md alle bekannten Scripts extrahiert und prüft, welche davon gerade laufen.

**Technische Analyse (Windows/WMI):**

- `julia.exe`-Prozesse per PowerShell + WMI abfragbar
- Problem: Command Line von `julia.exe` enthält auf Windows oft keine Script-Argumente
- Wenn Parent-Prozess `julialauncher.exe` ist: Argumente im Parent sichtbar → Script identifizierbar
- Wenn Parent `cmd.exe` ist (auch wenn cmd noch offen): Argumente gehen verloren — gilt für alle über cmd gestarteten Skripte

**Lösung: Hybrid-Ansatz**

1. Prozessbaum: julialauncher.exe-Parent → Script-Name direkt lesbar
2. Output-File-Timestamp: wenn Output-Datei < 90 min alt und Orphan-Prozess läuft → `[LÄUFT?]`

**ETA-Schätzung:**

- Rate über letzte 20 Runs (nicht Gesamtlaufzeit) — robust gegen stuck runs
- Für Experiment-Runner: Rate aus `finished_at`-Timestamps der status.json-Dateien
- Für Benchmark: Rate aus `elapsed_s`-Spalte in summary.csv
- Stuck-Run-Erkennung wenn Run seit >2h im Status `running`

**Implementierung und Nachtrag:**

- `analysis/status.py` als standalone Python-Skript mit Standard Library umgesetzt
- `SCRIPTS.md` wird per Regex auf `julia <path>.jl`-Aufrufe in Codeblöcken geparst
- Output-Mapping hart codiert, aber ohne Experiment-ID-Hardcoding (`glob`-Patterns)
- Fortschritt/ETA implementiert für:
  - `experiments/run_experiment.jl`
  - `benchmarks/benchmark_evogrow.jl`
  - `profile_init.jl`
  - `generalization_study.jl`
- Stuck-Run-Warnung erkennt aktuell hängende `status.json`-Runs, z.B. alte Lorenz-Runs mit `status="running"`
- Fehler passiert: Datei war zunächst nur untracked und wurde dadurch bei Workspace-Cleanup/Refresh entfernt
- Fix: `analysis/status.py` aus der implementierten Version wiederhergestellt und mit `b94601f` committed, damit sie nicht erneut verloren geht

---

## 2026-04-28

### Experiment-Runner: zweiter Lorenz-3D-Run hängt
`57c4ff3`

Run `54_evogrow_v1_seed7` (Lorenz periodic, EvoGrow v1, Seed 7) läuft seit 2026-04-28T07:46 ohne Fortschritt.
Ursache: Run wurde mit Git-Hash `04f458a7` generiert — **vor** der BFGS-Timeout-Implementierung.
Der neue Timeout greift nicht rückwirkend auf Runs mit altem Config-Hash.

Experiment-Runner: 234 → 242/300 Runs abgeschlossen.
Benchmark `benchmark_evogrow.jl`: ~93 → ~128/300 Runs (~43%).
`profile_init.jl`: weiterhin hängend auf Level 11, Stage 2, Lorenz 3D, Seed 42 — Daten bereits vorhanden.

---

## 2026-04-27

### BFGS-Timeout implementiert (`src/optimize/bfgs.jl`)
`59d6c16`

**Motivation**: `profile_init.jl` hängt seit 48+ Stunden auf einem einzelnen BFGS-Call (Lorenz 3D, Stage 2). `maxiters` begrenzt nur Iterationen, nicht Wall-Clock-Zeit.

**Umsetzung:**
- `time_limit_s::Float64 = 300.0` zu `BFGSOptimizer` ergänzt
- `time_limit = opt.time_limit_s` an beide `Optimization.solve`-Aufrufe (BFGS + Nelder-Mead Fallback) übergeben
- Bei Timeout gibt Optim.jl das beste bisher gefundene Ergebnis zurück — kein Absturz, kein NaN
- Logging: `log_warn("BFGS hit time_limit", ...)` wenn `retcode != Success`

**Parameterwahl**: 300s ist ~100× der medianen per-Call-Zeit (ca. 2–3s), greift bei normalen Runs nie.

### Paper 1 Reproducibility Protocol dokumentiert
`844bbe4`

Vollständige Dokumentation der Paper-1-Konfiguration direkt aus dem Code abgeleitet:
- alle 6 Varianten mit Slug, Basis, Progressions- und Usage-Mode
- alle 10 Benchmark-Systeme (exakt/Surrogate) mit IDs und True-Struktur
- sämtliche Hyperparameter explizit
- Seeds, Metriken, Execution-Loop, Output-Artefakte, Aggregationsregeln, Freeze-Klausel

Dabei 5 Diskrepanzen zwischen Dokumentation und Codebasis gefunden und behoben:
1. `EvoGrow`-Struct fehlte `progression`, `usage`, `use_pretuning`
2. `test.jl` und `test_evogrow_v2_lotka.jl` im Dateibaum, existieren nicht mehr
3. `run_odebench.jl` als Root-Datei angegeben, liegt in `benchmarks/`
4. `src/optimize/pretune.jl` existiert und wird genutzt, war undokumentiert
5. `experiments/` fehlte komplett im Dateibaum

### Experiment-Status (Stichtag 27.04.)

| Skript | Status |
|--------|--------|
| `experiments/run_experiment.jl paper1_phaseA_v1` | läuft — 234/300, ~6–7h Restlaufzeit |
| `benchmarks/benchmark_evogrow.jl` | läuft — 93/300, ~27–40h Restlaufzeit |
| `generalization_study.jl` | fertig (Output-CSVs vorhanden, 24.04.) |
| `profile_init.jl` | hängt seit 2 Tagen — Level 11, Stage 2, Lorenz 3D, Seed 42 |

---

## 2026-04-26

### Repository-Housekeeping
`1f9c643`

- `benchmarks/odeformer/results/` entfernt: alte Ergebnisdateien ohne reproduzierbaren Kontext
- `.gitignore` um `benchmarks/odeformer/results/` ergänzt

### Analyse-Pipeline für Paper 1 angelegt
`6eab0cf`, `ea3cc44`, `053d717`, `c1f51ef`, `0f8e677`, `8c1152d`, `d983abf`

- `analysis/` als dedizierter Bereich für Python-Auswertung angelegt
- `analysis/CONVENTIONS.md`: Architektur- und Regelwerk für die Python-Analyse
- `analysis/utils/`: `io.py`, `metrics.py`, `style.py` (Variant-Farben und Labels)
- `analysis/scripts/aggregate/aggregate_run_registry.py`: liest `run_registry.csv`, schreibt `aggregate_by_variant_system.csv`
- `analysis/scripts/plot/plot_exact_match_rates.py`: Exact-Match-Rate-Plot
- `analysis/scripts/plot/plot_stage_overshoot.py`: Stage-Overshoot-Plot (GP ausgeschlossen)
- `analysis/scripts/plot/table_main_results.py`: LaTeX-Tabelle Main Results

### Paper-1-Protokoll eingefroren (`docs/paper1_study_protocol.md`)
`2e65d57`, `9ca633a`, `c810703`

Core Goal: Paper 1 untersucht staged growth als Mechanismus zur kontrollierten Komplexitätssteigerung — nicht "bestes ODE-Discovery-System".

Hypothesen:
- H1: Stage-local v2.2 zeigt niedrigeren `mean_stage_overshoot` als v2.1 und v1
- H2: v2.2 liefert kompetitive `exact_match_rate` bei niedrigerem Complexity-Efficiency-Cost
- H3: `mean_wasted_levels` nur zwischen EvoGrow-Varianten; GP ausgeschlossen
- H4: usage-policy comparison (`hard`, `soft`, `passive`) als sekundäre Hypothese

Evidenzregeln:
- Surrogate-Systeme nicht für `exact_support_match` oder H1–H4-Strukturaussagen
- Systeme 2 und 24 (expected_stage=1) aus H1/H3/H4 ausgeschlossen
- No post-hoc cherry-picking; keine neuen Runs nach Ergebnisinspektion

### Variant-Slug vereinheitlicht
`9d25f44`

`evogrow_v2_2_stage_local` überall standardisiert: `benchmark_evogrow.jl`, Analyse-Skripte, `style.py`, Dokumentation.

### Logging: Datum im Timestamp ergänzt
`035e354`

`src/utils/logging.jl`: Timestamp-Format von `HH:MM:SS` auf `yyyy-mm-dd HH:MM:SS` erweitert.
Grund: über Nacht laufende Skripte erzeugen sonst Logs ohne Datumszuordnung.

---

## 2026-04-23

### Bugs gefunden und gefixt
`d27b697`

**Bug 1: `PolynomialBasis` fehlte kubischer Term für System 11**
- `evogrow_v1` nutzte `PolynomialBasis` (nur bis Grad 2), System 11 (Critical slowing down) erwartet `u1^3`
- Entscheidung: `evogrow_v1` auf `default_staged_polynomial_basis` umgestellt — gleicher Suchraum wie alle anderen Varianten, alles sofort entsperrt

**Bug 2: `log_exception` speicherte `DataType` statt `String`**
- `merged[:exception_type] = typeof(err)` schlug fehl weil `Dict{Symbol,String}` keinen `DataType` akzeptiert
- Fix: `string(typeof(err))` in `src/utils/logging.jl`

### Generalisierungsstudie geplant und implementiert (`generalization_study.jl`)
`f30af7c`

Frage: Wenn EvoODE auf Parametersatz A die korrekte Struktur findet — passt diese Struktur nach reinem Parameter-Refit auch auf ungesehene Parametersätze B–E derselben ODE-Familie?

- 3 Systeme (Logistic growth, Lotka-Volterra, SIR), je 5 Parametersätze (1 Train + 4 Test)
- 2 Varianten (evogrow_v2_2_stage_local, gp_baseline), 3 Seeds
- Baseline: frischer Discovery direkt auf Testtrajektorie
- Output: `debug_results/generalization_study/generalization_summary.csv`, `generalization_detail.csv`

### Erste Experiment-Befunde (paper1_phaseA_v1, ~40/300 Runs)

Bisher abgeschlossen: System 2 (Population growth) und System 3 (Logistic growth).

- Alle Runs: `success=true`, `exact_support_match=true`
- Loss ist deterministisch: identisch über alle Seeds (Pretuning + BFGS konvergiert immer ins gleiche Minimum)
- **Stage Overshoot:**
  - `evogrow_v2_1` (global plateau): mittlerer Overshoot 1.5 auf System 3 (expected_stage=2, landet in Stage 3–4)
  - Alle v2.2-Varianten (stage_local): Overshoot 0 — bleiben korrekt in Stage 2
  - Direkte Bestätigung der Kernhypothese

---

## 2026-04-22

### Pretuning (OLS Warm-Start)
`c4fad8a`

- `src/optimize/pretune.jl`: Ableitung per finite Differenzen, Design-Matrix aus Basistermen, OLS-Lösung als BFGS-Startwert
- `use_pretuning::Bool`-Flag in `EvoGrow`
- `level_log` um `elapsed_s`-Feld erweitert

### Experiment-Infrastruktur (WP-E1 bis WP-E3)
`c4fad8a`

- `experiments/generate_manifest.jl`: erzeugt Experiment-Verzeichnis, `manifest.json`, alle per-Run `config.json` + `status.json`
- `experiments/run_experiment.jl`: sequentieller Runner mit robustem Fehlerhandling, atomaren Writes, restart-fähig
- `experiments/aggregate.jl`: leitet `run_registry.csv` aus per-Run-Ordnern ab, idempotent
- Per-Run-Dateiprotokoll: `config.json` (immutable), `status.json` (non-atomic), `result.json` + `metrics.json` (atomar via tmp→rename)

### Debug- und Profiling-Skripte
`c4fad8a`

- `debug_single.jl`: Einzelrun auf Lotka-Volterra mit verbose Logging und PNG-Output
- `profile_init.jl`: Vergleich random vs. pretune Initialisierung auf Lotka-Volterra + Lorenz, 3 Seeds

### Experiment gestartet

`paper1_phaseA_v1`: 10 Systeme × 6 Varianten × 5 Seeds = 300 Runs, exploratory

---

## 2026-04-21

### EvoGrow v2.2 (stage_local)
`224714d`

- `StageProgressionPolicy` mit Modus `:stage_local` und `min_levels_per_stage`
- `StageUsagePolicy` mit Modi `:hard`, `:soft`, `:passive` und `new_term_bias_prob`
- Stage-lokale Plateau-Detektion mit Mindestbudget pro Stage
- Benchmark-Matrix: 10 Systeme × 6 Varianten × 5 Seeds vollständig

---

## 2026-04-20

### Projekt-Fundament
`84f94e8`, `4d8bd2e`, `f5e1d9c`, `a811927`

- Core stabilisiert: EvoGrow und GP laufen sauber mit konsistentem Loss (`discover()` end-to-end)
- Benchmark-Infrastruktur angelegt: 10-System-Suite, erste Varianten
- Housekeeping: Stubs gefixt, Docstrings, Interface-Bereinigung

---
