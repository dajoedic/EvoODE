# WP-N22 — ODEFormer: Konstantenoptimierung und das Vier-Konfigurationen-Raster
**Language: Python**

## Ausführung

Wie WP-N21: Codex schreibt und testet lokal, was ohne ODEFormer geht. Images bauen und fahren
macht Claude. Fertig ohne Ausführung → `blocked`, *Umgebung, nicht Sache*.

ODEFormer-Quelle am Pin: `outputs/third_party/odeformer/` (lesbar, nicht verändern). Jede Aussage
über ODEFormer mit Datei:Zeile.

## Entschieden (nicht neu verhandeln)

`docs/paper1_phaseC_benchmark_plan.md`, Absatz „ODEFormer arm — decided 2026-09-23":

- Publizierte Zahlen aus dem **Referenz-Image** (`baselines/Dockerfile.odeformer-reference`),
  dasselbe Raster im **Kandidaten-Image** als Sensitivitätsprüfung.
- **Vier Konfigurationen, alle berichtet, keine ausgewählt:** Beam-Größe 10 und 50, jeweils ohne
  und mit ODEFormers eigener Konstantenoptimierung.
- Ein Lauf je Zelle und Konfiguration — die Ausgabe ist je Umgebung deterministisch, der Seed ist
  wirkungslos (`odeformer/model/transformer.py:495`).
- **Nur ODEFormer** in diesen Images. SINDy läuft in seiner eigenen Umgebung (pysindy 2.1.0 braucht
  `numpy >= 2.0`, ODEFormer `numpy==1.23.5`).

## Teil 1 — Konstantenoptimierung

`param_optimizer.py` enthält `ConstantOptimizer`; im ODEFormer-Repository ruft ihn niemand auf.
Der Adapter bindet ihn als optionalen Nachschritt nach der Formelerzeugung ein:

- **ODEFormers Klasse unverändert benutzen**, nicht nachbauen, nicht patchen.
- **Alle Einstellungen aus ODEFormers eigenen Voreinstellungen** in dieser Klasse (Startwerte,
  Zielfunktion, Optimierer, Abbruch), jede mit Datei:Zeile belegt. Wo die Klasse einen Wert
  verlangt, den sie nicht vorgibt, ist die naheliegende Wahl die, die die Formel nicht verändert
  (etwa Start von ODEFormers eigenen Konstanten statt Zufall) — begründen, und als bewusste Wahl im
  Report kennzeichnen.
- Optimiert wird auf der **Fit-Trajektorie**. Die Generalisierungs-Trajektorie sieht der
  Optimierer nie.
- Record-Felder: vor und nach der Optimierung der Ausdruck, beide R²-Aggregationen für
  Rekonstruktion und Generalisierung **vor und nach**, Zahl der Iterationen und
  Zielfunktionsauswertungen, Abbruchgrund. Scheitert die Optimierung, bleibt der nicht optimierte
  Ausdruck das Ergebnis dieser Konfiguration und der Record sagt das ausdrücklich — kein stiller
  Rückfall.

## Teil 2 — Das Raster

Ein Konfigurationsobjekt je Konfiguration unter `baselines/configs/`, mit stabiler Kennung
(z. B. `beam10_noopt`, `beam10_opt`, `beam50_noopt`, `beam50_opt`), die jeder Record trägt.

Ein Runner, der für eine gegebene Umgebung **alle 63 Systeme × beide Anfangsbedingungen × vier
Konfigurationen** rechnet — 504 Records — und dabei:

- Records zellweise und **atomar** schreibt (temporäre Datei, dann umbenennen), sodass ein
  Abbruch nichts Halbes hinterlässt;
- **fortsetzbar** ist: bereits vorhandene vollständige Records werden übersprungen, nicht neu
  gerechnet;
- eine **Teilmenge** rechnen kann (Systemliste, Konfigurationsliste), damit Claude erst eine
  Zeitmessung auf wenigen Zellen fahren kann;
- ein **Zeitbudget je Zelle** kennt: Überschreitet eine Zelle es, wird sie als `timeout` markiert
  und der Lauf geht weiter. Wert konfigurierbar, im Report einen Vorschlag begründen;
- das Modell **einmal je Prozess** lädt, nicht je Zelle;
- optional **nach Index shardbar** ist (Indexed Job wie die Kampagne), falls die Zeitmessung ergibt,
  dass der Lauf auf den Cluster muss. Nur vorbereiten — keine Manifeste schreiben.

Records in dem Schema aus WP-N21, erweitert um Teil 1 und die Konfigurationskennung, plus
Umgebungskennung (`reference` / `candidate`) und Image-relevante Versionen.

## Teil 3 — Zusammenfassung

Ein Skript, das die Records einer oder beider Umgebungen zu Tabellen verdichtet: je Umgebung ×
Konfiguration × Dimension der Anteil R² > 0.9 für Rekonstruktion und Generalisierung, **beide**
Aggregationen (arithmetisch und varianzgewichtet) getrennt, Zahl der Fehler/Timeouts, und die
Zahl der Zellen mit identischem Ausdruck zwischen Referenz und Kandidat. Keine Mittelwerte als
Effektgröße; Zählungen und Anteile. Ausgabe unter
`analysis/data/paper1_phaseC_v1/odeformer_baseline/`.

## Verboten

- Keine Git-Operationen.
- `outputs/third_party/odeformer/` nicht verändern; ODEFormer nicht patchen oder monkeypatchen.
- Keine Einstellung wählen, die nicht aus ODEFormers Code belegt oder als bewusste Wahl begründet
  ist. Kein Tuning auf unseren Daten, keine Auswahl der „besten" Konfiguration.
- Den SINDy-Pfad nicht anfassen, außer das gemeinsame Schema erzwingt es.
- Nicht anfassen: `containers/`, `.gitlab-ci.yml`, `Project.toml`, `Manifest.toml`, `src/`,
  `studies/`, `experiments/`, `k8s/`.
- Keine Cluster-Jobs, keine Manifeste. Nichts, was länger als 15 Minuten läuft.

## Abnahme

1. Konstantenoptimierung über ODEFormers `ConstantOptimizer`, jede Einstellung belegt oder
   begründet; Vorher/Nachher-Felder im Record; kein stiller Rückfall.
2. Vier Konfigurationsdateien mit stabilen Kennungen.
3. Runner: atomar, fortsetzbar, Teilmengen, Zeitbudget je Zelle, Modell einmal geladen, shardbar.
4. Zusammenfassungsskript mit den Tabellen aus Teil 3.
5. `python -m pytest baselines/tests -q` lokal grün; neue Tests für Fortsetzbarkeit, atomares
   Schreiben, Timeout-Markierung und Zusammenfassung, mit Eingaben aus echten Exporten.
6. Report `codex/reports/REPORT_WP_N22.md` mit den **exakten Befehlen** für Claude — immer mit
   `--entrypoint python`, weil das Image-Entrypoint der Harness ist, und mit eingebundenem
   `baselines/` — für: (a) Images neu bauen, (b) Zeitmessung auf den Systemen 1, 2, 24 und einem
   dim-3-System über alle vier Konfigurationen, (c) den vollen Lauf je Umgebung, (d) die
   Zusammenfassung. Je Befehl erwartete Ausgabe und Pass-Kriterium.
