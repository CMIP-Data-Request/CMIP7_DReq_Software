import json
import os
import subprocess
import sys
from pathlib import Path

import data_request_api.content.dreq_content as dc
import pytest
import yaml


@pytest.fixture(scope="class")
def monkeyclass():
    with pytest.MonkeyPatch.context() as mp:
        yield mp


@pytest.fixture(scope="class")
def temp_config_file(tmp_path_factory, monkeyclass):
    temp_dir = tmp_path_factory.mktemp("data")
    config_file = temp_dir / ".CMIP7_data_request_api_config"
    monkeyclass.setenv("CMIP7_DR_API_CONFIGFILE", str(config_file))
    # Provide the test with the config file
    try:
        yield config_file
    finally:
        config_file.unlink(missing_ok=True)


@pytest.fixture(scope="class")
def consolidate(request):
    # "consolidate" or "no consolidate"
    return request.param


@pytest.mark.parametrize(
    "consolidate",
    ["consolidate", "no consolidate"],
    indirect=True,
    scope="class",
)
class TestExportDreqListsJson:
    @pytest.fixture(scope="function", autouse=True)
    def setup_method(self, request):
        # Initialize config and load v1.2.2 content version
        self.temp_config_file = request.getfixturevalue("temp_config_file")
        self.consolidate = request.getfixturevalue("consolidate")
        with open(self.temp_config_file, "w") as fh:
            config = {
                "consolidate": self.consolidate == "consolidate",
                "cache_dir": str(self.temp_config_file.parent),
            }
            yaml.dump(config, fh)
        dc.load("v1.2.2")

    def test_export_dreq_lists_json(self, temp_config_file, consolidate):
        ofile = temp_config_file.parent / "test1.json"
        ofile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.export_dreq_lists_json",
                "--all_opportunities",
                "v1.2.2",
                ofile,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile) and os.path.getsize(ofile) > 0

    def test_export_dreq_lists_json_with_opportunities_file(
        self, temp_config_file, consolidate
    ):
        # Test that the script creates an opportunities file template
        opportunities_file = temp_config_file.parent / "opportunities.json"
        opportunities_file.unlink(missing_ok=True)
        ofile = temp_config_file.parent / "test2.json"
        ofile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.export_dreq_lists_json",
                "--opportunities_file",
                opportunities_file,
                "v1.2.2",
                ofile,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert (
            os.path.exists(opportunities_file)
            and os.path.getsize(opportunities_file) > 0
        )
        assert not os.path.exists(ofile) or os.path.getsize(ofile) == 0

        # Test that it now applies the opportunities settings from opportunities_file
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.export_dreq_lists_json",
                "--opportunities_file",
                opportunities_file,
                "v1.2.2",
                ofile,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile) and os.path.getsize(ofile) > 0

    def test_export_dreq_lists_json_with_invalid_opportunities_file(
        self, temp_config_file, consolidate
    ):
        # Test that the script raises an error with an invalid opportunities file
        opportunities_file = temp_config_file.parent / "invalid_opportunities.json"
        opportunities_file.unlink(missing_ok=True)
        ofile = temp_config_file.parent / "test3.json"
        ofile.unlink(missing_ok=True)
        with open(opportunities_file, "w") as fh:
            json.dump({"Invalid": "data"}, fh)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.export_dreq_lists_json",
                "--opportunities_file",
                opportunities_file,
                "v1.2.2",
                ofile,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert not os.path.exists(ofile) or os.path.getsize(ofile) == 0

    def test_export_dreq_lists_json_with_time_subsets(
        self, temp_config_file, consolidate
    ):
        # Test that resulting json file includes time subsets
        ofile = temp_config_file.parent / "test4.json"
        ofile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.export_dreq_lists_json",
                "-i",
                "1,19,20,22,71,69",
                "-t",
                "v1.2.2.2",
                ofile,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile) and os.path.getsize(ofile) > 0
        # Read json file and assert content
        with open(ofile) as fh:
            data = json.load(fh)
        assert "experiment" in data and "Header" in data
        for exp, req in data["experiment"].items():
            assert all(req["Core"][i] == ["all"] for i in req["Core"].keys())

    def test_export_dreq_lists_json_with_time_subsets_and_combined_request(
        self, temp_config_file, consolidate
    ):
        # Test that resulting json file includes time subsets and combined requests
        ofile = temp_config_file.parent / "test5.json"
        ofile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.export_dreq_lists_json",
                "-i",
                "1,19,20,22,71,69",
                "-tc",
                "v1.2.2.2",
                ofile,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile) and os.path.getsize(ofile) > 0
        # Read json file and assert content
        with open(ofile) as fh:
            data = json.load(fh)
        assert all(
            i in data["experiment"].keys()
            for i in [
                "historical_experiments",
                "scenario_experiments",
                "all_experiments",
            ]
        )
        for exp, req in data["experiment"].items():
            assert all(
                isinstance(req[j], dict) for j in ["Core", "High", "Medium", "Low"]
            )

    def test_export_dreq_lists_json_with_combined_request(
        self, temp_config_file, consolidate
    ):
        # Test that the resulting json file includes combined requests
        ofile = temp_config_file.parent / "test6.json"
        ofile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.export_dreq_lists_json",
                "-a",
                "-c",
                "v1.2.2.2",
                ofile,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile) or os.path.getsize(ofile) > 0
        # Read json file and assert content
        with open(ofile) as fh:
            data = json.load(fh)
        assert all(
            [
                i in data["experiment"].keys()
                for i in [
                    "historical_experiments",
                    "scenario_experiments",
                    "all_experiments",
                ]
            ]
        )

    def test_export_dreq_lists_json_entry_point(self, temp_config_file, consolidate):
        ofile = temp_config_file.parent / "test7.json"
        ofile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                "export_dreq_lists_json",
                "--all_opportunities",
                "v1.2.2",
                ofile,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile) and os.path.getsize(ofile) > 0


