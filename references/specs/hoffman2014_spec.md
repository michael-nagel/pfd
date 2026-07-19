# Spec: hoffman2014 – The No-U-Turn Sampler: Adaptively Setting Path Lengths in Hamiltonian Monte Carlo

## Quelle
- Seiten/Abschnitt der Originalarbeit: Journal of Machine Learning Research,
  Vol. 15 (2014), S. 1593–1623 (Hoffman, Gelman). Zentral: Section 2
  (Hamiltonian Monte Carlo, S. 1594–1596, Algorithm 1), Section 3.1
  "No-U-Turn Hamiltonian Monte Carlo" (S. 1596–1600, Kriterium und
  rekursiver Verdopplungsalgorithmus), Section 3.2 "Setting the Step Size"
  (S. 1600–1610, Dual-Averaging-Adaption, δ-Parameter, Algorithmen 4–6).
- Zitiert in eigenem Paper: Appendix "Bayesian Estimation – Algorithms and
  Procedures" ("The No-U-Turn sampler (NUTS), as proposed by
  \citet{hoffman2014}, is a recursive algorithm for continuous variables
  based on Hamiltonian mechanics... We utilize the Rust implementation,
  Nutpie... For the NUTS estimations, we increase the acceptance
  probability slightly to 0.85 from the default 0.8...").

Hinweis zur Extraktionsqualität: `pdftotext -layout` lieferte für dieses
PDF (digital erzeugt) durchgehend sauberen Text inklusive der meisten
Gleichungen. EINE Ausnahme: die Dual-Averaging-Schrittweiten-Update-Formel
in Algorithm 5/6 wurde durch Zeilenumbruch beim Wurzelzeichen mehrdeutig
extrahiert ("log m = µ − γm H̄m" – unklar, ob dies "µ − (√m/γ)H̄_m" oder
"µ − γ√m·H̄_m" bedeutet). Ich habe daher die betroffene Seite (S. 1610,
PDF-Seite 18) als Bild gerendert und visuell bestätigt: die korrekte Formel
ist **log ε_m = µ − (√m/γ) H̄_m**.

## Methode/Modell

- **Algorithm 1 – Basis-HMC (S. 1594)**: Erweiterung des Zielraums um einen
  Impulsvektor r ~ N(0,I), gemeinsame (unnormierte) Dichte
  ```
  p(θ, r) ∝ exp{L(θ) − ½ r·r}
  ```
  L = Log-Dichte der Zielverteilung (bis auf Normierungskonstante).
  Leapfrog- (Störmer-Verlet-)Integrator:
  ```
  r_{t+ε/2} = r_t + (ε/2)∇_θL(θ_t);   θ_{t+ε} = θ_t + ε r_{t+ε/2};
  r_{t+ε} = r_{t+ε/2} + (ε/2)∇_θL(θ_{t+ε})
  ```
  Metropolis-Akzeptanzwahrscheinlichkeit nach L Leapfrog-Schritten:
  ```
  α = min{1, exp{L(θ̃) − ½ r̃·r̃} / exp{L(θ_{m−1}) − ½ r_0·r_0}}
  ```

- **No-U-Turn-Kriterium (Gl. 1, S. 1596)**: Ableitung der halben
  quadrierten Distanz zwischen Start- und aktueller Position nach der Zeit:
  ```
  d/dt [ (θ̃−θ)·(θ̃−θ)/2 ] = (θ̃−θ)·r̃                                  (1)
  ```
  Motiviert das Abbruchkriterium "stoppe, wenn dieser Ausdruck negativ
  wird" – ein naiver Algorithmus auf dieser Basis wäre jedoch nicht
  zeit-reversibel. NUTS löst dies durch einen **rekursiven, symmetrisch
  vorwärts/rückwärts simulierenden Verdopplungsalgorithmus** (Abbildung 1,
  S. 1597): bei jeder Verdopplung j wird zufällig eine Richtung
  (vorwärts/rückwärts) gewählt und die Hamilton-Dynamik für 2^j
  Leapfrog-Schritte in dieser Richtung simuliert, wodurch ein Binärbaum von
  Zuständen aufgebaut wird.

