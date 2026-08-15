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
  fit_rfa_mod (FEOpn−FECls) 82,53 %/17,47 %, kein Degenerationsmuster
  **[teilweise korrigiert, siehe Nachtrag 2026-08-08]**;
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

**Status:** Analyse abgeschlossen, Papertext ausstehend (alle vier Modelle
auf cluster-robuste Inferenz umgestellt; siehe Nachträge 2026-08-01 und
2026-08-08)

**Superseded:** die Erwartung, crossed random effects seien für alle
betroffenen Gleichungen der richtige Weg — sie sind es für keine, weil die
abhängigen Variablen innerhalb eines Matches nahezu konstant sind (Details
in den beiden Nachträgen).

**Für Response-Dokument:** Wir haben die Modelle zunächst wie vom Referee
vorgeschlagen mit crossed random effects für Bookmaker und Match neu
geschätzt (Umstieg auf R/lme4, da statsmodels gruppenübergreifende crossed
effects nicht korrekt abbildet). Wir werden darlegen, dass ein
Match-Random-Intercept in unserem Fall die abhängige Variable absorbiert
statt die Abhängigkeit zu modellieren — der Spielausgang ist über die
Bookmaker eines Matches per Konstruktion konstant — und dass die
crossed-Fassungen deshalb einen anderen Schätzgegenstand liefern, keinen
Präzisionsgewinn. Wir werden daher die vom Referee selbst genannte
Alternative verwenden, cluster-robuste Inferenz auf Match-Ebene, und
berichten, dass die Standardfehler dadurch um den Faktor 3 bis 4 steigen,
was die Kritik in der Sache bestätigt. Für die relative Prognosegenauigkeit
werden wir zusätzlich auf Bookmaker-Ebene clustern und begründen, warum das
dort nötig ist. Den starken Match-Cluster in eq:resp_to_info werden wir
zurückhaltend einordnen, weil er teilweise eine mechanische Eigenschaft der
Return-Metrik bei verlorenen Wetten ist.

**Offen / [zu ergänzen]:** match_icc (Anteil der Gesamtvarianz durch Matchup)
wurde als Zusatzkennzahl diskutiert, aber für keines der drei Modelle in
`crossed_comparison_summary.csv` ergänzt – Entscheidung offen. Formulierung
der finalen Paper-Passagen [zu ergänzen].

**Nachtrag 2026-08-01 – kontinuierliche Fassung: Cluster-robust statt
Match-RE.** Beleg: `revision/snapshots/continuous_unbiasedness/main_spec/`.
Die Hauptspezifikation der *kontinuierlichen* Unbiasedness-Regression
(`X = log(Stunden bis Anpfiff)`, Kovariaten, Bookmaker-Intercept + -Slope)
wurde gerechnet; der Match-Intercept erweist sich hier als der **falsche**
Weg, die R1-ii-Forderung zu erfüllen.

- **Absorption, exakt derselbe Mechanismus wie bei RtrnClsEnd oben:**
  `Endog = Match − p_ref` ist innerhalb einer Serie konstant, **99,83 %** der
  Varianz liegen auf Matchup-Ebene (ANOVA, Serienebene; 99,81 % auf
  Beobachtungsebene). Ein Match-RE absorbiert damit praktisch die abhängige
  Variable (sd 0,440 von 0,459), die Residual-sd fällt auf 0,015. Für die
  Within-Match-Identifikation bleiben **1,1 % der `p_ref`-Varianz**
  (Within-sd 0,0197 gegen 0,1900 insgesamt).
- **Folge:** die Fassung mit `(1|Matchup)` ist im Niveau zwar stabil
  (β₁ = 0,466 für k = 6/10/20), aber in der Kovarianzstruktur entartet –
  Bookmaker-Intercept sd 0,00017 (bei k = 10 meldet lme4 `boundary (singular)
  fit`), Bookmaker-Slope 6× der Wert ohne Match-RE, β₁-SE über das gesamte
  Gitter konstant 0,155. β₁ = 0,466 gegen 0,988 ohne Match-RE ist ein
  **Wechsel des Schätzobjekts**, kein Präzisionsgewinn.
