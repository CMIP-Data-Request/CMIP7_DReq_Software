import re
import sys
from collections import defaultdict

import data_request_api.content.consolidate_export as ce
import data_request_api.content.dreq_content as dc
from data_request_api.utilities.logger import (
    change_log_file,
    change_log_level,
    get_logger,
)

# Print consolidation log and full list of unmatched records
long_summary = True

change_log_file(default=True)
if long_summary:
    change_log_level("debug")
else:
    change_log_level("critical")
logger = get_logger()

if len(sys.argv) > 1:
    version = sys.argv[1]
else:
    print(
        "Please provide a version as first argument and optionally 'md' as second argument to generate markdown output:"
    )
    print("python", sys.argv[0], "<version> [md]")
    sys.exit(1)

# Whether to use Markdown/html formatting
if len(sys.argv) > 2 and sys.argv[2] == "md":
    h1s = "<h1>"
    h1e = "</h1>"
    h2s = "<h2>"
    h2e = "</h2>"
    h3s = "<h3>"
    h3e = "</h3>"
    h4s = "<h4>"
    h4e = "</h4>"
    dets = "<details>"
    dete = "</details>"
    sums = "<summary>"
    sume = "</summary>"
    code = "```"
    code1 = "`"
elif len(sys.argv) > 2 and sys.argv[2] != "md":
    print("ERROR Unknown argument:", sys.argv[2])
else:
    h1s = ""
    h1e = ""
    h2s = ""
    h2e = ""
    h3s = ""
    h3e = ""
    h4s = ""
    h4e = ""
    dets = ""
    dete = ""
    sums = ""
    sume = ""
    code = ""
    code1 = ""

offlineRAW = version in dc.get_cached(export="raw")
offlineREL = version in dc.get_cached(export="release")

if not h1s:
    print("#" * 50)
print(f"{h1s}Checking consolidation of '{version}'{h1e}")
if not h1s:
    print("#" * 50)
print(f"{dets}")


# Load raw export with consolidation
if long_summary:
    if not h1s:
        print("-" * 50)
    print(f"{sums}{h2s}Consolidation log for raw export{h2e}{sume}")
    if not h1s:
        print("-" * 50)
    if code:
        print()
    print(f"{code}")
dreqraw = dc.load(
    version,
    export="raw",
    consolidate=True,
    offline=offlineRAW,
    force_consolidate=True,
)
if long_summary:
    print(f"{code}")
    if code:
        print()
    print(f"{dete}")
    if dete:
        print()

# Load release export with consolidation
if long_summary:
    print(f"{dets}")
    if dets:
        print()
    if not h1s:
        print("-" * 50)
    print(f"{sums}{h2s}Consolidation log for release export{h2e}{sume}")
    if not h1s:
        print("-" * 50)
    if code:
        print()
    print(f"{code}")
dreqrel = dc.load(
    version, export="release", consolidate=True, offline=offlineREL
)
if long_summary:
    print(f"{code}")
    if code:
        print()
    print(f"{dete}")
    if dete:
        print()


