# Eq. 3 auf Kontraktebene (R2-C1, berührt R3-5)

Rein diagnostisch, **kein Eingriff in die Produktions-Pipeline**.

## Frage

Referee 2 (R2-C1): die publizierte Fassung (Tabelle 6) regressiert Gewinnraten
je Preisänderungs-Bin auf die mittlere Preisänderung des Bins. Gefordert ist
eine Spezifikation **auf Kontraktebene**, die für den **Opening-Preis**
kontrolliert — bei effizientem Opening sollte die Preisbewegung dann keine
eigenständige Information mehr tragen.

## Spezifikation

```
Match_ij = eta_0 + eta_1 * OpnOdds_ij + eta_2 * DltOpnCls_ij
           + TsDur + Compet_* + (1 + DltOpnCls | Bookies)
```

- `Match` binär 0/1 · `OpnOdds` normalisierte implizite Wahrscheinlichkeit
  beim Opening · `DltOpnCls = ClsOdds − OpnOdds`
- `lme4`, `REML = FALSE`, konsistent zur R1-ii-Arbeit

**LPM bewusst gewählt:** die theoretischen Vorhersagen des Papers stehen in
Wahrscheinlichkeitseinheiten (`eta_0 = 0,5`, `eta_1 > 0`), und bei effizienten
Opening-Preisen ist `eta_1 = 1` ein direkt testbarer Punktwert. Heteroskedasti-
zität und mögliche Vorhersagen außerhalb [0,1] sind vorhanden, betreffen aber
die Koeffizientenschätzung nicht; der Logit-Check unten sichert ab, dass der
Befund nicht an der Linearitätsannahme hängt.

**Datenbasis:** `df_oc` wie in `bookmaker_accuracy.py:81–88` — eine Zeile je
`GroupId`, normalisierte Preise, echte Opening/Closing-Werte, **keine
Imputation im Spiel**. 172.663 Kontrakte, 20.588 Matchups, 24 Bookmaker.

## Stufenreihe

| Stufe | eta_0 | eta_1 (OpnOdds) | eta_2 (DltOpnCls) | R² |
|---|---:|---:|---:|---:|
| S1 nur Preisänderung | 0,51000 (0,0012) | — | 0,83250 (0,0231) | 0,0075 |
| S2 + OpnOdds (Referee-Spez.) | −0,06246 (0,0032) | 1,12517 (0,0058) | 0,95697 (0,0209) | 0,1849 |
| S3 + Kovariaten | −0,05002 (0,0040) | 1,12480 (0,0058) | 0,95643 (0,0209) | 0,1851 |
| S4 + Bookmaker-RE | −0,05002 | 1,12480 | 0,95643 | 0,1851 |

SEs in Klammern modellbasiert. Quelle: `ladder.csv`, `s4_varcomp.csv`.

## Die drei zentralen Antworten

### 1) eta_2 überlebt die Kontrolle für den Opening-Preis

Der Koeffizient wird **größer statt kleiner**: 0,8325 → 0,9564.

| | Schätzer | SE | t | p |
|---|---:|---:|---:|---:|
| modellbasiert | 0,95643 | 0,02093 | 45,69 | < 1e−300 |
| **cluster-robust** | 0,95643 | 0,06893 | **13,87** | < 1e−43 |

**Die Erwartung des Referees trifft nicht zu.** Die Preisbewegung trägt
eigenständige Information, die im Opening-Preis nicht enthalten ist; die
Bin-Ergebnisse waren kein bloßer Niveaueffekt.

### 2) eta_1 liegt signifikant ÜBER 1

| Test | modellbasiert | cluster-robust |
|---|---:|---:|
| gegen 0 | t = 193,72 | t = 65,55 |
| **gegen 1** | t = 21,49 | **t = 7,27, p = 3,5e−13** |

Auch robust wird `eta_1 = 1` klar verworfen. Inhaltlich sind die
Opening-Preise **unterdispers**: bei `OpnOdds = 0,2` sagt das Modell 0,175
vorher, bei 0,8 dagegen 0,85. Longshots gewinnen seltener als impliziert,
Favoriten häufiger — der **Favorite-Longshot-Bias direkt auf Kontraktebene**
(verwertbar für R1-viii).

### 3) Der Logit-Check bestätigt beides

`Match ~ logit(OpnOdds) + DltOpnCls + (1 + DltOpnCls | Bookies)`, `glmer`,
binomial. `OpnOdds` liegt durchgehend in (0,1): 0,0304 – 0,9720.

| Term | Koeffizient | SE | Effizienzwert | Test |
|---|---:|---:|---:|---|
| (Intercept) | 0,00115 | 0,00534 | 0 | t = 0,21, **p = 0,83** ✔ |
| logit(OpnOdds) | 1,18431 | 0,00741 | 1 | t = 24,88, p ≈ 0 ✘ |
| DltOpnCls | 4,42109 | 0,10118 | 0 | t = 43,69 ✘ |

