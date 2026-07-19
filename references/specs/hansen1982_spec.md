# Spec: hansen1982 – Large Sample Properties of Generalized Method of Moments Estimators

## Quelle
- Seiten/Abschnitt der Originalarbeit: Econometrica, Vol. 50, No. 4 (Juli 1982),
  S. 1029–1054. Zentral für den GMM-Schätzer selbst: Section 2 "Consistency of
  the GMM Estimator" (S. 1032–1038, insb. Definition 2.1) und Section 3 "The
  Asymptotic Distribution of the GMM Estimator" (S. 1038–1048, insb. Theorem
  3.1 und Theorem 3.2). Section 4 "Testing Over-Identifying Restrictions"
  (S. 1048–1050) liefert zusätzlich den Overidentifikations-/J-Test.
- Zitiert in eigenem Paper: §3.7.1 "Generalized Methods of Moments Estimation"
  ("we utilize the Generalized Methods of Moments (GMM) as proposed by
  \citet{hansen1982}. The GMM estimator is consistent, asymptotically normal,
  and efficient.")

## Methode/Modell

- Orthogonalitätsbedingungen, S. 1033:
  ```
  u_n = F(x_n, β_0),   z_n = G(x_n, β_0)                          (1)
  E[u_n ⊗ z_n] = 0                                                 (2)
  f(x_n, β_0) = F(x_n, β_0) ⊗ G(x_n, β_0)                          (3)
  ```
  woraus E[f(x_n, β_0)] = 0 folgt. "⊗" ist das Kronecker-Produkt.

- GMM-Kriteriumsfunktion (unnummeriert, S. 1033):
  ```
  f_n(ω, β) = f[x_n(ω), β]
  g_N(ω, β) = (1/N) Σ_{n=1}^{N} f_n(ω, β)
  h_N(ω, β) = a_N(ω) g_N(ω, β)
  B_N(ω) = { β ∈ S : |h_N(ω, β)|² = inf_{β∈S} |h_N(ω, β)|² }
  ```

- DEFINITION 2.1 (S. 1034, wörtlich): "The GMM estimator {b_N : N ≥ 1} is a
  sequence of random vectors such that b_N(ω) ∈ B_N(ω) for N ≥ N*(ω) where
  N*(ω) is less than infinity for almost all ω in Ω."

- Bedeutung der Variablen/Parameter:
  - x_n: beobachtbarer p-dimensionaler stationärer, ergodischer stochastischer
    Prozess (Assumption 2.1 / 3.1)
  - β_0 ∈ S ⊂ R^q (bzw. Kompaktifizierung davon): zu schätzender Parametervektor
  - u_n: unbeobachtbarer Störterm; z_n: Instrumentenvektor
  - f : R^p × S → R^r, r ≥ q: die r Orthogonalitätsbedingungen
  - a_N: (zufällige) Gewichtungsmatrix; s×r mit q ≤ s ≤ r in Section 2
    (Konsistenz), q×r in Section 3 (Definition 3.1, Asymptotik/Effizienz)
  - d_0 = E[∂f/∂β(x_1, β_0)] (Notation direkt im Anschluss an Assumption 3.4,
    S. 1039)
  - S_w = Σ_{j=-∞}^{+∞} R_w(j) mit R_w(j) = E[w_0 w'_{-j}], w_n = f(x_n, β_0)
    (S. 1041–1042)

- Annahmen (zentral, nicht erschöpfend): Assumption 2.1/3.1 (Stationarität,
  Ergodizität von {x_n}); Assumption 2.2 ((S,σ) separabler metrischer Raum);
  Assumption 2.3/3.3 (Borel-Messbarkeit von f bzw. ∂f/∂β, Stetigkeit in β);
  Assumption 2.4 (E f(x_1,β) existiert für alle β, Nullstelle bei β_0);
  Assumption 2.5/3.6 (a_N bzw. a*_N konvergieren (f.s. bzw. in
  Wahrscheinlichkeit) gegen eine Matrix vollen Rangs); Assumption 3.4 (∂f/∂β
  "first moment continuous" bei β_0, E[∂f/∂β(x_1,β_0)] existiert, endlich,
  vollem Rang); Assumption 3.5 (Bedingungen für einen Zentralen Grenzwertsatz
  für Martingal-Differenzen, u.a. via Gordin [1969]).

## Schätzverfahren

- Verfahren: zweistufig behandelt — (i) Section 2: Konsistenz über Minimierung
  von |h_N(β)|² = g_N(β)' a_N' a_N g_N(β) über β ∈ S; (ii) Section 3: unter den
  first-order conditions von (i) wird die asymptotische Verteilung hergeleitet
  und die effiziente Gewichtungsmatrix charakterisiert.

- Verbindung der beiden Sichtweisen (Gl. 6–7, S. 1041):
  ```
  ∂g_N/∂β (b_N)' a_N' a_N g_N(b_N) = 0                              (6)
  a*_N = ∂g_N/∂β (b_N)' a_N' a_N                                    (7)
  ```

- THEOREM 3.1 (Asymptotische Normalität, S. 1042):
  ```
  √N (b*_N − β_0) →_d N( 0, (a*_0 d_0)^{-1} a*_0 S_w a*_0' (a*_0 d_0)^{-1′} )
  ```

- THEOREM 3.2 (optimale Gewichtungsmatrix / Effizienz, S. 1048):
  ```
  (a*_0 d_0)^{-1} a*_0 S_w a*_0 (a*_0 d_0)^{-1′} = (d_0' S_w^{-1} d_0)^{-1}    (10)
  a*_0 = e d_0' S_w^{-1}                                                     (11)
  ```
  für eine beliebige nichtsinguläre q×q-Matrix e. D.h. optimal (effizient) ist
  die Wahl a_0' a_0 = S_w^{-1}; die resultierende (kleinstmögliche) asymptotische
  Kovarianzmatrix ist (d_0' S_w^{-1} d_0)^{-1}. Dies ist die Grundlage für die
  im eigenen Paper genannte "Efficiency" der CUE (siehe hansen1996-Spec für die
  praktische Umsetzung der laufend aktualisierten Gewichtungsmatrix W(γ)).

- Overidentifikationstest (Lemma 4.2 + Folgesatz, S. 1049–1050):
  ```
  τ_N = g_N(b*_N)' (S^N_w)^{-1} g_N(b*_N)
  N τ_N →_d χ²(r − q)
  ```
  r = Anzahl Orthogonalitätsbedingungen (Momentbedingungen), q = Anzahl
  Parameter.

- Hyperparameter/Tuning-Werte aus dem Original: keine im üblichen Sinn – reine
  Theorie-Arbeit ohne empirische Anwendung, keine Startwerte, Iterationszahlen
  o.Ä.

- Instrumente/Moment-Bedingungen (falls GMM): im Original nicht konkret
  spezifiziert (allgemeine Theorie, Gl. 1–3); die konkrete Instrumentenwahl
  (7 Instrumente etc.) im eigenen Paper stammt NICHT aus hansen1982, sondern
  aus biais1999 (separat zu dokumentieren).

## Erwartete Ergebnisse (falls im Original berichtet)
- Keine. Hansen (1982) ist eine rein theoretische/methodische Arbeit ohne
  empirische Anwendung, Simulation oder Tabellen mit konkreten Zahlenwerten.
  Es gibt daher nichts, wogegen die eigene Implementierung numerisch validiert
  werden könnte – nur die Korrektheit der übernommenen Formeln/Ableitung ist
  hier relevant.

## Unsicherheiten
- Gleichungsnummer (10) wird im Original **zweimal vergeben** für zwei
  unterschiedliche Gleichungen: einmal für "f(x_n, β_0) = u_n ⊗ z_n" (S. 1042,
  zu Beginn von Section 3, im Kontext der Berechnung von S_w) und einmal für
  die Optimalitätsbedingung in Theorem 3.2 (S. 1048). Ich habe dies visuell an
  beiden Stellen im Original geprüft (nicht nur aus der Text-Extraktion) –
  es handelt sich nicht um einen Transkriptionsfehler meinerseits, sondern
  vermutlich um einen Nummerierungsfehler im Original (Econometrica 1982).
  Beide Vorkommen sind oben mit "(10)" gekennzeichnet, wie im Original gedruckt.
- Methodik der Transkription: pdftotext-Extraktion der PDF ergab für die
  mathematische Notation (griechische Buchstaben, Sub-/Superskripte, Striche)
  massiv fehlerhafte Zeichen (z.B. "IhN 2" statt "|h_N|²", "ado" statt "a₀d₀").
  Ich habe mich daher NICHT auf diese Text-Extraktion verlassen, sondern die
  betroffenen Seiten (S. 1033, 1034, 1040–1042, 1047–1050) mit pdftoppm als
  Bilder gerendert und die Gleichungen direkt visuell aus dem Original
  transkribiert. Alle oben angegebenen Gleichungen sind auf diese Weise visuell
  bestätigt.
- Definition 2.1 nennt eine Fußnote 7 zur Messbarkeits-Anforderung an {b_N};
  diese Fußnote habe ich inhaltlich erfasst, aber nicht wörtlich transkribiert
  (nicht zentral für die Schätzergleichung selbst).
- Nicht abschließend geprüft: die Argumentation/Beweise in den Lemmata 3.1–3.3
  und den "five special cases" (Case i–v) zur Berechnung von S_w unter
  verschiedenen Annahmen an die serielle Korrelation/Heteroskedastizität der
  Störterme – für die eigene GMM-Implementierung vermutlich nicht direkt
  relevant, da diese Struktur bei biais1999/hansen1996 übernommen wird, aber
  bei Bedarf nachzuliefern.

## Bezug zum eigenen Code
- Verwendet in: {Datei/Funktion, noch offen zu füllen}
- Unbestätigter Hinweis (nicht Teil der eigentlichen Spec-Prüfung, nur als
  Anhaltspunkt): `src/pfd/utils/_gen_meth_mom.py` (`_GenMethMom`, Unterklasse
  von `statsmodels.sandbox.regression.gmm.GMM`) und
  `src/pfd/helpers/fit_gmm_mod.py` scheinen die GMM-Schätzung im eigenen Code
  zu implementieren – nicht selbst gegen die obigen Gleichungen geprüft, bitte
  bei Bedarf separat verifizieren.
