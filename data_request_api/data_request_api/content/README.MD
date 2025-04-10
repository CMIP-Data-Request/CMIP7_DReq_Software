
**dreq_content.py**
====================

A Python script for retrieving and managing CMIP7 DReq content.
It is meant as a building block of the DReq API.

**Visible Functions**
--------------------

The following functions are available for use:

### `retrieve(version="latest_stable")`

Retrieve the JSON file for the specified version.

* `version`: The version to retrieve. Can be 'latest', 'latest_stable', 'dev', or a specific version, eg. '1.0.0', or even a branch like 'first_export'.
             'dev' points to the main development branch (in this case 'main'). In case of 'latest' or 'latest_stable', the tags on GitHub will be taken into account.
             Default is 'latest_stable'.
* Returns: A dictionary containing the path to the retrieved JSON file.

### `load(version="latest_stable")`

Load the JSON file for the specified version.

* `version`: The version to load. Can be 'latest', 'latest_stable', 'dev', or a specific version/branch, eg. '1.0.0'. Default is 'latest_stable'. Will attempt to `retrieve` the version to the local cache if needed.
* Returns: A dictionary containing the loaded JSON data.

### `get_versions(target="tags")`

Fetch the list of available versions (tags and main development branch).

* `target`: Can be 'tags' or 'branches'. The main development branch is excluded from 'branches' and considered under 'tags'.
* Returns: A list of available versions.

### `get_cached()`

* Returns: A list of locally cached versions (tags and branches).

### `delete(version="all", keep_latest=False)`

Delete one or all cached versions with option to keep latest versions.

* `version`: The version to delete. Can be 'all' or a specific version, eg. '1.0.0'. Default is 'all'.
* `keep_latest`: If True, keep the latest stable, prerelease and "dev" versions. If False, delete all locally cached versions. 
                 Has no application if `version` is not `"all"`. Note that 'latest' and 'latest_stable' apply on the locally cached
                 versions only. More recent versions that might be available online are not considered. Default is False.

### Function `kwargs`

Mainly to support the development and not intended for common usage, some functions allow `kwargs`to be passed
These are:
- export: "raw" or "release" (supported for `get_cached`, `retrieve`, `load`, `delete`)
  whether to respect the raw or release export json file. Per default, for official releases / tags, the release export json file is processed,
  and else the raw export json file.
- consolidate: True or False (supported for `load`)
  whether to consolidate in case a raw export json file is loaded. The default is to consolidate.
- dryrun: True or False (supported for `delete`)
  whether to only list the files that would be deleted instead of actually deleting them. The default is to delete the files and not to list them.

**Usage Examples**
-----------------

```python
import data_request_api.stable.content.dreq_content as dc

# Get the list of available versions
versions = dc.get_versions()
print(versions)

# List all available branches
branches = dc.get_versions('branches')
print(branches)

# Retrieve the latest stable version
version_dict = dc.retrieve()  # or dc.retrieve("latest_stable")
print(version_dict)

# Retrieve a certain branch/tag
version_dict = dc.retrieve("v1.0beta")
print(version_dict)

# Retrieve all available releases
version_dict = dc.retrieve("all")
print(version_dict)

# Load the latest stable version
dreq = dc.load()  # or dc.load("latest_stable")

# Load the latest version
dreq = dc.load("latest")

# Load the development version
dreq = dc.load("dev")

# Get list of locally cached versions
versions = dc.get_cached()
print(versions)

# Delete all cached versions except the latest, latest stable and "dev" versions
dc.delete(keep_latest=True)

# Delete a certain version
dc.delete("v1.0alpha")
```

