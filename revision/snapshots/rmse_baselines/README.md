# RMSE-Einordnung und Posting Time (R2-M7, zugleich R3-2)

Rein diagnostisch, **kein Eingriff in die Produktions-Pipeline**.
Datenbasis `revision-baseline` (normalisierte Preise, Match-Fix).

## Frage

Referee 2 (R2-M7) hat zwei Teile:

1. **Einordnung.** Der RMSE von „around 0.45" (tex:687) steht ohne
   Bezugspunkt. Ein Leser kann nicht beurteilen, ob das gut ist.
2. **Posting Time in Figur 1.** Bookmaker, die später eröffnen, haben die
   Preise der Konkurrenz bereits gesehen. Ihr Opening-RMSE wäre dann nicht
   besser kalibriert, sondern nur später gemessen.

Teil 2 ist derselbe Einwand wie **R3-2**, dort zugespitzt auf Pinnacle: dessen
auffällig hoher Opening-RMSE sei womöglich ein Artefakt früher
Marktteilnahme.

---

# TEIL 1 — Baselines für den RMSE

**Datenbasis:** `df_oc` wie in `bookmaker_accuracy.py:81–88`, 172.663
Kontrakte, 20.588 Matchups, 24 Bookmaker. Ungefilterte Fassung (184.415)
läuft überall als Sensitivität mit und ändert nichts.

## Die drei Bezugspunkte

| | Opening | Closing |
|---|---:|---:|
| Brier | 0,20664 | 0,20425 |
| **RMSE** | **0,45458** | **0,45194** |
| uninformiert (p ≡ 0,5) | 0,25 / RMSE 0,5 | 0,25 / RMSE 0,5 |
| **Brier Skill Score** | **0,1734** | **0,1830** |
| Grenze E[p(1−p)] | 0,21487 (RMSE 0,46341) | 0,21277 (RMSE 0,46126) |
| Abstand Brier − Grenze | **−0,00823** | **−0,00852** |
| SE (cluster Matchup) | 0,00121 | 0,00123 |
| t | **−6,78** | **−6,93** |

Quelle: `baselines.csv`.

**Lesart für den Text:** Ein RMSE von 0,455 klingt nach wenig Information,
ist aber der falsche Maßstab. Bei binärem Ausgang ist der Wertebereich eng —
der Münzwurf liegt bei 0,5, und die Preise nehmen davon **17,3 % der
Brier-Score-Masse** weg. Kalibrierung im Großen ist praktisch perfekt
(mittlerer Preis 0,5087 gegen Gewinnrate 0,5102, Differenz −0,0015).

## Der beobachtete Brier liegt UNTER der Kalibrierungsgrenze

Die Vermutung aus der Prüfspezifikation bestätigt sich, **und zwar exakt
testbar ohne jede Binnung**. Für binäres y gilt algebraisch

```
(y − p)² − p(1 − p) = (y − p)(1 − 2p)
```

Der Abstand des Brier-Scores zur Grenze ist also der Mittelwert einer
gewöhnlichen Beobachtungsgröße und lässt sich cluster-robust testen. Er ist
**negativ und hoch signifikant** (t = −6,78).

**Warum das kein Widerspruch ist:** E[p(1−p)] ist die Grenze eines perfekt
kalibrierten Prognostikers *mit genau dieser Preisverteilung*. Sind die Preise
**unterdispers** — die tatsächliche Gewinnrate liegt weiter von 0,5 entfernt
als der Preis —, dann ist die Grenze zu hoch angesetzt und der beobachtete
Brier unterbietet sie. Formal ist E[(y−p)(1−2p)] = E[(q−p)(1−2p)] mit
q = E[y|p]; bei Unterdispersion haben (q−p) und (1−2p) entgegengesetzte
Vorzeichen, also negativ.

Das ist **dieselbe Größe wie `eta_1` = 1,125** aus
`revision/snapshots/eq3_contract_level/ladder.csv`. Gegenprobe hier
(`calibration_slopes.csv`):

| | Kalibrierungssteigung, 20 Bins | auf Kontraktebene |
|---|---:|---:|
| Opening | 1,1165 | 1,1170 |
| Closing | 1,1137 | 1,1143 |

**Der Brier-Score unter der Grenze und der Favorite-Longshot-Bias sind
derselbe Befund in zwei Metriken.** Für die Antwort an die Referees ist das
verwertbar: der Bias ist nicht bloß statistisch nachweisbar, er ist groß
genug, um in der aggregierten Prognosegüte sichtbar zu werden.

