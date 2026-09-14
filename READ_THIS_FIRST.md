# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-14, 11:13. HEAD = `221a3a7`. Working Tree sauber.**

---

## 1. Wo wir stehen — in drei Sätzen

**Phase C ist gebaut und der Start läuft gerade ab.** Alle Voraussetzungen (P1–P9) und alle
Arbeitspakete (B1–B7) sind erledigt; die kanonische Basis ist seit 2026-09-13 eingefroren
(`staged_polynomial_basis_with_constant`). Bootstrap und Smoke-Test auf dem Cluster sind **bestanden**,
der **16-Zellen-Pilot läuft**; besteht er das Go-Kriterium, wird die Kampagne gestartet.

Autoritative Quellen: `PAPER_1.md` → `docs/paper1_phaseC_benchmark_plan.md` → `CLAUDE.md` →
`DIARY.md` (neueste Einträge oben).

---

## 2. Wie du selbst nachschaust

**Voraussetzung: VPN muss verbunden sein.** Ohne VPN ist weder GitLab noch der Cluster erreichbar.
Prüfen (PowerShell, **nicht** `getent` in der Git-Bash — das benutzt einen anderen Resolver und
meldet fälschlich „nicht auflösbar"):

```powershell
Resolve-DnsName api.orion.scch.at
```

Kommt `172.21.202.100`, steht die VPN.

### Was läuft gerade?

```bash
kubectl get jobs -n scch-das
```

Erwartet am 14.09. um 11:13:

| Job | Stand |
|---|---|
| `evoode-phase-c-bootstrap-campaign` | **Complete** 1/1 |
| `evoode-phase-c-indexed-smoke` | **Complete** 3/3 |
| `evoode-phase-c-p9-pilot` | **Running 8/16** ← darauf warten wir |
| `evoode-wp-n1-dim2-campaign` | Running 335/336 (alter Probelauf, blockiert nichts) |

### Wie weit ist der Pilot?

```bash
kubectl get pods -n scch-das -l app.kubernetes.io/component=p9-pilot
```

Alle 16 Zellen laufen **gleichzeitig** (`parallelism: 16`), es gibt also keine Warteschlange: die
Gesamtdauer ist die der langsamsten Zelle — vermutlich System 52 im ungekappten Arm.

**Woran du einen Fehlschlag erkennst:** `ErrImagePull` oder `ImagePullBackOff` heißt Anmeldung,
nicht fehlendes Image. `OOMKilled` heißt, die 2 GiB Speichergrenze hat nicht gereicht. `Completed`
bei allen 16 heißt fertig.

### Ergebnisse ansehen — ohne Cluster, direkt auf dem Share

```text
S:\BigDataOrion\data-science\joedicke\phase_c_campaign_221a3a72f0cb43164a22b09baac2d9ae82681a02\
```

Dort liegen `manifest.csv` (936 Zeilen) und die Indexlisten. Die **Pilot-Records** landen im
Unterordner der Job-Ausgabe; `cell_NNNNNN.jsonl` ist je ein Ergebnis, `*.heartbeat.jsonl` der
Verlauf.

---

## 3. Der Startablauf — wo wir darin stehen

| Schritt | Was | Stand |
|---|---|---|
| 1 | VPN verbinden | erledigt |
| 2 | Push nach GitHub und GitLab, Image-Build | erledigt, Image `221a3a72f0cb43164a22b09baac2d9ae82681a02` |
| 3 | Manifeste mit Hash rendern, gegen Cluster-API prüfen | erledigt, `outputs/k8s_phase_c_221a3a7/` |
| 4 | Bootstrap-Job | **bestanden** — Fingerprint aus dem Image = `0c9672de35c75a9d`, identisch mit lokal |
| 5 | Smoke-Job, 3 Zellen | **bestanden** — alle Prüfpunkte, `git_dirty = False` |
| 6 | Pilot, 16 Zellen | **läuft** |
| 7 | Go-Kriterium | offen, Kommandos unten |
| 8 | Kampagne starten | offen |

**Jobs startet ausschließlich der Nutzer** — Claude ist `kubectl apply` gesperrt
(„Modify Shared Resources"). Claude prüft.

---

## 4. Der nächste Schritt: Schritt 7, das Go-Kriterium

Sobald der Pilot **16/16 Complete** meldet, in dieser Reihenfolge:

**(a) Die 16 Records zu einer Datei zusammenführen.** `wp_n5_ic_generalization.jl` erwartet **eine**
`history.jsonl`, der Pilot schreibt aber eine Datei je Zelle.

**(b) Julia-Lauf für Kriterium 5** — baut jedes Modell aus seinem Record neu auf und muss die eigene
Rekonstruktion **exakt auf null** reproduzieren:

```powershell
julia --project=. --startup-file=no studies/regression/wp_n5_ic_generalization.jl --input <history.jsonl> --output-dir outputs/phase_c_pilot_probe
```

**(c) Das Go-Kriterium selbst:**

```powershell
python analysis/scripts/aggregate/verify_phasec_p9_pilot.py --records-dir <Pilot-tasks> --manifest <NFS manifest.csv> --reconstruction-probe outputs/phase_c_pilot_probe/reconstruction_probe.csv --expected-git-hash 221a3a7 --expected-stage-cap-behavior-fingerprint ffb0266c7913352c
```

**Exit 0 = Start frei.** Das Skript nennt bei Fehlschlag Kriterium **und** Zelle.
**Kriterium 4 oder 5 rot ist ein harter Stopp**: 4 entwertet Claim B, 5 entwertet Claim C — beide
sind jetzt billig zu finden und nach 12.300 Kernstunden nicht mehr.

### Danach Schritt 8 — die Kampagne

```bash
kubectl apply -f outputs/k8s_phase_c_221a3a7/phase_c_c1_c2_campaign_job.yaml
kubectl apply -f outputs/k8s_phase_c_221a3a7/phase_c_c3_campaign_job.yaml
```

Erst C-1+C-2 (756 Zellen, gepaart), dann C-3 (180). **Nicht in einen Job zusammenlegen:** C-1 und
C-2 teilen sich einen Job, weil ihre Paarung bindend ist; C-3 läuft getrennt, damit er streichbar
bleibt.

---

## 5. Was zu erwarten ist

**Dauer der Kampagne: grob 16–21 Tage** bei `parallelism: 32` (12.300–15.900 Kernstunden / 32).
Das ist Kapazitätsplanung, **keine Evidenz** (Designprinzip 7). Die Untergrenze ist die **längste
einzelne Zelle**, weil eine Zelle nicht teilbar ist — in Phase B waren das 289,7 h, im ungekappten
Arm kann es mehr sein.

**Der Lauf blockiert die Paperarbeit nicht.** Parallel möglich: C-4 (SINDy, rechnet in Minuten auf
dem Laptop), die Methoden- und Limitations-Abschnitte, das Phase-B-Diagnostikkapitel, Abbildungs-
und Tabellengerüste. Es warten nur die Haupttabellen und die abgeleiteten Arme C-5.

**Während des Laufs verboten:** irgendetwas an der eingefrorenen Konfiguration ändern. Eine
Änderung erzwingt eine neue Experiment-Identität.

---

## 6. Eine offene Beobachtung, die beim Piloten zu prüfen ist

Im Smoke-Test stoppten **alle drei Arme** bei Level 1 mit identischem Loss — System 1 ist unter der
konstanten Basis exakt lösbar, die Suche endet also, weil sie fertig ist. Das ist kein Defekt, aber
es heißt: **der Smoke-Test prüft den Pfad, nicht das Verhalten.**

Beim Piloten ist deshalb gezielt zu schauen, ob sich `executed_levels` zwischen gekapptem und
ungekapptem Arm auf den schwereren Systemen (24, 52, 63) **tatsächlich unterscheidet**. Stünde
überall dieselbe Zahl, wäre Kriterium 4 zwar formal grün, aber Claim B hätte kein sichtbares Signal
— das muss vor dem Start der Kampagne geklärt sein, nicht nachher.

---

## 7. Kleinkram, der sonst untergeht

- **Zelle 293 des alten dim-2-Probelaufs** hing gestern 20:33 UTC bei Level 28/30. Sie ändert nur
  einen R²-Nenner der WP-N15-Auswertung. Wenn sie fertig ist: die Auswertung ohne
  `--allow-incomplete` laufen lassen.
- **Das Deploy-Token läuft nie ab** (`orion-k8s-image-pull`, Scope `read_registry`). Die frühere
  Warnung vor einem Ablauf mitten im Lauf ist damit gegenstandslos.
- **Nodes darfst du nicht auflisten** (`Forbidden`). Der Cluster hat laut
  `docs/hpc_requirements.md` **96 Kerne auf zwei Knoten** (`alnilam01`, `alnilam02`); herleiten
  lässt sich das aus `kubectl get pods -n scch-das -o custom-columns='NODE:.spec.nodeName'`.
- **`parallelism: 32`** ist bewusst gewählt — ein Drittel des Clusters, fest reserviert
  (`requests == limits`). Vor dem Start prüfen, ob der Moment günstig ist:
  `kubectl -n scch-das get resourcequota,limitrange` (erwartet: nichts) und die Auslastung der
  Mitbenutzer. Am 14.09. um 10:15 waren es 4,55 Kerne.
- **Codex kann hier kein Julia ausführen.** Julia-Pakete werden geschrieben, als `blocked` gemeldet,
  Claude fährt die Abnahme.
- **Neue Protokollregel seit `221a3a7`:** Fixtures werden aus echten Records **abgeleitet**, nie
  erfunden. Drei Arbeitspakete sind am 14.09. mit grünen Tests an echten Daten umgefallen.
