# Wie der Code von meinem Rechner auf den HPC kommt

Dieses Dokument erklärt den Weg von einer Codeänderung bis zu einer rechnenden Zelle auf dem
SCCH-Cluster **Orion** — für Leserinnen und Leser ohne Vorkenntnisse in Docker, Kubernetes oder CI.

Es beschreibt den Stand vom 2026-08-13. Die technischen Details und die Begründungen für jede
Entscheidung stehen in `DIARY.md` unter den Einträgen WP-H2 bis WP-H6.

---

## 1. Die Kurzfassung

```mermaid
flowchart LR
    A["Dein Laptop<br/>Code schreiben"] --> B["GitHub<br/>Single Source of Truth"]
    A --> C["GitLab<br/>gitlab.scch.at"]
    C --> D["GitLab CI<br/>baut ein Image"]
    D --> E["Registry<br/>lagert das Image"]
    E --> F["OpenShift 'Orion'<br/>startet Pods"]
    F --> G["NFS<br/>Ergebnisse als JSON"]
    G --> H["Dein Explorer<br/>S:\\BigDataOrion\\..."]
```

Sechs Stationen. Du fasst nur die erste und die letzte an, alles dazwischen läuft von selbst.

---

## 2. Die vier Orte, und warum es vier sind

Am Anfang verwirrend ist, dass der Code an mehreren Stellen liegt. Jede hat genau eine Aufgabe.

| Ort | Was dort liegt | Wofür |
|---|---|---|
| **GitHub** (`github.com/dajoedic/EvoODE`) | der Code mit voller Historie | **Die Quelle der Wahrheit.** Privates Konto, bleibt dir erhalten, egal was mit dem Arbeitgeber ist |
| **GitLab** (`gitlab.scch.at/joedicke/evoode`) | eine Kopie des `main`-Branches | **Auslöser.** Ein Push hierher startet den Bau des Images |
| **Registry** (`registry.gitlab.scch.at`) | fertig gebaute Images | **Lager.** Von hier holt der Cluster sich das Image |
| **Orion** (OpenShift) | nichts dauerhaft | **Rechenmaschine.** Startet Container, wirft sie danach weg |

**Warum nicht alles auf GitLab?** Weil die institutionelle Infrastruktur dir nicht gehört. Wenn du
das SCCH verlässt, verlierst du GitLab und Orion — GitHub bleibt. Deshalb ist GitHub die Quelle und
GitLab nur ein Ziel, nie umgekehrt.

**Warum überhaupt GitLab?** Weil dort die CI läuft, die das Image baut. GitHub kann das für diesen
Cluster nicht.

---

## 3. Der Weg, Schritt für Schritt

### Schritt 1 — Du committest und pushst

```bash
git add <deine Dateien>
git commit -m "was du geändert hast"
git push origin main     # GitHub, die Quelle
git push gitlab main     # GitLab, löst den Bau aus
```

`origin` ist GitHub, `gitlab` ist das zweite Remote. Der zweite Push ist der eigentliche Auslöser.

**Nur `main` wird gepusht.** Feature-Branches bleiben auf GitHub. So kann nie halbfertiger Code auf
dem Cluster landen.

### Schritt 2 — GitLab CI baut ein Image

Sobald der Push ankommt, sieht GitLab die Datei `.gitlab-ci.yml` im Projektwurzelverzeichnis und
führt aus, was dort steht. Das Ergebnis ist ein **Docker-Image**.

Ein Image ist ein eingefrorenes Dateisystem: Linux, Julia 1.12.6, dein Code, alle Pakete, alles
vorkompiliert. Es ist kein Programm, das läuft, sondern eine Vorlage, aus der man beliebig viele
identische laufende Kopien erzeugen kann.

Das dauert rund **40 Minuten**, weil Julia dabei den kompletten Paketbaum vorkompiliert. Diese Zeit
zahlst du **einmal pro Commit** — dafür starten später alle 756 Rechenzellen in Sekunden.

Zu sehen unter: `gitlab.scch.at/joedicke/evoode` → **Build → Pipelines**

### Schritt 3 — Das Image landet in der Registry

Am Ende des Baus schiebt die CI das Image in die Registry, mit **zwei Namensschildern**:

