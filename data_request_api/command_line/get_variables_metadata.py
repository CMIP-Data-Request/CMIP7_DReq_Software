#!/usr/bin/env python
'''
Extract metadata of CMOR variables and write them to a json file.
Example output file: scripts/variable_info/all_var_info.json
Output file names (filepath) are set below.
'''

import argparse

import data_request_api.stable.content.dreq_content as dc
import data_request_api.stable.query.dreq_query as dq
from data_request_api import version as api_version


def parse_args():
    '''
    Parse command-line arguments
    '''

    parser = argparse.ArgumentParser(
        description='Get CMOR variables metadata and write to json.'
        )
    parser.add_argument('dreq_version', choices=dc.get_versions(),
                        help='data request version')
    def _var_metadata_check(arg):
        if arg.endswith('.json') or arg.endswith('.csv'):
            return arg
        else:
            raise ValueError()
    parser.register('type', 'json_or_csv_file', _var_metadata_check)
    required_named_args = parser.add_argument_group('required named arguments')
    required_named_args.add_argument('-o', '--outfile', nargs='+', type='json_or_csv_file', required=True,
                        help='output files containing variable metadata of requested variables, files with ".json" or ".csv" will be produced')
    parser.add_argument('-cn', '--compound_names', nargs='+', type=str,
                        help='include only variables with the specified Compound Names (examples: "Amon.tas", "Omon.sos")')
    parser.add_argument('-t', '--cmor_tables', nargs='+', type=str,
                        help='include only the specified CMOR tables (aka MIP tables, examples: "Amon", "Omon")')
    parser.add_argument('-v', '--cmor_variables', nargs='+', type=str,
                        help='include only the specified CMOR variables (out_name, examples: "tas", "siconc")')
    return parser.parse_args()


def main():

    args = parse_args()

    # Load data request content
    use_dreq_version = args.dreq_version
    dc.retrieve(use_dreq_version)  
    content = dc.load(use_dreq_version)

    # Get metadata for variables
    dq.DREQ_VERSION = use_dreq_version
    all_var_info = dq.get_variables_metadata(
        content,
        compound_names=args.compound_names,
        cmor_tables=args.cmor_tables,
        cmor_variables=args.cmor_variables,
        use_dreq_version=use_dreq_version  # TO DEPRECATE
        )

    # Write output file(s)
    for filepath in args.outfile:
        dq.write_variables_metadata(
            all_var_info,
            filepath,
            api_version=api_version,
            use_dreq_version=use_dreq_version,
            content_path = dc._dreq_content_loaded['json_path']
            )


if __name__ == '__main__':
    main()
