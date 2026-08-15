# Favorite-Longshot-Bias direkt gemessen (R1-viii)

Rein diagnostisch, **kein Eingriff in die Produktions-Pipeline**.
Datenbasis: normalisiert (`normalize = True`), `df_oc` mit **184.415
Kontrakten** in 20.920 Matchups (ungefiltert; die Produktionsfassung entfernt
zusätzlich Kontrakte ohne Preisbewegung, siehe Abschnitt 5).

## Was im Paper schon steht

| Stelle | Inhalt | Stützt sich auf |
|---|---|---|
| Zeile 172, 177 | FLB in der Literaturübersicht (Thaler/Ziemba 1988, Hegarty 2024) | fremde Studien |
| Zeile 575 (§Learning Rate) | **Definition** des Splits: Favorit = Player 1 hat den höheren Opening-Preis, bei Gleichstand entscheidet der Closing-Preis | — |
| Zeile 706 (§Results, Eq. 1) | „separating the sample into favorites and longshots is expected to yield a non-uniform allocation, as suggested by the favorite-longshot bias, providing an avenue for further exploration" | **nichts — das Paper kündigt es an und tut es nicht** |
| Zeile 858 + Fig. `post_gamma_nuts_fav_udd` | `\var{gamma_fav}` gegen `\var{gamma_udd}` | **Bayes-Block (veraltet)** |
| Zeile 878/879 + Fig. `post_gamma_nuts_ivals` | 10 Opening-Preis-Dezile | **Bayes-Block (veraltet)** |
| Zeile 914–917 (Discussion) | Interpretation der Lernratendifferenz als FLB | dieselben Bayes-Zahlen |

**Das Paper misst den Favorite-Longshot-Bias nirgends direkt.** Die einzige
eigene Evidenz ist die Lernratendifferenz zwischen Favoriten und Longshots —
genau die indirekte Kette, die der Referee bemängelt. Zeile 706 sagt sogar
selbst, dass die direkte Prüfung aussteht.

## Teil 1 — Zeigen die Preise selbst einen FLB? **Ja, beide.**

Kalibrierungsregression `Match = a + lambda * p`, CR1 auf Matchup.
Effizienz hiesse `lambda = 1`; `lambda > 1` ist Unterdispersion, also der FLB.
Quelle: `calibration_by_price.csv`.

| Spezifikation | a | lambda | SE cl. | t gegen 1 |
|---|---:|---:|---:|---:|
| Opening, roh | −0,0574 | **1,1155** | 0,0171 | **6,77** |
| Closing, roh | −0,0565 | **1,1131** | 0,0163 | **6,92** |
| Opening + Kovariaten | −0,0463 | 1,1151 | 0,0171 | 6,74 |
| Closing + Kovariaten | −0,0459 | 1,1127 | 0,0164 | 6,89 |
| Opening + DltOpnCls + Kov. (= Eq. 3, R2-C1) | −0,0509 | 1,1227 | 0,0170 | 7,23 |

Die letzte Zeile reproduziert die bekannte Eq.-3-Zahl auf der ungefilterten
Stichprobe (1,12266 laut `eq3_contract_level/filter_sensitivity.csv`) — die
beiden Rechnungen hängen zusammen.

**Logit-Kalibrierung** (`logit_calibration.csv`), robust gegen die
Linearitätsannahme: Steigung Opening **1,1649** (SE 0,0247, t gegen 1 = 6,68),
Closing **1,1665** (SE 0,0240, t = 6,95). Die Intercepts treffen die Null
(p = 0,93 und p = 0,98) — **die Verzerrung sitzt in der Steigung, nicht im
Niveau**, dasselbe Bild wie bei Eq. 3.

**Deskriptiv je Preisdezil** (`bias_by_decile.csv`), Bias = Gewinnrate minus
mittlerer Preis:

| Dezil | Preis opn | Bias opn | t | Preis cls | Bias cls | t |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 0,192 | **−0,0385** | −4,57 | 0,184 | **−0,0428** | −5,07 |
| 5 | 0,486 | +0,0025 | 0,21 | 0,481 | −0,0028 | −0,23 |
| 10 | 0,826 | **+0,0342** | 4,13 | 0,834 | **+0,0423** | 5,43 |

Longshots gewinnen seltener als ihr Preis behauptet, Favoriten häufiger — das
Lehrbuchmuster, und zwar an beiden Enden des Fensters.

## Teil 2 — Schrumpft der Bias über das Fenster? **Nein.**

### Endpunkte, gepaart

