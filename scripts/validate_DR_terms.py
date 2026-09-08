#!/usr/bin/env python
'''
Quick script to check DR content against CMIP7 CVs and report any inconsistencies found.
'''

import argparse
import json

# Ensure latest CMIP7 is used by esgvoc:
#   esgvoc use cmip7@latest
import esgvoc.api as ev

import data_request_api.content.dreq_content as dc
import data_request_api.query.dreq_query as dq
from data_request_api import version as api_version



def parse_args():
    descrip = '''
Check DR content against CMIP7 CVs and report any inconsistencies found.

User should ensure esgvoc is using the latest version of the CMIP7 CVs:
  esgvoc use cmip7@latest

Invoke either with DR version string or path to a DR release content export json file. Examples:
  python validate_DR_terms.py v1.2.2.4
  python validate_DR_terms.py CMIP7_DReq_Content/airtable_export/dreq_release_export.json
'''
    parser = argparse.ArgumentParser(description=descrip, formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    parser.add_argument('dr_content', type=str,
                        help='directory containing CCCma tables json files')    
    
    # Optional arguements
    parser.add_argument('--output-dr-vars', action='store_true', default=False,
                        help='output json file with metadata of DR variables that is used in the comparison')

    return parser.parse_args()

if __name__ == '__main__':

    args = parse_args()
    if args.dr_content.endswith('.json'):
        dr_file = args.dr_content
        with open(dr_file) as f:
            content = json.load(f)
        # re-key dict to remove version identifier
        # e.g. "Data Request v1.2.2.4" --> "Data Request"
        assert len(content.keys()) == 1
        key = next(iter(content.keys()))
        assert key.startswith('Data Request')
        dr_version = key.split()[-1]
        content['Data Request'] = content[key]
        content.pop(key)
        print(f'Using DR content from export file: {dr_file}')
        content_path=dr_file
    else:
        dr_version = args.dr_content
        content = dc.load(dr_version)
        print(f'Using DR content from versioned release: {dr_version}')
        content_path=dc._dreq_content_loaded['json_path']


    ###########################################################################
    # Validate DR variables against the CVs

    # Get metadata of all DR variables
    all_var_info = dq.get_variables_metadata(content, dr_version)

    # Mapping for attributes given a different name by dq.get_variables_metadata() than used in CVs.
    # Note that dq.get_variables_metadata() does not necessarily use the same attribute names as the columns
    # seen in the DR Airtable view (e.g. "Title" in the Airtable Variables table becomes "long_name").
    # (Reasons for DR attributes having different names in this file compared to CVs might be, but aren't necessarily, good reasons.)
    attr_map_cv2dr = {
        'realm': 'modeling_realm',
        'branded_variable': 'branded_variable_name',
        'variable': 'variableRootDD',
        'branding_suffix': 'branding_label',
    }

    if args.output_dr_vars:
        # Optionally, write output file with info on the DR variables.
        # In case it's convenient for any subsequent checks, or to make explicit what was looked at for the checks.
        # Attribute names may not necessarily all match the CVs (see attr_map_cv2dr).
        outfile = f'variables_{dr_version}.json'
        dq.write_variables_metadata(
            all_var_info,
            dr_version,
            outfile,
            api_version=api_version,
            content_path=content_path
        )

    # Get CVs info to compare to DR
    collec = ev.get_all_collections_in_project(project_id="cmip7")

    # Specify attributes to check, using attribute names as they appear in CVs
    check_attrs = []
    check_attrs.append('frequency')
    check_attrs.append('region')
    check_attrs.append('realm')
    check_attrs.append('branded_variable')
    check_attrs.append('variable')

    check_attrs.append('area_label')
    check_attrs.append('horizontal_label')
    check_attrs.append('vertical_label')
    check_attrs.append('temporal_label')

    for var_info in all_var_info.values():
        assert var_info['branded_variable_name'].count('_') == 1
        variable_id, branding_suffix = var_info['branded_variable_name'].split('_')
        assert var_info['variableRootDD'] == variable_id
        temporal_label, vertical_label, horizontal_label, area_label = branding_suffix.split('-')
        update = {
            'temporal_label': temporal_label,
            'vertical_label': vertical_label,
            'horizontal_label': horizontal_label,
            'area_label': area_label
        }
        assert not any([attr in var_info for attr in update.keys()])
        var_info.update(update)
        del update


    for attr in check_attrs:
        if attr in attr_map_cv2dr:
            # Adjust for different attribute name used in dq.get_variables_metadata()
            # (generally these match the CMOR tables name)
            attr_dr = attr_map_cv2dr[attr]
        else:
            # Assume same attribute name in CVs and dq.get_variables_metadata()
            attr_dr = attr

        all_dr_values = set([var_info[attr_dr] for var_info in all_var_info.values()])
        if attr_dr == 'modeling_realm':
            # These are space-delimited lists of realms, e.g. 'atmos land'
            w = ' '.join(all_dr_values)
            all_dr_values = set([s.strip() for s in w.split()])

        valid_terms = ev.get_all_terms_in_collection(project_id="cmip7", collection_id=attr)
        valid_values = set([t.drs_name for t in valid_terms])
        if not all_dr_values.issubset(valid_values):
            print(f'CVs validation error on: {attr}\n  Invalid DR values: {all_dr_values.difference(valid_values)}')
        else:
            print(f'All DR values validated for: {attr}')


    print()
    ###########################################################################
    # Validate DR experiments against CVs

    # Get all experiment names in the DR
    dr_tables = {
        'expts': content['Data Request']['Experiments'],
    }
    expts = dr_tables['expts']
    all_dr_values = set([rec.experiment for rec in expts.records.values()])
    attr = 'experiment'

    # Get all experiment names in the CVs
    valid_terms = ev.get_all_terms_in_collection(project_id="cmip7", collection_id=attr)
    valid_values = set([t.drs_name for t in valid_terms])
    if not all_dr_values.issubset(valid_values):
        invalid = all_dr_values.difference(valid_values)
        print(f'Experiments in DR but not in CVs ({len(invalid)}):')
        for s in sorted(invalid, key=str.lower):
            print(f'  {s}')

        # Check if, among these, there are any case-insensitive matches
        valid_values = set([s.lower() for s in valid_values])
        all_dr_values = set([s.lower() for s in invalid])
        match = all_dr_values.intersection(valid_values)
        if len(match) > 0:
            print(f'\n{len(match)} case-insensitive matches:')
            for s in sorted(match, key=str.lower):
                print(f'  {s}')
        else:
            print(f'None of these were case-insensitive matches to CVs experiments')
    else:
        print(f'All DR values validated for: {attr}')


