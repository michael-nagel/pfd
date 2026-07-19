# Spec: brooks1998 – General Methods for Monitoring Convergence of Iterative Simulations

## Quelle
- Seiten/Abschnitt der Originalarbeit: Journal of Computational and
  Graphical Statistics, Vol. 7, No. 4 (1998), S. 434–455 (Stephen P.
  Brooks, Andrew Gelman). Datei liegt unter `references/literature/
  gelman_1998.pdf` (Dateiname weicht vom Bib-Key ab, siehe
  `citation_map.md` – Titel im Dokument selbst wörtlich geprüft und
  bestätigt: "General Methods for Monitoring Convergence of Iterative
  Simulations", Autoren Brooks & Gelman). Zentral: Section 1.2 "Monitoring
  Convergence: The Original Method" (S. 436–437, univariate PSRF, Gl. 1.1),
  Section 1.3 "Correcting for Sampling Variability in the Variance
  Estimates" (S. 437–438, **korrigierter** Faktor), Section 4
  "Multivariate Extensions" (S. 445–446, MPSRF, Gl. 4.1, Lemma 1/2).
- Zitiert in eigenem Paper: Appendix "Bayesian Estimation – Algorithms and
  Procedures" ("we use the Gelman-Rubin statistic R̂ \citep{gelman1992,
  brooks1998} and dispay trace plots for the individual chains").

Hinweis zur Extraktionsqualität: `pdftotext -layout` konnte für dieses PDF
(digital erzeugt, aber mit Formeln als eingebettete Grafiken/Sonderfonts
gesetzt) die zentralen Gleichungen **überhaupt nicht** als Text erfassen –
an den Stellen der Gleichungen erschienen nur Leerstellen bzw. die
umgebenden Wörter "where", "and" ohne Formelinhalt. Dies ist eine andere
Art von Extraktionsproblem als bei den gescannten Papers (ashley1980,
hansen1982, gelman1992): hier fehlt der Inhalt komplett, statt nur
verzerrt zu sein. Ich habe daher ALLE unten stehenden Gleichungen durch
Rendern der betroffenen Seiten (S. 436–438, 445–446; PDF-Seiten 4–6,
13–14) als Bilder visuell aus dem Original transkribiert. Keine der
Formeln in diesem Dokument stammt aus der Text-Extraktion allein.

## Methode/Modell

### A. Univariate PSRF – Originalmethode (Section 1.2, S. 436–437)

Für eine skalare Zielgröße ψ mit Beobachtungen ψ_jt (Kette j, Zeit t),
m Ketten, je n Iterationen nach Verwerfen der ersten Hälfte:

```
B/n = (1/(m−1)) Σ_{j=1}^m (ψ̄_j. − ψ̄..)²
W   = (1/(m(n−1))) Σ_{j=1}^m Σ_{t=1}^n (ψ_jt − ψ̄_j.)²
```

Gepoolte Varianzschätzung:
```
σ̂²₊ = ((n−1)/n) W + B/n
```
(unverzerrt, falls Startpunkte aus der Zielverteilung stammen; überschätzt
σ² bei geeigneter Überdispersion). Gepoolte Posterior-Varianz unter
Berücksichtigung der Stichprobenvariabilität von μ̂:
```
V̂ = σ̂²₊ + B/(mn)
```

Skalenreduktionsfaktor (SRF) und **potenzieller** Skalenreduktionsfaktor
(PSRF, Gl. 1.1, S. 437, wörtlich zentral):
```
R = V̂/σ²           (population; σ² unbekannt)
R̂ = V̂/W = ((m+1)/m)(σ̂²₊/W) − (n−1)/(mn)                              (1.1)
```

### B. Korrektur für Stichprobenvariabilität (Section 1.3, S. 437–438,
**dies ist die entscheidende Abweichung von gelman1992**)

