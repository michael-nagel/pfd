# Cluster-robuste Inferenz für Eq. 1 und Eq. 2 (R1-ii)

Rein diagnostisch, **kein Eingriff in die Produktions-Pipeline**.
Datenbasis `revision-baseline` (normalisiert), `df_oc` mit 172.663 Kontrakten,
20.588 Matchups, 24 Bookmaker.

## Frage

Die Unbiasedness-Regression und Eq. 3 sind bereits auf cluster-robuste
Inferenz auf Matchup-Ebene umgestellt. Dieses Skript zieht die beiden
verbleibenden Modelle nach:

| | Modell | Kernkoeffizient |
|---|---|---|
| **Eq. 1** | `RtrnClsEnd ~ RtrnOpnCls + TsDur + Compet_*` (`fit_gpm_mod.py`) | `RtrnOpnCls` |
| **Eq. 2** | `Endog ~ Exog + TsDur + Compet_*`, „All"-Zweig (`fit_rfa_mod.py`) | `Exog`, plus Intercept = AGS-Statistik |

## 1) Gate: ist der OLS-Sandwich übertragbar?

Quelle: `gate.csv`. Schwelle 0,01 auf den Kernkoeffizienten.

| | β(OLS) | β(lme4) | \|Differenz\| | max über alle FE | Gate |
|---|---:|---:|---:|---:|:--|
| Eq. 1 | +0,027570 | +0,027570 | **0,000000** | 0,000000 | hält |
| Eq. 2 | −0,003985 | −0,003861 | **0,000125** | 0,000128 | hält |

**Beide Gates halten deutlich.** Bei Eq. 1 stimmen die Schätzer bitgenau
überein — beide lme4-Fits melden `boundary (singular) fit`, die
Bookmaker-Varianzkomponenten kollabieren auf null, und das Mixed Model fällt
damit exakt auf OLS zurück. Der Sandwich ist übertragbar.

## 2) CR1-Sandwich auf Matchup-Ebene

Quelle: `cluster_robust.csv`. `Faktor` = Cluster-SE geteilt durch die
modellbasierte lme4-SE.

### Eq. 1

| Term | β | SE lme4 | SE Match | Faktor |
|---|---:|---:|---:|---:|
| (Intercept) | 0,00500 | 0,00665 | 0,02622 | 3,95 |
| **RtrnOpnCls** | **0,02757** | **0,02112** | **0,08084** | **3,83** |
| TsDur | −0,00716 | 0,00322 | 0,01080 | 3,36 |
| Compet_Challenger_Men | −0,01243 | 0,00819 | 0,03151 | 3,85 |
| Compet_ITF_Men | −0,05797 | 0,00860 | 0,03108 | 3,61 |
| Compet_Misc | 0,03005 | 0,04986 | 0,18732 | 3,76 |
| Compet_WTA | −0,04715 | 0,00964 | 0,03872 | 4,02 |

**Faktor 3,36–4,02, exakt im Bereich der Unbiasedness-Regression (3,0–3,6)
und von Eq. 3 (2,96–4,11).** Der Kernkoeffizient geht von t = +1,31 auf
t = +0,34.

> **Für den Kernbefund ändert sich nichts:** `RtrnOpnCls` war auch
> publiziert schon insignifikant (p = 0,235 roh, p = 0,202 normalisiert).
> Die Aussage „close-to-end-Renditen sind nicht aus open-to-close
> vorhersagbar" wird durch die cluster-robuste Inferenz nur **verstärkt**.
>
> **Die Kontrollen fallen dagegen um:** `Compet_ITF_Men` von z = −6,67 auf
> t = −1,87, `Compet_WTA` von −4,89 auf −1,22, `TsDur` von −2,22 auf −0,66.
> In Tabelle 3 bleibt unter cluster-robuster Inferenz praktisch nichts
> signifikant.

### Eq. 2

