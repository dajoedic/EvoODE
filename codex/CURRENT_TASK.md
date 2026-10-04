# WP-G2A2-c — Gate 2A v2: Orakel-Absturz bei Ai, Stufe K ohne redundante Clean-Suche
**Language: Python**

Fortsetzung von WP-G2A2-b. Grundlage unverändert: `docs/GATE_2A_v2.md`. Gezielte Korrekturen, kein Neubau.

## Befund (Claude, Lauf am 04.10. abends)

`accept_01_oracle --workers 8` bricht ab: `NameError: name 'airyaiprime' is not defined`, im Worker, der K3
($\operatorname{Ai}(x)$) rechnet. Die anderen Worker haben ihre Caches unter `results/acceptance/` geschrieben.
Ursache vermutlich: Die SymPy-Ableitung von `airyai` ist `airyaiprime`, und die Übersetzung nach mpmath kennt den
Namen nicht. Gleiches Risiko besteht bei $J_0$ (`besselj`-Ableitungen) und bei höheren Ableitungen beider.

## Zu tun

1. **Abbildung reparieren.** Ai, Ai′ und $J_\nu$ bekommen eine explizite, korrekte Abbildung auf mpmath (und für
   die numerische Seite auf SciPy, falls dort dasselbe Problem besteht). Alle Ableitungen bis Ordnung 6 von K3 und
   K4 werden in einem pytest-Fall gegen mpmath-Differenzen geprüft, auf 30 Stellen, an einigen Punkten.
2. **Fortsetzen statt neu rechnen:** Ein erneuter Orakel-Lauf übernimmt vorhandene, vollständige Worker-Caches,
   wenn ihre Metadaten (Präzision, Punkte, Schwelle, Funktionsliste) übereinstimmen. Rechnet ihn **nicht** selbst
   voll, das macht Claude. Smoke: K3 allein, beide Domänen, muss durchlaufen.
3. **Stufe K, Teile ohne Redundanz:** Die Clean-Suche (K-c Punkt 4) läuft heute in **jedem** `--part`, verwendet
   wird aber nur Teil 0. Sie läuft nur noch in Teil 0. Die anderen Teile rechnen K-a, K-b, ex-ante und ihren Anteil
   am Monte-Carlo. Der Merge prüft, dass Teil 0 die Clean-Ergebnisse enthält, und dass K-a, K-b ($\ell_{\max}$,
   $\tau$) und die ex-ante-Klassen in allen Teilen identisch sind. Bei einer Abweichung bricht er ab.
4. Hilfsdateien der Worker (`accept_01_oracle_worker_*.cache.json`) werden nach einem erfolgreichen Merge nicht
   gelöscht, aber im Report beschrieben.

## Verboten

Wie in WP-G2A2-b. Keine Konstante, Schwelle oder Regel ändern, nichts auf F1–F10 rechnen außer dem Orakel-Smoke
für K3, kein Git außer lesend.

## Abnahme

- `pytest` für v2 und v1 grün, mit dem neuen Ableitungstest.
- Smoke K3 im Orakel läuft durch, die Zahlen stehen im Report.
- Report `codex/reports/REPORT_WP_G2A2_C.md`, `codex/STATUS.md` mit `WP-G2A2-c`, `done` oder `blocked`.
- Die exakten Befehle für Claude: Orakel fortsetzen, Stufe K in 8 Teilen, Merge.
