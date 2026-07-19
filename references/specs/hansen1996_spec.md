# Spec: hansen1996 – Finite-Sample Properties of Some Alternative GMM Estimators

## Quelle
- Seiten/Abschnitt der Originalarbeit: Journal of Business & Economic
  Statistics, Vol. 14, No. 3 (Juli 1996), S. 262–280 (Hansen, Heaton, Yaron).
  Zentral für den CUE: Section 1 "Alternative Estimators and Related
  Literature", S. 263 (Gleichungen 1–5). Praktische Umsetzung/Optimierung:
  Section 3.2 "Numerical Search Routines", S. 269.
- Zitiert in eigenem Paper: §3.7.1 "Generalized Methods of Moments
  Estimation" ("we apply the continuous-updating estimator (CUE), as proposed
  by \citet{hansen1996}, to improve the precision of our estimates. In the
  CUE approach, the weighting matrix W_N is replaced by the optimal weighting
  matrix W(γ), which is continuously updated during the minimization
  process.")

## Methode/Modell

Text-Extraktion per `pdftotext -layout` war für S. 263 (die zentrale Seite)
tatsächlich sauber lesbar (einspaltiges Layout mit klar getrennten
Gleichungen) – anders als bei hansen1982 war hier **kein** Rendern als Bild
nötig, um die Kernszenen zu transkribieren. Für S. 269 (Numerical Search
Routines) war die Extraktion dagegen wegen eingebetteter Abbildungen im
Zweispalten-Layout stark verstümmelt; dort wurde nur die Prosa (nicht-
mathematisch) ausgewertet, siehe "Unsicherheiten".

- Momentbedingungen (Gl. 1, S. 263):
  ```
  E[φ(X_t, β)] = 0                                                   (1)
  ```
  φ hat n ≥ k Koordinaten, β ist der k-dimensionale Parametervektor.
  Annahme: (1/√T) Σ_{t=1}^{T} φ(X_t, β) konvergiert in Verteilung gegen
  N(0, V(β)).

- Allgemeine (zweistufige) effiziente GMM-Zielfunktion (Gl. 2, S. 263):
  ```
  [ (1/T) Σ_{t=1}^{T} φ(X_t,b) ]' [V_T(b_T^1)]^{-1} [ (1/T) Σ_{t=1}^{T} φ(X_t,b) ]   (2)
  ```
  V_T(β) ist ein (infeasible) konsistenter Schätzer der Kovarianzmatrix
  V(β); b_T^1 ist ein vorab bestimmter konsistenter Schätzer von β (z.B. aus
  Gl. 3).

- Zwei-Schritt-Schätzer (Gl. 3, S. 263), definiert b_T^1:
  ```
  [ (1/T) Σ φ(X_t,b) ]' [ (1/T) Σ φ(X_t,b) ]                          (3)
  ```
  (Identitätsmatrix als Gewichtung.)

- Iterativer Schätzer (Prosa, S. 263): wiederholtes Neuschätzen von V(β) an
  der jeweils aktuellen Schätzung b_T^{j-1}, bis b_T^j konvergiert oder eine
  maximale Iterationszahl erreicht ist; Grenzwert b_T^∞.

- **CUE – Continuous-Updating Estimator (Gl. 4, S. 263, wörtlich zentral)**:
  ```
  Formally let b_T^c be the minimizer of

  [ (1/T) Σ_{t=1}^{T} φ(X_t,b) ]' [V_T(b)]^{-1} [ (1/T) Σ_{t=1}^{T} φ(X_t,b) ]   (4)
  ```
  Der entscheidende Unterschied zu (2)/(3): die Gewichtungsmatrix V_T(b) wird
  **an derselben Stelle b ausgewertet, über die gerade minimiert wird**, statt
  an einer vorab fixierten Schätzung b_T^1 (Zwei-Schritt) oder einem
  Fixpunkt-Iterat b_T^{j-1} (iterativ). Es handelt sich um EIN gemeinsames
  Minimierungsproblem über b, nicht zwei getrennte Stufen.

## Schätzverfahren

- Verfahren: Continuously Updated GMM (CUE), Spezialfall/Alternative zum
  klassischen zweistufigen GMM aus hansen1982.