## Murphy-Zerlegung

`Brier = REL − RES + UNC`, 20 Quantilsbins (Quelle: `murphy.csv`, dort auch
10/50 Bins und gleichbreite Bins).

| | Reliability | Resolution | Uncertainty | Rest |
|---|---:|---:|---:|---:|
| Opening | 0,000523 | 0,043482 | 0,249896 | −0,000294 |
| Closing | 0,000681 | 0,046032 | 0,249896 | −0,000291 |

- **REL ist winzig**: 0,25 % des Brier-Scores. Fehlkalibrierung ist als
  Ursache der 0,455 praktisch bedeutungslos.
- **RES trägt alles**: die Preise lösen **17,4 % der Ergebnisunsicherheit**
  auf (Closing 18,4 %). Der Rest ist irreduzible Unsicherheit des
  Tennisergebnisses, nicht Modellschwäche.
- **Der „Rest"** ist die Within-Bin-Varianz von p; die Zerlegung ist nur bei
  binkonstantem p exakt. Er schrumpft erwartungsgemäß mit feineren Bins
  (−0,0010 bei k = 10 → −0,0001 bei k = 50) und wird hier ausgewiesen statt
  weggelassen.

> **Achtung bei der Verwendung von REL in der Antwort.** Die Reliability aus
> der Murphy-Zerlegung mittelt über die gesamte Preisverteilung und ist
> gerade deshalb klein: Fehlkalibrierung nach oben und unten hebt sich in der
> Summe der Bins nicht auf, aber sie ist relativ zur Auflösung klein. Sie
> widerspricht dem Favorite-Longshot-Befund **nicht** — der zeigt sich in der
> Steigung, nicht in der mittleren quadrierten Abweichung.

## Opening gegen Closing

Gepaart auf denselben Serien (`opening_vs_closing.csv`):

```
Brier(Opening) − Brier(Closing) = +0,002389   SE 0,000376   t = +6,36
```

Das Closing nimmt **1,16 %** des Opening-Brier weg. Signifikant, aber klein —
konsistent mit der partiellen Lernrate.

## Stimmt „clustering around 0.45" noch?

**Nein, und das lag nicht an der Normalisierung.** Quelle:
`rmse_by_bookie_check.csv`.

| | Spanne | Median |
|---|---|---:|
| Figure-1-Größe (Panel, gewichtet) | 0,4506 – 0,4710 | 0,4622 |
| Serienebene (ungewichtet) | 0,4465 – 0,4646 | 0,4531 |
| publiziert (roh, `A_baseline`) | 0,4519 – 0,4719 | 0,4630 |

- max |Δ| gegen den publizierten Stand: **0,00244** (Interwetten). Die
  Rangfolge ist praktisch unverändert, die Extremränge exakt.
- In der Figure-1-Größe liegen **4 von 24** Bookmakern unter 0,455, **15** in
  [0,455; 0,465) und **5** ab 0,465.

**Der Satz war schon vor der Revision zu großzügig gerundet** — die
publizierten Werte reichen bis 0,4719. Vorschlag: *„with RMSE values between
0.45 and 0.47"*, plus die Einordnung aus Teil 1 statt des inhaltsleeren
„fairly accurate predictions".

---

# TEIL 2 — Posting Time

**Definition:** `OpnHrs` = Anpfiff minus erster beobachteter Zeitstempel der
Serie, in Stunden. **Groß = früh im Markt.** Restringiert auf die 24
Bookmaker der Schätzstichprobe (`shaped_data` enthält 33; der
`bm_quantile`-Filter in `filter_and_shape_data` reduziert auf 24).

## Mediane Eröffnungszeitpunkte

Auszug, vollständig in `posting_time_by_bookie.csv`:

| Bookmaker | Median h vor Anpfiff | Serien | RMSE Serienebene |
|---|---:|---:|---:|
| Betfair | 36,03 | 3.548 | 0,4568 |
| Betfred | 35,67 | 4.872 | 0,4578 |
| 888sport | 34,42 | 5.467 | 0,4591 |
| Betsafe / Betsson / NordicBet | ~25,0 | ~4.500 | ~0,4613 |
| **Pinnacle** | **20,63** | 8.657 | **0,4646** |
| **BetInAsia** | **20,27** | 6.373 | **0,4634** |
| GGBET | 19,27 | 11.602 | 0,4465 |
| Dafabet | 16,57 | 3.680 | 0,4513 |

**Spanne 16,6 h bis 36,0 h, Faktor 2,17.** Die Streuung ist real, aber vom
`ts_dur`-Filter [12, 72] h nach oben beschnitten.

