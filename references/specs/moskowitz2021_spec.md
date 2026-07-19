# Spec: moskowitz2021 – Asset Pricing and Sports Betting

## Quelle
- Seiten/Abschnitt der Originalarbeit: The Journal of Finance, Vol. 76, No. 6
  (Dezember 2021), S. 3153–3209 (Tobias J. Moskowitz). Zentral für die eigene
  Gleichung 1 (§3.3): Section I "Betting Market Efficiency" / Abschnitt kurz
  vor "Section III. Asset Pricing Tests", S. 3160–3162 (Herleitung von
  Prediction 1–3 und Gleichung (1)). Empirische Ergebnisse: Section III.A
  "Testing General Price Movements", Table II, S. 3172–3174.
- Zitiert in eigenem Paper: §3.3 "Price Movements on New Information"
  ("we adjust the linear regression proposed by \citet{moskowitz2021}...")
  und §5.2 "Price Movements on New Information" (Results-Abschnitt:
  "These results contradict those of \citet{moskowitz2021}, who identifies a
  tendency for overreactions in the market based on a different dataset
  covering various kinds of sports and betting contracts.")

Hinweis zur Extraktionsqualität: `pdftotext -layout` lieferte für dieses PDF
(digital erzeugt, kein Scan) durchgehend sauberen, eindeutig lesbaren Text
inklusive aller Formeln, Tabellenwerte und Fußnoten. Ein Rendern einzelner
Seiten als Bild (wie bei hansen1982) war NICHT nötig; alle Werte unten sind
direkt aus der Text-Extraktion übernommen und stichprobenartig gegen den
Fließtext um die jeweilige Stelle geprüft.

## Methode/Modell

- Identifikation der "eigenen Gleichung 1": Im Original ist dies **Gleichung
  (1)**, unmittelbar vor "PREDICTION 1" eingeführt (S. 3161) – die
  Nummerierung stimmt also direkt mit der Referenz im eigenen Paper überein,
  es gibt keine Verschiebung.

  ```
  R_{j,close:end} = α + β_1 R_{j,open:close} + ε_j                    (1)
  ```

  wobei R_{j,close:end} die Rendite vom Schluss- zum Endpreis (Ausgang der
  Wette) und R_{j,open:close} die Rendite vom Eröffnungs- zum Schlusspreis
  des Wettkontrakts j ist. α, β_1 sind zu schätzende Koeffizienten, ε_j der
  Störterm.

- Alternative Spezifikation (Fußnote 8, S. 3161, nicht Teil der eigenen
  Gleichung, aber im Original direkt verknüpft):
  ```
  R_{j,open:end} = α + β_0 R_{j,open:close} + ε_j,   mit β_0 = 1 + β_1
  ```
  getestet wird dort β_0 = 1.

- Bedeutung der Variablen: P_0 = Eröffnungspreis, P_1 = Schlusspreis,
  P_T = terminaler (Ausgangs-)Preis des Kontrakts. R_{open:close} =
  P_1/P_0 − 1 (analog zu pfd's r_{ijT}), R_{close:end} = P_T/P_1 − 1 (analog
  zu pfd's r_{ijω}). j indiziert einzelne Wettkontrakte.

- Drei Vorhersagen (S. 3161, wörtlich zentral, entsprechen 1:1 den drei
  Fällen in §3.3 des eigenen Papers):
  - PREDICTION 1: Wenn Preisbewegungen (P_0 ≠ P_1) auf Information beruhen
    und der Markt rational reagiert, dann β_1 = 0.
  - PREDICTION 2: Wenn Preisbewegungen (P_0 ≠ P_1) aus Nicht-Informations-
    Gründen (Sentiment/Rauschen) erfolgen, dann β_1 = −1.
  - PREDICTION 3: Wenn Preisbewegungen auf Information beruhen, der Markt
    aber irrational reagiert: (a) β_1 > 0 bei Unterreaktion; (b) β_1 < 0 bei
    Überreaktion.

- Annahmen: exogener, vom Marktgeschehen unabhängiger Terminalwert der
  Wettkontrakte (entscheidend für die Identifikation, im Gegensatz zu
  Finanzmarktanwendungen mit dem "joint hypothesis problem"); die Regression
  wird als gepoolte OLS-Regression über alle Kontrakte/Spiele geschätzt
  (im Original OHNE Random Effects je Buchmacher – das ist genau die
  Erweiterung, die das eigene Paper vornimmt: "we adjust the linear
  regression proposed by moskowitz2021 by incorporating bookmaker random
  effects").

## Schätzverfahren
- Verfahren: gepoolte OLS-Regression (Equation 1), Standardfehler/
  t-Statistiken geclustert auf Spielebene ("game level", siehe Tabellennotiz
  zu Table II).
- Hyperparameter/Tuning-Werte aus dem Original: keine (einfache OLS,
  Cluster-Robustheit auf Spielebene ist die einzige "Einstellung").
- Instrumente/Moment-Bedingungen (falls GMM): nicht zutreffend – dies ist
  keine GMM-Schätzung, sondern OLS.

## Erwartete Ergebnisse (falls im Original berichtet)

**Table II, Panel A ("Full Sample"), Zeile "All Sports"** (S. 3173) –
Koeffizient β_1 und t-Statistik (in Klammern; **keine** Standardfehler direkt
angegeben, siehe Unsicherheiten) je Kontrakttyp:

| Kontrakttyp   | β_1    | t-Statistik |
|---------------|--------|-------------|
| Point Spread  | −0.51  | −29.32      |
| Moneyline     | −0.68  | −4.17       |
| Over/Under    | −0.51  | −28.55      |

Für pfd (binäre Sieg/Niederlage-Wette auf Tennis) ist der **Moneyline**-Wert
(β_1 = −0.68, t = −4.17) der inhaltlich am ehesten vergleichbare Referenzwert.

Nach Sportart (Panel A, jeweils β_1 mit t-Statistik in Klammern):

| Sportart | Point Spread   | Moneyline      | Over/Under     |
|----------|----------------|----------------|----------------|
| NBA      | −0.51 (−20.36) | −1.28 (−4.97)  | −0.51 (−20.21) |
| NFL      | −0.47 (−8.66)  | −0.09 (−0.21)  | −0.50 (−9.08)  |
| MLB      | —              | −0.11 (−1.34)  | −0.52 (−16.14) |
| NHL      | —              | −0.15 (−1.20)  | −0.70 (−5.77)  |

(MLB und NHL haben laut Table I keine Point-Spread-Kontrakte, da diese dort
konstant bei ±1.5 quotiert sind.)

Panel B (S. 3173, Subsample nur Kontrakte mit tatsächlicher Preisbewegung,
"All Sports"): Point Spread β_1 = −0.50 (t = −29.61), Moneyline β_1 = −0.68
(t = −4.16), O/U β_1 = −0.51 (t = −28.61) – nahezu identisch zu Panel A.

**Interpretation im Original**: Die Koeffizienten sind durchgängig
signifikant negativ und signifikant verschieden von 0 UND von −1 →
Ablehnung von Prediction 1 (rational) und Prediction 2 (reines Rauschen);
konsistent mit Prediction 3b (Überreaktion). Die Größenordnung von ca.
−0.50 wird interpretiert als: "about half of the total price movement from
open-to-close is reversed at game outcome."

**Stichprobengröße**: Gesamtdatensatz laut Table I: **117.442
Wettkontrakte auf 59.592 Spiele** (NBA 1999–2013: 18.681 Spiele / 38.939
Kontrakte; NFL 1985–2013: 7.035 Spiele / 10.775 Kontrakte; MLB 2005–2013:
23.986 Spiele / 47.964 Kontrakte; NHL 2005–2013: 9.890 Spiele / 19.764
Kontrakte). Die exakte Fallzahl je Zelle von Table II (z.B. nur
Moneyline-Kontrakte, "All Sports") wird in der extrahierten Tabelle NICHT
separat berichtet (siehe Unsicherheiten).

**R²**: in Table II nicht berichtet (nur β_1 und t-Statistik je Zelle).

## Unsicherheiten
- Table II berichtet **t-Statistiken in Klammern, keine Standardfehler**.
  Ich habe die Standardfehler NICHT selbst durch SE = β_1 / t zurückgerechnet,
  um keine Werte zu erzeugen, die im Original nicht explizit stehen –
  falls für die eigene Validierung benötigt, müssten diese bei Bedarf
  gesondert (und als abgeleitet gekennzeichnet) berechnet werden.
- Die exakte Fallzahl (N) je einzelner Regressionszelle in Table II (z.B.
  "Moneyline, All Sports") ist in der extrahierten Tabelle nicht angegeben;
  nur die Gesamtstichprobe (Table I: 117.442 Kontrakte / 59.592 Spiele) und
  die Kontraktzahlen je Sportart/Panel sind bekannt. Eine Aufteilung nach
  Kontrakttyp (Point Spread vs. Moneyline vs. O/U) innerhalb der
  Sport-Panels wird in Table I nicht separat ausgewiesen.
- Panels C und D von Table II (Betting-Volumen bzw. "Big Interest Games")
  wurden der Vollständigkeit halber gesichtet, aber hier nicht transkribiert,
  da sie robustheitsprüfende Zusatzanalysen sind und nicht direkt Gleichung
  (1) im Kernsinn betreffen; bei Bedarf nachzuliefern.
- Ich habe die Tabellen-Fußnote zu Table II vollständig gelesen (Clustering
  auf Spielebene, Behandlung von Point Spread/O/U nur für eine Marktseite
  wegen Symmetrie, Moneyline für beide Seiten wegen Asymmetrie) – diese
  methodischen Detailanmerkungen sind oben in "Schätzverfahren" nur knapp
  zusammengefasst, nicht wörtlich vollständig übernommen.

## Bezug zum eigenen Code
- Verwendet in: {Datei/Funktion, noch offen zu füllen}
- Unbestätigter Hinweis (nicht Teil der eigentlichen Spec-Prüfung): die
  eigene Gleichung (resp_to_info) in §3.3 des eigenen Papers und die Funktion
  `fit_gpm_mod` (`src/pfd/helpers/fit_gpm_mod.py`, "Fit general price
  movements model") scheinen diese Regression (mit Bookmaker-Random-Effects
  erweitert) zu implementieren – nicht im Detail gegen Gleichung (1) geprüft,
  bitte separat verifizieren, insbesondere ob die Ergebnis-Diskussion in
  §5.2 des eigenen Papers ("results contradict moskowitz2021") korrekt an
  Table II gespiegelt ist (eigenes ν_1-Konfidenzintervall −0.015 bis 0.061,
  vs. hier β_1 = −0.68 (Moneyline) bzw. −0.51 (Point Spread/O/U), beide
  klar von 0 verschieden).
