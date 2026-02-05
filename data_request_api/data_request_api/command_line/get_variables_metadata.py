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
        formatter_class=argparse.RawTextHelpFormatter,
        description='Write data request variables metadata (cell_methods, dimensions, ...) to json or csv file.'
    )

    # Positional (mandatory) input arguments
    parser.add_argument('dreq_version', choices=dc.get_versions(),
                        help='data request version')
    parser.add_argument('outfile', type=str,
                        help='output file (specify ".json" or ".csv" extension)')

    sep = ','

    def parse_input_list(input_str: str, sep=sep) -> list:
        '''Create list of input args separated by separator "sep" (str)'''
        input_args = input_str.split(sep)
        # Guard against leading, trailing, or repeated instances of the separator
        input_args = [s for s in input_args if s not in ['']]
        return input_args

    # Optional input arguments
    parser.add_argument('-cn', '--compound_names', type=parse_input_list,
                        help=f'include only variables with the specified compound names, examples: \
                        \n  -cn Amon.tas{sep}Omon.sos \
                        \n  -cn atmos.tas.tavg-h2m-hxy-u.mon.glb{sep}ocean.sos.tavg-u-hxy-sea.mon.glb \
                        \n(uses CMIP7 or CMIP6 based config parameter variable_name, use CMIP7_data_request_api_config to set)')
    parser.add_argument('-v', '--cmor_variables', type=parse_input_list,
                        help=f'include only the specified CMOR variable out_name, example: -v tas{sep}siconc')
    parser.add_argument('-r', '--realms', type=parse_input_list,
                        help=f'include only the specified realms, examples: \
                        \n  -r atmos \
                        \n  -r ocean{sep}ocnBgchem{sep}seaIce')
    parser.add_argument('-t', '--cmip6_cmor_tables', type=parse_input_list,
                        help=f'include only the specified CMIP6 CMOR tables, example: -t Amon{sep}Omon')

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
        cmor_tables=args.cmip6_cmor_tables,
        cmor_variables=args.cmor_variables,
        realms=args.realms,
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
