'''
Functions to extract information from the data request.
E.g., get variables requested for each experiment.

The module has two basic sections:

1) Functions that take the data request content and convert it to python objects.
2) Functions that interrogate the data request, usually using output from (1) as their input.

'''
import os
import hashlib
import json
from collections import OrderedDict


from data_request_api.stable.query.dreq_classes import (
    dreq_table, expt_request, UNIQUE_VAR_NAME, PRIORITY_LEVELS)

# Version of data request content:
DREQ_VERSION = ''  # if a tagged version is being used, set this in calling script

# Version of software (python API):
from data_request_api import version as api_version

###############################################################################
# Functions to manage data request content input and use it to create python
# objects representing the tables.

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

        'working' : 3 bases containing the latest working version of data request content,
                    or 4 bases if the Schema table has been added to the export.

        'version' : 1 base containing the content of a tagged data request version.
    '''
    n = len(content)
    if n in [3,4]:
        content_type = 'working'
    elif n == 1:
        content_type = 'version'
    else:
        raise ValueError('Unable to determine type of data request content in the exported json file')
    return content_type

def version_base_name():
    return f'Data Request {DREQ_VERSION}'

def get_priority_levels():
    '''
    Return list of all valid priority levels (str) in the data request.
    List is ordered from highest to lowest priority.
    '''
    priority_levels = [s.capitalize() for s in PRIORITY_LEVELS]

    # The priorities are specified in PRIORITY_LEVELS from dreq_classes.
    # Check here that 'Core' is highest priority.
    # The 'Core' priority represents the Baseline Climate Variables (BCVs, https://doi.org/10.5194/egusphere-2024-2363).
    # It should be highest priority unless something has been mistakenly modified in dreq_classes.py.
    # Hence this check should NEVER fail, and is done here only to be EXTRA safe.
    assert priority_levels[0] == 'Core', 'error in PRIORITY_LEVELS: highest priority should be Core (BCVs)'
    
    return priority_levels

def get_table_id2name(base, base_name):
    '''
    Get a mapping from table id to table name
    '''
    table_id2name = {}
    for table_name, table in base.items():
        # assert table['name'] == table_name
        # assert table['base_name'] == base_name, table['base_name'] + ', ' + base_name
        table_id2name.update({
            table['id'] : table['name']
        })
    assert len(table_id2name) == len(base), 'table ids are not unique!'
    return table_id2name

def create_dreq_tables_for_request(content, consolidated=True):
    '''
    For the "request" part of the data request content (Opportunities, Variable Groups, etc),
    render raw airtable export content as dreq_table objects.
    
    For the "data" part of the data request, the corresponding function is create_dreq_tables_for_variables().

    Parameters
    ----------
    content : dict
        Raw airtable export. Dict is keyed by base name, for example:
        {'Data Request Opportunities (Public)' : {
            'Opportunity' : {...},
            ...
            },
         'Data Request Variables (Public)' : {
            'Variables' : {...}
            ...
            }
        }

    Returns
    -------
    Dict whose keys are table names and values are dreq_table objects.
    (The base name from the input 'content' dict no longer appears.)
    '''
    if not isinstance(content, dict):
        raise TypeError('Input should be dict from raw airtable export json file')

    # Content is dict loaded from raw airtable export json file
    if consolidated:
        base_name = 'Data Request'
        content_type = 'consolidated'
    else:
        # for backward compatibility
        content_type = get_content_type(content)
        if content_type == 'working':
            base_name = 'Data Request Opportunities (Public)'
        elif content_type == 'version':
            base_name = version_base_name()
        else:
            raise ValueError('Unknown content type: ' + content_type)
    # base_name = 'Data Request'
    base = content[base_name]

    # Create objects representing data request tables
    table_id2name = get_table_id2name(base, base_name)
    for table_name, table in base.items():
        # print('Creating table object for table: ' + table_name)
        base[table_name] = dreq_table(table, table_id2name)

    # Change names of tables if needed 
    # (insulates downstream code from upstream name changes that don't affect functionality)
    change_table_names = {}
    if content_type == 'working':
        change_table_names = {
            # old name : new name
            'Experiment' : 'Experiments',
            'Priority level' : 'Priority Level'
        }
    for old,new in change_table_names.items():
        assert new not in base, 'New table name already exists: ' + new
        if old not in base:
            # print(f'Unavailable table {old}, skipping name change')
            continue
        base[new] = base[old]
        base.pop(old)

    # Make some adjustments that are specific to the Opportunity table
    Opps = base['Opportunity']
    Opps.rename_attr('title_of_opportunity', 'title') # rename title attribute for brevity in downstream code
    for opp in Opps.records.values():
        opp.title = opp.title.strip()
    if content_type == 'working':
        if 'variable_groups' not in Opps.attr2field:
            # Try alternate names for the latest variable groups
            try_vg_attr = []
            try_vg_attr.append('working_updated_variable_groups') # takes precendence over originally requested groups
            try_vg_attr.append('originally_requested_variable_groups')
            for vg_attr in try_vg_attr:
                if vg_attr in Opps.attr2field:
                    Opps.rename_attr(vg_attr, 'variable_groups')
                    break
            assert 'variable_groups' in Opps.attr2field, f'unable to determine variable groups attribute for opportunity: {opp.title}'
    exclude_opps = set()
    for opp_id, opp in Opps.records.items():
        if not hasattr(opp, 'experiment_groups'):
            print(f' * WARNING *    no experiment groups found for Opportunity: {opp.title}')
            exclude_opps.add(opp_id)
        if not hasattr(opp, 'variable_groups'):
            print(f' * WARNING *    no variable groups found for Opportunity: {opp.title}')
            exclude_opps.add(opp_id)
    if len(exclude_opps) > 0:
        print('Quality control check is excluding these Opportunities:')
        for opp_id in exclude_opps:
            opp = Opps.records[opp_id]
            print(f'  {opp.title}')
            Opps.delete_record(opp_id)
        print()
    if len(Opps.records) == 0:
        # If there are no opportunities left, there's no point in continuing!
        # This check is here because if something changes upstream in Airtable, it might cause
        # the above code to erroneously remove all opportunities.
        raise Exception(' * ERROR *    All Opportunities were removed!')

    return base

def create_dreq_tables_for_variables(content, consolidated=True):
    '''
    For the "data" part of the data request content (Variables, Cell Methods etc),
    render raw airtable export content as dreq_table objects.

    For the "request" part of the data request, the corresponding function is create_dreq_tables_for_request().

    '''
    if not isinstance(content, dict):
        raise TypeError('Input should be dict from raw airtable export json file')

    # Content is dict loaded from raw airtable export json file
    if consolidated:
        base_name = 'Data Request'
        content_type = 'consolidated'
    else:
        # for backward compatibility
        content_type = get_content_type(content)
        if content_type == 'working':
            base_name = 'Data Request Variables (Public)'
        elif content_type == 'version':
            base_name = version_base_name()
        else:
            raise ValueError('Unknown content type: ' + content_type)
    base = content[base_name]

    # Create objects representing data request tables
    table_id2name = get_table_id2name(base, base_name)
    for table_name, table in base.items():
        # print('Creating table object for table: ' + table_name)
        base[table_name] = dreq_table(table, table_id2name)

    # Change names of tables if needed 
    # (insulates downstream code from upstream name changes that don't affect functionality)
    change_table_names = {}
    if content_type == 'working':
        change_table_names = {
            # old name : new name
            'Variable' : 'Variables',
            'Coordinate or Dimension' : 'Coordinates and Dimensions',
            'Physical Parameter' : 'Physical Parameters',
        }
    for old,new in change_table_names.items():
        assert new not in base, 'New table name already exists: ' + new
        base[new] = base[old]
        base.pop(old)

    return base

def _create_dreq_table_objects(content, working_base='Opportunities'):
    '''
    ******************
    *** DEPRECATED ***
    Replaced by two functions:
        create_dreq_tables_for_request()
        create_dreq_tables_for_variables()
    ******************

    
    Render raw airtable export content as dreq_table objects.

    The exported content (input dict 'content') has a slightly different
    structure depending on the content type, determined here by:
        get_content_type(content)
    If any finicky details need to be adjusted based on the content type,
    this function handles them. For example, if the experiments table is
    named "Experiments" in a versioned release but is named "Experiment"
    in the 'working' content type. Ideally there would be no such differences,
    but sometimes they happen. They are resolved here, insulating
    downstream code from having to deal with them. That is, downstream code
    should be independent of the content type.
    
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

    working_base : str
        If content dict has more than one base, as for the "working version",
        this specifies which one to convert and return.

    Returns
    -------
    base : dict
        Dict keys are table names, values are dreq_table objects.
    '''
    if not isinstance(content, dict):
        raise TypeError('Input should be dict from raw airtable export json file')

    # Content is dict loaded from raw airtable export json file
    content_type = get_content_type(content)

    if content_type == 'working':
        if working_base == 'Opportunities':
            base_name = 'Data Request Opportunities (Public)'
        elif working_base == 'Variables':
            base_name = 'Data Request Variables (Public)'
        else:
            raise ValueError('Which working base to use? Unknown type: ' + working_base)
    elif content_type == 'version':
        base_name = version_base_name()
    else:
        raise ValueError('Unknown content type: ' + content_type)
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

    if 'Opportunity' in base and working_base == 'Opportunities':
        # Make some adjustments that are specific to the Opportunity table
        Opps = base['Opportunity']
        Opps.rename_attr('title_of_opportunity', 'title') # rename title attribute for brevity in downstream code
        if content_type == 'working':
            if 'variable_groups' not in Opps.attr2field:
                if 'originally_requested_variable_groups' in Opps.attr2field:
                    Opps.rename_attr('originally_requested_variable_groups', 'variable_groups')
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
        if len(Opps.records) == 0:
            # If there are no opportunities left, there's no point in continuing!
            # This check is here because if something changes upstream in Airtable, it might cause
            # the above code to erroneously remove all opportunities.
            raise Exception(' * ERROR *    All Opportunities were removed!')

    # Other adjustments
    if content_type == 'working':

        if working_base == 'Opportunities':
            change_table_names = {
                # old name : new name
                'Experiment' : 'Experiments',
            }

            # if 'Experiments' not in base:
            #     # Unfortunately the 'working' bases have a different table name for experiments
            #     # than the official releases (as of Oct 2024)
            #     base['Experiments'] = base['Experiment']
            #     base.pop('Experiment')
            # assert 'Experiment' not in base

        elif working_base == 'Variables':
            change_table_names = {
                # old name : new name
                'Variable' : 'Variables',
                'Coordinate or Dimension' : 'Coordinates and Dimensions',
                'Physical Parameter' : 'Physical Parameters',
            }

            # if 'Variables' not in base:
            #     base['Variables'] = base['Variable']
            #     base.pop('Variable')
            # assert 'Variable' not in base

        for old,new in change_table_names.items():
            assert new not in base, 'New table name already exists: ' + new
            base[new] = base[old]
            base.pop(old)

    return base

###############################################################################
# Functions to interrogate the data request, e.g. get variables requested for
# each experiment.

def get_opp_ids(use_opps, Opps, verbose=False, quality_control=True):
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
        use_opps = sorted(set(use_opps))
        if all([isinstance(s, str) for s in use_opps]):
            # opp_ids = [opp_id for opp_id,opp in records.items() if opp.title in use_opps]
            title2id = {opp.title : opp_id for opp_id,opp in records.items()}
            assert len(records) == len(title2id), 'Opportunity titles are not unique'
            for title in use_opps:
                if title in title2id:
                    opp_ids.append(title2id[title])
                else:
                    # print(f'\n* WARNING *    Opportunity not found: {title}\n')
                    raise Exception(f'\n* ERROR *    The specified Opportunity is not found: {title}\n')

    assert len(set(opp_ids)) == len(opp_ids), 'found repeated opportunity ids'

    if quality_control:
        valid_opp_status = ['Accepted', 'Under review']
        discard_opp_id = set()
        for opp_id in opp_ids:
            opp = Opps.get_record(opp_id)
            # print(opp)
            # if len(opp) == 0:
            #     # discard empty opportunities
            #     discard_opp_id.add(opp_id)
            if hasattr(opp, 'status') and opp.status not in valid_opp_status:
                discard_opp_id.add(opp_id)
        for opp_id in discard_opp_id:
            Opps.delete_record(opp_id)
            opp_ids.remove(opp_id)
        del discard_opp_id

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
    str that states the priority level, e.g. "High"
    '''
    if not hasattr(var_group, 'priority_level'):
        return 'Undefined'

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
    if UNIQUE_VAR_NAME == 'compound name':
        return var.compound_name
    else:
        raise ValueError('Unknown identifier for UNIQUE_VAR_NAME: ' + UNIQUE_VAR_NAME + 
                         '\nHow should the unique variable name be determined?')

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
    if verbose:
        print('  Experiment Groups ({}):'.format(len(opp.experiment_groups)))
    for link in opp.experiment_groups:
        # expt_group = base[link.table_name].records[link.record_id]
        expt_group = ExptGroups.records[link.record_id]

        if not hasattr(expt_group, 'experiments'):
            continue

        if verbose:
            print(f'    {expt_group.name}  ({len(expt_group.experiments)} experiments)')

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
    if verbose:
        print('  Variable Groups ({}):'.format(len(opp.variable_groups)))
    for link in opp.variable_groups:
        var_group = VarGroups.records[link.record_id]

        priority_level = get_var_group_priority(var_group, PriorityLevel)
        if priority_level not in priority_levels:
            continue

        if verbose:
            print(f'    {var_group.name}  ({len(var_group.variables)} variables, {priority_level} priority)')

        for link in var_group.variables:
            var = Vars.records[link.record_id]
            var_name = get_unique_var_name(var)
            # Add this variable to the list of requested variables at the specified priority
            opp_vars[priority_level].add(var_name)
    return opp_vars



