
# CMIP7 Data Request Software

This repository contains python code to interact with the [CMIP7 data request](https://wcrp-cmip.org/cmip7/cmip7-data-request/). 
Its aim is to provide an API and scripts that can produce lists of the variables requested for each CMIP7 experiment, information about the requested variables, and in general allow users to querying and utilize the information in the data request.


## v1.0 release

The latest **official release** (22 Nov 2024) is tagged as `v1.0`. 
Access all information about the v1.0 release [on the CMIP website](https://wcrp-cmip.org/cmip7-data-request-v1-0/).
Those trying out the Software should use:
- the `v1.0` tag, or
- the latest stable version, which will be the most recent commmit on the `main` branch.

For the **Quick Start** guide, please see below.

**This Software is under active development** and will continue to evolve following the `v1.0` release. 
Accordingly we encourage users to try the latest stable version in order to access the latest features.

The next sections provide a brief overview of the Software and explain how to get started.
While the Software is a work in progress, **the Data Request Task Team encourages user feedback to help us improve upcoming versions.**
We are releasing v1.0 at an early stage of development in order to encourage community input into its design.
Here are some ways to provide feedback:
- For specific questions or issues (such as bugs) please [open a github issue](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/issues).
- For more general questions or concerns, such as suggestions for new features, contribute to the Software's [github discussion forum](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/discussions).


## Overview

The CMIP7 data request **Software** and **Content** are version controlled in separate github repositories.
Official releases of the data request correspond to a tag in each of these repositories (e.g., `v1.0`). 
However the Software can interact with different versions of the Content - for example, to examine changes that have occurred when a new version of the data request is issued.

The data request **Content**, which is version controlled [here](https://github.com/CMIP-Data-Request/CMIP7_DReq_Content), refers to all of the information comprising the data request. 
This includes descriptions of Opportunities and their lists of requested variables, definitions of the variables, etc.
The Content is stored as a large `json` file, which is read by the data request Software. 
However users should not interact with this `json` file directly and its structure is not designed for readability.
Users do not need to manually download the Content as this is done automatically by the Software (see "Getting Started", below, for further details).

The data request Content is an automatic export from **Airtable**, which a cloud platform used by the Data Request Task Team and CMIP IPO to facilitate ongoing community engagement in developing the data request.
Airtable provides users with a browseable web interface to explore data request information contained in relational databases that are referred to as "bases".
These Airtable bases contain interlinked tables that constitute the primary source of data request information.

The Content of each official release of the data request can be explored online using the [Airtable interface](https://bit.ly/CMIP7-DReq-v1_0).
This provides a browseable web view of the Content, allowing users to follow links between different elements of the data request - for example, to view the variables requested by a given Opportunity, or to view the Opportunities that request a given variable.
This view is complementary to the access to the Content that is provided via the Software, and both access methods (Airtable and Software) are based on the same underlying information.


Using the data request **Software** provides a way to interact programmatically with the data request Content, such as to:

- Given a list of supported opportunities and their priorities, produce lists of variables to output for each experiment (see Getting Started section to test this functionality),
- Output the CF-compliant metadata characterizing each variable - an example file with some of the metadata for each requested variable is [available in v1.0](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/tree/main/scripts/variable_info/all_var_info.json),
- Compare the requested output of CMIP7 experiments to a given model's published CMIP6 output.

An aim of the Software is to facilitate integration of the data request into modelling workflows.
Suggestions for functionality are welcome in the [github discussion forum](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/discussions).


During development, the Software and Content repositories reside in the github organisation https://github.com/CMIP-Data-Request.
Stable releases will eventually be migrated into the https://github.com/WCRP-CMIP organisation.


## Quick Start

To get started, in a shell session clone the Software and navigate to the `scripts/` directory:
```
git clone git@github.com:CMIP-Data-Request/CMIP7_DReq_Software.git
cd CMIP7_DReq_Software/scripts
```
The `env.yml` file can then be used to create a conda environment in which to run the Software:
```
conda env create -n my_dreq_env --file env.yml
```
where `my_dreq_env` can be replaced with your preferred environment name. 
Then activate this environment:
```
conda activate my_dreq_env
```
and run the the example script:
```
python workflow_example.py
```
This will produce a `json` file listing requested variables for each CMIP7 experiment.
The same functionality is available from a command-line interface. 
For example:
```
./export_dreq_lists_json.py v1.0 dreq_list.json --all_opportunities
```
will produce a file a listing the variables requested from all CMIP7 AR7 Fast Track experiments assuming that all Data Request Opportunities are supported.
The list can be customized by specifying which Opportunities are supported or filtering based on one or more experiment names.
The `-h` option provides further usage guidance:
```
./export_dreq_lists_json.py -h
```


## Further details

Th example script and the command-line tool contain a workflow to access the data request Content, specify a list of Opportunities and priority levels of variables, and output the lists of variables requested from each experiment in the specified Opportunities.
An example of the json file produced by running this script, which contains the names of output variables requested for each experiment, is available in `scripts/examples/`.
The example output file assumes that all data request Opportunities are supported at all priority levels, but this choice can be modified by the user.

Each listed variable in the output file is currently identified by a unique "compound name" using CMIP6-era table names and short variable names (`Amon.tas`, `Omon.tos`, etc).
Variable names may change in upcoming releases, but in any case a mapping to CMIP6-era variable names will be retained in the data request so as to allow comparison with CMIP6 output (for those variables that were defined in CMIP6).

To access the data request Content, the example script first needs to identify the version of the data request Content that is being used. 
This is done in the example script by specifying a tag in the Content repo and calling the retrieval function.
For example:
```
dc.retrieve('v1.0')
```
downloads `v1.0` of the Content into local cache, if it is not already there.
The script can then access it by loading it into a python dict variable:
```
content = dc.load('v1.0')
```
Currently a single version of the Content `json` file for a versioned release is roughly 20 MB in size.
The size of local cache can be managed by deleting unused versions.
For example, to remove a specific version:
```
dc.delete('v1.0')
```
Or to remove all locally cached versions:
```
dc.delete()
```