- **Formaler Unterschied zur hansen1982-Gewichtungsmatrix** (explizit
  angefordert):
  - hansen1982 (Section 2/3): die Gewichtungsmatrix a_N (Konsistenz-Teil)
    bzw. a*_N (Asymptotik-Teil) wird als **von β unabhängige, feste** Folge
    von Matrizen behandelt, die (fast sicher / in Wahrscheinlichkeit) gegen
    eine Konstante a_0 bzw. a*_0 konvergiert (Assumption 2.5/3.6). Die
    Minimierung von |h_N(β)|² = g_N(β)'a_N'a_N g_N(β) erfolgt bei
    FESTGEHALTENEM a_N; die "optimale" Wahl a_0'a_0 = S_w^{-1} (Theorem 3.2)
    wird typischerweise aus einer VORGESCHALTETEN (ersten) Stufe geschätzt.
  - hansen1996 (Gl. 4): die Gewichtungsmatrix V_T(b)^{-1} ist explizit eine
    **Funktion des Kandidatenwerts b**, über den gerade optimiert wird –
    sie wird bei jedem Optimierungsschritt für den JEWEILIGEN Wert von b neu
    berechnet ("continuously updated"), nicht nur einmal in einer
    Vorstufe. Formal: hansen1982 minimiert g(b)'W g(b) mit W fest (aus einer
    Vorstufe b_T^1), hansen1996/CUE minimiert g(b)'W(b)^{-1}g(b) mit W(b) =
    V_T(b) direkt als Funktion von b. Das eigene Paper übernimmt diese
    Notation direkt: "the weighting matrix W_N is replaced by the optimal
    weighting matrix W(γ), which is continuously updated during the
    minimization process" (§3.7.1).
  - Laut Originaltext (S. 263) hat das CUE-Minimierungsproblem dadurch einen
    "extra term" in den Erstordnungsbedingungen (durch die Ableitung von
    V_T(b) nach b) relativ zu Problemen mit fixer Gewichtungsmatrix; unter
    Verweis auf Pakes and Pollard (1989, S. 1044–1046) wird argumentiert,
    dass dieser Zusatzterm die asymptotische Verteilung des Schätzers NICHT
    verzerrt.

- **Optimierungsverfahren/Startwerte im Original** (explizit angefordert,
  Section 3.2 "Numerical Search Routines", S. 269 – aus Prosa, s.
  Unsicherheiten zur Extraktionsqualität dieser Seite):
  - "The two-step and iterative estimators are given by the minimizers of
    the objective function (2), and the continuous-updating estimator is
    given by the minimizer of the objective function (4)."
  - Für einige Spezifikationen ergeben sich die Schätzer als Lösung
    linearer Gleichungen; ansonsten wurden die MATLAB-"Optimization
    Toolbox"-Routinen `fminu.m` (Quasi-Newton-Verfahren, gradientenbasiert,
    abhängig von einem Startwert) und `fmins.m` (Nelder-Mead-Simplex-
    Suche) verwendet.
  - Um Sensitivität gegenüber der Initialisierung zu prüfen, wurden
    **mehrere unterschiedliche Startwerte verwendet, darunter explizit der
    wahre Parametervektor** (da es sich um eine Monte-Carlo-Studie mit
    bekanntem wahren Wert handelt).
  - Wenn das gradientenbasierte Verfahren (`fminu.m`) nicht konvergierte
    oder unplausible Schätzwerte lieferte, wurde auf `fmins.m` (Simplex)
    zurückgegriffen.
  - Ausdrücklich festgehalten: "the continuous-updating criterion can make
    numerical search for the minimizer difficult" – d.h. die Autoren
    berichten selbst von numerischen Schwierigkeiten bei der CUE-Minimierung
    und untersuchen dies in Section 4 gesondert.
  - Anmerkung zum eigenen Code: das eigene Paper/`fit_gmm_mod` verwendet
    laut Code (`optim_method="nm"`, Nelder-Mead) direkt das Verfahren, das
    im Original nur als **Rückfalloption** bei Konvergenzproblemen des
    Gradientenverfahrens vorgesehen war, nicht als Primärmethode. Dies ist
    keine Unstimmigkeit per se, aber ein methodischer Unterschied zur
    Originalarbeit, der dem Nutzer bewusst sein sollte.

