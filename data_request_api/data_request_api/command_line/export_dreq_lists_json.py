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
import data_request_api.content.dreq_content as dc
import data_request_api.query.dreq_query as dq


def parse_args():
    """
    Parse command-line arguments
    """

    parser = argparse.ArgumentParser(
        description='Get lists of requested variables by experiment, and write them to a json file.'
    )

    # Positional (mandatory) input arguments
    parser.add_argument('dreq_version', choices=dc.get_versions(), help="data request version")
    parser.add_argument('output_file', help='file to write JSON output to')

    sep = ','

    def parse_input_list(input_str: str, sep=sep) -> list:
        '''Create list of input args separated by separator "sep" (str)'''
        input_args = input_str.split(sep)
        # Guard against leading, trailing, or repeated instances of the separator
        input_args = [s for s in input_args if s not in ['']]
        return input_args

    # Optional input arguments
    parser.add_argument('-a', '--all_opportunities', action='store_true',
                        help="respond to all opportunities")
    parser.add_argument('-f', '--opportunities_file', type=str,
                        help="path to JSON file listing opportunities to respond to. \
                            If it doesn't exist, a template will be created")
    parser.add_argument('-i', '--opportunity_ids', type=parse_input_list,
                        help=f'opportunity ids (integers) of opportunities to respond to, \
                            example: -i 69{sep}22{sep}37')
    parser.add_argument('-e', '--experiments', type=parse_input_list,
                        help=f'limit output to the specified experiments (case sensitive), \
                            example: -e historical{sep}piControl')
    parser.add_argument('-p', '--priority_cutoff', default='low', choices=dq.PRIORITY_LEVELS,
                        help="discard variables that are requested at lower priority than this cutoff priority")
    parser.add_argument('-m', '--variables_metadata', type=str,
                        help='output file containing metadata of requested variables, can be ".json" or ".csv" file')
    parser.add_argument("-c", "--add_combined", action="store_true", default=False,
                        help="Include combined request from all selected opportunities and for all experiments. "
                             "Will create the new entry 'all_experiments' for the combined request.")
    parser.add_argument("-t", "--time_subsets", action="store_true", default=False,
                        help="Include time_subsets that variables are requested for.")
    parser.add_argument("-d", "--disable_core_vars_check", action="store_true", default=False,
                        help="Don't require that core variables are included in the request.")

    return parser.parse_args()


def main():
    """
    main routine
    """
    args = parse_args()

    use_dreq_version = args.dreq_version

    # Download specified version of data request content (if not locally cached)
    dc.retrieve(use_dreq_version)
    # Load content into python dict
    content = dc.load(use_dreq_version)
    # Render data request tables as dreq_table objects
    base = dq.create_dreq_tables_for_request(content, use_dreq_version)

    # Deal with opportunities
    if args.opportunities_file:
        # Select opportunities by their title, as given in a user-specified json file
        opportunities_file = args.opportunities_file
        dreq_opps = base['Opportunity']
        if not os.path.exists(opportunities_file):
            # create opportunities file template
            use_opps = sorted([opp.title for opp in dreq_opps.records.values()], key=str.lower)
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
                print("written opportunities dict to {}. Please edit and re-run".format(opportunities_file))
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
            valid_opps = [opp.title for opp in dreq_opps.records.values()]
            invalid_opps = [title for title in opportunity_dict if title not in valid_opps]
            if invalid_opps:
                raise ValueError(f'\nInvalid opportunities were found in {opportunities_file}:\n' + '\n'.join(sorted(invalid_opps, key=str.lower)))

            # filter opportunities
            use_opps = [title for title in opportunity_dict if opportunity_dict[title]]

    elif args.opportunity_ids:
        # Select opportunities by their integer IDs, specified from the command line
        dreq_opps = base['Opportunity']
        all_opp_ids = [opp.opportunity_id for opp in dreq_opps.records.values()]
        if len(all_opp_ids) != len(set(all_opp_ids)):
            raise ValueError(f'Opportunity IDs (integers) in data request {use_dreq_version} are not unique!')
        oppid2title = {int(opp.opportunity_id): opp.title for opp in dreq_opps.records.values()}
        use_opps = []
        invalid_opp_ids = set()
        for opp_id in args.opportunity_ids:
            try:
                opp_id = int(opp_id)
            except BaseException:
                ValueError('Opportunity ID should be an integer')
            if opp_id in oppid2title:
                use_opps.append(oppid2title[opp_id])
            else:
                invalid_opp_ids.add(opp_id)
        if len(invalid_opp_ids) > 0:
            raise ValueError(f'The following Opportunity IDs were not found in data request {use_dreq_version}: '
                             + ', '.join([str(opp_id) for opp_id in sorted(invalid_opp_ids)]))

    elif args.all_opportunities:
        # Use all available opportunities in the data request
        use_opps = 'all'

    else:
        print("Please use one of the opportunities arguments")
        sys.exit(1)

    # Get the requested variables for each opportunity and aggregate them into variable lists by experiment
    # (i.e., for every experiment, a list of the variables that should be produced to support all of the specified opportunities)
    expt_vars = dq.get_requested_variables(base, use_dreq_version,
                                           use_opps=use_opps, priority_cutoff=args.priority_cutoff,
                                           time_subsets=args.time_subsets, combined_request=args.add_combined,
                                           verbose=False, check_core_variables=not args.disable_core_vars_check)

    # filter output by requested experiments
    if args.experiments:
        experiments = list(expt_vars['experiment'].keys())  # names of experiments requested by opportunities in use_opps

        # validate the requested experiment names
        Expts = base['Experiments']
        valid_experiments = [expt.experiment for expt in Expts.records.values()]  # all valid experiment names in data request
        invalid_experiments = [entry for entry in args.experiments if entry not in valid_experiments]
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
        dq.write_requested_vars_json(outfile, expt_vars, use_dreq_version, args.priority_cutoff, content_path)

    else:
        print(f'\nFor data request version {use_dreq_version}, no requested variables were found')

    if args.variables_metadata:

        # Get all variable names for all requested experiments
        all_var_names = set()
        for vars_by_priority in expt_vars['experiment'].values():
            for var_names in vars_by_priority.values():
                all_var_names.update(var_names)

        # Get metadata for variables
        all_var_info = dq.get_variables_metadata(
            base,
            use_dreq_version,
            compound_names=all_var_names,
            verbose=False,
        )

        # Write output file(s)
        filepath = args.variables_metadata
        dq.write_variables_metadata(
            all_var_info,
            use_dreq_version,
            filepath,
            api_version=data_request_api.version,
            content_path=dc._dreq_content_loaded['json_path']
        )


if __name__ == '__main__':
    main()
