'''
Functions to extract information from the data request.
E.g., get variables requested for each experiment.
'''

from dreq_classes import dreq_table, expt_request, UNIQUE_VAR_NAME

DREQ_VERSION = ''  # if a tagged version is being used, set this in calling script

def get_content_type(content):
    '''
    Internal function to distinguish the type of airtable export we are working with, based on the input dict.

    Parameters
    ----------
    content : dict
        Dict containing data request content exported from airtable.

    Returns
    -------
    str indicating type of content:
        'working'   3 bases containing the latest working version of data request content
        'version'   1 base containing the content of a tagged data request version
    '''
    content_type = ''
    match len(content):
        case 3:
            content_type = 'working'
        case 1:
            content_type = 'version'
    return content_type

def version_base_name():
    return f'Data Request {DREQ_VERSION}'

def get_opp_id(use_opps, Opps, verbose=False):
    '''
    Return list of unique opportunity identifiers.

    Parameters
    ----------
    use_opps : str or list
        "all" : return all available ids
        list of str : return ids for with the listed opportunity titles
    Opps : dreq_table
        table object representing the opportunities table
    '''
    opp_ids = []
    records = Opps.records
    if use_opps == 'all':
        # Include all opportunities
        opp_ids = list(records.keys())
    elif isinstance(use_opps, list):
        if all([isinstance(s, str) for s in use_opps]):
            # opp_ids = [opp_id for opp_id,opp in records.items() if opp.title in use_opps]
            title2id = {opp.title : opp_id for opp_id,opp in records.items()}
            assert len(records) == len(title2id), 'Opportunity titles are not unique'
            for title in use_opps:
                if title in title2id:
                    opp_ids.append(title2id[title])
                else:
                    print(f'\n* WARNING *    Opportunity not found: {title}\n')
    if verbose:
        if len(opp_ids) > 0:
            print('Found {} Opportunities:'.format(len(opp_ids)))
            for opp_id in opp_ids:
                opp = records[opp_id]
                print('  ' + opp.title)
        else:
            print('No Opportunities found')
    return opp_ids

def get_var_group_priority(var_group, PriorityLevel=None):
    '''
    Returns string stating the priorty level of variable group.

    Parameters
    ----------
    var_group : dreq_record
        Object representing a variable group
        Its "priority_level" attribute specifies the priority as either string or link to PriorityLevel table 
    PriorityLevel : dreq_table
        Required if var_group.priority_level is link to PriorityLevel table 

    Returns
    -------
    str that states the priority level: "High", "Medium", or "Low"
    '''
    if isinstance(var_group.priority_level, list):
        assert len(var_group.priority_level) == 1, 'Variable group should have one specified priority level'
        link = var_group.priority_level[0]
        assert isinstance(PriorityLevel, dreq_table)
        rec = PriorityLevel.records[link.record_id]
        priority_level = rec.name
    elif isinstance(var_group.priority_level, str):
        priority_level = var_group.priority_level
    else:
        raise Exception('Unable to determine variable group priority level')
    if not isinstance(priority_level, str):
        raise TypeError('Priority level should be str, instead got {}'.format(type(priority_level)))
    return priority_level

def get_unique_var_name(var):
    '''
    Return name that uniquely identifies a variable.
    Reason to make this a function is to control this choice in one place.
    E.g., if compound_name is used initially, but something else chosen later.

    Parameters
    ----------
    var : dreq_record
        Object representing a variable

    Returns
    -------
    str that uniquely identifes a variable in the data request
    '''
    match UNIQUE_VAR_NAME:
        case 'compound name':
            return var.compound_name
        case _:
            raise Exception('How to determine unique variable name?')


def get_opp_expts(opp, ExptGroups, Expts, verbose=False):
    '''
    For one Opportunity, get its requested experiments.
    Input parameters are not modified.

    Parameters
    ----------
    opp : dreq_record
        One record from the Opportunity table
    ExptGroups : dreq_table
        Experiment Group table
    Expts : dreq_table
        Experiments table

    Returns
    -------
    Set giving names of experiments from which the Opportunity requests output.
    Example: {'historical', 'piControl'}
    '''
    # Follow links to experiment groups to find the names of requested experiments
    opp_expts = set() # list to store names of experiments requested by this Opportunity
    print('  Experiment Groups ({}):'.format(len(opp.experiment_groups)))
    for link in opp.experiment_groups:
        # expt_group = base[link.table_name].records[link.record_id]
        expt_group = ExptGroups.records[link.record_id]

        n = len(expt_group.experiments)
        print(f'    {expt_group.name}  ({n} experiments)')

        for link in expt_group.experiments:
            expt = Expts.records[link.record_id]
            # print(f'  {expt.experiment}')
            opp_expts.add(expt.experiment)
    return opp_expts