| Term | β | SE lme4 | SE Match | Faktor | SE 2-fach |
|---|---:|---:|---:|---:|---:|
| **(Intercept)** | **0,00264** | **0,00042** | **0,00102** | **2,43** | 0,00102 |
| **Exog** | **−0,00399** | **0,00036** | **0,00033** | **0,92** | **0,00050** |
| TsDur | 0,00060 | 0,00015 | 0,00049 | 3,31 | 0,00049 |
| Compet_Challenger_Men | 0,00163 | 0,00038 | 0,00127 | 3,37 | 0,00126 |
| Compet_ITF_Men | 0,00288 | 0,00040 | 0,00129 | 3,23 | 0,00128 |
| Compet_Misc | −0,00747 | 0,00229 | 0,00617 | 2,70 | 0,00596 |
| Compet_WTA | 0,00263 | 0,00044 | 0,00147 | 3,33 | 0,00144 |

Der Intercept ist hier die eigentliche AGS-Statistik (mittlerer
Genauigkeitsgewinn Opening → Closing): **t = +6,30 → +2,59**. Signifikant
bleibt er, aber deutlich schwächer.

> **`Exog` ist die Ausnahme: Faktor 0,92, die Cluster-SE liegt UNTER der
> modellbasierten.** Das ist kein Rechenfehler, sondern folgt aus der
> Konstruktion. `Exog` wird in `fit_rfa_mod.py:41-49` **je Bookmaker
> zentriert**; seine Variation ist damit weitgehend within-bookmaker, und
> Matchup-Clustering greift dort kaum (gegen die iid-SE ist der Faktor 2,7).
> Die modellbasierte SE ist ihrerseits groß, weil sie die Varianz des Random
> Slope über Bookmaker mitträgt.
>
> **Konsequenz: für Eq. 2 wäre ein reiner Matchup-Sandwich ein Rückschritt.**
> Er würde die Bookmaker-Unsicherheit fallen lassen, und die ist hier real
> (siehe 3). Zweifach geclustert (Matchup × Bookies, Cameron-Gelbach-Miller)
> steigt die SE auf 0,00050 und t sinkt von −11,90 auf **−8,00**.
> *Einschränkung:* nur 24 Bookmaker-Cluster, die zweite Dimension ist grob.

**Toolchain-Hinweis:** die modellbasierten SEs stammen aus lme4. Die im Paper
abgedruckten stammen aus `statsmodels` MixedLM und weichen bei diesen
singulären Fits ab (Eq. 2, Intercept: z = 3,84 dort gegen t = 6,30 bei lme4).
Die Faktoren oben sind gegen lme4 gerechnet; gegen die publizierte SE wäre
der Intercept-Faktor rund 1,5 statt 2,43.

## 3) Bookmaker-Heterogenität: Fixed Effects und Wald-Test

Mit OLS plus Sandwich entfällt der Random Slope. Die Heterogenitätsfrage
bleibt aber offen und wird deshalb wie bei Eq. 3 als **Fixed-Effects-Variante
mit Dummies und Interaktionen** geprüft, gemeinsamer Wald-Test
cluster-robust. Quelle: `bookie_wald.csv`, `*_bookie_fe_slopes.csv`.

| Test | Eq. 1 | Eq. 2 |
|---|---|---|
| Interaktionen (Steigung) | chi2(23) = 24,46, **p = 0,379** | chi2(23) = **304,15**, p < 0,0001 |
| Dummies (Niveau) | chi2(23) = 34,34, p = 0,060 | chi2(23) = **151,91**, p < 0,0001 |
| beide gemeinsam | chi2(46) = 57,08, p = 0,127 | chi2(46) = **507,72**, p < 0,0001 |
| R² ohne → mit | 0,000419 → 0,000591 | 0,006504 → 0,008405 |
| Steigungen | −0,113 bis +0,379, sd 0,115 | −0,0066 bis −0,0004, sd 0,0018 |

**Das Ergebnis fällt für die beiden Gleichungen entgegengesetzt aus.**

- **Eq. 1: keine Heterogenität**, wie bei Eq. 3. Die nominelle Streuung der
  Steigungen (−0,11 bis +0,38) ist Rauschen; das Basis-R² beträgt 0,0004,
  das Modell erklärt praktisch nichts.
- **Eq. 2: Heterogenität ist real und stark.** Das ist die direkte Stütze für
  die bookmakerspezifischen Slopes in **Tabelle 7** — anders als bei Eq. 3,
  wo derselbe Test nichts gefunden hat.

