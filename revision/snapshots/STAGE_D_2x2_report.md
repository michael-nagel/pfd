# Stufe D – 2×2-Zerlegung: Look-Ahead-Leak × Normalisierung

Ziel: die vierte, fehlende Zelle der 2×2-Matrix erzeugen und alle vier Stufen
nebeneinander vergleichen, um zu trennen, welcher Teil der Ergebnis-
verschiebung vom **Look-Ahead-Leak** (Match-Ausgang im Imputer, R2-C2) und
welcher von der **Normalisierung** (margenbereinigte Wahrscheinlichkeiten,
R1-i/R3-3) stammt – und ob die beiden Effekte additiv sind oder interagieren.

## Das 2×2-Design

Zwei binäre Achsen, vier Stufen:

|                          | **mit Leak** (Match im Imputer) | **ohne Leak** (Match-Fix) |
|--------------------------|---------------------------------|---------------------------|
| **roh** (1/dez)          | `B0_pre_fix` — publizierter Stand | `B_match_fix`           |
| **normalisiert** p/(p+p')| `C_norm_pre_fix` — **neu, diagnostisch** | `C_normalized`   |

- Zeilen = Messgröße (rohe einseitige inverse Quote vs. margenbereinigte,
  auf Summe 1 normierte Wahrscheinlichkeit).
- Spalten = Imputer-Feature-Set (mit vs. ohne Match-Ausgang).
- `C_norm_pre_fix` ist die einzige noch fehlende Zelle. Sie ist **rein
  diagnostisch, nicht committet** und dient nur dieser Zerlegung.

## Wie `C_norm_pre_fix` gebaut wurde

Gleiche Mechanik wie `B0_pre_fix`, nur mit `estimation.normalize=true`:

- **Resample wiederverwendet.** `C_norm_pre_fix` liest exakt dasselbe
  `data_resampled.h5` wie `C_normalized` (normalize=True; verifiziert:
  OddsMvt-Median 0,509, 183 210 Gruppen). Damit ist die resampelte Datenbasis
  zwischen den beiden normalisierten Stufen **identisch**; sie unterscheiden
  sich ausschließlich im Imputer.
- **Pre-Fix-Imputer.** Auf die pivotierte Wide-Form wurde
  `impute_missings_pre_fix` angewandt (Match-Ausgang **im** Feature-Set, wie
  vor Commit a2b694e), statt des heutigen `impute_missings` (Match entfernt).
- **Ablauf:** `pre → wide2 → post → gmm`, voll frequentistisch, kein Bayesian.

**Konsistenz-Beleg (baut Vertrauen in die Mechanik):** Der Leak berührt nur
die imputierten Frühpreise, nicht die Cross-Sections. Also müssen alle
`pre`-Artefakte von `C_norm_pre_fix` **bit-identisch** zu `C_normalized` sein –
und sie sind es: `iqr_rtrns=0,1206638749983886`,
`bootstr_std=0,030698753123470954`, `bootstr_low/up=0,7604135/0,8807504`,
`frac_missings=0,07846711852144383` stimmen auf allen Stellen überein. Damit
ist gesichert, dass `C_norm_pre_fix` und `C_normalized` sich – wie beabsichtigt
– **nur** in der Imputer-Dimension unterscheiden.

## Vergleichstabelle über alle vier Stufen

(Quelle: `revision/snapshots/compare_2x2.csv`. β₁-Kreuzung = erster Durchgang
des Pfads durch β₁=1, linear interpoliert; „–" = kein Durchgang, β₁>1 über den
gesamten Beobachtungshorizont. n_signif = Zahl der Perzentile, an denen β₁
statistisch **nicht** von 1 unterscheidbar ist. T6 = Tabelle 6 / `res_wp_re`,
AvgChange-Zeile; Koeffizient = Fixed Effect, SE = Bootstrap-SE, Signifikanz =
Bootstrap-KI schließt 0 aus.)

| Kennzahl | B0_pre_fix (roh, Leak) | B_match_fix (roh, Fix) | C_norm_pre_fix (norm, Leak) | C_normalized (norm, Fix) |
|---|---|---|---|---|
| normalisiert | Nein | Nein | Ja | Ja |
| **β₁ min** | 0,9192 | 0,9335 | 1,0151 | 1,0313 |
| **β₁ max** | 1,7891 | 1,9501 | 2,3414 | 2,5915 |
| **β₁ bei 50 %** | 0,9873 | 1,0089 | 1,1029 | 1,1273 |
| **β₁-Kreuzung von 1** | 47,8 % | 55,0 % | – (β₁>1) | – (β₁>1) |
| **# signif. Perzentile** | 31 | 28 | 4 | 1 |
| γ̄ (CUE) | 0,0332 | 0,0332 | 0,0320 | 0,0320 |
| γ min / max | 0,0029 / 0,0741 | 0,0029 / 0,0741 | 0,0042 / 0,0720 | 0,0042 / 0,0720 |
| bootstr_std | 0,0249 | 0,0249 | 0,0307 | 0,0307 |
| ADF-Stat | −5,35 | −5,35 | −3,79 | −3,79 |
| ADF-p | 0,0002 | 0,0002 | 0,0559 | 0,0560 |
| iqr_rtrns | 0,1237 | 0,1237 | 0,1207 | 0,1207 |
| n_groups (df_oc) | 169 574 | 169 574 | 172 663 | 172 663 |
| **T6 AvgChange-Koeff.** | 0,7413 | 0,7413 | 0,8206 | 0,8206 |
| **T6 AvgChange-SE** | 0,0249 | 0,0249 | 0,0307 | 0,0307 |
| **T6 AvgChange signif.** | ja | ja | ja | ja |
| RMSE-Rang Spearman vs. B0 | 1,00 | 1,00 | 0,9922 | 0,9922 |

γ-Extremränge (idxmin GGBET, idxmax Dafabet) sind in allen vier Stufen
identisch.

## Lesart 1 – Der Leak berührt ausschließlich den β₁-Pfad

Vergleicht man **spaltenweise** (mit vs. ohne Leak, Messgröße festgehalten),
so ändert der Leak **nur** die β₁-Kennzahlen (min/max/bei 50 %, Kreuzung,
Anzahl signifikanter Perzentile). Alle übrigen Zeilen sind innerhalb der
Rundung identisch:

- γ̄, γ min/max, idxmin/idxmax: unverändert (roh 0,0332; norm 0,0320).
- ADF, iqr_rtrns, bootstr_std, n_groups(df_oc), Tabelle 6, RMSE-Rang:
  unverändert.

Das ist exakt das Muster von Stufe B (B0 → B_match_fix): Der Match-Fix wirkt
auf die Unbiasedness-Regressionen und sonst nirgends – und dieses Muster
**hält auch unter Normalisierung**. Der Leak ist damit sauber auf die
imputationsabhängigen Frühpreise begrenzt; er verschiebt keine Cross-Section
und keine Lernrate.

Konkret auf den Signifikanz-Perzentilen: roh 31 → 28 (Leak entfernt −3),
normalisiert 4 → 1 (Leak entfernt −3). In **beide** Messgrößen-Welten kostet
das Entfernen des Leaks rund drei Perzentile – ein bemerkenswert stabiler,
messgrößenunabhängiger Leak-Fußabdruck.

## Lesart 2 – Die Normalisierung ist der dominierende Treiber

Vergleicht man **zeilenweise** (roh vs. normalisiert, Imputer festgehalten):

- **β₁ bleibt über den ganzen Horizont > 1.** Roh kreuzt der Pfad β₁=1 bei
  48 % (mit Leak) bzw. 55 % (ohne) und läuft danach auf/unter 1. Normalisiert
  liegt β₁ **durchgehend über 1** (min 1,015 bzw. 1,031); die Kreuzung
  verschwindet. Ökonomisch: Die scheinbare „Überschießen-nach-unten"-Phase
  spät im Fenster war ein Margen-Artefakt der rohen Preise – die
  systematische Margenschrumpfung Open→Close drückt die rohe Bewegung nach
  unten und β₁ unter 1. Ohne diese Komponente bleibt durchgängig
  β₁>1 (partielles Lernen / Unterreaktion, im Sinne von R2-C7).
- **Signifikante Perzentile brechen ein:** 28/31 → 1/4.
- **ADF −5,35 → −3,79** (p 0,0002 → 0,056): Die rohe Serie verwirft die
  Unit-Root deutlich, die normalisierte nur noch grenzwertig. Konsistent mit
  der Diagnose, dass die rohe Serie eine quasi-deterministische
  Driftkomponente aus der Margenschrumpfung enthielt; nach deren Entfernung
  ist die Serie näher an einem Random Walk. Die ADF-Kennzahl ist zwischen
  Leak-Varianten praktisch invariant (−3,79 in beiden), also rein
  normalisierungsgetrieben.
- **Tabelle 6 (AvgChange):** Koeffizient 0,7413 → 0,8206, SE 0,0249 → 0,0307,
  in allen Stufen signifikant. Die Normalisierung zentriert die
  Winning-Rate-Achse bei Nulländerung auf exakt 0,50 (roh: ~0,54,
  Halb-Margen-Aufschlag) und **steilert** die Steigung.

## Lesart 3 – Kompositionsverschiebung im df_oc-Sample

Die Normalisierung ändert, welche Gruppen eine Open→Close-Bewegung ungleich 0
haben (`bookmaker_accuracy.py:88`, `|RtrnOpnCls|>0`). Dadurch wächst das
df_oc-Sample (Grundlage von Tabelle 3/6 und Winning Proportions) von
**169 574 (roh) auf 172 663 (normalisiert) Gruppen, netto +3 089**.

Das deckt sich exakt mit der C2-Kompositionsdiagnose: **3 367 neu
hinzukommende − 278 herausfallende** Gruppen = +3 089
(`diagnostics/c2_zeromove_newly_in.csv` / `_out.csv`). Wichtig: Diese
Komposition betrifft df_oc (Cross-Section-Sample), **nicht** das
Unbiasedness-Sample der β₁-Regressionen – letzteres bleibt in beiden
normalisierten Stufen bei 183 210 Gruppen (NumOddsMvt<20 auf der Wide-Form).
Das df_oc-Sample ist zudem leak-invariant (roh 169 574 in beiden roh-Stufen,
norm 172 663 in beiden norm-Stufen), da es nur von Opening/Closing-Preisen
abhängt.

## Additivitätsprüfung des β₁-Pfads

Frage: Ist der volle Effekt gleich der Summe der Einzeleffekte?

    (C_normalized − B0_pre_fix) ≟ (B_match_fix − B0_pre_fix) + (C_norm_pre_fix − B0_pre_fix)
       voller Effekt            =        Leak-Anteil         +       Norm-Anteil

Residuum = voller Effekt − (Leak-Anteil + Norm-Anteil). Ein großes Residuum
bedeutet Interaktion zwischen Leak und Normalisierung.

Über die 50 Inkremente (Quelle `revision/snapshots/additivity_beta1.csv`):

- **mittleres |Residuum| = 0,0104**, gegenüber mittlerem |vollem Effekt| = **0,1926**
- **maximales |Residuum| = 0,0891** (bei Perzentil 2), max |voller Effekt| = 0,8024

Das Residuum ist also im Mittel ~5 % des Effekts – **die Zerlegung ist zu rund
95 % additiv.** Die Interaktion konzentriert sich vollständig auf die ersten,
extrem verrauschten Frühinkremente (Perzentil 2 hat die mit Abstand größte SE);
ab Perzentil ~20 liegt das Residuum durchgängig unter 0,01.

Beispielinkremente (Δβ₁ gegenüber B0_pre_fix):

| Perzentil | voll | Leak-Anteil | Norm-Anteil | vorhergesagt | Residuum |
|---|---|---|---|---|---|
| 2   | +0,802 | +0,161 | +0,552 | +0,713 | +0,089 |
| 20  | +0,242 | +0,055 | +0,181 | +0,236 | +0,006 |
| 50  | +0,140 | +0,022 | +0,116 | +0,137 | +0,003 |
| 76  | +0,119 | +0,017 | +0,099 | +0,116 | +0,003 |
| 100 | +0,112 | +0,014 | +0,096 | +0,110 | +0,002 |

An jedem Inkrement ist der **Norm-Anteil etwa das 4- bis 7-Fache des
Leak-Anteils**, beide heben β₁ an, und die Interaktion ist (außerhalb von
Perzentil 2) vernachlässigbar. Das rechtfertigt es, in der Reviewer-Antwort
Leak- und Normalisierungseffekt getrennt und additiv zu berichten: Der
publizierte Look-Ahead-Fix (Figure-3-Update) und die geplante Normalisierung
verstärken sich weitgehend unabhängig, wobei die Normalisierung den weit
größeren Teil der Verschiebung trägt.

## Abbildungen

Alle mit den projekteigenen Plot-Funktionen aus `src/pfd/` erzeugt
(`plot_unbiased_reg_res`, `plot_gmm_res`, der Barplot-Block aus
`bookmaker_accuracy`, der Scatter/Random-Slope-Block aus
`winning_proportions`; gleiche `PlotParams`-Styling-Config wie im Paper),
regeneriert aus den gespeicherten CSVs – kein Pipeline-Neulauf. Ablage:
`revision/snapshots/figures_2x2/`, je Stufe eindeutig benannt, als PDF **und**
PNG. Wo sinnvoll mit über alle vier Varianten **identischer Achsenskalierung**,
damit die Unterschiede nicht durch Autoscaling verdeckt werden.

- `montage_beta1.png` – Figure 3 / β₁-Pfad (Slope + RMSE), 2×2. Geteilte
  Slope-Achse. Zeigt unmittelbar: obere Zeile (roh) fällt auf/unter die
  β₁=1-Linie, untere Zeile (norm) bleibt durchgehend darüber; die Spalten
  (Leak) unterscheiden sich nur subtil → Normalisierung dominiert.
- `montage_gmm_params.png` – Lernrate γ je Bookmaker (First-Stage + CUE), 2×2,
  geteilte γ-Achse. Alle vier Panels praktisch deckungsgleich (Dafabet oben,
  GGBET unten) → γ ist gegen beide Achsen invariant.
- `montage_rmse.png` – Opening-RMSE je Bookmaker, 2×2, fixe Achse [0,39; 0,49]
  wie im Quellcode. Roh vs. norm nahezu identisch (Rang-Spearman 0,992).
- `montage_winprops.png` – Eq. 3 / Random Slopes, 1×2 (leak-invariant: roh |
  norm). Normalisierung zentriert den Achs-Nullpunkt auf Winning Rate 0,50 und
  steilert die Steigungen.

Einzeldateien: `beta1_<stage>.{pdf,png}`, `rmse_<stage>.{pdf,png}`,
`gmm_params_<stage>.{pdf,png}` (plus `gmm_jstat_*`, `gmm_pvalue_*` als
Nebenprodukt), `winprops_{raw,normalized}.{pdf,png}` samt Legende.

## Provenienz / Status

- Treiber: `run_freq_pipeline_v2.py` (Kopie von `run_freq_pipeline.py` mit zwei
  Prädikat-Anpassungen: `normalize = name.startswith("C_norm")`,
  Pre-Fix-Imputer bei `name.endswith("pre_fix")`). Liegt im Scratchpad, nicht
  im Repo.
- `C_norm_pre_fix` ist **diagnostisch und wird nicht committet**; das interim
  `data_resampled.h5` und die Wide-Form entsprechen der normalisierten Stufe.
- Neue Artefakte im Repo-Baum (bislang uncommittet, unter
  `revision/snapshots/`): `C_norm_pre_fix/` (Stage-Ordner),
  `compare_2x2.csv`, `additivity_beta1.csv`, `figures_2x2/`, dieser Bericht.
