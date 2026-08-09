#!/usr/bin/env python3
"""Vollstaendige Sample-Kette vom Rohscrape bis zur Schaetzstichprobe (R1-v).

`sample_stages.csv` beginnt erst bei `shaped_data.h5` und fasst
`filter_and_shape` zu einer einzigen Zeile zusammen. Der Referee fragt nach
der Zahl der verlorenen Beobachtungen; wenn der Rueckgang gross ist, muss er
aufgeschluesselt sein, sonst fragt er genau danach.

Dieses Skript zaehlt jede Stufe einzeln und in der Reihenfolge, in der die
Filter im Code stehen (`filter_and_shape.py:53-110`).

Einheit ist durchgehend die SERIE = ein (Matchup, Bookies)-Paar auf der
analysierten Marktseite (`spec = BmHome`). Der Rohbestand wird deshalb je
Seite gezaehlt, nicht ueber beide Seiten summiert.

Rein diagnostisch, nichts an der Produktions-Pipeline.
"""

import json
import sys

import numpy as np
import pandas as pd
from omegaconf import OmegaConf

sys.path.insert(0, "src")
from pfd.utils import enc_categ_var  # noqa: E402,F401  (Parity mit dem Code)

RAW = "data/raw/crawled_odds.json"
SHAPED = "data/processed/shaped_data.h5"
OUT = "revision/snapshots/censoring"
KEY = ["Matchup", "Bookies"]

pd.set_option("display.width", 220)
cfg = OmegaConf.create({"estimation": {
    "spec": "BmHome", "normalize": True, "compets": None,
    "bm_quantile": 0.25, "ts_dur": [12, 72]}})

rows = []


def step(label, n_ser, n_obs=np.nan, note=""):
    rows.append({"stufe": label, "serien": n_ser, "beobachtungen": n_obs,
                 "hinweis": note})
    print(f"  {label:<52s} {n_ser:>9,d}", flush=True)


# ------------------------------------------------------------- 0) Rohscrape
print("Rohscrape zaehlen ...", flush=True)
n_home = n_away = 0
with open(RAW) as f:
    for line in f:
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        n_home += len([e for e in (rec.get("OddsHome") or [])
                       if "Opening odds" in e])
        n_away += len([e for e in (rec.get("OddsAway") or [])
                       if "Opening odds" in e])

print(f"\nRohe Bookmaker-Serien: Home {n_home:,d}, Away {n_away:,d}, "
      f"beide Seiten {n_home + n_away:,d}")
print("Die Analyse nutzt EINE Seite (BmHome) -- Referenz ist deshalb Home.\n")
step("Rohscrape (crawled_odds.json, Home-Seite)", n_home)

# --------------------------------------------------- 1) shape_data / shape_odds
df = pd.read_hdf(SHAPED, "df")
for c in ("Date", "Update"):
    df[c] = pd.to_datetime(df[c])
n_shaped = df.groupby(KEY).ngroups
step("nach shape_data (Endergebnis, Datum ab 2023, Konsistenz)", n_shaped,
     len(df), "Sammelstufe, nicht weiter aufgeloest")

# ----------------------------------------------- 2) filter_and_shape, Schritt
# Reihenfolge exakt wie filter_and_shape.py:53-110.
df["Margin"] = 1 / df["OddsMvtHome"] + 1 / df["OddsMvtAway"] - 1
d = df.loc[(df["Margin"] >= 0) & (df["Margin"] <= 0.15)]
step("nach Margen-Filter (0 <= Marge <= 15 %)", d.groupby(KEY).ngroups, len(d),
     "beobachtungsweise -- kuerzt Serien auch teilweise")

d = d[d.groupby("Bookies")["Bookies"].transform("size")
      > d["Bookies"].value_counts().quantile(cfg.estimation.bm_quantile)]
step("nach Bookmaker-Quantilsfilter (unterstes 25 %)",
     d.groupby(KEY).ngroups, len(d))

d = d.copy()
d["GroupId"] = d.groupby(KEY).ngroup()
d["TsDur"] = (d.groupby("GroupId")["Update"].transform("last")
              - d.groupby("GroupId")["Update"].transform("first")
              ) / np.timedelta64(1, "h")
lo, hi = cfg.estimation.ts_dur
d = d[(d["TsDur"] >= lo) & (d["TsDur"] <= hi)]
step(f"nach ts_dur-Filter ({lo}-{hi} h Fensterlaenge)",
     d.groupby(KEY).ngroups, len(d))

# ------------------------------------------------------- 3) Nullvarianz
p_own, p_other = 1 / d["OddsMvtHome"], 1 / d["OddsMvtAway"]
d = d.assign(OddsMvt=p_own / (p_own + p_other))
d = d[d.groupby("GroupId")["OddsMvt"].transform("std") > 0]
step("nach Nullvarianz-Filter", d.groupby(KEY).ngroups, len(d))

# ------------------------------------------------------- 4) Modellfilter
d["NumOddsMvt"] = d.groupby("GroupId")["GroupId"].transform("size") - 1
d20 = d[d["NumOddsMvt"] < 20]
step("nach NumOddsMvt < 20 (nur Unbiasedness/GARCH)",
     d20.groupby(KEY).ngroups, len(d20))

# ------------------------------------------------------------------ Ausgabe
t = pd.DataFrame(rows)
t["anteil_vom_roh"] = t["serien"] / t["serien"].iloc[0]
t["entfernt"] = t["serien"].shift() - t["serien"]
t["entfernt_anteil"] = t["entfernt"] / t["serien"].shift()
t.to_csv(f"{OUT}/sample_chain.csv", index=False)

print("\n" + t[["stufe", "serien", "entfernt", "entfernt_anteil",
                "anteil_vom_roh"]].to_string(
    index=False, float_format=lambda v: f"{v:.4f}"))
print(f"\nGesamtrueckgang Rohscrape -> Schaetzstichprobe: "
      f"{(1 - t['serien'].iloc[-2] / t['serien'].iloc[0]) * 100:.1f} % "
      f"(bis Nullvarianz), "
      f"{(1 - t['serien'].iloc[-1] / t['serien'].iloc[0]) * 100:.1f} % "
      f"(inkl. NumOddsMvt < 20)")
print(f"\nDatei: {OUT}/sample_chain.csv")
