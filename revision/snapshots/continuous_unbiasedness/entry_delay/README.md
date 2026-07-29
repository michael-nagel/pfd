# Off-Market-Learning-Kontrolle: Eintrittsverspätung und β₁

Rein diagnostisch, **kein Eingriff in die Produktions-Pipeline**. Gehört zu
R2-C2 (Backward-Imputation) und nutzt dieselbe kontinuierliche Spezifikation
wie `../` (Modell R der Kanalzerlegung): echte Beobachtungen,
Matchup-Perzentilachse, `p_ref` = erster echt beobachteter Preis, ungewichtet,
`bam(Endog ~ s(X,k=6) + s(X, by=Exog, k=6))`.

## Frage

Referee 2 vermutet, dass spät einsteigende Bookmaker vor der eigenen Eröffnung
die Preise anderer beobachten ("Off-Market-Learning") – ihre zurückimputierten
Opening-Odds bilden dann nicht die tatsächliche Situation ab, und der
Markteintritts-Zeitpunkt wäre selbst informativ statt wegzuimputieren.

Prüfbare Fassung: hängt β₁ von der **Eintrittsverspätung** ab?

**Eintrittsverspätung** = Stunden zwischen dem matchweiten Marktstart
(frühester Preis über ALLE Bookmaker des Matchups, `TsStart` wie
`resample_and_impute.py:90`) und dem ersten eigenen beobachteten Preis.

Stichprobe: 1.292.338 Zeilen, **175.266 Serien**.

## 1) Verteilung der Eintrittsverspätung

| Kennzahl | Wert |
|---|---:|
| exakt 0 | 24.708 Serien (**14,10 %**) |
| ≤ 1 Minute | 18,33 % |
| Median | 0,617 h |
| Mittel | 2,421 h (sd 5,233) |
| 75. Perzentil | 2,217 h |
| 90. Perzentil | 6,067 h |
| 99. Perzentil | 25,0 h |
| Maximum | 168,98 h |

Die Verspätung ist also **kein Randphänomen**: die Hälfte aller Serien startet
mehr als 37 Minuten nach dem Markt, ein Viertel mehr als 2,2 Stunden, ein
Zehntel mehr als 6 Stunden.

Quartile (n je Gruppe 41.881–46.003):

| | Spanne (h) | Median (h) |
|---|---|---:|
| Q1 | 0,000 – 0,083 | 0,000 |
| Q2 | 0,100 – 0,617 | 0,300 |
| Q3 | 0,633 – 2,217 | 1,217 |
| Q4 | 2,233 – 168,983 | 4,867 |

## 2) β₁ je Quartil – die Hypothese trifft am linken Rand zu

| | n (Zeilen) | β₁ Mittel | β₁ am Anfang | β₁ am Ende |
|---|---:|---:|---:|---:|
| Q1 (zeitgleich) | 326.835 | 1,169 | **1,395** | 0,992 |
| Q2 | 336.180 | 0,919 | 1,303 | 0,867 |
| Q3 | 329.785 | 0,876 | 0,865 | 0,654 |
| Q4 (spät) | 299.538 | 0,983 | **0,881** | 0,482 |
| volle Stichprobe | 1.292.338 | 1,006 | 1,289 | 0,771 |

**Die Hypothese bestätigt sich am Fensteranfang, und zwar monoton.** Der
Abstand des Start-β₁ von 1 fällt mit der Verspätung: 0,395 → 0,303 → 0,135 →
0,119. Wer zeitgleich mit dem Markt eröffnet, startet bei β₁ ≈ 1,40; wer spät
einsteigt, startet praktisch bei 1 – konsistent damit, dass der Referenzpreis
der Spät-Einsteiger bereits informiert ist.

**Sie greift aber zu kurz:** die Späten bleiben nicht bei 1, sondern fallen
deutlich darunter (Q4 endet bei 0,482, Q3 bei 0,654), während Q1 als einzige
Gruppe bis zum Schluss auf ~1 bleibt (0,992). Späte Einsteiger konvergieren
also nicht gegen Unverzerrtheit, sondern laufen ins Gegenteil.

**Für R2-C2 zentral:** die frühe β₁-Überhöhung – die charakteristische Form
der publizierten Figure 3 – sitzt bei den Serien, die **zeitgleich mit dem
Markt eröffnen** (Q1: 1,395). Sie stammt *nicht* von den Spät-Einsteigern,
deren Frühwerte imputiert werden. Genau diese Q1-Serien brauchen gar keine
Imputation.