### Pinnacle ist kein Früh-Eröffner

Das ist der direkteste Befund für **R3-2**: Pinnacle liegt mit 20,6 h auf
**Rang 12 von 24** beim Posting-Zeitpunkt — praktisch exakt beim
Stichprobenmedian (20,45 h) — hat aber den **schlechtesten** RMSE (Rang 24).
BetInAsia dasselbe: Rang 13 beim Timing, Rang 23 beim RMSE. Die drei
tatsächlich frühesten Bookmaker sind Betfair, Betfred und 888sport, und die
liegen beim RMSE im Mittelfeld.

**Die konkrete Vermutung des Referees zu Pinnacle trifft nicht zu.**

## Die Korrelation hängt daran, welche RMSE-Fassung man nimmt

Quelle: `correlations.csv`.

| RMSE-Fassung | Pearson | p | Spearman | p |
|---|---:|---:|---:|---:|
| **panelgewichtet (= Figure 1)** | **−0,059** | 0,786 | −0,071 | 0,741 |
| **Serienebene** | **+0,409** | 0,047 | **+0,470** | 0,020 |
| publiziert (roh, `A_baseline`) | −0,083 | 0,699 | −0,069 | 0,750 |

Vorzeichen der Referee-Hypothese ist **positiv** (früh = schlechter). Auf der
Serienebene tritt sie ein, in der publizierten Fassung nicht.

### Warum die beiden Fassungen auseinanderlaufen

`bookmaker_accuracy.py:62` rechnet den RMSE **auf dem Panel**. `OpnOdds` ist
je Serie konstant, also geht jede Serie mit ihrer **Zahl an Preisupdates**
gewichtet ein. Für eine Aussage über Prognosegüte müsste jedes Spiel einmal
zählen.

```
rmse_gap (panel − series) vs obs_per_series   Pearson +0,433 (p 0,035)
rmse_gap (panel − series) vs opn_hrs_med      Pearson −0,728 (p 0,000)
obs_per_series            vs opn_hrs_med      Pearson −0,395 (p 0,056)
```

Spät postende Bookmaker liefern mehr Updates je Serie (5,6 bis 10,8) und
werden im Panel stärker gewichtet; die Gewichtung hebt genau den
Zusammenhang auf, den die Serienebene zeigt.

> **Das ist ein eigenständiger Befund und betrifft Figur 1 direkt.** Die
> publizierte Größe ist beobachtungsgewichtet, ohne dass das im Text steht.
> Der Effekt auf die Niveaus ist klein (0 bis +0,0126), aber er ist
> systematisch mit dem Posting-Zeitpunkt korreliert — also genau mit der
> Größe, die R2-M7 und R3-2 zum Thema machen. **Empfehlung: Figur 1 auf die
> Serienebene umstellen** und das als Detail in der Antwort erwähnen.

## Partiell, kontrolliert für die Bookmaker-Marge

Quelle: `partial_correlations.csv`, `joint_regression.csv`.

| RMSE-Fassung | roh | partiell (Marge heraus) | t | p | Rang-partiell |
|---|---:|---:|---:|---:|---:|
| panelgewichtet | −0,059 | −0,173 | −0,80 | 0,431 | −0,169 |
| **Serienebene** | **+0,409** | **+0,327** | +1,58 | 0,128 | +0,362 (p 0,090) |
| publiziert (roh) | −0,083 | −0,193 | −0,90 | 0,378 | −0,164 |

Der Zusammenhang **bleibt der Richtung nach bestehen, verliert aber die
Signifikanz** (0,409 → 0,327, p = 0,13). Grund: Marge und Posting-Zeitpunkt
sind selbst korreliert (Pearson −0,266, Spearman −0,435) — margenarme Häuser
posten tendenziell später.

Gegenprobe zum Eintrag im `revision_log` (Marge gegen **rohen** RMSE, dort
−0,34): **reproduziert, Pearson −0,3431**, Spearman −0,177.

Gemeinsame Regression über die 24 Bookmaker:

```
RMSE_panel = 0,48079 − 0,000161 · OpnHrs − 0,22026 · Marge      R² = 0,158
                        (0,000200)          (0,112387)
```

Eine Standardabweichung früheres Posting (5,48 h) verschiebt den RMSE um
−0,0009, gegen eine beobachtete Spanne von 0,0204. **Bei n = 24 hat dieser
Test wenig Power** — daraus folgt der nächste Abschnitt.

