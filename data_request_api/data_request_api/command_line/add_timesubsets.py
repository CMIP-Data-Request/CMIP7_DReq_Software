# add_timesubsets.py
# Helper utilities to augment a requested-variables JSON with time-subset tags

from __future__ import annotations
import json
from collections import OrderedDict
from typing import Iterable, Union, List, Dict, Any
from data_request_api.query import dreq_query as dq


# ---------- internal helpers ----------
def _find_ts_table_name(base) -> str | None:
    for name in ("Time Subset", "Time Subsets", "time_subsets"):
        if name in base:
            return name
    return None

def _opportunity_titles_with_timesubsets(base) -> list[str]:
    """All opportunity titles that link to at least one time subset."""
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


def _collect_opportunity_ts_labels(base) -> Dict[str, List[str]]:
    """
    Return: {Opportunity title: [subset_label, ...]}
    Uses labels exactly as specified in the DR.
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
            label = None
            for k in ("label", "title", "description", "name"):
                v = getattr(ts, k, None)
                if isinstance(v, str) and v.strip():
                    label = v.strip()
                    break
            label = label or "subset"
            labels.append(label)

        if labels:
            opp_subsets[opp.title.strip()] = list(dict.fromkeys(labels))

    return opp_subsets


def _map_subsets_to_experiments(
    base,
    use_opps: Union[str, Iterable[str]],
    opp_subsets: Dict[str, List[str]],
) -> Dict[str, List[str]]:
    """
    Build union of time-subset labels per experiment across the selected opportunities.
    Returns: {experiment_name: [distinct_labels]}
    """
    dreq_opps = base["Opportunity"]
    expt_groups = base["Experiment Group"]
    expts = base["Experiments"]

    # resolve 'all' to the title set
    if use_opps == "all":
        want_titles = [opp.title.strip() for opp in dreq_opps.records.values()]
    else:
        want_titles = [t.strip() for t in use_opps]

    # Only opportunities that actually have time subsets
    titles_with_ts = set(_opportunity_titles_with_timesubsets(base))
    want_titles = [t for t in want_titles if t in titles_with_ts]

    opp_ids = dq.get_opp_ids(want_titles, dreq_opps, verbose=False)
    expt_subsets: dict[str, list[str]] = {}

    for opp_id in opp_ids:
        opp = dreq_opps.records[opp_id]
        labels = opp_subsets.get(opp.title.strip(), [])
        
        # CMIP7 helper present in this repo; returns experiment NAMES (strings)
        opp_expts = dq.get_opp_expts(opp, expt_groups, expts, verbose=False)
        for expt in opp_expts:
            L = expt_subsets.setdefault(expt, [])
            L.extend(labels)

    for expt, L in expt_subsets.items():
        expt_subsets[expt] = list(dict.fromkeys(L))

    return expt_subsets


# ---------- Total builders ----------

def build_total_tag_aware(
    *,
    payload: Dict[str, Any],
    time_tags: Dict[str, Dict[str, Dict[str, List[str]]]]
) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    """Tag-aware Total block: {block: {priority: {var: [tags...]}}}"""
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
                tags = time_tags.get(expt, {}).get(p, {}).get(var, [])
                total["AllExp"][p][var] = tags
                if is_hist(expt):
                    total["historical"][p][var] = tags
                if is_scen(expt):
                    total["scenario"][p][var] = tags

    # Remove empty priority blocks
    for block in ("historical", "scenario", "AllExp"):
        total[block] = {k: v for k, v in total[block].items() if v}
    return total


def build_total_tag_agnostic(*, payload: Dict[str, Any]) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    """Tag-agnostic Total block: variables map to empty lists."""
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
                total["AllExp"][p][var] = []
                if is_hist(expt):
                    total["historical"][p][var] = []
                if is_scen(expt):
                    total["scenario"][p][var] = []

    for block in ("historical", "scenario", "AllExp"):
        total[block] = {k: v for k, v in total[block].items() if v}
    return total


# ---------- TimeTags builder ----------

def compute_time_tags_for_experiments(
    *,
    base,
    experiments_block: Dict[str, Dict[str, List[str]]],
    use_opps: Union[str, Iterable[str]],
) -> Dict[str, Dict[str, Dict[str, List[str]]]]:
    """
    Return TimeTags: {experiment: {priority: {var: [labels...]}}}
    - Use only labels linked via selected Opportunities.
    - If none → ["all"].
    - No canonicalization or invention of labels.
    """
    opp_subsets = _collect_opportunity_ts_labels(base)
    expt_subsets = _map_subsets_to_experiments(base, use_opps, opp_subsets)
    priorities = ["Core", "High", "Medium", "Low"]

    time_tags: Dict[str, Dict[str, Dict[str, List[str]]]] = {}
    for expt, req in experiments_block.items():
        labels = expt_subsets.get(expt, [])
        tags_for_vars = labels[:] if labels else ["all"]

        ex_tags: Dict[str, Dict[str, List[str]]] = {}
        for p in priorities:
            if p not in req:
                continue
            ex_tags[p] = {var: tags_for_vars[:] for var in req[p]}
        if ex_tags:
            time_tags[expt] = ex_tags

    return time_tags


# ---------- public API ----------

def augment_file_in_place(
    *,
    base,
    outfile: str,
    add_combined: bool = False,
    add_time_tags: bool = True,
    quiet: bool = True,
    use_opps: Union[str, Iterable[str]] = "all",
) -> None:
    """
    Read an already-written requested_*.json, attach TimeTags and/or Total.

    Rules:
      - TimeTags: only union of DR-provided time-subset labels across selected Opportunities.
      - If an experiment has NO labels, tag list is ["all"].
      - Total is tag-aware iff TimeTags are present; otherwise tag-agnostic.
    """
    with open(outfile, "r", encoding="utf-8") as f:
        payload = json.load(f)

    final_payload = payload.copy()
    time_tags = None

    if add_time_tags:
        time_tags = compute_time_tags_for_experiments(
            base=base, experiments_block=payload.get("experiment", {}), use_opps=use_opps
        )
        final_payload["TimeTags"] = time_tags

    if add_combined:
        if add_time_tags and time_tags is not None:
            final_payload["Total"] = build_total_tag_aware(payload=payload, time_tags=time_tags)
        else:
            final_payload["Total"] = build_total_tag_agnostic(payload=payload)

    text = json.dumps(final_payload, indent=4, ensure_ascii=True)
    with open(outfile, "w", encoding="ascii") as f:
        f.write(text)

    if not quiet:
        print(f"Updated {outfile}")