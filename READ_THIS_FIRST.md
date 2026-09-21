# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-21. Working Tree sauber bis auf diese Datei.**

---

## 1. Wo wir stehen — in zwei Sätzen

**Beide Kampagnen-Jobs rechnen fehlerfrei, und es gibt nichts zu tun als zu warten.** Stand 21.09.:
C-1+C-2 bei **79/756**, C-3 bei **170/180** und damit fast fertig. 249 Records, **0 Fehler**, ein
Identitätstripel über alle. 5.068 verbrauchte Kernstunden.

**Die Parallelität von C-1+C-2 wurde am 21.09. von 32 auf 64 gepatcht**, weil C-3 auslief und über
50 Kerne brachgelegen hätten:

```
kubectl -n scch-das patch job evoode-phase-c-c1-c2-campaign -p '{\"spec\":{\"parallelism\":64}}'
```

(In PowerShell **müssen** die inneren Anführungszeichen escaped werden, sonst kommt bei kubectl
ungültiges JSON an.) Das ist reines Scheduling — `completions` bleibt 756, jede Zelle rechnet
unverändert, **keine Änderung an der eingefrorenen Konfiguration**. Danach 64 + 10 Pods bei 3,6
Kernen Fremdlast, also rund 78 von 96, keine Pending.

**Folge fürs Auswerten:** ab Zelle 80 laufen doppelt so viele Pods pro Node, `elapsed_s` ist deshalb
**nicht mit den ersten 79 Zellen vergleichbar**. Wissenschaftlich folgenlos (Designprinzip 7), aber
wo `elapsed_s` als Kontext auftaucht, gehört der Wechsel dazugesagt.

C-1+C-2 steckt noch in dim 3 (Systeme 52–60); die teuersten Systeme 55 und 56 sind durch. Die erste
dim-2-Zelle ab Warteschlangenposition 121 kommt **später als der ursprünglich genannte 20.09.**

**Alles, was ohne Kampagnenergebnisse machbar war, ist gemacht.** Es steht **keine Entscheidung
offen**, die den Lauf betrifft.

Laufender Stand auch als Seite: <https://claude.ai/artifact/4sq6HhRsnxgrFVqVF2trBx> — im README
verlinkt, wird bei Statuswechseln neu veröffentlicht.

Autoritative Quellen: `PAPER_1.md` → `docs/paper1_phaseC_benchmark_plan.md` → `CLAUDE.md` →
`DIARY.md` (neueste Einträge oben).

---

## 2. Wie du nachschaust

**Voraussetzung: VPN.** Am 18.09. war sie zwischenzeitlich weg. Prüfen mit PowerShell — **nicht**
mit `getent` in der Git-Bash, das benutzt einen anderen Resolver und meldet fälschlich
„nicht auflösbar":

```powershell
Resolve-DnsName api.orion.scch.at     # erwartet 172.21.202.100
```

Meldet `kubectl` „must be logged in", ist das Token abgelaufen:

```
oc login --web https://api.orion.scch.at:6443
```

### Fortschritt

```bash
kubectl get jobs -n scch-das
```

Erwartet: beide Jobs **Running**, Zähler wachsend.

**Den Zähler nicht hochrechnen.** Die Warteschlange (`indices_c1_c2_cost_desc.txt`) ist
**kostenabsteigend**: Positionen 1–120 sind dim 3, 121–456 dim 2, 457–480 dim 4, 481–756 dim 1. Am
18.09. wurde aus einer Zellen-Hochrechnung einmal eine Restlaufzeit von 140 Tagen. **In Kernstunden
rechnen, nie in Zellen** — die fertigen Zellen sind stets ein weit größerer Kostenanteil, als ihre
Zahl nahelegt.

### Auslastung

```bash
kubectl -n scch-das get pods --field-selector=status.phase=Running -o jsonpath='{range .items[*]}{.spec.containers[*].resources.requests.cpu}{"\n"}{end}' | sort | uniq -c
```

Erwartet **74 Pods** mit je `1`, solange C-3 noch läuft (64 für C-1+C-2 plus dessen letzte 10),
danach 64 — plus die kleinen Pods der Mitbenutzer, zusammen rund 3,6 Kerne.
**CPU-Requests zählen, nicht Pods.** Keine ResourceQuota im Namespace; es begrenzt allein die
Node-Kapazität von 96 Kernen. Reicht sie nicht, werden Pods **Pending** — der harmlose Fehlermodus.