- **Stoppkriterium in Algorithm 6 (bestätigt aus Text-Extraktion, S. 1600,
  identisch mit dem in Algorithm 2/3 hergeleiteten)**:
  ```
  s ← s' · 𝟙[(θ+ − θ−)·r− ≥ 0] · 𝟙[(θ+ − θ−)·r+ ≥ 0]
  ```
  wobei θ+/θ− bzw. r+/r− die vordersten/hintersten Positions-/
  Impuls-Zustände des aktuell aufgebauten Baums sind; die Rekursion stoppt
  (s=0), sobald der Baum an einem seiner beiden Enden "zurückbiegt"
  (U-Turn) oder eine Simulationsinstabilität auftritt.

- **Setzen der Schrittweite ε via Dual Averaging (Section 3.2)**: Ziel ist
  eine mittlere Akzeptanzwahrscheinlichkeit δ. Für HMC (S. 1608–1609):
  ```
  H_t^HMC ≡ min{1, p(θ̃^t,r̃^t)/p(θ^{t−1},r^{t,0})};
  h^HMC(ε) ≡ E_t[H_t^HMC | ε]
  ```
  Für NUTS (S. 1609, da kein einzelner Accept/Reject-Schritt existiert):
  ```
  H_t^NUTS ≡ (1/|B_t^final|) Σ_{θ,r∈B_t^final} min{1, p(θ,r)/p(θ^{t−1},r^{t,0})};
  h^NUTS ≡ E_t[H_t^NUTS]
  ```
  B_t^final = Menge aller während der letzten Verdopplung von Iteration t
  besuchten Zustände.

- **Algorithm 5/6 – Dual-Averaging-Update (visuell bestätigt, S. 1610)**:
  ```
  H̄_m = (1 − 1/(m+t_0)) H̄_{m−1} + (1/(m+t_0)) (δ − α)
  log ε_m = µ − (√m/γ) H̄_m
  log ε̄_m = m^{−κ} log ε_m + (1 − m^{−κ}) log ε̄_{m−1}
  ```
  Default-Werte für die Dual-Averaging-Hyperparameter (S. 1609, wörtlich):
  γ = 0.05, t_0 = 10, κ = 0.75, µ = log(10ε_0), ε̄_0 = 1, H̄_0 = 0, wobei
  ε_0 aus Algorithm 4 (FindReasonableEpsilon-Heuristik) stammt.

- **Zielakzeptanzrate δ**: für HMC wird unter starken Annahmen ein
  theoretisch optimaler Wert von **δ ≈ 0.65** genannt (Beskos et al. 2010;
  Neal 2011, zitiert S. 1608). In den eigenen Experimenten des Papers
  (Section 4, S. 1610–…) wird ebenfalls für NUTS empirisch ein Optimum
  "around δ = 0.65" gefunden, "suggesting that this is indeed a reasonable
  default value" (S. 1615, Paraphrase – exakte Seitenzahl nicht
  gegengeprüft, siehe Unsicherheiten).

## Schätzverfahren
- Verfahren: HMC / NUTS mit Dual-Averaging-Schrittweitenadaption
  (Algorithmen 1–6, siehe oben).
- Hyperparameter/Tuning-Werte aus dem Original: γ=0.05, t_0=10, κ=0.75
  (Dual Averaging, fest in allen Experimenten des Papers); δ als
  einstellbarer Zielwert – Original empfiehlt δ≈0.65 als sinnvollen
  Default (siehe oben), NICHT 0.8.
- Instrumente/Moment-Bedingungen: nicht zutreffend (kein GMM).

## Erwartete Ergebnisse (falls im Original berichtet)
- Section 4 (S. 1610ff.) enthält umfangreiche empirische Vergleiche von
  HMC und NUTS (Effective Sample Size pro Gradientenauswertung) über vier
  Zielverteilungen (u.a. multivariate Normal-, hierarchisches logistisches
  Regressions-, stochastisches Volatilitätsmodell) und 15 (NUTS) bzw. 8
  (HMC) δ-Werte zwischen 0.25 und 0.95. Diese Werte sind reine
  Sampler-Effizienz-Benchmarks auf synthetischen/anderen empirischen
  Modellen und nicht auf die eigene Anwendung (Lernraten-Schätzung im
  Tenniswettmarkt) übertragbar – daher hier nicht im Detail transkribiert.
  Relevant ist nur die qualitative Schlussfolgerung δ≈0.65 als
  angemessener Default (siehe oben).