Eine gestapelte Regression `Match ~ (1 + p) * Closing`, damit die Differenz
einen Standardfehler bekommt, der die Paarung beider Preise desselben
Kontrakts trägt (`calibration_stacked.csv`):

| | lambda |
|---|---:|
| Opening | 1,1155 |
| Closing | 1,1131 |
| **Differenz** | **−0,0024** (SE 0,0051, t = −0,48, **p = 0,63**) |

Getrennt nach Gruppen (`shrinkage_by_group.csv`) ändert das nichts: Favoriten
1,0806 → 1,0984 (p = 0,37), Longshots 1,0892 → 1,0983 (p = 0,68). Beide
Punktschätzer gehen sogar leicht in die falsche Richtung.

### Über die ganze Zeitachse

`Match_it = a(X) + lambda(X) * p_it + Kovariaten`, `X = log(Stunden bis
Anpfiff)`, Basis `ns(df = 4)` wie in der Antwort zu Comment 7, CR1 auf
Matchup, 1.466.371 Preise aus 175.166 Serien
(`continuous_calibration.csv`):

| Stunden vor Anpfiff | lambda | SE cl. | t gegen 1 |
|---|---:|---:|---:|
| 24 | 1,0875 | 0,0263 | 3,33 |
| 12 | 1,0893 | 0,0212 | 4,22 |
| 6 | 1,0998 | 0,0225 | 4,43 |
| 3 | 1,1065 | 0,0208 | 5,12 |
| 1 | 1,1123 | 0,0224 | 5,02 |
| 0,25 | 1,1134 | 0,0214 | 5,30 |

**lambda liegt über das gesamte Fenster signifikant über 1 und nähert sich 1
nicht an.** Die Differenz zwischen der letzten und der ersten Marke ist
**+0,0259 (SE 0,0200, t = 1,29)**, also wenn überhaupt eine leichte
Verstärkung.

### Warum das nicht im Widerspruch zur Lernrate steht

Zwei verschiedene Grössen, gemessen an denselben Kontrakten
(`shrinkage_by_decile.csv`):

| | Opening | Closing | Differenz | t |
|---|---:|---:|---:|---:|
| mittlerer \|Bias\| je Kontrakt | 0,42055 | 0,41634 | **−0,00421** | **−11,16** |
| Brier-Score | 0,20616 | 0,20392 | **−0,00224** | **−6,36** |
| Kalibrierungsverzerrung Dezil 1 | −0,0385 | −0,0425 | **−0,0040** | **−4,93** |
| Kalibrierungsverzerrung Dezil 10 | +0,0342 | +0,0365 | **+0,0022** | **+2,76** |

**Der einzelne Preis wird treffsicherer, die systematische Verzerrung der
Gruppe nicht** — an den Rändern wird sie sogar signifikant grösser. Genau
dasselbe Muster wie bei R1-vii (Genauigkeit bewegt sich kaum, Verzerrung
schon), nur hier mit umgekehrtem Vorzeichen: was hier nicht schrumpft, ist die
*Quer*schnittsverzerrung über Preisniveaus, während die *Längs*schnitt-
verzerrung (beta_1 gegen 1) sich sehr wohl bewegt.

## Teil 3 — Hängen die Lernraten damit zusammen?

### Der GMM-Umweg funktioniert

`fit_gmm_mod` schneidet die Stichprobe ausschliesslich über die Spalte
`Bookies` zu (`fit_gmm_mod.py:47`), und `_create_gmm_data` liest nur `Match`
und die `OddsMvt*`-Spalten. Es genügt daher, `Bookies` mit dem Gruppenlabel zu
überschreiben — **kein Umbau, keine Änderung an der Pipeline**. Damit sind
aktuelle Zahlen mit korrigiertem Zerfallsexponenten verfügbar, ohne auf den
NUTS-Neulauf zu warten. Laufzeit: 5 s je Gruppe, 25 s insgesamt.
Quelle: `gmm_by_group.csv`, Basis `C_normalized/wide_imputed.h5`, `incr = 5`.

| Gruppe | n | gamma | SE | J (p) |
|---|---:|---:|---:|---:|
| Gesamt | 183.210 | 0,00481 | 0,00043 | 58,5 (0,000) |
| **Favoriten** | 94.789 | **0,00740** | 0,00060 | 53,6 (0,000) |
| **Longshots** | 88.421 | **0,00098** | 0,00062 | 56,0 (0,000) |

