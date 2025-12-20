'''
Functions to extract information from the data request.
E.g., get variables requested for each experiment.

The module has two basic sections:

1) Functions that take the data request content and convert it to python objects
   (instances of classes defined in dreq_classes.py).

2) Functions that interrogate the data request, usually using output from (1) as their input.

'''
import hashlib
import json
import os
import re
import warnings
from collections import OrderedDict

from data_request_api.query.dreq_classes import (
    DreqTable, ExptRequest, PRIORITY_LEVELS, format_attribute_name)
from data_request_api.utilities.decorators import append_kwargs_from_config
from data_request_api.utilities.tools import write_csv_output_file_content
from data_request_api.content.utils import _parse_version

# Version of software (python API):
from data_request_api import version as api_version

###############################################################################
# Functions to manage data request content input and use it to create python
# objects representing the tables.


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
    base.pop("version", None)
    for table in base.values():
        table_id2name.update({
            table['id']: table['name']
        })
    assert len(table_id2name) == len(base), 'table ids are not unique!'
    return table_id2name


@append_kwargs_from_config
def _get_base_dict(content, dreq_version, purpose='request', **kwargs):
    '''
    Return the appropriate entry from the 'content' input dict, which is a dict
    representing the content from an airtable base.

    Parameters
    ----------
    content : dict
        Airtable export (from json file). Dict is keyed by base name, for example:
        {'Data Request Opportunities (Public)' : {
            'Opportunity' : {...},
            ...
            },
         'Data Request Variables (Public)' : {
            'Variables' : {...}
            ...
            }
        }
    dreq_version : str
        Version string identifier for Data Request Content

    Returns
    -------
    Dict 'base' whose keys are table names and values are dicts with table content.
    (The base name from the input 'content' dict no longer appears.)
    '''
    # defaults
    CONFIG = {'consolidate': True, 'export': 'release'}
    # override with input args, if given
    CONFIG.update(kwargs)
    consolidate = CONFIG['consolidate']
    export = CONFIG['export']

    if not isinstance(content, dict):
        raise TypeError('Input should be dict from airtable export json file')
    if consolidate:
        # For the consolidated export, there's only one base.
        # This is because 1) a release base is already just one base, and 2) a raw base
        # is 3 or 4 bases that have been turned into one base by the consolidation.
        base_name = 'Data Request'
        content_type = 'consolidated'
    else:
        # This is for backward compatibility, from before consolidation was available,
        # but may be useful if it's necessary to turn off the consolidation.
        content_type = export
        if content_type == 'release':
            # For the release export, there's only one base.
            base_name = f'Data Request {dreq_version}'
        elif content_type == 'raw':
            # For the raw export, there is more than one base.
            # Which one we return depends on the intention.
            if purpose == 'request':
                base_name = 'Data Request Opportunities (Public)'
            elif purpose == 'variables':
                base_name = 'Data Request Variables (Public)'
            else:
                raise ValueError(f'What kind of raw base is needed? Received: {purpose}')
        else:
            raise ValueError('Unknown content type: ' + content_type)
    base = content[base_name]
    return base, content_type


@append_kwargs_from_config
def create_dreq_tables_for_request(content, dreq_version, **kwargs):
    '''
    For the "request" part of the data request content (Opportunities, Variable Groups, etc),
    render airtable export content as DreqTable objects.

    For the "data" part of the data request, the corresponding function is create_dreq_tables_for_variables().

    Parameters
    ----------
    content : dict
        Airtable export (from json file). Dict is keyed by base name, for example:
        {'Data Request Opportunities (Public)' : {
            'Opportunity' : {...},
            ...
            },
         'Data Request Variables (Public)' : {
            'Variables' : {...}
            ...
            }
        }
    dreq_version : str
        Version string identifier for Data Request Content

    Returns
    -------
    Dict 'base' whose keys are table names and values are DreqTable objects.
    '''
    base, content_type = _get_base_dict(content, dreq_version, purpose='request')
    # base, content_type = _get_base_dict(content, dreq_version)

    # Config defaults
    CONFIG = {'consolidate': True}
    # Override with input args, if given
    CONFIG.update(kwargs)
    # consolidate = CONFIG['consolidate']

    # Create objects representing data request tables
    table_id2name = get_table_id2name(base)
    for table_name, table in base.items():
        # print('Creating table object for table: ' + table_name)
        base[table_name] = DreqTable(table, table_id2name)

    # Change names of tables if needed
    # (insulates downstream code from upstream name changes that don't affect functionality)
    change_table_names = {}
    if content_type == 'raw':
        change_table_names = {
            # old name : new name
            'Experiment': 'Experiments',
            'Priority level': 'Priority Level'
        }
    for old, new in change_table_names.items():
        assert new not in base, 'New table name already exists: ' + new
        if old not in base:
            # print(f'Unavailable table {old}, skipping name change')
            continue
        base[new] = base[old]
        base.pop(old)

    # Make some adjustments that are specific to the Opportunity table
    dreq_opps = base['Opportunity']
    dreq_opps.rename_attr('title_of_opportunity', 'title')  # rename title attribute for brevity in downstream code
    for opp in dreq_opps.records.values():
        opp.title = opp.title.strip()
    if content_type == 'raw':
        if 'variable_groups' not in dreq_opps.attr2field:
            # Try alternate names for the latest variable groups
            try_vg_attr = []
            try_vg_attr.append('working_updated_variable_groups')  # takes precendence over originally requested groups
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

    return base


