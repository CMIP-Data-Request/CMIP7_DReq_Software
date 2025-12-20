[![pypi](https://img.shields.io/pypi/v/CMIP7-data-request-api.svg)](https://pypi.python.org/pypi/CMIP7-data-request-api)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/CMIP-Data-Request/CMIP7_DReq_Software/main?filepath=notebooks)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/CMIP-Data-Request/CMIP7_DReq_Software/)
[![NBviewer](https://raw.githubusercontent.com/jupyter/design/master/logos/Badges/nbviewer_badge.svg)](https://nbviewer.jupyter.org/github/CMIP-Data-Request/CMIP7_DReq_Software/tree/main/notebooks/)
[![license](https://img.shields.io/github/license/CMIP-Data-Request/CMIP7_DReq_Software.svg)](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/blob/main/LICENSE)
[![status](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)

# CMIP7 Data Request Software

Quick user guide for python software to interact with the [CMIP7 data request](https://wcrp-cmip.org/cmip7/cmip7-data-request/).

## Table of Contents
1. [Purpose](#purpose) 
2. [Release Versions](#release-versions)
3. [Try It Without Installation](#try-it-without-installation)
4. [Installation](#installation)  
5. [Configuration](#configuration)  
6. [Quick Start](#quick-start)
7. [Documentation](#documentation) 
8. [Contributors](#contributors) 
9. [Contact](#contact)  

## Purpose

**The CMIP7 DReq Software**  is Python software designed to interact with the [CMIP7 Data Request](https://wcrp-cmip.org/cmip7/cmip7-data-request/), which is referred to herein as the **Data Request Content** in order to distinguish from the **Software**; the schematic below shows the relationship between the two. It provides an API to *query* and *utilize* the information in the Data Request, including [command-line (CLI) utilities](#command-line-utilities), [example scripts](#python-scripts) and [notebooks](#notebooks) showing how to use the API. 
The main purpose of the CMIP7 DReq API is to extract the requested variables (along with their attributes) according to filters the user activates (a set of CMIP7 Experiments, and/or Opportunities, and/or Frequencies, etc.). It can generate the resulting lists in different formats (csv, json) or return them as python objects that make the API *plugable* in Modelling Centres' data production workflows. 

<img width=750px src=./docs/static/3boxes_schema.png>

**Target audience:**  
- *Modellers* configuring the output variables for climate models running CMIP7 simulations
- *Software engineers* preparing CMIP7 modelling workflows
- *Data providers* preparing CMIP7 netCDF output files for publication on [ESGF](https://esgf.github.io/)

**General features:** exploring the CMIP7 DR content - apply various filters - get the results in different formats.

## Release Versions

The latest **official release** of the CMIP7 Data Request Content is described on the  
[CMIP7 Data Request website](https://wcrp-cmip.org/cmip7-data-request-latest).

### Ways to browse the Data Request Content

You can view the Data Request content in multiple ways:

#### **1. Airtable View**
Online spreadsheet-style view of the Data Request Content:  
https://bit.ly/CMIP7-DReq-latest

#### **2. CMIP7 Data Request Webview**
A static, interactive HTML interface for browsing and searching CMIP7 Data Request records, including changes introduced in new releases, hosted via GitHub Pages.

- **Main entry point (access to all Data Request content versions and Webview tools):**  
  https://CMIP-Data-Request.github.io/cmip7-dreq-webview/index.html 

- **Permanent link to latest Data Request content:**  
  https://CMIP-Data-Request.github.io/cmip7-dreq-webview/latest/index.html  

The Webview provides:
- variable search across multiple attributes  
- browsing of data request changes between releases
- browsing of variable definition changes between releases  
- browsing Data Request content across different releases, with all records cross-linked 

These are the easiest ways to *inspect* the Data Request without installing or using the software.

#### **3. Programmatic Access (this repository)**
Using the CMIP7 Data Request API you can load, filter, query, and export the Data Request programmatically in Python.
This is also possible without installing the software on your local machine, see [Try It Without Installation](#try-it-without-installation).

:warning: **Note:** *The CMIP7 DReq Software versions are not aligned with the CMIP7 Data Request ones. So please, do not infer that e.g. v1.2.2 of the CMIP7 DReq Software "works with" or "reflects"  v1.2.2 of the CMIP7 Data Request, it is not the case!*

## Try It Without Installation

You can launch and interact with this repository  via [Binder](https://mybinder.org/) or [Google Colab](https://colab.research.google.com/). To do so, just click on one of the badges to run it in your browser:

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/CMIP-Data-Request/CMIP7_DReq_Software/main?filepath=notebooks)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/CMIP-Data-Request/CMIP7_DReq_Software/)
<br>
:bulb: This enables you, *without installing anything on your local system*, to play with the [notebooks](#notebooks), in a live environment that is your own playground.
(Note, in Google Colab it may be necessary to add `! pip install CMIP7-data-request-api` to the beginning of the notebooks, while Binder should take care of that for you.)

## Installation

### Install in User mode

Here is described how to install the *CMIP7 DReq Software* python package via `pip` for use as a python module in scripts/software or to use the command-line utilities. (To modify/develop the software, see below for [developer installation instructions](#install-in-developer-mode).)

In a python *venv* or *conda env* in which you want to install the package, do:
```bash
pip install CMIP7-data-request-api
```
If you choose the <u>**venv**</u> solution:
```bash
python -m venv my_dreq_env
source my_dreq_env/bin/activate
python -m pip install --upgrade pip
python -m pip install CMIP7-data-request-api
```
with  `my_dreq_env` being the environment name that can be changed to whatever preferred name.

This will automatically install the dependencies, but if necessary  they can be manually installed by doing:
```bash
wget https://raw.githubusercontent.com/CMIP-Data-Request/CMIP7_DReq_Software/refs/heads/main/requirements.txt
python -m pip install -r requirements.txt 
```
where the [`requirements.txt`](requirements.txt) file is the one present at the root-level  of this repository, which lists the package dependencies.

If a <u>**conda env**</u> is preferred instead of `venv`, an [`env.yml`](env.yml) file with the dependencies is also provided at root-level and a conda environment can be created by doing:
```bash
wget https://raw.githubusercontent.com/CMIP-Data-Request/CMIP7_DReq_Software/refs/heads/main/env.yml
conda env create -n my_dreq_env --file env.yml
```
At this stage, `my_dreq_env` conda environment contains all expected dependencies and to install the *"CMIP7 DReq Software"* package simply do:
```bash
conda activate my_dreq_env
python -m pip install --upgrade pip
python -m pip install CMIP7-data-request-api
```
:white_check_mark: If installation is ***successful*** you should be able to run the command:
```bash
export_dreq_lists_json --all_opportunities v1.2.2.3 amip.json --experiments amip
```
:x: If something went wrong, the package can be ***uninstalled*** using:
```bash
python -m pip uninstall CMIP7_data_request_api
```
:bell:To ***update*** a previousely installed version of the package:
```bash
python -m pip install --upgrade CMIP7_data_request_api
```
:bulb: And finally, if you want to run the [notebooks](#notebooks) in your enviromement (venv or conda), do not forget to install an ipykernel:
```bash
pip install jupyter
pip install ipykernel
python -m ipykernel install --user --name my_dreq_kernel
```
where `my_dreq_kernel` is the name of the kernel you want to appear in your `jupyter-notebook` interface.

### Install in Developer mode

To install the *CMIP7 DReq Software*  for development purposes, first clone the source repository:
```bash
git clone git@github.com:CMIP-Data-Request/CMIP7_DReq_Software.git
cd CMIP7_DReq_Software
```
Once an environment is created with the required dependencies (as in [user-mode install](#install-in-user-mode) above), this environement activated, go at the root-level directory of the repository and run: 
```bash
python -m pip install -e .
```

## Configuration

The package comes with a *default configuration*. After installation, you can ***initialize the configuration*** file with the default settings by running:
```bash
CMIP7_data_request_api_config init
```
This will create the `.CMIP7_data_request_api_config` file in your home directory.
Optionally, the default location of this file can be changed by setting the  `CMIP7_DR_API_CONFIGFILE` environment variable.

:bulb:**Note:** *Initializing the configuration file is optional, because the file will be automatically created the first time you use the software.*

The ***configuration file*** is a YAML file containing `key: value` pairs that
control the behavior of the software. 
You can modify the values by either editing the file directly or using the following command:
```bash
CMIP7_data_request_api_config <key> <value>
```
To reset the configuration to its default values, run:
```bash
CMIP7_data_request_api_config reset
```
For example, to set the software to run ***offline*** (i.e. without internet connection):
```bash
CMIP7_data_request_api_config offline true
```
This will prevent checks for updates and retrievals of new versions of the data request content.

## Quick Start

### Command-Line Utilities

A set of CLI utilities are available on pip install:
1. [`CMIP7_data_request_api_config`](data_request_api/data_request_api/command_line/config.py) to interact with config file, as [described above](#configuration)
2. [`export_dreq_lists_json.py`](data_request_api/data_request_api/command_line/export_dreq_lists_json.py) to get lists of requested variables
3. [`get_variables_metadata.py`](data_request_api/data_request_api/command_line/get_variables_metadata.py) to access variable names & definitions
4. [`compare_variables.py`](data_request_api/data_request_api/command_line/compare_variables.py) to track changes in variable definitions and attributes
5. [`estimate_dreq_volume.py`](data_request_api/data_request_api/command_line/estimate_dreq_volume.py) which is a configurable data volume estimator


**1. CMIP7_data_request_api_config**

This is for configuring of the CLI, which has already been presented in the [configuration section](#configuration). Here we provide some additional details like the complete list of config parameters. 

First time it is called, it generates a default configuration file in your HOME directory.

`CMIP7_data_request_api_config`

<details>
<summary>Click here to see the content of the default configuration file generated.</summary>

```
cache_dir: <YOUR-HOME-DIR>/.CMIP7_data_request_api_cache
check_api_version: true
consolidate: false
export: release
log_file: default
log_level: info
offline: false
variable_name: CMIP7 Compound Name
```
</details>
<br>

The configuration file can be edited manually or via the config utility, passing a (key, value) pair for each config parameter, for example:

`CMIP7_data_request_api_config offline true`

<details>
<summary>Click here to show all the available options.</summary>

```
 $ --> CMIP7_data_request_api_config -h

usage: CMIP7_data_request_api_config <arguments>

Config CLI

positional arguments:
  command

options:
  -h, --help  show this help message and exit

Arguments:
  init (or no arguments): Initialize the config file,
      i.e. create a config file with default values if it does not exist.
  list: List all keys in the config file.
  reset: Reset the config file to default values.
  <key> <value>: Update a specific key in the config file.
  help: print this help message.
```
</details>
<br>

<details>
<summary>Click here to show all the configuration parameters.</summary>

* `cache_dir` is the repository where the config file is stored
* `check_api_version` ('true' or 'false') checks if a newer version is available with pypi and raises a warning in case the installed version is not the latest one
* `consolidate` ('true' or 'false') to apply the consolidation on the _raw json-export_ of the DR * content (air tables) 
* `export` ('raw' or 'release') to use the _raw_ or _release json-export_ of the DR content (air tables) 
* `log_file` ('default' or prefered file path) to customize (or not) the log file
* `log_level` ('debug' or 'info') to set the verbosity level in CLI log files
* `offline` ('true' or 'false') set to 'true' to prevent checks for updates and retrievals of new versions of the data request content
* `variable_name` ('CMIP7 Compound Name' or 'CMIP6 Compound Name'), the  label used to uniquely identify the variables 

</details>
<br>

**2. export_dreq_lists_json**

A json file is generated, listing the variables requested by the CMIP7 DR for the selected criteria. The list of variables is sorted per experiment (if several requested) and per priority (Core, High, Medium and Low). Variables are identified by default with their _CMIP7 compound names_.

:bulb: By changing the configuration parameter `variable_name`, variables in the output file can instead be identified by their _CMIP6 compound names_, or any other unique identifier present in the variables' metadata (e.g., `uid`).

Call example:
<br>
`export_dreq_lists_json --all_opportunities v1.2.2.3 amip_all_Opps_v1.2.2.3.json --experiments amip`
<details>
<summary>Click here for a snapview of the output json file.</summary>

```
    "experiment": {
        "amip": {
            "Core": [
                "atmos.areacella.ti-u-hxy-u.fx.glb",
                "atmos.cl.tavg-al-hxy-u.mon.glb",
                "atmos.cli.tavg-al-hxy-u.mon.glb",
                "atmos.clivi.tavg-u-hxy-u.mon.glb",
                "atmos.clt.tavg-u-hxy-u.day.glb",
                "atmos.clt.tavg-u-hxy-u.mon.glb",
                "atmos.clw.tavg-al-hxy-u.mon.glb",
                "atmos.clwvi.tavg-u-hxy-u.mon.glb",
                "atmos.evspsbl.tavg-u-hxy-u.mon.glb",
                "atmos.hfls.tavg-u-hxy-u.mon.glb",
                "atmos.hfss.tavg-u-hxy-u.mon.glb",
                "atmos.hur.tavg-p19-hxy-air.mon.glb",
```
</details>
<br>

<details>
<summary>Click here to show all the available options.</summary>

```
$--> export_dreq_lists_json -h

usage: export_dreq_lists_json [-h] [-a] [-f OPPORTUNITIES_FILE] [-i OPPORTUNITY_IDS] [-e EXPERIMENTS] [-p {core,high,medium,low}] [-m VARIABLES_METADATA]
                              {v1.2.2.3,v1.2.2.2,v1.2.2.1,v1.2.2,v1.2.1,v1.2,v1.1,v1.0,v1.0beta,v1.0alpha,dev} output_file

Get lists of requested variables by experiment, and write them to a json file.

positional arguments:
  {v1.2.2.3,v1.2.2.2,v1.2.2.1,v1.2.2,v1.2.1,v1.2,v1.1,v1.0,v1.0beta,v1.0alpha,dev}
                        data request version
  output_file           file to write JSON output to

options:
  -h, --help            show this help message and exit
  -a, --all_opportunities
                        respond to all opportunities
  -f, --opportunities_file OPPORTUNITIES_FILE
                        path to JSON file listing opportunities to respond to. If it doesn't exist, a template will be created
  -i, --opportunity_ids OPPORTUNITY_IDS
                        opportunity ids (integers) of opportunities to respond to, example: -i 69,22,37
  -e, --experiments EXPERIMENTS
                        limit output to the specified experiments (case sensitive), example: -e historical,piControl
  -p, --priority_cutoff {core,high,medium,low}
                        discard variables that are requested at lower priority than this cutoff priority
  -m, --variables_metadata VARIABLES_METADATA
                        output file containing metadata of requested variables, can be ".json" or ".csv" file
(cmip7_dreq_venv-user) (base) 
```
</details>
<br>

**3. get_variables_metadata**

A json file is generated, containing the metadata of variables present in the CMIP7 DR (by default all of them, or alternately only the ones matching optional filter arguments). Each single entry of the json file is the _CMIP7 compound name_ of the variable and all of the attributes associated with this varaible are given as (key,value) pairs.

:bulb: By changing the configuration parameter `variable_name`, variables in the output file can instead be identified by their _CMIP6 compound names_.

Call example:
<br>
`get_variables_metadata v1.2.2.3 all_variables_metadata_v1.2.2.3.json`
<details>
<summary>Click here for a snapview of the output json file.</summary>

```json
{
  "Header": {
    "Description": "Metadata attributes that characterize CMOR variables. Each variable is uniquely idenfied by a compound name comprised of a CMIP6-era table name and a short variable name.",
    "no. of variables": 1974,
    "dreq content version": "v1.2.2.3",
    "dreq content file": "dreq_release_export.json",
    "dreq content sha256 hash": "61741fa99e2f8ca1744688e9d84f2adafd2e5204a80f92c0a5b903778fdcb732",
    "dreq api version": "1.4"
  },
  "Compound Name": {
    "aerosol.abs550aer.tavg-u-hxy-u.mon.glb": {
      "frequency": "mon",
      "modeling_realm": "aerosol",
      "standard_name": "atmosphere_absorption_optical_thickness_due_to_ambient_aerosol_particles",
      "units": "1",
      "cell_methods": "area: time: mean",
      "cell_measures": "area: areacella",
      "long_name": "Ambient Aerosol Absorption Optical Thickness at 550nm",
      "comment": "Optical thickness of atmospheric aerosols at wavelength 550 nanometers.",
      "processing_note": "",
      "dimensions": "longitude latitude time lambda550nm",
      "out_name": "abs550aer",
      "type": "real",
      "positive": "",
      "spatial_shape": "XY-na",
      "temporal_shape": "time-intv",
      "cmip6_table": "AERmon",
      "physical_parameter_name": "abs550aer",
      "variableRootDD": "abs550aer",
      "branding_label": "tavg-u-hxy-u",
      "branded_variable_name": "abs550aer_tavg-u-hxy-u",
      "region": "glb",
      "cmip6_compound_name": "AERmon.abs550aer",
      "cmip7_compound_name": "aerosol.abs550aer.tavg-u-hxy-u.mon.glb",
      "uid": "19bebf2a-81b1-11e6-92de-ac72891c3257"
    },
```
</details>
<br>

<details>
<summary>Click here to show all the available options.</summary>

```
$--> get_variables_metadata -h

usage: get_variables_metadata [-h] [-cn COMPOUND_NAMES] [-t CMOR_TABLES] [-v CMOR_VARIABLES]
                              {v1.2.2.3,v1.2.2.2,v1.2.2.1,v1.2.2,v1.2.1,v1.2,v1.1,v1.0,v1.0beta,v1.0alpha,dev} outfile

Get metadata of CMOR variables (e.g., cell_methods, dimensions, ...) and write it to a json file.

positional arguments:
  {v1.2.2.3,v1.2.2.2,v1.2.2.1,v1.2.2,v1.2.1,v1.2,v1.1,v1.0,v1.0beta,v1.0alpha,dev}
                        data request version
  outfile               output file containing metadata of requested variables, can be ".json" or ".csv" file

options:
  -h, --help            show this help message and exit
  -cn, --compound_names COMPOUND_NAMES
                        include only variables with the specified compound names, example: -cn Amon.tas,Omon.sos
  -t, --cmor_tables CMOR_TABLES
                        include only the specified CMOR tables, example: -t Amon,Omon
  -v, --cmor_variables CMOR_VARIABLES
                        include only the specified CMOR variable short names, example: -v tas,siconc
```
</details>
<br>

:bulb: The [CMIP7 CMOR tables](https://github.com/WCRP-CMIP/cmip7-cmor-tables) have been generated from the variables metadata in the DR. `get_variables_metadata` provides another way to view the variables metadata in the DR.

**4. compare_variables**

Useful for viewing the changes in variable metadata between two CMIP7 DR versions or between CMIP7 and CMIP6. If comparing to CMIP6, the CMIP6 CMOR tables will be loaded and a `cmip6.json` file created with the expected format to enable the comparison. There are 3 output files: one listing the missing variables and two files listing the differences (one sorted per variable, the other sorted per attribute). As above, variables are identified with their _CMIP7 compound names_.
<br>

Call example:
<br>
`compare_variables all_variables_metadata_v1.2.2.3.json cmip6`
<details>
<summary>Click here to see the CLI log.</summary>

```
Wrote cmip6.json
Loaded all_variables_metadata_v1.2.2.3.json
Loaded cmip6.json
Total number of variables with differences: 0
Wrote missing_variables.json
Wrote diffs_by_variable.json
Wrote diffs_by_attribute.json
```
</details>
<br>

<details>
<summary>Click here to see all the available options.</summary>

```
$--> compare_variables -h

usage: compare_variables [-h] [-c CONFIG_ATTRIBUTES] compare compare

Compare variables metadata between data request versions

positional arguments:
  compare               versions of variables to compare: json file or cmor tables

options:
  -h, --help            show this help message and exit
  -c, --config_attributes CONFIG_ATTRIBUTES
                        yaml file specifying metadata attributes to compare (will be created if it doesn't exist)
```
</details>
<br>

**5. estimate_dreq_volume**

Provides an estimate of the data volumes. It takes as input a yaml file where the model-grid size parameters are to be set. Please note that theses these estimates are provisional and must be used with caution. The output file is a json file where data volumes are given per experiment and grouped by variable priority (Core, High, Medium, Low).
<br>

To first create the yaml file, just call the utility with a DR version specified:
`estimate_dreq_volume v1.2.2.3`

A default  config file `size.yaml`is created. 
<details>
<summary>Click here to see the content of the default config file.</summary>

```
# Data sizes config file for estimate_volume.py

# Model-specific dimension sizes (edit as needed)
dimensions:
  alevel: 80
  alevhalf: 80
  gridlatitude: 100
  latitude: 180
  longitude: 360
  olevel: 80
  olevhalf: 80
  rho: 80
  sdepth: 20
  soilpools: 5
  spectband: 10

# Number of bytes per floating point number
bytes_per_float: 4

# Scaling factor (e.g., adjust to account for netcdf compression)
scale_file_size: 1

# No. of years to use if showing size of single variables (-vso option)
years: 1
```
</details>
<br>

After editing `size.yaml` with your model-specific settings, rerun the command.
<br>

<details>
<summary>Click here for a snapview of the outut json file.</summary>

```
```
</details>
<br>

<details>
<summary>Click here to see all the available options.</summary>

```
 $ --> estimate_dreq_volume -h

usage: estimate_dreq_volume [-h] [-o OUTFILE] [-c CONFIG_SIZE] [-v VARIABLES] [-e EXPERIMENTS] [-vso] request

Estimate volume of requested model output

positional arguments:
  request               json file specifying variables requested by experiment (output from export_dreq_lists_json, which specifies the data request version) OR
                        can be a data request version (e.g. "v1.2")

options:
  -h, --help            show this help message and exit
  -o, --outfile OUTFILE
                        name of output file, default: volume_estimate_{data request version}.json
  -c, --config-size CONFIG_SIZE
                        config file (yaml) giving size parameters to use in the volume estimate
  -v, --variables VARIABLES
                        include only the specified variables in the estimate, example: -v Amon.tas,Omon.tos
  -e, --experiments EXPERIMENTS
                        include only the specified experiments in the estimate, example: -e historical,piControl
  -vso, --variable-size-only
                        show ONLY the sizes of individual variables (ignores experiments)
```
</details>
<br>

### Notebooks

Notebooks are intended as a how-to guidelines for:
* loading the data request: ["HowTo-01"](notebooks/HowTo-01_Import_and_Load_the_DR.ipynb)
* discovering the data request: ["HowTo-02"](notebooks/HowTo-02_Discover_What_is_in_DR.ipynb)
* searching for experiments or variables: ["HowTo-03a"](notebooks/HowTo-03a_Find_Experiments_and_Variables_for_given_Opportunities.ipynb), ["HowTo-03b"](notebooks/HowTo-03b_Find_Experiments_and_Variables_for_given_Opportunities.ipynb)
* viewing attributes of experiments and variables: ["HowTo-04a"](notebooks/HowTo-04a_View_Attributes_of_Experiments_and_Variables.ipynb), ["HowTo-04b"](notebooks/HowTo-04a_View_Attributes_of_Experiments_and_Variables.ipynb)
* applying various search filters: ["HowTo-05"](notebooks/HowTo-05_Apply_Various_Search_Critria.ipynb)

### Python Scripts

Python scripts objective is to illustrate some use-case workflows.

:construction: *This section is under construction.* 

## Documentation

### General Documentation

:construction: *This section is under construction.* 


### Technical Documentation 

Auto-generated code documentation can be [found here](https://cmip-data-request.github.io/CMIP7_DReq_Software/data_request_api/).

## Contact

The CMIP7 Data Request Task Team encourages user feedback to help us improve the software.
Here are some ways to provide feedback:
- For *specific questions or issues* (such as bugs) please [open a github issue](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/issues).
- For *more general questions or concerns*, such as suggestions for new features, contribute to the Software's [github discussion forum](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/discussions).

## Contributors

[![Contributors](https://contrib.rocks/image?repo=CMIP-Data-Request/CMIP7_DReq_Software)](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/graphs/contributors/)
*Thanks to our contributors!*