Differenz **+0,00642**, SE 0,00086, **t = 7,44**. Die Kernaussage des Papers —
Favoriten lernen schneller — **hält also auch nach dem Exponenten-Fix**.
Longshots sind für sich genommen nicht von null unterscheidbar (t = 1,6).

### Aber die Dezilaussage hält nur zur Hälfte

| Dezil | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gamma (×1000) | 0,75 | 1,97 | 1,31 | −0,59 | **9,76** | 5,59 | 7,20 | 6,35 | 5,96 | 6,72 |

Der Befund „niedrig und ähnlich über die unteren Dezile" (Paper Zeile 878)
wird reproduziert: Dezil 1–4 liegen alle nahe null. Der Befund **„stronger
favorites tend to exhibit higher learning rates" wird NICHT reproduziert** —
das Maximum liegt bei Dezil 5, also mitten im Feld, und von Dezil 6 bis 10
ist die Reihe flach. Es ist eine **Stufe, kein Gradient**. Zeile 879 und 917
müssen entsprechend umgeschrieben werden.

### Einschränkung, die genannt werden muss

Der J-Test verwirft in praktisch jeder Gruppe (p < 0,05 in **9 von 10**
Dezilen -- allein D7 haelt mit p = 0,072 -- und auch im Gesamtmodell). Nach Bookmaker geschnitten verwirft er nur bei
1 von 24. Das Zusammenfassen über Bookmaker hinweg bringt Heterogenität in die
Momentbedingungen, die das Modell nicht abbildet. Die Gruppen-gammas sind
deshalb als **Vergleich untereinander** belastbar, nicht als Punktschätzer mit
derselben Qualität wie die bookmakerspezifischen.

### Der vom Referee vermutete Zusammenhang besteht so nicht

Der Referee fragt, ob die Lernraten mit der **Korrektur** des FLB
zusammenhängen. Teil 2 zeigt: es gibt keine Korrektur, die man erklären
könnte. Favoriten haben die höhere Lernrate, aber ihr Kalibrierungsbias ist
am Closing nicht kleiner als am Opening (1,0806 → 1,0984). Die Lernrate misst
die Konvergenz des Preises gegen den Ausgang im Sinne von Biais et al. — nicht
das Schliessen einer Querschnittsverzerrung über Preisniveaus. Das ist
beantwortbar, aber es ist **nicht** die Antwort, die der Kommentar erwartet.

## Zusatzprüfung — ändert die Normalisierung die Gruppenzuordnung?

Quelle: `split_invariance.csv`, `split_decile_crosstab.csv`; 182.941 in beiden
Fassungen vorhandene Serien.

- **`IsFav`: 0 abweichende Zuordnungen.** Bestätigt und erklärbar:
  `filter_and_shape.py:74-88` bildet `IsFav` aus dem Vergleich der beiden
  **rohen** Quoten, bevor die implizite Wahrscheinlichkeit gebildet wird. Der
  `normalize`-Schalter kann daran per Konstruktion nichts ändern.
- **Der Dezil-Split ist NICHT invariant, aber nur am Rand.** 169.092 von
  182.941 Serien (92,43 %) bleiben im selben Dezil, 13.849 (7,57 %)
  verschieben sich um genau eines, **keine einzige um zwei oder mehr**;
  Spearman 0,99922. Der Grund: `p = p_own / (p_own + p_other)` ist keine
  monotone Transformation von `p_own` allein, sondern hängt über die Marge
  auch von der Gegenseite ab. Zwei Kontrakte mit gleichem rohen Preis, aber
  verschiedener Marge tauschen die Rangfolge.
  Praktisch heisst das: die Dezilaussagen sind gegen die Normalisierung
  robust, aber es ist **kein** Nullbefund wie bei `IsFav`, und man sollte es
  nicht als solchen behaupten.

## Dateien

- `_flb_calibration.py` — Kalibrierung Opening/Closing, Logit, Bias je Dezil
- `_flb_shrinkage.py` — gepaarter Open-gegen-Close-Test je Dezil und Gruppe
- `_flb_continuous.py` — lambda(X) auf der kontinuierlichen Achse, `ns(df=4)`
- `_flb_gmm_split.py` — GMM je Gruppe, plus Invarianzprüfung des Splits
- `calibration_by_price.csv`, `calibration_stacked.csv`,
  `logit_calibration.csv`, `bias_by_decile.csv`, `calibration_filtered.csv`
- `shrinkage_by_decile.csv`, `shrinkage_by_group.csv`
- `continuous_calibration.csv`, `continuous_calibration_diff.csv`
- `gmm_by_group.csv`, `split_invariance.csv`, `split_decile_crosstab.csv`
