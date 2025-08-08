[![pypi](https://img.shields.io/pypi/v/CMIP7-data-request-api.svg)](https://pypi.python.org/pypi/CMIP7-data-request-api)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/CMIP-Data-Request/CMIP7_DReq_Software/main?filepath=notebooks)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/CMIP-Data-Request/CMIP7_DReq_Software/)
[![NBviewer](https://raw.githubusercontent.com/jupyter/design/master/logos/Badges/nbviewer_badge.svg)](https://nbviewer.jupyter.org/github/CMIP-Data-Request/CMIP7_DReq_Software/tree/main/notebooks/)
[![license](https://img.shields.io/github/license/CMIP-Data-Request/CMIP7_DReq_Software.svg)](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/blob/main/LICENSE)
[![status](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)

# CMIP7 Data Request Software

Python software to interact with the [CMIP7 data request](https://wcrp-cmip.org/cmip7/cmip7-data-request/).
It provides an API to query and utilize the information in the data request, including example scripts and notebooks showing how to use the API.

Please see below for the [installation guide](#installation) or how to [try it without installation](#try-it-without-installation).

The Data Request Task Team encourages user feedback to help us improve the software.
Here are some ways to provide feedback:
- For specific questions or issues (such as bugs) please [open a github issue](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/issues).
- For more general questions or concerns, such as suggestions for new features, contribute to the Software's [github discussion forum](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/discussions).


## v1.2.2 Data Request release

The latest **official release** of the CMIP7 Data Request is `v1.2.2` (25 July 2025).
[Learn more about this release on the CMIP website](https://wcrp-cmip.org/cmip7-data-request-v1-2-2/).


## Try It Without Installation

You can launch and interact with this repository in a live environment via [Binder](https://mybinder.org/) or [Google Colab](https://colab.research.google.com/) — no installation needed, just click on one of the badges to run it in your browser:

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/CMIP-Data-Request/CMIP7_DReq_Software/main?filepath=notebooks)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/CMIP-Data-Request/CMIP7_DReq_Software/)


## Installation

### Quick Start

In a python virtual environment or conda environment in which you want to install the package, do:

```bash
pip install CMIP7-data-request-api
```

If an environment first needs to be created, you can do:

```bash
python -m venv my_dreq_env
source my_dreq_env/bin/activate
pip install --upgrade pip
pip install CMIP7-data-request-api
```

This will automatically install the dependencies, but if necessary they can be manually installed by doing:

```bash
wget https://raw.githubusercontent.com/CMIP-Data-Request/CMIP7_DReq_Software/refs/heads/main/requirements.txt
pip install -r requirements.txt 
```

using the `requirements.txt` file from the top-level directory of this repository, which lists the package dependencies, and `my_dreq_env` can be changed to whatever environment name is preferred.
If a conda environment is preferred instead of `venv`, an `env.yml` file with the dependencies is also provided and a conda environment can be created by doing:
```
wget https://raw.githubusercontent.com/CMIP-Data-Request/CMIP7_DReq_Software/refs/heads/main/env.yml
conda env create -n my_dreq_env --file env.yml
```

If installation is successful you should be able to run the command
```bash
export_dreq_lists_json --all_opportunities v1.2.1 amip.json --experiments amip
```

The package can be uninstalled using
```bash
python -m pip uninstall CMIP7_data_request_api
```

### Configuration

The package comes with a default configuration.
After installation, you can initialize the configuration file with the default settings by running:
```bash
CMIP7_data_request_api_config init
```

This will create the `.CMIP7_data_request_api_config` file in your home directory. 
Optionally, the default location of this file can be changed by setting the `CMIP7_DR_API_CONFIGFILE` environment variable.
Alternatively, the file will be automatically created the first time you use the software.

The configuration file is a YAML file containing `key: value` pairs that
control the behavior of the software.
You can modify the values by either editing the file directly or using the following command:
```bash
CMIP7_data_request_api_config <key> <value>
```

To reset the configuration to its default values, run:
```bash
CMIP7_data_request_api_config reset
```

For example, to set the software to run offline, use:
```bash
CMIP7_data_request_api_config offline true
```
This will prevent checks for updates and retrievals of new versions of the data request content.


### Development

To install for development:
```bash
git clone git@github.com:CMIP-Data-Request/CMIP7_DReq_Software.git
cd CMIP7_DReq_Software
```
If needed create an environment with the required dependencies (as in Quick Start, above).
Then, in the top-level directory of the repository, run: 
```bash
python -m pip install -e .
```


## Documentation

### Technical Documentation 
https://cmip-data-request.github.io/CMIP7_DReq_Software/data_request_api/


## Contributors

[![Contributors](https://contrib.rocks/image?repo=CMIP-Data-Request/CMIP7_DReq_Software)](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software/graphs/contributors/)

Thanks to our contributors!
