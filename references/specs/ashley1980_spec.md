# Spec: ashley1980 – Advertising and Aggregate Consumption: An Analysis of Causality

## Quelle
- Seiten/Abschnitt der Originalarbeit: Econometrica, Vol. 48, No. 5 (Juli 1980),
  S. 1149–1167 (Ashley, Granger, Schmalensee). Zentral für den AGS-Test:
  Section 2 "A Practical Test for Causality" (S. 1152–1155, Gleichungen 1–4).
- Zitiert in eigenem Paper: §3.4 "Relative Forecast Accuracy of Opening and
  Closing Prices" ("we use the AGS test as applied by \citet{gandar1998} and
  developed by \citet{ashley1980}").

Hinweis zur Extraktionsqualität: `pdftotext -layout` ergab für dieses PDF
(gescannter Altbestand, ähnlich hansen1982) stark verstümmelte mathematische
Notation (z.B. "At = elt-e2t" statt "Δt = e1t − e2t", "#1"/"#2" statt
β1/β2, "It"/"2" statt Σt). Ich habe mich daher NICHT auf die Text-Extraktion
verlassen, sondern die betroffenen Seiten (S. 1153–1154, PDF-Seiten 7–8) als
Bilder gerendert (150dpi PNG via pdftoppm) und die Gleichungen visuell aus dem
Original transkribiert.

## Methode/Modell

- Kausalitätsdefinition (Granger-Sinn, S. 1152): Y verursacht X, wenn
  MSE(X, Y) < MSE(X), wobei MSE(X) der mittlere quadratische
  Ein-Schritt-Prognosefehler von X_{t+1} basierend nur auf vergangenen
  X-Werten ist, und MSE(X,Y) der entsprechende Fehler unter zusätzlicher
  Verwendung vergangener Y-Werte.

- **Zerlegung der MSE-Differenz** (Gl. 1, S. 1154):
  ```
  MSE(e1) − MSE(e2) = [s²(e1) − s²(e2)] + [m(e1)² − m(e2)²]           (1)
  ```
  wobei e1t, e2t die Prognosefehler des univariaten bzw. bivariaten Modells
  für eine Out-of-Sample-Beobachtung t sind; s² = Stichprobenvarianz,
  m = Stichprobenmittelwert.

- **Definition von Δ und Σ** (Gl. 2, S. 1154):
  ```
  Δ_t = e1t − e2t,     Σ_t = e1t + e2t                                 (2)
  ```

- Umschreibung via Kovarianz (Gl. 3, S. 1154):
  ```
  MSE(e1) − MSE(e2) = [ĉov(Δ, Σ)] + [m(e1)² − m(e2)²]                  (3)
  ```

- **Die eigentliche AGS-Testregression (Gl. 4, S. 1154) – dies ist die
  Gleichung, die gandar1998/das eigene Paper übernehmen und erweitern**:
  ```
  Δ_t = β_1 + β_2 [Σ_t − m(Σ_t)] + u_t                                 (4)
  ```
  mit E[u_t] = 0. Getestet wird H0: β_1 = β_2 = 0 gegen die Alternative,
  dass beide Koeffizienten nichtnegativ und mindestens einer positiv ist.

- Entsprechung zur eigenen/gandar1998-Notation (nicht im Original, eigene
  Übersetzung zur Einordnung): e1t/e2t ↔ e_ij0/e_ijT (Prognosefehler
  Eröffnungs-/Schlusspreis), Δt ↔ Δ_ij, Σt ↔ Σ_ij, β1/β2 ↔ λ_0j/λ_1j (im
  eigenen Paper zusätzlich als Random Effects je Buchmacher spezifiziert
  und um einen Vektor fixer Effekte θX_ij erweitert – das ist die
  Erweiterung, die das eigene Paper selbst vornimmt, nicht Teil von Gl. 4
  im Original).

- Entscheidungsregel (S. 1154, Prosa, nicht als separate Gleichung
  nummeriert): ist eine der beiden KQ-Schätzungen β̂_1, β̂_2 signifikant
  negativ, gilt das bivariate Modell nicht als signifikante Verbesserung;
  ist eine negativ aber nicht signifikant, einseitiger t-Test auf die
  andere Schätzung; sind beide positiv, F-Test mit **halbiertem**
  Signifikanzniveau aus der F-Tabelle (da der Test "four-tailed" ist,
  Begründung in Fußnote-nahem Absatz S. 1154–1155).