## Dieselbe Frage innerhalb desselben Matchups

Die 24-Punkte-Korrelation vergleicht Bookmaker mit **verschiedenen
Match-Portfolios**. Mit Matchup-Fixed-Effects fällt die Zusammensetzung
heraus: verglichen werden nur Bookmaker, die dasselbe Spiel quotieren.
18.394 Matchups, 181.889 Kontrakte, SEs cluster-robust auf Matchup.
Quelle: `within_matchup_fe.csv`.

| Spezifikation | Koeffizient auf `OpnHrs` | SE | t | p |
|---|---:|---:|---:|---:|
| Matchup-FE | +1,172e−04 | 2,84e−05 | +4,12 | 0,00004 |
| Matchup-FE + Bookmaker-FE | +1,138e−04 | 3,05e−05 | +3,73 | 0,0002 |

**Der Mechanismus des Referees existiert und ist hoch signifikant.** Eine
Stunde früheres Posting erhöht den erwarteten quadrierten Fehler um
1,17e−04. Dass der Koeffizient die zusätzlichen Bookmaker-FE praktisch
unverändert übersteht, zeigt: der Effekt läuft über das **Timing der
einzelnen Serie**, nicht über eine feste Bookmaker-Eigenschaft.

### Die Größenordnung

Hochgerechnet auf die Spanne der Bookmaker-Mediane (19,46 h):
**+0,00228 im Brier, das sind ≈ +0,0025 im RMSE.** Die beobachtete Spanne
über die Bookmaker beträgt 0,0204 auf Panel- bzw. 0,0181 auf Serienebene.

**Timing erklärt also rund ein Achtel der RMSE-Unterschiede — real, aber
nicht der Haupttreiber.** Einschränkung: die Within-Matchup-Streuung von
`OpnHrs` beträgt sd 4,1 h, die Hochrechnung auf 19,5 h extrapoliert über
diesen Bereich hinaus und unterstellt Linearität.

## Zusammenfassung Teil 2

1. **R3-2 zu Pinnacle: widerlegt.** Pinnacle eröffnet median, nicht früh.
2. **Der Mechanismus als solcher: bestätigt.** Innerhalb desselben Matchups
   schneidet der früher postende Bookmaker signifikant schlechter ab.
3. **Die Größenordnung: klein.** ≈ 0,0025 RMSE gegen eine Spanne von 0,018.
4. **Über die Bookmaker aggregiert** ist der Zusammenhang auf Serienebene
   sichtbar (r = +0,41), nach Kontrolle für die Marge nur noch tendenziell
   (r = +0,33, p = 0,13), und in der **publizierten panelgewichteten Fassung
   gar nicht** — was ein Artefakt der Beobachtungsgewichtung ist.

---

# Neufassung von Figure 1

**Zwei getrennte Abbildungen**, beide im Paper-Stil über `PlotParams` und
`sns.set_theme(palette=stata_colors, style="ticks")`, beide auf
**Serienebene**, Beschriftung durchgehend englisch.

> **Die Grenze sqrt(E[p(1−p)]) wird in keiner der beiden Abbildungen
> gezeigt** (Entscheidung, siehe `revision_log.md`, R2-M7). Eine
> Referenzlinie, die von zwei Dritteln der Balken unterschritten wird, ist
> ohne die Erklärung „unterdisperse Preise senken die Grenze" irreführend —
> und die gehört in den Text. Die Zahlen stehen in `baselines.csv` zur
> Verfügung.

## A — `rmse_posting_bars.{png,pdf}`, Skript `_fig_bars.py`

Gruppierte Balken je Bookmaker, alphabetisch wie die publizierte Figur
(`Root Mean Squared Error`, Beschriftung um 90° gedreht, Boxrahmen):

- **Balken 1, linke Achse:** RMSE, Skala `[0,44; 0,47]` statt der
  publizierten `[0,39; 0,49]`; die Serienebenen-Werte liegen zwischen
  0,4465 und 0,4646.
- **Balken 2, rechte Achse:** medianer Posting-Zeitpunkt in Stunden vor
  Anpfiff, ab null.
- Zwei Farben aus `stata_colors` (`#1A476F`, `#E37E00`), Legende über dem
  Panel.

> **Bekannter Nachteil der gruppierten Fassung:** die RMSE-Achse ist
> abgeschnitten, die Stundenachse beginnt bei null. Zwei nebeneinander
> stehende Balken laden zu einem Höhenvergleich ein, der hier bedeutungslos
> ist. Bewusst in Kauf genommen — die Alternative (Posting Time als Punkte
> auf der rechten Achse) steht in `_fig_rmse_posting.py` als Farbcodierung
> zur Verfügung, falls die Entscheidung revidiert wird.

