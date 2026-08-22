> **Claude-Status:** `waiting for codex` — WP-H7 übergeben. Melde dich über `codex/STATUS.md`,
> nicht in dieser Datei. Committe nichts.
> Der Dauerauftrag steht in `codex/CODEX_PROTOCOL.md`.

# WP-H7 — Kampagnen-Job und eine Startreihenfolge, die den Schwanz nicht ans Ende legt
**Language: Julia**

## Warum

Die Kampagne ist startbereit: Fingerprints verifiziert (`604e79733b22d64d` / `17fe7d9cfb8f1be3` /
`ffb0266c7913352c`), Manifest erzeugt, 756 Zeilen mit 756 eindeutigen Identitäten. Zwei Dinge
fehlen, bevor `oc apply` sinnvoll ist.

**Erstens gibt es kein Kampagnen-Manifest.** In `k8s/` liegen Bootstrap, Einzelzelle und ein
Smoke-Job über drei Zellen. Der Job für die 756 Zellen existiert nicht.

**Zweitens ist die Startreihenfolge ungünstig.** Ein Indexed Job teilt nicht statisch auf: Der
Controller hält `parallelism` Pods am Leben und startet beim Freiwerden den nächsten Index. Kein
Kern fällt trocken, solange Arbeit da ist. Was am Ende zählt, ist deshalb nicht die Lastverteilung,
sondern **wann die längste Zelle gestartet wurde**.

Das Manifest ist nach `system_id` sortiert, und die Dimensionsklassen liegen darin in
zusammenhängenden Blöcken: dim 1 sind die Systeme 1–23, dim 2 die 24–51, dim 3 die 52–61, dim 4 die
62–63. Die teuerste Klasse liegt damit **hinten**. Nach den Messungen in `docs/hpc_requirements.md`
§2 kostet eine dim-3-Zelle im Mittel 63.800 s, eine dim-2-Zelle 10.440 s, dim 4 rund 2.300 s und
dim 1 rund 250 s — die teure Klasse käme also zuletzt dran und hinge ihre Laufzeit an ein bereits
fast fertiges Feld. Grob gerechnet sind das rund zehn Tage statt rund acht.

**Die Reihenfolge ist wissenschaftlich neutral.** Jede Zelle rechnet dasselbe, `manifest_index`
wird mitgeschrieben, kein Fingerprint ändert sich. Es geht ausschließlich darum, in welcher
Reihenfolge der Cluster die Schlange abarbeitet. Genau deshalb darf diese Änderung auch nichts
anderes anfassen als die Reihenfolge.

## Auftrag

### 1. Eine kostensortierte Indexliste

`studies/regression/generate_phase_b_manifest.jl` schreibt bereits `indices_all.txt` mit allen 756
Zeilen sowie die vier Listen je Dimension. Ergänze **eine weitere** Liste, die dieselben 756 Indizes
in absteigender erwarteter Kosten-Reihenfolge enthält.

- Sortierschlüssel ist das **gemessene Mittel der Dimensionsklasse** aus
  `docs/hpc_requirements.md` §2. Nach diesen Zahlen ergibt sich die Klassenreihenfolge
  dim 3, dim 2, dim 4, dim 1 — leite sie aus den Werten ab, statt sie als Reihenfolge hinzuschreiben,
  damit sichtbar bleibt, woher sie kommt.
- Innerhalb einer Klasse bleibt die bestehende Reihenfolge des Manifests erhalten. Die Sortierung
  muss **stabil** und vollständig deterministisch sein.
- Kein System wird namentlich bevorzugt. Einzelne teure Systeme innerhalb einer Klasse bleiben
  unberücksichtigt; das ist eine bewusste Vereinfachung und gehört in den Report.
- Die vier Klassenmittel gehören als benannte Konstanten mit Quellenangabe in den Code, nicht als
  nackte Zahlen in eine Sortierfunktion.
- Die bestehenden Listen bleiben unverändert und werden weiterhin geschrieben.

### 2. Der Kampagnen-Job

Ein neues Manifest in `k8s/`, benannt wie die vorhandenen. Es orientiert sich an
`k8s/phase_b_indexed_smoke_job.yaml` — gleiche Struktur, gleiche Labels, gleiche
Ressourcenanforderung von einem Kern und 2 GB, gleiche NFS-Einbindung, `restartPolicy: Never`,
`ttlSecondsAfterFinished`, `<COMMIT_SHA>` als Platzhalter.

Unterschiede:

- `completions` entspricht der vollen Kampagne, `parallelism` ist **16** — das ist die mit dem
  Standort vereinbarte Kapazität und darf nicht überschritten werden.
- Die Indexliste ist die aus Punkt 1.
- Ausgabeverzeichnis und Manifestpfad zeigen in ein Kampagnenverzeichnis, nicht in ein
  Smoke-Verzeichnis. Halte dich an das Namensmuster, das die bestehenden Manifeste und
  `docs/hpc_deployment_guide.md` verwenden.
- `backoffLimit`: Eine Zelle, die zweimal scheitert, soll nicht endlos wiederholt werden. Begründe
  den gewählten Wert kurz im Report.

### 3. Der Runbook-Eintrag

`SCRIPTS.md` bekommt die Startreihenfolge für die Kampagne: Bootstrap, Prüfung der erzeugten
Dateien, Start der Zellen, Beobachtung, Aufräumen. Kurz und in derselben Form wie die vorhandenen
Einträge. Die Befehle stehen in `docs/hpc_deployment_guide.md` §7 — verweise darauf, statt sie
ein zweites Mal zu pflegen.

## Verboten

- **Keinen Cluster-Job starten.** Kein `oc`, kein `kubectl`, kein `apply`, auch nicht „nur zum
  Testen". Das Manifest wird geschrieben, nicht angewendet.
- **Keine Kampagnen-, Regressions- oder Sondierungsläufe**, lokal ebenso wenig.
- Nichts am Suchpfad, an `phase_b_config.jl`, am Support oder an den Varianten. Wenn deine Änderung
  einen Fingerprint bewegt, hast du zu viel angefasst — dann `blocked` melden.
- Keine Git-Operationen.

## Abnahme

Alles hier läuft in Sekunden bis Minuten.

1. **Manifest neu erzeugen** und zeigen, dass `phase_b_fingerprint` weiterhin `604e79733b22d64d`
   lautet und `rows=756` mit `unique_identities=756` gilt.
2. **Die neue Liste ist eine echte Permutation:** 756 Zeilen, jeder Index aus dem Manifest genau
   einmal, keiner fehlt, keiner doppelt. Prüfe das programmatisch und nenne die Zahlen.
3. **Die Reihenfolge stimmt:** Nenne die ersten und letzten fünf Einträge und die Position, an der
   die Klasse wechselt. Erwartung: die 120 dim-3-Zeilen stehen vorn, die 276 dim-1-Zeilen hinten.
4. **Zweimal erzeugen ergibt dieselbe Datei** — byteidentisch.
5. Das neue YAML ist wohlgeformt und lässt sich parsen; `completions` und `parallelism` tragen die
   verlangten Werte.

## Report

`docs/WP-H7.md`, kurz: die abgeleitete Klassenreihenfolge samt Zahlen, der gewählte `backoffLimit`
mit Begründung, die fünf Abnahmepunkte, und ausdrücklich der Satz, dass kein Cluster-Job gestartet
wurde.