def compare_dicts(raw, rel):
    print()
    rid_uid_map_raw = ce._gen_rid_uid_map(raw["Data Request"])
    rid_uid_map_rel = ce._gen_rid_uid_map(rel["Data Request"])
    print(f"- {len(ce.filtered_records)} filtered records")
    print(
        f"- {len(rid_uid_map_raw.keys())} rid->UID mapping entries (raw export)"
    )
    print(
        f"- {len(rid_uid_map_rel.keys())} rid->UID mapping entries (release export)"
    )
    print()

    if len(raw["Data Request"].keys()) != len(rel["Data Request"].keys()):
        print("ERROR: Different number of tables")
    if raw["Data Request"]["version"] != rel["Data Request"]["version"]:
        print("ERROR: Differing versions")

    # Clear version
    version = raw["Data Request"].pop("version")
    rel["Data Request"].pop("version")

    # Collect differences in dictionaries
    matches = defaultdict(lambda: defaultdict())
    matches_uid = defaultdict(lambda: defaultdict())
    examples = defaultdict(lambda: defaultdict())
    diff_fields_count = defaultdict(lambda: defaultdict(int))
    diff_string_count = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))
    )
    diff_rec_count = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    diff_rec = defaultdict(
        lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    )

    # Comparison for each table and field and record
    for table_i in raw["Data Request"]:
        print()
        print("-" * 50)
        print(
            f'{table_i}    (# records - raw: {len(raw["Data Request"][table_i]["records"].keys())} - release: {len(rel["Data Request"][table_i]["records"].keys())})'
        )
        print("-" * 50)
        print()
        if table_i not in rel["Data Request"]:
            print(
                f"ERROR: '{table_i}' is missing or named differently in release export"
            )
            continue

        # Compare table definition
        #  todo

        # Compare fields definition
        #  todo

        # Compare records
        nomatch = defaultdict(list)
        mltmatch = defaultdict(list)
        for rawid, rawrec in raw["Data Request"][table_i]["records"].items():
            # CMIP7 Compound Name is in raw export only for v1.2
            if version == "v1.2" and table_i == "Variables":
                rawrec.pop("CMIP7 Compound Name")

            # Match raw and release records via UID (not possible pre v1.2)
            relid = [
                rid
                for rid in rel["Data Request"][table_i]["records"].keys()
                if rel["Data Request"][table_i]["records"][rid]["UID"]
                == rawrec["UID"]
            ]
            if len(relid) == 0:
                nomatch[table_i].append(rawrec["UID"])
                continue
            elif len(relid) > 1:
                mltmatch[table_i].append(rawrec["UID"])
            relid = relid[0]
            relrec = rel["Data Request"][table_i]["records"][relid]
            matches_uid[table_i][rawid] = relid

            # "Image" field in Opportunity table is a nested dictionary and not relevant - so skip this field
            if table_i == "Opportunity" and "Image" in relrec:
                relrec.pop("Image")
            if table_i == "Opportunity" and "Image" in rawrec:
                rawrec.pop("Image")

            # Compare records to find fields that differ
            # Distinguish
            #  - match: all fields match
            #  - fmatch: current field matches
            # If fields reference other record(s), compare only referenced UIDs
            match = True
            for fld in set(rawrec.keys()) | set(relrec.keys()):
                fmatch = True
                if fld not in relrec.keys():
                    if rawrec[fld]:
                        match = False
                        fmatch = False
                        if isinstance(rawrec[fld], list) and any(
                            [item.startswith("rec") for item in rawrec[fld]]
                        ):
                            diff_rec_count[table_i][fld]["rawmore"] += 1
                            diff_rec_count[table_i][fld]["rawmoreuids"] += 1
                            rawuids = {
                                rid_uid_map_raw[ridx] for ridx in rawrec[fld]
                            }
                            diff_rec[table_i][fld]["raw"][rawrec["UID"]] = list(
                                rawuids
                            )
                    else:
                        continue
                elif fld not in rawrec.keys():
                    if relrec[fld]:
                        match = False
                        fmatch = False
                        if isinstance(relrec[fld], list) and any(
                            [item.startswith("rec") for item in relrec[fld]]
                        ):
                            diff_rec_count[table_i][fld]["relmore"] += 1
                            diff_rec_count[table_i][fld]["relmoreuids"] += 1
                            reluids = {
                                rid_uid_map_rel[ridx] for ridx in relrec[fld]
                            }
                            diff_rec[table_i][fld]["rel"][relrec["UID"]] = list(
                                reluids
                            )
                    else:
                        continue
                elif not rawrec[fld] and not relrec[fld]:
                    continue
                elif not isinstance(rawrec[fld], type(relrec[fld])) and (
                    rawrec[fld] or relrec[fld]
                ):
                    match = False
                    fmatch = False
                elif isinstance(rawrec[fld], list) and any(
                    [
                        item.startswith("rec")
                        for item in rawrec[fld]
                        if isinstance(item, str)
                    ]
                ):
                    rawuids = {rid_uid_map_raw[ridx] for ridx in rawrec[fld]}
                    reluids = {rid_uid_map_rel[ridx] for ridx in relrec[fld]}
                    if not len(rawrec[fld]) == len(relrec[fld]):
                        match = False
                        fmatch = False
                        if len(rawrec[fld]) > len(relrec[fld]):
                            diff_rec_count[table_i][fld]["rawmore"] += 1
                        else:
                            diff_rec_count[table_i][fld]["relmore"] += 1
                        if len(
                            [
                                rid
                                for rid in rawrec[fld]
                                if rid not in ce.filtered_records
                            ]
                        ) < len(rawrec[fld]):
                            diff_rec_count[table_i][fld]["unfiltered"] += 1
                            diff_rec_count[table_i][fld][rawrec["UID"]] = len(
                                rawrec[fld]
                            ) - len(
                                [
                                    rid
                                    for rid in rawrec[fld]
                                    if rid not in ce.filtered_records
                                ]
                            )
                    if len(rawuids) == len(reluids):
                        diff_rec_count[table_i][fld]["samenruids"] += 1
                    if rawuids != reluids:
                        match = False
                        fmatch = False
                        diff_rec[table_i][fld]["raw"][rawrec["UID"]] = [
                            uid for uid in rawuids if uid not in reluids
                        ]
                        diff_rec[table_i][fld]["rel"][relrec["UID"]] = [
                            uid for uid in reluids if uid not in rawuids
                        ]
                        if len(rawuids) > len(reluids):
                            diff_rec_count[table_i][fld]["rawmoreuids"] += 1
                        elif len(rawuids) < len(reluids):
                            diff_rec_count[table_i][fld]["relmoreuids"] += 1
                    else:
                        diff_rec_count[table_i][fld]["sameuids"] += 1
                elif isinstance(rawrec[fld], list):
                    if not sorted(rawrec[fld]) == sorted(relrec[fld]):
                        match = False
                        fmatch = False
                elif rawrec[fld] != relrec[fld]:
                    match = False
                    fmatch = False
                    if isinstance(rawrec[fld], str):
                        if re.sub(r"\s+", "", rawrec[fld]) == re.sub(
                            r"\s+", "", relrec[fld]
                        ):
                            diff_string_count[table_i][fld]["ws"] += 1
                        elif rawrec[fld].lower() == relrec[fld].lower():
                            diff_string_count[table_i][fld]["c"] += 1
                        elif (
                            re.sub(r"\s+", "", rawrec[fld]).lower()
                            == re.sub(r"\s+", "", relrec[fld]).lower()
                        ):
                            diff_string_count[table_i][fld]["wsc"] += 1
                if not fmatch:
                    examples[table_i][fld] = [
                        rawrec[fld] if fld in rawrec else "UNDEFINED",
                        relrec[fld] if fld in relrec else "UNDEFINED",
                        rawrec["UID"],
                    ]
                    diff_fields_count[table_i][fld] += 1
            if match:
                matches[table_i][rawid] = relid

        print(f"Perfect matches: {len(list(set(matches[table_i].keys())))}")
        if len(list(set(matches[table_i].keys()))) != len(
            raw["Data Request"][table_i]["records"].keys()
        ):
            print(
                f"Matches by UID: {len(list(set(matches_uid[table_i].keys())))}"
            )
        # release UIDs not in raw
        rel_unique = [
            rid_uid_map_rel[rel_recid]
            for rel_recid in rel["Data Request"][table_i]["records"].keys()
            if rid_uid_map_rel[rel_recid]
            not in [
                rid_uid_map_raw[raw_recid]
                for raw_recid in raw["Data Request"][table_i]["records"].keys()
            ]
        ]
        if rel_unique:
            print(dets)
            print(
                f"{sums}Unique UIDs in release export: {len(rel_unique)}{sume}"
            )
            print()
            for uid in sorted(rel_unique):
                print(f"  - {uid}")
            print(dete)
        # raw UIDs not in release
        if nomatch[table_i]:
            if long_summary:
                print(dets)
                print(f"{sums}No matches: {len(nomatch[table_i])}{sume}")
                print()
                for uid in nomatch[table_i]:
                    print(f"  - {uid}")
                print(dete)
            else:
                print(f"No matches: {len(nomatch[table_i])}")
        if mltmatch[table_i]:
            if long_summary:
                print(dets)
                print(f"{sums}Multiple matches: {len(mltmatch[table_i])}{sume}")
                print()
                for uid in mltmatch[table_i]:
                    print(f"  - {uid}")
                print(dete)
            else:
                print(f"Multiple matches: {len(mltmatch[table_i])}")
        if len(examples[table_i].keys()) > 0:
            print()
            print(f"{h4s}Differences occurred for the following fields:{h4e}")
            print()
            for fld in diff_fields_count[table_i]:
                diffstr = ""
                if diff_string_count[table_i][fld]["ws"]:
                    diffstr += (
                        f"whitespace {diff_string_count[table_i][fld]['ws']}, "
                    )
                if diff_string_count[table_i][fld]["c"]:
                    diffstr += f"case {diff_string_count[table_i][fld]['c']}, "
                if diff_string_count[table_i][fld]["wsc"]:
                    diffstr += f"whitespace&case {diff_string_count[table_i][fld]['wsc']}, "
                diffrecs = ""
                if diff_rec_count[table_i][fld]["rawmore"]:
                    diffrecs += f" (more records in raw export in {diff_rec_count[table_i][fld]['rawmore']} cases)"
                if diff_rec_count[table_i][fld]["unfiltered"]:
                    diffrecs += f" (unfiltered records encountered {diff_rec_count[table_i][fld]['unfiltered']} times)"
                    if (
                        diff_rec_count[table_i][fld]["rawmore"]
                        + diff_rec_count[table_i][fld]["relmore"]
                        != diff_fields_count[table_i][fld]
                    ):
                        print(
                            f"ERROR counting differences for '{table_i}'@'{fld}': {diff_rec_count[table_i][fld]['rawmore']} + {diff_rec_count[table_i][fld]['relmore']} != {diff_fields_count[table_i][fld]}"
                        )
                if diff_rec_count[table_i][fld]["rawmoreuids"]:
                    diffrecs += f" (More UIDs raw: {diff_rec_count[table_i][fld]['rawmoreuids']} cases)"
                if diff_rec_count[table_i][fld]["relmoreuids"]:
                    diffrecs += f" (More UIDs release: {diff_rec_count[table_i][fld]['relmoreuids']} cases)"
                if diff_rec_count[table_i][fld]["samenruids"]:
                    diffrecs += f" (Same number of UIDs: {diff_rec_count[table_i][fld]['samenruids']} cases)"
                if diff_rec_count[table_i][fld]["sameuids"]:
                    diffrecs += f" (Exact same UIDs: {diff_rec_count[table_i][fld]['sameuids']} cases)"
                print(
                    f"- {diff_fields_count[table_i][fld]} for field '{fld}' {'(Differences only in: ' + diffstr.strip(', ') + ')' if diffstr else ''}{diffrecs if diffrecs else ''}"
                )
            if dets:
                print()
            print(dets)
            print(f"{sums}Examples:{sume}")
            if dets:
                print()
            for fld in examples[table_i].keys():
                print(
                    f"{h4s}Field '{fld}' in table '{table_i}'       UID: '{examples[table_i][fld][2]}'{h4e}"
                )
                if code:
                    print()
                if isinstance(examples[table_i][fld][1], list) and any(
                    [
                        item.startswith("rec")
                        for item in examples[table_i][fld][1]
                        if isinstance(item, str)
                    ]
                ):
                    print(
                        f"- release: List of record ids with {len(examples[table_i][fld][1])} elements"
                    )
                    print(
                        f"  - unique UIDs in release {diff_rec[table_i][fld]['rel'][examples[table_i][fld][2]]}"
                    )
                elif isinstance(examples[table_i][fld][1], str):
                    print("- release:")
                    if code:
                        print()
                    print(code)
                    print(f"'{examples[table_i][fld][1]}'")
                    print(code)
                    if code:
                        print()
                else:
                    print(
                        f"- release: {code1}{examples[table_i][fld][1]}{code1}"
                    )
                if isinstance(examples[table_i][fld][0], list) and any(
                    [
                        item.startswith("rec")
                        for item in examples[table_i][fld][0]
                        if isinstance(item, str)
                    ]
                ):
                    print(
                        f"- raw: List of record ids with {len(examples[table_i][fld][0])} elements"
                    )
                    print(
                        f"  - unique UIDs in raw {diff_rec[table_i][fld]['raw'][examples[table_i][fld][2]]}"
                    )
                elif isinstance(examples[table_i][fld][0], str):
                    print("- raw:")
                    if code:
                        print()
                    print(code)
                    print(f"'{examples[table_i][fld][0]}'")
                    print(code)
                    if code:
                        print()
                else:
                    print(f"- raw: {code1}{examples[table_i][fld][0]}{code1}")
            if dete:
                print()
            if dete:
                print(dete)
            if dete:
                print()
            printsummary = False
            for fld in examples[table_i].keys():
                if (
                    isinstance(examples[table_i][fld][1], list)
                    and any(
                        [
                            item.startswith("rec")
                            for item in examples[table_i][fld][1]
                            if isinstance(item, str)
                        ]
                    )
                ) or (
                    isinstance(examples[table_i][fld][0], list)
                    and any(
                        [
                            item.startswith("rec")
                            for item in examples[table_i][fld][0]
                            if isinstance(item, str)
                        ]
                    )
                ):
                    printfld = False
                    uidlist = []
                    if diff_rec[table_i][fld]["raw"]:
                        uidlist.extend(
                            list(diff_rec[table_i][fld]["raw"].keys())
                        )
                    if diff_rec[table_i][fld]["rel"]:
                        uidlist.extend(
                            list(diff_rec[table_i][fld]["rel"].keys())
                        )
                    for uid in set(uidlist):
                        if (
                            diff_rec[table_i][fld]["raw"][uid]
                            or diff_rec[table_i][fld]["rel"][uid]
                        ):
                            if not printsummary:
                                if dets:
                                    print()
                                print(dets)
                                print(
                                    f"{sums}Full differences in record references (listed as UIDs):{sume}"
                                )
                                print()
                                printsummary = True
                            if not printfld:
                                print(f"- '{fld}' ({table_i})")
                                printfld = True
                            print(f"  - {uid}")
                            if diff_rec[table_i][fld]["raw"][uid]:
                                print(
                                    f"    - unique in raw ({len(diff_rec[table_i][fld]['raw'][uid])}):",
                                    diff_rec[table_i][fld]["raw"][uid],
                                )
                            if diff_rec[table_i][fld]["rel"][uid]:
                                print(
                                    f"    - unique in release ({len(diff_rec[table_i][fld]['rel'][uid])}):",
                                    diff_rec[table_i][fld]["rel"][uid],
                                )
            if printsummary:
                print(dete)
                if dete:
                    print()


compare_dicts(dreqraw, dreqrel)
