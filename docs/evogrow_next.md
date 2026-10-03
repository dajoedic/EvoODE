# EvoGrow-next — Methodenspur (ab 2026-10-03)

**Was das ist:** eine schnelle Labor-Spur parallel zu Paper 1. Ziel ist, die Methode so zu verbessern,
dass sie auf wenigen, **bekannt schweren** Systemen sehr gut funktioniert. Keine Methoden-Einschränkung
außer: Am Ende steht eine symbolische Gleichung. Phase C, die Images und die laufenden Kampagnen werden
**nicht** berührt. Code liegt unter `studies/evogrow_next/`.

**Grundsätze (Nutzer):** von einfach zu komplex. Nicht in Richtung genetische Programmierung. Nichts, was
auf Arbeiten mit Gabriel Kronberger aufbaut (Operon, E-Graph-SR, Shape-constrained SR …).

## Systeme

| Rolle | dim 1 | dim 2 | dim 3 | dim 4 |
|---|---|---|---|---|
| **Entwicklung** | 7 Gompertz | 40 Duffing | 56 Lorenz (chaotisch) | 63 SEIR |
| **Verschlossenes Prüfset** (erst am Ende) | 4 RC, nichtlinear | 49 Brusselator | 59 Rössler (chaotisch) | 62 Binok. Rivalität |

An allen Entwicklungssystemen scheitern heute EvoGrow (C-1), SINDy und ODEFormer in der Generalisierung
(0 %). Gompertz braucht einen Logarithmus, ist mit der kanonischen Basis also nicht darstellbar.

**Erfolg je System:** exakte Struktur **roh** (ohne Pruning-Hilfe) und R² > 0,9 in Rekonstruktion **und**
Generalisierung, sauber und bei (σ 0,05; ρ 0,5). Immer beide Metriken.

## Reihenfolge

1. **Multiple Shooting (Entscheidung des Nutzers, 03.10.): erster Test.** Zuerst als Orakel-Refit der
   wahren Struktur, ohne Suche. Grund: C-8 zeigte, dass Lorenz 55/56, Rössler 59 und Chen-Lee 61 selbst mit
   wahrer Struktur und ohne Grenze nicht fitbar sind (0/6). Der Fit verliert, also kann die Suche nicht
   gewinnen. Multiple Shooting ist das klassische Mittel gegen genau das (Bock 1981; Baake et al. 1992,
   „Fitting ODEs to chaotic data“).
2. Schwache Form (integrieren statt ableiten) zur Kandidatenbewertung, Auswahl per MDL/BIC.
3. ESR-artige vollständige Aufzählung nach Komplexität über eine reichere Grammatik (ln, Brüche, gemischte Terme).
4. Optimierung für Terme, die nichtlinear in den Parametern sind (RILS-ROLS-/ParFam-artig).
5. Gelernte Steuerung der Suche.

Jede Stufe misst sich an derselben Messbasis. Weiter geht es erst nach echter Verbesserung.

## Log

- 2026-10-03: Spur angelegt, Systeme gewählt, WP-M1 (Multiple-Shooting-Orakel) beauftragt.
