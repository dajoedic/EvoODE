# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon. Alles Dauerhafte gehört dorthin, nach `PAPER_1.md` oder ins `DIARY.md` —
**nicht hierher.**

**Regeln:** wird immer **vollständig überschrieben**, nie angehängt. Was älter als ein paar Tage
ist, ist vermutlich falsch — dann gilt `CLAUDE.md`.

**Stand: 2026-09-22, 23:55.**

---

## 1. Der nächste Handgriff

**Der Nutzer startet HPC-Jobs selbst** (Regel wieder in Kraft seit 2026-09-22 spät abends; die
Delegation an Claude galt nur für diesen einen Abend). Claude bereitet vor und prüft, führt aber
kein `oc apply` mehr aus.

Zwei Befehle stehen aus. Die Manifeste liegen substituiert unter `outputs/k8s_wp_t1e/`
(gitignoriert, überlebt Sitzungen), alle auf Image
`evoode:5a87efb3438ef459f57e28fca9fde8564b97217f`.

**Schritt 1 — Smoke, zwei Zellen, wenige Minuten:**

```powershell
oc apply -f outputs\k8s_wp_t1e\wp_t1e_indexed_smoke_job.yaml
oc get job evoode-wp-t1e-indexed-smoke -o custom-columns="JOB:.metadata.name,SUCCEEDED:.status.succeeded,FAILED:.status.failed"
```

Pass-Kriterium `SUCCEEDED = 2`. **Danach prüft Claude die Records**, bevor Schritt 2 kommt.

**Schritt 2 — der Lauf, 36 Zellen, `parallelism: 2`, ~5–6 h. Erst nach Abnahme des Smoke:**

```powershell
oc apply -f outputs\k8s_wp_t1e\wp_t1e_indexed_campaign_job.yaml
```

## 2. Wer was macht

