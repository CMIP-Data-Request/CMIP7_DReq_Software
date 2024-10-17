import json
import os
import re
import time
import warnings
from filecmp import cmp
from shutil import move

import pooch
import requests

# Base URL template for fetching Dreq content json files from GitHub
_json_export = "dreq_raw_export.json"
_dev_branch = "main"
# _github_org = "WCRP-CMIP"
_github_org = "CMIP-Data-Request"
REPO_RAW_URL = "https://raw.githubusercontent.com/{_github_org}/CMIP7_DReq_Content/{version}/airtable_export/{_json_export}"

# API URL for fetching tags
REPO_API_URL = f"https://api.github.com/repos/{_github_org}/CMIP7_DReq_content/tags"

# List of tags - will be populated by get_versions()
versions = []
_versions_retrieved_last = 0
branches = []
_branches_retrieved_last = 0

# Regex pattern for version parsing (captures major, minor, patch and optional pre-release parts)
_version_pattern = re.compile(
    r"^v?(\d+)\.(\d+)(?:\.(\d+))?((?:alpha|beta|a|b)?)?(\d*)$", re.IGNORECASE
)


# Directory where to find/store the data request JSON files
_dreq_res = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dreq_res")


def _parse_version(version):
    """Parse a version tag and return a tuple for sorting.

    Args:
        version (str): The version tag to parse.

    Returns:
        tuple: The parsed version tuple:
               (major, minor, patch, pre_release_type, pre_release_number)
    """
    match = _version_pattern.match(version)
    if match:
        major, minor, patch = map(lambda x: int(x) if x else 0, match.groups()[:3])
        # 'a' for alpha, 'b' for beta, or None
        pre_release_type = match.group(4)[0] if match.group(4) else None
        # alpha/beta version number or 0
        pre_release_number = (
            int(match.group(5)) if match.group(5) and pre_release_type else 0
        )
        return (major, minor, patch, pre_release_type or "", pre_release_number)
    # if no valid version
    return (0, 0, 0, "", 0)


def get_cached():
    """Get list of cached versions.

    Returns:
        list: The list of cached versions.
    """
    local_versions = []
    if os.path.isdir(_dreq_res):
        # List all subdirectories in the dreq_res directory that include a dreq.json
        #   - the subdirectory name is the tag name
        local_versions = [
            name
            for name in os.listdir(_dreq_res)
            if os.path.isfile(os.path.join(_dreq_res, name, _json_export))
        ]
    return local_versions


def get_versions(list_branches=False):
    """Fetch list of tags from the GitHub repository using the GitHub API.

    Args:
        list_branches (bool): If True, lists only branches and not tags.
                              The main development branch is excluded as it is
                              included in the list of tags. The default is False.
    Returns:
        list: A list of tags (or optionally branches).
    """
    global versions
    global _versions_retrieved_last
    global branches
    global _branches_retrieved_last
    if list_branches:
        if not branches or _branches_retrieved_last - time.time() > 60 * 60:
            # Request the list of branches via the GitHub API
            response = requests.get(REPO_API_URL.replace("tags", "branches"))

            # Raise an error for bad responses
            response.raise_for_status()

            # Extract the list of branches from the response
            branches = [
                branch["name"]
                for branch in response.json()
                if "name" in branch and branch["name"] != _dev_branch
            ] or []

            # Update the last time the branches were retrieved
            _branches_retrieved_last = time.time()

        # List branches hosted on GitHub
        return branches

    # Retrieve list of tags hosted on GitHub
    if not versions or _versions_retrieved_last - time.time() > 60 * 60:
        # Request the list of tags via the GitHub API
        response = requests.get(REPO_API_URL)

        # Raise an error for bad responses
        response.raise_for_status()

        # Extract the list of tags from the response
        versions = [tag["name"] for tag in response.json() if "name" in tag] or []
        versions.append("dev")

        # Update the last time the tags were retrieved
        _versions_retrieved_last = time.time()

    # List tags hosted on GitHub
    return versions


def _get_latest_version(stable=True):
    """Get the latest version

    Args:
        stable (bool): If True, return the latest stable version.
                       If False, return the latest version (i.e. incl. alpha/beta versions).
                       The default is True.


    Returns:
        str: The latest version, or None if no versions are found.
    """
    versions = get_versions()
    if stable:
        sversions = [
            version
            for version in versions
            if all([x not in version for x in ["a", "b", "dev"]])
        ]
        return max(sversions, key=_parse_version) if sversions else None
    return max(versions, key=_parse_version)


