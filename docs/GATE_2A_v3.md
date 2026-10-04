# Gate 2A v3 – Änderungen gegenüber v2

**Status: ENTWURF zur Freigabe durch den Nutzer (2026-10-05).** v3 ist `docs/GATE_2A_v2.md` mit genau den hier
aufgeführten Änderungen. Alles andere gilt wörtlich weiter: Fragestellung, Hypothesenraum, F1–F10, Kalibrier-Set
K1–K8, Daten, Weak-Matrix, Test, A1–A3, Ergebniszustände, ex-ante-Klassen, Stufe K, Abnahme, Gate-Kriterien,
Kill-Kriterien, Raster und Ablauf. v2 bleibt eingefroren, und ihr Ergebnis bleibt als Befund stehen.

## 1. Warum v3

Stufe K von v2 lief am 04./05.10. (N = 2000, 1.000 Realisierungen, 8 Teile). K-a und K-b bestanden:
$\ell_{\max} = 4$, $\tau = 3.4\cdot10^{-7}$. **K-c scheiterte** an K1 ($\cosh x$, Ordnung 2) und K6 (Ordnung 3):
Ablehnungsrate 100 %, $\hat c$ bis zu 90° vom wahren Operator entfernt. K2 (Ordnung 1) bestand sauber.

Diagnose (Claude, auf dem Kalibrier-Set, 05.10.): Die FNS-Iteration aus v2 §6 nimmt den Eigenvektor zum
**betragskleinsten** Eigenwert von $X(c)$. Sie findet damit Punkte, an denen der Gradient verschwindet, aber keine
Minima. Bei K1, Seed 0, landet sie bei $J = 548$, obwohl der wahre Operator $J(c^*) = 0.099$ hat. Das
AML-Kriterium selbst ist in Ordnung, nur der Algorithmus verfehlt sein Minimum. Der Fehler steckt in der
Spezifikation, nicht in der Implementierung.

Gemessen an je 3 Seeds, breit, 1 %:

| Zelle | Ordnung | FNS (v2) | L-BFGS vom SVD-Start | $J(\hat c)$ gegen $J(c^*)$ |
|---|---|---|---|---|
| K1 | 2 | 90° | 0,02–0,25° | $\le$ |
| K2 | 1 | 0,06–0,25° | 0,06–0,25° | $\le$ |
| K6 | 3 | 14–33° | 0,25–4,4° | $\le$ |
| K5 | 4 | 73° | 28–53° | $<$, auch an Punkten weit von $c^*$ |
| K8 | 6 | 2–5° | 8–13° | $<$, Punkte bis 90° von $c^*$ haben kleineres $J$ |

Mehrere Starts aus allen rechten Singulärvektoren von $A_{\text{fit}}$ verbessern nichts: Bei K1, K2 und K6
findet schon der SVD-Start das globale Minimum. Bei K5 und K8 gibt es Punkte, die weit vom wahren Operator
entfernt liegen und ein kleineres $J$ haben als $c^*$. Das ist kein Versagen der Optimierung, sondern
Nicht-Identifizierbarkeit bei 1 %. Genau dafür gibt es die ex-ante-Klasse N2 und A3.

## 2. Änderungen

**Ä1, Kandidat (ersetzt v2 §6 Schritt 1).** $\hat c$ ist ein lokales Minimum von
$J(c) = (A_{\text{fit}}c)^\top S(c)^+ (A_{\text{fit}}c)$ auf $\|c\| = 1$ (AML, unverändert). Berechnet wird es
durch Minimierung von $J(x/\|x\|)$ über $x \in \mathbb R^n$ mit L-BFGS (SciPy `L-BFGS-B`, ohne Schranken), mit
dem analytischen Gradienten $2X(c)c$ projiziert auf den Tangentialraum und geteilt durch $\|x\|$. Start ist der
SVD-Kandidat wie in v1. Feste Einstellungen: `gtol` $10^{-12}$, `ftol` $10^{-15}$, `maxiter` 2000. Es gibt
keinen Multistart. Nicht-Konvergenz wird protokolliert, und das Ergebnis wird trotzdem verwendet. FNS entfällt.
Im Bericht heißt der Schätzer „AML (L-BFGS)“. **Abgrenzung in v2 §0:** Diese L-BFGS-Minimierung ersetzt die
FNS-Iteration als einzige zugelassene nichtlineare Optimierung.

