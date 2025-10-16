import os
import pathlib
import tempfile

import data_request_api.utilities.config as dreqcfg
import pytest
from data_request_api.content import dreq_content as dc
from data_request_api.utilities.logger import change_log_file, change_log_level

# Set up temporary config file with default config
temp_config_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
dreqcfg.CONFIG_FILE = pathlib.Path(temp_config_file.name)


# Configure logger for testing
change_log_file(default=True)
change_log_level("info")


def test_parse_version():
    "Test the _parse_version function with different version strings."
    assert dc._parse_version("v1.0.0") == (1, 0, 0, 0, "", 0)
    assert dc._parse_version("v1.0alpha2") == (1, 0, 0, 0, "a", 2)
    assert dc._parse_version("1.0.0a3") == (1, 0, 0, 0, "a", 3)
    assert dc._parse_version("1.0.0beta") == (1, 0, 0, 0, "b", 0)
    assert dc._parse_version("something") == (0, 0, 0, 0, "", 0)
    assert dc._parse_version("2.0.3.4b4") == (2, 0, 3, 4, "b", 4)
    with pytest.raises(TypeError):
        dc._parse_version(None)


def test_get_versions():
    "Test the get_versions function."
    versions = dc.get_versions()
    assert "dev" in versions
    assert "v1.0alpha" in versions
    assert "v1.0beta" in versions
    assert "v1.2.2.2" in versions


def test_get_versions_list_branches():
    "Test the get_versions function for branches."
    branches = dc.get_versions(target="branches")
    assert "dev" not in branches
    assert "main" not in branches


def test_get_latest_version(monkeypatch):
    "Test the _get_latest_version function."
    monkeypatch.setattr(
        dc, "get_versions", lambda **kwargs: ["1.0.1.2", "1.0.1", "2.0.2b", "2.0.2a"]
    )
    assert dc._get_latest_version() == "1.0.1.2"
    assert dc._get_latest_version(stable=False) == "2.0.2b"


def test_get_cached(tmp_path):
    "Test the get_cached function."
    # Create a temporary directory with a subdirectory containing a dreq.json file
    version_dir = tmp_path / "v1.0.0"
    version_dir.mkdir()
    (version_dir / dc._json_release).touch()

    # Set the _dreq_res variable to the temporary directory
    dc._dreq_res = str(tmp_path)

    # Test the get_cached function
    cached_versions = dc.get_cached()
    assert cached_versions == ["v1.0.0"]


def test_retrieve(tmp_path, caplog):
    "Test the retrieval function."
    dc._dreq_res = str(tmp_path)

    # Retrieve 'dev' version
    json_path = dc.retrieve("dev")["dev"]
    assert os.path.isfile(json_path)

    # Alter on disk (delete first line)
    with open(json_path) as f:
        lines = f.read().splitlines(keepends=True)
    with open(json_path, "w") as f:
        f.writelines(lines[1:])

    # Make sure it updates
    json_path = dc.retrieve("dev")["dev"]
    assert len(caplog.text.splitlines()) == 2
    assert "Retrieved version 'dev'." in caplog.text
    assert "Updated version 'dev'." in caplog.text
    # ... and the file was replaced
    with open(json_path) as f:
        lines_update = f.read().splitlines(keepends=True)
    assert lines == lines_update


def test_retrieve_with_invalid_version(tmp_path):
    "Test the retrieval function with an invalid version."
    dc._dreq_res = str(tmp_path)
    with pytest.raises(ValueError):
        dc.retrieve(" invalid-version ")


def test_retrieve_with_invalid_export(tmp_path):
    "Test the retrieval function with an invalid export."
    dc._dreq_res = str(tmp_path)
    with pytest.raises(ValueError):
        dc.retrieve("v1.2.1", export="invalid")


def test_api_and_html_request(recwarn):
    "Test the _send_api_request and _send_html_request functions."
    tags1 = set(dc._send_api_request(dc.REPO_API_URL, "", "tags"))
    for warning in recwarn.list:
        if str(warning.message).startswith(
            "A HTTP error occurred when retrieving 'tags' via the GitHub API "
        ):
            pytest.xfail("GitHub API not accessible.")
    tags2 = set(dc._send_html_request(dc.REPO_PAGE_URL, "tags"))
    recwarn.clear()
    assert tags1 == tags2

    branches1 = set(dc._send_api_request(dc.REPO_API_URL, "", "branches"))
    for warning in recwarn.list:
        if str(warning.message).startswith(
            "A HTTP error occurred when retrieving 'branches' via the GitHub API "
        ):
            pytest.xfail("GitHub API not accessible.")
    branches2 = set(dc._send_html_request(dc.REPO_PAGE_URL, "branches"))
    assert branches1 == branches2


