# WP-N17 — B7: die Kubernetes-Manifeste für Phase C

**Language: Julia** — der Schwerpunkt sind **YAML-Manifeste** unter `k8s/`, dazu voraussichtlich
eine kleine Ergänzung am Phase-C-Manifestgenerator (Abschnitt 2). Julia kann Codex hier nicht
ausführen; der Julia-Teil wird geschrieben, als `blocked` gemeldet, Claude fährt die Abnahme.

## Ausgangslage

B1 und B4 sind erledigt (WP-N16, `6212809`). Es gibt:

- `studies/regression/phase_c_config.jl`, Identität **`0c9672de35c75a9d`**, mit Basisname und
  `max_fit_attempts = 3` im Fingerprint;
- `studies/regression/generate_phase_c_manifest.jl` → **936 Zeilen** (C-1 378, C-2 378, C-3 180)
  plus Indexlisten `indices_all.txt`, `indices_cost_desc.txt`, `indices_dim1..4.txt`;
- `studies/regression/phase_c_support.json`, **30 exakt / 33 Surrogat**;
- einen laufenden Smoke-Test auf einer echten Zelle.

**B7 ist das letzte Bauteil vor dem Pilotlauf.** Danach fehlt nur noch P9.

Vorlagen sind die Phase-B- und `wp_n1`-Manifeste in `k8s/`. Sie **nicht ändern** — Phase B und der
Probelauf sind abgeschlossene Kampagnen, ihre Manifeste sind Provenienz.

## 1 — Was gebaut wird

Nach dem Muster der vorhandenen Manifeste, aber für Phase C:

- ein **Bootstrap-Job**, der das Manifest **im Image auf NFS** erzeugt (Vorbild
  `phase_b_bootstrap_campaign_job.yaml`). Das ist kein Komfort, sondern der Grund, warum
  Kampagnendaten überhaupt vertrauenswürdig sind: das Manifest entsteht aus **demselben Code**, der
  die Zellen rechnet, statt vom Laptop hochgeladen zu werden;
- die **Kampagnen-Jobs** (Abschnitt 3 entscheidet, wie viele);
- je ein **Smoke-Job** dazu.

Alle mit `ttlSecondsAfterFinished`, `restartPolicy: Never`, `requests == limits`,
`imagePullSecrets: evoode-gitlab-pull`, den Labels der bestehenden Manifeste und den
`<COMMIT_SHA>`-Platzhaltern in Imagetag **und** Ausgabepfaden.

## 2 — Die Indexliste: eine Entscheidung, die schon gefallen ist

`indices_cost_desc.txt` ist die richtige Liste, und zwar aus **zwei** Gründen gleichzeitig. Ich habe
beide nachgerechnet:

1. Sie stellt die teuren Zellen nach vorn. Die längste dim-2-Zelle des Probelaufs lief 47 h, die
   teuerste Phase-B-Zelle **289,7 h**. Kommen die teuren zuletzt, bestimmen sie allein die
   Gesamtdauer, während der Rest der Pods leerläuft.
2. Sie hält **alle 378 gepaarten Zellen benachbart** — gekappt und ungekappt derselben
   (System, Seed, IC-Set)-Kombination stehen direkt hintereinander. Ein Abbruch trifft damit beide
   Arme gleichmäßig, und **Claim B, die Hauptabbildung des Papers, überlebt einen Teillauf.**

`indices_all.txt` hat nur Eigenschaft 2, die Dimensionslisten keine von beiden.

**Was fehlt:** eine Liste je Arm. C-3 ist der Bestätigungsarm — wenn das Budget knapp wird, ist er
das, was man streicht, und das geht nur, wenn er getrennt startbar ist. Ergänze den Generator um
die Listen, die Abschnitt 3 braucht, in derselben kostenabsteigenden Ordnung. Bestehende Listen
bleiben unverändert.

## 3 — Die eine offene Entscheidung, mit meiner Empfehlung

Wie viele Kampagnen-Jobs?

**Empfehlung: zwei.** Ein Job über die **gepaarten Arme C-1 + C-2** (756 Zellen, kostenabsteigend,
Paare benachbart) und ein getrennter Job für **C-3** (180 Zellen). Begründung: die Paarung ist
wissenschaftlich bindend (§2b des Plans verlangt identische Bedingungen je Paar), also dürfen C-1
und C-2 nie in getrennten Jobs mit getrennten Abbruchzeitpunkten laufen. C-3 dagegen ist gegen
niemanden gepaart, kostet ~2.400 Kernstunden und muss einzeln streichbar und einzeln nachfahrbar
sein.

Wenn du das anders siehst, entscheide anders — aber **begründe es im Report**, und die Paarung von
C-1 und C-2 ist nicht verhandelbar.

## 4 — `parallelism`: nachrechnen, nicht abschreiben