- Hyperparameter/Tuning-Werte aus dem Original: keine festen Zahlenwerte
  (z.B. Toleranzen, max. Iterationszahlen) im extrahierten Text auffindbar;
  nur der Verweis auf die "MATLAB Optimization Toolbox manual" für Details
  zu `fminu.m`/`fmins.m`.

- Instrumente/Moment-Bedingungen (falls GMM): im Original anwendungsspezifisch
  (CCAPM-Euler-Gleichungen, Gl. 6–9, S. 264) – nicht identisch mit den
  Instrumenten des eigenen Papers (die aus biais1999 stammen).

## Erwartete Ergebnisse (falls im Original berichtet)
- Das Paper ist eine Monte-Carlo-Simulationsstudie (Datengenerierung basierend
  auf einem CCAPM, nicht auf Wettquoten) und berichtet Verzerrung, RMSE und
  Überdeckungsraten für die drei Schätzer (Zwei-Schritt, iterativ,
  CUE) über mehrere Designs (Tabellen und Abbildungen in Section 4).
  Diese Zahlenwerte sind nicht direkt auf die eigene Tennis-Wettquoten-
  Anwendung übertragbar (andere Datengenerierung, andere Momentbedingungen)
  und wurden daher hier nicht transkribiert. Falls für die Validierung der
  eigenen CUE-Implementierung benötigt, müssten die konkreten Tabellen in
  Section 4 (S. 265ff.) gesondert herangezogen werden.

## Unsicherheiten
- Seite 263 (Gleichungen 1–5, inkl. der CUE-definierenden Gleichung 4) war
  per `pdftotext -layout` sauber und eindeutig lesbar; ich habe sie NICHT
  zusätzlich als Bild gerendert, da keine verstümmelten Symbole auftraten.
  Falls Zweifel bestehen, empfehle ich dennoch einen Abgleich mit dem
  Original, da ich diese Seite – anders als bei hansen1982 – nicht visuell
  gegengeprüft habe.
- Section 3.2 (Numerical Search Routines, S. 269) enthält eine weitere,
  mit Gleichungsnummer "(2)" gekennzeichnete Formel für einen alternativen
  Kovarianzschätzer V_T(b) mit MA(1)-artigen Kreuzprodukt-Termen (relevant
  für den Fall seriell korrelierter Störterme). Die Text-Extraktion dieser
  Seite war durch eingebettete Abbildungen im Zweispalten-Layout stark
  gestört; ich konnte die genaue Gleichungsnummer NICHT zweifelsfrei lesen
  (könnte auch "(12)" o.Ä. sein, wobei eine führende Ziffer beim Spaltenumbruch
  verlorenging) und habe diese Seite nicht als Bild nachgerendert, da sie
  nicht Teil der eigentlichen CUE-Definition ist (Fokус laut Auftrag). Diese
  Formel wurde daher bewusst NICHT in "Methode/Modell" übernommen – nur ihre
  Existenz und ihr ungefährer Ort (S. 269) sind hier vermerkt.
- Die genauen MATLAB-Optimierungsdetails (Toleranzen, max. Iterationen) sind
  im Haupttext nicht enthalten, nur der Verweis auf das Toolbox-Manual –
  daher als "keine im Original berichteten Werte" eingetragen statt geraten.

## Bezug zum eigenen Code
- Verwendet in: {Datei/Funktion, noch offen zu füllen}
- Unbestätigter Hinweis (nicht Teil der eigentlichen Spec-Prüfung): laut
  `src/pfd/helpers/fit_gmm_mod.py` wird `max_iter="cue"` an
  `statsmodels.sandbox.regression.gmm.GMM.fit()` übergeben, was dort intern
  die kontinuierlich aktualisierte GMM-Variante auslöst – nicht gegen die
  obige Definition (Gl. 4) im Detail geprüft, bitte separat verifizieren,
  insbesondere ob statsmodels' CUE-Implementierung tatsächlich Gl. (4)
  entspricht.
