import json, statistics as st
import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import config  # noqa: E402

base = str(config.RESULTS_DIR)
for group in ("time","density"):
    try:
        d = json.load(open(base + f"\\{group}.json", encoding="utf-8"))
    except FileNotFoundError:
        print("missing", group); continue
    print("=== ", group)
    for case in dict.fromkeys(r["case"] for r in d["records"]):
        for pl in ("Dijkstra","A*","WA*","RRT*"):
            rows=[r for r in d["records"] if r["case"]==case and r["planner"]==pl and r["success"]]
            if not rows: continue
            print("%-7s %-9s nodes=%7d t=%7.2fs PL=%7.1f RC=%9.1f RC/L=%.4f" % (
                case, pl, st.median([r["nodes"] for r in rows]), st.median([r["time_s"] for r in rows]),
                st.mean([r["pl_m"] for r in rows]), st.median([r["rc"] for r in rows]), st.mean([r["rc_norm"] for r in rows])))