## B — `rmse_vs_posting_scatter.{png,pdf}`, Skript `_fig_scatter.py`

Scatter RMSE gegen medianen Posting-Zeitpunkt über die 24 Bookmaker mit
Regressionsgerade und den Korrelationen als Annotation (Pearson +0,409,
Spearman +0,470).

**Alle 24 Punkte sind beschriftet.** Die Platzierung nutzt kein `adjustText`,
sondern probiert je Punkt eine feste Kandidatenliste von Versätzen durch und
nimmt den ersten kollisionsfreien — deterministisch, ohne zusätzliche
Abhängigkeit. Reihenfolge: gedrängte Punkte zuerst, weil sie die wenigsten
freien Plätze haben. Im aktuellen Lauf reicht für **alle 24** der kleinste
Versatz (4 pt), Verbindungslinien werden nicht gebraucht; die Fallback-Logik
dafür bleibt für den Fall geänderter Daten im Skript.

## Superseded

- `fig_rmse_posting.{png,pdf}`, Skript `_fig_rmse_posting.py` — die frühere
  Zwei-Panel-Fassung. Ersetzt durch A und B, die Referenzlinie ist auch dort
  entfernt. Bleibt liegen, weil sie den Posting-Zeitpunkt als **Farbe im
  Balkenpanel** kodiert statt über eine zweite Achse; das ist die
  Rückfalloption, falls die zweite y-Achse in A stört.
- `rmse_posting_time.{png,pdf}`, Skript `_rmse_posting_plot.py` — das erste
  Diagnose-Bild mit deutscher Beschriftung. Zeigt die
  **bookmakerspezifische** Grenze je Bookmaker als Dumbbell und beide
  RMSE-Fassungen nebeneinander. Nicht für das Paper, aber nützlich, um die
  Gewichtungsfrage in der Antwort an die Referees zu belegen.

# Dateien

- `_rmse_baselines.py` — Frame-Bau, Baselines, Murphy-Zerlegung,
  Kalibrierungssteigungen, Prüfung des Papertextes
- `_posting_time.py` — Posting-Zeitpunkte, Korrelationen, partielle
  Betrachtung, Within-Matchup-FE
- `_fig_bars.py` — **Abbildung A**, gruppierte Balken mit zweiter y-Achse
- `_fig_scatter.py` — **Abbildung B**, Scatter mit beschrifteten Punkten
- `_fig_rmse_posting.py` — superseded, Zwei-Panel-Fassung mit Farbcodierung
- `_rmse_posting_plot.py` — superseded, erste Diagnose-Fassung
- `baselines.csv` — Brier, RMSE, BSS, Grenze, Abstand mit cluster-robustem
  Test, je für Opening/Closing und mit/ohne `|RtrnOpnCls| > 0`-Filter
- `opening_vs_closing.csv` — gepaarter Brier-Vergleich
- `murphy.csv` — REL/RES/UNC für 10/20/50 Bins, quantil und gleichbreit,
  inklusive Within-Bin-Rest
- `calibration_opening.csv`, `calibration_closing.csv` — Kalibrierungskurven
  (20 Quantilsbins)
- `calibration_slopes.csv` — Steigungen, Bin-Fassung und Kontraktebene
- `rmse_by_bookie_check.csv` — Figure-1-Größe, Serienebene und publizierter
  Wert je Bookmaker
- `posting_time_by_bookie.csv` — Posting-Zeitpunkte, Marge, beide
  RMSE-Fassungen, Updates je Serie
- `correlations.csv`, `partial_correlations.csv`, `joint_regression.csv`
- `within_matchup_fe.csv` — FE-Schätzungen mit cluster-robusten SEs
- `rmse_posting_bars.{png,pdf}`, `rmse_vs_posting_scatter.{png,pdf}`,
  `fig_rmse_posting.{png,pdf}`, `rmse_posting_time.{png,pdf}` — Abbildungen
  (**gitignoriert**, aus den Plotskripten regenerierbar)

**Cache:** die Skripte legen den Serien-Frame als Parquet im Scratchpad ab
(Pfadkonstante `FRAME` in `_rmse_baselines.py`). `_posting_time.py` und
`_rmse_posting_plot.py` lesen ihn nur; für einen Neubau die Datei löschen
oder `_rmse_baselines.py` zuerst laufen lassen.
