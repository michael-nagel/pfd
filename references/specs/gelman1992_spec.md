# Spec: gelman1992 – A Single Series from the Gibbs Sampler Provides a False Sense of Security

## Quelle
- Seiten/Abschnitt der Originalarbeit: Bayesian Statistics 4 (1992),
  S. 625–631 (Gelman, Rubin) – hier anhand des als Technical Report
  No. 305 / Valencia-Konferenzbeitrags (Berkeley/Harvard, 1991) vorliegenden
  PDFs geprüft (Titel im Dokument identisch mit dem Bib-Eintrag: "A Single
  Series from the Gibbs Sampler Provides a False Sense of Security").
  Zentral: Section 6 "Using components of variance from multiple
  sequences" (S. 9–10 des PDFs, sechsstufiges Verfahren inkl.
  potenzieller Skalenreduktion √R̂).
- Zitiert in eigenem Paper: Appendix "Bayesian Estimation – Algorithms and
  Procedures" ("we use the Gelman-Rubin statistic R̂ \citep{gelman1992,
  brooks1998} and dispay trace plots for the individual chains").

Hinweis zur Extraktionsqualität: `pdftotext -layout` lieferte für dieses
PDF (gescanntes Technical Report/Konferenzpapier, ähnlich hansen1982) für
die zentralen Formeln (Varianzkomponenten, Freiheitsgrade, √R̂) stark
verstümmelte Notation (z.B. "s?" statt s_i², "62" statt σ̂², "VR" statt
√R̂, Sub-/Superskripte durcheinander). Ich habe daher die betroffenen
Seiten (S. 9–10 des PDFs, PDF-Seiten 10–11) als Bilder gerendert und alle
Formeln unten visuell aus dem Original transkribiert.

## Methode/Modell

Sechsstufiges Verfahren (Section 6, wörtlich zentral):

1. Simuliere unabhängig m ≥ 2 Sequenzen der Länge 2n, mit Startpunkten aus
   einer gegenüber der Zielverteilung überdispergierten Verteilung. Verwerfe
   die ersten n Iterationen jeder Sequenz (Burn-in), betrachte nur die
   letzten n.

2. Für jede skalare Zielgröße X: berechne je Sequenz i=1,…,m Stichproben-
   mittel und -varianz:
   ```
   x̄_{i.} = (1/n) Σ_j x_{ij},     s_i² = (1/(n−1)) Σ_j (x_{ij} − x̄_{i.})²
   ```
   Varianzkomponenten:
   ```
   W = Mittelwert der m Innerhalb-Sequenz-Varianzen s_i² (je n−1 Freiheitsgrade)
   B/n = Varianz zwischen den m Sequenzmitteln x̄_{i.} (je n Werte von X)
   ```
   Ist W nicht wesentlich größer als B/n, sind die Sequenzen noch nicht
   nahe an einer gemeinsamen Verteilung konvergiert.

3. Schätze den Zielmittelwert μ = ∫XP(X)dX durch:
   ```
   μ̂ = (1/m) Σ_i x̄_{i.}
   ```

4. Schätze die Zielvarianz σ² = ∫(X−μ)²P(X)dX als gewichteten Durchschnitt
   von W und B:
   ```
   σ̂² = ((n−1)/n) W + (1/n) B
   ```
   (überschätzt σ², solange die Startverteilung P₀(X) überdispergiert ist;
   unverzerrt unter Stationarität bzw. im Limes n→∞).

5. Konstruiere eine konservative Student-t-Verteilung für X mit Zentrum μ̂,
   Skala und Freiheitsgraden:
   ```
   √V̂ = √(σ̂² + B/(mn))
   ν = 2V̂² / var(V̂)
   ```
   wobei
   ```
   var(V̂) = ((n−1)/n)² (1/m) var(s_i²)
           + ((m+1)/(mn))² (2/(m−1)) B²
           + 2 ((m−1)(n−1)/(mn²)) · (n/m) [cov(s_i², x̄_{i.}²) − 2x̄.. cov(s_i², x̄_{i.})]
   ```
   (Varianzen/Kovarianzen werden aus den m Stichprobenwerten von s_i²,
   x̄_{i.} und x̄_{i.}² geschätzt; x̄.. = Gesamtmittel).

6. **Potenzielle Skalenreduktion (die zentrale, im eigenen Paper zitierte
   Größe R̂)**:
   ```
   √R̂ = √[ (V̂/W) · (ν/(ν−2)) ]
   ```
   fällt mit n→∞ gegen 1.

- Bedeutung der Variablen: X = univariate (skalare) Zielgröße von
  Interesse (im eigenen Paper z.B. ein einzelner Modellparameter wie γ
  oder mean_gamma); m = Anzahl paralleler Ketten/Sequenzen; n = Anzahl
  Iterationen je Kette nach Burn-in; W = mittlere Varianz innerhalb der
  Ketten; B = Varianz zwischen den Kettenmitteln (× n).

- Annahmen: überdispergierte Startverteilung relativ zur Zielverteilung
  (analog zu Importance Sampling); univariate Zielgröße X (dies ist DIE
  univariate Variante – siehe brooks1998_spec.md für die multivariate
  Erweiterung).

## Schätzverfahren
- Verfahren: Varianzkomponentenanalyse aus m parallelen MCMC-Ketten,
  Momentenschätzer für Mittelwert, Varianz und Freiheitsgrade einer
  Student-t-Approximation der Zielgröße.
