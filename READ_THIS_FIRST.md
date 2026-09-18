# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-18. HEAD siehe `git log -1`. Working Tree sauber.**

---

## 1. Wo wir stehen — in zwei Sätzen

**Die Phase-C-Kampagne läuft, und es gibt nichts zu tun als zu warten.** C-1+C-2 (756 gepaarte
Zellen) rechnet seit dem 14.09. mittags auf Orion, Stand 18.09. vormittags **41/756**; C-3
(180 Zellen) ist **absichtlich angehalten** und wird erst danach gestartet.

**Die Zellzahl ist irreführend, und zwar systematisch.** Die Warteschlange
(`indices_c1_c2_cost_desc.txt`) ist **nach absteigenden Kosten** sortiert: erledigt und laufend sind
bisher ausschließlich dim-3-Zellen, die 276 dim-1-Zellen stehen ganz hinten. Die 41 Zellen sind
**13,5 % der Gesamtkosten**, nicht 5,4 %. Eine Rate „Zellen pro Tag" hochzurechnen ergibt darum
grob falsche Zahlen — am 18.09. einmal auf 140 Tage danebengegriffen. Nach Kernstunden statt nach
Zellen gerechnet liegt der Lauf **vor** Plan, Rest grob 6 Tage bei `parallelism: 32`. Kapazitäts-
planung, keine Evidenz (Designprinzip 7).

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

1. **Warten.** Grob 6 Tage Rest für C-1+C-2 (Stand 18.09., LPT-Simulation über die Restwarte-
   schlange mit den Phase-B-Kosten je Zelle). Kapazitätsplanung, keine Evidenz (Designprinzip 7);
   die Untergrenze ist die längste **einzelne** Zelle — noch nicht gestartet sind 92 h. Mehr
   Parallelität bringt ab etwa 48 Slots fast nichts mehr, weil dann diese Einzelzelle bindet und
   nicht mehr die Slotzahl.

   **Die Kostenprognose ist am 18.09. gegen die Wirklichkeit geprüft.** Jede der 41 fertigen Zellen
   gegen ihre Phase-B-Messung (gleiches System, Seed, IC-Set, Arm `pretune_off`): Medianfaktor
   **0,83 gekappt / 0,75 ungekappt**, Mittel 0,95 / 0,98. Die Zellen laufen also eher **billiger**
   als das Phase-B-Vorbild, trotz Konstantenbasis und k = 3 — der in `CLAUDE.md` eingeplante
   Aufschlag von +20 % zeigt sich auf dim 3 nicht. Gemessen ist das **nur auf dim 3**; dim 1 und
   dim 2 stehen noch aus.
2. **Danach C-3 fortsetzen** (siehe Abschnitt 4).
3. **Parallel möglich, ohne Cluster:** Methoden- und Limitations-Abschnitte, das
   Phase-B-Diagnostikkapitel, Abbildungs- und Tabellengerüste.

**C-4 (SINDy) ist weitgehend erledigt** — WP-C4a/C4a2, `465ef58` und `a8f45b5`. Gerechnet sind
63 Systeme × 2 IC-Sets × 10 Konfigurationen × 2 Richtungen unter
`analysis/data/paper1_phaseC_v1/phasec_sindy_baseline/`. Offen und **erst mit C-1 möglich**: die
Paarung gegen die echten C-1-Zellen und der Hash-Abgleich der Trajektorien. Letzterer braucht ein
Julia-Paket (WP-C4b), weil **die Records keinen Trajektorien-Hash tragen** — `run_regression.jl`
schreibt keinen, und Claim D verlangt „by hash, not by assertion". Das Hash-Format ist in
`codex/reports/REPORT_WP_C4a.md` so beschrieben, dass die Julia-Seite es nachbilden kann.

**Während des Laufs verboten:** irgendetwas an der eingefrorenen Konfiguration ändern. Eine
Änderung erzwingt eine neue Experiment-Identität.

### Das Pipeline-Audit vom 2026-09-15 — und warum es die Kampagne nicht berührt

`.gitlab-ci.yml` und `containers/Dockerfile` wurden geändert (WP-CI1 bis WP-CI4, siehe
`CHANGELOG.md`): Base-Images über den Harbor-Cache, `workflow: rules`, vier nicht blockierende
Security-Jobs, plus der Ausnahmenkatalog nach §11.1 der SCCH-Pipeline-Policy.

**Die laufende Kampagne ist davon nicht betroffen**, und zwar aus zwei voneinander unabhängigen
Gründen: Das Job-Manifest pinnt einen festen Image-SHA, und ein Bau wird ohnehin nur durch einen
Push nach **GitLab** ausgelöst — der letzte war `221a3a7` vom 14.09. Alles seither liegt nur auf
GitHub.

**Daraus folgt aber eine Vorsichtsregel:** Der nächste Push nach GitLab baut ein Image, das auf
einem anderen Basis-Bezug beruht als das der laufenden Kampagne. Solange C-1+C-2 rechnet, nicht
nach GitLab pushen — und wenn doch, das Kampagnen-Manifest nicht auf den neuen SHA umstellen.

Die Wirksamkeit der Pipeline-Änderungen ist **ungeprüft**; sie zeigt sich erst beim ersten
bewussten GitLab-Push. Zwei Fehlerarten wären dabei still: ein Tippfehler in `workflow: rules`
(gar keine Pipeline) und ein unbekannter Component-Input (Include abgelehnt, ebenfalls keine
Pipeline). Beide wurden statisch geprüft — Inputs gegen die Komponenten-Repositories, Auslöserwerte
gegen die GitLab-Dokumentation —, aber statisch ist nicht gelaufen.

