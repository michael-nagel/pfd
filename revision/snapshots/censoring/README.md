# Zensierung und der `NumOddsMvt < 20`-Filter (R1-v, vom AE priorisiert)

Rein diagnostisch, **kein Eingriff in die Produktions-Pipeline**.
Datenbasis `revision-baseline` (normalisierte Preise, Match-Fix).

## Frage

Referee 1 (Kommentar 5), vom Associate Editor ausdrücklich priorisiert:
Oddsportal liefert nur den Opening-Preis plus die letzten 20 Updates. Der
Preispfad ist damit zensiert, und der Filter auf Serien mit weniger als 20
Preisänderungen entfernt womöglich genau die aktivsten Märkte. Gefordert sind
drei Dinge: **Zahl der verlorenen Beobachtungen**, **Vergleich included gegen
excluded**, **Robustheit der Schlussfolgerungen**.

## Präzisierung vorab: wo der Filter überhaupt sitzt

Der Filter steht in `unbiasedness_regressions.py:55` und
`time_series_diagnostics.py:73` — **nicht** in `filter_and_shape` und
**nicht** in `resample_and_impute`.

**Betroffen:** die Unbiasedness-Regressionen (Figure 3) und die
GARCH-Diagnostik.
**Nicht betroffen:** RMSE (Figure 1), Tabellen 3–7, GMM und Bayesian.

Der Einwand ist damit enger als im Kommentar unterstellt. Er trifft aber
genau die Lernkurve, um die es dem Referee geht.

## 1) Zahl der verlorenen Beobachtungen

Quelle: `sample_stages.csv`.

| Stufe | Serien | verbleibend |
|---|---:|---:|
| shaped_data (roh) | 587.414 | |
| nach `filter_and_shape` (Marge, Bookmaker, TsDur) | 184.415 | 31,4 % |
| nach Nullvarianz-Filter | 184.112 | 99,8 % |
| **nach `NumOddsMvt < 20`** | **175.266** | **95,2 %** |

**Der Filter entfernt 8.846 von 184.112 Serien, also 4,80 %.**

Vollständig verlorene Matchups: **94 von 20.854** (0,45 %); 99,55 % der
Matchups behalten mindestens einen Bookmaker.

## 2) Die Ausgeschlossenen sind genau die Zensierten

Quelle: `num_updates_distribution.csv`.

```
Median 7   Mittel 7,98   Maximum 20
genau 20: 8.846   über 20: 0
```

**`NumOddsMvt` ist bei exakt 20 gekappt** — keine einzige Serie liegt
darüber. Das ist die Signatur der Datenquelle: wer 20 Updates zeigt, hat in
Wahrheit mindestens 20, und die Pfadmitte fehlt.

> **Damit ist der Filter kein willkürlicher Ausschluss, sondern genau der
> Ausschluss der zensierten Serien.** Das ist eine verteidigbare
> Konstruktion — man behält die Serien, deren Pfad man plausibel vollständig
> sieht — aber es selektiert auf Marktaktivität, und genau das ist der
> Einwand des Referees.

## 3) Included gegen excluded

Quelle: `included_vs_excluded.csv`. `Std. diff.` ist die Mittelwertdifferenz
in Standardabweichungen der jeweiligen Größe.

| | included | excluded | Std. diff. |
|---|---:|---:|---:|
| Preisänderungen | 7,37 | 20,00 | 2,36 |
| Fensterlänge (h) | 24,71 | 29,88 | 0,37 |
| Posting-Zeitpunkt (h vor Anpfiff) | 27,39 | 31,36 | 0,26 |
| \|Opening − Closing\| | 0,0351 | 0,0529 | 0,51 |
| Anteil ATP/WTA | 0,314 | 0,411 | 0,21 |
| Opening-Wahrscheinlichkeit | 0,5092 | 0,5091 | −0,00 |
| Marge beim Opening | 0,0728 | 0,0731 | 0,02 |
| Gewinnrate | 0,5103 | 0,5148 | 0,01 |
| Anteil Favoriten | 0,518 | 0,511 | −0,01 |
| **n** | **175.266** | **8.846** | |

