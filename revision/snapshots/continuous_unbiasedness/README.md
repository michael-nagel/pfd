# Robustness-Check: kontinuierliche Zeitachse für die Unbiasedness-Regressionen

Rein diagnostisch, **kein Eingriff in die Produktions-Pipeline**. Vergleichsbasis
ist die normalisierte Perzentil-Baseline (Tag `revision-baseline`, Stufe
`C_normalized`).

## Frage

Reproduziert ein varying-coefficient-Modell auf den **echten, nicht imputierten,
nicht resampelten** Beobachtungen den β₁(t)-Verlauf der 50 Perzentil-
Regressionen?

## Datenquelle

`data/processed/shaped_data.h5` – der Stand **vor** `resample_and_impute`.
Enthält je Beobachtung den Original-Zeitstempel (`Update`) und den Anpfiff
(`Date`, 289 verschiedene Uhrzeiten, also echte Kickoff-Zeit). Auf diesen
Rohstand wurde die projekteigene `filter_and_shape_data(normalize=True)`
angewandt, damit Margen-, Bookmaker- und `ts_dur`-Filter exakt der Baseline
entsprechen.

Stichprobenaufbau (Zahlen aus `build_continuous_sample.py`):

| Schritt | Zeilen | Serien |
|---|---:|---:|
| roh (`shaped_data.h5`) | 2.952.877 | 32.147 Matchups |
| nach `filter_and_shape` | 1.654.415 | 184.415 |
| Update nach Anpfiff verworfen (0,07 %) | 1.653.197 | 184.415 |
| Nullvarianz-Serien entfernt | 1.652.048 | 184.012 |
| `NumOddsMvt < 20` | 1.466.371 | 175.166 |
| Referenzbeobachtung je Serie entfernt | **1.291.205** | **175.166** |

Zum Abgleich: die resampelte Baseline hat 183.210 Gruppen – die 184.012 hier
passen dazu (das Resampling wendet den Nullvarianz-Filter ein zweites Mal an).

## Spezifikation

- Endog = `Match − p_ref`, Exog = `p(t) − p_ref`, mit `p_ref` = erster **echt
  beobachteter** normalisierter Preis der Serie.
- Achse: relative Position im **Matchup**-Fenster (`TsStart`/`TsEnd` als
  min/max `Update` über alle Bookmaker, exakt wie `resample_and_impute.py:90`).
  Zusätzlich eine Variante auf log(Stunden vor Anpfiff).
- Modell: `bam(Endog ~ s(X, k) + s(X, by = Exog, k))`, mgcv 1.9.4, fREML.
  β₁(X) wird per lpmatrix-Differenzierung extrahiert (korrekt unabhängig von
  mgcvs Zentrierungskonvention; die Variante mit explizitem Haupteffekt stimmt
  auf 6e−8 überein).
- **Ohne** Bookmaker-Random-Effects (wie vereinbart).

## Ergebnis: der Verlauf wird NICHT reproduziert

| | Baseline (Perzentil) | kontinuierlich (k=6) |
|---|---|---|
| β₁ min / max | 1,031 / 2,591 | 0,771 / 1,289 |
| β₁ bei Perzentil 50 | 1,127 | 1,056 |
| Anteil der Kurve > 1 | 100 % | 44 % |
| innerhalb der Baseline-KIs | – | **0 von 50** Perzentilen |

Die kontinuierliche Kurve liegt **systematisch unter** der Baseline und fällt
unter 1. Der Abstand ist früh am größten (Perzentil 10: 1,485 vs. 1,008) und
bleibt über das ganze Fenster bestehen.

## Was die Ursache NICHT ist

- **Nicht die Achsendefinition.** Auch auf der Matchup-Perzentil-Achse – also
  derselben Achse wie die Baseline – bleibt die Abweichung bestehen.
- **Nicht der Schätzer.** Am Perzentil 50, auf denselben echten Beobachtungen:
  pooled OLS 1,011 → + Kovariaten 1,011 → + Bookmaker-RE (exakt
  `fit_mixed_lm`) 1,008. Die Schätzerkomponenten bewegen β₁ um < 0,003.
  Die Baseline liegt an derselben Stelle bei 1,127.

## Was die Ursache plausibel IST

Die verbleibende Differenz ist die **Datenbasis**: resampeltes, imputiertes
Perzentil-Raster vs. echte Beobachtungen. Dafür spricht, dass die Lücke genau
dort am größten ist, wo die Imputation konzentriert ist (`OddsMvt0–4` machen
laut Stufe-B-Diagnose 60 % der Imputation aus) – am frühen Rand des Fensters,
wo die Baseline auf 2,59 steigt und die kontinuierliche Schätzung bei ~1,3
bleibt.

