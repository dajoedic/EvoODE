# WP-N39 (Fortsetzung) — PySR genau wie ODEFormers Harness: Hyperparameter-Suche an, beide Varianten
**Language: Python**

WP-N39 ist abgenommen und committet, bis auf eine Festlegung. **Weiterarbeiten, nicht neu anfangen.**

## Befund (Claude, 2026-10-02)

`docs/WP-N39.md` A.3 friert `optimize_hyperparams=false` ein, mit der Begründung „damit nichts nach
Ergebnissen gewählt wird“. Das trägt nicht. ODEFormers Wrapper
(`outputs/third_party/odeformer/odeformer/baselines/pysr_wrapper.py:64-68, 90-102`) sucht mit
`optimize_hyperparams=True` über `finite_difference_order ∈ {2,3,4}` × `smoother_window_length ∈
{None, 15}`. Ausgewählt wird auf einem zurückgehaltenen Teil (`hyper_opt_eval_fraction`) **der
Trainingstrajektorie**. Das ist Teil des Verfahrens, keine Auswahl nach unseren Ergebnissen. Plan
§9.5 und WP-N39 A.3 verlangen ODEFormers Budget **unverändert**. Außerdem rechnet ODEFormer zwei
PySR-Baselines: `pysr` und `pysr_poly` (`unary_operators=[]`, `scripts/run_baselines.py:101-115`).

## Umsetzung

1. Faithful: `optimize_hyperparams=True`, `hyper_opt_eval_fraction=0.3`, `sorting_metric="r2"`
   (ODEFormers Defaults, `run_baselines.py:213-223`). Das Hyper-Raster kommt aus dem Wrapper,
   nachgebaut oder per Import, mit Zeilenangabe. Das gewählte Hyper-Paar je Gleichung steht im Record.
   Die Auswahl darf **nur** die zurückgehaltenen Trainingsdaten sehen, niemals die sauberen Ziele.
   Ein Test prüft das.
2. Zwei Konfigurationen wie bei ODEFormer: `pysr` (Operatoren wie jetzt) und `pysr_poly`
   (`unary_operators=[]`). **Beide werden immer gerechnet und beide berichtet**, keine wird gewählt,
   wie bei SINDys zehn Konfigurationen.
3. `docs/WP-N39.md`: A.3 und die Kostenformel anpassen (6 Hyper-Fits × 2 Konfigurationen je
   Gleichung, als Faktor ausgewiesen). Die alte Festlegung als „verworfen 2026-10-02“ stehen lassen,
   mit Grund.
4. Der Smoke-Befehl im Report rechnet beide Konfigurationen auf System 1, (σ 0,01; ρ 0).

## Verboten

Wie WP-N39. Hyper-Raster, Iterationen oder Operatoren über das Vorbild hinaus ändern.

## Abnahme

Tests grün, Doku und Report angepasst, `STATUS.md` nach Protokoll.
