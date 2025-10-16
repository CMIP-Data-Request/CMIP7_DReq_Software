## Scripts used to generate branded variables from DR content

This folder stores scripts that were used to generate branded variable names using the [CMIP branded variable mapper](https://github.com/znicholls/CMIP-branded-variable-mapper).
They are included here mainly for completeness and documentation.
Most users probably won't ever need to run them.
That said, they might be useful for generating branded names if/when new variables are added to the DR, or for future data requests by CMIP or community MIPs.
If the branding algorithm is updated, they could be useful for regenerating branded names.

### Usage examples

To generate branded names, using as input the variables metadata json file for DR v1.2.2.2 produced by the `get_variables_metadata` command-line tool:
```bash
./generate_branded_names.py ../examples/variables_v1.2.2.2_cmip6names.json vars.json
```
The output file `vars.json` will be identical to the input file except that its branded names will be updated.
If the branding algorithm has not been changed since the input file was generated, the input and output files should be identical.

To check that DR variables sharing the same branded variable names have identical metadata:
```bash
./compare_branded_variables.py ../examples/variables_v1.2.2.2_cmip6names.json out.json
```
The output file `out.json` has a summary of any differences found.
The input file is not changed in any way.
The metadata parameters that are checked are set in `branded_variable_attributes.yaml`.
For example:
```yaml
compare_attributes:
- comment
- long_name
- cell_methods
```
will compare DR variables for only these metadata attributes, ignoring all others.

