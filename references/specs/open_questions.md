# Open Questions

Gesammelte methodische Abweichungen/Widersprüche zwischen Original-Papers
und eigenem Code/Paper, die beim Erstellen der Spec-Dateien aufgefallen
sind. Nur anhängen, nichts Bestehendes verändern.

## biais1999: fehlender K-Nuisance-Parameter in den Momentbedingungen

Quelle: `references/specs/biais1999_spec.md`, Abschnitt "Bezug zum eigenen
Code".

Biais, Hillion, and Spatt (1999), Gleichung (12) (S. 1240), definiert die
GMM-Momentbedingungen für die Lernrate γ mit einem zusätzlichen
Nuisance-Parameter **K** (Varianz des Proxy-Fehlers φ = v̂ − v zwischen
beobachtetem Schlusskurs-Proxy und wahrem Wert v):

```
E[ (P_t−v̂)² − ((t−1)/t)^{2γ}(P_{t−1}−v̂)² − K(1−((t−1)/t)^{2γ}) | I_{t−2} ] = 0
```

Der eigene Code (`src/pfd/utils/_gen_meth_mom.py`, `_GenMethMom.momcond`)
sowie die eigene Herleitung im Paper (Gleichungen "expres_1"/"express_2"/
"moment_conditions") verwenden dieselbe Struktur **ohne den K-Term** und
schätzen nur γ (`k_params=1` in `src/pfd/helpers/fit_gmm_mod.py`).

Mögliche Erklärung: im eigenen Setting ist die terminale Größe der exakte
Spielausgang ω ∈ {0,1} (kein Preis-Proxy für einen unbeobachteten
"wahren Wert" wie bei Biais et al.), sodass der Proxy-Fehler φ ≡ 0 und
K = 0 plausibel gerechtfertigt sein könnte. Diese Annahme wird im eigenen
Paper jedoch an keiner Stelle explizit benannt oder begründet – der Text
erweckt durch "Following \citet{biais1999}, we employ the following seven
instruments" den Eindruck einer direkten Übernahme, obwohl die
Momentbedingung selbst (nicht nur die Instrumente) modifiziert wurde.

**Zu klären:** Ist die K=0-Annahme beabsichtigt und sollte im Paper explizit
begründet werden (z.B. in einer Fußnote zu §3.7), oder wurde K beim
Übertragen der Methodik versehentlich weggelassen?

## hansen1996: CUE-Optimierungsverfahren weicht vom Original ab

Quelle: `references/specs/hansen1996_spec.md`, Abschnitt "Bezug zum
eigenen Code".

Hansen, Heaton, and Yaron (1996) verwenden für die CUE-Schätzung primär
ein gradientenbasiertes Quasi-Newton-Verfahren (MATLAB `fminu.m`) mit
mehreren Startwerten (inkl. dem wahren Parametervektor, da Monte-Carlo-
Studie), und fallen erst bei Konvergenzproblemen auf eine
Nelder-Mead-Simplex-Suche (`fmins.m`) zurück. Die Originalarbeit merkt
außerdem explizit an: "the continuous-updating criterion can make
numerical search for the minimizer difficult."

Der eigene Code (`src/pfd/helpers/fit_gmm_mod.py`) verwendet
`optim_method="nm"` (Nelder-Mead) **direkt und ausschließlich**, auch für
die CUE-Schätzung – also genau das Verfahren, das im Original nur als
Rückfalloption vorgesehen war, nicht als Primärmethode.

Verwandter Befund in biais1999 (siehe deren Spec-Datei): dort wird für die
CUE-Schätzung stattdessen eine erschöpfende Gittersuche über γ und K
verwendet (kein Optimierer im engeren Sinn), was allerdings nur bei 2
Parametern praktikabel ist.

**Zu klären:** Ist Nelder-Mead als alleiniges Verfahren für die
CUE-Schätzung im eigenen 1-Parameter-Fall (nur γ je Buchmacher) robust
genug, oder sollte – wie im Original nahegelegt – zusätzlich ein
gradientenbasiertes Verfahren mit mehreren Startwerten zum Vergleich
herangezogen werden, gerade weil die Originalarbeiten selbst auf
numerische Schwierigkeiten bei der CUE-Minimierung hinweisen?

## hoffman2014: "default 0.8" vs. im Original empfohlenes δ≈0.65

