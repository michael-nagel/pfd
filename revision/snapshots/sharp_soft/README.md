# Sharp/Soft-Klassifikation und Robustheit (R1-iv, berührt R2-M3)

Rein diagnostisch, **kein Eingriff in die Produktions-Pipeline**.
Basis: normalisiert, 24 Bookmaker, 184.415 Serien (Margen) bzw. der
Unbiasedness-Frame mit 175.166 Serien (beta_1-Kurve).

## Richtigstellung vorab: Betfair ist hier das Sportsbook

Der Referee nimmt an, Betfair stehe für einen Exchange-Markt. In diesen Daten
ist es das **Sportsbook**, und die Marge bestätigt das: Median **7,47 %**
über alle Beobachtungen, **7,80 %** beim Opening — **Rang 14 von 24**, oberes
Mittelfeld. Ein Exchange läge bei einer effektiven Marge von rund 1–2 % und
damit weit unter Pinnacle. Das ist eine Klarstellung, kein Fall für die
Robustheitsanalyse.

## 1) Klassifikationsproxy: Median-Marge je Bookmaker

Quelle: `margin_by_bookie.csv`. Zwei Definitionen, weil beide Zahlen im
Umlauf sind: über alle Beobachtungen und nur am Opening.

| Bookmaker | Marge (alle) | Marge (Opening) | Serien | Anteil |
|---|---:|---:|---:|---:|
| **Pinnacle** | **4,62 %** | **4,90 %** | 8.657 | 4,69 % |
| **BetInAsia** | **4,78 %** | **5,11 %** | 6.373 | 3,46 % |
| BetVictor | 5,56 % | 6,17 % | 5.618 | 3,05 % |
| Betfred | 5,81 % | 5,71 % | 4.872 | 2,64 % |
| 10Bet | 5,96 % | 6,41 % | 5.572 | 3,02 % |
| … | | | | |
| Betfair | 7,47 % | 7,80 % | 3.548 | 1,92 % |
| … | | | | |
| Interwetten | **8,28 %** | **8,33 %** | 5.705 | 3,09 % |

Spanne 4,62 % bis 8,28 % über alle Beobachtungen, 4,90 % bis 8,33 % am
Opening. **Die in `open_questions.md` notierten 4,90 % / 8,33 % sind die
Opening-Werte** — beide Zahlenpaare stimmen, sie messen nur Verschiedenes.

## 2) Wie viele der 24 gelten in der Literatur als sharp?

**Zwei.** Pinnacle ist der Standardfall (niedrige Marge, hohe Limits, nimmt
Gewinner an); BetInAsia ist ein Broker, der Zugang zu asiatischen
Sharp-Märkten vermittelt. Beide stehen auch in unseren Daten an der Spitze
der Margenrangfolge — die externe Klassifikation und der interne Proxy
stimmen also überein. Betfair wäre der dritte Fall, aber nur als Exchange,
und das ist es hier nicht. Alle übrigen 21 sind retailorientierte
Sportsbooks.

Zusammen tragen Pinnacle und BetInAsia **8,15 % der Serien**, die vier
margenärmsten Häuser **13,84 %**.

## 3) Robustheit der beiden Kernbefunde

**Der Ausschluss ist beim GMM gratis.** `gamma` wird je Bookmaker geschätzt
(`fit_gmm_mod.py:47`), der Ausschluss betrifft also nur die Aggregation.
Quelle: `gmm_without_sharp.csv`, Basis `E_gmm_exponent_fix/gmm_by_bookie.csv`.

| Variante | n | gamma Mittel | Spanne | Argmin/Argmax |
|---|---:|---:|---|---|
| volles Sample | 24 | **0,00540** | 0,00138–0,01240 | GGBET / Dafabet |
| ohne 2 margenärmste | 22 | **0,00571** | unverändert | unverändert |
| ohne 4 margenärmste | 20 | **0,00589** | unverändert | unverändert |

