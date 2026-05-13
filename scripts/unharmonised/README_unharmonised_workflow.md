
## MIP workflow for Unharmonised Data Request

⚠️ *Everything in this document is a proposal, under development, and likely to change*

### Opportunity template

This allows MIPs to create a `json` file representation of a DR "Opportunity" with minimal effort. 

A DR Opportunity lists variables that are requested from a specified set of experiments.
It includes a description of the scienfitic purpose of the request.
This can be very brief, but including detailed information is also possible.
A template Opportunity is provided in `yaml` format, which a MIP can edit.

First, copy the template:
```bash
cp DR_Opportunity_template.yaml new_MIP_data_request.yaml
```
Edit the new file, which in this example is named  `new_MIP_data_request.yaml`, to specify the requested variables and experiments from which they're requested.
Variables are grouped into Variable Groups, which have a priority level (High, Medium, Low) attached.
Experiments are grouped into Experiment Groups.
If a MIP simply has one list of variables that are all requested from the same list of experiments, then one Variable Group and one Experiment Group is sufficient.

Then validate the new request against existing DR content:
```bash
./ingest.py new_MIP_data_request.yaml new_MIP_data_request.json v1.2.2.3
```
This should be run in an env where the DR python API is installed ([see here](https://github.com/CMIP-Data-Request/CMIP7_DReq_Software#installation) for installation guidance).
This performs some sanity checks, including checking that variable and experiment names are valid (i.e., they are defined in existing DR content and CMIP7 CVs).
If the checks pass, the output file, which here is `new_MIP_data_request.json`, represents in the new request's information in a format that can be used in the DR python API.
