# WP-N9 — Der dim-2-Probelauf über den vorhandenen Cluster-Pfad

**Language: Julia**

## Warum

Der dim-2-Probelauf entscheidet die kanonische Basis für Phase C — der einzige noch offene
eingefrorene Parameter (`docs/paper1_phaseC_benchmark_plan.md`, P2/P3). Er ist **nicht** lauffähig:

- Die Kosten liegen bei **~1.200 Kernstunden**, nicht bei den lange zitierten 114. Nachgerechnet am
  dim-2-Arm der Kampagne, der dieselben 336 Zellen unter derselben Konfigurationsfamilie hatte:
  1.167,5 h, Mittel 3,47 h je Zelle. Seriell auf einem Rechner sind das rund sieben Wochen.
- `studies/regression/wp_n1_basis_probe.jl` ist eine **serielle Schleife**, die in eine einzige
  `history.jsonl` anhängt. Es hat kein Index- oder Shard-Argument und kann den Cluster-Pfad der
  Kampagne nicht nutzen.

## Der Ansatz — und was ausdrücklich nicht gemacht wird

**Kein Sharding in `wp_n1_basis_probe.jl` einbauen.** Das erzeugte einen zweiten, parallelen
Ausführungspfad neben dem der Kampagne, mit eigener Wiederaufnahme-, Schreib- und Identitätslogik.
Zwei Pfade laufen auseinander; das Projekt hat diese Fehlerklasse gerade zweimal bezahlt
(`exact_support_match` mit zwei Bedeutungen, `git_hash` als Platzhalter).

Stattdessen der vorhandene Weg, unverändert in seiner Struktur:

```text
Manifest-Generator  ->  manifest.csv + Indexliste  ->  run_k8s_indexed_cell.jl  ->  run_batch_cell.jl
```

`run_batch_cell.jl` löst die Methodenkonfiguration bereits über die Spalte `variant` auf
(`phase_b_variant(row["variant"])`). **Die beiden Basis-Modi der Probe gehören deshalb als Varianten
in dieselbe Auflösung**, nicht als Sonderweg.

Das zahlt doppelt: Phase C braucht denselben Mechanismus für den **ungekappten Arm**, der ebenfalls
nur eine Variante derselben Zelle ist. Lege die Erweiterung deshalb so an, dass sie
Methodenkonfiguration je Zeile trägt, und nicht als Einzelfall „Basis".

## Was zu tun ist

1. **Die WP-N1-Basis-Modi als Varianten auflösbar machen.** Die Modi stehen in
   `_wp_n1_basis_modes()` in `studies/regression/wp_n1_basis_probe.jl`; die Auflösung liegt bei
   `phase_b_variant`. Bestehende Kampagnen-Varianten bleiben unverändert — eine Änderung an ihnen
   verändert den Config-Fingerprint und damit die Identität der 756 Kampagnenrecords.
2. **Einen Manifest-Generator für die Probe**, nach dem Muster von
   `studies/regression/generate_phase_b_manifest.jl`. Er erzeugt die Zeilen für
   28 dim-2-Systeme × 2 Basen × 2 IC-Sätze × 3 Seeds = **336 Zellen**, plus die Indexliste, die
   `run_k8s_indexed_cell.jl` erwartet.
3. **Ein k8s-Job-Manifest** nach dem Muster von `k8s/phase_b_indexed_campaign_job.yaml` und
   `k8s/phase_b_indexed_smoke_job.yaml` — beides, ein Smoke-Job über wenige Zellen und der volle
   Lauf. Ressourcenanforderungen aus dem Kampagnen-Manifest übernehmen, nicht neu erfinden.
4. **Die Identitätsfelder müssen erhalten bleiben.** Die Records tragen weiterhin echten git-Hash,
   Config-Fingerprint und Behaviour-Fingerprint, und der WP-N8-Wächter darf nicht umgangen werden.
   Ein Cluster-Lauf ohne ermittelbare Identität nutzt den in `containers/Dockerfile` eingebackenen
   `EVOODE_GIT_SHA` — sieh nach, wie `git_provenance()` das behandelt.