```
registry.gitlab.scch.at:443/joedicke/evoode:be6bf99d1b751d6ef748769336bbfa8e4e06314a
registry.gitlab.scch.at:443/joedicke/evoode:main
```

Das erste ist der **Commit-Hash**, das zweite der Branchname. Warum beides, steht in Abschnitt 5.

Zu sehen unter: **Deploy → Container Registry**

### Schritt 4 — Du startest die Rechnung

Jetzt kommst wieder du ins Spiel. Auf deinem Rechner läuft `oc`, das Kommandozeilenwerkzeug für
OpenShift. Du schickst eine YAML-Datei hin, die beschreibt, *was* gerechnet werden soll:

```powershell
oc apply -f manifest.yaml
```

Diese Datei nennt das Image, wie viele Zellen laufen sollen, wie viel Speicher jede bekommt und wo
die Ergebnisse hin sollen. Der Cluster liest das, holt sich das Image aus der Registry und startet
die entsprechende Zahl Container.

### Schritt 5 — Die Ergebnisse landen in deinem Explorer

Jede Zelle schreibt am Ende eine JSON-Datei auf den Netzwerkspeicher. Und dieser Speicher ist
derselbe, den du als Laufwerk `S:` siehst:

```
im Container:   /outputs/…/tasks/cell_000139.jsonl
bei dir:        S:\BigDataOrion\data-science\joedicke\…\tasks\cell_000139.jsonl
```

Du kannst also **live zuschauen**, während der Cluster rechnet, ohne dich irgendwo anzumelden.

---

## 4. Die Begriffe, in Alltagssprache

| Begriff | Was es ist |
|---|---|
| **Image** | Eine eingefrorene Festplatte mit allem drauf. Wird gebaut, dann nie wieder verändert |
| **Container** | Ein laufendes Exemplar eines Images. Startet, rechnet, verschwindet |
| **Pod** | Kubernetes' Wort für „ein laufender Container plus Drumherum" |
| **Job** | Eine Rechnung, die **fertig wird**. Läuft bis zum Ende, dann `Completed` |
| **Deployment** | Ein Dienst, der **laufen soll**. Wird bei Absturz neu gestartet. Brauchst du nicht |
| **Namespace** | Dein abgetrennter Bereich auf dem Cluster. Bei dir: `scch-das` |
| **Registry** | Das Lager für Images |
| **Runner** | Die Maschine, die die CI ausführt. Bei uns `ALEXANDRIA` |
| **NFS** | Netzwerkspeicher, den alle Pods gemeinsam sehen. Bei dir Laufwerk `S:` |
| **Manifest** | Eine YAML-Datei, die beschreibt, was der Cluster tun soll |
| **`oc`** | Das Kommandozeilenwerkzeug für OpenShift |
| **`kubectl`** | Dasselbe für normales Kubernetes. `oc` kann alles, was `kubectl` kann, und mehr |

**Die wichtigste Unterscheidung:** *Image* ist die Vorlage, *Pod* ist die laufende Kopie. 756 Pods
aus einem Image bedeuten 756-mal exakt derselbe Code.

---

## 5. Was eingestellt ist, und warum

Diese Entscheidungen sehen wie Kleinigkeiten aus. Jede einzelne wurde durch einen konkreten Fehler
erzwungen oder verhindert einen.

### Das Image trägt den Commit-Hash als Namensschild

```yaml
image: registry.gitlab.scch.at:443/joedicke/evoode:be6bf99d1b75…
```

Nicht `:main`. Der Grund ist der wichtigste im ganzen Dokument.

Jeder Ergebnisdatensatz notiert den Git-Commit, aus dem er stammt. Eine Kampagne, deren Zellen auf
**verschiedenen** Codeständen liefen, ist wissenschaftlich wertlos — und der Fehler wäre unsichtbar,
weil jeder Datensatz brav *irgendeinen* Hash nennt.

`:main` wandert bei jedem Push weiter. Ein Pod, der morgens startet, und einer, der abends startet,
bekämen unterschiedlichen Code unter demselben Namen. Der Commit-Hash wandert nicht. Damit ist der
Fehler **baulich ausgeschlossen** statt durch Disziplin vermieden.

### Julia kompiliert für zwei Prozessortypen

```dockerfile
JULIA_CPU_TARGET="generic;znver3,clone_all"
```

