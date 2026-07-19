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
