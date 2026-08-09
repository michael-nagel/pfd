# Cluster-Effekt für die DISKRETE Unbiasedness-Spezifikation (R1-ii)

Rein diagnostisch, **kein Eingriff in die Produktions-Pipeline**.
Datenbasis `revision-baseline` (`C_normalized/wide_imputed.h5`),
174.392 Serien, 20.725 Matchups, 24 Bookmaker.

## Frage

Die bisher berichteten Cluster-Zahlen für die Unbiasedness-Regression
(Faktor 3,0–3,6) stammen aus der **kontinuierlichen** Spezifikation
(`../continuous_unbiasedness/main_spec/`). Die wechselt gegenüber der
Produktion gleichzeitig drei Dinge: Zeitachse (log-Stunden statt
Perzentile), Datenbasis (echte Beobachtungen statt imputiertes
Perzentilraster) und Schätzer (ein GAM statt 50 Mixed-LM-Fits). Der Faktor
dort **vermengt Clusterung und Achsenwechsel**.

Hier wird die Clusterung isoliert: dieselbe Produktionsspezifikation,
dieselben Daten, derselbe Punktschätzer — nur die Kovarianzmatrix wechselt
von modellbasiert auf CR1-Sandwich, geclustert auf Matchup. Vorgehen wie in
`../cluster_inference_eq12/`.

## 1) Gate: reproduziert OLS den Mixed-LM-Punktschätzer?

`max |β₁(OLS) − β₁(MixedLM)| = 0,290`, Median 0,007. Bei Schwelle 0,01 hält
das Gate an **42 von 50** Perzentilen.

**Alle 8 Verletzungen liegen am frühen Rand** (Perzentile 2, 4, 6, 8, 10,
12, 14, 18), die größte bei Perzentil 2 (2,591 gegen 2,301). Das ist
derselbe Bereich, in dem die Imputation konzentriert ist und in dem der
Bookmaker-Random-Slope tatsächlich arbeitet. Ab Perzentil 20 hält das Gate
durchgehend.

Konsequenz: Der Faktor ist dort belastbar, wo das Gate hält — und dort ist
er **gegen die Einschränkung unempfindlich**:

| | Median | Spanne |
|---|---:|---|
| alle 50 Perzentile | 2,12 | 1,14–3,10 |
| nur wo Gate hält (42) | **2,13** | 1,76–3,10 |
| ab Perzentil 20 (41) | **2,13** | 1,76–3,10 |

## 2) CR1-Sandwich auf Matchup

| Faktor | Median | Spanne |
|---|---:|---|
| Cluster / modellbasiert | **2,13** | 1,76–3,10 |
| Cluster / iid | 2,64 | 1,61–2,76 |

Perzentile mit β₁ signifikant ≠ 1: **49 von 50** modellbasiert gegen
**34 von 50** cluster-robust (26 von 42 dort, wo das Gate hält).

Ausgewählte Perzentile:

| Perzentil | β₁ (MixedLM) | SE Modell | SE Cluster | Faktor | t Modell | t Cluster |
|---:|---:|---:|---:|---:|---:|---:|
| 50 | 1,127 | 0,0248 | 0,0528 | 2,13 | 5,14 | 2,55 |
| 100 | 1,031 | 0,0181 | 0,0452 | 2,49 | 1,73 | 0,72 |

## Einordnung gegen die kontinuierliche Fassung

| Fassung | Faktor |
|---|---|
| **diskret, isoliert (hier)** | **2,1** |
| kontinuierlich (`main_spec`, Sandwich) | 3,0 |
| kontinuierlich (`main_spec`, Bootstrap) | 3,3–3,6 |

Die Differenz ist **nicht** Clusterung, sondern der Wechsel von Achse,
Datenbasis und Schätzer. Für eine Aussage über den reinen Preis der
Match-Abhängigkeit in der publizierten Spezifikation ist **2,1** die
richtige Zahl.

## Dateien

- `_discrete_cluster.py` — Gate und CR1-Sandwich je Perzentil
- `discrete_cluster_beta1.csv` — 50 Perzentile: β₁ (MixedLM und OLS),
  Gate-Differenz, SE modellbasiert/iid/Cluster, Faktoren, t-Werte
