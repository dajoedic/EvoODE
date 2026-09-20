# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-20. Kampagnenzahlen vom 19.09. Working Tree: DIARY.md und diese Datei geändert.**

---

## 1. Wo wir stehen — in zwei Sätzen

**Beide Kampagnen-Jobs rechnen fehlerfrei, und es gibt nichts zu tun als zu warten.** Stand 19.09.:
C-1+C-2 bei **52/756**, C-3 bei **62/180**, 0 Fehler, ein Identitätstripel über alle 114 Records,
1.965 verbrauchte Kernstunden gegen 12.300–15.900 geplant. Fremdlast rund 3,6 Kerne, 64 Pods à
1 Kern belegt. C-1+C-2 steckt noch komplett in dim 3 (Systeme 52–57); die erste dim-2-Zelle ab
Warteschlangenposition 121 kommt **später als der in der alten Übergabe genannte 20.09.** — der
Zähler stieg zuletzt um 8 Zellen in 15 Stunden, und die vorderen Positionen sind die teuersten.

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

Erwartet 64 Pods mit je `1` — unsere zwei Jobs — plus die kleinen Pods der Mitbenutzer.
**CPU-Requests zählen, nicht Pods.**

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
2. **Warten.** Kapazitätsplanung, keine Evidenz (Designprinzip 7). Die alte 5-Tage-Angabe stammt vom
   18.09.; der Zähler ist seither langsamer gelaufen als sie unterstellt.
3. **Danach auswerten**, dann Claim D über die Paarung gegen die gerechnete SINDy-Baseline schließen,
   inklusive Trajektorien-Abgleich per Hash.
4. **Nach Kampagnenende:** Baseline-Image bauen, damit ODEFormer laufen kann.

**Während des Laufs verboten:** irgendetwas an der eingefrorenen Konfiguration ändern, und **nicht
nach GitLab pushen** — ein Push baut das Kampagnen-Image neu. Alles seit `221a3a7` liegt nur auf
GitHub.

---

## 4. Der eine offene Befund: die Kappe terminiert nur, wenn sie *alle* Gleichungen kappt

**Stand 20.09., 25 vollständige Paare, alle dim 3, Systeme 52–57.** Ausführlich im `DIARY.md` unter
dem 20.09.; hier die Kurzform und was daraus für die Auswertung folgt.

- **15 Paare ohne Kappe:** `total_loss_evals` und `executed_levels` **15/15 bit-identisch**. Das ist
  eine bestandene Kontrolle — die Arme unterscheiden sich durch die Kappe und sonst nichts.
- **10 Paare mit Kappe** (`[None,3,3]`, `[None,None,3]`): **alle zehn fahren 30/30 Level.** Loss und
  R² sind in **7 von 10 bit-identisch**; die Kostenabweichungen liegen bei 1,3–8,8 % in beide
  Richtungen und sind **kein Befund**.

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

**Beim Auswerten prüfen:** die drei ausstehenden dim-3-Zeilen, dann die 15 voll gekappten dim-2-Zeilen
gegen die 21 nur teilweise gekappten, dann die 32 voll gekappten dim-1-Zeilen. Fällt die Ersparnis
auch bei voller Kappe aus, betrifft das Claim B im Kern.

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

## 5. Was am 18.09. dazugekommen ist

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
