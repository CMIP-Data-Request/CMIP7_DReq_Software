import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

import data_request_api.content.dreq_content as dc


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
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, request):
        # Initialize config and load v1.2 content version
        self.temp_config_file = request.getfixturevalue("temp_config_file")
        self.consolidate = request.getfixturevalue("consolidate")
        with open(self.temp_config_file, "w") as fh:
            config = {
                "consolidate": self.consolidate == "consolidate",
                "cache_dir": str(self.temp_config_file.parent),
            }
            yaml.dump(config, fh)
        dc.load("v1.2")

    def test_export_dreq_lists_json(self, temp_config_file, consolidate):
        ofile = temp_config_file.parent / "test1.json"
        ofile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.export_dreq_lists_json",
                "--all_opportunities",
                "v1.2",
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
                "v1.2",
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
                "v1.2",
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
        opportunities_file = (
            temp_config_file.parent / "invalid_opportunities.json"
        )
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
                "v1.2",
                ofile,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert not os.path.exists(ofile) or os.path.getsize(ofile) == 0

    def test_export_dreq_lists_json_entry_point(
        self, temp_config_file, consolidate
    ):
        ofile = temp_config_file.parent / "test4.json"
        ofile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                "export_dreq_lists_json",
                "--all_opportunities",
                "v1.2",
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
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, request):
        # Initialize config and load v1.2 content version
        self.temp_config_file = request.getfixturevalue("temp_config_file")
        self.consolidate = request.getfixturevalue("consolidate")
        with open(self.temp_config_file, "w") as fh:
            config = {
                "consolidate": self.consolidate == "consolidate",
                "cache_dir": str(self.temp_config_file.parent),
            }
            yaml.dump(config, fh)
        dc.load("v1.2")

    def test_get_variables_metadata(self, temp_config_file, consolidate):
        ofile = temp_config_file.parent / "test1.json"
        ofile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "data_request_api.command_line.get_variables_metadata",
                "v1.2",
                "-o",
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
                "v1.2",
                "-o",
                ofile,
                "-cn",
                "Amon.tas",
                "Omon.sos",
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
                "v1.2",
                "-o",
                ofile,
                "-t",
                "Amon",
                "Omon",
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
                "v1.2",
                "-o",
                ofile,
                "-v",
                "tas",
                "siconc",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile) and os.path.getsize(ofile) > 0

    def test_get_variables_metadata_entry_point(
        self, temp_config_file, consolidate
    ):
        ofile = temp_config_file.parent / "test5.json"
        ofile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                "get_variables_metadata",
                "v1.2",
                "-o",
                ofile,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(ofile) and os.path.getsize(ofile) > 0
