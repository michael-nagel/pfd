# Revision Log – JRSSA-Mar-2026-0082

Erzählte Revisions-Chronik pro Reviewer-Kommentar. Zweck: interne
Nachvollziehbarkeit der Bearbeitung UND Rohmaterial für das spätere
Response-to-Reviewers-Dokument.

Faktenbasis: `revision/reviewer_tracker.md` (kondensierte Kommentare) und
`references/specs/open_questions.md` (Untersuchungsbefunde). Nichts wurde
hinzuerfunden; fehlende Details sind mit **[zu ergänzen]** markiert.

**Pflegeregeln:**
- Einträge werden **nie gelöscht**.
- Wird eine Maßnahme später gegenstandslos, wird sie **nicht entfernt**,
  sondern im Feld **Superseded** als überholt markiert – mit Verweis auf den
  ablösenden Eintrag/die ablösende Entscheidung und Datum. Die Historie
  bleibt sichtbar.
- Status-Werte: `offen` / `in Arbeit` / `umgesetzt` / `verifiziert` /
  `superseded`.

Reihenfolge: zuerst Kommentare mit echtem Arbeitsstand, danach leere
Vorlagen für die noch nicht bearbeiteten Kommentare.

---

# Teil 1 – Kommentare mit Arbeitsstand

## R1-ii – Crossed Random Effects (Bookmaker × Match)
**Kommentar (kondensiert):** Random Effects nur für Bookmaker sind
unzureichend, da Beobachtungen zusätzlich auf Match-Ebene geclustert sind
(gleiches Match bei mehreren Bookmakern, gleicher Spielausgang). Gefordert
werden crossed random effects für Bookmaker UND Match, mindestens
cluster-robuste Inferenz auf Match-Ebene. Betroffen: eq:resp_to_info,
eq:ags_test, eq:unbiasedness_reg. Von AE mitgetragen.

**Stand vor Revision:** Alle drei Modelle nutzten ausschließlich ein
bookmaker-Random-Effect (statsmodels MixedLM, durchgängig `reml=False`/ML).
Der Match-Cluster wurde nicht modelliert.

**Untersuchung:**
- Toolchain: statsmodels MixedLM kann echte crossed random effects nicht
  abbilden, wenn ein Faktor (Matchup) über die `groups`-Grenzen eines anderen
  (Bookies) hinweg realisiert wird – `vc_formula`-Random-Effects werden pro
  `groups`-Level separat gezogen, nicht gruppenübergreifend geteilt
  (verifiziert gegen installierten statsmodels-0.14.0-Quellcode und Doku).
- Folge: Umstieg auf R/lme4 2.0.6 via rpy2 3.6.7 für alle drei Modelle
  (resp_to_info, ags_test "All"-Zweig, unbiasedness_reg).
- Befund zu `match_var` in eq:resp_to_info: mit ~1,1493 ca. 4 Größenordnungen
  über allen Bookies-Varianzkomponenten. Ursache identifiziert (kein Bug):
  RtrnClsEnd = Match/ClsOdds − 1 ist bei Match==0 mathematisch immer exakt −1,
  unabhängig von Bookmaker/ClsOdds – triviale Eigenschaft der Return-Metrik
  auf eine binäre Wette (voller Verlust). Bestätigt über 3 Wege: lme4-Fit,
  ANOVA-Zerlegung (99,72 % Between-Match; 53 % der Matches mit exakt 0
  Within-Varianz), Formel-Analyse.
- Sensitivitäts-Fit auf Match==1 (n=86.097): match_var fällt von 1,1493 auf
  0,7265 (~37 % mechanisch), bleibt aber ~2 Größenordnungen über den
  Bookies-Komponenten → R1-ii-Befund hält auch nach Bereinigung.
- Deskriptive Between/Within-Prüfung der anderen beiden Zielgrößen:
  fit_rfa_mod (FEOpn−FECls) 82,53 %/17,47 %, kein Degenerationsmuster;
  fit_mixed_lm (OddsMvt0) 99,35 %/0,65 %, extrem aber ohne algebraische
  Degeneration (nur 0,5 % Gruppen mit 0 Within-Varianz) – ökonomisch
  substanziell (Opening-Preise bei Markteröffnung naturgemäß ähnlich), anders
  einzuordnen als der RtrnClsEnd-Befund.
- Nebenbefund: bookies_slope_var steigt in der Wins-only-Teilmenge um Faktor
  ~10 (0,000516 → 0,005130); plausibel, weil Match==0-Zeilen für den
  RtrnOpnCls-Slope uninformativ sind. Für spätere Robustheits-Diskussion
  vorgemerkt, nicht weiter verifiziert.

**Entscheidung:**
- REML vs. ML: `REML=FALSE` für alle lme4-Fits, um Konsistenz mit dem
  bestehenden ML-Schätzparadigma des Papers zu wahren. Bewusste Abweichung
  vom Lehrbuch-Standard (REML wäre für einen validen LR-Test bei nur
  geänderter Random-Effects-Struktur die übliche Wahl), in Kauf genommen für
  Vergleichbarkeit mit dem Rest des Papers.
- Für einen sauberen LR-Test (Original vs. Crossed) wird das
  bookmaker-only-Modell zusätzlich in lme4 refittet (reine Kontrollrechnung,
  kein Ersatz für den statsmodels-Code im Paper), da ein LR-Test über zwei
  Implementierungen (statsmodels- vs. lme4-Loglik) nicht formal valide wäre.
  Der direkte statsmodels-Original vs. lme4-Crossed-Vergleich bleibt als
  informelle Zusatzinfo.
- Interpretations-Leitplanke: match_var NICHT als Evidenz für
  "Informations-Konvergenz zwischen Bookmakern" verkaufen – bei RtrnClsEnd ist
  ein substanzieller Teil mathematische Trivialität der Return-Definition bei
  Verlust; echte bookmaker-abhängige Variation nur bei Match==1.

**Umsetzung:** Modellarbeit abgeschlossen. Alle drei Modelle (gpm, rfa,
unbiasedness_reg) vollständig in `results/crossed_comparison_summary.csv`
(60 Zeilen) und `results/crossed_comparison_coefs.csv` (413 Zeilen). rpy2 als
Abhängigkeit ergänzt (Commit b65c974). Paper-Text / Reviewer-Antwort
(Interpretation der drei Modelle, Einordnung von match_var) noch nicht
geschrieben.

