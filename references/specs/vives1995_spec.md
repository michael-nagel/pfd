# Spec: vives1995 – The Speed of Information Revelation in a Financial Market Mechanism

## Quelle
- Seiten/Abschnitt der Originalarbeit: Journal of Economic Theory, Vol. 67
  (1995), S. 178–204 (Xavier Vives). Datei: `references/literature/
  vives_1995.pdf` (Titel im Dokument geprüft und bestätigt: "The Speed of
  Information Revelation in a Financial Market Mechanism"). Zentral:
  Section 2 "A Static Financial Market Model" (S. 182–185, Proposition
  2.1/2.2), Section 3 "An Information Tâtonnement Process" (S. 185–188,
  Proposition 3.1, dynamische Verallgemeinerung), Section 5 "The Speed of
  Information Revelation" (S. 192–193, **Proposition 5.1/5.2, der im
  eigenen Paper zitierte Kernbefund**).
- Zitiert in eigenem Paper: (1) Abschnitt zur Lernraten-Schätzung
  ("we estimate the learning rate using the methodology outlined by
  \citet{biais1999}... The procedure builds on the work of
  \citet{vives1995}, who characterizes the asymptotic speed of learning
  as..."; Zeile 401 von `oup-authoring-template2.tex`); (2) im
  Ergebnisteil, direkter Zahlenvergleich (Zeile 821): "Our estimated
  learning rates for the tennis sports betting market are inconsistent
  with the theoretical prediction of 0.5 by \citet{vives1995}... and with
  the extension to 1.5 by \citet{germain1996}... Furthermore,
  \citet{biais1999} find an even higher learning rate of 2.7...".

Hinweis zur Extraktionsqualität: `pdftotext -layout` lieferte für dieses
PDF **komplett leeren Text** (0 Bytes Output trotz 27 Seiten laut
`pdfinfo`) – anders als bei den bisher geprüften gescannten Papers
(hansen1982, gelman1992: verstümmelter, aber vorhandener Text), hier
offenbar überhaupt keine extrahierbare Textebene (Producer laut
`pdfinfo`: "Acrobat PDFWriter 2.01 for Windows", ein sehr altes,
wahrscheinlich rein rasterbasiertes Digitalisat ohne OCR-Schicht). Ich
habe daher **alle** unten stehenden Gleichungen und Aussagen durch
Rendern der jeweiligen Seiten (PDF-Seiten 1, 6–8, 10–12, 15–16, entspr.
Druckseiten 178, 183–185, 187–189, 192–193) als 150-dpi-PNGs visuell aus
dem Original transkribiert. Keine Formel in diesem Dokument stammt aus
Text-Extraktion.

## Methode/Modell

### A. Statisches Basismodell (Section 2, S. 182–183)

Ein risikobehaftetes Asset mit (ex post) Liquidationswert v, gehandelt
zwischen einem Kontinuum informierter Agenten i∈[0,1] und Noise-Tradern,
vermittelt durch kompetitive, risikoneutrale Market Maker. Agent i hat
CARA-Nutzen `U(π_i) = −exp{−ρπ_i}`, Gewinn `π_i = (v−p)x_i`. Privates
Signal: `s_i = v + ε_i` (v, ε_i unkorreliert; ε_i auch untereinander
unkorreliert; gepooltes Signal `s̃ = ∫₀¹ s_i di = v` f.s. per Konvention).
Noise-Trader-Orderfluss: `u_1 − α_1 p_1` (u_1 zufällig, α_1 Konstante).
Order-Book:
```
L_1(p_1) = x̃_1 + u_1 − α_1 p_1,   mit  x̃_1 = ∫₀¹ X_{1i}(s_i) di
```
Alle Zufallsvariablen normalverteilt: v ~ (v̄, σ_v²); s_i | v ~ (v, σ_ε²);
u_1 ~ (0, σ_u²). Präzisions-Notation: τ_x ≡ (σ_x²)^{−1} für beliebige
Zufallsvariable x. τ_1 ≡ [Var(v|p_1)]^{−1} = Informativität des Preises.

**Proposition 2.1** (eindeutiges lineares Gleichgewicht, statischer Fall):
```
X_1(s_i) = a_1(s_i − v̄),   p_1 = λ_1 ω_1 + v̄
```
wobei `a_1 = (ρ(σ_ε² + Var p_1))^{−1}` die eindeutige positive Nullstelle
der kubischen Gleichung `F_1(a) ≡ (ρτ_ε a − 1)τ_v + ρλ_1a² = 0` ist, mit
`λ_1 = τ_u a/τ_1`, `τ_1 = τ_v + τ_u a²`.

**Proposition 2.2** (komparative Statik, S. 184): a_1 und τ_1 fallen mit
ρ, σ_ε², σ_v² und steigen mit σ_u²; Var(p_1) fällt mit ρ, σ_ε², σ_u² und
steigt mit σ_v²; erwartetes Handelsvolumen `E|x̃_1| = (2/π)^{1/2}a_1σ_ε`
fällt mit ρ, σ_ε² und steigt mit σ_u².

### B. Dynamische Erweiterung: Informations-Tâtonnement (Section 3, S. 185–188)

Unendlicher Horizont: in Runde n besteht Wahrscheinlichkeit γ_n
(nichtfallende Folge), dass v realisiert und Handel abgeschlossen wird
(gegeben, dass bis Runde n kein Handel stattfand). Informierte Agenten
reichen Marktorders basierend auf privatem Signal UND öffentlicher
Information (bisherige Preisnotierungen p^{n−1}) ein; Market Maker
bepreisen effizient anhand des kumulierten Orderbuchs. Wegen
Bertrand-Wettbewerb und gemeinsamer Normalverteilung ist p_{n−1} eine
suffiziente Statistik für die gesamte Preishistorie: `E(v|p^{n−1}) =
p_{n−1}`; Preise folgen einem Martingal.

**Proposition 3.1** (eindeutiges lineares dynamisches Gleichgewicht,
n=1,2,…):
```
X_n(s_i, p^{n−1}) = a_n(s_i − p_{n−1}),   p_n = λ_n ω_n + p_{n−1},
ω_n = a_n(v − p_{n−1}) + u_n
```
mit `a_n = (ρ(σ_ε² + Var(p_n|p_{n−1})))^{−1}`, eindeutige positive
Nullstelle der rekursiven kubischen Gleichung
`F_n(a_n) ≡ (ρ(τ_ε)^{−1}a_n − 1)τ_{n−1} + ρλ_na_n² = 0`, mit
```
λ_n = τ_u a_n/τ_n,   τ_n = τ_v + τ_u Σ_{t=1}^n a_t²,
Var{p_n|p_{n−1}} = (τ_{n−1})^{−1} − (τ_n)^{−1}
```
(τ_n hier: Informativität von p_n, akkumuliert über alle Runden).

### C. Konvergenzgeschwindigkeit (Section 5, S. 192–193, **Kernresultat**)

**Proposition 5.1** (Asymptotik der Marktparameter, n→∞):
1. Reaktionsstärke `a_n` steigt monoton gegen `a = (ρσ_ε²)^{−1}`.
2. Informativität `τ_n` steigt monoton unbeschränkt, mit Rate n:
   `Aτ_∞ ≡ lim_{n→∞} n^{−1}τ_n = τ_u a²`.
3. Markttiefe `λ_n^{−1}` steigt unbeschränkt mit Rate n.
4. Unbedingte Preisvolatilität `Var p_n` steigt monoton gegen σ_v²;
   bedingte Volatilität `Var{p_n|p_{n−1}}` fällt gegen 0.
5. Erwartetes Handelsvolumen informierter Agenten
   `E|x̃_n| = (2/π)^{1/2}a_n√(Var(v|p_{n−1}))` fällt gegen 0.

**Proposition 5.2** (Preis als Schätzer von v, **der im eigenen Paper
zitierte Satz**, wörtlich zentral, S. 193):
> (i) biased (in the sense of regression toward the mean:
> Sign{E{(v−p_n)|v}} = Sign{v−v̄})
> (ii) strongly consistent (that is, p_n → v a.s.)
> (iii) **normal with asymptotic variance (Aτ_∞)^{−1} = σ_u²ρ²σ_ε^4 and
> convergence rate 1/√n (that is, √n(p_n−v) →^d N(0, σ_u²ρ²σ_ε^4))**.

Dies ist die exakte, formal bewiesene Grundlage für die im eigenen Paper
(und in der Einleitung des Originals, S. 180) prosaisch formulierte
Aussage "Price quotations converge to the underlying value of the asset
v at a rate of 1/√n" – und damit für die "theoretical prediction of 0.5"
(der Exponent von n in der Konvergenzrate p_n−v = O_p(n^{−1/2})).

### D. Kontrastresultat ohne Market Maker (Section 6, nur die
zusammenfassende Aussage aus der Einleitung transkribiert, S. 181,
NICHT im Detail aus Section 6 selbst nachvollzogen – siehe
Unsicherheiten):
> "Removing the market makers results in a market of constant depth...
> and the speed of convergence of prices to v is much slower: 1/√(n^{1/3})."