**Offen, bewusst zurückgestellt:** §9.2, also Multi-Stage-Dockerfile und non-root. Das ist der
einzige verbliebene mandatory-Punkt und fasst den Bauweg des Kampagnen-Images an — erst nach der
Kampagne.

---

## 4. C-3: angehalten, und warum

**Beide Kampagnen-Jobs stehen einzeln auf `parallelism: 32` — zusammen 64 der 96 Clusterkerne.**
Am 14.09. wurden sie zugleich gestartet, die Belegung lag bei 68,55 Kernen (71 %), und C-3 wurde
binnen Minuten angehalten. Bei 0 von 180 Zellen ging nichts verloren.

**Der Aufräumschritt ist hinfällig — hier stand bis zum 18.09. das Gegenteil.** Der abgebrochene
Start hat für die Zellen **883–914** je 3–18 Heartbeat-Zeilen hinterlassen (32 Dateien, kein
Ergebnis; die früher notierten „3–6" waren zu niedrig, Zelle 883 kam bis Level 17). Der Runner
schreibt anhängend (`run_regression.jl:520`), und der Leser verschmolz beide Läufe einmal zu einer
Reihe mit doppelten Levelnummern. **Genau das hat WP-C5 am 15.09. repariert** (`35366c3`):
`read_heartbeat` trennt an `start`-Ereignissen und wählt mit
`findlast(segment -> !isempty(segment.levels), ...)` das **letzte** Segment mit Level-Ereignissen
(`analyze_wasted_search_levels.jl:108–158`). Der angehängte echte C-3-Lauf gewinnt also, die Reste
werden verworfen und gezählt. **Nichts ist vorher zu tun.**

**Und verschieben ginge ohnehin nicht.** Die Freigabe ist über SMB **nur lesbar**: die ACL auf
`tasks` gibt `SCCH\Domain Users` und `Everyone` nur `ReadAndExecute`, `FullControl` hat allein
`S-1-22-1-0` — die NFS-Kennung, unter der die Pods schreiben. Am 18.09. scheiterten sowohl Git Bash
als auch PowerShell mit `UnauthorizedAccessException`, auch ohne Sandbox. Wer die Reste wirklich
beiseiteräumen will, braucht einen Pod, der die Freigabe über NFS einhängt. Lohnt nicht.

**Der Grund, C-3 angehalten zu lassen, ist am 18.09. entfallen.** Er war Kapazität: am 14.09.
lagen 68,55 Kerne (71 %) belegt. Inzwischen ist die Fremdlast im Namensraum von 36,55 auf **~3,4
Kerne** gefallen — mit unseren 32 sind rund **60 der 96 Kerne frei**, C-3 käme auf ~67. Die
ursprüngliche Auflage „erst wenn C-1+C-2 auf 756/756 steht" ist damit sachlich überholt; sie war nie
eine wissenschaftliche Bedingung, sondern eine Rücksicht auf Mitbenutzer. Die Belegung vor dem
Fortsetzen trotzdem neu zählen — **nach CPU-Requests, nicht nach Pods** (§2).

Fortsetzen:

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

**(c) Auf dim 3 hat Claim B bisher null Signal — nachzählen, sobald dim 2 anläuft (18.09.).** Die
ersten 19 vollständigen Paare der Kampagne, alle dim 3, sehen so aus:

- **14 von 19 Paaren haben gar keine Kappe** (`stage_caps == [None, None, None]`, Systeme 52, 53,
  57). Dort sind `total_loss_evals` und `executed_levels` zwischen den Armen **bit-identisch** —
  erwartbar, aber es heißt eben auch: kein Beitrag zu Claim B.
- Die 5 Paare **mit** Kappe (`[None, 3, 3]`, Systeme 54 und 56) fahren **in beiden Armen 30 von 30
  Leveln**. Die Kappe terminiert nichts. In einem Fall ist der gekappte Arm sogar minimal teurer
  (5.692.463 gegen 5.602.929 Evaluationen).

Der Mechanismus ist plausibel und sollte beim Auswerten bestätigt werden: kappt die Kappe nicht
*alle* Gleichungen, läuft die Suche bis zum Levelbudget weiter — `[None, 3, 3]` lässt Gleichung 1
offen. Das ist schärfer als (b): dort waren alle Kappen `nothing`, hier sind Kappen **vorhanden und
wirkungslos**.

**Nicht überinterpretieren.** 19 dim-3-Paare entscheiden nichts, und die Gegenprobe oben sagt, dass
Kappen auf dim 1 (32/46) und dim 2 (36/56) binden — genau die Zellen stehen noch aus, ab Position 74
der Warteschlange. **Zu tun:** sobald die ersten dim-2-Zellen fertig sind, dieselbe Paartabelle
(`stage_caps`, `executed_levels`, `total_loss_evals`) nachziehen. Findet sich dort ebenfalls kein
Unterschied, ist das keine Kleinigkeit, sondern betrifft Claim B im Kern — dann ist vor dem
Weiterrechnen zu klären, ob die Kappe überhaupt je ein Levelbudget einspart oder nur die Stufe
begrenzt.

**Folge für die Kostenplanung:** die Annahme aus `CLAUDE.md`, „der ungekappte Spiegel trägt den
Großteil der Kosten", trifft auf dim 3 nicht zu — beide Arme kosten dort praktisch gleich viel. Das
ist der Grund, warum die Gesamtprognose jetzt unter dem geplanten Band liegt.

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
