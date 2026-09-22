# WP-T1e — WP-T1d reparieren, begrenzen und clusterfähig machen
**Language: Julia**

## Ausführung

Codex kann hier kein Julia ausführen. Schreiben, dann `blocked` melden; Claude fährt den
Smoke-Test, der Nutzer startet den Cluster-Lauf. Der Code muss also ohne eigenen Probelauf korrekt
sein. **Genau daran ist der letzte Anlauf gescheitert** — siehe die zwei Defekte unten.

## Teil 1 — Zwei Defekte in `studies/regression/wp_t1d_neighbourhood_loss.jl`

Beide sitzen in `log10_loss_ratio`, beide entstanden aus demselben Griff: `true` ist in Julia ein
Schlüsselwort und darf weder als Variable noch als Wert für den wahren Loss stehen.

**Defekt 1, Zeile 278: `true = Float64(true_loss)`.** Zuweisung an ein Schlüsselwort, **Parse-Fehler**.
Das Skript lässt sich nicht laden. Laut, harmlos, sofort sichtbar.

**Defekt 2, Zeile 282: `return log10(neighbor / true)`.** Das **parst und läuft**, weil `true` als
`1` durchgeht. Berechnet würde `log10(neighbor)` statt `log10(neighbor / true_loss)` — **die
Hauptmetrik dieses Work Packages wäre still falsch gewesen**, mit plausibel aussehenden Zahlen.
Hätte Defekt 1 das Laden nicht verhindert, wäre das unentdeckt durchgelaufen.

Beide beheben, indem die lokale Variable einen zulässigen Namen bekommt und **beide** Verwendungen
darauf zeigen. Anschließend die ganze Datei nach weiteren Zuweisungen an Schlüsselwörter absuchen;
eine Suche über beide Dateien hat sonst nichts gefunden, aber die Prüfung gehört in den Report.

**Verpflichtender Regressionstest**, ohne den die Reparatur nicht abgenommen wird: `log10_loss_ratio`
wird mit bekannten Werten geprüft, sodass Defekt 2 auffallen **muss** — etwa Nachbarloss `1e-4`
gegen wahren Loss `1e-2` ergibt exakt `-2.0`. Ein Test, der nur auf „nicht `nothing`" prüft, ist
wertlos: Defekt 2 hätte ihn bestanden.

## Teil 2 — Die Laufzeit konstruktiv begrenzen

Heute ist die Laufzeit **geschätzt**, nicht begrenzt. Das ist zu wenig: `CLAUDE.md` führt unter
„Unbudgeted call sites", dass elf Skripte unter `benchmarks/` und `studies/` den Optimierer **ohne
Budget** konstruieren und seit WP-B3 unbeschränkt sind — mit hoher Wahrscheinlichkeit auch der
Pfad, den `wp_n3_oracle_refit.jl` benutzt und den dieses Skript übernimmt. Phase B kennt
pathologische Line-Searches mit bis zu 39.933 Loss-Evaluationen bei zwei Parametern; ein entarteter
Nachbarträger ist genau der Fall, in dem das eintritt.

**Der Optimierer bekommt ein explizites Loss-Eval-Budget je Fit.** Verwende den Mechanismus, den die
Kampagnenrunner bereits benutzen (`studies/regression/phase_c_config.jl`,
`studies/regression/run_regression.jl`) — **nicht** einen neu erfundenen. Den Namen des Feldes und
den gewählten Wert im Report nennen.

Ein Fit, der am Budget endet, wird als `budget_exhausted` markiert, geht in die Records ein und
wird **nie** als „Nachbar schlägt Wahrheit" gewertet — in keine Richtung, genau wie die
Sentinel-Fälle.

Warum das zählt: die Messung auf System 24 ergab 1,80 s je Fit, die Projektion rechnet mit 9,48 s,
und Phase B zeigt zwischen den dim-2-Systemen einen Faktor **1.800** bei den Kosten je Zelle
(0,003 h bis 5,33 h). Eine Schätzung über diese Spanne ist keine Schranke.

## Teil 3 — Sharding über Zellindizes

Der Lauf wird auf Orion als Indexed Job gefahren, also muss das Skript **eine Zelle je Index**
rechnen können.

- Eine Zelle ist ein Paar (System, IC-Satz). Umfang: 18 exakte Systeme auf dim 2 und dim 3, beide
  IC-Sätze, also **36 Zellen**, Index 0 bis 35.
- Die Reihenfolge ist **deterministisch und dokumentiert** (System aufsteigend, darin IC 1 vor
  IC 2), damit ein Index dauerhaft dieselbe Zelle bezeichnet.
- Die Auswahl kommt aus der Umgebung, nach dem Muster von
  `studies/regression/run_k8s_indexed_cell.jl`: eine Indexliste und ein Ausgabeverzeichnis als
  Umgebungsvariablen. Dieses Muster lesen und übernehmen, nicht neu erfinden.