def get_opp_vars(opp, priority_levels, VarGroups, Vars, PriorityLevel=None, verbose=False):
    '''
    For one Opportunity, get its requested variables grouped by priority level.
    Input parameters are not modified.

    Parameters
    ----------
    opp : dreq_record
        One record from the Opportunity table
    priority_levels : list[str]
        Priority levels to get, example: ['High', 'Medium']
    VarGroups : dreq_table
        Variable Group table
    Vars : dreq_table
        Variables table
    PriorityLevel : dreq_table
        Required if var_group.priority_level is link to PriorityLevel table 

    Returns
    -------
    Dict giving set of variables requested at each specified priority level
    Example: {'High' : {'Amon.tas', 'day.tas'}, 'Medium' : {'day.ua'}}
    '''
    # Follow links to variable groups to find names of requested variables
    opp_vars = {p : set() for p in priority_levels}
    print('  Variable Groups ({}):'.format(len(opp.variable_groups)))
    for link in opp.variable_groups:
        var_group = VarGroups.records[link.record_id]

        priority_level = get_var_group_priority(var_group, PriorityLevel)
        if priority_level not in priority_levels:
            continue

        n = len(var_group.variables)
        print(f'    {var_group.name}  ({n} variables, {priority_level} priority)')

        for link in var_group.variables:
            var = Vars.records[link.record_id]
            var_name = get_unique_var_name(var)
            # Add this variable to the list of requested variables at the specified priority
            opp_vars[priority_level].add(var_name)
    return opp_vars

def create_dreq_table_objects(content):
    '''
    Render raw airtable export content as dreq_table objects.

    Parameters
    ----------
    content : dict
        Raw airtable export, keyed by base name:
        { base 1 name : {
            table 1 name : {...}
            table 2 name : {...}
            }
          base 2 name : ...
        }
        For further details see "Structure of the exported content" in 
        scripts/README_airtable_export.md in the content repo:
            https://github.com/CMIP-Data-Request/CMIP7_DReq_Content/
        or equivalently for release versions:
            https://github.com/CMIP-CMIP/CMIP7_DReq_Content/
    '''
    if not isinstance(content, dict):
        raise TypeError('Input should be dict from raw airtable export json file')

    # Content is dict loaded from raw airtable export json file
    content_type = get_content_type(content)
    match content_type:
        case 'working':
            base_name = 'Data Request Opportunities (Public)'
        case 'version':
            base_name = version_base_name()
    base = content[base_name]

    # Get a mapping from table id to table name
    table_id2name = {}
    for table_name, table in base.items():
        assert table['name'] == table_name
        assert table['base_name'] == base_name
        table_id2name.update({
            table['id'] : table['name']
        })
    assert len(table_id2name) == len(base)
    # Create objects representing data request tables
    for table_name, table in base.items():
        # print('Creating table object for table: ' + table_name)
        base[table_name] = dreq_table(table, table_id2name)

    # Make some adjustments that are specific to the Opportunity table
    Opps = base['Opportunity']
    Opps.rename_attr('title_of_opportunity', 'title') # rename title attribute for brevity in downstream code
    exclude_opps = set()
    for opp_id, opp in Opps.records.items():
        if not hasattr(opp, 'experiment_groups'):
            print(f' * WARNING *    no experiment groups found for Opportunity {opp.title}')
            exclude_opps.add(opp_id)
        if not hasattr(opp, 'variable_groups'):
            print(f' * WARNING *    no variable groups found for Opportunity {opp.title}')
            exclude_opps.add(opp_id)
    if len(exclude_opps) > 0:
        print('Excluding Opportunities:')
        for opp_id in exclude_opps:
            opp = Opps.records[opp_id]
            print(f'  {opp.title}')
            Opps.delete_record(opp_id)

    return base

