#!/usr/bin/env python

import argparse
import json
import os
import sys
import yaml
from collections import OrderedDict, defaultdict

import data_request_api.content.dreq_content as dc
import data_request_api.query.dreq_query as dq
from data_request_api.content.utils import _parse_version

# Set block size to use for converting bytes to larger units that are more easily readable (KB, MB, etc).
# Using BLOCK_SIZE = 1024 seems to give results closer to what bash shell 'du -h' produces.
BLOCK_SIZE = 1024  # 1 KB = 1024 B, 1 MB = 1024 KB, etc
# BLOCK_SIZE = 1000  # 1 KB = 1000 B, 1 MB = 1000 KB, etc


def file_size_str(size):
    '''
    Given file size in bytes, return string giving the size in nice
    human-readable units (like ls -h does at the shell prompt).
    '''
    SIZE_SUFFIX = {
        'B': 1,
        'KB': BLOCK_SIZE,
        'MB': BLOCK_SIZE**2,
        'GB': BLOCK_SIZE**3,
        'TB': BLOCK_SIZE**4,
        'PB': BLOCK_SIZE**5,
    }
    # sort size suffixes from largest to smallest
    uo = sorted([(1. / SIZE_SUFFIX[s], s) for s in SIZE_SUFFIX])
    # choose the most sensible size to display
    for tu in uo:
        if (size * tu[0]) > 1:
            break
    su = tu[1]
    size *= tu[0]
    sa = str('%.3g' % size)
    return sa + ' ' + su


def get_variable_size(var_info, dreq_dim_sizes, time_dims, freq_times_per_year, config):
    '''
    Return size (B) of 1 year of a variable.
    Also return a dict giving its dimension sizes (no. of gridpoints, with the time size being for 1 year).
    '''
    dimensions = var_info['dimensions']
    if isinstance(dimensions, str):
        dimensions = dimensions.split()
    assert all([isinstance(dim, str) for dim in dimensions])

    dim_sizes = {}
    temporal_shape = None
    for dim in dimensions:
        n = None
        if dim in time_dims:
            # Get number of time gridpoints in one year
            frequency = var_info['frequency']
            if dim == 'diurnal-cycle':
                # Special case: diurnal cycle averaged over a month
                assert frequency == '1hr', 'What frequency is correct for mean diurnal cycle? Received: ' + frequency
                n = 24 * 12
            else:
                n = freq_times_per_year[frequency]
            temporal_shape = time_dims[dim]
        elif dim in config['dimensions']:
            # Use model-specific dimension size
            n = config['dimensions'][dim]
        else:
            # Use dimension size specified in the data request
            # (e.g. for plev19, n = 19)
            n = dreq_dim_sizes[dim]

        if n is None:
            raise ValueError(f'No size found for dimension: {dim}')

        dim_sizes[dim] = n

    num_gridpoints = 1
    for dim in dim_sizes:
        num_gridpoints *= dim_sizes[dim]

    size = num_gridpoints
    size *= config['bytes_per_float']
    size *= config['scale_file_size']

    return size, dim_sizes, temporal_shape


def parse_args():
    '''
    Parse command-line arguments
    '''

    parser = argparse.ArgumentParser(
        description='Estimate volume of requested model output'
    )
    # Positional arguments
    parser.add_argument('request', type=str,
                        help='json file specifying variables requested by experiment \
                        (output from export_dreq_lists_json, which specifies the data request version) \
                        OR can be a data request version (e.g. "v1.2")')

    sep = ','

    def parse_input_list(input_str: str, sep=sep) -> list:
        '''Create list of input args separated by separator "sep" (str)'''
        input_args = input_str.split(sep)
        # Guard against leading, trailing, or repeated instances of the separator
        input_args = [s for s in input_args if s not in ['']]
        return input_args

    # Optional arguments
    parser.add_argument('-o', '--outfile', type=str,
                        help='name of output file, default: volume_estimate_{data request version}.json')
    parser.add_argument('-c', '--config-size', type=str, default='size.yaml',
                        help='config file (yaml) giving size parameters to use in the volume estimate')
    parser.add_argument('-v', '--variables', type=parse_input_list,
                        help=f'include only the specified variables in the estimate, \
                            example: -v Amon.tas{sep}Omon.tos')
    parser.add_argument('-e', '--experiments', type=parse_input_list,
                        help=f'include only the specified experiments in the estimate, \
                            example: -e historical{sep}piControl')
    parser.add_argument('-vso', '--variable-size-only', action='store_true',
                        help='show ONLY the sizes of individual variables (ignores experiments)')
    return parser.parse_args()


