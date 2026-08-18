# RUN_SPEC — Neulauf JRSSA-Mar-2026-0082

Verbindliche Spezifikation für den nächsten vollständigen Schätzlauf.
Branch `revision-jrssa`. Diese Datei beschreibt den **Sollzustand des Laufs**,
nicht seine Geschichte. Entscheidungsgeschichte steht in
`revision/revision_log.md`, technische Befunde in
`references/specs/open_questions.md`.

Lesart je Eintrag: **entschieden** = eine Belegstelle trägt die Entscheidung;
**VERIFIZIEREN** = vor dem Lauf festzustellen, nicht zu entscheiden;
**nicht belegbar** = keine Belegstelle vorhanden, nicht geschätzt.

Stand des Codes bei Abfassung: HEAD `9772498`, Tag `pre-cleanup-20260818`,
`git status src/` sauber. Mehrere der unten gesetzten Punkte sind durch
Commit `1a2923c` („Anchor the percentile grid per series and use the full
support range") **bereits implementiert** und nur noch zu verifizieren.

---

## 0. Übergeordnete Vorgabe — Pipeline-Umfang

**Papertext UND Antwortdokument werden vollständig aus der Code-Pipeline
gespeist.** Keine Zahl, keine Tabelle und keine Abbildung darf nach dem
Umbau aus einem Snapshot-Skript oder einem vorgehaltenen Zwischenframe
stammen. **Keine Referenzklasse**: eingefrorene Vorher-Zahlen aus
`revision/snapshots/` tragen nach dem Umbau keine Aussage mehr.

**Einzige Ausnahme:** `data/processed/shaped_data.h5` (25.11.2024) bleibt
Eingang, weil der Scrape nicht wiederholbar ist. Nachgeordnet gilt dasselbe
für `data/raw/crawled_odds.json`, aus dem `shaped_data.h5` stammt und das
als einziges den Scrape-Zeitstempel trägt (Abschnitt 8).

### Inventar A1–A21

| # | Analyse | Zielmodul in `src/pfd` | Phase | Status |
|---|---|---|---|---|
| A1 | Marge/Overround, Preisniveau, Table-5-Bins, RMSE-Rangfolge (`tab:r1c1`) | `models/filter_and_shape.py:118`; `models/bookmaker_accuracy.py:62-93`; `models/winning_proportions.py:72-123` | `pre` | **neu zu spezifizieren** (Abschnitt 7) |
| A2 | Cluster-Inferenz Eq. 1/Eq. 2, Varianzzerlegung, Wald-Tests (`tab:r1c2`) | `models/bookmaker_accuracy.py` | `pre` | überführen (Neufassung, rpy2/lme4) |
| A3 | Cluster-Faktor der **diskreten** Unbiasedness, 2,1 (`tab:r1c2`, Zeile „Unbiasedness (Fig. 3)") | — | — | **entfällt** (Abschnitt 6) |
| A4 | Margen je Bookmaker (`tab:r1c4`) | `models/filter_and_shape.py:118` → `models/bookmaker_accuracy.py` | `pre` | überführen (Neufassung) |
| A5a | γ ohne Pinnacle/BetInAsia (`tab:r1c4b`) | `models/gmm_estimation.py:84` | `gmm` | überführen, **Referenz wechselt** von `E_gmm_exponent_fix/gmm_by_bookie.csv` (V1\|A) auf das Produktionsergebnis |
| A5b | β₁ ohne Pinnacle/BetInAsia (`tab:r1c4b`) | `models/unbiasedness_regressions.py` | `pre` | überführen (Neufassung, rpy2/splines) |
| A6 | Zensierung: Stichprobenkette, included vs. excluded (`tab:r1c5`) | `models/filter_and_shape.py` | `pre` | überführen (Neufassung) |
| A7 | Zensierung: β₁ mit/ohne Filter, Schwellenleiter (`tab:r1c5b`) | `models/unbiasedness_regressions.py` | `pre` | überführen (Neufassung) |
| A8 | Kontinuierliche Unbiasedness, `ns(df=4)`, Bootstrap B = 100, sup-t (`fig:r1c7new`, `tab:r1c7`) | `models/unbiasedness_regressions.py` | `pre` (**nicht** `post`) | überführen (Neufassung, rpy2/lme4) |
| A9 | RMSE-Bins der unteren Tafel (`fig:r1c7new`) | dasselbe Modul | `pre` | überführen; **V1-Anteil `rmse_real_vs_imputed.csv` entfällt** |
| A10 | Gepaarter Brier erster/letzter beobachteter Preis (`reply:342`) | dasselbe Modul | `pre` | überführen |
| A11 | Benachbarte Änderungen der publizierten β₁-Kurve, \|z\| ≤ 0,92 (`reply:333`) | — | — | **entfällt** (Abschnitt 6) |
| A12 | FLB-Kalibrierung Opening/Closing (`tab:r1c8`) | `models/bookmaker_accuracy.py` bzw. FLB-Modul | `pre` | überführen (Neufassung, rpy2) |
| A13 | FLB-Kalibrierung über die Zeit, λ(X) (`fig:r1c8`) | dasselbe Modul | `pre` | überführen (Neufassung, rpy2/splines) |
| A14 | FLB nach Dezilen, 3,9 / 3,4 pp (`reply:382`) | dasselbe Modul | `pre` | überführen |
| A15 | Eq. 3 Kontraktebene, Leiter S1–S4, Logit (`tab:r2c1`) | `models/winning_proportions.py` | `pre` | überführen (Neufassung, rpy2/lme4) |
| A16 | γ̄ unter V2\|B (`reply:484`) | `models/gmm_estimation.py` | `gmm` | **bereits Pipeline**; V1-Spalten entfallen |
| A17 | γ Favoriten/Longshots (`reply:391`, `:484`) | `models/gmm_estimation.py` (Teilmengen `IsFav`) | `gmm` | überführen; V1-Anteile entfallen |
| A18 | Scrape-Lag, Median 19,1 h / 92 % (`reply:93`) | `features/shape_data.py` | vor `pre` | **neu zu spezifizieren** (Abschnitt 8) |
| A19 | `fig:r1c7pub`, reproduzierte eingereichte Figure 3 | — | — | **entfällt** (Abschnitt 6) |
| A20 | Gepaarter Opening/Closing-Brier (`reply:391`) | `models/bookmaker_accuracy.py` | `pre` | überführen; Vorzeichen prüfen (Abschnitt 11) |
| A21 | GMM je Opening-Preis-Dezil, J-Test (`reply:391`) | `models/gmm_estimation.py` | `gmm` | **neu zu spezifizieren** — Eingang sind heute V1-Wide-Frames |

---

## 1. Gesetzte Entscheidungen

### 1.1 K in der Momentbedingung — unverändert, keine Codeänderung

**Entschieden.** Die Momentbedingung schätzt weiterhin nur γ, K bleibt
implizit 0.

| Stelle | Was dort steht |
|---|---|
| `src/pfd/utils/_gen_meth_mom.py:61-66` | `mom_cond_1/2` ohne K-Term |
| `src/pfd/helpers/fit_gmm_mod.py:54-55` | `k_moms=14`, `k_params=1` |
| `src/pfd/helpers/base/create_pm_mod.py:99-104` | Bayesian-Pendant, ohne K |

Beleg für „nicht ändern": `revision/snapshots/gmm_rasterfree/README.md`
(freies K bei kleinem γ nicht identifiziert, γ entgleist gepoolt, J
verschlechtert sich).

**Nicht gedeckt:** die Begründung im Text. `reply1_20260728.tex:320-321`
behauptet „that error is zero by construction";
`gmm_rasterfree/README.md:14-24` misst `E[q(1−q)] = 0,2176` gegen
`E[(P−ω)²] = 0,2111`, also 103 % der gemessenen Größe. Siehe W7.

### 1.2 Bayesian-Priors — unverändert, insbesondere `sd_gamma`

**Entschieden.** Keine Änderung an `create_pm_mod.py`.

| Zeile | Prior |
|---|---|
| `create_pm_mod.py:72` | `sd_eps = pm.HalfCauchy(beta=0.01)` |
| `create_pm_mod.py:75-79` | `mean_gamma = pm.Truncated(Normal(mu=0, sigma=1), lower=0)` |
| `create_pm_mod.py:80` | **`sd_gamma = pm.Exponential(lam=2.5)`** |
| `create_pm_mod.py:81-86` | `gamma = pm.Truncated(Normal(mean_gamma, sd_gamma), lower=0, dims="bookmakers")` |

Offener Widerspruch bleibt bestehen und wird nicht durch eine Priorwahl
geheilt: `references/specs/open_questions.md:432-442` — Posterior-Median
`sd_gamma` 0,007723 bei `mean_gamma` 0,0036; frequentistisch τ = 0,000,
I² = 0 %, Cochran-Q p = 0,749. Konsequenz: Abschnitt 10.4 verlangt
Posterior-vs-Prior-Diagnostik **ohne** Priorwechsel.

### 1.3 ADF/GARCH — nicht rechnen, Code auskommentieren

**Entschieden.** Beleg: im eingereichten Paper ist der Block bereits
vollständig auskommentiert.

| Belegstelle | Inhalt |
|---|---|
| `oup-authoring-template2.tex:624` | Verweissatz auf `appx:time_series_properties`, auskommentiert |
| `oup-authoring-template2.tex:1119-1191` | ADF, PACF, EGARCH, `\var{adf_stat}`, `\var{adf_p}`, `\InputTable{res_garch}` — durchgehend auskommentiert |

**Auszukommentieren:**

| Datei | Zeilen |
|---|---|
| `run_estimation.py:24` | Import `analyze_time_series_diagnostics` |
| `run_estimation.py:119-127` | Aufruf im `_post`-Lambda |
| `run_estimation.py:134` | `return (*garch, idx)` → nur `idx` |
| `run_estimation.py:136-138` | Entpacken → nur `signific_time_idx` |
| `run_estimation.py:232-233` | `values_to_save`-Einträge `adf_stat`, `adf_p` |
| `run_estimation.py:264` | `res_garch.tex` in `file_configs` |
| `src/pfd/models/time_series_diagnostics.py` | ganzes Modul (194 Zeilen), inaktiv — **nicht löschen** |

Mitentfallend: `cs_mean_rtrn.pdf`, `pacf.pdf`, `reports/tables/res_garch.tex`,
`\var{adf_stat}`, `\var{adf_p}`, und die zweite Kopie des
`NumOddsMvt < 20`-Filters in `time_series_diagnostics.py:73`.

Falls je reaktiviert: `baseline_status.md:125-130` — unter Normalisierung
ADF −5,35 → −3,79, p 0,0002 → 0,056.

### 1.4 Figure 6 (`scatter_gamma_loss`) — entfällt, Code auskommentieren

**Entschieden.** Auszukommentieren ist `bayesian_estimation.py:150-166`
(rcParams `:150-152`, `plt.subplots` `:154-155`, `sns.regplot` `:156`,
Tick-Schleife `:157-162`, `finalize_plot` `:163-166`).

### 1.5 `corr_gamma_loss` — gestrichen, in Code und Papertext

**Entschieden.** Löst W1 auf. **Nicht** die Folge von 1.4: Plot und
Korrelation sind getrennte Konsumenten von `metrics`.

**Code:**

| Datei | Zeilen | Folge |
|---|---|---|
| `run_estimation.py:234-237` | `corr_gamma_loss` in `values_to_save` | Schlüssel entfällt |
| `bayesian_estimation.py:140-148` | Aufbau von `metrics` | ohne Konsument |
| `bayesian_estimation.py:298` | `metrics` im Rückgabe-Tupel | Signatur `:39`, Docstring `:65-66` nachziehen |
| `run_estimation.py:168` | `rmse=rmse` an `estimate_bayesian_learning_rate` | Parameter entfällt |
| `bayesian_estimation.py:35, 53-54` | Parameter `rmse` + Docstring | entfällt |
| `run_estimation.py:203-207` | `metrics.to_hdf` | entfällt; `data/processed/metrics.h5` wird nicht mehr erzeugt |

**Papertext** (`oup-authoring-template2.tex`): Zeile **845** (Satz mit
`\var{corr_gamma_loss}` samt Folgesatz), Zeilen **847-854**
(`\begin{figure}` … `\end{figure}` mit `scatter_gamma_loss.pdf` `:850` und
`\label{fig:scatter_gamma_loss}` `:851`), Zeile **856**
(„Figure~\ref{fig:scatter_gamma_loss} visually demonstrates …").

### 1.6 `frac_missings` und `imput_loss.pdf` — ersatzlos entfernt

**Entschieden — im Code bereits vollzogen** (`1a2923c`).

| Prüfpunkt | Stand |
|---|---|
| `resample_and_impute.py` | kein `frac_missings`, kein `calc_imput_loss`, kein `imput_loss.pdf` |
| `resample_and_impute.py:121-128` | stattdessen Assertion: `n_missings` > 0 → `ValueError` |
| `grep -rn "frac_missings" src/` | keine Treffer |

**Stale Key.** `save_values.py:36-50` schreibt Zeilen in place und löscht nie
einen Schlüssel, den der Lauf nicht mehr erzeugt. Deshalb:

> **Verbindlich:** `reports/values/values.dat` ist **vor** dem Lauf zu
> löschen, nicht zu überschreiben. Betrifft `frac_missings`, `adf_stat`,
> `adf_p`, `corr_gamma_loss`.

### 1.7 Zeitfenster und Stützstellen — V2|B

**Entschieden — im Code bereits vollzogen** (`1a2923c`).

| Stelle | Ist-Stand | Ergibt bei `n_per=51`, `incr=5` |
|---|---|---|
| `resample_and_impute.py:83-84` | `groupby("GroupId")` auf `Update` | serieneigenes Fenster (V2) |
| `_create_gmm_data.py:57-58` | `OddsMvt{n_per-1-((i-1)*incr)}` | **50/45/40/35/30** (B) |
| `_gen_meth_mom.py:54` | `tau = [n_per-(i-1)*incr for i in (1,2,3)]` | **τ = [51, 46, 41]** |
| `create_pm_mod.py:93` | dieselbe Formel, dupliziert (Hinweis `:88-92`) | τ = [51, 46, 41] |

**Kontrollpunkt (verbindlich): γ̄ = 0,003474.**

| Größe | Sollwert | Belegstelle |
|---|---|---|
| γ̄ | **0,003474** | `gmm_rasterfree/support_shift_gamma.csv`, Spalte `V2 serieneigen \| B` |
| γ min | −0,000375 (Pinnacle) | dieselbe Spalte |
| γ max | 0,008758 (10Bet) | dieselbe Spalte |
| Median / neg / sig / J verw. | 0,003257 / 1 / 7 von 24 / 0 von 24 | `gmm_rasterfree/README.md:219` |

Die Referenz wurde mit `optim_method="nm"`, Startwert 0,01 und
`maxiter="cue"` gerechnet (`gmm_rasterfree/_support_shift.py:85-86`) —
identisch zu dem, was `gmm_estimation.py:81` verwertet (`ele[0]`, also der
feste Startwert aus `:66`). **Optimierer und Startwertbehandlung bleiben
unverändert; sonst verliert der Kontrollpunkt seine Referenz.**

`shift.log` ist gitignoriert (`.gitignore:61`) und taugt nicht als Beleg;
`support_shift_gamma.csv` ist getrackt.

Pfadfalle: `MIGRATION_V2B.md:131` nennt `eq_window_scope/…`; die Datei liegt
in `gmm_rasterfree/`.

### 1.8 `NumOddsMvt < 20`-Filter — nur Unbiasedness-Regressionen

**Entschieden**, abgeleitet aus `reply1_20260728.tex:263`:

> „[…] and it applies only to the unbiasedness regressions and the
> time-series diagnostics, not to the cross-sections in Tables 3--7 or to
> the GMM and Bayesian learning-rate estimates […]"

| Analyseblock | Filter | Codestelle |
|---|---|---|
| Unbiasedness-Regressionen | **an** | `unbiasedness_regressions.py:55` |
| ADF/GARCH | entfällt mit dem Block (1.3) | war `time_series_diagnostics.py:73` |
| GMM | aus | `gmm_estimation.py` |
| Bayesian | aus | `bayesian_estimation.py`, `gen_res_obj.py` |
| Cross-Sections Tab. 3–7 | aus | `bookmaker_accuracy.py`, `winning_proportions.py` |

Bestätigt durch `censoring/README.md:20-27`. **Folge:** der Satzteil „and
the time-series diagnostics" wird unzutreffend (W6).

### 1.9 Kontinuierliche Unbiasedness-Fassung — Überführung nach `src/pfd`

**Entschieden.** Ersetzt die 50 Perzentilregressionen in
`unbiasedness_regressions.py:54-92`.

| Element | Festlegung | Belegstelle |
|---|---|---|
| Achse | `X = log(Stunden bis Anpfiff)` | `revision_log.md:729-731`; `reply:333-334` |
| Basis | natürlicher kubischer Spline, **ns(df = 4)**, lineare Randbedingungen | `reply:334`; `main_spec/_ns_main.py`, `_ns_final.py` |
| Referenzpreis | `p_ref` = erster echt beobachteter normalisierter Preis der Serie | `continuous_unbiasedness/README.md` |
| Random Effects | **keine**; Match-RE ausgeschlossen (99,83 % der `Endog`-Varianz auf Matchup-Ebene) | `revision_log.md:734-736` |
| Inferenz primär | Cluster-Bootstrap **B = 100**, Cluster = Matchup | `revision_log.md:737-739` |
| Inferenz sekundär | CR1-Sandwich auf Matchup | `main_spec/_ns_final.py` |
| Simultanes Band | **sup-t** aus der Bootstrap-Kovarianz, α = 0,05, NSIM = 200 000 | `_ns_final.py:36-38` |
| Berichtsfenster | `HMAX = 48` h, Gitter 96 Punkte | `_ns_final.py:35`; `ns4_final_counts.csv` |
| Kovariaten | `TsDur`, `Compet_Challenger_Men`, `Compet_ITF_Men`, `Compet_Misc`, `Compet_WTA` | `_ns_bootstrap.py`, `COVS` |
| Filter | `NumOddsMvt < 20` (1.8) | `continuous_unbiasedness/README.md` |

**Überführung:** Eingang ist der Long-Frame aus Abschnitt 9, **nicht** der
Wide-Frame; die Analyse gehört damit in `_pre`, nicht in `_post`.
rpy2/lme4 nötig; R nach Initialisierung **nicht fork-sicher**
(`_ns_bootstrap.py`, Docstring) — der `Pool()`-Aufruf in
`unbiasedness_regressions.py:71-72` ist nicht übertragbar.
Snapshot-Skripte **nicht übernehmbar** (Ausgabepfade, Frame-Cache,
`part`-Aufteilung, Zwischendateien); Modellformel und sup-t-Rechnung ja.

**Laufzeit:** 58 s je Fit (M_c); B = 100 sequentiell ≈ 1,6 h, zwei Prozesse
≈ 0,8 h (`main_spec/README.md:316`). Speicher 3,39 GB je Fit, drei Prozesse
≈ 10,2 GB gegen 11,4 GB. Für `ns(df=4)` nicht separat vermessen → **nicht
belegbar**, ob billiger. Volle crossed RE ausgeschlossen: p ≈ 20 806,
~25 h, Speicheruntergrenze ~17 GB (`main_spec/README.md:70-86`).

### 1.10 Eq. 3 auf Kontraktebene — Überführung nach `src/pfd`

**Entschieden.** Ersetzt die bisherige Fassung in `winning_proportions.py`.

| Element | Festlegung | Belegstelle |
|---|---|---|
| Spezifikation | `Match = eta_0 + eta_1·OpnOdds + eta_2·DltOpnCls + TsDur + Compet_* + (1 + DltOpnCls \| Bookies)` | `revision_log.md:1305-1308` |
| Hauptmodell | **LPM** | `_eq3_contract.py`, Docstring |
| Robustheit | **Logit** | `revision_log.md:1351-1352`; `logit_check.csv` |
| Inferenz | cluster-robuste SEs statt Match-RE | `revision_log.md:1352-1353` |
| Stichprobe | 172 663 Kontrakte, 20 588 Matchups, 24 Bookmaker | `revision_log.md:1304-1306` |
| Schätzung | lme4, `REML = FALSE` | `revision_log.md:1308` |
| Sollwerte | eta_1 = 1,125, eta_2 = 0,956 | `revision_log.md:1314-1317` |
| Tabelle 6 | bleibt aggregiert, nicht mehr als Test gegen den Opening-Preis | `revision_log.md:1353-1355` |

Eingang ist `df_oc` — bereits Pipeline-Objekt (`run_estimation.py:98`).
rpy2/lme4. Snapshot-Skript **nicht übernehmbar**. Laufzeit **nicht
belegbar**. Umgebungshinweis: `baseline_status.md:221-232` — Reproduktion
von `ladder_cluster.csv` in WSL mit schlechtester relativer Abweichung
1,6e−12.

### 1.11 Figure 1 — ersetzt durch `rmse_vs_posting_scatter`, genau eine Abbildung

**Entschieden.** Eine Abbildung, nicht zwei; die Balkenfassung entfällt.

| Punkt | Feststellung |
|---|---|
| Vorlage | `rmse_baselines/_fig_scatter.py` (getrackt) |
| Ausgabe | `rmse_vs_posting_scatter.{pdf,png}` — gitignoriert (`.gitignore:39-40`) |
| Eingang des Skripts | `_fig_scatter.py:38-41`, Scratchpad-Parquet einer früheren Sitzung — **existiert nicht mehr**; Skript so nicht ausführbar |
| Zugrundeliegende CSV | `rmse_baselines/posting_time_by_bookie.csv` (getrackt) |
| Deren Spalten | `Bookies, n_series, n_obs, opn_hrs_med, opn_hrs_mean, opn_hrs_q25, opn_hrs_q75, cls_hrs_med, ts_dur_med, margin_opn_med, rmse_panel, rmse_series, rmse_publiziert, obs_per_series, rmse_gap` |
| Geplottet | x = `opn_hrs_med`, y = RMSE **auf Serienebene** (`_fig_scatter.py:47-51`, Docstring `:5`) — in der CSV `rmse_series`; exakte Identität ohne den Frame nicht nachprüfbar |
| Annotation | Pearson +0,409, Spearman +0,470 (`rmse_baselines/README.md:325`) |
| Referenzlinie `E[p(1−p)]` | wird **nicht** gezeigt (`revision_log.md:1715-1720`) |

### 1.12 Aggregationsebene — einheitlich Serienebene

**Entschieden.** Tabelle 7 behält ihr Design.

| Artefakt | heutige Ebene | Codestelle |
|---|---|---|
| **Figure 1** (`rmse.pdf`) | **Panelebene** | `bookmaker_accuracy.py:62-65`; `revision_log.md:714-717` |
| **Tabelle 7** (`res_rfa_tot.tex`) | **bereits Serienebene** | `bookmaker_accuracy.py:81` (`df_oc`), `fit_rfa_mod.py:65-66` |

**Zu ändern ist nur Figure 1:** `bookmaker_accuracy.py:62-65` muss auf einen
Frame mit einer Zeile je `GroupId` rechnen. `ylim=[0.39, 0.49]` (`:74`) ist
mitzuziehen (`rmse_baselines/README.md:305-308` nennt `[0,44; 0,47]`).

> **VERIFIZIEREN, nicht entscheiden:** auf *welchem* Serienframe. `df_oc`
> trägt zusätzlich `|RtrnOpnCls| > 0` (`bookmaker_accuracy.py:88`); ein
> ungefilterter Serienframe nicht. Die Größen unterscheiden sich messbar
> (`rmse_by_bookie_check.csv` führt `rmse_df_oc`, `posting_time_by_bookie.csv`
> führt `rmse_series`; Betfair 0,456811 gegen 0,456784). Keine Belegstelle
> wählt eine der beiden → **nicht belegbar**.

Textkorrektur: „clustering around 0.45" (`tex:687`) trifft nicht zu und traf
schon für die publizierte Fassung nicht zu (`revision_log.md:1701-1705`).

### 1.13 Seed — 42

**Entschieden.** `config.yaml:30`; `general/alt_seed.yaml` (`seed: 77`) bleibt
unbenutzt. Wirksam in `run_estimation.py:71`, weitergereicht über
`gen_res_obj.py:65, 95`. Vor dem Lauf verifizieren, dass die
`defaults`-Liste (`config.yaml:3`) den Wert nicht überschreibt (V-O7).

### 1.14 Aufräumen — toter Code und regenerierbarer Output

**Entschieden.** Grenze:

> **Unangetastet bleiben `revision/snapshots/`, `references/specs/` und die
> `revision/*.md`-Dateien.** Details in Abschnitt 12.

---

## 2. Weitere laufrelevante Spezifikationsentscheidungen

| # | Gegenstand | Entscheidung | Belegstelle | Status |
|---|---|---|---|---|
| S1 | Preisgröße | margenbereinigt, `p_own/(p_own+p_other)`, konsistent durch die Pipeline | `baseline_status.md:42-51`; `filter_and_shape.py:117-123`; `config.yaml:9` | entschieden |
| S2 | Zeitachse Unbiasedness | kontinuierliche absolute Achse, `ns(df=4)` | `revision_log.md:729-733` | entschieden; Überführung 1.9 |
| S3 | Zeitachse GMM/Bayesian | diskrete relative Perzentil-Achse | `revision_log.md:729-736, 1007-1009` | entschieden |
| S4 | Inferenz Unbiasedness | cluster-robust auf Matchup; Bootstrap-SEs primär | `revision_log.md:734-740` | entschieden |
| S5 | Simultane Inferenz | sup-t auf B = 100; krit. Wert 2,617 gegen 1,960; sup-\|t\| 2,509, p = 0,066 | `revision_log.md:1123-1132`; `global_tests.csv` | entschieden |
| S6 | Phasen-Narrativ | aufgegeben; monotone Beschreibung | `revision_log.md:1110-1118` | entschieden |
| S7 | Eq. 3 | Kontraktebene, LPM/Logit, cluster-robust | `revision_log.md:1351-1356` | entschieden; Überführung 1.10 |
| S8 | Inferenz Eq. 1–3 + Unbiasedness | alle vier cluster-robust; Eq. 2 zweiweg | `revision_log.md:177` | entschieden |
| S9 | Look-Ahead in der Imputation | Match aus dem Imputer-Feature-Set entfernt (`a2b694e`) | `baseline_status.md:20-27` | entschieden |
| S10 | `incr = 5` | beibehalten; datengetrieben optimal | `open_questions.md:322-340`; `config.yaml:16` | entschieden |
| S11 | Zählkonvention τ | 1-basiert (τ = Index + 1) | `open_questions.md:342-346` | entschieden |
| S12 | GMM-Schätzer | CUE plus First Stage; **Nelder-Mead**; verwertet wird der feste Startwert 0,01 | `config.yaml:17`; `gmm_estimation.py:58-66, 81, 88-99`; `fit_gmm_mod.py:67, 99` | entschieden (O6 geschlossen) |
| S13 | Sampling-Parameter | `hdi 0.95`, `n_chains 4`, `n_draws 5000`, `n_tune 2000`, `n_cores 4`, `targ_acpt 0.85`, `vi_n_iter 25000`, `vi_n_draws 10000` | `config.yaml:72-81` | entschieden; V-O7 |
| S14 | Bayesian-Läufe | 1 ADVI + 15 NUTS (`tot`, `fav`, `udd`, `pro`, `amat`, `q1`–`q10`) | `bayesian_estimation.py:84-124` | entschieden |
| S15 | Dezilbildung Bayesian | 10 Intervalle auf `OddsMvt0`, unter V2 der echte Opening-Preis | `bayesian_estimation.py:70-79`; `MIGRATION_V2B.md:104-107` | entschieden |
| S16 | Bookmaker-Heterogenität | wird **nicht mehr** als Heterogenitätsbefund berichtet (I² = 0 %, Q p = 0,749) | `revision_log.md:1771` | entschieden |
| S17 | Segment Favoriten/Longshots | 0,005531 gegen 0,001181 unter V2\|B, t = 4,49 | `revision_log.md:1791`; `favlong_by_spec.csv` | entschieden |
| S18 | Seed | 42 | 1.13 | entschieden |

---

## 3. VERIFIZIEREN — vor dem Lauf festzustellen, nicht zu entscheiden

| # | Punkt | Was fehlt |
|---|---|---|
| V-O5 | Gelten 8.846 / 184.112 / 4,80 % / 94 von 20.854 (`reply:263`) auch unter V2? | Belegzahlen aus `censoring/sample_stages.csv` auf `revision-baseline` (V1); kein Dokument rechnet sie unter V2 nach |
| V-O7 | Welcher `sampling`-Block bindet? | `config.yaml:2` listet `sampling: fast_sampling` vor `_self_` (`n_chains: 2`, `n_draws: 1000`, `n_tune: 500`, `targ_acpt: 0.8`); `config.yaml:72-81` setzt die Produktionswerte |
| V-O8 | `Estimation.start_params` | `config.py:23` deklariert das Feld; `config.yaml` enthält es nicht; `gmm_estimation.py:58-66` liest es nicht |
| V-O9 | Konsistenz-Bedingung Normalisierung, Punkt (2) „pro Zeitpunkt normalisieren" | `open_questions.md:283-287` stellt die Bedingung auf; kein Dokument stellt fest, ob `filter_and_shape.py:117-123` sie erfüllt |
| V-1.12 | Welcher Serienframe für Figure 1 (mit oder ohne `\|RtrnOpnCls\| > 0`) | siehe 1.12 |

---

## 4. Widersprüche zwischen Dokumenten

| # | Größe | Beleg A | Beleg B | Stand |
|---|---|---|---|---|
| W1 | Schicksal von `corr_gamma_loss` | `reply:580` (Entwurf): „retaining the qualitative description […] in the text only" | `revision_log.md:1782`: „wird nach R2-M10 ohnehin entfernt" | **aufgelöst durch 1.5**; `reply:580` und `:590` nachzuziehen |
| W2 | Aggregationsebene Figure 1 / Tabelle 7 | `revision_log.md:730-731, 777-779`: offen | `revision_log.md:1709-1711, 810-811`: Serienebene | **aufgelöst durch 1.12**; Restfrage V-1.12 |
| W3 | Serienzahl nach Nullvarianz- und `<20`-Filter | `censoring/sample_stages.csv`: 184.112 → 175.266 | `continuous_unbiasedness/README.md`: 184.012 → 175.166 | offen (je 100 Differenz) |
| W4 | `avg_gamma_gmm` im Live-Stand | `MIGRATION_V2B.md:8`: 0.0332 | `values.dat:19`: 0.0035 | offen; erledigt sich mit dem Neulauf |
| W5 | Bearbeitungsstand R2-M7 | `reviewer_tracker.md`: „in Arbeit"; `revision_log.md:1709` mit Entscheidung | `reply:559-565`: Minor Comment #7 ohne Antwort | offen (Reply-Lücke) |
| W6 | Reichweite `NumOddsMvt < 20` | `reply:263`: „and the time-series diagnostics" | 1.3: ADF/GARCH entfällt | entsteht durch 1.3 |
| W7 | K = 0 „by construction" | `reply:320-321` | `gmm_rasterfree/README.md:14-24`: Bodensatz 103 % | offen, bewusst |
| W8 | Seed | `config.yaml:30`: 42 | `general/alt_seed.yaml`: 77 | **aufgelöst durch 1.13** |
| W9 | Zeilenverweis `frac_missings` | `MIGRATION_V2B.md:28`: `run_estimation.py:203` | dort steht `metrics.to_hdf`; `frac_missings` kommt nicht vor | offen (stale) |
| W10 | Pfad zur V2\|B-Referenz | `MIGRATION_V2B.md:131`: `eq_window_scope/…` | Datei liegt in `gmm_rasterfree/` | offen (stale) |
| W11 | β₁-Marken und SE-Faktor | `revision_log.md:1117, 1121`: 1,244 / 0,938 / 0,759 und Faktor 3,6 — aus `cluster_robust_marks.csv` (cr-Basis, k = 6) | `reply:333`: 1,17 / 0,92 / 0,78 — aus `ns4_marks.csv` (ns(df=4)) | offen: zwei Basen, beide belegt |
| W12 | Vorzeichen des Opening/Closing-Brier-t | `reply:391`: `t = -6.4` | `rmse_baselines/opening_vs_closing.csv`: `delta_brier` 0,002389, `t` **+6,357** | offen — Vorzeichenkonvention beim Neulauf festlegen |
| W13 | Betfair-Margenrang | `reply:208` und `tab:r1c4`: **Rang 15 von 24**, 7,80 % | `sharp_soft/README.md:12-13`: **Rang 14 von 24** | offen — beim Neulauf von A4 entscheidet die Pipeline |

---

## 5. Gesetzte Streichungen im Antwortdokument

Diese drei Stellen fallen ersatzlos bzw. werden ersetzt. `reply1_20260728.tex`
wird dafür separat bearbeitet; `reply1_20260808.tex` bleibt unangetastet.

| Stelle | Was gestrichen wird | Begründung |
|---|---|---|
| **`reply:346-348`** | `fig:r1c7pub`, die reproduzierte eingereichte Figure 3 samt Bildunterschrift und `\label` | Die Abbildung steht im eingereichten Paper. `revision/reply_figures/published_unbiased_reg.pdf` ist byte-identisch mit `A_baseline/figures/unbiased_reg.pdf` (sha256 `024644d5dbb52a77bf117d12742db407c94b201fd61c7c17437451ae737678c1`) und konnte per Konstruktion nie aus der neuen Pipeline stammen |
| **`reply:484`** | der Vergleich „the learning rate averaged over bookmakers moves from 0.0054 to 0.0035" | Referenzklasse. 0,0054 ist ein V1\|A-Wert (`E_gmm_exponent_fix/values.csv:12`), den die neue Pipeline nicht mehr erzeugt. **Nur der neue Wert bleibt** |
| **`reply:174, 180, 338`** | `tab:r1c2` Zeile „Unbiasedness (Fig.~3)" samt „factor of 2.1" in `:338` | Der Eingang fehlt (`_discrete_cluster.py:27-28` liest V1-Artefakte) und der Gegenstand fehlt: der Snapshot definiert sich als „dieselbe **Produktionsspezifikation**" (`cluster_inference_unbiased/README.md:17-19`), die nach 1.9 die kontinuierliche ist |

**Kein Ersatz aus `ns4_final_se.csv`.** Die dortige Spalte `ratio` ist
`se_boot / se_sandwich` (0,2751567 / 0,3006913 = 0,91508), also ein Vergleich
**zweier cluster-robuster Verfahren**. Die gestrichene Zeile verglich
**cluster-robust gegen modellbasiert** (`discrete_cluster_beta1.csv`, Spalte
`factor_vs_model`, Median 2,13). Eine modellbasierte SE ist in keiner
`ns4_*`-Datei abgelegt. Die einzige belegte Cluster-gegen-Modell-Zahl auf
kontinuierlicher Basis ist 3,56 auf der cr-Basis
(`cluster_robust_marks.csv`, 0,1143736 / 0,0321556) — andere Basis.

---

## 6. Gegenstandslos gewordene Analysen

| # | Analyse | Begründung |
|---|---|---|
| A3 | Cluster-Faktor der diskreten Unbiasedness | Eingang **und** Gegenstand entfallen; siehe Abschnitt 5 |
| A11 | Benachbarte Änderungen der publizierten β₁-Kurve, \|z\| ≤ 0,92 | `reply:333` wird ersetzt (6.1); `_simultaneous.py:31` liest `C_normalized/beta1_curve.csv`, das die neue Pipeline nicht erzeugt |
| A19 | `fig:r1c7pub` | gestrichen (Abschnitt 5) |
| A9, Teil | `rmse_real_vs_imputed.csv` (`_rmse_magnitude.py:187`) | unter V2 gibt es keine imputierten Zellen (`resample_and_impute.py:121-128`); im Reply nicht zitiert |
| A16/A17, V1-Anteile | V1-Spalten von `support_shift_gamma.csv` und `favlong_by_spec.csv` | tragen nach der Streichung des Vergleichs keine Reply-Zahl mehr |

### 6.1 Ersatz für `reply:333`

**Neu zu formulieren:** der Pfad ist **signifikant nicht konstant**
(`p_boot` 0,0), während H0 „β₁(t) = 1 überall" simultan **nicht** verworfen
wird (p 0,066) und simultan **kein Gitterpunkt von 96** die 1 ausschließt.

Belege, `main_spec/global_tests.csv`:

```
test,stat,crit_5pct,p_gauss,p_boot,arg_max_hours
H0: beta_1(t) = 1 ueberall,2.5089371712578092,2.6165547067445334,0.066515,0.06,0.3466674966234331
H0: beta_1(t) konstant,3.9984815483755343,2.6600942593698815,0.00059,0.0,16.240149351297315
beta_1(24h) - beta_1(0.25h),4.076640664656311,1.959963984540054,,0.0,
```

und `main_spec/ns4_final_counts.csv`:

```
Band,punktweise,simultan,von
Sandwich,45,0,96
Bootstrap,38,0,96
```

> **Ausdrücklich vermerkt:** die heutige Formulierung in `reply:333` —
> „not one of the 48 adjacent changes in the published curve is individually
> significant" — gibt den Befund **falsch** wieder. Die Konstanz-Nullhypothese
> wird verworfen (`stat` 3,998 > `crit_5pct` 2,660, `p_boot` 0,0), ebenso ist
> der Randkontrast β₁(24 h) − β₁(0,25 h) signifikant (`stat` 4,077 > 1,960,
> `p_boot` 0,0). Es gibt eine Bewegung; unbestimmt bleibt nur **wo** der Pfad
> von 1 abweicht.

### 6.2 Restsatz in `reply:484`

Nach Streichung des Vergleichs bleiben stehen:

- „favorites learn measurably faster than longshots (0.0055 against 0.0012,
  a difference of 4.5 standard errors)" — getragen von A17,
  `favlong_by_spec.csv`, Zeile `V2|B`: 0,005531 / 0,001181 / t = 4,4914.
- „the longshot rate remains indistinguishable from zero" — getragen von
  A16/A17.
- „the figures quoted here are the current state of the re-estimation rather
  than final table values" — zahlenfreier Vorbehalt.

> **Umzuformulieren:** „**The finding that carries Section~5.5 survives the
> change**". „survives **the change**" und „**remains**" setzen den
> gestrichenen Vorher-Zustand voraus. Ohne ihn steht im Absatz keine
> Vergleichsgröße mehr; der Satz ist ohne die 0,0054 nicht schlüssig.

---

## 7. `tab:r1c1` — bleibt, wird vollständig neu gerechnet

Die Tabelle bleibt im Antwortdokument. Sie stellt rohe inverse Quoten gegen
margenbereinigte; die Raw-Spalte ist damit ein Ergebnis unter
`normalize = False`.

### 7.1 Heutige Werte und ihre Herkunft

Wörtlich, `reply1_20260728.tex:132-141`:

```
 & Raw inverse odds & Margin-adjusted \\
Median overround, opening / closing   & 7.81\% / 7.60\% & --- \\
Median opening probability, Player 1  & 0.5464 & 0.5063 \\
Winning rate, lowest revision bin (Table~5)  & 0.3369 & 0.3292 \\
Winning rate, highest revision bin (Table~5) & 0.6345 & 0.6519 \\
Bookmaker RMSE ranking & Spearman 0.992, largest shift 2 places \\
```

| Zeile | Quelle | Art |
|---|---|---|
| Overround 7,81 % / 7,60 % | **keine Datei**; `open_questions.md:255-256` nennt 7,82 % / 7,61 % | **nicht belegbar** |
| Median opening probability 0,5464 / 0,5063 | **keine Datei**; `open_questions.md:264` nennt roh 0,5405 | **nicht belegbar** |
| Winning rate lowest / highest, Raw | `A_baseline/table5_res_wp.csv:2` und `:13` | eingefrorenes Snapshot-Artefakt |
| Winning rate lowest / highest, normalisiert | `open_questions.md:270-272`; Pipeline-Output `res_wp.tex` | Pipeline |
| Spearman 0,992 | `compare_2x2.csv`, Zeile `rmse_spearman_vs_B0` = 0,9922 | Snapshot-Vergleichsdatei |
| „largest shift 2 places" | **keine Datei** | **nicht belegbar** |

> **Drei der heutigen Werte sind nicht belegbar:** Overround 7,81/7,60,
> Median-Opening-Wahrscheinlichkeit 0,5464/0,5063, „largest shift 2 places".

### 7.2 Raw-Spalte aus der Pipeline

`normalize` wirkt an genau einer Stelle — `filter_and_shape.py:120-122`:

```python
    impl_probs = (
        p_own / (p_own + p_other) if cfg.estimation.normalize else p_own
    )
```

Der Overround (`p_own + p_other`) ist ausschließlich in `:118` verfügbar;
`:125` verwirft `other_col`.

**Teildurchgang mit `normalize=False`** über:

| Modul | für |
|---|---|
| `models/filter_and_shape.py` (`filter_and_shape_data`) | `OddsMvt`, `OpnOdds`, Overround |
| `models/bookmaker_accuracy.py:62-93` | RMSE je Bookmaker, `df_oc`, `iqr_rtrns` |
| `models/winning_proportions.py:72-123` | Bins von Table 5 |

**Nicht nötig:** `bookmaker_accuracy.py:115` (`fit_gpm_mod`), `:129-132`
(`fit_rfa_mod`, 25 Pool-Tasks), `winning_proportions.py:140-141`
(`bootstrap_std_error`, `n_bootstraps=1000`, speist nur die SE von Tabelle 6,
`:204`), `:160-200` (Abbildung).

**Nicht doppelt laufen:** `wide`, `post`, `gmm`, `bayesian` — keine Größe der
Tabelle stammt aus dem Wide-Frame (`baseline_status.md:90-93`).

**Laufzeit und Speicher des zweiten Durchgangs: nicht belegbar.** Es gibt
keine gemessene Laufzeit für `pre` allein; belegt sind nur die „~19 min" für
einen vollen frequentistischen Lauf (`E_gmm_exponent_fix/MANIFEST.md`).

### 7.3 Was sich unter V2|B ohnehin ändert

| Zeile | durch V2\|B | Begründung |
|---|---|---|
| Overround | **nein** | entsteht vor dem Resampling |
| Median opening probability | **nein** | `OpnOdds` aus `filter_and_shape.py:130` |
| Winning rate lowest / highest bin | **nein** | Table 5 läuft auf `df_oc`; `MIGRATION_V2B.md:70` führt `res_wp.tex` als „nein" |
| Bookmaker RMSE ranking | **nein durch V2\|B — ja durch 1.12** | Serienebene verschiebt die Werte von 0,4519–0,4719 auf 0,4465–0,4646 (`revision_log.md:1701-1704`) |

Keine Zeile ändert sich wegen V2|B; neu zu rechnen sind alle vier ohnehin.

---

## 8. Scrape-Lag (A18)

Behauptet in `reply:93`: Median-Lag **19,1 h nach Anpfiff**, **92 %**
innerhalb 48 h, kein Datensatz vor Anpfiff.

### 8.1 Heute nicht ableitbar

| Kandidat | Befund |
|---|---|
| `data/processed/shaped_data.h5` | kein Scrape-Zeitstempel; `shape_data.py:108-114` (`cols_base`) enthält `Timestamp` nicht |
| `data/processed/timestamps.h5` | nur Zeitstempel, ohne Anpfiff und ohne verwendbaren Schlüssel: `shape_data.py:51-52` kopiert `df["Timestamp"]` **vor** `dropna` (`:61-71`), vor dem `Final result`-Filter (`:74`), vor dem Datums-Regexfilter (`:82-88`) und vor drei `reset_index(drop=True)` |
| `reports/values/values.dat` | führt `crawl_start`, `crawl_end`, `crawl_dur` — Crawl-Zeitraum, nicht den Abstand zum Anpfiff |
| `revision/snapshots/` | keine Datei enthält die Größe |

### 8.2 Rohgröße und Ort der Rechnung

Die Aussage trägt **Scrape-Zeitpunkt minus Anpfiff**:

| Größe | Herkunft |
|---|---|
| Scrape-Zeitpunkt | `_crawl_data.py:199`: `data["Timestamp"] = str(pd.Timestamp.now())`; Feld `Timestamp` in `data/raw/crawled_odds.json` (Codebook: „Timestamp of when the data was crawled") |
| Anpfiff | Feld `Date`, in `shape_data.py:76-90` bereinigt und geparst |

**Rechnung in `src/pfd/features/shape_data.py`, nach `:90` und vor
`:108-114`** — dort liegen beide Größen gleichzeitig im Frame:

```python
lag_h = (pd.to_datetime(df["Timestamp"]) - df["Date"]).dt.total_seconds() / 3600
```

Der Halbsatz „recording a match only once its final result had been posted"
entspricht dem Filter `shape_data.py:74`.

### 8.3 Ablage

| Ziel | Inhalt |
|---|---|
| `revision/snapshots/<STUFE>/scrape_lag.csv` | `n_records, lag_median_h, lag_mean_h, share_le_48h, share_negative, lag_p05_h, lag_p95_h, lag_max_h` |
| zwei `\var{}`-Schlüssel über `save_values` (wie `crawl_*` in `shape_data.py:322-330`) | `scrape_lag_med`, `scrape_within48` |

### 8.4 Offen

1. **Über welche Filterstufe gemittelt wird.** `reply:93` sagt „across all
   scraped records"; ob damit die rohen Datensätze (wie `timestamps` in
   `:51`) oder die nach `:74`/`:88` gefilterten gemeint sind, sagt keine
   Belegstelle → **nicht belegbar**.
2. **Wie der Durchlauf erfolgt, ohne `shaped_data.h5` neu zu schreiben.**
   `shape_data()` schreibt die Datei; sie soll unangetastet bleiben. Ob ein
   eigener Durchlauf über `crawled_odds.json` oder eine Erweiterung von
   `shape_data` mit unterdrücktem Schreiben gewählt wird → **nicht
   belegbar**.

Ob die konkreten Zahlen 19,1 h und 92 % herauskommen, ist mangels
Vergleichsdatei **nicht belegbar**.

---

## 9. Zwei neue Pipeline-Objekte

### 9.1 Long-Frame mit Anpfiffabstand

| Punkt | Feststellung |
|---|---|
| **Ort** | `src/pfd/models/filter_and_shape.py`. Zwei Eingriffe: (a) `Date` in die Spaltenauswahl `:155-164` aufnehmen — sie enthält heute `Matchup, GroupId, Competition, IsPro, IsFav, Bookies, NumOddsMvt, TsDur, Match, Update, OddsMvt, OpnOdds, ClsOdds`, **kein `Date`**; (b) `Kick` und `HoursToKick` bilden, sinnvoll bei `:101-104`, wo `Update` bereits gruppiert wird |
| **Vorbild** | Jedes Snapshot-Skript baut es nach: `kick = raw.groupby("Matchup")["Date"].first()`, dann `HoursToKick = (Kick − Update)/3600` — identisch in `sharp_soft/_sharp_soft.py:57-60`, `flb_calibration/_flb_continuous.py:52-56`, `censoring/_censoring_thresholds.build` |
| **Spalten** | `GroupId, Matchup, Bookies, Update, Date, Kick, HoursToKick, X = log(HoursToKick), p_ref, Match, OddsMvt, OpnOdds, ClsOdds, NumOddsMvt, IsFav, IsPro, TsDur, Compet_*` |
| **Filterschritte** | `HoursToKick > 0`; Nullvarianz je `GroupId`; `NumOddsMvt < 20` (`_flb_continuous.py:57-59`) |
| **Daran hängend** | A5b, A7, A8, A9, A10, A13 |
| **Ersetzt** | `pfd_mainspec_frame2.parquet`, `pfd_flb_continuous.parquet`, `pfd_sharp_frame.parquet` |
| **Scrape-Lag darauf?** | **Nein** — der Lag braucht `Timestamp`, das bereits in `shape_data.py:108-114` aus dem Frame fällt. Gemeinsam ist nur die Spalte `Date` |

### 9.2 Ungefilterte `df_oc`-Variante

| Punkt | Feststellung |
|---|---|
| **Ort** | `src/pfd/models/bookmaker_accuracy.py`, der Zustand **zwischen `:85` und `:88`**: `:81` `df_oc = df.groupby("GroupId", as_index=False).first()`, `:84-85` `RtrnClsEnd`/`RtrnOpnCls`, `:88` `df_oc = df_oc[df_oc["RtrnOpnCls"].abs() > 0]` |
| **Größe** | 184.415 Kontrakte in 20.920 Matchups ungefiltert gegen 172.663 gefiltert (`flb_calibration/README.md:4-6`; `compare_2x2.csv`, `n_groups_dfoc`) |
| **Spalten** | `GroupId, Matchup, Bookies, Match, OpnOdds, ClsOdds, RtrnClsEnd, RtrnOpnCls, IsFav, IsPro, TsDur, Compet_*`; für A2/A15 zusätzlich `FEOpn, FECls, Endog, Exog` |
| **Daran hängend** | ungefiltert: A12, A14 — gefiltert: A2, A15, A20, A1 |
| **Ersetzt** | `pfd_flb_frame.parquet` sowie die nicht mehr existierenden Caches `pfd_eq3_frame.parquet` und `pfd_eq12_frame.parquet` |

---

## 10. Artefaktplan

### 10.1 Versionierter Ersatz für `values.dat`

`reports/values/values.dat` ist gitignoriert (`reports/values/.gitignore:2`,
`.gitignore:24`); ebenso `reports/figures/*`, `reports/tables/*`, `models/*`,
`data/interim/*`.

> **Versionierter Ersatz: `revision/snapshots/<STUFE>/values.csv`** —
> zweispaltig `key,value`. Format nach `A_baseline/MANIFEST.md`.

Zusätzlich `revision/DIFF_TO_PUBLISHED.md` über
`python revision/compare_to_published.py <STUFE>`.

### 10.2 Ort des Snapshots

`revision/snapshots/F_v2b/`. Global gitignoriert und daher nicht ablegbar:
`*.h5`, `*.parquet`, `*.pdf`, `*.png`, `*.log` (`.gitignore:38-42, 61`).
**Logs sind kein Beleg.**

### 10.3 Abbildungen — CSV und sha256

Weil `.pdf`/`.png` unter `revision/snapshots/**` gitignoriert sind, gilt für
**jede** vom Lauf erzeugte Abbildung:

1. Die **erzeugende CSV** liegt im Snapshot und enthält alle geplotteten
   Werte, so dass die Abbildung ohne den Originalframe neu zeichenbar ist.
2. Der **sha256** der Abbildungsdatei wird in `figures/sha256.csv` geführt
   (Spalten `file,sha256,bytes`); Vorbild `A_baseline/figures/sha256.csv`.

| Abbildung | erzeugende CSV | Spalten |
|---|---|---|
| `rmse_vs_posting_scatter.pdf` (ersetzt Figure 1) | `rmse_posting_by_bookie.csv` | `bookie, n_series, opn_hrs_med, rmse_series, pearson, spearman` |
| Figure 3, obere Tafel | `beta1_curve.csv` | `hours, beta_1, se_sandwich, se_boot, pw_lo, pw_up, sim_lo, sim_up, excl_1_sim` |
| Figure 3, untere Tafel | `beta1_rmse_bins.csv` | `h_lo, h_up, h_mid, n, brier, rmse` |
| `gmm_params.pdf`, `gmm_jstat.pdf`, `gmm_pvalue.pdf` | `gmm_by_bookie.csv`, `gmm_by_bookie_first_stage.csv` | `bookie, gamma, std_gamma, J_stat, p_value` |
| `post_gamma_*.pdf` | `bayes_summary.csv`, `bayes_by_bookie.csv` | siehe 10.4 |
| `rtrn_opn_cls.pdf`, `win_props_re.pdf`, `tracker_advi.pdf`, `traces_*.pdf`, `facetgrid_*.pdf` | nur sha256 | — |

Entfallen: `scatter_gamma_loss.pdf` (1.4/1.5), `cs_mean_rtrn.pdf`, `pacf.pdf`
(1.3), `imput_loss.pdf` (1.6).

### 10.4 Artefakte je Schritt

| Schritt | Datei | Inhalt | Deckt ab |
|---|---|---|---|
| shape | `scrape_lag.csv` | siehe 8.3 | `reply:93` |
| pre | `values.csv` | alle Schlüssel | `iqr_rtrns`, `n_obs`, `n_groups`, `is_pro/amateur`, `bootstr_*`, `bm_quantile`, `ts_dur_*`, `n_per` |
| pre | `values_raw.csv` | Teildurchgang `normalize=False` | Raw-Spalte von `tab:r1c1` (7.2) |
| pre | `margin_by_bookie.csv` | `bookie, margin_all_med, margin_opn_med, n_series, share` | `tab:r1c4`, W13 |
| pre | `rmse_posting_by_bookie.csv` | siehe 10.3, **Serienebene** (1.12) | Figure 1 |
| pre | `sample_stages.csv` | `stufe, n_serien, n_zeilen` | V-O5, `reply:263` |
| pre | `included_vs_excluded.csv` | wie `censoring/` | `tab:r1c5` |
| pre | `table3_res_gpm.csv` … `table7_res_rfa_tot.csv` | wie `A_baseline` | Tabellen 3–7 |
| pre | `eq12_cluster.csv`, `eq12_varcomp.csv`, `eq12_wald.csv` | Punktschätzer, SE modellbasiert und cluster-robust, Faktor, Between-Match-Anteil | `tab:r1c2`, `reply:208` |
| pre | `eq3_contract.csv`, `eq3_logit_check.csv` | eta_0/1/2, SE cluster-robust, Stufen S1–S4 | `tab:r2c1` |
| pre | `beta1_curve.csv`, `beta1_rmse_bins.csv`, `global_tests.csv`, `beta1_band_counts.csv` | siehe 10.3 und 6.1 | `fig:r1c7new`, `tab:r1c7`, Ersatz für `reply:333` |
| pre | `beta1_filter_marks.csv`, `beta1_thresholds.csv` | β₁ mit/ohne Filter, Schwellenleiter | `tab:r1c5b` |
| pre | `beta1_without_sharp.csv` | β₁ ohne 2 / ohne 4 | `tab:r1c4b` |
| pre | `brier_paired.csv` | `brier_first, brier_last, diff, se_cluster, t, n_series, n_matchups, hours_first, hours_last` | `reply:342` |
| pre | `opening_vs_closing.csv` | `delta_brier, se_cluster, t, p, bss_cls_vs_opn` | `reply:391`, W12 |
| pre | `calibration_by_price.csv`, `continuous_calibration_grid.csv`, `bias_by_decile.csv` | λ, SE, t; λ(X) über das Gitter; Dezilabweichungen | `tab:r1c8`, `fig:r1c8`, `reply:382` |
| wide | `wide_shape.csv` | `n_serien, n_matchups, n_bookies, n_per, n_nan` | Kontrolle: `n_nan` **muss 0** sein (`resample_and_impute.py:123-128`) |
| gmm | `gmm_by_bookie.csv` | `bookie, gamma, std_gamma, J_stat, p_value` | **γ̄ = 0,003474**, min/max/argmin/argmax |
| gmm | `gmm_by_bookie_first_stage.csv` | dito, `maxiter=1` | First-Stage-Vergleich |
| gmm | `gmm_without_sharp.csv` | Aggregat über Teilmengen | `tab:r1c4b` |
| gmm | `gmm_favlong.csv` | γ je `IsFav`-Teilmenge, Differenz, t | `reply:391`, `:484` |
| gmm | `gmm_by_decile.csv` | γ, J, p je Opening-Preis-Dezil | `reply:391` (A21) |
| gmm | `gmm_start_spread.csv` | `bookie, gamma_start0, gamma_min, gamma_max, gamma_range, gamma_std, gamma_median, n_distinct_4dp, max_abs_dev_from_start0` | O6 auf V2\|B — die vorhandene Datei ist auf V1\|A gerechnet (γ̄ 0,033222) |
| bayesian | `bayes_summary.csv` | `subset, param, median, mean, sd, hdi_lower, hdi_upper` | die sieben Bayesian-`\var{}`-Werte |
| bayesian | `bayes_by_bookie.csv` | `subset, bookie, median, hdi_lower, hdi_upper` | S16 |
| bayesian | `bayes_convergence.csv` | `subset, rhat, ess_bulk, ess_tail, div, draws` | Vorbild `gmm_rasterfree/bayes_convergence.csv` |
| bayesian | `bayes_zero_mass.csv` | `bookie, median, p_lt_0005, p_lt_001, gmm` | Truncation-Bindung |
| bayesian | `bayes_sdgamma.csv` | Verteilungskennzahlen der `sd_gamma`-Draws | Vorbild `gmm_rasterfree/bayes_sdgamma.csv` |
| bayesian | `bayes_sdgamma_prior.csv` | Posterior-Median, Prior-Median (`Exponential(2.5)` → 0,27726), Verhältnis, Perzentil in der Prior-Verteilung | `open_questions.md:432-442`; Prior bleibt unverändert (1.2) |
| bayesian | `bayes_vs_gmm.csv` | `subset, bayes, gmm, verhaeltnis` | `open_questions.md:421-426` (tot 1,03; udd 0,97; fav 1,53) |
| alle | `figures/sha256.csv` | `file, sha256, bytes` | 10.3 |

### 10.5 Was ins `MANIFEST.md` gehört

Vorbild: `A_baseline/MANIFEST.md`, `E_gmm_exponent_fix/MANIFEST.md`.

1. **Provenance:** HEAD-SHA, `git status --short`, Referenzstufen, Datum,
   Maschine.
2. **Spezifikation:** V2|B ausgeschrieben — `groupby("GroupId")`,
   Stützstellen 50/45/40/35/30, τ = [51, 46, 41], `n_per = 51`, `incr = 5`,
   `pctl = 2`, `max_iter = "cue"`, `optim_method = "nm"`, verwerteter
   Startwert 0,01, `normalize = True`, `ts_dur = [12, 72]`,
   `bm_quantile = 0.25`.
3. **Effektive Sampling-Werte** (V-O7), effektiver Seed (1.13), Zustand von
   `estimation.checkpoint`.
4. **Was abgeschaltet wurde:** ADF/GARCH (1.3), Figure 6 (1.4),
   `corr_gamma_loss` (1.5) — mit den auskommentierten Zeilenbereichen.
5. **Was überführt wurde:** A1–A21 nach Abschnitt 0, mit den ersetzten
   Funktionen.
6. **Herkunft jeder Datei:** neu gerechnet gegen kopiert.
7. **Abbildungen:** je Abbildung die erzeugende CSV und der sha256-Eintrag
   in `figures/sha256.csv`; für Abbildungen ohne Rekonstruktions-CSV
   ausdrücklich vermerken, dass nur der Hash vorliegt.
8. **Kontrollpunkt:** γ̄ getroffen ja/nein, erreichter Wert auf sechs
   Nachkommastellen gegen 0,003474.
9. **Bekannte Lücken:** welche `\var{}`-Schlüssel der Lauf nicht mehr
   erzeugt (`frac_missings`, `adf_stat`, `adf_p`, `corr_gamma_loss`) — mit
   der Notiz, dass `values.dat` vor dem Lauf gelöscht wurde, weil
   `save_values.py:36-50` Schlüssel nur aktualisiert, nie entfernt.
10. **Vorbehalt bei Wiederaufnahme:** der globale NumPy-RNG wird nicht
    wiederhergestellt; `bootstr_std` kann um bis zu ~0,0009 abweichen. Für γ
    gegenstandslos, weil `gmm_estimation.py:81` nur den festen Startwert
    0,01 verwertet (S12).

---

## 11. Offene Punkte

| # | Punkt | Stand |
|---|---|---|
| O-A20 | Vorzeichen des Opening/Closing-Brier-t: `reply:391` schreibt −6,4, `rmse_baselines/opening_vs_closing.csv` führt `delta_brier` 0,002389 und `t` **+6,357** | Vorzeichenkonvention beim Neulauf festlegen und den Reply danach ausrichten. Welche gemeint ist: **nicht belegbar** |
| O-A21 | GMM je Opening-Preis-Dezil ist **neu zu spezifizieren**: `_flb_gmm_split.py:32-33` liest die V1-Wide-Frames `C_normalized/wide_imputed.h5` und `C1_refactor/wide_imputed.h5`, die es unter V2\|B nicht mehr gibt | Ein V2\|B-Sollwert für die Dezil-J-Tests existiert nicht → gegen sich selbst nicht prüfbar, **nicht belegbar** |
| O-W13 | Betfair-Margenrang: `reply:208` und `tab:r1c4` nennen **Rang 15 von 24** (7,80 %), `sharp_soft/README.md:12-13` nennt **Rang 14 von 24** | Entscheidet der Neulauf von A4 |
| O6 | Nelder-Mead als alleiniges CUE-Verfahren | Durch S12 **geschlossen**: unverändert, damit der Kontrollpunkt seine Referenz behält. Die Frage aus `open_questions.md:63-68` bleibt als Textfrage offen |
| V-O5, V-O7, V-O8, V-O9, V-1.12 | siehe Abschnitt 3 | vor dem Lauf zu **verifizieren** |
| W3, W4, W7, W9, W10, W11 | siehe Abschnitt 4 | offen |

---

## 12. Geschützte Belege

Solange ein Block nicht überführt ist, ist sein Snapshot-Artefakt die
**einzige** Quelle der zugehörigen Reply-Zahl. Diese Dateien dürfen bis dahin
nicht gelöscht werden.

### 12.1 Dauerhaft geschützt

| Datei | Größe | Grund |
|---|---|---|
| `data/processed/shaped_data.h5` | 262.131.472 B | Eingang aller Analysen; gesetzte Ausnahme |
| **`data/raw/crawled_odds.json`** | 352.460.804 B, git-getrackt | **Einzige Quelle des Scrape-Lags (A18)**; `shaped_data.h5` trägt `Timestamp` nicht. Neu in dieser Rolle |
| `data/raw/crawled_urls.txt` | 5.612.907 B, git-getrackt | Rohdatum des Scrapes |
| `revision/snapshots/`, `references/specs/`, `revision/*.md` | — | Belegebene der Revision |
| `models/archive_2024-12-02_published/` | Verzeichnis | publizierter Vergleichsstand (`open_questions.md:415-417`) |
| `models/leftovers/`, `reports/figures/{leftovers,v1,v2}/` | Verzeichnisse | nicht regenerierbar |

### 12.2 Die vier Diagnostik-Parquets

| Parquet | Größe | freigebbar nach Überführung von |
|---|---|---|
| `data/interim/pfd_mainspec_frame2.parquet` | 16.069.902 B | **A8** (und damit A5b, A7, A9, A10, A13) |
| `data/interim/pfd_flb_continuous.parquet` | 8.807.145 B | **A13** |
| `data/interim/pfd_sharp_frame.parquet` | 12.555.985 B | **A5a + A5b** |
| `data/interim/pfd_flb_frame.parquet` | 4.529.996 B | **A12 + A14** |

### 12.3 Von „regenerierbar" auf „geschützt" gewechselt

| Datei | trägt welche Reply-Stelle | geschützt bis |
|---|---|---|
| `revision/snapshots/C_normalized/wide_imputed.h5` | Eingang von A21 | **A21** |
| `revision/snapshots/C1_refactor/wide_imputed.h5` | Eingang von A21 (`RAW`) | **A21** |
| `revision/snapshots/C_normalized/beta1_curve.csv` | Eingang von A3 und A11 | beide entfallen → freigebbar, sobald `tab:r1c2` Zeile 4 und `reply:333` umgeschrieben sind |
| `revision/snapshots/E_gmm_exponent_fix/gmm_by_bookie.csv` | γ-Referenz von A5a | **A5a** |
| `revision/snapshots/A_baseline/table5_res_wp.csv` | Raw-Spalte `tab:r1c1`, Zeilen 2 und 13 | **A1** |
| `revision/snapshots/compare_2x2.csv` | „Spearman 0.992" in `tab:r1c1` | **A1** |
| `revision/snapshots/rmse_baselines/opening_vs_closing.csv` | `reply:391` Brier-Teil | **A20** |
| `revision/snapshots/rmse_baselines/posting_time_by_bookie.csv` | Figure-1-Vorlage (1.11) | **A1 + 1.11** |
| `revision/snapshots/flb_calibration/gmm_by_group.csv` | `reply:391` J-Test | **A21** |
| `revision/snapshots/continuous_unbiasedness/main_spec/ns4_*.csv` | `fig:r1c7new`, `tab:r1c7`, `reply:333-342` | **A8** |
| `revision/snapshots/eq3_contract_level/ladder*.csv`, `logit_check.csv`, `cluster_robust.csv` | `tab:r2c1` | **A15** |
| `revision/snapshots/censoring/*.csv` | `tab:r1c5`, `tab:r1c5b`, `reply:263` | **A6 + A7** |
| `revision/snapshots/flb_calibration/calibration_*.csv`, `continuous_calibration_grid.csv`, `bias_by_decile.csv` | `tab:r1c8`, `fig:r1c8`, `reply:382` | **A12 + A13 + A14** |
| `revision/snapshots/cluster_inference_eq12/*.csv` | `tab:r1c2` Eq. 1/Eq. 2, Wald-Tests | **A2** |
| `revision/snapshots/gmm_rasterfree/support_shift_gamma.csv` | Kontrollpunkt γ̄ = 0,003474 | **dauerhaft** — Referenz des Kontrollpunkts |
| `revision/snapshots/gmm_rasterfree/favlong_by_spec.csv` | `reply:391`, `:484` | **A17** |
| `revision/snapshots/sharp_soft/margin_by_bookie.csv`, `gmm_without_sharp.csv`, `beta1_without_sharp.csv` | `tab:r1c4`, `tab:r1c4b` | **A4 + A5a + A5b** |
| `data/processed/timestamps.h5` | speist `crawling_process.pdf` | solange `shape_data()` nicht läuft |

---

## 13. Reihenfolge der Überführung

Kriterium: nach jedem Schritt besteht ein lauffähiger Zustand.

### Schritt 0 — Streichungen im Reply vollziehen
**Überführt:** nichts. **Entfernt:** `fig:r1c7pub` (`reply:346-348`), der
Vergleich in `reply:484`, `tab:r1c2` Zeile „Unbiasedness (Fig. 3)" samt
`reply:338`; `reply:333` wird nach 6.1 ersetzt, der Restsatz in `reply:484`
nach 6.2 umformuliert.
**Freigegeben:** `C_normalized/beta1_curve.csv`, `published_unbiased_reg.pdf`.
**Vollständiger Lauf nötig:** nein. **Isoliert testbar:** ja.

### Schritt 1 — Objekt 1 und Objekt 2 anlegen
**Überführt:** `filter_and_shape.py:155-164` um `Date` erweitert,
`HoursToKick`/`X` bei `:101-104`; `bookmaker_accuracy.py` gibt die
ungefilterte `df_oc`-Variante zusätzlich zurück (zwischen `:85` und `:88`).
**Danach belegt:** nichts Neues — Infrastruktur.
**Vollständiger Lauf nötig:** nein, `pre` genügt. **Isoliert testbar:** ja —
Spaltenbestand und Zeilenzahlen gegen `flb_calibration/README.md:4-6`
(184.415) und `continuous_unbiasedness/README.md` (184.012 / 175.166).

### Schritt 2 — A6, A1, A4
**Überführt:** Zensierungskette; Overround in `filter_and_shape.py:118`;
RMSE-Rangfolge auf Serienebene; Margen je Bookmaker; Teildurchgang
`normalize=False` (7.2).
**Danach belegt:** `tab:r1c1` vollständig, `tab:r1c4`, `tab:r1c5`,
`reply:263` Teil 1.
**Freigegeben:** `A_baseline/table5_res_wp.csv`, `compare_2x2.csv`,
`posting_time_by_bookie.csv`.
**Vollständiger Lauf nötig:** nein, `pre`. **Isoliert testbar:** ja.

### Schritt 3 — A16, A17, A5a
**Überführt:** γ̄ als Produktionsergebnis; γ je `IsFav`-Teilmenge;
Aggregation ohne Pinnacle/BetInAsia.
**Danach belegt:** `reply:484` Restsätze, `reply:391` γ-Teil, `tab:r1c4b`
Zeile „Learning rate".
**Freigegeben:** `E_gmm_exponent_fix/gmm_by_bookie.csv`,
`favlong_by_spec.csv`.
**Vollständiger Lauf nötig:** **ja** — `pre` + `wide` + `gmm`. Resample
≈ 670 s, GMM 10–16 s je Durchgang.
**Isoliert testbar:** Kontrollpunkt γ̄ = 0,003474.

### Schritt 4 — A8, dann A9, A10
**Überführt:** `unbiasedness_regressions.py` auf `ns(df=4)`,
Cluster-Bootstrap B = 100, sup-t; RMSE-Bins; gepaarter Brier.
**Danach belegt:** `fig:r1c7new`, `tab:r1c7`, `reply:334-342`, Ersatz für
`reply:333`.
**Freigegeben:** `pfd_mainspec_frame2.parquet`, `main_spec/ns4_*.csv`.
**Vollständiger Lauf nötig:** nein, `pre`.
**Isoliert testbar:** ja, gegen `ns4_marks.csv` (1,1728 / 0,9245 / 0,7763),
`global_tests.csv` (sup-\|t\| 2,5089, crit 2,6166) und `ns4_final_counts.csv`
(45/0/96 bzw. 38/0/96).
**Laufzeit:** 58 s je Fit; B = 100 sequentiell ≈ 1,6 h. **Hier wird das
fehlende Teil-Checkpointing zuerst spürbar (14.3).**

### Schritt 5 — A7, A5b
**Überführt:** β₁ ohne Filter und Schwellenleiter; β₁ ohne
Pinnacle/BetInAsia.
**Danach belegt:** `tab:r1c5b`, `reply:263` Teil 2, `tab:r1c4b` β₁-Zeilen.
**Freigegeben:** `pfd_sharp_frame.parquet`, `censoring/beta1_*.csv`,
`sharp_soft/beta1_without_sharp.csv`.
**Vollständiger Lauf nötig:** nein, `pre`. **Isoliert testbar:** ja.

### Schritt 6 — A12, A13, A14, A20
**Überführt:** Kalibrierung Opening/Closing, λ(X), Dezilabweichungen,
gepaarter Opening/Closing-Brier.
**Danach belegt:** `tab:r1c8`, `fig:r1c8`, `reply:382`, `reply:391`
Brier-Teil.
**Freigegeben:** `pfd_flb_frame.parquet`, `pfd_flb_continuous.parquet`,
`flb_calibration/calibration_*.csv`, `bias_by_decile.csv`,
`rmse_baselines/opening_vs_closing.csv`.
**Vollständiger Lauf nötig:** nein, `pre`. **Isoliert testbar:** ja, gegen
`calibration_slopes.csv` (1,1155 / 1,1131) und `opening_vs_closing.csv`
(Vorzeichen, O-A20).

### Schritt 7 — A2, A15
**Überführt:** Cluster-Inferenz Eq. 1/Eq. 2 mit Varianzzerlegung und
Wald-Tests; Eq. 3 auf Kontraktebene mit Logit-Check.
**Danach belegt:** `tab:r1c2` Zeilen Eq. 1/Eq. 2/Eq. 3, `tab:r2c1`,
`reply:208` Wald-Tests, `reply:439-458`.
**Freigegeben:** `cluster_inference_eq12/*.csv`, `eq3_contract_level/*.csv`.
**Vollständiger Lauf nötig:** nein, `pre`. **Isoliert testbar:** ja, gegen
`eq3_contract_level/ladder_cluster.csv` (WSL-Reproduktion mit schlechtester
relativer Abweichung 1,6e−12, `baseline_status.md:221-232`).

### Schritt 8 — A21
**Überführt:** GMM auf den zehn Opening-Preis-Dezilen unter V2|B, **neu
spezifiziert**.
**Danach belegt:** `reply:391` J-Test-Aussage.
**Freigegeben:** `C_normalized/wide_imputed.h5`,
`C1_refactor/wide_imputed.h5`, `flb_calibration/gmm_by_group.csv`.
**Vollständiger Lauf nötig:** **ja** — braucht den Wide-Frame.
**Isoliert testbar:** nein; ein V2|B-Sollwert existiert nicht (O-A21).

### Schritt 9 — A18 Scrape-Lag
**Überführt:** Lag-Rechnung in `shape_data.py` nach `:90`, Ausgabe
`scrape_lag.csv` und zwei `\var{}`-Schlüssel.
**Danach belegt:** `reply:93`.
**Freigegeben:** nichts — `crawled_odds.json` bleibt dauerhaft geschützt.
**Vollständiger Lauf nötig:** nein, aber ein Durchlauf über
`crawled_odds.json`, der `shaped_data.h5` nicht neu schreibt (8.4).
**Isoliert testbar:** nein — es existiert keine Vergleichsdatei.

### Schritt 10 — Bayesian
**Überführt:** nichts Neues; der Block läuft unverändert auf dem
V2|B-Wide-Frame.
**Danach belegt:** die sieben Bayesian-`\var{}`-Werte im Papertext.
**Vollständiger Lauf nötig:** **ja**, 13–25 h auf dieser Maschine bzw.
1–3 h auf der 32-vCPU-Maschine (`baseline_status.md:159-170`).

**Parallelität:** Schritt 3 und 8 brauchen den Wide-Frame, alle übrigen
nicht. Schritte 4–7 hängen an Schritt 1; Schritte 5 und 6 zusätzlich an
Schritt 4 (gemeinsame Spline-Basis, `sharp_soft/README.md:66-68`,
`_r1c8_figure.py:4-7`). Zwischen dem Bootstrap aus Schritt 4 (3,39 GB je
Prozess) und dem Bayesian-Block aus Schritt 10 besteht ein Speicherkonflikt
gegen 11,4 GB verfügbar.

---

## 14. Lauf: Vorbereitung, Laufzeit, Checkpoint

### 14.1 Vorbereitung

| # | Schritt |
|---|---|
| V1 | V-O5, V-O7, V-O8, V-O9, V-1.12 **verifizieren** |
| V2 | Codeänderungen 1.3, 1.4, 1.5 einspielen; Überführungen nach Abschnitt 13; 1.6, 1.7, 1.13 verifizieren |
| V3 | `reports/values/values.dat` **löschen** (1.6) |
| V4 | `data/interim/ckpt_*.pkl` und `models/trace_*.nc.ckpt` aus früheren Läufen entfernen — der Sentinel-Mechanismus (`gen_res_obj.py:83-92`) schützt nur, solange keine Sentinels einer anderen Spezifikation liegen bleiben |
| V5 | Einstiegspunkt klären (14.2) |
| V6 | `data/processed/shaped_data.h5` unangetastet lassen |

### 14.2 Einstiegspunkt

**Der reguläre Einstiegspunkt ist `python -m pfd`**, `src/pfd/__main__.py`.
Er ruft in `:39-41` sequentiell `shape_data()`, `run_estimation()`,
`create_descriptives()`. `pyproject.toml` enthält keinen
`[project.scripts]`-Eintrag; das `Makefile` deckt nur `sync`, `lint`,
`format`, `typecheck`, `test` ab.

Was fehlt, damit der Lauf darüber statt über
`revision/snapshots/eq_window_scope/_run_v2b.py` startet:

1. **`shape_data()` läuft mit** und schriebe `shaped_data.h5` neu
   (`__main__.py:39`); es gibt keinen Schalter, der den Schritt überspringt.
2. **Arbeitsverzeichnis.** `config.yaml:48-57` verwendet relative Pfade
   (`../../../data/`); `Paths.__post_init__` (`config.py:99-102`) wirft
   `ValueError: Invalid path`, wenn sie nicht auflösen. `_run_v2b.py` setzt
   deshalb `os.chdir(f"{REPO}/src/pfd/models")`. Die absolute Variante steht
   auskommentiert in `config.yaml:38-47` mit `# TODO`.
3. **Hydra-Overrides.** `hydra.job.chdir=false` und
   `estimation.checkpoint=true` werden von `_run_v2b.py` über `sys.argv`
   gesetzt (`:22-26`).
4. **Config-Pfad.** `__main__.py:26` nutzt `config_path="conf"`,
   `run_estimation.py:47` nutzt `config_path="../conf"`.

Solange 1.–3. nicht geregelt sind, ist `_run_v2b.py` der einzige belegte
Startweg. Ob der Lauf über den regulären Einstieg geführt wird: **nicht
belegbar entschieden**.

### 14.3 Laufzeit und Checkpoint

| # | Phase | `run_phase` | Inhalt | Laufzeit | Beleg |
|---|---|---|---|---|---|
| 1 | pre | `"pre"` | filter/accuracy/winprops **plus** A1, A2, A5b, A6, A7, A8, A9, A10, A12, A13, A14, A15, A20 | Grundlast in der ~19-min-Schätzung; **plus Bootstrap** | `E_gmm_exponent_fix/MANIFEST.md` |
| 1a | — | — | Cluster-Bootstrap B = 100 (A8) | 58 s je Fit → sequentiell ≈ **1,6 h**; zwei Prozesse ≈ 0,8 h; 3,39 GB je Fit | `main_spec/README.md:316-319` |
| 2 | wide | `"wide"` | serieneigenes Resampling, Pivot | **≈ 670 s** | `eq_window_scope/README.md`, Abschnitt 4 |
| 3 | post | `"post"` | entfällt: ADF/GARCH gestrichen (1.3), Unbiasedness nach `_pre` verschoben (1.9) | — | |
| 4 | gmm | `"gmm"` | CUE + First Stage, plus A5a, A17, A21 | **10–16 s** je Durchgang | `eq_window_scope/README.md` |
| 5 | bayesian | `"bayesian"` | 1 ADVI + 15 NUTS | **13–25 h** hier; **1–3 h** auf 32 vCPU | `baseline_status.md:159-170` |

**Gesamtlaufzeit `pre`: nicht belegbar.** Belegt ist allein die untere
Schranke aus dem Bootstrap.

Kalibrierung des Bayesian-Blocks (`baseline_status.md:159-165`):
nutpie-Kompilierung 101 s je Lauf (16 Läufe), NUTS 1,537 ms/Iteration, ADVI
158 ms/Iteration; 4 Ketten, 2.000 tune, 5.000 draws, 25.000
ADVI-Iterationen; Speicher ~1,6 GB gegen 11,4 GB.

**Wo `estimation.checkpoint` greift.** Default `False` (`config.yaml:18`);
`_run_v2b.py` setzt `true`. Der Schalter steuert ausschließlich Schreiben und
Lesen, nie das Gerechnete (`checkpoint.py:6-10, 50-51`).

| Ebene | Wo | Datei | Verhalten |
|---|---|---|---|
| **Phase** | `run_estimation.py:110, 112, 136, 140, 163` | `data/interim/ckpt_{pre,wide,post,gmm,bayesian}.pkl` | Liegt die Datei, wird geladen (`checkpoint.py:55-58`). Schreiben über `.tmp` + `os.replace` (`:63-72`); unpicklebares Ergebnis → Fragment gelöscht, `RuntimeError` (`:73-80`) |
| **Einzelner NUTS-Lauf** | `gen_res_obj.py:88-92, 111-115` | `models/trace_nuts_<subset>.nc` + Sentinel `.nc.ckpt` | Wiederaufnahme keyt auf den **Sentinel**, nicht die `.nc`-Datei (`:83-87`) |

**Fehlende Checkpoints:**

| Lücke | Konsequenz |
|---|---|
| **Cluster-Bootstrap B = 100 (A8)** | liegt in `_pre`; ein Abbruch nach 80 Replikaten verwirft alle 100. Die Diagnostikfassung löst das über getrennte Teilausgaben je `part` (`ns4_bootstrap_part{0,1}.csv`, `…_beta1_part{0,1}.npy`); eine Entsprechung in der Pipeline existiert nicht |
| **`_pre` insgesamt** | wächst von Minuten auf mindestens 1,6 h und wird als **ein** Block gecheckpointet |
| **Die R-Fits** (A2, A5b, A7, A8, A12, A13, A15) | jeder ein eigener teurer Schritt ohne Wiederaufnahmepunkt |
| **Frame-Aufbau** | der Long-Frame (9.1) wird heute als Parquet gecacht und dadurch faktisch gecheckpointet; `_ns_bootstrap.py:34-36` begründet den Ablageort ausdrücklich damit |
| **Fork-Sicherheit** | „R ist nach der Initialisierung nicht fork-sicher" (`_ns_bootstrap.py`, Docstring); Parallelisierung nur über getrennte Prozesse, was eigene Teilausgaben verlangt |
| **ADVI** | nicht sentinelgeschützt (`gen_res_obj.py:62-75`); wird bei jedem Wiederanlauf der Phase neu gerechnet, solange `ckpt_bayesian.pkl` fehlt |

**Warum Checkpointing nicht optional ist:** die WSL-VM startet gelegentlich
neu und nimmt abgekoppelte Läufe mit; `vmIdleTimeout=3600000` hat das nicht
verlässlich behoben.
