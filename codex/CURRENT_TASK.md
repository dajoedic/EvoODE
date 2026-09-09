# WP-N8 — Identität im Probe-Skript: Reparatur und Wächter

**Language: Julia**

## Warum

`studies/regression/wp_n1_basis_probe.jl:273` setzt die Provenienz hart auf
`(git_hash = "not_collected", git_dirty = nothing)`. Jeder Record des Probelaufs trägt damit eine
Platzhalter-Identität, obwohl das Projekt Publizierbarkeit an ein vollständiges Identity-Triple
bindet (git-Hash, Config-Fingerprint, Behaviour-Fingerprint; `PAPER_1.md`, WP-P1).

Das blockiert den kritischen Pfad: der **dim-2-Probelauf zur Konstanten entscheidet die kanonische
Basis für Phase C** (`docs/paper1_phaseC_benchmark_plan.md`, Voraussetzung P2 und P3). Daten mit
Platzhalter-Identität dürfen eine eingefrorene Konfigurationsentscheidung nicht tragen.

Die Reparatur selbst ist klein: `git_provenance()` steht in `studies/regression/run_regression.jl`
und ist über den vorhandenen `include` in Zeile 8 bereits im Geltungsbereich des Probe-Skripts. Sie
behandelt auch den Containerfall über `EVOODE_GIT_SHA`.

**Das Paket ist deshalb bewusst weiter geschnitten als die eine Zeile.** Eine Platzhalter-Identität
konnte unbemerkt in ein Skript geraten, das Entscheidungsdaten erzeugt — die Fehlerklasse ist das
eigentliche Ziel, nicht der Einzelfall.

## Was zu tun ist

### Teil 1 — Reparatur

Die hartkodierte Provenienz durch die vorhandene Funktion ersetzen. **Nicht neu implementieren** —
eine zweite Provenienzlogik läuft von der ersten weg.

Prüfe im selben Zug, ob die übrigen Identitätsfelder des Probe-Skripts tatsächlich gefüllt werden
und nicht nur gesetzt aussehen: `base_config_fingerprint` und `stage_cap_behavior_fingerprint` in
den Zeilen um 166/167, und ob beide im geschriebenen Record landen. Was fehlt, ergänzen; was da ist,
unangetastet lassen.

### Teil 2 — Wächter gegen Platzhalter-Identität

Das Skript darf einen Record mit unbrauchbarer Identität **nicht schreiben**. Unbrauchbar heißt:
git-Hash fehlt, ist leer, oder ist einer der Platzhalter (`"not_collected"`, `"unknown"`).

Verhalten: **laut abbrechen, bevor der erste Record geschrieben wird**, mit einer Meldung, die sagt,
welches Feld fehlt und warum das den Lauf ungültig macht. Kein stilles Weiterlaufen, keine Warnung,
die im Log untergeht — ein Lauf über viele Stunden, dessen Daten am Ende unbrauchbar sind, ist
teurer als ein Abbruch nach zwei Sekunden.

Ein ausdrücklicher Ausweg gehört dazu, weil Entwicklungsläufe legitim sind: eine Umgebungsvariable,
die den Abbruch aufhebt und dafür den Record sichtbar als Entwicklungsdaten markiert. Der Name der
Variablen und das Markierungsfeld sind deine Wahl; beides gehört in den Report und in `SCRIPTS.md`.

### Teil 3 — Die Altdaten bleiben unterscheidbar

Die vorhandenen dim-1-Probedaten unter `outputs/wp_n1_dim1_probe/` wurden **vor** dieser Reparatur
geschrieben und tragen `git_hash = "not_collected"`. Sie werden **nicht** verändert, nicht migriert
und nicht nachträglich mit einem Hash versehen — ein nachgetragener Hash wäre eine Behauptung, die
niemand prüfen kann.

Sie müssen aber von den neuen Daten unterscheidbar bleiben, und das Zusammenführen beider in einer
Auswertung darf nicht stillschweigend möglich sein. Das ist dieselbe Fehlerklasse, für die in
WP-N7b `analysis/utils/support_match_definition.py` gebaut wurde — **sieh dir an, wie der Wächter
dort funktioniert, und halte dich an dasselbe Muster**, statt ein zweites Verfahren zu erfinden.

Auf der Julia-Seite genügt, dass die Unterscheidung im Record steht. Die Auswertungsseite ist nicht
Teil dieses Pakets.

### Teil 4 — `SCRIPTS.md`

Der Eintrag zum Probe-Skript nennt die neue Umgebungsvariable, den Abbruchfall und was der Abbruch
bedeutet. Bestehende Einträge nicht umformulieren.

## Abnahme

1. Das Skript schreibt einen echten git-Hash und `git_dirty`, sichtbar im geschriebenen Record.
2. Ohne ermittelbare Identität bricht das Skript ab, **bevor** ein Record geschrieben wird.
3. Der Ausweg über die Umgebungsvariable funktioniert und markiert die Records als Entwicklungsdaten.
4. Alte und neue Probedaten sind am Record unterscheidbar; die Altdaten sind unverändert.
5. `SCRIPTS.md` ist ergänzt.

**Julia lässt sich in deiner Sitzung nicht ausführen.** Erwartet ist deshalb: Code schreiben,
statisch sorgfältig prüfen, `status: blocked` melden mit `note: Umgebung, nicht Sache`. Claude führt
die Abnahme aus.

Weil jede Runde bei Claude einen vollen Durchlauf kostet, geh das **ganze** geänderte Skript auf
Laufzeitfehlerklassen durch, die ein statischer Blick übersieht: Zugriffe auf Record-Felder, die
fehlen können, `Set` gegen `Vector`, fehlende `collect`-Aufrufe, `JSON3.Object` wo ein `Dict`
erwartet wird, Indizierung mit `nothing`. WP-R1 ist an einem fehlenden `include` gescheitert, also
an etwas, das ohne Ausführung sichtbar war.

## Verboten

- **Den Probelauf nicht starten.** Weder dim 1 noch dim 2, auch nicht verkürzt. Der dim-2-Lauf
  kostet 114 Kernstunden und wird ausschließlich vom Nutzer gestartet.
- **Keine Cluster-Jobs, keine Manifeste dafür, nichts über 15 Minuten.**
- **Altdaten unter `outputs/wp_n1_dim1_probe/` nicht verändern, nicht migrieren, nicht löschen.**
- Keine zweite Provenienz- oder Fingerprint-Implementierung.
- Keine Änderung an `run_regression.jl`, `phase_b_config.jl` oder der Ausdünnungsregel.
- Nicht committen, nicht stagen, keine Git-Operationen.

## Report

`codex/reports/REPORT_WP_N8.md`. Enthält:

- welche Identitätsfelder vorher fehlten und welche jetzt geschrieben werden
- Name und Wirkung der Umgebungsvariable, und wie ein Entwicklungsrecord markiert ist
- wie alte von neuen Probedaten unterscheidbar sind
- **zwei Kommandos**: ein kurzer Testlauf über wenige Zellen und der volle dim-2-Lauf, jeweils mit
  erwarteter Zellenzahl. Keine erfundenen Ergebnisse — der Report enthält die Kommandos, nicht deren
  Ausgabe
- die Laufzeitfehlerklassen, die du durchgesehen hast