- **Empfohlene Fassung: CR1-Cluster-Sandwich auf Matchup-Ebene** – exakt die
  im Kommentar genannte Minimalvariante („mindestens cluster-robuste Inferenz
  auf Match-Ebene"). Punktschätzer unverändert
  (`max |β₁(OLS) − β₁(lme4)| = 0,006`), SEs **3,02× modellbasiert** und
  6,34× iid. Inferenziell materiell: β₁ ist danach nur am fernen Rand
  (darüber) und anpfiffnah (darunter) von 1 verschieden, **im mittleren
  Bereich nicht**.
- **Querprüfung gegen die R1-ii-Fits:** `match_var` 0,19365 hier gegen
  0,19316 in `crossed_mixed_lm_single_test.csv`, `bookies_cov` −5,0797e−05
  gegen −5,073e−05 – die Komponenten reproduzieren.
- **Toolchain-Nebenbefund:** mgcv kann den Match-RE nicht tragen (20.741
  Level, dichte Behandlung, gemessen ~p³ → ~25 h, Speicheruntergrenze ~17 GB
  gegen 11,4 GB) und erlaubt ohnehin nur **unabhängige** REs (`bs="re"` ist
  „simple independent"; `xt`/`paraPen` nehmen nur feste Präzisionsmatrizen).
  Daher Spline-Basis via `smoothCon` explizit gebaut und in `lmer` gesteckt –
  gleiche Toolchain wie oben, korrelierte REs inkl. `bookies_cov` verfügbar.
- **Offen:** Bootstrap-Validierung des Sandwich (B = 100, Cluster =
  Matchup) lief zum Commit-Zeitpunkt noch; begründet, weil die Cluster stark
  unbalanciert sind (1–24 Bookmaker je Matchup, Median 7) und die
  CR1-Skalarkorrektur das nicht sieht.

**Nachtrag 2026-08-08 – Eq. 1 und Eq. 2 nachgezogen, Cluster-Dimension folgt
der Abhängigkeitsstruktur.** Beleg:
`revision/snapshots/cluster_inference_eq12/`. Datenbasis `revision-baseline`
(normalisiert), `df_oc` mit 172.663 Kontrakten, 20.588 Matchups, 24
Bookmaker.

**Entscheidung: alle vier Modelle nutzen cluster-robuste Inferenz, aber
nicht dieselbe Clusterdimension.**

| Modell | Inferenz |
|---|---|
| Unbiasedness-Regression | CR1 auf Matchup |
| Eq. 1 (`resp_to_info`) | CR1 auf Matchup |
| Eq. 3 (Kontraktebene) | CR1 auf Matchup |
| **Eq. 2 (`ags_test`, „All")** | **zweifach geclustert, Matchup + Bookmaker (Cameron-Gelbach-Miller)** |

*Gate vorab* (Schwelle 0,01 auf den Kernkoeffizienten, wie bei der
Unbiasedness-Regression): Eq. 1 |β(OLS) − β(lme4)| = **0,000000** – beide
Fits melden `boundary (singular) fit`, die Bookmaker-Komponenten kollabieren
auf null und das Mixed Model fällt exakt auf OLS zurück. Eq. 2
**0,000125**. Beide Gates halten, der Sandwich ist übertragbar.

*SE-Inflation gegen die modellbasierte lme4-SE:*

- **Eq. 1: Faktor 3,36–4,02**, Kernkoeffizient `RtrnOpnCls` **3,83**
  (0,02112 → 0,08084). Damit im selben Bereich wie die
  Unbiasedness-Regression (3,0–3,6) und Eq. 3 (2,96–4,11). `RtrnOpnCls`
  geht von t = +1,31 auf **+0,34**; der Kernbefund ändert sich nicht, weil
  der Koeffizient auch publiziert schon insignifikant war (p = 0,202
  normalisiert).
- **Eq. 2: Intercept (= AGS-Statistik) Faktor 2,43** (t = +6,30 → **+2,59**),
  Kovariaten **2,70–3,37**.

*Warum Eq. 2 die zweite Dimension braucht.* Für `Exog` ist die
Matchup-Cluster-SE **kleiner** als die modellbasierte, **Faktor 0,92**. Das
ist kein Rechenfehler: `Exog` wird in `fit_rfa_mod.py:41–49` **je Bookmaker
zentriert**, seine Variation ist damit weitgehend within-bookmaker, und
Matchup-Clustering greift dort kaum (gegen die iid-SE ist der Faktor
trotzdem 2,7). Die modellbasierte SE ist ihrerseits groß, weil sie die
Varianz des Random Slope über Bookmaker mitträgt. Ein reiner
Matchup-Sandwich würde diese Unsicherheit **fallen lassen** – und sie ist
hier real (siehe R2-M8). Zweifach geclustert steigt die `Exog`-SE von
**0,00033 auf 0,00050**, t von −11,90 auf **−8,00**. *Einschränkung:* nur 24
Bookmaker-Cluster, die zweite Dimension ist grob.

**Korrektur der Einschätzung oben zu `fit_rfa_mod`.** Die dort festgehaltene
Aussage „82,53 %/17,47 %, kein Degenerationsmuster" war **deskriptiv
richtig** und wird nicht zurückgezogen – die Between/Within-Zerlegung zeigt
tatsächlich keinen algebraischen Kollaps wie bei `RtrnClsEnd`. Der
tatsächlich geschätzte crossed-Fit kippt den Koeffizienten aber dennoch:

```
beta(Exog)  Bookmaker-only -0,00386   ->   crossed +0,01970   (Vorzeichenwechsel)
Matchup-Komponente 0,002698  >  Varianz der AV 0,002675   (Residual 0,000495)
```

Die Matchup-Varianzkomponente **übersteigt die Gesamtvarianz der abhängigen
Variablen**. Auch ohne algebraische Degeneration ist der crossed-Fit damit
ein **Wechsel des Schätzgegenstands**, kein Präzisionsgewinn – dieselbe
Lehre wie bei der Unbiasedness-Regression und bei Eq. 1 (dort deutlicher:
Residual-sd 0,057 gegen AV-sd 1,124, Bookmaker-Slope-Varianz von ~0 auf
1,65, β von +0,0276 auf −0,2200, und `lme4` meldet dabei **keine** Warnung).

**Offen 1 – welche SE-Basis wird in den Tabellen berichtet?** Die
publizierten Standardfehler stammen aus `statsmodels` MixedLM, die neuen aus
`lme4`. Bei diesen singulären Fits weichen beide ab: Eq. 2, Intercept
**z = 3,84 (statsmodels) gegen t = 6,30 (lme4)**. Gegen die publizierte SE
wäre der Inflationsfaktor rund **1,5** statt 2,43. **Vor dem Schreiben
klären**, welche Basis in den Tabellen steht – sonst enthält die
ausgewiesene SE-Inflation einen Softwareanteil und ist gegenüber den
Referees nicht sauber begründbar.

**Offen 2 – Eq. 1: die Kovariaten fallen unter Signifikanz.** Nach
Clustering: `Compet_ITF_Men` z = −6,67 → t = **−1,87**, `Compet_WTA` −4,89 →
**−1,22**, `TsDur` −2,22 → **−0,66**. In Tabelle 3 bleibt cluster-robust
praktisch nichts signifikant. **Beim Schreiben prüfen:** enthält der
Papertext Aussagen über Wettbewerbsunterschiede in der Vorhersagbarkeit von
close-to-end-Renditen, sind diese nicht mehr haltbar. Der Kernbefund
(`RtrnOpnCls` insignifikant) ist davon unberührt und wird sogar deutlicher.

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
- **Within-Bookmaker-Test des Verspätungseffekts** (arbeitet die
  Konfundierungs-Einschränkung ab). Erstens ist die Konfundierung mild:
  **86,4 %** der Variation von log1p(Verspätung) sitzen *innerhalb* der
  Bookmaker, nur 13,6 % zwischen ihnen; 22 von 24 Bookmakern haben alle vier
  Verspätungsquartile mit ≥ 5 % besetzt (mittlerer HHI 0,308 gegen 0,250 bei
  perfekter Streuung). Zweitens überlebt der Effekt die Within-Identifikation:
  mit Bookmaker-FE, bookmakerspezifischer Steigung (`Exog:B`) und
  within-zentrierter Verspätung bleibt der Interaktionsterm bei 24 edf
  hochsignifikant, und **90 %** der Endspreizung bleiben erhalten (−0,350
  gegen gepoolt −0,390); ohne `Exog:B` sind es 94 % (−0,366). β₁ wird dabei
  über eine über alle Verspätungsstufen **feste** Bookmaker-Gewichtung
  marginalisiert, damit kein Kompositionseffekt einläuft. Drittens, modellfrei:
  Split je Bookmaker an der *eigenen* Median-Verspätung ergibt am Fensterende
  bei **18 von 24** Bookmakern ein negatives Δ (Vorzeichentest p = 0,011,
  t-Test p = 0,0008, gewichtetes Mittel −0,323) – konsistent mit dem
  GAM-Wert. Bei den fünf Bookmakern mit der breitesten eigenen Verteilung ist
  der Kontrast stärker (−0,478). **Grenze:** für das Kurven*mittel* trägt der
  Within-Befund nicht (13 von 24, p = 0,42); belastbar ist nur der Endwert.
  Die Konfundierung mit der Serienlänge bleibt unkontrolliert.

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
(Abschnitt 5, Skript `_attenuation.py`), der Within-Bookmaker-Test ebendort
(Abschnitt 6, Skript `_within_bookmaker.py`; M0 reproduziert das committete
Interaktionsmodell auf edf/F exakt).

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
Attenuation ist – die geringere Regressorvarianz erklärt davon ~1 %. Er ist
auch kein Bookmaker-Effekt: 86 % der Verspätungsvariation liegen innerhalb der
Bookmaker, und 90 % der Endspreizung überleben Bookmaker-Fixed-Effects; im
bookmaker-eigenen Früh/Spät-Split zeigen 18 von 24 denselben Kontrast.

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

**KORREKTUR (09.08.2026) – die „exakte Zentrierung auf 0,50" trägt nicht.**
Der oben unter *Level-Effekt* notierte Satz, die Normalisierung zentriere die
Player-1-Opening-Wahrscheinlichkeit **exakt auf 0,50 (roh: Median 0,5405)**,
ist auf der isolierten Vergleichsbasis `C1_refactor` → `C_normalized`
(identischer Code, identische Daten, einziger Unterschied das
`normalize`-Flag) **nicht reproduzierbar**. Gemessen auf `wide_imputed.h5`
beider Stufen, Spalte `OddsMvt0`:

| | C1_refactor (roh) | C_normalized (normalisiert) |
|---|---:|---:|
| Median Opening-Preis | **0,5464** | **0,5063** |
| Intercept Table 6 (`res_wp_re.tex`) | 0,505 | 0,504 |

Zwei getrennte Befunde, die vorher vermengt waren:

1. **Der Level-Effekt existiert** – die Normalisierung nimmt rund 4 pp aus dem
   Preisniveau (0,5464 → 0,5063), größenordnungsmäßig die halbe Marge bei
   7,8 % Overround. Das Ergebnis ist aber **0,5063, nicht 0,5000**, und das
   ist kein Margenrest: die Normalisierung erzwingt p₁ + p₂ = 1, nicht
   p₁ = 0,5. Die verbleibenden 0,006 sind eine echte Asymmetrie (Spieler 1
   ist etwas häufiger Favorit).
2. **Der Intercept bewegt sich gar nicht** – 0,505 roh gegen 0,504
   normalisiert. Er lag **nie** bei 0,54.

Woher die alten Zahlen stammen: 0,5405 aus der deskriptiven Margen-Diagnose
auf einer rekonstruierten Fassung, 0,5438 aus dem Papertext (`tex:628`, dort
als panelgewichtetes Mittel über alle Beobachtungen, nicht als Median der
Opening-Preise). Beides **andere Stichproben und andere Statistiken** als der
C1/C2-Vergleich – die Differenz ist kein Widerspruch, sondern ein
Objektwechsel.

**Konsequenz für die Antworten:** Die Aussage „der Intercept um 0,5 ist ein
Margen-Artefakt" trägt in dieser Form **nicht** und darf auch in der
**R2-C1**-Antwort (und R2-M5) nicht verwendet werden. Der R2-C1-Einwand zum
unintuitiven Intercept ist durch die Normalisierung **nicht** erledigt und
braucht eine eigene Antwort. Die R1-i-Antwort in `reply1_20260728.tex`
formuliert entsprechend nur noch, dass die Normalisierung den Level-Markup
entfernt, ohne eine Zentrierungszahl zu behaupten.

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
- R2-C3 (Perzentil- vs. Absolutzeit): **empirisch geprüft, R2 hat recht.**
  Derselbe absolute Zeitpunkt liegt je nach Marktlänge an ganz
  unterschiedlicher Stelle der relativen Achse: 5 h vor Anpfiff entspricht
  bei kurzen Märkten dem **65.**, bei langen dem **92. Perzentil**. Die
  Betting-Fenster streuen extrem (Median 16,8 h, p90 42,3 h, Maximum 197 h,
  CV 0,77) – die Perzentil-Achse mittelt also über sehr verschiedene
  absolute Lernperioden.
- Gegenprobe zur Fairness der relativen Achse: das **Within-Group-Lernprofil
  ist über die relative Achse glatt und monoton, über die absolute
  unregelmäßig.** Die relative Achse ist strukturell also *nicht* schlechter.
  Ausschlaggebend war deshalb nicht die Achse selbst, sondern dass die
  relative Achse ein Raster erzwingt und damit die Imputation – genau den
  Mechanismus, den R2-C2 angreift. Die kontinuierliche absolute Fassung
  kommt ohne Raster und ohne Imputation aus.
- R3-2 (RMSE-Konfundierung): Eine mögliche zusätzliche Konfundierung durch
  bookmaker-spezifische Margen wurde deskriptiv geprüft und **widerlegt** –
  die Korrelation zwischen Median-Opening-Marge und rohem RMSE über die
  Bookmaker ist NEGATIV (−0,34): die margenärmsten (sharp) Bookmaker
  (Pinnacle, BetInAsia) haben gerade die HÖCHSTEN RMSE. Die Margen-
  Konfundierungs-Hypothese scheidet damit als Erklärung aus; die RMSE-Anomalie
  läuft über Timing (R3-2 im engeren Sinn: unterschiedliche Opening-Zeitpunkte),
  nicht über die Marge. Details in open_questions.md (Abschnitt Margen/
  Normalisierung).
- **R3-2 (Timing-Kontrolle), nachgeholt.** Posting-Zeitpunkt je Serie =
  Anpfiff minus erster beobachteter Zeitstempel; Mediane je Bookmaker über
  die 24 der Schätzstichprobe. Spanne 16,57 h (Dafabet) bis 36,03 h
  (Betfair), Faktor 2,17.

  **Die konkrete Hypothese des Referees trifft nicht zu.** Pinnacle
  eröffnet median bei **20,63 h — Timing-Rang 12 von 24**, praktisch exakt
  beim Stichprobenmedian (20,45 h) — bei **RMSE-Rang 24**. BetInAsia
  dasselbe: Timing-Rang 13, RMSE-Rang 23. Die frühesten Eröffner (Betfair
  36,0 h, Betfred 35,7 h, 888sport 34,4 h) liegen beim RMSE im Mittelfeld.
  Pinnacles hoher Opening-RMSE ist kein Artefakt früher Marktteilnahme.

  **Der Mechanismus existiert dennoch.** Über die 24 Bookmaker auf
  Serienebene: Pearson **+0,409** (p = 0,047), Spearman **+0,470**
  (p = 0,020) — Vorzeichen wie vom Referee erwartet. Weil dieser
  Querschnitt über verschiedene Match-Portfolios mittelt und mit n = 24
  wenig Power hat, zusätzlich **innerhalb desselben Matchups** (18.394
  Matchups, 181.889 Kontrakte, cluster-robust auf Matchup): der
  Koeffizient auf `OpnHrs` im quadrierten Opening-Fehler beträgt
  **+1,17e−04, t = 4,12**; mit zusätzlichen Bookmaker-FE +1,14e−04,
  t = 3,73. **Sauber identifiziert**, nicht nur ein Querschnitt über 24
  Punkte — und die Stabilität gegenüber den Bookmaker-FE zeigt, dass der
  Effekt am Timing der einzelnen Serie hängt, nicht an einer festen
  Bookmaker-Eigenschaft.

  **Größenordnung: real, aber nicht der Haupttreiber.** Hochgerechnet auf
  die 19,46-h-Spanne der Bookmaker-Mediane ergibt der Within-Koeffizient
  ≈ **+0,0025 RMSE** gegen eine beobachtete Spanne von **0,018** auf
  Serienebene — rund ein Achtel. *Einschränkung:* die Within-Matchup-
  Streuung von `OpnHrs` beträgt sd 4,1 h, die Hochrechnung extrapoliert
  über diesen Bereich hinaus und unterstellt Linearität.

  **Marge herausgerechnet** bleibt die Richtung, nicht die Signifikanz:
  +0,409 → **+0,327** (p = 0,13; Rang-partiell +0,362, p = 0,090). Marge
  und Posting-Zeitpunkt sind selbst korreliert (Pearson −0,266, Spearman
  −0,435): margenarme Häuser eröffnen tendenziell später.
- **METHODISCHER BEFUND — in der publizierten Figur 1 ist der Zusammenhang
  unsichtbar.** Panelgewichtet beträgt die Korrelation **−0,059** (p = 0,79),
  auf den publizierten rohen Werten −0,083. Ursache:
  `bookmaker_accuracy.py:62` rechnet den RMSE **auf Panelebene**. `OpnOdds`
  ist je Serie konstant, also geht jede Serie mit ihrer Zahl an Preisupdates
  gewichtet ein. Diese Zahl korreliert **−0,73** mit dem Posting-Zeitpunkt
  (spät postende Bookmaker liefern mehr Updates je Serie, 5,6 bis 10,8) —
  **die Gewichtung hebt den Effekt exakt auf.**

  Serienebene ist die inhaltlich richtige Einheit: ein Bookmaker mit vielen
  Updates hat nicht mehr Prognosen abgegeben, sondern **dieselbe Prognose
  öfter aktualisiert**. Der Opening-Preis, um den es hier geht, existiert je
  Serie genau einmal.

  *Offen:* Entscheidung, ob die Produktionsrechnung auf Serienebene
  umgestellt wird. Betrifft **Figur 1 und Tabelle 7**.

**Entscheidung: getroffen — gespaltene Zeitachse.**
- **Unbiasedness-Regressionen: kontinuierliche absolute Achse**,
  `X = log(Stunden bis Anpfiff)`. Damit entfallen Raster und Imputation.
- **GMM und Bayesian bleiben auf der diskreten relativen Perzentil-Achse.**
  Begründung siehe R1-vi: Biais et al. (1999) ist rein zeitdiskret, eine
  kontinuierliche Lernrate wäre dort nicht ableitbar, sondern ein neues
  Modell.

Damit ist die frühere Alternative (a)/(b) nicht als Entweder-oder aufgelöst,
sondern nach Zielgröße getrennt: (a) für die Unbiasedness, (b) für das GMM —
jeweils mit eigener Begründung statt eines einheitlichen Kompromisses.

**Umsetzung:** Diagnostik abgeschlossen, Paper-Text ausstehend. Die
Hauptspezifikation der kontinuierlichen Fassung liegt in
`revision/snapshots/continuous_unbiasedness/main_spec/` (Ladder M_a–M_c,
Machbarkeitsmessung, cluster-robuste Inferenz, Bootstrap-Validierung,
Randdiagnostik). Ergebnis der neuen Spezifikation:

- **β₁ 1,244 (24 h) → 0,938 (6 h) → 0,759 (1 h)**: Unterreaktion früh,
  Unverzerrtheit in der Mitte, Überreaktion nahe Anpfiff. Ein **Kontinuum,
  keine Phasen** — das beantwortet zugleich R2-C7 und R1-vii.
- **Match-Random-Effect begründet ausgeschlossen**: 99,83 % der
  `Endog`-Varianz liegen auf Matchup-Ebene, für die Within-Match-
  Identifikation bleiben nur 1,1 % der `p_ref`-Varianz. Stattdessen
  **cluster-robuste Inferenz auf Matchup-Ebene** — die von R1-ii ausdrücklich
  genannte Alternative („mindestens cluster-robuste Inferenz auf
  Match-Ebene").
- **Die bisherigen SEs waren um den Faktor 3,6 zu klein**
  (Bootstrap gegen modellbasiert). Sandwich und Bootstrap stimmen an den
  Rändern überein, in der Fenstermitte ist der Bootstrap 10–22 % weiter;
  **berichtet werden die Bootstrap-SEs** als Primärinferenz.
- **Feste vs. penalisierte Spline-Basis**: Median |Δ| = 0,0159 über den
  Berichtsbereich 0,067–48 h — der Preis der festen Basis, die die
  lme4-Route erzwingt, ist vernachlässigbar.

**Beleg/Validierung:** RMSE-Rangfolge und Margen-Kennzahlen gegen Paper-Zahlen
validiert (fig:rmse-Extremränge exakt reproduziert); negative Margen-RMSE-
Korrelation empirisch bestätigt. Für die Zeitachsen-Entscheidung:
`revision/snapshots/continuous_unbiasedness/` (Commits `5680d91`, `9c05946`,
`56a0af6`) und `revision/snapshots/gmm_imputation_test/` (`bf9b97a`). Für die
Timing-Kontrolle im engeren Sinn: `revision/snapshots/rmse_baselines/` —
`posting_time_by_bookie.csv`, `correlations.csv`,
`partial_correlations.csv`, `joint_regression.csv`, `within_matchup_fe.csv`.
Die Margen-RMSE-Korrelation von −0,34 wurde dabei exakt reproduziert
(−0,3431).

**Status:** R2-C3 umgesetzt (Diagnostik abgeschlossen, Paper-Text ausstehend);
R3-2 Diagnostik abgeschlossen, Papertext ausstehend (Margen-Konfundierung
widerlegt, Timing-Kontrolle durchgeführt; offen bleibt allein die
Entscheidung über die Serienebene in der Produktionsrechnung)

**Superseded:** die frühere Formulierung „Entscheidung: Offen. (a) vs. (b)"
ist durch die gespaltene Achse oben ersetzt.

**Für Response-Dokument:** Wir werden bestätigen, dass die Kritik zutrifft, und
sie mit der eigenen Prüfung belegen (5 h vor Anpfiff = 65. Perzentil bei
kurzen, 92. bei langen Märkten; Fensterlängen mit CV 0,77). Wir werden die
Unbiasedness-Regressionen auf eine **kontinuierliche absolute Zeitachse**
(log Stunden bis Anpfiff) umstellen und begründen, dass dies zugleich die
Imputation überflüssig macht (Verbindung zu R2-C2). Wir werden erläutern,
warum GMM und Bayesian auf der diskreten relativen Achse bleiben: das
zugrunde liegende Modell von Biais et al. (1999) ist rein zeitdiskret, eine
kontinuierliche Lernrate wäre dort nicht ableitbar (Details unter R1-vi).
Wir werden zudem darlegen, dass die
Unterschiede in der Opening-Genauigkeit nicht durch bookmaker-spezifische
Margen erklärt werden (die margenärmsten Bookmaker weisen die höchsten
Forecast-Fehler auf).

Zur Timing-Konfundierung werden wir dem Referee in der Sache zustimmen und
zugleich sein konkretes Beispiel korrigieren: Pinnacle eröffnet nicht früher
als die anderen, sondern genau beim Stichprobenmedian (Rang 12 von 24), hat
aber den höchsten Opening-RMSE — der Befund lässt sich dort also nicht mit
früher Marktteilnahme erklären. Wir werden den vom Referee vermuteten
Mechanismus dennoch nachweisen, und zwar sauber identifiziert innerhalb
desselben Spiels: unter Matchup- und Bookmaker-Fixed-Effects erhöht eine
Stunde früheres Posting den quadrierten Opening-Fehler signifikant. Wir werden
die Größenordnung offenlegen — über die Spanne der Bookmaker-Mediane
entspricht das etwa 0,0025 RMSE gegen eine beobachtete Spanne von 0,018, also
rund einem Achtel der Unterschiede — und daraus folgern, dass Timing die
Rangfolge mitprägt, sie aber nicht erklärt. Wir werden die Posting-Zeit wie
von Referee 2 vorgeschlagen in Figure 1 aufnehmen (siehe R2-M7) und dabei
offenlegen, dass die Bookmaker-RMSE künftig auf Serienebene berichtet werden:
in der bisherigen panelgewichteten Rechnung geht jede Serie mit ihrer Zahl an
Preisupdates ein, und weil diese Zahl mit dem Posting-Zeitpunkt korreliert,
verdeckt die Gewichtung genau den Zusammenhang, nach dem der Referee fragt.

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

**Untersuchung:** Querverweis auf **R2-C1**: in der Kontraktebenen-Fassung von
Eq. 3 gibt es **keine Bookmaker-Heterogenität in der Preisinformativität**.
RE und FE kommen unabhängig zum selben Schluss (Belege
`revision/snapshots/eq3_contract_level/`, Commit `d4183ab`):

- Random Effects (S4): Varianzen **exakt null** (`boundary (singular) fit`),
  S4 identisch zu S3 bis fünf Nachkommastellen, R² marginal = konditional.
- Fixed Effects mit vollen Dummies und Interaktionen: R²-Zuwachs **0,0001**
  für 46 Parameter; cluster-robuste Wald-Tests Niveau chi2(23) = 31,48
  (p = 0,111), Steigung chi2(23) = 20,78 (p = 0,595), gemeinsam
  chi2(46) = 52,91 (p = 0,225). Die bookmakerspezifischen Steigungen streuen
  nominell 0,771 (BetInAsia) – 1,083 (Dafabet), aber **kein einziger der 23
  Kontraste** ist von der Referenz zu unterscheiden.

**Für die Sharp/Soft-Frage ist das direkt relevant:** Pinnacle (0,8135) und
Betfair (0,8063) — die im Kommentar als „typischerweise sharp" genannten —
liegen zwar am unteren Rand der Steigungsverteilung, aber innerhalb des
Rauschens (t = −1,35 bzw. −1,13 gegen die Referenz). **Eine Sharp/Soft-
Klassifikation ließe sich aus Eq. 3 also nicht begründen.**

Bemerkenswert ist der **Kontrast zu den Lernraten**, wo die
Bookmaker-Heterogenität substanziell und robust ist (γ von 0,0014 bei GGBET
bis 0,0124 bei Dafabet, Faktor 9, stabile Rangfolge über Spezifikationen,
Spearman 0,88 auch nach dem Exponenten-Fix). **Bookmaker unterscheiden sich
darin, wie schnell sie lernen, aber nicht darin, wie gut ihre Preisbewegungen
den Ausgang vorhersagen.**

*Einschränkung:* Dafabet hat mit SE 0,2031 den größten Standardfehler bei
zugleich höchster Steigung — bei dünn besetzten Bookmakern ist die Power
gering. Belastbar ist die Aussage für das Kollektiv (Wald über alle 23), für
einzelne kleine Bookmaker nur schwach.

**Entscheidung:** [zu ergänzen]

**Umsetzung:** [zu ergänzen]

**Beleg/Validierung:**
`revision/snapshots/eq3_contract_level/bookie_fe_slopes.csv`, `s4_varcomp.csv`

**Status:** offen (Befund zur fehlenden Heterogenität liegt vor, Konsequenz
für die Klassifikation noch zu ziehen)

**Superseded:** —

**Für Response-Dokument:** Wir werden die Sharp/Soft-Charakterisierung
abschwächen und dabei auf einen eigenen Befund verweisen: in der
Kontraktebenen-Fassung von Eq. 3 finden wir **keine** Bookmaker-Heterogenität
in der Preisinformativität — weder über Random noch über Fixed Effects, und
auch die als sharp geltenden Anbieter (Pinnacle, Betfair) liegen innerhalb des
Rauschens. Heterogenität zeigt sich bei den Lernraten, nicht bei der
Prognosegüte der Preisbewegungen.

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

**Nachtrag – Zeitdiskretheit, trägt die Achsen-Entscheidung in R2-C3:**
- **Biais et al. (1999) ist rein zeitdiskret.** Das asymptotische Resultat
  stammt aus Vives (1995) / Germain et al. (1996) und ist ein Grenzwert in
  der **Anzahl diskreter Handelsrunden**, kein Diffusionslimes. Im Original
  gibt es keine SDE, kein `dt` und keinen Kalman-Bucy-Filter. Eine
  kontinuierliche Learning Rate wäre daher nicht aus diesem Rahmen
  ableitbar, sondern ein **neues Modell** — deshalb bleiben GMM und Bayesian
  auf der diskreten relativen Achse.
- **Biais adressiert R2-C3 selbst, aus dem Originalrahmen heraus**
  (S. 1240, Gl. 13): die Momentbedingung ist **invariant gegenüber
  Zeitskalierung**. Ist die wahre Lernzeit `n·t` statt `t`, kürzt sich `n`
  im Verhältnis zweier Momentgleichungen heraus. Die Kritik „die
  Perzentil-Achse dehnt/staucht die Zeit je Match" trifft das GMM damit
  nicht in gleicher Weise wie die Unbiasedness-Regressionen.
- **ZU PRÜFEN, noch offen:** Gilt diese Invarianz auch bei **match-
  spezifischem `n`**? Biais' Argument ist für einen globalen Skalenfaktor
  formuliert. Da die Fensterlängen hier stark streuen (CV 0,77, siehe
  R2-C3), ist `n` gerade nicht konstant über Matches. Solange das nicht
  geklärt ist, trägt das Invarianzargument die GMM-Entscheidung nur unter
  Vorbehalt.

**Entscheidung:** GMM und Bayesian bleiben auf der diskreten relativen
Perzentil-Achse (siehe Nachtrag oben und R2-C3). Die beiden älteren
Befunde (K=0, Nelder-Mead) sind davon unberührt und weiterhin offen.
**Umsetzung:** [zu ergänzen]
**Beleg/Validierung:** [zu ergänzen]
**Status:** teilweise (Zeitdiskretheit geklärt und für R2-C3 nutzbar, mit
offener Frage zur match-spezifischen Skalierung; K=0 und Nelder-Mead offen)
**Superseded:** —
**Für Response-Dokument:** Wir werden darlegen, dass das zugrunde liegende
Modell von Biais et al. (1999) rein zeitdiskret ist – das asymptotische
Resultat ist ein Grenzwert in der Anzahl diskreter Runden (Vives 1995;
Germain et al. 1996), kein Diffusionslimes – und dass eine kontinuierliche
Lernrate daher ein anderes Modell wäre. Wir werden ergänzen, dass Biais die
Zeitskalierungs-Frage selbst behandelt (S. 1240, Gl. 13): der Skalenfaktor
kürzt sich im Verhältnis zweier Momentgleichungen heraus. [zu ergänzen:
Behandlung des match-spezifischen Skalenfaktors]

## R1-vii – Überinterpretation der Unbiasedness-Regressionen / glatterer Koeffizientenpfad
**Kommentar (kondensiert):** Die Unbiasedness-Regressionen (Fig. 3) werden zu
stark interpretiert – die ökonomische Größenordnung des RMSE-Rückgangs ist
moderat, und das "Phasen"-Narrativ beruht auf wiederholten punktweisen
Konfidenzintervallen. Gefordert: formale Tests mit simultanen
Konfidenzbändern oder ein glatteres dynamisches Modell des Koeffizientenpfads.
**Stand vor Revision:** Punktweise Schätzung an 50 Perzentilen mit
punktweisen Konfidenzintervallen; das „Phasen"-Narrativ (Lernen, Pause,
Wiederaufnahme) wurde aus dem Zackenmuster dieser Punktschätzer gelesen.

**Untersuchung:** Der Referee hat recht, und zwar deutlich.
- **0 von 48 benachbarten punktweisen Änderungen sind einzeln signifikant**
  (größtes |z| = 1,93). Das Zackenmuster, auf dem das Phasen-Narrativ
  beruht, ist **Rauschen** – schon ohne Korrektur für multiples Testen.
- **Ein Spline über die punktweisen Schätzer bringt null zusätzliche
  Struktur**, gegenüber einer Geraden dagegen **+20 Punkte R²_w**. Die
  wahre Kurve ist glatt und monoton, ohne Wendepunkte.

**Entscheidung:** Das **Phasen-Narrativ wird aufgegeben** („pause in
learning", „resumption") und durch eine **monotone Beschreibung** ersetzt.
Umgesetzt wird das über dieselbe kontinuierliche Spezifikation wie in R2-C3;
damit ist zugleich die Forderung nach einem „glatteren dynamischen Modell des
Koeffizientenpfads" erfüllt.

**Umsetzung:** Diagnostik abgeschlossen, Paper-Text ausstehend. Die neue
Fassung liefert **β₁ 1,244 (24 h) → 0,938 (6 h) → 0,759 (1 h)**: früh
Unterreaktion, in der Mitte Unverzerrtheit, nahe Anpfiff Überreaktion – ein
Kontinuum ohne Phasen (siehe auch R2-C7). Die Inferenz läuft über
cluster-robuste Standardfehler auf Matchup-Ebene, validiert per
Cluster-Bootstrap; die bisherigen SEs waren um Faktor 3,6 zu klein.

**Nachtrag – simultane Inferenz (die wörtliche Forderung des Referees).**
Auf die B = 100 Cluster-Bootstrap-Replikate wurde ein **sup-t-Band** gesetzt.
Die Kovarianz von β₁(·) über das Gitter hat effektiven **Rang 5** (k = 6-
Splinebasis), ist also aus 100 Replikaten gut geschätzt; kritischer Wert
**2,617 gegen 1,960** punktweise. Ergebnis in zwei Teilen:
- **H0: β₁(t) = 1 für alle t → NICHT verworfen** (sup-|t| = 2,509,
  p = 0,066). Simultan schließen **0 von 96** Gitterpunkten die 1 aus, gegen
  **44 von 96** punktweise. Wo genau der Preis verzerrt ist, lässt sich nicht
  mehr sagen. Der Test liegt auf der 5-%-Grenze und kippt mit dem
  Berichtsfenster (0,066 / 0,057 / 0,044 bei Trim 48/36/24 h) – bewusst als
  *nicht verworfen* berichtet, nicht als knapper Erfolg beim engsten Trim.
- **H0: β₁(t) konstant → VERWORFEN** (sup-|t| = 3,998, p = 0,0006, gegen
  Trim unempfindlich). Randkontrast β₁(24 h) − β₁(0,25 h) = **0,477**,
  SE 0,117, **t = 4,08**. Der Pfad existiert, seine Lokalisierung nicht.

Gegenrechnung auf der publizierten Kurve: **49/50** Perzentile punktweise →
47/50 unter Šidák → 18/50 mit SE × 3 → **1/50 unter beidem**. Die
Multiplizität kostet fast nichts, die Clusterung fast alles.

**Nachtrag – RMSE-Größenordnung (Teil 1 des Kommentars, vorher unbearbeitet).**
Der geplottete `rmse` ist der **Residual-RMSE der Regression**
(`fit_mixed_lm.py:60`), nicht der RMSE des Preises. Der direkte,
kompositionsfreie Vergleich auf echten Beobachtungen (je Serie erste gegen
letzte, matchup-cluster-robust): Brier **0,20428 → 0,20315**, Differenz
**−0,00113**, SE 0,00026, **t = −4,39**. Signifikant, aber klein: **das
Wettfenster steuert 2,5 % der Prognoseleistung des Preises gegenüber dem
Münzwurf bei, 97,5 % stehen bei der ersten Beobachtung fest.** Der Referee hat
in der Sache recht.

**Und auch hier ist die Imputation im Spiel:** dieselbe Größe auf dem
Produktionsraster gerechnet ergibt −0,00462 statt −0,00113, **Faktor 4,08**.
Die späten Werte stimmen überein (0,20330 gegen 0,20315), die ganze Differenz
sitzt am frühen Rand – derselbe Mechanismus wie beim β₁-Pfad.

**Einschränkung:** Der Formtest läuft auf der vollen kontinuierlichen
Stichprobe (Zelle C). Auf den vollständig beobachteten Serien (Zelle D) ist
der Pfad flacher: 1,299 → 1,087 statt 1,289 → 0,771. Richtung robust,
Amplitude teilweise Komposition. Bootstrap-Replikate für Zelle D existieren
nicht.

**Beleg/Validierung:** `revision/snapshots/continuous_unbiasedness/`
(Commits `5680d91`, `9c05946`, `56a0af6`); simultane Inferenz und
RMSE-Einordnung in `continuous_unbiasedness/main_spec/`, Nachtrag zu
`README.md`, Skripte `_simultaneous.py` und `_rmse_magnitude.py`.

**Status:** Antwort im Reply-Dokument entworfen; Paper-Text ausstehend

**Superseded:** —

**Für Response-Dokument:** Entworfen in `revision/reply1_20260808.tex`
(R1, Kommentar 7), dreiteilig: (i) die RMSE-Größenordnung wird zugestanden und
mit 2,5 % / 97,5 % beziffert, plus Skill-Score-Einordnung (Querverweis
R2-M7); (ii) das Phasen-Narrativ wird zurückgenommen, belegt mit der Tabelle
49/50 → 1/50; (iii) an seine Stelle treten das glatte dynamische Modell und
die beiden globalen Tests – *wo* der Preis verzerrt ist, sagen wir nicht mehr,
*dass* es einen Koeffizientenpfad gibt, sagen wir jetzt formal. Anschluss an
R2-C7 (Lernen als Kontinuum).

## R1-viii – Favorite-Longshot-Bias direkt zeigen
**Kommentar (kondensiert):** Favorite-Longshot-Ergebnisse plausibel, aber
indirekt. Direkt zeigen: Favorite-Longshot-Bias in Opening-/Closing-Preisen,
seine Verkleinerung über das Betting-Fenster und den Zusammenhang mit den
geschätzten Lernraten.
**Stand vor Revision:** [zu ergänzen]

**Untersuchung:** Ein direkter Nachweis fällt als Nebenprodukt der
Kontraktebenen-Spezifikation aus **R2-C1** an (Belege dort,
`revision/snapshots/eq3_contract_level/`, Commit `d4183ab`):

- **LPM:** `eta_1 = 1,12480` auf den Opening-Preis, cluster-robust
  **t = 7,27 gegen 1** (p = 3,5e−13). Ein Koeffizient über 1 heißt: die
  Opening-Preise sind **unterdispers**. Bei `OpnOdds = 0,2` sagt das Modell
  0,175 vorher, bei 0,8 dagegen 0,85 — Longshots gewinnen seltener als
  impliziert, Favoriten häufiger. Das ist der Favorite-Longshot-Bias in
  direkt ablesbarer Form.
- **Logit-Kalibrierung:** Steigung auf `logit(OpnOdds)` = **1,18431**
  (gegen 1: t = 24,88), Intercept 0,00115 (gegen 0: p = 0,83). Die
  Verzerrung sitzt **in der Steigung, nicht im Niveau** — genau die Signatur
  eines Favorite-Longshot-Bias, nicht eines allgemeinen Miskalibrierungs-
  Offsets.

Damit sind zwei der drei vom Referee geforderten Punkte abgedeckt (Bias in
den Opening-Preisen, direkt statt indirekt). **Offen bleiben:** (a) dieselbe
Kalibrierung für **Closing**-Preise, um die geforderte *Verkleinerung über das
Betting-Fenster* zu zeigen; (b) der Zusammenhang mit den geschätzten
Lernraten. Beides ist mit demselben Frame billig nachzurechnen.

**Entscheidung:** [zu ergänzen]

**Umsetzung:** Teilweise — Opening-Kalibrierung liegt vor, Closing-Vergleich
und Lernraten-Bezug ausstehend.

**Beleg/Validierung:** `revision/snapshots/eq3_contract_level/ladder.csv`,
`logit_check.csv`, `cluster_robust.csv`.

**Status:** beantwortet (siehe Nachtrag 2026-08-15)

**Superseded:** Der Satz „Beides ist mit demselben Frame billig nachzurechnen"
stimmte; das Ergebnis der Nachrechnung widerspricht aber der im Kommentar
unterstellten Richtung — siehe Nachtrag.

**Für Response-Dokument:** Wir werden den Favorite-Longshot-Bias direkt
ausweisen: der Koeffizient auf den Opening-Preis liegt bei 1,125 und damit
signifikant über eins, und die Logit-Kalibrierungssteigung bei 1,184 bei einem
Intercept, der den Effizienzwert null exakt trifft. Wir werden ergänzen, wie
sich diese Kalibrierung vom Opening zum Closing verändert und wie sie sich zu
den geschätzten Lernraten verhält.

### Nachtrag 2026-08-15 – alle drei Teilfragen gerechnet

Belege: `revision/snapshots/flb_calibration/` (README + vier Skripte + CSVs),
Antwort geschrieben in `reply1_20260728.tex`.

1. **Bias in beiden Preisen, direkt gemessen.** Kalibrierungssteigung
   `lambda` = **1,1155** am Opening und **1,1131** am Closing, CR1 auf
   Matchup, t gegen 1 = 6,77 und 6,92; Logit 1,1649 und 1,1665, Intercepts
   treffen die Null (p = 0,93 / 0,98). Deskriptiv unterstes Preisdezil
   −0,0385, oberstes +0,0342.
2. **Der Bias schrumpft NICHT.** Differenz Closing minus Opening
   **−0,0024** (SE 0,0051, **t = −0,48**, p = 0,63), gestapelt geschätzt.
   Getrennt nach Gruppen ebenso wenig (Favoriten p = 0,37, Longshots
   p = 0,68). Auf der kontinuierlichen Achse liegt `lambda` über das ganze
   48-h-Fenster signifikant über 1, das punktweise Band überdeckt die 1 an
   keinem Gitterpunkt.
3. **Lernraten per GMM statt Bayes.** `fit_gmm_mod` schneidet nur über die
   Spalte `Bookies` zu, deshalb genügt das Überschreiben dieser Spalte mit
   dem Gruppenlabel — kein Umbau. Favoriten **0,00740**, Longshots
   **0,00098**, Differenz t = 7,44. Die Rangfolge des Papers hält also auch
   nach dem Exponenten-Fix.

**OFFEN – inhaltliche Textentscheidung, nicht getroffen:** Die Discussion
(tex Z. 914–917) deutet die Lernratendifferenz zwischen Favoriten und
Longshots als **Korrektur** des Favorite-Longshot-Bias. Diese Interpretation
ist nach Punkt 2 nicht mehr haltbar: der Bias schrumpft über das
Betting-Fenster nicht (1,1155 gegen 1,1131, t = −0,48). Findet keine
Korrektur statt, kann die höhere Lernrate der Favoriten sie auch nicht
bewirken. Die Passage muss **gestrichen oder neu begründet** werden. Ebenso
betroffen ist die Dezil-Gradienten-Aussage („stronger favorites tend to
exhibit higher learning rates", tex Z. 879 und 917): die GMM-Dezile zeigen
eine **Stufe** zwischen Favoriten und Longshots, keinen Gradienten — das
Maximum liegt bei Dezil 5 (0,00976), Dezil 6 bis 10 sind flach
(0,0056–0,0072).

**Einschränkungen, die in den Text gehören:** die Longshot-Lernrate ist für
sich nicht von null zu unterscheiden (t = 1,6); der J-Test verwirft in
**9 von 10** Dezilen, sobald über Bookmaker gepoolt wird (nach Bookmaker
geschnitten nur 1 von 24); die Bayesian-Werte im Paper sind bis zum
NUTS-Neulauf veraltet, die GMM-Zahlen sind Zwischenstand.

**Zuordnung der Gruppen unter Normalisierung:** `IsFav` ist **exakt
invariant** (0 Abweichungen von 182.941 Serien), weil
`filter_and_shape.py:74-88` die rohen Quoten beider Seiten vergleicht. Der
Dezil-Split ist es **nicht**: 92,43 % bleiben, 7,57 % verschieben sich um
genau ein Dezil, keine um zwei (Spearman 0,99922). Nicht als
Invarianzbeleg verwenden.

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

**Stand vor Revision:** Tabelle 6 (`res_wp_re`) regressiert Gewinnraten je
Preisänderungs-Bin auf die mittlere Preisänderung des Bins
(`winning_proportions.py:126`, Einheit = Bookmaker × Bin), ohne Kontrolle für
den Opening-Preis. Normalisiert: Intercept 0,504, AvgChange 0,821.

**Untersuchung:** Neue Spezifikation auf **Kontraktebene** (172.663
Kontrakte, 20.588 Matchups, 24 Bookmaker; `df_oc`, normalisiert, echte
Opening/Closing-Preise, keine Imputation), lineares Wahrscheinlichkeitsmodell
`Match = eta_0 + eta_1·OpnOdds + eta_2·DltOpnCls + TsDur + Compet_* +
(1 + DltOpnCls | Bookies)`, lme4, REML = FALSE.

| Stufe | eta_0 | eta_1 | eta_2 | R² |
|---|---:|---:|---:|---:|
| S1 nur Preisänderung | 0,510 | — | 0,833 | 0,0075 |
| S2 + OpnOdds | −0,062 | 1,125 | 0,957 | 0,1849 |
| S3 + Kovariaten | −0,050 | 1,125 | 0,956 | 0,1851 |
| S4 + Bookmaker-RE | −0,050 | 1,125 | 0,956 | 0,1851 |

- **Der Einwand trifft empirisch nicht zu:** eta_2 wird nach Kontrolle für den
  Opening-Preis **größer statt kleiner** (0,833 → 0,956) und bleibt
  cluster-robust hochsignifikant (t = 13,87). Die Preisbewegung trägt
  eigenständige Information; die Bin-Ergebnisse waren kein Niveaueffekt.
- **eta_1 = 1,125 liegt signifikant ÜBER 1** (cluster-robust t = 7,27 gegen 1,
  p = 3,5e−13) → Opening-Preise sind unterdispers, siehe R1-viii.
- **Der unintuitive Intercept ist aufgeklärt:** die ~0,5 entstehen nur ohne
  Baseline-Kontrolle (S1: 0,510). Mit `OpnOdds` im Modell liegt eta_0 bei
  −0,050, und in der Logit-Fassung trifft der Intercept den Effizienzwert 0
  exakt (0,00115, p = 0,83). Der Referee hat mit der Diagnose recht, auch wenn
  seine Vorhersage zu eta_2 nicht eintritt.
- **Logit-Robustheitscheck** (`glmer`, `Match ~ logit(OpnOdds) + DltOpnCls`):
  Steigung 1,184 (gegen 1: t = 24,88), Intercept 0,00115 (gegen 0: p = 0,83),
  DltOpnCls 4,421 (t = 43,69). Qualitativ identisch — der Befund hängt nicht
  an der Linearitätsannahme.
- **Match-RE ist hier NICHT identifiziert:** `Match` ist der Spielausgang und
  per Konstruktion konstant über die Bookmaker eines Matchups — **100,00 %**
  der Varianz between Matchup, 0 von 20.588 Matchups mit mehr als einem Wert
  (strenger als die 99,83 % bei der Unbiasedness-Regression). Die
  crossed-Variante treibt die Residualvarianz auf sd = 1e−6, ohne dass lme4
  eine Warnung meldet (`isSingular` prüft die RE-Kovarianz, nicht das
  Residuum). Inferenz daher **cluster-robust auf Matchup-Ebene**, Faktor
  2,96–4,11 gegenüber modellbasiert — dieselbe Größenordnung wie bei der
  Unbiasedness-Regression.
- **Filter-Sensitivität:** der Produktionsfilter `|RtrnOpnCls| > 0` entfernt
  11.752 Kontrakte (6,4 %). Auf der ungefilterten Stichprobe (184.415)
  verschiebt sich eta_2 um **0,00026**, eta_1 um −0,00215 — der Befund kann
  auf der vollen Stichprobe berichtet werden, was den Selektionseinwand
  („auf bewegte Preise selektiert") von vornherein erledigt.
- **Keine Bookmaker-Heterogenität**, RE und FE unabhängig übereinstimmend:
  siehe R2-M8 / R1-iv.

**Entscheidung:** Die Kontraktebenen-Spezifikation wird als neue Fassung von
Eq. 3 übernommen (LPM als Hauptspezifikation, Logit als Robustheitscheck,
cluster-robuste SEs statt Match-RE). Tabelle 6 bleibt als aggregierte
Darstellung erhalten, wird aber nicht mehr als Test gegen den Opening-Preis
gelesen.

**Umsetzung:** Analyse abgeschlossen, Paper-Text ausstehend.

**Beleg/Validierung:** `revision/snapshots/eq3_contract_level/` (Commit
`d4183ab`): `ladder.csv`, `match_anova.csv`, `cluster_robust.csv`,
`logit_check.csv`, `filter_sensitivity.csv`, `bookie_fe_slopes.csv`.
Übertragbarkeit des Sandwich verifiziert
(`max |beta(OLS) − beta(lmer)| = 0,000000`).

**Status:** Analyse abgeschlossen, Paper-Text ausstehend

**Superseded:** —

**Für Response-Dokument:** Wir werden Eq. 3 auf Kontraktebene neu schätzen und
den Opening-Preis wie vorgeschlagen als Baseline-Kovariate aufnehmen. Wir
werden zeigen, dass der Koeffizient auf die Preisänderung dabei **nicht**
verschwindet, sondern von 0,83 auf 0,96 steigt und cluster-robust
hochsignifikant bleibt — die Preisbewegung trägt also Information über den
Opening-Preis hinaus. Wir werden ergänzen, dass der vom Referee zu Recht als
unintuitiv bezeichnete Intercept von ~0,5 eine Folge der fehlenden
Baseline-Kontrolle war: mit Opening-Preis im Modell liegt er bei −0,05, und in
der Logit-Fassung exakt beim Effizienzwert null. Wir werden ferner darlegen,
dass der Koeffizient auf den Opening-Preis mit 1,125 signifikant über eins
liegt, was den Favorite-Longshot-Bias direkt sichtbar macht (siehe R1-viii).

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
**Untersuchung:** Von der Zeitachsen-Entscheidung mitbeantwortet (siehe
R2-C3, R1-vii): die kontinuierliche Spezifikation liefert einen glatten,
monotonen β₁-Pfad von 1,244 (24 h) über 0,938 (6 h) auf 0,759 (1 h) – also
Unterreaktion, Unverzerrtheit und Überreaktion als **Punkte auf einem
Kontinuum** statt als binäre Kategorien.
**Entscheidung:** [zu ergänzen: Formulierung im Text]
**Umsetzung:** Empirisch durch die kontinuierliche Fassung abgedeckt;
Paper-Text ausstehend.
**Beleg/Validierung:** `revision/snapshots/continuous_unbiasedness/`
**Status:** offen (empirisch abgedeckt, Textfassung ausstehend)
**Superseded:** —
**Für Response-Dokument:** [zu ergänzen — der Befund aus R2-C3/R1-vii trägt
diese Antwort bereits]

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

**Untersuchung:** Der vom Referee vorgeschlagene direktere Test ist genau die
Kontraktebenen-Spezifikation aus **R2-C1** — Realized Outcome auf
Opening-Preis **und** Revision, also bedingt auf das initiale
Probability-Level. Belege dort.

Der Benchmark lässt sich zudem als **testbare Restriktion** schreiben. Unter
`Opening = p + e1 + e2`, `Closing = p + e2` mit `e1` unabhängig von `p` ist
`Closing` die bessere Prognose, und da
`Closing = Opening + DltOpnCls` gilt:

```
E[Match | Opening, DltOpnCls] = lambda * Closing
                              = lambda * Opening + lambda * DltOpnCls
```

Reine Rauschreduktion impliziert also **eta_1 = eta_2 = lambda** (Reliabilität
des Closing-Preises) — **nicht** eta_2 = 0. Das präzisiert die
Referee-Intuition: die Frage ist nicht, ob die Revision überhaupt vorhersagt,
sondern ob sie **genauso stark** vorhersagt wie der Opening-Preis.

Ergebnis (cluster-robust auf Matchup-Ebene, n = 172.663, G = 20.588):

| Restriktion | Wert | Test |
|---|---:|---|
| `eta_1 − eta_2` | +0,16838 (SE 0,07163) | t = 2,35, **p = 0,019** |
| `eta_1 = eta_2 = 1` gemeinsam | — | chi2(2) = 53,04, **p = 3,0e−12** |

- **Die Gleichheitsrestriktion wird nur knapp verworfen** (p = 0,019, auf
  1 %-Niveau nicht). Die Daten liegen also **nahe** am reinen
  Rauschreduktions-Benchmark — die Revision sagt fast genauso stark vorher wie
  der Opening-Preis selbst.
- **Die stärkere Fassung `eta_1 = eta_2 = 1`** (Closing als hinreichende
  Statistik ohne Shrinkage) wird dagegen klar verworfen, und zwar getrieben
  von `eta_1 = 1,125 > 1`, nicht von einer Abweichung zwischen den beiden
  Koeffizienten. Die Abweichung vom Benchmark ist damit **ein
  Kalibrierungsproblem des Opening-Preises (Favorite-Longshot, R1-viii), kein
  Sortierungsartefakt**.
- Damit ist die im Kommentar vermutete „Sortierung nach zugrundeliegender
  Wahrscheinlichkeit" empirisch lokalisiert: sie sitzt im Niveau
  (`eta_1 > 1`), nicht im Revisionskanal.

**Entscheidung:** [zu ergänzen: ob der Benchmark-Test als eigene Passage in
den Text geht oder als Fußnote zu Eq. 3]

**Umsetzung:** Analyse abgeschlossen, Paper-Text ausstehend.

**Beleg/Validierung:** `revision/snapshots/eq3_contract_level/` (Commit
`d4183ab`). Der Benchmark-Test selbst ist eine Nebenrechnung auf demselben
Frame und derselben Cluster-Kovarianz; er liegt **nicht** als eigene CSV vor.

**Status:** Analyse abgeschlossen, Paper-Text ausstehend

**Superseded:** —

**Für Response-Dokument:** Wir werden den vom Referee vorgeschlagenen
direkteren Test durchführen — Realized Outcomes auf Opening-Preis und
Revision gemeinsam — und den Benchmark als testbare Restriktion formulieren:
reine Rauschreduktion impliziert gleiche Koeffizienten auf beiden Größen, nicht
einen Nullkoeffizienten auf der Revision. Wir werden zeigen, dass diese
Gleichheit nur knapp verworfen wird (p = 0,019), die Daten also nahe am
Benchmark liegen, und dass die verbleibende Abweichung von der Kalibrierung
des Opening-Preises herrührt (Koeffizient 1,125 statt 1) und nicht vom
Revisionskanal.

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
**Stand vor Revision:** `tex:687` schreibt „all bookmakers show similar
prediction accuracy based on opening prices, with RMSE values clustering
around 0.45. These values suggest that the bookmakers' models make fairly
accurate predictions." Kein Bezugspunkt, gegen den 0,45 einzuordnen wäre. Der
auskommentierte Absatz darunter (`tex:689`) enthielt den Münzwurf-Vergleich,
steht aber nicht im Text. Figure 1 zeigt ausschließlich den RMSE.

**Untersuchung:** Drei Bezugspunkte gerechnet (`df_oc`, normalisiert;
Serienebene ungefiltert als Sensitivität):

| | Opening | Closing |
|---|---:|---:|
| Brier / RMSE | 0,20664 / **0,4546** | 0,20425 / 0,4519 |
| uninformiert (p ≡ 0,5) | 0,25 / 0,5 | 0,25 / 0,5 |
| **Brier Skill Score** | **0,1734** | **0,1830** |
| erreichbare Grenze E[p(1−p)] | 0,21487 (RMSE 0,4634) | 0,21277 (0,4613) |

Auf der Serienebene ohne Filter — der Stichprobe, auf der die Abbildung
rechnet — liegt die Grenze bei **RMSE 0,4630**.

- **Murphy-Zerlegung** (20 Quantilsbins, Opening): REL 0,00052,
  RES 0,04348, UNC 0,24990. Die Fehlkalibrierung macht **0,25 % des
  Brier-Scores** aus und scheidet als Erklärung der 0,4546 aus; die Preise
  lösen **17,4 % der Ergebnisunsicherheit** auf (Closing 18,4 %). Der Rest
  ist irreduzible Unsicherheit des Tennisergebnisses, keine Modellschwäche.
  Der Within-Bin-Rest der Zerlegung wird in `murphy.csv` mitgeführt und
  schrumpft erwartungsgemäß mit feineren Bins (−0,0010 bei k = 10 →
  −0,0001 bei k = 50).
- **Der beobachtete Brier liegt signifikant UNTER der Grenze**
  (−0,00823, SE 0,00121 cluster-robust auf Matchup, **t = −6,78**). Exakt
  testbar ohne Binnung, weil für binäres y algebraisch gilt
  `(y − p)² − p(1 − p) = (y − p)(1 − 2p)`; der Abstand ist damit der
  Mittelwert einer gewöhnlichen Beobachtungsgröße.
- **Das ist derselbe Befund wie `eta_1` = 1,125 aus R2-C1**, nur in einer
  anderen Metrik. E[p(1−p)] ist die Grenze eines perfekt kalibrierten
  Prognostikers *mit dieser Preisverteilung*; sind die Preise unterdispers,
  ist die Grenze zu hoch angesetzt und wird unterboten. Gegenprobe: die
  Kalibrierungssteigung beträgt 1,1170 auf Kontraktebene (1,1165 über 20
  Bins). **Der Favorite-Longshot-Bias ist groß genug, um in der
  aggregierten Prognosegüte sichtbar zu werden** — verwertbar für R1-viii.
- **Textkorrektur nötig:** „clustering around 0.45" trifft nicht zu. Die
  publizierten Werte reichen von **0,4519 (Vulkan Bet) bis 0,4719
  (Pinnacle)**; auf der Serienebene von 0,4465 bis 0,4646. Das galt
  **bereits für die publizierte Fassung** — die Normalisierung verschiebt
  die Werte um maximal 0,00244 (Interwetten) und ist nicht die Ursache.
- **Posting Time:** die Mediane streuen von 16,57 h (Dafabet) bis 36,03 h
  (Betfair) vor Anpfiff, Faktor 2,17. Die inhaltliche Auswertung dazu steht
  unter **R3-2**, mit dem dieser Punkt zusammenfällt.

**Entscheidung:** Figure 1 wird durch **zwei getrennte Abbildungen** ersetzt,
beide auf Serienebene: (A) gruppierte Balken je Bookmaker, RMSE auf der
linken und medianer Posting-Zeitpunkt auf der rechten y-Achse; (B) Scatter
RMSE gegen Posting-Zeitpunkt über die 24 Bookmaker mit Regressionsgerade,
Korrelationen und Bookmaker-Annotation an jedem Punkt.

**Die Grenze E[p(1−p)] wird in der Abbildung NICHT gezeigt.** Sie steht als
Einordnung für den Papertext zur Verfügung. Grund: eine Referenzlinie, die von
zwei Dritteln der Balken unterschritten wird, ist ohne die Erklärung
„unterdisperse Preise senken die Grenze" irreführend, und diese Erklärung
gehört in den Text, nicht in eine Bildunterschrift.

**Umsetzung:** Analyse abgeschlossen, Papertext ausstehend.

**Beleg/Validierung:** `revision/snapshots/rmse_baselines/`: `baselines.csv`
(Brier, RMSE, BSS, Grenze, cluster-robuster Test des Abstands),
`murphy.csv`, `calibration_slopes.csv`, `opening_vs_closing.csv`,
`rmse_by_bookie_check.csv` (Figure-1-Größe, Serienebene und publizierter Wert
je Bookmaker). Abbildungen aus `_fig_bars.py` und `_fig_scatter.py`.

**Status:** Analyse abgeschlossen, Papertext ausstehend

**Superseded:** —

**Für Response-Dokument:** Wir werden dem Referee zustimmen und den RMSE
einordnen, statt ihn unkommentiert stehen zu lassen. Wir werden die
uninformierte Prognose als oberen Bezugspunkt nennen (Brier 0,25 / RMSE 0,5)
und daraus den Brier Skill Score von 0,173 berichten, und wir werden über die
Murphy-Zerlegung zeigen, dass die verbleibende Fehlerhöhe fast vollständig aus
der irreduziblen Unsicherheit des Spielausgangs stammt und nur zu 0,25 % aus
Fehlkalibrierung. Wir werden ergänzen, dass der beobachtete Brier-Score sogar
unter der bei perfekter Kalibrierung erreichbaren Grenze liegt, und erläutern,
dass dies kein Widerspruch ist, sondern die Kehrseite der unterdispersen
Preise, die wir unter R1-viii und R2-C1 dokumentieren. Wir werden die Formel
„clustering around 0.45" korrigieren und die tatsächliche Spanne angeben. Wir
werden Figure 1 zudem um den medianen Posting-Zeitpunkt je Bookmaker
erweitern, wie vom Referee vorgeschlagen; die inhaltliche Auswertung dieser
Größe berichten wir zusammen mit R3-2.

## R2-M8 – Table 7: Rauschen vs. systematischer Unterschied
**Kommentar (kondensiert):** Zu Table 7 (Forecast-Error-Varianz-Unterschiede
zwischen Bookmakern, z. B. 10Bet) mehr Intuition gewünscht: Rauschen durch
Stichprobengröße oder systematisch? Fokus eher auf Aggregatergebnisse?
**Stand vor Revision:** [zu ergänzen]

**Untersuchung:** Querverweis auf **R2-C1**. Für die Preisinformativität
lautet die Antwort auf die Frage des Referees eindeutig **„Rauschen"**: in der
Kontraktebenen-Fassung von Eq. 3 gibt es **keine** Bookmaker-Heterogenität
(Belege `revision/snapshots/eq3_contract_level/`, Commit `d4183ab`).

- Random Effects exakt null (`boundary (singular) fit`).
- Fixed Effects mit Dummies **und** Interaktionen: R²-Zuwachs 0,0001 für 46
  Parameter; cluster-robust Niveau chi2(23) = 31,48 (p = 0,111), Steigung
  chi2(23) = 20,78 (p = 0,595), gemeinsam chi2(46) = 52,91 (p = 0,225).
- Nominelle Spreizung der Steigungen 0,771–1,083 (sd 0,085), aber **0 von 23**
  Kontrasten einzeln signifikant; SEs 0,08–0,20.

**Das ist der belastbare Fall für „Fokus auf Aggregatergebnisse"**, den der
Referee anregt — und zwar mit einem Test statt einer Vermutung: die
nominellen Unterschiede zwischen Bookmakern verschwinden, sobald man sie
formal prüft.

**Wichtige Abgrenzung:** das gilt für die **Preisinformativität**, nicht
generell. Bei den **Lernraten** ist die Heterogenität substanziell und robust
(γ 0,0014–0,0124, Faktor 9, stabile Rangfolge). Die Antwort auf R2-M8 ist also
größenabhängig und sollte nicht pauschal als „alles nur Rauschen" formuliert
werden.

*Offen:* Table 7 selbst (Forecast-Error-Varianz) ist damit **nicht** direkt
getestet — die Aussage betrifft die Steigung in Eq. 3, nicht die RMSE-Streuung.
Ein analoger Test auf Table 7 steht aus.
**[erledigt, siehe Nachtrag 2026-08-08]**

**Nachtrag 2026-08-08 – die Antwort ist gleichungsabhängig.** Beleg:
`revision/snapshots/cluster_inference_eq12/bookie_wald.csv`. Derselbe Test
wie bei Eq. 3 (Bookmaker-Dummies **und** Interaktionen, gemeinsamer
Wald-Test, cluster-robust auf Matchup) jetzt auch für Eq. 1 und Eq. 2:

| Test | Eq. 1 (`resp_to_info`) | **Eq. 2 (`ags_test`, trägt Tabelle 7)** | Eq. 3 |
|---|---|---|---|
| Interaktionen (Steigung) | chi2(23) = 24,46, p = 0,379 | chi2(23) = **304,15**, p < 0,0001 | chi2(23) = 20,78, p = 0,595 |
| Dummies (Niveau) | chi2(23) = 34,34, p = 0,060 | chi2(23) = **151,91**, p < 0,0001 | chi2(23) = 31,48, p = 0,111 |
| beide gemeinsam | chi2(46) = 57,08, p = 0,127 | chi2(46) = **507,72**, p < 0,0001 | chi2(46) = 52,91, p = 0,225 |
| R² ohne → mit | 0,000419 → 0,000591 | 0,006504 → 0,008405 | 0,185114 → 0,185216 |

**Die pauschale Formulierung „Fokus auf Aggregatergebnisse" gilt NICHT für
Tabelle 7.** Genauer:

- **Preisinformativität (Eq. 3) und Vorhersagbarkeit der close-to-end-Renditen
  (Eq. 1): Rauschen.** Bei Eq. 1 ist die nominelle Steigungsstreuung mit
  −0,113 bis +0,379 (sd 0,115) sogar groß, aber das Basis-R² beträgt 0,0004
  — das Modell erklärt praktisch nichts, und der gemeinsame Test findet
  nichts.
- **Relative Prognosegenauigkeit (Eq. 2, die Grundlage von Tabelle 7):
  systematisch.** Der Test ist hoch signifikant, die Steigungen streuen von
  −0,0066 bis −0,0004 (sd 0,0018). Die bookmakerspezifischen Angaben in
  Tabelle 7 sind damit **belegt**, nicht bloß deskriptiv.

Das ist zugleich die Begründung für die zweifache Clusterung bei Eq. 2
(siehe R1-ii, Nachtrag 2026-08-08): weil die Bookmaker-Heterogenität dort
real ist, darf die Inferenz sie nicht wegfallen lassen.

**Entscheidung:** [zu ergänzen]

**Umsetzung:** [zu ergänzen]

**Beleg/Validierung:**
`revision/snapshots/eq3_contract_level/bookie_fe_slopes.csv`,
`revision/snapshots/cluster_inference_eq12/bookie_wald.csv` und
`Eq{1,2}_*_bookie_fe_slopes.csv`

**Status:** Analyse abgeschlossen, Papertext ausstehend (Test jetzt für alle
drei Gleichungen gerechnet; Befund ist gleichungsabhängig)

**Superseded:** die frühere Lesart, „Fokus auf Aggregatergebnisse" gelte
generell — sie gilt für Eq. 1 und Eq. 3, **nicht** für Tabelle 7 (Eq. 2).

**Für Response-Dokument:** Wir werden die Frage des Referees getrennt nach
Größe beantworten, weil die Antwort unterschiedlich ausfällt. Für die
Preisinformativität (Eq. 3) und für die Vorhersagbarkeit der
close-to-end-Renditen (Eq. 1) werden wir zeigen, dass die nominellen
Unterschiede zwischen Bookmakern einem gemeinsamen Test nicht standhalten —
weder über Random noch über Fixed Effects — und die Darstellung dort auf die
Aggregatergebnisse konzentrieren. Für die relative Prognosegenauigkeit, also
genau die in Tabelle 7 berichteten Größen, werden wir dagegen belegen, dass
die Unterschiede **systematisch** sind und einem cluster-robusten Wald-Test
über alle 46 Kontraste deutlich standhalten; die bookmakerspezifischen
Angaben in Tabelle 7 bleiben damit als eigenständiger Befund stehen. Wir
werden ferner abgrenzen, dass dasselbe für die Lernraten gilt, wo die
Heterogenität substanziell und über Spezifikationen stabil ist.

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
