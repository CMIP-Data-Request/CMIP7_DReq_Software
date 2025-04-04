'''
Functions to extract information from the data request.
E.g., get variables requested for each experiment.

The module has two basic sections:

1) Functions that take the data request content and convert it to python objects.
2) Functions that interrogate the data request, usually using output from (1) as their input.

'''
import hashlib
import json
import os
from collections import OrderedDict

from data_request_api.stable.query.dreq_classes import (
    DreqTable, ExptRequest, UNIQUE_VAR_NAME, PRIORITY_LEVELS, format_attribute_name)
from data_request_api.stable.utilities.tools import write_csv_output_file_content

# Version of software (python API):
from data_request_api import version as api_version

# Version of data request content:
DREQ_VERSION = ''  # if a tagged version is being used, set this in calling script

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


def get_table_id2name(base):
    '''
    Get a mapping from table id to table name
    '''
    table_id2name = {}
    for table in base.values():
        table_id2name.update({
            table['id'] : table['name']
        })
    assert len(table_id2name) == len(base), 'table ids are not unique!'
    return table_id2name


def create_dreq_tables_for_request(content, consolidated=True):
    '''
    For the "request" part of the data request content (Opportunities, Variable Groups, etc),
    render raw airtable export content as DreqTable objects.
    
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
    Dict whose keys are table names and values are DreqTable objects.
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
    table_id2name = get_table_id2name(base)
    for table_name, table in base.items():
        # print('Creating table object for table: ' + table_name)
        base[table_name] = DreqTable(table, table_id2name)

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
    dreq_opps = base['Opportunity']
    dreq_opps.rename_attr('title_of_opportunity', 'title') # rename title attribute for brevity in downstream code
    for opp in dreq_opps.records.values():
        opp.title = opp.title.strip()
    if content_type == 'working':
        if 'variable_groups' not in dreq_opps.attr2field:
            # Try alternate names for the latest variable groups
            try_vg_attr = []
            try_vg_attr.append('working_updated_variable_groups') # takes precendence over originally requested groups
            try_vg_attr.append('originally_requested_variable_groups')
            for vg_attr in try_vg_attr:
                if vg_attr in dreq_opps.attr2field:
                    dreq_opps.rename_attr(vg_attr, 'variable_groups')
                    break
            assert 'variable_groups' in dreq_opps.attr2field, f'unable to determine variable groups attribute for opportunity: {opp.title}'
    exclude_opps = set()
    for opp_id, opp in dreq_opps.records.items():
        if not hasattr(opp, 'experiment_groups'):
            print(f' * WARNING *    no experiment groups found for Opportunity: {opp.title}')
            exclude_opps.add(opp_id)
        if not hasattr(opp, 'variable_groups'):
            print(f' * WARNING *    no variable groups found for Opportunity: {opp.title}')
            exclude_opps.add(opp_id)
    if len(exclude_opps) > 0:
        print('Quality control check is excluding these Opportunities:')
        for opp_id in exclude_opps:
            opp = dreq_opps.records[opp_id]
            print(f'  {opp.title}')
            dreq_opps.delete_record(opp_id)
        print()
    if len(dreq_opps.records) == 0:
        # If there are no opportunities left, there's no point in continuing!
        # This check is here because if something changes upstream in Airtable, it might cause
        # the above code to erroneously remove all opportunities.
        raise Exception(' * ERROR *    All Opportunities were removed!')

    # Determine which compound name to use based on dreq content version
    USE_COMPOUND_NAME = 'compound_name'
    version = tuple(map(int, DREQ_VERSION.strip('v').split('.')))  # e.g. 'v1.2' --> (1,2)
    if version[:2] >= (1,2):
        USE_COMPOUND_NAME = 'cmip6_compound_name'
    if USE_COMPOUND_NAME != 'compound_name':
        table_name = 'Variables'
        for rec in base[table_name].records.values():
            if hasattr(rec, 'compound_name'):
                raise Exception(f'compound_name attribute is already defined for table "{table_name}"')
            rec.compound_name = getattr(rec, USE_COMPOUND_NAME)

    return base


def create_dreq_tables_for_variables(content, consolidated=True):
    '''
    For the "data" part of the data request content (Variables, Cell Methods etc),
    render raw airtable export content as DreqTable objects.

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
    table_id2name = get_table_id2name(base)
    for table_name, table in base.items():
        # print('Creating table object for table: ' + table_name)
        base[table_name] = DreqTable(table, table_id2name)

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