def get_requested_variables(content, use_opps='all', priority_cutoff='Low', verbose=True, consolidated=True, check_core_variables=True):
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
    priority_cutoff : str
        Only return variables of equal or higher priority level than priority_cutoff.
        E.g., priority_cutoff='Low' means all priority levels are returned.
    check_core_variables : bool
        True ==> check that all experiments contain a non-empty list of Core variables,
        and that it's the same list for all experiments.

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
            base = create_dreq_tables_for_request(content, consolidated=consolidated)
    else:
        raise TypeError('Expect dict as input')

    Opps = base['Opportunity']
    opp_ids = get_opp_ids(use_opps, Opps, verbose=verbose)

    ExptGroups = base['Experiment Group']
    Expts = base['Experiments']
    VarGroups = base['Variable Group']
    Vars = base['Variables']

    # all_priority_levels = ['Core', 'High', 'Medium', 'Low']
    # all_priority_levels = [s.capitalize() for s in PRIORITY_LEVELS]
    all_priority_levels = get_priority_levels()

    if 'Priority Level' in base:
        PriorityLevel = base['Priority Level']
        priority_levels_from_table = [rec.name for rec in PriorityLevel.records.values()]
        assert set(all_priority_levels) == set(priority_levels_from_table), \
            'inconsistent priority levels:\n  ' + str(all_priority_levels) + '\n  ' + str(priority_levels_from_table)
    else:
        PriorityLevel = None
    priority_cutoff = priority_cutoff.capitalize()
    if priority_cutoff not in all_priority_levels:
        raise ValueError('Invalid priority level cutoff: ' + priority_cutoff + '\nCould not determine priority levels to include.')
    m = all_priority_levels.index(priority_cutoff)
    priority_levels = all_priority_levels[:m+1]
    del priority_cutoff

    # Loop over Opportunities to get prioritized lists of variables
    request = {} # dict to hold aggregated request
    for opp_id in opp_ids:
        opp = Opps.records[opp_id] # one record from the Opportunity table

        if verbose:
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

    opp_titles = sorted([Opps.get_record(opp_id).title for opp_id in opp_ids])
    requested_vars = {
        'Header' : {
            'Opportunities' : opp_titles,
            'dreq version' : DREQ_VERSION,
        },
        'experiment' : {},
    }
    for expt_name, expt_req in request.items():
        requested_vars['experiment'].update(expt_req.to_dict())

    if check_core_variables:
        # Confirm that 'Core' priority level variables are included, and identical for each experiment.
        # The setting of priority_levels list, above, should guarantee this.
        # Putting this extra check here just to be extra sure.
        core_vars = set()
        for expt_name, expt_req in requested_vars['experiment'].items():
            assert 'Core' in expt_req, 'Missing Core variables for experiment: ' + expt_name
            vars = set(expt_req['Core'])
            assert len(vars) > 0, 'Empty Core variables list for experiment: ' + expt_name
            if len(core_vars) == 0:
                core_vars = vars
            assert vars == core_vars, 'Inconsistent Core variables for experiment: ' + expt_name
 
    return requested_vars



