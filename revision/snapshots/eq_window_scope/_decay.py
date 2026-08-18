#!/usr/bin/env python3
"""Modellfreier Varianzzerfall je Gruppe und Variante.

Das GMM fittet das Verhaeltnis E[(p_t - w)^2] / E[(p_t-1 - w)^2]. Hier wird
dieses Verhaeltnis direkt ausgerechnet, ohne Schaetzer - damit sichtbar wird,
welches Regime den Zerfall auf den fortgeschriebenen Serien verzerrt.
"""

import sys

import numpy as np
import pandas as pd
from omegaconf import OmegaConf

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

OUT = "revision/snapshots/eq_window_scope"
SUPPORT = [26, 31, 36, 41, 46]
SCOLS = [f"OddsMvt{k}" for k in SUPPORT]
H = np.timedelta64(1, "h")
KEY = ["Matchup", "Bookies"]
N_PER = 51

cfg = OmegaConf.create({"estimation": {
    "spec": "BmHome", "normalize": True, "compets": None,
    "bm_quantile": 0.25, "ts_dur": [12, 72], "period": None,
    "resample_freq": "1min", "pctl": 2}})
raw = pd.read_hdf("data/processed/shaped_data.h5", "df")
for c in ("Date", "Update"):
    raw[c] = pd.to_datetime(raw[c])
df, *_ = filter_and_shape_data(raw.copy(), cfg)
gstd = df.groupby("GroupId")["OddsMvt"].transform("std")
df = df[gstd > 0].copy()

g = df.groupby("GroupId")
s = pd.DataFrame({"Matchup": g["Matchup"].first(), "Bookies": g["Bookies"].first(),
                  "own_end": g["Update"].max()})
m = df.groupby("Matchup")["Update"].agg(["min", "max"])
s = s.join(m.rename(columns={"min": "m_start", "max": "m_end"}), on="Matchup")
ff = pd.Series(False, index=s.index)
for k in SUPPORT:
    t1 = s["m_start"] + pd.to_timedelta(
        (k / (N_PER - 1)) * (s["m_end"] - s["m_start"]) / H, unit="h")
    ff |= t1 > s["own_end"]
flag = s.assign(ffill=ff).set_index(KEY)["ffill"]

v1 = pd.read_hdf("revision/snapshots/C_normalized/wide_imputed.h5", key="wide")
v2 = pd.read_parquet(f"{OUT}/wide_series_own.parquet")
i1, i2 = pd.MultiIndex.from_frame(v1[KEY]), pd.MultiIndex.from_frame(v2[KEY])
common = i1.intersection(i2)
v1, v2 = v1[i1.isin(common)].copy(), v2[i2.isin(common)].copy()
f1 = flag.reindex(pd.MultiIndex.from_frame(v1[KEY])).fillna(False).to_numpy()
f2 = flag.reindex(pd.MultiIndex.from_frame(v2[KEY])).fillna(False).to_numpy()

rows = []
print("=" * 78)
print("MITTLERER QUADRIERTER PROGNOSEFEHLER E[(p_k - Match)^2]")
print("=" * 78)
print(f"  {'Gruppe / Variante':<34s}" + "".join(f"{c:>11s}" for c in SCOLS)
      + f"{'46/36':>9s}")
for lab, fr, mask in (("sauber            V1", v1, ~f1),
                      ("sauber            V2", v2, ~f2),
                      ("fortgeschrieben   V1", v1, f1),
                      ("fortgeschrieben   V2", v2, f2)):
    d = fr[mask]
    w = d["Match"].to_numpy(float)
    e = {c: float(np.mean((d[c].to_numpy(float) - w) ** 2)) for c in SCOLS}
    ratio = e["OddsMvt46"] / e["OddsMvt36"]
    print(f"  {lab:<34s}" + "".join(f"{e[c]:>11.5f}" for c in SCOLS)
          + f"{ratio:>9.4f}")
    rows.append({"Gruppe_Variante": lab, **e, "ratio_46_36": ratio})

print("\n  Das GMM fittet genau dieses Verhaeltnis: kleiner = schnellerer")
print("  Zerfall = groesseres gamma. Referenz ohne Lernen waere 1,0000.")
pd.DataFrame(rows).to_csv(f"{OUT}/decay_by_group.csv", index=False)
print(f"\ngeschrieben: {OUT}/decay_by_group.csv")
