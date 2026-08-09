#!/usr/bin/env python3
"""Simultane Inferenz für den beta_1-Pfad (R1-vii).

R1-vii: das Phasen-Narrativ beruht auf 50 punktweisen Konfidenzintervallen.
Gefordert sind formale Tests mit simultanen Konfidenzbändern oder ein
glatteres dynamisches Modell des Koeffizientenpfads. Das glatte Modell steht
schon in `../main_spec` (varying-coefficient-GAM, Abschnitte 3-6); hier kommt
die simultane Inferenz dazu. Grundlage sind die 100 gespeicherten
Cluster-Bootstrap-Replikate -- kein Neufit, keine Datenladung.

Vier Objekte:

  1) sup-t-Band (simultan, 95 %) statt punktweiser Bänder.
  2) Globaler Test H0: beta_1(t) = 1 für alle t.
  3) Globaler Test H0: beta_1(t) konstant -- gibt es überhaupt einen Pfad?
     Unter H0 ist beta_1(t) minus Gittermittel identisch null, egal mit
     welchen Gewichten gemittelt wird; die Wahl trifft also nur die Güte,
     nicht die Gültigkeit.
  4) Der Randkontrast beta_1(24 h) - beta_1(0,25 h) als Effektmaß.

Dazu die Gegenrechnung auf der publizierten Perzentil-Kurve: wie viele der
50 punktweisen Intervalle überleben eine Multiplizitätskorrektur, und wie
viele zusätzlich den Cluster-Faktor 3.

Rein diagnostisch, nichts an der Produktions-Pipeline.
"""

import numpy as np
import pandas as pd
from scipy.stats import norm

OUT = "revision/snapshots/continuous_unbiasedness/main_spec"
BASE = "revision/snapshots/C_normalized/beta1_curve.csv"
HMAX = 48.0          # Berichtsfenster wie in `_main_spec_plot.py`
MARKS = [24.0, 12.0, 6.0, 3.0, 1.0, 0.25]
ALPHA = 0.05
NSIM = 200_000
SEED = 20260809

pd.set_option("display.width", 220)
rng = np.random.default_rng(SEED)
Z_PW = float(norm.ppf(1 - ALPHA / 2))


def block(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78, flush=True)


def gauss_sup(cov, se):
    """Simulierte sup-|t|-Nullverteilung aus N(0, cov).

    Der beta_1-Pfad lebt in einem 6-dimensionalen Splineraum, die
    Kovarianzmatrix über das Gitter hat also Rang <= 6. Mit B = 100
    Replikaten ist sie damit gut geschätzt -- anders als das 95-%-Quantil
    eines Maximums, wenn man es roh aus 100 Ziehungen nimmt.
    """
    w, v = np.linalg.eigh(cov)
    keep = w > w.max() * 1e-10
    root = v[:, keep] * np.sqrt(w[keep])
    draws = rng.standard_normal((NSIM, root.shape[1])) @ root.T
    return np.abs(draws / se).max(axis=1), int(keep.sum())


def report(name, stat, null_gauss, null_boot, where):
    """Kritischer Wert und p-Wert eines sup-|t| aus beiden Nullverteilungen."""
    crit = float(np.percentile(null_gauss, 100 * (1 - ALPHA)))
    p_g = float((null_gauss >= stat).mean())
    p_b = float((null_boot >= stat).mean())
    print(f"sup-|t| = {stat:.3f}   (Maximum bei {where:.2f} h vor Anpfiff)")
    print(f"  kritischer Wert 5 % : {crit:.3f}")
    print(f"  p (Gauss-Sim)       : {p_g:.4f}")
    print(f"  p (roh, B = 100)    : {p_b:.4f}")
    print("  -> " + ("H0 verworfen" if p_g < ALPHA else "H0 NICHT verworfen"))
    return crit, p_g, p_b


