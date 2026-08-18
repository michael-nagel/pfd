# Was bei einer Umstellung auf V2|B nachzuziehen wäre

Bestandsaufnahme, **keine Umsetzung**. V2 = Zeitraster je Serie (eigenes
Opening bis eigener Schlusspreis), B = Stützstellen 50/45/40/35/30 statt
46/41/36/31/26.

> **Vorbemerkung, unabhängig von der Entscheidung:** `reports/values/values.dat`
> ist bereits veraltet. Dort steht `avg_gamma_gmm = 0.0332`, also der Stand
> **vor** dem Zerfallsexponenten-Fix (`d8d26bc`); der heutige Code liefert
> 0,0054. Ein Neulauf der Wertedatei ist ohnehin fällig.

## 1. Code — die Umstellung selbst

| Datei | Zeile | Änderung |
|---|---|---|
| `models/resample_and_impute.py` | 90–91 | `groupby("Matchup")` → `groupby("GroupId")` |
| `utils/_create_gmm_data.py` | 52–53 | `range(1,6)` / `n_per - i*incr` → `range(0,5)` / `n_per - 1 - i*incr`; TODO-Marker auflösen |
| `utils/_gen_meth_mom.py` | 53 | `tau = [n_per - i*incr + 1]` → `[n_per - (i-1)*incr]`, also [51, 46, 41] |

**Ersatzlos zu entfernen**, weil die Imputationsmasse auf null fällt:

| Datei | Zeile | Was |
|---|---|---|
| `resample_and_impute.py` | 128–129 | `frac_missings` |
| | 164–184 | `calc_imput_loss`-Schleife (`n_mvt` würde 0) |
| | 186–214 | Abbildung `imput_loss.pdf` |
| | 217 | `impute_missings`-Aufruf |
| `run_estimation.py` | 203 | `frac_missings` in `values.dat` |

Ungenutzt werden damit `helpers/impute_missings.py` und
`utils/calc_imput_loss.py`.

**Nicht betroffen:** `TsDur` ist in `filter_and_shape.py:101` bereits je
`GroupId` gebildet; der Filter `[12, 72]` und die Kovariate bleiben.

## 2. `\var{}`-Werte

Alle über `estimate_gmm_learning_rate` und `estimate_bayesian_learning_rate`
erzeugten Werte ändern sich.

| Wert | aktuell | Papierzeile | Quelle |
|---|---|---|---|
| `avg_gamma_gmm` | 0,0332 | 820 | GMM |
| `min_gamma_gmm` | 0,0029 | 820 | GMM |
| `max_gamma_gmm` | 0,0741 | 820 | GMM |
| `idxmin_gamma_gmm` | GGBET | 820 | GMM |
| `idxmax_gamma_gmm` | Dafabet | 820 | GMM |
| `corr_gamma_loss` | −0,2414 | 845 | GMM × RMSE |
| `gamma_med_nuts` | 0,0494 | 841 | Bayesian |
| `gamma_lower_nuts` | 0,0324 | 841 | Bayesian |
| `gamma_upper_nuts` | 0,0624 | 841 | Bayesian |
| `gamma_fav` | 0,0608 | 858 | Bayesian |
| `gamma_udd` | 0,0215 | 858 | Bayesian |
| `gamma_pro` | 0,0389 | 881 | Bayesian |
| `gamma_amat` | 0,0354 | 881 | Bayesian |
| `frac_missings` | 0,0784 | – | **entfällt ganz** |

`idxmin`/`idxmax` sind besonders heikel: die Extremwerte wandern
(`argmin` GGBET → Pinnacle, `argmax` Dafabet → 10Bet).

## 3. Tabellen

| Tabelle | betroffen? | Grund |
|---|---|---|
| `res_pm_mod.tex` (Bayesian) | **ja** | läuft auf dem Wide-Frame |
| `res_garch.tex` (ADF/GARCH) | **ja** | läuft auf dem Wide-Frame |
| `res_gpm.tex` (Tab. 3, Eq. 1) | nein | `df_oc`, vor dem Resampling |
| `res_rfa.tex` (Tab. 4, Eq. 2) | nein | Opening/Closing-Querschnitt |
| `res_rfa_tot.tex` (Tab. 7) | nein | dito |
| `res_wp.tex` / `res_wp_re.tex` (Tab. 5/6) | nein | `df_oc`; Eq. 3 wird ohnehin auf Kontraktebene ersetzt (R2-C1) |

## 4. Abbildungen

