"""Aggregate results/*.json into CSV, Markdown and LaTeX tables."""
from __future__ import annotations

import json
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
OUT = os.path.join(HERE, "tables")
os.makedirs(OUT, exist_ok=True)

ORDER = ["A*-dist", "A*", "PSO", "RRT*"]


def load(name):
    with open(os.path.join(RES, f"{name}.json"), encoding="utf-8") as fh:
        return json.load(fh)["records"]


def agg(records):
    rows = []
    cases = []
    for r in records:
        if r["case"] not in cases:
            cases.append(r["case"])
    for case in cases:
        for planner in ORDER:
            sel = [r for r in records if r["case"] == case and r["planner"] == planner]
            if not sel:
                continue
            ok = [r for r in sel if r["success"]]
            def med(key):
                vals = [r[key] for r in ok if r.get(key) == r.get(key)]
                return st.median(vals) if vals else float("nan")
            def q(key):
                vals = sorted(r[key] for r in ok if r.get(key) == r.get(key))
                if len(vals) < 4:
                    return (float("nan"), float("nan"))
                return (vals[len(vals) // 4], vals[3 * len(vals) // 4])
            def mean(key):
                vals = [r[key] for r in ok if r.get(key) == r.get(key)]
                return (st.mean(vals), st.pstdev(vals) if len(vals) > 1 else 0.0) if vals else (float("nan"), 0.0)
            pl_m, pl_s = mean("pl_m")
            rc_m, rc_s = mean("rc")
            rcn = mean("rc_norm")
            lo, hi = q("rc")
            rows.append(dict(case=case, planner=planner, runs=len(sel), success=len(ok) / len(sel),
                             nodes=med("nodes"), time_s=med("time_s"), pl_m=pl_m, pl_s=pl_s,
                             rc_med=med("rc"), rc_q1=lo, rc_q3=hi, rc_mean=rc_m, rc_std=rc_s,
                             rc_norm=rcn[0]))
    return rows


def latex(rows, caption, label):
    lines = [r"\begin{table}[!htbp]", r"\centering", r"\scriptsize",
             r"\caption{%s}" % caption, r"\label{%s}" % label,
             r"\begin{tabular}{@{}llrrrrrr@{}}", r"\toprule",
             r"Case & Planner & Succ. & Nodes & Time (s) & $PL$ (m) & $RC$ & $RC/L$ \\", r"\midrule"]
    for r in rows:
        succ = "%.0f%%" % (100 * r["success"])
        if r["planner"] in ("RRT*", "PSO"):
            rc = r"%.1f [%.1f, %.1f]" % (r["rc_med"], r["rc_q1"], r["rc_q3"])
        else:
            rc = r"%.1f" % r["rc_med"]
        lines.append(r"%s & %s & %s & %d & %.2f & %.1f & %s & %.4f \\" % (
            r["case"], r["planner"].replace("*", "$^{*}$"), succ, int(r["nodes"]), r["time_s"],
            r["pl_m"], rc, r["rc_norm"]))
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    return "\n".join(lines)


def markdown(rows, title):
    out = [f"## {title}", "", "| case | planner | succ | nodes | time (s) | PL (m) | RC | RC/L |",
           "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append("| %s | %s | %.0f%% | %d | %.2f | %.1f | %.1f | %.4f |" % (
            r["case"], r["planner"], 100 * r["success"], r["nodes"], r["time_s"], r["pl_m"],
            r["rc_med"], r["rc_norm"]))
    return "\n".join(out)


def main():
    md = []
    for name, title in (("time", "Time slices (TPR02)"), ("density", "Urban density"),
                        ("ablation", "Risk-factor ablation")):
        path = os.path.join(RES, f"{name}.json")
        if not os.path.exists(path):
            continue
        rows = agg(load(name))
        md.append(markdown(rows, title))
        with open(os.path.join(OUT, f"table_{name}.tex"), "w", encoding="utf-8") as fh:
            fh.write(latex(rows, title + " performance", "tab:" + name))
        with open(os.path.join(OUT, f"table_{name}.csv"), "w", encoding="utf-8") as fh:
            keys = list(rows[0].keys())
            fh.write(",".join(keys) + "\n")
            for r in rows:
                fh.write(",".join(str(r[k]) for k in keys) + "\n")
    with open(os.path.join(OUT, "summary.md"), "w", encoding="utf-8") as fh:
        fh.write("# Aggregated results\n\n" + "\n\n".join(md) + "\n")
    print("\n\n".join(md))


if __name__ == "__main__":
    main()