def _get_requested_variables(content, use_opp='all', priority_cutoff='Low', verbose=True):
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
    priority_cutoff : str
        Only return variables of equal or higher priority level than priority_cutoff.
        E.g., priority_cutoff='Low' means all priority levels are returned.

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
    if content_type == 'working':
        base_name = 'Data Request Opportunities (Public)'
    elif content_type == 'version':
        base_name = version_base_name()

    tables = content[base_name]

    all_opps = tables['Opportunity']  # Opportunities table, specifying all defined data request opportunities

    filter_opps = True
    if filter_opps:
        # somehow empty opportunities are in the v1.0alpha base
        # this will cause problems below
        # discard them
        discard_opp_id = set()
        for opp_id, opp in all_opps['records'].items():
            if len(opp) == 0:
                # discard empty opportunities
                discard_opp_id.add(opp_id)
            if 'Status' in opp and opp['Status'] not in ['Accepted', 'Under review']:
                discard_opp_id.add(opp_id)
        for opp_id in discard_opp_id:
            all_opps['records'].pop(opp_id)
        del discard_opp_id

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
    priority_levels = get_priority_levels()
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

                # cluge
                if content_type == 'working':
                    expt_table_name = 'Experiment'
                elif content_type == 'version':
                    expt_table_name = 'Experiments'

                expt = tables[expt_table_name]['records'][expt_id]
                expt_key = expt[' Experiment'].strip()  # Name of experiment, e.g "historical"
                opp_expts.add(expt_key)
                if expt_key not in expt_vars:
                    expt_vars[expt_key] = {p : set() for p in priority_levels}

        try_vg_fields = []
        try_vg_fields.append('Variable Groups')
        try_vg_fields.append('Working/Updated Variable Groups')
        try_vg_fields.append('Originally Requested Variable Groups')
        vg_key = None
        for vg_key in try_vg_fields:
            if vg_key in opp:
                break
        if vg_key not in opp:
            print('No variable groups defined for opportunity: ' + opp['Title of Opportunity'])
            continue
        for var_group_id in opp[vg_key]:  # Loop over variable groups in this opportunity
            var_group = tables['Variable Group']['records'][var_group_id]
            priority = var_group['Priority Level']

            if isinstance(priority, list):  # True if priority is a link to a Priority Level record (instead of just a string)
                assert len(priority) == 1, 'Variable Group should have one specified priority level'
                prilev_id = priority[0]
                
                # prilev = tables['Priority Level']['records'][prilev_id]
                # cluge for testing with latest working bases
                pl_table = None
                pl_try = ['Priority Level', 'Priority level']
                for s in pl_try:
                    if s in tables:
                        pl_table = tables[s]
                        break
                prilev = pl_table['records'][prilev_id]
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
    assert priority_levels == ['Core', 'High', 'Medium', 'Low']
    for expt_key, expt_var in expt_vars.items():
        # remove any Core priority variables from other groups
        for p in ['High', 'Medium', 'Low']:
            expt_var[p] = expt_var[p].difference(expt_var['Core'])
        # remove any High priority variables from lower priority groups
        for p in ['Medium', 'Low']:
            expt_var[p] = expt_var[p].difference(expt_var['High'])
        # remove any Medium priority variables from lower priority groups
        for p in ['Low']:
            expt_var[p] = expt_var[p].difference(expt_var['Medium'])
    # Remove unwanted priority levels
    for expt_key, expt_var in expt_vars.items():
        if priority_cutoff.lower() == 'core':
            expt_var.pop('High')
            expt_var.pop('Medium')
            expt_var.pop('Low')
        elif priority_cutoff.lower() == 'high':
            expt_var.pop('Medium')
            expt_var.pop('Low')
        elif priority_cutoff.lower() == 'medium':
            expt_var.pop('Low')

    for expt, req in expt_vars.items():
        # Change sets to lists
        for p in req:
            req[p] = sorted(req[p], key=str.lower)

    opp_titles = sorted([all_opps['records'][opp_id]['Title of Opportunity'] for opp_id in use_opp])
    requested_vars = {
        'Header' : {
            'Opportunities' : opp_titles,
            'dreq version' : DREQ_VERSION,
        },
        'experiment' : expt_vars,
    }
    return requested_vars


