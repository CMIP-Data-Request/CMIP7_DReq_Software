
## MIP workflow for Unharmonised Data Request

⚠️ *Everything in this document is a proposal, under development, and likely to change*

### Opportunity template

Example usage of the validation script:
```bash
cp Opportunity/TEMPLATE_Opportunity.yaml Opportunity/my_new_opportunity.yaml
[edit my_new_opportunity.yaml as needed]
./ingest.py Opportunity/my_new_opportunity.yaml out.json v1.2.2.5
```
Usage info: `./ingest.py -h`

### Lists of DR variables

Example of creating a customized csv or json file listing variable names and metadata:
```bash
get_variables_metadata -r atmos -a branded_variable_name,long_name,standard_name,frequency,modeling_realm,region,dimension
s,cell_methods v1.2.2.5 vars.json
```
Changing the output file from `vars.json` to `vars.csv` will produce a csv file (spreadsheet) with the same info.
Here the `-r` option is used to restrict to variables whose realm list includes `atmos`. 
The `-a` option can be used to restrict the metadata attributes included.
Another example:
```bash
get_variables_metadata v1.2.2.5 vars.csv
```
writes a csv file listing all variables from the Harmonised DR (at version v1.2.2.5).
