# WP-N19b — Baseline-Harness: die drei Befunde der Abnahme schliessen
**Language: Python**

## Ausgangslage

WP-N19 ist committet (`919cd5c`) und die Harness unter `baselines/` funktioniert: Hashpruefung mit
Abbruch, Fehler-Records statt fehlender Zeilen, Koeffizienten gespeichert, `containers/Dockerfile`
unberuehrt. Die Abnahme durch Claude hat drei Befunde ergeben, die hier geschlossen werden. **Es
geht um Nachbesserung, nicht um Neubau** — der bestehende Aufbau bleibt.

## Befund 1 — die Systemauswahl ist festverdrahtet

`selected_systems` in `baselines/harness.py` filtert hart auf `dim == 1`. Damit ist der eigentliche
Zweck der Harness — alle 126 exportierten Trajektorien — **nicht erreichbar**; sie kann bisher nur
den Rauchtest.

Die Auswahl gehoert in die Konfiguration. Verlangt sind drei Angaben, die sich kombinieren lassen:
eine Einschraenkung auf Dimensionen, eine Einschraenkung auf ausdrueckliche System-Kennungen, und
eine Obergrenze fuer die Anzahl. Ohne jede Angabe laeuft die Harness ueber **alle** Systeme des
Manifests — das ist der Normalfall, nicht der Sonderfall.

Die Auswahl muss deterministisch sein: dieselbe Konfiguration ergibt dieselbe Systemliste in
derselben Reihenfolge. Welche Systeme ein Lauf umfasst, gehoert in jeden Record oder in eine
Begleitdatei, nicht nur in die Konfiguration.

`max_dim1_systems` aus der bestehenden Smoke-Konfiguration verschwindet damit. Der Name hat die
Einschraenkung mitgetragen und darf nicht als Synonym weiterleben.

## Befund 2 — die Schwellenflags waehlen heimlich eine Hauptzahl

`reconstruction_r2_gt_0_9` und `generalization_r2_gt_0_9` werden allein aus dem arithmetischen
Mittel gebildet (`harness.py:284-285`). Der Auftrag von WP-N19 verbot ausdruecklich, eine der beiden
Aggregationen zur Hauptzahl zu erklaeren — hier ist es implizit doch geschehen.

Verlangt ist **je ein Flag pro Aggregation**, beide Richtungen, also vier Felder. Die Benennung muss
die Aggregation im Namen tragen, sodass eine Auswertung nicht raten muss. Die beiden bisherigen
Feldnamen duerfen **nicht** bestehen bleiben: ein Name ohne Aggregationsangabe ist genau der Defekt,
der geschlossen wird — `CLAUDE.md` fuehrt unter „Known Gaps" bereits einen Fall, in dem ein
Spaltenname zwei Bedeutungen trug.

Warum das zaehlt: an echten Trajektorien liegen die beiden Aggregationen 1,7 Punkte (System 24,
dim 2) und 2,0 Punkte (System 52, dim 3) auseinander. An einer Schwelle von 0,9 entscheidet das
ueber Treffer oder Nichttreffer.

## Befund 3 — der Mehrdimensions-Test erfindet seine Fixture

`test_r2_aggregations_are_distinct_on_multidimensional_case` baut ein Array aus vier Zeilen von
Hand. Das verstoesst gegen die Regel in `codex/CODEX_PROTOCOL.md`, und schwerer wiegt die Folge: der
Rauchtest deckt nur Dimension 1 ab, wo beide Aggregationen **konstruktionsbedingt gleich** sind.
Die beiden Codepfade sind auf echten mehrdimensionalen Daten nie verglichen worden.

Der Test leitet seine Daten kuenftig aus dem **echten Export** ab
(`outputs/phase_c_trajectory_hashes/wp_c4c/trajectory_export/`, 126 Zeilen, Rohdaten als float64
mit Achsenangaben im Manifest). Referenz ist eine reale Trajektorie eines mehrdimensionalen Systems;
die Vorhersage darf daraus abgeleitet werden, solange die Ableitung sichtbar ist und die Varianzen
der Dimensionen aus den echten Daten stammen — genau sie erzeugen den Unterschied.

Fuer Records gilt dieselbe Regel, und die Grundlage existiert jetzt:
`analysis/data/paper1_phaseC_v1/phasec_external_baselines_wp_n19_smoke/records.jsonl` ist ein
echter, versionierter Recordbestand.

## Zusaetzlich: der Rauchtest muss mehrdimensional werden

Bisher deckt er drei Systeme der Dimension 1 ab und kann die Kernaussage aus Befund 2 deshalb gar
nicht pruefen. Kuenftig enthaelt er **mindestens ein System mit Dimension 2 oder hoeher**. SINDy ist
dort eine lineare Regression je Gleichung, also weiterhin im Minutenbereich.

Aendert sich durch die Umbenennung der Felder der Recordbestand unter
`phasec_external_baselines_wp_n19_smoke/`, wird er **neu erzeugt** und nicht von Hand angepasst.

## Was ausdruecklich nicht gerechnet wird

Kein Lauf ueber alle 126 Trajektorien, auch wenn die Auswahl ihn jetzt zulaesst. Kein Bauen des
Baseline-Images, kein Netzzugriff auf die ODEFormer-Gewichte. **Nicht nach GitLab pushen** —
C-1+C-2 rechnet, und ein Push baut das Kampagnen-Image neu.

`containers/Dockerfile` bleibt unberuehrt.

## Abnahmekriterium

1. Eine Konfiguration ohne Auswahlangabe umfasst alle 126 Manifestzeilen; eine mit Dimensions- oder
   Kennungsfilter genau die erwartete Teilmenge. Beides nachweisbar **ohne** die Zellen zu rechnen.
2. Ein Record traegt vier Schwellenflags, je Richtung und Aggregation, mit der Aggregation im
   Namen. Die beiden alten Namen kommen im Recordbestand nicht mehr vor.
3. Der Rauchtest enthaelt mindestens ein System mit Dimension >= 2, und fuer dieses System sind die
   beiden Aggregationen im Record **nachweislich verschieden**.
4. Kein Test im Paket baut seine Eingabedaten von Hand; jeder leitet sie aus dem Export oder aus dem
   vorhandenen Recordbestand ab. Im Report ist je Test die Herkunft benannt.
5. Die Zusagen aus WP-N19 halten weiterhin: verfaelschter Hash bricht ab, gescheiterte Methode
   erzeugt einen Fehler-Record, `containers/Dockerfile` unveraendert.

## Bericht

`codex/reports/REPORT_WP_N19b.md`. Aufzunehmen: die neuen Feldnamen mit ihrer Herkunft, die
Herkunft der Testdaten je Test, die gemessene Differenz der beiden Aggregationen auf dem
mehrdimensionalen Rauchtestsystem, und jede Stelle, an der die Umbenennung eine bestehende Datei
beruehrt hat.
