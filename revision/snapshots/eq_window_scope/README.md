# Matchweites vs. serieneigenes Zeitfenster (Machbarkeitsprüfung)

Rein diagnostisch, **kein Eingriff in die Produktions-Pipeline**.
Vergleichsbasis ist die normalisierte Baseline (Tag `revision-baseline`,
Stufe `C_normalized`) mit dem aktuellen Code, also **inklusive**
Zerfallsexponenten-Fix (`d8d26bc`).

> **Referenzfalle:** `C_normalized/gmm_by_bookie.csv` (γ̄ = 0,0320) ist **vor**
> dem Exponenten-Fix gerechnet. Die zum heutigen Code passende Referenz ist
> `E_gmm_exponent_fix/gmm_by_bookie.csv` (γ̄ = 0,005396). Gegen die falsche
> Referenz beträgt die Abweichung 5,96e−02 statt 9,89e−17.

## Frage

`resample_and_impute.py:90-91` setzt die Fenstergrenzen **je Matchup**:

```python
df["TsStart"] = df.groupby("Matchup")["Update"].transform("min")
df["TsEnd"]   = df.groupby("Matchup")["Update"].transform("max")
```

Bei serieneigenem Fenster wäre der Schlüssel `GroupId` (= Matchup × Bookies).
Ist der Wechsel machbar, und was kostet er?

## 1) Was geändert werden müsste

**Die Umstellung selbst sind zwei Zeilen.** `TsStart`/`TsEnd` kommen im
gesamten Code nur an zwei Stellen vor: gesetzt in `resample_and_impute.py:90-91`,
gelesen in `utils/resample.py:39-43`. Dort werden sie benutzt, um vor den
ersten eigenen Timestamp eine Zeile zu setzen (`OddsMvt` bleibt NaN, weil
`ffill` nicht rückwärts füllt) und hinter den letzten eine anzuhängen
(per `ffill` gefüllt). Bei serieneigenem Fenster sind beide Bedingungen
`False` — die Zweige werden unerreichbar, ohne dass man sie anfassen muss.

**Der Rattenschwanz hängt an der Imputation, nicht am Fenster.** Fällt die
Imputationsmasse auf null, werden im selben File mehrere Blöcke gegenstandslos
und müssen entfernt oder abgesichert werden, nicht bloß stehen gelassen:

| Stelle | Was passiert |
|---|---|
| `resample_and_impute.py:128-129` | `frac_missings` → 0 |
| `:164-176` | `calc_imput_loss` mit `n_mvt = round(frac_missings·51)` → **0 maskierte Zellen** |
| `:186-214` | Abbildung `imput_loss.pdf` wird inhaltsleer |
| `:217` | `impute_missings` wird zum No-Op |
| `run_estimation.py:203` | schreibt `frac_missings` (aktuell **0,0784**) nach `values.dat` — der Wert verschwindet aus dem Papertext |

**Nicht betroffen:** `TsDur` wird in `filter_and_shape.py:101` bereits **je
`GroupId`** gebildet. Der Filter `ts_dur = [12, 72]` und die Kovariate `TsDur`
sind also schon serieneigen und ändern sich nicht. `GroupId` existiert an der
Änderungsstelle (`:96` nutzt es bereits). Die Matchup-weise Partitionierung für
den Pool (`:107-118`) funktioniert unverändert.

**Vier Konsumenten des Wide-Frames sind betroffen**, nicht nur das GMM:
`analyze_time_series_diagnostics` (ADF/GARCH), `estimate_unbiasedness_regressions`,
`estimate_gmm_learning_rate`, `estimate_bayesian_learning_rate`.

> Praktisch reduziert sich das: nach der bereits getroffenen Achsen-Entscheidung
> in **R2-C3** laufen die Unbiasedness-Regressionen künftig auf der
> kontinuierlichen absoluten Achse — dort entfallen Raster und Imputation
> ohnehin. Die Fensterfrage betrifft damit im Kern **GMM und Bayesian**
> (plus die GARCH-Tabelle).

## 2) Konsequenz für die Imputation: sie entfällt vollständig

Gemessen auf der Baseline-Stichprobe (184.112 Serien nach Varianzfilter,
20.854 Matchups). Quelle: `_window_scope.py`, `window_scope_per_series.csv`.

