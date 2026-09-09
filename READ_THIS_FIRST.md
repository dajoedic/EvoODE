# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon, und es wird in jeder Sitzung ohnehin automatisch geladen. Alles Dauerhafte gehört
dorthin, nach `PAPER_1.md` oder ins `DIARY.md` — **nicht hierher.**

**Regeln für dieses Dokument:** wird immer **vollständig überschrieben**, nie angehängt. Alles darin
ist mit einem Datum versehen. Was älter als ein paar Tage ist, ist vermutlich falsch — dann gilt
`CLAUDE.md`.

**Stand: 2026-09-09, spätabends. HEAD = `d558828`.**

---

## 1. Wo das Projekt inhaltlich steht — in drei Sätzen

Paper 1 ist seit dem 09.09. ein **Methodenpaper**: EvoGrow ist der Gegenstand, die Stufenkappe eine
Komponente mit eigener Ablation, die Failure-Analyse ein Limitations-Abschnitt. Die 756-Zellen-Phase-B-Kampagne
ist vom Hauptbenchmark zu **Diagnostik und Ablationsquelle degradiert**, weil sie vor Abschluss des
methodischen Audits gerechnet wurde. Die neue kanonische Evaluation heißt **Phase C** und ist
definiert, aber nicht gestartet.

Autoritative Quellen, in dieser Reihenfolge: `PAPER_1.md` (Zuschnitt und Claims) →
`docs/paper1_phaseC_benchmark_plan.md` (Experimentmatrix, Freeze-Liste, Voraussetzungen) →
`CLAUDE.md` (Orientierung) → `DIARY.md` (Chronologie, neueste Einträge oben).

---

## 2. Was JETZT läuft — beim Sitzungsstart prüfen

### Cluster: der dim-2-Probelauf

```bash
kubectl get jobs -n scch-das
```

Erwartet: `evoode-wp-n1-dim2-campaign`, Ziel **336** Zellen, `parallelism: 32`.
Stand 09.09. ~23:00: **46/336 nach 122 Minuten.**

Erwartete Gesamtdauer **~47 Stunden**, also bis etwa **11.09. abends**. Der Fortschritt verlangsamt
sich stark — Median 1,12 h je Zelle, p90 10,5 h, längste Kampagnenzelle 46,98 h. Ein langsam
kriechender Zähler am Ende ist **normal, kein Hängen**; mehr Pods würden nichts bringen, weil eine
Zelle ein Pod ist und nicht teilbar.

Ergebnisse ohne Anmeldung sichtbar unter:
`S:\BigDataOrion\data-science\joedicke\wp_n1_dim2_probe_ec3b6bd5b43f06539d38b633257ca51115bfa47f\tasks\`

**Wozu der Lauf dient:** Er entscheidet den **letzten offenen eingefrorenen Parameter** der Phase C —
ob der konstante Term `1` in die kanonische Basis kommt. Ohne diese Entscheidung darf Phase C nicht
starten.

**Wie er ausgewertet werden muss** (wichtig, sonst wird falsch verglichen): gegen eine **Rohbasis von
17,6 %**, nicht gegen die vertrauten 49,1 %. Siehe Abschnitt 4.

### Lokal: eine Messung im Hintergrund

Eine Regressionszelle auf **System 26** (dim 2, gekoppelt) misst die `StructureSpec`-Duplikatrate.
Erwartete Laufzeit 11–27 Minuten. Ergebnis landet in
`outputs/studies/regression/wp_n10_dup_26/history.jsonl`, Felder
`total_candidate_structures_evaluated` und `unique_candidate_structures_evaluated`.

Falls die Datei fehlt oder leer ist, ist der Lauf gestorben — dann einfach neu starten (Kommando in
`codex/reports/REPORT_WP_N10.md`).

---

## 3. Was uncommittet im Working Tree liegt — WP-N10

```text
 M src/structure/evogrow.jl              <- kanonischer Strukturschlüssel + Duplikatzähler
 M studies/regression/run_regression.jl  <- neue Felder in die Records
 M codex/CURRENT_TASK.md, codex/STATUS.md