## 3) Interaktionsmodell – β₁ hängt signifikant von beidem ab

Ein einzelner Fit,
`bam(Endog ~ te(X,D,k=c(6,6)) + te(X,D,k=c(6,6), by=Exog))` mit
`D = log1p(Verspätung in h)` (log1p, weil die Verspätung häufig exakt 0 ist):

| Term | edf | Ref.df | F | p |
|---|---:|---:|---:|---:|
| `te(X,D)` | 13,997 | 16,011 | 23,35 | < 2e−16 |
| `te(X,D):Exog` | **26,200** | 27,954 | **471,77** | < 2e−16 |

Der Interaktionsterm ist hochsignifikant mit 26 effektiven Freiheitsgraden –
β₁ variiert also **gemeinsam** über Zeit und Verspätung, nicht nur über die
Zeit. An den Quartilsmedianen ausgewertet reproduziert das eine Modell die
vier getrennten Fits:

| an Median | β₁ Mittel | Anfang | Ende |
|---|---:|---:|---:|
| Q1 0,00 h | 1,105 | 1,445 | 0,947 |
| Q2 0,30 h | 1,010 | 1,211 | 0,851 |
| Q3 1,22 h | 0,877 | 0,861 | 0,679 |
| Q4 4,87 h | 1,037 | 1,098 | 0,559 |

**Das ist die direkte, testbare Antwort auf R2-C2:** der
Markteintritts-Zeitpunkt ist informativ. Ihn wegzuimputieren verwirft
Information, die β₁ nachweislich erklärt.

## 4) Kompositions-Kontrolle – und ein unerwarteter Befund

Kontrolle der Prämisse: von den 24.568 vollständig beobachteten Serien des
Masking-Tests haben **100,0 % eine Verspätung von exakt 0** (alle 24.568
wurden im kontinuierlichen Frame wiedergefunden). Sie sind also eine
Teilmenge der Q1-Gruppe. Die übrigen Serien haben Median 0,917 h.

| Spezifikation | Serien | β₁ Mittel |
|---|---:|---:|
| volle Stichprobe | 175.266 | 1,006 |
| nur vollständig beobachtete | 24.568 | **1,200** |
| Differenz | | **+0,194** |

**Das ist ein Kompositionseffekt, kein Messgrößeneffekt** – dieselbe
Spezifikation, dieselben echten Preise, nur eine andere Serienmenge. Die
früh eröffnenden Serien haben ein systematisch **höheres und flacheres** β₁
(1,299 → 1,087) als die Gesamtpopulation (1,289 → 0,771).

### Konsequenz für die bisherige Lesart

Der Niveau-Versatz von −0,220 zwischen kontinuierlicher Schätzung und
Baseline (Kanalzerlegung in `../README.md`) ist damit **nicht allein** der
Imputation zuzuschreiben. Das mittlere β₁ der Baseline liegt bei ~1,226; die
kontinuierliche Schätzung **auf den vollständig beobachteten Serien allein**
erreicht 1,200 – also fast dasselbe Niveau, ganz ohne Imputation.

Das **entkräftet den Masking-Befund nicht**: der ist ein
*Within-Sample*-Vergleich (dieselben 24.568 Serien, echt vs. imputiert) und
damit per Konstruktion kompositionsfrei. Es ergänzt ihn:

1. **Innerhalb** derselben Serien hebt die Imputation β₁ am frühen Rand stark
   an (Masking-Test: 1,262 → 2,460 bei Perzentil 2).
2. **Zwischen** den Serien ist β₁ echt heterogen: früh eröffnende Serien haben
   ein höheres, flacheres β₁ als spät einsteigende.

Beides zeigt in dieselbe Richtung: die Imputation wird ausgerechnet auf die
Spät-Einsteiger angewandt, deren wahres β₁ **niedriger** liegt, und ersetzt
deren Frühwerte durch Werte, die sich wie die der Früh-Eröffner verhalten. Die
zwei Effekte verstärken einander.

Die Zerlegung des Versatzes in Imputations- und Kompositionsanteil ist
inzwischen durchgerechnet – über die vierte Zelle des 2×2 (Baseline-Methode auf
denselben 24.568 Serien). Ergebnis: der Kompositionseffekt existiert **nur** in
der echten Datenansicht (−0,195), unter der Baseline-Methode verschwindet er
(−0,010); 84 % der Gesamtlücke sind Imputation. Siehe `../README.md`,
Nachtrag 3.