Qualitativ identisch zum LPM: Kalibrierungssteigung über 1, Preisänderung mit
eigenständiger Information. Der Intercept trifft den Effizienzwert sauber —
**die Verzerrung sitzt in der Steigung, nicht im Niveau.** Quelle:
`logit_check.csv`.

## Inferenz: cluster-robust, kein Match-RE

### Ein Match-Random-Intercept ist hier NICHT identifiziert

| | Wert |
|---|---:|
| var(`Match`) gesamt | 0,249896 |
| var between Matchup | 0,249896 |
| **Anteil between** | **100,00 %** |
| Matchups mit mehr als einem `Match`-Wert | **0 von 20.588** |

`Match` ist der Spielausgang und damit **per Konstruktion konstant** über die
Bookmaker eines Matchups. Das ist strenger als bei der
Unbiasedness-Regression (dort 99,83 %): der Match-RE würde die abhängige
Variable nicht nur weitgehend, sondern **exakt** absorbieren.

Die crossed-Variante zur Illustration (`crossed_varcomp.csv`) bestätigt das:

```
Matchup  (Intercept)   vcov 0.029923   sd 0.172984
Bookies  (Intercept)   vcov 0.014446   sd 0.120191
Bookies  DltOpnCls     vcov 0.046390   sd 0.215384
Residual               vcov 0.000000   sd 0.000001   <- kollabiert
```

Die **Residualvarianz fällt auf sd = 1e−6**. Bemerkenswert: die
Bookmaker-Varianzen, die in S4 exakt null sind, werden hier plötzlich
substanziell — das typische Bild eines entarteten Fits, bei dem die Varianz
nach dem Nullsetzen des Residuums beliebig verteilt wird.

> **`lme4` meldet dafür keine Warnung.** `isSingular` prüft die
> RE-Kovarianzmatrix, nicht die Residualvarianz — die Entartung sitzt hier
> aber genau dort. Dieselbe Lehre wie bei den Verspätungs-Kontrollmodellen,
> wo die edf/F-Tabelle sauber aussah, während das Modell rangdefizient war:
> die Konvergenzmeldung ist kein Gütesiegel.

### CR1-Sandwich auf Matchup-Ebene

`max |beta(OLS) − beta(lmer)| = 0,000000` — der Sandwich ist übertragbar.
G = 20.588, N = 172.663, K = 8. Quelle: `cluster_robust.csv`.

| Term | beta | SE Modell | SE Cluster | Faktor |
|---|---:|---:|---:|---:|
| (Intercept) | −0,05002 | 0,00401 | 0,01419 | 3,54 |
| OpnOdds | 1,12480 | 0,00581 | 0,01716 | 2,96 |
| DltOpnCls | 0,95643 | 0,02093 | 0,06893 | 3,29 |
| TsDur | 0,00102 | 0,00129 | 0,00449 | 3,47 |
| Compet_* | | | | 3,73 – 4,11 |

Faktor 2,96 – 4,11 — dieselbe Größenordnung wie bei der
Unbiasedness-Regression (3,0). Beide Kernbefunde überleben.

## Sensitivität gegenüber dem Filter `|RtrnOpnCls| > 0`

Die Produktionsfassung von `df_oc` entfernt Kontrakte ohne
Open-to-Close-Bewegung. Da die Frage lautet „trägt die Preisbewegung
Information", wäre eine Selektion auf bewegte Preise angreifbar. Quelle:
`filter_sensitivity.csv`.

| Stichprobe | n | ohne Bewegung | eta_1 | eta_2 | R² |
|---|---:|---:|---:|---:|---:|
| gefiltert (Produktion) | 172.663 | 0 | 1,12480 | 0,95643 | 0,18511 |
| **ungefiltert** | **184.415** | 11.752 (6,4 %) | 1,12266 | 0,95617 | 0,18631 |
| Δ | | | −0,00215 | **−0,00026** | |

**Der Filter ist unkritisch.** eta_2 verschiebt sich um 0,00026, also um 0,4 %
eines Standardfehlers; die cluster-robusten t-Werte sind praktisch identisch
(eta_2: 13,87 in beiden; eta_1 gegen 1: 7,27 vs. 7,23). Die Kontrakte mit
`DltOpnCls = 0` liegen auf der Regressionsgeraden und ziehen die Steigung
nicht. **Für den Text heißt das: der Befund kann auf der vollen Stichprobe
berichtet werden**, was den Einwand von vornherein erledigt.

## Keine Bookmaker-Heterogenität — RE und FE stimmen überein

