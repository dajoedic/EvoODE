# WP-N22b — ODEFormer-Runner: harte Zeitgrenze je Zelle statt nachträglicher Markierung
**Language: Python**

## Ausführung

Klein und lokal testbar. Ausführung in den Images macht Claude.

## Der Defekt

`baselines/run_odeformer_grid.py:165-189` misst die Laufzeit einer Zelle **nach** ihrem Ende und
markiert sie dann als `timeout`. Das begrenzt nichts: Eine Zelle, die hängt — etwa eine
ODE-Integration in `ConstantOptimizer`, die bei einem entarteten Ausdruck nicht terminiert —
blockiert den ganzen Lauf unbegrenzt. `CLAUDE.md` verlangt seit 2026-09-22, dass lange Läufe
**konstruktiv** begrenzt sind, nicht per Schätzung. Zweitens verwirft die heutige Logik ein
fertig gerechnetes Ergebnis, nur weil es langsam war — das ist weder Budget noch Befund.

## Was zu tun ist

- Die Zeitgrenze je Zelle **bricht die Zelle ab**, während sie läuft. Die Images laufen unter
  Linux; ein Mechanismus, der dort zuverlässig einen hängenden Python-Aufruf unterbricht, genügt.
  Auf Windows (lokale Tests) darf die harte Grenze fehlen, muss dann aber im Record und im Log als
  `timeout_enforced=false` erkennbar sein — kein stilles Weglassen.
- Welcher Mechanismus, im Report begründen. Beachten: Das Modell wird einmal je Prozess geladen
  und soll das bleiben; ein Abbruch darf den Prozess nicht in einem Zustand hinterlassen, in dem
  die nächste Zelle falsch rechnet. Wenn der gewählte Mechanismus das nicht garantieren kann,
  lieber die Zelle in einem Kindprozess rechnen und das Modell dort je Kindprozess laden — dann die
  Kosten im Report nennen.
- Eine abgebrochene Zelle wird als `status=timeout` mit `timeout_enforced=true` geschrieben, atomar
  wie alle anderen, und der Lauf geht weiter. Eine Zelle, die **innerhalb** der Grenze fertig wird,
  behält ihr Ergebnis — keine nachträgliche Umdeutung mehr.
- Beim Fortsetzen werden `timeout`-Zellen **nicht** automatisch neu gerechnet; ein eigener
  Schalter erlaubt das ausdrücklich.

## Verboten

- Keine Git-Operationen. ODEFormer nicht patchen. Keine Änderung an Konfigurationswerten, am
  Record-Schema über die Timeout-Felder hinaus, am SINDy-Pfad.
- Nichts, was länger als 15 Minuten läuft.

## Abnahme

1. Harte Zeitgrenze unter Linux, begründet; `timeout_enforced` in jedem Record.
2. Test, der eine künstlich hängende Zellfunktion (nicht ODEFormer) mit kurzer Grenze abbricht und
   prüft, dass der Lauf danach die nächste Zelle korrekt rechnet — unter Windows als
   übersprungen markiert, wenn der Mechanismus dort nicht greift, mit Begründung im Skip-Text.
3. `python -m pytest baselines/tests -q` lokal grün.
4. Report `codex/reports/REPORT_WP_N22b.md` mit dem Befehl, mit dem Claude den Abbruch-Test im
   Linux-Image fährt (`--entrypoint python`, `baselines/` eingebunden), und dem Pass-Kriterium.
