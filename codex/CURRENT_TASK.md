# WP-N11b — Zwei Defekte aus der Abnahme von WP-N11

**Language: Julia**

## Ausgangslage

WP-N11 ist inhaltlich richtig umgesetzt. Die Abnahme durch Claude hat ergeben:

- Fehlschlag-Prädikat, k = 1 ohne Wiederholung, Annahme des zweiten Versuchs, Erschöpfung aller
  Versuche: **grün**.
- `phase_b_fingerprint()` = `604e79733b22d64d`, `config_fingerprint()` = `17fe7d9cfb8f1be3`,
  `stage_cap_behavior_fingerprint()` = `ffb0266c7913352c` — alle drei **unverändert**.
- `test/test_bfgs_budget.jl` und `test/test_bfgs_fallback_order.jl`: **grün**.

Zwei Defekte bleiben. Beide sind durch Ausführung belegt, nicht vermutet.

## Defekt 1 — das Paket präkompiliert nicht mehr (blockierend)

`_append_unique_strings!` ist jetzt **zweimal mit identischer Signatur im Modul `EvoODE`** definiert:
`src/optimize/bfgs.jl:148` (neu) und `src/structure/evogrow.jl:509` (bestand vorher). Julia meldet
bei jedem Start:

```text
WARNING: Method definition _append_unique_strings!(Array{String, 1}, Any) in module EvoODE
at src/optimize/bfgs.jl:148 overwritten at src/structure/evogrow.jl:509.
ERROR: Method overwriting is not permitted during Module precompilation.
```

Die Bodies sind zeichengleich, das Verhalten ist also korrekt — **aber die Präkompilierung schlägt
fehl und jeder Julia-Start zahlt die volle Kompilierzeit.** Bei einer Kampagne mit 378 Pods trifft
das jede einzelne Zelle.

**Was zu tun ist:** genau **eine** Definition im Modul. Ort so wählen, dass der Optimierer nicht von
der Suchschicht abhängt — `bfgs.jl` wird in `src/EvoODE.jl` an Zeile 109 eingebunden, `evogrow.jl`
erst an Zeile 126. Der Helfer wird ausserdem von `evogrow_v3.jl` und `evogrow_screening.jl` benutzt.
Ein eigener kleiner Platz unter `src/utils/`, früh eingebunden, ist die naheliegende Lösung; die
konkrete Wahl ist deine, die Randbedingungen sind: eine Definition, saubere Schichtung, Modul
präkompiliert ohne Warnung und ohne Fehler.

## Defekt 2 — exakter Float-Vergleich im neuen Test

`test/test_bfgs_retry_policy.jl:175` vergleicht mit `==`:

```text
Expression: lval == 0.25
Evaluated:  0.24999999999999994 == 0.25
```

Das ist ein Testfehler, kein Codefehler. Verwende einen Toleranzvergleich. **Gehe die ganze Datei
durch** und ersetze jeden exakten Gleichheitsvergleich auf Fliesskommawerte; belasse exakte
Vergleiche nur dort, wo sie beabsichtigt sind, etwa bei Zählern.

## Verboten

- **Keinen langen Lauf starten.** Weder Kampagne noch Regressionszelle.
- **Keine inhaltliche Änderung an der Retry-Logik.** Sie ist abgenommen. Diese Aufgabe repariert
  ausschliesslich die beiden genannten Punkte.
- **`phase_b_fingerprint()`, `config_fingerprint()` und `stage_cap_behavior_fingerprint()` nicht
  anfassen**, und die Fingerprint-Eingaben ebenfalls nicht.
- Keine Umbenennung bestehender Metriken.

## Abnahme

Julia lässt sich in dieser Umgebung nicht ausführen; melde `blocked`, Claude fährt die Abnahme.

Im Report brauche ich:

- wo die eine verbliebene Definition jetzt liegt und warum dort,
- die Liste der geänderten Dateien mit je einem Satz,
- welche Zeilen im Test von exakter auf tolerante Gleichheit umgestellt wurden.

Claude prüft: `julia --project=. -e 'using EvoODE'` läuft **ohne** Präkompilierungswarnung und ohne
Fehler; `test/test_bfgs_retry_policy.jl`, `test/test_bfgs_budget.jl` und
`test/test_bfgs_fallback_order.jl` vollständig grün; die drei Fingerprints unverändert; anschliessend
eine reale Regressionszelle bei k = 1 bitgleich gegen `HEAD`.

Report nach `codex/reports/REPORT_WP_N11b.md`.