def retrieve(version="latest_stable"):
    """Retrieve the JSON file for the specified version

    Args:
        version (str): The version to retrieve.
                       Can be 'latest', 'latest_stable', 'dev', or 'all'
                       or a specific version, eg. '1.0.0'.
                       The default is 'latest_stable'.

    Returns:
        dict: The path to the retrieved JSON file.

    Raises:
        ValueError: If the specified version is not found.
    """
    if version == "latest":
        versions = [_get_latest_version()]
    elif version == "latest_stable":
        versions = [_get_latest_version(stable=True)]
    elif version == "dev":
        versions = ["dev"]
    elif version == "all":
        versions = get_versions()
    else:
        versions = [version]

    if versions == [None] or not versions:
        raise ValueError(f"Version '{version}' not found.")

    json_paths = dict()
    for version in versions:
        # Define the path for storing the dreq.json in the installation directory
        #  Store it as path_to_dreqapi/dreq_api/dreq_res/version/{_json_export}
        retrieve_to_dir = os.path.join(_dreq_res, version)
        json_path = os.path.join(retrieve_to_dir, _json_export)
        os.makedirs(retrieve_to_dir, exist_ok=True)

        # If not already cached download with POOCH
        if not os.path.isfile(json_path):
            # Download with pooch - use "main" branch for "dev"
            try:
                json_path = pooch.retrieve(
                    path=retrieve_to_dir,
                    url=REPO_RAW_URL.format(
                        version=_dev_branch if version == "dev" else version,
                        _json_export=_json_export,
                        _github_org=_github_org,
                    ),
                    known_hash=None,
                    fname=_json_export,
                )
            except Exception as e:
                print(f"Could not retrieve version {version}: {e}")
                continue
            print(f"Retrieved version '{version}'.")

        # or if the version is "dev" or a branch rather than a tag
        elif version == "dev" or version not in get_versions():
            # Download with pooch to temporary file and compare to cached version
            json_path_temp = json_path + ".tmp"
            try:
                # Delete temp file if it exists
                if os.path.exists(json_path_temp):
                    os.remove(json_path_temp)
                # Retrieve
                json_path_temp = pooch.retrieve(
                    path=retrieve_to_dir,
                    url=REPO_RAW_URL.format(
                        version=_dev_branch if version == "dev" else version,
                        _json_export=_json_export,
                        _github_org=_github_org,
                    ),
                    known_hash=None,
                    fname=_json_export + ".tmp",
                )
                # Compare files
                if not cmp(json_path, json_path_temp, shallow=False):
                    move(json_path_temp, json_path)
                    print(f"Updated version '{version}'.")
                else:
                    os.remove(json_path_temp)
                    print(f"Version '{version}' is up to date.")
            except Exception as e:
                print(f"Potential update for version {version} failed: {e}")

        # Store the path to the dreq.json in the json_paths dictionary
        json_paths[version] = json_path

    return json_paths


def delete(version="all", keep_latest=False):
    """Delete one or all cached versions with option to keep latest versions.

    Args:
        version (str): The version to delete.
                       Can be 'all' or a specific version, eg. '1.0.0'.
                       The default is 'all'.
        keep_latest (bool): If True, keep the latest stable, prerelease and "dev" versions.
                            If False, delete all locally cached versions.
                            The default is False.
    """
    # Get locally cached versions
    local_versions = get_cached()

    if version == "all":
        if keep_latest:
            # Identify the latest stable and prerelease versions
            valid_versions = [v for v in local_versions if _version_pattern.match(v)]
            valid_sversions = [
                v for v in valid_versions if "a" not in v and "b" not in v
            ]
            latest = False
            latest_stable = False
            if valid_versions:
                latest = max(valid_versions, key=_parse_version)
            if valid_sversions:
                latest_stable = max(valid_sversions, key=_parse_version)
            to_keep = [v for v in ["dev", latest, latest_stable] if v]
            local_versions = [v for v in local_versions if v not in to_keep]
    else:
        if keep_latest:
            warnings.warn(
                "'keep_latest' option is ignored when 'version' is not 'all'."
            )
        local_versions = [version] if version in local_versions else []

    # Deletion
    if local_versions:
        print("Deleting the following version(s):")
        print(local_versions)
    else:
        print("No version(s) found to delete.")

    cached_files = [os.path.join(_dreq_res, v, _json_export) for v in local_versions]
    for f in cached_files:
        os.remove(f)


def load(version="latest_stable"):
    """Load the JSON file for the specified version.

    Args:
        version: The version to load.
                 Can be 'latest', 'latest_stable', 'dev',
                 or a specific version, eg. '1.0.0'.
                 The default is 'latest_stable'.

    Returns:
        dict: of the loaded JSON file.
    """
    if version == "all":
        raise ValueError("Cannot load 'all' versions.")
    json_path = retrieve(version)[version]
    with open(json_path) as f:
        return json.load(f)