| | |
|---|---:|
| Serien mit eigenem Start **nach** dem Matchup-Start | **158.204 (85,9 %)** |
| Verspätung Median / Mittel / p99 / Max (h) | 0,617 / 2,391 / 24,8 / 169,0 |
| Rasterzellen vor dem eigenen Start | **7,85 %** |
| berichteter `frac_missings` (`values.dat`) | **7,84 %** ✔ |

Die 7,85 % reproduzieren den berichteten Wert — die analytische Rechnung
(Stützstelle *k* liegt bei `k/50` des Fensters, weil das 1-min-Raster
gleichabständig ist) trifft die Pipeline.

**Restfälle gibt es nicht.** Direkt an `resample()` geprüft, beide Regime auf
denselben Serien, Matchups vollständig gezogen (`_window_scope_c.py`):

| Regime | Zeilen | NaN | Serien mit NaN |
|---|---:|---:|---:|
| matchweit | 364.803 | 28.914 (7,93 %) | 6.142 |
| **serieneigen** | 364.803 | **0** | **0** |

Auf dem **vollen** Frame bestätigt: 183.221 Serien, `NaN(long) = 0`.
Lücken *innerhalb* einer Serie erzeugen keine NaN, weil
`asfreq(freq, method="ffill")` sie vorwärts füllt; die erste Rasterzelle ist
per Konstruktion der eigene erste Timestamp. Schlusspreise sind in beiden
Regimen identisch.

**Die Imputation sitzt fast vollständig am Fensteranfang:**

| Stützstelle | Lage im Fenster | Anteil imputierter Serien |
|---|---:|---:|
| `OddsMvt0` | 0 % | **85,93 %** |
| `OddsMvt26` | 52 % | 1,42 % |
| `OddsMvt31` | 62 % | 0,53 % |
| `OddsMvt36` | 72 % | 0,13 % |
| `OddsMvt41` | 82 % | 0,01 % |
| `OddsMvt46` | 92 % | 0,00 % |

## 3) Konsequenz für das GMM: die Momentbedingung bleibt gültig

**Der Zerfallsfaktor ändert sich nicht.** `_gen_meth_mom.momcond` bildet ihn
aus den Rasterpositionen `tau = [n_per − i·incr + 1] = [47, 42, 37]`. Das ist
eine reine Funktion von `n_per` und `incr`, für **jede** Serie dieselbe Zahl,
in beiden Regimen. Endog/Exog/Instrumente ändern nur ihre Werte, nicht ihre
Konstruktion.

**Die Invarianz trägt.** Das Paper beruft sich bereits darauf (`tex:481`):
„if the true learning rate $t$ was scaled by a constant $n$, we would still
obtain the same moment conditions as $n$ cancels during the division of the
two equations." Der `revision_log` (R1-vi, Nachtrag 2026-08-15) hat das
verschärft: der Faktor kürzt sich **schon innerhalb der Zeile**, denn
`(n·tau₂)/(n·tau₁) = tau₂/tau₁`. Ein *match*-spezifisches `n_m` ist damit
unschädlich — und ein *serien*-spezifisches `n_i` genauso. **Die Herleitung
ändert sich nicht; der Index wechselt von `m` auf `i`.**

**Was die Invarianz nicht abdeckt: den Ursprung der Uhr.** Vives (1995) zählt
`t` ab Beginn des Lernens. Matchweit ist `tau = 1` der erste Preis des
*Marktes* — für einen Spät-Eröffner ein Zeitpunkt, zu dem er noch gar keinen
Preis gestellt hatte und dessen Wert imputiert ist. Serieneigen ist `tau = 1`
sein eigener erster Preis. Der Wechsel rückt den Ursprung also näher an die
Theorie; die Skaleninvarianz sagt dazu nichts.

**Empirisch relevanter ist aber das Fenster*ende*.** Die Stützstellen werden
neu vertaktet, und zwar überwiegend hinten (`_retiming.py`):

| Stützstelle | Verschiebung serieneigen − matchweit (h) | |
|---|---:|---:|
| | Median | Mittel |
| `OddsMvt46` | −0,31 | −1,83 |
| `OddsMvt41` | −0,16 | −1,37 |
| `OddsMvt36` | −0,07 | −0,92 |
| `OddsMvt26` | +0,00 | +0,00 |
| `OddsMvt0` | +0,62 | +2,39 |

