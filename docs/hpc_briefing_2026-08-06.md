# EvoODE — HPC-Beratung am 2026-08-06

Kurzfassung für den Termin. Details und Herleitungen: `docs/hpc_requirements.md`.
Ansprechpartner: David Jödicke. Projekt: EvoODE (Dissertation).

---

## a) Was das Projekt macht

EvoODE findet **Differentialgleichungssysteme aus Messdaten** — nicht als Blackbox-Modell, sondern
als lesbare Gleichung. Eingabe ist eine Zeitreihe, Ausgabe ein ODE-System, das man hinschreiben und
interpretieren kann.

Der methodische Kern: statt aus einer festen Bibliothek zu wählen oder global über große Zufalls-
strukturen zu suchen, **startet EvoODE minimal und lässt die Struktur wachsen** — Komplexität wird
erst freigeschaltet, wenn einfachere Strukturen nachweislich nicht reichen.

Rechnerisch bedeutet das: eine Suche probiert viele Kandidatenstrukturen, passt für jede die
Parameter an, und jede Parameteranpassung integriert das ODE-System viele Male numerisch. Ein
einzelner Lauf kostet daher Größenordnung **10⁴ bis 10⁶ ODE-Integrationen**.

**Wofür der Rechner gebraucht wird:** die Auswertungskampagne für die erste Publikation. 63
Benchmark-Systeme, zwei Konfigurationen, drei Zufallssaaten, zwei Anfangsbedingungen. Das ist kein
Laptop-Workload mehr — die Methode selbst ist fertig und entschieden.

---

## b) Anforderungen — was wir brauchen

| | |
|---|---|
| **Workload** | 846 unabhängige Einzelkern-Jobs, keine Kommunikation untereinander |
| **Ausführungsmodell** | Slurm-Job-Arrays, ein Array-Task pro Job, vier Arrays nach Systemdimension |
| **Kerne pro Job** | 1 (bewusst single-threaded) |
| **RAM pro Job** | 2 GB |
| **Speicher gesamt** | < 10 GB Ausgabe, ~50 MB Eingabe |
| **Rechenzeit** | geschätzt ~4.500 Kernstunden, **beantragt 10.000** |
| **Längster Einzeljob** | geschätzt ~23 h (ein 4D-System) — die unsicherste Zahl im Antrag |
| **Software** | Julia 1.12.6, exakt gepinnt. Die vorhandenen Phase-A- und Regressionsresultate wurden auf 1.12.6 erzeugt; die fruehere 1.11.5-Dokumentationsbehauptung war falsch. Kein MPI, kein GPU, keine Lizenzen |
| **Netz zur Laufzeit** | keines — nur einmal beim Bau des Container-Images |

**Ein Job ist eine reine Funktion seiner Eingaben.** Er liest einen kleinen Datensatz, schreibt
einen JSON-Record, teilt nichts mit anderen Jobs. Keine Reihenfolge, kein gemeinsamer Zustand.
Fehlgeschlagene Jobs werden einzeln neu eingereicht. Der Durchsatz skaliert damit linear mit den
verfügbaren Kernen, und die Kampagne lässt sich beliebig aufteilen.

**Was auf unserer Seite fertig ist:** die Portierung. Ein Manifest listet die Kampagne als
geordnete Zellenliste, ein Einstiegspunkt rechnet genau eine Zelle und beendet sich, ein
Merge-Schritt führt die Einzelergebnisse zusammen. Eine Zelle ist end-to-end durch diesen Pfad
verifiziert. Die Apptainer-Definition existiert (Julia gepinnt, Pakete zur **Bauzeit**
vorkompiliert, Depot im Image) — sie ist nur noch nicht gebaut, weil uns lokal die Laufzeitumgebung
fehlt.

**Zwei Dinge, die bei Julia auf Clustern erfahrungsgemäß schiefgehen** und die wir vorwegnehmen:

1. *Paketinstallation braucht genau einmal Internet.* Compute-Knoten haben meist keins. Lösung:
   Container mit vorinstallierten **und vorkompilierten** Paketen. Ohne Vorkompilierung zahlt jeder
   der 846 Jobs die Kompilierzeit erneut.