# ------------------------------------------------------------------ Daten
cr = pd.read_csv(f"{OUT}/cluster_robust_beta1.csv")
boot = np.vstack([np.load(f"{OUT}/bootstrap_beta1_part{p}.npy")
                  for p in (0, 1)])

m = (cr["hours"] <= HMAX).to_numpy()
hours = cr["hours"].to_numpy()[m]
beta = cr["beta_1"].to_numpy()[m]
se_model = cr["se_lmer_model"].to_numpy()[m]
se_sand = cr["se_cluster"].to_numpy()[m]
boot = boot[:, m]

B, T = boot.shape
se = boot.std(axis=0, ddof=1)
dev = boot - boot.mean(axis=0)          # zentrierte Replikate = Nullverteilung

print(f"Gitter: {T} Punkte, {hours.min():.3f}-{hours.max():.1f} h "
      f"(Trim bei {HMAX:.0f} h)")
print(f"Bootstrap: B = {B} Replikate")

# ---------------------------------------------------------- 1) sup-t-Band
block("1) SIMULTANES 95-%-BAND (sup-t)")

null1_g, rank = gauss_sup(np.cov(boot, rowvar=False), se)
c_gauss = float(np.percentile(null1_g, 100 * (1 - ALPHA)))
null1_b = np.abs(dev / se).max(axis=1)
c_boot = float(np.percentile(null1_b, 100 * (1 - ALPHA)))

print(f"Effektiver Rang der Kovarianzmatrix: {rank} "
      f"(Splinebasis k = 6 -> erwartet <= 6)")
print(f"  punktweise           z = {Z_PW:.3f}")
print(f"  sup-t, Gauss-Sim     c = {c_gauss:.3f}   ({c_gauss / Z_PW:.2f}x)")
print(f"  sup-t, roh (B = {B})  c = {c_boot:.3f}   (Kontrolle)")

band = pd.DataFrame({
    "hours": hours,
    "beta_1": beta,
    "se_boot": se,
    "se_sandwich": se_sand,
    "se_model": se_model,
    "pw_lo": beta - Z_PW * se,
    "pw_up": beta + Z_PW * se,
    "sim_lo": beta - c_gauss * se,
    "sim_up": beta + c_gauss * se,
})
band["excl_1_pointwise"] = (band["pw_lo"] > 1) | (band["pw_up"] < 1)
band["excl_1_simultaneous"] = (band["sim_lo"] > 1) | (band["sim_up"] < 1)
band.to_csv(f"{OUT}/simultaneous_band.csv", index=False)

print(f"\nGitterpunkte, an denen das Band die 1 ausschliesst:"
      f"  punktweise {int(band['excl_1_pointwise'].sum())}/{T}"
      f"   simultan {int(band['excl_1_simultaneous'].sum())}/{T}")

marks = pd.DataFrame([band.iloc[int(np.abs(hours - h).argmin())]
                      for h in MARKS])
print("\n" + marks[["hours", "beta_1", "se_boot", "pw_lo", "pw_up",
                    "sim_lo", "sim_up"]].to_string(
    index=False, float_format=lambda v: f"{v:8.3f}"))
marks.to_csv(f"{OUT}/simultaneous_marks.csv", index=False)

# ------------------------------------------ 2) H0: beta_1(t) = 1 überall
block("2) GLOBALER TEST  H0: beta_1(t) = 1 FÜR ALLE t")

t1 = np.abs(beta - 1) / se
s1 = float(t1.max())
crit1, p1_g, p1_b = report("level", s1, null1_g, null1_b,
                           hours[int(t1.argmax())])

# ---------------------------------------- 3) H0: beta_1(t) konstant
block("3) GLOBALER TEST  H0: beta_1(t) KONSTANT (gibt es einen Pfad?)")

d_hat = beta - beta.mean()
d_boot = boot - boot.mean(axis=1, keepdims=True)
se_d = d_boot.std(axis=0, ddof=1)
null2_g, rank_d = gauss_sup(np.cov(d_boot, rowvar=False), se_d)
null2_b = np.abs((d_boot - d_boot.mean(axis=0)) / se_d).max(axis=1)