**Noch nicht auseinandergerechnet:** Resampling (Forward-Fill auf 1-min-Raster)
und Imputation der Frühpreise sind hier noch nicht getrennt, und die
Gewichtung unterscheidet sich (die Baseline nimmt je Serie *eine* Beobachtung
pro Zeitpunkt, das GAM poolt alle Beobachtungen einer Serie). Beides ist offen.

## Zur Oszillation

Die Kurve bei hohem k oszilliert. Das ist ein Flexibilitätsartefakt, kein
Signal: die Zahl der Wendepunkte skaliert mit der Basisdimension
(k=6 → 2, k=10 → 7, k=20 → 11, k=40 → 17), während das **Niveau** stabil bleibt
(Mittelwert β₁ = 1,006 bei jedem k, Anteil > 1 zwischen 44 % und 53 %).
Interpretiert werden darf daher das Niveau, nicht die einzelnen Kreuzungen
von 1. Die Hauptabbildung zeigt k=6, k=20 gestrichelt als Sensitivität.

## Dateien

- `beta1_percentile_axis.{pdf,png}` – Hauptabbildung: Baseline + Spline
- `beta1_hours_axis.{pdf,png}` – Spline auf absoluter Stundenachse
- `series_composition_hours.{pdf,png}` – Anteil beobachteter Serien je Stunde
- `beta1_continuous_k6.csv`, `_k20.csv` – Perzentil-Achse, β₁ mit KI
- `beta1_continuous_matchup_axis.csv` – k=20-Fit (identisch zu `_k20`)
- `beta1_continuous_loghours.csv` – log-Stunden-Achse

## Nebenbefund zur absoluten Zeitachse (R2-C3)

Auf der absoluten Stundenachse tragen zu jedem Zeitpunkt nur 2–32 % der Serien
bei (`series_composition_hours`): bei 48 h 7,7 %, bei 12 h 31,9 %, bei 0,1 h
2,2 %. Die Population wechselt also entlang der absoluten Achse vollständig.
Eine rein absolute Zeitachse vergleicht damit über die Zeit hinweg
unterschiedliche Stichproben – ein Argument *für* eine relative Achse, das für
die Antwort auf R2-C3 verwendbar ist.

---

# Nachtrag 1 – Kanalzerlegung des konstanten Versatzes

Drei Kanäle, je EINE Änderung gegenüber der kontinuierlichen Referenz R
(echte Beobachtungen, Matchup-Perzentil-Achse, k=6, ungewichtet):

| Modell | Versatz vs. Baseline | vs. R | Anteil der Lücke |
|---|---:|---:|---:|
| R Referenz (echt) | −0,220 | ±0 | – |
| C1 Referenzpunkt = imputierter `OddsMvt0` | −0,192 | +0,027 | +13 % |
| C2 Gewichtung 1/n_obs je Serie | −0,183 | +0,036 | +16 % |
| C3 resampelt, nicht imputiert | −0,218 | +0,001 | +1 % |
| **C4 dasselbe GAM auf den Baseline-Daten** | **−0,021** | **+0,199** | **+90 %** |

**Keiner der drei angefragten Kanäle schließt die Lücke.** C4 (nachträglich
ergänzt) zeigt, dass der Schätzer nicht die Ursache ist: das gepoolte GAM
reproduziert die 50 punktweisen Mixed-LM-Fits, wenn es dieselben Daten
bekommt. C3 vs. C4 unterscheiden sich in genau einer Sache – C3 verwirft die
ursprünglich fehlenden Zellen, C4 nimmt die imputierten Werte mit:
**die 7,85 % imputierten Zellen heben mittleres β₁ von 1,003 auf 1,203.**

Dateien: `beta1_channel_{R,C1,C2,C3,C4}.csv`,
`beta1_channel_decomposition.{pdf,png}`.

---

# Nachtrag 2 – Masking-Test: erzeugt die Imputation den β₁-Pfad?

Design wie `calc_imput_loss`, aber auf die Downstream-Frage erweitert.
**24.568 Kandidatenserien** (14,1 % der 174.392 Serien mit `NumOddsMvt<20`)
sind über das ganze Fenster echt beobachtet. Bei ihnen wurden führende Zellen
im real beobachteten Muster maskiert (Blocklängen aus der empirischen
Verteilung der Spät-Eröffner gezogen, Median 2, Mittel 4,7 Zellen) – insgesamt
**115.104 Zellen** – und mit dem Produktions-Imputer gefüllt (ohne Match,
normalisiert, Seed 42, Fit auf dem vollständigen Frame wie in der Pipeline).
Das Fehlmuster ist zu 100 % rein führend, die Nachbildung also exakt.