2. *Thread-Oversubscription.* Julia und OpenBLAS greifen sich per Default alle sichtbaren Kerne. Bei
   vielen Einzelkern-Tasks pro Knoten bricht der Durchsatz zusammen. Wir setzen
   `JULIA_NUM_THREADS=1` und `OPENBLAS_NUM_THREADS=1` explizit.

### Zur Ehrlichkeit der Zeitschätzung

Wir können derzeit **keine belastbare Laufzeitangabe machen** — und das ist einer der Gründe für
diesen Termin. Alle bisherigen Zeiten stammen von einem Arbeitslaptop, auf dem Nebenlast, Standby
und Throttling keine Spur in den Daten hinterlassen. Das Projekt behandelt Wall-Clock daher
grundsätzlich nicht als Beleg und argumentiert Kosten über **Zählgrößen**.

Belastbar sind: Parameteranpassungen und ODE-Integrationen pro Job, gemessen. Die Umrechnung in
Kernstunden ist eine ausgewiesene **Planungsannahme** mit Faktor 2 Unsicherheit in beide Richtungen
— daher die 10.000 statt 4.500.

---

## c) Die Fragen, in der Reihenfolge, in der sie uns blockieren

**1. Apptainer/Singularity verfügbar — und dürfen wir das Image selbst bauen?**
Der Bau braucht root oder fakeroot und ausgehendes Netz. Falls beides vor Ort nicht geht, brauchen
wir eine Alternative: Build-Service, ein Login-Knoten mit fakeroot, oder extern bauen und das
fertige `.sif` einspielen. *Das ist der einzige Punkt, der uns aktuell wirklich aufhält.*

**2. Falls Container unerwünscht: gibt es ein Julia-Modul, in welcher Version, und wo soll ein
gemeinsames Depot liegen?**
Es müsste vom Login-Knoten aus befüllt **und vorkompiliert** werden, bevor das Array startet.

**3. Ist `--array` mit Concurrency-Cap (`%N`) das erwartete Muster in dieser Größenordnung, und
welcher Cap gilt als höflich?**
846 Jobs sind wenig Rechenzeit, aber viele Jobs.

**4. Gibt es eine Empfehlung für das Dateisystem des Julia-Depots?**
Viele kleine Dateien, leselastig beim Jobstart. Unsere Antwort ist bisher „im Image", was die Frage
umgeht — wir würden gern wissen, ob das der üblichen Praxis entspricht.

**5. Ist eine kleine Pilot-Allokation vorab möglich — etwa 20 Jobs, ~50 Kernstunden?**
Das ist die wichtigste Frage nach Punkt 1. Sie ersetzt unsere Extrapolationen durch Messungen und
verschafft dem Projekt seine erste vertrauenswürdige Zeitangabe überhaupt.

**6. Wie hoch ist die maximale Walltime pro Job?**
Wir planen vier Arrays: 1D 1 h, 2D 12 h, 3D 24 h, 4D 48 h. Liegt das Limit unter den 3D/4D-Werten,
müssen wir reden: der Workload hat heute **keinen natürlichen Checkpoint** — ein Lauf ist eine
zusammenhängende Suche, die ihr Ergebnis am Ende liefert. Checkpointing wäre machbar, aber ein
Eingriff in den wissenschaftlichen Code; wir würden die tatsächlichen Laufzeiten lieber erst im
Piloten bestätigen.

---

## Randbedingung, die die Planung betrifft

**Alle Jobs einer Kampagne müssen aus einem Codestand laufen.** Jeder Job schreibt den
Git-Commit-Hash und einen Konfigurations-Fingerprint mit; eine Kampagne mit gemischten Ständen ist
nicht publizierbar und müsste wiederholt werden. Der Einstiegspunkt verweigert deshalb den Start,
wenn der Fingerprint nicht zum Manifest passt.

Praktisch heißt das: die Kampagne kann in beliebiger Reihenfolge, unterbrochen und über Wochen
verteilt laufen — aber sie kann nicht mittendrin auf eine neue Codeversion wechseln.