def create_dreq_tables_for_variables(content, dreq_version):
    '''
    For the "data" part of the data request content (Variables, Cell Methods etc),
    render airtable export content as DreqTable objects.

    For the "request" part of the data request, the corresponding function is create_dreq_tables_for_request().

    '''
    base, content_type = _get_base_dict(content, dreq_version, purpose='variables')

    # Create objects representing data request tables
    table_id2name = get_table_id2name(base)
    for table_name, table in base.items():
        # print('Creating table object for table: ' + table_name)
        base[table_name] = DreqTable(table, table_id2name)

    # Change names of tables if needed
    # (insulates downstream code from upstream name changes that don't affect functionality)
    change_table_names = {}
    if content_type == 'raw':
        change_table_names = {
            # old name : new name
            'Variable': 'Variables',
            'Coordinate or Dimension': 'Coordinates and Dimensions',
            'Physical Parameter': 'Physical Parameters',
        }
    for old, new in change_table_names.items():
        assert new not in base, 'New table name already exists: ' + new
        base[new] = base[old]
        base.pop(old)

    return base

###############################################################################
# Functions to query the data request, e.g. get variables requested for each experiment.


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
            title2id = {opp.title: opp_id for opp_id, opp in records.items()}
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


@append_kwargs_from_config
def use_unique_var_name(**kwargs):
    '''
    Return parameter name to use to uniquely identify requested variables.
    This is a user configuration setting.
    '''
    return format_attribute_name(kwargs['variable_name'])


def get_unique_var_name(var):
    '''
    Return name that uniquely identifies a variable.
    This function should be called whenever a unique variable name is used in the code,
    so that the choice of name is consistently controlled in one place.

    Parameters
    ----------
    var : DreqRecord
        Object representing a variable

    Returns
    -------
    str that uniquely identifes a variable in the data request
    '''
    var_name_param = use_unique_var_name()

    if not hasattr(var, var_name_param):
        raise ValueError(f'Unrecognized unique variable identifier: {var_name_param}'
                         + '\nSet "variable_name" in API configuration')

    var_name = getattr(var, var_name_param)
    return var_name


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
    opp_expts = set()  # list to store names of experiments requested by this Opportunity
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
    opp_vars = {p: set() for p in priority_levels}
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


def get_opp_time_subsets(opp, ts, verbose=False):
    """
    For one opportunity, get its requested time subsets.

    Parameters
    ----------
    opp : DreqRecord
        One record from the Opportunity table
    ts : DreqTable
        Time Subsets table

    Returns
    -------
    List
        List of time subsets requested by the given opportunity
    """
    subsets = dict()
    ts_ids = list()

    if hasattr(opp, "time_subsets"):
        ts_ids = opp.time_subsets
    elif hasattr(opp, "time_subset"):
        ts_ids = opp.time_subset

    for ts_id in ts_ids:
        subsets[ts.get_record(ts_id).label] = ts.get_record(ts_id)

    if not subsets or "all" in subsets:
        subsets = {"all": "Whole time series"}

    if verbose:
        print(f'  Time Subsets ({len(subsets)}):')
        for subset, record in subsets.items():
            if subset == "all":
                print(f'    {subset} ({record})')
            else:
                print(f'    {subset} ({record.title}, {record.nyears} simulation years)')

    return subsets


def _get_base_dreq_tables(content, dreq_version, purpose='request'):
    if isinstance(content, dict):
        if all([isinstance(table, DreqTable) for table in content.values()]):
            # tables have already been rendered as DreqTable objects
            base = content
        else:
            # render tables as DreqTable objects
            if purpose == 'request':
                base = create_dreq_tables_for_request(content, dreq_version)
            # elif purpose == 'variables':  # only needed for raw export?
            #     base = create_dreq_tables_for_variables(content, dreq_version)
            else:
                raise ValueError(f'What kind of dreq tables are needed? Received: {purpose}')
    else:
        raise TypeError('Expect dict as input')
    return base


