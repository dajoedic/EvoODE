# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-14, 15:45. HEAD siehe `git log -1`. Working Tree sauber.**

---

## 1. Wo wir stehen — in zwei Sätzen

**Die Phase-C-Kampagne läuft, und es gibt nichts zu tun als zu warten.** C-1+C-2 (756 gepaarte
Zellen) rechnet seit dem 14.09. mittags auf Orion, Stand 15:45 **18/756**; C-3 (180 Zellen) ist
**absichtlich angehalten** und wird erst danach gestartet.

**Alle Vorarbeiten sind abgeschlossen.** Bootstrap, Smoke-Test und der 16-Zellen-Pilot sind
bestanden, das Go-Kriterium war grün, und der alte dim-2-Probelauf ist mit 336/336 fertig und
ausgewertet. Es steht **keine Entscheidung offen**, die den Lauf betrifft.

Autoritative Quellen: `PAPER_1.md` → `docs/paper1_phaseC_benchmark_plan.md` → `CLAUDE.md` →
`DIARY.md` (neueste Einträge oben).

---

## 2. Wie du nachschaust

**Voraussetzung: VPN.** Ohne sie ist weder GitLab noch der Cluster erreichbar. Prüfen mit
PowerShell — **nicht** mit `getent` in der Git-Bash, das benutzt einen anderen Resolver und meldet
fälschlich „nicht auflösbar":

```powershell
Resolve-DnsName api.orion.scch.at     # erwartet 172.21.202.100
```

### Fortschritt

```bash
kubectl get jobs -n scch-das
```

Erwartet: `evoode-phase-c-c1-c2-campaign` **Running**, Zähler wächst Richtung 756;
`evoode-phase-c-c3-campaign` **Suspended** 0/180. Der Probelauf-Job `evoode-wp-n1-dim2-campaign`
hat sich am 14.09. selbst abgeräumt und ist weg — das ist korrekt und kein Verlust, die Records
liegen auf der Freigabe.

### Auslastung — der Posten, der schon einmal schiefging

```bash
kubectl -n scch-das get pods -l job-name=evoode-phase-c-c1-c2-campaign --field-selector=status.phase=Running --no-headers | wc -l
```

Erwartet **32** — die Parallelität des Jobs, am 14.09. um 15:45 bestätigt. **Nicht** die Gesamtzahl
der Pods im Namensraum zählen: die Mitbenutzer fahren viele kleine Pods (am 14.09. 45 Pods bei nur
36,55 belegten Kernen), Pods und Kerne sind hier also nicht dasselbe. Wer wissen will, wie viel wir
wirklich belegen, zählt **CPU-Requests**, nicht Pods.

### Ergebnisse, ohne Cluster

```text
S:\BigDataOrion\data-science\joedicke\phase_c_campaign_221a3a72f0cb43164a22b09baac2d9ae82681a02\tasks\
```

**Wenn `S:` nicht da ist** — am 14.09. meldete `net use` das Laufwerk als `Unavailable`, obwohl die
VPN stand —, dann geht derselbe Pfad über UNC ohne jedes Zutun:

```text
\\scch.at\scch\BigDataOrion\data-science\joedicke\...
```

Die Analyseskripte haben `S:` als Vorgabewert einkompiliert, nehmen aber `--input`.

`cell_NNNNNN.jsonl` ist je ein Ergebnis, `*.heartbeat.jsonl` der Verlauf. **Beim Zählen die
Heartbeats ausschließen** — ein Glob auf `cell_*.jsonl` fängt sie mit ein, genau daran ist der
Pilotprüfer einmal gescheitert.

**Fehlerbilder:** `ErrImagePull` heißt Anmeldung, nicht fehlendes Image. `OOMKilled` heißt, die
2 GiB haben nicht gereicht. Beides fiele sonst nicht auf, weil ein hängender Job aussieht wie ein
laufender.

---

## 3. Was als Nächstes ansteht

1. **Warten.** Grob 16–21 Tage für C-1+C-2. Kapazitätsplanung, keine Evidenz (Designprinzip 7);
   die Untergrenze ist die längste **einzelne** Zelle — in Phase B 289,7 h, im ungekappten Arm
   potenziell mehr, weil er die vollen 30 Level fährt.
2. **Danach C-3 fortsetzen** (siehe Abschnitt 4).
3. **Parallel möglich, ohne Cluster:** C-4 (SINDy, Minuten auf dem Laptop), Methoden- und
   Limitations-Abschnitte, das Phase-B-Diagnostikkapitel, Abbildungs- und Tabellengerüste.

**Während des Laufs verboten:** irgendetwas an der eingefrorenen Konfiguration ändern. Eine
Änderung erzwingt eine neue Experiment-Identität.

---

## 4. C-3: angehalten, und warum

**Beide Kampagnen-Jobs stehen einzeln auf `parallelism: 32` — zusammen 64 der 96 Clusterkerne.**
Am 14.09. wurden sie zugleich gestartet, die Belegung lag bei 68,55 Kernen (71 %), und C-3 wurde
binnen Minuten angehalten. Bei 0 von 180 Zellen ging nichts verloren.

Fortsetzen, **erst wenn C-1+C-2 auf 756/756 steht**:

