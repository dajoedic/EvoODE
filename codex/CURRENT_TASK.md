> **Claude-Status:** `idle` — Warteschlange abgearbeitet, der autonome Loop ist beendet.
> Der Nutzer entscheidet über die nächsten Schritte. Codex: nichts tun.

# Kein aktiver Task

## Stand nach dem autonomen Durchlauf vom 2026-08-17

Abgeschlossen und committet: WP-C4 (Zweifelsband im Stage-Cap), WP-P1/P1b (Verhaltens-Fingerprint
plus Reparatur der fehlenden `SHA`-Abhängigkeit), WP-A2 (Auswertung verwirft Kampagnenvarianten
nicht mehr still), WP-W1 (`docs/PAPER_1_draft.md`).

Abgelehnt und ersetzt: WP-C3, wegen eines hartkodierten Stufenindex, der die Abnahme trug.

**Das HPC-Tor ist offen.** Regressionslauf und `pretune_off`-Sondierung warten auf den Nutzer;
gestartet wird nichts ohne ihn.

## Offene Punkte für die nächste Runde, nicht beauftragt

1. **Das Audit-Skript schreibt auf einen festen Pfad.** `studies/lookahead/audit_exact_stage_cap_horizons.jl`
   hat bei den Abnahmeläufen von WP-C2 und WP-C4 jeweils den Bericht des vorherigen Arbeitspakets
   überschrieben. Bereinigt wurde von Hand; das Skript selbst braucht ein Ziel, das mit dem
   Arbeitspaket mitwandert.
2. **Die Bandkonstanten stecken in keinem Fingerprint.** `0.35`, `0.62` und `0.1` sind `const` in
   `stage_cap.jl`; die Sonde des Verhaltens-Fingerprints prüft bei 0,2 / 0,5 / 0,8 und würde eine
   Verschiebung einer Bandgrenze auf 0,45 nicht bemerken.
3. **12 / IC 1 verliert einen korrekten Cap aus falschem Grund** — Floor-Ratio 9,9e-06, die
   Ablehnung stützt sich auf reines Rauschen. Die Floor-Tiefen-Bedingung sollte die Bandlogik ganz
   abschalten, nicht nur den Wiederaufnahmezweig.
4. **Split-Aggregation.** Zwei der vier Ablehnungen entstehen durch Stimmenmehrheit, nicht durch
   klare Erkennung.
5. **`tests/` liegt im Wurzelverzeichnis** neben dem Julia-`test/`. Verwirrend und in
   `analysis/CONVENTIONS.md` nicht vorgesehen.
