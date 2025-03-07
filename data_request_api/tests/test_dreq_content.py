import os
import pathlib
import sys
import tempfile

import pytest

import data_request_api.stable.utilities.config
from data_request_api.stable.content import dreq_content as dc
from data_request_api.stable.utilities.logger import change_log_file, change_log_level

# Set up config file
temp_config_file = tempfile.NamedTemporaryFile(delete=False, suffix=".yaml")
data_request_api.stable.utilities.config.CONFIG_FILE = pathlib.Path(
    temp_config_file.name
)

# Configure logger for testing
change_log_file(default=True)
change_log_level("info")


def test_parse_version():
    "Test the _parse_version function with different version strings."
    assert dc._parse_version("v1.0.0") == (1, 0, 0, "", 0)
    assert dc._parse_version("v1.0alpha2") == (1, 0, 0, "a", 2)
    assert dc._parse_version("1.0.0a3") == (1, 0, 0, "a", 3)
    assert dc._parse_version("1.0.0beta") == (1, 0, 0, "b", 0)
    assert dc._parse_version("something") == (0, 0, 0, "", 0)
    with pytest.raises(TypeError):
        dc._parse_version(None)


def test_get_versions():
    "Test the get_versions function."
    versions = dc.get_versions()
    assert "dev" in versions
    assert "v1.0alpha" in versions
    assert "v1.0beta" in versions


def test_get_versions_list_branches():
    "Test the get_versions function for branches."
    branches = dc.get_versions(target="branches")
    assert "dev" not in branches
    assert "main" not in branches


def test_get_latest_version(monkeypatch):
    "Test the _get_latest_version function."
    monkeypatch.setattr(dc, "get_versions", lambda: ["1.0.0", "2.0.2b", "2.0.2a"])
    assert dc._get_latest_version() == "1.0.0"
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
    jsondict = dc.load("dev", consolidate=False)
    assert isinstance(jsondict, dict)
    assert os.path.isfile(tmp_path / "dev" / dc._json_raw)
    assert not os.path.isfile(tmp_path / "dev" / dc._json_release)

    # Load release export without consolidation
    jsondict = dc.load("dev", export="release", consolidate=False)
    assert isinstance(jsondict, dict)
    assert os.path.isfile(tmp_path / "dev" / dc._json_release)


def test_load_consolidate(tmp_path):
    "Test the load function."
    dc._dreq_res = str(tmp_path)

    with pytest.raises(ValueError):
        jsondict = dc.load(" invalid-version ")

    # Load multi-base export with consolidation
    with pytest.raises(KeyError):
        jsondict = dc.load("dev", consolidate=True)
    # assert isinstance(jsondict, dict)
    # assert os.path.isfile(tmp_path / "dev" / dc._json_raw)
    # assert not os.path.isfile(tmp_path / "dev" / dc._json_release)

    # Load release export with consolidation
    jsondict = dc.load("dev", export="release", consolidate=True)
    assert isinstance(jsondict, dict)
    assert os.path.isfile(tmp_path / "dev" / dc._json_release)


class TestDreqContent:
    """
    Test various functions of the dreq_content module.
    """

    @pytest.fixture(autouse=True, scope="function")
    def setup(self, tmp_path):
        self.versions = ["v1.0.0", "1.0.1", "2.0.1b", "2.0.1", "2.0.2b"]
        self.branches = ["one", "or", "another"]
        self.dreq_res = tmp_path
        for v in self.versions:
            (self.dreq_res / v).mkdir()
            (self.dreq_res / v / dc._json_release).write_text("{}")
        for b in self.branches:
            (self.dreq_res / b).mkdir()
            (self.dreq_res / b / dc._json_raw).write_text("{}")

    def test_get_cached(self):
        "Test the get_cached function."
        dc._dreq_res = self.dreq_res
        # Basic
        cached_versions = dc.get_cached()
        assert set(cached_versions) == set(self.versions + self.branches)

        # With export kwarg "release"
        cached_tags = dc.get_cached(export="release")
        assert set(cached_tags) == set(self.versions)

        # With export kwarg "raw"
        cached_branches = dc.get_cached(export="raw")
        assert set(cached_branches) == set(self.branches)

        # With invalid export kwarg
        with pytest.warns(UserWarning, match="Unknown export type"):
            dc.get_cached(export="invalid")

    def test_delete(self, caplog):
        "Test the delete function."
        dc._dreq_res = self.dreq_res
        # Delete non-existent version

        dc.delete("notpresent")
        assert len(caplog.text.splitlines()) == 1
        assert "No version(s) found to delete." in caplog.text

        # Delete only branches / dryrun
        caplog.clear()
        dc.delete("all", export="raw", dryrun=True)
        assert len(caplog.text.splitlines()) == 5
        assert "Deleting the following version(s):" in caplog.text
        for b in self.branches:
            assert (
                f"Dryrun: would delete '{dc._dreq_res / b / dc._json_raw}'."
                in caplog.text
            )

        # Delete all but latest
        dc.delete(keep_latest=True)
        assert set(dc.get_cached()) == {"2.0.1", "2.0.2b"}
        assert dc.get_cached(export="raw") == []

        # Delete 2.0.1 with warning
        with pytest.warns(UserWarning, match=" option is ignored "):
            dc.delete("2.0.1", keep_latest=True)

        # Delete all with ValueError for kwargs
        with pytest.raises(ValueError):
            dc.delete(export="none")

        # Delete all
        dc.delete()
        assert dc.get_cached() == []

        # Now there is no ValueError since no version is found
        dc.delete(export="none")

    # def test_load(self):
    #    dc._dreq_res = self.tmp_dir.name
    #    data = dc.load("1.0.0")
    #    assert data == {}