- Hyperparameter/Tuning-Werte aus dem Original: keine festen Zahlenwerte
  (m, n sind vom Anwender zu wählen, keine empfohlenen Defaults im
  gelesenen Abschnitt angegeben).
- Instrumente/Moment-Bedingungen (falls GMM): nicht zutreffend.

## Erwartete Ergebnisse (falls im Original berichtet)
- Das Paper illustriert die Methode anhand eines Ising-Modell-Beispiels
  (Section 4, Figuren 1–3, Gibbs-Sampler in einem zweikammerigen Raum),
  bei dem eine einzelne Kette fälschlich Konvergenz suggeriert. Konkrete
  numerische R̂-Werte für dieses Beispiel wurden nicht transkribiert, da
  sie sich auf ein Ising-Modell beziehen, nicht auf die eigene Anwendung,
  und der Fokus des Auftrags auf der Methodendefinition selbst lag. Bei
  Bedarf: Section 4 des Originals (vor Section 5 "Discussion").

## Unsicherheiten
- Das Paper selbst verweist mehrfach auf "Gelman and Rubin (1991)" für
  Details und ein Rechenprogramm – dies ist vermutlich ein Verweis auf die
  ausführlichere Fassung (später veröffentlicht als Gelman and Rubin,
  1992, "Inference from Iterative Simulation Using Multiple Sequences",
  Statistical Science). Ich habe NICHT geprüft, ob diese ausführlichere
  Fassung dieselben Formeln enthält oder ob sich Notation/Koeffizienten
  dort unterscheiden – falls das eigene Paper tatsächlich diese andere
  (nicht in `references/literature/` vorliegende) Arbeit meint, wäre dies
  gesondert zu prüfen. Der Bib-Eintrag `gelman1992` in `citation_map.md`
  verweist jedoch eindeutig auf den hier geprüften, kürzeren Valencia-
  Konferenzbeitrag (Titel identisch).
- Section 4 (Ising-Modell-Beispiel, Herleitung der Notwendigkeit multipler
  Ketten) wurde nicht im Detail gelesen/transkribiert – nur Section 5
  (Discussion) und Section 6 (die eigentliche Methode) waren Gegenstand
  dieser Spec, da nur diese für die R̂-Definition selbst relevant sind.
- Ich habe nicht geprüft, ob "ν" (Freiheitsgrade) in der Formel für √R̂
  im eigenen Code exakt so (mit dem ν/(ν−2)-Korrekturfaktor) oder in einer
  vereinfachten Form (z.B. ohne den t-Verteilungs-Korrekturfaktor, wie in
  manchen späteren Implementierungen wie z.B. PyMC/ArviZ üblich) berechnet
  wird – siehe "Bezug zum eigenen Code".

## Nachtrag (beim Erstellen von brooks1998_spec.md festgestellt)

**Wichtig:** Beim Lesen von brooks1998 (Brooks and Gelman 1998, S. 438,
Section 1.3 "Correcting for Sampling Variability in the Variance
Estimates") wurde festgestellt, dass die Autoren selbst schreiben:
"Gelman and Rubin (1992a) **incorrectly adopted** the correction factor
d/(d−2). This incorrect factor has led to a number of problems, in that
the corrected SRF (CSRF) can be infinite or even negative in the cases
where convergence is so slow that d < 2." Das entspricht exakt dem
ν/(ν−2)-Faktor in Schritt 6 oben (ν ≡ d, die Freiheitsgrade). Brooks and
Gelman (1998) ersetzen ihn durch **(d+3)/(d+1)** (siehe
brooks1998_spec.md, Section "Methode/Modell").

Die oben in Schritt 6 dokumentierte Formel √R̂ = √[(V̂/W)·(ν/(ν−2))] ist
also nach Aussage der Folgearbeit selbst **fehlerhaft** – sie ist hier
bewusst dennoch unverändert stehengelassen (originalgetreue Transkription
des 1992er-Papers ist der Zweck dieser Spec-Datei), aber für die
Validierung des eigenen Codes ist NICHT diese Formel, sondern die
korrigierte Fassung aus brooks1998_spec.md maßgeblich. Siehe dort sowie
`references/specs/open_questions.md` für Details.

## Bezug zum eigenen Code
- Verwendet in: {Datei/Funktion, noch offen zu füllen}
- Unbestätigter Hinweis (nicht Teil der eigentlichen Spec-Prüfung): das
  eigene Paper und der Code (`az.summary(...)` in
  `src/pfd/models/bayesian_estimation.py`, welches $\hat{R}$ ausgibt)
  verwenden vermutlich ArviZ' Implementierung des R̂-Diagnostikums, die
  auf der WEITERENTWICKELTEN, multivariaten/rank-normalisierten Version
  (Vehtari et al. 2021, nicht Teil dieser Spec-Serie) basiert, nicht auf
  der hier dokumentierten univariaten Original-Formel von 1992 (bzw.
  deren multivariater Erweiterung in brooks1998). Dies ist bei modernen
  Bayes-Bibliotheken Standard und wahrscheinlich unproblematisch, sollte
  aber nicht stillschweigend als "identisch mit Gelman and Rubin (1992)"
  angenommen werden, wenn im eigenen Paper auf die genaue Formel verwiesen
  wird. Nicht im Detail gegen den ArviZ-Quellcode geprüft, bitte separat
  verifizieren.