```powershell
kubectl -n scch-das patch job evoode-phase-c-c3-campaign --type=merge --patch-file outputs/k8s_phase_c_221a3a7/resume_c3.json
```

Anhalten geht mit `suspend_c3.json` genauso. **Patch-Dateien statt Inline-JSON**, weil PowerShell
die inneren Anführungszeichen frisst. `kubectl scale job --replicas=0` funktioniert **nicht** —
`jobs/scale` ist für diesen Account nicht freigegeben.

**C-1 und C-2 dürfen nie getrennt werden:** ihre Paarung ist bindend, getrennte Jobs hätten
getrennte Abbruchzeitpunkte und unvollständige Paare.

---

## 5. Zwei Dinge, die beim Auswerten zu prüfen sind

Beide sind **keine offenen Aufgaben**, sondern Merkposten für den Tag, an dem C-1 fertig ist. Die
Herleitung steht im `DIARY.md` unter dem 14.09.

**(a) Hilft k = 3 gegen den Konstanten-Defekt auf dim 2?** Der dim-2-Probelauf lief unter `ec3b6bd`,
also **vor** der Restart-Politik (`4908b07`, Vorgabewert 1) — er ist k = 1, C-1 fährt k = 3. Die
Vermutung, der Einbruch der Strukturtreffer (pruned 55,6 % → 35,2 %) sei ein Artefakt zu weniger
Parameterstarts, ist geprüft und **vermutlich falsch**: der Neustart repariert *gescheiterte* Fits,
auf dim 2 gelingen die Fits aber und treffen nur die falsche Struktur (0 Sentinel-Losses in 336
Zellen, 0 invalide Fits in ~148.000 Fits, R² > 0,9 in beiden Armen identisch 51/54). C-1 enthält
dieselben Systeme, Seeds und IC-Sets wie der Probelauf, der Unterschied ist im Wesentlichen k —
**also beim Auswerten nachsehen.** Zwei Auflagen: anderes Identitätstripel, deshalb **Diagnostik und
niemals eine gemeinsame Tabelle**; und der Git-Hash driftet mit, k ist nicht sauber isoliert. Sauber
wird es nur in der Restart-Ablation über den Orakel-Pfad.

**(b) Der Pilot konnte Claim B nicht prüfen.** In allen acht Paaren waren `executed_levels`,
`final_stage` und `loss` identisch — weil in allen 16 Zellen jede Kappe `nothing` war. Kriterium 4
besteht damit **trivial**. Ursache ist die Auswahlregel „billigstes exaktes System je
Dimensionsklasse": sie trifft genau die Systeme, auf denen die Suche früh endet und die Kappe
belanglos ist. Die Gegenprobe ohne jede Suche (`estimate_stage_caps`, alle 63 Systeme, beide
IC-Sets, beide Basen, `outputs/phase_c_cap_incidence/stage_caps_by_basis.csv`):

| Basis | gekappte Gleichungen | Zellen mit mindestens einer Kappe |
|---|---|---|
| alt | 124 / 234 (53,0 %) | 94 / 126 |
| **kanonisch** | **111 / 234 (47,4 %)** | **83 / 126** |

Je Dimension kanonisch: dim 1 32/46, dim 2 36/56, dim 3 15/20, **dim 4 0/4**. Die Kampagne hat also
Signal für Claim B; der Pilot hatte nur zufällig keines. Zwei deklarationspflichtige Folgen: die
Konstante senkt die Kappenhäufigkeit leicht, und auf dim 4 bindet **keine** Kappe — dort sind C-1
und C-2 strukturell dieselbe Rechnung.

---

## 6. Kleinkram, der sonst untergeht

- **Identität dieser Kampagne:** `git 221a3a72f0cb43164a22b09baac2d9ae82681a02`,
  `config_fingerprint 0c9672de35c75a9d`, Verhaltens-Fingerprint `ffb0266c7913352c`, Basis
  `staged_polynomial_basis_with_constant`, `max_fit_attempts = 3`. Der Bootstrap hat den Fingerprint
  **aus dem Image** gegen den lokalen geprüft — identisch, und `git_dirty = False`.
- **Jobs startet ausschließlich der Nutzer.** Claude sind `kubectl apply`, `patch` und `delete`
  gesperrt („Shared Cluster Mutation"); Claude liest und prüft.
- **Das Deploy-Token läuft nie ab** (`orion-k8s-image-pull`, Scope `read_registry`).
- **Nodes darfst du nicht auflisten** (`Forbidden`). Der Cluster hat laut `docs/hpc_requirements.md`
  96 Kerne auf zwei Knoten (`alnilam01`, `alnilam02`); herleitbar aus
  `kubectl get pods -n scch-das -o custom-columns='NODE:.spec.nodeName'`.
- **Fertige Jobs räumen sich selbst weg** (`ttlSecondsAfterFinished: 3600`). Eine kürzer werdende
  Jobliste heißt „aufgeräumt", nicht „fertig".
- **Codex kann hier kein Julia ausführen.** Julia-Pakete werden geschrieben, als `blocked` gemeldet,
  Claude fährt die Abnahme.
- **Protokollregel seit `221a3a7`:** Fixtures werden aus echten Records **abgeleitet**, nie
  erfunden. Am 14.09. sind vier Arbeitspakete mit grünen Tests an echten Daten umgefallen.
