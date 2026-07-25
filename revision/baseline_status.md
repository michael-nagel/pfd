# Baseline-Status – JRSSA-Mar-2026-0082

**Stand: 25.07.2026**

> **Neue Referenz-Baseline für die Revision. Ersetzt `pre-revision-baseline`
> als Ausgangspunkt für alle weiteren Änderungen.**

Ab hier gilt: normalisierte (margenbereinigte) Wahrscheinlichkeiten und
Imputation ohne Match-Ausgang sind der **Default**, kein Override und kein
Diagnose-Zweig mehr. Jede weitere Revisionsänderung wird gegen diesen Stand
gemessen, nicht mehr gegen den publizierten Stand.

Tag: `revision-baseline` (Branch `revision-jrssa`).
Entspricht Stufe `C_normalized` in `revision/snapshots/`.

---

## IMPLEMENTIERT

### 1. Match-Fix – Look-Ahead aus der Imputation entfernt (R2-C2)

**Commit `a2b694e`** „Remove match outcome from imputation feature set
(look-ahead fix)".

Der `IterativeImputer` (BayesianRidge) nutzte den Match-Ausgang als Feature.
Das ist ein Look-Ahead-Kanal: die zurückimputierten Frühpreise kannten das
Ergebnis. Match wurde aus dem Feature-Set entfernt.

**Effekt:**
- **β₁-Pfad materiell.** Die Kreuzung von β₁ = 1 verschiebt sich von 48 % auf
  57 % des Zeitfensters (max |Δβ₁| = 0,19, mittleres |Δ| = 0,043); Zahl der
  Perzentile mit signifikantem β₁ ≠ 1: 31 → 28. Das sind die Werte **vor**
  Normalisierung (Stufen B0 → B_match_fix).
- **Tabellen und GMM unberührt.** Tabellen 3–7, alle `\var{}`-Werte und die
  GMM-Lernraten (beide Varianten, je Bookmaker) bleiben innerhalb numerischer
  Auflösung unverändert (GMM-Änderung 8,9e−5).

Kontrollstufe `B0_pre_fix` (heutiger Code, Match wieder im Imputer)
reproduziert die publizierten Signifikanzperzentile exakt (31, identische
Menge) und validiert damit die Zerlegung.

### 2. Normalisierung – margenbereinigte Wahrscheinlichkeiten (R1-i / R3-3)

**Commits `dcd0f51`** (C1-Refactor: beide Quotenseiten durch
`filter_and_shape` durchgereicht, `estimation.normalize`-Flag eingeführt,
Default noch off) **+ dieser Commit** (Flag-Default auf `True`).

Implizite Wahrscheinlichkeiten sind jetzt `p_norm = p_home / (p_home +
p_away)` statt der rohen einseitigen inversen Dezimalquote. Die Normalisierung
zieht **konsistent durch die gesamte Pipeline**: Cross-Sections, GMM und
Unbiasedness-Regressionen nutzen dieselbe margenbereinigte Größe.

**Effekt (Stufen B_match_fix → C_normalized, Quelle
`revision/snapshots/compare_2x2.csv`):**
- **γ robust.** Mittlere Lernrate (CUE) 0,0332 → 0,0320; idxmin (GGBET) und
  idxmax (Dafabet) unverändert.
- **RMSE-Rangfolge robust.** Spearman roh vs. normalisiert 0,992,
  Extremränge stabil.
- **Tabelle 6 stärker.** AvgChange-Koeffizient 0,7413 → 0,8206
  (Bootstrap-SE 0,0249 → 0,0307, in beiden Stufen signifikant). Die
  Winning-Rate-Achse wird bei Nulländerung exakt auf 0,50 zentriert (roh:
  ~0,54, ein halber Margenaufschlag).
- **β₁ durchgehend > 1.** Normalisiert liegt β₁ über den gesamten
  Beobachtungshorizont über 1 (min 1,031); die Kreuzung von β₁ = 1
  **verschwindet**. Die scheinbare „Unterschießen"-Phase spät im Fenster war
  ein Margen-Artefakt der rohen Preise (systematische Margenschrumpfung
  Open→Close).
- **`signific_time_idx` kollabiert auf `{100}`.** Nur noch ein einziges
  Perzentil (das letzte) hat ein von 1 statistisch unterscheidbares β₁,
  gegenüber 28 vor der Normalisierung.

Die 2×2-Zerlegung (`revision/snapshots/STAGE_D_2x2_report.md`) zeigt: Match-Fix
und Normalisierung sind zu ~95 % additiv, und der Normalisierungsanteil ist an
jedem Inkrement das 4- bis 7-Fache des Leak-Anteils.

---

## REICHWEITE

Wichtig für die Einordnung jeder weiteren Änderung: **Imputation und
Perzentil-Raster betreffen nur einen Teil der Analyse.**

**Betroffen von Imputation und Perzentil-Raster:**
- Unbiasedness-Regressionen (β₁-Pfad, Figure 3)
- GMM-Lernraten
- Bayesian-Schätzung

Diese laufen auf der resampelten, imputierten Wide-Form (`OddsMvt0..50`).