### Ergebnisse, ohne Cluster

```text
S:\BigDataOrion\data-science\joedicke\phase_c_campaign_221a3a72f0cb43164a22b09baac2d9ae82681a02\tasks\
```

`cell_NNNNNN.jsonl` ist je ein Ergebnis, `*.heartbeat.jsonl` der Verlauf — **beim Zählen die
Heartbeats ausschließen.** Die Freigabe ist über SMB **nur lesbar**: `FullControl` hat allein die
NFS-Kennung, unter der die Pods schreiben. Schreibversuche scheitern auch ohne Sandbox.

**Fehlerbilder:** `ErrImagePull` heißt Anmeldung, nicht fehlendes Image. `OOMKilled` heißt, die
2 GiB haben nicht gereicht.

---

## 3. Was als Nächstes ansteht

1. **Die dim-2-Nachzählung — der einzige terminierte Punkt.** Sobald die ersten dim-2-Zellen fertig
   sind (ab Warteschlangenposition 121), dieselbe Paartabelle ziehen: `stage_caps`,
   `executed_levels`, `total_loss_evals`. **Dabei nach voll gegen teilweise gekappten Zeilen
   trennen** — das ist der eigentliche Test, Begründung in Abschnitt 4.
   Vorher noch interessant: die drei voll gekappten dim-3-Zeilen (System 60 IC 2, System 61 IC 1/2).
2. **Warten.** Rest grob **2 bis 2,5 Tage** bei 64 Kernen — Kapazitätsplanung, keine Evidenz
   (Designprinzip 7). Hergeleitet aus ~3.400 offenen Kernstunden: dim 3 noch ~1.650 h (41 Zellen,
   davon 12 auf System 61), dim 2 ~1.450–2.000 h (2,0 h/Zelle aus C-3 mal Faktor 2,17, dem
   gemessenen Pretuning-Unterschied auf dim 3), dim 1 und dim 4 zusammen unter 35 h. **Die
   Restlaufzeit hängt an der längsten Einzelzelle, nicht am Durchsatz** — die teuerste bisher lief
   167 Stunden.
   Nebenrechnung: 5.068 verbraucht plus ~3.400 Rest ergibt **~8.500 Kernstunden gegen die geplanten
   12.300–15.900**. Vor allem, weil C-3 mit ~1.000 h statt 2.400 h durchläuft. Die Planzahl war
   konservativ — beim Schreiben so sagen, sonst wird sie als Messwert zitiert.
3. **Danach auswerten**, dann Claim D über die Paarung gegen die gerechnete SINDy-Baseline schließen,
   inklusive Trajektorien-Abgleich per Hash.
4. **Nach Kampagnenende:** Baseline-Image bauen, damit ODEFormer laufen kann.

**Während des Laufs verboten:** irgendetwas an der eingefrorenen Konfiguration ändern, und **nicht
nach GitLab pushen** — ein Push baut das Kampagnen-Image neu. Alles seit `221a3a7` liegt nur auf
GitHub.

---

## 4. Der eine offene Befund: die Kappe terminiert nur, wenn sie *alle* Gleichungen kappt

**Stand 21.09., 38 vollständige Paare, alle dim 3, Systeme 52–60.** Ausführlich im `DIARY.md` unter
dem 20.09.; hier die Kurzform und was daraus für die Auswertung folgt.

- **15 Paare ohne Kappe:** `total_loss_evals` und `executed_levels` **15/15 bit-identisch**. Das ist
  eine bestandene Kontrolle — die Arme unterscheiden sich durch die Kappe und sonst nichts.
- **23 Paare teilweise gekappt** (`[None,3,3]`, `[None,None,3]`): **22 von 23 fahren 30/30 Level**
  (die Ausnahme 29). Die Kappe terminiert dort nichts — Zahlen weiter unten.
- **Kein vollständiges Paar mit voller Kappe**, und genau das wäre der Test.

**Der Mechanismus steht im Code.** `_effective_max_stage` (`src/structure/evogrow.jl:141-144`)
nimmt das **Maximum** über die Kappen und setzt `nothing` auf `max_stage`; eine offene Gleichung
hält das volle Stufenbudget für alle offen. Gekappte Gleichungen werden nur in ihren Termen
begrenzt, nicht eingefroren.