**Ä2, $n_{\text{exact}}$ ist domänenunabhängig (ergänzt v2 §3).** $L[f]$ ist analytisch auf der zusammenhängenden
Analytizitätsdomäne von $f$. Verschwindet $L[f]$ auf einem Intervall, verschwindet es überall (Identitätssatz).
Die affine Abbildung zwischen breit und schmal erhält $(r, d)$ und die Nullraumdimension. Deshalb gilt die auf der
**breiten** Domäne berechnete $n_{\text{exact}}$-Tabelle für beide Domänen. Die schmale Rechnung läuft weiter als
Diagnose. Abweichungen werden berichtet, blockieren aber nicht. Hintergrund: Bei K7 und K8 schmal ergab das
v2-Orakel trotz 100 Stellen in hohen Klassen ((4,6) bis (6,6)) zu große Nullräume. Das ist dasselbe
Präzisionsartefakt wie früher bei F10. Es tritt nur auf schmalen Domänen auf und erhöht $n$ immer nur. Für die
schmale Domäne gelten $c^*$ und die Referenzklasse als Transformation der breiten Werte (wie Transfer, v2 §8). Die
direkt berechnete schmale Referenzklasse muss trotzdem übereinstimmen.

**Ä3, Verifikation von $c^*$ in echter Präzision (präzisiert v2 §3).** Die v2-Implementierung verifizierte mit
float-Koeffizienten an float-Stützstellen. Damit war $10^{-45}$ unerreichbar, und die „symbolische“ Prüfung lief
nur gegen $10^{-8}$. Verlangt ist, wie in v1:
- F1–F9 und alle K-Funktionen mit rationalen Parametern: Koeffizienten per `nsimplify` rationalisiert, $L^*[f]$
  vereinfacht in SymPy exakt zu 0;
- F10 und alles, was sich nicht rationalisieren lässt: mpmath mit mindestens 50 Stellen, Koeffizienten und
  Stützstellen als `mpf`, $|L^*[f]|$ relativ unter $10^{-45}$;
- K3 und K4 über ihre Definitions-ODE, symbolisch.

## 3. Was neu läuft

Orakel (nur die Verifikation, die Nullraumrechnung aus v2 bleibt gültig), Stufe K vollständig, Anhang A. Danach
gilt der Ablauf aus v2 §14 E9 unverändert. K-a und K-b hängen nicht vom Schätzer ab. Ihre Werte sollten sich
reproduzieren und werden trotzdem neu berechnet.

## 4. Was v3 bewusst **nicht** ändert

- Keine Schwelle, kein Kill-Kriterium, keine Zellklasse, keine Rauschstufe.
- Kein Multistart und keine Regularisierung, um K5 oder K8 „zu retten“. Die Nicht-Identifizierbarkeit ab Ordnung 4
  bei 1 % ist ein Befund und wird nicht wegkonstruiert.
- Die ex-ante-Klassen rechnen mit dem neuen Schätzer. Die Regel aus v2 §9 bleibt.

## 5. Vorab festgehaltene Erwartung

Damit später niemand die Hypothese nachträglich anpasst, steht hier schon jetzt, was wir erwarten: K-c sollte für
die I-Zellen K1, K2 und K6 bestehen. Ab Ordnung 4 rechnen wir mit N2-Zellen. Auf F1–F10 ist offen, ob die breiten
Zellen F4 und F5 (Ordnung 2/3 mit $d = 1$) identifizierbar sind. Die Analoga K3/K4 (Airy, Bessel) sind es bei 1 %
nicht (N1, ein Operator (4,0) ist datenkonsistent). Wenn das auf F übertragbar ist, droht K6.
