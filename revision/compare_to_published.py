#!/usr/bin/env python3
"""Vergleicht eine Revisions-Stufe gegen die PUBLIZIERTE Paper-Version.

Referenz ist `revision/snapshots/A_baseline` -- NICHT der Tag
`pre-revision-baseline`. Zwischen beiden liegen drei Commits Code-Drift;
A_baseline ist der eingefrorene Stand, gegen den laut
`revision/baseline_status.md` alle Revisionsänderungen gemessen werden.

Aufruf:
    python revision/compare_to_published.py <stage>

`<stage>` ist entweder ein Unterverzeichnis von `revision/snapshots/`
(z. B. `C_normalized`) oder `live` für den aktuellen Pipeline-Output unter
`reports/`.

Ausgabe: `revision/DIFF_TO_PUBLISHED.md` (wird bei jedem Lauf überschrieben)
plus eine knappe Konsolen-Zusammenfassung.

Was A_baseline NICHT enthält (siehe dessen MANIFEST.md) und daher nicht
verglichen werden kann:
  - gamma je Bookmaker (nur die Aggregate wurden gespeichert)
  - der volle beta_1-Pfad (nur die Perzentile, an denen beta_1 von 1
    ununterscheidbar ist)
Beides wird als "nicht vergleichbar" ausgewiesen, nicht stillschweigend
übergangen.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SNAP = ROOT / "revision" / "snapshots"
REF = SNAP / "A_baseline"
OUT_MD = ROOT / "revision" / "DIFF_TO_PUBLISHED.md"

TABLES = [
    ("3", "res_gpm", "Predictability of Close-to-End Returns"),
    ("4", "res_rfa", "Relative Forecast Accuracy of Opening/Closing Prices"),
    ("5", "res_wp", "Winning Rates at Different Price-Change Magnitudes"),
    ("6", "res_wp_re", "Winning Rates vs. Price-Change Magnitudes"),
    ("7", "res_rfa_tot", "Relative Forecast Accuracy by Bookmaker"),
]


def num(s):
    """Zahl aus einem Zellwert, sonst None. Tausenderkommas werden entfernt."""
    if s is None:
        return None
    t = str(s).strip().replace(",", "")
    if t == "" or t == "-":
        return None
    try:
        return float(t)
    except ValueError:
        return None


def esc(v):
    """Pipes maskieren, sonst zerbricht die Markdown-Tabelle (`P> |z|`)."""
    return str(v).replace("|", "\|")


def fmt(v):
    """Kompakte Darstellung eines Zellwerts."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return "—"
    f = num(v)
    if f is None:
        return str(v).strip()
    return f"{f:,.6g}"


def read_values(stage_dir, live):
    """values.csv der Stufe bzw. values.dat des Live-Outputs als dict."""
    if live:
        out = {}
        for line in (ROOT / "reports" / "values" / "values.dat").read_text(
                encoding="utf-8").splitlines():
            if ";" in line:
                k, v = line.split(";", 1)
                out[k.strip()] = v.strip()
        return out
    p = stage_dir / "values.csv"
    if not p.exists():
        return {}
    d = pd.read_csv(p, dtype=str).fillna("")
    return dict(zip(d["key"], d["value"], strict=True))


def read_tex_table(path):
    """LaTeX-Tabellenrumpf -> DataFrame (erste Spalte = Zeilenname).

    Beide Seiten werden über das .tex gelesen: A_baseline hat zusätzlich ein
    .csv, die Stufen haben nur das .tex.
    """
    if not path.exists():
        return None
    rows, header = [], None
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("\\midrule") or s.startswith("\\bottomrule"):
            continue
        if "&" not in s:
            continue
        cells = [c.strip() for c in s.rstrip("\\").split("&")]
        if header is None:
            header = ["Row"] + [c.replace("$", "").replace("\\", "")
                                for c in cells[1:]]
            continue
        cells = [c.replace("\\_", "_") for c in cells]
        rows.append(cells[:len(header)] + [""] * (len(header) - len(cells)))
    if header is None or not rows:
        return None
    return pd.DataFrame(rows, columns=header).set_index("Row")


def table_paths(stage_dir, live, n, slug):
    """(Referenzpfad, Stufenpfad) für eine Tabelle."""
    ref = REF / f"table{n}_{slug}.tex"
    cur = (ROOT / "reports" / "tables" / f"{slug}.tex" if live
           else stage_dir / "tables" / f"{slug}.tex")
    return ref, cur


