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


def get_variable_size(var_info, config, dreq_tables):
    '''
    Return size (B) of 1 year of a variable.
    Also return a dict giving its dimension sizes (no. of gridpoints, with the time size being for 1 year).
    '''

    # Available frequencies
    freqs = [rec.name for rec in dreq_tables['frequency'].records.values()]
    days_per_year = 365
    freq_times_per_year = {
        'subhr': days_per_year*48,
        '1hr': days_per_year*24,
        '3hr': days_per_year*8,
        '6hr': days_per_year*4,
        'day': days_per_year,
        'mon': 12,
        'yr': 1,
        'dec': 0.1,
        'fx': 1,
    }
    if set(freq_times_per_year.keys()) != set(freqs):
        raise Exception('Times per year must be defined for all available frequencies')

    # Available time dimensions ('time-intv', 'time-point', etc)
    time_dims = [rec.name for rec in dreq_tables['temporal shape'].records.values()]

    dimensions = var_info['dimensions']
    if isinstance(dimensions, str):
        dimensions = dimensions.split()
    assert all([isinstance(dim, str) for dim in dimensions])

    dim_sizes = {}
    for dim in dimensions:
        n = None
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
                # raise ValueError(f'Unknown size for dimension: {dim}')
        dim_sizes[dim] = n

    num_gridpoints = 1
    for dim in dim_sizes:
        num_gridpoints *= dim_sizes[dim]

    size = num_gridpoints
    size *= config['bytes_per_float']
    size *= config['scale_file_size']

    return size, dim_sizes


def parse_args():
    '''
    Parse command-line arguments
    '''

    parser = argparse.ArgumentParser(
        description='Estimate volume of requested model output'
    )
    # Positional arguments
    parser.add_argument('requested_variables', type=str,
                        help='json file specifying variables requested by experiment' +
                        ' (output from export_dreq_lists_json, which specifies the data request version)')
    # Optional arguments
    parser.add_argument('-v', '--variables', nargs='+', type=str,
                        help='include only the specified variables in the estimate')
    parser.add_argument('-e', '--experiments', nargs='+', type=str,
                        help='include only the specified experiments in the estimate')
    parser.add_argument('-c', '--config-size', type=str, default='size.yaml',
                        help='config file (yaml) giving size parameters to use in the volume estimate')
    parser.add_argument('-o', '--outfile', type=str,
                        help='name of output file, default: volume_estimate_{data request version}.json')
    parser.add_argument('-vso', '--variable-size-only', action='store_true',
                        help='show ONLY the sizes of individual variables (ignores experiments)')
    return parser.parse_args()


def main():

    args = parse_args()

    config_file = args.config_size
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
        print('Loaded ' + config_file)

    warning_msg = '\n * * * WARNING * * *'
    warning_msg += '\n These volumes are an initial estimate, to be improved in the next software version.'
    warning_msg += '\n They should be used with caution and verified against known data volumes.\n'

    filepath = args.requested_variables
    with open(filepath, 'r') as f:
        requested = json.load(f)
        print('Loaded ' + filepath)
    use_dreq_version = requested['Header']['dreq content version']
    print(f'Estimating volume for data request {use_dreq_version}')

    if not args.outfile:
        outfile = f'volume_estimate_{use_dreq_version}.json'
    else:
        outfile = args.outfile

    expts = requested['Header']['Experiments included']
    if args.experiments:
        # Only retain specified experiments
        expts = [expt for expt in expts if expt in args.experiments]
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
        'temporal shape': base['Temporal Shape'],
        'frequency': base['CMIP7 Frequency'],
    }

    # Get metadata for variables
    variables = dq.get_variables_metadata(
        base,
        use_dreq_version,
        compound_names=args.variables,
    )

    if args.variables and args.variable_size_only:
        # Find size of specified variables, then exit
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

    expt_records = {expt_rec.experiment: expt_rec for expt_rec in dreq_tables['expts'].records.values()}
    expt_size = OrderedDict()
    for expt in expts:
        expt_rec = expt_records[expt]
        # print('%-5s' % expt_rec.size_years_minimum, expt)
        request_size = OrderedDict()
        for priority, var_list in vars_by_expt[expt].items():
            if args.variables:
                # Only retain specified variables from the list of requested  variables
                var_list = [var_name for var_name in var_list if var_name in args.variables]
            request_size[priority] = OrderedDict({
                'no. of vars': len(var_list),
                'size': 0, 
                })
            for var_name in var_list:
                var_info = variables[var_name]
                # Get size of 1 year of this variable
                size, dim_sizes = get_variable_size(var_info, config, dreq_tables)
                if var_info['frequency'] == 'fx':
                    pass
                # ALSO NEED TO HANDLE CLIMATOLOGIES
                else:
                    # Multiply by minimum number of request years for this experiment
                    size *= expt_rec.size_years_minimum
                # Increment size tally for this experiment at this priority level
                request_size[priority]['size'] += size

        priority = 'TOTAL'    
        assert priority not in request_size
        request_size[priority] = OrderedDict({
            'no of vars': sum([d['no. of vars'] for d in request_size.values()]),
            'size': sum([d['size'] for d in request_size.values()]),
            })
        for d in request_size.values():
            d['size_str'] = file_size_str(d['size'])

        expt_size[expt] = OrderedDict({
            'no. of years': expt_rec.size_years_minimum,
            'no. of ensemble members': 1,  # ADD ENSEMBLE MEMBER INFO LATER!
        })
        # if args.variables:
        #     expt_size[expt]['variables subset of request'] = args.variables
        expt_size[expt].update({
            'total request size (all priorities)': request_size['TOTAL'],
            'request size by priority level': OrderedDict(),
        })
        for priority in vars_by_expt[expt]:
            expt_size[expt]['request size by priority level'][priority] = request_size[priority]

    out = OrderedDict({
        'Header': OrderedDict({
            'dreq content version': use_dreq_version,
            'requested experiments and variables': args.requested_variables,
            'model-specific size options': args.config_size,
        }),
        'volume by experiment': expt_size,
    })
    if args.variables:
        out['Header']['variables subset of request'] = args.variables
    if args.experiments:
        out['Header']['experiments subset of request'] = args.experiments

    with open(outfile, 'w') as f:
        json.dump(out, f, indent=4)
        print('Wrote ' + outfile)

    print(warning_msg)

if __name__ == '__main__':
    main()