def get_requested_variables(content, use_opps='all', max_priority='Low', verbose=True):
    '''
    Return variables requested for each experiment, as a function of opportunities supported and priority level of variables.

    Parameters
    ----------
    content : dict
        Dict containing either:
        - data request content as exported from airtable
        OR
        - dreq_table objects representing tables (dict keys are table names)
    use_opp : str or list of str/int
        Identifies the opportunities being supported. Options:
            'all' : include all available opportunities
            integers : include opportunities identified by their integer IDs
            strings : include opportunities identified by their titles
    max_priority : str
        Variables up to this priority level will be returned.
        E.g., max_priority='Low' means all priority levels (High, Medium, Low) are returned.

    Returns
    -------
    Dict keyed by experiment name, giving prioritized variables for each experiment.
    Example:
    {   'Header' : ... (Header contains info about where this request comes from)
        'experiment' : {
            'historical' :
                'High' : ['Amon.tas', 'day.tas', ...],
                'Medium' : ...
            }
            ...
        }
    }
    '''
    if isinstance(content, dict):
        if all([isinstance(table, dreq_table) for table in content.values()]):
            # tables have already been rendered as dreq_table objects
            base = content
        else:
            # render tables as dreq_table objects
            base = create_dreq_table_objects(content)
    else:
        raise TypeError('Expect dict as input')

    Opps = base['Opportunity']
    opp_ids = get_opp_id(use_opps, Opps, verbose=verbose)

    ExptGroups = base['Experiment Group']
    Expts = base['Experiments']
    VarGroups = base['Variable Group']
    Vars = base['Variables']

    all_priority_levels = ['High', 'Medium', 'Low']
    if 'Priority Level' in base:
        PriorityLevel = base['Priority Level']
        priority_levels_from_table = [rec.name for rec in PriorityLevel.records.values()]
        assert set(all_priority_levels) == set(priority_levels_from_table)
    else:
        PriorityLevel = None
    m = all_priority_levels.index(max_priority)
    priority_levels = all_priority_levels[:m+1]

    # Loop over Opportunities to get prioritized lists of variables
    request = {} # dict to hold aggregated request
    for opp_id in opp_ids:
        opp = Opps.records[opp_id] # one record from the Opportunity table
        print(f'Opportunity: {opp.title}')

        opp_expts = get_opp_expts(opp, ExptGroups, Expts, verbose=verbose)
        opp_vars = get_opp_vars(opp, priority_levels, VarGroups, Vars, PriorityLevel, verbose=verbose)

        # Aggregate this Opportunity's request into the master list of requests
        for expt_name in opp_expts:
            if expt_name not in request:
                # If we haven't encountered this experiment yet, initialize an expt_request object for it
                request[expt_name] = expt_request(expt_name)

            # Add this Opportunity's variables request to the expt_request object
            for priority_level, var_names in opp_vars.items():
                request[expt_name].add_vars(var_names, priority_level)

    request_dict = {
        'Header' : {
            'Opportunities' : use_opps,
            'dreq version' : DREQ_VERSION,
        },
        'experiment' : {},
    }
    for expt_name, expt_req in request.items():
        request_dict['experiment'].update(expt_req.to_dict())
    return request_dict