def diff_tables(stage_dir, live, name):
    """Zellweiser Vergleich; nur abweichende Zellen werden gemeldet."""
    out = []
    for n, slug, title in TABLES:
        ref_p, cur_p = table_paths(stage_dir, live, n, slug)
        a, b = read_tex_table(ref_p), read_tex_table(cur_p)
        if a is None or b is None:
            miss = "A_baseline" if a is None else name
            out.append((n, slug, title, None, f"nicht vorhanden in {miss}"))
            continue
        cells, changed = 0, []
        for r in a.index:
            for c in a.columns:
                if r not in b.index or c not in b.columns:
                    continue
                cells += 1
                x, y = a.loc[r, c], b.loc[r, c]
                fx, fy = num(x), num(y)
                same = (abs(fx - fy) < 5e-7 if fx is not None
                        and fy is not None else str(x).strip()
                        == str(y).strip())
                if not same:
                    changed.append((r, c, x, y,
                                    None if fx is None or fy is None
                                    else fy - fx))
        out.append((n, slug, title, (cells, changed), None))
    return out


def gmm_block(stage_dir, live, name):
    """Aggregate vergleichen; gamma je Bookmaker nur berichten."""
    ref = {}
    p = REF / "gmm.csv"
    if p.exists():
        d = pd.read_csv(p, dtype=str)
        ref = dict(zip(d["key"], d["value"], strict=True))
    cur_p = (ROOT / "reports" / "gmm_by_bookie.csv" if live
             else stage_dir / "gmm_by_bookie.csv")
    per = pd.read_csv(cur_p) if cur_p.exists() else None
    agg = {}
    if per is not None and {"bookie", "gamma"} <= set(per.columns):
        g = per.set_index("bookie")["gamma"]
        agg = {"avg_gamma_gmm": g.mean(), "min_gamma_gmm": g.min(),
               "max_gamma_gmm": g.max(), "idxmax_gamma_gmm": g.idxmax(),
               "idxmin_gamma_gmm": g.idxmin()}
    return ref, agg, per


def beta1_block(stage_dir, live):
    """beta_1-Kurve der Stufe; A_baseline hat keine (MANIFEST-Lücke 2)."""
    p = (ROOT / "reports" / "beta1_curve.csv" if live
         else stage_dir / "beta1_curve.csv")
    if not p.exists():
        return None, None
    c = pd.read_csv(p)
    cross = None
    for i in range(1, len(c)):
        a, b = c["beta_1"].iloc[i - 1], c["beta_1"].iloc[i]
        if (a - 1) * (b - 1) < 0:
            x0, x1 = c["pctl"].iloc[i - 1], c["pctl"].iloc[i]
            cross = x0 + (1 - a) * (x1 - x0) / (b - a)
            break
    return c, cross


def read_set(path):
    if not path.exists():
        return None
    d = pd.read_csv(path)
    return set(d[d.columns[0]].tolist())