**Nicht betroffen:**
- Alle Cross-Sections – RMSE, Eq. 1 / Eq. 2, Tabellen 5 und 6 – laufen auf den
  **echten Opening- und Closing-Preisen vor dem Resampling**. Sie sehen weder
  imputierte Werte noch das Perzentil-Raster.

Folge: Der Match-Fix und jede künftige Änderung am Perzentil-Raster
(R2-C3 / R3-2) können die Cross-Sections gar nicht verschieben. Die
Normalisierung dagegen wirkt überall – aber dort als **reine
Messgrößenänderung** (andere Größe gemessen, nicht anderes Sample bzw. anderes
Verfahren). Einzige Ausnahme mit Sample-Wirkung: das `df_oc`-Sample
(Grundlage Tabelle 3/6 und Winning Proportions) wächst von 169 574 auf
172 663 Gruppen (netto +3 089), weil der `|RtrnOpnCls| > 0`-Filter nach
Normalisierung andere Gruppen greift.

---

## NOCH OFFEN

Konsequenzen, die aus der neuen Baseline folgen, aber noch **nicht** umgesetzt
sind:

1. **`tex:801` neu formulieren** (R1-vii / R2-C7). Der Absatz beschreibt das
   alte Phasen-Narrativ (Kreuzung bei 4 %, Pause zwischen 12 % und 30 %,
   Wiederaufnahme ab 30 %, Dip unter 1 kurz vor Closing). Unter der neuen
   Baseline liegt β₁ durchgehend über 1 – das ist als **partielles Lernen /
   Unterreaktion** zu formulieren (Kontinuum statt binär, R2-C7), nicht als
   Abwesenheit von Lernen.

2. **`signific_time_idx` umbenennen.** Der Name suggeriert „signifikante
   Zeitpunkte"; tatsächlich enthält die Größe die Perzentile, an denen β₁ von
   1 **unterscheidbar** ist. Unter der neuen Baseline ist das `{100}` – der
   irreführende Name fällt jetzt stärker ins Gewicht.
   (`src/pfd/models/unbiasedness_regressions.py:81`,
   `src/pfd/models/run_estimation.py:118`)

3. **ADF-Appendix-Satz bei Reaktivierung korrigieren.** Der Appendix-Block
   (`tex:1138–1148`) ist derzeit auskommentiert. Er behauptet, die Nullhypothese
   einer Unit Root werde „auf konventionellen Signifikanzniveaus" verworfen.
   Unter Normalisierung: ADF −5,35 → −3,79, p 0,0002 → 0,056 – die Ablehnung
   ist nur noch grenzwertig. Falls der Block reaktiviert wird, muss der Satz
   entsprechend abgeschwächt werden.

4. **R1-vii-Abbildung final erzeugen.** Die Abbildungen in
   `revision/snapshots/figures_2x2/` sind Diagnose-Montagen aus gespeicherten
   CSVs. Die finale Paper-Abbildung (Figure 3) auf der neuen Baseline –
   inklusive der von R1-vii geforderten simultanen Konfidenzbänder bzw. des
   glatteren Koeffizientenpfads – steht noch aus.

5. **Bayesian-Lauf auf neuer Baseline ausstehend.** Der Neulauf lief bislang
   nur frequentistisch bis einschließlich GMM. Die Bayesian-Schätzung ist auf
   der neuen Baseline noch nicht gerechnet.

---

## Tags und Referenzpunkte

- **pre-revision-baseline** (`1067d77`): ACHTUNG – markiert NICHT den
  publizierten Stand von November 2024, sondern einen Punkt danach
  (Bootstrap-Parallelisierungs-Commit). Zwischen den publizierten Artefakten
  und diesem Tag liegen drei Commits Code-Drift, die nie neu gerechnet wurden.
  Bekannter Effekt: bootstr_std 0,0258 → 0,0249 (als Monte-Carlo-Rauschen
  verifiziert, siehe `revision_log.md` R2-C2).
  *Präzisierung:* Die Drift steckt im **Code**, nicht in den abgelegten
  Zahlen – die committeten Artefakte unter `reports/` und `data/` sind an
  diesem Tag byte-identisch zu `A_baseline` (`git diff pre-revision-baseline
  HEAD -- reports data` war leer, siehe `A_baseline/MANIFEST.md`). Der
  bootstr_std-Unterschied tritt erst auf, wenn man den Code dieses Tags neu
  laufen lässt (Stufe B0), nicht in den dort liegenden Dateien.
- **A_baseline** (Snapshot, kein Tag): die tatsächlich publizierten Artefakte
  vom 29.11.2024. Das ist die korrekte Referenz für jede Vorher/Nachher-
  Aussage gegenüber den Referees.
- **B0_pre_fix** (Snapshot): heutiger Code, aber Match zurück im Imputer –
  die Kontrollstufe, die Code-Drift von Match-Fix trennt.
- **revision-baseline** (`e95ce5a`): neue Referenz, normalisierte Quoten +
  Match-Fix. Ausgangspunkt für alle weiteren Änderungen.

**Merksatz:** Für Aussagen an die Referees ist `A_baseline` die Referenz,
nicht der Tag `pre-revision-baseline`.
