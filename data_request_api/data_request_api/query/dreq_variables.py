#!/usr/bin/env python
'''
Functions to interrogate DR variables.
'''

from collections import OrderedDict, defaultdict


KEEP_ATTRIBUTES_KEY = 'keep_attributes'


def get_available_attributes(vars: dict[str, dict[str, str]]) -> set[str]:
    '''
    Get list of attributes (keys) for variables in dict vars.
    '''
    available_attrs = set()
    # Loop over all dicts because it's possible some have attributes that others lack, e.g. flag_values
    for var_info in vars.values():
        available_attrs.update(var_info.keys())
    return available_attrs


def get_available_values(vars: dict[str, dict[str, str]]) -> dict[str, set[str]]:
    '''
    Get list of attribute values available in vars.
    '''
    available_values = defaultdict(set)
    # Find all available values of each attribute by looping over all variables
    for var_info in vars.values():
        for attr, value in var_info.items():
            available_values[attr].add(value)
    return available_values


def validate_filters(vars: dict[str, dict[str, str]], filters: dict[str, list[str]]):
    '''
    Check that attribute names and attribute values passed by user are valid in the DR.
    '''

    available_attrs = get_available_attributes(vars)
    unavailable_attrs = set()
    available_values = get_available_values(vars)
    unavailable_values = defaultdict(set)

    # If given a list of attribute names to retain, validate it
    if KEEP_ATTRIBUTES_KEY in filters and not filters[KEEP_ATTRIBUTES_KEY]:
        # An empty list was passed, so ignore it (i.e., keep all attributes)
        del filters[KEEP_ATTRIBUTES_KEY]
    restore_keep_attrs = False
    if KEEP_ATTRIBUTES_KEY in filters:
        # Remove duplicate attribute names if any
        keep_attrs = list(dict.fromkeys(filters[KEEP_ATTRIBUTES_KEY]))
        # Check for invalid attribute names
        for attr in list(keep_attrs):
            if attr not in available_attrs:
                unavailable_attrs.add(attr)
                # Remove invalid attribute name
                keep_attrs.remove(attr)
        del filters[KEEP_ATTRIBUTES_KEY]  # will add this back in below
        # Remove any filtering by attributes that have been discarded
        ignore_attrs = [attr for attr in filters if attr not in keep_attrs]
        if len(ignore_attrs) > 0:
            print('\nFilters for these discarded attributes will be ignored: ' + ', '.join(ignore_attrs))
        for attr in ignore_attrs:
            del filters[attr]
        restore_keep_attrs = True

    # Validate names of the attributes to filter on
    for attr in list(filters):
        if attr not in available_attrs:
            unavailable_attrs.add(attr)
            # Remove invalid attribute from filters
            del filters[attr]

    # Validate values of the attributes to filter on
    for attr in filters:
        # Remove duplicates if any
        filters[attr] = list(dict.fromkeys(filters[attr]))
        # Check validity of values in the list
        for value in list(filters[attr]):
            if value not in available_values[attr]:
                unavailable_values[attr].add(value)
                # Remove invalid value from this attribute's filter
                filters[attr].remove(value)

    if restore_keep_attrs:
        # Retore the list of attributes to keep, if it was given
        filters[KEEP_ATTRIBUTES_KEY] = keep_attrs

    # Warn user if unavailable attribute names and/or attribute values were requested
    if len(unavailable_attrs) > 0:
        print('\nIgnoring invalid attributes: ' + ', '.join(sorted(unavailable_attrs)))
        print('Available attributes:')
        # List available attributes in format that can be cut-paste into yaml
        for attr in sorted(available_attrs):
            print(f'- {attr}')
    if any([len(values) > 0 for values in unavailable_values.values()]):
        print('\nIgnoring invalid attribute values:')
        for attr in sorted(unavailable_values):
            print(f'  {attr}: ' + ', '.join(sorted(unavailable_values[attr])))
        print('Available attribute values:')
        for attr in sorted(unavailable_values):
            print(f'  {attr}: ' + ', '.join(sorted(available_values[attr])))


def filter_variables_metadata(vars: dict[str, dict[str, str]], filters: dict[str, list[str]]):
    '''
    Apply filters to subset variables dict returned by get_variables_metadata().
    '''
    # Ensure filters contain only valid attribute names and values
    validate_filters(vars, filters)

    if KEEP_ATTRIBUTES_KEY in filters:
        keep_attrs = filters[KEEP_ATTRIBUTES_KEY]
        # Remove unwanted attributes
        for var_info in vars.values():
            for attr in list(var_info):
                if attr not in keep_attrs:
                    del var_info[attr]
        # Set attribute order based on input list order
        for var_name, var_info in vars.items():
            vars[var_name] = OrderedDict({attr:var_info[attr] for attr in keep_attrs})
        # List of attributes is no longer needed
        del filters[KEEP_ATTRIBUTES_KEY]

    # Filter variables by attribute values
    exclude_vars = []
    for var_name, var_info in vars.items():
        check = []
        for attr, values in filters.items():
            check.append(var_info[attr] in values)
        if not all(check):
            exclude_vars.append(var_name)
    for var_name in exclude_vars:
        del vars[var_name]
    