###############################################################################
# Functions to interrogate the data request, e.g. get variables requested for
# each experiment.

def get_opp_ids(use_opps, dreq_opps, verbose=False, quality_control=True):
    '''
    Return list of unique opportunity identifiers.

    Parameters
    ----------
    use_opps : str or list
        "all" : return all available ids
        list of str : return ids for with the listed opportunity titles
    dreq_opps : DreqTable
        table object representing the opportunities table
    '''
    opp_ids = []
    records = dreq_opps.records
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
            opp = dreq_opps.get_record(opp_id)
            # print(opp)
            # if len(opp) == 0:
            #     # discard empty opportunities
            #     discard_opp_id.add(opp_id)
            if hasattr(opp, 'status') and opp.status not in valid_opp_status:
                discard_opp_id.add(opp_id)
        for opp_id in discard_opp_id:
            dreq_opps.delete_record(opp_id)
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


def get_var_group_priority(var_group, dreq_priorities=None):
    '''
    Returns string stating the priorty level of variable group.

    Parameters
    ----------
    var_group : DreqRecord
        Object representing a variable group
        Its "priority_level" attribute specifies the priority as either string or link to dreq_priorities table 
    dreq_priorities : DreqTable
        Required if var_group.priority_level is link to dreq_priorities table 

    Returns
    -------
    str that states the priority level, e.g. "High"
    '''
    if not hasattr(var_group, 'priority_level'):
        return 'Undefined'

    if isinstance(var_group.priority_level, list):
        assert len(var_group.priority_level) == 1, 'Variable group should have one specified priority level'
        link = var_group.priority_level[0]
        assert isinstance(dreq_priorities, DreqTable)
        rec = dreq_priorities.records[link.record_id]
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
    var : DreqRecord
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


