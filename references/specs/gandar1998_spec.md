# Spec: gandar1998 – Informed Traders and Price Variations in the Betting Market for Professional Basketball Games

## Quelle
- Seiten/Abschnitt der Originalarbeit: The Journal of Finance, Vol. 53,
  No. 1 (Februar 1998), S. 385–401 (Gandar, Dare, Brown, Zuber). Zentral:
  Section II "Relative Forecast Accuracy of Opening and Closing Lines"
  (S. 391–393, AGS-Testanwendung, Gl. 1, Table III); Section III.A–C
  (S. 393–398, Richtung/Magnitude von Line Changes, Table IV, Gl. 2–4,
  Table-Regressionen).
- Zitiert in eigenem Paper: §3.2 "Price Change Mechanisms" ("Price
  movements... convert bookmakers' forecasts... \citep{gandar1998}"; "three
  explanations for betting imbalances... \citet{gandar1998}"), §3.4
  "Relative Forecast Accuracy" ("the AGS test as applied by
  \citet{gandar1998}"), §3.5 "Magnitude and Direction of Price Movements"
  ("regressing the winning rates on the intervals' average price change
  magnitudes \citep{gandar1998}").

Hinweis zur Extraktionsqualität: `pdftotext -layout` lieferte für dieses
PDF einen systematisch, aber konsistent verzerrten Zeichensatz (scanbasiert;
z.B. "5" statt "=", "2" statt "−", "~...!" statt "(...)", "@...#" statt
"[...]"). Diese Verzerrung ist ein durchgängiges, dekodierbares Muster
(keine zufällige Verstümmelung), das ich anhand des Kontexts mehrfach
kreuzgeprüft habe. Zur zusätzlichen Absicherung habe ich die Seite mit den
zentralen Gleichungen (2)–(4) (S. 397, PDF-Seite 13) als Bild gerendert und
visuell bestätigt – dabei eine Korrektur gegenüber der Text-Extraktion
festgestellt: die Kovarianzmatrix in Fußnote 12 heißt **Ω(N)**, nicht
"V(N)" (wie die Text-Extraktion nahelegte).

## Methode/Modell

- **AGS-Testgleichung, angewandt auf Point-Spread-Vorhersagefehler
  (Gl. 1, S. 391)**:
  ```
  (FEO − FEC) = a + b[(FEO + FEC) − (MFEO + MFEC)] + m                (1)
  ```
  FEO/FEC = individuelle Vorhersagefehler der Opening-/Closing-Line;
  MFEO/MFEC = deren Mittelwerte; m = Fehlerterm. Dies ist die direkte
  Anwendung von ashley1980's Gleichung (4) (siehe ashley1980_spec.md) auf
  Wettlinien-Vorhersagefehler – identische Struktur, andere Variablennamen
  (FEO/FEC statt e1t/e2t).
  - Nullhypothese: a = b = 0 (kein Unterschied in MSFE zwischen Opening-
    und Closing-Line). Alternative: MSFEO > MSFEC (bzw. <) erfordert
    beide Koeffizienten nichtnegativ (bzw. nichtpositiv) und mindestens
    einen strikt positiv (negativ).
  - t-Statistik auf â testet Unterschiede in mittleren absoluten
    Vorhersagefehlern; t-Statistik auf b̂ testet Unterschiede in den
    Vorhersagefehler-**Varianzen**.

- **Gewinnanteils-Regression (Gl. 2, S. 397) – dies ist die im eigenen
  Paper referenzierte "regressing the winning rates on ... average price
  change magnitudes"-Quelle**:
  ```
  WPO_ΔL = α + β ΔL + ε                                                (2)
  ```
  WPO_ΔL = tatsächlicher Gewinnanteil des Heimteams bei Opening-Lines für
  jede Line-Change-Magnitude ΔL; ε = Fehlerterm. Unter der
  "Noise-Trading"-Nullhypothese: [α, β] = [0.5, 0]. Bei informierten
  Bettern: β > 0.
  - Analog für Closing-Lines (WPC_ΔL ersetzt WPO_ΔL): unter der
    "Informed-Trading"-Nullhypothese ebenfalls [α, β] = [0.5, 0].

- Bedeutung: DL/ΔL = Line-Change-Magnitude = CL − OL (Closing minus
  Opening Line), aus Sicht des Heimteams.

## Schätzverfahren

- AGS-Test (Gl. 1): OLS-Schätzung von a, b auf individuellen
  Spiel-Vorhersagefehlern.
- Gewinnanteils-Regression (Gl. 2): **Weighted Least Squares (WLS)** über
  die 26 individuellen Line-Change-Magnituden-Bins, NICHT auf
  Einzelspiel-Ebene. Gewichtung explizit angegeben (Fußnote 12, S. 397,
  visuell bestätigt):
  ```
  Ω(N)_jj = σ² / n_j
  ```
  wobei n_j die Anzahl der Line Changes bei Magnitude ΔL_j ist (Begründung:
  Varianz der abhängigen Variable WPO_ΔL/WPC_ΔL ist umgekehrt proportional
  zur Beobachtungszahl je Bin).
- Hyperparameter/Tuning-Werte: keine im üblichen Sinn – WLS-Gewichte sind
  datengetrieben (aus n_j), keine frei wählbaren Tuning-Parameter.
- Instrumente/Moment-Bedingungen (falls GMM): nicht zutreffend – OLS/WLS,
  keine GMM-Schätzung.

## Erwartete Ergebnisse (falls im Original berichtet)

**Table III (S. 392) – AGS-Test auf Point-Spread-Vorhersagefehler, gepoolt
über alle 9 Saisons ("All seasons", N = 7,904 Spiele mit Line-Änderung)**:

| | MAFEO | MAFEC | MSFEO | MSFEC | â (p-Wert) | b̂ (p-Wert) |
|---|---|---|---|---|---|---|
| All seasons | 9.00 | 8.92 | 133.29 | 131.39 | 0.006 (0.663) | 0.004 (0.000) |

Interpretation: MSFEC signifikant kleiner als MSFEO für die Gesamtstich-
probe und 7 von 9 Einzelsaisons; b̂ signifikant positiv (p<0.01) → Closing
Lines sind statistisch genauere Vorhersagen als Opening Lines.

**Gleichungen (3)/(4), S. 397 (WLS über 26 Line-Change-Bins)**:
```
WPO_ΔL = 0.50 + 0.04 ΔL,   p-Werte: (0.77) für α̂, (0.00) für β̂        (3)
WPC_ΔL = 0.50 + 0.00 ΔL,   p-Werte: (0.71) für α̂, (0.52) für β̂        (4)
```
Zugehörige F-Tests (S. 397–398, Prosa): Noise-Trading-Nullhypothese bei
Opening Lines dezidiert verworfen (F = 49.89, p < 0.01); Informed-Trading-
Nullhypothese bei Closing Lines NICHT verworfen (F = 0.28, p = 0.76).
Bei Einzelsaison-Regressionen: Noise-Trading-Nullhypothese bei Opening
Lines für 8 von 9 Saisons auf 10 %-Niveau verworfen (6 von 9 auf
5 %-Niveau); Informed-Trading-Nullhypothese bei Closing Lines nur für 1
von 9 Saisons verworfen (p = 0.09).

**Table IV (S. 395) – Gewinnanteile nach Line-Change-Magnitude (Auszug,
Heimteam "beats" Opening/Closing Line)**:

| ΔL | N | Anteil (OL) | Z (OL) | p (OL) | Anteil (CL) | Z (CL) | p (CL) |
|---|---|---|---|---|---|---|---|
| ≤ −4.0 | 28 | 0.25 | −2.65 | 0.008 | 0.46 | −0.38 | 0.70 |
| −1.0 | 1212 | 0.47 | −2.27 | 0.02 | 0.51 | 0.50 | 0.62 |
| 0.0 | 2036 | 0.51 | 1.04 | 0.30 | 0.51 | 1.04 | 0.30 |
| +1.0 | 1202 | 0.53 | 1.81 | 0.07 | 0.49 | −0.50 | 0.62 |
| ≥ +4.0 | 19 | 0.74 | 2.06 | 0.04 | 0.58 | 0.69 | 0.49 |

(vollständige Tabelle hat 17 Zeilen von ΔL ≤ −4.0 bis ΔL ≥ +4.0; hier nur
Auszug transkribiert, siehe Unsicherheiten). Aggregiert (Prosa, S. 395):
3,996 positive Line-Change-Spiele → Gewinnanteil OL ≈ 0.54 (Z = 4.68,
p < 0.01); 3,908 negative Line-Change-Spiele → Gewinnanteil OL ≈ 0.45
(Z = −5.85, p < 0.01); 2,036 No-Change-Spiele → Anteil 0.51 (Z = 1.04,
p = 0.30, nicht signifikant von 0.5 verschieden).

## Unsicherheiten
- Table IV wurde nur auszugsweise (5 von 17 Zeilen) transkribiert, um den
  Umfang zu begrenzen – die vollständige Tabelle enthält Zeilen für
  ΔL = −4.0, −3.5, −3.0, −2.5, −2.0, −1.5, −1.0, −0.5, 0.0, +0.5, +1.0,
  +1.5, +2.0, +2.5, +3.0, +3.5, ≥+4.0 (17 Zeilen à N, Proportion, Z, p für
  OL und CL). Bei Bedarf für eine vollständige Validierung müsste die
  komplette Tabelle nachtranskribiert werden (Quelle: S. 395 des Originals,
  per Text-Extraktion bereits vollständig, aber hier nicht ins Dokument
  übernommen).
- Section "C.2. Tests Based on Forecast Errors" (Brown-und-Sauer-basierte
  "pure noise"/"pure fundamentals"-Tests) wurde gelesen, aber nicht in
  "Methode/Modell" übernommen, da sie nicht die im eigenen Paper zitierte
  Methodik ist (das eigene Paper bezieht sich nur auf die AGS-Test- und
  Gewinnanteils-Regressions-Teile von gandar1998, nicht auf die
  Brown/Sauer-Erweiterung) – nur der Vollständigkeit halber hier erwähnt.
- Ich habe NICHT geprüft, ob gandar1998 selbst eine Version der
  Gewinnanteils-Regression mit Kontrolle für die Anzahl der Line Changes
  je Bin (analog zum κC-Term im eigenen Paper, "controlling for the number
  of price changes") enthält – im gelesenen Abschnitt (Gl. 2–4) taucht nur
  ΔL als Regressor auf, kein zusätzlicher Kontrollterm. Der κC-Term im
  eigenen Paper dürfte daher eine eigene Erweiterung sein, nicht aus
  gandar1998 übernommen – dies sollte bei Bedarf im eigenen Paper klar
  gekennzeichnet werden (nicht Teil dieser Spec-Prüfung selbst, da es
  keine Aussage über gandar1998 ist, sondern über das eigene Paper).

## Bezug zum eigenen Code
- Verwendet in: {Datei/Funktion, noch offen zu füllen}
- Unbestätigter Hinweis (nicht Teil der eigentlichen Spec-Prüfung):
  `src/pfd/helpers/fit_rfa_mod.py` (AGS-Test, Gl. 1 erweitert) und
  `src/pfd/utils/calc_win_props.py` bzw. die Regression in
  `src/pfd/models/winning_proportions.py` (Gewinnanteils-Regression, Gl. 2)
  scheinen diese beiden Verfahren zu implementieren. Auffällig: das
  eigene Paper verwendet für die Gewinnanteils-Regression laut Code
  (`smf.mixedlm(...)` in `winning_proportions.py`) ein **Mixed-Effects-
  Modell mit Bootstrap-Standardfehlern**, nicht die **WLS**-Schätzung mit
  Ω(N)-Gewichtung, die gandar1998 im Original verwendet (Gl. 2–4,
  Fußnote 12). Dies ist wahrscheinlich eine bewusste methodische
  Erweiterung des eigenen Papers (Bookmaker-Random-Effects statt einer
  gepoolten WLS-Regression über alle Bookmaker hinweg), aber keine direkte
  Übernahme des gandar1998-Schätzverfahrens – sollte ggf. explizit im
  eigenen Paper als Erweiterung benannt werden, ist aber keine
  offensichtliche Unstimmigkeit (das eigene Paper sagt bereits "We use a
  random effects model to incorporate bookmaker-specific effects", was
  bewusst über gandar1998 hinausgeht). Kein Eintrag in open_questions.md,
  da dies eher eine explizit angekündigte Erweiterung als ein
  unbemerkter Widerspruch ist.