Die Verschiebung an `OddsMvt46` korreliert mit der Eintrittsverspätung nur mit
**r = 0,057**. Treiber ist nicht der späte Start, sondern das **frühere eigene
Fensterende**: matchweit wird eine Serie per `ffill` bis zum Matchup-Ende
gestreckt, serieneigen endet sie bei ihrem letzten eigenen Update. Median-Abstand
von `OddsMvt46` zum Matchup-Ende: 1,71 h → 2,72 h.

## 4) Wirkung auf gamma: die Lernrate halbiert sich

Aufwand gemessen (6 Kerne, WSL): Resample serieneigen voll **669,6 s**,
Kontrollbau auf 2.000 Matchups 84,2 s, GMM 24 Bookmaker 10–16 s. Insgesamt
rund **15 Minuten** je Durchgang.

**Zwei Kontrollen vorweg:**

- Der eigene Resample-Pfad reproduziert `wide_imputed.h5` an den
  Momentbedingungs-Stützstellen `OddsMvt46/41/36/31` **bit-genau**
  (max |diff| = 0, 100,00 % identisch); `OddsMvt26` 99,99 %, `OddsMvt0`
  99,88 % (dort sind nur 2.432 von 18.002 Zellen überhaupt beobachtet).
- Das GMM auf dem Baseline-Frame reproduziert `E_gmm_exponent_fix/gmm_by_bookie.csv`
  auf **max |Δγ| = 9,89e−17**.

**Ergebnis** (`gmm_window_scope.csv`, CUE, `n_per=51`, `incr=5`, Start 0,01):

| | matchweit | serieneigen |
|---|---:|---:|
| γ Mittel | 0,005396 | **0,002671** |
| γ Median | 0,005748 | 0,003104 |
| Spanne | [0,00138, 0,01240] | [−0,00094, 0,00441] |
| negative γ | 0 | **2** |
| signifikant (\|t\| > 1,96) | **16 / 24** | **7 / 24** |
| J-Test verworfen (p < 0,05) | 1 / 24 | 2 / 24 |
| mittlere SE | 0,002213 | 0,001792 |

- Δγ Mittel **−0,002725 (−50,5 %)**, Median je Bookmaker **−41,6 %**.
- **23 von 24 Bookmakern fallen**, einer steigt (max Δ = +0,000303).
- Rangkorrelation matchweit/serieneigen **Spearman 0,35** — die Rangfolge löst
  sich weitgehend auf. `argmin` GGBET → BetInAsia, `argmax` Dafabet → Betfair:
  **beide Extreme wechseln**.

**Das ist nicht die Imputation.** Der Masking-Test in
`../gmm_imputation_test/` hat gezeigt, dass die Imputation γ auf 96,7 % der
Serien um **+0,0002** bewegt, also praktisch nicht; der gepoolte Versatz von
+0,0130 dort wird von 3,3 % der Serien getragen. Die Halbierung hier stammt
folglich aus der **Neuvertaktung der Stützstellen**, und die sitzt nach
Abschnitt 3 überwiegend am Fensterende.

## 5) Variante 3: `TsStart` serieneigen, `TsEnd` matchweit

Gedacht als Trennung der beiden Kanäle: Imputation am Anfang beseitigen, die
Stützstellen am Ende aber liegen lassen. Quelle: `_variant3.py`,
`support_beyond_last_price.csv`, `gmm_three_variants.csv`.
Der V3-Frame hat **183.374 Serien und 0 NaN** — die Imputation entfällt hier
genauso vollständig wie in V2.

### Serien enden fast genauso oft zu früh, wie sie zu spät beginnen

| | |
|---|---:|
| Serien, die vor dem Matchup-Ende aufhören | **157.772 (85,7 %)** |
| Abstand eigenes Ende → Matchup-Ende, Median / Mittel (h) | 0,483 / 2,201 |
| p90 / p99 / Max (h) | 5,52 / 25,45 / 174,6 |
| Anteil des Matchup-Fensters hinter dem eigenen Ende | Median 1,87 %, Mittel 6,47 % |

Das Bild ist fast spiegelbildlich zur Eintrittsverspätung (85,9 %, Median
0,617 h). Der „Schwanz" ist kein Randphänomen.