def get_opp_expts(opp, expt_groups, expts, verbose=False):
    '''
    For one Opportunity, get its requested experiments.
    Input parameters are not modified.

    Parameters
    ----------
    opp : DreqRecord
        One record from the Opportunity table
    expt_groups : DreqTable
        Experiment Group table
    expts : DreqTable
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
        expt_group = expt_groups.records[link.record_id]

        if not hasattr(expt_group, 'experiments'):
            continue

        if verbose:
            print(f'    {expt_group.name}  ({len(expt_group.experiments)} experiments)')

        for link in expt_group.experiments:
            expt = expts.records[link.record_id]
            opp_expts.add(expt.experiment)
    return opp_expts


def get_opp_vars(opp, priority_levels, var_groups, dreq_vars, dreq_priorities=None, verbose=False):
    '''
    For one Opportunity, get its requested variables grouped by priority level.
    Input parameters are not modified.

    Parameters
    ----------
    opp : DreqRecord
        One record from the Opportunity table
    priority_levels : list[str]
        Priority levels to get, example: ['High', 'Medium']
    var_groups : DreqTable
        Variable Group table
    dreq_vars : DreqTable
        Variables table
    dreq_priorities : DreqTable
        Required if var_group.priority_level is link to dreq_priorities table 

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
        var_group = var_groups.records[link.record_id]

        priority_level = get_var_group_priority(var_group, dreq_priorities)
        if priority_level not in priority_levels:
            continue

        if verbose:
            print(f'    {var_group.name}  ({len(var_group.variables)} variables, {priority_level} priority)')

        for link in var_group.variables:
            var = dreq_vars.records[link.record_id]
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
        - DreqTable objects representing tables (dict keys are table names)
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
        if all([isinstance(table, DreqTable) for table in content.values()]):
            # tables have already been rendered as DreqTable objects
            base = content
        else:
            # render tables as DreqTable objects
            base = create_dreq_tables_for_request(content, consolidated=consolidated)
    else:
        raise TypeError('Expect dict as input')

    dreq_tables = {
        'opps' : base['Opportunity'],
        'expt groups' : base['Experiment Group'],
        'expts' : base['Experiments'],
        'var groups' : base['Variable Group'],
        'vars' : base['Variables']
    }
    opp_ids = get_opp_ids(use_opps, dreq_tables['opps'], verbose=verbose)

    # all_priority_levels = ['Core', 'High', 'Medium', 'Low']
    # all_priority_levels = [s.capitalize() for s in PRIORITY_LEVELS]
    all_priority_levels = get_priority_levels()

    if 'Priority Level' in base:
        dreq_tables['priority level'] = base['Priority Level']
        priority_levels_from_table = [rec.name for rec in dreq_tables['priority level'].records.values()]
        assert set(all_priority_levels) == set(priority_levels_from_table), \
            'inconsistent priority levels:\n  ' + str(all_priority_levels) + '\n  ' + str(priority_levels_from_table)
    else:
        dreq_tables['priority level'] = None
    priority_cutoff = priority_cutoff.capitalize()
    if priority_cutoff not in all_priority_levels:
        raise ValueError('Invalid priority level cutoff: ' + priority_cutoff + '\nCould not determine priority levels to include.')
    m = all_priority_levels.index(priority_cutoff)
    priority_levels = all_priority_levels[:m+1]
    del priority_cutoff

    # Loop over Opportunities to get prioritized lists of variables
    request = {} # dict to hold aggregated request
    for opp_id in opp_ids:
        opp = dreq_tables['opps'].records[opp_id] # one record from the Opportunity table

        if verbose:
            print(f'Opportunity: {opp.title}')

        opp_expts = get_opp_expts(opp, 
                                  dreq_tables['expt groups'], 
                                  dreq_tables['expts'], 
                                  verbose=verbose)
        
        opp_vars = get_opp_vars(opp, 
                                priority_levels, 
                                dreq_tables['var groups'], 
                                dreq_tables['vars'], 
                                dreq_tables['priority level'], 
                                verbose=verbose)

        # Aggregate this Opportunity's request into the master list of requests
        for expt_name in opp_expts:
            if expt_name not in request:
                # If we haven't encountered this experiment yet, initialize an ExptRequest object for it
                request[expt_name] = ExptRequest(expt_name)

            # Add this Opportunity's variables request to the ExptRequest object
            for priority_level, var_names in opp_vars.items():
                request[expt_name].add_vars(var_names, priority_level)

    opp_titles = sorted([dreq_tables['opps'].get_record(opp_id).title for opp_id in opp_ids])
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
            if len(vars) == 0:
                msg = 'Empty Core variables list for experiment: ' + expt_name
                raise ValueError(msg)

            if len(core_vars) == 0:
                core_vars = vars

            if vars != core_vars:
                msg = 'Inconsistent Core variables for experiment: ' + expt_name + \
                    f'\n{len(core_vars)} {len(vars)} {len(core_vars.intersection(vars))}'
                raise ValueError(msg)

    return requested_vars