**Beleg/Validierung:** Parallelisierung (spawn-Kontext, Pool-Initializer)
gegen sequenziellen Refit auf exakte Übereinstimmung validiert. match_var-
Ursache über 3 unabhängige Wege bestätigt (siehe Untersuchung). Symbolische
Prüfung der anderen zwei Zielgrößen (kein exakte-Null-Kollaps) plus
empirische Between/Within-Zerlegung.

**Status:** in Arbeit (Modelle verifiziert, Paper-Interpretation offen)

**Superseded:** —

**Für Response-Dokument:** Wir haben die Modelle mit crossed random effects
für Bookmaker und Match neu geschätzt (Umstieg auf R/lme4, da statsmodels
gruppenübergreifende crossed effects nicht korrekt abbildet); die Ergebnisse
liegen für alle drei betroffenen Gleichungen vor. Der starke Match-Cluster in
eq:resp_to_info ist teilweise eine mechanische Eigenschaft der Return-Metrik
bei verlorenen Wetten und werden wir in der Interpretation entsprechend
zurückhaltend einordnen.

**Offen / [zu ergänzen]:** match_icc (Anteil der Gesamtvarianz durch Matchup)
wurde als Zusatzkennzahl diskutiert, aber für keines der drei Modelle in
`crossed_comparison_summary.csv` ergänzt – Entscheidung offen. Formulierung
der finalen Paper-Passagen [zu ergänzen].

---

## R2-C2 – Backward-Imputation / Look-Ahead-Leck
**Kommentar (kondensiert):** Backward-Imputation-Strategie (S. 11, Appendix C)
unklar erläutert. Falls spät einsteigende Bookmaker vor eigener Eröffnung
Preise anderer Bookmaker beobachten ("Off-Market-Learning"), spiegeln
zurückimputierte Opening-Odds evtl. nicht die tatsächliche Situation wider.
Zwei Lernkanäle (Posting+Beobachten vs. Warten+Beobachten) sollten
unterschieden werden; der Zeitpunkt des Markteintritts könnte selbst
informativ sein, statt wegimputiert zu werden.

**Stand vor Revision:** Der IterativeImputer (BayesianRidge) nutzte den
Match-Ausgang als Feature. Der Appendix (Zeile 1100) beschreibt die
Imputations-Features als "implied probabilities of other bookmakers for the
same and different matches".

**Untersuchung:**
- Look-Ahead-Leck bestätigt per sauberem a/b-Test: Match als Imputer-Feature
  erzeugt eine ausgangs-korrelierte Differenz (corr 0,56–0,88 in OddsMvt0–4,
  die 60 % der Imputation ausmachen). Absolutbetrag der Differenz jedoch
  winzig (~0,0001); BayesianRidge-Koeffizient auf Match liegt auf Rang 51/51.
- Paper-Code-Diskrepanz aufgedeckt: Tatsächlich nutzt der IterativeImputer
  primär die anderen Spalten DERSELBEN Zeile – d. h. die eigenen späteren
  Preise desselben Bookmakers (OddsMvt1..50, OddsMvt1 dominant,
  standardisierter Beitrag ~0,19) – nicht die Preise anderer Bookmaker wie im
  Appendix beschrieben. Dieser Punkt ist inhaltlich relevant für R2-C2
  (Rückwärts-Information innerhalb desselben Bookmakers).
- **Robustness-Check kontinuierliche Zeitachse** (ohne Imputation, ohne
  Perzentil-Raster, echte Zeitstempel, varying-coefficient-GAM): reproduziert
  den Baseline-β₁-Verlauf NICHT. Durchgehender Niveau-Versatz von −0,22; die
  kontinuierliche Kurve liegt an keinem der 50 Perzentile über der Baseline.
- **Kanalzerlegung** des Versatzes: Referenzpunkt +13 %, Gewichtung +16 %,
  Forward-Fill +1 %, dasselbe GAM auf den Baseline-Daten +90 % → die Differenz
  ist vollständig Datenbasis, nicht Schätzer. C3 vs. C4 lokalisiert sie: die
  7,85 % imputierten Zellen tragen den kompletten Niveauunterschied.
- **Masking-Test** (24.568 vollständig beobachtete Serien, künstlich maskiert
  im empirischen Fehlmuster der Spät-Eröffner): auf ECHTEN Frühpreisen ist β₁
  über das ganze Fenster flach (1,262 bei Perzentil 2 → 1,161 bei 99). Auf
  imputierten Frühpreisen 2,460 → 1,199, mittlerer Versatz +0,263. Der steile
  Abfall – die charakteristische Form der publizierten Figure 3 – entsteht
  durch die Imputation.
- **Mechanismus:** p₀ steht auf BEIDEN Seiten der Regression (Endog = ω − p₀,
  Exog = p_t − p₀). Ein geteilter Messfehler verschiebt beide Seiten
  gleichzeitig und erzeugt künstliche Kovarianz – kein gewöhnlicher
  Errors-in-Variables-Fall (der würde attenuieren). Verstärkt durch die
  systematische Schrumpfung der imputierten Werte um 23 % zur Mitte. Der
  Effekt klingt mit der Distanz zum imputierten Block ab.
- Die **Imputationsqualität isoliert betrachtet ist unauffällig** (RMSE 0,091,
  Bias −0,0015, corr 0,913) – ein geringer Imputationsfehler schließt den
  Downstream-Effekt also nicht aus.
- **GMM dagegen ROBUST:** γ gepoolt 0,0305 (echt) vs. 0,0435 (imputiert), aber
  dieser Versatz ist Hebelwirkung von 3,3 % der Serien (Blocklänge ≥ 22); ohne
  diese +0,0002. Stützstellentausch OddsMvt0 → OddsMvt21 auf dem
  Produktions-Frame: +1,5 %. Deterministische Kontrolle: wenn keine
  Stützstelle imputiert ist, bewegt sich γ um exakt 0,0000.
- **Struktureller Grund für die Asymmetrie:** OddsMvt0 geht ins GMM nur über
  EIN Instrument ein (OddsMvt26 − OddsMvt0); die Momentbedingungen nutzen
  OddsMvt46/41/36 (0–0,15 % imputiert). In der Unbiasedness-Regression steht
  OddsMvt0 auf beiden Seiten.
- **Cross-Sections nicht betroffen** (RMSE, Eq. 1/2, Tab. 5/6) – sie laufen auf
  den echten Opening-/Closing-Preisen vor dem Resampling.
