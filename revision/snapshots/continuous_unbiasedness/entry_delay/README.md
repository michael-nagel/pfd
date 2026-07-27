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
  eröffnen systematisch früh). Die Quartile sind **keine** bookmaker-bereinigten
  Gruppen; ein Fit mit Bookmaker-Effekten ist nicht gerechnet.
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
- `_entry_delay.py`, `_entry_delay_plot.py`, `_attenuation.py` –
  Reproduktionsskripte
