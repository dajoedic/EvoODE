# Idee: Strukturelle Diagnostik vor der symbolischen Rekonstruktion

Idee des Nutzers, festgehalten am 2026-10-04. Bisher nur Denkstand, nichts gebaut oder bewertet.
Kontext: `docs/evogrow_next.md`.

## Grundproblem

Gegeben sind rein beobachtete Zustände eines autonomen dynamischen Systems

$$
\dot{\mathbf x}(t)=\mathbf f(\mathbf x(t)),
\qquad
\mathbf x\in\mathbb R^d,
$$

aus einer oder mehreren Trajektorien. Gesucht ist eine explizite symbolische Darstellung des unbekannten
Vektorfelds

$$
\mathbf f=(f_1,\ldots,f_d),
$$

ohne vorausgesetzte feste Polynom-Bibliothek und ohne kombinatorische Expression Search als primären
Mechanismus.

## Kernhypothese

Mathematische Funktionsklassen besitzen charakteristische Differentialrelationen. Diese können genutzt
werden, um die Struktur des unbekannten Vektorfelds vor der symbolischen Rekonstruktion einzugrenzen.

Für eine skalare Abhängigkeit $g(x)$ gelten beispielsweise:

$$
g(x)=ae^{bx}
\quad\Rightarrow\quad
g\,g''-(g')^2=0,
$$

$$
g(x)=ax^p
\quad\Rightarrow\quad
\frac{x\,g'}{g}=p=\mathrm{const.},
$$

$$
g(x)=a\log x+b
\quad\Rightarrow\quad
x\,g'=a=\mathrm{const.},
$$

$$
g(x)\in\mathcal P_m
\quad\Rightarrow\quad
g^{(m+1)}=0.
$$

Damit definiert jede betrachtete Operator- oder Funktionsfamilie $\mathcal F_k$ eine Menge diagnostischer
Relationen

$$
R_k(g,g',g'',\ldots)=0.
$$

Aus den Daten wird nicht zunächst ein Ausdruck $g$ gesucht, sondern getestet, welche Relationen $R_k$ mit
den beobachteten Dynamiken vereinbar sind.

## Algorithmisches Prinzip

Für jede Gleichung $f_i$:

$$
\text{Trajektoriendaten}
\rightarrow
\text{Strukturelle Diagnostik}
\rightarrow
\text{zulässige Funktionsklassen}
\rightarrow
\text{dateninduzierter Hypothesenraum}
\rightarrow
\text{symbolische Rekonstruktion}.
$$

Die strukturelle Diagnostik soll nacheinander bestimmen:

- **relevante Variablen**
- **notwendige Interaktionen**
- **mögliche Funktionsfamilien**
- **aus den Daten nicht unterscheidbare Alternativen**

Erst danach wird eine kleine Grammatik bzw. Bibliothek erzeugt. Die symbolische Suche findet damit nicht
mehr in einem universellen Ausdrucksraum statt, sondern ausschließlich innerhalb der durch die Daten
gestützten Struktur.

## Zentrale methodische Forderung

Der Algorithmus darf Unsicherheit nicht durch einen beliebigen Ausdruck verdecken.

Sind zwei Strukturen anhand der beobachteten Daten nicht unterscheidbar, muss das Ergebnis zum Beispiel

$$
\{\text{power law},\ \text{exponential}\}
$$

oder `AMBIGUOUS` lauten können, statt zwangsläufig eine einzelne Gleichung zurückzugeben.

Damit wird Identifizierbarkeit Teil des Discovery-Prozesses.

## Minimaler Scope für ein erstes Paper

Zunächst keine beliebig verschachtelten Ausdrücke.

Primitive Familien:

$$
\mathcal F=
\{
\text{constant},\
\text{linear},\
\text{polynomial},\
\text{power},\
\exp,\
\log,\
\sin/\cos,\
\text{simple rational}
\}.
$$

Zunächst Systeme mit niedriger Dimension und kontrollierter Abdeckung des Zustandsraums. Mehrere
Anfangsbedingungen dürfen für dieses Paper ausdrücklich genutzt werden, um räumliche Eigenschaften des
Vektorfelds identifizierbar zu machen.

Das Paper beantwortet nur eine Frage:

> Kann die mathematische Klasse des unbekannten Vektorfelds aus den Daten diagnostiziert und dadurch eine
> korrekte symbolische Gleichung ohne breite Expression Search rekonstruiert werden?

## Erfolgskriterium

Die Idee gilt nur dann als tragfähig, wenn gegenüber ungelenkter bzw. bibliotheksbasierter Discovery
**gleichzeitig** gezeigt werden kann:

- höhere Strukturtreue,
- bessere Generalisierung auf neue Anfangsbedingungen,
- deutlich kleinerer tatsächlich untersuchter Ausdrucksraum,
- Laufzeit im Bereich Sekunden bis wenige Minuten pro System.

Die abschließende ODE-Integration dient der Validierung und liegt außerhalb der inneren Suchschleife.

## Offene Punkte (für die Bewertung, noch nicht bearbeitet)

- Literaturprüfung: Gibt es Verfahren, die Funktionsklassen über Differentialrelationen diagnostizieren?
- Wie wirken sich Rauschen und Differentiation höherer Ordnung auf die Relationen aus?
- Wie wird das „Vektorfeld als Funktion des Zustands“ aus Trajektoriendaten gewonnen (Abdeckung, mehrere ICs)?
- Wie werden Mehrvariablen-Strukturen (Interaktionen, Summen von Familien) zerlegt?

## Verfeinerung 04.10. (Diskussion Nutzer ↔ Claude): minimaler Annihilator statt Signaturkatalog

**Kern:** keine handgebauten Signaturen je Familie, sondern direkt einen möglichst einfachen linearen
Differentialoperator mit Polynomkoeffizienten aus den Daten rekonstruieren:

$$
L=\sum_{k=0}^{r}p_k(x)D^k,\qquad L[f]pprox 0.
$$

Rahmen: holonome (D-finite) Funktionen. Polynome, exp, sin/cos, log, Potenzen, einfache rationale
Funktionen, e^{-x^2}, sin(ax+b), x·log x (Gompertz) sind enthalten, und die Klasse ist **unter Summe und
Produkt abgeschlossen**, anders als Einzelsignaturen. Der Hypothesenraum wird nicht vorgegeben, er entsteht
aus dem Lösungsraum des gefundenen Operators. Später: D-algebraisch/kompositionell als natürliche
Erweiterung.

**Pipeline:**
trajectory data → weak operator matrix → nullspace / minimal annihilator → operator
factorization/classification → solution space → symbolic f.

**Schwache Form in x** (nicht in t): ∫ φ·L[f] dx = Σ_k (−1)^k ∫ (p_k φ)^{(k)} f dx, linear in den
Koeffizienten der p_k → Matrix über viele Testfunktionen φ_m → Nullraum per SVD.

**Festgehaltene Vorsichtspunkte:**
1. Operator → schöne Basis ist ein eigener Schritt (Faktorisierung bzw. Klassifikation). Für den
   eingeschränkten Scope genügt vermutlich eine Klassifikation: konstante Koeffizienten → exp/Polynom/
   sin/cos; Euler-Typ → Potenzen/log; erste Ordnung → exp(∫ rational).
2. Die Kette von x(t) zum Operator im Zustandsraum ist der **wichtigste technische Engpass unter Rauschen**.
3. Mehrere Dimensionen: Ein Attraktor liefert keine transversale Information. Mehrere ICs helfen nur, wenn
   sie relevante Regionen und Richtungen abdecken. Identifizierbarkeit bleibt zentral.
4. Nullraum-Mehrdeutigkeit ist eingebaut: Mit L annulliert auch Q·L. Deshalb (r, d) von klein nach groß
   durchlaufen. Der erste Operator mit Residuum unter dem Rauschboden ist der minimale (zugleich das
   Abbruchkriterium).
5. **`AMBIGUOUS` mathematisch begründet, nicht als Konfidenzschwelle:** mehr als eine Nullraumrichtung
   unter dem Rauschboden bei minimalem (r, d), oder mehrere (r, d) gleicher Komplexität innerhalb des
   Rauschbodens. Den Rauschboden aus dem Singulärwertspektrum ableiten (vgl. S-04: Rauschboden
   vorhersagbar).
6. Normierung ‖c‖ = 1 und Skalierung von x und f, vorab festgelegt.

**Gates (vorab festgelegt):**
- **Gate 2A, noch keine ODE:** verrauschte Samples (x_i, f_i) bekannter Funktionen: x², e^{ax}, x^p,
  log x, x·log x, e^{−x²}, sin(ax+b), x/(K+x), dazu zwei **Summen** (z. B. x² + e^x, Gompertz +
  Konstante). Rauschen 0 / 1 % / 5 %, schmaler und breiter x-Bereich. Daraus blind den minimalen Operator
  rekonstruieren. **Bestanden:** ohne Rauschen immer der minimale Operator (bis auf Skalierung), unter
  Rauschen der richtige oder ein begründetes `AMBIGUOUS`, **nie selbstbewusst ein falscher**. **Idee tot**,
  wenn schon ohne Rauschen falsche Operatoren kommen oder bei 1 % falsche mit Konfidenz.
- **Gate 2B, erst danach:** echte 1D-Zeitreihen x(t), insbesondere Gompertz (7). Komplette Pipeline bis
  zur Generalisierung auf neue ICs, erst sauber, dann mit Rauschen.

**Umsetzung:** Gate 2A ist reine Lineare Algebra → **Python** (numpy/scipy). Codex kann Python selbst
ausführen, Julia nicht, das macht schnelle Iterationen möglich.

**Einschätzung (Claude, 04.10.):** 1D sauber ~80 %, 1D bei 5 % Rauschen ~45 %, 2D/3D polynomial sauber
mit mehreren ICs ~50 %, alles zusammen schneller und besser als E-WSINDy ~25 %. Nächste Verwandte in der
Literatur (noch zu prüfen): AI Feynman (Udrescu & Tegmark, Diagnostik vor der Suche), „Guessing“ von
Annihilatoren aus exakten Reihen in der Computeralgebra (z. B. Kauers). Die Kombination aus verrauschten
Trajektorien, schwacher Form und `AMBIGUOUS` ist Claude nicht bekannt.

**Namenshinweis:** „Paper 1“ in diesem Dokument meint das erste Paper *dieser* Idee, nicht das laufende
EvoGrow-Paper 1.