## Abnahme

**Der entscheidende Punkt ist Äquivalenz, nicht Funktion.** Ein neuer Ausführungspfad, der andere
Zahlen liefert als der alte, ist wertlos für eine Konfigurationsentscheidung.

1. **Äquivalenznachweis auf dim 1.** Lasse einige dim-1-Zellen über den neuen Manifest-Pfad laufen
   und vergleiche gegen die vorhandenen Records in `outputs/wp_n1_dim1_probe/history.jsonl`. Für
   dieselbe Kombination aus Basis, System, IC-Satz und Seed müssen `loss`, `pruned_match` und die
   gefundene Termmenge übereinstimmen. Nenne im Report, welche Zellen du verglichen hast und wie
   genau sie übereinstimmen.
   Die Altdaten tragen `git_hash = "not_collected"` und keine Identitätsfelder — das ist erwartet
   und **kein** Abweichungsgrund; verglichen werden die Ergebnisfelder, nicht die Provenienz.
2. Der Manifest-Generator erzeugt 336 Zeilen für dim 2, und die Indexliste passt dazu.
3. Die erzeugten Records enthalten dieselben WP-N1-spezifischen Felder wie bisher, damit die
   vorhandenen Auswertungsskripte sie lesen können. Prüfe das an
   `analysis/scripts/aggregate/aggregate_wp_n1_coefficient_metrics.py`, welche Felder erwartet
   werden. Fehlt eines, ist das ein Abnahmefehler.
4. Kampagnen-Varianten und deren Fingerprint sind unverändert. Weise das nach.
5. Smoke- und Voll-Manifest liegen vor.

**Julia lässt sich in deiner Sitzung nicht ausführen** — Code schreiben, statisch prüfen,
`status: blocked` melden mit `note: Umgebung, nicht Sache`. Claude fährt die Abnahme, inklusive des
Äquivalenzlaufs.

Weil jede Runde bei Claude einen vollen Durchlauf kostet, geh die geänderten Dateien auf
Laufzeitfehlerklassen durch, die ein statischer Blick übersieht: fehlende Manifestspalten, `Set`
gegen `Vector`, `JSON3.Object` wo ein `Dict` erwartet wird, Indizierung mit `nothing`, Zugriffe auf
Record-Felder, die fehlen können, und Pfade, die nur im Container existieren.

## Verboten

- **Keinen Lauf starten** — weder lokal noch auf dem Cluster, weder dim 1 noch dim 2. Auch keine
  Cluster-Jobs einreichen. Der volle Lauf kostet ~1.200 Kernstunden und wird ausschließlich vom
  Nutzer gestartet.
- **Nichts über 15 Minuten.**
- **Kampagnen-Varianten, `phase_b_config.jl`-Konstanten, den Config-Fingerprint und die
  Ausdünnungsregel nicht verändern.** Die 756 Kampagnenrecords hängen daran.
- **Altdaten unter `outputs/wp_n1_dim1_probe/` nicht verändern.**
- Keine zweite Provenienz-, Fingerprint- oder Wiederaufnahmelogik.
- Den WP-N8-Identitätswächter nicht aufweichen.
- Nicht committen, nicht stagen, keine Git-Operationen.

## Report

`codex/reports/REPORT_WP_N9.md`. Enthält:

- welche Zellen für den Äquivalenznachweis vorgesehen sind und mit welchem Kommando Claude ihn fährt
- den Nachweis, dass die Kampagnen-Fingerprints unverändert sind
- die erwartete Zeilenzahl von Manifest und Indexliste
- **drei Kommandos**: Manifest erzeugen, Smoke-Job, voller dim-2-Lauf — mit erwarteter Zellenzahl.
  Keine erfundenen Ergebnisse
- die durchgesehenen Laufzeitfehlerklassen