t2 = np.abs(d_hat) / se_d
s2 = float(t2.max())
print(f"Gittermittel beta_1 = {beta.mean():.4f}   (Rang {rank_d})")
crit2, p2_g, p2_b = report("shape", s2, null2_g, null2_b,
                           hours[int(t2.argmax())])

# ----------------------------------------------------- 4) Randkontrast
block("4) RANDKONTRAST  beta_1(24 h) - beta_1(0,25 h)")

i24 = int(np.abs(hours - 24.0).argmin())
i025 = int(np.abs(hours - 0.25).argmin())
d_pt = beta[i24] - beta[i025]
d_rep = boot[:, i24] - boot[:, i025]
se_dc = float(d_rep.std(ddof=1))
lo, up = np.percentile(d_rep, [2.5, 97.5])
p_dc = 2 * min((d_rep - d_rep.mean() >= d_pt).mean(),
               (d_rep - d_rep.mean() <= -d_pt).mean())

print(f"beta_1({hours[i24]:.1f} h) = {beta[i24]:.3f}   "
      f"beta_1({hours[i025]:.2f} h) = {beta[i025]:.3f}")
print(f"Differenz = {d_pt:.3f}   SE(Bootstrap) = {se_dc:.3f}   "
      f"t = {d_pt / se_dc:.2f}")
print(f"Bootstrap-Perzentil-CI: [{lo:.3f} , {up:.3f}]")
print(f"zweiseitiges Bootstrap-p: {p_dc:.4f}")

pd.DataFrame([
    {"test": "H0: beta_1(t) = 1 ueberall", "stat": s1, "crit_5pct": crit1,
     "p_gauss": p1_g, "p_boot": p1_b, "arg_max_hours": hours[int(t1.argmax())]},
    {"test": "H0: beta_1(t) konstant", "stat": s2, "crit_5pct": crit2,
     "p_gauss": p2_g, "p_boot": p2_b, "arg_max_hours": hours[int(t2.argmax())]},
    {"test": "beta_1(24h) - beta_1(0.25h)", "stat": d_pt / se_dc,
     "crit_5pct": Z_PW, "p_gauss": np.nan, "p_boot": p_dc,
     "arg_max_hours": np.nan},
]).to_csv(f"{OUT}/global_tests.csv", index=False)

# ------------------------- 5) Gegenrechnung auf der publizierten Kurve
block("5) DIE PUBLIZIERTE PERZENTIL-KURVE: MULTIPLIZITÄT UND CLUSTERUNG")

pub = pd.read_csv(BASE)
n = len(pub)
z_sidak = float(norm.ppf(1 - (1 - (1 - ALPHA) ** (1 / n)) / 2))
print(f"{n} Perzentilregressionen -> Šidák-z = {z_sidak:.3f} statt {Z_PW:.3f}")

rows = []
for lab, zc, fac in (("punktweise, modellbasiert", Z_PW, 1.0),
                     ("Šidák über 50 Tests", z_sidak, 1.0),
                     ("punktweise, SE x 3 (Cluster)", Z_PW, 3.0),
                     ("Šidák + SE x 3", z_sidak, 3.0)):
    s = pub["std_beta_1"] * fac
    excl = (pub["beta_1"] - zc * s > 1) | (pub["beta_1"] + zc * s < 1)
    rows.append({"Fassung": lab, "z": zc, "SE-Faktor": fac,
                 "Perzentile_mit_CI_ohne_1": int(excl.sum()), "von": n,
                 "Anteil": excl.mean()})
