# Hauptspezifikation der kontinuierlichen Unbiasedness-Regression

Rein diagnostisch, **kein Eingriff in die Produktions-Pipeline**. Erweitert den
kontinuierlichen Robustness-Check aus `../` um Kovariaten und Random Effects
und klärt, wie die Abhängigkeit der Bookmaker-Serien innerhalb eines Matchups
(R1-ii / R2) zu berücksichtigen ist.

## Spezifikation

Datenbasis wie in `../`: `shaped_data.h5`,
`filter_and_shape_data(normalize=True)`, Updates nach Anpfiff raus,
Nullvarianz raus, `NumOddsMvt < 20`, Referenzbeobachtung raus.

- `p_ref` = erster **echt beobachteter** normalisierter Preis der **eigenen**
  Bookmaker-Serie (nicht matchweit, nicht imputiert)
- `Endog = Match − p_ref`, `Exog = p(t) − p_ref`
- `X = log(Stunden bis Anpfiff)`
- Kovariaten: `TsDur` (standardisiert) + `Compet_Challenger_Men` +
  `Compet_ITF_Men` + `Compet_Misc` + `Compet_WTA`. **`NumOddsMvt` bewusst
  nicht.**
- ungewichtet, `k = 6`, `bs = "cr"`, `method = "fREML"`, `discrete = TRUE`

Stichprobe: **1.291.205 Zeilen**, 175.166 Serien, **20.741 Matchups**, 24
Bookmaker. Gegenüber dem Frame in `../` (1.292.338 Zeilen) kostet der neue
Anpfiff-Filter nur ~1.100 Zeilen. Stunden bis Anpfiff: Median 9,25, Minimum
0,017 h, Maximum 181,2 h.

### Zur Ableserichtung

`X = log(Stunden bis Anpfiff)` läuft **rückwärts** zur Perzentilachse aus
`../`: das **Fensterende** (Anpfiff) liegt beim **kleinsten** X. „Ende"
bezeichnet unten immer den anpfiffnahen Rand.

### Zwei Mittelwerte, nur einer ist vergleichbar

Das **Gittermittel** über ein gleichmäßiges log(Stunden)-Gitter gewichtet den
dünn besetzten fernen Rand über; es liegt bei ~0,90 und ist **nicht** mit dem
gepoolten β₁ = 1,006 aus `../` vergleichbar. Vergleichbar ist das
**beobachtungsgewichtete** Mittel (β₁ an 500 Quantilen von X): **0,988**. Alle
Aussagen unten benutzen dieses.

## 1) mgcv-Syntax für Random Effects — gegen die installierte Doku geprüft

mgcv 1.9-4, `/usr/lib/R/site-library/mgcv`.

- **Random Slope**: `s(Exog, Bookies, bs = "re")`. `random.effects.Rd`: „If
  `g` is a factor and `x` is numeric, then `s(x,g,bs="re")` produces an i.i.d.
  normal random slope relating the response to `x` for each level of `g`."
  `smooth.construct.re.smooth.spec.Rd` ergänzt, dass `s(x,z,bs="re")` die
  Modellmatrix `~x:z-1` anhängt.
- **Korrelation Intercept/Slope: in mgcv nicht darstellbar.** Die Hilfeseite
  heißt „*Simple* random effects in GAMs" und beginnt mit „`gam` can deal with
  simple **independent** random effects"; die Koeffizienten sind „assumed
  i.i.d. normal" unter einer Ridge-Penalty. Beide dokumentierten Auswege
  helfen nicht: `xt` nimmt eine Präzisionsmatrix nur „known **to within a
  multiplicative constant**"; `paraPen` kombiniert **feste** Präzisionsmatrizen
  mit über *log*-Smoothing-Parameter positiv skalierten Gewichten. Eine freie,
  vorzeichenbehaftete Kovarianz ist damit nicht parametrisierbar.

Für die korrelierte Struktur aus der R1-ii-Arbeit (`bookies_cov`) bleibt
`gamm4` (hier **nicht installiert**) oder direkt `lme4` — siehe Abschnitt 3.

## 2) Machbarkeit: der Match-Intercept sprengt `bam()`

Quelle: `feasibility_scaling.csv`, Skript `_feasibility.py`.

mgcv behandelt Random Effects **dicht**. `random.effects.Rd`: „`gam` can be
slow for fitting models with large numbers of random effects, because it
**does not exploit the sparsity** that is often a feature of parametric random
effects." 20.741 Matchup-Level ergeben p ≈ 20.800.

| m Matchups | n | p | Laufzeit | Peak-RSS |
|---:|---:|---:|---:|---:|
| 400 | 25.831 | 465 | 3,3 s | (nicht aussagekräftig) |
| 800 | 50.677 | 865 | 4,8 s | (nicht aussagekräftig) |
| 1.600 | 102.847 | 1.665 | 37,3 s | (nicht aussagekräftig) |
| 3.200 | 201.538 | 3.265 | 344,0 s | 3,78 GB |

Von p = 1.665 auf 3.265 (×1,96) steigt die Laufzeit um das 9,2-fache; p³
sagt 7,5 vorher, gemessen ist also ~p^3,3 — die Cholesky-Skalierung.
Hochgerechnet auf p = 20.806: **~25 h**. Speicher: eine dichte p×p-Matrix
sind 3,46 GB, fREML braucht mehrere gleichzeitig (Kreuzprodukt,
Cholesky-Faktor, Ableitungen je Smoothing-Parameter) — **Untergrenze ~17 GB**
gegen 11,4 GB auf dieser Maschine.