**Vorhersage, datiert vor der Messung:** Ersparnis genau dort, wo **alle** Gleichungen eine endliche
Kappe tragen. Die suchfreie Gegenprobe
(`outputs/phase_c_cap_incidence/stage_caps_by_basis.csv`) sagt, wo das ist — voll gekappt sind
**dim 1: 32/46, dim 2: 15/56, dim 3: 3/20, dim 4: 0/4**. Die drei dim-3-Zeilen sind **System 60 IC 2
und System 61 IC 1/2** und stehen noch aus. Bisher gemessen wurden ausschließlich Zellen, in denen
die Kappe strukturell nicht terminieren kann — **Claim B ist nicht widerlegt, sondern noch nicht
getestet.**

**Erster Beleg, Stand 21.09. — er passt, trägt aber noch nicht.** Über alle dim-3-Zellen mit
aktiver Kappenpolitik:

| Kappenklasse | n | Level min/median/max | erreichen 30 Level |
|---|---|---|---|
| keine | 24 | 20 / 22 / 26 | 0 / 24 |
| teilweise | 47 | 23 / **30** / 30 | **41 / 47** |
| voll | 7 | 14 / 23 / 25 | **0 / 7** |

Alle sieben voll gekappten Zellen enden auf **Endstufe 3** — exakt dem Kappenwert. **Aber der
Systemeffekt ist nicht abgetrennt:** „voll" (Median 23) liegt nicht früher als „keine" (Median 22),
und die Kappenklasse *ist* eine Systemeigenschaft. Sechs der sieben Zellen gehören zu C-3 und haben
gar kein Gegenstück; von System 60 IC 2 Seed 123 (`[3,3,2]`, 14 Level, Stufe 3) fehlt der
uncapped-Partner noch.

**Die scharfe Einzelvorhersage lautet deshalb: der uncapped-Partner von 60/IC 2/Seed 123 erreicht
Stufe 5 und fährt deutlich mehr als 14 Level.** Trifft das nicht zu, ist der Mechanismus falsch.

**Teilweise gekappt, jetzt 23 Paare statt 10:** 14 teurer, 2 billiger, 7 gleich, in Summe
**+1,36 %** — systematisch, aber winzig. Qualität spricht eher für die Kappe: Loss in 7 Paaren
besser, in 3 schlechter. Die 15 kappenlosen Paare bleiben **15/15 bit-identisch**.

**Beim Auswerten prüfen:** die ausstehenden voll gekappten dim-3-Paare (System 60 IC 2, System 61),
dann die 15 voll gekappten dim-2-Zeilen gegen die 21 nur teilweise gekappten, dann die 32 voll
gekappten dim-1-Zeilen. Fällt die Ersparnis auch bei voller Kappe aus, betrifft das Claim B im
Kern.

**Nicht an der Kappe drehen.** Aggressiver kappen hieße, auf die Abwesenheit von Evidenz zu kappen
(vom System-63-Defekt ausgeschlossen); die Schwellen nachziehen ist der WP-V1-Fehler. Der Hebel wäre
die Granularität der Terminierung — gekappte Gleichungen einfrieren statt nur ihre Terme begrenzen.
**Paper 2, nicht jetzt**, und zu messen statt zu behaupten.

**Instrumentierungslücke:** im ungekappten Arm sind `eq_final_stages`, `stage_caps` und
`eq_overshoot` **0/26 befüllt**; nur `final_stage` existiert, und das ist das Maximum über die
Gleichungen. Aus der suchfreien Gegenprobe rekonstruierbar.

**Zweiter Merkposten fürs Auswerten:** hilft k = 3 gegen den Konstanten-Defekt auf dim 2? Der
dim-2-Probelauf lief unter `ec3b6bd`, also vor der Restart-Politik, mit k = 1; C-1 fährt k = 3. Die
Vermutung ist geprüft und **vermutlich falsch** (0 Sentinel-Losses in 336 Zellen), aber nachsehen.
Zwei Auflagen: anderes Identitätstripel, deshalb **Diagnostik und niemals eine gemeinsame Tabelle**;
und der Git-Hash driftet mit, k ist nicht sauber isoliert.

---

## 5. Was am 18.09. dazugekommen ist (unverändert gültig)