> **Wichtig für R2-M8.** Die Antwort auf „Rauschen oder systematisch?" ist
> **größenabhängig**: bei der Preisinformativität (Eq. 3) und bei Eq. 1
> Rauschen, bei der relativen Prognosegenauigkeit (Eq. 2 / Tabelle 7)
> systematisch. Die bisherige Log-Formulierung zu R2-M8 („Fokus auf
> Aggregatergebnisse") gilt damit **nicht** pauschal für Tabelle 7.

## 4) Crossed auf der normalisierten Baseline

Quelle: `varcomp.csv`, `match_anova.csv`. Dokumentiert, dass der erste Weg
geprüft wurde, bevor auf den Sandwich gewechselt wird.

| | Anteil Between-Match an der AV |
|---|---:|
| Eq. 1 (`RtrnClsEnd`) | **99,76 %** |
| Eq. 2 (`Endog`) | **82,62 %** |

### Eq. 1 — entartet

```
Matchup  (Intercept)              vcov 1.319513   sd 1.148701
Bookies  (Intercept)              vcov 0.000002   sd 0.001345
Bookies  RtrnOpnCls               vcov 1.650753   sd 1.284816
Bookies  (Intercept)~RtrnOpnCls   vcov -0.000297  cor -0.171611
Residual                          vcov 0.003243   sd 0.056950
```

Varianz der AV: 1,2632. Die Residualvarianz fällt auf 0,0032 (sd 0,057 gegen
sd 1,124 der AV), und die Bookmaker-Slope-Varianz explodiert von praktisch
null im Bookmaker-only-Fit auf **1,65**. Der Kernkoeffizient kippt von
**+0,0276 auf −0,2200**. Dasselbe Muster wie bei der crossed-Illustration zu
Eq. 3: sobald das Residuum kollabiert, wird die Varianz beliebig verteilt.
`lme4` meldet dabei **keine** Warnung.

### Eq. 2 — Wechsel des Schätzgegenstands

```
Matchup  (Intercept)       vcov 0.002698   sd 0.051939
Bookies  (Intercept)       vcov 0.000002   sd 0.001271
Bookies  Exog              vcov 0.000004   sd 0.001935
Bookies  (Intercept)~Exog  vcov -0.000001  cor -0.548637
Residual                   vcov 0.000495   sd 0.022247
```

Varianz der AV: 0,002675 — die **Matchup-Komponente allein (0,002698)
übersteigt sie**. Der Kernkoeffizient wechselt das Vorzeichen, von
**−0,00386 auf +0,01970**.

> Das ergänzt die frühere Einschätzung im `revision_log` (R1-ii), die für
> `fit_rfa_mod` bei 82,53 % Between-Varianz „kein Degenerationsmuster"
> festgehalten hatte. Deskriptiv stimmt das; der tatsächlich geschätzte
> crossed-Fit kippt den Koeffizienten dennoch. **Beide crossed-Fassungen
> beantworten eine andere Frage als das Bookmaker-Modell, sie schätzen nicht
> dieselbe Größe präziser.**

## Empfehlung

| | Inferenz | Begründung |
|---|---|---|
| Eq. 1 | **CR1 auf Matchup** | Gate hält bitgenau, crossed entartet, keine Bookmaker-Heterogenität |
| Eq. 2 | **zweifach geclustert, Matchup × Bookies** | Gate hält, crossed kippt den Koeffizienten, aber die Bookmaker-Heterogenität ist real und darf nicht wegfallen |

Damit ist die Umstellung **nicht ganz einheitlich** — Eq. 2 braucht die
zweite Clusterdimension, die anderen drei Gleichungen nicht. Der Grund ist
inhaltlich und benennbar: nur bei Eq. 2 unterscheiden sich die Bookmaker
nachweislich.

## Dateien

- `_eq12_cluster.py` — Gate, Sandwich (Matchup, Bookies, zweifach),
  Bookmaker-FE mit Wald-Test, crossed
- `gate.csv` — OLS gegen lme4 je Kernkoeffizient
- `cluster_robust.csv` — alle SE-Varianten und t-Werte je Term
- `bookie_wald.csv` — die drei Wald-Tests je Modell
- `Eq1_resp_to_info_bookie_fe_slopes.csv`,
  `Eq2_ags_test_bookie_fe_slopes.csv` — Steigung je Bookmaker mit
  cluster-robuster SE
- `match_anova.csv` — Anteil der Between-Match-Varianz je AV
- `varcomp.csv` — Varianzkomponenten, Bookmaker-only und crossed