> **Zwei Warnungen zu diesem CSV.** Die Spalte `secs`-Extrapolation im
> Skriptlog nennt 243,9 min; sie stammt aus einem `a + b·p²`-Fit und
> **unterschätzt um rund das 6-fache**, weil die Skalierung kubisch ist. Und
> die `peak_gb`-Werte der ersten drei Zeilen sind vom Prozess-Höchststand
> (`ru_maxrss`, monoton seit Prozessstart) dominiert und zeigen nicht den
> Zuwachs je Fit; erst ab m = 3.200 übersteigt der Fit die Grundlast. In
> `_lme4_main.py` ist das auf aktuellen RSS aus `/proc/self/statm` umgestellt.

**Konsequenz:** M_d in `bam()` wurde **nicht** gerechnet.

## 3) Stufenreihe M_a bis M_c (mgcv) — die REs bewegen β₁ kaum

Quellen: `ladder_summary.csv`, `ladder_beta1.csv`, `ladder_marks.csv`,
Skript `_ladder.py`.

| | p | Laufzeit | β₁ beob.gew. | β₁ fern (59,9 h) | β₁ Ende (0,067 h) | SE Ende | Residual-sd |
|---|---:|---:|---:|---:|---:|---:|---:|
| M_a ohne REs | 17 | 4,2 s | 0,9847 | 1,0549 | 0,8074 | 0,045 | 0,4589 |
| M_b + Bookmaker-Intercept | 41 | 3,6 s | 0,9848 | 1,0550 | 0,8074 | 0,045 | 0,4589 |
| M_c + Bookmaker-Slope | 65 | 3,8 s | 0,9881 | 1,0544 | 0,8129 | 0,053 | 0,4588 |

Der Bookmaker-**Intercept** ändert β₁ um exakt 0,000 — das ist keine
Überraschung, sondern Algebra: ein Intercept-RE steht in keiner Spalte der
`Exog`-Kontrastmatrix. Der **Slope** bewegt +0,002 im Mittel und +0,006 am
Rand.

Varianzkomponenten M_c (sd-Skala): Bookmaker-Intercept **0,00325**,
Bookmaker-Slope **0,07693**, Residual **0,45883**.

> **Gotcha, der einmal zu falschen Zahlen führte:** `m$scale` matcht in R per
> Teilstring auf `m$scale.estimated` (`TRUE`) und liefert still eine
> Residualvarianz von exakt 1,000. Richtig ist **`m$sig2`**. Alle sd-Werte
> oben sind mit `sig2` gerechnet; σ² = 0,2105 passt zu var(`Endog`) ≈ 0,21.

edf/F (M_c): `s(X)` 3,93/12,4 · `s(X):Exog` 5,13/265,5 · `s(Bookies)`
15,94/2,77 · `s(Exog,Bookies)` 19,97/7,70, alle p < 2e−16.

### Diagnostik (M_c)

`gam.check()`: **Model rank 65/65**, also keine Rangdefizienz; k-index 1,0 mit
p = 0,41 / 0,46 für die beiden X-Smooths, k = 6 ist ausreichend; Gradient
1e−5…1e−8, Hessematrix positiv definit.

`concurvity(full = FALSE)`, `estimate` — die für β₁ entscheidende Zeile ist
unauffällig:

```
                 para  s(X) s(X):Exog s(Bookies) s(Exog,Bookies)
s(X):Exog       0.000 0.000     1.000      0.000           0.057
```

`s(X):Exog` **ist** β₁ und ist gegen alles andere praktisch orthogonal
(max 0,057). Zwei andere Zellen sind hoch (`s(X)`↔`para` 0,895,
`s(Bookies)`↔`para` 1,000), betreffen aber den β₁-Kontrast nicht; für
`re`-Terme sind Concurvity-Maße ohnehin unzuverlässig — ein 24-stufiges RE
kann nicht im 6-spaltigen parametrischen Raum liegen.

Diese Prüfung war Pflicht, weil bei den Kontrollmodellen der
Verspätungsanalyse (`../entry_delay/`) die edf/F-Tabelle unauffällig aussah,
während das Modell rangdefizient war.

### k-Sensitivität (M_c)

Quelle: `ladder_k_sensitivity.csv`.

| k | p | Gittermittel | **beob.gew.** | Ende |
|---:|---:|---:|---:|---:|
| 6 | 65 | 0,901 | **0,988** | 0,813 |
| 10 | 73 | 0,902 | **0,988** | 0,810 |
| 20 | 93 | 0,888 | **0,988** | 0,810 |

Das beobachtungsgewichtete Mittel ist auf drei Nachkommastellen invariant. Das
Gittermittel wackelt nur deshalb, weil das gleichmäßige log-Gitter den fernen
Rand übergewichtet: dort liegt 1 % der Beobachtungen, und eine k=20-Basis
schwingt entsprechend (β₁ fern springt auf 1,401). **Der ferne Rand ist ein
Randartefakt und nicht interpretierbar** — eine Verschärfung der Regel aus
`../README.md`, die bisher nur die Zahl der Wendepunkte betraf.

## 4) Hauptspezifikation über lme4 — im Niveau stabil, in der Kovarianz entartet

Quellen: `lme4_gate.csv`, `lme4_main_summary.csv`, `lme4_varcomp.csv`,
`lme4_beta1.csv`, `lme4_marks.csv`, `lme4_k_sensitivity.csv`,
Skript `_lme4_main.py`.