In S4 sind die Bookmaker-REs **exakt null** (Varianzen 0,000000, sdcor
0,000014, `boundary (singular) fit`); S4 ist bis auf fünf Nachkommastellen
identisch zu S3, R² marginal = konditional. Um auszuschließen, dass der
RE-Ansatz Heterogenität nur nicht *sieht*, zusätzlich eine
Fixed-Effects-Variante mit vollen Dummies und Interaktionen. Quelle:
`bookie_fe_slopes.csv`.

```
R²:  S3 (ohne Bookmaker) 0.185114   FE + Interaktion 0.185216   Zuwachs 0.000103

Wald (cluster-robust), Dummies (Niveau)        chi2(23) = 31.48   p = 0.111
Wald (cluster-robust), Interaktionen (Steigung) chi2(23) = 20.78   p = 0.595
Wald (cluster-robust), beide gemeinsam          chi2(46) = 52.91   p = 0.225
```

Die bookmakerspezifischen Steigungen streuen nominell von **0,771**
(BetInAsia) bis **1,083** (Dafabet), sd 0,085 — aber **kein einziger der 23
Kontraste ist von der Referenz zu unterscheiden** (SEs 0,08–0,20).

**Das ist ein eigenständiger Befund, kein Nullresultat aus Schwäche:** RE und
FE kommen unabhängig zum selben Schluss, die FE-Variante mit voller
Flexibilität. Bemerkenswert ist der **Kontrast zu den Lernraten**, wo die
Bookmaker-Heterogenität substanziell und robust ist (γ von 0,0014 bei GGBET
bis 0,0124 bei Dafabet, Faktor 9, mit stabiler Rangfolge). **Bookmaker
unterscheiden sich darin, wie schnell sie lernen, aber nicht darin, wie gut
ihre Preisbewegungen den Ausgang vorhersagen.** Relevant für R2-M8 und R1-iv.

*Einschränkung:* Dafabet hat mit SE 0,2031 den größten Standardfehler und
zugleich die höchste Steigung — bei dünn besetzten Bookmakern ist die Power
gering. Die Aussage gilt belastbar für das Kollektiv (Wald über alle 23), für
einzelne kleine Bookmaker nur schwach.

## Verhältnis zu Tabelle 6

Tabelle 6 (normalisiert, `C_normalized/tables/res_wp_re.tex`): Intercept
0,504, **AvgChange 0,821** (SE 0,031). Kontraktebene S3/S4: Intercept −0,050,
**eta_2 0,956**.

**Die Größen sind nicht gleichzusetzen**, aus drei Gründen:

1. **Andere Beobachtungseinheit.** Tabelle 6 läuft auf (Bookmaker ×
   Preisänderungs-Bin)-Zellen (`winning_proportions.py:126`) — abhängige
   Variable ist eine Gewinnrate über ein Bin, Regressor dessen Mittelwert.
   `eta_2` ist die Individualsteigung über Kontrakte.
2. **Andere Kontrollmenge.** Tabelle 6 kontrolliert für `NumMatches`, **nicht
   für den Opening-Preis**. Ihr AvgChange-Koeffizient entspricht strukturell
   daher eher **S1** (0,8325) als S2–S4 — und dort stimmen beide auffallend
   gut überein (0,821 vs. 0,833).
3. **Aggregationseffekt.** Die Bins sind nach dem Regressor selbst gebildet;
   das mittelt Rauschen in der abhängigen Variablen weg und verändert die
   Steigung im Allgemeinen.

**Saubere Lesart: Tabelle 6 ≈ S1, und der Referee-Einwand betrifft genau den
Schritt S1 → S2.** Dieser Schritt hebt den Koeffizienten von 0,83 auf 0,96 —
er entkräftet den Befund nicht, sondern verstärkt ihn.

## R2-C6: Signifikanz der bookmakerspezifischen Slopes

Referee 2 (R2-C6) fragt nach der Signifikanz der bookmakerspezifischen
Steigungen. Die bisherige Abbildung (`fig:win_props_re`) zeigt **24
Einzelgeraden**, die visuell erhebliche Heterogenität nahelegen — der Text
(`tex:782`) liest daraus „steeper slopes indicating greater explanatory
power".

### Welcher Test

**Ein gemeinsamer Wald-Test über alle 23 Interaktionskontraste**
(`DltOpnCls × Bookmaker`, Referenzkategorie 10Bet), cluster-robust auf
Matchup-Ebene, aus der **Fixed-Effects**-Variante — **nicht** 24 Einzeltests.

Begründung: 24 Einzeltests auf 5 % würden allein durch Zufall gut einen
Treffer erzeugen; die Frage „unterscheiden sich die Bookmaker?" ist eine
**gemeinsame** Hypothese und gehört gemeinsam getestet. Die FE-Variante wurde
gewählt, weil die Random Effects in S4 **singulär** sind (Varianzen exakt
null) und dort per Konstruktion keine Heterogenität zeigen könnten — FE prüft
dieselbe Frage mit voller Flexibilität und ohne Verteilungsannahme.

