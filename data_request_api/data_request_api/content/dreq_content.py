#!/usr/bin/env python

import atexit
import json
import os
import re
import time
import warnings
from filecmp import cmp
from shutil import move

import pooch
import requests
from bs4 import BeautifulSoup

import data_request_api.utilities.config as dreqcfg
from data_request_api.content import consolidate_export as ce
from data_request_api.content.mapping_table import mapping_table
from data_request_api.utilities.decorators import append_kwargs_from_config
from data_request_api.utilities.logger import get_logger  # noqa

# Suppress pooch info output
pooch.get_logger().setLevel("WARNING")

# File names of Airtable exports in JSON format
_json_raw = "dreq_raw_export.json"
_json_release = "dreq_release_export.json"

# Base URL template for fetching Dreq content json files from GitHub
# _github_org = "WCRP-CMIP"
_github_org = "CMIP-Data-Request"
REPO_RAW_URL = (
    "https://raw.githubusercontent.com/{_github_org}/CMIP7_DReq_Content/{version}/airtable_export/{_json_export}"
)
_dev_branch = "main"

# API URL for fetching tags or branches
REPO_API_URL = f"https://api.github.com/repos/{_github_org}/CMIP7_DReq_content/"

# Alternative Repo URL for fetching tags
REPO_PAGE_URL = f"https://github.com/{_github_org}/CMIP7_DReq_content/"

# List of versions (tags, branches) - will be populated by get_versions(target="tags" or "branches")
versions = {"tags": [], "branches": []}
_versions_retrieved_last = {"tags": 0, "branches": 0}

# When retrieving versions (tags, branches), fall back to parsing the public GitHub page for
#  the GitHub API returning the following status codes:
#   403 Forbidden
#   429 Too Many Requests
#   500 Internal Server Error
#   502 Bad Gateway
#   503 Service Unavailable
#   504 Gateway Timeout
_fallback_status_codes = [403, 429, 500, 502, 503, 504]

# Regex pattern for version parsing (captures major, minor, patch and optional pre-release parts)
_version_pattern = re.compile(r"^v?(\d+)\.(\d+)(?:\.(\d+))?((?:alpha|beta|a|b)?)?(\d*)$", re.IGNORECASE)

# Directory where to find/store the data request JSON files
try:
    _dreq_res = dreqcfg.load_config()["cache_dir"]
except KeyError:
    _dreq_res = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dreq_res")

_dreq_content_loaded = {}

# Internal flag used to determine whether a warning on API version can be issued
# (Purpose is to prevent the warning being issued more than once per session)
_CHECK_API_VERSION = True


def _parse_version(version):
    """Parse a version tag and return a tuple for sorting.

    Parameters
    ----------
    version : str
        The version tag to parse.

    Returns
    -------
    tuple
        The parsed version tuple:
        (major, minor, patch, pre_release_type, pre_release_number)
    """
    match = _version_pattern.match(version)
    if match:
        major, minor, patch = map(lambda x: int(x) if x else 0, match.groups()[:3])
        # 'a' for alpha, 'b' for beta, or None
        pre_release_type = match.group(4)[0] if match.group(4) else None
        # alpha/beta version number or 0
        pre_release_number = int(match.group(5)) if match.group(5) and pre_release_type else 0
        return (major, minor, patch, pre_release_type or "", pre_release_number)
    # if no valid version
    return (0, 0, 0, "", 0)


@append_kwargs_from_config
def get_cached(**kwargs):
    """Get list of cached versions.

    Parameters
    ----------
    **kwargs
        export : {'raw', 'release'}, optional
            Export type. Defaults to "release".

    Returns
    -------
    list
        The list of cached versions.

    Raises
    ------
    Warning
        If known kwargs have an invalid value.
    """
    local_versions = []
    if os.path.isdir(_dreq_res):
        # List all subdirectories in the dreq_res directory that include both dreq.json files
        #   - the subdirectory name is the tag name
        if "export" in kwargs:
            if kwargs["export"] == "raw":
                json_export = _json_raw
            elif kwargs["export"] == "release":
                json_export = _json_release
        local_versions = [
            name for name in os.listdir(_dreq_res) if os.path.isfile(os.path.join(_dreq_res, name, json_export))
        ]
    return local_versions