Weil `bam()` den Match-Intercept nicht tragen kann, wird die Spline-Basis
(k = 6, `cr`, Constraint absorbiert, über `smoothCon`) explizit gebaut und in
`lmer()` gesteckt — dieselben 5 Spalten tragen Haupteffekt und
`Exog`-Interaktion. Das nutzt lme4s Sparsity und erlaubt **korrelierte** REs.
Preis: feste statt penalisierter Basis.

### Gate gegen mgcv-M_c (ohne Matchup)

| Größe | mgcv | lme4 | Diff |
|---|---:|---:|---:|
| β₁ beob.gew. | 0,98810 | 0,98917 | **+0,00107** |
| β₁ Ende | 0,81290 | 0,85017 | +0,03727 |
| Residual-sd | 0,45883 | 0,45880 | −0,00003 |
| sd Bookmaker-Intercept | 0,00325 | 0,00314 | |
| sd Bookmaker-Slope | 0,07693 | 0,12525 | |

Penalisiert vs. fest kostet **+0,001 im Niveau** und +0,037 am Rand — der
Randwert reagiert erwartungsgemäß stärker, weil dort keine Strafe bremst.

### Hauptspezifikation `+ (1 | Matchup)`, `REML = FALSE`

266 s, Peak-RSS 3,85 GB, keine Konvergenzmeldungen.

| Komponente | vcov | sd / corr |
|---|---:|---:|
| Matchup-Intercept | 0,193652 | 0,440059 |
| Bookmaker-Intercept | 2,94e−08 | **0,000171** |
| Bookmaker-Slope (`Exog`) | 0,577036 | 0,759629 |
| **`bookies_cov`** | **−5,0797e−05** | corr −0,390 |
| Residual | 0,000226 | 0,015036 |

β₁ beobachtungsgewichtet **0,4664**, Ende **0,3883 (SE 0,1551)**.
Stundenmarken: 24 h 0,563 · 12 h 0,485 · 6 h 0,426 · 3 h 0,385 · 1 h 0,352 ·
0,25 h 0,355.

**Querprüfung gegen R1-ii** (`results/crossed_mixed_lm_single_test.csv`): zwei
Komponenten stimmen fast exakt überein — `match_var` 0,19316 dort gegen
0,19365 hier, `bookies_cov` −5,073e−05 gegen −5,0797e−05. Die
Bookmaker-**Slope**-Varianz unterscheidet sich um Faktor ~200 (0,00287 gegen
0,577); das ist ein Skalenartefakt, weil R1-ii auf ein Preisniveau regressiert,
hier aber `Exog = p(t) − p_ref` mit sd ≈ 0,047 steht und Slope-Varianz mit
1/Skala² geht.

### Warum die Kovarianzstruktur entartet

Drei Symptome: der Bookmaker-Intercept fällt auf sd 0,000171 (Randwert; bei
k = 10 meldet lme4 explizit `boundary (singular) fit`), der Slope springt vom
6-fachen des Gate-Werts, und die SE von β₁ ist über das **gesamte** Gitter
konstant 0,1551 — ein Zeichen, dass `Var(c_Exog)` alles dominiert.

Die Ursache ist strukturell und nicht durch Tuning behebbar: **`Endog` ist
innerhalb einer Serie konstant** (`Match` ist matchup-, `p_ref` serienweit
fest). Siehe Abschnitt 5.

### k-Sensitivität der Hauptspezifikation

| k | β₁ beob.gew. | Ende | sd Matchup | Konvergenz | Laufzeit | Peak |
|---:|---:|---:|---:|---|---:|---:|
| 6 | 0,46639 | 0,3883 | 0,44006 | sauber | 291 s | 4,26 GB |
| 10 | 0,46620 | 0,3732 | 0,44013 | **boundary (singular) fit** | 790 s | 4,93 GB |
| 20 | 0,46636 | 0,3580 | 0,43750 | sauber | 1362 s | 6,76 GB |

**Das Niveau ist invariant** (0,4664 / 0,4662 / 0,4664), `sd_matchup` stabil.
Der Randwert driftet wie in Abschnitt 3. Die Entartung sitzt im
Bookmaker-Intercept, nicht in β₁.

Beide lme4-Fits melden zusätzlich
`Some predictor variables are on very different scales: consider rescaling`.
Angesichts der Übereinstimmung mit mgcv auf 0,001 ist das ein numerischer
Hinweis, kein Konvergenzproblem — hier bewusst nicht unterdrückt.

## 5) Absorption: der Match-Intercept frisst die abhängige Variable

Quellen: `absorption_anova.csv`, `pref_within_between.csv`,
Skript `_cluster_inference.py`.

| Ebene | n | var gesamt | var between | **Anteil** |
|---|---:|---:|---:|---:|
| Serienebene | 175.166 | 0,205269 | 0,204927 | **99,83 %** |
| Beobachtungsebene | 1.291.205 | 0,212712 | 0,212314 | 99,81 % |
| modellbasiert | | | | 99,88 % |

**99,8 % der Varianz von `Endog` liegen auf Matchup-Ebene.** Ein
Match-Random-Intercept absorbiert damit praktisch die gesamte abhängige
Variable (sd 0,440 von insgesamt 0,459), die Residual-sd fällt auf 0,015.

Was für die Within-Match-Identifikation übrig bleibt:

| | sd |
|---|---:|
| `p_ref` insgesamt | 0,19002 |
| `p_ref` innerhalb eines Matchups (gepoolt, 18.191 Matchups mit ≥ 2 Bookmakern) | **0,01970** |
| Median der Within-sd | 0,01001 |

