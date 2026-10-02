# WP-N38 (Fortsetzung) — die Kontrolle paart falsch
**Language: Python**

Auftrag und Abnahme von WP-N38 gelten unverändert. Die Dateien liegen uncommittet im Working Tree.
**Weiterarbeiten, nicht neu anfangen.**

## Befund (Claude, Docker-Kontrolle, 2026-10-02)

Die Kontrolle lief im lokalen Referenz-Image `evoode/odeformer-reference:wp-n27c`, gebaut aus dem
Dockerfile-Stand `55e9c75`. Das Image hat einen festen Einstiegspunkt, deshalb braucht der Aufruf
`--entrypoint python`. Verglichen wurde gegen
`analysis/data/paper1_phaseC_v1/odeformer_baseline/reference_orion_55e9c75/records.jsonl`.

Ausgabe: `outputs/wp_n38_noise_odeformer/control_system1_beam10_noopt/control_equivalence.json`,
`passed: false` mit 131 Befunden. Inhaltlich ist die Kontrolle aber bestanden. Claude hat das von
Hand geprüft: Der Kandidat (System 1, fit IC 1, `beam10_noopt`) liefert `0.2835 - 0.3557*x_0`,
dieselbe `fit_state_sha256` und dieselbe `environment` wie alle drei Referenz-Wiederholungen von
`beam10_noopt`. Die R²-Werte weichen um ~2e-13 ab.

Die Befunde kommen aus zwei Fehlern im Vergleich:

1. **125 × `record_presence`:** Der Vergleich verlangt das ganze Referenzraster. Verglichen werden
   darf nur die Schnittmenge, also die Referenz-Records mit den Schlüsseln, die der Kandidat erzeugt
   hat. Fehlt ein Kandidatenschlüssel in der Referenz, ist das ein Fehler. Umgekehrt nicht.
2. **Falsche Paarung:** Der Zellschlüssel (`[1, 1, 2]` usw.) enthält weder `odeformer_config_id`
   noch die Wiederholung. Der Kandidat `beam10_noopt` wurde deshalb gegen `beam10_opt`
   (`0.3023574… - 0.3605930…*x_0`) verglichen. Der Schlüssel muss System, Fit-IC,
   Generalisierungs-IC **und** Konfiguration enthalten. Wegen des Nicht-Determinismus gilt bei der
   Wiederholung der Maßstab aus WP-N24: Ein Kandidat besteht, wenn er mit **einer** Referenz-Wiederholung
   derselben Konfiguration übereinstimmt.

## Umsetzung

Den Vergleich in `baselines/run_odeformer_noise.py` (oder in der wiederverwendeten Funktion, falls
er dort liegt) entsprechend korrigieren. Ein Test muss genau diesen Fall abdecken: ein Kandidat,
eine Referenz mit vier Konfigurationen × drei Wiederholungen über viele Zellen. Er besteht, wenn
der Kandidat zu einer Wiederholung seiner Konfiguration passt, und er scheitert, wenn der Kandidat
nur zu einer anderen Konfiguration passt. Gilt die Korrektur einer Funktion, die auch das
Referenzraster nutzt (`compare_odeformer_equivalence.py`), muss deren bisheriges Verhalten auf
vollen Rastern unverändert bleiben (Test).

Im Report die Docker-Befehle korrigieren: das lokale Image `evoode/odeformer-reference:wp-n27c`,
`--entrypoint python`, `MSYS_NO_PATHCONV=1` für Git Bash, Volume als `C:/…`-Pfad, Referenz
`reference_orion_55e9c75`.

## Verboten

Wie WP-N38. Toleranzen lockern ist verboten.

## Abnahme

Tests grün. Report ergänzt. `STATUS.md` nach Protokoll. Claude fährt die Kontrolle erneut.