def show_requested_vars_summary(expt_vars, use_dreq_version):
    '''
    Display quick summary to stdout of variables requested.
    expt_vars is the output dict from dq.get_requested_variables().
    '''
    print(f'\nFor data request version {use_dreq_version}, number of requested variables found by experiment:')
    priority_levels=get_priority_levels()
    for expt, req in sorted(expt_vars['experiment'].items()):
        d = {p : 0 for p in priority_levels}
        for p in priority_levels:
            if p in req:
                d[p] = len(req[p])
        n_total = sum(d.values())
        print(f'  {expt} : ' + ' ,'.join(['{p}={n}'.format(p=p,n=d[p]) for p in priority_levels]) + f', TOTAL={n_total}')


def write_requested_vars_json(outfile, expt_vars, use_dreq_version, priority_cutoff, content_path):
    '''
    Write a nicely formatted json file with lists of requested variables by experiment.
    expt_vars is the output dict from dq.get_requested_variables().
    '''

    Header = OrderedDict({
        'Description' : 'This file gives the names of output variables that are requested from CMIP experiments by the supported Opportunities. The variables requested from each experiment are listed under each experiment name, grouped according to the priority level at which they are requested. For each experiment, the prioritized list of variables was determined by compiling together all requests made by the supported Opportunities for output from that experiment.',
        'Opportunities supported' : sorted(expt_vars['Header']['Opportunities'], key=str.lower)
    })

    # List supported priority levels
    priority_levels=get_priority_levels()
    priority_cutoff = priority_cutoff.capitalize()
    m = priority_levels.index(priority_cutoff)+1
    Header.update({
        'Priority levels supported' : priority_levels[:m]
    })
    for req in expt_vars['experiment'].values():
        for p in priority_levels[m:]:
            assert req[p] == []
            req.pop(p) # remove empty lists of unsupported priorities from the output

    # List included experiments
    Header.update({
        'Experiments included' : sorted(expt_vars['experiment'].keys(), key=str.lower)
    })

    # Get provenance of content to include in the Header
    # content_path = dc._dreq_content_loaded['json_path']
    with open(content_path, 'rb') as f:
        content_hash = hashlib.sha256(f.read()).hexdigest()
    Header.update({
        'dreq content version' : use_dreq_version,
        'dreq content file' : os.path.basename(os.path.normpath(content_path)),
        'dreq content sha256 hash' : content_hash,
        'dreq api version' : api_version,
    })

    out = {
        'Header' : Header,
        'experiment' : OrderedDict(),
    }
    expt_names = sorted(expt_vars['experiment'].keys(), key=str.lower)
    for expt_name in expt_names:
        out['experiment'][expt_name] = OrderedDict()
        req = expt_vars['experiment'][expt_name]
        for p in priority_levels:
            if p in req:
                out['experiment'][expt_name][p] = req[p]

    # Write the results to json
    with open(outfile, 'w') as f:
        # json.dump(expt_vars, f, indent=4, sort_keys=True)
        json.dump(out, f, indent=4)
        print('\nWrote requested variables to ' + outfile)