Das `wp_n1`-Manifest steht auf **32** statt der in `docs/hpc_requirements.md` vereinbarten 16, mit
einer ausführlichen Begründung im Kommentar: keine ResourceQuota, keine LimitRange, Leerlauf bei den
Mitbenutzern, und `requests == limits`, sodass überzählige Pods `Pending` bleiben statt jemanden zu
verdrängen.

**Diese Begründung ist eine Momentaufnahme vom 09.09. und darf nicht einfach kopiert werden.** Sie
stützt sich auf einen Zustand des Namensraums, den niemand seither geprüft hat. Übernimm den Wert,
wenn du ihn für richtig hältst — aber schreibe in den Kommentar, dass die Prüfung **vor dem Start zu
wiederholen ist**, und nenne die Kommandos dafür. Claude kann sie derzeit nicht ausführen: das
kubectl-Token ist abgelaufen.

Zur Größenordnung: 936 Zellen, geschätzt ~12.300–15.900 Kernstunden. Die Untergrenze der Wanduhr ist
die **längste einzelne Zelle**, weil eine Zelle nicht teilbar ist.

## 5 — Die Fehlermodi, die schon zugeschlagen haben

Beide gehören als Kommentar in die Manifeste, nicht nur in den Report.

**Das Deploy-Token.** Am 09.09. lief es mitten im Smoke-Job ab: `ErrImagePull` mit
`HTTP Basic: Access denied` — das sieht nach einem fehlenden Image aus, ist aber die Anmeldung.
Bei **5–7 Wochen Laufzeit** ist das kein Randrisiko: Pods werden über die gesamte Zeit neu erzeugt,
läuft das Token in der Mitte ab, entsteht ein Datensatz mit einer Lücke in der Mitte — und zwar
einer, die wie ein wissenschaftliches Ergebnis aussieht, weil sie ganze Systeme trifft. Das Secret
heißt `evoode-gitlab-pull`. Fehlermodus: `docs/hpc_deployment_guide.md` §8.

**Reihenfolge des Starts.** Erst Bootstrap, dann Smoke, dann Kampagne — nie Smoke überspringen. Der
Smoke-Job ist die einzige Stelle, an der ein Tokenfehler billig auffällt.

## 6 — Der Smoke-Job muss die Arme wirklich abdecken

Ein Smoke-Job, der dreimal dieselbe Sorte Zelle rechnet, prüft nichts. Verlangt ist **mindestens
eine Zelle je Arm** — gekappt, ungekappt, Pretuning —, und zwar **billige** (dim 1), damit er in
Minuten durch ist.

Was er belegen muss, und was im Report als Prüfliste stehen soll: `config_fingerprint`
= `0c9672de35c75a9d`, `basis_name` = `staged_polynomial_basis_with_constant`,
`max_fit_attempts` = 3, ein **gefülltes** `executed_levels`, ein echter `git_hash` (kein
`not_collected`), und `error` leer.

## 7 — Was in den Report gehört

Eine **Startanleitung in Reihenfolge**, mit den echten Kommandos: Token anlegen, Secret erzeugen,
`<COMMIT_SHA>` ersetzen, Bootstrap, Smoke, Prüfliste aus Abschnitt 6, Kampagne, Überwachung. Der
Nutzer muss sie ausführen können, ohne den Plan zu lesen.

## Verboten

- **Keinen Job starten.** Dieses Paket erzeugt Manifeste. Lange Läufe startet ausschließlich der
  Nutzer — und derzeit ist ohnehin kein gültiges Cluster-Token da.
- **Keine Änderung an den Phase-B- oder `wp_n1`-Manifesten**, an `phase_b_config.jl` oder an
  `phase_b_support.json`.
- **Kein Geheimnis im Repository.** Das Deploy-Token wird **nie** in eine Datei geschrieben, auch
  nicht als Beispiel. Im Manifest steht nur der Name des Secrets.
- **Kein `git add -A`.**

## Abnahmekriterien

1. Die Manifeste liegen unter `k8s/` mit `phase_c`-Namen, sind gültiges YAML und tragen die
   Platzhalter konsistent in Imagetag und Ausgabepfaden.
2. Bootstrap, Kampagne(n) und Smoke sind vollständig; die Jobnamen kollidieren nicht mit den
   bestehenden.
3. Die Indexlisten, die die Jobs referenzieren, werden vom Generator auch erzeugt.
4. Die Entscheidung aus Abschnitt 3 ist getroffen und begründet.
5. Die beiden Fehlermodi aus Abschnitt 5 stehen als Kommentar in den Manifesten.
6. Report nach `codex/reports/REPORT_WP_N17.md` mit der Startanleitung aus Abschnitt 7.

Melde den Julia-Teil als `blocked` mit den Kommandos für Claude.
