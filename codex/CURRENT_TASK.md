> **Claude-Status:** `waiting for codex` — WP-A3 übergeben, ich prüfe alle 20 Minuten.
> Melde dich über `codex/STATUS.md`, nicht in dieser Datei. Committe nichts.
> Der Dauerauftrag steht in `codex/CODEX_PROTOCOL.md`.

# WP-A3 — Die Hypothesenauswertung kennt nur Phase A
**Language: Python**

## Der Befund

WP-A2 hat `table_main_results.py` und zwei Plot-Skripte von der eingefrorenen Phase-A-Variantenliste
gelöst. `analysis/scripts/*/evaluate_hypotheses.py` ist unangetastet geblieben und trägt weiterhin
eine fest verdrahtete `EXPECTED_VARIANTS`-Liste, gegen die es hart abbricht:

```text
raise ValueError(f"Missing expected variants: {', '.join(missing_variants)}")
```

Das ist ehrlicher als das stille Fallenlassen, das WP-A2 beseitigt hat — aber es macht das Skript
für Kampagnendaten unbrauchbar. Nach 756 Zellen wäre das die Stelle, an der die Auswertung stehen
bleibt.

Dazu kommt ein inhaltliches Problem: Die Hypothesen H1 bis H4 stammen aus
`docs/paper1_study_protocol.md` und beziehen sich auf den **Phase-A-Variantenvergleich** (v1, v2.1,
v2.2-Usage-Modi, GP). Die Kampagne vergleicht etwas anderes: `evogrow_v2_2_stage_capped` mit
`pretuning` an gegen aus. H1 bis H4 sind darauf nicht anwendbar.

## Umfang

### Teil 1 — Bestandsaufnahme, bevor irgendetwas geändert wird

Lies `docs/paper1_study_protocol.md` und stelle je Hypothese fest, ob sie auf den
Kampagnenumfang überhaupt übertragbar ist. Ergebnis in den Report als Tabelle: Hypothese,
übertragbar ja/nein, Begründung in einem Satz.

**Erfinde keine neuen Hypothesen.** Wenn H1 bis H4 nicht passen, ist das ein Befund und keine
Einladung, Ersatz zu formulieren — welche Aussagen die Kampagne trägt, entscheidet der Nutzer.

### Teil 2 — Das Skript soll unterscheiden können

`evaluate_hypotheses.py` muss erkennen, ob ihm Phase-A-Daten oder Kampagnendaten vorliegen, und
sich entsprechend verhalten:

- Bei Phase-A-Daten: **exakt wie bisher**, unverändert in Ergebnis und Fehlerverhalten.
- Bei Kampagnendaten: keine Auswertung erzwingen, die nicht definiert ist. Es soll klar und
  verständlich melden, was es vorfindet und warum es die Phase-A-Hypothesen nicht anwendet —
  nicht mit `Missing expected variants` abbrechen, als fehlten Daten.

Wie du erkennst, um welchen Fall es sich handelt, entscheidest du; begründe es im Report. Die
Variantenliste allein ist ein schwaches Signal, es gibt in den Daten auch `campaign`- und
`condition`-Felder.

### Teil 3 — Nachweis

- Phase-A-Lauf vorher und nachher, Ausgaben wert- oder bytegleich, mit Prüfsumme belegt.
- Ein Lauf gegen die Kampagnen-Brückendaten aus WP-A1
  (`analysis/data/wp_a1_campaign_bridge_probe/`), der zeigt, dass die Meldung verständlich ist.
- Ein Test, der beide Fälle abdeckt.

Halte dich an `analysis/CONVENTIONS.md`.

## Verboten

- **Keine Änderung an Julia-Code, an der Cap-Logik oder an irgendetwas Fingerprint-Relevantem.**
  Auf Orion laufen zwei Sondierungszellen, und die 120 Regressions-Records liegen unter
  `1d0ccf8d53c6576d` / `61b6548ef0014593`. Diese Werte müssen stehen bleiben.
- **Keine Cluster-Jobs, keine Kampagne, keine Läufe auf Orion.**
- **Keine neuen Hypothesen und keine neuen Metrikdefinitionen.**
- **Keine Änderung an den eingefrorenen Phase-A-Artefakten** unter `experiments/`.
- **Nichts committen, nichts stagen, nichts pushen. Kein `git add -A`.**
- Nichts, was länger als 15 Minuten läuft.

## Abnahme

- Die Übertragbarkeitstabelle aus Teil 1 liegt vor.
- Phase A liefert unverändert dieselben Ergebnisse, mit Prüfsumme belegt.
- Kampagnendaten führen zu einer verständlichen Meldung statt zu `Missing expected variants`.
- Der neue Test deckt beide Fälle ab.