def main():

    args = parse_args()

    config_file = args.config_size
    if not os.path.exists(config_file):
        # If config file is not found, create default verison in the current dir
        config_file = 'size.yaml'
        if os.path.exists(config_file):
            # Be careful not to accidentally overwrite an existing size.yaml file
            print(f'Default config file found in current directory: {config_file}' +
                  '\nRe-run without -c argument to use this file, or use -c to specify an existing config file.')
            sys.exit()
        # Settings for the default config file
        w = '''# Data sizes config file for estimate_volume.py

# Model-specific dimension sizes (edit as needed)
dimensions:
  alevel: 80
  alevhalf: 80
  gridlatitude: 100
  latitude: 180
  longitude: 360
  olevel: 80
  olevhalf: 80
  rho: 80
  sdepth: 20
  soilpools: 5
  spectband: 10

# Number of bytes per floating point number
bytes_per_float: 4

# Scaling factor (e.g., adjust to account for netcdf compression)
scale_file_size: 1

# No. of years to use if showing size of single variables (-vso option)
years: 1

'''
        with open(config_file, 'w') as f:
            f.write(w)
            print('Created default config file: ' + config_file +
                  '\nRe-run after editing size.yaml with model-specific settings needed for data volume estimate.')
            sys.exit()

    # Get config file settings
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
        print('Loaded ' + config_file)

    warning_msg = '\n * * * * * * * * * * * * * * * WARNING * * * * * * * * * * * * * * *'
    warning_msg += '\n These volumes are an initial estimate.'
    warning_msg += '\n They should be used with caution and verified against known data volumes.'
    warning_msg += '\n * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * *\n'

    request_from_input_file = None
    if os.path.isfile(args.request):
        # Argument is a file that lists requested variables
        filepath = args.request
        with open(filepath, 'r') as f:
            request_from_input_file = json.load(f)
            print('Loaded ' + filepath)
        use_dreq_version = request_from_input_file['Header']['dreq content version']
        use_request = args.request
    elif args.request in dc.get_versions():
        # Argument is a recognized data request version string
        use_dreq_version = args.request
        use_request = 'all Opportunities'
    else:
        raise ValueError(f'"request" argument must be a json file (output from export_dreq_lists_json)' +
                         ' or data request version (e.g., "v1.2")')
    print(f'Estimating volume for data request {use_dreq_version}')

    if not args.outfile:
        outfile = f'volume_estimate_{use_dreq_version}.json'
    else:
        outfile = args.outfile

    # Download specified version of data request content (if not locally cached)
    dc.retrieve(use_dreq_version)
    # Load content into python dict
    content = dc.load(use_dreq_version)
    # Render data request tables as dreq_table objects
    base = dq.create_dreq_tables_for_request(content, use_dreq_version)

    dreq_tables = {
        'coordinates and dimensions': base['Coordinates and Dimensions'],
        'expts': base['Experiments'],
        'temporal shape': base['Temporal Shape'],
        'frequency': base['CMIP7 Frequency'],
        'spatial shape': base['Spatial Shape'],
        # 'opps': base['Opportunity'], # would need for ensemble members
    }

    # Get lookup table of dimension sizes
    dreq_dim_sizes = dq.get_dimension_sizes(dreq_tables)

    # Get available frequencies
    freqs = [rec.name for rec in dreq_tables['frequency'].records.values()]
    # Make lookup table of number of time points per year for each frequency
    days_per_year = 365
    freq_times_per_year = {
        'subhr': days_per_year * 48,
        '1hr': days_per_year * 24,
        '3hr': days_per_year * 8,
        '6hr': days_per_year * 4,
        'day': days_per_year,
        'mon': 12,
        'yr': 1,
        'dec': 0.1,
        'fx': 1,
    }
    # Make sure we got all frequencies
    if set(freq_times_per_year.keys()) != set(freqs):
        raise Exception('Times per year must be defined for all available frequencies')

    # Get mapping from time dimension name to temporal shape name
    # {'time1': 'time-point', 'time': 'time-intv', ... etc}
    time_dims = {}
    for rec in dreq_tables['temporal shape'].records.values():
        shape_name = rec.name
        if hasattr(rec, 'dimensions'):
            assert len(rec.dimensions) == 1
            link = rec.dimensions[0]
            dim_rec = dreq_tables['coordinates and dimensions'].get_record(link)
            dim_name = dim_rec.name
        else:
            dim_name = 'None'
        assert dim_name not in time_dims, 'time dimension names are not unique'
        time_dims[dim_name] = shape_name

    # Get metadata for variables
    variables = dq.get_variables_metadata(
        base,
        use_dreq_version,
        compound_names=args.variables,
    )

    if args.variables:
        # Confirm variables were found
        # (guards against typos in variable names causing silent fail)
        for var_name in args.variables:
            if var_name not in variables:
                raise ValueError(f'Variable not found: {var_name}')

    if args.variables and args.variable_size_only:
        # Find size of specified variables, then exit
        for var_name in args.variables:
            var_info = variables[var_name]
            size, dim_sizes, temporal_shape = get_variable_size(var_info, dreq_dim_sizes,
                                                                time_dims, freq_times_per_year, config)

            nyr = 1
            if 'years' in config:
                nyr = config['years']
                if nyr < 0:
                    raise ValueError(f'No. of years must be positive, received: {nyr}')
                size *= nyr
            syr = f'{nyr} year'
            if nyr > 1:
                syr += 's'
            msg = f'Size of {syr} of {var_name}: {file_size_str(size)}'
            dim_str = ', '.join([f'{k}={v}' for k, v in dim_sizes.items()])
            msg += f' (dimension sizes for 1 year: {dim_str})'
            print(msg)
        print(warning_msg)
        sys.exit()

    if request_from_input_file:
        # Use experiments from input file
        expts = request_from_input_file['Header']['Experiments included']
        vars_by_expt = request_from_input_file['experiment']
        del request_from_input_file
    else:
        # Generate lists of requested variables
        if use_request == 'all Opportunities':
            use_opps = 'all'
        else:
            raise ValueError('What Opportunities to use? Received: ' + use_request)
        # Get the requested variables
        priority_cutoff = 'Low'
        expt_vars = dq.get_requested_variables(base, use_dreq_version,
                                               use_opps=use_opps, priority_cutoff=priority_cutoff,
                                               verbose=False)
        expts = sorted(expt_vars['experiment'].keys(), key=str.lower)
        vars_by_expt = expt_vars['experiment']

    if args.experiments:
        # Check specified experiments are valid (guard against silent fail)
        for expt in args.experiments:
            if expt not in expts:
                raise ValueError(f'Experiment {expt} not found, is it missing from the input file or a typo?')
        # Only retain specified experiments
        expts = [expt for expt in expts if expt in args.experiments]

    # Loop over experiments, estimating output volume for each one
    expt_records = {expt_rec.experiment: expt_rec for expt_rec in dreq_tables['expts'].records.values()}
    expt_size = OrderedDict()
    all_vars = defaultdict(set)
    total_size = OrderedDict({'all priorities': 0})
    total_size.update({priority: 0 for priority in dq.get_priority_levels()})
    for expt in expts:
        expt_rec = expt_records[expt]

        if hasattr(expt_rec, 'size_years_minimum'):
            num_years = expt_rec.size_years_minimum
        else:
            num_years = 100
            print(f'Warning: number of years not found for experiment {expt}, assuming size_years_minimum = {num_years}')
        num_ensem = 1

        # Loop over priority levels of requeste variables
        request_size = OrderedDict()
        for priority, var_list in vars_by_expt[expt].items():
            if args.variables:
                # Only retain specified variables from the list of requested  variables
                var_list = [var_name for var_name in var_list if var_name in args.variables]
            request_size[priority] = OrderedDict({
                'no. of variables': len(var_list),
                'size (bytes)': 0,
            })

            # Loop over variables requested at this priority level
            for var_name in var_list:
                var_info = variables[var_name]
                # Get size of 1 year of this variable
                size, dim_sizes, temporal_shape = get_variable_size(var_info, dreq_dim_sizes,
                                                                    time_dims, freq_times_per_year, config)

                if var_info['frequency'] == 'fx' or temporal_shape in [None, 'None', 'time-fxc']:
                    # For fixed fields, get_variable_size() assumed 1 "time" point per year,
                    # and no need to multiply by number of years.
                    pass
                elif temporal_shape == 'climatology':
                    # For climatology, should not multiply by number of years.
                    pass
                elif temporal_shape == 'diurnal-cycle':
                    # Assume this is a climatology, so don't multiply by number of years
                    pass
                else:
                    valid_shapes = ['time-intv', 'time-point', 'monthly-mean-daily-stat']
                    if _parse_version(use_dreq_version) < (1, 2, 0, 0, "", 0):
                        # Prior to v1.2, monthly-mean-daily-stat was called monthly-mean-stat
                        valid_shapes.append('monthly-mean-stat')
                    assert temporal_shape in valid_shapes, \
                        'Unknown temporal shape: ' + str(temporal_shape)
                    # Multiply the 1-year size by the minimum number of request years for this experiment
                    size *= num_years

                # Multiply by number of ensemble members
                size *= num_ensem
                # Increment size tally for this experiment at this priority level
                request_size[priority]['size (bytes)'] += size

                # Increment variables count
                all_vars[priority].add(var_name)

        # Get total size and number of variables across all priorities
        priority = 'all priorities'
        assert priority not in request_size
        request_size[priority] = OrderedDict({
            'no. of variables': sum([d['no. of variables'] for d in request_size.values()]),
            'size (bytes)': sum([d['size (bytes)'] for d in request_size.values()]),
        })

        # Provide sizes more readable units than number of bytes
        for d in request_size.values():
            d['size (human readable)'] = file_size_str(d['size (bytes)'])

        # Clarify assumptions that went into the volume estimate
        expt_size[expt] = OrderedDict({
            'assumed no. of years': num_years,
            'assumed no. of ensemble members': num_ensem,
        })

        # Give volumes by priority level and for the total (all priorities)
        expt_size[expt].update({
            'total request size (all priorities)': request_size['all priorities'],
            'request size by priority level': OrderedDict(),
        })
        for priority in vars_by_expt[expt]:
            expt_size[expt]['request size by priority level'][priority] = request_size[priority]

        # Increment total size estimate (total across all experiments)
        for priority in request_size:
            total_size[priority] += request_size[priority]['size (bytes)']

    # Show total number of variables (by priority level) across all experiments
    total_vars = OrderedDict({
        'all priorities': set()
    })
    for priority in dq.get_priority_levels():
        total_vars[priority] = len(all_vars[priority])
        total_vars['all priorities'].update(all_vars[priority])
    total_vars['all priorities'] = len(total_vars['all priorities'])

    # Show human-readable units for total sizes in the output file
    # (size in bytes is available from the experiment entries, this is a summary for the file header)
    for priority, size in total_size.items():
        total_size[priority] = file_size_str(size)

    out = OrderedDict({
        'Header': OrderedDict({
            'dreq content version': use_dreq_version,
            'requested experiments and variables': use_request,
            'no. of experiments': len(expts),
            'total for all experiments': OrderedDict({
                'no. of variables': total_vars,
                'size (human readable)': total_size,
            }),
            'model-specific size options': args.config_size,
            'block size for converting bytes to human-readable units': BLOCK_SIZE,
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
