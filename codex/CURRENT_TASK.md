# WP-N21 — ODEFormer-Baseline: Adapter, Image mit Gewichten, Umgebungsäquivalenz
**Language: Python**

## Ausführung

Codex schreibt, testet lokal was ohne ODEFormer geht, und meldet dann. Alles, was ein Docker-Image
oder die ODEFormer-Gewichte braucht, **führt Claude aus** — Codex hat weder Docker noch Netz. Wenn
die Umsetzung fertig ist und nur die Ausführung fehlt: `blocked` mit *Umgebung, nicht Sache*.
Der Code muss also ohne eigenen Probelauf der Docker-Teile korrekt sein; die Skripte bekommen
deshalb klare Ein- und Ausgaben, die Claude mit einem Befehl pro Schritt fahren kann.

Der ODEFormer-Quellcode am gepinnten Commit `c9193012ad07a97186290b98d8290d1a177f4609` liegt
**lesbar** unter `outputs/third_party/odeformer/` (gitignored, nicht verändern, nicht committen).
Jede Aussage über ODEFormer im Report nennt Datei und Zeile dort.

## Worum es geht

Claim D vergleicht EvoGrow mit etablierten Verfahren (`docs/paper1_phaseC_benchmark_plan.md`,
Abschnitte 6a und die folgenden). SINDy läuft. ODEFormer ist im Harness nur ein Stub:
`baselines/harness.py:304-310` schreibt einen `NotImplementedError`-Datensatz. Dieses Paket macht
ODEFormer lauffähig — auf **unseren** exportierten Trajektorien, mit **ODEFormers eigener**
Evaluationskonfiguration, in einem Image, das seine Gewichte enthält.

## Teil 1 — Der Umgebungskonflikt

`baselines/requirements.txt` pinnt `torch==2.0.0`. Das hat einen CRITICAL- und mehrere
HIGH-Befunde (`CHANGELOG.md`, Ausnahme E6). Jedes torch, das sie behebt (≥ 2.10, braucht
Python ≥ 3.10), verlangt `sympy ≥ 1.13.3`; ODEFormer pinnt in `setup.py` exakt `sympy==1.11.1`.
Das lässt sich nicht gemeinsam per pip auflösen.

**Zwei Umgebungen, zwei Dockerfiles:**

- **Referenz** — das, wofür ODEFormer gebaut ist: Python 3.9, `torch==2.0.0` (CPU-Wheel),
  `sympy==1.11.1`, `numpy==1.23.5`, `sympytorch==0.1.1`, ODEFormer am gepinnten Commit mit seinen
  eigenen Abhängigkeiten. Dient **nur** als Vergleichsmaßstab, wird nie für Records benutzt.
- **Kandidat** — die Umgebung, die künftig rechnet: Python 3.11, aktuelles torch **ohne bekannte
  HIGH/CRITICAL-Befunde** (Stand heute 2.14.0, CPU-Wheel), `sympy` in der kleinsten Version, die
  torch zulässt, ODEFormer **ohne** seine eigene Abhängigkeitsauflösung installiert (die übrigen
  Laufzeitabhängigkeiten einzeln gepinnt, inklusive `sympytorch`). Alle übrigen Pins wie heute.

Beide als eigene Dockerfiles unter `baselines/`, beide Basisimages über den Harbor-Cache
(`registry.scch.at/cache/library/python:<tag>`), wie es die Pipeline-Policy verlangt.
`baselines/Dockerfile.dockerignore` existiert seit heute und regelt den Build-Kontext; für ein
zweites Dockerfile braucht es eine eigene `<name>.dockerignore` daneben.

**`torch.load`.** `odeformer/model/sklearn_wrapper.py:69` lädt ein vollständig gepickeltes Modell
ohne `weights_only`-Argument. Ab torch 2.6 ist der Standard `weights_only=True`, der Aufruf
scheitert dort. Lösen, **ohne den ODEFormer-Quellcode zu patchen** — etwa über den Mechanismus,
den torch für genau diesen Fall vorsieht. Welcher Weg, im Report begründen. Dass damit ein
vollständiges Unpickling aktiviert wird, ist bewusst: die Datei stammt aus einer festen Quelle und
wird über ihren Hash geprüft (Teil 2). Das gehört als Satz in den Report.

## Teil 2 — Gewichte ins Image

ODEFormer lädt seine Gewichte zur Laufzeit per `gdown` von Google Drive
(`sklearn_wrapper.py:59-66`). Auf dem Cluster geht das nicht: ohne Egress scheitert jeder Pod, mit
Egress fragen bis zu 32 Pods gleichzeitig Google Drive an. Die Gewichte kommen deshalb **beim Bau**
ins Image, in beide Images identisch.

- Download im Build-Schritt, danach **SHA-256-Prüfung gegen einen festen Wert im Dockerfile**.
  Stimmt der Hash nicht, bricht der Build ab. Den Wert kennt heute niemand: im Dockerfile als klar
  benannten Platzhalter hinterlegen, Claude trägt ihn nach dem ersten Download ein und dokumentiert
  die Herkunft.
- Zur Laufzeit darf kein Netzzugriff mehr nötig sein; der Adapter zeigt ODEFormer auf die Datei im
  Image.
- Jeder Record trägt den Gewichts-Hash.

## Teil 3 — Der Adapter

`run_odeformer_record` in `baselines/harness.py` ersetzt den Stub. Er fittet auf der Trajektorie
der Fit-Zelle und wertet Rekonstruktion (gleiche Anfangsbedingung) und Generalisierung (die andere
Anfangsbedingung, durch Integration des gefundenen Modells) aus — **dieselbe Record-Form wie der
SINDy-Pfad**, inklusive beider R²-Aggregationen und ihrer `> 0.9`-Felder aus WP-N19b.