### Ergebnis

```
chi2(23) = 20.78   p = 0.595      Interaktionen (Steigung)
chi2(23) = 31.48   p = 0.111      Dummies (Niveau)
chi2(46) = 52.91   p = 0.225      beide gemeinsam
```

Steigungen 0,771 (BetInAsia) – 1,083 (Dafabet), sd 0,085, gepoolt 0,956.
**Jedes einzelne 95-%-Intervall überschneidet die gepoolte Steigung**, kein
Kontrast ist einzeln signifikant, und der R²-Zuwachs für 46 zusätzliche
Parameter beträgt 0,0001.

### Konsequenz für die Abbildung

`eq3_two_panel.{png,pdf}` (Skript `_eq3_plot.py`) ersetzt
`fig:win_props_re`:

- **Links, rein deskriptiv:** die 288 Bin-Punkte (24 Bookmaker × 12
  Intervalle), farbcodiert wie bisher, mit Referenzlinien bei y = 0,5 und
  x = 0. **Keine Regressionsgerade.**
- **Rechts, die Inferenz:** die 24 Steigungen als Caterpillar mit
  95-%-Intervallen, sortiert, gestrichelte Linie bei der gepoolten Steigung,
  Wald-Test als Annotation.

**Warum links keine Gerade mehr steht:** Da Eq. 3 wegen **R2-C1** auf die
Kontraktebene umgestellt wird, ist die Bin-Regression **nicht mehr die
Spezifikation**. Eine gepoolte Bin-Gerade hätte die Steigung 0,766 (nach
Fallzahl gewichtet), die Kontraktebene liefert 0,956. **Zwei verschiedene
Steigungen in einer Abbildung wären irreführend** — der Leser müsste raten,
welche die geschätzte ist. Links steht deshalb nur noch die Beschreibung,
rechts die Schätzung; die Abbildung zeigt genau **eine** Steigung, und zwar
die tatsächlich geschätzte.

> **Die separate Legendenseite entfällt.** Die bisherige Abbildung brauchte
> eine eigene Legendendatei (`legend_winprops_*`), um 24 Farben zu benennen.
> In der neuen Fassung stehen die Namen rechts direkt an den Punkten; die
> Farbcodierung links ist damit redundant beschriftet und die Legendenseite
> überflüssig.

### Zu ändern im Papertext

**`tex:782` muss zurückgenommen werden.** Die Formulierung „steeper slopes
indicating greater explanatory power" behauptet eine Heterogenität, die einem
gemeinsamen Test nicht standhält (p = 0,595). Die nominellen Unterschiede
zwischen den Einzelgeraden sind Schätzrauschen, kein systematischer
Bookmaker-Effekt. Siehe auch R2-M8 (Fokus auf Aggregatergebnisse) und R1-iv
(eine Sharp/Soft-Klassifikation ließe sich hieraus nicht begründen —
Pinnacle 0,814 und Betfair 0,806 liegen am unteren Rand, aber innerhalb des
Rauschens).

## Dateien

- `_eq3_contract.py` — Stufenreihe, Match-ANOVA, Cluster-Sandwich,
  crossed-Illustration, Logit-Check
- `_eq3_sensitivity.py` — Filter-Sensitivität und Bookmaker-FE-Test
- `ladder.csv` — S1–S4 mit Koeffizienten, SEs, R²
- `match_anova.csv` — Varianzzerlegung von `Match` auf Matchup-Ebene
- `s4_varcomp.csv`, `crossed_varcomp.csv` — Varianzkomponenten
- `cluster_robust.csv` — CR1-Sandwich gegen modellbasiert
- `logit_check.csv` — glmer-Kalibrierungsregression
- `filter_sensitivity.csv` — gefiltert vs. ungefiltert
- `bookie_fe_slopes.csv` — bookmakerspezifische Steigungen (FE) mit
  `se_slope_cl` und 95-%-Grenzen. **Achtung:** `se_interaktion_cl` ist die SE
  des *Kontrasts* zur Referenz, `se_slope_cl` die der *Steigung selbst*
  (`Var(eta_2) + Var(int_b) + 2·Cov`) — für den Caterpillar wird letztere
  gebraucht.
- `_eq3_plot.py` — Zwei-Panel-Abbildung; rechnet die FE-Steigungen mit
  korrekten SEs neu und schreibt `bookie_fe_slopes.csv` dabei fort
- `eq3_two_panel.{png,pdf}` — Ersatz für `fig:win_props_re`
  (**gitignoriert**, aus `_eq3_plot.py` regenerierbar)