Quelle: `references/specs/hoffman2014_spec.md`, Abschnitt "Bezug zum
eigenen Code".

Das eigene Paper schreibt (Appendix "Bayesian Estimation – Algorithms and
Procedures"): "we increase the acceptance probability slightly to 0.85
from the default 0.8." Diese Formulierung steht direkt im Anschluss an
den Satz, der NUTS unter Zitation von \citet{hoffman2014} einführt, was
den Eindruck erwecken könnte, der Wert 0.8 stamme aus dieser
Originalarbeit.

Tatsächlich empfiehlt Hoffman and Gelman (2014) selbst **δ ≈ 0.65** als
sinnvollen Default – sowohl unter Verweis auf Beskos et al. (2010) und
Neal (2011) für HMC (S. 1608) als auch basierend auf eigenen Experimenten
des Papers für NUTS (Section 4: "occurs around δ = 0.65, suggesting that
this is indeed a reasonable default value"). Der Wert 0.8 ist – soweit
recherchierbar – eine spätere Konvention der Software-Implementierungen
(PyMC/Stan), nicht ein Wert aus der zitierten Originalarbeit selbst.

**Zu klären:** Sollte im eigenen Paper klargestellt werden, dass "0.8" der
Software-Default (PyMC), nicht der von Hoffman and Gelman (2014) selbst
empfohlene Wert (≈0.65) ist, um Fehlzuschreibungen an die zitierte Quelle
zu vermeiden?

## gelman1992/brooks1998: fehlerhafter vs. korrigierter R̂-Korrekturfaktor, keine Korrektur im multivariaten Fall

Quelle: `references/specs/gelman1992_spec.md` (Abschnitt "Nachtrag") und
`references/specs/brooks1998_spec.md` (Abschnitt "Bezug zum eigenen
Code").

Das eigene Paper zitiert gelman1992 und brooks1998 gemeinsam für "the
Gelman-Rubin statistic R̂", ohne zwischen zwei tatsächlich verschiedenen
Formeln zu unterscheiden:

1. Gelman and Rubin (1992a) definieren (Section 6, Schritt 6):
   `√R̂ = √[(V̂/W) · (ν/(ν−2))]`.
2. Brooks and Gelman (1998, S. 438) stellen dazu explizit fest: "Gelman
   and Rubin (1992a) **incorrectly adopted** the correction factor
   d/(d−2). This incorrect factor has led to a number of problems, in
   that the corrected SRF (CSRF) can be infinite or even negative in the
   cases where convergence is so slow that d < 2." Sie ersetzen den
   Faktor durch `(d+3)/(d+1)`, sodass `R̂_c = ((d+3)/(d+1))(V̂/W)`.
3. Die multivariate Erweiterung (MPSRF, brooks1998 Section 4, Gl. 4.1 /
   Lemma 2: `R̂^p = (n−1)/n + ((m+1)/m)λ_1`) enthält AUCH nach der
   Korrektur **keinen** t-Verteilungs-Korrekturfaktor (weder d/(d−2) noch
   (d+3)/(d+1)) – dies wird im gelesenen Abschnitt nicht kommentiert.

Da der eigene Code vermutlich ArviZ' $\hat{R}$-Implementierung verwendet
(die auf der noch neueren, rank-normalisierten Version von Vehtari et al.
2021 beruht, nicht auf einer der beiden hier dokumentierten Fassungen von
1992/1998), ist der konkrete Zahlenwert im eigenen Ergebnis wahrscheinlich
nicht betroffen. Die Zitierung selbst vermischt jedoch eine vom
Original-Autor selbst als "incorrect" bezeichnete Formel mit ihrer
Korrektur, ohne dies kenntlich zu machen.

**Zu klären:** (1) Welche R̂-Variante berechnet ArviZ tatsächlich, und wie
verhält sie sich zu den drei oben genannten Fassungen (gelman1992
unkorrigiert, brooks1998 korrigiert univariat, brooks1998 multivariat
ohne Korrekturfaktor)? (2) Sollte die Zitierung im eigenen Paper
präzisiert werden, um nicht implizit zu suggerieren, gelman1992 und
brooks1998 definierten dieselbe (korrekte) Formel?

## Crossed Random Effects – Methodik (R1-ii)
- **Toolchain-Wechsel**: statsmodels MixedLM kann echte crossed random effects 
  nicht abbilden, wenn ein Faktor (Matchup) über die groups-Grenzen eines 
  anderen (Bookies) hinweg realisiert wird — vc_formula-Random-Effects werden 
  PRO groups-Level separat gezogen, nicht gruppenübergreifend geteilt (verifiziert 
  gegen installierten statsmodels-0.14.0-Quellcode und offizielle Doku). Umstieg 
  auf R/lme4 2.0.6 via rpy2==3.6.7 für alle drei betroffenen Modelle 
  (resp_to_info, ags_test "All"-Zweig, unbiasedness_reg).
- **REML vs. ML**: bestehender statsmodels-Code nutzt durchgängig reml=False 
  (ML). lme4-Default ist REML=TRUE. Entscheidung: REML=FALSE für alle 
  lme4-Fits, um Konsistenz mit dem bestehenden Schätzparadigma zu wahren – 
  Abweichung vom Lehrbuch-Standard (REML wäre bei unverändertem Fixed-Effects-
  Teil und nur unterschiedlicher Random-Effects-Struktur eigentlich die 
  übliche Wahl für einen validen LR-Test), bewusst in Kauf genommen für 
  Vergleichbarkeit mit dem Rest des Papers.
- **Original-Modell zusätzlich in lme4 refitten**: für einen sauberen LR-Test 
  (Original vs. Crossed) muss das bookmaker-only-Modell zusätzlich einmal in 
  lme4 gefittet werden (reine Kontrollrechnung, kein Ersatz für den 
  statsmodels-Code im Paper), da ein LR-Test über zwei verschiedene 
  Implementierungen (statsmodels-Loglik vs. lme4-Loglik) nicht formal valide 
  wäre. Der direkte statsmodels-Original vs. lme4-Crossed-Vergleich bleibt als 
  informelle Zusatzinfo, ist aber kein sauberer Test.

## Crossed Random Effects – match_var Interpretation (eq:resp_to_info)
- match_var (1,1493) ist ~4 Größenordnungen größer als alle Bookies-
  Varianzkomponenten. Ursache identifiziert (nicht Artefakt, nicht Bug): 
  RtrnClsEnd = Match/ClsOdds - 1 (bookmaker_accuracy.py:84). Bei Match==0 ist 
  RtrnClsEnd mathematisch IMMER exakt -1, unabhängig von ClsOdds oder 
  Bookmaker - eine Eigenschaft jeder Return-Metrik auf eine binäre Wette 
  (voller Verlust bei Niederlage), keine Besonderheit dieses Datensatzes.
- Bestätigt über 3 unabhängige Wege: lme4-Fit (match_var), reine ANOVA-
  Zerlegung (99,72% Between-Match-Varianz, 53% der Matches mit exakt 0 
  Within-Match-Varianz), Code-Analyse der Formel.
- Konsequenz für Interpretation im Paper/Reviewer-Antwort: Crossed-Effects-Fix 
  bleibt notwendig und korrekt (R1-ii adressiert), ABER match_var NICHT als 
  Evidenz für "Informations-Konvergenz zwischen Bookmakern" verkaufen - 
  substanzieller Teil ist mathematische Trivialität der Return-Definition bei 
  Verlust, nicht ökonomische Entdeckung. Echte bookmaker-abhängige Variation 
  nur bei Match==1 (86.097 von 169.574 Zeilen) vorhanden.
- Sensitivitäts-Fit auf Match==1-Teilmenge geplant, um zu prüfen ob match_var 
  auch ohne die mechanische Komponente substanziell bleibt.
- Zu prüfen: liegt dieselbe Struktur (Zielgröße deterministisch vom 
  Match-Ausgang abhängig) auch bei eq:ags_test/eq:unbiasedness_reg vor?
- Sensitivitäts-Fit (Match==1 only, n=86.097) bestätigt: match_var fällt von 
  1,1493 auf 0,7265 (~37% mechanisch bedingt durch RtrnClsEnd≡-1 bei Match==0), 
  bleibt aber weiterhin ~2 Größenordnungen über allen Bookies-Varianzkomponenten 
  - R1-ii-Befund hält auch nach Bereinigung.
- Nebenbefund: bookies_slope_var steigt in der Wins-only-Teilmenge um Faktor 
  ~10 (0,000516→0,005130). Plausible Erklärung: Match==0-Zeilen sind für 
  RtrnOpnCls-Slope uninformativ (RtrnClsEnd konstant -1, unabhängig von 
  RtrnOpnCls), verdünnen dadurch die erkennbare Bookmaker-Slope-Heterogenität 
  in der Gesamtstichprobe. Nicht weiter verifiziert, für spätere Robustheits-
  Diskussion vormerken.
- Symbolische Prüfung (keine exakte-Null-Kollaps-Struktur bei den Zielgrößen 
  von eq:ags_test und eq:unbiasedness_reg) durchgeführt, empirische 
  Bestätigung ausstehend/folgt.
- Empirische Between/Within-Prüfung für die anderen beiden Zielgrößen 
  (keine Modellschätzung, rein deskriptiv): fit_rfa_mod (Endog=FEOpn-FECls): 
  82,53%/17,47% Between/Within, kein exakte-Null-Degenerationsmuster wie bei 
  RtrnClsEnd - moderater, unproblematischer Match-Cluster-Effekt erwartet.
  fit_mixed_lm (Endog=Match-OddsMvt0): 99,35%/0,65% Between/Within, fast so 
  extrem wie RtrnClsEnd, aber NICHT durch dieselbe algebraische Degeneration 
  verursacht (nur 0,5% der Matchup-Gruppen mit exakt 0 Within-Varianz statt 
  53%). Plausible Erklärung: OddsMvt0 (Opening-Preis) ist zwischen 
  Bookmakern bei Markteröffnung naturgemäß ähnlich, bevor sich Preise 
  auseinanderentwickeln - ökonomisch substanzieller Befund über 
  Preisbildung, nicht mathematische Trivialität. Sollte im Paper 
  entsprechend anders eingeordnet werden als der RtrnClsEnd-Befund.
- **Abschluss-Vermerk**: alle drei Modelle (gpm, rfa, unbiasedness_reg) 
  vollständig in results/crossed_comparison_summary.csv (60 Zeilen) und 
  results/crossed_comparison_coefs.csv (413 Zeilen) erfasst. Parallelisierung 
  (spawn-Kontext, Pool-Initializer-Muster) validiert - exakte Übereinstimmung 
  gegen sequenziellen Refit bestätigt, Details siehe Chat-Verlauf/
  Commit-Historie. Offen für die Paper-Überarbeitung: match_icc (Anteil der Gesamtvarianz durch 
  Matchup erklärt) wurde als Idee diskutiert, aber für keines der drei Modelle 
  tatsächlich in results/crossed_comparison_summary.csv ergänzt - offene 
  Entscheidung, ob das für die finale Interpretation/Reviewer-Antwort noch 
  nachgeholt wird.

## Imputation – Befunde aus Review-Revision
- Look-Ahead-Leck bestätigt (sauberer a/b-Test): Match als Imputer-Feature 
  erzeugt ausgangs-korrelierte Differenz (corr 0,56-0,88 in OddsMvt0-4, die 
  60% der Imputation ausmachen), Absolutbetrag winzig (~0,0001), 
  BayesianRidge-Koeffizient auf Match Rang 51/51. Entscheidung: Match aus 
  Imputer-Features entfernt (kein inhaltlicher Grund, beseitigt Angriffsfläche).
- Paper-Code-Diskrepanz: Appendix (Zeile 1100) beschreibt Features als 
  "implied probabilities of other bookmakers for the same and different 
  matches". Tatsächlich nutzt IterativeImputer die anderen Spalten DERSELBEN 
  Zeile = die eigenen späteren Preise desselben Bookmakers (OddsMvt1..50) als 
  Hauptprädiktoren (OddsMvt1 dominant, standardisierter Beitrag ~0,19). 
  Appendix-Beschreibung muss korrigiert werden; inhaltlich relevant für 
  R2-C2 (Rückwärts-Information innerhalb des Bookmakers).
- KORREKTUR (Stufe-B-Bericht): Die Einschätzung "Effekt vernachlässigbar" 
  gilt NUR für den Absolutbetrag pro imputierter Zelle, NICHT downstream. 
  Der Match-Fix verschiebt den β₁-Pfad der Unbiasedness-Regressionen um bis 
  zu 0,19 (mittleres |Δ| 0,043); die Kreuzung von β₁=1 wandert von 48% 
  (publizierte Figure 3) auf 56,7%. Signifikanzperzentile ändern sich von 31 
  auf 28, mit anderer Zusammensetzung (frühe raus, späte rein). Mechanismus: 
  OddsMvt0 ist zu 86% imputiert und steht auf beiden Seiten der Regression 
  (Endog = Match − OddsMvt0, Exog = OddsMvt_t − OddsMvt0); eine systematisch 
  ausgangskorrelierte Verschiebung hat dort Hebelwirkung weit über ihren 
  Absolutbetrag hinaus. Tabellen 3–7, alle \var{}-Werte und die GMM-Lernraten 
  bleiben dagegen unverändert (GMM-Änderung 8,9e−5, innerhalb der 
  Nelder-Mead-Toleranz von 8,7e−5).
- Inhaltliche Richtung: Der Look-Ahead täuschte frühe Effizienz vor. Nach dem 
  Fix wird Unverzerrtheit spät im Betting-Fenster erreicht statt sofort – 
  Price Discovery erscheint als Prozess, nicht als Zustand.

## Cross-Section – Code-vs-Paper-Diskrepanzen (Review-Revision)
- REML vs. ML: Table-Notes (tex Z. 723, 761, 1076) behaupten "restricted 
  maximum likelihood", Code fittet aber durchgängig reml=False (ML). Der 
  Per-Bookmaker-AGS (Table 7) ist zudem sm.OLS mit cov_type="HC1", gar kein 
  Mixed Model. Muss angeglichen werden (Text an Code oder umgekehrt) – 
  betrifft auch die R1-ii-lme4-Arbeit, wo REML=FALSE bewusst gewählt wurde.
- R2-C6-Verortung: Der Kommentar zitiert "steeper slopes indicating greater 
  explanatory power" und verortet ihn beim AGS-Slope-Vergleich. Tatsächlich 
  stammt diese Figur (fig:win_props_re, tex Z. 782) aus dem win_rates-Modell 
  (Eq. 3, winning_proportions.py), nicht aus fit_rfa_mod (AGS). R2-C6 muss am 
  win_rates-Modell beantwortet werden.

## Margen/Normalisierung (R1-i/R3-3, R3-2)
Diagnose (rein deskriptiv, gegen Paper-Zahlen validiert: Table 5 Bins und 
fig:rmse-Rangfolge exakt reproduziert):
- Ursprung ist eine einzige rohe Größe: filter_and_shape.py:117, 
  OddsMvt = 1/dez_home (einseitig, nicht normalisiert). Away-Seite wird bei 
  Perspektivwahl (:91-98) verworfen. Alle Cross-Sections (OpnOdds/ClsOdds) 
  UND alle Zeitreihen (OddsMvt0..50) erben diese Größe.
- Marge (Overround): Opening Median 7,82%, Closing 7,61%; schrumpft ~0,2pp 
  Open→Close (bei 55,9% der Gruppen), systematisch aber klein. Bookmaker-
  spezifisch: 4,90% (Pinnacle) bis 8,33% (Interwetten), Spread ~3,4pp.
- Level-Effekt: rohes Preis-Level liegt ~halbe Marge (~3,6pp) zu hoch; 
  Normalisierung zentriert Player-1-Opening-Wahrscheinlichkeit exakt auf 0,50 
  (roh: Median 0,5405). Relevant auch für R2-C1/R2-M5 (Intercept um 0,5).
- Bewegungs-Effekt: raw↔norm Open-to-Close korrelieren 0,997; ~90% echte 
  Belief-Änderung, ~10% Margen-Änderung. Netto-Abwärtsdrift der rohen 
  Bewegung ist vollständig Margen-Artefakt.
- Table 5 robust: Monotonie/Vorzeichen erhalten, ~12% Gruppen wechseln Bin, 
  Extrembins verlieren ~30% Mitglieder und werden "reiner" (Top-Bin-WR 
  0,635→0,652). 
- RMSE robust: Spearman raw vs. norm 0,99, Extremränge stabil.
- WICHTIG für R3-2: Margen-RMSE-Korrelation über Bookmaker ist NEGATIV 
  (−0,34) – margenärmste (sharp) Bookmaker (Pinnacle, BetInAsia) haben die 
  HÖCHSTEN RMSE. R3s implizite Margen-Konfundierungs-Hypothese wird damit 
  widerlegt; die RMSE-Anomalie erklärt sich über Timing (R3-2 eng), nicht 
  über Marge.
- Level-vs-Differenz-Regel: Normalisierung ist materiell bei Größen gegen 
  den Ausgang ω (RtrnClsEnd, FEOpn/FECls/RMSE, GMM-Momentbedingungen, 
  Unbiasedness-Endog), vernachlässigbar bei Differenzen/Ratios gleichseitiger 
  Preise (RtrnOpnCls, DltOpnCls, GMM-Instrumente).
- KONSISTENZ-BEDINGUNG: GMM/Bayesian/Unbiasedness nutzen dieselbe rohe 
  1/dez-Größe wie die Cross-Sections. Konsistente Normalisierung erfordert: 
  (1) Away-Seite durch resample_and_impute mitführen (aktuell verworfen), 
  (2) pro Zeitpunkt normalisieren, (3) Imputation der Frühwerte auf der 
  normalisierten/zweiseitigen Größe konsistent lösen. Punkt 3 kollidiert mit 
  der offenen Imputations-/Zeitachsen-Umstellung – Reihenfolge beachten.

## GMM Exponent (incr/n_per)

Quelle: `references/specs/biais1999_spec.md` (Gl. 12/13, S. 1240–1242);
eigener Code `src/pfd/utils/_gen_meth_mom.py`, `_create_gmm_data.py`.
Belege: `revision/snapshots/E_gmm_exponent_fix/`.

**Befund:** Die Produktionsformel nutzte den Zerfallsfaktor
`((n_per−1)/n_per)^2γ` bzw. `((n_per−2)/(n_per−1))^2γ` — **unabhängig von
`incr`**. Korrekt ist das Verhältnis der **tatsächlichen
Stützstellenpositionen**: `_create_gmm_data` zieht `OddsMvt{n_per − i·incr}`,
bei `incr = 5` also OddsMvt46/41/36, womit der Faktor 42/47 = 0,8936 lauten
muss statt 50/51 = 0,9804 (1-basiert, τ = Index + 1).

Bei `incr = 1` fallen beide Formeln exakt zusammen (τ = 51/50/49 → 50/51 und
49/50) — **dort ist der Code korrekt**. Bei `incr = 5`, dem konfigurierten
Wert, nicht mehr. Der Fehler ist also an `incr` gekoppelt, nicht am Prinzip.

**Beleg über die Invarianz.** Biais Gl. (13): die Momentbedingung ist
invariant gegen Zeitskalierung, die Wahl des Stützstellenabstands darf γ also
nicht verändern. Gemessen mit der Produktionsformel:

| `incr` | 1 | 2 | 5 |
|---|---:|---:|---:|
| γ Mittel | 0,0051 | 0,0016 | 0,0293 |

Nicht invariant. Mit korrigiertem Exponenten kollabiert es bei **festgehaltenen
Stützstellen** (OddsMvt46/41/36) auf 0,0049 — praktisch der `incr = 1`-Wert
0,0051, also genau die von Gl. (13) geforderte Invarianz. Damit ist auch die
Alternativerklärung „anderes Fenster" ausgeschlossen.

**Effekt des Fixes:** `avg_gamma_gmm` 0,0320 → 0,0054 (Faktor ≈ 5,9).
Unverändert: Argmin/Argmax (GGBET/Dafabet) und damit die beiden Namen in
`oup-authoring-template2.tex:820`; Signifikanzmuster 15 → 16 von 24 mit
|t| > 1,96; J-Test-Verwerfungen 1/24 (Interwetten). Rangfolge weitgehend
erhalten (Spearman 0,884), aber **drei materielle Ausreißer in der Feldmitte**
— am stärksten Lasbet (Rang 5 → 19). Ursache: die beiden Momentbedingungen
implizieren unterschiedliche Reskalierungen (5,81 vs. 6,44), der Kompromiss
hängt also von der Datenlage des jeweiligen Bookmakers ab.

**`incr = 5` ist datengetrieben optimal, nicht bloß von Biais übernommen.**
Mit korrigierten Faktoren über alle Abstände:

| `incr` | 1 | 2 | 3 | 4 | **5** | 6 | 8 | 10 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SE Mittel | 0,0095 | 0,0048 | 0,0034 | 0,0027 | **0,0022** | 0,0019 | 0,0015 | 0,0012 |
| γ < 0 | 7/24 | 10/24 | 2/24 | 3/24 | **0/24** | 0/24 | 1/24 | 0/24 |
| \|t\| > 1,96 | 1/24 | 1/24 | 3/24 | 7/24 | **16/24** | 16/24 | 13/24 | 19/24 |

Bei `incr = 1` — dem einzigen Wert, bei dem der alte Code korrekt wäre — sind
7 von 24 Lernraten negativ und genau eine signifikant. **Die Rückkehr zu
`incr = 1` ist also keine Lösung**; der Fix gehört an den Exponenten.

Das stützt zugleich **R1-vi**: Biais' Begründung für weiter auseinander
liegende Stützstellen („less numerical instability in the estimate of this
slope") gilt hier empirisch, sie wurde nicht nur mitübernommen.

**Zu klären:** (1) Zählkonvention bewusst festlegen — 1-basiert (τ = Index+1)
wurde gewählt, weil der Fix damit bei `incr = 1` exakt in die alte Formel
übergeht; 0-basiert (41/46 statt 42/47) ändert γ um max. 9 % je Bookmaker bei
**Rangkorrelation 1,000**, ist also empirisch gleichwertig. (2) Ob die
Größenordnung γ ≈ 0,005 die Interpretation in **R2-C8** verändert. (3) Ob die
drei Rang-Ausreißer die Bookmaker-Vergleiche im Text berühren.

## Bookmaker-Heterogenität der Lernraten — nicht nachweisbar (R1-iv / R2-M8)

Quelle: `revision/snapshots/gmm_rasterfree/_hetero.py`,
`hetero_by_bookie.csv`, `hetero_summary.csv`.
**Eigenständiger Befund, unabhängig von der Spezifikationswahl.**

**Befund:** Die Streuung der 24 bookmakerspezifischen `gamma` ist in **keiner**
Spezifikation größer, als ihre Standardfehler erwarten lassen.

| | V1\|A (publiziert) | V2\|B (Kandidat) |
|---|---:|---:|
| Cochran-Q (df 23) | 23,94 | 18,16 |
| p | **0,407** | **0,749** |
| I² | 3,9 % | **0,0 %** |
| τ zwischen Bookmakern | 0,000410 | 0,000000 |
| sd der γ / mittlere SE | 0,002391 / 0,002213 | 0,002272 / 0,002423 |
| Intervalle ohne den gepoolten Wert | 2 von 24 | **0 von 24** |
| paarweise Kontraste signifikant | 12/276 = **4,3 %** | 5/276 = **1,8 %** |

4,3 % signifikante Kontraste sind exakt Zufallsniveau bei α = 0,05; unter
V2|B liegt der Anteil sogar darunter. Unter V2|B schließt **kein einziges**
95-%-Intervall den gepoolten Wert (0,003555) aus.

**Konsequenz:** Der Wechsel der Bookmaker-Rangfolge zwischen Spezifikationen
(Spearman 0,456) ist **kein Argument gegen eine der Fassungen** — es gibt
keine Ordnung, die brechen könnte. Die nominellen Extremwerte (GGBET,
Dafabet) sind Schätzrauschen.

**Betroffen (Textüberarbeitung, OFFEN):**
- **Abstract**: „find substantial heterogeneity across bookmakers and market
  segments" — der Bookmaker-Teil ist nicht haltbar; der Segment-Teil bleibt.
- `\var{}`: `min_gamma_gmm`, `max_gamma_gmm`, `idxmin_gamma_gmm` (GGBET),
  `idxmax_gamma_gmm` (Dafabet) in `oup-authoring-template2.tex:820`.
- `corr_gamma_loss` / Figure 6 (Lernrate vs. RMSE) — wird nach **R2-M10**
  ohnehin entfernt, ist damit zusätzlich unhaltbar.
- Diskussion in §5.5 und §6, soweit sie Bookmaker-Unterschiede deutet.

**Stützt dagegen:** **R1-iv** (dort bereits: Bookmaker in Eq. 1 mit p = 0,379
und Eq. 3 mit p = 0,595 nicht unterscheidbar — das gilt nun auch für die
Lernraten) und **R2-M8** (Fokus auf Aggregatergebnisse).

**Unberührt:** Der **Segment**-Unterschied Favoriten/Longshots hält:
0,005531 gegen 0,001181 unter V2|B, Differenz +0,004350 bei
t = **4,49**; Longshots bleiben ununterscheidbar von null. Unter V1|A
t = 7,44.

Damit ist auch Punkt (3) unter *GMM Exponent (incr/n_per)* beantwortet: die
Rang-Ausreißer berühren die Bookmaker-Vergleiche im Text nicht, weil diese
Vergleiche insgesamt nicht tragen.

**Vorbehalt:** Der Q-Test behandelt die 24 Schätzungen als unabhängig. Sie
teilen sich Match-Ausgänge, wodurch die wahre Varianz der Kontraste kleiner
ist als unterstellt — der Test unterschätzt Heterogenität tendenziell. Bei
I² = 0–4 % ist der Abstand groß, ein Cluster-Bootstrap auf Matchup-Ebene
(B ≈ 100) wäre der saubere Abschluss. **Offen.**

## Bayesian unter V2|B – Befund festgehalten, nicht weiterverfolgt

Quelle: `revision/snapshots/gmm_rasterfree/_bayes_diag.py`,
`bayes_convergence.csv`, `bayes_zero_mass.csv`, `bayes_sdgamma.csv`;
Traces in `models/`, publizierter Vergleichsstand in
`models/archive_2024-12-02_published/`.

**Konvergenz ist sauber.** 15 NUTS-Läufe à 20.000 Draws: R-hat durchgehend
1,0000, kein Lauf über 1,01; minimale ESS bulk 1.866 (`fav`), keiner unter
400; 43 Divergenzen insgesamt (≤ 0,085 % der Draws), konzentriert auf die
Dezil-Läufe `quantile5` (17), `quantile3` (12), `quantile6` (8).

**Übereinstimmung mit dem GMM ist gut – bis auf `fav`.**

| Subset | Bayes | GMM | Verhältnis |
|---|---:|---:|---:|
| tot | 0,003575 | 0,003474 | 1,03 |
| udd | 0,001149 | 0,001181 | 0,97 |
| **fav** | **0,008453** | **0,005531** | **1,53** |

`tot` und `udd` stimmen auf 3 % überein; `fav` weicht um Faktor 1,53 ab.
Vermutung (ungeprüft): `mean_gamma` ist der Mittelwert der *zugrunde
liegenden* Normalverteilung, nicht der der bei null abgeschnittenen; bei
grossem `sd_gamma` fallen beide auseinander. `fav` hat zugleich die
niedrigste Effizienz im Feld. **Nicht weiterverfolgt.**

**Offener Widerspruch: `sd_gamma`.** Posterior-Median **0,007723** bei einem
`mean_gamma` von 0,0036 – die geschätzte Streuung zwischen Bookmakern ist
doppelt so gross wie das Niveau selbst. Frequentistisch ist dieselbe
Streuung **nicht nachweisbar** (τ = 0,000, I² = 0 %, Cochran-Q p = 0,749).
Die Daten ziehen `sd_gamma` zwar um Faktor 36 unter den Prior-Median
(Exponential(2,5), Median 0,27726), der Posterior sitzt aber immer noch bei
nur 1,9 % der Prior-Verteilung. Ob der Rest Prior-Druck oder Signal ist,
ist **offen**.

> **Betrifft dieselbe Abstract-Passage** wie der Heterogenitätsbefund
> weiter oben („substantial heterogeneity across bookmakers"). Solange die
> beiden Schätzverfahren auf denselben Daten uneins sind, sollte die
> Passage keine Bookmaker-Heterogenität behaupten.

**Truncation bindet.** `gamma ~ Truncated(Normal, lower=0)` ist bei drei von
24 Bookmakern spürbar: BetVictor **99,9 %** der Posterior-Masse unter 0,001
(GMM 0,000394), Pinnacle 28,3 % (GMM −0,000375, negativ und damit im Modell
unzulässig), Marathonbet 22,6 %. Rangkorrelation Posterior-Median gegen GMM
nur **0,3409**.

**Status:** Befund festgehalten, nicht weiterverfolgt.