### Der entscheidende Befund: die Stützstellen sind zu einem Viertel fortgeschrieben

Anteil der Serien, bei denen die Stützstelle **zeitlich hinter dem letzten
tatsächlich beobachteten Preis** liegt — der Wert ist dort eine über das
Quotierungsende hinaus fortgeschriebene Konstante:

| Stützstelle | V1 matchweit | V2 serieneigen | **V3 Start eigen** |
|---|---:|---:|---:|
| `OddsMvt26` | 1,46 % | 0,00 % | 1,74 % |
| `OddsMvt31` | 2,70 % | 0,00 % | 3,13 % |
| `OddsMvt36` | 5,22 % | 0,00 % | 6,07 % |
| `OddsMvt41` | 11,09 % | 0,00 % | 12,37 % |
| **`OddsMvt46`** | **24,43 %** | **0,00 %** | **26,05 %** |

Staleness dort, wo fortgeschrieben wird (`OddsMvt46`): Median 2,19 h (V1) bzw.
2,13 h (V3), p90 rund 13 h.

**V3 löst das Problem nicht, sondern verschärft es leicht** — der spätere
Fensterstart schiebt alle Stützstellen nach rechts.

> **Nebenbefund über die publizierte Fassung:** schon in V1, also in der
> aktuellen Spezifikation, ist knapp **ein Viertel** von `OddsMvt46` ein
> fortgeschriebener Wert. `OddsMvt46` ist `exog[:,0]`, steht also **direkt in
> der ersten Momentbedingung** — anders als das viel diskutierte `OddsMvt0`,
> das nur über ein Instrument eingeht. Der Anteil ist dreimal so groß wie die
> Imputationsmasse (7,85 %) und bisher nirgends quantifiziert.

### gamma: beide Kanäle wiegen etwa gleich schwer

| | V1 matchweit | **V3 Start eigen** | V2 serieneigen |
|---|---:|---:|---:|
| γ Mittel | 0,005396 | **0,004139** | 0,002671 |
| γ Median | 0,005748 | 0,004736 | 0,003104 |
| Spanne | [0,00138, 0,01240] | [−0,00031, 0,00699] | [−0,00094, 0,00441] |
| negativ | 0 | 2 | 2 |
| signifikant (\|t\|>1,96) | 16 / 24 | 12 / 24 | 7 / 24 |
| Δ zu V1 | – | −23,3 % | −50,5 % |

**Zerlegung:** Kanal Anfang −0,001257 (−23,3 %), Kanal Ende −0,001468
(weitere −27,2 Prozentpunkte von V1). **Die frühere Vermutung, die Halbierung
komme überwiegend vom Fensterende, trifft nicht zu — beide Kanäle wiegen
etwa gleich.**

Da der Masking-Test (`../gmm_imputation_test/`) zeigt, dass die Imputation
selbst γ nur um +0,0002 bewegt, ist auch der Anfangskanal fast vollständig
**Neuvertaktung**, nicht Imputationsbereinigung.

Spearman-Rangkorrelationen: V1↔V2 **0,3496**, V1↔V3 **0,4922**,
V2↔V3 **0,7322**. `argmax` wandert Dafabet → Interwetten (V3) → Betfair (V2);
Dafabet selbst fällt von 0,0124 auf 0,0035 (V3) bzw. 0,0017 (V2).

## 6) Sensitivität: gamma auf Serien ohne fortgeschriebene Stützstellen

Quelle: `_clean_subset.py`, `gmm_clean_subset.csv`. „Sauber" heißt: alle fünf
Stützstellen `OddsMvt26/31/36/41/46` liegen zeitlich weder vor dem eigenen
ersten noch nach dem eigenen letzten Preis.

| Teilmenge | n Serien | Anteil |
|---|---:|---:|
| sauber unter V1 | 136.760 | 74,3 % |
| sauber unter V3 | 136.154 | 74,0 % |
| **Schnittmenge V1 ∩ V3** | **134.342** | **73,0 %** |
| V2 | alle | 100 % (per Konstruktion) |

Rund **ein Viertel aller Serien** hat mindestens eine fortgeschriebene
Stützstelle. Kleinstes Bookmaker-n auf der Schnittmenge: 1.529 — die
per-Bookmaker-Schätzung bleibt tragfähig.