Das sind **10,4 % der Gesamtstreuung, also 1,1 % der Varianz**. Bookmaker je
Matchup: Median 7, Mittel 8,4, Spanne 1–24.

> Die Spalte `sd_between` in `pref_within_between.csv` (0,2072) ist die
> **ungewichtete** sd der Matchup-Mittel bei ungleichen Gruppengrößen und
> übersteigt deshalb `sd_total`. Sie ist **kein** Teil einer exakten Zerlegung
> — dafür ist die ANOVA oben zuständig.

**Damit ist β₁ = 0,466 (Hauptspezifikation) und β₁ = 0,988 (M_c) kein
Präzisions-Trade-off, sondern ein Wechsel des Schätzobjekts:** die
Hauptspezifikation identifiziert β₁ ausschließlich aus 1,1 % der
`p_ref`-Varianz zwischen Bookmakern desselben Matchups.

## 6) Cluster-robuste Inferenz — die empfohlene Fassung

Quellen: `cluster_robust_beta1.csv`, `cluster_robust_marks.csv`,
Skript `_cluster_inference.py`, Abbildung `main_spec.{png,pdf}`.

Statt die 99 % identifizierende Variation über ein Random Intercept
auszugeben, wird die Matchup-Abhängigkeit über einen **CR1-Cluster-Sandwich**
auf M_c berücksichtigt — der Punktschätzer bleibt unverändert:

```
V_CR1 = c · (X'X)⁻¹ [ Σ_g X_g'u_g u_g'X_g ] (X'X)⁻¹,
c = G/(G−1) · (N−1)/(N−K),  G = 20.741,  N = 1.291.205,  K = 17
```

Übertragbarkeitsprüfung: `max |β₁(OLS) − β₁(M_c lme4)| = 0,00600` — die
Bookmaker-REs verschieben den Punktschätzer nicht, der OLS-Sandwich gilt
für M_c.

| SE-Vergleich | Median | Spanne |
|---|---:|---|
| Cluster / modellbasiert | **3,02** | 2,56–5,62 |
| Cluster / OLS-iid | **6,34** | |

| Stunden | β₁ | SE Cluster | SE Modell | 95 % CI (Cluster) | 1 enthalten? |
|---:|---:|---:|---:|---|---|
| 24 | 1,244 | 0,114 | 0,032 | [1,020 · 1,469] | nein (darüber) |
| 12 | 1,083 | 0,088 | 0,029 | [0,911 · 1,255] | **ja** |
| 6 | 0,938 | 0,084 | 0,028 | [0,774 · 1,103] | **ja** |
| 3 | 0,839 | 0,089 | 0,029 | [0,663 · 1,014] | **ja** |
| 1 | 0,759 | 0,093 | 0,030 | [0,577 · 0,940] | nein (darunter) |
| 0,25 | 0,767 | 0,092 | 0,034 | [0,586 · 0,948] | nein (darunter) |

**Das ändert die inferenzielle Aussage materiell.** Mit modellbasierten SEs
wäre die Kurve fast überall signifikant von 1 verschieden; unter
Matchup-Clusterung ist sie das nur am fernen Rand (darüber) und anpfiffnah
(darunter) — **im mittleren Bereich ist β₁ nicht von 1 zu unterscheiden**.

### Warum ein Bootstrap statt eines Sandwich zu teuer war

M_c braucht 58 s je Fit. B = 300 wären sequentiell 4,8 h; parallel begrenzt
nicht die Kernzahl, sondern der Speicher (3,39 GB je Fit, drei Prozesse ≈
10,2 GB gegen 11,4 GB — genau die Konstellation, die in dieser Sitzung schon
einmal die WSL-VM neu gestartet hat). Bei G = 20.741 Clustern ist der Sandwich
die asymptotische Fassung dessen, was der Bootstrap approximiert; ein
Bootstrap-Vorteil bestünde vor allem bei wenigen Clustern (Faustregel < 50).

Eine unabhängige Bestätigung mit **B = 100** (zwei Prozesse à 50 Replikate,
`_cluster_bootstrap.py`) war trotzdem begründet, weil die Cluster stark
unbalanciert sind (1–24 Bookmaker je Matchup, Median 7) und die
CR1-Korrektur ein **Skalar** ist, der davon nichts sieht.

### 6a) Bootstrap-Validierung (B = 100) — Ränder bestätigt, Mitte 10–22 % weiter

Quellen: `bootstrap_vs_sandwich.csv`, `bootstrap_vs_sandwich_marks.csv`,
`bootstrap_beta1_part{0,1}.npy`, Skripte `_cluster_bootstrap.py` und
`_bootstrap_compare.py`. Durchlauf: 2 × 50 Replikate, **1 singulärer Fit,
0 Fehler**, 145,3 bzw. 151,9 min.

| SE-Verhältnis Bootstrap / CR1-Sandwich | |
|---|---:|
| Median | **1,109** |
| Mittel | 1,077 |
| Spanne | 0,849–1,225 |

| Stunden | β₁ | SE Sandwich | **SE Bootstrap** | SE modellbasiert | Verhältnis B/S | Bootstrap-Perzentil-CI | 1 enthalten? |
|---:|---:|---:|---:|---:|---:|---|---|
| 24,5 | 1,244 | 0,1148 | 0,1143 | 0,0322 | **1,00** | [1,070 · 1,495] | nein (darüber) |
| 12,3 | 1,090 | 0,0886 | 0,1015 | 0,0286 | 1,15 | [0,910 · 1,317] | **ja** |
| 5,8 | 0,933 | 0,0840 | 0,1028 | 0,0285 | **1,22** | [0,740 · 1,158] | **ja** |
| 2,9 | 0,835 | 0,0896 | 0,1087 | 0,0294 | 1,21 | [0,631 · 1,060] | **ja** |
| 0,97 | 0,758 | 0,0926 | 0,1080 | 0,0300 | 1,17 | [0,558 · 0,961] | nein (darunter) |
| 0,25 | 0,768 | 0,0926 | 0,0942 | 0,0342 | 1,02 | [0,603 · 0,938] | nein (darunter) |