## Schätzverfahren
- Nicht zutreffend im Sinne eines Schätzverfahrens für Daten: vives1995
  ist ein rein theoretisches Modell (Beweis von Existenz/Eindeutigkeit
  eines linearen Gleichgewichts und dessen asymptotischer Eigenschaften),
  keine empirische Schätzung. Liefert einen **theoretischen Benchmark-
  Wert** (γ_theoretisch = 0.5 im Sinne der Konvergenzraten-Exponenten),
  gegen den die eigene empirische GMM-Schätzung von γ verglichen wird.
- Instrumente/Moment-Bedingungen (falls GMM): nicht zutreffend – kein GMM
  in vives1995 selbst. Die strukturelle Analogie liegt darin, dass
  biais1999 (siehe `biais1999_spec.md`) UND das eigene Paper denselben
  Parameter γ über eine Momentbedingung mit Exponent `((t−1)/t)^{2γ}`
  auf die Varianz des Preisfehlers schätzen – Vives (1995) Proposition
  5.2(iii) impliziert für dieses Modell γ = 0.5 (da Var(p_n−v) = O(n^{−1}),
  also Exponent 1 in der Varianz = 2×0.5 im Sinne der `((t−1)/t)^{2γ}`-
  Konvention).

## Erwartete Ergebnisse (falls im Original berichtet)
- Kein empirisches Ergebnis (rein theoretisches Paper). Der einzige
  "Zahlenwert" ist der implizite Konvergenzraten-Exponent 1/2 aus
  Proposition 5.2(iii) (siehe oben) – dies ist der Wert, den das eigene
  Paper als "theoretical prediction of 0.5" zitiert.

