#!/usr/bin/env python3
"""Richtungskontrolle: liegt der Bootstrap ueber oder unter dem Sandwich?

Der vollstaendige Cluster-Bootstrap auf der ns-Basis liess sich in dieser
Umgebung nicht zu Ende rechnen (Hintergrundprozesse werden abgebrochen,
rund 2 min je Fit im Vordergrund). Die bereits gerechneten Replikate
reichen aber fuer die Frage, auf die es fuer die Antwort ankommt:

Das simultane Band im Antwortdokument stammt aus dem CR1-Sandwich. Beim
frueheren cr-Lauf war der Bootstrap in der Fenstermitte 10-22 % WEITER als
der Sandwich (README Abschnitt 6a). Ist das hier auch so, dann ist das
berichtete Band die ENGERE Fassung -- und die Aussage "beta_1 ist nirgends
von 1 unterscheidbar" gilt unter dem weiteren Band erst recht.

Rein diagnostisch.
"""

import numpy as np
import pandas as pd

OUT = "revision/snapshots/continuous_unbiasedness/main_spec"
MARKS = [24.0, 12.0, 6.0, 3.0, 1.0, 0.25]

boot = np.vstack([np.load(f"{OUT}/ns4_bootstrap_beta1_part{p}.npy")
                  for p in (0, 1)])
ns = pd.read_csv(f"{OUT}/ns4_beta1.csv")
B = len(boot)
print(f"Replikate: {B}   Gitterpunkte: {boot.shape[1]}")

se_boot = boot.std(axis=0, ddof=1)
m = ns["hours"] <= 48
ratio = se_boot / ns["se_cluster"].to_numpy()

print("\nSE-Verhaeltnis Bootstrap / Sandwich (Fenster <= 48 h):")
r = ratio[m.to_numpy()]
print(f"  Median {np.median(r):.3f}   Mittel {r.mean():.3f}   "
      f"Spanne {r.min():.3f}-{r.max():.3f}")
print(f"  Anteil der Punkte mit Bootstrap > Sandwich: "
      f"{(r > 1).mean() * 100:.0f} %")

rows = []
for h in MARKS:
    i = int(np.abs(ns["hours"] - h).argmin())
    rows.append({"hours": ns["hours"].iloc[i], "beta_1": ns["beta_1"].iloc[i],
                 "se_sandwich": ns["se_cluster"].iloc[i],
                 "se_boot": se_boot[i], "verhaeltnis": ratio[i]})
t = pd.DataFrame(rows)
print("\n" + t.to_string(index=False, float_format=lambda v: f"{v:8.4f}"))
t.to_csv(f"{OUT}/ns4_boot_check.csv", index=False)

med = float(np.median(r))
print(f"\nBefund: der Bootstrap liegt {'UEBER' if med > 1 else 'UNTER'} dem "
      f"Sandwich (Median {med:.3f}).")

if med > 1:
    print("Das Sandwich-Band ist die engere Fassung; ein Bootstrap-Band "
          "wuerde es\nverbreitern und die Aussage 'nirgends von 1 "
          "unterscheidbar' nicht kippen.")
else:
    print("ACHTUNG, andere Richtung als beim frueheren cr-Lauf: das "
          "Sandwich-Band ist hier\ndie WEITERE Fassung. Ein Bootstrap-Band "
          "waere enger und koennte die 1 an\neinzelnen Stellen ausschliessen "
          "-- die Aussage 'nirgends von 1 unterscheidbar'\nist damit NICHT "
          "gegen die Wahl der Kovarianzschaetzung robust.")
    # Wo genau wuerde es kippen? Kritischer Wert bleibt der des Sandwich,
    # das ist nur eine Groessenordnung, keine fertige Inferenz.
    crit = 2.666
    lo = ns["beta_1"].to_numpy() - crit * se_boot
    up = ns["beta_1"].to_numpy() + crit * se_boot
    excl = ((lo > 1) | (up < 1)) & m.to_numpy()
    print(f"\n  Gitterpunkte, an denen ein Band mit den Bootstrap-SEs die 1 "
          f"ausschloesse: {int(excl.sum())} von {int(m.sum())}")
    if excl.any():
        print(f"  betroffener Bereich: "
              f"{ns['hours'][excl].min():.2f} bis "
              f"{ns['hours'][excl].max():.2f} h vor Anpfiff")

print(f"\nEinschraenkung: B = {B} ist klein (relativer Standardfehler einer "
      f"SD rund\n{100 / np.sqrt(2 * (B - 1)):.0f} %), die einzelnen SEs sind "
      f"entsprechend verrauscht. Der Median 0,95\nist von 1 nicht sicher zu "
      f"unterscheiden. Belastbar ist hier nichts ausser der\nFeststellung, "
      f"dass die Frage offen ist.")
print(f"\nDatei: {OUT}/ns4_boot_check.csv")