def test_load_dont_consolidate(tmp_path):
    "Test the load function."
    dc._dreq_res = str(tmp_path)

    with pytest.raises(ValueError):
        jsondict = dc.load(" invalid-version ")

    # Load multi-base export without consolidation
    jsondict = dc.load("dev", consolidate=False, export="raw")
    assert isinstance(jsondict, dict)
    assert os.path.isfile(tmp_path / "dev" / dc._json_raw)
    assert not os.path.isfile(tmp_path / "dev" / dc._json_release)

    # Load release export without consolidation
    jsondict = dc.load("dev", consolidate=False, export="release")
    assert isinstance(jsondict, dict)
    assert os.path.isfile(tmp_path / "dev" / dc._json_release)


def test_load_consolidate(tmp_path, monkeypatch):
    "Test the load function."
    dc._dreq_res = str(tmp_path)

    # Alter mapping table - skip time consuming bits of consolidation
    import data_request_api.content.mapping_table as mt

    original_mapping_table = mt.mapping_table
    updated_mapping_table = original_mapping_table.copy()
    for key in updated_mapping_table:
        if key != "Variables":
            updated_mapping_table[key]["internal_mapping"] = {}
    monkeypatch.setattr(mt, "mapping_table", updated_mapping_table)

    with pytest.raises(ValueError):
        jsondict = dc.load(" invalid-version ")

    # Load multi-base export with consolidation
    jsondict = dc.load("dev", consolidate=True, export="raw")
    assert isinstance(jsondict, dict)
    assert os.path.isfile(tmp_path / "dev" / dc._json_raw)
    assert not os.path.isfile(tmp_path / "dev" / dc._json_release)

    # Load release export with consolidation
    jsondict = dc.load("dev", consolidate=True, export="release")
    assert isinstance(jsondict, dict)
    assert "Data Request" in jsondict
    assert jsondict["Data Request"]["version"] == "dev"
    assert os.path.isfile(tmp_path / "dev" / dc._json_release)


