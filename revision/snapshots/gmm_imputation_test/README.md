# GMM gegen die Imputation testen (Masking-Design, analog zu β₁)

Rein diagnostisch, **kein Eingriff in die Produktions-Pipeline**. Vergleichsbasis
ist die normalisierte Baseline (Tag `revision-baseline`, Stufe `C_normalized`).

## Frage

Der Masking-Test in `../continuous_unbiasedness/` (Nachtrag 2) hat gezeigt, dass
der β₁(t)-Verlauf weitgehend ein Imputationsartefakt ist. Gilt dasselbe für die
GMM-Lernrate γ?

Zusatzfrage: `OddsMvt0` ist eine der sechs Stützstellen in `_create_gmm_data`
und zu 86 % imputiert. Wie viel von γ hängt an dieser Stützstelle?

## Design

Dieselben **24.568 vollständig beobachteten Serien** wie im β₁-Masking-Test,
dieselbe Maskierung (Seed 42, Blocklängen aus der empirischen Verteilung der
Spät-Eröffner), derselbe Produktions-Imputer (`impute_missings`, ohne `Match`).
Kontrolle gegen den committeten Test: RMSE 0,09089, Bias −0,00145,
corr 0,9128 — identisch, die Stichprobe ist bit-gleich rekonstruiert.

115.104 maskierte Zellen (9,19 %), Blocklänge Median 2, Mittel 4,7, Max 42.

Vier CUE-Schätzungen auf **denselben** Serien:

| | Frühwerte | 6. Stützstelle |
|---|---|---|
| **A** | echt | `OddsMvt0` |
| **B** | maskiert + imputiert | `OddsMvt0` |
| **C** | echt | `OddsMvt21` |
| **D** | maskiert + imputiert | `OddsMvt21` |

`A→B` = Imputationseffekt. `C→D` = derselbe Effekt, aber ohne die imputierte
Stützstelle. Die Stützstelle wird getauscht, indem die Spalte `OddsMvt0`
überschrieben wird — das ist die einzige Stelle, an der `_create_gmm_data` sie
liest (`exog_list[5]`); alles andere bleibt unberührt.

Schätzereinstellungen exakt wie die Baseline: `n_per=51`, `incr=5`,
`max_iter="cue"`, Startwert 0,01. **Reproduktionskontrolle**: derselbe Harness
auf dem Produktions-Frame reproduziert `C_normalized/gmm_by_bookie.csv` auf
max |Δγ| = 7,6e−17.

### Das Masking-Design trifft die echten Imputationsraten

| Stützstelle | maskiert (Design) | imputiert (Produktion) |
|---|---:|---:|
| `OddsMvt0` | 100,00 % | 85,95 % |
| `OddsMvt21` | 3,26 % | 2,79 % |
| `OddsMvt26` | 1,60 % | 1,42 % |
| `OddsMvt31` | 0,58 % | 0,53 % |
| `OddsMvt36` | 0,15 % | 0,13 % |
| `OddsMvt41` | 0,01 % | 0,01 % |
| `OddsMvt46` | 0,00 % | 0,00 % |

Nur `OddsMvt0` ist stark imputiert (Design 100 % statt 86 %, weil jede
Blocklänge ≥ 1 die Zelle 0 trifft — der Test ist an dieser Stelle also
*strenger* als die Realität).

## Je Bookmaker: die Teilstichprobe ist zu klein

Die 24.568 Serien verteilen sich mit **n = 117 bis 4.530** auf die 24
Bookmaker. Die per-Bookmaker-Schätzungen sind entsprechend instabil: γ liegt
im Bereich **[−0,145, +0,139]** mit 4 negativen Werten, gegenüber
**[0,004, 0,072]** in der Baseline. Auf dieser Basis ist kein
per-Bookmaker-Vergleich belastbar.

Der Imputationseffekt je Bookmaker (`B−A`) hat Median −0,0010 bei
11 positiven / 13 negativen Vorzeichen; der Mittelwert +0,0048 wird von einem
einzigen Ausreißer getragen (BetInAsia +0,0974, dessen A-Schätzung −0,0485
ist). **Kein systematischer Effekt, nur Rauschen.**

Deshalb ist unten die **gepoolte** Schätzung die belastbare Zahl. Details je
Bookmaker in `gmm_masking_gamma_compare.csv`.

## Ergebnis: γ ist robust — im Gegensatz zu β₁

Gepoolt (n = 24.568):

| | γ | vs. A |
|---|---:|---:|
| A echt / `OddsMvt0` | 0,0305 | – |
| B imputiert / `OddsMvt0` | 0,0435 | +0,0130 |
| C echt / `OddsMvt21` | 0,0310 | +0,0005 |
| D imputiert / `OddsMvt21` | 0,0423 | – |

Zum Vergleich: γ echt (0,0305) liegt praktisch auf der Baseline (0,0320).

### Die Stützstelle `OddsMvt0` trägt praktisch nichts

Drei unabhängige Wege, alle mit demselben Ergebnis:

1. **Tausch auf dem vollen Produktions-Frame** (183.210 Serien, 24 Bookmaker,
   `gmm_baseline_support_swap.csv`): mittleres γ **0,0320 → 0,0325**
   (+0,0005, **+1,5 %**). Deltas je Bookmaker in [−0,0043, +0,0123],
   9 positiv / 15 negativ. J-Test-Verwerfungen unverändert 1 von 24.
2. **Tausch auf echten Daten** (C−A): gepoolt +0,0005, je Bookmaker
   Mittel −0,0013.
