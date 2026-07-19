# Spec: biais1999 – Price Discovery and Learning During the Preopening Period in the Paris Bourse

## Quelle
- Seiten/Abschnitt der Originalarbeit: Journal of Political Economy, Vol. 107,
  No. 6 (1999), S. 1218–1248 (Biais, Hillion, Spatt). Zentral: Section
  "B. The Speed of Learning", Unterabschnitte "1. Moment Conditions"
  (S. 1238–1240, Gl. 5–14), "2. Econometric Approach" (S. 1241–1242,
  GMM-/CUE-Minimierung, Instrumente, Zeitpunktwahl), "3. Results"
  (S. 1242–1243, empirische Schätzwerte).
- Zitiert in eigenem Paper: §3.6 "Alternative Hypotheses" (Unbiasedness-
  Regressionen, "we follow \citet{biais1999}"), §3.7 "Learning Rate"
  (Herleitung der Momentbedingungen, sieben Instrumente, Wahl der
  Zeitinkremente – jeweils "Following \citet{biais1999}"/"we follow the
  recommendation of \citet{biais1999}"), §5.6.1 (Results, Vergleich der
  eigenen Schätzwerte mit γ̂ = 2.7 aus dem Original).

Hinweis zur Extraktionsqualität: `pdftotext -layout` lieferte für die
gesamte relevante Passage (S. 1238–1243, Gl. 5–14 sowie die
GMM-/CUE-Minimierungsprogramme) sauberen, eindeutig lesbaren Text
inklusive aller Sub-/Superskripte und griechischer Buchstaben (γ, σ, φ,
ε, χ²). Ein Rendern als Bild war hier NICHT nötig; alle Gleichungen unten
sind direkt aus der Text-Extraktion übernommen.

## Methode/Modell

- Asymptotische Lerngeschwindigkeit (Gl. 5, S. 1239):
  ```
  t^γ (P_t − v) → N(0, σ²),   t → ∞                                    (5)
  ```
  konsistent mit Vives (1995) für γ = 0.5 bzw. Germain et al. (1996) für
  γ = 1.5.

- Näherung für große t (Gl. 6):
  ```
  P_t − v = (ε/t^γ) σ,   E(ε|I_t) = 0,   var(ε|I_t) = 1               (6)
  ```

- Berücksichtigung von Messfehlern im Proxy für v (Gl. 7):
  ```
  v̂ = v + φ,   φ ⊥ v,   φ ⊥ ε                                         (7)
  ```
  → P_t − v̂ = (ε/t^γ)σ − φ

- Quadrieren und Erwartungswert bilden (Gl. 8–9):
  ```
  E[(P_t − v̂)² | I_t] = E(φ²|I_t) + σ²/t^{2γ} − 2E(εφσ/t^γ | I_t)      (8)
  E[(P_t − v̂)² | I_t] − E(φ²|I_t) = σ²/t^{2γ}                          (9)
  ```
  (der letzte Term in (8) verschwindet, da ε und φ unabhängig sind und
  E(ε)=0). Analog für t−1 (Gl. 10):
  ```
  E[(P_{t−1} − v̂)² | I_{t−1}] − E(φ²|I_{t−1}) = σ²/(t−1)^{2γ}          (10)
  ```
  Mit E(φ²|I_t) = E(φ²|I_{t−1}) =: K (Modellparameter).

- Verhältnisbildung (Gl. 11):
  ```
  [E[(P_t−v̂)²|I_t] − K] / [E[(P_{t−1}−v̂)²|I_{t−1}] − K] = ((t−1)/t)^{2γ}   (11)
  ```

- **Die zwei zentralen Momentbedingungen (Gl. 12, S. 1240)**:
  ```
  E[ (P_t−v̂)² − ((t−1)/t)^{2γ}(P_{t−1}−v̂)² − K(1−((t−1)/t)^{2γ}) | I_{t−2} ] = 0
  E[ (P_{t−1}−v̂)² − ((t−2)/(t−1))^{2γ}(P_{t−2}−v̂)² − K(1−((t−2)/(t−1))^{2γ}) | I_{t−2} ] = 0
  ```                                                                    (12)
  Zu schätzende Parameter: γ und **K** (Nuisance-Parameter, die
  Proxy-Fehler-Varianz E(φ²)).

- Robustheitseigenschaften von (12) (wörtlich, S. 1240): (i) robust
  gegenüber Heteroskedastizität, da σ² herausfällt; (ii) robust gegenüber
  zeitlicher Aggregation – wird die wahre Lernzeit statt t durch nt (n
  unbekannte Konstante) ersetzt (Gl. 13–14), kürzt sich n beim
  Verhältnisbilden heraus und (12) bleibt die korrekte Momentbedingung.