- Jede Zelle schreibt ihre eigene Ergebnisdatei. **Kein gemeinsames Anhängen an eine Datei** — 36
  Pods, die in dieselbe Datei schreiben, ist ein Datenverlust mit Anlauf.
- Die Aggregation über alle Zellen bleibt ein **getrennter, lokaler Schritt** und läuft nicht im Pod.

Die bestehende lokale Aufrufform (`--systems`, `--limit-cells`, `--smoke`, `--self-test`,
`--projection-only`) bleibt erhalten und unverändert.

## Teil 4 — Trajektorien im Image

**Der gehashte Export liegt unter `outputs/` und ist gitignoriert, ist also nicht im Image.** Auf
dem Cluster integriert das Skript die Trajektorien deshalb **selbst**, mit demselben Codepfad und
denselben Einstellungen wie die Kampagne (`Tsit5`, `abstol = reltol = 1e-9`, 512 Punkte über
t ∈ [0,10], beide IC-Sätze). Das ist nicht der zweitbeste Weg, sondern der genauere: es ist exakt
der Pfad, der die Kampagnenzahlen erzeugt hat.

Jede Zelle schreibt die **`trajectory_sha256`** ihrer Trajektorie in den Record. Der Abgleich gegen
`trajectory_manifest.csv` des Exports passiert später lokal; im Pod wird nichts verglichen, weil
dort nichts zu vergleichen ist.

Ist der Export lokal vorhanden, wird er lokal weiterhin bevorzugt — aber **eine Zelle benutzt genau
eine Quelle**, und welche, steht im Record. Mischen ist verboten.

## Teil 5 — Die Cluster-Artefakte

Drei neue Dateien unter `k8s/`, gebaut nach dem Muster der vorhandenen Manifeste — Namensschilder
`hpc.scch.at/service` und `hpc.scch.at/responsibility`, `imagePullSecrets: evoode-gitlab-pull`,
Image `registry.gitlab.scch.at:443/joedicke/evoode:<COMMIT_SHA>` als Platzhalter,
`JULIA_NUM_THREADS=1` und `OPENBLAS_NUM_THREADS=1`, `cpu: "1"` und `memory: 2Gi` je Pod:

1. **Ein Bootstrap- oder Indexlisten-Schritt**, der die 36 Zellen als Liste erzeugt und auf die
   Freigabe schreibt — analog zum Kampagnen-Bootstrap.
2. **Ein Smoke-Job mit zwei Zellen.** Nimm die beiden billigsten, System 24 IC 1 und System 25 IC 1
   (Phase B: 0,003 und 0,004 h je Zelle). Zweck ist **nicht** Wissenschaft, sondern der Nachweis,
   dass Image, Deploy-Token und Freigabe funktionieren — das Kampagnen-Manifest begründet das in
   seinem eigenen Kommentar, und ein abgelaufenes Token zeigt sich sonst erst mitten im langen Lauf.
3. **Der eigentliche Job:** `completions: 36`, **`parallelism: 2`**, und
   **`activeDeadlineSeconds: 86400`**.

`parallelism: 2` ist bewusst klein: die Kampagne belegt 64 der 96 Kerne, und der Nutzer will den
Cluster nicht ausreizen. `activeDeadlineSeconds` ist eine **Decke, keine Erwartung** — erwartet
sind bei 36 Zellen und zwei Pods rund fünf bis sechs Stunden. Beides im Manifest kommentieren, wie
es die bestehenden Manifeste tun.

## Verbote

- Keine Änderung an `src/`, an `studies/regression/run_regression.jl`, an `phase_c_config.jl`, an
  bestehenden Manifesten oder an irgendeinem Fingerprint. Neue Dateien, keine Umbauten.
- Kein Schreiben in `analysis/data/paper1_phase*` oder `experiments/`. Die Phase-C-Kampagne läuft.
- Kein Ausführen des vollen Laufs, kein GitLab-Push, kein `oc apply`.
- Keine neue Abhängigkeit; fehlt etwas, als Blocker melden.

## Abnahmekriterium

Das Skript lädt fehlerfrei; der Regressionstest für `log10_loss_ratio` prüft einen bekannten
Zahlenwert und würde Defekt 2 fangen; das Budget ist gesetzt und `budget_exhausted` wird geführt;
eine Zelle je Index ist rechenbar und die Indexordnung ist dokumentiert; die drei Manifeste liegen
vor. Melde `blocked` mit dem Hinweis auf die fehlende Julia-Ausführung.

## Bericht

`codex/reports/REPORT_WP_T1e.md`. Zwingend: beide Defekte mit ihrer Wirkung — insbesondere, dass
Defekt 2 still war —, der verwendete Budgetmechanismus samt Wert und Herkunft, die Indexordnung,
die Trajektorienquelle je Umgebung, und die Begründung für `parallelism: 2` und
`activeDeadlineSeconds`.
