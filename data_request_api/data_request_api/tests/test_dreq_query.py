import os
import tempfile

import data_request_api.content.dreq_content as dc
import data_request_api.query.dreq_query as dq
import data_request_api.utilities.config as dreqcfg
import pytest
import yaml
from data_request_api.utilities.logger import change_log_file, change_log_level

# Configure logger for testing
change_log_file(default=True)
change_log_level("info")


@pytest.fixture(scope="function")
def temp_config_file(tmp_path_factory):
    temp_dir = tmp_path_factory.mktemp("data")
    config_file = temp_dir / ".CMIP7_data_request_api_config"
    cfg = {"cache_dir": str(temp_dir)}
    with open(config_file, "w") as f:
        yaml.dump(cfg, f)
    try:
        yield config_file
    finally:
        config_file.unlink(missing_ok=True)
        dreqcfg.CONFIG = {}


@pytest.fixture(scope="function")
def monkeypatch(monkeypatch):
    return monkeypatch


def test_get_requested_variables_time_subsets(temp_config_file, monkeypatch):
    dreqcfg.CONFIG = {}
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    dc._dreq_res = os.path.dirname(temp_config_file)
    dc.versions = {"tags": [], "branches": []}
    dc._versions_retrieved_last = {"tags": 0, "branches": 0}
    use_dreq_version = "v1.2.2.2"
    data = dc.load(use_dreq_version)
    assert dreqcfg.CONFIG == {
        **dreqcfg.DEFAULT_CONFIG,
        "cache_dir": str(os.path.dirname(temp_config_file)),
    }
    base = dq.create_dreq_tables_for_request(data, use_dreq_version)

    # Select opportunities
    dreq_opps = base["Opportunity"]
    all_opp_ids = [opp.opportunity_id for opp in dreq_opps.records.values()]
    assert len(all_opp_ids) == len(set(all_opp_ids))
    oppid2title = {
        int(opp.opportunity_id): opp.title for opp in dreq_opps.records.values()
    }
    opp_ids = [1, 69, 20]
    use_opps = []
    for opp_id in opp_ids:
        use_opps.append(oppid2title[opp_id])

    # Run get_requested_variables
    no_ts = dq.get_requested_variables(
        base, use_dreq_version, use_opps=use_opps, time_subsets=False, verbose=False
    )
    inc_ts = dq.get_requested_variables(
        base, use_dreq_version, use_opps=use_opps, time_subsets=True, verbose=False
    )

    # Check that time subsets are included and that the same variables are included
    assert list(inc_ts["experiment"].keys()) == list(no_ts["experiment"].keys())
    for exp, req in inc_ts["experiment"].items():
        assert all(req["Core"][i] == ["all"] for i in req["Core"].keys())
        for prio in ["Core", "High", "Medium", "Low"]:
            # This may actually not be true depending on the selected opportunities and dreq version:
            #   one opp could request a variable for time subset hist72 at medium priority and another
            #   one the same variable for hist36 at High priority
            assert list(req[prio].keys()) == no_ts["experiment"][exp][prio]


def test_get_requested_variables_combined_request(temp_config_file, monkeypatch):
    dreqcfg.CONFIG = {}
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    dc._dreq_res = os.path.dirname(temp_config_file)
    dc.versions = {"tags": [], "branches": []}
    dc._versions_retrieved_last = {"tags": 0, "branches": 0}
    use_dreq_version = "v1.2.2.2"
    data = dc.load(use_dreq_version)
    assert dreqcfg.CONFIG == {
        **dreqcfg.DEFAULT_CONFIG,
        "cache_dir": str(os.path.dirname(temp_config_file)),
    }
    base = dq.create_dreq_tables_for_request(data, use_dreq_version)

    # Run get_requested_variables
    no_cr = dq.get_requested_variables(
        base,
        use_dreq_version,
        use_opps="all",
        time_subsets=False,
        combined_request=False,
        verbose=False,
    )
    inc_cr = dq.get_requested_variables(
        base,
        use_dreq_version,
        use_opps="all",
        time_subsets=False,
        combined_request=True,
        verbose=False,
    )

    # Check that time subsets are included and that the same variables are included
    assert sorted(list(inc_cr["experiment"].keys())) == sorted(
        list(no_cr["experiment"].keys())
        + ["all_experiments", "historical_experiments", "scenario_experiments"]
    )
    joint_request = dict()
    for prio in ["Core", "High", "Medium", "Low"]:
        joint_request[prio] = [
            var for prioreq in no_cr["experiment"].values() for var in prioreq[prio]
        ]
        joint_request[prio] = set(joint_request[prio])

    # Remove higher priority vars from low priority requests
    joint_request["High"] = joint_request["High"].difference(joint_request["Core"])

    joint_request["Medium"] = joint_request["Medium"].difference(joint_request["Core"])
    joint_request["Medium"] = joint_request["Medium"].difference(joint_request["High"])

    joint_request["Low"] = joint_request["Low"].difference(joint_request["Core"])
    joint_request["Low"] = joint_request["Low"].difference(joint_request["High"])
    joint_request["Low"] = joint_request["Low"].difference(joint_request["Medium"])

    # Check that all variables are included in the joint request
    for prio in ["Core", "High", "Medium", "Low"]:
        assert set(joint_request[prio]) == set(
            inc_cr["experiment"]["all_experiments"][prio]
        )


def test_get_requested_variables_time_subsets_combined_request(
    temp_config_file, monkeypatch
):
    dreqcfg.CONFIG = {}
    monkeypatch.setattr(
        "data_request_api.utilities.config.CONFIG_FILE", temp_config_file
    )
    dc._dreq_res = os.path.dirname(temp_config_file)
    dc.versions = {"tags": [], "branches": []}
    dc._versions_retrieved_last = {"tags": 0, "branches": 0}
    use_dreq_version = "v1.2.2.2"
    data = dc.load(use_dreq_version)
    assert dreqcfg.CONFIG == {
        **dreqcfg.DEFAULT_CONFIG,
        "cache_dir": str(os.path.dirname(temp_config_file)),
    }
    base = dq.create_dreq_tables_for_request(data, use_dreq_version)

    # Run get_requested_variables
    tscr = dq.get_requested_variables(
        base,
        use_dreq_version,
        use_opps="all",
        time_subsets=True,
        combined_request=True,
        verbose=False,
    )

    # Check that time subsets are included and that the same variables are included
    assert all(
        exp in tscr["experiment"].keys()
        for exp in ["all_experiments", "historical_experiments", "scenario_experiments"]
    )

    # Loop over all experiments
    #  We expect to find "duplicates": variables that are requested in multiple
    #    priority levels with differing time_subsets for one and the same experiment
    #    if we consider all opportunities
    duplicate_found = False
    for e in tscr["experiment"]:
        seen = {}

        for p in tscr["experiment"][e]:
            for v in tscr["experiment"][e][p]:
                try:
                    if v in seen:
                        duplicate_found = True
                        seen[v].append((p, tscr["experiment"][e][p][v]))
                    else:
                        seen[v] = [(p, tscr["experiment"][e][p][v])]
                except TypeError:
                    # This branch handles unhashable values
                    if v in seen:
                        duplicate_found = True
                        seen[v].append(p)
                    else:
                        seen[v] = [p]

    assert duplicate_found, "No 'duplicates' found in time subsets combined request"
