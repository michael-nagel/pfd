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
- `_main_spec_plot.py` — Abbildung
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
- `main_spec.{png,pdf}` — β₁ über Stunden vor Anpfiff mit Cluster-Band,
  daneben die Perzentil-Baseline auf identischer y-Achse
  (**gitignoriert**, aus `_main_spec_plot.py` regenerierbar)
