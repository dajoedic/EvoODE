# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-18 abends. HEAD `a6fc5ec`. Working Tree sauber, nichts uncommittet.**

---

## 1. Wo wir stehen — in zwei Sätzen

**Beide Kampagnen-Jobs rechnen fehlerfrei, und es gibt nichts zu tun als zu warten.** C-1+C-2 steht
bei **44/756**, C-3 bei **8/180**; C-3 wurde am 18.09. vorgezogen, weil die Fremdlast auf dem Cluster
von 36,6 auf 3,4 Kerne gefallen war.

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
**kostenabsteigend**: Positionen 1–120 sind dim 3, 121–456 dim 2, 457–480 dim 4, 481–756 dim 1. Die
44 fertigen Zellen sind **14,7 % der Kosten**, nicht 5,8 %. Am 18.09. wurde daraus einmal eine
Restlaufzeit von 140 Tagen statt der tatsächlichen ~5 Tage. **In Kernstunden rechnen, nie in
Zellen.**

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
   sind (ab Warteschlangenposition 121, also etwa ab dem 20.09.), dieselbe Paartabelle ziehen:
   `stage_caps`, `executed_levels`, `total_loss_evals`. Begründung in Abschnitt 4.
2. **Warten.** Rest grob **5 Tage** für C-1+C-2, C-3 deutlich früher fertig. Kapazitätsplanung,
   keine Evidenz (Designprinzip 7).
3. **Danach auswerten**, dann Claim D über die Paarung gegen die gerechnete SINDy-Baseline schließen,
   inklusive Trajektorien-Abgleich per Hash.
4. **Nach Kampagnenende:** Baseline-Image bauen, damit ODEFormer laufen kann.

**Während des Laufs verboten:** irgendetwas an der eingefrorenen Konfiguration ändern, und **nicht
nach GitLab pushen** — ein Push baut das Kampagnen-Image neu. Alles seit `221a3a7` liegt nur auf
GitHub.

---

## 4. Der eine offene Befund: Claim B hat auf dim 3 kein Signal

Über alle bisher vollständigen Paare, alle dim 3:

- **14 von 19 tragen gar keine Kappe** (`stage_caps == [None, None, None]`); dort sind
  `total_loss_evals` und `executed_levels` zwischen den Armen **bit-identisch**.
- Die 5 Paare **mit** Kappe (`[None, 3, 3]`, Systeme 54 und 56) fahren **in beiden Armen 30 von 30
  Leveln**. Die Kappe terminiert nichts; in einem Fall ist der gekappte Arm minimal teurer.

Plausibler, **unbestätigter** Mechanismus: kappt die Kappe nicht *alle* Gleichungen, läuft die Suche
bis zum Levelbudget weiter — `[None, 3, 3]` lässt Gleichung 1 offen.

**Nicht überinterpretieren.** 19 dim-3-Paare entscheiden nichts, und die suchfreie Gegenprobe
(`outputs/phase_c_cap_incidence/stage_caps_by_basis.csv`) sagt, dass Kappen auf dim 1 (32/46) und
dim 2 (36/56) binden — auf **dim 4 dagegen gar nicht**, dort sind C-1 und C-2 strukturell dieselbe
Rechnung. Findet sich auch auf dim 2 kein Unterschied, betrifft das Claim B im Kern; dann ist zu
klären, ob die Kappe je ein Levelbudget einspart oder nur die Stufe begrenzt.

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
