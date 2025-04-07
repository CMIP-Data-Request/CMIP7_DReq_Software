#!/usr/bin/env python
"""
Command line interface for retrieving simple variable lists from the data request.
"""

import sys
import json
import os
import argparse
from collections import OrderedDict

import data_request_api
import data_request_api.stable.content.dreq_content as dc
import data_request_api.stable.query.dreq_query as dq


def parse_args():
    """
    Parse command line arguments
    """

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'dreq_version', choices=dc.get_versions(), help="data request version")
    parser.add_argument(
        '--opportunities_file', type=str,
        help="path to JSON file listing opportunities to respond to. If it doesn't exist a template will be created")
    parser.add_argument('--all_opportunities', action='store_true',
                        help="respond to all opportunities")
    parser.add_argument('--experiments', nargs='+', type=str,
                        help='limit output to the specified experiments (space-delimited list, case sensitive)')
    parser.add_argument('--priority_cutoff', default='low', choices=dq.PRIORITY_LEVELS,
                        help="discard variables that are requested at lower priority than this cutoff priority")
    parser.add_argument('output_file', help='file to write JSON output to')
    parser.add_argument('--version', action='store_true',
                        help='Return version information and exit')

    def _var_metadata_check(arg):
        if arg.endswith('.json') or arg.endswith('.csv'):
            return arg
        else:
            raise ValueError()
    parser.register('type', 'json_or_csv_file', _var_metadata_check)
    parser.add_argument('-vm', '--variables_metadata', nargs='+', type='json_or_csv_file',
                        help='output files containing variable metadata of requested variables, files with ".json" or ".csv" will be produced')

    return parser.parse_args()


def main():
    """
    main routine
    """
    args = parse_args()

    if args.version:
        print("CMIP7 data request api version {}".format(
            data_request_api.version))
        sys.exit(0)
    use_dreq_version = args.dreq_version

    # Download specified version of data request content (if not locally cached)
    dc.retrieve(use_dreq_version)
    # Load content into python dict
    content = dc.load(use_dreq_version)
    # Render data request tables as dreq_table objects
    base = dq.create_dreq_tables_for_request(content)

    # Deal with opportunities
    if args.opportunities_file:
        opportunities_file = args.opportunities_file
        Opps = base['Opportunity']
        if not os.path.exists(opportunities_file):
            # create opportunities file template
            use_opps = sorted(
                [opp.title for opp in Opps.records.values()], key=str.lower)
            default_opportunity_dict = OrderedDict({
                'Header': OrderedDict({
                    'Description': 'Opportunities template file for use with export_dreq_lists_json. Set supported/unsupported Opportunities to true/false.',
                    'dreq content version': use_dreq_version,
                    'dreq api version': data_request_api.version,
                }),
                'Opportunity': OrderedDict({title: True for title in use_opps})
            })
            with open(opportunities_file, 'w') as fh:
                json.dump(default_opportunity_dict, fh, indent=4)
                print(
                    "written opportunities dict to {}. Please edit and re-run".format(opportunities_file))
                sys.exit(0)
        else:
            # load existing opportunities file
            with open(opportunities_file, 'r') as fh:
                opportunity_dict = json.load(fh)

            dreq_version = opportunity_dict['Header']['dreq content version']
            if dreq_version != use_dreq_version:
                raise ValueError('Data request version mismatch!' +
                                 f'\nOpportunities file was generated for data request version {dreq_version}' +
                                 f'\nPlease regenerate the file using version {use_dreq_version}')

            opportunity_dict = opportunity_dict['Opportunity']

            # validate opportunities
            # (mismatches can occur if an opportunities file created with an earlier data request version is loaded)
            valid_opps = [opp.title for opp in Opps.records.values()]
            invalid_opps = [
                title for title in opportunity_dict if title not in valid_opps]
            if invalid_opps:
                raise ValueError(f'\nInvalid opportunities were found in {opportunities_file}:\n' + '\n'.join(
                    sorted(invalid_opps, key=str.lower)))

            # filter opportunities
            use_opps = [
                title for title in opportunity_dict if opportunity_dict[title]]

    elif args.all_opportunities:
        use_opps = 'all'
    else:
        print("Please use one of the opportunities arguments")
        sys.exit(1)

    # Get consolidated list of requested variables that supports these opportunities
    dq.DREQ_VERSION = use_dreq_version
    expt_vars = dq.get_requested_variables(
        base, use_opps, priority_cutoff=args.priority_cutoff, verbose=False)

    # filter output by requested experiments
    if args.experiments:
        # names of experiments requested by opportunities in use_opps
        experiments = list(expt_vars['experiment'].keys())

        # validate the requested experiment names
        Expts = base['Experiments']
        # all valid experiment names in data request
        valid_experiments = [
            expt.experiment for expt in Expts.records.values()]
        invalid_experiments = [
            entry for entry in args.experiments if entry not in valid_experiments]
        if invalid_experiments:
            raise ValueError('\nInvalid experiments: ' + ', '.join(sorted(invalid_experiments, key=str.lower)) +
                             '\nValid experiment names: ' + ', '.join(sorted(valid_experiments, key=str.lower)))

        # discard experiments that aren't requested
        for entry in experiments:
            if entry not in args.experiments:
                del expt_vars['experiment'][entry]

    # Construct output
    if len(expt_vars['experiment']) > 0:

        # Show user what was found
        dq.show_requested_vars_summary(expt_vars, use_dreq_version)

        # Write json file with the variable lists
        content_path = dc._dreq_content_loaded['json_path']
        outfile = args.output_file
        dq.write_requested_vars_json(
            outfile, expt_vars, use_dreq_version, args.priority_cutoff, content_path)

    else:
        print(
            f'\nFor data request version {use_dreq_version}, no requested variables were found')

    if args.variables_metadata:

        # Get all variable names for all requested experiments
        all_var_names = set()
        for expt_name, vars_by_priority in expt_vars['experiment'].items():
            for priority_level, var_names in vars_by_priority.items():
                all_var_names.update(var_names)

        # Get metadata for variables
        all_var_info = dq.get_variables_metadata(
            base,
            compound_names=all_var_names,
            use_dreq_version=use_dreq_version  # TO DEPRECATE
        )

        # Write output file(s)
        for filepath in args.variables_metadata:
            dq.write_variables_metadata(
                all_var_info,
                filepath,
                api_version=data_request_api.version,
                use_dreq_version=use_dreq_version,
                content_path=dc._dreq_content_loaded['json_path']
            )


if __name__ == '__main__':
    main()
