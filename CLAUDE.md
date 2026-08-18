# pfd — Revision JRSSA-Mar-2026-0082

Paper: „Price Formation Dynamics and Learning in the Tennis Sports Betting
Market". Branch `revision-jrssa`.

## Übergeordnete Vorgabe

**Papertext UND Antwortdokument werden vollständig aus der Code-Pipeline
gespeist.** Keine Zahl, keine Tabelle und keine Abbildung darf aus einem
Snapshot-Skript oder einem vorgehaltenen Zwischenframe stammen. Keine
Referenzklasse: eingefrorene Vorher-Zahlen aus `revision/snapshots/` tragen
keine Aussage mehr.

Einzige Ausnahme: `data/processed/shaped_data.h5` (Nov 2024) und die daraus
hervorgegangene Quelle `data/raw/crawled_odds.json` bleiben Eingang, weil der
Scrape nicht wiederholbar ist.

## Aktive Spezifikation

| Element | Stand |
|---|---|
| Preise | margin-bereinigt, auf Summe 1 normalisiert (`p_home/(p_home+p_away)`) |
| Imputation | entfällt vollständig |
| Zeitraster | serieneigen je `GroupId`, eigenes Opening bis eigener Schlusspreis |
| GMM-Stützstellen | 50/45/40/35/30 plus `OddsMvt0` |
| Zerfallsfaktor | τ = [51, 46, 41] |
| Unbiasedness | kontinuierliche absolute Achse, `ns(df=4)` in `log(Stunden bis Anpfiff)`, cluster-robust auf Matchup, Bootstrap B = 100, sup-t-Band |
| GMM/Bayesian | diskrete relative Perzentil-Achse |
| Eq. 3 | Kontraktebene, LPM als Hauptspezifikation, Logit als Robustheit |
| RMSE-Aggregation | einheitlich Serienebene |
| ADF/GARCH, Figure 6, `corr_gamma_loss` | gestrichen |

**Kontrollpunkt bei jedem Neulauf: γ̄ = 0,003474**
(`revision/snapshots/gmm_rasterfree/support_shift_gamma.csv`, Spalte
`V2 serieneigen | B`). Optimierer Nelder-Mead und der feste Startwert 0,01
bleiben unverändert — sonst verliert der Kontrollpunkt seine Referenz.

## Arbeitsregeln

- **`revision/RUN_SPEC.md` ist die verbindliche Laufspezifikation.** Dort
  stehen die gesetzten Entscheidungen, die offenen Punkte, der Artefaktplan,
  die Schutzliste und die Überführungsreihenfolge Schritt 0–10.
- Jede Zahl im Antwortdokument muss aus einem committeten Snapshot stammen.
- `reports/values/values.dat` vor jedem Lauf **löschen**, nicht
  überschreiben: `save_values.py` aktualisiert Schlüssel nur, entfernt sie
  nie.
- Abbildungen sind gitignoriert. Je Abbildung gehören die erzeugende CSV und
  ein sha256-Eintrag in den Snapshot.
- Lange Läufe nur mit `estimation.checkpoint=true`.
- `revision/reply1_20260728.tex` ist das aktive Antwortdokument.
  `reply1_20260808.tex` nicht anfassen. Eigene Antworten mit `\ReplyMN{}`;
  ersetzte Entwürfe des Kollegen bleiben auskommentiert stehen.
- Kompilieren nach `.build/`, PDF danach ins `revision/` kopieren.

## Dokumentation

| Datei | Zweck |
|---|---|
| `revision/RUN_SPEC.md` | **verbindliche Laufspezifikation** |
| `revision/reviewer_tracker.md` | ein Kommentar pro Zeile, Status |
| `revision/revision_log.md` | Chronik je Kommentar, Entscheidungsgeschichte |
| `references/specs/open_questions.md` | technische Befunde, offene Punkte |
| `revision/baseline_status.md` | Baseline, Tags, Arbeitsumgebung |
| `revision/snapshots/*/README.md` | je Diagnostik: Frage, Design, Ergebnis |

## Technische Umgebung

Das Projekt läuft **nur in WSL2 Ubuntu**, nicht in Windows: dort fehlen `uv`
und R, und das System-Python ist 3.8.

- venv: **`~/.venvs/pfd`** (ausserhalb von OneDrive). Neu:
  `export UV_PROJECT_ENVIRONMENT=$HOME/.venvs/pfd; uv sync --frozen`
- R 4.6.1 mit `lme4` und `mgcv`, rpy2 3.6.7. R ist nach der Initialisierung
  **nicht fork-sicher** — Parallelisierung nur über getrennte Prozesse.
- Ein venv im Projektordner erscheint von Windows aus als **0-Byte-Dateien**
  (Linux-Symlinks) — das ist kein Defekt, nicht „reparieren".
- **Die WSL-VM startet gelegentlich neu** und nimmt abgekoppelte Läufe mit;
  `vmIdleTimeout=3600000` hat das nicht verlässlich behoben.
- Speicher 11,4 GB. Der Cluster-Bootstrap braucht 3,39 GB je Prozess und darf
  sich nicht mit dem Bayesian-Block überlappen.

Lauf starten: `revision/snapshots/eq_window_scope/_run_v2b.py` (nur
`run_estimation`, lässt `shaped_data.h5` unberührt). Der reguläre
Einstiegspunkt `python -m pfd` ist noch nicht nutzbar — Begründung in
`RUN_SPEC.md`, Abschnitt 14.2.

## Geprüft und verworfen

Nur als Notiz, damit es nicht erneut aufgerollt wird — Belege in den
Snapshots:

- **Variante 3** (`TsStart` serieneigen, `TsEnd` matchweit): löst nichts,
  26,05 % von `OddsMvt46` bleiben fortgeschrieben. → `eq_window_scope/`
- **Freies K** in der Momentbedingung: bei kleinem γ nicht identifiziert,
  γ entgleist auf 2,6 gepoolt, J verschlechtert sich. → `gmm_rasterfree/`
- **Log-lineare rasterfreie Schätzung**: unterstellt ebenfalls K = 0 und
  verzerrt γ nach unten. → `gmm_rasterfree/_prep.py`
- **Bayesian-Heterogenität** (`sd_gamma` = 0,0077 gegen frequentistisch
  I² = 0 %): als offener Widerspruch vermerkt, nicht weiterverfolgt.