## Unsicherheiten
- Die Dual-Averaging-Update-Formel wurde wie oben beschrieben durch
  Seitenrendering visuell bestätigt (log ε_m = µ − (√m/γ)H̄_m). Alle
  anderen Formeln in diesem Dokument stammen aus der (für diese PDF
  überwiegend sauberen) Text-Extraktion und wurden NICHT zusätzlich
  bildlich verifiziert – bei Bedarf für eine besonders kritische
  Anwendung sollte dies nachgeholt werden, insbesondere Algorithm 6
  (vollständige NUTS-Rekursion inkl. BuildTree-Unterfunktion, die hier
  nicht im Detail transkribiert wurde, siehe unten).
- Die vollständige `BuildTree`-Rekursionsfunktion (Kernstück von
  Algorithm 3/6, die den Binärbaum rekursiv aufbaut) wurde NICHT
  transkribiert – nur das übergeordnete Doubling-Verfahren und das
  Stoppkriterium. Für eine vollständige algorithmische Nachvollziehbarkeit
  (z.B. Code-Review von Nutpie/PyMC) müsste diese Funktion (S. 1598–1600
  im Original) gesondert transkribiert werden.
- Die genaue Seitenzahl für die Aussage "occurs around δ=0.65,
  suggesting that this is indeed a reasonable default value" wurde aus
  einer früheren Stichwortsuche übernommen (Zeile ~1325 der
  Text-Extraktion) und nicht nochmals einzeln auf der Seite
  gegengeprüft – die Kernaussage (δ≈0.65 als empfohlener Default) ist
  jedoch durch zwei unabhängige Stellen im Text belegt (Beskos/Neal-Zitat
  UND eigene Experimente des Papers).

## Bezug zum eigenen Code

**Wichtiger Befund – mögliche Unschärfe in der eigenen Paper-Formulierung**
(auch an `references/specs/open_questions.md` angehängt):

Das eigene Paper schreibt: "we increase the acceptance probability
slightly to 0.85 from **the default 0.8**". Diese Formulierung könnte so
gelesen werden, als stamme der Wert 0.8 aus Hoffman and Gelman (2014)
selbst. Tatsächlich empfiehlt das Original jedoch **δ ≈ 0.65** als
sinnvollen Default (sowohl theoretisch für HMC als auch empirisch für
NUTS in den eigenen Experimenten des Papers, S. 1608 und Section 4). Der
Wert 0.8 als "Default" ist – soweit hier nachvollziehbar – eine spätere
Konvention der Software-Implementierungen (PyMC/Stan), nicht ein aus
Hoffman and Gelman (2014) selbst zitierter Wert. Dies ist wahrscheinlich
keine sachliche Falschaussage (das eigene Paper zitiert hoffman2014 nur
für den NUTS-Algorithmus selbst, nicht explizit für den Wert 0.8), aber
die Formulierung "the default 0.8" ohne Quellenangabe könnte bei
Leserinnen und Lesern den Eindruck erwecken, dieser Wert stamme aus der
zitierten Originalarbeit.

**Zu klären:** Sollte im eigenen Paper klargestellt werden, dass "0.8" der
Software-Default (PyMC) ist, während Hoffman and Gelman (2014) selbst
δ≈0.65 empfehlen?

- Verwendet in: {Datei/Funktion, noch offen zu füllen}
- Unbestätigter Hinweis (nicht Teil der eigentlichen Spec-Prüfung):
  `src/pfd/utils/est_pm_mod.py` übergibt `target_accept` an
  `nutpie.sample(...)`, mit dem Wert `cfg.sampling.targ_acpt` aus der
  Config (Standardkonfiguration: 0.85 laut `conf/config.yaml`) – nicht
  gegen die obige δ-Definition im Detail geprüft, bitte separat
  verifizieren, ob Nutpie intern exakt Algorithm 6 (Dual Averaging mit
  γ=0.05, t_0=10, κ=0.75) implementiert oder eine abweichende
  Parametrisierung verwendet.
