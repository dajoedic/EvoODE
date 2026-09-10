# READ_THIS_FIRST.md — Sitzungsübergabe

**Was dieses Dokument ist:** der flüchtige Zustand *zwischen* zwei Chat-Sitzungen — was gerade läuft,
was uncommittet im Working Tree liegt, welche Entscheidung als Nächstes ansteht. Nichts weiter.

**Was es ausdrücklich nicht ist:** ein Planungs- oder Statusdokument. `CLAUDE.md` verbietet ein
zweites davon, und es wird in jeder Sitzung ohnehin automatisch geladen. Alles Dauerhafte gehört
dorthin, nach `PAPER_1.md` oder ins `DIARY.md` — **nicht hierher.**

**Regeln für dieses Dokument:** wird immer **vollständig überschrieben**, nie angehängt. Alles darin
ist mit einem Datum versehen. Was älter als ein paar Tage ist, ist vermutlich falsch — dann gilt
`CLAUDE.md`.

**Stand: 2026-09-10, nachmittags. HEAD = `c049f6b`. Working Tree sauber.**

---

## 1. Wo das Projekt inhaltlich steht — in drei Sätzen

Paper 1 ist ein **Methodenpaper**; die 756-Zellen-Phase-B-Kampagne ist zu Diagnostik und
Ablationsquelle degradiert. Die kanonische Evaluation heißt **Phase C**, ihre Matrix ist seit dem
10.09. **vollständig** — jeder Claim nennt Arm, Skript, Ausgabepfad und Pass-Kriterium — und alle
fünf offenen Planfragen sind entschieden. Gestartet ist Phase C **nicht**: es fehlt die kanonische
Basis, und die entscheidet ein Probelauf, der gerade rechnet.

Autoritative Quellen, in dieser Reihenfolge: `PAPER_1.md` (Zuschnitt und Claims) →
`docs/paper1_phaseC_benchmark_plan.md` (Experimentmatrix, Freeze-Liste, Voraussetzungen) →
`CLAUDE.md` (Orientierung) → `DIARY.md` (Chronologie, neueste Einträge oben).

---

## 2. Was JETZT läuft — beim Sitzungsstart prüfen

### Cluster: der dim-2-Probelauf

```bash
kubectl get jobs -n scch-das
```

Erwartet: `evoode-wp-n1-dim2-campaign`, Ziel **336** Zellen, `parallelism: 32`.
Stand 10.09. ~13:45: **124/336 nach 16 Stunden**, 32 aktiv, **0 failed**, keine Pod-Restarts.