### Auf sauberen Serien laufen die drei Zeitachsen zusammen

| | V1 matchweit | V3 Start eigen | V2 serieneigen |
|---|---:|---:|---:|
| volle Stichprobe | 0,005396 | 0,004139 | **0,002671** |
| eigene saubere Teilmenge | 0,003918 | 0,003227 | – |
| **Schnittmenge (identische Serien)** | **0,003699** | **0,003182** | **0,003366** |

Auf der Schnittmenge liegen alle drei zwischen **0,0032 und 0,0037**. Die
Spannweite schrumpft von 0,0027 (volle Stichprobe) auf 0,0005. **V2 ist dort
kein Ausreißer mehr, sondern liegt zwischen V1 und V3.**

Spearman auf der Schnittmenge: V1↔V3 **0,6704**, V1↔V2 **0,7026** — gegenüber
0,4922 und 0,3496 auf der vollen Stichprobe.

### Zwei Konsequenzen

**Erstens, zur gestellten Frage:** der V1→V3-Unterschied beruht nur teilweise
auf den fortgeschriebenen Serien. Er schrumpft von −23,3 % (voll) über −17,6 %
(eigene saubere Teilmengen) auf **−14,0 % (Schnittmenge)**, verschwindet also
nicht. Etwa 40 % des Abstands sind Stichprobenzusammensetzung, etwa 60 %
bleiben **reine Neuvertaktung**. Damit ist die Achsenwahl auf sauberen Serien
tatsächlich eine inhaltliche Frage — aber sie bewegt γ nur noch um 14 %, nicht
um 50 %.

**Zweitens, und gewichtiger:** die Halbierung von γ unter V2 war **fast
vollständig ein Effekt der fortgeschriebenen Serien**, nicht der eigenen
Zeitachse. Dieselben Serien wirken in beide Richtungen: unter V1 heben sie γ
von 0,0037 auf 0,0054 (+46 %), unter V2 senken sie es von 0,0034 auf 0,0027
(−21 %).

> **Das trifft die publizierte Fassung direkt.** Restringiert man V1 auf
> saubere Serien, fällt die Zahl signifikanter Bookmaker von **16 auf 8 von
> 24** und γ von 0,0054 auf 0,0037. Ein erheblicher Teil des publizierten
> Befundes ruht damit auf Stützstellen, die für ein Viertel der Serien keine
> beobachteten Preise sind. Das ist unabhängig von jeder Fensterentscheidung
> und sollte als Sensitivität berichtet werden.

*Einschränkung:* „Sauber" selektiert auf Serien, die bis nahe an das
Matchup-Ende quotieren — also auf aktivere, länger gestellte Märkte. Die
Teilmenge ist nicht die „wahre" Stichprobe, sondern die, auf der die
Momentbedingung ohne fortgeschriebene Werte auskommt.

## 7) Woher der V1/V2-Unterschied kommt: die fortgeschriebenen Serien

Quelle: `_split_ffill.py`, `_decay.py`, `gmm_group_split.csv`,
`support_ties.csv`, `decay_by_group.csv`. Gruppen nach dem **V1**-Raster
gebildet; unter V2 sind dieselben Serien per Konstruktion alle sauber.

| Gruppe | n | γ unter V1 | γ unter V2 | Differenz |
|---|---:|---:|---:|---:|
| sauber | 138.432 | 0,003840 | 0,003095 | −0,000745 |
| **fortgeschrieben** | **44.607** | **0,007954** | **0,002152** | **−0,005802** |

Die fortgeschriebenen Serien (24,4 %) tragen unter V1 ein **doppelt so hohes**
γ wie die sauberen und **fast das Vierfache** dessen, was dieselben Serien
unter V2 zeigen. Auf der sauberen Gruppe ist der Regimeunterschied achtmal
kleiner. **Der V1/V2-Abstand auf der vollen Stichprobe stammt fast
vollständig aus dieser Gruppe.** Unter V2 ist dort **kein einziger** der 24
Bookmaker signifikant (0/24).

### Der modellfreie Zerfall zeigt dasselbe

Mittlerer quadrierter Prognosefehler `E[(p_k − Match)²]` — genau das
Verhältnis, das die Momentbedingung fittet:

| Gruppe / Variante | `OddsMvt36` | `OddsMvt41` | `OddsMvt46` | Verhältnis 46/36 |
|---|---:|---:|---:|---:|
| sauber V1 | 0,20556 | 0,20529 | 0,20522 | 0,9983 |
| sauber V2 | 0,20552 | 0,20531 | 0,20525 | 0,9987 |
| **fortgeschrieben V1** | 0,20148 | 0,20103 | 0,20064 | **0,9958** |
| **fortgeschrieben V2** | 0,20164 | 0,20168 | 0,20142 | **0,9989** |

Auf denselben Serien misst V1 einen deutlich steileren Zerfall als V2
(0,9958 gegen 0,9989; ohne Lernen wäre 1,0000). Die Werte reproduzieren die
GMM-Schätzungen: aus γ = 0,00795 folgt `(37/47)^(2γ) = 0,9962`, aus
γ = 0,00215 folgt `0,99897` — beobachtet 0,9958 und 0,9989.

### Die Hypothese trifft im Ergebnis zu, aber nicht im Mechanismus

Vermutet war: unter V1 sind die späten Stützstellen konstant, das erhöht den
gemessenen Varianzzerfall künstlich. Die Tie-Statistik widerlegt den zweiten
Teil:

| | Mittel verschiedener Werte unter den 5 Stützstellen | alle fünf identisch |
|---|---:|---:|
| V1 sauber | 2,230 | 28,21 % |
| **V1 fortgeschrieben** | **2,411** | **9,67 %** |
| **V2 dieselben Serien** | **1,818** | **43,80 %** |

Unter V1 sind die fortgeschriebenen Serien **variabler** als die sauberen und
deutlich variabler als dieselben Serien unter V2. Die künstliche Konstanz
entsteht nicht unter V1, sondern **unter V2**: dort wird das Raster in das
kurze eigene Fenster gestaucht, in dem oft nur wenige Updates liegen, und
43,8 % der Serien tragen an allen fünf Stützstellen denselben Wert.

Das passt zur Algebra: sind zwei Stützstellen identisch, wird
`(p−ω)² − (τ₂/τ₁)^{2γ}(p−ω)² = 0` nur von **γ = 0** gelöst. Konstanz drückt γ
gegen null — deshalb V2 mit 0,00215 und 0/24 signifikant.

**Der tatsächliche Mechanismus unter V1 ist ein anderer:** die Fortschreibung
macht die späten Stützstellen nicht neutral konstant, sondern stempelt ihnen
den **letzten echten Preis** auf — also den genauesten Preis der Serie —
während die frühen Stützstellen echte, ungenauere Frühpreise bleiben. Der
quadrierte Fehler fällt in dieser Gruppe von 0,20148 auf 0,20064, obwohl
dazwischen gar nicht mehr quotiert wurde. Das erzeugt einen Kontrast, der wie
schnelles Lernen aussieht.

**Beide Regime verzerren diese 24,4 % der Serien, in entgegengesetzte
Richtungen:** V1 überzeichnet den Zerfall, indem es die terminale Genauigkeit
nach vorn stempelt; V2 löscht ihn, indem es das Raster in ein Fenster mit zu
wenigen Updates staucht. Auf dieser Teilmenge ist **keine** der beiden
Zeitachsen vertrauenswürdig.

## 8) Fortschreibung oder andere Märkte? Die Dosis-Wirkungs-Kurve entscheidet

Quelle: `_diagnose_ffill.py`, `_diagnose2.py`, `gmm_fill_ladder.csv`,
`pairwise_diffs.csv`, `ffill_by_bookie.csv`.

### Gamma steigt monoton mit der Menge der Fortschreibung — und bricht dann zusammen

Gepoolte CUE-Schätzung, `n_fill` = Zahl der fünf Stützstellen hinter dem
letzten echten Preis:

| `n_fill` | n | γ unter V1 | γ unter V2 (dieselben Serien) |
|---:|---:|---:|---:|
| 0 | 138.432 | **0,003562** | 0,002883 |
| 1 | 24.408 | **0,006623** | 0,002034 |
| 2 | 10.738 | **0,012988** | 0,002300 |
| 3 | 4.597 | **nicht schätzbar** | −0,001125 |
| 4 | 2.233 | **nicht schätzbar** | 0,004331 |
| 5 | 2.631 | **nicht schätzbar** | 0,005141 |