## a) Imputationsqualität auf den maskierten Zellen

| Kennzahl | Wert |
|---|---:|
| RMSE | 0,0909 |
| Bias (imputiert − wahr) | −0,0015 |
| sd der wahren Frühwerte | 0,2097 |
| corr(imputiert, wahr) | 0,913 |
| **sd(imputiert)/sd(wahr) − 1** | **−0,232** |
| corr(Fehler, späterer Pfad) | +0,040 |
| corr(Fehler, Ausgang) | −0,311 |

Die Imputation ist im Mittel unverzerrt und korreliert hoch mit der Wahrheit,
**schrumpft die Frühwerte aber um 23 % zur Mitte**. Die Korrelation des
Fehlers mit dem Ausgang (−0,31) folgt mechanisch aus dieser Schrumpfung
(Preise sagen den Ausgang vorher, also korreliert ein zur Mitte gezogener
Fehler negativ mit ihm) – sie ist **kein** eigenständiger Beleg für
zusätzliches Look-Ahead. Die Korrelation mit dem späteren Pfad ist mit +0,04
praktisch null.

## b) Downstream – β₁ auf denselben Serien

| Perzentil | echte Frühwerte | imputierte Frühwerte | Differenz |
|---:|---:|---:|---:|
| 2 | 1,262 | 2,460 | **+1,198** |
| 10 | 1,259 | 2,113 | +0,854 |
| 25 | 1,252 | 1,610 | +0,358 |
| 50 | 1,231 | 1,346 | +0,116 |
| 75 | 1,197 | 1,227 | +0,031 |
| 99 | 1,161 | 1,199 | +0,038 |

Mittlerer Versatz **+0,263**, Maximum +1,242 am frühen Rand.

**Befund:** Auf den echten Frühpreisen ist β₁ über das ganze Fenster
**praktisch flach bei ~1,2** (1,262 → 1,161). Erst die Imputation erzeugt den
steilen Abfall von ~2,5 auf ~1,2 – also genau die Form der publizierten
Figure 3. Der β₁-Pfad ist damit weitgehend ein Imputationsartefakt, nicht ein
gemessener Lernverlauf.

Abbildung: `masking_test_beta1.{pdf,png}`, Kurven in
`masking_beta1_{true,imputed}.csv`.

## Einschränkungen

- Die Kandidaten sind **früh eröffnende Bookmaker** (14 % der Serien). Ob die
  Imputation bei Spät-Eröffnern gleich stark verzerrt, ist eine Extrapolation
  – plausibel, aber nicht gezeigt.
- Der Test bewertet die Imputation an ihrem eigenen Zweck (Rekonstruktion
  fehlender Frühpreise). Dass β₁ auf echten Werten flach ist, sagt für sich
  genommen nichts darüber, welcher der beiden Verläufe ökonomisch „richtig"
  ist – wohl aber, dass der publizierte Verlauf ohne die Imputation nicht
  besteht.

---

# Nachtrag 3 – Das vollständige 2×2: Imputation vs. Komposition

Die Kompositions-Kontrolle in `entry_delay/` (Abschnitt 4) hatte gezeigt, dass
die 24.568 vollständig beobachteten Serien ein höheres β₁ haben (1,200) als die
Gesamtpopulation (1,006) – ohne jede Imputation. Damit stand die Frage offen,
wie viel des Niveauversatzes zur Baseline überhaupt der Imputation zuzurechnen
ist. Sie ist jetzt entschieden, weil die vierte Zelle vorliegt.

## Das Design

Zwei binäre Achsen, vier Zellen:

|                            | **alle Serien** | **nur vollständig beobachtete** |
|----------------------------|-----------------|---------------------------------|
| **Baseline / imputiert** (Perzentil-Methode) | **A** | **B** — *neu* |
| **kontinuierlich / echt** (varying-coefficient-GAM) | **C** | **D** |

- Zeilen = Datenbasis + Schätzverfahren (resampeltes, imputiertes
  Perzentil-Raster mit 50 Mixed-LM-Fits vs. echte Beobachtungen mit einem
  gepoolten GAM).
- Spalten = Serienmenge (alle Serien mit `NumOddsMvt<20` vs. die 24.568, die
  über das ganze Fenster echt beobachtet sind).
