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
6. [Examples](#examples)
7. [Documentation](#documentation) 
8. [Glossary](#glossary)
9. [Contributors](#contributors) 
10. [Contact](#contact)  

## Purpose

**The CMIP7 DReq Software**  is a Python software designed to interact with the [CMIP7 Data Request](https://wcrp-cmip.org/cmip7/cmip7-data-request/). It provides an API to *query* and *utilize* the information in the Data Request, including [command-line (CLI) utilities](#command-line-utilities), [example scripts](#python-scripts) and [notebooks](#notebooks) showing how to use the API. 
The main purpose of the CMIP7 DReq API is to extract the requested variables (along with their attributes) according to filters the user activates (a set of CMIP7 Experiments, and/or Opportunities, and/or Frequencies, etc.). It can either generates the resulting list in various formats (xls, csv, json) or return them as python objets that make the API *plugable* in Modelling Centres' data production workflows. 

:coffee: ==add James' 3 blue-green boxes schema there==

**Target audience:**  
- *Modellers* configuring the climate models running CMIP7 simulations
- *Software engineers* preparing CMIP7 modelling workflows
- *Data providers* preparing CMIP7 output

**Focus: practical usage:** exploring the CMIP7 DR content - apply various filters - get the results in different formats.

## Release Versions

The latest **official release** of the CMIP7 Data Request is `v1.2.2` (25 July 2025).
[Learn more about this release on the CMIP website](https://wcrp-cmip.org/cmip7-data-request-v1-2-2/).

:warning: **Note:** *The CMIP7 DReq Software versions are not aligned with the CMIP7 Data Request ones. So please, do not infer that v1.2.2 of the CMIP7 DReq Software "works with" or "reflects"  v1.2.2 of the CMIP7 Data Request, it is not the case!*

## Try It Without Installation

You can launch and interact with this repository  via [Binder](https://mybinder.org/) or [Google Colab](https://colab.research.google.com/). To do so, just click on one of the badges to run it in your browser:

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/CMIP-Data-Request/CMIP7_DReq_Software/main?filepath=notebooks)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/CMIP-Data-Request/CMIP7_DReq_Software/)
:bulb: This enables you, *without installing anything*, to play with the [notebooks](#notebooks), in a live environment that is your own playground.

## Installation

### Install in User mode

In a python <u>**virtual environment**</u> or conda environment in which you want to install the package, do:
```
pip install CMIP7-data-request-api
```
If an environment first needs to be created, you can do:

```
python -m venv my_dreq_env
source my_dreq_env/bin/activate
pip install --upgrade pip
pip install CMIP7-data-request-api
```
with  `my_dreq_env` being the environment name that can be changed to whatever preferred name.

This will automatically install the dependencies, but if necessary  they can be manually installed by doing:
```
wget https://raw.githubusercontent.com/CMIP-Data-Request/CMIP7_DReq_Software/refs/heads/main/requirements.txt
pip install -r requirements.txt 
```
where the [`requirements.txt`](requirements.txt) file is the one present at the root-level  of this repository, which lists the package dependencies.

If a <u>**conda environment**</u> is preferred instead of `venv`, an [`env.yml`](env.yml) file with the dependencies is also provided at root-level and a conda environment can be created by doing:
```
wget https://raw.githubusercontent.com/CMIP-Data-Request/CMIP7_DReq_Software/refs/heads/main/env.yml
conda env create -n my_dreq_env --file env.yml
```
:white_check_mark: If installation is ***successful*** you should be able to run the command:
```
export_dreq_lists_json --all_opportunities v1.2.1 amip.json --experiments amip
```
:x: If something went wrong, the package can be ***uninstalled*** using:
```
python -m pip uninstall CMIP7_data_request_api
```

### Install in Developpement mode

To install for development purpose:
```
git clone git@github.com:CMIP-Data-Request/CMIP7_DReq_Software.git
cd CMIP7_DReq_Software
```
If needed, create an environment with the required dependencies (as in [user-mode install](#install-in-user-mode) above).
Then, in the root-level directory of the repository, run: 
```
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
```
CMIP7_data_request_api_config <key> <value>
```
To reset the configuration to its default values, run:
```
CMIP7_data_request_api_config reset
```
For example, to set the software to run ***offline*** (i.e. without internet connection):
```
CMIP7_data_request_api_config offline true
```
This will prevent checks for updates and retrievals of new versions of the data request content.

## Quick Start

### Command-Line Utilities

A set of CLI utilities are available on pip install:
* [`CMIP7_data_request_api_config`]() to interact with config file
* [`export_dreq_lists_json.py`](data_request_api/data_request_api/command_line/export_dreq_lists_json.py) to get lists of requested variables
* [`estimate_dreq_volume.py`](data_request_api/data_request_api/command_line/estimate_dreq_volume.py) which is a configurable data volume estimator
* [`get_variables_metadata.py`](data_request_api/data_request_api/command_line/get_variables_metadata.py) to access variable names & definitions
* [`compare_variables.py`](data_request_api/data_request_api/command_line/compare_variables.py) to track changes in variable definitions and attributes

:coffee: ==add CLI usage examples here + link missing for 1st CLI==

### Notebooks

Notebooks are intended as a how-to guides for:
* loading the data request
* searching for experiments or variables
* viewing attributes of experiments and variables
* applying various search filters

:coffee: ==add notebooks names and links==

### Python Scripts

Python scripts objective is to illustrate some use-case workflows.

:coffee: ==add script list here==

## Documentation

### General Documentation

:construction: *Our appologies, This section is under construction. The current README is the best we have so far...*

### Technical Documentation 

Auto-generated code documentation can be found here:  https://cmip-data-request.github.io/CMIP7_DReq_Software/data_request_api/

## Contact

The CMIP7 Data Request Task Team encourages user feedback to help us improve the software.
Here are some ways to provide feedback:
- For *specific questions or issues* (such as bugs) please [open a github issue](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/issues).
- For *more general questions or concerns*, such as suggestions for new features, contribute to the Software's [github discussion forum](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/discussions).

## Contributors

[![Contributors](https://contrib.rocks/image?repo=CMIP-Data-Request/CMIP7_DReq_Software)](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/graphs/contributors/)
*Thanks to our contributors!*