| Abbildung | Status |
|---|---|
| `gmm_params.pdf` (`fig:gmm_params`) | neu zu rechnen |
| `post_gamma_tot.pdf` | neu (Bayesian) |
| `post_gamma_nuts_fav_udd.pdf` | neu (Bayesian) |
| `post_gamma_nuts_ivals.pdf` | neu (Bayesian) — Dezile werden auf `OddsMvt0` gebildet, das unter V2 der **echte** Opening-Preis ist statt eines imputierten |
| `post_gamma_nuts_pro_amat.pdf` | neu (Bayesian) |
| `imput_loss.pdf` | **entfällt** |
| Fig. 3 (β₁-Pfad) | wird ohnehin durch die kontinuierliche Fassung ersetzt (R1-vii / R2-C3) |
| Fig. 6 (Lernrate vs. RMSE) | wird ohnehin entfernt (R2-M10) |
| `fig:win_props_re` | wird ohnehin ersetzt (R2-C6) |

## 5. Bereits geschriebene Antworten

| Stelle | Was dort steht | Handlungsbedarf |
|---|---|---|
| **R1-iv**, Z. 208 + Tab. `tab:r1c4b` Z. 244 | „average learning rate moves from 0.0054 to 0.0057" beim Ausschluss von Pinnacle/BetInAsia | **beide Zahlen neu**; die Sharp/Soft-Robustheitsprüfung ist komplett neu zu rechnen |
| **R1-vi**, Z. 316 | „support points lie in the closing half of the window and never touch the stretch that a truncated series leaves unobserved" | prüfen: unter B ist die letzte Stützstelle der Schlusspreis selbst |
| **R1-vi**, Z. 318–319 | Abstands-Argument („spacing them as Biais et al. do") mit der `incr`-Invarianztabelle | Tabelle unter der neuen Spezifikation neu rechnen |
| **R1-vi**, Z. 320–321 | „because the match outcome is observed here, that error is zero by construction, we set K = 0" | **sachlich falsch, unabhängig von der Umstellung.** Der Bodensatz `E[q(1−q)] ≈ 0,21` macht praktisch die ganze gemessene Größe aus (siehe `../gmm_rasterfree/`). Muss so oder so umgeschrieben werden |
| **R1-viii**, Z. 391 | „favorites at 0.0074 against 0.0010 for longshots (t = 7.44)" | wird zu **0,0055 / 0,0012, t = 4,49** — Aussage bleibt, Zahlen ändern sich |
| **R2-C2** (neu) | zitiert 0,0054 → 0,0035 und 0,0055/0,0012 | mit Vorbehalt formuliert; nach dem Produktionslauf gegenprüfen |
| **R2-C8**, Z. 514 | Entwurf zur Interpretation der Lernraten-Größenordnung | Zahlenbeispiele prüfen |

**Nicht betroffen:** die Wald-Tests `p = 0,379` (Eq. 1) und `p = 0,595`
(Eq. 3) in R1-iv — die stammen aus den Querschnittsgleichungen, nicht aus dem
GMM.

## 6. Bayesian — ja, betroffen, und der teuerste Posten

`bayesian_estimation.py` bekommt den Wide-Frame und `n_per` übergeben und
bildet die Preisdezile auf `OddsMvt0` (Z. 70–74). Unter V2 ist `OddsMvt0` der
**echte** eigene Opening-Preis statt eines zu 86 % imputierten Werts — die
Dezilgrenzen selbst verschieben sich also, nicht nur die Schätzung darauf.

Fünf NUTS-Läufe sind fällig: `tot`, `fav`, `udd`, `pro`, `amat`, dazu die
Dezil-Reihe für `post_gamma_nuts_ivals`. Bei `n_chains = 4`,
`n_draws = 5000`, `n_tune = 2000` auf 6 Kernen ist das der bestimmende
Zeitfaktor des gesamten Neulaufs.

*Hinweis:* Der Bayesian-Lauf steht ohnehin aus (er ist seit der
Normalisierung nicht neu gerechnet worden). Die Umstellung würde ihn nicht
zusätzlich verursachen, sondern nur seinen Inhalt ändern.

## 7. Diagnostik-Snapshots, die ihren Gegenstand verlieren

- `gmm_imputation_test/` — der ganze Masking-Test wird gegenstandslos, weil
  es keine Imputation mehr gibt. Als Beleg dafür, dass die Imputation γ
  **nicht** bewegt hat, bleibt er inhaltlich wertvoll.
- `E_gmm_exponent_fix/` — Referenzwerte wären neu zu erzeugen.
- `eq_window_scope/`, `gmm_rasterfree/` — beschreiben genau den Übergang und
  bleiben als Begründung stehen.

## 8. Reihenfolge, falls umgestellt wird

1. Code-Änderungen (Abschnitt 1), Imputationsblöcke entfernen.
2. Frequentistischen Teil neu rechnen, `values.dat` und `gmm_params.pdf`
   gegen `eq_window_scope/support_shift_gamma.csv` (Spalte V2|B) prüfen —
   erwartet: γ̄ = 0,003474.
3. Erst danach die fünf NUTS-Läufe, damit der teure Schritt nicht auf einem
   noch wackligen Frame läuft.
4. Zuletzt die Antworten aus Abschnitt 5 nachziehen und den Papertext
   (§3.5 K-Annahme und Stützstellendefinition, §4/Anhang B Imputation,
   §5.5 Lernraten).