Julia legt beim Vorkompilieren echten Maschinencode ab, und der wird beim Start gegen die CPU
geprüft. Der Bau-Rechner ALEXANDRIA ist ein Intel, die Orion-Knoten sind AMD EPYC. Ohne diese Zeile
verwirft Julia den kompletten vorkompilierten Bestand und übersetzt neu — **46 Minuten pro Pod**,
mal 756.

Mit der Zeile: **22 Sekunden.** Die Einstellung erzeugt Code für einen portablen Grundstock *und*
für die AMD-Architektur, sodass beide Seiten etwas Brauchbares finden.

### Die CI braucht einen Docker-Hilfsdienst

```yaml
services:
  - name: docker:29-dind
    alias: docker
variables:
  DOCKER_TLS_CERTDIR: ""
```

Der GitLab-Runner erwartet, dass man einen Docker-Dienst mitstartet („Docker-in-Docker"). Ohne
diesen Block scheitert der Bau sofort mit `dial tcp: lookup docker … server misbehaving`.

### Gebaut wird auf dem CPU-Runner

```yaml
tags:
  - cpu
```

Es gibt zwei Runner: `GOLDBERG` mit GPUs und `ALEXANDRIA` ohne. Ein Julia-Bau profitiert von einer
GPU **nicht im Geringsten** — sie zu belegen würde nur anderen die knappe Ressource wegnehmen.

### Jeder Pod trägt einen Namensschild mit Verantwortlichem

```yaml
hpc.scch.at/service: evoode-phase-b-cells
hpc.scch.at/responsibility: joedicke
```

Sieht nach Bürokratie aus, ist aber deine Versicherung. Der Cluster-Betrieb hat zugesagt, Jobs in
Ruhe zu lassen und **vorher Bescheid zu geben**, falls etwas auffällt — ausdrücklich unter der
Bedingung, dass die Workload identifizierbar ist. Ohne diese zwei Zeilen sieht jemand einen Pod, der
seit 40 Stunden rechnet, und hat niemanden zu fragen.

### Gescheiterte Pods bleiben stehen

```yaml
restartPolicy: Never
```

Bei der Alternative `OnFailure` **löscht** Kubernetes den gescheiterten Pod, bevor es neu startet —
samt Logs. Genau so ist einmal eine Fehlermeldung verloren gegangen, und die Ursache musste
nachgestellt werden. Mit `Never` bleibt jeder Fehlschlag mit seiner Ausgabe liegen.

### Jede Zelle läuft einkernig

```yaml
JULIA_NUM_THREADS: "1"
OPENBLAS_NUM_THREADS: "1"
resources:
  limits:
    cpu: "1"
```

Nicht aus Bescheidenheit: Einkernig ist die Voraussetzung dafür, dass jede Zelle bei gleichem Seed
**exakt dasselbe** Ergebnis liefert. Die Parallelität kommt nicht aus dem Code, sondern daraus, dass
viele unabhängige Zellen gleichzeitig laufen.

---

## 6. Wie viele gleichzeitig? — `completions` und `parallelism`

```yaml
completionMode: Indexed
completions: 756      # so viele Zellen insgesamt
parallelism: 16       # so viele gleichzeitig
```

Kubernetes gibt jedem Pod eine laufende Nummer in der Umgebungsvariablen `JOB_COMPLETION_INDEX`.
Der Code schlägt damit in einer Liste nach, welche Zeile des Kampagnen-Manifests er rechnen soll.

**Achtung, klassische Fehlerquelle:** Diese Nummer beginnt bei **0**, Zeilennummern in Dateien bei
**1**. Eine wörtliche Übersetzung überspringt die erste Zelle und liest einmal über das Listenende
hinaus — leise, mit 755 plausibel aussehenden Ergebnissen.

`parallelism` ist die Höflichkeitsschraube. Der ganze Cluster hat **96 Kerne** auf zwei Knoten, und
die sind eigentlich dazu da, acht GPUs zu füttern. Abgesprochen sind 16.

---

## 7. Die übliche Reihenfolge

```powershell
# 1. Anmelden (Token läuft nach einiger Zeit ab)
oc login --web https://api.orion.scch.at:6443
oc project scch-das

# 2. Einmalig: Manifest und Indexlisten erzeugen
oc apply -f bootstrap.yaml
oc wait --for=condition=Complete job/<name> --timeout=1800s
oc logs -l job-name=<name> --tail=20

# 3. Die Rechenzellen starten
oc apply -f cells.yaml

# 4. Zuschauen
oc get jobs -l hpc.scch.at/responsibility=joedicke
oc get pods -l hpc.scch.at/responsibility=joedicke

# 5. Aufräumen, wenn fertig
oc delete job <name>
```

**Die Reihenfolge 2 vor 3 ist zwingend.** Die Zellen lesen das Manifest, das der Bootstrap anlegt.

**Ohne Anmeldung zuschauen** geht auch — über den Explorer:

```powershell
Get-ChildItem "S:\BigDataOrion\data-science\joedicke\<lauf>\tasks\*.heartbeat.jsonl" |
  ForEach-Object { "{0}: {1}" -f $_.Name, (Get-Content $_.FullName -Tail 1) }
```

Das zeigt für jede laufende Zelle den letzten Fortschrittseintrag. Praktischer als jedes Log, weil
es alle Zellen auf einmal abdeckt.

---

## 8. Was schiefgehen kann, und woran man es erkennt

Alle diese Fälle sind tatsächlich aufgetreten.

| Symptom | Ursache | Abhilfe |
|---|---|---|
| `ImagePullBackOff`, scheitert nach 1 s | Das Zugangsgeheimnis gilt nicht für dein Projekt | Deploy-Token mit `read_registry` anlegen, daraus ein eigenes Secret |
| `OOMKilled` | Speicherlimit zu niedrig | Wert im Manifest erhöhen. RAM ist auf Orion reichlich vorhanden |
| Pod läuft 40 min, bevor er rechnet | `JULIA_CPU_TARGET` fehlt | siehe Abschnitt 5 |
| `dial tcp: lookup docker … server misbehaving` | Docker-Hilfsdienst fehlt in der CI | `services:`-Block ergänzen |
| Job `Failed`, keine Logs mehr da | `restartPolicy: OnFailure` hat den Pod gelöscht | Auf `Never` umstellen |
| `You must be logged in to the server` | Token abgelaufen | Neu anmelden. **Die laufenden Jobs stört das nicht** |
| Job `Pending`, „waiting for runner" | Der Tag passt zu keinem Runner | Tag im Manifest prüfen |

**Wichtig:** `Completed` heißt nur, dass das Programm ohne Absturz endete — **nicht**, dass das
Ergebnis brauchbar ist. Fehler werden im Datensatz im Feld `error` festgehalten, und der Pod endet
trotzdem sauber. Immer prüfen:

```powershell
Select-String -Path "S:\...\tasks\*.jsonl" -NotMatch -Pattern '"error":null'
```

Was hier ausgegeben wird, ist fehlerhaft.

---

## 9. Wo die konkreten Werte stehen

| Was | Wert |
|---|---|
| Namespace | `scch-das` |
| API-Adresse | `https://api.orion.scch.at:6443` |
| Web-Oberfläche | `https://console-openshift-console.apps.orion.scch.at/` |
| Image | `registry.gitlab.scch.at:443/joedicke/evoode:<commit-hash>` |
| Zugangsgeheimnis | `evoode-gitlab-pull` |
| NFS-Server | `nfs.orion.scch.at`, Export `/bigdata` |
| Arbeitsverzeichnis | `/bigdata/data-science/joedicke` = `S:\BigDataOrion\data-science\joedicke` |
| Ansprechpartner | Rainer Meindl |

Die Vorlagen liegen unter `k8s/` im Repository. Der Commit-Hash darin ist ein Platzhalter und muss
vor dem Anwenden durch den tatsächlichen ersetzt werden.

---

## 10. Was dieses Dokument nicht behandelt

- **Die wissenschaftliche Seite** — was gerechnet wird und warum: `CLAUDE.md` und `PAPER_1.md`
- **Die Chronologie** — welcher Fehler wann auftrat und wie er gefunden wurde: `DIARY.md`, Einträge
  WP-H2 bis WP-H6
- **Die Kostenrechnung** — `docs/hpc_requirements.md`. Achtung: Dieses Dokument beschreibt noch einen
  Slurm-Standort und enthält Schätzungen, die sich als um ein bis zwei Größenordnungen zu hoch
  erwiesen haben. Es wird überarbeitet, sobald die Pilotmessungen vollständig sind.