def get_variables_metadata(content, compound_names=None, cmor_tables=None, cmor_variables=None, consolidated=True, use_dreq_version=None):
    '''
    Get metadata for CMOR variables (dimensions, cell_methods, out_name, ...).

    Parameters:
    -----------
    content : dict
        Dict containing either:
        - data request content as exported from airtable
        OR
        - DreqTable objects representing tables (dict keys are table names)
    compound_names : list[str]
        Compound names of variables to include. If not given, all are included.
        Example: ['Amon.tas', 'Omon.sos']
    cmor_tables : list[str]
        Names of CMOR tables to include. If not given, all are included.
        Example: ['Amon', 'Omon']
    cmor_variables : list[str]
        Names of CMOR variables to include. If not given, all are included.
        Here the out_name is used as the CMOR variable name.
        Example: ['tas', 'siconc']

    Returns:
    --------
    all_var_info : dict
        Dictionary indexed by unique variable name, giving metadata for each variable.
        Also includes a header giving info on provenance of the info (data request version used, etc).

    Notes:
    ------
    TO DEPRECATE: use_dreq_version as input should be removed once CMIP6 frequency issue fixed.
    '''
    if isinstance(content, dict):
        if all([isinstance(table, DreqTable) for table in content.values()]):
            # tables have already been rendered as DreqTable objects
            base = content
        else:
            # render tables as DreqTable objects
            base = create_dreq_tables_for_request(content, consolidated=consolidated)
    else:
        raise TypeError('Expect dict as input')
    
    # Some variables in these dreq versions lack a 'frequency' attribute; use the legacy CMIP6 frequency for them
    dreq_versions_substitute_cmip6_freq = ['v1.0', 'v1.1']
    if not use_dreq_version:
        raise ValueError('\n(TO DEPRECATE) use_dreq_version is required to set frequencies\n')

    # Use dict dreq_tables to store instances of the DreqTable class that are used in this function.
    # Mostly this would be the same as simply using base[table name], but in some cases there's a choice
    # of which table to use. Using dreq_tables as a mapping makes this choice explicit.
    dreq_tables = {
        'variables' : base['Variables']
    }
    # The Variables table is the master list of variables in the data request.
    # Each entry (row) is a CMOR variable, containing the variable's metadata.
    # Many of these entries are links to other tables in the database (see below).

    # Choose which table to use for freqency
    try_freq_table_name = []
    try_freq_table_name.append('Frequency') # not available in v1.0beta release export, need to use CMIP7 or CMIP6 one instead
    try_freq_table_name.append('CMIP7 Frequency')
    try_freq_table_name.append('CMIP6 Frequency (legacy)')

    found_freq = False
    for freq_table_name in try_freq_table_name:
        freq_attr_name = format_attribute_name(freq_table_name)
        if freq_attr_name not in dreq_tables['variables'].attr2field:
            continue
        if 'frequency' not in dreq_tables['variables'].attr2field:
            # code below assumes a variable's frequency is given by its "frequency" 
            dreq_tables['variables'].rename_attr(freq_attr_name, 'frequency')
        if freq_table_name in base:
            dreq_tables['frequency'] = base[freq_table_name]
        found_freq = True
        break
    if not found_freq:
        raise ValueError('Which airtable field gives the frequency?')

    # Get other tables from the database that are required to find all of a variable's metadata used by CMOR.
    dreq_tables.update({
        'spatial shape' : base['Spatial Shape'],
        'coordinates and dimensions' : base['Coordinates and Dimensions'],
        'temporal shape' : base['Temporal Shape'],
        'cell methods' : base['Cell Methods'],
        'physical parameters' : base['Physical Parameters'],
        'realm' : base['Modelling Realm'],
        'cell measures' : base['Cell Measures'],
        'CF standard name' : None,
    })
    if 'CF Standard Names' in base:
        dreq_tables['CF standard name'] = base['CF Standard Names']

    if 'Table Identifiers' in base:
        dreq_tables['CMOR tables'] = base['Table Identifiers']
        attr_table = 'table'
        attr_realm = 'modelling_realm'
    elif 'CMIP6 Table Identifiers (legacy)' in base:
        dreq_tables['CMOR tables'] = base['CMIP6 Table Identifiers (legacy)']
        attr_table = 'cmip6_table_legacy'
        attr_realm = 'modelling_realm___primary'
    else:
        raise ValueError('Which table contains CMOR table identifiers?')

    if use_dreq_version in dreq_versions_substitute_cmip6_freq:
        # needed for corrections below
        dreq_tables['CMIP6 frequency'] = base['CMIP6 Frequency (legacy)']

    # Compound names will be used to uniquely identify variables.
    # Check here that this is indeed a unique name as expected.
    var_name_map = {record.compound_name : record_id for record_id, record in dreq_tables['variables'].records.items()}
    assert len(var_name_map) == len(dreq_tables['variables'].records), 'compound names do not uniquely map to variable record ids'

    if cmor_tables:
        print('Retaining only these CMOR tables: ' + ', '.join(cmor_tables))
    if cmor_variables:
        print('Retaining only these CMOR variables: ' + ', '.join(cmor_variables))
    if compound_names:
        print('Retaining only these compound names: ' + ', '.join(compound_names))

    substitute = {
        # replacement character(s) : [characters to replace with the replacement character]
        '_' : ['\\_']
    }
    all_var_info = {}
    for var in dreq_tables['variables'].records.values():

        if compound_names:
            if var.compound_name not in compound_names:
                continue

        link_table = getattr(var, attr_table)
        if len(link_table) != 1:
            raise Exception(f'variable {var.compound_name} should have one table link, found: ' + str(link_table))
        table_id = dreq_tables['CMOR tables'].get_record(link_table[0]).name
        if cmor_tables:
            # Filter by CMOR table name
            if table_id not in cmor_tables:
                continue

        if not hasattr(var, 'frequency') and use_dreq_version in dreq_versions_substitute_cmip6_freq:
            # seems to be an error for some vars in v1.0, so instead use their CMIP6 frequency
            assert len(var.cmip6_frequency_legacy) == 1
            link = var.cmip6_frequency_legacy[0]
            var.frequency = [dreq_tables['CMIP6 frequency'].get_record(link).name]
            # print('using CMIP6 frequency for ' + var.compound_name)

        if isinstance(var.frequency[0], str):
            # retain this option for non-consolidated raw export?
            assert isinstance(var.frequency, list)
            frequency = var.frequency[0]
        else:
            link = var.frequency[0]
            freq = dreq_tables['frequency'].get_record(link)
            frequency = freq.name

        link = var.temporal_shape[0]
        temporal_shape = dreq_tables['temporal shape'].get_record(link)

        cell_methods = ''
        area_label_dd = ''
        if hasattr(var, 'cell_methods'):
            assert len(var.cell_methods) == 1
            link = var.cell_methods[0]
            cm = dreq_tables['cell methods'].get_record(link)
            cell_methods = cm.cell_methods
            if hasattr(cm, 'brand_id'):
                area_label_dd = cm.brand_id

        # get the 'Spatial Shape' record, which contains info about dimensions
        assert len(var.spatial_shape) == 1
        link = var.spatial_shape[0]
        spatial_shape = dreq_tables['spatial shape'].get_record(link)

        dims_list = []
        dims = None
        if hasattr(spatial_shape, 'dimensions'):
            for link in spatial_shape.dimensions:
                dims = dreq_tables['coordinates and dimensions'].get_record(link)
                dims_list.append(dims.name)
        dims_list.append(temporal_shape.name)
        if hasattr(var, 'coordinates'):
            for link in var.coordinates:
                coordinate = dreq_tables['coordinates and dimensions'].get_record(link)
                dims_list.append(coordinate.name)

        # Get physical parameter record and out_name
        link = var.physical_parameter[0]
        phys_param = dreq_tables['physical parameters'].get_record(link)
        out_name = phys_param.name

        if cmor_variables:
            # Filter by CMOR variable name
            if out_name not in cmor_variables:
                continue

        # Get CF standard name, if it exists
        standard_name = ''
        standard_name_proposed = ''
        if hasattr(phys_param, 'cf_standard_name'):
            if isinstance(phys_param.cf_standard_name, str):
                # retain this option for non-consolidated raw export?
                standard_name = phys_param.cf_standard_name
            else:
                link = phys_param.cf_standard_name[0]
                cfsn = dreq_tables['CF standard name'].get_record(link)
                standard_name = cfsn.name
        else:
            standard_name_proposed = phys_param.proposed_cf_standard_name

        link_realm = getattr(var, attr_realm)
        modeling_realm = [dreq_tables['realm'].get_record(link).id for link in link_realm]

        cell_measures = ''
        if hasattr(var, 'cell_measures'):
            cell_measures = [dreq_tables['cell measures'].get_record(link).name for link in var.cell_measures]

        positive = ''
        if hasattr(var, 'positive_direction'):
            positive = var.positive_direction

        comment = ''
        if hasattr(var, 'description'):
            comment = var.description

        var_info = OrderedDict()
        # Insert fields in order given by CMIP6 cmor tables (https://github.com/PCMDI/cmip6-cmor-tables)
        var_info.update({
            'frequency' : frequency,
            'modeling_realm' : ' '.join(modeling_realm),
        })
        if standard_name != '':
            var_info['standard_name'] = standard_name
        else:
            var_info['standard_name_proposed'] = standard_name_proposed
        var_info.update({
            'units' : phys_param.units,
            'cell_methods' : cell_methods,
            'cell_measures' : ' '.join(cell_measures),

            'long_name' : var.title,
            'comment' : comment,

            'dimensions' : ' '.join(dims_list),
            'out_name' : out_name,
            'type' : var.type,
            'positive' : positive,

            'spatial_shape' : spatial_shape.name,
            'temporal_shape' : temporal_shape.name,

            # 'temporalLabelDD' : temporal_shape.brand,
            # 'verticalLabelDD' : spatial_shape.vertical_label_dd,
            # 'horizontalLabelDD' : spatial_shape.hor_label_dd,
            # 'areaLabelDD' : area_label_dd,  # this comes from cell methods

            'table' : table_id,
        })
        for k,v in var_info.items():
            v = v.strip()
            for replacement in substitute:
                for s in substitute[replacement]:
                    if s in v:
                        v = v.replace(s, replacement)
            var_info[k] = v
        var_name = var.compound_name
        assert var_name not in all_var_info, 'non-unique variable name: ' + var_name
        all_var_info[var_name] = var_info

        del var_info, var_name

    # Sort the all-variables dict
    d = OrderedDict()
    for var_name in sorted(all_var_info, key=str.lower):
        d[var_name] = all_var_info[var_name]
    all_var_info = d
    del d

    return all_var_info


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

    header = OrderedDict({
        'Description' : 'This file gives the names of output variables that are requested from CMIP experiments by the supported Opportunities. The variables requested from each experiment are listed under each experiment name, grouped according to the priority level at which they are requested. For each experiment, the prioritized list of variables was determined by compiling together all requests made by the supported Opportunities for output from that experiment.',
        'Opportunities supported' : sorted(expt_vars['Header']['Opportunities'], key=str.lower)
    })

    # List supported priority levels
    priority_levels=get_priority_levels()
    priority_cutoff = priority_cutoff.capitalize()
    m = priority_levels.index(priority_cutoff)+1
    header.update({
        'Priority levels supported' : priority_levels[:m]
    })
    for req in expt_vars['experiment'].values():
        for p in priority_levels[m:]:
            assert req[p] == []
            req.pop(p) # remove empty lists of unsupported priorities from the output

    # List included experiments
    header.update({
        'Experiments included' : sorted(expt_vars['experiment'].keys(), key=str.lower)
    })

    # Get provenance of content to include in the header
    # content_path = dc._dreq_content_loaded['json_path']
    with open(content_path, 'rb') as f:
        content_hash = hashlib.sha256(f.read()).hexdigest()
    header.update({
        'dreq content version' : use_dreq_version,
        'dreq content file' : os.path.basename(os.path.normpath(content_path)),
        'dreq content sha256 hash' : content_hash,
        'dreq api version' : api_version,
    })

    out = {
        'Header' : header,
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


def write_variables_metadata(all_var_info, filepath, api_version=None, use_dreq_version=None, content_path=None):
 
    ext = os.path.splitext(filepath)[-1]

    if not api_version:
        raise ValueError(f'Must provide API version, received: {api_version}')
    if not use_dreq_version:
        raise ValueError(f'Must provide data request content version, received: {use_dreq_version}')
    if not content_path:
        raise ValueError(f'Must provide path to data request content, received: {content_path}')

    if ext == '.json':
        # Get provenance of content to include in the header
        with open(content_path, 'rb') as f:
            content_hash = hashlib.sha256(f.read()).hexdigest()

        # Create output dict
        out = OrderedDict({
            'Header' : OrderedDict({
                'Description' : 'Metadata attributes that characterize CMOR variables. Each variable is uniquely idenfied by a compound name comprised of a CMIP6-era table name and a short variable name.',
                'no. of variables' : len(all_var_info),
                'dreq content version': use_dreq_version,
                'dreq content file' : os.path.basename(os.path.normpath(content_path)),
                'dreq content sha256 hash' : content_hash,
                'dreq api version' : api_version,
            }),
            'Compound Name' : all_var_info,
        })

        # Write variables metadata to json
        with open(filepath, 'w') as f:
            json.dump(out, f, indent=4)
            print(f'Wrote {filepath} for {len(all_var_info)} variables, dreq version = {use_dreq_version}')

    elif ext == '.csv':
        # Write variables metadata to csv
        var_info = next(iter(all_var_info.values()))
        attrs = list(var_info.keys())
        columns = ['Compound Name']
        columns.append('standard_name')
        columns.append('standard_name_proposed')
        columns += [s for s in attrs if s not in columns]
        rows = [columns]  # column header line
        # Add each variable as a row
        for var_name, var_info in all_var_info.items():
            row = []
            for col in columns:
                if col == 'Compound Name':
                    val = var_name
                elif col in var_info:
                    val = var_info[col]
                else:
                    val = ''
                row.append(val)
            rows.append(row)
        write_csv_output_file_content(filepath, rows)
        n = len(all_var_info)
        print(f'Wrote {filepath} for {n} variables, dreq version = {use_dreq_version}')