def get_requested_variables(content, dreq_version,
                            use_opps='all', priority_cutoff='Low',
                            combined_request=False, time_subsets=False,
                            verbose=True, check_core_variables=True):
    '''
    Return variables requested for each experiment, as a function of opportunities supported and priority level of variables.

    Parameters
    ----------
    content : dict
        Dict containing either:
        - data request content as exported from airtable
        OR
        - DreqTable objects representing tables (dict keys are table names)
    dreq_version : str
        Version string identifier for Data Request Content
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
    combined_request : bool
        True ==> combine requests from all experiments into a single request,
        and add it as experiment 'all_experiments'
    time_subsets : bool
        True ==> attach requested time subsets to each requested variable

    Returns
    -------
    Dict keyed by experiment name, giving prioritized variables for each experiment.
    If time_subsets is True, then also returns the time subsets for each experiment attached to each variable.
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
    Example if time_subsets is True:
    {   'Header' : ... (Header contains info about where this request comes from)
        'experiment' : {
            'historical' :
                'High' : {'Amon.tas': ['hist72'], 'day.tas': ['hist72', 'histext'], ...},
                'Medium' : {'Amon.tas': ['all'], ...},
                'Low' : ...
            }
            ...
        }
    }
    '''
    base = _get_base_dreq_tables(content, dreq_version, purpose='request')

    dreq_tables = {
        'opps': base['Opportunity'],
        'expt groups': base['Experiment Group'],
        'expts': base['Experiments'],
        'var groups': base['Variable Group'],
        'vars': base['Variables'],
        'ts': base['Time Subset'],
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
    priority_levels = all_priority_levels[:m + 1]
    del priority_cutoff

    # Loop over Opportunities to get prioritized lists of variables
    request = {}  # dict to hold aggregated request
    if combined_request:  # Optionally add combined request entries
        request['all_experiments'] = ExptRequest('all_experiments')
        request['historical_experiments'] = ExptRequest('historical_experiments')
        request['scenario_experiments'] = ExptRequest('scenario_experiments')
    for opp_id in opp_ids:
        opp = dreq_tables['opps'].records[opp_id]  # one record from the Opportunity table

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

        opp_time_subsets = get_opp_time_subsets(opp,
                                                dreq_tables['ts'],
                                                verbose=verbose)

        # Aggregate this Opportunity's request into the master list of requests
        for expt_name in opp_expts:
            if expt_name not in request:
                # If we haven't encountered this experiment yet, initialize an ExptRequest object for it
                request[expt_name] = ExptRequest(expt_name)

            # Add this Opportunity's variables request to the ExptRequest object
            for priority_level, var_names in opp_vars.items():
                if time_subsets:
                    request[expt_name].add_vars(var_names, priority_level, time_subsets=opp_time_subsets)
                    if combined_request:
                        request['all_experiments'].add_vars(var_names, priority_level, time_subsets=opp_time_subsets)
                        if 'hist' in expt_name.lower():
                            request['historical_experiments'].add_vars(var_names, priority_level, time_subsets=opp_time_subsets)
                        elif any(scen_part in expt_name.lower() for scen_part in ['ssp', 'scen']):
                            request['scenario_experiments'].add_vars(var_names, priority_level, time_subsets=opp_time_subsets)
                else:
                    request[expt_name].add_vars(var_names, priority_level)
                    if combined_request:
                        request['all_experiments'].add_vars(var_names, priority_level)
                        if 'hist' in expt_name.lower():
                            request['historical_experiments'].add_vars(var_names, priority_level)
                        elif any(scen_part in expt_name.lower() for scen_part in ['ssp', 'scen']):
                            request['scenario_experiments'].add_vars(var_names, priority_level)

    opp_titles = sorted([dreq_tables['opps'].get_record(opp_id).title for opp_id in opp_ids])
    requested_vars = {
        'Header': {
            'Opportunities': opp_titles,
            'dreq version': dreq_version,
        },
        'experiment': {},
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


def get_variables_metadata(content, dreq_version,
                           compound_names=None, cmor_tables=None, cmor_variables=None,
                           verbose=True):
    '''
    Get metadata for CMOR variables (dimensions, cell_methods, out_name, ...).

    Parameters:
    -----------
    content : dict
        Dict containing either:
        - data request content as exported from airtable
        OR
        - DreqTable objects representing tables (dict keys are table names)
    dreq_version : str
        Version string identifier for Data Request Content
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
    '''
    base = _get_base_dreq_tables(content, dreq_version, purpose='request')

    # Some variables in these dreq versions lack a 'frequency' attribute; use the legacy CMIP6 frequency for them
    dreq_versions_substitute_cmip6_freq = ['v1.0', 'v1.1']

    # Use dict dreq_tables to store instances of the DreqTable class that are used in this function.
    # Mostly this would be the same as simply using base[table name], but in some cases there's a choice
    # of which table to use. Using dreq_tables as a mapping makes this choice explicit.
    dreq_tables = {
        'variables': base['Variables']
    }
    # The Variables table is the master list of variables in the data request.
    # Each entry (row) is a CMOR variable, containing the variable's metadata.
    # Many of these entries are links to other tables in the database (see below).

    # Set frequency table and (if necessary) frequency attribute of variables table
    freq_table_name = 'CMIP7 Frequency'
    dreq_tables['frequency'] = base[freq_table_name]
    if 'frequency' not in dreq_tables['variables'].attr2field:
        # The code below assumes each variable has an attribute called 'frequency'.
        # Here adjust for the possibility that the variables table may not yet have an attribute with this name.
        freq_attr_name = format_attribute_name(freq_table_name)
        if freq_attr_name in dreq_tables['variables'].attr2field:
            # If the attribute name corresponding to this table name is available, rename it as 'frequency'
            dreq_tables['variables'].rename_attr(freq_attr_name, 'frequency')
        else:
            raise ValueError(f'Expected attribute {freq_attr_name} linking to table {freq_table_name}')
        # Confirm that the 'frequency' attribute points to the correct table
        # (this is checking if the above change was made self-consistently).
        assert dreq_tables['variables'].links['frequency'] == freq_table_name, \
            'inconsistent table link for frequency attribute'

    # Get other tables from the database that are required to find all of a variable's metadata used by CMOR.
    dreq_tables.update({
        'spatial shape': base['Spatial Shape'],
        'coordinates and dimensions': base['Coordinates and Dimensions'],
        'temporal shape': base['Temporal Shape'],
        'cell methods': base['Cell Methods'],
        'physical parameters': base['Physical Parameters'],
        'realm': base['Modelling Realm'],
        'cell measures': base['Cell Measures'],
        'CF standard name': None,
    })
    if 'CF Standard Names' in base:
        dreq_tables['CF standard name'] = base['CF Standard Names']
    if 'Structure' in base:
        dreq_tables['structure'] = base['Structure']

    # Specify names of some DR variable attributes depending the DR version
    # TO DO: is this logic still needed? If so, make it explicitly depend on DR Content version?
    if 'CMIP6 Table Identifiers (legacy)' in base:
        dreq_tables['CMOR tables'] = base['CMIP6 Table Identifiers (legacy)']
        attr_table = 'cmip6_table_legacy'
        attr_realm = 'modelling_realm___primary'
    elif 'Table Identifiers' in base:
        dreq_tables['CMOR tables'] = base['Table Identifiers']
        attr_table = 'table'
        attr_realm = 'modelling_realm'
    else:
        raise ValueError('Which table contains CMOR table identifiers?')
    attr_realm_additional = 'modelling_realm___secondary'

    if dreq_version in dreq_versions_substitute_cmip6_freq:
        # needed for corrections below
        dreq_tables['CMIP6 frequency'] = base['CMIP6 Frequency (legacy)']

    # Check uniqueness of chosen variable names.
    var_name_map = {get_unique_var_name(record): record_id for record_id, record in dreq_tables['variables'].records.items()}
    assert len(var_name_map) == len(dreq_tables['variables'].records), \
        f'Variable names specified by {use_unique_var_name()} do not uniquely map to variable record ids'

    if verbose:
        if cmor_tables:
            print('Retaining only these CMOR tables: ' + ', '.join(sorted(cmor_tables, key=str.lower)))
        if cmor_variables:
            print('Retaining only these CMOR variables: ' + ', '.join(sorted(cmor_variables, key=str.lower)))
        if compound_names:
            print('Retaining only these compound names: ' + ', '.join(sorted(compound_names, key=str.lower)))

    substitute = {
        # replacement character(s) : [characters to replace with the replacement character]
        '_': ['\\_']
    }
    all_var_info = {}
    for var in dreq_tables['variables'].records.values():

        var_name = get_unique_var_name(var)

        if compound_names:
            if var_name not in compound_names:
                continue

        link_table = getattr(var, attr_table)
        if len(link_table) != 1:
            raise Exception(f'variable {var_name} should have one table link, found: ' + str(link_table))
        table_id = dreq_tables['CMOR tables'].get_record(link_table[0]).name
        if cmor_tables:
            # Filter by CMOR table name
            if table_id not in cmor_tables:
                continue

        if not hasattr(var, 'frequency') and dreq_version in dreq_versions_substitute_cmip6_freq:
            # seems to be an error for some vars in v1.0, so instead use their CMIP6 frequency
            assert len(var.cmip6_frequency_legacy) == 1
            link = var.cmip6_frequency_legacy[0]
            var.frequency = [dreq_tables['CMIP6 frequency'].get_record(link).name]
            # print('using CMIP6 frequency for ' + var_name)

        if isinstance(var.frequency[0], str):
            # retain this option for non-consolidated airtable export?
            assert isinstance(var.frequency, list)
            frequency = var.frequency[0]
        else:
            link = var.frequency[0]
            freq = dreq_tables['frequency'].get_record(link)
            frequency = freq.name

        cell_methods = ''
        area_label_dd = ''
        if hasattr(var, 'cell_methods'):
            assert len(var.cell_methods) == 1
            link = var.cell_methods[0]
            cm = dreq_tables['cell methods'].get_record(link)
            cell_methods = cm.cell_methods
            if hasattr(cm, 'brand_id'):
                area_label_dd = cm.brand_id

        # Get dimensions by
        # 1) using dimensions attribute from variable table, if given
        # 2) following database links
        dimensions_var = None
        if hasattr(var, 'dimensions'):
            # The variable table record gives the dimensions
            # dreq versions before v1.2 don't have a dimensions attribute in the variables table
            assert isinstance(var.dimensions, str), \
                f'Expected comma-delimited string giving the dimensions for {var_name}'
            dims_list = [s.strip() for s in var.dimensions.split(',')]
            dimensions_var = ' '.join(dims_list)

            # As an extra check, confirm each name in the list corresponds to a record in the coords+dims table
            for dim_name in dims_list:
                dimension = dreq_tables['coordinates and dimensions'].get_attr_record('name', dim_name, unique=True)
                # get_attr_record() with unique=True will fail if the name doesn't uniquely correspond
                # to a coordinates & dimensions table record.

        # Create dimensions list by following the relevant database links.
        dims_list = []
        # Get the 'Spatial Shape' record, which contains info about dimensions
        assert len(var.spatial_shape) == 1
        link = var.spatial_shape[0]
        spatial_shape = dreq_tables['spatial shape'].get_record(link)
        if hasattr(spatial_shape, 'dimensions'):
            for link in spatial_shape.dimensions:
                dimension = dreq_tables['coordinates and dimensions'].get_record(link)
                dims_list.append(dimension.name)
        # Add any dimensions present in structure record, if given
        # (A 'structure' link gives dimensions besides spatial & temporal ones, e.g. 'tau')
        if hasattr(var, 'structure_title'):
            link = var.structure_title[0]
            structure = dreq_tables['structure'].get_record(link)
            if hasattr(structure, 'dimensions'):
                for link in structure.dimensions:
                    dimension = dreq_tables['coordinates and dimensions'].get_record(link)
                    dims_list.append(dimension.name)
        # Add temporal dimensions
        link = var.temporal_shape[0]
        temporal_shape = dreq_tables['temporal shape'].get_record(link)
        # dims_list.append(temporal_shape.name)
        # An example of temporal_shape.name is 'time-point', but the equivalent dimensions list
        # entry for this is 'time1'.
        if hasattr(temporal_shape, 'dimensions'):
            for link in temporal_shape.dimensions:
                dimension = dreq_tables['coordinates and dimensions'].get_record(link)
                dims_list.append(dimension.name)
        # Add any coordinates
        if hasattr(var, 'coordinates'):
            for link in var.coordinates:
                coordinate = dreq_tables['coordinates and dimensions'].get_record(link)
                dims_list.append(coordinate.name)

        dimensions_linked = ' '.join(dims_list)

        compare_dims = False
        if compare_dims and dimensions_var:
            # Compare dimensions obtained from links vs. variable table record.
            # This check is expected to fail for some variables for v1.2 onward because the
            # Structure table was removed from the release base. It's left here in the code
            # as an internal option because it can be useful for debugging.
            if dimensions_linked != dimensions_var:
                msg = f'Inconsistent dimensions for {var_name}:\n  {dimensions_var}\n  {dimensions_linked}'
                print(msg)

        if dimensions_var:
            dimensions = dimensions_var
        else:
            dimensions = dimensions_linked

        # Get physical parameter record and use its name as out_name
        link = var.physical_parameter[0]
        phys_param = dreq_tables['physical parameters'].get_record(link)
        if hasattr(phys_param, 'variablerootdd'):
            # variableRootDD (aka "root name") is available in DR v1.2.2 onward
            out_name = phys_param.variablerootdd
        else:
            # Comparison with CMIP6 CMOR tables shows that out_name is the same as physical parameter name
            # for almost all variables in dreq v1.2.1
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
                # retain this option for non-consolidated airtable export?
                standard_name = phys_param.cf_standard_name
            else:
                link = phys_param.cf_standard_name[0]
                cfsn = dreq_tables['CF standard name'].get_record(link)
                standard_name = cfsn.name
        else:
            standard_name_proposed = phys_param.proposed_cf_standard_name

        # Get realm(s)
        link_realm = getattr(var, attr_realm)
        modeling_realm = [dreq_tables['realm'].get_record(link).id for link in link_realm]
        if hasattr(var, attr_realm_additional):
            # Add secondary realm(s), if any, to the list
            link_realm_additional = getattr(var, attr_realm_additional)
            modeling_realm += [dreq_tables['realm'].get_record(link).id for link in link_realm_additional]
        # Raise error if any realm is duplicated in the list
        if len(modeling_realm) != len(set(modeling_realm)):
            raise ValueError(f'Redundant realm(s) found for DR variable {var_name}: {modeling_realm}')

        cell_measures = ''
        if hasattr(var, 'cell_measures'):
            cell_measures = [dreq_tables['cell measures'].get_record(link).name for link in var.cell_measures]

        positive = ''
        if hasattr(var, 'positive_direction'):
            positive = var.positive_direction

        comment = ''
        if hasattr(var, 'description'):
            comment = var.description

        processing_note = ''
        if hasattr(var, 'processing_note'):
            processing_note = var.processing_note

        var_info = OrderedDict()
        # Insert fields in order given by CMIP6 cmor tables (https://github.com/PCMDI/cmip6-cmor-tables)
        var_info.update({
            'frequency': frequency,
            'modeling_realm': ' '.join(modeling_realm),
        })
        if standard_name != '':
            var_info['standard_name'] = standard_name
        else:
            var_info['standard_name_proposed'] = standard_name_proposed
        var_info.update({
            'units': phys_param.units,
            'cell_methods': cell_methods,
            'cell_measures': ' '.join(cell_measures),

            'long_name': var.title,
            'comment': comment,
            'processing_note': processing_note,

            'dimensions': dimensions,

            'out_name': out_name,
            'type': var.type,
            'positive': positive,

            'spatial_shape': spatial_shape.name,
            'temporal_shape': temporal_shape.name,

            # 'temporalLabelDD' : temporal_shape.brand,
            # 'verticalLabelDD' : spatial_shape.vertical_label_dd,
            # 'horizontalLabelDD' : spatial_shape.hor_label_dd,
            # 'areaLabelDD' : area_label_dd,

            'cmip6_table': table_id,
            'physical_parameter_name': phys_param.name,
        })

        for attr in ['flag_values', 'flag_meanings']:
            if hasattr(var, attr):
                var_info[attr] = getattr(var, attr)

        # Get info on branded variable name, if available
        if hasattr(var, 'branded_variable_name'):
            branded_variable_name = var.branded_variable_name

            variableRootDD, branding_label = None, None

            # Get variableRootDD, the short variable name used in the branded name
            if hasattr(phys_param, 'variablerootdd'):
                # variableRootDD is included in the Physical Parameter record for this variable
                variableRootDD = phys_param.variablerootdd

            # Get the branding label by parsing the branded variable name
            if branded_variable_name.count('_') == 1:
                s, branding_label = branded_variable_name.split('_')
                if not variableRootDD:
                    # Set variableRootDD if it wasn't already defined
                    variableRootDD = s

            # Handle undefined cases, to ensure variableRootDD and branding_label are not left undefined
            # (any such cases are anticipated to vanish in post-v1.2.2 dreq versions)
            if not variableRootDD:
                variableRootDD = 'None'
            if not branding_label:
                assert var.branded_variable_name_status not in ['Accepted']
                if branded_variable_name.startswith('unknown'):
                    branding_label = branded_variable_name
                else:
                    branding_label = 'None'

            check_branded_name = False
            if check_branded_name:
                # Consistency check on definition of branded name.
                # For development, not intended as a user option.
                if branded_variable_name != f'{variableRootDD}_{branding_label}':
                    warnings.warn(f'Inconsistency between branded variable name {branded_variable_name} '
                                  + f'and its components: {variableRootDD}, {branding_label}')

            var_info.update({
                'variableRootDD': variableRootDD,
                'branding_label': branding_label,
                'branded_variable_name': branded_variable_name,
            })

        if hasattr(var, 'region'):
            var_info['region'] = var.region

        # To help clarify the origin of the "compound name" used as a unique identifier to index
        # the output dict (all_var_info), include the CMIP6 and CMIP7 compoun names explicitly
        # as metadata parameters.
        for attr in ['cmip6_compound_name', 'cmip7_compound_name']:
            if hasattr(var, attr):
                var_info[attr] = getattr(var, attr)

        check_c7_name = False
        if check_c7_name:
            # Consistency check on definition of CMIP7 compound name.
            # For development, not intended as a user option.
            if _parse_version(dreq_version) >= (1, 2, 2, 0, "", 0):
                cn = []
                cn.append(modeling_realm[0])
                cn.append(variableRootDD)
                cn.append(branding_label)
                cn.append(frequency)
                cn.append(var_info['region'])
                sep = '.'
                s = sep.join(cn)
                if var_info['cmip7_compound_name'] != s:
                    warnings.warn(f'Unexpected CMIP7 compound name in {dreq_version}: '
                                  + var_info['cmip7_compound_name'])

        # Include hash-like unique identifier string from the CMIP7 dreq Variables table ("UID" column)
        # Example: 'bab52da8-e5dd-11e5-8482-ac72891c3257'
        # This should also be a unique variable identifier.
        valid_uid = isinstance(var.uid, str) and len(var.uid) >= 36
        if not valid_uid:
            raise ValueError(f'Invalid UID string: {var.uid}')
        var_info.update({
            'uid': var.uid,
        })

        for k, v in var_info.items():
            v = v.strip()
            for replacement in substitute:
                for s in substitute[replacement]:
                    if s in v:
                        v = v.replace(s, replacement)
            var_info[k] = v

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


def get_dimension_sizes(dreq_tables):
    '''
    Create lookup table of dimension sizes by examining records in the Spatial Shape table.

    Parameters
    ----------
    dreq_tables: dict
        Dict values are DreqTable objects for the required tables, e.g.:
        dreq_tables = {
            'coordinates and dimensions': base['Coordinates and Dimensions'],
            'spatial shape': base['Spatial Shape'],
        }
    '''
    dim_names = [dimension.name for dimension in dreq_tables['coordinates and dimensions'].records.values()]
    assert len(set(dim_names)) == len(dim_names)
    dim_names.sort(key=str.lower)
    # Initialize dict having names of all dimensions in the data request (to ensure we don't miss any).
    # Each entry is a set(), and below we determine dimension sizes by any available method,
    # and then after the fact check to see if the answers were consistent.
    dim_sizes = OrderedDict({dim: set() for dim in dim_names})

    # Determine dimension sizes based on their records in the Coordinates & Dimensions table.
    for dimension in dreq_tables['coordinates and dimensions'].records.values():
        dim = dimension.name
        if hasattr(dimension, 'grid_class'):
            # Get size based on what type of grid this dimension is labelled as.
            if dimension.grid_class in ['model', 'options']:
                dim_sizes[dim].add(dimension.grid_class)
            elif dimension.grid_class in ['fixedScalar', 'fixedScaler']:  # fixedScaler = typo in Airtable
                dim_sizes[dim].add(1)
            elif dimension.grid_class == 'fixed':
                if hasattr(dimension, 'size'):
                    dim_sizes[dim].add(dimension.size)
                elif hasattr(dimension, 'requested_values'):
                    if not isinstance(dimension.requested_values, str):
                        raise TypeError(f'Expected space-delimited string for requested_values for dimension {dimension.name}')
                    dim_sizes[dim].add(len(dimension.requested_values.split()))
                else:
                    # raise AttributeError(f'How should the size of dimension {dimension.name} be determined?')
                    pass
            elif dimension.grid_class == 'fixedExternal':
                pass
            else:
                raise ValueError(f'Unknown grid class for dimension {dim}: {dimension.grid_class}')
        if hasattr(dimension, 'size'):
            # Use the size attribute, if it exists.
            dim_sizes[dim].add(dimension.size)
        if hasattr(dimension, 'requested_values'):
            # If a set of requested values if specified (e.g. for pressure levels grids like "plev19"),
            # use the length of the list of values.
            # The list is stored in Airtable as a space-delimited string.
            assert isinstance(dimension.requested_values, str), \
                f'Expected str for dimension.requested_values, received: {type(dimension.requested_values)}'
            values = dimension.requested_values.split()
            dim_sizes[dim].add(len(values))

    # Determine dimension sizes where possible by looking in the Spatial Shape table records.
    # This is an extra consistency check on the results from dimensions, but it doesn't seem to change
    # the results (as tested on dreq v1.2 content).
    for spatial_shape in dreq_tables['spatial shape'].records.values():
        if hasattr(spatial_shape, 'dimensions'):
            # Follow links from Spatial Shape to dimensions, if they exist
            for link in spatial_shape.dimensions:
                dimension = dreq_tables['coordinates and dimensions'].get_record(link)
                dim = dimension.name
                if hasattr(dimension, 'axis_flag') and dimension.axis_flag == 'Z':
                    dim_sizes[dim].add(spatial_shape.number_of_levels)
                if hasattr(dimension, 'size'):
                    dim_sizes[dim].add(dimension.size)

    # Check that the results make sense
    # Each dimension should have only one size
    # User-determined sizes are indicated by the grid_class values listed in user_sizes
    for dim, sizes in dim_sizes.items():
        user_sizes = {'options', 'model'}
        if len(user_sizes.intersection(sizes)) > 1:
            # Raise error if more than one user-determined size option is given, because
            # the result is ambiguous (which should be used?).
            raise ValueError(f'Unexpected sizes: {sizes}')
        for grid_class in user_sizes:
            if grid_class in sizes:
                sizes = {grid_class}

        if len(sizes) == 1:
            size = list(sizes)[0]
        elif len(sizes) > 1:
            size = max(sizes)
            print(f'Warning: found sizes {sorted(sizes)} for dimension "{dim}", assuming size = {size}')
        else:
            size = None
            msg = f'Warning: found no size for dimension "{dim}"'
            if dim in ['xant', 'yant']:
                size = 200
                msg += f', assuming size = {size}'
            print(msg)

        dim_sizes[dim] = size

    return dim_sizes


def show_requested_vars_summary(expt_vars, dreq_version):
    '''
    Display quick summary to stdout of variables requested.
    expt_vars is the output dict from dq.get_requested_variables().
    '''
    print(f'\nFor data request version {dreq_version}, number of requested variables found by experiment:')
    priority_levels = get_priority_levels()
    for expt, req in sorted(expt_vars['experiment'].items()):
        d = {p: 0 for p in priority_levels}
        for p in priority_levels:
            if p in req:
                d[p] = len(req[p])
        n_total = sum(d.values())
        print(f'  {expt} : ' + ' ,'.join(['{p}={n}'.format(p=p, n=d[p]) for p in priority_levels]) + f', TOTAL={n_total}')


def write_requested_vars_json(outfile, expt_vars, dreq_version, priority_cutoff, content_path):
    '''
    Write a nicely formatted json file with lists of requested variables by experiment.
    expt_vars is the output dict from dq.get_requested_variables().
    '''

    header = OrderedDict({
        'Description': 'This file gives the names of output variables that are requested from CMIP experiments by the supported Opportunities. The variables requested from each experiment are listed under each experiment name, grouped according to the priority level at which they are requested. For each experiment, the prioritized list of variables was determined by compiling together all requests made by the supported Opportunities for output from that experiment.',
        'Opportunities supported': sorted(expt_vars['Header']['Opportunities'], key=str.lower)
    })
    # Add Note about combined request, if included
    if "all_experiments" in expt_vars["experiment"]:
        header["Note"] = "Added combined request for all experiments as entry 'all_experiments'. Added combined request for all historical and scenario experiments as entries 'historical_experiments' and 'scenario_experiments', respectively."

    # List supported priority levels
    priority_levels = get_priority_levels()
    priority_cutoff = priority_cutoff.capitalize()
    m = priority_levels.index(priority_cutoff) + 1
    header.update({
        'Priority levels supported': priority_levels[:m]
    })
    for req in expt_vars['experiment'].values():
        for p in priority_levels[m:]:
            assert req[p] == [] or req[p] == {}
            req.pop(p)  # remove empty lists of unsupported priorities from the output

    # List included experiments
    header.update({
        'Experiments included': sorted(expt_vars['experiment'].keys(), key=str.lower)
    })

    # Get provenance of content to include in the header
    # content_path = dc._dreq_content_loaded['json_path']
    with open(content_path, 'rb') as f:
        content_hash = hashlib.sha256(f.read()).hexdigest()
    header.update({
        'dreq content version': dreq_version,
        'dreq content file': os.path.basename(os.path.normpath(content_path)),
        'dreq content sha256 hash': content_hash,
        'dreq api version': api_version,
    })

    out = {
        'Header': header,
        'experiment': OrderedDict(),
    }
    # Put sorted contents of expt_vars into OrderedDict
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


def write_variables_metadata(all_var_info, dreq_version, filepath,
                             api_version=None, content_path=None):

    ext = os.path.splitext(filepath)[-1]

    if not api_version:
        raise ValueError(f'Must provide API version, received: {api_version}')
    if not content_path:
        raise ValueError(f'Must provide path to data request content, received: {content_path}')

    if ext == '.json':
        # Get provenance of content to include in the header
        with open(content_path, 'rb') as f:
            content_hash = hashlib.sha256(f.read()).hexdigest()

        # Create output dict
        out = OrderedDict({
            'Header': OrderedDict({
                'Description': 'Metadata attributes that characterize CMOR variables. Each variable is uniquely idenfied by a compound name comprised of a CMIP6-era table name and a short variable name.',
                'no. of variables': len(all_var_info),
                'dreq content version': dreq_version,
                'dreq content file': os.path.basename(os.path.normpath(content_path)),
                'dreq content sha256 hash': content_hash,
                'dreq api version': api_version,
            }),
            'Compound Name': all_var_info,
        })

        # Write variables metadata to json
        with open(filepath, 'w') as f:
            json.dump(out, f, indent=4)
            print(f'Wrote {filepath} for {len(all_var_info)} variables, dreq version = {dreq_version}')

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
        print(f'Wrote {filepath} for {n} variables, dreq version = {dreq_version}')

    else:
        raise ValueError('Unsupported file extension: ' + ext)
