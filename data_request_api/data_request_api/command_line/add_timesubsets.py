# add_timesubsets.py
# Export requested variables grouped by priority (all priorities),
# restricted to Opportunities that have ≥1 Time Subset.

from __future__ import annotations
import argparse
import os
import json
from collections import OrderedDict

from data_request_api.content import dreq_content as dc
from data_request_api.query import dreq_query as dq
from data_request_api.query.time_subsets import patch_time_subset_periods

CANON_TS = [
    "hist20", "hist43", "hist72", "histext",
    "scenario20", "scenario20mid", "scenario30mid"
]


# ---------------------------------------------------------------------
# Load DR
# ---------------------------------------------------------------------
def _load_dr(version: str = "latest_stable"):
    resolved = dc.retrieve(version)
    ver = next(iter(resolved))
    content = dc.load(ver)
    base = dq.create_dreq_tables_for_request(content, ver)
    content_path = dc._dreq_content_loaded.get("json_path")
    if not content_path or not os.path.isfile(content_path):
        raise SystemExit("Could not determine path to data request JSON.")
    return base, ver, content_path


# ---------------------------------------------------------------------
# Helpers for Time Subsets
# ---------------------------------------------------------------------
def _find_ts_table_name(base) -> str | None:
    for name in ("Time Subset", "Time Subsets", "time_subsets"):
        if name in base:
            return name
    return None


def _opportunity_titles_with_timesubsets(base) -> list[str]:
    if "Opportunity" not in base:
        raise SystemExit("Missing 'Opportunity' table in DR base.")
    opp_tbl = base["Opportunity"]
    ts_tbl_name = _find_ts_table_name(base)
    if ts_tbl_name is None:
        return []
    ts_tbl = base[ts_tbl_name]

    titles: list[str] = []
    for opp in opp_tbl.records.values():
        links = []
        if hasattr(opp, "time_subsets"):
            links = opp.time_subsets
        elif hasattr(opp, "time_subset"):
            links = opp.time_subset

        has_ts = False
        for link in (links or []):
            rec_id = getattr(link, "record_id", link)
            if rec_id and ts_tbl.get_record(rec_id):
                has_ts = True
                break
        if has_ts:
            titles.append(opp.title.strip())

    return list(dict.fromkeys(titles))


def _extract_opportunity_time_subsets(base) -> tuple[dict[str, list[str]], dict[str, str]]:
    """Return:
        opp_subsets: {Opportunity title: [subset_label,...]}
        tag_periods: {subset_label: 'YYYY-YYYY'} 
    """
    if "Opportunity" not in base:
        raise SystemExit("Missing 'Opportunity' table in DR base.")
    opp_tbl = base["Opportunity"]
    ts_name = _find_ts_table_name(base)
    ts_tbl = base[ts_name] if ts_name else None

    opp_subsets: dict[str, list[str]] = {}
    for opp in opp_tbl.records.values():
        labels = []
        if ts_tbl and hasattr(opp, "time_subsets"):
            links = opp.time_subsets
        elif ts_tbl and hasattr(opp, "time_subset"):
            links = opp.time_subset
        else:
            links = []

        for link in (links or []):
            ts = ts_tbl.get_record(getattr(link, "record_id", link))
            if not ts:
                continue
            # choose best label
            label = None
            for k in ("label", "title", "description", "name"):
                v = getattr(ts, k, None)
                if isinstance(v, str) and v.strip():
                    label = v.strip()
                    break
            label = label or "subset"
            # Build a canonical period string (normalize UTF dashes to ASCII)
            period = patch_time_subset_periods(label, getattr(ts, "start", None), getattr(ts, "end", None))
            period = period.replace("–", "-")
            # we only need labels here (periods are predefined below)
            labels.append(label)

        if labels:
            known = [t for t in CANON_TS if t in labels]
            unknown = sorted([t for t in labels if t not in CANON_TS], key=str.lower)
            opp_subsets[opp.title.strip()] = known + unknown

    tag_periods = {
        "hist72": "1950-2021",
        "histext": "2022-2026",
        "scenario20mid": "2040-2059",
        "scenario30mid": "2040-2069",
        "scenario20": "2081-2100",
        "hist20": "2002-2021",
        "hist43": "1979-2021",
        "all": "Whole time series"
    }

    return opp_subsets, tag_periods


def _map_subsets_to_experiments(base, use_opps, opp_subsets: dict[str, list[str]]) -> dict[str, list[str]]:
    dreq_opps = base["Opportunity"]
    expt_groups = base["Experiment Group"]
    expts = base["Experiments"]
    opp_ids = dq.get_opp_ids(use_opps, dreq_opps, verbose=False)
    expt_subsets: dict[str, list[str]] = {}
    for opp_id in opp_ids:
        opp = dreq_opps.records[opp_id]
        labels = opp_subsets.get(opp.title.strip(), [])
        opp_expts = dq.get_opp_expts(opp, expt_groups, expts, verbose=False)
        for expt in opp_expts:
            L = expt_subsets.setdefault(expt, [])
            L.extend(labels)
    for expt, L in expt_subsets.items():
        uniq = list(dict.fromkeys(L))
        known = [t for t in CANON_TS if t in uniq]
        other = sorted([t for t in uniq if t not in CANON_TS], key=str.lower)
        expt_subsets[expt] = known + other
    return expt_subsets


