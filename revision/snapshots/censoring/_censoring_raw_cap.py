#!/usr/bin/env python3
"""Ist die Kappung bei 20 Updates die Plattform oder unser eigener Filter?

Hintergrund: `README.md`, Abschnitt 2, schliesst aus `num_updates_distribution`
(Maximum 20, keine Serie darueber), die Kappung sei "die Signatur der
Datenquelle". Dieser Schluss war so nicht gedeckt: `shape_odds.py:104`
verwirft selbst alle Gruppen mit mehr als 21 Beobachtungen
(= mehr als 20 Updates). Im `shaped_data.h5` KANN deshalb per Konstruktion
nichts ueber 20 stehen -- das Argument war zirkulaer.

Dieses Skript prueft die Behauptung dort, wo sie pruefbar ist: im rohen
Scrape (`data/raw/crawled_odds.json`), vor jedem eigenen Filter. Jeder
Bookmaker-Eintrag hat die Form

    ODDS MOVEMENT \n <t_n> ... <t_1> \n <quoten> \n <deltas> \n
    Opening odds: \n <t_0> \n <quote>

Die Zahl der Zeitstempel vor "Opening odds" ist die Zahl der angezeigten
Updates.

Rein diagnostisch, nichts an der Produktions-Pipeline.
"""

import collections
import json
import re

import pandas as pd

RAW = "data/raw/crawled_odds.json"
OUT = "revision/snapshots/censoring"
STAMP = re.compile(r"\d{2} [A-Za-z]{3}, \d{2}:\d{2}")

cnt: collections.Counter = collections.Counter()
with open(RAW) as f:
    for line in f:
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        for side in ("OddsHome", "OddsAway"):
            for entry in rec.get(side, []) or []:
                if "Opening odds" not in entry:
                    continue
                head = entry.split("Opening odds")[0]
                cnt[len(STAMP.findall(head))] += 1

tot = sum(cnt.values())
d = pd.DataFrame({"n_updates": sorted(cnt)})
d["n_serien"] = d["n_updates"].map(cnt)
d["anteil"] = d["n_serien"] / tot
d.to_csv(f"{OUT}/raw_updates_distribution.csv", index=False)

print(f"Bookmaker-Serien im Rohbestand: {tot:,d}")
print(f"Maximum Updates: {d['n_updates'].max()}")
print(f"Serien mit mehr als 20 Updates: "
      f"{int(d.loc[d['n_updates'] > 20, 'n_serien'].sum()):,d}")
print("\nRand der Verteilung:")
print(d[d["n_updates"] >= 16].to_string(
    index=False, float_format=lambda v: f"{v:.4f}"))

at20 = int(d.loc[d["n_updates"] == 20, "n_serien"].iloc[0])
at19 = int(d.loc[d["n_updates"] == 19, "n_serien"].iloc[0])
print(f"\nHaeufung bei genau 20: {at20:,d} gegen {at19:,d} bei 19 "
      f"-- Faktor {at20 / at19:.1f}")
print(f"\nDatei: {OUT}/raw_updates_distribution.csv")