def _send_api_request(api_url, page_url="", target="tags"):
    """
    Send a request to the GitHub API for a list of tags or branches.

    Parameters
    ----------
    api_url : str
        The base URL to send the request to.
    page_url : str, optional
        The page URL to send the request to if the GitHub API request to api_url fails.
    target : str, optional
        The target to send the request for, either 'tags' or 'branches' (default is 'tags').

    Returns
    -------
    list
        A list of tags (or optionally branches).

    Raises
    ------
    Warning
        If the GitHub API is not accessible and page_url is not set.
    Warning
        If a HTTP error occurs when retrieving the list of tags or branches.
    Warning
        If an exception occurs when retrieving the list of tags or branches.
    """
    # Request the list of tags or branches via the GitHub API
    global _fallback_status_codes
    results = []
    response = requests.get(api_url + target)
    try:
        # Raise an error for bad responses
        response.raise_for_status()

        # Extract the list of tags or branches from the response
        results = [entry["name"] for entry in response.json() if "name" in entry and entry["name"] != _dev_branch] or []

    except requests.exceptions.HTTPError as http_err:
        if response.status_code in _fallback_status_codes:
            if page_url:
                warnings.warn(
                    f"GitHub API not accessible, falling back to parsing the public GitHub page: {http_err}"
                )
                results = _send_html_request(page_url, target)
            else:
                warnings.warn(
                    f"A HTTP error occurred when retrieving '{target}' via the"
                    f" GitHub API ({response.status_code}): {http_err}"
                )
        else:
            warnings.warn(f"A HTTP error occurred when retrieving '{target}' ({response.status_code}): {http_err}")
    except Exception as e:
        warnings.warn(f"An error occurred when retrieving '{target}': {e}")

    return results


def _send_html_request(page_url, target="tags"):
    """
    Fallback method: Parse the the public GitHub page to get the list of tags or branches.

    Parameters
    ----------
    page_url : str
        The base URL to send the request to.
    target : str, optional
        The target to send the request for, either 'tags' or 'branches' (default is 'tags').

    Returns
    -------
    list
        A list of tags (or optionally branches).

    Raises
    ------
    ValueError
        If the html response cannot be parsed.
    Warning
        If a HTTP error occurs when retrieving the list of tags or branches.

    Notes
    -----
        Making use of the pagination mechanism of GitHub could only be tested for tags
        so might not work for branches.
    """
    # Request the list of tags or (active) branches via the GitHub Page
    results = []
    addon = ""
    if target == "branches":
        addon = "/active"
    current_url = page_url + target + addon
    current_urls = list()
    while current_url:
        response = requests.get(current_url)
        try:
            # Raise an error for bad responses
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            if target == "branches":
                # Find the branches on the page - GitHub embeds json data under the script tag
                script_tag = soup.find("script", {"data-target": "react-app.embeddedData"})
                if not script_tag:
                    raise ValueError("Could not find the 'script' tag in the html response.")
                json_response = json.loads(script_tag.string)
                results_json = json_response["payload"][target]
                results += [
                    entry["name"] for entry in results_json if "name" in entry and entry["name"] != _dev_branch
                ] or []
            else:
                # Find the tags on the page - GitHub uses "Link--primary" class for tags / branches
                results += [entry.text.strip() for entry in soup.find_all("a", class_="Link--primary")]

            # Check for pagination links and construct URL for the next page
            # ToDo: I could not find a repo with more branches than fit on a single page
            #       so the next_page_links may have to be adapted for branches
            next_page_links = soup.find_all("a", {"href": lambda x: x and "after=" in x})
            if next_page_links:
                current_urls.append(current_url)
                current_url = "https://github.com" + next_page_links[-1]["href"]
                if current_url in current_urls:
                    current_url = None
            else:
                current_url = None
        except Exception as e:
            warnings.warn(f"An error occurred when retrieving '{target}': {e}")
            current_url = None

    return results