# ---------------------------------------------------------------------
# Build Total block
# ---------------------------------------------------------------------
def _build_total_block(payload, time_tags):
    priorities = ["Core", "High", "Medium", "Low"]
    total = {
        "historical": {p: {} for p in priorities},
        "scenario": {p: {} for p in priorities},
        "AllExp": {p: {} for p in priorities},
    }

    def is_hist(name: str) -> bool:
        n = name.lower()
        return n == "historical" or n.startswith("hist")

    def is_scen(name: str) -> bool:
        n = name.lower()
        return n.startswith(("scen", "ssp", "scenario"))

    for expt, req in payload.get("experiment", {}).items():
        for p in priorities:
            if p not in req:
                continue
            for var in req[p]:
                tags = []
                if expt in time_tags and p in time_tags[expt]:
                    tags = time_tags[expt][p].get(var, [])
                total["AllExp"][p][var] = tags
                if is_hist(expt):
                    total["historical"][p][var] = tags
                if is_scen(expt):
                    total["scenario"][p][var] = tags

    # Remove empty priority blocks
    for block in ("historical", "scenario", "AllExp"):
        total[block] = {k: v for k, v in total[block].items() if v}
    return total


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(
        description=(
            "Export requested variables grouped by priority (all priorities), "
            "restricted to Opportunities with Time Subsets. Adds per-variable time-subset tags, "
            'and inserts "Subset periods" inside Header right after Description. '
            "Optionally adds a rolled-up Total block."
        )
    )
    p.add_argument("-o", "--outfile",
                   help="Output JSON path. Default: requested_<version>_cmip7names.timesubsetted.json")
    p.add_argument("--add-combined", action="store_true",
                   help="Add rolled-up Total block (historical/scenario/AllExp).")
    p.add_argument(
    "--prefer-version",
    default="latest_stable",
    help="Data Request version to load (default: latest_stable).",)
    p.add_argument("--quiet", action="store_true", help="Suppress verbose logging.")
    return p.parse_args()


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------
def main():
    args = parse_args()
    base, ver, content_path = _load_dr(args.prefer_version)
    opp_titles = _opportunity_titles_with_timesubsets(base)
    if not opp_titles:
        raise SystemExit("No Opportunities with Time Subsets found; nothing to export.")

    if not args.quiet:
        print(f"Found {len(opp_titles)} Opportunities with Time Subsets:")
        for t in sorted(opp_titles, key=str.lower):
            print("  -", t)

    # Build requested variables 
    expt_vars = dq.get_requested_variables(
        base, ver,
        use_opps=sorted(opp_titles, key=str.lower),
        priority_cutoff=args.priority_cutoff,
        verbose=not args.quiet,
        check_core_variables=False,
    )

    outfile = args.outfile or f"requested_{ver}_cmip7names.timesubsetted.json"

    # Write requested file
    dq.write_requested_vars_json(
        outfile,
        expt_vars,
        ver,
        priority_cutoff=args.priority_cutoff,
        content_path=content_path,
    )

    # Build time subset info
    opp_subsets, tag_periods = _extract_opportunity_time_subsets(base)
    expt_subsets = _map_subsets_to_experiments(base, sorted(opp_titles, key=str.lower), opp_subsets)

    # Load the canonical payload back
    with open(outfile, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Build timetags (if 'all' is present, it's the only tag)
    priorities = ["Core", "High", "Medium", "Low"]
    time_tags = {}
    for expt, req in payload.get("experiment", {}).items():
        tags = ["all"] + expt_subsets.get(expt, [])
        known = [t for t in CANON_TS if t in tags]
        other = sorted([t for t in tags if t not in CANON_TS and t != "all"], key=str.lower)
        tags_ordered = ["all"] + known + other
        if "all" in tags_ordered:
            tags_ordered = ["all"]

        time_tags[expt] = {}
        for p in priorities:
            if p in req:
                time_tags[expt][p] = {var: tags_ordered[:] for var in req[p]}

    orig_header = payload.get("Header", {})
    new_header = OrderedDict()

    if "Description" in orig_header:
        new_header["Description"] = orig_header["Description"]

    new_header["Subset periods"] = tag_periods  # subset periods info inserted after Description

    for k, v in orig_header.items():
        if k == "Description":
            continue
        new_header[k] = v

    # final payload
    final_payload = payload.copy()
    final_payload["Header"] = new_header
    final_payload["TimeTags"] = time_tags

    if args.add_combined:
        total_block = _build_total_block(payload, time_tags)
        final_payload["Total"] = total_block

    text = json.dumps(final_payload, indent=4, ensure_ascii=True)
    text = text.replace("–", "-").replace("—", "-")
    with open(outfile, "w", encoding="ascii") as f:
        f.write(text)
    print("Wrote:", outfile)


if __name__ == "__main__":
    main()