- **Die sieben Instrumente (S. 1241, wörtlich zentral)**:
  ```
  1,
  P_{t−2} − P_{t−3},
  (P_{t−2} − P_{t−3})²,
  P_{t−3} − P_{t−4},
  (P_{t−3} − P_{t−4})²,
  P_{t−4} − E(v | I_0),
  [P_{t−4} − E(v | I_0)]²
  ```
  → 2 Momentbedingungen × 7 Instrumente = 14×1-Vektor
  E[φ(X_n, γ, K)] = 0, N = 39 Aktien × 19 Tage = 741 Beobachtungen.

## Schätzverfahren

- Verfahren: GMM, zwei Varianten (S. 1241):
  - Standard-Minimierung mit fixer Gewichtungsmatrix V:
    ```
    min_{γ,K} [ (1/N)Σ_{n=1}^N φ(X_n,γ,K) ]' V^{-1} [ (1/N)Σ φ(X_n,γ,K) ]
    ```
  - **Continuous-Updating (CUE)**, unter direktem Verweis auf Hansen,
    Heaton, and Yaron (1996) – siehe hansen1996_spec.md:
    ```
    min_{γ,K} [ (1/N)Σ φ(X_n,γ,K) ]' [V_N(γ,K)]^{-1} [ (1/N)Σ φ(X_n,γ,K) ]
    ```
    V_N(γ,K) ist die für die jeweiligen Kandidatenwerte γ,K berechnete
    Gewichtungsmatrix (kontinuierlich aktualisiert).

- **Optimierungsverfahren im Original** (S. 1242, explizit): "Since we
  have only two parameters to estimate, implementation of the continuous
  updating method is relatively simple. We constructed a **grid** of
  possible values for γ and K, computed the χ² for each point of the grid,
  and selected the pair of parameter values for which the objective
  function was the smallest." Konkret: γ ∈ [0, 3] in Schritten von 0.05;
  K ∈ [0, 0.0005] in Schritten von 0.0001. **Kein Gradienten- oder
  Simplex-Verfahren** wird für die CUE-Schätzung verwendet, sondern
  erschöpfende Gittersuche – anders als hansen1996 (dort `fminu.m`/
  `fmins.m`, siehe hansen1996_spec.md) und anders als das eigene Papier
  (Nelder-Mead, siehe unten).

- **Wahl der Zeitpunkte t, t−1, ..., t−4 (S. 1241–1242, wörtlich
  zentral, direkte Grundlage für die eigene "every fifth increment"-
  Begründung)**: "instead of considering one-minute intervals between t
  and t − 1 or t − 1 and t − 2, we consider five-minute intervals."
  Konkret: t = 10:00, t−1 = 9:55, t−2 = 9:50, t−3 = 9:45, t−4 = 9:40.
  Begründung: numerische Instabilität bei zu eng beieinanderliegenden
  Zeitpunkten.

- Instrumente/Moment-Bedingungen: siehe oben (Gl. 12, sieben Instrumente).
  **Dies ist die Quelle der Instrumentenwahl im eigenen Paper (nicht
  hansen1982) – wie in hansen1982_spec.md vermerkt.**

## Erwartete Ergebnisse (falls im Original berichtet)
Aus Section 3 "Results" (S. 1242–1243), Anwendung auf 39 CAC-40-Aktien,
19 Tage, N = 741:

| Methode        | γ̂   | SE(γ̂) | K̂      | SE(K̂)   | χ²    | p-Wert |
|----------------|------|--------|---------|----------|-------|--------|
| CUE (Gittersuche) | 1.35 | — (nicht berichtet) | 0.0001  | — (nicht berichtet) | 11.7  | 47.1 % |
| Iteriertes GMM | 2.7  | 0.86   | 0.00016 | 0.000025 | 12.47 | 43 %   |

Interpretation im Original: beide χ²-Werte sind konsistent mit der
Nullhypothese, dass das Modell gültig ist (Momentbedingungen nicht
verworfen). K̂ ist in beiden Methoden ähnlich und signifikant von null
verschieden. γ̂ unterscheidet sich zwischen den Methoden, ist aber in
beiden Fällen "hoch"; mit dem iterierten Schätzer werden sowohl γ=0
(keine Lernen) als auch γ=0.5 (Vives 1995) verworfen, γ=1.5 (Germain et
al. 1996) dagegen nicht.