Die mittlere Lernrate steigt leicht (+6 % bzw. +9 %), was zu erwarten ist:
Pinnacle (0,0020) und BetInAsia (0,0018) liegen im unteren Drittel. Die
Extremwerte und ihre Träger bleiben identisch.

**Die beta_1-Kurve muss neu geschätzt werden.** `ns(df = 4)`, CR1 auf
Matchup, ohne Random Effects — dieselbe Spezifikation wie in der Antwort zu
Comment 7. Quelle: `beta1_without_sharp.csv`.

| Stunden vor Anpfiff | voll | ohne 2 | Δ | ohne 4 | Δ | SE (voll) |
|---|---:|---:|---:|---:|---:|---:|
| 24 | 1,1733 | 1,1844 | +0,0111 | 1,1752 | +0,0020 | 0,1194 |
| 12 | 1,0793 | 1,1035 | +0,0242 | 1,0958 | +0,0166 | 0,0920 |
| 6 | 0,9301 | 0,9588 | +0,0287 | 0,9506 | +0,0206 | 0,0984 |
| 3 | 0,8446 | 0,8788 | +0,0342 | 0,8774 | +0,0328 | 0,0899 |
| 1 | 0,7773 | 0,8177 | +0,0404 | 0,8213 | +0,0440 | 0,0978 |
| 0,25 | 0,7700 | 0,8139 | +0,0439 | 0,8093 | +0,0393 | 0,0958 |

**Grösste Abweichung 0,044 = 0,46 Standardfehler.** Form, Niveau und der
Durchgang durch 1 bleiben erhalten.

> **Validierung nebenbei:** die Spalte „voll" reproduziert die in der
> R1-vii-Antwort berichtete Kurve (1,173 bei 24 h, 0,770 bei 0,25 h) auf vier
> Nachkommastellen, obwohl hier OLS + CR1 statt lme4 mit Bookmaker-RE
> gerechnet wird. Das bestätigt zugleich den Gate-Befund aus R1-ii.

## 4) Das Argument, das die Analyse überflüssig macht, wo sie überflüssig ist

Aus `cluster_inference_eq12/README.md` und `eq3_contract_level/README.md`:

| Gleichung | Bookmaker-Heterogenität | Wald-Test |
|---|---|---|
| Eq. 1 (Table 3) | keine | chi2(23) = 24,46, **p = 0,379** (Steigungen); gemeinsam p = 0,127 |
| Eq. 3 (Kontraktebene) | keine | chi2(23) = 20,78, **p = 0,595** |
| Eq. 2 (Table 4/7) | **real und stark** | chi2(46) = 507,7, p < 0,0001 |

**Wo sich die Bookmaker nachweislich nicht unterscheiden, ist eine
Sharp/Soft-Trennung gegenstandslos.** Der Einwand des Referees betrifft
damit nur die Grössen mit echter Heterogenität — die Lernraten und Eq. 2 —
und genau dort liegt die Robustheitsprüfung aus Abschnitt 3.

## Nicht verwendet: Opening-Zeitpunkt als Kriterium

Die Klassifikation über den Eröffnungszeitpunkt würde falsch klassifizieren.
Pinnacle liegt beim Median-Opening bei **20,63 h** gegen einen
Stichprobenmedian von **20,45 h** — Rang 12 von 24, also exakt Mittelfeld
(Quelle: `rmse_baselines/posting_time_by_bookie.csv`, R2-M7/R3-2). Die
frühesten Eröffner sind klassische Soft-Bookies.

## Dateien

- `_sharp_soft.py` — Margen, GMM-Aggregation, beta_1-Kurve je Variante
- `margin_by_bookie.csv` — Median-Marge je Bookmaker, beide Definitionen
- `gmm_without_sharp.csv` — Lernrate voll / ohne 2 / ohne 4
- `beta1_without_sharp.csv` — Koeffizientenpfad je Variante mit SE