**Der Referee hat der Art nach recht, dem Ausmaß nach nicht.** Die
ausgeschlossenen Serien sind aktiver (größere Bewegung, längeres Fenster,
häufiger ATP/WTA), aber sie unterscheiden sich **nicht** in den Größen, die
eine Lernschätzung verzerren würden: Preisniveau, Marge, Favoritenanteil und
Gewinnrate stimmen auf ein Hundertstel einer Standardabweichung überein.

Ausschlussquote je Bookmaker (`exclusion_by_bookies.csv`): 9,96 %
(Marathonbet) bis 0,05 % (888sport). Auffällig niedrig bei den früh
eröffnenden und sharpen Häusern — Pinnacle 0,89 %, BetInAsia 0,39 %,
Betfair 0,17 %. Je Wettbewerb (`exclusion_by_competition.csv`): ATP 6,93 %,
WTA 5,30 %, Challenger 4,21 %, ITF 4,09 %.

## 4) Robustheit: β₁ mit und ohne den Filter

Quelle: `beta1_filter_marks.csv`, Skript `_censoring_beta1.py`.

Hauptspezifikation M_c der kontinuierlichen Unbiasedness-Regression, zweimal
geschätzt — einmal mit dem Produktionsfilter, einmal auf allen Serien, wobei
für die zensierten Serien schlicht die vorhandenen Beobachtungen verwendet
werden. Alles andere identisch.

```
produktion    1.291.205 Zeilen, 175.166 Serien
vollständig   1.468.036 Zeilen, 184.012 Serien   (+8.846 Serien)
```

| Stunden vor Anpfiff | mit Filter | volle Stichprobe | Differenz | in SE |
|---:|---:|---:|---:|---:|
| 24 | 1,2413 | 1,2513 | +0,0101 | +0,21 |
| 12 | 1,1853 | 1,1516 | −0,0337 | −0,70 |
| 6 | 1,0285 | 0,9728 | −0,0557 | −1,15 |
| 3 | 0,9302 | 0,9020 | −0,0281 | −0,58 |
| 1 | 0,8736 | 0,9037 | +0,0301 | +0,60 |
| 0,25 | 0,8664 | 0,9094 | +0,0431 | +0,84 |

**Größte Abweichung 0,056, das sind 1,15 modellbasierte Standardfehler.**
Gemessen an den cluster-robusten SEs aus R1-ii (Faktor ≈ 3) ist es unter
einem halben Standardfehler. Der Verlauf — Unterreaktion früh, Unverzerrtheit
in der Mitte, Überreaktion nahe Anpfiff — ist in beiden Fassungen derselbe.

*Gegenprobe:* β₁(24 h) = 1,2413 hier gegen 1,2444 in
`continuous_unbiasedness/main_spec/cluster_robust_marks.csv` (lme4-Route
statt bam-RE). Die Spezifikation reproduziert.

## Konsequenz für das Paper

1. **Der Filter muss in die Datensektion.** Er war in der publizierten
   Fassung nicht dokumentiert — das ist der eigentliche Mangel, den der
   Kommentar aufdeckt.
2. Tabellen aus 1) und 3) in den Appendix.
3. Der Robustheitscheck aus 4) in den Ergebnisteil.

Inhaltlich ändert sich nichts.

## Dateien

- `_censoring.py` — Stufenzählung, Verteilung der Updatezahl, included vs.
  excluded, Ausschlussquoten je Bookmaker und Wettbewerb
- `_censoring_beta1.py` — M_c mit und ohne Filter
- `sample_stages.csv`, `num_updates_distribution.csv`,
  `included_vs_excluded.csv`, `exclusion_by_bookies.csv`,
  `exclusion_by_competition.csv`
- `beta1_filter_marks.csv`, `beta1_filter_marks_long.csv`
- `series_frame.parquet` — Serien-Frame des ersten Skripts (Cache)

---

# Nachtrag 1 – Korrektur: die Kappung war zirkulär belegt

Abschnitt 2 schloss aus `num_updates_distribution.csv` (Maximum 20, keine
Serie darüber), die Kappung sei „die Signatur der Datenquelle". **Dieser
Schluss war nicht gedeckt.** `shape_odds.py:104` verwirft selbst alle Gruppen
mit mehr als 21 Beobachtungen:

```python
group_sizes = df.groupby(["Matchup", "Bookies"])["Matchup"].transform(len)
df = df[group_sizes <= 21]
```

