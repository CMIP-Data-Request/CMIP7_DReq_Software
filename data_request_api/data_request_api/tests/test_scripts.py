"""
Test scripts
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import data_request_api.content.dreq_content as dc
import data_request_api.utilities.config as dreqcfg
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
def export(request):
    # "consolidate" or "no consolidate"
    return request.param


@pytest.mark.parametrize(
    "export",
    ["raw", "release"],
    indirect=True,
    scope="class",
)
class TestWorkflowV10:
    @pytest.fixture(scope="function", autouse=True)
    def setup_method(self, request):
        # Initialize config and load v1.0 content version
        self.temp_config_file = request.getfixturevalue("temp_config_file")
        self.export = request.getfixturevalue("export")
        self.version = "v1.0"
        with open(self.temp_config_file, "w") as fh:
            config = {
                "export": self.export,
                "consolidate": False,
                "cache_dir": str(self.temp_config_file.parent),
            }
            yaml.dump(config, fh)
        dc._dreq_res = self.temp_config_file.parent
        dc.versions = {"tags": [], "branches": []}
        dreqcfg.CONFIG_FILE = self.temp_config_file
        dreqcfg.CONFIG = {}  # alternatively: dreqcfg.load_config(reload=True)
        dc.load(self.version)

    def test_database_transformation(self, temp_config_file, export):
        DRfile = temp_config_file.parent / self.version / "{base}_{export}_content.json".format(base="DR", export=export)
        DRfile.unlink(missing_ok=True)
        VSfile = temp_config_file.parent / self.version / "{base}_{export}_content.json".format(base="VS", export=export)
        VSfile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                os.sep.join(["scripts", "database_transformation.py"]),
                "--output_dir",
                str(temp_config_file.parent),
                "--version",
                self.version,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(DRfile) and os.path.getsize(DRfile) > 0
        assert os.path.exists(VSfile) and os.path.getsize(VSfile) > 0

    def test_workflow_example_2(self, temp_config_file, export):
        output_files = [temp_config_file.parent / out for out in ["op_per_th.csv", "var_per_op.csv","var_per_spsh.csv",
                                                                  "var_per_op_filtered.csv",
                                                                  "var_per_op_regrouped_filtered.csv",
                                                                  "var_per_exp_regrouped_filtered.csv",
                                                                  "var_per_exp_filtered.csv", "exp_per_op.csv",
                                                                  "exp_per_op_regrouped_filtered.csv",
                                                                  "exp_per_op_filtered.csv", "op.csv"]]
        for output_file in output_files:
            output_file.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                os.sep.join(["scripts", "workflow_example_2.py"]),
                "--output_dir",
                str(temp_config_file.parent),
                "--version",
                self.version,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        for output_file in output_files:
            assert os.path.exists(output_file) and os.path.getsize(output_file) > 0

    def test_check_variables_attributes(self, temp_config_file, export):
        checkfile = temp_config_file.parent / self.version / "check_attributes_{}.json".format(export)
        checkfile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                os.sep.join(["scripts", "check_variables_attributes.py"]),
                "--output_dir",
                str(temp_config_file.parent),
                "--version",
                self.version,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(checkfile) and os.path.getsize(checkfile) > 0


@pytest.mark.skip
@pytest.mark.parametrize(
    "export",
    ["release", ],
    indirect=True,
    scope="class",
)
class TestWorkflowV11:
    @pytest.fixture(scope="function", autouse=True)
    def setup_method(self, request):
        # Initialize config and load v1.0 content version
        self.temp_config_file = request.getfixturevalue("temp_config_file")
        self.export = request.getfixturevalue("export")
        self.version = "v1.1"
        with open(self.temp_config_file, "w") as fh:
            config = {
                "export": self.export,
                "consolidate": False,
                "cache_dir": str(self.temp_config_file.parent),
            }
            yaml.dump(config, fh)
        dc._dreq_res = self.temp_config_file.parent
        dc.versions = {"tags": [], "branches": []}
        dreqcfg.CONFIG_FILE = self.temp_config_file
        dreqcfg.CONFIG = {}  # alternatively: dreqcfg.load_config(reload=True)
        dc.load(self.version)

    def test_database_transformation(self, temp_config_file, export):
        DRfile = temp_config_file.parent / self.version / "{base}_{export}_content.json".format(base="DR", export=export)
        DRfile.unlink(missing_ok=True)
        VSfile = temp_config_file.parent / self.version / "{base}_{export}_content.json".format(base="VS", export=export)
        VSfile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                os.sep.join(["scripts", "database_transformation.py"]),
                "--output_dir",
                str(temp_config_file.parent),
                "--version",
                self.version,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(DRfile) and os.path.getsize(DRfile) > 0
        assert os.path.exists(VSfile) and os.path.getsize(VSfile) > 0

    def test_workflow_example_2(self, temp_config_file, export):
        output_files = [temp_config_file.parent / out for out in ["op_per_th.csv", "var_per_op.csv","var_per_spsh.csv",
                                                                  "var_per_op_filtered.csv",
                                                                  "var_per_op_regrouped_filtered.csv",
                                                                  "var_per_exp_regrouped_filtered.csv",
                                                                  "var_per_exp_filtered.csv", "exp_per_op.csv",
                                                                  "exp_per_op_regrouped_filtered.csv",
                                                                  "exp_per_op_filtered.csv", "op.csv"]]
        for output_file in output_files:
            output_file.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                os.sep.join(["scripts", "workflow_example_2.py"]),
                "--output_dir",
                str(temp_config_file.parent),
                "--version",
                self.version,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        for output_file in output_files:
            assert os.path.exists(output_file) and os.path.getsize(output_file) > 0

    def test_check_variables_attributes(self, temp_config_file, export):
        checkfile = temp_config_file.parent / self.version / "check_attributes_{}.json".format(export)
        checkfile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                os.sep.join(["scripts", "check_variables_attributes.py"]),
                "--output_dir",
                str(temp_config_file.parent),
                "--version",
                self.version,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(checkfile) and os.path.getsize(checkfile) > 0


@pytest.mark.parametrize(
    "export",
    ["raw", "release"],
    indirect=True,
    scope="class",
)
class TestWorkflowV12:
    @pytest.fixture(scope="function", autouse=True)
    def setup_method(self, request):
        # Initialize config and load v1.0 content version
        self.temp_config_file = request.getfixturevalue("temp_config_file")
        self.export = request.getfixturevalue("export")
        self.version = "v1.2"
        with open(self.temp_config_file, "w") as fh:
            config = {
                "export": self.export,
                "consolidate": False,
                "cache_dir": str(self.temp_config_file.parent),
            }
            yaml.dump(config, fh)
        dc._dreq_res = self.temp_config_file.parent
        dc.versions = {"tags": [], "branches": []}
        dreqcfg.CONFIG_FILE = self.temp_config_file
        dreqcfg.CONFIG = {}  # alternatively: dreqcfg.load_config(reload=True)
        dc.load(self.version)

    def test_database_transformation(self, temp_config_file, export):
        DRfile = temp_config_file.parent / self.version / "{base}_{export}_content.json".format(base="DR", export=export)
        DRfile.unlink(missing_ok=True)
        VSfile = temp_config_file.parent / self.version / "{base}_{export}_content.json".format(base="VS", export=export)
        VSfile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                os.sep.join(["scripts", "database_transformation.py"]),
                "--output_dir",
                str(temp_config_file.parent),
                "--version",
                self.version,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(DRfile) and os.path.getsize(DRfile) > 0
        assert os.path.exists(VSfile) and os.path.getsize(VSfile) > 0

    def test_workflow_example_2(self, temp_config_file, export):
        output_files = [temp_config_file.parent / out for out in ["op_per_th.csv", "var_per_op.csv","var_per_spsh.csv",
                                                                  "var_per_op_filtered.csv",
                                                                  "var_per_op_regrouped_filtered.csv",
                                                                  "var_per_exp_regrouped_filtered.csv",
                                                                  "var_per_exp_filtered.csv", "exp_per_op.csv",
                                                                  "exp_per_op_regrouped_filtered.csv",
                                                                  "exp_per_op_filtered.csv", "op.csv"]]
        for output_file in output_files:
            output_file.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                os.sep.join(["scripts", "workflow_example_2.py"]),
                "--output_dir",
                str(temp_config_file.parent),
                "--version",
                self.version,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        for output_file in output_files:
            assert os.path.exists(output_file) and os.path.getsize(output_file) > 0

    def test_check_variables_attributes(self, temp_config_file, export):
        checkfile = temp_config_file.parent / self.version / "check_attributes_{}.json".format(export)
        checkfile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                os.sep.join(["scripts", "check_variables_attributes.py"]),
                "--output_dir",
                str(temp_config_file.parent),
                "--version",
                self.version,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(checkfile) and os.path.getsize(checkfile) > 0


@pytest.mark.parametrize(
    "export",
    ["raw", "release"],
    indirect=True,
    scope="class",
)
class TestWorkflowV121:
    @pytest.fixture(scope="function", autouse=True)
    def setup_method(self, request):
        # Initialize config and load v1.0 content version
        self.temp_config_file = request.getfixturevalue("temp_config_file")
        self.export = request.getfixturevalue("export")
        self.version = "v1.2.1"
        with open(self.temp_config_file, "w") as fh:
            config = {
                "export": self.export,
                "consolidate": False,
                "cache_dir": str(self.temp_config_file.parent),
            }
            yaml.dump(config, fh)
        dc._dreq_res = self.temp_config_file.parent
        dc.versions = {"tags": [], "branches": []}
        dreqcfg.CONFIG_FILE = self.temp_config_file
        dreqcfg.CONFIG = {}  # alternatively: dreqcfg.load_config(reload=True)
        dc.load(self.version)

    def test_database_transformation(self, temp_config_file, export):
        DRfile = temp_config_file.parent / self.version / "{base}_{export}_content.json".format(base="DR", export=export)
        DRfile.unlink(missing_ok=True)
        VSfile = temp_config_file.parent / self.version / "{base}_{export}_content.json".format(base="VS", export=export)
        VSfile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                os.sep.join(["scripts", "database_transformation.py"]),
                "--output_dir",
                str(temp_config_file.parent),
                "--version",
                self.version,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(DRfile) and os.path.getsize(DRfile) > 0
        assert os.path.exists(VSfile) and os.path.getsize(VSfile) > 0

    def test_workflow_example_2(self, temp_config_file, export):
        output_files = [temp_config_file.parent / out for out in ["op_per_th.csv", "var_per_op.csv","var_per_spsh.csv",
                                                                  "var_per_op_filtered.csv",
                                                                  "var_per_op_regrouped_filtered.csv",
                                                                  "var_per_exp_regrouped_filtered.csv",
                                                                  "var_per_exp_filtered.csv", "exp_per_op.csv",
                                                                  "exp_per_op_regrouped_filtered.csv",
                                                                  "exp_per_op_filtered.csv", "op.csv"]]
        for output_file in output_files:
            output_file.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                os.sep.join(["scripts", "workflow_example_2.py"]),
                "--output_dir",
                str(temp_config_file.parent),
                "--version",
                self.version,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        for output_file in output_files:
            assert os.path.exists(output_file) and os.path.getsize(output_file) > 0

    def test_check_variables_attributes(self, temp_config_file, export):
        checkfile = temp_config_file.parent / self.version / "check_attributes_{}.json".format(export)
        checkfile.unlink(missing_ok=True)
        result = subprocess.run(
            [
                sys.executable,
                os.sep.join(["scripts", "check_variables_attributes.py"]),
                "--output_dir",
                str(temp_config_file.parent),
                "--version",
                self.version,
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert os.path.exists(checkfile) and os.path.getsize(checkfile) > 0
