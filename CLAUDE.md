# pfd — Revision JRSSA-Mar-2026-0082

Paper: „Price Formation Dynamics and Learning in the Tennis Sports Betting
Market". Diese Datei beschreibt den **aktuellen Stand**, nicht den Weg dahin.

## Aktive Spezifikation

Branch `revision-jrssa`. Gegenüber der eingereichten Fassung gilt:

| Element | Stand |
|---|---|
| Preise | margin-bereinigt, auf Summe 1 normalisiert (`p_home/(p_home+p_away)`) |
| Imputation | **entfällt vollständig** |
| Zeitraster | **serieneigen**: eigenes Opening bis eigener Schlusspreis, je `GroupId` |
| GMM-Stützstellen | **50/45/40/35/30** plus `OddsMvt0` |
| Zerfallsfaktor | τ = [51, 46, 41], aus den tatsächlichen Stützstellenpositionen |
| Inferenz | cluster-robust auf Matchup (Eq. 1–3, Unbiasedness); Eq. 2 zweiweg |
| Eq. 3 | auf **Kontraktebene**, binärer Ausgang, Opening-Preis als Kovariate |
| Unbiasedness | kontinuierliche absolute Achse, `log(Stunden bis Anpfiff)` |
| GMM/Bayesian | bleiben auf der diskreten relativen Perzentil-Achse |

Kernzahlen: γ̄ = **0,003474** (24 Bookmaker), Favoriten 0,005531 gegen
Longshots 0,001181 (t = 4,49). Eq. 3 Kontraktebene: η₁ = 1,125, η₂ = 0,956.

**Kontrollpunkt bei jedem Neulauf:** γ̄ muss 0,003474 treffen. Bei `incr = 1`
fallen alte und neue Stützstellen-Indexierung exakt zusammen — das ist der
Rückwärtskompatibilitätsanker.

## Dokumentation

| Datei | Zweck |
|---|---|
| `revision/reviewer_tracker.md` | Übersicht: ein Kommentar pro Zeile, Status |
| `revision/revision_log.md` | Chronik je Kommentar: Stand → Untersuchung → Entscheidung → Beleg |
| `references/specs/open_questions.md` | technische Befunde, offene Punkte |
| `revision/baseline_status.md` | Baseline, Tags, Arbeitsumgebung |
| `revision/snapshots/*/README.md` | je Diagnostik: Frage, Design, Ergebnis, Einschränkung |

Jede Zahl im Antwortdokument muss aus einem committeten Snapshot stammen.

## Antwortdokument

**`revision/reply1_20260728.tex`** ist das aktive Dokument.
**`reply1_20260808.tex` nicht anfassen.**

- Eigene Antworten mit `\ReplyMN{}` (ergibt die `[MN]`-Markierung).
- Entwürfe des Kollegen stehen als `\Reply{}`; werden sie ersetzt, bleiben
  sie auskommentiert stehen mit der Zeile
  „% Entwurf des Kollegen, durch die Antwort oben ersetzt (nicht geloescht):".
- Stil: knapp, konstruktiv, englisch; kurze Absätze. Erst die Sache, dann
  die Zahl. Prämissen des Reviewers höflich richtigstellen, wenn sie nicht
  stimmen.
- Kompilieren nach `.build/`, PDF danach ins `revision/` kopieren.

## Beantwortete Kommentare

AE-1 · R1-i · R1-ii · R1-iv · R1-v · R1-vi · R1-vii · R1-viii · R2-C1 · R2-C2

Offen im Papertext: Abstract („substantial heterogeneity across bookmakers"
ist nicht haltbar), `\var{}`-Werte `min/max/idxmin/idxmax_gamma_gmm`,
§3.5 (K-Annahme), §4/Anhang B (Imputation streichen), §5.5.

Die **K-Passage in der R1-vi-Antwort** („that error is zero by construction")
ist sachlich falsch und noch nicht überarbeitet — bewusst so belassen.

## Technische Umgebung

Das Projekt läuft **nur in WSL2 Ubuntu**, nicht in Windows: dort fehlen `uv`
und R, und das System-Python ist 3.8.

- venv: **`~/.venvs/pfd`** (ausserhalb von OneDrive). Neu:
  `export UV_PROJECT_ENVIRONMENT=$HOME/.venvs/pfd; uv sync --frozen`
- R 4.6.1 mit `lme4` und `mgcv`, rpy2 3.6.7
- Ein venv im Projektordner erscheint von Windows aus als **0-Byte-Dateien**
  (Linux-Symlinks) — das ist kein Defekt, nicht „reparieren".
- **Die WSL-VM startet gelegentlich neu** und nimmt abgekoppelte Läufe mit.
  `vmIdleTimeout=3600000` in `.wslconfig` hat es nicht verlässlich behoben.

**Lange Läufe deshalb immer mit Checkpointing:**
`estimation.checkpoint=true` (Default `false`). Phasen `pre/wide/post/gmm/
bayesian` liegen als `data/interim/ckpt_*.pkl`, Sampler-Läufe als
`models/trace_*.nc` mit `.ckpt`-Sentinel. Neustart überspringt Fertiges.
Der Schalter steuert **nur** Schreiben und Lesen, nie das Gerechnete.
Vorbehalt: ein wiederaufgenommener Lauf stellt den globalen NumPy-RNG nicht
wieder her — `bootstr_std` kann um bis zu ~0,0009 abweichen.

Lauf starten: `revision/snapshots/eq_window_scope/_run_v2b.py` (nur
`run_estimation`, lässt `shaped_data.h5` unberührt).

## Geprüft und verworfen

Nur als Notiz, damit es nicht erneut aufgerollt wird — Belege in den
Snapshots:

- **Variante 3** (`TsStart` serieneigen, `TsEnd` matchweit): löst nichts,
  26,05 % von `OddsMvt46` bleiben fortgeschrieben. → `eq_window_scope/`
- **Freies K** in der Momentbedingung: bei kleinem γ nicht identifiziert,
  γ entgleist auf 2,6 gepoolt, J verschlechtert sich. → `gmm_rasterfree/`
- **Log-lineare rasterfreie Schätzung**: unterstellt ebenfalls K = 0 und
  verzerrt γ nach unten; der Bodensatz `E[q(1−q)] ≈ 0,21` macht praktisch
  die ganze gemessene Grösse aus. → `gmm_rasterfree/_prep.py`
- **Bayesian-Heterogenität** (`sd_gamma` = 0,0077 gegen frequentistisch
  I² = 0 %): als offener Widerspruch vermerkt, nicht weiterverfolgt.
