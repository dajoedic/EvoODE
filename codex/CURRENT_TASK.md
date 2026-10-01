# WP-N33c (Fortsetzung) — Stufe-2-Orion-Job: Bootstrap ohne Python
**Language: YAML + Julia** (+ `SCRIPTS.md`)

Die erste Sitzung zu WP-N33c brach am Nutzungslimit ab. Im Working Tree liegen schon
`k8s/phase_c_robustness_stage2_orion_job.yaml`, die Markierung im System-18-Manifest, eine
Änderung an `SCRIPTS.md` und `codex/reports/REPORT_WP_N33C.md`. **Weiterarbeiten, nicht neu
anfangen.** Der ursprüngliche Auftrag (System 18 und 24, je `(0.01, 0)` und `(0.05, 0.5)`, Seed 42,
IC 1, Realisierung 1, `clamp_val = 10`, 4 Zellen, Deadline 86400, Smoke auf System 1) gilt
unverändert.

## Befund (Claude, Abnahme)

Der Bootstrap-Job ruft `python - <<'PY'` auf, um die vier Zeilen auszuwählen. Das Kampagnen-Image
(`containers/Dockerfile`, Basis `julia:1.12.6-bookworm`) installiert **kein Python**. Der Bootstrap
würde auf Orion sofort scheitern. Dasselbe gilt für das ersetzte
`k8s/phase_c_robustness_stage2_system18_job.yaml`.

## Umsetzung

Die Zeilenauswahl darf nur mit dem arbeiten, was das Image hat: Julia und `sh`. Zwei zulässige
Wege, wähle einen und begründe ihn im Report:
- (a) Die Auswahl erledigt Julia, zum Beispiel ein kleines Skript unter `studies/regression/`, das
  aus einem Phase-C-Manifest die Zeilen zu gegebenen `system_id`, Seed, IC-Set und Variante
  auswählt, neu nummeriert und schreibt. Es nutzt den vorhandenen CSV-Weg des Projekts und braucht
  keine neue Abhängigkeit.
- (b) Kein Bootstrap auf dem Cluster. Das 4-Zeilen-Manifest und das Smoke-Manifest entstehen lokal
  und werden per `oc cp` aufs NFS gelegt. Die Befehle stehen in `SCRIPTS.md` als Vorlage.

Danach greppst du alle Manifeste unter `k8s/` nach `python`. Jedes Manifest, das das
Kampagnen-Image nutzt und Python aufruft, steht im Report. Repariert wird nur das Stufe-2-Manifest.

## Verboten

Jobs starten, `oc` ausführen, Methoden- oder Runner-Code ändern, Git, `docs/`,
`codex/CURRENT_TASK.md` bearbeiten.

## Abnahme

1. YAML gültig (`yaml.safe_load_all`), jede Deadline ≤ 86400. Kein `python`-Aufruf in einem Manifest,
   das das Kampagnen-Image nutzt.
2. Bei Weg (a): ein Julia-Test für die Zeilenauswahl. Das Kommando steht im Report, Claude führt es
   aus. Bei Weg (b): Die Manifeste liegen erzeugt unter `outputs/stage2_orion/`, und ihre Zeilen sind
   im Report aufgelistet.
3. Report `codex/reports/REPORT_WP_N33C.md` vervollständigen, `STATUS.md` nach Protokoll.
