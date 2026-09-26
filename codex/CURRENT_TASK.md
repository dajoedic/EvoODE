# WP-N29 — ODEFormer-Kandidatenraster (torch 2.14) auf Orion: CI-Image, Runner-Parameter, Manifeste
**Language: Python**

## Ausführung

Lokal umsetzbar. Nur die betroffenen Python-Tests ausführen. Keine Git-Operationen, kein Docker-Build,
kein `oc`/`kubectl`. Nichts, was länger als 15 Minuten läuft.

## Ausgangslage

Das ODEFormer-Referenzraster (torch 2.0.0, Image `odeformer-reference`) lief am 26.09. auf Orion:
3 Wiederholungen × 42 Shards = 126 Completions, 1.512 Records, sauber. Entschieden am 26.09. mit dem
Nutzer: Das **Kandidatenraster** (torch 2.14, `baselines/Dockerfile.odeformer-candidate`) läuft unter
**demselben Protokoll** auf Orion, als Sensitivitätsprüfung neben der Referenz
(`docs/paper1_phaseC_benchmark_plan.md`, Absatz „ODEFormer arm“).

Was fehlt:

1. `.gitlab-ci.yml` baut und scannt nur `odeformer-reference`. Ein Kandidaten-Image gibt es in der
   Registry nicht.
2. `baselines/run_odeformer_grid_k8s.py` setzt `environment_id="reference"` fest.
3. Es gibt nur Manifeste für die Referenz (`k8s/odeformer_reference_grid_job.yaml`,
   `k8s/odeformer_reference_grid_smoke_job.yaml`).

Das Kandidaten-Dockerfile unterscheidet sich von der Referenz nur in der Python-Basis (3.11 statt
3.10) und der Requirements-Datei. Die `param_optimizer`-Übernahme mit Hash-Prüfung aus WP-N27c ist
schon enthalten.

## Was zu tun ist

1. **CI:** In `.gitlab-ci.yml` einen Job `build_odeformer_candidate_image` und einen Trivy-Job
   `trivy-odeformer-candidate-image` anlegen, **exakt nach dem Muster** der Referenz-Jobs: dieselbe
   dind-Digest-Pinnung, dieselben Attestation-Schalter, dieselben `rules` (automatisch bei
   Änderungen unter `baselines/**/*`, sonst manuell auf `main`), `needs` auf den eigenen Build-Job.
   Image-Pfad `$CI_REGISTRY_IMAGE/odeformer-candidate:$CI_COMMIT_SHA` plus Branch-Tag. Die
   bestehenden Jobs bleiben unverändert.
2. **CHANGELOG:** In `CHANGELOG.md` einen Eintrag für die CI-Änderung, im Stil der vorhandenen
   Einträge. Die HIGH/CRITICAL-Befunde des Kandidaten-Image sind noch nicht gemessen; das so
   vermerken und auf E7 verweisen, keine Zahlen erfinden.
3. **Runner:** `run_odeformer_grid_k8s.py` bekommt `--environment-id` mit den Werten `reference` und
   `candidate`, Default `reference`, damit das bestehende Referenz-Manifest unverändert gültig
   bleibt. **Schutz gegen das falsche Image:** Vor dem ersten Record prüft der Runner, dass die
   installierte torch-Version zur gewählten Umgebung passt. Die Sollversion wird aus
   `baselines/requirements-odeformer-<environment_id>.txt` gelesen, nicht als Konstante in den Code
   geschrieben. Bei Abweichung: harter Abbruch vor jeder Berechnung. Die Beschreibung des Parsers
   sagt nicht mehr „reference grid“.
4. **Manifeste:** `k8s/odeformer_candidate_grid_job.yaml` und
   `k8s/odeformer_candidate_grid_smoke_job.yaml`, abgeleitet von den Referenz-Manifesten. Job-Namen
   und Labels mit `candidate`, Image `odeformer-candidate:<COMMIT_SHA>`,
   `--environment-id candidate`, Ausgabe `/outputs/odeformer_grid_<COMMIT_SHA>/candidate` (Smoke:
   `…/candidate/smoke`). Ressourcen, `parallelism`, `backoffLimit` und `activeDeadlineSeconds` wie
   die Referenz, mit demselben Begründungskommentar.
   **Trajektorien:** Beide Arme sollen **dieselben Dateien** lesen. Das Kandidaten-Manifest nimmt
   den Trajektorienpfad deshalb über einen eigenen Platzhalter `<TRAJECTORY_SHA>`
   (`/outputs/odeformer_grid_<TRAJECTORY_SHA>/trajectory_export`), getrennt vom Image-SHA. Ein
   Kommentar im Manifest sagt, dass hier der SHA des Referenzrasters (`55e9c75…`, voller Hash aus
   dem NFS-Pfad) einzusetzen ist, damit die Hash-Prüfung gegen identische Eingaben läuft.
5. **Einsammeln:** Prüfen, ob das bestehende `--collect --repetitions 3` (siehe `SCRIPTS.md`,
   Abschnitt ODEFormer auf Orion) auch für `…/candidate` funktioniert. Wenn es `reference` fest
   annimmt, parametrisieren (Default unverändert).
6. **`SCRIPTS.md`**, Abschnitt ODEFormer auf Orion: die Kandidaten-Befehle neben die
   Referenz-Befehle stellen (Smoke, Grid, Einsammeln), mit beiden Platzhaltern und dem Hinweis,
   dass der Smoke eine `_opt`-Zelle mit `odeformer_optimization_status = success` zeigen muss,
   bevor der Grid startet. `docs/hpc_deployment_guide.md` nur ergänzen, wo es Manifeste oder
   Image-Pfade aufzählt.

## Verboten

- Keine Git-Operationen, kein Docker, kein `oc`/`kubectl`.
- Keine Änderung am Verhalten des Referenzarms: Referenz-Manifeste, Referenz-CI-Jobs und das
  Default-Verhalten des Runners bleiben, wie sie sind.
- Keine Änderung an `baselines/harness.py`, `baselines/configs/` oder an der ODEFormer-Konfiguration
  (Beam, Optimierung, 1-s-Timeout). Der Kandidat unterscheidet sich **nur** durch das Image.
- Keine Änderung an `containers/Dockerfile` oder am Kampagnen-Build (C-1 bis C-3 laufen noch).
- Nichts unter `analysis/data/` oder `analysis/tables/` schreiben.

## Abnahme

1. Tests für den Runner: `--environment-id` wird durchgereicht; Default ist `reference`; die
   torch-Prüfung bricht bei Abweichung ab und lässt die passende Version durch (Version im Test
   simuliert, nicht vom installierten torch abhängig); die Sollversion kommt aus der
   Requirements-Datei.
2. Die neuen YAML-Dateien und `.gitlab-ci.yml` sind gültiges YAML (mit Python geparst). Ein
   Diff-Vergleich Referenz- gegen Kandidaten-Manifest zeigt nur die beabsichtigten Unterschiede. Den
   Diff in den Report.
3. Die bestehenden ODEFormer-Tests unter `baselines/` bzw. `test/` laufen weiter grün.
4. Report `codex/reports/REPORT_WP_N29.md`: geänderte Dateien, der Manifest-Diff, die Befehle für
   Smoke, Grid und Einsammeln mit Platzhaltern, was nicht verifiziert ist (Image-Bau, Pull,
   NFS-Pfad).
