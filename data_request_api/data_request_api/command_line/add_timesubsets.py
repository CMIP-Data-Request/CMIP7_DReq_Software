# data_request_api/command_line/add_timesubsets.py
from __future__ import annotations

import argparse
import json
import re
from typing import Iterable, Any

from data_request_api.content import dreq_content as dc
from data_request_api.query   import dreq_query   as dq
from data_request_api.query   import patch_time_subset_periods

YEAR_RE = re.compile(r"\b(1[6-9]\d{2}|20\d{2}|2100)\b")

def _tbl(base: dict, *names: str):
    for n in names:
        if n in base:
            return base[n]

def _iter_ids(obj: Any, *attrs: str) -> Iterable[str]:
    """Yield record ids from attributes that might be strings, lists, or objects."""
    for a in attrs:
        if not hasattr(obj, a):
            continue
        L = getattr(obj, a)
        seq = L if isinstance(L, (list, tuple)) else [L]
        for item in seq:
            if item is None:
                continue
            if isinstance(item, str):
                yield item
                continue
            # try common id attribute names or dict keys
            for k in ("record_id", "uid", "id"):
                v = getattr(item, k, None) if not isinstance(item, dict) else item.get(k)
                if v:
                    yield v
                    break

def _subset_name(ts) -> str:
    for k in ("label", "title", "description", "name"):
        v = getattr(ts, k, None)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return "subset"

def main():
    ap = argparse.ArgumentParser(
        description="Export Opportunity -> Time Subsets with canonical period strings."
    )
    ap.add_argument("version", help="Data Request version, e.g. v1.2.2 or v1.2.1")
    ap.add_argument("output",  help="Path to output JSON")
    args = ap.parse_args()

    # Load content & build base tables via API
    content = dc.load(args.version)
    base = dq.create_dreq_tables_for_request(content, args.version)

    Opp = _tbl(base, "Opportunity", "Opportunities")
    TS  = _tbl(base, "Time Subset", "Time Subsets", "time_subsets")
    if Opp is None or TS is None:
        raise SystemExit("This DR export doesn't contain Opportunity / Time Subset tables.")

    out = {"version": args.version, "opportunities": {}}
    for oid, o in Opp.records.items():
        otitle = getattr(o, "title", getattr(o, "name", "UNKNOWN"))
        ts_ids = list(_iter_ids(o, "time_subset", "time_subsets"))

        subsets = []
        for ts_id in ts_ids:
            ts = TS.records.get(ts_id)
            if not ts:
                continue

            start = getattr(ts, "start", None)
            end   = getattr(ts, "end",   None)
            label = _subset_name(ts)

            # Canonical period string (uses explicit years if present, else tag inference)
            period = patch_time_subset_periods(label, start, end)

            # Normalize numeric start/end when possible
            def _to_int(x):
                if isinstance(x, int):
                    return x
                if isinstance(x, str) and x.isdigit():
                    return int(x)
                return None

            subsets.append({
                "name":   label,
                "start":  _to_int(start),
                "end":    _to_int(end),
                "period": period,
                # Optional fields if present
                "nyears": getattr(ts, "nyears", None),
                "type":   getattr(ts, "type",   None),
                "notes":  getattr(ts, "description", None),
            })

        if subsets:
            out["opportunities"][otitle] = {"time_subsets": subsets}

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
