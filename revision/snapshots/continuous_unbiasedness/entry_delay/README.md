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

**Offen und wichtig für die Formulierung der Response:** die Zerlegung des
−0,220-Versatzes in Imputations- und Kompositionsanteil ist damit noch nicht
sauber quantifiziert. Die naheliegende Rechnung – Masking-Test auf einer nach
Verspätung *gewichteten* Stichprobe, oder Reweighting der vollständig
beobachteten Serien auf die Verspätungsverteilung der Gesamtpopulation – ist
nicht durchgeführt.

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
- `_entry_delay.py`, `_entry_delay_plot.py` – Reproduktionsskripte
