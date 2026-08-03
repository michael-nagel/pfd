# Stage E_gmm_exponent_fix

`C_normalized` mit korrigiertem Zerfallsexponenten im GMM. Alles andere ist
**per Konstruktion** identisch zu `C_normalized` — Begründung unten.

## Was geändert wurde

`src/pfd/utils/_gen_meth_mom.py`, `momcond`: der Zerfallsfaktor wird aus den
**tatsächlichen Positionen der verwendeten Stützstellen** gebildet statt fest
aus `n_per`.

```python
# vorher
mom_cond_1 = (exog[:,0] - endog)**2 - (((n_per-1)/n_per)**(2*param)) * (exog[:,1] - endog)**2
mom_cond_2 = (exog[:,1] - endog)**2 - (((n_per-2)/(n_per-1))**(2*param)) * (exog[:,2] - endog)**2

# nachher
tau = [n_per - i * incr + 1 for i in (1, 2, 3)]     # 1-basiert: OddsMvt0 = 1. Timestamp
mom_cond_1 = (exog[:,0] - endog)**2 - ((tau[1]/tau[0])**(2*param)) * (exog[:,1] - endog)**2
mom_cond_2 = (exog[:,1] - endog)**2 - ((tau[2]/tau[1])**(2*param)) * (exog[:,2] - endog)**2
```

`src/pfd/helpers/fit_gmm_mod.py` reicht dafür `incr` an den Schätzer durch.

**Rückwärtskompatibel:** bei `incr = 1` ist `tau = [51, 50, 49]`, also
`tau[1]/tau[0] = 50/51 = (n_per−1)/n_per` und `tau[2]/tau[1] = 49/50 =
(n_per−2)/(n_per−1)` — bitgenau die alte Formel (numerisch verifiziert,
Differenz 0). Der Fix ist eine Verallgemeinerung, keine Ersetzung.

Bei `incr = 5` (dem konfigurierten Wert) ist `tau = [47, 42, 37]`, der Faktor
also 42/47 = 0,8936 statt 50/51 = 0,9804.

## Warum die übrigen Artefakte identisch sind

Der Exponent steht **ausschließlich** in `_GenMethMom.momcond`. Daraus folgt:

1. **`_create_gmm_data` ist unberührt** — die Spaltenauswahl
   (`OddsMvt{n_per − i·incr}`) und die sieben Instrumente hängen an `n_per`
   und `incr`, nicht am Exponenten. Endog/Exog/Instrumente sind byte-identisch.
2. **Das GMM ist der letzte frequentistische Schritt.** In
   `run_estimation.py` läuft `estimate_gmm_learning_rate` nach
   filter/accuracy/winprops/resample/GARCH/unbiasedness; keiner dieser
   Schritte liest ein GMM-Ergebnis. Es gibt **keine Rückkopplung** in
   vorgelagerte Schritte.
3. **Die Ausgänge des GMM sind abzählbar**: die fünf Werte
   `avg_gamma_gmm`, `min_gamma_gmm`, `max_gamma_gmm`, `idxmin_gamma_gmm`,
   `idxmax_gamma_gmm`, die Datei `gmm_by_bookie.csv` (plus
   `..._first_stage.csv`) und drei Abbildungen (`gmm_params.pdf`,
   `gmm_jstat.pdf`, `gmm_pvalue.pdf`). Sonst nichts.
4. **`corr_gamma_loss` hängt nicht am GMM**, sondern an
   `metrics["Learning Rate"]` aus dem Bayesian-Block
   (`run_estimation.py:213`) — der hier ohnehin nicht läuft.

Ein voller Pipeline-Lauf hätte daher dieselben Dateien erzeugt. Er wurde nicht
durchgeführt, weil er ~19 min für eine beweisbar auf fünf Zahlen begrenzte
Änderung gekostet hätte und der gestufte Runner früherer Sessions nicht mehr
im Repo liegt.

## Herkunft der Dateien

| Datei | Herkunft |
|---|---|
| `gmm_by_bookie.csv` | **neu gerechnet** (CUE, Startwert 0,01, `maxiter="cue"`) |
| `gmm_by_bookie_first_stage.csv` | **neu gerechnet** (First Stage, `maxiter=1`) |
| `values.csv` | aus `C_normalized`, **fünf GMM-Keys ersetzt** |
| `beta1_curve.csv` | Kopie aus `C_normalized` |
| `rmse_by_bookie.csv` | Kopie aus `C_normalized` |
| `signific_time_idx.csv` | Kopie aus `C_normalized` |
| `checkpoint.json` | Kopie aus `C_normalized` |
| `tables/`, `values/` | Kopie aus `C_normalized` |

Datenbasis: `C_normalized/wide_imputed.h5` (normalisiert, Match-Fix), 24
Bookmaker, `n_per = 51`, `incr = 5`.

**Nicht enthalten:** `wide_imputed.h5` (unverändert, liegt in `C_normalized`)
und die drei GMM-Abbildungen (gitignoriert, aus `gmm_by_bookie.csv`
regenerierbar).

## Effekt

| Kennzahl | C_normalized | E_gmm_exponent_fix |
|---|---:|---:|
| `avg_gamma_gmm` | 0,0320 | **0,0054** |
| `min_gamma_gmm` | 0,0042 | 0,0014 |
| `max_gamma_gmm` | 0,0720 | 0,0124 |
| `idxmin_gamma_gmm` | GGBET | GGBET |
| `idxmax_gamma_gmm` | Dafabet | Dafabet |

γ fällt um Faktor ≈ 5,9. Unverändert bleiben Argmin/Argmax (und damit die
beiden Namen im Papersatz `oup-authoring-template2.tex:820`), das
Signifikanzmuster (15 → 16 von 24 mit |t| > 1,96) und die J-Test-Verwerfungen
(1/24, Interwetten). Die Rangfolge über Bookmaker bleibt weitgehend erhalten
(Spearman 0,884), mit drei materiellen Ausreißern in der Feldmitte — am
stärksten Lasbet (Rang 5 → 19).

Hintergrund und Belege: `references/specs/open_questions.md`, Abschnitt
„GMM Exponent (incr/n_per)".