- **Vollständiges 2×2 Imputation × Komposition** (vierte Zelle nachgerechnet:
  Baseline-Perzentil-Methode auf denselben 24.568 vollständig beobachteten
  Serien). Mittleres β₁ auf gemeinsamem Träger: Baseline/alle 1,224 –
  Baseline/vollst. beob. 1,234 – kontinuierlich/alle 1,006 –
  kontinuierlich/vollst. beob. 1,200. Daraus: Methodeneffekt **ohne**
  Imputation (B−D) = +0,034, also 16 % der Gesamtlücke von +0,218; die
  restlichen **84 % (+0,184)** sind der Interaktionsterm, der nur entsteht, wo
  imputiert wird. Der Kompositionseffekt existiert nur in der echten
  Datenansicht (−0,195) und schrumpft unter der Baseline-Methode auf −0,010
  (5 %) – die Imputation löscht 95 % der wahren Heterogenität zwischen früh und
  spät eröffnenden Serien. Größenordnungskontrolle: der within-sample
  Masking-Test liefert unabhängig +0,261. Konsistenzkontrolle: Zelle B (1,234)
  und `masking_beta1_true.csv` (1,223) messen dasselbe auf zwei Wegen und
  stimmen auf 0,011 überein. Zelle A reproduziert `C_normalized/beta1_curve.csv`
  auf 2,2e−16; ohne Random Effects (OLS) ändert sich Zelle B um 0,015.
  → Damit ist die früher offene Zerlegung des Niveauversatzes in Imputations-
  und Kompositionsanteil erledigt: sie ist überwiegend Imputation.
- **Attenuations-Check der Verspätungsquartile** (vor inhaltlicher Deutung des
  Q4-Abfalls auf β₁ = 0,482). Die Prämisse trifft zu: var(p_t − p_ref) fällt
  monoton mit der Verspätung (Q1 0,00275 → Q4 0,00143, also 52 %), bei
  praktisch konstanter var(Endog) (0,208–0,215); Q4 sitzt in längeren
  Matchup-Fenstern (Median 37,6 h vs. 17,5 h), deckt davon aber nur 72 % ab
  statt 94 %. Am Fensterende – wo der Abfall sitzt – ist der Varianzabstand
  jedoch *kleiner* (Q4/Q1 = 0,579) als früh (0,434). Die Arithmetik schließt
  Attenuation aus: ein gemeinsames σ²_u, das Q4 von 1 auf 0,482 drückt
  (σ²_u = 0,00179), sagt für Q1 0,617 vorher – beobachtet 0,992, rund 12 SE
  daneben; umgekehrt liefert das aus Q1 implizierte σ²_u = 0,000024 für Q4
  β₁ = 0,986 statt 0,482. Der Varianzunterschied erklärt damit **~1 %** des
  Q1→Q4-Abstands; σ²_u müsste in Q4 rund 75-mal größer sein. Zudem wirkt der
  zweite Messfehlerkanal gegenläufig: `p_ref` steht auf beiden Seiten der
  Regression, geteiltes Rauschen zieht β₁ **gegen 1**, kann 0,482 also nicht
  erzeugen. Der Q4-Abfall ist als Befund belastbar; die Konfundierung mit
  Bookmaker-Identität und Serienlänge bleibt davon unberührt offen.

**Entscheidung:** Match aus den Imputer-Features entfernt – kein inhaltlicher
Grund für seine Aufnahme, und die Entfernung beseitigt die Angriffsfläche
(Look-Ahead), auch wenn der Effekt betragsmäßig winzig war. Die
Appendix-Beschreibung der Features muss korrigiert werden.

