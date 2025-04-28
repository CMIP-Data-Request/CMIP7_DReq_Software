import sys

import data_request_api.content.consolidate_export as ce
import data_request_api.content.dreq_content as dc
from data_request_api.utilities.logger import (
    change_log_file,
    change_log_level,
    get_logger,
)

change_log_file(default=True)
change_log_level("debug")
logger = get_logger()

if len(sys.argv) > 1:
    version = sys.argv[1]
else:
    print("Please provide a version as an argument:")
    print("python", sys.argv[0], "<version>")
    sys.exit(1)

offlineRAW = version in dc.get_cached(export="raw")
offlineREL = version in dc.get_cached(export="release")

rel = dc.load(version, export="release", consolidate=True, offline=offlineREL)
rel["Data Request"].pop("version")
raw = dc.load(
    version,
    export="raw",
    consolidate=True,
    offline=offlineRAW,
    force_consolidate=True,
)
raw["Data Request"].pop("version")

print()
print()
print()
print("#-" * 25)
print("#-" + " " * 45 + "-#-")
print(f"#- Consolidation check results for '{version}':")
print("#-" + " " * 45 + "-#-")
print("#-" * 25)
print()
print("-" * 50)
print(f"Tables and #records in release export / {version}")
print("-" * 50)
reldict = dict()
for i in sorted(rel["Data Request"].keys()):
    print(i, len(rel["Data Request"][i]["records"]))
    reldict[i] = len(rel["Data Request"][i]["records"])

print("-" * 50)
print(f"Tables and #records in raw export / {version}")
print("-" * 50)
rawdict = dict()
for i in sorted(raw["Data Request"].keys()):
    print(i, len(raw["Data Request"][i]["records"]))
    rawdict[i] = len(raw["Data Request"][i]["records"])

print()
print("-" * 50)
print("Differences:")
print("-" * 50)
print(
    "Tables exclusive for raw export:",
    [i for i in rawdict.keys() if i not in reldict.keys()],
)
print()
print(
    "Tables exclusive for release export:",
    [i for i in reldict.keys() if i not in rawdict.keys()],
)
print()
print("Differences in the number of records per table:")
for i in sorted(raw["Data Request"].keys()):
    if i in reldict.keys():
        if rawdict[i] != reldict[i]:
            print(i, "- raw:", rawdict[i], " | release:", reldict[i])
print()
print("-" * 50)
print("Differences in the fields per table:")
print("-" * 50)
# Compare fields
for i in sorted(raw["Data Request"].keys()):
    fields_rel = list()
    fields_raw = list()
    for idrel in rel["Data Request"][i]["records"].keys():
        for f in rel["Data Request"][i]["records"][idrel].keys():
            fields_rel.append(f)
    for idraw in raw["Data Request"][i]["records"].keys():
        for f in raw["Data Request"][i]["records"][idraw].keys():
            fields_raw.append(f)
    fields_rel = sorted(list(set(fields_rel)))
    fields_raw = sorted(list(set(fields_raw)))
    only_fields_rel = [k for k in fields_rel if k not in fields_raw]
    only_fields_raw = [k for k in fields_raw if k not in fields_rel]
    if only_fields_rel or only_fields_raw:
        print("-------------------------------------------")
        print(i)
        print("-------------------------------------------")
        print("Fields of release export:")
        print(fields_rel)
        print()
        print("Fields of raw export:")
        print(fields_raw)
        print()
        print("-> Fields exclusive for release export:")
        print([k for k in fields_rel if k not in fields_raw])
        print()
        print("-> Fields exclusive for raw export:")
        print([k for k in fields_raw if k not in fields_rel])
        print()
