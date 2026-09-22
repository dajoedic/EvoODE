# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-22. Working Tree sauber bis auf diese Datei.**

---

## 1. Wo wir stehen — in zwei Sätzen

**Beide Jobs rechnen fehlerfrei, und die Kappen-Vorhersage ist eingetroffen.** Stand 22.09.:
C-1+C-2 bei **184/756**, C-3 bei **171/180**. 355 Records, **0 Fehler**, ein Identitätstripel über
alle, 5.874 verbrauchte Kernstunden.

Der Sprung von 249 auf 355 Records über Nacht ist die Parallelitätserhöhung vom 21.09. (32 → 64).
**Folge fürs Auswerten unverändert:** ab Zelle 80 laufen doppelt so viele Pods pro Node, `elapsed_s`
ist deshalb nicht mit den ersten 79 Zellen vergleichbar. Wissenschaftlich folgenlos
(Designprinzip 7), aber deklarationspflichtig, wo `elapsed_s` als Kontext auftaucht.

**Die dim-2-Zellen sind angelaufen** — damit existiert zum ersten Mal die Zellklasse, die Claim B
testet. Ergebnis in Abschnitt 4. **Es steht keine Entscheidung offen, die den Lauf betrifft.**

Laufender Stand auch als Seite: <https://claude.ai/artifact/4sq6HhRsnxgrFVqVF2trBx> — im README
verlinkt, wird bei Statuswechseln neu veröffentlicht. **Noch nicht auf den 22.09. aktualisiert.**

Autoritative Quellen: `PAPER_1.md` → `docs/paper1_phaseC_benchmark_plan.md` → `CLAUDE.md` →
`DIARY.md` (neueste Einträge oben).

---

## 2. Wie du nachschaust

**Voraussetzung: VPN.** Prüfen mit PowerShell — **nicht** mit `getent` in der Git-Bash, das benutzt
einen anderen Resolver und meldet fälschlich „nicht auflösbar":

```powershell
Resolve-DnsName api.orion.scch.at     # erwartet 172.21.202.100
```

**Neu am 22.09.: ein nicht erreichbares `S:` heißt nicht zwangsläufig „VPN weg".** Die Freigabe war
abgehängt, während das VPN stand. Zurückgeholt mit:

```powershell
net use S: /delete /y
net use S: \\scch.at\scch
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
**kostenabsteigend**: Positionen 1–120 sind dim 3, 121–456 dim 2, 457–480 dim 4, 481–756 dim 1.
Die Reihenfolge ist **nicht strikt** — bei 64 Arbeitern starten Positionen ab 121, während teure
dim-3-Zellen noch laufen. Bei 184 fertigen Zellen waren 84 davon dim 3 und 100 dim 2, es fehlen
also noch 36 dim-3-Nachzügler. **In Kernstunden rechnen, nie in Zellen.**

### Auslastung

```powershell
$p = kubectl -n scch-das get pods --no-headers
($p | Select-String " Running ").Count      # 22.09.: 85, davon 64 C-1+C-2, 9 C-3, 12 fremd
($p | Select-String " Pending ").Count      # muss 0 sein
```

**CPU-Requests zählen, nicht Pods.** Keine ResourceQuota im Namespace; es begrenzt allein die
Node-Kapazität von 96 Kernen. Reicht sie nicht, werden Pods **Pending** — der harmlose Fehlermodus.

### Ergebnisse, ohne Cluster

```text
S:\BigDataOrion\data-science\joedicke\phase_c_campaign_221a3a72f0cb43164a22b09baac2d9ae82681a02\tasks\
```

`cell_NNNNNN.jsonl` ist je ein Ergebnis, `*.heartbeat.jsonl` der Verlauf — **beim Zählen die
Heartbeats ausschließen.** Die Freigabe ist über SMB **nur lesbar**: `FullControl` hat allein die
NFS-Kennung, unter der die Pods schreiben.

**Fehlerbilder:** `ErrImagePull` heißt Anmeldung, nicht fehlendes Image. `OOMKilled` heißt, die
2 GiB haben nicht gereicht.

---

## 3. Was als Nächstes ansteht

1. **Warten.** Offen sind 36 dim-3-Zellen (Median 47,2 h, es sind die teuren Nachzügler), 236
   dim-2-Zellen (Median 2,47 h) sowie dim 4 und dim 1. Grob **~3.000 Kernstunden**, also 2 bis 3
   Tage — Kapazitätsplanung, keine Evidenz (Designprinzip 7). **Die Restlaufzeit hängt an der
   längsten Einzelzelle, nicht am Durchsatz.**
   Nebenrechnung: 5.874 verbraucht plus ~3.000 Rest ergibt **~8.900 Kernstunden gegen die geplanten
   12.300–15.900**. Die Planzahl war konservativ — beim Schreiben so sagen, sonst wird sie als
   Messwert zitiert.
2. **Die Kappenauswertung nachziehen, sobald mehr voll gekappte Paare da sind** — die 15 voll
   gekappten dim-2-Zeilen der suchfreien Gegenprobe sind erst teilweise gepaart, die 32 dim-1-Zeilen
   gar nicht. Fünf Systeme sind fünf Cluster; die Zahlen in Abschnitt 4 sind Zwischenstand.
3. **Danach auswerten**, dann Claim D über die Paarung gegen die gerechnete SINDy-Baseline schließen,
   inklusive Trajektorien-Abgleich per Hash.
4. **Nach Kampagnenende:** Baseline-Image bauen, damit ODEFormer laufen kann.

**Während des Laufs verboten:** irgendetwas an der eingefrorenen Konfiguration ändern, und **nicht
nach GitLab pushen** — ein Push baut das Kampagnen-Image neu. Alles seit `221a3a7` liegt nur auf
GitHub.

---

## 4. Claim B ist getestet, und die Vorhersage hat gehalten

Ausführlich im `DIARY.md` unter dem 22.09.; hier die Kurzform.

Die am 20.09. **vor der Messung** datierte Einzelvorhersage lautete: der ungekappte Partner von
System 60 / IC 2 / Seed 123 erreicht Stufe 5 und fährt deutlich mehr als 14 Level.

```text
System 60, IC 2, Seed 123, stage_caps [3,3,2]
  gekappt:    14 Level, Endstufe 3,  3.098.076 loss evals
  ungekappt:  22 Level, Endstufe 5,  5.336.451 loss evals
