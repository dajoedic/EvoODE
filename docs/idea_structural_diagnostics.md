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