class TestDreqContent:
    """
    Test various functions of the dreq_content module.
    """

    @pytest.fixture(autouse=True, scope="function")
    def setup(self, tmp_path):
        self.dreq_res = tmp_path
        # Cached content
        self.versions = ["v1.0.0", "1.0.1", "2.0.1b", "2.0.1", "2.0.2b"]
        self.branches = ["one", "or", "another"]
        for v in self.versions:
            (self.dreq_res / v).mkdir()
            (self.dreq_res / v / dc._json_release).write_text("{}")
        for b in self.branches:
            (self.dreq_res / b).mkdir()
            (self.dreq_res / b / dc._json_raw).write_text("{}")
        # Cached modified content (consolidated/transformed)
        self.mversions = ["v1.0.0", "3.1", "3.2.2.2b5"]
        self.mbranches = ["another", "v1.2.2.2rc"]
        for v in self.mversions:
            (self.dreq_res / v).mkdir(exist_ok=True)
            (self.dreq_res / v / dc._json_release_c).write_text("{}")
        for b in self.mbranches:
            (self.dreq_res / b).mkdir(exist_ok=True)
            (self.dreq_res / b / dc._json_release_nc_VS).write_text("{}")
            (self.dreq_res / b / dc._json_release_nc_DR).write_text("{}")
            (self.dreq_res / b / dc._json_raw_c).write_text("{}")

    def test_get_cached(self):
        "Test the get_cached function."
        dc._dreq_res = self.dreq_res

        # Without export kwarg
        cached_tags = dc.get_cached()
        assert set(cached_tags) == set(self.versions)

        # With export kwarg "release"
        cached_tags = dc.get_cached(export="release")
        assert set(cached_tags) == set(self.versions)

        # With export kwarg "raw"
        cached_branches = dc.get_cached(export="raw")
        assert set(cached_branches) == set(self.branches)

        # With invalid export kwarg
        with pytest.raises(
            ValueError, match="Invalid value for config key export: invalid."
        ):
            dc.get_cached(export="invalid")

    def test_get_partly_cached(self):
        "Test the get_partly_cached function."
        dc._dreq_res = self.dreq_res

        # Without export kwarg
        partly_cached = dc._get_partly_cached()
        assert set(partly_cached) == {"3.1", "3.2.2.2b5", "another", "v1.2.2.2rc"}

        # With export kwarg "release"
        partly_cached = dc._get_partly_cached(export="release")
        assert set(partly_cached) == {"3.1", "3.2.2.2b5", "another", "v1.2.2.2rc"}

        # With export kwarg "raw"
        partly_cached = dc._get_partly_cached(export="raw")
        assert set(partly_cached) == {"v1.2.2.2rc"}

        # With export kwarg "raw" and assume_deleted kwarg
        partly_cached = dc._get_partly_cached(export="raw", assume_deleted=["another"])
        assert set(partly_cached) == {"v1.2.2.2rc", "another"}

        # With invalid export kwarg
        with pytest.raises(
            ValueError, match="Invalid value for config key export: invalid."
        ):
            dc._get_partly_cached(export="invalid")

    def test_delete_and_cleanup(self, caplog):
        "Test the delete and cleanup functions."
        dc._dreq_res = self.dreq_res

        # Cleanup dryrun
        caplog.clear()
        dc.cleanup(export="raw", dryrun=True)
        assert len(caplog.text.splitlines()) == 2
        assert (
            "Cleaning up files for the following incompletely cached versions:"
            in caplog.text
        )
        for b in ["v1.2.2.2rc"]:
            assert (
                f"Dryrun: would delete '{dc._dreq_res / b / dc._json_raw_c}'."
                in caplog.text
            )

        # Cleanup dryrun + assume_deleted
        caplog.clear()
        dc.cleanup(export="raw", dryrun=True, assume_deleted=["another"])
        assert len(caplog.text.splitlines()) == 3
        assert (
            "Cleaning up files for the following incompletely cached versions:"
            in caplog.text
        )
        for b in ["v1.2.2.2rc", "another"]:
            assert (
                f"Dryrun: would delete '{dc._dreq_res / b / dc._json_raw_c}'."
                in caplog.text
            )

        # Cleanup
        dc.cleanup(export="raw")
        assert len(dc._get_partly_cached(export="raw")) == 0
        dc.cleanup(export="release")
        assert len(dc._get_partly_cached(export="release")) == 0

        # Delete non-existent version
        caplog.clear()
        dc.delete("notpresent")
        assert len(caplog.text.splitlines()) == 1
        assert "No version(s) found to delete." in caplog.text

        # Delete only branches / dryrun
        caplog.clear()
        dc.delete("all", export="raw", dryrun=True)
        assert len(caplog.text.splitlines()) == 4
        assert "Deleting the following version(s):" in caplog.text
        for b in self.branches:
            assert (
                f"Dryrun: would delete '{dc._dreq_res / b / dc._json_raw}'."
                in caplog.text
            )

        # Delete all but latest
        caplog.clear()
        dc.delete(keep_latest=True)
        assert len(caplog.text.splitlines()) == 6
        assert "Deleting the following version(s):" in caplog.text
        assert (
            "Cleaning up files for the following incompletely cached versions:"
            in caplog.text
        )
        assert set(dc.get_cached()) == {"2.0.1", "2.0.2b"}
        assert set(dc.get_cached(export="raw")) == set(self.branches)

        # Delete 2.0.1 with warning
        with pytest.warns(UserWarning, match=" option is ignored "):
            dc.delete("2.0.1", keep_latest=True)

        # Delete all with ValueError for kwargs
        with pytest.raises(ValueError):
            dc.delete(export="none")

        # Delete all
        dc.delete(export="raw")
        assert dc.get_cached() == ["2.0.2b"]
        assert dc.get_cached(export="raw") == []

        # Now there is no ValueError since no version is found
        dc.delete("2.0.2b")

        # But illegal config kwargs raise ValueError nonetheless
        with pytest.raises(
            ValueError, match="Invalid value for config key export: none."
        ):
            dc.delete(export="none")

    def test_offline_mode(self, monkeypatch):
        "Test the offline mode explicitly."
        dc._dreq_res = self.dreq_res

        def mock_requests_get(*args, **kwargs):
            raise Exception("Network request detected despite active offline mode.")

        monkeypatch.setattr("requests.get", mock_requests_get)

        # Call dc.load with offline=True
        dc.load("v1.0.0", consolidate=False, offline=True)

        # Call dc.load with offline=False
        with pytest.raises(Exception, match="Network request detected"):
            dc.load("v1.0.0", consolidate=False, offline=False)

    # def test_load(self):
    #    dc._dreq_res = self.tmp_dir.name
    #    data = dc.load("1.0.0")
    #    assert data == {}