Ergebnisse ohne Anmeldung sichtbar unter:
`S:\BigDataOrion\data-science\joedicke\wp_n1_dim2_probe_ec3b6bd5b43f06539d38b633257ca51115bfa47f\tasks\`

**Zwei Dinge, die man über diesen Lauf wissen muss.**

**(a) Der Vergleichsarm hat noch nicht begonnen.** Das Manifest schleift `for variant` **außen**
(`generate_wp_n1_basis_probe_manifest.jl:32`), also ist Index **1–168 die alte Basis** und
**169–336 die konstante**. Alle bisher fertigen Zellen tragen `basis_name =
default_staged_polynomial_basis`. Ein Abbruch vor Index 169 hinterließe 168 Zellen einer Basis, die
wir schon kennen — für die Entscheidung wertlos. Der Lauf ist erst ab dort überhaupt teilauswertbar.

**(b) Der Rest dauert länger als die erste Hälfte.** Die konstante Basis durchsucht einen größeren
Raum. Realistisch **41–47 Stunden gesamt**, also 11.09. abends bis 12.09. früh. Zeitangaben sind
Kapazitätsplanung, keine Evidenz (Designprinzip 7).

**Gesundheitsprüfung, falls Zweifel:** 124 Ergebnis-Records auf dem Share, `error` in allen leer,
ein Git-Hash `ec3b6bd`, ein `config_fingerprint`, ein Verhaltens-Fingerprint. Die WP-N8-Reparatur
greift nachweislich — kein `not_collected` mehr in echten Daten.

**Wozu der Lauf dient:** Er entscheidet den **letzten offenen eingefrorenen Parameter** der Phase C —
ob der konstante Term `1` in die kanonische Basis kommt. Ohne diese Entscheidung darf Phase C nicht
starten, und **drei der sieben Arbeitspakete hängen daran**.

**Wie er ausgewertet werden muss:** gegen eine **rohe dim-2-Basisrate von 17,6 %**, nicht gegen die
vertrauten 49,1 %. Der Unterschied ist die Ausdünnungsregel, siehe `CLAUDE.md`, Known Gaps.

### Lokal: nichts mehr

Die WP-N10-Messung auf System 26 ist **durchgelaufen**, das Ergebnis steht in Abschnitt 4.

---

## 3. Was uncommittet im Working Tree liegt

**Nichts.** Alle sechs Arbeitspakete dieser Sitzung sind abgenommen und committet.

---

## 4. Was diese Sitzung erledigt hat

Sechs Arbeitspakete, alle von Claude abgenommen, nicht von Codex.

| WP | Inhalt | Commit |
|---|---|---|
| N10 | `StructureSpec`-Duplikatzähler, verhaltensneutral | `22a9059` |
| **P8** | **Phase-C-Matrix vollständig, fünf Planfragen entschieden** | `02d80dd` |
| N11 | Restart-Politik als benannter Parameter, Default k = 1 | `4908b07` |
| N12 | Roher und ausgedünnter Support getrennt im Record | `47920a2` |
| N13 | Kampagne als expliziter, geprüfter Parameter der Auswertung | `1c984a6` |
| N14 | Gepaarte Kappen-Ablation — die Hauptabbildung des Papers | `e738b0c` |

**Die dim-2-Duplikatrate ist da und dreht eine Lesart um.** System 26, dim 2: 310 Fits über **45**
eindeutige Strukturen, Rate 85,5 %. Die Aggregatzahl ähnelt dim 1 (98,2 % und 99,0 %), **die
Verteilung nicht**: Wiederholungen je Struktur von **1** über einen Median von **5** bis 32, gegen
55–97 auf dim 1. Strukturen mit **genau einem** Fit gibt es auf gekoppelten Systemen also — und dort
greift ein expliziter Retry. Die eingefrorene Politik `retry-on-failure bis k = 3` steht damit
besser da, als die dim-1-Zahlen vermuten ließen. **Eine Zelle entscheidet nichts**, sie zeigt die
Größenordnung; die Verteilung über 378 Zellen liefert Phase C umsonst.

**Drei Befunde aus der Abnahme, die kein Report gemeldet hatte** — alle drei durch Ausführung oder
Gegenrechnen gefunden, nicht durch Lesen:

- **Das Paket präkompilierte nicht mehr** (WP-N11): eine doppelte Methodendefinition im selben
  Modul. Verhalten korrekt, aber jeder Julia-Start hätte die volle Kompilierzeit gezahlt — auf 378
  Pods jede Zelle.
- **`campaign_manifest_index`** (WP-N14) musste zwischen den Armen übereinstimmen, kann das aber
  nicht: jeder Arm hat seine eigene Manifestzeile, in Phase B weicht die Spalte in **378 von 378**
  Paarungen ab. Die Hauptabbildung wäre in jeder Paarung abgebrochen — mit der Meldung „die
  Bedingungen sind nicht identisch", also einem Buchhaltungsfeld, das wie ein wissenschaftlicher
  Befund aussieht.
- **`.gitignore` hätte alle Phase-C-Ergebnisse verschluckt** (bei WP-N13 aufgefallen):
  `analysis/{data,figures,tables}/*` sind ignoriert mit Ausnahmen **je Kampagne**, und für
  `paper1_phaseC_v1` gab es keine. Drei Zeilen ergänzt.

**Und eine falsche Beschreibung im Plan selbst:** B6 behauptete, die Aggregatskripte seien auf
Phase B verdrahtet. Sie waren es nie — nur ihre Defaults. Die echte Lücke war, dass
`verify_campaign_registry.py` `experiment_id` **überhaupt nicht** prüfte; eine Registry aus zwei
Kampagnen bestand die Prüfung.

---

## 5. Was als Nächstes ansteht

**Die Arbeit, die ohne die Basisentscheidung möglich ist, ist aufgebraucht.** Freeze-Liste
(`docs/paper1_phaseC_benchmark_plan.md` §2a und §4):

| | Voraussetzung | Stand |
|---|---|---|
| P1 | `git_hash` im Probe-Skript | erledigt (WP-N8) |
| P2 | dim-2-Probelauf | **läuft**, 124/336 |
| P3 | kanonische Basis entscheiden und einfrieren | **wartet auf P2 — der Engpass** |
| P4/P5 | Strukturmetriken, dreiwertige Repräsentierbarkeit | erledigt (WP-N7/N7b) |
| P6 | Restart-Politik | Code erledigt (WP-N11), Deklaration im Phase-C-Fingerprint offen → B1 |
| P7 | Duplikatrate | Zähler erledigt (WP-N10), Verteilung kommt aus C-1 |
| P8 | Phase-C-Matrix | **erledigt** |
| P9 | Smoke-Test und 12-Zellen-Pilot | offen |
| B1 | `phase_c_config.jl` + Manifestgenerator | **offen, braucht die Basis** |
| B2 | Roh/Ausgedünnt-Felder | erledigt (WP-N12) |
| B4 | Support-Tabelle für die kanonische Basis | **offen, braucht die Basis** |
| B5 | Auswertung Claim B | erledigt (WP-N14) |
| B6 | Kampagne als geprüfter Parameter | erledigt (WP-N13) |
| B7 | k8s-Manifeste | **offen, braucht B1** |

**B1 hat drei Anforderungen geerbt**, alle im Plan festgeschrieben, alle leicht zu vergessen:

1. die Spaltenliste, die das Ablationsskript verlangt — allen voran **`executed_levels`**, und
   ausdrücklich **nicht** `n_levels`, das die Konstante 30 ist;
2. die Deklaration des Restart-Parameters im **Phase-C**-Fingerprint, wobei k = 3 in der
   Phase-C-Konfiguration gesetzt wird und **nie** im Optimierer-Default, der auf 1 bleibt;
3. die Phase-C-Erwartungswerte für `verify_campaign_registry.py`, der sonst gegen Phase-B-Zahlen
   prüft (756 statt 378 und so weiter).

---

## 6. Was man nicht vergessen darf

Dinge, die nichts blockieren und genau deshalb untergehen.

**Das Deploy-Token für die Registry läuft ab.** Am 09.09. ist genau das passiert, mitten im
Smoke-Job (`ErrImagePull` mit `HTTP Basic: Access denied` — sieht nach fehlendem Image aus, ist aber
die Anmeldung). Aktuelles Token `gitlab+deploy-token-13`, angelegt 09.09. **Pods werden über die
ganze Laufzeit neu erzeugt** — läuft das Token mitten in einem mehrtägigen Lauf ab, entsteht ein
halb fertiger Datensatz mit einer Lücke in der Mitte. Also: Ablaufdatum großzügig, und **immer erst
den Smoke-Job**. Fehlermodus in `docs/hpc_deployment_guide.md` §8. Das Token steht im Klartext im
Chatverlauf vom 09.09.; read-only auf die Registry beschränkt, aber tauschbar, wenn es stört.

**`parallelism` steht auf 32, nicht auf den vereinbarten 16.** Begründung als Kommentar im Manifest
`k8s/wp_n1_basis_probe_dim2_campaign_job.yaml`. Technisch unbedenklich, weil `requests == limits`
gilt und überzählige Pods `Pending` bleiben. Falls sich jemand meldet: das ist der Kontext.

**Die 756 Kampagnenzellen tragen keine Koeffizienten.** Jede dimensionsübergreifende
Generalisierungszahl erfordert einen Neulauf. Das ist der Grund, warum Phase C nötig ist.

**Niemand führt die Python-Tests automatisch aus.** Die GitLab-CI baut ausschließlich das
Kampagnen-Image. Aktuell **27 Tests grün**, aber nur weil sie von Hand laufen. Ein Wächtertest war
schon einmal drei Wochen rot, ohne dass es auffiel — und WP-N13 hat genau deshalb die Exit-Codes
getrennt geprüft, nicht nur die Meldungen.

**Elf Skripte** unter `benchmarks/` und `studies/` konstruieren den Optimierer ohne Budget und sind
seit WP-B3 unbeschränkt. Bewusster Rückstand, gelistet in `codex/reports/REPORT_WP_D3.md`.

**Die externen Spalten des Protokoll-Audits** (`docs/paper1_odebench_protocol_alignment.md`) sind
der letzte substanzielle Phase-3-Posten — inklusive der offenen Frage, ob publizierte
Vergleichszahlen auf den *mitgelieferten* Trajektorien gerechnet wurden. Falls ja, arbeiten wir auf
saubereren Daten als der Vergleich, und das muss deklariert werden.

**`DIARY.md` wächst schnell und wird bei fast jedem Commit angefasst.** Das hatte `.git` schon
einmal auf 852 MB aufgebläht. Nach `git gc --prune=now` sind es 11 MB. Gelegentlich wiederholen.

**Reste im Arbeitsbaum, alle gitignoriert:** `outputs/wp_n13_bytecheck/`,
`analysis/tables/wp_n13_bytecheck/`, `.pytest_tmp/`. Können weg, stören aber nicht.

---

## 7. Arbeitsweise — was eine neue Sitzung wissen muss

**Codex-Handschlag.** Claude schreibt `codex/CURRENT_TASK.md` und startet die Sitzung selbst per
`codex exec`; Codex schreibt ausschließlich `codex/STATUS.md`. **Julia kann Codex hier nicht
ausführen** — Julia-Pakete werden geschrieben, als `blocked` gemeldet, Claude fährt die Abnahme.
**Python läuft normal**, dort fährt Codex die Abnahme selbst und meldet `done`.

**Drei Startfallen, alle real aufgetreten:**

- `codex exec` mit `nohup ... &` meldet **sofort exit 0**, während der Kindprozess weiterläuft. Am
  10.09. sind so **drei gleichzeitige Sitzungen** am selben Auftrag entstanden. Immer als getrackten
  Hintergrundprozess starten, und **vor jedem Neustart** die Prozessliste prüfen:
  `Get-CimInstance Win32_Process -Filter "Name='codex.exe'"`. Die Sitzung des VS-Code-Plugins ist an
  `.vscode\extensions\openai.chatgpt-*` in der Kommandozeile erkennbar und gehört nicht dazu.
- Codex **löscht** `STATUS.md` manchmal, statt sie zu überschreiben.
- Bei einem Absturz bleibt `status: working` stehen. **Immer beides prüfen: Working Tree und
  CPU-Zeit**, nie nur `STATUS.md`. Ein leerer Log ist kein Beleg für einen toten Lauf.

**Den Reports nicht blind glauben.** Alle drei gravierenden Befunde dieser Sitzung standen in
keinem Report — sie kamen aus Gegenlesen und Ausführen. Bewährt hat sich: **eine reale Zelle
bitgleich gegen `HEAD`** (Julia) und **Ableitungen an Ort und Stelle neu erzeugen, `git status` muss
leer bleiben** (Python). Letzteres deckt 43 von 45 Phase-B-Dateien ab.

**Lange Läufe startet ausschließlich der Nutzer.** Claude bereitet vor, prüft, gibt die Kommandos im
Chat aus — mit Zweck, Dauer, Pass-Kriterium und ob die Ausgabe gebraucht wird.

**Wall-clock ist nie Evidenz** (Designprinzip 7). **Immer beide Metriken** (Designprinzip 9):
Strukturtreffer **und** Anteil R² > 0,9. **Kein Mittelwert oder Median als Effektstärke** —
Quantile und Schwellengitter, und die Schwelle wird nie nach Sicht der Daten gewählt.

---

## 8. Wenn dieses Dokument alt ist

Prüfe zuerst `git log --oneline -10` und die obersten Einträge in `DIARY.md`. Weicht der HEAD von
`c049f6b` ab, ist alles in Abschnitt 2 bis 4 vermutlich überholt — dann gilt `CLAUDE.md`, und dieses
Dokument gehört neu geschrieben statt geflickt.
