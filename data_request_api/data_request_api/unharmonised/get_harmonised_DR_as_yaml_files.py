#!/usr/bin/env python

import argparse
import textwrap
import yaml

from pathlib import Path
# from textwrap import dedent, wrap

import data_request_api.content.dreq_content as dc
import data_request_api.query.dreq_query as dq
from data_request_api.query.dreq_classes import (format_attribute_name)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Write yaml files with content from Harmonised Data Request'
    )

    parser.add_argument('dreq_version', choices=dc.get_versions(), 
                        help="version of Harmonised CMIP7 Data Request content")

    parser.add_argument('-op', '--opportunity', action='store_true', default=False,
                        help='write yaml files for DR Opportunities')
    parser.add_argument('-eg', '--experiment-group', action='store_true', default=False,
                        help='write yaml files for experiment groups')
    parser.add_argument('-vg', '--variable-group', action='store_true', default=False,
                        help='write yaml files for variable groups')

    return parser.parse_args()

def outdir_setup(dir_name: str) -> Path:
    outdir = Path(dir_name)
    if not outdir.is_dir():
        raise FileNotFoundError(f'Expected directory to exist: {outdir}')
    # outdir = outdir / 'Harmonised'
    outdir = 'reference_Harmonised' / outdir
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir

def format_text(text: str) -> str:
    text = text.replace('\xa0', '')
    # text = textwrap.wrap(text)
    # text = textwrap.fill(text)
    # breakpoint()

    text = text.replace('\n', ' ')
    text = ' '.join(text.split())

    # text = f' | \n{text}'

    return text

def main():
    args = parse_args()
    dreq_version = args.dreq_version

    dreq_content = dc.load(dreq_version)
    base = dq._get_base_dreq_tables(dreq_content, dreq_version, purpose='request')

    if args.opportunity:
        # opp_names = set(rec.title for rec in base['Opportunity'].records.values())
        outdir = outdir_setup('Opportunity')

        for rec in base['Opportunity'].records.values():

            # Get names of Variable Groups linked from this Opportunity
            vg_names = [base['Variable Group'].records[link.record_id].name 
                        for link in rec.variable_groups]
            # Get names of Experiment Groups linked from this Opportunity
            eg_names = [base['Experiment Group'].records[link.record_id].name 
                        for link in rec.experiment_groups]

            info = {
                'Title': rec.title,
                # "text": "Hello\nWorld\nThis is a multiline string.",
                'Description': format_text(rec.description),
                'Expected Impacts': format_text(rec.expected_impacts),
                'Justification of Resources': format_text(rec.justification_of_resources),
                'Experiment Groups': eg_names,
                'Variable Groups': vg_names,
            }

            # Add additional info present in the Harmonised DR
            themes = [base['Data Request Themes'].records[link.record_id].name 
                      for link in rec.themes]
            info.update({
                'Opportunity ID': int(rec.opportunity_id),
                'Themes': themes,
            })
            if hasattr(rec, 'mips___high_priority'):
                mip_names = [base['MIPs'].records[link.record_id].mip_short_name 
                                  for link in rec.mips___high_priority]
                info.update({
                    'MIPs - high priority': mip_names,
                })
            if hasattr(rec, 'mips___lower_priority'):
                mip_names = [base['MIPs'].records[link.record_id].mip_short_name 
                                   for link in rec.mips___lower_priority]
                info.update({
                    'MIPs - lower priority': mip_names,
                })

            info_yaml = yaml.safe_dump(info, default_flow_style=False, sort_keys=False, allow_unicode=True)

            filename = f'{format_attribute_name(rec.title)}.yaml'
            outfile = outdir / filename
            with open(outfile, 'w') as f:
                f.write(info_yaml)
                print(f'Wrote {outfile}')

    if args.experiment_group:
        outdir = outdir_setup('Experiment_Group')

        for rec in base['Experiment Group'].records.values():

            # Get names of experiments belonging to this experiment group
            expt_names = [base['Experiments'].records[link.record_id].experiment 
                     for link in rec.experiments]
            assert len(expt_names) == len(set(expt_names))
            
            title = rec.title if hasattr(rec, 'title') else ''
            info = {
                'Name': rec.name,
                'Title': title,
                'Experiments': expt_names,
                'Number of experiments in group': len(expt_names),
            }
            info_yaml = yaml.safe_dump(info, default_flow_style=False, sort_keys=False, allow_unicode=True)

            filename = f'{format_attribute_name(rec.name)}.yaml'
            outfile = outdir / filename
            with open(outfile, 'w') as f:
                f.write(info_yaml)
                print(f'Wrote {outfile}')

    if args.variable_group:
        outdir = outdir_setup('Variable_Group')

        for rec in base['Variable Group'].records.values():

            # Get names of variables belong to this variable group
            var_names = [base['Variables'].records[link.record_id].cmip7_compound_name
                     for link in rec.variables]
            assert len(var_names) == len(set(var_names))

            # Get priority level of this variable group
            priority_level = [base['Priority Level'].records[link.record_id].name
                              for link in rec.priority_level]
            assert len(priority_level) == 1, f'Unexpected priority level: {priority_level}'
            priority_level = priority_level[0]

            title = rec.title if hasattr(rec, 'title') else ''
            justification = rec.justification if hasattr(rec, 'justification') else ''
            notes = rec.notes if hasattr(rec, 'notes') else ''
            info = {
                'Name': rec.name,
                'Title': title,
                'Priority Level': priority_level,
                'Justification': format_text(justification),
                'Notes': notes,
                'Variables': var_names,
                'Number of variables in group': len(var_names),
            }

            # Add additional info present in the Harmonised DR
            if hasattr(rec, 'theme'):
                themes = [base['Data Request Themes'].records[link.record_id].name 
                        for link in rec.theme]
                info.update({
                    'Themes': themes,
                })
            if hasattr(rec, 'mip_ownership'):
                mip_names = [base['MIPs'].records[link.record_id].mip_short_name 
                                  for link in rec.mip_ownership]
                info.update({
                    'MIP ownership': mip_names,
                })
            if hasattr(rec, 'of_interest_to_mips'):
                mip_names = [base['MIPs'].records[link.record_id].mip_short_name 
                                   for link in rec.of_interest_to_mips]
                info.update({
                    'Of interest to MIPs': mip_names,
                })

            info_yaml = yaml.safe_dump(info, default_flow_style=False, sort_keys=False, allow_unicode=True)

            filename = f'{format_attribute_name(rec.name)}.yaml'
            outfile = outdir / filename
            with open(outfile, 'w') as f:
                f.write(info_yaml)
                print(f'Wrote {outfile}')


if __name__ == '__main__':
    main()