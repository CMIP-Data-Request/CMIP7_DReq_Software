import os

import dreq_content as dc
import pytest


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


def test_get_versions_list_branches():
    "Test the get_versions function for branches."
    branches = dc.get_versions(target="branches")
    assert "dev" not in branches
    assert "main" not in branches
    assert len(branches) > 0


def test_get_cached(tmp_path):
    # Create a temporary directory with a subdirectory containing a dreq.json file
    version_dir = tmp_path / "v1.0.0"
    version_dir.mkdir()
    (version_dir / dc._json_export).touch()

    # Set the _dreq_res variable to the temporary directory
    dc._dreq_res = str(tmp_path)

    # Test the get_cached function
    cached_versions = dc.get_cached()
    assert cached_versions == ["v1.0.0"]


def test_retrieve(tmp_path, capfd):
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
    stdout = capfd.readouterr().out.splitlines()
    assert len(stdout) == 2
    assert "Retrieved version 'dev'." in stdout
    assert "Updated version 'dev'." in stdout
    # ... and the file was replaced
    with open(json_path) as f:
        lines_update = f.read().splitlines(keepends=True)
    assert lines == lines_update


def test_retrieve_with_invalid_version(tmp_path):
    "Test the retrieval function with an invalid version."
    dc._dreq_res = str(tmp_path)
    with pytest.warns(UserWarning, match="Could not retrieve version"):
        dc.retrieve(" invalid-version ")


def test_api_and_html_request():
    "Test the _send_api_request and _send_html_request functions."
    tags1 = set(dc._send_api_request(dc.REPO_API_URL, "", "tags"))
    tags2 = set(dc._send_html_request(dc.REPO_PAGE_URL, "tags"))
    assert tags1 == tags2

    branches1 = set(dc._send_api_request(dc.REPO_API_URL, "", "branches"))
    branches2 = set(dc._send_html_request(dc.REPO_PAGE_URL, "branches"))
    assert branches1 == branches2


def test_load(tmp_path):
    "Test the load function."
    dc._dreq_res = str(tmp_path)

    with pytest.warns(UserWarning, match="Could not retrieve version"):
        with pytest.raises(KeyError):
            jsondict = dc.load(" invalid-version ")

    jsondict = dc.load("dev")
    assert isinstance(jsondict, dict)
    assert os.path.isfile(tmp_path / "dev" / dc._json_export)