**Konfiguration: ODEFormers eigene, nicht unsere.** Beam-Größe, Temperatur, Parameteroptimierung,
Rescaling, Subsampling — alles aus der Konfiguration, mit der ODEFormer auf ODEBench evaluiert wurde,
belegt mit Datei und Zeile unter `outputs/third_party/odeformer/`. Wo ODEFormer mehrere
Einstellungen berichtet, die im Paper für ODEBench verwendete. Wo das nicht eindeutig
feststellbar ist: **nicht raten**, im Report als offene Frage an Claude benennen und die
Wrapper-Voreinstellung verwenden, ausdrücklich so markiert. In `baselines/configs/` abgelegt, nicht
im Code verstreut.

**Record-Felder zusätzlich zum SINDy-Schema:**
- das gefundene Modell als Zeichenkette, so wie ODEFormer es ausgibt, und eine
  sympy-kanonische Form davon
- die Konfigurationswerte oben
- Gewichts-Hash, torch-, sympy-, Python-Version
- **strukturelle Kosten je Instanz**, soweit ODEFormer sie hergibt: Beam-Größe, Zahl der
  bewerteten Kandidaten, Iterationen der Parameteroptimierung. Wanduhrzeit höchstens als
  `elapsed_s_non_evidence` (Designprinzip 7, Plan-Abschnitt 6a)

**Determinismus:** feste Seeds für torch/numpy/random, `torch.set_num_threads(1)`, CPU. Zwei Läufe
derselben Zelle in derselben Umgebung müssen identische Records liefern (bis auf Zeitfelder).

**Nicht in diesem Paket:** die Abbildung von ODEFormers Ausdrücken auf unsere Basisterme
(Strukturmetriken für Claim A). ODEFormer erzeugt beliebige Ausdrücke; die Abbildung ist eine
eigene methodische Entscheidung. Den Ausdruck speichern, nicht zerlegen.

## Teil 4 — Äquivalenz der beiden Umgebungen

Ein Skript, das in einem Image läuft und für eine feste Zellliste ODEFormer ausführt und eine
Ergebnisdatei schreibt; ein zweites, das zwei solche Dateien vergleicht. Zellliste: die
Smoke-Systeme 1, 2 und 24, beide Anfangsbedingungen, beide Richtungen.

Verglichen werden je Zelle: kanonischer Ausdruck, gefittete Konstanten, beide R²-Aggregationen für
Rekonstruktion und Generalisierung.

**Die Vergleichsregel wird vor dem Lauf festgelegt und im Skript kodiert, nicht danach gewählt:**
Ausdrücke kanonisch identisch; Konstanten und R² innerhalb einer Toleranz, die im Report begründet
wird, bevor Claude die Images baut. Eine Abweichung ist **ein Befund, kein Fehler** — das Skript
meldet sie vollständig, Codex passt keine Toleranz nachträglich an.

## Verboten

- Keine Git-Operationen, keine Commits, kein Staging.
- `outputs/third_party/odeformer/` nicht verändern.
- ODEFormer-Quellcode nicht patchen, auch nicht per Monkeypatch zur Laufzeit.
- Keine ODEFormer-Hyperparameter wählen, die nicht aus ODEFormers eigenem Code oder Paper belegt
  sind. Kein Tuning auf unseren Daten.
- Nicht anfassen: `containers/Dockerfile`, `.gitlab-ci.yml`, `Project.toml`, `Manifest.toml`,
  `src/`, `studies/`, `experiments/`, `k8s/`, den SINDy-Pfad im Harness über das hinaus, was ein
  gemeinsames Record-Schema erzwingt.
- Keine Cluster-Jobs, keine Manifeste dafür.
- Nichts, was länger als 15 Minuten läuft.

## Abnahme

1. Beide Dockerfiles und ihre `.dockerignore`-Dateien liegen vor; das Kandidaten-requirements
   enthält kein Paket mit bekanntem HIGH/CRITICAL-Befund (im Report per Paket belegt, Quelle
   OSV oder Trivy-Datenbank, Stand heute).
2. `run_odeformer_record` ist implementiert und schreibt das Record-Schema aus Teil 3.
3. Die ODEFormer-Konfiguration liegt unter `baselines/configs/`, jeder Wert mit Datei:Zeile belegt
   oder ausdrücklich als offene Frage markiert.
4. Äquivalenz-Lauf- und Vergleichsskript liegen vor, Vergleichsregel kodiert und im Report
   begründet.
5. `python -m pytest baselines/tests/test_harness.py -q` läuft lokal grün. Lokal ist ODEFormer
   nicht installiert — die Tests prüfen dort, dass der Adapter dann einen sauberen
   Fehler-Record schreibt statt abzustürzen. Neue Tests für Vergleichsregel und Record-Schema
   laufen ebenfalls lokal, mit Eingaben, die aus echten Exporten stammen, nicht handgebaut.
6. Der Report `codex/reports/REPORT_WP_N21.md` enthält **die exakten Befehle**, mit denen Claude:
   (a) beide Images baut, (b) den Gewichts-Hash ermittelt und einträgt, (c) den Äquivalenzlauf in
   beiden Images fährt, (d) den Vergleich ausführt, (e) den Smoke-Test des Harness im
   Kandidaten-Image fährt. Je Befehl: erwartete Ausgabe und Pass-Kriterium.
