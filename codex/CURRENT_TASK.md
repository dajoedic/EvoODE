# WP-N3b — Laufzeitfehler in `wp_n3_oracle_refit.jl` beheben

**Language: Julia**

## Lage

Der Auftrag WP-N3 ist inhaltlich unveraendert gueltig (siehe `codex/REPORT_WP_N3.md` fuer den
bisherigen Stand). Das Skript `studies/regression/wp_n3_oracle_refit.jl` liegt vor, wurde von Claude
ausgefuehrt und **stuerzt sofort ab**, bevor eine einzige Zelle gerechnet wird.

**Du kannst Julia in dieser Umgebung nicht starten** (`A specified logon session does not exist`),
also auch diesen Fix nicht selbst verifizieren. Claude fuehrt den Lauf aus und meldet zurueck. Das
macht diesen Auftrag anders als sonst: **du arbeitest blind, und jede Runde kostet einen vollen
Durchlauf.** Entsprechend sorgfaeltig ist das ganze Skript durchzusehen, nicht nur die gemeldete
Zeile.

## Der gemeldete Fehler

Kommando:

```
julia --project=. --startup-file=no studies/regression/wp_n3_oracle_refit.jl --input outputs/wp_n1_dim1_probe/history.jsonl --output-dir outputs/wp_n3_oracle_refit --fresh
```

Ausgabe:

```
WP-N3 fingerprint: abb604eb07ba4223
Input: outputs/wp_n1_dim1_probe/history.jsonl
Output: outputs/wp_n3_oracle_refit
Cells requested: 132
ERROR: LoadError: MethodError: no method matching sort(::Set{Int64})

Stacktrace:
  [1] (::var"#_intersect_terms##0#_intersect_terms##1")(::Tuple{Vector{Int64}, Vector{Int64}})
  [4] _intersect_terms  studies/regression/wp_n3_oracle_refit.jl:131
  [5] _run_record       studies/regression/wp_n3_oracle_refit.jl:244
  [6] main              studies/regression/wp_n3_oracle_refit.jl:478
```

Die verursachende Zeile 131:

```julia
return [sort(intersect(Set(found_eq), Set(true_eq))) for (found_eq, true_eq) in zip(found, truth)]
```

`intersect` auf zwei `Set` liefert ein `Set`, und `sort` nimmt kein `Set`. Es fehlt ein `collect`
oder der Umweg ueber `Set` ist ueberfluessig.

## Auftrag

1. **Diesen Fehler beheben.**

2. **Das gesamte Skript auf gleichartige Laufzeitfehler durchsehen**, die ein Typprueflauf nicht
   findet: Operationen auf `Set` statt `Vector`, `JSON3.Object` dort, wo ein `Dict` erwartet wird,
   fehlende `collect`-Aufrufe, Indizierung mit `nothing`, Zugriffe auf Felder, die im Record fehlen
   koennen (`model_terms`, `wp_n1_expected_support_terms`, `basis_name`), und Zellen, deren
   Wahrheit `nothing` ist. Jede Stelle, an der du etwas aenderst, im Report benennen.

3. **Einen billigen Selbsttest einbauen oder vorbereiten**, der ohne vollen Lauf zeigt, dass die
   Datenpfade tragen — etwa ein `--limit`-Pfad ueber wenige Zellen, den Claude in Sekunden
   ausfuehren kann, bevor die vollen 132 gerechnet werden. Falls `--limit` schon existiert, halte im
   Report fest, wie es zu benutzen ist.

**Aendere nichts an der Fragestellung von WP-N3.** Die beiden Nachanpassungen — Oracle-Beschneidung
und suchfreie Referenzanpassung — und die Berichtspflicht fuer **beide** Metriken (Strukturtreffer
und Anteil R2 > 0,9, Design-Prinzip 9) bleiben unveraendert.

## Verboten

- keine Aenderung an der Suchlogik, der Basis, am Stage-Cap oder an `pruned_match`
- keine Aenderung an `outputs/wp_n1_dim1_probe/`, an der Kampagne oder an den A5-bis-A9-Skripten
- **keine erfundenen Ergebnisse** — du kannst nicht ausfuehren, also berichte auch nichts, was einen
  Lauf voraussetzt
- keine Ergebnisse in `PAPER_1.md`, `CLAUDE.md` oder `DIARY.md`
- kein `git add -A`, keine Git-Operationen

## Akzeptanzkriterium

Das Skript enthaelt keine der oben genannten Fehlerklassen mehr, so weit statisch pruefbar. Im Report
steht das genaue Kommando fuer einen kurzen Testlauf ueber wenige Zellen **und** das Kommando fuer
den vollen Lauf ueber 132 Zellen.

## Report

`codex/REPORT_WP_N3b.md`. Enthaelt: jede geaenderte Stelle mit Begruendung, die Liste der zusaetzlich
geprueften Fehlerklassen und ihr Ergebnis, sowie die beiden Kommandos.
