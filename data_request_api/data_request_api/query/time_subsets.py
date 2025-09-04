# data_request_api/query/time_subsets.py
from __future__ import annotations

def get_timeperiod(subset_key: str) -> str:
    """
    Return the time period for a given subset key.
    """
    mapping = {
        "all": "Whole time series",
        "hist20": "2002–2021",
        "hist43": "1979–2021",
        "hist72": "1950–2021",
        "histext": "2022–2026 (Extended historical period)",
        "scenario20": "2081–2100",
        "scenario20mid": "2040–2059",
        "scenario30mid": "2040–2069",
    }
    return mapping.get(subset_key, "Unknown subset")


def patch_time_subset_periods(
    name_or_label: str | None,
    start: int | str | None,
    end: int | str | None
) -> str:
    """
    Build a canonical 'period' string for a time subset:
    - If numeric (start,end) exist, prefer "start–end".
    - Else infer from a known tag present in the name/label using get_timeperiod.
    - Else return "Unknown subset".
    """
    # Prefer explicit numeric bounds
    if start is not None and end is not None:
        try:
            return f"{int(start)}–{int(end)}"
        except Exception:
            return f"{start}–{end}"

    # Fall back to inferring from the label
    if isinstance(name_or_label, str):
        label = name_or_label.strip()
        known = (
            "hist20", "hist43", "hist72", "histext",
            "scenario20mid", "scenario30mid", "scenario20", "all"
        )
        if label in known:
            return get_timeperiod(label)
        for tag in known:
            if tag in label:
                return get_timeperiod(tag)

    return "Unknown subset"
