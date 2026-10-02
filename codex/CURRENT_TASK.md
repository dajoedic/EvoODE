# WP-N39 (Fortsetzung 2) — das PySR-Image baut nicht
**Language: Python** (Docker-Build-Dateien)

WP-N39 ist abgenommen und committet (`4987ce2`). Dieses Paket betrifft nur den Build.

## Befund (Claude, `docker build -f baselines/Dockerfile.pysr -t evoode-pysr:wp-n39 .`, 2026-10-02)

```
ERROR: failed to compute cache key: "/baselines/requirements-pysr.txt": not found
```

Die Ursache ist die Root-`.dockerignore`, die nur das Julia-Kampagnen-Image freigibt. Die
ODEFormer-Images haben dafür je eine eigene `baselines/Dockerfile.odeformer-*.dockerignore`
(BuildKit-Konvention `<Dockerfile>.dockerignore`). Für PySR fehlt sie.

Zweiter Punkt: Das Dockerfile installiert nur die Python-Pakete. `juliacall`/`juliapkg` lädt Julia und
`SymbolicRegression.jl` erst beim ersten `import pysr` herunter und kompiliert sie. Das würde in
jedem Container-Lauf neu passieren, mit Netzwerkzugriff und ungepinnter Laufzeit des
Ersteinrichtens.

## Umsetzung

1. `baselines/Dockerfile.pysr.dockerignore` nach dem Muster von
   `baselines/Dockerfile.odeformer-reference.dockerignore`. Freigegeben wird nur, was der Runner
   braucht (`baselines/`, `analysis/`, `benchmarks/data/`), ohne `__pycache__`.
2. Im Dockerfile nach der Paketinstallation ein Build-Schritt, der Julia und das PySR-Backend
   installiert und vorkompiliert, sodass ein Container-Lauf **ohne Netzwerk** startet. Wie PySR
   1.5.9 das vorsieht (z. B. `python -c "import pysr"` bzw. die dokumentierte Install-Routine):
   Quelle zitieren. Julia-Version und Backend-Version ins Image-Label oder in eine Datei schreiben,
   der Runner übernimmt sie in jeden Record.
3. Im Report den Image-Tag `evoode-pysr:wp-n39` verwenden (bisher `evocode-…`) und die
   `docker run`-Befehle für Git Bash auf Windows angeben: `MSYS_NO_PATHCONV=1`, Volume als
   `C:/…:/workspace/EvoODE`, `--cpus=1`.

## Verboten

Wie WP-N39. Keine PySR-Läufe, keine Builds (die fährt Claude). Git, `oc`.

## Abnahme

Report ergänzt, `STATUS.md` nach Protokoll. Claude baut und fährt den Smoke.