Unter V1 verdreifacht sich γ von `n_fill = 0` auf `n_fill = 2` (0,0036 →
0,0130). Bei `n_fill ≥ 3` wird die Momentkovarianz **singulär** und CUE bricht
mit `LinAlgError` ab — mehrere Instrumente sind Differenzen identischer Werte
und damit exakt null. Der Ein-Schritt-Rückfall liefert dort γ = 0,000000, was
kein Schätzwert ist, sondern die algebraische Konsequenz identischer
Stützstellen. Schon `n_fill = 2` zeigt die Entartung an: SE 0,00016 und
t = 81 sind für diese Datenlage unplausibel präzise.

**Unter V2 fehlt jede Systematik** — γ schwankt ohne Trend zwischen −0,001 und
0,005. Dieselben Serien, nur auf der eigenen Achse getaktet, zeigen den
Gradienten nicht.

### Die paarweisen Differenzen widerlegen die Konstanz-Erklärung endgültig

Anteil exakt gleicher benachbarter Stützstellen:

| | `P46 − P41` = 0 | `P41 − P36` = 0 | mean \|P46−P41\| |
|---|---:|---:|---:|
| V1 sauber | 60,55 % | 66,34 % | 0,00609 |
| **V1 fortgeschrieben** | **49,99 %** | **59,50 %** | **0,00830** |
| V2 fortgeschrieben | 75,43 % | 77,47 % | 0,00382 |

Unter V1 sind die fortgeschriebenen Serien **seltener** konstant und
**stärker** bewegt als die sauberen. Der Grund steht in der `n_fill`-Verteilung:
55 % der betroffenen Serien haben nur **eine** gefüllte Stützstelle, meist
`OddsMvt46`. Dann ist `P46` der letzte echte — und genaueste — Preis, `P41`
noch ein echter Frühpreis, und die beiden unterscheiden sich gerade deshalb
besonders deutlich.

**Damit ist der Mechanismus identifiziert:** nicht Konstanz erzeugt den
Scheinzerfall, sondern der **aufgestempelte terminale Preis** im Kontrast zu
echten Frühpreisen. Konstanz wirkt in die Gegenrichtung und zerstört bei
`n_fill ≥ 3` die Schätzbarkeit.

### Es sind nicht andere Märkte

| Merkmal | sauber | fortgeschrieben | Diff |
|---|---:|---:|---:|
| `OpnOdds` (Median) | 0,500 | 0,500 | ±0,000 |
| Favoritenanteil | 0,5176 | 0,5161 | −0,0015 |
| Pro-Anteil | 0,3211 | 0,3122 | −0,0089 |
| Gewinnrate | 0,5102 | 0,5118 | +0,0016 |
| `NumOddsMvt` (Median / Mittel) | 7 / 8,51 | 5 / 6,36 | −2 / −2,15 |
| eigenes Fenster h (Median) | 18,68 | 16,83 | −1,85 |
| Matchup-Fenster h (Median) | 20,82 | 23,87 | +3,05 |

Preisniveau, Favoritenstatus, Wettbewerbsklasse und Ausgang sind **praktisch
identisch**. Die betroffenen Serien unterscheiden sich allein in der
Aktivität (rund 25 % weniger Preisänderungen) und darin, dass sie in längeren
Matchup-Fenstern liegen — beides genau die mechanischen Ursachen der
Fortschreibung, keine Markteigenschaft, die eine höhere Lernrate begründen
würde.

**Aber die Bookmaker sind sehr ungleich betroffen:** von 16,2 % (GGBET) bis
**56,5 % (Vulkan Bet)**, 53,0 % (Betfair), 47,1 % (888sport). Der
Querschnittsvergleich der Lernraten über Bookmaker ist damit systematisch
kontaminiert — das erklärt, warum Betfair und Dafabet zwischen den Varianten
so stark wandern.

### Antwort

**Die publizierte Zahl ist verzerrt, nicht bloß gemischt.** Vier Gründe:

1. **Within-Serie:** dieselben 44.607 Serien liefern 0,0078 (V1) gegen 0,0021
   (V2). Selektion kann einen Unterschied auf identischen Serien nicht
   erklären.
2. **Dosis-Wirkung:** γ wächst monoton mit der Menge der Fortschreibung
   (0,0036 → 0,0066 → 0,0130).