@pytest.mark.parametrize(
    "consolidate",
    ["consolidate", "no consolidate"],
    indirect=True,
    scope="class",
)
class TestGetVariablesMetadata:
    @pytest.fixture(scope="function", autouse=True)
    def setup_method(self, request):
        # Initialize config and load v1.2.2 content version
        self.temp_config_file = request.getfixturevalue("temp_config_file")
        self.consolidate = request.getfixturevalue("consolidate")
        with open(self.temp_config_file, "w") as fh:
            config = {
                "consolidate": self.consolidate == "consolidate",
                "cache_dir": str(self.temp_config_file.parent),
            }
            yaml.dump(config, fh)
        dc.load("v1.2.2")

    def test_get_variables_metadata(self, temp_config_file, consolidate):
        ofile = temp_config_file.parent / "test1.json"
        ofile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.get_variables_metadata",
                "v1.2.2",
                ofile,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile) and os.path.getsize(ofile) > 0

    def test_get_variables_metadata_with_compound_names(
        self, temp_config_file, consolidate
    ):
        ofile = temp_config_file.parent / "test2.json"
        ofile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.get_variables_metadata",
                "v1.2.2",
                ofile,
                "-cn",
                # "Amon.tas,Omon.sos",
                "atmos.tas.tavg-h2m-hxy-u.mon.GLB,ocean.sos.tavg-u-hxy-sea.mon.GLB",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile) and os.path.getsize(ofile) > 0

    def test_get_variables_metadata_with_cmor_tables(
        self, temp_config_file, consolidate
    ):
        ofile = temp_config_file.parent / "test3.json"
        ofile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.get_variables_metadata",
                "v1.2.2",
                ofile,
                "-t",
                "Amon,Omon",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile) and os.path.getsize(ofile) > 0

    def test_get_variables_metadata_with_cmor_variables(
        self, temp_config_file, consolidate
    ):
        ofile = temp_config_file.parent / "test4.json"
        ofile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.get_variables_metadata",
                "v1.2.2",
                ofile,
                "-v",
                "tas,siconc",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile) and os.path.getsize(ofile) > 0

    def test_get_variables_metadata_entry_point(self, temp_config_file, consolidate):
        ofile = temp_config_file.parent / "test5.json"
        ofile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                "get_variables_metadata",
                "v1.2.2",
                ofile,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile) and os.path.getsize(ofile) > 0