Claude kann die Freigabe `S:\BigDataOrion\data-science\joedicke\` **lesen** und `oc` für
Statusabfragen benutzen. Prüfen, auswerten, committen macht also Claude. Der Nutzer muss nur die
zwei `oc apply` oben ausführen — und die GitLab-Pipeline ansehen, falls ein Bau scheitert, denn
`glab` fehlt und die Registry verweigert Docker den Lesezugriff.

## 3. Was heute Abend auf dem Cluster passiert ist

| | |
|---|---|
| WP-T1e lokal verifiziert | 188 + 3 Tests, Smoke über 4 Zellen |
| Commit + Push | `10ba7ad`, dann CI-Fix `5a87efb` |
| **Erster Bau scheiterte** | `blob unknown to registry` beim Manifest-Push |
| Ursache | BuildKit hängt eine Provenance-Attestation an → OCI-Index, den die Registry ablehnt |
| Fix | `--provenance=false --sbom=false` + `BUILDX_NO_DEFAULT_ATTESTATIONS: "1"` |
| Zweiter Bau | **Passed**, 35:17 |
| Bootstrap-Job | **fertig** — 36 Indizes, `cell_index_map.csv` geprüft |

**Die eigentliche Ursache ist der gleitende Tag `docker:29-dind`.** Ein Versionssprung darin hat
Attestationen eingeschaltet. Der Fix behandelt das Symptom; das Pinnen auf eine exakte Version
steht als Folgeaufgabe im `CHANGELOG.md`.

## 4. Die zwei fehlgeschlagenen Sicherheitsjobs — angesehen, nicht erledigt

In Pipeline #8379 (`5a87efb3`) sind **`trivy-fs` und `trivy-image` fehlgeschlagen**, beide mit
`allow-failure: true`, die Pipeline ist also grün. `python-sast` und `python-dependency-vuln` sind
durchgelaufen.

**Das sind die ersten echten Ergebnisse dieser Jobs überhaupt.** Sie wurden am 2026-09-15
hinzugefügt, der letzte erfolgreiche Bau davor war `221a3a7` vom 2026-09-14 — seither wurde die
`security`-Stage jedes Mal übersprungen, weil `build` scheiterte.

**Vermutliche Bedeutung, nicht verifiziert:** bei Trivy ist ein Fehlercode das vorgesehene Signal
für Funde, nicht für einen Werkzeugfehler. Beide laufen mit `severity: HIGH,CRITICAL`.
`trivy-image` (47 s) scannt das Debian-basierte Julia-Image, `trivy-fs` (21 s) das Repository,
wo die gepinnten Python-Abhängigkeiten der wahrscheinlichste Kandidat sind. Ein reiner
Konfigurationsfehler ist ohne Blick ins Log nicht ausgeschlossen — beide Laufzeiten sind kurz.

**Zu tun, wenn Ruhe ist:** Logs ansehen, und falls es echte Funde sind, eine Zeile ins
`CHANGELOG.md` — §11.1 will dokumentierte Abweichungen im Projekt haben. **Blockiert nichts**, der
Container läuft intern und die Jobs sind bewusst nicht-blockierend eingerichtet.

## 5. Was heute committet wurde

| Commit | Inhalt |
|---|---|
| `700a685` / `2eb54e6` | DIARY: Seitenzweig umgehängt — Strukturtreffer statt Compute |
| `ae7573d` / `b4498f6` | WP-T1: Term-Relevanz, Gate **positiv** |
| `139dd89` | Paper-Bogen umgebaut, `PAPER_TIMELINE.md` eingearbeitet |
| `32c7989` / `401e07f` | DIARY: vier Bogen-Entscheidungen, Grenzen-Rahmung behalten |
| `10a809c` / `75baed6` | WP-T1b: Standalone-Rangliste, Deutung **C** |
| `58cb17a` / `0701cf6` | DIARY: WP-T1b und die Kreuzprüfung |
| `0dc79cc` / `5a6a447` | Seitenzweig eingefroren, T1d-Kosten korrigiert |
| `25e4ad5` | WP-T1c: **kein Gewinner**, `forward` bleibt |
| `a9a9471` / `bf5d353` | Kampagnen-Image dokumentiert, Prüfbefehl im Guide §6b |
| `c6d714e` | 8-Stunden-Regel in `CLAUDE.md` |
| `10ba7ad` | WP-T1d/T1e: Nachbarschaftssonde, repariert, begrenzt, shardbar |
| `5a87efb` | CI-Fix: keine Build-Attestationen mehr, CHANGELOG nach §11.1 |

**GitHub ist nicht gepusht** — dort liegen die Commits für den Nutzer.

## 6. Die Kampagne, unberührt

C-1/C-2 bei 226 Zellen, C-3 bei 171, beide auf `:221a3a72f0cb…`. Der Push konnte sie nicht
erreichen: neuer SHA-Tag, `:main` wandert ins Leere, und die CI hat keinen Deploy-Schritt.
Prüfbefehl in `docs/hpc_deployment_guide.md` §6b.

## 7. Der Stand des Seitenzweigs

Eingefrorene Liste in `docs/phd_thesis_arc.md` §5. Schritte 0–2 abgeschlossen:

- **WP-T1** — Signal vorhanden, Median `n_false_before_last_true` = 0,0 auf dim 2+3
- **WP-T1b** — ersetzt die Suche **nicht** (Deutung C)
- **WP-T1c** — **kein Gewinner**, `forward` bleibt Prioritätsgeber
- **WP-T1d** — läuft gerade an: ist der wahre Träger ein lokales Optimum unseres Loss?

Entscheidende Klasse ist `swap_one` bei gleicher Größe. `add_one` zu gewinnen ist Verschachtelung,
kein Befund. Die drei Klassen werden nie zu einer Kennzahl verrechnet.

## 8. Offene Entscheidungen

1. **Rauschzuschnitt von Paper 1** — größter unbudgetierter Posten, `docs/phd_thesis_arc.md` §3/§11
2. **Prädiktives Kriterium für Kappen-Versagen** — hat unter Claim A–D keinen Besitzer
3. **Was WP-T2a wird** — hängt an WP-T1ds Ausgang
4. **`docker:29-dind` pinnen** und eine Registry-Cleanup-Policy — Betrieb, nicht Forschung