```

Getroffen. Dazu **21 voll gekappte Paare** auf fünf Systemen (26, 27, 29, 31, 60), 89 vollständige
Paare insgesamt:

| Kappenklasse | dim | n | identisch | gekappt billiger | teurer | evals cap/unc |
|---|---|---|---|---|---|---|
| keine | 2 | 24 | **24** | 0 | 0 | 1,000 |
| keine | 3 | 15 | **15** | 0 | 0 | 1,000 |
| teilweise | 2 | 5 | 5 | 0 | 0 | 1,000 |
| teilweise | 3 | 24 | 7 | 2 | 15 | 1,013 |
| **voll** | **2** | **20** | 1 | **19** | 0 | **0,727** |
| **voll** | **3** | **1** | 0 | **1** | 0 | **0,581** |

Gepoolt über die 21 voll gekappten Paare: **28,3 % Ersparnis** an `total_loss_evals`, Ratio pro Paar
0,521 / **0,634** / 1,000. Das einzige Paar ohne Ersparnis ist System 27 Seed 7 IC 1, wo **auch der
ungekappte Arm bei Stufe 3 endet** — derselbe Mechanismus von der anderen Seite, kein Gegenbeispiel.

**Bei unverändertem Ergebnis:** `pruned_match` in **21/21** gleich, R² in **16/21** bitidentisch,
größte Abweichung 0,0045 (System 27 Seed 123 IC 1), einmal ist der gekappte Arm besser.

**Die Kontrolle hält:** die inzwischen **39 kappenlosen Paare sind 39/39 bitidentisch** in
`total_loss_evals` und `executed_levels`.

**Der Mechanismus steht im Code.** `_effective_max_stage` (`src/structure/evogrow.jl:141-144`) bildet
das **Maximum** über die Kappen; eine offene Gleichung hält das volle Stufenbudget für alle offen.
Claim B lautet deshalb präzise: **die Kappe spart genau dann, wenn sie alle Gleichungen kappt.** Wie
oft das eintritt, sagt die suchfreie Gegenprobe (`outputs/phase_c_cap_incidence/stage_caps_by_basis.csv`):
dim 1 **32/46**, dim 2 **15/56**, dim 3 **3/20**, dim 4 **0/4**. Ersparnis real und messbar, aber auf
einen Minderheitenfall beschränkt — **beides gehört in denselben Satz.**

**Nicht an der Kappe drehen.** Aggressiver kappen hieße, auf die Abwesenheit von Evidenz zu kappen
(vom System-63-Defekt ausgeschlossen); die Schwellen nachziehen ist der WP-V1-Fehler. Der Hebel ist
die **Granularität der Terminierung** — gekappte Gleichungen einfrieren statt nur ihre Terme
begrenzen. **Paper 2, nicht jetzt**, und zu messen statt zu behaupten.

**Instrumentierungslücke:** im ungekappten Arm sind `eq_final_stages`, `stage_caps` und
`eq_overshoot` nicht befüllt; nur `final_stage` existiert, und das ist das Maximum über die
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
  Lauf gewinnt.
- **`baselines/`** — Harness, die Fremdmethoden auf **unseren** 126 exportierten Trajektorien
  rechnet, mit Hashprüfung als Abbruchbedingung und gespeicherten Koeffizienten. `odeformer` ist
  **gepinnt** (`c9193012`), nicht einkopiert; eigenes Python-3.9-Image; `containers/Dockerfile`
  unberührt. SINDy läuft, ODEFormer wartet aufs Image. WP-N19 / WP-N19b.
- **Zwei Entscheidungen vor der Messung eingefroren**, beide in
  `docs/paper1_phaseC_benchmark_plan.md`: **§6a** — Methodenkosten sind *strukturell*, Zeit ist
  sekundär und deklarationspflichtig. **§6b** — beide R²-Aggregationen werden berichtet, die
  varianzgewichtete trägt das Etikett Literaturvergleich, **weil** sie ODEBench' Definition ist.
- **WP-N20**: die varianzgewichtete Aggregation ist aus vorhandenen Records rekonstruierbar, ohne
  Neulauf. Über die volle Phase-B-Kampagne: **53 von 756 Zellen kippen über die 0,9-Schwelle, alle
  53 nach oben, 0 nach unten.** Kontrolle in 756/756 bestanden.
- **README korrigiert** — er führte die auf Diagnostik herabgestufte Phase B noch als „die Evidenz".

---

## 6. Kleinkram, der sonst untergeht

- **Identität dieser Kampagne:** `git 221a3a72f0cb43164a22b09baac2d9ae82681a02`,
  `config_fingerprint 0c9672de35c75a9d`, Verhaltens-Fingerprint `ffb0266c7913352c`, Basis
  `staged_polynomial_basis_with_constant`, `max_fit_attempts = 3`. Am 22.09. über alle 355 Records
  geprüft: ein Tripel, `git_dirty` nirgends.
- **Jobs startet ausschließlich der Nutzer.** Claude sind `kubectl apply`, `patch` und `delete`
  gesperrt; Claude liest und prüft.
- **`codex exec` braucht im Auto-Modus eine `allow`-Regel**, sonst scheitert die Übergabe **still**.
  Die Regel steht in `.claude/settings.json`, die ignoriert ist und daher nur auf diesem Rechner
  lebt; die Anforderung ist in `codex/CODEX_PROTOCOL.md` dokumentiert. **Claude darf sie nicht selbst
  setzen** — das blockt der Auto-Modus als Self-Modification, zu Recht.
- **Codex kann hier kein Julia ausführen.** Julia-Pakete werden geschrieben, als `blocked` gemeldet,
  Claude fährt die Abnahme. Python läuft normal.
- **Nodes darfst du nicht auflisten** (`Forbidden`). 96 Kerne auf `alnilam01` / `alnilam02`.
- **Fertige Jobs räumen sich selbst weg** (`ttlSecondsAfterFinished: 3600`). Eine kürzer werdende
  Jobliste heißt „aufgeräumt", nicht „fertig".
- **Protokollregel:** Fixtures werden aus echten Records **abgeleitet**, nie erfunden. Grüne Tests
  an erfundenen Daten haben schon mehrere Arbeitspakete durchgewinkt, die an echten Daten umfielen.
- **Eine deklarierte, ungeprüfte Annahme** (§6b): die Gewichte der Phase-B-Auswertung stammen aus
  dem **Phase-C**-Trajektorienexport, weil Phase Bs eigene Trajektorien nicht versioniert sind. Das
  Protokoll ist identisch, also sollten es dieselben Zahlen sein — geprüft ist es nicht.