def main():
    if len(sys.argv) != 2:
        sys.exit("Aufruf: python revision/compare_to_published.py <stage>")
    name = sys.argv[1]
    live = name == "live"
    stage_dir = SNAP / name
    if not live and not stage_dir.is_dir():
        sys.exit(f"Unbekannte Stufe '{name}'. Verfügbar: "
                 + ", ".join(sorted(p.name for p in SNAP.iterdir()
                                    if p.is_dir())) + ", live")

    md = ["# Unterschiede zur publizierten Version",
          "",
          f"- **Stufe:** `{name}`",
          "- **Referenz:** `revision/snapshots/A_baseline` (publizierter "
          "Stand; NICHT der Tag `pre-revision-baseline`, zwischen beiden "
          "liegen drei Commits Code-Drift)",
          f"- **Erzeugt:** {datetime.now(UTC):%Y-%m-%d %H:%M} UTC "
          f"von `revision/compare_to_published.py`",
          ""]
    console = []

    # ---------------------------------------------------------- 1) values
    a_val, b_val = read_values(REF, False), read_values(stage_dir, live)
    common = [k for k in a_val if k in b_val]
    changed, unchanged = [], 0
    for k in common:
        x, y = a_val[k], b_val[k]
        fx, fy = num(x), num(y)
        if fx is not None and fy is not None:
            if abs(fx - fy) < 5e-7:
                unchanged += 1
            else:
                rel = (fy - fx) / abs(fx) if fx else float("nan")
                changed.append((k, x, y, fy - fx, rel))
        elif str(x).strip() == str(y).strip():
            unchanged += 1
        else:
            changed.append((k, x, y, None, None))
    missing = [k for k in a_val if k not in b_val]

    md += [f"## 1) values ({len(common)} Schlüssel vergleichbar, "
           f"{len(missing)} von dieser Stufe nicht erzeugt)", ""]
    if changed:
        md += ["| key | publiziert | aktuell | Delta | rel. |",
               "|---|---:|---:|---:|---:|"]
        for k, x, y, d, r in changed:
            rs = "—" if r is None or r != r else f"{r * 100:+.2f} %"
            ds = "—" if d is None else f"{d:+,.6g}"
            md.append(f"| `{k}` | {fmt(x)} | {fmt(y)} | {ds} | {rs} |")
        md.append("")
    md += [f"**{len(changed)} von {len(common)} geändert, {unchanged} "
           f"unverändert (nicht aufgelistet).**", ""]
    if missing:
        md += ["Nicht erzeugt von dieser Stufe: "
               + ", ".join(f"`{k}`" for k in missing), ""]
    console.append(f"values      {len(changed):>3d}/{len(common)} geändert"
                   f"   ({unchanged} unverändert, {len(missing)} fehlen)")

    # ---------------------------------------------------------- 2) Tabellen
    md += ["## 2) Tabellen 3-7", ""]
    tab_changed = 0
    for n, slug, title, res, err in diff_tables(stage_dir, live, name):
        md.append(f"### Tabelle {n} — {title} (`{slug}`)")
        if err:
            md += ["", f"- {err}", ""]
            continue
        cells, ch = res
        tab_changed += len(ch)
        if not ch:
            md += ["", f"- identisch ({cells} Zellen verglichen)", ""]
            continue
        md += ["", f"- **{len(ch)} von {cells} Zellen geändert**", "",
               "| Zeile | Spalte | publiziert | aktuell | Delta |",
               "|---|---|---:|---:|---:|"]
        for r, c, x, y, d in ch:
            md.append(f"| {esc(r)} | {esc(c)} | {fmt(x)} | {fmt(y)} | "
                      f"{'—' if d is None else f'{d:+,.6g}'} |")
        md.append("")
    console.append(f"Tabellen    {tab_changed:>3d} Zellen geändert (3-7)")

    # ---------------------------------------------------------------- 3) GMM
    ref_gmm, agg, per = gmm_block(stage_dir, live, name)
    md += ["## 3) GMM", ""]
    if agg:
        md += ["| Kennzahl | publiziert | aktuell | Delta |",
               "|---|---:|---:|---:|"]
        for k in ("avg_gamma_gmm", "min_gamma_gmm", "max_gamma_gmm",
                  "idxmin_gamma_gmm", "idxmax_gamma_gmm"):
            x, y = ref_gmm.get(k), agg.get(k)
            fx, fy = num(x), num(y)
            d = (f"{fy - fx:+,.6g}" if fx is not None and fy is not None
                 else "—")
            md.append(f"| `{k}` | {fmt(x)} | {fmt(y)} | {d} |")
        md.append("")
    else:
        md += ["- keine `gmm_by_bookie.csv` in dieser Stufe", ""]
    md += ["> **gamma je Bookmaker ist gegen A_baseline nicht vergleichbar.** "
           "Der publizierte Lauf hat nur Mittelwert/Min/Max/Argmin/Argmax "
           "behalten, die 24 Einzelwerte wurden nach dem Zeichnen verworfen "
           "(`A_baseline/MANIFEST.md`, Lücke 1).", ""]
    if per is not None:
        md += [f"Zur Dokumentation, gamma dieser Stufe ({len(per)} "
               f"Bookmaker): Median {per['gamma'].median():.4f}, "
               f"Spanne {per['gamma'].min():.4f}–{per['gamma'].max():.4f}", ""]
    if agg and num(ref_gmm.get("avg_gamma_gmm")) is not None:
        dd = agg["avg_gamma_gmm"] - num(ref_gmm["avg_gamma_gmm"])
        ra = num(ref_gmm["avg_gamma_gmm"])
        console.append(f"GMM         avg gamma {ra:.4f} -> "
                       f"{agg['avg_gamma_gmm']:.4f}  ({dd:+.4f})")
    else:
        console.append("GMM         Aggregate nicht vergleichbar")

    # ------------------------------------------------------------ 4) beta_1
    curve, cross = beta1_block(stage_dir, live)
    md += ["## 4) beta_1-Pfad", ""]
    md += ["> **Der volle Pfad ist gegen A_baseline nicht vergleichbar.** "
           "Der publizierte Lauf hat nur die Perzentile gespeichert, an denen "
           "beta_1 von 1 ununterscheidbar ist, nicht die (beta_1, SE)-Paare "
           "(`A_baseline/MANIFEST.md`, Lücke 2). max/mittleres |Delta| sind "
           "daher nur zwischen zwei Stufen mit `beta1_curve.csv` bestimmbar.",
           ""]
    if curve is not None:
        md += [f"- Kurve dieser Stufe: {len(curve)} Stützstellen, "
               f"beta_1 von {curve['beta_1'].iloc[0]:.4f} (Perzentil "
               f"{curve['pctl'].iloc[0]:g}) bis {curve['beta_1'].iloc[-1]:.4f} "
               f"(Perzentil {curve['pctl'].iloc[-1]:g})",
               f"- Mittleres beta_1: {curve['beta_1'].mean():.4f}",
               "- **Kreuzung von 1:** "
               + (f"Perzentil {cross:.1f}" if cross is not None
                  else "keine Kreuzung im Gitter"), ""]
        console.append("beta_1      Kreuzung von 1 bei Perzentil "
                       + (f"{cross:.1f}" if cross is not None else "—")
                       + "  (Pfad selbst nicht gegen A_baseline vergleichbar)")
    else:
        md += ["- keine `beta1_curve.csv` in dieser Stufe", ""]
        console.append("beta_1      keine Kurve in dieser Stufe")

    # -------------------------------------------- 5) Signifikanz-Perzentile
    a_sig = read_set(REF / "signific_time_idx.csv")
    b_sig = read_set(ROOT / "reports" / "signific_time_idx.csv" if live
                     else stage_dir / "signific_time_idx.csv")
    md += ["## 5) Perzentile, an denen beta_1 von 1 ununterscheidbar ist", ""]
    if a_sig is None or b_sig is None:
        md += ["- nicht auf beiden Seiten vorhanden", ""]
        console.append("Perzentile  nicht vergleichbar")
    else:
        add, rem = sorted(b_sig - a_sig), sorted(a_sig - b_sig)
        md += [f"- publiziert ({len(a_sig)}): "
               + ", ".join(str(x) for x in sorted(a_sig)),
               f"- aktuell ({len(b_sig)}): "
               + ", ".join(str(x) for x in sorted(b_sig)),
               f"- **hinzugekommen ({len(add)}):** "
               + (", ".join(str(x) for x in add) or "—"),
               f"- **weggefallen ({len(rem)}):** "
               + (", ".join(str(x) for x in rem) or "—"), ""]
        console.append(f"Perzentile  {len(a_sig)} -> {len(b_sig)}"
                       f"   (+{len(add)} / -{len(rem)})")

    # ------------------------------------------------- 6) RMSE je Bookmaker
    a_r = REF / "rmse_by_bookie.csv"
    b_r = (ROOT / "reports" / "rmse_by_bookie.csv" if live
           else stage_dir / "rmse_by_bookie.csv")
    md += ["## 6) RMSE je Bookmaker", ""]
    if a_r.exists() and b_r.exists():
        x = pd.read_csv(a_r).set_index("bookie")["rmse"]
        y = pd.read_csv(b_r).set_index("bookie")["rmse"]
        j = pd.concat([x.rename("pub"), y.rename("cur")], axis=1).dropna()
        d = (j["cur"] - j["pub"]).abs()
        md += [f"- {len(j)} Bookmaker verglichen; max |Delta| {d.max():.3g}, "
               f"mittleres |Delta| {d.mean():.3g}, "
               f"{int((d > 5e-7).sum())} über 5e-7", ""]
        console.append(f"RMSE        max |Δ| {d.max():.3g}   "
                       f"{int((d > 5e-7).sum())}/{len(j)} materiell geändert")
    else:
        md += ["- nicht auf beiden Seiten vorhanden", ""]
        console.append("RMSE        nicht vergleichbar")

    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"\nStufe '{name}' gegen A_baseline (publiziert)")
    print("-" * 62)
    for line in console:
        print("  " + line)
    print("-" * 62)
    print(f"  geschrieben: {OUT_MD.relative_to(ROOT)}\n")


if __name__ == "__main__":
    main()