?? codex/reports/REPORT_WP_N10.md
?? test/test_structure_canonical_key.jl
```

**Die Abnahme ist gefahren und bestanden**, alles davon von Claude verifiziert, nicht von Codex:

| Prüfung | Ergebnis |
|---|---|
| A/B bit-identisch (dieselbe Zelle mit/ohne Zähler) | **0 Abweichungen** — `loss` über alle 15 Stellen gleich, `total_loss_evals`, `total_parameter_fits`, `total_ode_solves`, `r2`, `pruned_match`, `support_terms` identisch |
| `phase_b_fingerprint()` | `604e79733b22d64d`, unverändert |
| `stage_cap_behavior_fingerprint()` | `ffb0266c7913352c`, unverändert |
| Tests | 9 grün (`test/test_structure_canonical_key.jl`) |

**Warum noch nicht committet:** Ich wollte die dim-2-Duplikatrate abwarten, damit Abnahme und Befund
in einem Commit stehen. **Wenn das stört: committen ist unbedenklich**, die Abnahme ist vollständig.

---

## 4. Die zwei Befunde von heute, die künftige Auswertungen binden

### (a) 36 % unserer Strukturtreffer stammen von der Ausdünnungsregel

Auf den 240 exakten Phase-B-Zellen: **roher** exakter Match **70**, **ausgedünnter** Match **110**
(die berichtete Zahl), **40 Treffer allein durch die Ausdünnung**. Die Aufschlüsselung ist der
eigentliche Befund:

| dim | roh | ausgedünnt | gerettet |
|---|---:|---:|---:|
| 1 | 51/72 (70,8 %) | 57/72 (79,2 %) | 6 |
| **2** | **19/108 (17,6 %)** | **53/108 (49,1 %)** | **34** |
| 3, 4 | 0 | 0 | 0 |

Auf dim 2 produziert **die Schwelle 64 % der Treffer, nicht die Suche**. Ehrliche Lesart: die Suche
landet auf gekoppelten Systemen fast nie auf dem exakten Support, sondern auf einer Obermenge, und
die Schwelle räumt auf.

**Bindende Regeln daraus:** roh **und** ausgedünnt immer nebeneinander berichten. Die Schwelle
`max(1e-6, 1e-3*max_abs)` bleibt **eingefroren** — das ist ein Grund zu berichten, nie zu justieren
(WP-V1, WP-N2). Phase-C-Records speichern **roh, ausgedünnt und Koeffizienten**, alle drei.

Nicht betroffen: **WP-A7** (Pretuning-Seed-Kollaps) gruppiert auf rohen `support_terms` und ist
schwellenunabhängig. Betroffen und weiterhin zurückgezogen: WP-A6.

### (b) Ein Spaltenname, zwei Bedeutungen

`experiments/run_experiment.jl:405` schreibt den **rohen** Match in `exact_support_match` (Phase-A-Pfad);
`studies/regression/run_regression.jl` schreibt `pruned_match` unter demselben Namen (Phase-B-Pfad).
**Phase A und Phase B über diese Spalte zu joinen vergleicht verschiedene Größen.** Wächter:
`analysis/utils/support_match_definition.py`.

---

## 5. Die offene Frage, die als Nächstes entschieden werden muss

**Die eingefrorene Restart-Politik steht auf wackliger Begründung.**

Entschieden am 09.09.: kanonisch ist `pretuning = false` plus **retry-on-failure bis k = 3**.
Begründung war WP-N4: mit der *wahren* Struktur scheitert ein **einzelner** Fit in 15 von 102 Zellen
am Sentinel-Loss, bei k = 3 in keiner.

**Die heutige Messung stellt die Prämisse infrage.** Auf dim 1 bekommt jede Struktur effektiv
**20 bis 160 Fits**, nicht einen:

| System | Fits | eindeutige Strukturen | Duplikatrate |
|---|---:|---:|---:|
| 3 | 110 | 2 | 98,2 % |
| 11 | 290 | 3 | 99,0 % |

Der implizite Multistart ist auf dim 1 also **riesig**, und WP-N4 lief auf dim-1-Zellen — genau dort.
Ein „einzelner Fit" ist ein Zustand, den die Suche dort gar nicht herstellt.

**Wichtige Einordnung, die eine frühere Fehldeutung korrigiert:** Die hohe Duplikatrate heißt **nicht**
„die Suche exploriert nicht". Auf dim 1 und niedriger Stufe ist der Strukturraum so klein, dass es
kaum mehr Strukturen *gibt*. Der Befund lautet „Raum erschöpft", nicht „Suche untätig".

**Was die Entscheidung bringt:** die laufende dim-2-Messung (System 26). Ist die Duplikatrate auf
gekoppelten Systemen ebenfalls sehr hoch, trägt der explizite Retry kaum etwas bei und die Politik
gehört neu begründet. Ist sie niedrig, greift er genau dort, wo die Trefferquote 0 von 50 ist.
**Eine einzelne Zelle entscheidet die Frage nicht** — sie zeigt die Größenordnung. Phase C liefert
die belastbare Verteilung über 378 Zellen umsonst, weil der Zähler jetzt drin ist.

---

## 6. Was danach ansteht

Die blockierenden Voraussetzungen stehen vollständig in
`docs/paper1_phaseC_benchmark_plan.md` §4. Kurzfassung des Stands:

| | Voraussetzung | Stand |
|---|---|---|
| P1 | `git_hash` im Probe-Skript reparieren | **erledigt** (WP-N8) |
| P2 | dim-2-Probelauf | **läuft** |
| P3 | kanonische Basis entscheiden und einfrieren | wartet auf P2 |
| P4 | Strukturmetriken (F1, Precision, Recall, Koeffizientenfehler) | **erledigt** (WP-N7/N7b) |
| P5 | dreiwertige Repräsentierbarkeit | **erledigt** (WP-N7) |
| P6 | Restart-Politik implementieren und deklarieren | **offen**, siehe §5 |
| P7 | Duplikatrate messen | **Zähler gebaut** (WP-N10), Zahl kommt aus Phase C |
| P8 | Phase-C-Matrix vervollständigen | offen |
| P9 | Smoke-Test vor Einreichung | offen |

Dazu **fünf offene Fragen** in §7 des Phase-C-Plans, die den Freeze blockieren: Zuschnitt der
SINDy-Vergleichsmenge, Systeme und k-Werte der Restart-Ablation, Oracle-Arm auf einer oder beiden
Basen, Pretuning-Ablation neu rechnen oder Phase B zitieren, Pilot samt Go-Kriterium.

Zu einer davon gibt es bereits eine begründete Empfehlung: **die Pretuning-Ablation muss Phase C
nicht neu rechnen.** WP-A7 ist schwellenunabhängig gemessen und unter Vorgänger-Label zitierbar —
das spart einen kompletten 378-Zellen-Arm.

---

## 6b. Was man nicht vergessen darf

Dinge, die nichts blockieren und genau deshalb untergehen. Keine davon ist dringend; jede kostet
später mehr als jetzt.

**Das Deploy-Token für die Registry läuft ab.** Am 09.09. ist genau das passiert, mitten im
Smoke-Job (`ErrImagePull` mit `HTTP Basic: Access denied` — es sieht nach einem fehlenden Image aus,
ist aber die Anmeldung). Das aktuelle Token ist `gitlab+deploy-token-13`, angelegt 09.09. **Pods
werden über die ganze Laufzeit hinweg neu erzeugt** — läuft das Token mitten in einem mehrtägigen
Lauf ab, entsteht ein halb fertiger Datensatz mit einer Lücke in der Mitte. Deshalb: Ablaufdatum
großzügig, und **immer erst den Smoke-Job**. Fehlermodus dokumentiert in
`docs/hpc_deployment_guide.md` §8.

**Das Token steht im Klartext im Chatverlauf vom 09.09.** Read-only auf die Registry beschränkt,
aber wenn es stört: tauschen.

**`parallelism` steht auf 32, nicht auf den vereinbarten 16.** Begründung als Kommentar im Manifest
`k8s/wp_n1_basis_probe_dim2_campaign_job.yaml`. Der Namespace hat keine `ResourceQuota` und keine
`LimitRange`, die 16 waren eine Absprache — nicht abgestimmt, aber technisch unbedenklich, weil
`requests == limits` gilt und überzählige Pods `Pending` bleiben statt jemanden zu verdrängen.
Falls sich jemand meldet: das ist der Kontext.

**Die 756 Kampagnenzellen tragen keine Koeffizienten.** Jede dimensionsübergreifende
Generalisierungszahl erfordert einen Neulauf. Das ist der Grund, warum Phase C überhaupt nötig ist.

**Niemand führt die Python-Tests aus.** Die GitLab-CI baut ausschließlich das Kampagnen-Image. Ein
Wächtertest war drei Wochen rot, ohne dass es auffiel. Aktuell 15 Tests grün, aber nur weil sie von
Hand laufen.

**Elf Skripte** unter `benchmarks/` und `studies/` konstruieren den Optimierer ohne Budget und sind
seit WP-B3 unbeschränkt. Bewusster Rückstand, gelistet in `codex/reports/REPORT_WP_D3.md`.

**Die externen Spalten des Protokoll-Audits** (`docs/paper1_odebench_protocol_alignment.md`) sind
der letzte substanzielle Phase-3-Posten — inklusive der offenen Frage, ob publizierte Vergleichszahlen
auf den *mitgelieferten* Trajektorien gerechnet wurden. Falls ja, arbeiten wir auf saubereren Daten
als der Vergleich, und das muss deklariert werden.

**`DIARY.md` ist 400+ KB und wird bei fast jedem Commit angefasst.** Das hatte `.git` auf 852 MB
aufgebläht (tatsächlicher Inhalt: 6,3 MB, der Rest lose Objekte). Nach `git gc --prune=now` sind es
11 MB. Gelegentlich wiederholen.

---

## 7. Arbeitsweise — was eine neue Sitzung wissen muss

**Codex-Handschlag.** Claude schreibt `codex/CURRENT_TASK.md` und startet die Sitzung selbst per
`codex exec`; Codex schreibt ausschließlich `codex/STATUS.md`. **Codex kann in dieser Umgebung kein
Julia ausführen** — Julia-Pakete werden geschrieben, als `blocked` gemeldet, und Claude fährt die
Abnahme. Python läuft normal.

**Zwei Fallen, heute beide aufgetreten:**

- Codex **löscht** `STATUS.md` manchmal, statt sie zu überschreiben — das Signal fehlt dann kurz ganz.
- Bei einem Absturz (`ERROR: Selected model is at capacity`) bleibt `status: working` stehen. Eine
  tote Sitzung ist an `STATUS.md` **nicht** von einer arbeitenden zu unterscheiden. **Immer beides
  prüfen: Working Tree und Prozess-CPU-Zeit**, nie nur `STATUS.md`.

**Lange Läufe startet ausschließlich der Nutzer.** Claude bereitet vor, prüft, gibt die Kommandos im
Chat aus — mit Zweck, Dauer, Pass-Kriterium und ob die Ausgabe gebraucht wird.

**Wall-clock ist nie Evidenz** (Designprinzip 7). Kostenaussagen ruhen auf Zählern; Zeiten dienen
der Kapazitätsplanung und werden als solche gekennzeichnet.

**Immer beide Metriken** (Designprinzip 9): Strukturtreffer **und** Anteil R² > 0,9, nie eine allein.

**Kein Mittelwert oder Median als Effektstärke** — Quantile und Schwellengitter, und die Schwelle
wird nie nach Sicht der Daten gewählt.

---

## 8. Wenn dieses Dokument alt ist

Prüfe zuerst `git log --oneline -10` und die obersten Einträge in `DIARY.md`. Weicht der HEAD von
`d558828` ab, ist alles in Abschnitt 2 und 3 hier vermutlich überholt — dann gilt `CLAUDE.md`, und
dieses Dokument gehört neu geschrieben statt geflickt.