@append_kwargs_from_config
def get_versions(target="tags", **kwargs):
    """Fetch list of tags from the GitHub repository using the GitHub API.

    Args:
        target (str): The target to send the request for, either 'tags' or 'branches'.
                      The default is 'tags'.

    Parameters
    ----------
    target : str, optional
        The target to send the request for, either 'tags' or 'branches' (default is 'tags').
        Please note that the main development branch is excluded from the list of branches
        and is included in the list of tags.
    **kwargs
        offline : bool, optional
            Whether to disable online requests / retrievals. Defaults to False.

    Returns
    -------
    list
        A list of tags or branches.

    Raises
    ------
    ValueError
        If target is not 'tags' or 'branches'.
    """
    global versions
    global _versions_retrieved_last
    global _CHECK_API_VERSION

    if target not in ["tags", "branches"]:
        raise ValueError("target must be 'tags' or 'branches'.")

    if "offline" in kwargs and kwargs["offline"]:
        lversions = get_cached(**kwargs)
        if target == "tags":
            versions[target] = [lv for lv in lversions if lv == "dev" or _parse_version(lv) != (0, 0, 0, "", 0)]
        else:
            versions[target] = [lv for lv in lversions if lv != "dev" and _parse_version(lv) == (0, 0, 0, "", 0)]
    else:
        # Retrieve the list of tags or branches from the GitHub API
        if not versions[target] or _versions_retrieved_last[target] - time.time() > 60 * 60:
            versions[target] = _send_api_request(REPO_API_URL, REPO_PAGE_URL, target)

            # Update the last time the tags/branches were retrieved
            _versions_retrieved_last[target] = time.time()

        if target == "tags" and "dev" not in versions[target]:
            versions[target].append("dev")

    if kwargs['check_api_version'] and not kwargs["offline"]:
        # Warn user if the API version is not the latest one available on PyPI
        if _CHECK_API_VERSION:
            atexit.register(dreqcfg.check_api_version)
            # Set flag to prevent the same warning being shown more than once
            _CHECK_API_VERSION = False

    # List tags of dreq versions hosted on GitHub
    return versions[target]


@append_kwargs_from_config
def _get_latest_version(stable=True, **kwargs):
    """Get the latest version

    Parameters
    ----------
    stable : bool, optional
        If True, return the latest stable version. If False, return the latest version
        (i.e. incl. alpha/beta versions) (default is True).
    **kwargs
        offline : bool, optional
            Whether to disable online requests / retrievals. Defaults to False.

    Returns
    -------
    str
        The latest version, or None if no versions are found.
    """
    versions = get_versions(**kwargs)
    if stable:
        sversions = [version for version in versions if all([x not in version for x in ["a", "b", "dev"]])]
        return max(sversions, key=_parse_version) if sversions else None
    return max(versions, key=_parse_version)