Dies ist exakt der Wert (γ̂=2.7, SE=0.86), auf den sich das eigene Paper
in §5.6.1 bezieht ("\citet{biais1999} find an even higher learning rate
of 2.7 with a relatively large standard error of 0.86") – wörtlich
bestätigt.

## Unsicherheiten
- Für die CUE-Schätzung werden im Original keine Standardfehler für γ̂
  und K̂ berichtet (nur für die iterierte GMM-Schätzung) – dies wurde
  bewusst als "nicht berichtet" statt geraten oder aus der iterierten
  Schätzung übernommen eingetragen.
- Der genaue Aufbau der Gewichtungsmatrix V (Standard-GMM, nicht-CUE-
  Variante) wird im Originaltext nicht explizit als Formel angegeben
  (nur "V is an estimator of the variance-covariance matrix of the
  normally distributed random variable to which (1/N)ΣNφ(X_n,γ,K) is
  assumed to converge in distribution") – keine geschlossene Formel dafür
  im gelesenen Ausschnitt gefunden.
- Section "A. Unbiasedness Regressions" (vor "B. The Speed of Learning",
  auf S. 1236–1238) wurde nur teilweise gelesen (Ergebnisdiskussion zu
  Median-Slopes, RMSE), nicht die vollständige Modellherleitung – diese
  ist vermutlich für §3.6 des eigenen Papers (Unbiasedness-Regressionen)
  relevant und sollte bei Bedarf gesondert transkribiert werden (hier
  nicht Teil des Auftrags, der sich auf die GMM-Instrumente/
  Momentbedingungen konzentrierte).

## Bezug zum eigenen Code

**Wichtiger Befund – methodische Abweichung zwischen Original und eigenem
Code/Paper** (auch an `references/specs/open_questions.md` angehängt):

Die Momentbedingungen im eigenen Code (`src/pfd/utils/_gen_meth_mom.py`,
`_GenMethMom.momcond`) lauten:
```python
mom_cond_1 = (exog[:, 0] - endog) ** 2 - (
    ((n_per - 1) / n_per) ** (2 * param)
) * (exog[:, 1] - endog) ** 2
mom_cond_2 = (exog[:, 1] - endog) ** 2 - (
    ((n_per - 2) / (n_per - 1)) ** (2 * param)
) * (exog[:, 2] - endog) ** 2
```
Diese entsprechen strukturell Gleichung (12) aus dem Original, **enthalten
aber keinen K-Term** (`k_params=1` in `fit_gmm_mod.py`, d.h. nur γ wird
geschätzt). Im Original ist K jedoch ein explizit mitgeschätzter
Nuisance-Parameter, der die Varianz des Proxy-Fehlers φ (Differenz
zwischen der beobachteten und der wahren terminalen Größe v) abbildet.

Dies ist wahrscheinlich eine **bewusste und inhaltlich begründbare
Vereinfachung**: Im eigenen Paper ist die terminale Größe der exakte,
fehlerfreie Spielausgang ω ∈ {0,1} (kein Preis-Proxy wie bei Biais et
al., die die Schlusskurs als Proxy für den "wahren" Wert v verwenden und
daher einen Messfehler φ = v̂ − v einkalkulieren müssen). Insofern könnte
K = 0 im eigenen Kontext korrekt sein, weil φ ≡ 0 (kein Proxy-Fehler,
da ω exakt beobachtet wird). Das eigene Papier selbst leitet die
Momentbedingungen entsprechend OHNE K-Term her (vgl. eigene Gleichungen
"expres_1"/"express_2"/"moment_conditions" im eigenen LaTeX-Quelltext,
die direkt E[(p_t−ω)²|I_t] = σ²/t^{2γ} ohne K schreiben).

**Diese Vereinfachung wird jedoch an keiner Stelle im eigenen Paper
explizit als Abweichung von biais1999 benannt oder begründet** – der Text
sagt nur "Following \citet{biais1999}, we employ the following seven
instruments," was den Eindruck einer 1:1-Übernahme erweckt, obwohl die
zugrundeliegende Momentbedingung (12) selbst modifiziert wurde. Dies
sollte geprüft/explizit dokumentiert werden, insbesondere weil die
fehlende K-Korrektur die Schätzung von γ (und ihre Vergleichbarkeit mit
γ̂=2.7 aus dem Original) beeinflussen könnte, falls die Annahme φ≡0 nicht
exakt zutrifft (z.B. durch Rundungsfehler oder Marktunvollkommenheiten in
den Wettquoten).

- Verwendet in: {Datei/Funktion, noch offen zu füllen}
- Weiterer unbestätigter Hinweis: `fit_gmm_mod.py` verwendet
  `optim_method="nm"` (Nelder-Mead) für sowohl die Erststufen- als auch
  die CUE-Schätzung – das Original verwendet für CUE dagegen eine
  erschöpfende Gittersuche (kein gradienten- oder simplexbasiertes
  Verfahren), da nur 2 Parameter geschätzt werden. Da das eigene Modell
  nur 1 Parameter (γ) je Buchmacher schätzt, ist Nelder-Mead plausibel
  praktikabler als eine Gittersuche, dies ist aber eine bewusste,
  unbenannte Methodenentscheidung, keine direkte Übernahme des
  Original-Vorgehens.