3. **Der Gradient verschwindet**, sobald die Fortschreibung entfällt (V2).
4. **Keine Marktunterschiede** in Preisniveau, Favoritenanteil, Klasse oder
   Ausgang.

Größenordnung: die publizierten **0,0054** gegenüber **0,0036** auf Serien
ohne Fortschreibung — rund **+50 % Aufwärtsverzerrung**.

*Einschränkung:* V2 ist für diese Teilmenge kein sauberer Kontrafaktus, weil
dort die Stauchung des Rasters γ nach unten drückt (Abschnitt 7). Die
belastbare Referenz bleibt die **saubere Teilmenge**, auf der beide Regime
übereinstimmen.

## Einschätzung

Machbar ist der Wechsel ohne weiteres — zwei Zeilen plus das Ausräumen der
Imputationsblöcke. Er ist auch theoretisch sauber: die Momentbedingung bleibt
gültig, die Herleitung unverändert, und der Ursprung der Lernuhr rückt näher
an Vives/Biais. Er beseitigt zudem die Imputation an der Wurzel, statt sie zu
bestreiten — für R2-C2 wäre das das stärkste denkbare Argument.

**Der Preis ist hoch.** γ halbiert sich, die Zahl signifikanter Bookmaker
fällt von 16 auf 7, zwei γ werden negativ, und die Rangfolge über Bookmaker
löst sich fast auf (Spearman 0,35). Sämtliche γ-Aussagen des Papers — auch die
in den bereits geschriebenen Antworten zu R1-iv und R1-viii verwendeten
Zahlen — müssten neu geschrieben werden, dazu die Bayesian-Schätzung.

**Nachtrag nach Variante 3 (Abschnitt 5):** Die Kanaltrennung ist gerechnet.
Sie entlastet die Umstellung nicht, sondern verschiebt die Frage. Erstens
wiegen beide Kanäle etwa gleich (−23,3 % / −27,2 %), die Halbierung ist also
kein Endeffekt-Artefakt. Zweitens — und wichtiger — ist V3 keine Lösung: dort
sind **26,05 % von `OddsMvt46` fortgeschriebene Werte** statt beobachteter
Preise, geringfügig mehr als in der Baseline (24,43 %).

**Damit steht ein größeres Problem im Raum als die Imputation.** In der
publizierten Fassung beruht die erste Momentbedingung auf einer Stützstelle,
die für ein Viertel der Serien kein beobachteter Preis ist, sondern eine im
Median 2,2 Stunden alte Konstante.

**Nachtrag nach Abschnitt 6 — die Fensterfrage ist nicht die wichtige Frage.**
Auf Serien ohne fortgeschriebene Stützstellen liefern alle drei Zeitachsen
praktisch dasselbe γ (0,0032 bis 0,0037); die Achsenwahl bewegt γ dort um 14 %,
nicht um 50 %. Die Halbierung unter V2 war fast vollständig ein Effekt der
fortgeschriebenen Serien.

Empfehlung: **die Fenstergrenzen nicht umstellen.** Der Gewinn ist klein, der
Preis (Neuschreiben aller γ-Aussagen plus Bayesian) hoch, und V3 löst nichts.
Stattdessen die Fortschreibungsquote und die saubere Teilmenge als
Sensitivität berichten — das ist der ehrlichere und billigere Weg, und er
adressiert R2-C2 mit einer stärkeren Zahl als jede Fensterdiskussion: die
Imputation am Anfang bewegt γ nachweislich nicht, die Fortschreibung am Ende
schon.

## Dateien

- `_window_scope.py` — Verspätung, Imputationsmasse, Rest-NaN (Serienstichprobe)
- `_window_scope_c.py` — Rest-NaN korrekt auf ganzen Matchups gezogen
- `_retiming.py` — Verschiebung der Stützstellen in absoluter Zeit
- `_window_scope_gmm.py` — Wide-Frame serieneigen, Kontrollen, GMM beide Regime
- `window_scope_per_series.csv` — je Serie: Verspätung, Fensterlängen, imputierte Zellen
- `gmm_window_scope.csv` — γ, SE, J, p je Bookmaker in beiden Regimen
- `wide_series_own.parquet` — serieneigener Wide-Frame (regenerierbar)
