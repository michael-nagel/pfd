"""Ist OddsMvt50 unter V2 wirklich der echte Schlusspreis der Serie?

Empirisch statt analytisch: Vergleich der Rasterzelle mit dem letzten
tatsaechlich beobachteten Preis je Serie.
"""
import sys

import numpy as np
import pandas as pd
from omegaconf import OmegaConf

sys.path.insert(0, "src")
from pfd.models.filter_and_shape import filter_and_shape_data  # noqa: E402

KEY = ["Matchup", "Bookies"]
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
df = df.sort_values(["GroupId", "Update"])
last = df.groupby("GroupId").agg(
    Matchup=("Matchup", "first"), Bookies=("Bookies", "first"),
    ClsReal=("OddsMvt", "last")).set_index(KEY)

for name, path, key in (
        ("V2 serieneigen", "revision/snapshots/eq_window_scope/"
                           "wide_series_own.parquet", None),
        ("V1 matchweit", "revision/snapshots/C_normalized/wide_imputed.h5",
         "wide")):
    fr = (pd.read_parquet(path) if key is None
          else pd.read_hdf(path, key=key))
    ix = pd.MultiIndex.from_frame(fr[KEY])
    real = last["ClsReal"].reindex(ix).to_numpy()
    ok = ~np.isnan(real)
    print(f"\n{name}  (n = {int(ok.sum()):,d})")
    for c in (50, 46):
        v = fr[f"OddsMvt{c}"].to_numpy(float)[ok]
        d = np.abs(v - real[ok])
        print(f"  OddsMvt{c}: identisch mit letztem echten Preis "
              f"{np.mean(d < 1e-12) * 100:6.2f} %   "
              f"mean|diff| {d.mean():.6f}   max {d.max():.4f}")