## 5) Attenuations-Check – ist der Q4-Abfall auf 0,482 ein Varianzartefakt?

Bevor aus dem Abfall der Spät-Einsteiger auf 0,482 eine inhaltliche Aussage
(„Überreaktion") wird, muss die mechanische Alternative ausgeschlossen sein:
klassischer Messfehler im Regressor dämpft die Steigung um die Reliabilität
λ = var(x\*)/(var(x\*)+σ²_u). Hat Q4 einfach deutlich weniger Regressorvarianz,
fällt β₁ schon deshalb.

**Die Prämisse trifft zu – Q4 hat wirklich weniger Varianz.** Über alle
Beobachtungen (Quelle `attenuation_by_quartile.csv`):

| | var(Exog) | sd(Exog) | var rel. Q1 | mittl. \|p_t − p_ref\| | mittl. \|Endbewegung\| | var(Endog) |
|---|---:|---:|---:|---:|---:|---:|
| Q1 (zeitgleich) | 0,002748 | 0,0524 | 1,000 | 0,0379 | 0,0377 | 0,2079 |
| Q2 | 0,002488 | 0,0499 | 0,906 | 0,0369 | 0,0391 | 0,2135 |
| Q3 | 0,001988 | 0,0446 | 0,724 | 0,0328 | 0,0351 | 0,2153 |
| Q4 (spät) | 0,001433 | 0,0379 | **0,521** | 0,0268 | 0,0284 | 0,2141 |
| volle Stichprobe | 0,002182 | 0,0467 | 0,794 | 0,0337 | 0,0351 | 0,2127 |

Die Regressorvarianz fällt monoton mit der Verspätung, auf knapp die Hälfte in
Q4 – plausibel, denn wer spät einsteigt, startet bei einem schon informierten
Referenzpreis, dem weniger Bewegung folgt. var(Endog) ist dagegen über alle
Quartile praktisch konstant (0,208–0,215), es fehlt also nicht an
Ausgangsvarianz, sondern an Preisbewegung.

**Fensterlänge** (Quelle `window_length_by_quartile.csv`): Q4 sitzt in
deutlich *längeren* Matchup-Fenstern (Median 37,6 h vs. 17,5 h in Q1), deckt
davon aber nur 72 % ab statt 94 %. Eigene Fensterlänge und Beobachtungszahl
sind dagegen quartilsübergreifend ähnlich – die geringere Varianz kommt nicht
von kürzeren oder dünner besetzten Serien.

| | Matchup-Fenster (h, Median) | eigenes Fenster (h, Median) | Anteil am Matchup-Fenster | NumOddsMvt (Median) | Beob./Serie (Median) |
|---|---:|---:|---:|---:|---:|
| Q1 | 17,50 | 16,40 | 0,939 | 6 | 6 |
| Q2 | 20,57 | 18,75 | 0,912 | 7 | 7 |
| Q3 | 20,58 | 17,92 | 0,875 | 7 | 7 |
| Q4 | 37,58 | 21,85 | **0,722** | 6 | 6 |
| volle Stichprobe | 21,25 | 18,08 | 0,863 | 6 | 6 |

**Am Fensterende – dort, wo der Abfall sitzt – ist der Varianzunterschied
kleiner, nicht größer.** Nach Fensterposition aufgelöst
(`var_exog_by_position.csv`) liegt Q4/Q1 im ersten Dezil bei 0,434, im letzten
Dezil aber bei **0,579**. Der Varianzabstand *schrumpft* also genau dort, wo
β₁ auseinanderläuft:

| X-Dezil | Q1 | Q2 | Q3 | Q4 | Q4/Q1 |
|---|---:|---:|---:|---:|---:|
| (0,0 – 0,1] | 0,00192 | 0,00168 | 0,00124 | 0,00084 | 0,434 |
| (0,4 – 0,5] | 0,00276 | 0,00258 | 0,00189 | 0,00120 | 0,435 |
| (0,8 – 0,9] | 0,00302 | 0,00291 | 0,00226 | 0,00152 | 0,502 |
| **(0,9 – 1,0]** | 0,00288 | 0,00282 | 0,00235 | **0,00167** | **0,579** |

### Die Arithmetik: Attenuation reicht nicht

Am Fensterende (X > 0,9), gegen die beobachteten Randwerte der Quartilskurven:

| | var(Exog) bei X>0,9 | rel. Q1 | β₁ Ende (SE) |
|---|---:|---:|---:|
| Q1 | 0,00288 | 1,000 | 0,992 (0,031) |
| Q2 | 0,00282 | 0,976 | 0,867 (0,037) |
| Q3 | 0,00235 | 0,813 | 0,654 (0,039) |
| Q4 | 0,00167 | 0,579 | 0,482 (0,043) |

Zwei Rechnungen, beide gegen die Attenuationsthese:

1. **Vorwärts.** Damit Attenuation allein Q4 von einem wahren β₁=1 auf 0,482
   drückt, wäre σ²_u = 0,00179 nötig – das 1,07-Fache der Q4-Regressorvarianz.
   Dasselbe σ²_u auf die anderen Quartile angewandt sagt vorher:
   Q1 0,617, Q2 0,611, Q3 0,567 – beobachtet sind 0,992, 0,867, 0,654.
   Für Q1 liegt die Vorhersage **0,375 unter** dem beobachteten Wert, das sind
   rund 12 Standardfehler. Ein gemeinsames σ²_u kann die Quartilsspreizung
   nicht erzeugen: es sagt eine Spanne von 0,135 vorher, beobachtet sind 0,510.
2. **Rückwärts.** Setzt man Q1 als (nahezu) unverzerrt an, folgt daraus
   σ²_u = 0,000024. Auf Q4s geringere Varianz hochgerechnet ergibt das
   β₁(Q4) = **0,986** – beobachtet 0,482. Vom Q1→Q4-Abstand von 0,510 erklärt
   der Varianzunterschied damit 0,006, also **etwa 1 %**.

Damit Attenuation die Sache trüge, müsste σ²_u in Q4 rund **75-mal größer**
sein als das aus Q1 implizierte Niveau – das ist keine Attenuationsannahme
mehr, sondern eine eigenständige inhaltliche Behauptung über die Preisqualität
der Spät-Einsteiger, die dann selbst zu belegen wäre.

### Warum die zweite Messfehlerquelle in die Gegenrichtung wirkt

Die obige Rechnung modelliert Rauschen in `p_t` (idiosynkratisch, nur in
`Exog`) – das ist der Kanal, der klassisch gegen 0 dämpft, also die
konservative Variante. Rauschen im **Referenzpreis** `p_ref` wirkt umgekehrt:
`p_ref` steht auf beiden Seiten (Endog = ω − p_ref, Exog = p_t − p_ref), ein
geteilter Fehler u hebt Kovarianz *und* Varianz um var(u) an, sodass
β₁ = (cov\* + var u)/(var\* + var u) **gegen 1** gezogen wird. Ein β₁ von 0,482
kann dieser Kanal nicht erzeugen; er würde 0,482 im Gegenteil in Richtung 1
verzerren. Der beobachtete Abfall ist unter Berücksichtigung beider Kanäle
also eher unter- als überzeichnet.

**Fazit:** Der Varianzunterschied ist real und musste geprüft werden, erklärt
aber nur etwa 1 % des Q4-Abfalls. Der Abfall auf 0,482 ist damit als Befund
belastbar, nicht als Attenuationsartefakt zu verwerfen. Die Interpretation als
„Überreaktion" bleibt trotzdem eine Interpretation – siehe die
Einschränkungen unten (Konfundierung mit Bookmaker-Identität und Serienlänge
ist damit **nicht** ausgeräumt).

## 6) Within-Bookmaker-Test – hält der Verspätungseffekt bei festem Bookmaker?

Die Einschränkung unten („Verspätung und Bookmaker-Identität sind
konfundiert") ist der ernsteste Einwand gegen Abschnitt 2/3: manche Bookmaker
eröffnen systematisch früh, die Quartile könnten also verkappte
Bookmaker-Gruppen sein. Dieser Test identifiziert den Effekt **within**
Bookmaker – derselbe Bookmaker mal früh, mal spät eingestiegen.

### a) Die Quartile sind keine Bookmaker-Gruppen

Varianzzerlegung von log1p(Verspätung) über die 175.266 Serien:

| | Varianz | Anteil |
|---|---:|---:|
| gesamt | 0,6798 | |
| **between** Bookmaker | 0,0924 | **13,6 %** |
| **within** Bookmaker | 0,5874 | **86,4 %** |

Fast die gesamte Verspätungsvariation sitzt **innerhalb** der Bookmaker. Die
Konfundierung ist real, aber mild – und der Within-Test damit gut
identifiziert.

Kreuztabelle (Zeilenanteile; vollständig in `bookie_delay_crosstab.csv`,
sortiert nach n):

| Bookmaker | n Serien | Median h | IQR h | Q1 | Q2 | Q3 | Q4 | HHI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1xBet | 12.376 | 0,13 | 0,52 | 0,458 | 0,322 | 0,173 | 0,047 | 0,345 |
| GGBET | 11.049 | 0,87 | 3,75 | 0,352 | 0,120 | 0,183 | 0,346 | 0,291 |
| Marathonbet | 10.890 | 0,42 | 2,12 | 0,331 | 0,217 | 0,212 | 0,240 | 0,259 |
| VOBET | 10.850 | 0,53 | 1,85 | 0,288 | 0,239 | 0,257 | 0,216 | 0,253 |
| Pinnacle | 8.576 | 1,00 | 2,47 | 0,242 | 0,165 | 0,304 | 0,289 | 0,262 |
| BetVictor | 5.427 | 1,78 | 4,50 | 0,126 | 0,203 | 0,228 | 0,444 | 0,306 |
| Interwetten | 5.379 | 0,03 | 0,40 | 0,589 | 0,202 | 0,125 | 0,084 | 0,411 |
| Vulkan Bet | 4.462 | 4,30 | 6,76 | 0,108 | 0,056 | 0,146 | 0,690 | 0,512 |
| Dafabet | 3.549 | 5,97 | 20,42 | 0,047 | 0,039 | 0,157 | 0,758 | 0,603 |

- **22 von 24** Bookmakern haben alle vier Quartile mit ≥ 5 % besetzt,
  **17 von 24** mit ≥ 10 %.
- Mittlerer HHI **0,308** gegen 0,250 bei perfekter Streuung.
- Die Extreme sind erwartbar (Interwetten/1xBet fast immer sofort,
  Dafabet/Vulkan Bet fast immer spät), aber selbst Dafabet hat 24 % seiner
  Serien außerhalb von Q4.

### b) GAM mit Verspätungs-Interaktion, gepoolt vs. within

Drei Stufen auf denselben 1.292.338 Zeilen. `LD` = log1p(Verspätung),
`DW` = `LD` minus dem Bookmaker-Mittel (within-zentriert, damit per
Konstruktion orthogonal zur Bookmaker-Identität). β₁ wird in allen Stufen über
die Bookmaker-Verteilung marginalisiert, mit **über alle Verspätungsstufen
festen** Gewichten – so kann kein Kompositionseffekt in die Spreizung laufen.

| Modell | Spezifikation | edf(te:Exog) | F | p |
|---|---|---:|---:|---:|
| M0 gepoolt | `te(X,LD) + te(X,LD,by=Exog)` | 26,20 | 471,8 | < 2e−16 |
| **M1 within** | `+ B + Exog:B`, `DW` statt `LD` | **24,18** | **16,6** | **< 2e−16** |
| M2 within | wie M1, ohne `Exog:B` | 25,45 | 460,9 | < 2e−16 |

β₁ an den Verspätungsstufen (q10 … q90), Wert am Fensterende:

| Stufe | M0 (roh) | M1 (within) | M2 (within) |
|---|---:|---:|---:|
| q10 | 0,947 | 0,957 | 0,950 |
| q25 | 0,917 | 0,927 | 0,926 |
| q50 | 0,775 | 0,784 | 0,794 |
| q75 | 0,598 | 0,610 | 0,607 |
| q90 | 0,556 | 0,607 | 0,583 |
| **Spreizung q90 − q10** | **−0,390** | **−0,350** | **−0,366** |

**Der Effekt hält.** Der Interaktionsterm bleibt mit ~24 effektiven
Freiheitsgraden hochsignifikant, und **90 % (M1) bzw. 94 % (M2) der
Endspreizung überleben** die Within-Identifikation. Dass M1s F von 471,8 auf
16,6 fällt, ist erwartbar und kein Widerspruch: `Exog:B` absorbiert 24
Freiheitsgrade bookmakerspezifischer Steigung, gegen die der Interaktionsterm
dann antreten muss. M1 ist damit die konservative Fassung; M2 zeigt, dass die
Rangfrage um `Exog:B` das Ergebnis nicht trägt.

Die *Mittelwert*-Spreizung ist in beiden Within-Modellen sogar größer als
gepoolt (−0,207 / −0,229 gegen −0,106, also 194 % / 215 %). Dieses Verhältnis
ist jedoch instabil, weil M0s Mittelwert-Spreizung durch den nicht-monotonen
q90-Wert klein ausfällt; belastbar ist die Endspreizung.

### c) Modellfrei: Split an der eigenen Median-Verspätung

Ohne GAM-Interaktion, ohne Verteilungsannahme: je Bookmaker die eigenen Serien
an der **eigenen** Median-Verspätung teilen und für beide Hälften getrennt
β₁ schätzen (gleiche Spezifikation wie Modell R, k=6). Alle 24 Bookmaker
erfüllen die Mindestgröße, die Hälften sind je Bookmaker praktisch gleich groß.

| | Anteil negativ | Vorzeichentest | t-Test | gew. Mittel | ungew. Median |
|---|---:|---:|---:|---:|---:|
| Δ am Fensterende | **18 / 24** | **p = 0,011** | **p = 0,0008** | **−0,323** | −0,270 |
| Δ im Kurvenmittel | 13 / 24 | p = 0,42 | p = 0,074 | −0,183 | −0,191 |

**Am Fensterende ist der Effekt eine bookmakerübergreifende Regularität**
(18 von 24 Bookmakern negativ, gewichtet −0,323 – gut vereinbar mit M1s
−0,350). **Im Kurvenmittel ist er es nicht**: 13 von 24 ist vom Zufall nicht
zu unterscheiden. Das deckt sich mit b) und mit Abschnitt 2, wo der Mittelwert
über die Quartile nicht monoton ist, der Endwert aber schon.

Die fünf Bookmaker mit der breitesten eigenen Verteilung
(`bookie_widest_delay.csv`):

| Bookmaker | n früh/spät | Median h | sd log | β₁ früh (Ende) | β₁ spät (Ende) | Δ Ende |
|---|---:|---:|---:|---:|---:|---:|
| Dafabet | 1.775 / 1.774 | 5,97 | 1,140 | 1,054 | 0,795 | −0,259 |
| Betfair | 1.768 / 1.761 | 0,97 | 0,974 | 1,114 | 0,975 | −0,139 |
| GGBET | 5.530 / 5.519 | 0,87 | 0,958 | 0,988 | 0,625 | −0,364 |
| BetVictor | 2.714 / 2.713 | 1,78 | 0,935 | 1,154 | 0,139 | −1,015 |
| Vulkan Bet | 2.235 / 2.227 | 4,30 | 0,923 | 1,114 | 0,565 | −0,549 |

Alle fünf zeigen am Ende das erwartete Vorzeichen; gewichtet liegt ihr
Δ Ende bei **−0,478**, deutlich stärker als der Gesamtwert −0,323. Passend
dazu korreliert Δ Ende schwach negativ mit der eigenen Verspätungsstreuung
(r = −0,21): wer mehr eigene Variation hat, zeigt den Kontrast deutlicher.

Die Streuung über Bookmaker ist allerdings groß (sd der Δ Ende = 0,333, von
−1,015 bei BetVictor bis +0,294 bei Betway). Bei den dünn besetzten
Bookmakern sind die Kurven entsprechend unsicher – Dafabets Spät-Kurve
schwankt auf 1.774 Serien zwischen −1,3 und +3,0. **Interpretierbar sind
Niveau und Randwerte, nicht die Wellen** (siehe unten); die Abbildung
`within_bookmaker.{png,pdf}` skaliert die unteren Panels je Bookmaker
einzeln, die y-Achsen sind dort also **nicht** vergleichbar.

### Fazit

Der Verspätungseffekt am Fensterende ist **nicht** durch Bookmaker-Identität
erklärt: er überlebt Bookmaker-Fixed-Effects mit within-zentrierter
Verspätung (90–94 % der Spreizung) und zeigt sich unabhängig davon in einem
modellfreien Within-Split bei 18 von 24 Bookmakern. Damit ist die unten
gelistete Konfundierungs-Einschränkung für den **Endwert** ausgeräumt. Nicht
ausgeräumt ist sie für das Kurvenmittel, und die Konfundierung mit der
Serienlänge (`NumOddsMvt`, `TsDur`) bleibt in allen Stufen unkontrolliert.

## Zur Interpretation der Kurvenform

Wie in `../README.md` dokumentiert: bei k=6 ist die Zahl der Wendepunkte ein
Flexibilitätsartefakt. Interpretiert werden dürfen **Niveau und Randwerte**,
nicht die einzelnen Kreuzungen von 1. Das gilt hier ebenso für die
Oszillation der Q2/Q3/Q4-Kurven im mittleren Fensterbereich und für die
stärkere Welligkeit des Interaktionsmodells (te mit 6×6-Basis ist flexibler
als s(k=6)).

## Einschränkungen

- Die Verspätung ist **relativ zum beobachteten Marktstart** definiert, nicht
  zur tatsächlichen Markteröffnung – Oddsportal liefert nur, was gecrawlt
  wurde. Ein Bookmaker mit Verspätung 0 ist "der früheste im Datensatz", nicht
  notwendig "der früheste der Welt".
- Verspätung und Bookmaker-Identität sind konfundiert (manche Bookmaker
  eröffnen systematisch früh); die Quartile in Abschnitt 2 sind **keine**
  bookmaker-bereinigten Gruppen. Für den **Endwert** ist dieser Einwand in
  Abschnitt 6 abgearbeitet (86,4 % der Verspätungsvariation sind within
  Bookmaker; 90–94 % der Endspreizung überleben Bookmaker-FE; 18 von 24
  Bookmakern zeigen den Kontrast im eigenen Split). Für das **Kurvenmittel**
  bleibt er offen: dort ist die Within-Evidenz mit 13 von 24 Bookmakern nicht
  von Zufall zu unterscheiden.
- Verspätung korreliert mechanisch mit der Serienlänge (`NumOddsMvt`,
  `TsDur`); auch dafür ist nicht kontrolliert.
- Die Kausalrichtung ist nicht identifiziert: dass spätes Eintreten mit einem
  Start-β₁ näher an 1 einhergeht, ist mit Off-Market-Learning konsistent, aber
  auch mit Selektion (wer wartet, ist ein anderer Bookmaker-Typ).

## Dateien

- `entry_delay.{png,pdf}` – vier Panels: Verteilung, Quartilskurven,
  Interaktionsmodell, Kompositions-Kontrolle
- `delay_per_series.csv` – Verspätung + Quartil je Serie (mit Matchup/Bookies);
  liegt auf der Platte, ist aber **nicht committet** (6,2 MB, 175.266 Zeilen,
  aus `_entry_delay.py` regenerierbar)
- `delay_describe.csv` – Kennzahlen der Verteilung
- `beta1_delay_Q{1..4}.csv` – β₁ mit SE je Quartil
- `beta1_delay_full.csv` – β₁ auf der vollen Stichprobe
- `beta1_fully_observed.csv` – β₁ auf den 24.568 vollständig beobachteten
- `beta1_interaction.csv` – β₁(X, D) des Interaktionsmodells auf dem Gitter
- `attenuation_by_quartile.csv` – var(Exog), sd, mittlere absolute Bewegung
- `window_length_by_quartile.csv` – Fensterlängen und Belegung je Quartil
- `var_exog_by_position.csv` – var(Exog) je Quartil × X-Dezil
- `bookie_delay_crosstab.csv` – Bookmaker × Quartil, Streuungsmaße, HHI
- `bookie_widest_delay.csv` – die 5 Bookmaker mit der breitesten eigenen
  Verspätungsverteilung
- `beta1_within_bookmaker_models.csv` – β₁(X) je Modell (M0/M1/M2) und
  Verspätungsstufe
- `beta1_within_bookmaker_summary.csv` – Kennzahlen je Modell und Stufe
- `beta1_within_bookmaker_split.csv` – Within-Differenzen je Bookmaker
- `beta1_within_bookmaker_curves.csv` – β₁-Kurven früh/spät je Bookmaker
- `within_bookmaker.{png,pdf}` – Kreuztabelle, M0 vs. M1, fünf Einzel-Splits
- `_entry_delay.py`, `_entry_delay_plot.py`, `_attenuation.py`,
  `_within_bookmaker.py`, `_within_bookmaker_plot.py` – Reproduktionsskripte
