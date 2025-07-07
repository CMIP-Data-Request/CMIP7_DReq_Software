#!/usr/bin/env python
'''
Extract metadata of CMOR variables and write them to a json file.
'''

import argparse
import os

import data_request_api.content.dreq_content as dc
import data_request_api.query.dreq_query as dq
from data_request_api import version as api_version


def parse_args():
    '''
    Parse command-line arguments
    '''

    parser = argparse.ArgumentParser(
        description='Get metadata of CMOR variables (e.g., cell_methods, dimensions, ...) and write it to a json file.'
    )
    
    # Positional (mandatory) input arguments
    parser.add_argument('dreq_version', choices=dc.get_versions(),
                        help='data request version')
    parser.add_argument('outfile', type=str,
                        help='output file containing metadata of requested variables, can be ".json" or ".csv" file')

    # Optional input arguments
    parser.add_argument('-cn', '--compound_names', nargs='+', type=str,
                        help='include only variables with the specified Compound Names (examples: "Amon.tas", "Omon.sos")')
    parser.add_argument('-t', '--cmor_tables', nargs='+', type=str,
                        help='include only the specified CMOR tables (aka MIP tables, examples: "Amon", "Omon")')
    parser.add_argument('-v', '--cmor_variables', nargs='+', type=str,
                        help='include only the specified CMOR variables (out_name, examples: "tas", "siconc")')
    
    return parser.parse_args()


def main():

    args = parse_args()

    # Check validity of requested output file type.
    # This should conform to what dq.write_variables_metadata() expects, which throws an error if file type is wrong.
    # Checking this here is redundant, but useful to catch input error before spending time retrieving the metadata.
    filepath = args.outfile
    ext = os.path.splitext(filepath)[-1]
    valid_ext = ['.json', '.csv']
    if ext not in valid_ext:
        raise ValueError(f'{ext} file extension is not supported, valid types are: {", ".join(valid_ext)}')

    # Load data request content
    use_dreq_version = args.dreq_version
    dc.retrieve(use_dreq_version)
    content = dc.load(use_dreq_version)

    # Get metadata for variables
    all_var_info = dq.get_variables_metadata(
        content,
        use_dreq_version,
        compound_names=args.compound_names,
        cmor_tables=args.cmor_tables,
        cmor_variables=args.cmor_variables,
    )

    # Write output file
    dq.write_variables_metadata(
        all_var_info,
        use_dreq_version,
        filepath,
        api_version=api_version,
        content_path=dc._dreq_content_loaded['json_path']
    )


if __name__ == '__main__':
    main()