def _get_requested_variables(content, use_opp='all', max_priority='Low', verbose=True):
    '''
    ******************
    *** DEPRECATED ***
    This is an initial version of the search function that uses python dicts from the airtable export directly.
    It may be useful to keep in the module for testing, i.e. to validate other codes.
    ******************

    Return variables requested for each experiment, as a function of opportunities supported and priority level of variables.

    Parameters
    ----------
    content : dict
        Dict containing data request content exported from airtable.
    use_opp : str or list of str/int
        Identifies the opportunities being supported. Options:
            'all' : include all available opportunities
            integers : include opportunities identified by their integer IDs
            strings : include opportunities identified by their titles
    max_priority : str
        Variables up to this priority level will be returned.
        E.g., max_priority='Low' means all priority levels (High, Medium, Low) are returned.

    Returns
    -------
    Dict keyed by experiment name, giving prioritized variables for each experiment.
    Example:
    {   'Header' : ... (Header contains info about where this request comes from)
        'experiment' : {
            'historical' :
                'High' : ['Amon.tas', 'day.tas', ...],
                'Medium' : ...
            }
            ...
        }
    }
    '''

    if not isinstance(content, dict):
        raise TypeError('Input should be dict from raw airtable export json file')

    content_type = get_content_type(content)
    match content_type:
        case 'working':
            base_name = 'Data Request Opportunities (Public)'
        case 'version':
            base_name = version_base_name()

    tables = content[base_name]

    all_opps = tables['Opportunity']  # Opportunities table, specifying all defined data request opportunities

    discard_empty_opps = True
    if discard_empty_opps:
        # somehow empty opportunities are in the v1.0alpha base
        # this will cause problems below
        # discard them
        discard_opp_id = []
        for opp_id, opp in all_opps['records'].items():
            if len(opp) == 0:
                discard_opp_id.append(opp_id)
        for opp_id in discard_opp_id:
            all_opps['records'].pop(opp_id)

    if use_opp == 'all':
        # Include all opportunities
        use_opp = [opp_id for opp_id in all_opps['records']]
    elif isinstance(use_opp, list):
        if all([isinstance(m, int) for m in use_opp]):
            # Opportunity IDs have been given as input
            use_opp = [opp_id for opp_id,opp in all_opps['records'].items() if int(opp['Opportunity ID']) in use_opp]
        elif all([isinstance(s, str) for s in use_opp]):
            # Opportunity titles have been given as input
            use_opp = [opp_id for opp_id,opp in all_opps['records'].items() if opp['Title of Opportunity'] in use_opp]
    use_opp = list(set(use_opp))
    if len(use_opp) == 0:
        print('No opportunities found')
        return
    if verbose:
        n = len(use_opp)
        print(f'Finding requested variables for {n} Opportunities:')
        for opp_id in use_opp:
            opp = all_opps['records'][opp_id]
            print('  ' + opp['Title of Opportunity'])

    # Loop over the opportunities
    expt_vars = {}
    priority_levels = ['High', 'Medium', 'Low']
    for opp_id in use_opp:
        opp = all_opps['records'][opp_id] # one record from the Opportunity table

        if 'Experiment Groups' not in opp:
            print('No experiment groups defined for opportunity: ' + opp['Title of Opportunity'])
            continue
        opp_expts = set() # will hold names of experiments requested by this opportunity
        for expt_group_id in opp['Experiment Groups']:  # Loop over experiment groups in this opportunity
            expt_group = tables['Experiment Group']['records'][expt_group_id]
            # Get names of experiments in this experiment group
            for expt_id in expt_group['Experiments']:

                match content_type: # cluge, fix later
                    case 'working':
                        expt_table_name = 'Experiment'
                    case 'version':
                        expt_table_name = 'Experiments'

                expt = tables[expt_table_name]['records'][expt_id]
                expt_key = expt[' Experiment'].strip()  # Name of experiment, e.g "historical"
                opp_expts.add(expt_key)
                if expt_key not in expt_vars:
                    expt_vars[expt_key] = {p : set() for p in priority_levels}

        if 'Variable Groups' not in opp:
            print('No variable groups defined for opportunity: ' + opp['Title of Opportunity'])
            continue
        for var_group_id in opp['Variable Groups']:  # Loop over variable groups in this opportunity
            var_group = tables['Variable Group']['records'][var_group_id]
            priority = var_group['Priority Level']

            if isinstance(priority, list):  # True if priority is a link to a Priority Level record (instead of just a string)
                assert len(priority) == 1, 'Variable Group should have one specified priority level'
                prilev_id = priority[0]
                prilev = tables['Priority Level']['records'][prilev_id]
                priority = prilev['Name']
                assert priority in priority_levels, 'Unrecognized priority level: ' + priority
                del prilev

            # Get names of variables in this variable group
            for var_id in var_group['Variables']:  # Loop over variables in this variable group
                var = tables['Variables']['records'][var_id]
                var_key = var['Compound Name']  # Name of variable, e.g. "Amon.tas"
                for expt_key in opp_expts:
                    # Add this variable to the experiment's output set, at the priority level specified by the variable group
                    expt_vars[expt_key][priority].add(var_key)

    # Remove overlaps between priority levels
    for expt_key, expt_var in expt_vars.items():
        # remove from Medium priority group any variables already occuring in High priority group
        expt_var['Medium'] = expt_var['Medium'].difference(expt_var['High'])  
        # remove from Low priority group any variables already occuring in Medium or High priority groups
        expt_var['Low'] = expt_var['Low'].difference(expt_var['Medium'])
        expt_var['Low'] = expt_var['Low'].difference(expt_var['High'])

    # Remove unwanted priority levels
    for expt_key, expt_var in expt_vars.items():
        if max_priority.lower() == 'high':
            expt_var.pop('Medium')
            expt_var.pop('Low')
        elif max_priority.lower() == 'medium':
            expt_var.pop('Low')

    for expt, req in expt_vars.items():
        # Change sets to lists
        for p in req:
            req[p] = sorted(req[p], key=str.lower)

    request_dict = {
        'Header' : {
            'Opportunities' : [all_opps['records'][opp_id]['Title of Opportunity'] for opp_id in use_opp],
            'dreq version' : DREQ_VERSION,
        },
        'experiment' : expt_vars,
    }
    return request_dict