**Umsetzung:** Match aus dem IterativeImputer-Feature-Set entfernt
(`impute_missings.py`, Commit a2b694e "Remove match outcome from imputation
feature set (look-ahead fix)"). Korrektur der Appendix-Beschreibung
(Zeile 1100) noch **nicht** vorgenommen [zu ergänzen].

**Beleg/Validierung:** Sauberer a/b-Test (Leck bestätigt und quantifiziert:
corr 0,56–0,88 auf OddsMvt0–4, Absolutbetrag ~0,0001). Downstream-Neulauf-
Diagnose durchgeführt: Stufe-B-Bericht, frequentistischer Neulauf bis
einschließlich GMM (`revision/snapshots/`). Da zwischen den publizierten
Artefakten (29.11.2024) und heute drei weitere Commits `src/pfd/` verändert
haben, die nie neu gerechnet wurden, wurde eine Kontrollstufe B0 eingezogen
(heutiger Code, aber Match wieder im Imputer). B − B0 isoliert damit den
Match-Fix, B0 − A misst die Code-Drift. B0 reproduziert die publizierten
Signifikanzperzentile exakt (31, identische Menge) und alle Tabellen bis auf
drei Bootstrap-Zellen, validiert also die Kontrolle. Ergebnis: Der Match-Fix
wirkt ausschließlich auf die Unbiasedness-Regressionen (β₁-Kreuzung 48 % →
56,7 %, max |Δβ₁| 0,19, Signifikanzperzentile 31 → 28); Tabellen 3–7,
\var{}-Werte und GMM (beide Varianten, je Bookmaker) bleiben innerhalb
numerischer Auflösung unverändert. Die Differenz in `bootstr_std`
(0,0258 → 0,0249) stammt aus der Bootstrap-Parallelisierung (Commit 1067d77)
und ist als Monte-Carlo-Rauschen verifiziert (5 Seeds × 1000 Resamples je
Schema, Welch p = 0,51; Draw-Level-Test zeigt konsekutive Seeds so
unkorreliert wie separierte), nicht als Effekt des Match-Fix.
Appendix-Korrektur weiterhin offen [zu ergänzen].
Belege der beiden Imputations-Robustness-Checks:
`revision/snapshots/continuous_unbiasedness/` (Commit 5680d91) und
`revision/snapshots/gmm_imputation_test/` (Commit bf9b97a), jeweils mit README,
CSVs und Reproduktionsskripten. Der GMM-Harness reproduziert
`C_normalized/gmm_by_bookie.csv` auf 7,6e−17. Das vollständige
Imputation-×-Komposition-2×2 steht in
`revision/snapshots/continuous_unbiasedness/README.md` (Nachtrag 3,
Skript `_composition_2x2.py`; Zelle A reproduziert die Baseline auf 2,2e−16),
der Attenuations-Check der Verspätungsquartile in
`revision/snapshots/continuous_unbiasedness/entry_delay/README.md`
(Abschnitt 5, Skript `_attenuation.py`).

**Status:** in Arbeit – Befund steht, Konsequenz für den
Unbiasedness-Abschnitt des Papers noch zu entscheiden.

**Superseded:** —

**Für Response-Dokument:** Wir haben die Imputation überprüft und den
Match-Ausgang aus den Prädiktoren entfernt, um jeden Look-Ahead-Kanal
auszuschließen. Der Effekt auf die Tabellen 3–7, alle \var{}-Werte und die
GMM-Lernraten ist vernachlässigbar (GMM-Änderung 8,9e−5, innerhalb der
numerischen Toleranz des Optimierers). Auf den β₁-Pfad der
Unbiasedness-Regressionen ist er dagegen NICHT vernachlässigbar: Die Kreuzung
von β₁=1 verschiebt sich von 48 % (publizierte Figure 3) auf 57 %, mit
maximaler Verschiebung von 0,19 (mittleres |Δ| 0,043). Figure 3 und die
zugehörige Interpretation müssen entsprechend aktualisiert werden. Wir
werden außerdem die Appendix-Beschreibung präzisieren: Die zurückimputierten
Opening-Odds stützen sich primär auf spätere Preise desselben Bookmakers, was
für die von Referee 2 aufgeworfene Frage der bookmaker-internen
Rückwärts-Information direkt relevant ist. Die konzeptionelle Frage der zwei
Lernkanäle / Markteintritts-Zeitpunkt wird [zu ergänzen].

Ergänzend (Futur, da noch nicht umgesetzt): Wir werden darlegen, dass der
Look-Ahead über den Match-Ausgang der kleinere Teil des Problems war; der
wesentliche Befund ist, dass die zurückimputierten Frühpreise den β₁-Verlauf
tragen, auf dem das Lern-Narrativ aufbaut. Die Learning-Rate-Schätzung (GMM)
ist davon nachweislich nicht betroffen. Der naheliegende Gegeneinwand – der
Unterschied komme aus der Stichprobenzusammensetzung, weil die vollständig
beobachteten Serien früh eröffnende Bookmaker sind – ist über ein 2×2
ausgeschlossen: auf denselben 24.568 Serien liegen beide Verfahren nur 0,034
auseinander, 84 % der Gesamtdifferenz von 0,218 entstehen erst dort, wo
imputiert wird. Zum Markteintritts-Zeitpunkt können wir zudem zeigen, dass er
informativ ist (hochsignifikante Interaktion, β₁ hängt gemeinsam von Zeit und
Verspätung ab) und dass der Abfall bei den Spät-Einsteigern keine
Attenuation ist – die geringere Regressorvarianz erklärt davon ~1 %.

**Offen / [zu ergänzen]:** Konzeptionelle Antwort auf die zwei Lernkanäle
(Posting+Beobachten vs. Warten+Beobachten) und die Frage, ob der
Markteintritts-Zeitpunkt selbst als Information behandelt statt wegimputiert
werden sollte. Verweis: R2-C3/R3-2 (Timing) berühren dieselbe Datenbasis.
Außerdem offen: wie der Unbiasedness-Abschnitt neu aufgesetzt wird – eigene
Entscheidung, siehe nächster Schritt.

---

## R1-i / R3-3 – Bookmaker-Margen / normalisierte Wahrscheinlichkeiten
**Kommentar (kondensiert):** Implied probabilities enthalten Bookmaker-Margen;
Vergleiche sollten mit margin-bereinigten (normalisierten) Wahrscheinlichkeiten
statt rohen inversen Odds erfolgen, mit Robustheit gegen alternative
Margin-Removal-Methoden (R1-i). Inverse dezimale Odds werden als Forecasts
behandelt, ohne die Marge (Summe >1) ausreichend zu berücksichtigen; Marge
könnte über Zeit variieren (höher in unsichererer früher Phase, leicht
prüfbar) (R3-3).
**Stand vor Revision:** Implizite Wahrscheinlichkeiten werden als rohes
Inverses der Dezimalquote der gewählten Seite gebildet (`filter_and_shape.py:117`,
`OddsMvt = 1/dez_home`, einseitig), ohne Normalisierung auf Summe 1. Die Marge
wird berechnet, aber nur als Filter (`0 ≤ Margin ≤ 0.15`) verwendet, nicht
abgezogen. Die Away-Seite wird nach der Perspektivwahl (`:91-98`) verworfen.
Alle Cross-Sections (OpnOdds/ClsOdds) und alle Zeitreihen (OddsMvt0..50)
erben diese rohe Größe.
**Untersuchung:** Diagnose rein deskriptiv, gegen Paper-Zahlen validiert
(Table-5-Bins und fig:rmse-Rangfolge exakt reproduziert). Kernbefunde:
- Marge: Opening-Median 7,82 %, Closing 7,61 %; schrumpft ~0,2 pp Open→Close
  (bei 55,9 % der Gruppen) – systematisch, aber klein. Bookmaker-spezifisch
  4,90 % (Pinnacle) bis 8,33 % (Interwetten), Spread ~3,4 pp.
- Level-Effekt: rohes Preis-Level ~halbe Marge (~3,6 pp) zu hoch;
  Normalisierung zentriert die Player-1-Opening-Wahrscheinlichkeit exakt auf
  0,50 (roh: Median 0,5405) – relevant auch für R2-C1/R2-M5 (Intercept ~0,5).
- Bewegungs-Effekt: raw↔norm Open-to-Close korrelieren 0,997; ~90 % echte
  Belief-Änderung, ~10 % Margen-Änderung; die Netto-Abwärtsdrift der rohen
  Bewegung ist vollständig Margen-Artefakt.
- Robustheit: Table 5 behält Monotonie/Vorzeichen (~12 % Gruppen wechseln
  Bin, Extrembins verlieren ~30 % Mitglieder, Top-Bin-WR 0,635→0,652);
  RMSE-Rangfolge Spearman raw vs. norm 0,99, Extremränge stabil.
- Level-vs-Differenz-Regel: Normalisierung materiell bei Größen gegen den
  Ausgang ω (RtrnClsEnd, FEOpn/FECls/RMSE, GMM-Momentbedingungen,
  Unbiasedness-Endog), vernachlässigbar bei Differenzen/Ratios gleichseitiger
  Preise (RtrnOpnCls, DltOpnCls, GMM-Instrumente).
- Konsistenz: GMM/Bayesian/Unbiasedness nutzen dieselbe rohe 1/dez-Größe wie
  die Cross-Sections (Detail in open_questions.md, Abschnitt Margen/
  Normalisierung).
**Entscheidung:** Umgestellt auf margin-bereinigte, auf Summe 1 normierte
Wahrscheinlichkeiten statt roher inverser Quoten – umgesetzt und als
Referenz-Baseline gesetzt (Tag `revision-baseline`). Die drei
Konsistenzbedingungen für eine durchgängige Normalisierung der Zeitreihen sind
damit alle erfüllt: (1) Mitführen der Away-Seite durch `filter_and_shape` /
`resample_and_impute` und (2) Normalisierung pro Zeitpunkt sind mit `dcd0f51`
erledigt; (3) Imputation der Frühwerte auf der normalisierten/zweiseitigen
Größe ergibt sich aus der neuen Baseline, da der Imputer nun auf der
normalisierten `OddsMvt`-Größe arbeitet. Die ursprünglich offene
Reihenfolgefrage gegenüber der Zeitachsen-Entscheidung (R2-C3/R3-2) ist damit
gegenstandslos: Die Normalisierung steht fest, eine spätere Umstellung der
Zeitachse setzt auf ihr auf.
**Umsetzung:** Normalisierung implementiert: die implizite Wahrscheinlichkeit
ist jetzt `p_norm = p_home / (p_home + p_away)` statt der rohen einseitigen
inversen Dezimalquote, konsistent über Cross-Sections, GMM und
Unbiasedness-Regressionen. Zwei Schritte: C1-Refactor (beide Quotenseiten
werden durch `filter_and_shape` durchgereicht, `estimation.normalize`-Flag
eingeführt, Default noch off) in Commit `dcd0f51`; Umstellung des
Flag-Defaults auf `True` in Commit `e95ce5a`. **Ab `e95ce5a` / Tag
`revision-baseline` ist die Normalisierung der neue Standard**, kein Override
mehr – siehe `revision/baseline_status.md`.
**Beleg/Validierung:** Vorab (Diagnose): Diagnose-Skripte reproduzieren
Table-5-Bins (z. B. Bin [-1,-0.15]: n=1484, WR 0,3369) und die
fig:rmse-Rangfolge (Pinnacle/BetInAsia/NordicBet als schlechteste) exakt gegen
die Paper-Zahlen; Level-Shift ~halbe Marge und die 0,997-Korrelation empirisch
bestätigt.
Nach Umsetzung: Stufen-D-Vergleich C1 vs. C2 und volle 2×2-Matrix
(Look-Ahead × Normalisierung), Quelle `revision/snapshots/compare_2x2.csv`,
Bericht `revision/snapshots/STAGE_D_2x2_report.md`. Die Kernbefunde sind robust:
- γ̄ (CUE) 0,0332 → 0,0320, idxmin (GGBET) / idxmax (Dafabet) unverändert.
- RMSE-Rangfolge Spearman roh vs. normalisiert 0,992, Extremränge stabil.
- Tabelle 6 (AvgChange) 0,7413 → 0,8206, weiterhin signifikant (Bootstrap-SE
  0,0249 → 0,0307).
Kompositionseffekt geprüft (Prüfkriterien vorab festgeschrieben in
`revision/c2_check_spec.md`): Das df_oc-Sample wächst über den
`|RtrnOpnCls| > 0`-Filter um netto **+3 089** Gruppen (3 367 neu hinzu,
278 heraus). Die Aufschlüsselung nach Bookmaker
(`revision/snapshots/diagnostics/c2_zeromove_by_bookie.csv`) widerlegt die
Sorge aus der Prüfspezifikation, margenstarke Bookmaker könnten
überproportional betroffen sein. Die Stichprobenverschiebung **läuft nicht
entlang des Margenniveaus (Korrelation −0,28, schwach negativ)** – bewusst
nicht als „nicht margenkorreliert" formuliert, das wäre nicht belegt. Das
Vorzeichen ist die unkritische Richtung: wenn überhaupt, sind die
*margenärmsten* Bookmaker stärker betroffen (Pinnacle +3,3 %, BetInAsia
+3,7 %), und die am stärksten betroffenen Bookmaker streuen über den gesamten
Margenbereich (10Bet 6,94 % / +6,0 %; Betfair 7,79 % / +5,0 %; ComeOn 8,14 % /
+4,1 %), ohne monotones Muster. Der gemessene Effekt ist damit
Messgrößenänderung, nicht Komposition. Beleg: `c2_zeromove_by_bookie.csv`
(Median-Marge je Bookmaker gegen Netto-Anteil, Pearson und Spearman je −0,28).
**Status:** umgesetzt (Baseline) – Code-seitig abgeschlossen und als
Referenz-Baseline gesetzt; Paper-Zahlen und -Formulierungen noch anzupassen
(offene Punkte in `revision/baseline_status.md`, Abschnitt NOCH OFFEN)
**Superseded:** —
**Für Response-Dokument:** Wir haben auf margin-bereinigte, normalisierte
Wahrscheinlichkeiten umgestellt: implizite Wahrscheinlichkeiten werden jetzt
als p/(p_home+p_away) gebildet, konsistent über Cross-Sections und
Zeitreihen. Die qualitativen Kernbefunde bleiben unverändert – die
Table-5-Monotonie hält, die RMSE-Rangfolge korreliert mit 0,99 (Spearman) mit
der bisherigen, und die geschätzten Lernraten sind praktisch identisch
(0,033 → 0,032, gleiche Extrembookmaker). Die Normalisierung entfernt einen
systematischen Level-Aufschlag von ~halber Marge; dadurch wird die
Winning-Rate-Achse bei Nulländerung exakt auf 0,50 zentriert (bisher ~0,54),
was zugleich den von Referee 2 angemerkten unintuitiven Intercept adressiert
(R2-C1/R2-M5), und der Zusammenhang in Tabelle 6 wird stärker (0,741 → 0,821).
Materiell ändert sich die Interpretation der Unbiasedness-Regressionen: β₁
liegt nach Normalisierung über den gesamten Beobachtungshorizont über 1, die
bisher berichtete Unterschreitung spät im Wettfenster war ein Artefakt der
Margenschrumpfung zwischen Opening und Closing. Wir berichten dies als
partielles Lernen (Unterreaktion) im Sinne von R2-C7. Die Robustheit gegen
alternative Margin-Removal-Methoden werden wir [zu ergänzen] zeigen.

---

## R1-v – Zensierung durch Opening-Odds + letzte 20 Updates
**Kommentar (kondensiert):** Oddsportal liefert nur Opening-Odds plus die
letzten 20 Updates → mögliche Zensierung, v. a. bei aktiven Märkten. Die
Beschränkung auf Zeitreihen mit <20 Preisänderungen könnte gerade die
informativsten Matches entfernen. Gefordert: Anzahl verlorener Beobachtungen
quantifizieren, included vs. excluded vergleichen, Robustheit zeigen. Von AE
explizit priorisiert (AE-3).

**Stand vor Revision:** Ein `NumOddsMvt<20`-Filter ist im Code vorhanden, im
Paper aber nicht beschrieben. Die Imputation ist frontlastig (füllt frühe
Preisbewegungen); das Closing wird nie imputiert.

**Untersuchung:** Befund bislang qualitativ: undokumentierter
`NumOddsMvt<20`-Filter identifiziert; Imputation frontlastig; Closing nie
imputiert. Quantifizierung (Zahl verlorener Beobachtungen, included vs.
excluded) noch nicht durchgeführt. [zu ergänzen]

**Entscheidung:** [zu ergänzen – noch keine Umsetzung, nur Befund]

**Umsetzung:** [zu ergänzen]

**Beleg/Validierung:** [zu ergänzen]

**Status:** offen (Befund identifiziert, noch keine Umsetzung)

**Superseded:** —

**Für Response-Dokument:** Wir dokumentieren das durch die Datenquelle
(Opening + letzte 20 Updates) bedingte Zensierungsmuster und den bislang
undokumentierten Filter transparent und werden included- vs.
excluded-Stichproben vergleichen. [zu ergänzen: Quantifizierung, Robustheit]

---

## R2-C3 / R3-2 – Perzentil- vs. Absolutzeit, Opening-Zeitpunkt-Konfundierung
**Kommentar (kondensiert):**
- R2-C3: Perzentil-basiertes statt absolutes Timing verzerrt die
  Interpretation – ein 18h-Fenster vs. 9h-Fenster gewichtet dieselbe absolute
  Lernperiode (z. B. letzte Stunde vor Kickoff) unterschiedlich stark.
  Absolute Zeit zumindest für Teile der Analyse erwägen.
- R3-2: Opening-RMSE-Vergleiche zwischen Bookmakern sind durch stark
  unterschiedliche Opening-Zeitpunkte konfundiert (48h vs. 6h vor Match =
  unterschiedliche Informationsmengen); Pinnacles hohe Opening-RMSE evtl. nur
  Artefakt früherer Marktteilnahme.

**Stand vor Revision:** Analyse auf perzentil-basierter (homogenisierter)
Zeitachse; Opening-RMSE über Bookmaker ohne Kontrolle des jeweiligen
Opening-Zeitpunkts.

**Untersuchung:**
- R2-C3 (Perzentil- vs. Absolutzeit): In Diskussion, noch keine empirische
  Prüfung dokumentiert. [zu ergänzen]
- R3-2 (RMSE-Konfundierung): Eine mögliche zusätzliche Konfundierung durch
  bookmaker-spezifische Margen wurde deskriptiv geprüft und **widerlegt** –
  die Korrelation zwischen Median-Opening-Marge und rohem RMSE über die
  Bookmaker ist NEGATIV (−0,34): die margenärmsten (sharp) Bookmaker
  (Pinnacle, BetInAsia) haben gerade die HÖCHSTEN RMSE. Die Margen-
  Konfundierungs-Hypothese scheidet damit als Erklärung aus; die RMSE-Anomalie
  läuft über Timing (R3-2 im engeren Sinn: unterschiedliche Opening-Zeitpunkte),
  nicht über die Marge. Details in open_questions.md (Abschnitt Margen/
  Normalisierung). Die eigentliche Timing-Kontrolle (Opening-Zeitpunkt als
  Kovariate/Matching) ist noch offen. [zu ergänzen]

**Entscheidung:** Offen. Abgewogene Optionen:
- (a) Kontinuierliche Spline-Zeitachse zugunsten von Unbiasedness.
- (b) Diskrete Zeitachse mit expliziter Bias-Rechtfertigung für das GMM.
Noch nicht entschieden.

**Umsetzung:** [zu ergänzen]

**Beleg/Validierung:** RMSE-Rangfolge und Margen-Kennzahlen gegen Paper-Zahlen
validiert (fig:rmse-Extremränge exakt reproduziert); negative Margen-RMSE-
Korrelation empirisch bestätigt. Timing-Kontrolle selbst noch nicht
umgesetzt. [zu ergänzen]

**Status:** offen (in Abwägung; Margen-Konfundierung geklärt/widerlegt)

**Superseded:** —

**Für Response-Dokument:** Wir werden die Konfundierung durch Opening-Zeitpunkt
und die Perzentil-Achse adressieren und eine (kontinuierliche bzw. absolute)
Zeitrepräsentation prüfen; die Wahl zwischen Unbiasedness-orientierter
kontinuierlicher Achse und einer für das GMM diskreten Achse ist [zu
ergänzen: finale Entscheidung]. Wir werden zudem darlegen, dass die
Unterschiede in der Opening-Genauigkeit nicht durch bookmaker-spezifische
Margen erklärt werden (die margenärmsten Bookmaker weisen die höchsten
Forecast-Fehler auf), sodass die verbleibende Erklärung beim Timing der
Markteröffnung liegt.

---

# Teil 2 – Leere Vorlagen (noch nicht bearbeitet)

## R1-iii / R2-C5 / R3-4 – Zuschreibung an "rational bettors"
**Kommentar (kondensiert):** Die Zuschreibung von Preisbewegungen an "rational
bettors" ist zu stark – alternative Ursachen (Bookmaker kopieren sharpe
Bookmaker, Risikomanagement, Marginänderungen, Arbitrage, mechanische
Algorithmen) (R1-iii). "Market learning is driven primarily by rational
bettors" wird als Fakt dargestellt, obwohl der Bettertyp nicht beobachtet wird
– als Inferenz kennzeichnen (R2-C5). Ergebnisse zeigen nur, dass sich
verengende Preise häufiger gewinnen, nicht dass Bettor systematisch profitabel
handeln konnten (Margen/Overround; Bezug Thaler & Ziemba 1988) (R3-4).
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R1-iv / R2-M3 – Klassifikation Sharp/Soft-Bookmaker
**Kommentar (kondensiert):** Sharp/Soft-Klassifikation unklar – die Liste
enthält Pinnacle/Betfair (typischerweise sharpe/Exchange-Märkte), obwohl das
Paper sich auf den "soft bookmaker market" beschränkt; Klassifikation
dokumentieren oder Robustheit ohne sharpe Bookmaker zeigen (R1-iv). Die
Sharp/Soft-Charakterisierung (S. 3) ist zu vereinfachend – ein Bookmaker kann
beide Rollen einnehmen (R2-M3).
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R1-vi – Plausibilität der GMM-Momentbedingungen (Biais-Annahmen)
**Kommentar (kondensiert):** GMM-Momentbedingungen aus einem asymptotischen
Finanzmarkt-Setting übernommen (Biais et al. 1999) – unklar, ob der
Lernraten-Parameter dieselbe Interpretation in einem Finite-Horizon-Wettmarkt
mit binärem Ausgang, irregulär beobachteten Preisen, Margen und zensierten
Preispfaden hat. Plausibilität der Annahmen diskutieren.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** Aus `open_questions.md` liegen zwei einschlägige interne
Befunde vor (noch nicht zu einer Reviewer-Antwort verarbeitet):
- biais1999: Die eigenen Momentbedingungen lassen den Nuisance-Parameter K
  (Varianz des Proxy-Fehlers φ) weg und schätzen nur γ (`k_params=1`).
  Mögliche Rechtfertigung: terminale Größe ist der exakte Ausgang ω∈{0,1},
  also φ≡0 und K=0 – im Paper aber nirgends benannt/begründet, obwohl der Text
  ("Following biais1999 … seven instruments") eine direkte Übernahme
  suggeriert. Zu klären: K=0 beabsichtigt und zu begründen, oder versehentlich
  weggelassen?
