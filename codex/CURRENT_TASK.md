# WP-N39 (Fortsetzung 3) — zwei PySR-Versionen: 0.19.x (wie ODEFormer) und 1.5.9
**Language: Python** (Docker-Build-Dateien und Harness)

WP-N39 ist committet (`093cbe4`). **Weiterarbeiten, nicht neu anfangen.**

## Befund (Claude, Smoke, 2026-10-03)

Das Image `evoode-pysr:wp-n39` baut, startet ohne Netzwerk und schreibt die Metadaten (PySR 1.5.9,
Julia 1.13.1, SymbolicRegression.jl 1.11.3). Jeder Fit bricht aber ab mit:

```
TypeError: `equation_file` is not a valid keyword argument for PySRRegressor.
```

ODEFormer pinnt PySR nirgends (`outputs/third_party/odeformer/requirements.txt`, `setup.cfg`). Sein
Wrapper (`pysr_wrapper.py:23-55`) benutzt aber die API von **vor PySR 1.0**. Der Nutzer hat
entschieden: **beide Varianten testen und berichten.**

## Umsetzung

1. **Zwei Images, beide gepinnt:**
   - `baselines/Dockerfile.pysr` mit `baselines/requirements-pysr.txt`: PySR 1.5.9, wie bisher.
   - `baselines/Dockerfile.pysr-legacy` mit `baselines/requirements-pysr-legacy.txt` und eigener
     `.dockerignore`: die **letzte PySR-0.x-Version, die alle Argumente aus ODEFormers Wrapper
     akzeptiert**. Bestimme sie aus PySRs Changelog bzw. Quelltext und zitiere die Quelle (vermutlich
     0.19.4). Dazu passende Julia/juliacall-Pins, sodass der Build reproduzierbar bleibt. Genauso
     mit Backend-Vorkompilierung, Offline-Start und Metadatei.
2. **Harness für beide APIs.** Der Adapter erkennt die installierte PySR-Version. Unter 0.x gehen
   die Argumente **wörtlich wie in ODEFormers Wrapper** hinein. Unter 1.x werden nur
   **nicht-algorithmische** Argumente umbenannt (`equation_file` → `output_directory`/`run_id` bzw.
   das 1.x-Äquivalent, Quelle zitieren). Alles Algorithmische bleibt gleich. Jeder Record trägt
   `pysr_api` (`legacy_0x` / `v1`) und die Liste der umbenannten Argumente.
3. **Default-Differenzen deklarieren:** In `docs/WP-N39.md` eine Tabelle aller
   `PySRRegressor`-Parameter, die ODEFormer **nicht** explizit setzt und deren Default sich zwischen
   der Legacy-Version und 1.5.9 unterscheidet (Populationen, Populationsgröße, Parsimony,
   `maxsize`, `ncycles_per_iteration`, Optimizer-Einstellungen usw.). Beide Werte mit Quelle
   (Quelltext der jeweiligen Version). Keine dieser Defaults wird angeglichen, beide Varianten
   laufen mit ihren eigenen Defaults.
4. Der Output-Pfad der Varianten wird über eine Option bzw. den Image-Tag getrennt. Records beider
   Versionen dürfen nicht im selben Ausgabeordner landen, ohne dass `pysr_api` sie unterscheidet.
5. Im Report die Build- und Smoke-Befehle für **beide** Images (Git Bash: `MSYS_NO_PATHCONV=1`,
   `C:/…`-Volume, `--cpus=1`, `--network none`). Smoke auf System 1, (σ 0,01; ρ 0), Seed 1,
   `--limit 1`.

## Verboten

Wie WP-N39. Algorithmische Argumente zwischen den Versionen angleichen. Keine Builds, keine
PySR-Läufe (die fährt Claude). Git, `oc`.

## Abnahme

Tests grün, und zwar auch ein Test, der die Argumentabbildung für beide API-Varianten ohne
installiertes PySR prüft. `docs/WP-N39.md` mit Versionsbegründung und Default-Tabelle, Report,
`STATUS.md` nach Protokoll.