@append_kwargs_from_config
def retrieve(version="latest_stable", **kwargs):
    """Retrieve the JSON file for the specified version

    Parameters
    ----------
    version: str, optional
        The version to retrieve. Can be 'latest', 'latest_stable',
        'dev', or 'all' or a specific version, eg. '1.0.0'.
        (default is 'latest_stable').
    **kwargs
        export : {'raw', 'release'}, optional
            Export type. Defaults to 'release'.
        offline : bool, optional
            Whether to disable online requests / retrievals. Defaults to False.

    Returns
    -------
    dict
        The path to the retrieved JSON file.

    Raises
    ------
    ValueError
        If the specified version is not found.
    Warning
        If the specified version does not have the specified export type.
    Warning
        If the known kwargs have an invalid value.
    Warning
        If the specified version could not be downloaded or (if applicable) updated.
    """
    logger = get_logger()
    if version == "latest":
        versions = [_get_latest_version(stable=False, **kwargs)]
    elif version == "latest_stable":
        versions = [_get_latest_version(stable=True, **kwargs)]
    elif version == "dev":
        versions = ["dev"]
    elif version == "all":
        versions = get_versions(**kwargs)
    else:
        if version not in get_versions(**kwargs) + get_versions(target="branches", **kwargs):
            if version not in get_cached(**kwargs):
                raise ValueError(f"Version '{version}' not found.")
        versions = [version]

    if versions == [None] or not versions:
        raise ValueError(f"Version '{version}' not found.")
    elif version in ["v1.0alpha"] and "export" in kwargs and kwargs["export"] == "raw":
        warnings.warn(f"For version '{version}' no raw export exists. Defaulting to release export.")

    json_paths = dict()
    for version in versions:
        # Define the path for storing the dreq.json in the installation directory
        #  Store it as path_to_api/content/dreq_res/version/{_json_raw/release}
        retrieve_to_dir = os.path.join(_dreq_res, version)
        # Decide whether to download release or raw json file
        if "export" in kwargs:
            if kwargs["export"] == "release" or version == "v1.0alpha":
                json_export = _json_release
            elif kwargs["export"] == "raw":
                json_export = _json_raw
        elif _version_pattern.match(version):
            json_export = _json_release
        else:
            json_export = _json_raw
        json_path = os.path.join(retrieve_to_dir, json_export)

        if "offline" in kwargs and kwargs["offline"]:
            if os.path.isfile(json_path):
                json_paths[version] = json_path
        else:
            os.makedirs(retrieve_to_dir, exist_ok=True)

            # If not already cached download with POOCH
            if not os.path.isfile(json_path):
                # Download with pooch - use "main" branch for "dev"
                try:
                    json_path = pooch.retrieve(
                        path=retrieve_to_dir,
                        url=REPO_RAW_URL.format(
                            version=(_dev_branch if version == "dev" else version),
                            _json_export=json_export,
                            _github_org=_github_org,
                        ),
                        known_hash=None,
                        fname=json_export,
                    )
                except Exception as e:
                    warnings.warn(f"Could not retrieve version '{version}': {e}")
                    continue
                logger.info(f"Retrieved version '{version}'.")

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
                            version=(_dev_branch if version == "dev" else version),
                            _json_export=json_export,
                            _github_org=_github_org,
                        ),
                        known_hash=None,
                        fname=json_export + ".tmp",
                    )
                    # Compare files
                    if not cmp(json_path, json_path_temp, shallow=False):
                        move(json_path_temp, json_path)
                        logger.info(f"Updated version '{version}'.")
                    else:
                        os.remove(json_path_temp)
                except Exception as e:
                    warnings.warn(f"Potential update for version '{version}' failed: {e}")

            # Store the path to the dreq.json in the json_paths dictionary
            json_paths[version] = json_path

    # Capture no correct export found for cached versions (offline mode)
    if not json_paths or json_paths == {}:
        raise ValueError(
            "The version(s) you requested are not cached. Please deactivate offline mode and try again."
        )

    return json_paths