3. **Der reine `OddsMvt0`-Kanal**: bei Blocklänge = 1 (n = 9.502) ist
   *ausschließlich* `OddsMvt0` imputiert. Dort ist `B−A = +0,0002`.

### Warum — und warum β₁ anders reagiert

Strukturell: `OddsMvt0` geht in `_create_gmm_data` nur als `exog_list[5]` ein
und wird allein im Instrument `OddsMvt26 − OddsMvt0` (und dessen Quadrat)
verwendet. Die Momentbedingungen selbst (`_gen_meth_mom.momcond`) benutzen
`OddsMvt46/41/36` — zu 0–0,15 % imputiert. In der Unbiasedness-Regression
steht `OddsMvt0` dagegen auf **beiden** Seiten (Endog = `Match − OddsMvt0`,
Exog = `OddsMvt_t − OddsMvt0`) und hat dadurch massive Hebelwirkung.

Das deckt sich mit dem bereits dokumentierten Befund, dass der Look-ahead-Fix
γ nur um 8,9e−5 bewegt hat, den β₁-Pfad aber material.

## Der verbleibende gepoolte Versatz von +0,0130 ist Hebelwirkung, nicht Stützstelle

`D−C` (+0,0113) ist fast so groß wie `B−A` (+0,0130), obwohl in Spec D kaum
eine Stützstelle imputiert ist. Aufgelöst über die Blocklänge
(`gmm_masking_by_blocklength.csv`):

| Blocklänge | n | `B−A` | `D−C` |
|---|---:|---:|---:|
| 1 (nur `OddsMvt0`) | 9.502 | +0,0002 | **0,0000** |
| 2–5 | 8.658 | −0,0007 | **0,0000** |
| 6–21 | 5.608 | +0,0025 | **0,0000** |
| ≥ 22 (auch `OddsMvt21`) | 800 | −0,0515 | −0,0575 |
| alle | 24.568 | +0,0130 | +0,0113 |

Zwei Kontrollen stützen die Lesart:

- Der Imputer lässt beobachtete Zellen **bit-identisch** (max |Δ| = 0,00e+00).
  Eine Serie kann γ also nur über ihre maskierten Zellen bewegen.
- **Falsifikationsprobe bestanden**: `D−C` ist bei Blocklänge ≤ 21 in jedem
  Bin **exakt 0,0000** — wenn keine Stützstelle imputiert ist, kann die
  Imputation γ nachweislich nicht bewegen. Das validiert das ganze Design.

γ ist über Teilstichproben nicht additiv, deshalb direkt geprüft
(`gmm_masking_influence.csv`):

| Teilstichprobe | n | γ echt | γ imputiert | Diff |
|---|---:|---:|---:|---:|
| alle | 24.568 | 0,0305 | 0,0435 | +0,0130 |
| **ohne Blocklänge ≥ 22** | 23.768 | 0,0328 | 0,0331 | **+0,0002** |
| nur Blocklänge ≥ 22 | 800 | −0,0266 | −0,0781 | −0,0515 |

**Der gesamte gepoolte Versatz wird von 3,3 % der Serien getragen.** Auf den
übrigen 96,7 % ist der Imputationseffekt auf γ +0,0002, also null. Diese 800
Serien sind die, deren Imputation bis in die Stützstellen hineinreicht; ihr
eigenes γ verschiebt sich um −0,05, im gepoolten Fit hebeln sie γ aber um
+0,013 nach oben.

## Fazit

γ ist gegen die Imputation robust — **anders als β₁**, dessen Verlauf der
Masking-Test als Imputationsartefakt entlarvt hat. Die Ursache ist strukturell:
die stark imputierte Stützstelle `OddsMvt0` betritt das GMM nur über ein
Instrument, nicht über die Momentbedingungen.

## Einschränkungen

- Wie beim β₁-Masking-Test sind die Kandidaten **früh eröffnende Bookmaker**
  (14 % der Serien). Extrapolation auf Spät-Eröffner ist plausibel, aber nicht
  gezeigt.
- Die per-Bookmaker-Schätzung ist auf dieser Teilstichprobe **nicht**
  belastbar (n ab 117, γ teils negativ). Belastbar ist die gepoolte Zahl plus
  der Stützstellen-Tausch auf dem vollen Frame.
- Die Hebelwirkung der lang-imputierten Serien ist ein Befund über den
  **gepoolten** Fit. Die publizierte Schätzung läuft je Bookmaker; dort bewegt
  der Stützstellen-Tausch auf dem vollen Frame γ um +1,5 %. **Offen (nicht
  geprüft):** dieselbe Trimmung — Serien verwerfen, deren imputierter
  Führungsblock über Zelle 21 hinausreicht — auf dem Produktions-Frame je
  Bookmaker. Kostet einen Rebuild des Prä-Imputations-Frames.

## Dateien

- `gmm_masking_by_bookie.csv` – alle vier Specs je Bookmaker, Rohausgabe
  (γ, SE, J-Statistik, p-Wert, n)
- `gmm_masking_gamma_compare.csv` – γ-Vergleichstabelle inkl. `B−A`, `D−C`, `C−A`
- `gmm_baseline_support_swap.csv` – Stützstellen-Tausch auf dem vollen
  Produktions-Frame, je Bookmaker
- `gmm_masking_by_blocklength.csv` – Zerlegung nach Blocklänge
- `gmm_masking_influence.csv` – Einflussprobe (mit/ohne Blocklänge ≥ 22)
- `_step1.py` … `_step5.py` – Reproduktionsskripte (Reihenfolge = Nummer;
  `_step1.py` baut den Cache, den 2/4/5 lesen, `_step3.py` ist unabhängig)