- **B war die fehlende Zelle.** Sie nutzt den Produktionsschätzer wörtlich –
  dieselbe Restriktion `NumOddsMvt<20`, dieselbe Differenzierung gegen
  `OddsMvt0`, dasselbe `Endog = Match − OddsMvt0`, dieselben 50
  `fit_mixed_lm`-Aufrufe auf demselben imputierten Wide-Frame
  (`C_normalized/wide_imputed.h5`). Es unterscheidet sich **ausschließlich die
  Zeilenmenge**.

**Reproduktionskontrolle:** Zelle A, mit demselben Harness neu gerechnet,
reproduziert `C_normalized/beta1_curve.csv` auf max |Δβ₁| = 2,2e−16. Die
Kandidatenmenge wird im Skript aus dem Fehlmuster **vor** der Imputation neu
abgeleitet (kein Zwischen-Cache) und ergibt wieder exakt 24.568 Serien; deren
NaN-Anteil vor der Imputation ist 0,00 % gegenüber 7,85 % über alle Serien.

## Alle vier Zellen nebeneinander

Quelle `compare_2x2_composition.csv`. Die Mittelwerte sind auf einem
**gemeinsamen Träger** gebildet (Perzentile 2, 4, …, 98 – die Baseline-Punkte,
die im GAM-Gitter 1–99 liegen), damit die 50- und 200-Punkt-Gitter vergleichbar
sind; die nativen Mittel stehen daneben und weichen um ≤ 0,004 ab.

| Kennzahl | **A** Baseline, alle | **B** Baseline, nur vollst. beob. | **C** kontinuierlich, alle | **D** kontinuierlich, nur vollst. beob. |
|---|---:|---:|---:|---:|
| Serien | 174.392 | 24.568 | 175.266 | 24.568 |
| Gitterpunkte | 50 | 50 | 200 | 200 |
| **β₁ Mittel (gem. Träger)** | **1,224** | **1,234** | **1,006** | **1,200** |
| β₁ Mittel (nativ) | 1,220 | 1,233 | 1,006 | 1,200 |
| β₁ min | 1,031 | 1,158 | 0,771 | 1,087 |
| β₁ max | 2,592 | 1,308 | 1,289 | 1,299 |
| β₁ am Anfang | 2,592 | 1,273 | 1,289 | 1,299 |
| β₁ am Ende | 1,031 | 1,158 | 0,771 | 1,087 |
| β₁ bei Perzentil 50 | 1,127 | 1,255 | 0,913 | 1,205 |
| Anteil der Kurve > 1 | 100 % | 100 % | 44,9 % | 100 % |
| # signif. Perzentile | 1 | 16 | – | – |

Die Zeile „# signif. Perzentile" (β₁ nicht von 1 unterscheidbar) ist nur
innerhalb der Baseline-Spalten vergleichbar und **nicht** als „unverzerrter"
zu lesen: Zelle B hat ein Siebtel der Serien und damit breitere
Konfidenzintervalle. Für die kontinuierlichen Zellen ist die Kennzahl nicht
definiert (Splinegitter statt 50 Einzelregressionen).

## Die Zerlegung

|                          | alle Serien | nur vollst. beob. | **Kompositionseffekt** |
|--------------------------|---:|---:|---:|
| **Baseline / imputiert** | 1,224 | 1,234 | **−0,010** |
| **kontinuierlich / echt**| 1,006 | 1,200 | **−0,195** |
| **Methoden-/Imput.-effekt** | **+0,218** | **+0,034** | +0,184 (Interaktion) |

Das 2×2 ist – anders als das Leak×Normalisierung-2×2 der Stufe D – **stark
nicht-additiv**, und genau die Nicht-Additivität ist der Befund:

- **Methodeneffekt ohne Imputation: B − D = +0,034** (16 % der Gesamtlücke).
  Auf den vollständig beobachteten Serien, wo praktisch nichts zu imputieren
  ist, stimmen die beiden Verfahren fast überein: 1,234 (Perzentil-Raster,
  Mixed LM) gegen 1,200 (echte Zeitstempel, GAM). Resampling, Perzentil-Achse,
  Referenzpunkt, Gewichtung und Schätzer zusammen tragen also nur +0,034. Das
  bestätigt die Kanalzerlegung (Nachtrag 1) aus der anderen Richtung: der
  Schätzer ist nicht die Ursache.
- **Gesamtlücke: A − C = +0,218.** Davon sind 0,034 Methode; die verbleibenden
  **+0,184 (84 %)** sind der Interaktionsterm – der Teil, der nur entsteht,
  wo Imputation tatsächlich arbeitet.