Im `shaped_data.h5` **kann** per Konstruktion nichts über 20 Updates stehen.
Die Verteilung dort belegt also unseren eigenen Filter, nicht die Plattform.

## Der Nachweis am Rohbestand

Skript `_censoring_raw_cap.py`, Quelle `data/raw/crawled_odds.json` — vor
jedem eigenen Filter. Je Bookmaker-Eintrag ist die Zahl der Zeitstempel vor
`Opening odds` die Zahl der angezeigten Updates.

**1.425.576 rohe Bookmaker-Serien.**

| Updates | 16 | 17 | 18 | 19 | **20** | > 20 |
|---|---:|---:|---:|---:|---:|---:|
| Serien | 11.547 | 10.199 | 8.391 | 7.164 | **54.054** | **0** |

- **Maximum 20, keine einzige Serie darüber** — unabhängig von unserem Code.
- **Sprung um Faktor 7,5** von 19 auf 20 (7.164 → 54.054).

Die Kappung ist damit belegt eine Eigenschaft von Oddsportal. Die Aussage aus
Abschnitt 2 bleibt richtig, sie steht jetzt nur auf tragfähigem Grund.

**Nebenbefund:** weil im Rohbestand nichts über 20 Updates liegt, entfernt die
`shape_odds`-Regel `<= 21 Beobachtungen` **null Serien**; sie ist bindungslos.
Zwischen ihr und dem Modellfilter `NumOddsMvt < 20` liegt genau
`NumOddsMvt == 20`, also die 8.846 zensierten Serien. Die einzige wirksame
Restriktion ist unsere.

Datei: `raw_updates_distribution.csv`.

---

# Nachtrag 2 – Alternative Filterschwellen

Abschnitt 4 vergleicht nur zwei Fälle (Produktionsfilter gegen alle Serien).
Skript `_censoring_thresholds.py` schätzt dieselbe Spezifikation M_c über
eine Reihe von Schwellen; der Frame wird einmal gebaut und danach nur
geteilt, die Schwellen unterscheiden sich also ausschliesslich in der
Zeilenmenge.

| Stunden vor Anpfiff | < 10 | < 15 | < 18 | **< 20** (Produktion) | < 21 (alle) |
|---:|---:|---:|---:|---:|---:|
| 24 | 0,9952 | 1,1338 | 1,2055 | **1,2413** | 1,2513 |
| 12 | 1,0783 | 1,0881 | 1,1642 | **1,1853** | 1,1516 |
| 6 | 0,8684 | 0,9099 | 0,9782 | **1,0285** | 0,9728 |
| 3 | 0,7800 | 0,7966 | 0,8598 | **0,9302** | 0,9020 |
| 1 | 0,7972 | 0,7309 | 0,7938 | **0,8736** | 0,9037 |
| 0,25 | 0,7927 | 0,7163 | 0,7884 | **0,8664** | 0,9094 |
| **Serien** | 123.795 | 157.065 | 168.489 | **175.166** | 184.012 |

Grösste absolute Abweichung von der Produktionsschwelle: **0,2461**, bei
`< 10` am fernen Rand.

## Lesart – differenziert, nicht pauschal

- **Die Form hält an jeder Schwelle.** β₁ fällt überall vom fernen Rand zum
  Anpfiff hin und liegt anpfiffnah unter 1: von 0,995 → 0,793 bei `< 10` bis
  1,251 → 0,909 bei allen Serien. Unterreaktion früh, Überreaktion spät ist
  gegen die Schwelle unempfindlich.
- **Das Niveau nicht.** Engere Schwellen senken β₁ systematisch, am stärksten
  früh im Fenster (24 h: 1,241 → 0,995 bei `< 10`).
- **Grössenordnung:** Bei `< 18` und bei allen Serien bleibt die Abweichung
  unter 0,080, gemessen an den cluster-robusten SEs (Faktor ≈ 2,1 auf
  modellbasierte ~0,048, also ~0,10) **unter einem Standardfehler**. Bei
  `< 10` sind 0,246 dagegen rund **2,4 Standardfehler** — diese Schwelle
  verwirft aber auch 30 % der Serien.

**Für die Antwort verwertbar:** robust gegen Schwellen in der Nähe der
gewählten, nicht robust gegen eine drastische Verschärfung. Das gehört so
gesagt.

Dateien: `beta1_thresholds.csv`, `beta1_thresholds_long.csv`.