Alles committet, alles im `DIARY.md` unter dem 18.09. mit Hashes.

- **C-3 gestartet** (`resume_c3.json`). Der Aufräumschritt aus der alten Übergabe war **hinfällig**:
  WP-C5 hat den Heartbeat-Leser am 15.09. an `start`-Ereignissen segmentiert, der angehängte echte
  Lauf gewinnt. Nachgeprüft — die Reste der Zellen 883–914 tragen jetzt zwei `start`-Zeitstempel.
- **`baselines/`** — Harness, die Fremdmethoden auf **unseren** 126 exportierten Trajektorien
  rechnet, mit Hashprüfung als Abbruchbedingung und gespeicherten Koeffizienten. `odeformer` ist
  **gepinnt** (`c9193012`), nicht einkopiert; eigenes Python-3.9-Image; `containers/Dockerfile`
  unberührt. SINDy läuft, ODEFormer wartet aufs Image. WP-N19 / WP-N19b.
- **Zwei Entscheidungen vor der Messung eingefroren**, beide in
  `docs/paper1_phaseC_benchmark_plan.md`: **§6a** — Methodenkosten sind *strukturell*, Zeit ist
  sekundär und deklarationspflichtig, weil es über Methoden hinweg keine gemeinsame Zähleinheit
  gibt. **§6b** — beide R²-Aggregationen werden berichtet, die varianzgewichtete trägt das Etikett
  Literaturvergleich, **weil** sie ODEBench' Definition ist und nicht, weil sie besser aussieht.
- **WP-N20**: die varianzgewichtete Aggregation ist aus vorhandenen Records rekonstruierbar, ohne
  Neulauf. Über die volle Phase-B-Kampagne: **53 von 756 Zellen kippen über die 0,9-Schwelle, alle
  53 nach oben, 0 nach unten.** Kontrolle in 756/756 bestanden.
- **README korrigiert** — er führte die auf Diagnostik herabgestufte Phase B noch als „die Evidenz"
  und „die Hauptkampagne", während Phase C im Fließtext gar nicht vorkam. Plus fünf kleinere.

---

## 6. Kleinkram, der sonst untergeht

- **Identität dieser Kampagne:** `git 221a3a72f0cb43164a22b09baac2d9ae82681a02`,
  `config_fingerprint 0c9672de35c75a9d`, Verhaltens-Fingerprint `ffb0266c7913352c`, Basis
  `staged_polynomial_basis_with_constant`, `max_fit_attempts = 3`.
- **Jobs startet ausschließlich der Nutzer.** Claude sind `kubectl apply`, `patch` und `delete`
  gesperrt; Claude liest und prüft.
- **`codex exec` braucht im Auto-Modus eine `allow`-Regel**, sonst scheitert die Übergabe **still** —
  der Auftrag ist geschrieben, aber nie übergeben. Die Regel steht in `.claude/settings.json`, die
  ignoriert ist und daher nur auf diesem Rechner lebt; die Anforderung ist deshalb in
  `codex/CODEX_PROTOCOL.md` dokumentiert. **Claude darf sie nicht selbst setzen** — das blockt der
  Auto-Modus als Self-Modification, zu Recht.
- **Codex kann hier kein Julia ausführen.** Julia-Pakete werden geschrieben, als `blocked` gemeldet,
  Claude fährt die Abnahme. Python läuft normal.
- **Nodes darfst du nicht auflisten** (`Forbidden`). 96 Kerne auf `alnilam01` / `alnilam02`.
- **Fertige Jobs räumen sich selbst weg** (`ttlSecondsAfterFinished: 3600`). Eine kürzer werdende
  Jobliste heißt „aufgeräumt", nicht „fertig".
- **Protokollregel:** Fixtures werden aus echten Records **abgeleitet**, nie erfunden. Grüne Tests
  an erfundenen Daten haben schon mehrere Arbeitspakete durchgewinkt, die an echten Daten umfielen.
- **Eine deklarierte, ungeprüfte Annahme** (§6b): die Gewichte der Phase-B-Auswertung stammen aus
  dem **Phase-C**-Trajektorienexport, weil Phase Bs eigene Trajektorien nicht versioniert sind. Das
  Protokoll ist identisch, also sollten es dieselben Zahlen sein — geprüft ist es nicht, und die
  Kontrollen können es nicht prüfen.