comp = pd.DataFrame(rows)
print("\n" + comp.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
comp.to_csv(f"{OUT}/pointwise_vs_corrected.csv", index=False)

# ------------------- 5b) Trägt das Zackenmuster der publizierten Kurve?
block("5b) SIND DIE BENACHBARTEN ÄNDERUNGEN DER PUBLIZIERTEN KURVE SIGNIFIKANT?")

# Das Phasen-Narrativ (Lernen, Pause, wiederaufgenommenes Lernen) liest
# Struktur aus den Sprüngen zwischen benachbarten Perzentilschätzern. Wenn
# keiner dieser Sprünge einzeln signifikant ist, ist das Muster Rauschen.
# Die beiden Schätzer sind positiv korreliert (überlappende Daten), sd der
# Differenz ist also HÖCHSTENS sqrt(se_i^2 + se_j^2) -- der Test ist damit
# konservativ zugunsten des Narrativs.
b = pub["beta_1"].to_numpy()
sb = pub["std_beta_1"].to_numpy()
diff = np.diff(b)
z_adj = diff / np.sqrt(sb[:-1] ** 2 + sb[1:] ** 2)

adj = pd.DataFrame({
    "pctl_von": pub["pctl"].to_numpy()[:-1],
    "pctl_bis": pub["pctl"].to_numpy()[1:],
    "diff": diff, "z": z_adj, "signifikant": np.abs(z_adj) > Z_PW,
})
adj.to_csv(f"{OUT}/adjacent_changes.csv", index=False)

drop1 = adj.iloc[1:]      # ohne den Sprung vom Randperzentil 2
for lab, a in (("alle Paare", adj), ("ohne das Randperzentil 2", drop1)):
    print(f"{lab:<26s} n = {len(a):>2d}   signifikant: "
          f"{int(a['signifikant'].sum())}   max |z| = {a['z'].abs().max():.2f}")
print("\nDie größten drei Sprünge:")
print(adj.reindex(adj["z"].abs().sort_values(ascending=False).index)
      .head(3).to_string(index=False, float_format=lambda v: f"{v:.4f}"))

# ------------------------------------------------------ 6) Trim-Sensitivität
block("6) SENSITIVITÄT GEGEN DAS BERICHTSFENSTER")

# README Abschnitt 7 hatte den Trim bewusst offen gelassen: das Maximum der
# Diskrepanz zwischen fester und penalisierter Basis liegt bei 45,5 h, also
# genau am linken Rand des 48-h-Fensters. Ein sup-Test ist auf diesen Rand
# empfindlich, weil er über alle Gitterpunkte maximiert.
h_all = cr["hours"].to_numpy()
b_all = cr["beta_1"].to_numpy()
boot_all = np.vstack([np.load(f"{OUT}/bootstrap_beta1_part{p}.npy")
                      for p in (0, 1)])

rows = []
for hmax in (48.0, 36.0, 24.0):
    k = h_all <= hmax
    bb, hh = boot_all[:, k], h_all[k]
    ss = bb.std(axis=0, ddof=1)
    bt = b_all[k]

    n_g, _ = gauss_sup(np.cov(bb, rowvar=False), ss)
    s_lvl = float((np.abs(bt - 1) / ss).max())

    dd = bb - bb.mean(axis=1, keepdims=True)
    sd = dd.std(axis=0, ddof=1)
    n2_g, _ = gauss_sup(np.cov(dd, rowvar=False), sd)
    s_shp = float((np.abs(bt - bt.mean()) / sd).max())

    rows.append({
        "HMAX_h": hmax, "Gitterpunkte": int(k.sum()),
        "c_sup": float(np.percentile(n_g, 100 * (1 - ALPHA))),
        "sup_t_level": s_lvl, "p_level": float((n_g >= s_lvl).mean()),
        "sup_t_shape": s_shp, "p_shape": float((n2_g >= s_shp).mean()),
    })
sens = pd.DataFrame(rows)
print(sens.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
sens.to_csv(f"{OUT}/simultaneous_trim_sensitivity.csv", index=False)

print("\nDateien: simultaneous_band.csv, simultaneous_marks.csv, "
      "global_tests.csv, pointwise_vs_corrected.csv, "
      "simultaneous_trim_sensitivity.csv")
