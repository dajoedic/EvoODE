# WP-T1f-b — Korrektur nach dem Smoke: Vergleich trotz erschöpftem Budget, Kontrollmodus, Pfad-Label
**Language: Julia**

## Ausführung

Codex kann in dieser Umgebung kein Julia ausführen (`codex/CODEX_PROTOCOL.md`). Umsetzen, Befehle für
Claude im Report auflisten, Status `blocked` melden. Keine Git-Operationen, kein `oc`/`kubectl`,
kein Lauf der Probe.

## Ausgangslage

WP-T1f ist umgesetzt (`codex/reports/REPORT_WP_T1f.md`, uncommittet im Working Tree). Tests,
Self-Test und ein lokaler Smoke (Systeme 24 und 52, IC 1) liefen bei Claude. Die Kontrolle stimmt
(6e-14 bzw. 2e-15), der Boden liegt bei ~1e-15.

**Der Defekt:** Ein Fit, der am Optimum startet, bricht nicht ab. BFGS sucht bei ~1e-15 im
numerischen Rauschen weiter, bis `bfgs_max_loss_evals = 20000` erschöpft ist. Das trifft den Boden
in **jeder** Zelle und alle `add_one`-Nachbarn. Die aus WP-T1d übernommene Regel in
`log10_loss_ratio` (`wp_t1d_neighbourhood_loss.jl`) gibt `nothing` zurück, sobald eine Seite das
Budget erschöpft hat. Im Smoke ist deshalb **jede** `log10_loss_ratio` leer und `beats_floor`
überall `false` — ein leerer Befund, kein echter. Für kalte Fits bedeutete „Budget erschöpft“
„nicht konvergiert“; für warme Fits ist es der Normalfall und kein Ungültigkeitsgrund.

## Die Korrektur (vorab festgelegt, nicht verändern)

1. **Vergleich immer auf den rohen Losses.** In den WP-T1f-Rohzeilen wird das Verhältnis
   Nachbar/Boden immer berechnet, solange beide Losses endlich sind und kein Wächterwert vorliegt.
   `beats_floor` folgt daraus. Zusätzlich je Zeile ein Feld `comparison_budget_stratum` mit den
   Werten `neither_exhausted`, `neighbour_exhausted`, `floor_exhausted`, `both_exhausted`.
   Die Budget-Flags beider Seiten bleiben wie bisher in der Zeile.
2. **Aggregation berichtet beides**, pro Dimension und Nachbarklasse, nie über Klassen summiert:
   (a) alle vergleichbaren Zeilen, (b) nur `neither_exhausted`, (c) die Zählung je Schicht.
   Das volle Margin-Raster (`WP_T1D_MARGIN_FACTORS`) und die Quantile gelten für (a) und (b).
   Für die Variante `cold_reference` (alte WP-T1d-Rohzeilen) gilt dieselbe Aggregation: Die alten
   Zeilen tragen `loss_true`, `loss_neighbor`, `budget_exhausted_true`, `budget_exhausted_neighbor`,
   daraus werden Verhältnis und Schicht in der Aggregation neu berechnet. So stehen kalt und warm
   nach identischer Regel nebeneinander.
3. **`wp_t1d_neighbourhood_loss.jl` bleibt unverändert**, auch `log10_loss_ratio` dort. Die neue
   Regel lebt in `wp_t1f_warm_neighbourhood.jl`.
4. **Neuer Modus `--control-only`:** berechnet für **alle 36 Zellen** nur den Kontroll-Loss (ein
   Loss-Aufruf an den wahren Parametern, keine Optimierung) und schreibt eine CSV mit System, IC,
   Dimension und Kontroll-Loss nach `outputs/wp_t1f_warm_neighbourhood/control_only.csv`. Er bricht
   **nicht** beim ersten Wert über `1e-4` ab, sondern schreibt alle 36 und meldet am Ende die Liste
   der Zellen über der Grenze und einen Exit-Code ≠ 0, falls es solche gibt.
5. **Pfad-Label:** `t1f_analysis_dir_for` liefert bei einem `--input-dir` mit abschließendem
   Schrägstrich ein leeres Label und fällt auf `aggregate` zurück. Abschließende Trenner vor
   `basename` entfernen.

## Verboten

- Keine Änderung an Schwellen (`1e-4`, `1e-8`, `1e-3`), an m, an den Margins, am Optimierer, am
  Loss-Budget oder an den Manifesten.
- Keine Änderung an `wp_t1d_neighbourhood_loss.jl` und an `src/`.

## Abnahme

1. `test/test_wp_t1f_warm_neighbourhood.jl` erweitert: Ein Vergleich mit erschöpftem Boden-Budget
   liefert ein Verhältnis und die richtige Schicht; ein Wächterwert liefert keins; die Aggregation
   weist (a), (b), (c) getrennt aus; die `cold_reference`-Aggregation rechnet nach derselben Regel;
   das Pfad-Label mit und ohne Schrägstrich ist gleich.
2. Report `codex/reports/REPORT_WP_T1f_b.md` mit den Julia-Befehlen für Claude: Test, `--self-test`,
   `--control-only`, `--smoke --fresh`, `--aggregate-only` auf
   `outputs/wp_t1d_neighbourhood/orion_5a87efb`. `SCRIPTS.md`, Abschnitt WP-T1f, um
   `--control-only` ergänzen.
3. `codex/STATUS.md`: `status: blocked`, WP-T1f-b, Report-Pfad.
