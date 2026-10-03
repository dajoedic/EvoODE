# WP-N41 (Fortsetzung) — `--stage2-cells` vergleicht `clamp_val` als Zeichenkette
**Language: Julia**

WP-N41 ist committet (`66b2004`). **Weiterarbeiten, nicht neu anfangen.**

## Befund (Claude, Bootstrap-Trockenlauf, 2026-10-03)

```
ERROR: LoadError: Expected one match for cell 52:1:1000, got 0
```

`select_phase_c_stage2_manifest.jl` vergleicht `row["clamp_val"] == string(clamp_val)`
(Zeilen ~104 und ~121). `generate_phase_c_manifest.jl` schreibt aber `1000.0`, und die Zellangabe
lautet `1000`. `Inf` passt nur zufällig. Mit `52:1:1000.0` läuft der Trockenlauf, und alle 10 Zeilen
plus der Smoke stimmen. Der Unit-Test hat das nicht gefunden, weil seine synthetischen Manifeste
`clamp_val` anders formatieren als das echte Generatorskript.

## Umsetzung

1. Vergleich **numerisch**: Beide Seiten werden mit derselben Funktion geparst, mit der die
   Kampagne `clamp_val` liest (`parse_clamp_val` o. ä., wiederverwenden). `1000`, `1000.0` und
   `1e3` treffen dieselbe Zeile, `Inf`/`inf` ebenso. Ein ungültiger Wert bricht ab.
2. Test mit einem Manifest im **echten Format**, also eine Zeile, wie `generate_phase_c_manifest.jl`
   sie schreibt (`1000.0`, `Inf`). Am besten wird der Test aus dem echten Generator erzeugt oder ein
   eingefrorener Ausschnitt eines Generator-Outputs verwendet. Dazu `52:1:1000` → Treffer.
3. Stufe-2/3-Aufrufe bleiben byte-identisch (bestehender Test).
4. `k8s/phase_c_c8_search_b05_job.yaml`: Kopfkommentar ergänzen. Der Job wurde am 03.10. **ohne
   Bootstrap** gestartet (Manifest lokal erzeugt, aufs NFS gelegt), weil das Image `5dd1df8`
   `--stage2-cells` nicht kennt. Der Bootstrap braucht ein Image ab dem Commit dieses Fixes. Das
   Manifest selbst ändert sich inhaltlich nicht.

## Verboten

Wie WP-N41. Git, `oc`, `codex/CURRENT_TASK.md` bearbeiten.

## Abnahme

Tests geschrieben. Claude führt sie aus, weil Julia in der Sandbox nicht läuft. Report ergänzt, `STATUS.md` nach Protokoll.