## Unsicherheiten
- Section 4 (Beweise zu Section 3, S. 188–191) und Section 6 (Entfernung
  der Market Maker), Section 7 (komparative Dynamik) sowie die
  Concluding Remarks wurden **nicht im Detail gelesen/transkribiert** –
  nur die für den eigenen Zitationskontext (Konvergenzrate, γ=0.5-
  Benchmark) zentralen Abschnitte 2, 3 und 5. Die in Section 6
  berichtete Kontrastrate 1/√(n^{1/3}) (ohne Market Maker) stammt aus der
  Zusammenfassung in der Einleitung (S. 181), nicht aus einer eigens
  geprüften Proposition in Section 6 selbst – falls diese Kontrastrate
  für die eigene Diskussion relevant werden sollte, müsste Section 6
  gesondert geprüft werden.
- Ich habe nicht geprüft, ob der Exponent 2γ in der eigenen/biais1999
  GMM-Momentbedingung (`((t−1)/t)^{2γ}`, siehe `biais1999_spec.md`)
  tatsächlich dieselbe Größe misst wie Vives' asymptotische Varianzrate
  `Var(p_n−v) = (Aτ_∞)^{−1}/n` – die Übereinstimmung "γ=0.5" wurde von
  mir aus der Analogie der Funktionalform hergeleitet (Var ∝ n^{−1} ⇔
  Exponent 2γ=1 ⇔ γ=0.5 in der `((t−1)/t)^{2γ}`-Konvention), NICHT durch
  einen expliziten Vergleich der beiden Modellableitungen (Vives'
  Marktmikrostruktur-Tâtonnement vs. Biais et al.'s bzw. das eigene
  GMM-Setup). Diese Analogie erscheint plausibel (beide Paper werden im
  eigenen Text in direktem Zusammenhang mit derselben Zahl 0.5 zitiert),
  wird hier aber explizit als Annahme und nicht als verifizierte
  Äquivalenz gekennzeichnet.
- Die im eigenen Paper (Zeile 821) zusätzlich genannte "extension to 1.5
  by \citet{germain1996}" bezieht sich auf ein anderes Paper
  (germain1996), das laut `citation_map.md` NICHT zu den zu prüfenden
  Kern-Referenzen gehört und hier entsprechend nicht geprüft wurde.

## Bezug zum eigenen Code
- Kein direkter Code-Bezug: vives1995 liefert ausschließlich einen
  **theoretischen Vergleichswert** (γ=0.5) für die Diskussion/
  Interpretation der empirisch geschätzten Lernraten γ im eigenen Paper
  (Zeile 821 von `oup-authoring-template2.tex`), wird selbst aber nicht
  algorithmisch implementiert. Der empirische Schätzparameter γ wird wie
  in `biais1999_spec.md` beschrieben in `src/pfd/utils/_gen_meth_mom.py`
  (`_GenMethMom.momcond`) und `src/pfd/helpers/fit_gmm_mod.py` erzeugt.
- Kein Widerspruch/keine methodische Abweichung festgestellt, die einen
  Eintrag in `references/specs/open_questions.md` rechtfertigen würde:
  Die Zitierung im eigenen Paper ist korrekt als **theoretischer
  Kontrastwert** ("inconsistent with the theoretical prediction of 0.5")
  formuliert, nicht als Behauptung methodischer Identität mit dem
  eigenen Schätzverfahren.
- Verwendet in: {Datei/Funktion, noch offen zu füllen} – ausschließlich
  in der Ergebnisdiskussion des Papers (Textzitat), keine Code-Datei.
