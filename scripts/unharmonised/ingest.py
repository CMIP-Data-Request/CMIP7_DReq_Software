#!/usr/bin/env python

import pprint
import os
import yaml


filepath = 'opp_test.yaml'
with open(filepath, 'r') as f:
    opp = yaml.safe_load(f)

pprint.pprint(opp, width=120)


