#!/usr/bin/env python
'''
Example script for basic use of CMIP7 data request content

Getting started
---------------
First create an environment with the required dependencies:

    conda env create -n my_dreq_env --file env.yml

(replacing my_dreq_env with your preferred env name). Then activate it and run the script:

    conda activate my_dreq_env
    python workflow_example.py

will load the data request content and save a json file of requested variables in the current dir.
To run interactively in ipython:

    run -i workflow_example.py

'''
# try: tables
# except: tables = {}

# use_export = 'release'
# use_export = 'raw'

# if True:
if False:

    for use_export in tables:

        print(f'\n*** {use_export}  ***')

        VarGroups = tables[use_export]['VarGroups']
        Opps = tables[use_export]['Opps']

        titles = []
        titles.append('Temperature variability')
        titles.append('Ocean Extremes')

        for title in titles:
            print()
            opp = Opps.get_attr_record('title', title)
            print(opp.title)
            for link in opp.variable_groups:
                vg = VarGroups.get_record(link)
                print(vg.name)

    stop

import sys
import json
add_paths = ['../sandbox/MS/dreq_api/', '../sandbox/JA', '../sandbox/GR']
for path in add_paths:
    if path not in sys.path:
        sys.path.append(path)
import dreq_content as dc
import dreq_query as dq

from importlib import reload
reload(dq)


test = True


# Specify opportunities that modelling group chooses to support
# This can be a subset:
use_opps = []
use_opps.append('Baseline Climate Variables for Earth System Modelling')
# use_opps.append('Synoptic systems and impacts')
# use_opps.append('Climate impact assessments on freshwater ecosystems')
use_opps.append('Ocean Extremes')

# Or to use all opportunities in the data request:
use_opps = 'all'


if test:

    import os

    use_dreq_version = 'v1.0beta'

    use_export = 'release'
    use_export = 'raw'

    use_consolidated = not True

    load_manually = not True

    if load_manually:
        # just for testing
        path = '/home/rja001/code/dreq/CMIP7_DReq_Content/airtable_export'
        filepath = os.path.join(path, 'dreq_working.json')
        with open(filepath, 'r') as f:
            content = json.load(f)
            print('loaded ' + filepath)

        use_consolidated = False

    else:
        # Download specified version of data request content (if not locally cached)
        dc.retrieve(use_dreq_version, export=use_export)
        # Load content into python dict
        content = dc.load(use_dreq_version, export=use_export, consolidate=use_consolidated)




else:

    use_dreq_version = 'v1.0beta'

    # Download specified version of data request content (if not locally cached)
    dc.retrieve(use_dreq_version)
    # Load content into python dict
    content = dc.load(use_dreq_version)


# Get consolidated list of requested variables that supports these opportunities
dq.DREQ_VERSION = use_dreq_version

if test:

    use_old_get = False

    if use_old_get:

        if len(content.keys()) == 1:
            k = 'Data Request'
            if k in content:
                content[f'{k} {use_dreq_version}'] = content[k]
                content.pop(k)
        expt_vars = dq._get_requested_variables(content, use_opps, priority_cutoff='Low')

    else:

        expt_vars = dq.get_requested_variables(content, use_opps, priority_cutoff='Low', verbose=False, consolidated=use_consolidated)




        if False:
            # return Opps, VarGroups, PriorityLevel, ExptGroups, Expts

            Opps, VarGroups, PriorityLevel, ExptGroups, Expts = expt_vars
            del expt_vars

            tables[use_export] = {
                'Opps' : Opps, 'VarGroups' : VarGroups,
            }
            
            opps = []
            opps.append( Opps.get_attr_record('title', 'Temperature variability') )

            # opps.append( Opps.get_attr_record('title', 'Ocean Extremes') )

            for title in [            
                "Ocean Extremes",
                "Ocean changes, drivers and impacts",
                "Rapid Evaluation Framework",
                "Paleoclimate research at the interface between past, present, and future",
                "Robust Risk Assessment of Tipping Points",
            ]:
                opps.append( Opps.get_attr_record('title', title) )

            # achtung!
            # "Ocean Extremes",
            # "Ocean changes, drivers and impacts",
            # "Rapid Evaluation Framework",
            # "Paleoclimate research at the interface between past, present, and future",
            # "Robust Risk Assessment of Tipping Points",

            # opp = opps[0]
            # opp_expts0 = dq.get_opp_expts(opp, ExptGroups, Expts, verbose=False)

            for opp in opps:
                print('\n' + opp.title)
                # opp_expts = dq.get_opp_expts(opp, ExptGroups, Expts, verbose=False)
                # print(opp_expts.difference(opp_expts0))
                for link in opp.variable_groups: 
                    vg = VarGroups.get_record(link)
                    if isinstance(vg.priority_level, str):
                        assert PriorityLevel is None
                        print(vg.priority_level)
                    else:
                        link = vg.priority_level[0]
                        pl = PriorityLevel.get_record(link)
                        print('  ' + pl.name)
            stop


else:
    
    expt_vars = dq.get_requested_variables(content, use_opps, priority_cutoff='Low')


if len(expt_vars['experiment']) > 0:

    # Show user what was found
    print(f'\nFor data request version {use_dreq_version}, number of requested variables found by experiment:')
    priority_levels = ['Core', 'High', 'Medium', 'Low']
    for expt, req in expt_vars['experiment'].items():
        d = {p : 0 for p in priority_levels}
        for p in priority_levels:
            if p in req:
                d[p] = len(req[p])
        n_total = sum(d.values())
        print(f'  {expt} : ' + ' ,'.join(['{p}={n}'.format(p=p,n=d[p]) for p in priority_levels]) + f', TOTAL={n_total}')

    # Write the results to json
    # filename = 'requested.json'
    filename = f'requested_{use_export}.json'

    with open(filename, 'w') as f:
        json.dump(expt_vars, f, indent=4, sort_keys=True)
        print('\nWrote requested variables to ' + filename)

else:
    print(f'\nFor data request version {use_dreq_version}, no requested variables were found')

# To remove locally cached version:
# dc.delete(use_dreq_version)
# To remove all locally cached versions:
# dc.delete()