Freiheitsgrade der t-Approximation (Momentenschätzer, identisch zu
gelman1992's ν): d ≈ 2V̂/v̂ar(V̂).

**Wörtliches Zitat (S. 438)**: "Gelman and Rubin (1992a) **incorrectly
adopted** the correction factor d/(d−2). This incorrect factor has led to
a number of problems, in that the corrected SRF (CSRF) can be infinite or
even negative in the cases where convergence is so slow that d < 2. In
order to correctly account for the sampling variability, the correction
factor (d+3)/(d+1) should be used. The correct factor, (d+3)/(d+1),
removes the problems associated with that proposed in the original
article."

Begründung (S. 438, Prosa): der Korrekturfaktor (d+3)/(d+1) ergibt sich
aus der Fisher-Information der t_d-Verteilung (Fisher 1935) und
berücksichtigt korrekt sowohl die Varianzschätzung s² als auch deren
Freiheitsgrade d.

**Korrigierte Formel (S. 438, wörtlich zentral, ersetzt gelman1992's
Schritt 6)**:
```
R̂_c = ((d+3)/(d+1)) R̂ = ((d+3)/(d+1)) (V̂/W)
```
"This correction is minor, because at convergence d tends to be large"
(d.h. für großes d nähert sich (d+3)/(d+1) → 1, ähnlich wie d/(d−2) → 1,
aber ohne die Singularität/Negativität bei kleinem d).

### C. Multivariate Erweiterung (Section 4, S. 445–446, Gl. 4.1)

Für einen p-dimensionalen Parametervektor ψ mit Beobachtungen ψ_jt^(i):

```
V̂ = ((n−1)/n) W + (1 + 1/m) B/n
W  = (1/(m(n−1))) Σ_{j=1}^m Σ_{t=1}^n (ψ_jt − ψ̄_j.)(ψ_jt − ψ̄_j.)'
B/n = (1/(m−1)) Σ_{j=1}^m (ψ̄_j. − ψ̄..)(ψ̄_j. − ψ̄..)'
```
(W, B/n sind jetzt p×p-Kovarianzmatrizen, nicht Skalare.) **Beachte**: der
Koeffizient von B/n ist hier "(1 + 1/m)", nicht "1" wie im univariaten
σ̂²₊ – dies ist keine Inkonsistenz, sondern weil V̂ hier direkt die
gepoolte Kovarianzmatrix INKLUSIVE des B/(mn)-Stichprobenvariabilitäts-
terms aus Schritt A zusammenfasst (1/n · (1+1/m) = 1/n + 1/(mn)).

**Multivariater PSRF (MPSRF), Gl. (4.1), S. 446, wörtlich zentral**:
```
R̂^p = max_a (a'V̂a) / (a'Wa)                                          (4.1)
```
("maximum root statistic", das Maximum des univariaten SRF über alle
linearen Projektionen a'ψ von ψ).

**Lemma 1** (S. 446): für zwei nichtsinguläre, positiv definite,
symmetrische Matrizen M, N gilt max_a (a'Ma)/(a'Na) = λ, wobei λ der
größte Eigenwert von N⁻¹M ist (Beweis: Mardia, Kent, Bibby 1979, A.9.2).

**Lemma 2** (geschlossene Form für MPSRF, S. 446, wörtlich zentral):
```
R̂^p = (n−1)/n + ((m+1)/m) λ_1
```
wobei λ_1 der größte Eigenwert der symmetrischen, positiv definiten
Matrix W⁻¹B/n ist. Herleitung (per Lemma 1, direkt aus Gl. 4.1 und der
Definition von V̂): R̂^p → 1 für großes n unter der Annahme gleicher
Mittelwerte zwischen den Sequenzen (λ_1 → 0).

**Wichtige Beobachtung (eigene Einordnung, nicht wörtlich im Original so
benannt)**: Die MPSRF-Formel in Abschnitt C basiert auf der
UNKORRIGIERTEN Struktur von Gl. (1.1) (R̂, nicht R̂_c) – nirgends in
Section 4 wird der (d+3)/(d+1)-Korrekturfaktor aus Section 1.3 auf den
multivariaten Fall angewendet oder erwähnt. Ob dies beabsichtigt ist
(Korrektur nur für den univariaten Fall relevant/hergeleitet) oder eine
im Original schlicht nicht behandelte Erweiterung, wird im gelesenen
Abschnitt nicht diskutiert – siehe Unsicherheiten.

## Schätzverfahren
- Verfahren: Varianzkomponentenanalyse aus m parallelen Ketten (wie
  gelman1992), univariat mit Fisher-Informations-basierter
  Freiheitsgradkorrektur (d+3)/(d+1), multivariat via Maximum-Root-
  Statistik (größter Eigenwert von W⁻¹B/n).
- Hyperparameter/Tuning-Werte aus dem Original: keine (m, n frei wählbar;
  keine empfohlenen Defaults im gelesenen Abschnitt).
- Instrumente/Moment-Bedingungen (falls GMM): nicht zutreffend.

## Erwartete Ergebnisse (falls im Original berichtet)
- Section 3 (Beispiele, u.a. bivariates Normalverteilungsbeispiel, Figure
  5: MPSRF- und PSRF-Sequenzen) und die Pharmakokinetik-Anwendung mit 141
  Parametern (Figure 7) enthalten empirische Illustrationen der MPSRF.
  Diese numerischen Werte (z.B. "MPSRF value takes values no larger than
  1.3" für 3 Sätze unabhängiger Normalstichproben, S. ~1033 der
  Text-Extraktion/Section 4-Diskussion) beziehen sich auf andere
  Anwendungsbeispiele (nicht die eigene Tenniswettmarkt-Anwendung) und
  wurden hier nicht im Detail transkribiert, da sie keine direkte
  Validierungsgrundlage für die eigene Implementierung bieten.

## Unsicherheiten
- Ob der (d+3)/(d+1)-Korrekturfaktor auch auf die multivariate MPSRF
  (Abschnitt C) angewendet werden sollte oder ob die Autoren die
  MPSRF bewusst nur auf der unkorrigierten R̂-Struktur aufbauen, wird im
  gelesenen Abschnitt (Section 4, S. 445–446) nicht explizit diskutiert.
  Ich habe die nachfolgenden Abschnitte des Papers (Section 5 und später,
  falls vorhanden) NICHT gelesen – möglich, dass dort eine korrigierte
  multivariate Version noch nachgereicht wird. Dies wurde bewusst nicht
  angenommen/interpoliert, sondern hier als offene Frage vermerkt.
- Ich habe nicht geprüft, ob "Gelman and Rubin (1992a)", auf das
  brooks1998 sich für die Originalmethode bezieht, exakt die in
  `gelman1992_spec.md` dokumentierte Arbeit ("A Single Series...", Bayesian
  Statistics 4) ist oder die längere Statistical-Science-Fassung
  ("Inference from Iterative Simulation Using Multiple Sequences", 1992) –
  beide werden in der Literatur oft synonym als "Gelman and Rubin (1992)"
  zitiert. Der d/(d−2)-Korrekturfaktor, den brooks1998 als "incorrect"
  bezeichnet, entspricht jedoch strukturell exakt dem ν/(ν−2)-Faktor, den
  ich in `gelman1992_spec.md` aus der dort geprüften PDF-Datei
  transkribiert habe – die Kritik trifft also mindestens auf diese Fassung
  zu (oder eine inhaltsgleiche Formel in der längeren Fassung).
- Section 1.1 (vor der hier dokumentierten Section 1.2) sowie die
  Abschnitte zwischen Section 1.3 und Section 4 (Section 2 "An Iterated
  Graphical Approach" und Section 3 "Examples") wurden nur teilweise
  gelesen (Section 2 nur der Beginn, S. 438, siehe gerendertes Bild oben)
  bzw. nicht im Detail transkribiert, da sie nicht Teil des Kernauftrags
  (PSRF-/MPSRF-Definition) waren.

## Bezug zum eigenen Code

**Wichtiger Befund – potenziell veraltete/inkorrekte Formel-Referenz**
(auch an `references/specs/open_questions.md` angehängt, UND als Nachtrag
in `references/specs/gelman1992_spec.md` vermerkt):

Das eigene Paper zitiert gelman1992 UND brooks1998 gemeinsam für "the
Gelman-Rubin statistic R̂", ohne zwischen der (nach Aussage von brooks1998
selbst) **fehlerhaften** Originalformel (d/(d−2)-Korrektur, gelman1992)
und der **korrigierten** Fassung ((d+3)/(d+1)-Korrektur, brooks1998) zu
unterscheiden. Da der eigene Code laut Hinweis in `gelman1992_spec.md`
vermutlich ArviZ' $\hat{R}$-Implementierung verwendet (die auf der noch
neueren, rank-normalisierten Version von Vehtari et al. 2021 basiert,
nicht auf einer der beiden hier dokumentierten Fassungen), ist dies
wahrscheinlich praktisch irrelevant für das tatsächliche Ergebnis – aber
die **Zitierung selbst** könnte präzisiert werden.

**Zu klären:** (1) Ist bekannt/geprüft, welche R̂-Variante ArviZ konkret
berechnet, und stimmt diese eher mit brooks1998's korrigierter Formel,
mit einer der beiden hier dokumentierten Fassungen, oder mit der noch
neueren Vehtari-et-al.-Variante überein? (2) Falls es sich um die
Vehtari-Variante handelt: sollte das eigene Paper diese (statt oder
zusätzlich zu gelman1992/brooks1998) zitieren, um korrekt zu attribuieren,
was tatsächlich berechnet wird?

- Verwendet in: {Datei/Funktion, noch offen zu füllen}
- Unbestätigter Hinweis (nicht Teil der eigentlichen Spec-Prüfung): siehe
  identischer Hinweis in `gelman1992_spec.md` ("Bezug zum eigenen Code") –
  gilt hier analog für die multivariate Erweiterung.