@pytest.mark.parametrize(
    "consolidate",
    ["consolidate", "no consolidate"],
    indirect=True,
    scope="class",
)
class TestCompareVariables:
    @pytest.fixture(scope="function", autouse=True)
    def setup_method(self, request):
        # Initialize config and load v1.2 content version
        self.temp_config_file = request.getfixturevalue("temp_config_file")
        self.consolidate = request.getfixturevalue("consolidate")
        with open(self.temp_config_file, "w") as fh:
            config = {
                "consolidate": self.consolidate == "consolidate",
                "variable_name": "CMIP6 Compound Name",
                "cache_dir": str(self.temp_config_file.parent),
            }
            yaml.dump(config, fh)
        dc.load("v1.2.1")
        dc.load("v1.2.2")

    def test_compare_variables(self, temp_config_file, consolidate):
        os.chdir(temp_config_file.parent)
        ofileA = temp_config_file.parent / "testA.json"
        ofileB = temp_config_file.parent / "testB.json"
        ofile_vars = temp_config_file.parent / "diffs_by_variable.json"
        ofile_attr = temp_config_file.parent / "diffs_by_attribute.json"
        ofile_missing = temp_config_file.parent / "missing_variables.json"
        attr_file = temp_config_file.parent / "attributes.yaml"

        # Part 1 - Standard comparison
        ofile_vars.unlink(missing_ok=True)
        ofile_attr.unlink(missing_ok=True)
        ofile_missing.unlink(missing_ok=True)
        ofileA.unlink(missing_ok=True)
        ofileB.unlink(missing_ok=True)
        attr_file.unlink(missing_ok=True)
        # Create Variable List A
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.get_variables_metadata",
                "v1.2.1",
                ofileA,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofileA) and os.path.getsize(ofileA) > 0
        # Create Variable List B
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.get_variables_metadata",
                "v1.2.2",
                ofileB,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofileB) and os.path.getsize(ofileB) > 0
        # Actual comparison
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.compare_variables",
                ofileA,
                ofileB,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile_missing) and os.path.getsize(ofile_missing) > 0
        assert os.path.exists(ofile_vars) and os.path.getsize(ofile_vars) > 0
        assert os.path.exists(ofile_attr) and os.path.getsize(ofile_attr) > 0
        assert os.path.exists(attr_file) and os.path.getsize(attr_file) > 0

        # Part 2 - Provide attribute file
        ofile_vars.unlink(missing_ok=True)
        ofile_attr.unlink(missing_ok=True)
        ofile_missing.unlink(missing_ok=True)
        # Write custom attributes file
        cattr_file = temp_config_file.parent / "custom_attrs.yaml"
        cattr_file.unlink(missing_ok=True)
        config = {
            "compare_attributes": ["standard_name", "units", "cell_methods"],
            "repos": {
                "cmip6": {
                    "url": "https://github.com/PCMDI/cmip6-cmor-tables",
                }
            },
        }
        with open(cattr_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
        # Actual comparison
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.compare_variables",
                ofileA,
                ofileB,
                "-c",
                cattr_file,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile_missing) and os.path.getsize(ofile_missing) > 0
        assert os.path.exists(ofile_vars) and os.path.getsize(ofile_vars) > 0
        assert os.path.exists(ofile_attr) and os.path.getsize(ofile_attr) > 0
        assert os.path.getsize(cattr_file) < os.path.getsize(attr_file)

        # Part 3 - Compare with CMIP6
        ofile_vars.unlink(missing_ok=True)
        ofile_attr.unlink(missing_ok=True)
        ofile_missing.unlink(missing_ok=True)
        # Actual comparison
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.compare_variables",
                ofileB,
                "cmip6",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile_missing) and os.path.getsize(ofile_missing) > 0
        assert os.path.exists(ofile_vars) and os.path.getsize(ofile_vars) > 0
        assert os.path.exists(ofile_attr) and os.path.getsize(ofile_attr) > 0


@pytest.mark.parametrize(
    "consolidate",
    ["consolidate", "no consolidate"],
    indirect=True,
    scope="class",
)
class TestEstimateDreqVolume:
    @pytest.fixture(scope="function", autouse=True)
    def setup_method(self, request):
        # Initialize config and load v1.2 content version
        self.temp_config_file = request.getfixturevalue("temp_config_file")
        self.consolidate = request.getfixturevalue("consolidate")
        with open(self.temp_config_file, "w") as fh:
            config = {
                "consolidate": self.consolidate == "consolidate",
                "cache_dir": str(self.temp_config_file.parent),
            }
            yaml.dump(config, fh)
        dc.load("v1.2.2")

    def test_estimate_dreq_volume(self, temp_config_file, consolidate):
        os.chdir(temp_config_file.parent)
        ofile = temp_config_file.parent / "test1.json"
        sizecfg = temp_config_file.parent / "size.yaml"
        ofile.unlink(missing_ok=True)
        sizecfg.unlink(missing_ok=True)
        # Part 1 - Create size.yaml
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.estimate_dreq_volume",
                "v1.2.2",
                "-o",
                ofile,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert not os.path.exists(ofile) or os.path.getsize(ofile) == 0
        assert os.path.exists(sizecfg) and os.path.getsize(sizecfg) > 0
        # Part 2 - Actual volume estimate
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.estimate_dreq_volume",
                "v1.2.2",
                "-o",
                ofile,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile) and os.path.getsize(ofile) > 0
        assert os.path.exists(sizecfg) and os.path.getsize(sizecfg) > 0
        # Part 3 - Custom size.yaml
        ofile.unlink(missing_ok=True)
        csizecfg = temp_config_file.parent / "custom_size.yaml"
        csizecfg.unlink(missing_ok=True)
        # Read default size.yaml
        with open(sizecfg) as fh:
            config = yaml.safe_load(fh)
        sizecfg.unlink(missing_ok=True)
        # Update config
        config["longitude"] = 720
        config["latitude"] = 360
        # Write custom size.yaml
        with open(csizecfg, "w") as fh:
            yaml.dump(config, fh)
        # Actual volume estimate
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.estimate_dreq_volume",
                "v1.2.2",
                "-o",
                ofile,
                "-c",
                csizecfg,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile) and os.path.getsize(ofile) > 0
        assert os.path.exists(csizecfg) and os.path.getsize(csizecfg) > 0
        assert not os.path.exists(sizecfg) or os.path.getsize(sizecfg) == 0
