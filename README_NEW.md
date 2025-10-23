[![pypi](https://img.shields.io/pypi/v/CMIP7-data-request-api.svg)](https://pypi.python.org/pypi/CMIP7-data-request-api)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/CMIP-Data-Request/CMIP7_DReq_Software/main?filepath=notebooks)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/CMIP-Data-Request/CMIP7_DReq_Software/)
[![NBviewer](https://raw.githubusercontent.com/jupyter/design/master/logos/Badges/nbviewer_badge.svg)](https://nbviewer.jupyter.org/github/CMIP-Data-Request/CMIP7_DReq_Software/tree/main/notebooks/)
[![license](https://img.shields.io/github/license/CMIP-Data-Request/CMIP7_DReq_Software.svg)](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/blob/main/LICENSE)
[![status](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)

# CMIP7 Data Request Software (CMIP7 DReq Software) – Quick User Guide

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

**The CMIP7 DReq Software**  is a Python software designed to interact with the [CMIP7 Data Request](https://wcrp-cmip.org/cmip7/cmip7-data-request/) (this latter is also qualified as "Data Request ***Content***" in order to distinguish from the current "Data Request ***Software***", see the schema bellow to see the pathway between the two). It provides an API to *query* and *utilize* the information in the Data Request, including [command-line (CLI) utilities](#command-line-utilities), [example scripts](#python-scripts) and [notebooks](#notebooks) showing how to use the API. 
The main purpose of the CMIP7 DReq API is to extract the requested variables (along with their attributes) according to filters the user activates (a set of CMIP7 Experiments, and/or Opportunities, and/or Frequencies, etc.). It can either generates the resulting list in various formats (xls, csv, json) or return them as python objets that make the API *plugable* in Modelling Centres' data production workflows. 

<img width=750px src=./docs/static/3boxes_schema.png>

**Target audience:**  
- *Modellers* configuring the climate models running CMIP7 simulations
- *Software engineers* preparing CMIP7 modelling workflows
- *Data providers* preparing CMIP7 output

**Focus: practical usage:** exploring the CMIP7 DR content - apply various filters - get the results in different formats.

## Release Versions

The latest **official release** of the CMIP7 Data Request is `v1.2.2.2` (30 September 2025).
[Learn more about this release on the CMIP website](https://wcrp-cmip.org/cmip7-data-request-v1-2-2/).

:warning: **Note:** *The CMIP7 DReq Software versions are not aligned with the CMIP7 Data Request ones. So please, do not infer that v1.2.2 of the CMIP7 DReq Software "works with" or "reflects"  v1.2.2 of the CMIP7 Data Request, it is not the case!*

## Try It Without Installation

You can launch and interact with this repository  via [Binder](https://mybinder.org/) or [Google Colab](https://colab.research.google.com/). To do so, just click on one of the badges to run it in your browser:

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/CMIP-Data-Request/CMIP7_DReq_Software/main?filepath=notebooks)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/CMIP-Data-Request/CMIP7_DReq_Software/)
:bulb: This enables you, *without installing anything*, to play with the [notebooks](#notebooks), in a live environment that is your own playground.

## Installation

### Install in User mode

Here is decribed the install of the *CMIP7 DReq Software* python package via `pip` for a simple user-mode usage.

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
export_dreq_lists_json --all_opportunities v1.2.2 amip.json --experiments amip
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
python -m ipykernel install --user --name my_dreq_kernel
```
where `my_dreq_kernel` is the name of the kernel you want to appear in your `jupyter-notebook` interface.

### Install in Developpement mode

To install the *CMIP7 DReq Software*  for development purpose, first clone the source repository:
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

:bulb:**Note:** *This initialization of the configuration step is optionnal, because in any case, the file will be automatically created the first time you use the software.*

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
1. [`CMIP7_data_request_api_config`]() to interact with config file
2. [`export_dreq_lists_json.py`](data_request_api/data_request_api/command_line/export_dreq_lists_json.py) to get lists of requested variables
3. [`get_variables_metadata.py`](data_request_api/data_request_api/command_line/get_variables_metadata.py) to access variable names & definitions
4. [`compare_variables.py`](data_request_api/data_request_api/command_line/compare_variables.py) to track changes in variable definitions and attributes
5. [`estimate_dreq_volume.py`](data_request_api/data_request_api/command_line/estimate_dreq_volume.py) which is a configurable data volume estimator

:coffee: ==TODO: link for CLI 1 is missing==

Here are some CLI calling examples: 

**1. CMIP7_data_request_api_config**

This command line blabla...
:coffee: ==TODO: complete this CLI quick-guide==

Call example:
`the-command-line`
<details>
<summary>Click here to expand.</summary>

```
```
</details>
<br>

Additionnal filter options are available: 
<details>
<summary>Click here to expand.</summary>

```
```
</details>
<br>

**2. export_dreq_lists_json**

A json file is generated, listing the variables requested by the CMIP7 DR for the selected criteria.

Call example:
`export_dreq_lists_json --all_opportunities v1.2.2.2 amip_all_Opps_v1.2.2.2.json --experiments amip`
<details>
<summary>Click here to expand.</summary>

```
```
</details>
<br>

Additionnal filter options are available: 
<details>
<summary>Click here to expand.</summary>

```
export_dreq_lists_json -h
usage: export_dreq_lists_json [-h] [-a] [-f OPPORTUNITIES_FILE] [-i OPPORTUNITY_IDS] [-e EXPERIMENTS] [-p {core,high,medium,low}] [-m VARIABLES_METADATA]
                              {v1.2.2.2,v1.2.2.1,v1.2.2,v1.2.1,v1.2,v1.1,v1.0,v1.0beta,v1.0alpha,dev} output_file

Get lists of requested variables by experiment, and write them to a json file.

positional arguments:
  {v1.2.2.2,v1.2.2.1,v1.2.2,v1.2.1,v1.2,v1.1,v1.0,v1.0beta,v1.0alpha,dev}
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

A json file is generated, containing the variables  present in the CMIP7 DR (all or only the ones matching filter options, see below). Each single entry of the json file is the CMIP7 compound name of the variable and all of the attributes associated with this varaible are given as (key,value) pairs.

Call example:
`get_variables_metadata v1.2.2.2 all_variables_metadata_v1.2.2.2.json`
<details>
<summary>Click here to expand.</summary>

```
    {
    "Header": {
        "Description": "Metadata attributes that characterize CMOR variables. Each variable is uniquely idenfied by a compound name comprised of a CMIP6-era table name and a short variable name.",
        "no. of variables": 1974,
        "dreq content version": "v1.2.2.2",
        "dreq content file": "dreq_release_export.json",
        "dreq content sha256 hash": "d396e3f8ef2ef1c3a184612cf50476cdda26101c734afd92f2fdfb373aceac6a",
    "Compound Name": {
        "aerosol.abs550aer.tavg-u-hxy-u.mon.GLB": {
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
            "region": "GLB",
            "cmip6_compound_name": "AERmon.abs550aer",
            "cmip7_compound_name": "aerosol.abs550aer.tavg-u-hxy-u.mon.GLB",
            "uid": "19bebf2a-81b1-11e6-92de-ac72891c3257"
        },
```
</details>
<br>

Additionnal filter options are available:
`get_variables_metadata -h`
<details>
<summary>Click here to expand.</summary>

```
usage: get_variables_metadata [-h] [-cn COMPOUND_NAMES] [-t CMOR_TABLES] [-v CMOR_VARIABLES]
                              {v1.2.2.2,v1.2.2.1,v1.2.2,v1.2.1,v1.2,v1.1,v1.0,v1.0beta,v1.0alpha,dev} outfile

Get metadata of CMOR variables (e.g., cell_methods, dimensions, ...) and write it to a json file.

positional arguments:
  {v1.2.2.2,v1.2.2.1,v1.2.2,v1.2.1,v1.2,v1.1,v1.0,v1.0beta,v1.0alpha,dev}
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

**4. compare_variables**

This command line blabla...
:coffee: ==TODO: complete this CLI quick-guide==

Call example:
`the-command-line`
<details>
<summary>Click here to expand.</summary>

```
```
</details>
<br>

Additionnal filter options are available: 
`cli-script-name -h`
<details>
<summary>Click here to expand.</summary>

```
```
</details>
<br>

**5. estimate_dreq_volume**

This command line blabla...
:coffee: ==TODO: complete this CLI quick-guide==

Call example:
`the-command-line`
<details>
<summary>Click here to expand.</summary>

```
```
</details>
<br>

Additionnal filter options are available: 
`cli-script-name -h`
<details>
<summary>Click here to expand.</summary>

```
```
</details>
<br>

### Notebooks

Notebooks are intended as a how-to guidelines for:
* loading the data request: [`HowTo-01`](notebooks/HowTo-01_Import_and_Load_the_DR.ipynb)
* discovering the data request: [`HowTo-02`](notebooks/HowTo-02_Discover_What_is_in_DR.ipynb)
* searching for experiments or variables: [`HowTo-03a`](notebooks/HowTo-03a_Find_Experiments_and_Variables_for_given_Opportunities.ipynb), [`HowTo-03b`](notebooks/HowTo-03b_Find_Experiments_and_Variables_for_given_Opportunities.ipynb)
* viewing attributes of experiments and variables: [`HowTo-04a`](notebooks/HowTo-04a_View_Attributes_of_Experiments_and_Variables.ipynb), [`HowTo-04b`](notebooks/HowTo-04a_View_Attributes_of_Experiments_and_Variables.ipynb)
* applying various search filters: [`HowTo-05`](notebooks/HowTo-05_Apply_Various_Search_Critria.ipynb)

### Python Scripts

Python scripts objective is to illustrate some use-case workflows.

:coffee: ==TODO: add the script list here + call examples==

## Documentation

### General Documentation

:construction: *This section is under construction.* 


### Technical Documentation 

Auto-generated code documentation can be found [here:](https://cmip-data-request.github.io/CMIP7_DReq_Software/data_request_api/)

## Contact

The CMIP7 Data Request Task Team encourages user feedback to help us improve the software.
Here are some ways to provide feedback:
- For *specific questions or issues* (such as bugs) please [open a github issue](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/issues).
- For *more general questions or concerns*, such as suggestions for new features, contribute to the Software's [github discussion forum](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/discussions).

## Contributors

[![Contributors](https://contrib.rocks/image?repo=CMIP-Data-Request/CMIP7_DReq_Software)](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/graphs/contributors/)
*Thanks to our contributors!*