@append_kwargs_from_config
def delete(version="all", keep_latest=False, **kwargs):
    """Delete one or all cached versions with option to keep latest versions.

    Parameters
    ----------
    version : str, optional
        The version to delete. Can be 'all' or a specific version,
        eg. '1.0.0' (default is 'all').
    keep_latest : bool, optional
        If True, keep the latest stable, prerelease and "dev" versions.
        If False, delete all locally cached versions (default is False).
    **kwargs
        export : {'raw', 'release'}, optional
            Export type. Defaults to 'release'.
        dryrun : bool, optional
            Whether to only list the files that would be removed instead of actually
            removing them. Defaults to False.

    Returns
    -------
    None

    Raises
    ------
    ValueError
        If the known kwargs have an invalid value.
    Warning
        If 'keep_latest' option is active when 'version' is not 'all'.
    """
    logger = get_logger()
    # Get locally cached versions
    local_versions = get_cached(**kwargs)

    if version == "all":
        if keep_latest:
            # Identify the latest stable and prerelease versions
            valid_versions = [v for v in local_versions if _version_pattern.match(v)]
            valid_sversions = [v for v in valid_versions if "a" not in v and "b" not in v]
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
            warnings.warn("'keep_latest' option is ignored when 'version' is not 'all'.")
        local_versions = [version] if version in local_versions else []

    # Deletion
    if local_versions:
        logger.info("Deleting the following version(s):")
        logger.info(local_versions)
    else:
        logger.info("No version(s) found to delete.")
        return

    # Compile file paths
    if kwargs["export"] == "raw":
        cached_files = [os.path.join(_dreq_res, v, _json_raw) for v in local_versions]
    elif kwargs["export"] == "release":
        cached_files = [os.path.join(_dreq_res, v, _json_release) for v in local_versions]

    # Delete files
    for f in cached_files:
        if os.path.isfile(f):
            if "dryrun" in kwargs and kwargs["dryrun"]:
                logger.info(f"Dryrun: would delete '{f}'.")
            else:
                os.remove(f)


@append_kwargs_from_config
def load(version="latest_stable", **kwargs):
    """Load the JSON file for the specified version.

    Args:
        version (str): The version to load.
                 Can be 'latest', 'latest_stable', 'dev',
                 or a specific version, eg. '1.0.0'.
                 The default is 'latest_stable'.
    **kwargs
        export : {'raw', 'release'}, optional
            Export type. Defaults to 'release'.
        consolidate: bool, optional
            Whether to consolidate the data request dictionary after loading it.
            Experimental feature. Defaults to True.
        offline : bool, optional
            Whether to disable online requests / retrievals. Defaults to False.
        force_consolidate : bool, optional
            Whether to force consolidation of the data request dictionary for raw exports
            of versions "<v1.2", where consolidation is not supported. Defaults to False.

    Returns:
        dict: of the loaded JSON file.
    """
    _dreq_content_loaded["json_path"] = ""
    logger = get_logger()
    if version == "all":
        raise ValueError("Cannot load 'all' versions.")

    version_dict = retrieve(version, **kwargs)
    if version_dict == {}:
        logger.info(f"Version '{version}' could not be loaded.")
        return {}
    else:
        json_path = next(iter(version_dict.values()))
        logger.info(f"Loading version {next(iter(version_dict.keys()))}'.")

    _dreq_content_loaded["json_path"] = json_path

    with open(json_path) as f:
        consolidate_error = (
            "Consolidation mapping is not supported for raw exports of versions < v1.2."
            " Set 'export' to \"release\" (recommended), or set 'consolidate' to True"
            " or set 'force_consolidate' to True to force consolidation regardless."
        )
        consolidate_warning = (
            "Consolidation mapping is not supported for raw exports of versions < v1.2." " Forcing it regardless ..."
        )
        if "consolidate" in kwargs:
            if kwargs["consolidate"]:
                if "export" in kwargs and kwargs["export"] == "raw":
                    if _parse_version(version) < _parse_version("v1.2") and version != "dev":
                        if "force_consolidate" in kwargs and kwargs["force_consolidate"]:
                            logger.warning(consolidate_warning)
                        else:
                            logger.error(consolidate_error)
                            raise ValueError(consolidate_error)
                return ce.map_data(json.load(f), mapping_table, next(iter(version_dict.keys())), **kwargs)
            else:
                return json.load(f)
        else:
            if "export" in kwargs and kwargs["export"] == "raw":
                if _parse_version(version) < _parse_version("v1.2") and version != "dev":
                    if "force_consolidate" in kwargs and kwargs["force_consolidate"]:
                        logger.warning(consolidate_warning)
                    else:
                        logger.error(consolidate_error)
                        raise ValueError(consolidate_error)
            return ce.map_data(json.load(f), mapping_table, next(iter(version_dict.keys())), **kwargs)