- **Der Kompositionseffekt ist eine Eigenschaft des Verfahrens, nicht der
  Daten.** Auf den echten Beobachtungen beträgt er −0,195 (früh eröffnende
  Serien haben ein höheres, flacheres β₁); unter der Baseline-Methode schrumpft
  er auf −0,010, also **5 % des echten Werts**. Die Imputation löscht 95 % der
  wahren Heterogenität zwischen früh und spät eröffnenden Serien.

Der Mechanismus dahinter ist genau der aus Nachtrag 2: die Imputation ersetzt
die Frühpreise der Spät-Einsteiger durch Werte, die sich wie die der
Früh-Eröffner verhalten. Danach sehen alle Serien gleich aus – die Baseline
misst auf allen 174.392 Serien dasselbe Niveau, das die echten Daten nur auf
den 24.568 früh eröffnenden zeigen (1,224 vs. 1,234, praktisch identisch).

**Größenordnungskontrolle:** Der Masking-Test (Nachtrag 2, within-sample auf
denselben 24.568 Serien) bezifferte den Imputationseffekt auf +0,261 (echt
1,223 → imputiert 1,484, auf gemeinsamem Träger gerechnet). Der hier
unabhängig bestimmte Interaktionsterm liegt bei +0,184. Zwei
methodisch getrennte Wege, gleiches Vorzeichen und gleiche Größenordnung. Dass
der Masking-Wert höher liegt, ist erwartbar: der Test maskiert `OddsMvt0` bei
100 % der Serien, in der Produktion sind es 86 %.

**Konsistenzkontrolle B ↔ Masking-Test:** Zelle B (1,234; Ränder 1,273 →
1,158) und `masking_beta1_true.csv` (1,223; Ränder 1,263 → 1,161) messen
dasselbe Objekt auf zwei Wegen – Perzentil-Mixed-LMs auf dem
Produktions-Frame gegen ein gepooltes GAM auf den unmaskierten Wahrheitswerten
derselben Serien. Sie stimmen auf 0,011 überein.

## Schätzerrobustheit von Zelle B

`statsmodels` meldet bei Zelle B in 50 von 50 Fits „MLE on the boundary" und
in 3 von 50 „RE covariance singular" – die Random-Effects-Varianz läuft an den
Rand. Das ist **keine Eigenheit der restringierten Stichprobe**: Beide
Stichproben enthalten dieselben 24 Bookmaker, und die Boundary-Warnung tritt im
Produktionslauf über alle 174.392 Serien genauso auf (nachgeprüft an den
Perzentilen 2, 50 und 100 – Boundary in allen drei Fällen, „singular"
zusätzlich bei Perzentil 2). Es handelt sich also um eine Eigenschaft der
Produktionsspezifikation, nicht um einen Defekt von Zelle B.

Das Niveau hängt daran ohnehin nicht: dieselbe Spezifikation **ohne** Random
Effects (reines OLS) ergibt für Zelle B mittleres β₁ = 1,218 statt 1,233,
max |Δ| = 0,037, corr = 0,959
(`beta1_baseline_fully_observed_convergence.csv`). Die Aussage des 2×2 ist
gegen diese Wahl unempfindlich.

## Dateien

- `beta1_baseline_fully_observed.csv` – Zelle B, 50 Perzentile mit SE
- `beta1_baseline_fully_observed_convergence.csv` – Konvergenzzensus und
  OLS-Gegenrechnung für Zelle B
- `compare_2x2_composition.csv` – alle vier Zellen, Kennzahlen nebeneinander
- `beta1_2x2_composition_curves.csv` – die vier Kurven auf dem gemeinsamen
  Träger
- `composition_2x2.{pdf,png}` – Abbildung: vier Kurven + Zerlegung
- `_composition_2x2.py`, `_composition_2x2_plot.py` – Reproduktionsskripte

## Einschränkungen

- Die Spalte „nur vollständig beobachtete" ist keine Zufallsstichprobe, sondern
  **die früh eröffnenden Bookmaker** (100 % Verspätung 0). Das 2×2 trennt
  Imputation und Komposition sauber, sagt aber nichts darüber, wie sich die
  Imputation bei Spät-Einsteigern verhielte, wenn man deren Wahrheit kennen
  würde – die kennt man nicht.
- Die Zeilenachse bündelt Datenbasis *und* Schätzer. Zelle B zeigt, dass dieses
  Bündel klein ist (+0,034), aber es ist nicht weiter aufgelöst; die
  Einzelkanäle stehen in Nachtrag 1.
- Alle Mittelwerte sind Niveaumaße über die Kurve. Die *Form* – der steile
  Frühabfall der Baseline – ist in Nachtrag 2 behandelt und wird durch die
  Niveauzerlegung nicht ersetzt.
