#!/usr/bin/env python

import argparse
import json
import os
import sys
import yaml
from collections import OrderedDict

import data_request_api
import data_request_api.content.dreq_content as dc
import data_request_api.query.dreq_query as dq

def parse_args():
    '''
    Parse command-line arguments
    '''

    parser = argparse.ArgumentParser(
        description='Estimate volume of requested model output'
    )
    # Positional arguments
    parser.add_argument('requested_vars', type=str,
                        help='json file specifying variables requested by experiment' +
                        '(output from export_dreq_lists_json)')
    # Optional arguments
    parser.add_argument('-v', '--variables', nargs='+', type=str,
                        help='include only the specified variables in the estimate')
    parser.add_argument('-c', '--config_size', type=str, default='size.yaml',
                        help='config file (yaml) giving size parameters to use in the volume estimate')
    return parser.parse_args()

def file_size_str(size):
    '''
    Given file size in bytes, return string giving the size in nice
    human-readable units (like ls -h does at the shell prompt).
    '''
    BLOCK_SIZE = 1024.  # 1 MB = 1024 KB, 1 GB = 1024 MB, etc
    # BLOCK_SIZE = 1000.  # 1 MB = 1000 KB, 1 GB = 1000 MB, etc
    SIZE_SUFFIX = {
        'B' : 1,
        'KB': BLOCK_SIZE,
        'MB': BLOCK_SIZE**2,
        'GB': BLOCK_SIZE**3,
        'TB': BLOCK_SIZE**4,
        'PB': BLOCK_SIZE**5,
    }
    # sort size suffixes from largest to smallest
    uo = sorted([(1./SIZE_SUFFIX[s], s) for s in SIZE_SUFFIX])
    # choose the most sensible size to display
    for tu in uo:
        if (size*tu[0]) > 1: break
    su = tu[1]
    size *= tu[0]
    sa = str('%.3g' % size)
    return sa + ' ' + su


def get_variable_size(var_info, config, dreq_tables):   # MOVE INTO DREQ_QUERY
    '''
    Return size (B) of 1 year of a variable.
    Also return a dict giving its dimension sizes (no. of gridpoints, with the time size being for 1 year).
    '''

    days_per_year = 365
    freq_times_per_year = {
        # 'subhr': days_per_year*48,
        '3hr': days_per_year*8,
        '6hr': days_per_year*4,
        'day': days_per_year,
        'mon': 12,
        'yr': 1,
        'dec': 0.1,
    }

    time_dims = ['time-intv', 'time-point']   # NEEDS TO BE COMPLETE

    dimensions = var_info['dimensions']
    if isinstance(dimensions, str):
        dimensions = dimensions.split()
    assert all([isinstance(dim, str) for dim in dimensions])

    dim_sizes = {}
    for dim in dimensions:
        if dim in time_dims:
            # Get number of time gridpoints in one year
            frequency = var_info['frequency']
            n = freq_times_per_year[frequency]
        elif dim in config['dimensions']:
            # Use model-specific dimension size
            n = config['dimensions'][dim]
        else:
            # Use requested dimension size (i.e., size given in the data request)
            
            rec = dreq_tables['coordinates and dimensions'].get_attr_record('name', dim, unique=True)
            # print(rec)
            if hasattr(rec, 'size'):
                n = rec.size
            else:
                n = 1

        dim_sizes[dim] = n

    num_gridpoints = 1
    for dim in dim_sizes:
        num_gridpoints *= dim_sizes[dim]

    size = num_gridpoints
    size *= config['bytes_per_float']
    size *= config['scale_file_size']

    return size, dim_sizes


def main():

    args = parse_args()

    config_file = args.config_size
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
        print('Loaded ' + config_file)

    warning_msg = '\n * * * WARNING * * *'
    warning_msg += '\n These volumes are only an estimate, and should be verified against known data volumes\n'

    filepath = args.requested_vars
    with open(filepath, 'r') as f:
        requested = json.load(f)
        print('Loaded ' + filepath)
    use_dreq_version = requested['Header']['dreq content version']
    print(f'Estimating volume for data request {use_dreq_version}')

    expts = requested['Header']['Experiments included']
    vars_by_expt = requested['experiment']

    # Download specified version of data request content (if not locally cached)
    dc.retrieve(use_dreq_version)
    # Load content into python dict
    content = dc.load(use_dreq_version)
    # Render data request tables as dreq_table objects
    base = dq.create_dreq_tables_for_request(content, use_dreq_version)

    dreq_tables = {
        'coordinates and dimensions': base['Coordinates and Dimensions'],
        'expts': base['Experiments'],
        'opps': base['Opportunity'],
    }

    # Get metadata for variables
    variables = dq.get_variables_metadata(
        base,
        use_dreq_version
    )

    if args.variables:
        # Find size of 1 year of specified variables, then exit
        for var_name in args.variables:
            var_info = variables[var_name]
            size, dim_sizes = get_variable_size(var_info, config, dreq_tables)
            nyr = 1
            if 'years' in config:
                nyr = config['years']
                if nyr < 0:
                    raise ValueError(f'No. of years must be positive, received: {nyr}')
                size *= nyr
            syr = f'{nyr} year'
            if nyr > 1: syr += 's'
            msg = f'Size of {syr} of {var_name}: {file_size_str(size)}'
            dim_str = ', '.join([f'{k}={v}' for k,v in dim_sizes.items()])
            msg += f' (dimension sizes for 1 year: {dim_str})'
            print(msg)

        print(warning_msg)
        sys.exit()



    # print(dreq_tables['expts'])

    # print(dreq_tables['expts'].get_record(0))

    expt_records = {expt_rec.experiment: expt_rec for expt_rec in dreq_tables['expts'].records.values()}

    # for expt in sorted(expt_records, key=str.lower):
    for expt in expts:
        expt_rec = expt_records[expt]

        print('%-5s' % expt_rec.size_years_minimum, expt)

        request_size = {}
        for priority, var_list in vars_by_expt[expt].items():
            # print(priority)
            # print(var_list, len(var_list))
            request_size[priority] = {'size' : 0, 'no. of vars' : len(var_list)}
            for var_name in var_list:
                var_info = variables[var_name]

                try:
                    size, dim_sizes = get_variable_size(var_info, config, dreq_tables)  # FIX
                except:
                    size = 1

                request_size[priority]['size'] += size

        priority = 'TOTAL'    
        assert priority not in request_size
        request_size[priority] = {
            'size': sum([d['size'] for d in request_size.values()]),
            'no of vars': sum([len(var_list) for var_list in vars_by_expt[expt].values()])
        }

        for priority in request_size:
            size = request_size[priority]['size']
            request_size[priority]['size_str'] = file_size_str(size)

        print(expt, request_size)
        stop
            



        # show size per expt as function of priority level

        break

    # print(dreq_tables['var groups'].get_record(0))

    # print(dreq_tables['opps'].get_record(0))
    '''
    minimum_ensemble_size: 1
    other ensem info?

    give size per ensem member  
    
    add ensem member info to vars list json, b/c depends on opportunity

    prob cannot account for timeslices

    get var frequencies, convert to time gridpoints per year

    allow to display per variable for file of given size, so can adjust scale factor (e.g. for nc compression)

    '''



if __name__ == '__main__':
    main()