**Der Sandwich stimmt an beiden Rändern praktisch exakt** (Verhältnis 1,00 bei
24,5 h und 1,02 bei 0,25 h) und **unterschätzt die Streuung in der
Fenstermitte um 10–22 %**. Das ist genau das erwartete Muster bei
unbalancierten Clustern: wo die Schätzung überwiegend von Matchups mit vielen
Bookmakern getragen wird, greift eine skalare Korrektur zu kurz. Die
Abweichung ist real, aber moderat — 41 von 100 Gitterpunkten liegen mehr als
15 % auseinander.

**Bootstrap-Bias vernachlässigbar:** Median der Differenz (Mittel der
Replikate − Punktschätzer) −0,0027, maximaler |Bias| 0,0505.

**Die inhaltlichen Schlüsse sind identisch.** Das Muster der Perzentil-CIs
deckt sich Punkt für Punkt mit dem Sandwich: β₁ ist bei 24 h signifikant
**über** 1, bei 1 h und 0,25 h signifikant **unter** 1, und bei 12 h / 6 h /
3 h **nicht von 1 zu unterscheiden**. Der SE-Faktor gegenüber der
modellbasierten Inferenz steigt lediglich von ~3,0 auf **3,3–3,6** in der
Mitte — die Aussage „Clusterung kostet rund den Faktor 3" bleibt.

> **Berichtet werden die Bootstrap-SEs als Primärinferenz**, der Sandwich als
> Kontrolle. Er bleibt die schnelle, analytische Fassung (Sekunden statt
> 2,5 h) und ist an den Rändern nicht zu unterscheiden; in der Mitte ist der
> Bootstrap die konservativere und wegen der Unbalanciertheit die
> angemessenere Wahl.

## 7) Randdiagnostik: Trim bei 48 h und das Artefakt der festen Basis

Quellen: `edge_distribution.csv`, `edge_beta1_fullrange.csv`,
`edge_beta1_by_k.csv`, `fixed_vs_penalised_trim.csv`, Skripte
`_edge_diagnostics.py` und `_edge_plot.py`, Abbildung
`main_spec_edge.{png,pdf}`. **Diagnostik für die Belege, nicht für den
Haupttext.**

### Datendichte über die Achse

| Bin | Beobachtungen | Serien | Anteil | kumuliert von links |
|---|---:|---:|---:|---:|
| > 72 h | 1.923 | 744 | 0,15 % | 0,15 % |
| 48–72 h | 36.387 | 11.728 | 2,82 % | 2,97 % |
| 24–48 h | 174.795 | 49.483 | 13,54 % | 16,50 % |
| 12–24 h | 325.960 | 111.006 | 25,25 % | 41,75 % |
| 6–12 h | 244.708 | 100.656 | 18,95 % | 60,70 % |
| 3–6 h | 164.780 | 81.786 | 12,76 % | 73,46 % |
| 1–3 h | 173.715 | 90.036 | 13,45 % | 86,92 % |
| < 1 h | 168.937 | 93.526 | 13,08 % | 100 % |

### Der Knick links ist ein Artefakt der unpenalisierten festen Basis

Die lme4-/Sandwich-/Bootstrap-Route braucht eine **feste** Basis (Abschnitt 4).
Ohne Strafe schwingt sie am linken Rand aus; die **penalisierte**
mgcv-Schätzung tut das nicht:

| Stunden | feste Basis | SE | penalisiert (mgcv M_c) | SE |
|---:|---:|---:|---:|---:|
| 59,9 | 1,349 | 0,400 | 1,054 | 0,052 |
| 52,2 | 0,952 | 0,285 | 1,071 | 0,044 |
| 48,7 | 0,851 | 0,271 | 1,080 | 0,042 |
| 45,5 | **0,825** | 0,257 | 1,089 | 0,040 |
| 39,7 | 0,918 | 0,204 | 1,106 | 0,037 |
| 34,6 | 1,079 | 0,146 | 1,114 | 0,036 |

**Kernaussage:** Der Abfall auf 0,83 links ist **kein Befund**. Die
penalisierte Schätzung ist dort **monoton** (1,054 → 1,150 bei 24 h), der
Bereich enthält **< 3 % der Beobachtungen**, und der Ausschlag ist vom
Konfidenzband ohnehin gedeckt (SE 0,26–0,40 gegen 0,03 in der Fenstermitte).

Stabilität über k (Spannweite von β₁ für k = 6/10/20): innerhalb des
1.–99.-Perzentil-Gitters Median **0,032**, links außerhalb Median **2,379**
(max 4,417). k = 6 und k = 10 stimmen praktisch überall überein; nur k = 20
oszilliert links und liefert jenseits von 72 h Unsinn (−0,89 bei 181 h,
−3,35 bei 120 h).

### Übereinstimmung fester vs. penalisierter Basis innerhalb des Trims

Das ist die Zahl, mit der die feste Basis gerechtfertigt wird — beide Kurven
liegen auf demselben Gitter, daher direkte Differenz:

