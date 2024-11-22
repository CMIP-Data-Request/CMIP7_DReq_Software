#!/usr/bin/env python
"""
Command line interface for retrieving simple variable lists from the data request.
"""

import sys
import json
import os
import argparse

# The following should be removed once python packaging is completed.
sys.path.append(os.path.join(os.path.dirname('__file__'), '..'))

import data_request_api.stable.content.dreq_api as dreq_api
import data_request_api.stable.content.dreq_api.dreq_content as dc
import data_request_api.stable.query.dreq_query as dq


def parse_args():
    """
    Parse command line arguments
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('dreq_version', choices=dc.get_versions(), help="data request version")
    parser.add_argument('--opportunities_file', type=str, help="path to JSON file listing opportunities to respond to. If it doesn't exist a template will be created")
    parser.add_argument('--all_opportunities', action='store_true', help="Respond to all opporunities")
    parser.add_argument('--experiments', nargs='+', type=str, help='limit output to the specified experiments')
    parser.add_argument('output_file', help='file to write JSON output to')
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

    # Deal with opportunities
    default_opportunity_dict = {j['Title of Opportunity']: True 
                            for j in content['Data Request']['Opportunity']['records'].values()}
    if args.opportunities_file:
        opportunities_file = args.opportunities_file
        if not os.path.exists(opportunities_file):
            with open(opportunities_file, 'w') as fh:
                json.dump(default_opportunity_dict, fh, indent=2) 
                print("written opportunities dict to {}. Please edit and re-run".format(opportunities_file))
                sys.exit(0)
        else:
            with open(opportunities_file, 'r') as fh:
                opportunity_dict = json.load(fh)
    elif args.all_opportunities:
        opportunity_dict = default_opportunity_dict
    else:
        print("Please use one of the opportunities arguments")
        sys.exit(1)

    use_opps = [i for i in opportunity_dict if opportunity_dict[i]]


    # Get consolidated list of requested variables that supports these opportunities
    dq.DREQ_VERSION = use_dreq_version
    expt_vars = dq.get_requested_variables(content, use_opps, priority_cutoff='Low', verbose=False)

    # filter output by requested experiments
    if args.experiments:
        experiments = list(expt_vars['experiment'].keys())
        for entry in experiments:
            if entry not in args.experiments:
                del expt_vars['experiment'][entry]

    # Construct output
    if len(expt_vars['experiment']) > 0:

        # Show user what was found
        print(f'\nFor data request version {use_dreq_version}, number of requested variables found by experiment:')
        priority_levels = ['Core', 'High', 'Medium', 'Low']
        for expt, req in sorted(expt_vars['experiment'].items()):
            d = {p : 0 for p in priority_levels}
            for p in priority_levels:
                if p in req:
                    d[p] = len(req[p])
            n_total = sum(d.values())
            print(f'  {expt} : ' + ' ,'.join(['{p}={n}'.format(p=p,n=d[p]) for p in priority_levels]) + f', TOTAL={n_total}')

        # Write the results to json
        filename = args.output_file
        with open(filename, 'w') as f:
            json.dump(expt_vars, f, indent=4, sort_keys=True)
            print('\nWrote requested variables to ' + filename)

    else:
        print(f'\nFor data request version {use_dreq_version}, no requested variables were found')

    # To remove locally cached version:
    # dc.delete(use_dreq_version)
    # To remove all locally cached versions:
    # dc.delete()


if __name__ == '__main__':
    main()