- hansen1996: Eigener Code nutzt Nelder-Mead direkt/ausschließlich auch für
  die CUE-Schätzung – im Original nur Rückfalloption, nicht Primärmethode
  (dort gradientenbasiertes Quasi-Newton mit mehreren Startwerten). Zu klären:
  robust genug im 1-Parameter-Fall, oder gradientenbasierter Vergleich nötig?
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen (Befunde vorhanden, Bewertung/Umsetzung ausstehend)
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R1-vii – Überinterpretation der Unbiasedness-Regressionen / glatterer Koeffizientenpfad
**Kommentar (kondensiert):** Die Unbiasedness-Regressionen (Fig. 3) werden zu
stark interpretiert – die ökonomische Größenordnung des RMSE-Rückgangs ist
moderat, und das "Phasen"-Narrativ beruht auf wiederholten punktweisen
Konfidenzintervallen. Gefordert: formale Tests mit simultanen
Konfidenzbändern oder ein glatteres dynamisches Modell des Koeffizientenpfads.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R1-viii – Favorite-Longshot-Bias direkt zeigen
**Kommentar (kondensiert):** Favorite-Longshot-Ergebnisse plausibel, aber
indirekt. Direkt zeigen: Favorite-Longshot-Bias in Opening-/Closing-Preisen,
seine Verkleinerung über das Betting-Fenster und den Zusammenhang mit den
geschätzten Lernraten.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R1-ix – Kausale Sprache abschwächen
**Kommentar (kondensiert):** Kausale Sprache zu stark ("market identifies and
corrects mispricing", "rational bettors force bookmakers to adjust").
Vorsichtigere Formulierung gefordert – die Evidenz ist konsistent mit Price
Discovery, aber nicht abschließend zu Mechanismus/Akteuren. Überschneidet mit
R1-iii, R2-C5, R3-4.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R2-C1 – Spezifikation von "Equation 3" (eq:win_rates)
**Kommentar (kondensiert):** Binäres Win/Loss als AV mit der Preisänderung als
einziger UV weicht von der Standardpraxis ab. Empfehlung: den Opening-Preis
zusätzlich als Kovariate (Baseline-Wahrscheinlichkeit) aufnehmen, sodass die
Preisänderung zusätzliche Information testet. Der aktuelle Intercept ~0.5 ist
unintuitiv, v. a. bei gemischter Favoriten/Longshot-Stichprobe.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R2-C4 – Mispricing- vs. Informations-Interpretation
**Kommentar (kondensiert):** Preisbewegungen werden zu oft als
Mispricing/Ineffizienz interpretiert (v. a. Eq. 3-Diskussion, Tables 5-6)
statt als mögliche Reaktion auf neue Information zwischen Opening und Closing;
besonders relevant bei großen Bewegungen (>10-15 % Implied-Prob-Änderung). Die
Unterscheidung zwischen direkt Beobachtetem (Preisbewegung sagt Ausgang
vorher) und Inferiertem (Mispricing-Korrektur vs. Informationsreaktion)
schärfen.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R2-C6 – Signifikanz der bookmaker-spezifischen Slopes
**Kommentar (kondensiert):** Zur Figur mit bookmaker-spezifischen Slopes
("steeper slopes indicating greater explanatory power") fehlen
Signifikanztests, ob sich die Slope-Parameter zwischen Bookmakern tatsächlich
statistisch unterscheiden.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R2-C7 – Lernen als Kontinuum statt binär
**Kommentar (kondensiert):** Lernen wird binär charakterisiert (β1>1 = "keine
Evidenz für Lernen"). Tatsächlich zeigt jedes β1>0 etwas Lernen, β1=1
vollständiges, β1>1 partielles Lernen (Unterreaktion) – nicht Abwesenheit von
Lernen. Lernen als Kontinuum darstellen.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R2-C8 – Intuitive Interpretation der Lernraten-Größenordnungen
**Kommentar (kondensiert):** Den Lernraten-Größenordnungen (z. B. 0.05 vs.
0.03) fehlt eine intuitive Interpretation. Gewünscht: Vergleich zu anderen
Wettmärkten oder Simulation/Umrechnung in eine interpretierbarere Metrik (z. B.
"X % der Fehlbepreisung wird innerhalb Y Stunden korrigiert").
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R3-1 – Institutionelle Details der Odds-Bildung
**Kommentar (kondensiert):** Der Hauptbefund (Closing-Preise informativer) ist
in Märkten mit Informationsakkumulation konzeptionell wenig überraschend.
Institutionelle Details fehlen (z. B. sharpe Bookmaker wie Pinnacle öffnen
früher / mit niedrigeren Limits, andere folgen); Bookmaker werden zu
symmetrisch behandelt.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R3-5 – Table 5 Benchmark / Sortierungsmechanismus
**Kommentar (kondensiert):** Benchmark-Argument: Wenn Opening = p + e1 + e2 und
Closing = p + e2 (e1 unabhängig von p entfernt), sollte eine Sortierung nach
Revisionsgröße NICHT nach Winning-Probability sortieren (~50 % je Bin), obwohl
Closing genauer ist. Die beobachtete große Spannweite (34 %-63 %) deutet auf
Sortierung nach zugrundeliegender Wahrscheinlichkeit hin, nicht nur
Rauschreduktion – Mechanismus/Benchmark unerklärt. Vorschlag: direkterer Test
(Realized Outcomes vs. Opening/Closing-Probabilities bedingt auf initiales
Probability-Level). Überschneidet mit R2-M9.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R3-6 – Informationsdiffusion zwischen Bookmakern (Reframing-Vorschlag)
**Kommentar (kondensiert):** Größere Perspektive: Der Datensatz eignet sich für
die Analyse des Informationsdiffusionsprozesses zwischen Bookmakern (welche
Bookmaker führen Preisänderungen an, welche folgen mit Lag; Rolle sharper
Bookmaker; Diffusionsgeschwindigkeit im Netzwerk; Zusammenhang Opening-Zeitpunkt
und Forecast-Accuracy). Wird als vielversprechendere Stoßrichtung vorgeschlagen
als generische Lern-Dynamik.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R2-M1 – Contribution vor Literaturübersicht
**Kommentar (kondensiert):** Das Intro enthält viel Literaturübersicht vor
klarer Nennung des eigenen Beitrags. Contribution zuerst, dann Literatur.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R2-M2 – Moskowitz-(2021)-Absatz kürzen
**Kommentar (kondensiert):** Der Absatz zu Moskowitz (2021) / Sportwettenmärkte
als Labor für Finanzmärkte (S. 2-3) ist evtl. verzichtbar/kürzbar, da in der
Literatur etabliert.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R2-M4 – Konkrete Zahlenbeispiele bei Metrik-Einführung
**Kommentar (kondensiert):** Konkrete Zahlenbeispiele beim Einführen von
Metriken (Close-to-End-Returns, Open-to-Close-Returns etc.) gewünscht.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R2-M5 – "winning rate should exceed/fall below 0.5" nur im Aggregat
**Kommentar (kondensiert):** Die Aussage "winning rate … should exceed/fall
below 0.5" (S. 6) gilt nur im Aggregat, nicht für einzelne Wetten (Beispiel:
20 %→30 %-Preis bleibt <50 %). Durchgängig klarer machen, wenn
Durchschnittsannahmen gemeint sind.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R2-M6 – Balanced-Book-Theory zu stark betont
**Kommentar (kondensiert):** Balanced-Book-Theory wird zu stark betont (S. 6) –
empirische Evidenz zeigt, dass viele Bookmaker nicht primär Buch-Balance
anstreben, sondern Positionen halten, wenn sie die eigenen Preise für genauer
halten. Durchgängig überdenken.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R2-M7 – RMSE-Einordnung / durchschnittliche Posting-Zeit in Figure 1
**Kommentar (kondensiert):** RMSE von 0.45 (S. 12) ohne intuitive
Einordnung/Baseline. Figure 1 sollte zusätzlich die durchschnittliche
Posting-Zeit zeigen (später postende Bookmaker profitieren evtl. nur von der
Beobachtung der Konkurrenz).
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R2-M8 – Table 7: Rauschen vs. systematischer Unterschied
**Kommentar (kondensiert):** Zu Table 7 (Forecast-Error-Varianz-Unterschiede
zwischen Bookmakern, z. B. 10Bet) mehr Intuition gewünscht: Rauschen durch
Stichprobengröße oder systematisch? Fokus eher auf Aggregatergebnisse?
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R2-M9 – Tables 5/6 + Eq. 3: Befund fast definitional
**Kommentar (kondensiert):** Der Befund (größere positive Preisbewegung →
höhere Winning Rate) ist wenig überraschend/fast definitional. Zusätzlich:
"if prices do not change, winning rates are approximately 0.5" ist für
Einzelwetten nicht korrekt (Favorit bei 0.70 bleibt bei 0.70). Analyse evtl.
als konfirmatorisch statt Primärergebnis einordnen. Überschneidet mit R3-5.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R2-M10 – Figure 6 (Lernrate vs. RMSE) entfernen
**Kommentar (kondensiert):** Figure 6 (Lernrate vs. RMSE-Korrelation,
corr_gamma_loss) entfernen – der Punkt lässt sich textlich genauso gut machen.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R2-M11 – Mechanik des Lernens bei Favoriten vs. Longshots
**Kommentar (kondensiert):** Mehr Intuition zu Richtung/Mechanik des Lernens
bei Favoriten vs. Longshots gewünscht: Öffnen Märkte zu aggressiv/konservativ
bei Favoriten, wie äußert sich Lernen konkret in der Preisbewegungsrichtung?
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R2-M12 – Lernraten bei bereits effizientem Opening
**Kommentar (kondensiert):** Wie sehen Lernraten aus, wenn der Markt bei
Opening bereits nahe effizient ist? Eine niedrige Lernrate könnte weniger
Ineffizienz statt langsamere Anpassung bedeuten – die Interpretation der
Querschnittsbefunde entsprechend einordnen.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## R2-M13 – "more competitive" statt "higher level"
**Kommentar (kondensiert):** "more competitive" (S. 22, Profi vs. Amateur) ist
präziser als "higher level"/"higher caliber" – beide Ligen sind kompetitiv,
der Unterschied ist das Spielniveau, nicht das Vorhandensein von Wettbewerb.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## AE-1 – Fußnote zu Pre-Match-Odds-Movements bei Oddsportal
**Kommentar (kondensiert):** Pre-match odds movements sind laut AE gut
dokumentiert kurz vor Spielende bei Oddsportal – verdient evtl. eine Fußnote
bei der Beschreibung der Datenerhebung.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## AE-2 – Inkonsistenz Pre-Match vs. In-Play in der Literaturübersicht
**Kommentar (kondensiert):** Inkonsistenz: Das Paper wertet in der
Literaturübersicht eine andere Studie ab, weil deren Daten überwiegend In-Play
seien, während das eigene Paper selbst explizit Pre-Match statt In-Play
fokussiert.
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** [zu ergänzen]
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]

## AE-3 – Priorität: alle Referees, Fokus auf Zensierung (R1-v)
**Kommentar (kondensiert):** Ausdrückliche Priorität des AE: Kommentare aller
Referees behandeln, mit besonderem Fokus auf die Zensierungs-Bedenken von
Referee 1 (siehe R1-v).
**Stand vor Revision:** [zu ergänzen]
**Untersuchung:** Meta-Kommentar; die inhaltliche Bearbeitung läuft unter
R1-v (Zensierung).
**Entscheidung:** [zu ergänzen]
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** offen
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen]
