> **Claude-Status:** `idle` — sichere Warteschlange abgearbeitet, Loop laeuft nur noch
> als Beobachter der beiden Sondierungszellen. Codex: nichts tun.

# Kein aktiver Task

## Stand 2026-08-19

Abgeschlossen und committet: WP-C4, WP-P1/P1b, WP-A2, WP-W1, WP-E1, WP-A3, WP-E2.
Abgelehnt und ersetzt: WP-C3.

Auf Orion laufen `evoode-cell-709` (System 56) und `evoode-cell-727` (System 59), beide
`pretune_off`, seit rund 24 Stunden bei Level 24 bzw. 21 von 30.

## Warum hier nichts mehr ansteht

Die verbliebenen Cap-Posten sind **fingerprint-relevant** und wuerden
`stage_cap_behavior_fingerprint = 61b6548ef0014593` bewegen. Unter diesem Wert liegen die 120
abgeschlossenen Regressions-Records. Sie sind deshalb vom Nutzer terminiert zu entscheiden — vor
der Kampagne mit Neurechnung der Regression, oder danach:

1. Die Bandkonstanten `0.35` / `0.62` / `0.1` stecken in keinem Fingerprint. Die Sonde prueft bei
   0,2 / 0,5 / 0,8 und wuerde eine Verschiebung einer Bandgrenze auf 0,45 nicht bemerken.
2. System 12 / IC 1 verliert einen korrekten Cap aus falschem Grund: Floor-Ratio 9,9e-06, die
   Ablehnung stuetzt sich auf reines Rauschen. Die Floor-Tiefen-Bedingung sollte die Bandlogik
   ganz abschalten, nicht nur den Wiederaufnahmezweig.
3. Split-Aggregation: Zwei der vier Ablehnungen entstehen durch Stimmenmehrheit statt klarer
   Erkennung.

## Weitere offene Punkte, ohne Codex loesbar

4. Die eingefrorenen Phase-A-Artefakte unter `analysis/data/` sind gitignoriert und damit nicht
   wirklich eingefroren. Das JSON traegt seit dem 2026-08-19 einen falschen `generated_at`.
5. `tests/` liegt im Wurzelverzeichnis neben dem Julia-`test/`, in `analysis/CONVENTIONS.md` nicht
   vorgesehen.
6. `docs/hpc_deployment_guide.md` enthaelt Bash-Befehle fuer eine PowerShell-Umgebung; die vier
   Betriebsfallen stehen bisher nur in `SCRIPTS.md`.
7. `docs/PAPER_1_draft.md` wartet auf das Review des Nutzers, inklusive der fuenf dort
   aufgelisteten Widersprueche.
8. Das Kostenmodell in `docs/hpc_requirements.md` wartet auf die beiden laufenden Zellen.