| Trim | Gitterpunkte | Median \|Δ\| | max \|Δ\| | p90 \|Δ\| | Datenanteil |
|---:|---:|---:|---:|---:|---:|
| **≤ 48 h** | 96 | **0,0159** | **0,2639** | 0,0585 | 97,0 % |
| ≤ 36 h | 92 | 0,0155 | 0,0941 | 0,0385 | 91,2 % |
| ≤ 24 h | 86 | 0,0152 | 0,0894 | 0,0284 | 83,5 % |

Im Median stimmen die beiden Fassungen auf **0,016** überein. Die Abweichung
konzentriert sich auf 36–60 h (Maximum 0,264 bei 45,5 h) und ist ab ~34 h
verschwunden (0,043).

> **Offener Punkt:** Die Hauptabbildung ist bei **48 h** getrimmt (97 % der
> Beobachtungen, 24 h liegt komfortabel im Inneren). Das Maximum der
> Basis-Diskrepanz liegt damit aber genau am neuen linken Rand. Ein Trim bei
> **36 h** würde den Rest auf 0,094 drücken und immer noch 91 % der Daten
> behalten — bewusst offen gelassen, nicht stillschweigend entschieden.

### Was getrimmt wird und was nicht

Das **Rechengitter** bleibt beim 1.–99. Perzentil (59,9–0,067 h), damit die
bereits gerechneten Bootstrap-Replikate (`bootstrap_beta1_part{0,1}.npy`,
2,5 h Rechenzeit) auf demselben Gitter gültig bleiben. Getrimmt wird bei
**Auswertung und Darstellung** (`HMAX = 48` in `_main_spec_plot.py`) — die
Schätzungen sind identisch, nur das Berichtsfenster ist enger. Die
Stundenmarken (24 … 0,25 h) liegen ohnehin alle innerhalb.

## Fazit für R1-ii / R2

Die Abhängigkeit der Serien innerhalb eines Matchups lässt sich hier über
**cluster-robuste Inferenz** erfüllen, nicht nur über ein Match-Random-Intercept:

1. Der Match-Intercept gibt 99,8 % der Varianz der abhängigen Variablen aus,
   um aus 1,1 % der `p_ref`-Varianz zu identifizieren — Ergebnis sind
   entartete Varianzkomponenten und ein schwach identifiziertes
   β₁ = 0,466 ± 0,155.
2. Cluster-robuste Inferenz berücksichtigt dieselbe Abhängigkeit, lässt den
   Populationsschätzer β₁ = 0,988 unangetastet und beziffert den Preis des
   bisherigen Ignorierens: **rund 3× die modellbasierten SEs** (Sandwich
   3,0×; Bootstrap 3,3–3,6× in der Fenstermitte). Berichtet werden die
   Bootstrap-SEs, der Sandwich als Kontrolle — beide führen zu denselben
   Schlüssen.

**Wichtige Unterscheidung für den Text:** cluster-robuste Inferenz behebt
**Abhängigkeit**, nicht **Konfundierung**. Sollte der Einwand lauten, dass
match-spezifische ausgelassene Variablen mit `Exog` korrelieren, hilft nur der
Within-Match-Schätzer — zum oben bezifferten Preis. Lautet er, dass Serien
desselben Matchups keine unabhängigen Beobachtungen sind, ist er mit dem
Sandwich vollständig beantwortet.

## Dateien

- `_feasibility.py` — Frame-Aufbau und Skalierungsmessung für `bam()`
- `_ladder.py` — M_a/M_b/M_c, Diagnostik, k-Sensitivität (mgcv)
- `_lme4_main.py` — Basis-Konstruktion, Gate, Hauptspezifikation,
  k-Sensitivität (lme4)
- `_cluster_inference.py` — ANOVA-Absorption, `p_ref`-Streuung, CR1-Sandwich
- `_cluster_bootstrap.py` — Cluster-Bootstrap zur Validierung des Sandwich
  (Aufruf: `_cluster_bootstrap.py <part> <n_rep>`, zwei Prozesse à 50)
- `_bootstrap_compare.py` — Bootstrap-SEs gegen den Sandwich
- `_edge_diagnostics.py` — Datendichte über die Achse, β₁ über den vollen
  beobachteten Bereich für k = 6/10/20
- `_edge_plot.py` — Randdiagnostik-Abbildung
- `_main_spec_plot.py` — Hauptabbildung (Trim `HMAX = 48`)
- `feasibility_scaling.csv` — Laufzeit/Speicher je Teilstichprobe
- `ladder_{summary,beta1,marks,k_sensitivity}.csv` — Stufenreihe (mgcv)
- `lme4_{gate,main_summary,varcomp,beta1,marks,k_sensitivity}.csv` — lme4
- `absorption_anova.csv`, `pref_within_between.csv` — Absorptionsrechnung
- `cluster_robust_{beta1,marks}.csv` — β₁ mit CR1-Band, drei SE-Varianten
- `bootstrap_beta1_part{0,1}.npy` — die 2 × 50 β₁-Kurven der Replikate
  (je 40 KB, committet, damit der Vergleich ohne 2,5 h Neurechnung
  reproduzierbar bleibt)
- `bootstrap_part{0,1}.csv` — SE und Mittel je Teillauf
- `bootstrap_vs_sandwich{,_marks}.csv` — Bootstrap gegen Sandwich gegen
  modellbasiert auf demselben Gitter
- `edge_distribution.csv` — Beobachtungen und Serien je Stunden-Bin
- `edge_beta1_fullrange.csv` — β₁ über 0,017–181 h für k = 6/10/20
  (penalisiert)