- Fünf-Schritt-Verfahren zur Kausalitätsanalyse (S. 1153, Schritte i–v):
  (i) Prewhitening beider Serien via Box-Jenkins-ARIMA; (ii) Kreuzkorrelogramm
  der Residuen; (iii) bivariates Modell für die Residuen bei angezeigter
  Kausalität; (iv) Rücktransformation auf Originalserien; (v) Vergleich der
  Out-of-Sample-Ein-Schritt-Prognosefehler von univariatem vs. bivariatem
  Modell — **Schritt (v) ist der Ausgangspunkt für die Gleichungen (1)–(4)**.

## Schätzverfahren
- Verfahren: gewöhnliche KQ-Schätzung (OLS) von Gleichung (4); laut
  Fußnote 11 (S. 1153) wird OLS für alle bivariaten Modelle im Paper
  verwendet ("All estimation in this study is OLS"), mit dem Hinweis, dass
  GLS (seemingly-unrelated regressions) bei starker zeitgleicher Korrelation
  der Residuen bessere Ergebnisse liefern könnte.
- Hyperparameter/Tuning-Werte aus dem Original: keine allgemeingültigen
  (die Anwendung in Section 5 des Originals betrifft Werbe-/Konsumdaten,
  nicht auf die eigene Anwendung übertragbar).
- Instrumente/Moment-Bedingungen (falls GMM): nicht zutreffend – dies ist
  keine GMM-Schätzung, sondern eine OLS-Regression auf Prognosefehler-
  Transformationen.

## Erwartete Ergebnisse (falls im Original berichtet)
- Section 5 des Originals wendet den Test auf US-Werbeausgaben und
  Konsumdaten an (Ford-Motor-Company- bzw. Aggregatdaten). Diese
  Zahlenwerte sind inhaltlich nicht auf die Tennis-Wettquoten-Anwendung
  übertragbar und wurden hier nicht transkribiert, da sie keine Validierungs-
  grundlage für die eigene Implementierung bieten (andere Daten, anderer
  Kontext). Falls dennoch benötigt, siehe S. 1158–1164 des Originals
  (Section 5 "An Empirical Application").

## Unsicherheiten
- Gleichung (2) im Original zeigt in der gerenderten Abbildung eindeutig
  "Σ_t = e1t + e2t" (nicht "Σ_2", wie eine erste, nicht-visuelle
  Durchsicht vermuten ließ) – durch Seitenrendering zweifelsfrei bestätigt.
- Die Fußnote 13 (S. 1154) enthält eine zusätzliche Bias-Diskussion für
  β̂_2 (cov(Σ_t, u_t) = cov(Σ_t, Δ_t) − β_2 var(Σ_t)); diese wurde inhaltlich
  erfasst, aber nicht als eigene nummerierte Gleichung transkribiert, da sie
  im Original selbst keine Gleichungsnummer trägt und nicht Teil der
  Kern-Testgleichung ist.
- Der genaue F-Test-Mechanismus bei beidseitig positiven Koeffizienten
  (S. 1155, "iso-probability curves") wurde inhaltlich zusammengefasst,
  aber die geometrische Begründung nicht im Detail nachvollzogen/geprüft –
  für die reine Testanwendung (wie in gandar1998/eigenem Paper) vermutlich
  nicht kritisch, da dort primär auf t-Statistiken/Konfidenzintervalle für
  β_0 (Intercept) bzw. β_1 (Slope) abgestellt wird, nicht auf den
  kombinierten F-Test.
- Section 5 (empirische Anwendung) wurde nicht im Detail gelesen (siehe
  "Erwartete Ergebnisse") – falls dort weitere methodische Details zur
  praktischen Umsetzung von Gl. (4) stehen (z.B. Umgang mit negativen
  Fehlermittelwerten, im Haupttext als Sonderfall erwähnt: "Let us assume
  that both error means are positive; the modifications necessary in the
  other cases should become clear" S. 1154), wurden diese Modifikationen
  NICHT transkribiert, da im Original selbst nur als Prosa-Hinweis ohne
  explizite Formel gegeben ("should become clear" – keine Formel
  angegeben).

## Bezug zum eigenen Code
- Verwendet in: {Datei/Funktion, noch offen zu füllen}
- Unbestätigter Hinweis (nicht Teil der eigentlichen Spec-Prüfung):
  `src/pfd/helpers/fit_rfa_mod.py` ("Fit relative forecast accuracy model")
  scheint Gleichung (4) (erweitert um Random Effects und Kontrollvariablen)
  zu implementieren – nicht im Detail gegen die Vorzeichen-/Signifikanz-
  Entscheidungsregel oben geprüft, bitte separat verifizieren, insbesondere
  ob der eigene Code die Asymmetrie-Fallunterscheidung (beide negativ /
  eine negativ / beide positiv) überhaupt abbildet oder nur die generische
  Koeffizienten-Signifikanz auswertet.