- `edge_beta1_by_k.csv` — β₁ an ausgewählten Stunden je k, mit Fallzahlen
- `fixed_vs_penalised_trim.csv` — Übereinstimmung beider Basen im Trim
- `main_spec.{png,pdf}` — Hauptabbildung: β₁ über Stunden vor Anpfiff bis
  48 h mit Bootstrap-Band (primär), Sandwich und modellbasiertem Band, dazu
  die penalisierte mgcv-Kurve als dünne Referenz; daneben die
  Perzentil-Baseline auf identischer y-Achse
- `main_spec_edge.{png,pdf}` — Randdiagnostik: voller beobachteter Bereich
  für k = 6/10/20 mit markierten Trim-Zonen, darunter die Datendichte

  (alle PNG/PDF **gitignoriert**, aus den `_*_plot.py` regenerierbar)

---

# Nachtrag – Simultane Inferenz und RMSE-Grössenordnung (R1-vii)

R1-vii hat zwei Teile: (a) die ökonomische Grössenordnung des RMSE-Rückgangs
sei bescheiden, und (b) das Narrativ über Phasen des Lernens beruhe auf
wiederholten **punktweisen** Konfidenzintervallen; gefordert sind formale
Tests mit **simultanen** Bändern oder ein glatteres dynamisches Modell des
Koeffizientenpfads.

Das glatte dynamische Modell ist die Hauptspezifikation dieses Verzeichnisses
(Abschnitte 3–6). Was fehlte, war die simultane Inferenz darauf — und die
Einordnung des RMSE. Skripte: `_simultaneous.py` (rechnet nur auf den
gespeicherten Bootstrap-Replikaten, keine Datenladung) und
`_rmse_magnitude.py`.

## 8) Simultane Bänder und globale Tests

Grundlage sind die B = 100 Cluster-Bootstrap-Replikate aus Abschnitt 6a,
getrimmt auf das Berichtsfenster ≤ 48 h (96 Gitterpunkte).

### Der kritische Wert

Die Kovarianzmatrix von β₁(·) über das Gitter hat **effektiven Rang 5** — der
Pfad lebt in der k = 6-Splinebasis. Damit ist sie aus 100 Replikaten gut
geschätzt, und der sup-t-Wert lässt sich aus N(0, Σ̂) simulieren, statt das
95-%-Quantil eines Maximums roh aus 100 Ziehungen zu nehmen.

| | kritischer Wert |
|---|---:|
| punktweise | 1,960 |
| **sup-t (Gauss-Simulation, 200.000 Ziehungen)** | **2,617** (1,34×) |
| sup-t roh aus B = 100 (Kontrolle) | 2,516 |

### Das Band

| Stunden | β₁ | SE (Bootstrap) | punktweises 95 % | **simultanes 95 %** |
|---:|---:|---:|---|---|
| 24,5 | 1,244 | 0,114 | [1,020 · 1,468] | [0,945 · 1,543] |
| 12,3 | 1,090 | 0,101 | [0,891 · 1,289] | [0,824 · 1,355] |
| 5,8 | 0,932 | 0,103 | [0,731 · 1,134] | [0,663 · 1,202] |
| 2,9 | 0,835 | 0,109 | [0,622 · 1,049] | [0,551 · 1,120] |
| 0,97 | 0,758 | 0,108 | [0,546 · 0,970] | [0,475 · 1,040] |
| 0,25 | 0,768 | 0,094 | [0,583 · 0,952] | [0,521 · 1,014] |

**Punktweise schliessen 44 von 96 Gitterpunkten die 1 aus, simultan 0 von 96.**

### Zwei globale Tests

| H0 | sup-\|t\| | krit. 5 % | p | Ergebnis |
|---|---:|---:|---:|---|
| β₁(t) = 1 für alle t | 2,509 | 2,617 | **0,066** | **nicht verworfen** |
| β₁(t) konstant | 3,998 | 2,660 | **0,0006** | **verworfen** |

Dazu der Randkontrast als Effektmass:

```
β₁(24,5 h) − β₁(0,25 h) = 0,477   SE 0,117   t = 4,08
Bootstrap-Perzentil-CI [0,261 · 0,705]
```

**Die Aufteilung ist der eigentliche Befund.** Dass β₁ an irgendeiner
*bestimmten* Stelle von 1 verschieden ist, überlebt die simultane Korrektur
**nicht**. Dass es überhaupt einen **Pfad** gibt — β₁ fällt monoton von ~1,24
auf ~0,77, also von Unterreaktion durch Unverzerrtheit in leichte
Überreaktion — überlebt sie **deutlich**.

### Trim-Sensitivität

Abschnitt 7 hatte den Trim offen gelassen; ein sup-Test maximiert über alle
Gitterpunkte und ist deshalb auf den linken Rand empfindlich.

| Trim | Punkte | c_sup | sup-\|t\| Niveau | p | sup-\|t\| Form | p |
|---:|---:|---:|---:|---:|---:|---:|
| 48 h | 96 | 2,620 | 2,509 | 0,0663 | 3,998 | 0,00063 |
| 36 h | 92 | 2,559 | 2,509 | 0,0571 | 4,091 | 0,00039 |
| 24 h | 86 | 2,458 | 2,509 | **0,0439** | 4,106 | 0,00029 |

**Der Niveautest liegt genau auf der 5-%-Grenze und kippt mit dem
Berichtsfenster** (0,066 / 0,057 / 0,044). Er wird deshalb als *nicht
verworfen* berichtet, mit ausgewiesener Sensitivität — nicht als knapper
Erfolg beim engsten Trim. Der Formtest ist gegen den Trim unempfindlich.

### Gegenrechnung auf der publizierten Perzentil-Kurve

Was die 50 punktweisen Mixed-LM-Fits übrig lassen, wenn man Multiplizität
(Šidák über 50 Tests) und Clusterung (SE × 3 aus Abschnitt 6) berücksichtigt:

| Fassung | z | SE-Faktor | Perzentile mit CI ohne 1 |
|---|---:|---:|---:|
| punktweise, modellbasiert (publiziert) | 1,960 | 1,0 | **49 / 50** |
| Šidák über 50 Tests | 3,283 | 1,0 | 47 / 50 |
| punktweise, SE × 3 | 1,960 | 3,0 | 18 / 50 |
| **Šidák + SE × 3** | 3,283 | 3,0 | **1 / 50** |

Die Multiplizität allein kostet fast nichts (49 → 47); die Clusterung kostet
fast alles. Beides zusammen lässt **ein** Perzentil übrig.

## 9) Ökonomische Grössenordnung des RMSE-Rückgangs

### Was die Kurve in Figur 3 misst

Der geplottete `rmse` ist der **Residual-RMSE der Unbiasedness-Regression**
(`fit_mixed_lm.py:60`), nicht der RMSE des Preises. Er fällt über das Fenster
von 0,45566 auf 0,45081 (**−1,06 %**), in Brier-Einheiten von 0,20762 auf
0,20323 (−2,12 %), Brier Skill Score 16,95 % → 18,71 %.

### Der direkte, kompositionsfreie Vergleich

Auf **echten** Beobachtungen, je Serie erste gegen letzte, matchup-cluster-robust
(175.166 Serien, 20.741 Matchups):

| | Brier | RMSE | BSS |
|---|---:|---:|---:|
| Münzwurf (p ≡ 0,5) | 0,25000 | 0,50000 | 0 % |
| erster echter Preis (Ø 21,2 h vor Anpfiff) | 0,20428 | 0,45197 | 18,29 % |
| letzter echter Preis (Ø 2,70 h vor Anpfiff) | 0,20315 | 0,45072 | 18,74 % |

```
Differenz = −0,00113   SE (Cluster) 0,00026   t = −4,39
```

**Signifikant, aber klein: das Wettfenster steuert 2,5 % der gesamten
Prognoseleistung des Preises gegenüber dem Münzwurf bei. 97,5 % stehen schon
bei der ersten Beobachtung fest.** Der Referee hat in der Sache recht.

Die Stundenbins (`rmse_by_hour_bin.csv`) sind dafür **nicht** verwendbar: die
Population wechselt zwischen ihnen (der Bin > 48 h hat den *besten* Brier,
weil dort nur 11.927 früh eröffnende Serien stehen). Nur der gepaarte
Vergleich ist kompositionsfrei.

### Auch der RMSE-Rückgang ist zu einem grossen Teil Imputation

Damit die Aussage belastbar ist, wird **dieselbe** Grösse — Brier des rohen
Preises, erste gegen letzte Spalte — auch auf dem Produktionsraster gerechnet:

| | Brier früh | Brier spät | Differenz | t |
|---|---:|---:|---:|---:|
| echte Beobachtungen | 0,20428 | 0,20315 | **−0,00113** | −4,39 |
| imputiertes Perzentilraster | 0,20791 | 0,20330 | **−0,00462** | −11,59 |

**Faktor 4,08.** Die späten Werte stimmen praktisch überein (0,20330 gegen
0,20315); die gesamte Differenz sitzt am **frühen** Rand (0,20791 gegen
0,20428). Das ist derselbe Mechanismus wie in `../README.md`, Nachtrag 2: die
Imputation lässt den Frühpreis schlechter aussehen, als er ist, und
vergrössert dadurch sowohl den β₁-Abfall als auch den RMSE-Rückgang.

### Einschränkung

Der Formtest (β₁ nicht konstant) läuft auf der **vollen** kontinuierlichen
Stichprobe, also Zelle C des 2×2. Auf den vollständig beobachteten Serien
(Zelle D) ist der Pfad flacher und höher: 1,299 → 1,087 statt 1,289 → 0,771.
Die **Richtung** des Abfalls ist also robust, die **Amplitude** nicht — ein
Teil davon ist Komposition (spät eröffnende Serien). Bootstrap-Replikate für
Zelle D existieren nicht, ein Formtest dort ist nicht gerechnet.

## Dateien (Nachtrag)

- `_simultaneous.py` — sup-t-Band, globale Tests, Trim-Sensitivität,
  Gegenrechnung auf der publizierten Kurve
- `_rmse_magnitude.py` — RMSE-Einordnung, gepaarter Vergleich, echt gegen
  imputiert
- `simultaneous_band.csv` — 96 Gitterpunkte mit punktweisem und simultanem Band
- `simultaneous_marks.csv` — dasselbe an den sechs Stundenmarken
- `global_tests.csv` — die beiden sup-Tests und der Randkontrast
- `simultaneous_trim_sensitivity.csv` — beide Tests bei Trim 48/36/24 h
- `pointwise_vs_corrected.csv` — publizierte Kurve unter Šidák und SE × 3
- `rmse_magnitude_curve.csv` — Figur-3-Kurve als Brier und Skill Score
- `rmse_by_hour_bin.csv` — Brier je Stundenbin (kompositionsbehaftet)
- `rmse_paired_first_last.csv` — gepaarter Vergleich, cluster-robust
- `rmse_real_vs_imputed.csv` — dieselbe Grösse echt gegen imputiert
