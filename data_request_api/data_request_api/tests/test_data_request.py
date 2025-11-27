#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test data_request.py
"""
from __future__ import print_function, division, unicode_literals, absolute_import

import copy
import os
import tempfile
import unittest


from data_request_api.utilities.tools import read_json_input_file_content
from data_request_api.query.data_request import DRObjects, ExperimentsGroup, VariablesGroup, Opportunity, \
    DataRequest, version
from data_request_api.query.vocabulary_server import VocabularyServer, ConstantValueObj
from data_request_api.tests import filepath


class TestDRObjects(unittest.TestCase):
    def setUp(self):
        self.dr = DataRequest.from_separated_inputs(VS_input=filepath("VS_release_not-consolidate_content.json"),
                                                    DR_input=filepath("DR_release_not-consolidate_content.json"))

    def test_init(self):
        with self.assertRaises(TypeError):
            DRObjects()

        with self.assertRaises(TypeError):
            DRObjects("link::my_id")

        with self.assertRaises(TypeError):
            DRObjects(self.dr)

        obj = DRObjects("link::my_id", self.dr)
        obj = DRObjects(id="link::my_id", dr=self.dr)
        self.assertEqual(obj.DR_type, "undef")

    def test_from_input(self):
        with self.assertRaises(TypeError):
            DRObjects.from_input()

        with self.assertRaises(TypeError):
            DRObjects.from_input("link::my_id")

        with self.assertRaises(TypeError):
            DRObjects.from_input(self.dr)

        obj = DRObjects.from_input(dr=self.dr, id="link::my_id")

        obj = DRObjects.from_input(dr=self.dr, id="link::my_id", DR_type="priority_level")

        obj = DRObjects.from_input(dr=self.dr, id="link::High", DR_type="priority_level")

    def test_check(self):
        obj = DRObjects("my_id", self.dr)
        obj.check()

    def test_print(self):
        obj = DRObjects(id="link::my_id", dr=self.dr)
        self.assertEqual(str(obj), "undef: undef (id: my_id)")

    def test_eq(self):
        obj = DRObjects(id="link::my_id", dr=self.dr)
        obj2 = copy.deepcopy(obj)
        self.assertEqual(obj, obj2)

        obj3 = DRObjects(id="link::my_id_2", dr=self.dr)
        self.assertNotEqual(obj, obj3)
        self.assertTrue(obj < obj3)
        self.assertFalse(obj > obj3)

    def test_hash(self):
        obj = DRObjects(id="link::my_id", dr=self.dr)
        my_set = set()
        my_set.add(obj)
        my_set.add(DRObjects(id="link::my_id_2", dr=self.dr))
        my_set.add(copy.deepcopy(obj))
        self.assertEqual(len(my_set), 2)

        my_dict = dict()
        obj2 = self.dr.find_element("cmip7_frequency", "link::63215c10-8ca5-11ef-944e-41a8eb05f654")
        obj3 = self.dr.find_element("cmip7_frequency", "link::63215c11-8ca5-11ef-944e-41a8eb05f654")
        self.assertTrue(isinstance(obj2, DRObjects))
        self.assertTrue(isinstance(obj2.name, ConstantValueObj))
        self.assertTrue(isinstance(obj3.name, ConstantValueObj))
        my_dict[obj2.id] = obj2
        my_dict[obj2.name] = obj2
        my_dict[obj3.id] = obj3
        my_dict[obj3.name] = obj3

    def test_get(self):
        obj1 = DRObjects(id="my_id", dr=self.dr)
        self.assertEqual(obj1.get("id"), "my_id")
        self.assertEqual(obj1.get("DR_type"), "undef")
        self.assertEqual(obj1.get("test"), "undef")

    def test_filter_on_request(self):
        obj1 = DRObjects(id="my_id", DR_type="test", dr=self.dr)
        obj2 = copy.deepcopy(obj1)
        obj3 = DRObjects(id="my_other_id", DR_type="test", dr=self.dr)
        obj4 = DRObjects(id="my_id", DR_type="test2", dr=self.dr)
        self.assertEqual(obj1.filter_on_request(obj2), (True, True))
        self.assertEqual(obj1.filter_on_request(obj3), (True, False))
        self.assertEqual(obj1.filter_on_request(obj4), (False, False))


class TestExperimentsGroup(unittest.TestCase):
    def setUp(self):
        self.dr = DataRequest.from_separated_inputs(VS_input=filepath("VS_release_not-consolidate_content.json"),
                                                    DR_input=filepath("DR_release_not-consolidate_content.json"))

    def test_init(self):
        with self.assertRaises(TypeError):
            ExperimentsGroup()

        with self.assertRaises(TypeError):
            ExperimentsGroup("link::my_id")

        with self.assertRaises(TypeError):
            ExperimentsGroup(self.dr)

        obj = ExperimentsGroup("link::my_id", self.dr)

        obj = ExperimentsGroup(id="link::my_id", dr=self.dr, name="test")
        self.assertEqual(obj.DR_type, "experiment_groups")

    def test_from_input(self):
        with self.assertRaises(TypeError):
            ExperimentsGroup.from_input()

        with self.assertRaises(TypeError):
            ExperimentsGroup.from_input("link::my_id")

        with self.assertRaises(TypeError):
            ExperimentsGroup.from_input(self.dr)

        obj = ExperimentsGroup.from_input(id="link::my_id", dr=self.dr)

        with self.assertRaises(ValueError):
            obj = ExperimentsGroup.from_input(id="link::my_id", dr=self.dr, experiments=["link::test", ])

        obj = ExperimentsGroup.from_input(id="link::my_id", dr=self.dr,
                                          experiments=["link::amip", "link::esm-hist"])

    def test_check(self):
        obj = ExperimentsGroup(id="link::my_id", dr=self.dr)
        obj.check()

        obj = ExperimentsGroup(id="link::my_id", dr=self.dr, experiments=["link::amip", "link::esm-hist"])
        obj.check()

    def test_methods(self):
        obj = ExperimentsGroup(id="link::my_id", dr=self.dr)
        self.assertEqual(obj.count(), 0)
        self.assertEqual(obj.get_experiments(), list())

        obj = ExperimentsGroup.from_input(id="link::80ab7324-a698-11ef-914a-613c0433d878", dr=self.dr,
                                          experiments=["link::amip", "link::esm-hist"])
        self.assertEqual(obj.count(), 2)
        self.assertListEqual(obj.get_experiments(),
                             [self.dr.find_element("experiments", "link::amip"),
                              self.dr.find_element("experiments", "link::esm-hist")])
        self.assertEqual(obj.get_experiments()[0].DR_type, "experiments")

    def test_print(self):
        obj = ExperimentsGroup.from_input(id="link::historical", dr=self.dr,
                                          experiments=["link::historical", "link::esm-hist"], name="historical")
        ref_str = "experiment_group: historical"
        ref_str_2 = [
            ref_str,
            "    Experiments included:",
            "        experiment: historical",
            "        experiment: esm-hist"
        ]
        self.assertEqual(obj.print_content(add_content=False), [ref_str, ])
        self.assertEqual(obj.print_content(level=1, add_content=False), ["    " + ref_str, ])
        self.assertEqual(obj.print_content(), ref_str_2)
        self.assertEqual(obj.print_content(level=1), ["    " + elt for elt in ref_str_2])
        self.assertEqual(str(obj), os.linesep.join(ref_str_2))

    def test_eq(self):
        obj = ExperimentsGroup(id="link::my_id", dr=self.dr)
        obj2 = copy.deepcopy(obj)
        self.assertEqual(obj, obj2)

        obj3 = ExperimentsGroup(id="link::my_id_2", dr=self.dr)
        self.assertNotEqual(obj, obj3)

        obj4 = ExperimentsGroup(id="link::my_id", dr=self.dr, experiments=["link::amip", "link::esm-hist"])
        self.assertNotEqual(obj, obj4)

        obj5 = DRObjects(id="link::my_id", dr=self.dr)
        self.assertNotEqual(obj, obj5)

    def test_filter_on_request(self):
        exp_grp1 = self.dr.find_element("experiment_groups", "link::dcpp")
        exp_grp2 = copy.deepcopy(exp_grp1)
        exp_grp3 = self.dr.find_element("experiment_groups", "link::deck")
        exp_1 = self.dr.find_element("experiments", "link::dcppB-forecast-cmip6")
        exp_2 = self.dr.find_element("experiments", "link::esm-hist")
        obj = DRObjects(id="link::my_id", dr=self.dr)
        self.assertEqual(exp_grp1.filter_on_request(exp_grp2), (True, True))
        self.assertEqual(exp_grp1.filter_on_request(exp_grp3), (True, False))
        self.assertEqual(exp_grp1.filter_on_request(exp_1), (True, True))
        self.assertEqual(exp_grp1.filter_on_request(exp_2), (True, False))
        self.assertEqual(exp_grp1.filter_on_request(obj), (False, False))


class TestVariables(unittest.TestCase):
    def setUp(self):
        self.dr = DataRequest.from_separated_inputs(VS_input=filepath("VS_release_not-consolidate_content.json"),
                                                    DR_input=filepath("DR_release_not-consolidate_content.json"))

    def test_print(self):
        obj = self.dr.find_element("variable", "ocean.wo.tavg-ol-hxy-sea.mon.GLB")
        ref_str = 'variable: wo at frequency mon (id: ocean.wo.tavg-ol-hxy-sea.mon.GLB, title: Sea Water Vertical Velocity)'
        ref_str_2 = [
            ref_str,
        ]
        self.assertEqual(obj.print_content(add_content=False), [ref_str, ])
        self.assertEqual(obj.print_content(level=1, add_content=False), ["    " + ref_str, ])
        self.assertEqual(obj.print_content(), ref_str_2)
        self.assertEqual(obj.print_content(level=1), ["    " + elt for elt in ref_str_2])
        self.assertEqual(str(obj), os.linesep.join(ref_str_2))

    def test_filter_on_request(self):
        var_1 = self.dr.find_element("variable", "ocean.wo.tavg-ol-hxy-sea.mon.GLB")
        var_2 = copy.deepcopy(var_1)
        var_3 = self.dr.find_element("variable", "atmos.tas.tavg-h2m-hxy-u.day.GLB")
        table_1 = self.dr.find_element("table_identifier", "527f5d06-8c97-11ef-944e-41a8eb05f654")
        table_2 = self.dr.find_element("table_identifier", "527f5d03-8c97-11ef-944e-41a8eb05f654")
        tshp_1 = self.dr.find_element("temporal_shape", "cf34c974-80be-11e6-97ee-ac72891c3257")
        tshp_2 = self.dr.find_element("temporal_shape", "a06034e5-bbca-11ef-9840-9de7167a7ecb")
        sshp_1 = self.dr.find_element("spatial_shape", "a6562c2a-8883-11e5-b571-ac72891c3257")
        sshp_2 = self.dr.find_element("spatial_shape", "a6562a9a-8883-11e5-b571-ac72891c3257")
        param_1 = self.dr.find_element("physical_parameter", "d476e6113f5c466d27fd3aa9e9c35411")
        param_2 = self.dr.find_element("physical_parameter", "d76ba4c5868a0a9a02f433dc3c86d5d2")
        realm_1 = self.dr.find_element("modelling_realm", "ocean")
        realm_2 = self.dr.find_element("modelling_realm", "atmos")
        bcv_1 = self.dr.find_element("esm-bcv", "80ab7377-a698-11ef-914a-613c0433d878")
        bcv_2 = self.dr.find_element("esm-bcv", "80ab737f-a698-11ef-914a-613c0433d878")
        cf_1 = self.dr.find_element("cf_standard_name", "3ba9a909-8ca2-11ef-944e-41a8eb05f654")
        cf_2 = self.dr.find_element("cf_standard_name", "3ba9a9d3-8ca2-11ef-944e-41a8eb05f654")
        cell_method_1 = self.dr.find_element("cell_method", "a269a4cd-8c9b-11ef-944e-41a8eb05f654")
        cell_method_2 = self.dr.find_element("cell_method", "a269a4ce-8c9b-11ef-944e-41a8eb05f654")
        cell_measure_1 = self.dr.find_element("cell_measure", "a269a4f6-8c9b-11ef-944e-41a8eb05f654")
        cell_measure_2 = self.dr.find_element("cell_measure", "a269a4f4-8c9b-11ef-944e-41a8eb05f654")
        obj = DRObjects(id="link::my_id", dr=self.dr)
        self.assertEqual(var_1.filter_on_request(var_2), (True, True))
        self.assertEqual(var_1.filter_on_request(var_3), (True, False))
        self.assertEqual(var_1.filter_on_request(table_1), (True, True))
        self.assertEqual(var_1.filter_on_request(table_2), (True, False))
        self.assertEqual(var_1.filter_on_request(tshp_1), (True, True))
        self.assertEqual(var_1.filter_on_request(tshp_2), (True, False))
        self.assertEqual(var_1.filter_on_request(sshp_1), (True, True))
        self.assertEqual(var_1.filter_on_request(sshp_2), (True, False))
        self.assertEqual(var_1.filter_on_request(param_1), (True, True))
        self.assertEqual(var_1.filter_on_request(param_2), (True, False))
        self.assertEqual(var_1.filter_on_request(realm_1), (True, True))
        self.assertEqual(var_1.filter_on_request(realm_2), (True, False))
        self.assertEqual(var_1.filter_on_request(bcv_1), (True, True))
        self.assertEqual(var_1.filter_on_request(bcv_2), (True, False))
        self.assertEqual(var_1.filter_on_request(cf_1), (True, True))
        self.assertEqual(var_1.filter_on_request(cf_2), (True, False))
        self.assertEqual(var_1.filter_on_request(cell_method_1), (True, True))
        self.assertEqual(var_1.filter_on_request(cell_method_2), (True, False))
        self.assertEqual(var_1.filter_on_request(cell_measure_1), (True, True))
        self.assertEqual(var_1.filter_on_request(cell_measure_2), (True, False))
        self.assertEqual(var_1.filter_on_request(obj), (False, False))


class TestVariablesGroup(unittest.TestCase):
    def setUp(self):
        self.dr = DataRequest.from_separated_inputs(DR_input=filepath("DR_release_not-consolidate_content.json"),
                                                    VS_input=filepath("VS_release_not-consolidate_content.json"))

    def test_init(self):
        with self.assertRaises(TypeError):
            VariablesGroup()

        with self.assertRaises(TypeError):
            VariablesGroup("link::my_id")

        with self.assertRaises(TypeError):
            VariablesGroup(self.dr)

        obj = VariablesGroup("link::my_id", self.dr)
        self.assertEqual(obj.DR_type, "variable_groups")

        with self.assertRaises(ValueError):
            VariablesGroup("link::my_id", self.dr, name="test", physical_parameter="link::my_link")

    def test_from_input(self):
        with self.assertRaises(TypeError):
            VariablesGroup.from_input()

        with self.assertRaises(TypeError):
            VariablesGroup.from_input("link::my_id")

        with self.assertRaises(TypeError):
            VariablesGroup.from_input(self.dr)

        obj = VariablesGroup.from_input(id="link::my_id", dr=self.dr)

        with self.assertRaises(ValueError):
            obj = VariablesGroup.from_input(id="link:my_id", dr=self.dr, variables=["link::test", ])

        obj = VariablesGroup.from_input(id="link::my_id", dr=self.dr,
                                        variables=["link::atmos.pr.tavg-u-hxy-u.mon.GLB",
                                                   "link::atmos.prc.tavg-u-hxy-u.mon.GLB"])

    def test_check(self):
        obj = VariablesGroup(id="link::my_id", dr=self.dr)
        obj.check()

        obj = VariablesGroup(id="link::my_id", dr=self.dr,
                             variables=["link::atmos.pr.tavg-u-hxy-u.mon.GLB",
                                        "link::atmos.prc.tavg-u-hxy-u.mon.GLB"])
        obj.check()

    def test_methods(self):
        obj = VariablesGroup.from_input(id="link::my_id", dr=self.dr, priority_level="High")
        self.assertEqual(obj.count(), 0)
        self.assertEqual(obj.get_variables(), list())
        self.assertEqual(obj.get_mips(), list())
        self.assertEqual(obj.get_priority_level(), self.dr.find_element("priority_level", "High"))

        obj = VariablesGroup.from_input(id="link::dafc7484-8c95-11ef-944e-41a8eb05f654", dr=self.dr,
                                        variables=["link::atmos.pr.tavg-u-hxy-u.mon.GLB",
                                                   "link::atmos.prc.tavg-u-hxy-u.mon.GLB"],
                                        mips=["link::C4MIP", ], priority_level="High")
        self.assertEqual(obj.count(), 2)
        self.assertListEqual(obj.get_variables(),
                             [self.dr.find_element("variables", "link::atmos.pr.tavg-u-hxy-u.mon.GLB"),
                              self.dr.find_element("variables", "link::atmos.prc.tavg-u-hxy-u.mon.GLB")])
        self.assertEqual(obj.get_mips(), [self.dr.find_element("mips", "link::C4MIP")])
        self.assertDictEqual(obj.get_priority_level().attributes,
                             {'name': "High", "notes": "The variables support the core objectives of the opportunity.  These are required to make the opportunity viable.", "value": 2,
                              'id': "High", 'uid': '527f5c94-8c97-11ef-944e-41a8eb05f654'})

    def test_filter_on_request(self):
        var_grp1 = self.dr.find_element("variable_groups", "ocean_KE_vorticity_extremes")
        var_grp2 = copy.deepcopy(var_grp1)
        var_grp3 = self.dr.find_element("variable_groups", "ocean_temperature_extremes")
        var_2 = self.dr.find_element("variable", "ocean.tossq.tavg-u-hxy-sea.day.GLB")
        var_1 = self.dr.find_element("variable", "ocean.vos.tavg-u-hxy-sea.day.GLB")
        mip_2 = self.dr.find_element("mips", "CORDEX")
        mip_1 = self.dr.find_element("mips", "TIPMIP")
        prio_2 = self.dr.find_element("priority_level", "High")
        prio_1 = self.dr.find_element("priority_level", "Medium")
        max_prio_1 = self.dr.find_element("max_priority_level", "Medium")
        max_prio_2 = self.dr.find_element("max_priority_level", "High")
        table_1 = self.dr.find_element("table_identifier", "527f5d03-8c97-11ef-944e-41a8eb05f654")
        table_2 = self.dr.find_element("table_identifier", "527f5d06-8c97-11ef-944e-41a8eb05f654")
        tshp_1 = self.dr.find_element("temporal_shape", "cf34c974-80be-11e6-97ee-ac72891c3257")
        tshp_2 = self.dr.find_element("temporal_shape", "a06034e5-bbca-11ef-9840-9de7167a7ecb")
        sshp_1 = self.dr.find_element("spatial_shape", "a656047a-8883-11e5-b571-ac72891c3257")
        sshp_2 = self.dr.find_element("spatial_shape", "a65615fa-8883-11e5-b571-ac72891c3257")
        param_1 = self.dr.find_element("physical_parameter", "2fabd221-a80c-11ef-851e-c9d2077e3a3c")
        param_2 = self.dr.find_element("physical_parameter", "00e77372e8b909d9a827a0790e991fd9")
        realm_1 = self.dr.find_element("modelling_realm", "ocean")
        realm_2 = self.dr.find_element("modelling_realm", "atmos")
        bcv_2 = self.dr.find_element("esm-bcv", "link::80ab7303-a698-11ef-914a-613c0433d878")
        cf_std_1 = self.dr.find_element("cf_standard_name", "3ba8dccf-8ca2-11ef-944e-41a8eb05f654")
        cf_std_2 = self.dr.find_element("cf_standard_name", "3ba81236-8ca2-11ef-944e-41a8eb05f654")
        cell_method_1 = self.dr.find_element("cell_methods", "a269a4cd-8c9b-11ef-944e-41a8eb05f654")
        cell_method_2 = self.dr.find_element("cell_methods", "a269a4e2-8c9b-11ef-944e-41a8eb05f654")
        cell_measure_1 = self.dr.find_element("cell_measure", "link::a269a4f5-8c9b-11ef-944e-41a8eb05f654")
        cell_measure_2 = self.dr.find_element("cell_measure", "link::a269a4f4-8c9b-11ef-944e-41a8eb05f654")
        obj = DRObjects(id="link::my_id", dr=self.dr)
        self.assertEqual(var_grp1.filter_on_request(var_grp2), (True, True))
        self.assertEqual(var_grp1.filter_on_request(var_grp3), (True, False))
        self.assertEqual(var_grp1.filter_on_request(var_1), (True, True))
        self.assertEqual(var_grp1.filter_on_request(var_2), (True, False))
        self.assertEqual(var_grp1.filter_on_request(mip_1), (True, True))
        self.assertEqual(var_grp1.filter_on_request(mip_2), (True, False))
        self.assertEqual(var_grp1.filter_on_request(prio_1), (True, True))
        self.assertEqual(var_grp1.filter_on_request(prio_2), (True, False))
        self.assertEqual(var_grp1.filter_on_request(max_prio_1), (True, True))
        self.assertEqual(var_grp1.filter_on_request(max_prio_2), (True, False))
        self.assertEqual(var_grp1.filter_on_request(table_1), (True, True))
        self.assertEqual(var_grp1.filter_on_request(table_2), (True, False))
        self.assertEqual(var_grp1.filter_on_request(tshp_1), (True, True))
        self.assertEqual(var_grp1.filter_on_request(tshp_2), (True, False))
        self.assertEqual(var_grp1.filter_on_request(sshp_1), (True, True))
        self.assertEqual(var_grp1.filter_on_request(sshp_2), (True, False))
        self.assertEqual(var_grp1.filter_on_request(param_1), (True, True))
        self.assertEqual(var_grp1.filter_on_request(param_2), (True, False))
        self.assertEqual(var_grp1.filter_on_request(realm_1), (True, True))
        self.assertEqual(var_grp1.filter_on_request(realm_2), (True, False))
        self.assertEqual(var_grp1.filter_on_request(bcv_2), (True, False))
        self.assertEqual(var_grp1.filter_on_request(cf_std_1), (True, True))
        self.assertEqual(var_grp1.filter_on_request(cf_std_2), (True, False))
        self.assertEqual(var_grp1.filter_on_request(cell_method_1), (True, True))
        self.assertEqual(var_grp1.filter_on_request(cell_method_2), (True, False))
        self.assertEqual(var_grp1.filter_on_request(cell_measure_1), (True, True))
        self.assertEqual(var_grp1.filter_on_request(cell_measure_2), (True, False))
        self.assertEqual(var_grp1.filter_on_request(obj), (False, False))

    def test_print(self):
        obj = VariablesGroup.from_input(id="link::baseline_monthly", dr=self.dr, priority_level="Medium",
                                        name="baseline_monthly",
                                        variables=["link::atmos.pr.tavg-u-hxy-u.mon.GLB",
                                                   "link::atmos.prc.tavg-u-hxy-u.mon.GLB"])
        ref_str = "variable_group: baseline_monthly"
        ref_str_2 = [
            ref_str,
            "    Variables included:",
            "        variable: pr at frequency mon (id: atmos.pr.tavg-u-hxy-u.mon.GLB, title: Precipitation)",
            "        variable: prc at frequency mon (id: atmos.prc.tavg-u-hxy-u.mon.GLB, "
            "title: Convective Precipitation)"
        ]
        self.assertEqual(obj.print_content(add_content=False), [ref_str, ])
        self.assertEqual(obj.print_content(level=1, add_content=False), ["    " + ref_str, ])
        self.assertEqual(obj.print_content(), ref_str_2)
        self.assertEqual(obj.print_content(level=1), ["    " + elt for elt in ref_str_2])
        self.assertEqual(str(obj), os.linesep.join(ref_str_2))

    def test_eq(self):
        obj = VariablesGroup(id="link::my_id", dr=self.dr)
        obj2 = copy.deepcopy(obj)
        self.assertEqual(obj, obj2)

        obj3 = VariablesGroup(id="link::my_id_2", dr=self.dr)
        self.assertNotEqual(obj, obj3)

        obj4 = VariablesGroup(id="link::my_id", dr=self.dr, variables=["link::atmos.pr.tavg-u-hxy-u.mon.GLB",
                                                                       "link::atmos.prc.tavg-u-hxy-u.mon.GLB"])
        self.assertNotEqual(obj, obj4)

        obj5 = VariablesGroup(id="link::my_id", dr=self.dr, mips=["link::C4MIP", ])
        self.assertNotEqual(obj, obj5)

        obj6 = VariablesGroup(id="link::my_id", dr=self.dr, priority="Medium")
        self.assertNotEqual(obj, obj6)

        obj7 = DRObjects(id="link::my_id", dr=self.dr)
        self.assertNotEqual(obj, obj7)


class TestOpportunity(unittest.TestCase):
    def setUp(self):
        self.dr = DataRequest.from_separated_inputs(DR_input=filepath("DR_release_not-consolidate_content.json"),
                                                    VS_input=filepath("VS_release_not-consolidate_content.json"))

    def test_init(self):
        with self.assertRaises(TypeError):
            Opportunity()

        with self.assertRaises(TypeError):
            Opportunity("my_id")

        with self.assertRaises(TypeError):
            Opportunity(self.dr)

        obj = Opportunity("my_id", self.dr)

        obj = Opportunity(id="my_id", dr=self.dr, variables_groups=["test1", "test2"],
                          experiments_groups=["test3", "test4"], themes=["theme1", "theme2"])
        self.assertEqual(obj.DR_type, "opportunities")

    def test_from_input(self):
        with self.assertRaises(TypeError):
            Opportunity.from_input()

        with self.assertRaises(TypeError):
            Opportunity.from_input("my_id")

        with self.assertRaises(TypeError):
            Opportunity.from_input(self.dr)

        obj = Opportunity.from_input("my_id", self.dr)

        obj = Opportunity.from_input(id="my_id", dr=self.dr)

        with self.assertRaises(ValueError):
            obj = Opportunity.from_input(id="my_id", dr=self.dr, variable_groups=["test", ])

        obj = Opportunity.from_input(id="my_id", dr=self.dr,
                                     variable_groups=["link::surgemip_variables", "link::landatm_coupling_3hA"],
                                     experiment_groups=["link::fast-track", ],
                                     data_request_themes=["link::atmosphere", "link::earth_system",
                                                          "link::impacts"])

    def test_check(self):
        obj = Opportunity(id="my_id", dr=self.dr)
        obj.check()

        obj = Opportunity(id="my_id", dr=self.dr, variables_groups=["default_733", "default_734"])
        obj.check()

    def test_methods(self):
        obj = Opportunity(id="my_id", dr=self.dr)
        self.assertEqual(obj.get_experiment_groups(), list())
        self.assertEqual(obj.get_variable_groups(), list())
        self.assertEqual(obj.get_themes(), list())

        obj = Opportunity.from_input(id="link::default_425", dr=self.dr,
                                     variable_groups=["link::surgemip_variables", "link::landatm_coupling_3hA"],
                                     experiment_groups=["link::fast-track", ],
                                     data_request_themes=["link::earth_system", "link::impacts",
                                                          "link::ocean_seaice"])
        self.assertListEqual(obj.get_experiment_groups(), [self.dr.find_element("experiment_groups", "fast-track")])
        self.assertListEqual(obj.get_variable_groups(),
                             [self.dr.find_element("variable_groups", "link::surgemip_variables"),
                              self.dr.find_element("variable_groups", "link::landatm_coupling_3hA")])
        self.assertListEqual(obj.get_themes(),
                             [self.dr.find_element("data_request_themes", "link::earth_system"),
                              self.dr.find_element("data_request_themes", "link::impacts"),
                              self.dr.find_element("data_request_themes", "link::ocean_seaice")
                              ])

    def test_print(self):
        obj = Opportunity.from_input(id="link::Ocean Extremes", dr=self.dr, name="Ocean Extremes",
                                     variable_groups=["link::baseline_monthly", "link::baseline_subdaily"],
                                     experiment_groups=["link::fast-track", ],
                                     data_request_themes=["link::atmosphere", "link::impacts",
                                                          "link::land_landice"])
        ref_str = "opportunity: Ocean Extremes"
        ref_str_2 = [
            ref_str,
            "    Experiments groups included:",
            "        experiment_group: fast-track",
            "    Variables groups included:",
            "        variable_group: baseline_monthly",
            "        variable_group: baseline_subdaily",
            "    Themes included:",
            "        data_request_theme: Atmosphere (id: atmosphere)",
            "        data_request_theme: Impacts & Adaptation (id: impacts)",
            "        data_request_theme: Land & Land-Ice (id: land_landice)",
            "    Time subsets included:"
        ]
        self.assertEqual(obj.print_content(add_content=False), [ref_str, ])
        self.assertEqual(obj.print_content(level=1, add_content=False), ["    " + ref_str, ])
        self.assertEqual(obj.print_content(), ref_str_2)
        self.assertEqual(obj.print_content(level=1), ["    " + elt for elt in ref_str_2])
        self.assertEqual(str(obj), os.linesep.join(ref_str_2))

    def test_eq(self):
        obj = Opportunity(id="my_id", dr=self.dr)
        obj2 = copy.deepcopy(obj)
        self.assertEqual(obj, obj2)

        obj3 = Opportunity(id="my_id_2", dr=self.dr)
        self.assertNotEqual(obj, obj3)

        obj4 = Opportunity(id="my_id", dr=self.dr, experiments_groups=["fast-track", ])
        self.assertNotEqual(obj, obj4)

        obj5 = Opportunity(id="my_id", dr=self.dr, variables_groups=["default_733", "default_734"])
        self.assertNotEqual(obj, obj5)

        obj6 = Opportunity(id="my_id", dr=self.dr, themes=["63215c10-8ca5-11ef-944e-41a8eb05f654", "63215c11-8ca5-11ef-944e-41a8eb05f654", "default_106"])
        self.assertNotEqual(obj, obj6)

        obj7 = DRObjects(id="my_id", dr=self.dr)
        self.assertNotEqual(obj, obj7)

    def test_filter_on_request(self):
        op_1 = self.dr.find_element("opportunities", "Accurate assessment of land-atmosphere coupling")
        op_2 = copy.deepcopy(op_1)
        op_3 = self.dr.find_element("opportunities", "Ocean Extremes")
        theme_1 = self.dr.find_element("data_request_theme", "atmosphere")
        theme_2 = self.dr.find_element("data_request_theme", "ocean_seaice")
        var_grp_1 = self.dr.find_element("variable_group", "surgemip_variables")
        var_grp_2 = self.dr.find_element("variable_group", "landatm_coupling_3hA")
        exp_grp_1 = self.dr.find_element("experiment_group", "historical")
        exp_grp_2 = self.dr.find_element("experiment_group", "fast-track")
        exp_1 = self.dr.find_element("experiment", "esm-hist")
        exp_2 = self.dr.find_element("experiment", "piClim-NOX")
        time_1 = self.dr.find_element("time_subset", "link::hist20")
        var_2 = self.dr.find_element("variable", "atmos.tas.tavg-h2m-hxy-u.day.GLB")
        var_1 = self.dr.find_element("variable", "ocean.vos.tavg-u-hxy-sea.day.GLB")
        mip_2 = self.dr.find_element("mips", "LUMIP")
        mip_1 = self.dr.find_element("mips", "TIPMIP")
        prio_2 = self.dr.find_element("priority_level", "High")
        prio_1 = self.dr.find_element("priority_level", "Medium")
        max_prio_1 = self.dr.find_element("max_priority_level", "Medium")
        max_prio_2 = self.dr.find_element("max_priority_level", "High")
        table_1 = self.dr.find_element("table_identifier", "527f5d03-8c97-11ef-944e-41a8eb05f654")
        table_2 = self.dr.find_element("table_identifier", "527f5ce9-8c97-11ef-944e-41a8eb05f654")
        tshp_1 = self.dr.find_element("temporal_shape", "cf34c974-80be-11e6-97ee-ac72891c3257")
        tshp_2 = self.dr.find_element("temporal_shape", "a06034e5-bbca-11ef-9840-9de7167a7ecb")
        sshp_1 = self.dr.find_element("spatial_shape", "a656047a-8883-11e5-b571-ac72891c3257")
        sshp_2 = self.dr.find_element("spatial_shape", "a65615fa-8883-11e5-b571-ac72891c3257")
        param_1 = self.dr.find_element("physical_parameter", "0e5d376315a376cd2b1e37f440fe43d3")
        param_2 = self.dr.find_element("physical_parameter", "00e77372e8b909d9a827a0790e991fd9")
        realm_1 = self.dr.find_element("modelling_realm", "ocean")
        realm_2 = self.dr.find_element("modelling_realm", "land")
        bcv_2 = self.dr.find_element("esm-bcv", "link::80ab7303-a698-11ef-914a-613c0433d878")
        cf_std_1 = self.dr.find_element("cf_standard_name", "3ba812a0-8ca2-11ef-944e-41a8eb05f654")
        cf_std_2 = self.dr.find_element("cf_standard_name", "3ba8dadd-8ca2-11ef-944e-41a8eb05f654")
        cell_method_1 = self.dr.find_element("cell_methods", "a269a4cd-8c9b-11ef-944e-41a8eb05f654")
        cell_method_2 = self.dr.find_element("cell_methods", "a269a4c3-8c9b-11ef-944e-41a8eb05f654")
        cell_measure_1 = self.dr.find_element("cell_measure", "link::a269a4f5-8c9b-11ef-944e-41a8eb05f654")
        obj = DRObjects(id="link::my_id", dr=self.dr)
        self.assertEqual(op_1.filter_on_request(op_2), (True, True))
        self.assertEqual(op_1.filter_on_request(op_3), (True, False))
        self.assertEqual(op_1.filter_on_request(theme_1), (True, True))
        self.assertEqual(op_1.filter_on_request(theme_2), (True, False))
        self.assertEqual(op_1.filter_on_request(exp_1), (True, True))
        self.assertEqual(op_1.filter_on_request(exp_2), (True, False))
        self.assertEqual(op_1.filter_on_request(time_1), (True, True))
        self.assertEqual(op_3.filter_on_request(time_1), (True, False))
        self.assertEqual(op_1.filter_on_request(exp_grp_1), (True, True))
        self.assertEqual(op_1.filter_on_request(exp_grp_2), (True, False))
        self.assertEqual(op_1.filter_on_request(var_grp_2), (True, True))
        self.assertEqual(op_1.filter_on_request(var_grp_1), (True, False))
        self.assertEqual(op_3.filter_on_request(var_1), (True, True))
        self.assertEqual(op_3.filter_on_request(var_2), (True, False))
        self.assertEqual(op_3.filter_on_request(mip_1), (True, True))
        self.assertEqual(op_3.filter_on_request(mip_2), (True, False))
        self.assertEqual(op_3.filter_on_request(prio_1), (True, True))
        self.assertEqual(op_3.filter_on_request(prio_2), (True, True))
        self.assertEqual(op_3.filter_on_request(max_prio_1), (True, True))
        self.assertEqual(op_3.filter_on_request(max_prio_2), (True, True))
        self.assertEqual(op_3.filter_on_request(table_1), (True, True))
        self.assertEqual(op_3.filter_on_request(table_2), (True, False))
        self.assertEqual(op_3.filter_on_request(tshp_1), (True, True))
        self.assertEqual(op_3.filter_on_request(tshp_2), (True, False))
        self.assertEqual(op_3.filter_on_request(sshp_1), (True, True))
        self.assertEqual(op_3.filter_on_request(sshp_2), (True, False))
        self.assertEqual(op_3.filter_on_request(param_1), (True, True))
        self.assertEqual(op_3.filter_on_request(param_2), (True, False))
        self.assertEqual(op_3.filter_on_request(realm_1), (True, True))
        self.assertEqual(op_3.filter_on_request(realm_2), (True, False))
        self.assertEqual(op_3.filter_on_request(bcv_2), (True, False))
        self.assertEqual(op_3.filter_on_request(cf_std_1), (True, True))
        self.assertEqual(op_3.filter_on_request(cf_std_2), (True, False))
        self.assertEqual(op_3.filter_on_request(cell_method_1), (True, True))
        self.assertEqual(op_3.filter_on_request(cell_method_2), (True, False))
        self.assertEqual(op_3.filter_on_request(cell_measure_1), (True, True))
        self.assertEqual(op_1.filter_on_request(cell_measure_1), (True, False))
        self.assertEqual(op_3.filter_on_request(obj), (False, False))


class TestDataRequest(unittest.TestCase):
    def setUp(self):
        self.vs_file = filepath("VS_release_not-consolidate_content.json")
        self.vs_dict = read_json_input_file_content(self.vs_file)
        self.vs = VocabularyServer.from_input(self.vs_file)
        self.input_database_file = filepath("DR_release_not-consolidate_content.json")
        self.input_database = read_json_input_file_content(self.input_database_file)
        self.complete_input_file = filepath("dreq_release_export.json")
        self.complete_input = read_json_input_file_content(self.complete_input_file)
        self.DR_dump = filepath("DR_release_not-consolidate_content_dump.txt")

    def test_init(self):
        with self.assertRaises(TypeError):
            DataRequest()

        with self.assertRaises(TypeError):
            DataRequest(self.vs)

        with self.assertRaises(TypeError):
            DataRequest(self.input_database)

        obj = DataRequest(input_database=self.input_database, VS=self.vs)
        self.assertEqual(len(obj.get_experiment_groups()), 6)
        self.assertEqual(len(obj.get_variable_groups()), 13)
        self.assertEqual(len(obj.get_opportunities()), 4)

    def test_from_input(self):
        with self.assertRaises(TypeError):
            DataRequest.from_input()

        with self.assertRaises(TypeError):
            DataRequest.from_input(self.complete_input)

        with self.assertRaises(TypeError):
            DataRequest.from_input("test")

        with self.assertRaises(TypeError):
            DataRequest.from_input(self.input_database, version=self.vs)

        with self.assertRaises(TypeError):
            DataRequest.from_input(self.complete_input_file + "tmp", version="test")

        obj = DataRequest.from_input(json_input=self.complete_input, version="test")
        self.assertEqual(len(obj.get_experiment_groups()), 6)
        self.assertEqual(len(obj.get_variable_groups()), 13)
        self.assertEqual(len(obj.get_opportunities()), 4)

        obj = DataRequest.from_input(json_input=self.complete_input_file, version="test")
        self.assertEqual(len(obj.get_experiment_groups()), 6)
        self.assertEqual(len(obj.get_variable_groups()), 13)
        self.assertEqual(len(obj.get_opportunities()), 4)

    def test_from_separated_inputs(self):
        with self.assertRaises(TypeError):
            DataRequest.from_separated_inputs()

        with self.assertRaises(TypeError):
            DataRequest.from_separated_inputs(self.input_database)

        with self.assertRaises(TypeError):
            DataRequest.from_separated_inputs(self.vs)

        with self.assertRaises(TypeError):
            DataRequest.from_separated_inputs(DR_input=self.input_database, VS_input=self.vs_file + "tmp")

        with self.assertRaises(TypeError):
            DataRequest.from_separated_inputs(DR_input=self.input_database_file + "tmp", VS_input=self.vs_dict)

        with self.assertRaises(TypeError):
            DataRequest.from_separated_inputs(DR_input=self.input_database_file, VS_input=self.vs)

        obj = DataRequest.from_separated_inputs(DR_input=self.input_database, VS_input=self.vs_dict)
        self.assertEqual(len(obj.get_experiment_groups()), 6)
        self.assertEqual(len(obj.get_variable_groups()), 13)
        self.assertEqual(len(obj.get_opportunities()), 4)

        obj = DataRequest.from_separated_inputs(DR_input=self.input_database_file, VS_input=self.vs_dict)
        self.assertEqual(len(obj.get_experiment_groups()), 6)
        self.assertEqual(len(obj.get_variable_groups()), 13)
        self.assertEqual(len(obj.get_opportunities()), 4)

        obj = DataRequest.from_separated_inputs(DR_input=self.input_database, VS_input=self.vs_file)
        self.assertEqual(len(obj.get_experiment_groups()), 6)
        self.assertEqual(len(obj.get_variable_groups()), 13)
        self.assertEqual(len(obj.get_opportunities()), 4)

        obj = DataRequest.from_separated_inputs(DR_input=self.input_database_file, VS_input=self.vs_file)
        self.assertEqual(len(obj.get_experiment_groups()), 6)
        self.assertEqual(len(obj.get_variable_groups()), 13)
        self.assertEqual(len(obj.get_opportunities()), 4)

    def test_split_content_from_input_json(self):
        with self.assertRaises(TypeError):
            DataRequest._split_content_from_input_json()

        with self.assertRaises(TypeError):
            DataRequest._split_content_from_input_json(self.complete_input)

        with self.assertRaises(TypeError):
            DataRequest._split_content_from_input_json("test")

        with self.assertRaises(TypeError):
            DataRequest._split_content_from_input_json(self.input_database, version=self.vs)

        with self.assertRaises(TypeError):
            DataRequest._split_content_from_input_json(self.complete_input_file + "tmp", version="test")

        DR, VS = DataRequest._split_content_from_input_json(input_json=self.complete_input, version="test")
        self.assertDictEqual(DR, self.input_database)
        self.assertDictEqual(VS, self.vs_dict)

        DR, VS = DataRequest._split_content_from_input_json(input_json=self.complete_input_file, version="test")
        self.assertDictEqual(DR, self.input_database)
        self.assertDictEqual(VS, self.vs_dict)

    def test_check(self):
        obj = DataRequest(input_database=self.input_database, VS=self.vs)
        obj.check()

    def test_version(self):
        obj = DataRequest(input_database=self.input_database, VS=self.vs)
        self.assertEqual(obj.software_version, version)
        self.assertEqual(obj.content_version, self.input_database["version"])
        self.assertEqual(obj.version, f"Software {version} - Content {self.input_database['version']}")

    def test_str(self):
        obj = DataRequest(input_database=self.input_database, VS=self.vs)
        with open(self.DR_dump, encoding="utf-8", newline="\n") as f:
            ref_str = f.read()
        self.assertEqual(str(obj), ref_str)

    def test_get_experiment_groups(self):
        obj = DataRequest(input_database=self.input_database, VS=self.vs)
        exp_groups = obj.get_experiment_groups()
        self.assertEqual(len(exp_groups), 6)
        self.assertListEqual(exp_groups,
                             [obj.find_element("experiment_groups", id)
                              for id in ["dcpp", "deck", "fast-track", "historical",
                                         "scenarios", "scenarios_extensions"]])

    def test_get_experiment_group(self):
        obj = DataRequest(input_database=self.input_database, VS=self.vs)
        exp_grp = obj.get_experiment_group("link::fast-track")
        self.assertEqual(exp_grp,
                         obj.find_element("experiment_groups", "link::fast-track"))
        with self.assertRaises(ValueError):
            exp_grp = obj.get_experiment_group("test")

    def test_get_opportunities(self):
        obj = DataRequest(input_database=self.input_database, VS=self.vs)
        opportunities = obj.get_opportunities()
        self.assertEqual(len(opportunities), 4)
        self.assertListEqual(opportunities, [obj.find_element("opportunities", id)
                                             for id in ["1", "49", "68", "69"]])

    def test_get_opportunity(self):
        obj = DataRequest(input_database=self.input_database, VS=self.vs)
        opportunity = obj.get_opportunity("link::Accurate assessment of land-atmosphere coupling")
        self.assertEqual(opportunity,
                         obj.find_element("opportunities", "link::Accurate assessment of land-atmosphere coupling"))
        with self.assertRaises(ValueError):
            op = obj.get_opportunity("test")

    def test_get_variable_groups(self):
        obj = DataRequest(input_database=self.input_database, VS=self.vs)
        var_groups = obj.get_variable_groups()
        self.assertEqual(len(var_groups), 13)
        self.assertListEqual(var_groups,
                             [obj.find_element("variable_groups", id)
                              for id in ["baseline_daily", "baseline_fixed", "baseline_monthly", "baseline_subdaily",
                                         "landatm_coupling_3hA", "landatm_coupling_3hr_medium", "mixed_layer_extremes",
                                         "ocean_KE_vorticity_extremes", "ocean_acidification_oxygen_extremes",
                                         "ocean_temperature_extremes", "sea_level_extremes", "sfc_waves",
                                         "surgemip_variables"]])

    def test_get_variable_group(self):
        obj = DataRequest(input_database=self.input_database, VS=self.vs)
        var_grp = obj.get_variable_group("link::baseline_monthly")
        self.assertEqual(var_grp,
                         obj.find_element("variable_groups", "link::baseline_monthly"))
        with self.assertRaises(ValueError):
            var_grp = obj.get_variable_group("test")

    def test_get_variables(self):
        obj = DataRequest(input_database=self.input_database, VS=self.vs)
        variables = obj.get_variables()
        self.assertListEqual(variables,
                             [obj.find_element("variables", f"link::{nb}")
                              for nb in sorted(list(self.vs.vocabulary_server["variables"]))])

    def test_get_mips(self):
        obj = DataRequest(input_database=self.input_database, VS=self.vs)
        mips = obj.get_mips()
        self.assertListEqual(mips,
                             [obj.find_element("mips", f"link::{nb}")
                              for nb in sorted(list(self.vs.vocabulary_server["mips"]))])

    def test_get_experiments(self):
        obj = DataRequest(input_database=self.input_database, VS=self.vs)
        experiments = obj.get_experiments()
        self.assertListEqual(experiments,
                             [obj.find_element("experiments", f"link::{nb}")
                              for nb in sorted(list(self.vs.vocabulary_server["experiments"]))])

    def test_get_themes(self):
        obj = DataRequest(input_database=self.input_database, VS=self.vs)
        themes = obj.get_data_request_themes()
        self.assertListEqual(themes,
                             [obj.find_element("data_request_themes", f"link::{nb}")
                              for nb in sorted(list(self.vs.vocabulary_server["data_request_themes"]))])

    def test_get_filtering_structure(self):
        obj = DataRequest(input_database=self.input_database, VS=self.vs)
        self.assertSetEqual(obj.get_filtering_structure("variable_groups"), {"opportunities", })
        self.assertSetEqual(obj.get_filtering_structure("variables"), {"opportunities", "variable_groups"})
        self.assertSetEqual(obj.get_filtering_structure("physical_parameters"), {"opportunities", "variable_groups", "variables"})
        self.assertSetEqual(obj.get_filtering_structure("experiment_groups"), {"opportunities", })
        self.assertSetEqual(obj.get_filtering_structure("experiments"), {"opportunities", "experiment_groups"})
        self.assertSetEqual(obj.get_filtering_structure("test"), set())
        self.assertSetEqual(obj.get_filtering_structure("opportunities"), set())

    def test_find_element(self):
        obj = DataRequest(input_database=self.input_database, VS=self.vs)
        elt1 = obj.find_element("theme", "Atmosphere")
        self.assertEqual(elt1.DR_type, "data_request_themes")
        elt2 = obj.find_element("priority_level", "Medium")
        self.assertEqual(elt2.DR_type, "priority_levels")
        elt3 = obj.find_element("max_priority_level", "High")
        self.assertEqual(elt3.DR_type, "max_priority_levels")


class TestDataRequestFilter(unittest.TestCase):
    def setUp(self):
        self.vs_file = filepath("VS_release_not-consolidate_content.json")
        self.vs = VocabularyServer.from_input(self.vs_file)
        self.input_database_file = filepath("DR_release_not-consolidate_content.json")
        self.input_database = read_json_input_file_content(self.input_database_file)
        self.dr = DataRequest(input_database=self.input_database, VS=self.vs)
        self.exp_export = filepath("experiments_export.txt")
        self.exp_expgrp_summmary = filepath("exp_expgrp_summary.txt")
        self.maxDiff = None

    def test_element_per_identifier_from_vs(self):
        id_var = "link::ocean.wo.tavg-ol-hxy-sea.mon.GLB"
        name_var = "ocean.wo.tavg-ol-hxy-sea.mon.GLB"
        target_var = self.dr.find_element("variables", id_var)
        self.assertEqual(self.dr.find_element_per_identifier_from_vs(element_type="variables", key="id", value=id_var),
                         target_var)
        self.assertEqual(self.dr.find_element_per_identifier_from_vs(element_type="variables", key="name",
                                                                     value=name_var),
                         target_var)
        with self.assertRaises(ValueError):
            self.dr.find_element_per_identifier_from_vs(element_type="variables", key="name", value="toto")
        with self.assertRaises(ValueError):
            self.dr.find_element_per_identifier_from_vs(element_type="variables", key="id", value="link::toto")
        self.assertEqual(self.dr.find_element_per_identifier_from_vs(element_type="variables", key="id",
                                                                     value="link::toto", default=None),
                         None)
        self.assertEqual(self.dr.find_element_per_identifier_from_vs(element_type="variables", key="name",
                                                                     value="toto", default=None),
                         None)
        with self.assertRaises(ValueError):
            self.dr.find_element_per_identifier_from_vs(element_type="opportunity/variable_group_comments", key="name",
                                                        value="undef")

        self.assertEqual(self.dr.find_element_per_identifier_from_vs(element_type="variable", value=None, key="id", default=None),
                         None)

    def test_element_from_vs(self):
        id_var = "link::ocean.wo.tavg-ol-hxy-sea.mon.GLB"
        name_var = "ocean.wo.tavg-ol-hxy-sea.mon.GLB"
        target_var = self.dr.find_element("variables", id_var)
        self.assertEqual(self.dr.find_element_from_vs(element_type="variables", value=id_var), target_var)
        self.assertEqual(self.dr.find_element_from_vs(element_type="variables", value=name_var), target_var)
        with self.assertRaises(ValueError):
            self.dr.find_element_from_vs(element_type="variables", value="toto")
        with self.assertRaises(ValueError):
            self.dr.find_element_from_vs(element_type="variables", value="link::toto")
        self.assertEqual(self.dr.find_element_from_vs(element_type="variables", value="link::toto", default=None), None)
        self.assertEqual(self.dr.find_element_from_vs(element_type="variables", value="toto", default=None), None)
        with self.assertRaises(ValueError):
            self.dr.find_element_from_vs(element_type="opportunity/variable_group_comments", value="undef")
        self.assertEqual(self.dr.find_element_from_vs(element_type="variables", value=id_var, key="id"), target_var)

    def test_filter_elements_per_request(self):
        with self.assertRaises(TypeError):
            self.dr.filter_elements_per_request()

        self.assertEqual(self.dr.filter_elements_per_request("opportunities"), self.dr.get_opportunities())
        self.assertEqual(self.dr.filter_elements_per_request("opportunities", request_operation="any"),
                         self.dr.get_opportunities())
        with self.assertRaises(ValueError):
            self.dr.filter_elements_per_request("opportunities", request_operation="one")

        with self.assertRaises(ValueError):
            self.dr.filter_elements_per_request("opportunities", requests=dict(variables="link::test_dummy"))
        self.assertListEqual(self.dr.filter_elements_per_request("opportunities", skip_if_missing=True,
                                                                 requests=dict(variables="link::test_dummy")),
                             self.dr.get_opportunities())

        self.assertListEqual(self.dr.filter_elements_per_request("experiment_groups",
                                                                 requests=dict(variable="ocean.wo.tavg-ol-hxy-sea.mon.GLB")),
                             [self.dr.find_element("experiment_group", id)
                              for id in ["link::deck", "link::fast-track", "link::historical", "link::scenarios",
                                         "link::scenarios_extensions"]])
        list_var_grp = [self.dr.find_element("variable_groups", id)
                        for id in ["link::baseline_daily", "link::baseline_fixed", "link::baseline_monthly",
                                   "link::baseline_subdaily", "link::mixed_layer_extremes",
                                   "link::ocean_KE_vorticity_extremes", "link::ocean_acidification_oxygen_extremes",
                                   "link::ocean_temperature_extremes", "link::sea_level_extremes", "link::sfc_waves",
                                   "link::surgemip_variables"]]
        self.assertListEqual(self.dr.filter_elements_per_request("variable_groups",
                                                                 requests=dict(experiment="scen7-hc-ext")),
                             list_var_grp)
        found_vargrp_all = self.dr.filter_elements_per_request("variable_groups",
                                                               requests=dict(experiment="scen7-hc-ext"),
                                                               not_requests=dict(
                                                                   opportunity="Effects and Feedbacks of Wind-Driven Ocean Surface Waves Coupled Within Earth System Models",
                                                                   variable=["ocean.tos.tpt-u-hxy-sea.3hr.GLB", "seaIce.sithick.tavg-u-hxy-si.day.GLB"]),
                                                               not_request_operation="all")
        self.assertEqual(len(found_vargrp_all), len(list_var_grp))
        self.assertListEqual(found_vargrp_all, list_var_grp)
        found_vargrp_any = self.dr.filter_elements_per_request("variable_groups",
                                                               requests=dict(experiment="scen7-hc-ext"),
                                                               not_requests=dict(
                                                                   opportunity="Effects and Feedbacks of Wind-Driven Ocean Surface Waves Coupled Within Earth System Models",
                                                                   variable=["ocean.tos.tpt-u-hxy-sea.3hr.GLB", "seaIce.sithick.tavg-u-hxy-si.day.GLB"]),
                                                               not_request_operation="any")
        list_vargrp_any = [self.dr.find_element("variable_group", elt)
                           for elt in ["link::mixed_layer_extremes", "link::ocean_KE_vorticity_extremes",
                                       "link::ocean_acidification_oxygen_extremes", "link::sea_level_extremes"]]
        self.assertEqual(len(found_vargrp_any), len(list_vargrp_any))
        self.assertListEqual(found_vargrp_any, list_vargrp_any)
        found_vargrp_anyofall = self.dr.filter_elements_per_request("variable_groups",
                                                                    requests=dict(experiment="scen7-hc-ext"),
                                                                    not_requests=dict(
                                                                        opportunity="Effects and Feedbacks of Wind-Driven Ocean Surface Waves Coupled Within Earth System Models",
                                                                        variable=["ocean.tos.tpt-u-hxy-sea.3hr.GLB", "seaIce.sithick.tavg-u-hxy-si.day.GLB"]),
                                                                    not_request_operation="any_of_all")
        list_vargrp_anyofall = [self.dr.find_element("variable_group", elt)
                                for elt in ["link::mixed_layer_extremes", "link::ocean_KE_vorticity_extremes",
                                            "link::ocean_acidification_oxygen_extremes", "link::ocean_temperature_extremes",
                                            "link::sea_level_extremes"]]
        self.assertEqual(len(found_vargrp_anyofall), len(list_vargrp_anyofall))
        self.assertListEqual(found_vargrp_anyofall, list_vargrp_anyofall)
        found_vargrp_allofany = self.dr.filter_elements_per_request("variable_groups",
                                                                    requests=dict(experiment="scen7-hc-ext"),
                                                                    not_requests=dict(
                                                                        opportunity="Effects and Feedbacks of Wind-Driven Ocean Surface Waves Coupled Within Earth System Models",
                                                                        variable=["ocean.tos.tpt-u-hxy-sea.3hr.GLB", "seaIce.sithick.tavg-u-hxy-si.day.GLB"]),
                                                                    not_request_operation="all_of_any")
        self.assertEqual(len(found_vargrp_allofany), len(list_var_grp))
        self.assertListEqual(found_vargrp_allofany, list_var_grp)
        self.assertListEqual(self.dr.filter_elements_per_request("variable_groups",
                                                                 requests=dict(experiment="scen7-hc-ext"),
                                                                 not_requests=dict(opportunity="Effects and Feedbacks of Wind-Driven Ocean Surface Waves Coupled Within Earth System Models")),
                             [self.dr.find_element("variable_group", elt)
                              for elt in ["link::mixed_layer_extremes", "link::ocean_KE_vorticity_extremes",
                                          "link::ocean_acidification_oxygen_extremes", "link::ocean_temperature_extremes",
                                          "link::sea_level_extremes", "link::surgemip_variables"]])
        self.assertListEqual(self.dr.filter_elements_per_request(self.dr.get_variable_groups(),
                                                                 requests=dict(experiment="scen7-hc-ext")),
                             list_var_grp)
        self.assertListEqual(self.dr.filter_elements_per_request(self.dr.get_variable_group("ocean_temperature_extremes"),
                                                                 requests=dict(experiment="scen7-hc-ext")),
                             [self.dr.find_element("variable_group", "ocean_temperature_extremes"), ])

    def test_find_variables_per_priority(self):
        priority = "Medium"
        priority_obj = self.dr.find_element("priority_level", "link::Medium")
        target_var_list = [self.dr.find_element("variables", id)
                           for id in ["link::atmos.rlds.tavg-u-hxy-u.3hr.GLB", "link::atmos.rlus.tavg-u-hxy-u.3hr.GLB",
                                      "link::atmos.ta.tpt-p6-hxy-air.3hr.GLB", "link::land.hfdsl.tavg-u-hxy-lnd.3hr.GLB",
                                      "link::land.mrsol.tavg-d100cm-hxy-lnd.3hr.GLB", "link::land.tran.tavg-u-hxy-u.3hr.GLB",
                                      "link::ocean.so.tavg-ol-hxy-sea.day.GLB", "link::ocean.sos.tavg-u-hxy-sea.day.GLB",
                                      "link::ocean.thetao.tavg-op20bar-hxy-sea.day.GLB", "link::ocean.tnkebto.tavg-u-hxy-sea.yr.GLB",
                                      "link::ocean.tos.tavg-u-hxy-sea.day.GLB", "link::ocean.uos.tavg-u-hxy-sea.day.GLB",
                                      "link::ocean.vos.tavg-u-hxy-sea.day.GLB", "link::ocnBgchem.arag.tavg-d0m-hxy-sea.mon.GLB",
                                      "link::ocnBgchem.arag.tavg-ol-hxy-sea.mon.GLB", "link::ocnBgchem.calc.tavg-d0m-hxy-sea.mon.GLB",
                                      "link::ocnBgchem.calc.tavg-ol-hxy-sea.mon.GLB", "link::ocnBgchem.chl.tavg-op20bar-hxy-sea.day.GLB",
                                      "link::ocnBgchem.dissic.tavg-ol-hxy-sea.mon.GLB", "link::ocnBgchem.o2.tavg-op20bar-hxy-sea.day.GLB",
                                      "link::ocnBgchem.ph.tavg-op20bar-hxy-sea.day.GLB", "link::ocnBgchem.talk.tavg-ol-hxy-sea.mon.GLB"]]
        var_list = self.dr.find_variables_per_priority(priority=priority)
        self.assertEqual(len(var_list), 22)
        self.assertListEqual(var_list, target_var_list)
        var_list = self.dr.find_variables_per_priority(priority=priority_obj)
        self.assertEqual(len(var_list), 22)
        self.assertListEqual(var_list, target_var_list)

    def test_find_opportunities_per_theme(self):
        theme_id = "link::atmosphere"
        theme_name = "Atmosphere"
        theme_target = self.dr.find_element("data_request_themes", theme_id)
        opportunities = [self.dr.get_opportunity(id)
                         for id in ["link::1", "link::68", "link::69"]]
        self.assertListEqual(self.dr.find_opportunities_per_theme(theme_id), opportunities)
        self.assertListEqual(self.dr.find_opportunities_per_theme(theme_name), opportunities)
        self.assertListEqual(self.dr.find_opportunities_per_theme(theme_target), opportunities)
        with self.assertRaises(ValueError):
            self.dr.find_opportunities_per_theme("toto")
        with self.assertRaises(ValueError):
            self.dr.find_opportunities_per_theme("link::toto")

    def test_find_experiments_per_theme(self):
        theme_id = "link::land_landice"
        theme_name = "Land & Land-Ice"
        theme_target = self.dr.find_element("data_request_themes", theme_id)
        exp = [self.dr.find_element("experiments", id)
               for id in ["link::amip", "link::dcppB-forecast-cmip6", "link::esm-flat10", "link::esm-hist",
                          "link::esm-piControl", "link::g7-1p5K-sai", "link::historical", "link::land-hist",
                          "link::piClim-NOX", "link::scen7-hc", "link::scen7-mc", "link::scen7-mlc",
                          "link::scen7-vlloc"]]
        self.assertListEqual(self.dr.find_experiments_per_theme(theme_id), exp)
        self.assertListEqual(self.dr.find_experiments_per_theme(theme_name), exp)
        self.assertListEqual(self.dr.find_experiments_per_theme(theme_target), exp)

    def test_find_variables_per_theme(self):
        theme_id = "link::land_landice"
        theme_name = "Land & Land-Ice"
        theme_target = self.dr.find_element("data_request_themes", theme_id)
        var = [self.dr.find_element("variables", id)
               for id in ["link::atmos.areacell.ti-u-hxy-u.fx.GLB", "link::atmos.bldep.tpt-u-hxy-u.3hr.GLB",
                          "link::atmos.hfls.tavg-u-hxy-u.3hr.GLB", "link::atmos.hfss.tavg-u-hxy-u.3hr.GLB",
                          "link::atmos.hurs.tavg-h2m-hxy-u.6hr.GLB", "link::atmos.huss.tpt-h2m-hxy-u.3hr.GLB",
                          "link::atmos.pr.tavg-u-hxy-u.1hr.GLB", "link::atmos.pr.tavg-u-hxy-u.3hr.GLB",
                          "link::atmos.pr.tavg-u-hxy-u.day.GLB", "link::atmos.pr.tavg-u-hxy-u.mon.GLB",
                          "link::atmos.prc.tavg-u-hxy-u.mon.GLB", "link::atmos.ps.tavg-u-hxy-u.day.GLB",
                          "link::atmos.ps.tpt-u-hxy-u.3hr.GLB", "link::atmos.psl.tavg-u-hxy-u.day.GLB",
                          "link::atmos.rlds.tavg-u-hxy-u.3hr.GLB", "link::atmos.rlus.tavg-u-hxy-u.3hr.GLB",
                          "link::atmos.sfcWind.tavg-h10m-hxy-u.day.GLB", "link::atmos.sfcWind.tavg-h10m-hxy-u.mon.GLB",
                          "link::atmos.sftlf.ti-u-hxy-u.fx.GLB", "link::atmos.ta.tavg-p19-hxy-air.day.GLB",
                          "link::atmos.ta.tavg-p19-hxy-air.mon.GLB", "link::atmos.ta.tpt-p3-hxy-air.6hr.GLB",
                          "link::atmos.ta.tpt-p6-hxy-air.3hr.GLB", "link::atmos.tas.tavg-h2m-hxy-u.day.GLB",
                          "link::atmos.tas.tavg-h2m-hxy-u.mon.GLB", "link::atmos.tas.tmax-h2m-hxy-u.day.GLB",
                          "link::atmos.tas.tmax-h2m-hxy-u.mon.GLB", "link::atmos.tas.tmin-h2m-hxy-u.day.GLB",
                          "link::atmos.tas.tmin-h2m-hxy-u.mon.GLB", "link::atmos.tas.tpt-h2m-hxy-u.3hr.GLB",
                          "link::atmos.ts.tavg-u-hxy-u.mon.GLB", "link::atmos.zg.tavg-p19-hxy-air.day.GLB",
                          "link::atmos.zg.tavg-p19-hxy-air.mon.GLB", "link::land.hfdsl.tavg-u-hxy-lnd.3hr.GLB",
                          "link::land.lai.tavg-u-hxy-lnd.mon.GLB", "link::land.mrso.tavg-u-hxy-lnd.mon.GLB",
                          "link::land.mrsol.tavg-d100cm-hxy-lnd.3hr.GLB", "land.mrsol.tavg-d10cm-hxy-lnd.mon.GLB",
                          "link::land.mrsol.tpt-d10cm-hxy-lnd.3hr.GLB", "link::land.orog.ti-u-hxy-u.fx.GLB",
                          "link::land.rootd.ti-u-hxy-lnd.fx.GLB", "link::land.slthick.ti-sl-hxy-lnd.fx.GLB",
                          "link::land.srfrad.tavg-u-hxy-u.3hr.GLB", "link::land.tran.tavg-u-hxy-u.3hr.GLB",
                          "link::land.tslsi.tpt-u-hxy-u.3hr.GLB", "link::landIce.snc.tavg-u-hxy-lnd.mon.GLB",
                          "link::ocean.areacell.ti-u-hxy-u.fx.GLB", "link::ocean.bigthetao.tavg-ol-hxy-sea.mon.GLB",
                          "link::ocean.deptho.ti-u-hxy-sea.fx.GLB", "link::ocean.masscello.ti-ol-hxy-sea.fx.GLB",
                          "link::ocean.so.tavg-ol-hxy-sea.mon.GLB", "link::ocean.sos.tavg-u-hxy-sea.day.GLB",
                          "link::ocean.sos.tavg-u-hxy-sea.mon.GLB", "link::ocean.thetao.tavg-ol-hxy-sea.mon.GLB",
                          "link::ocean.tos.tavg-u-hxy-sea.day.GLB", "link::ocean.tos.tavg-u-hxy-sea.mon.GLB",
                          "link::ocean.wo.tavg-ol-hxy-sea.mon.GLB", "link::ocean.zos.tavg-u-hxy-sea.day.GLB",
                          "link::ocean.zos.tavg-u-hxy-sea.mon.GLB", "link::ocean.zostoga.tavg-u-hm-sea.mon.GLB",
                          "link::seaIce.siconc.tavg-u-hxy-u.day.GLB", "link::seaIce.siconc.tavg-u-hxy-u.mon.GLB",
                          "link::seaIce.simass.tavg-u-hxy-sea.mon.GLB", "link::seaIce.sithick.tavg-u-hxy-si.mon.GLB",
                          "link::seaIce.siu.tavg-u-hxy-si.mon.GLB", "link::seaIce.siv.tavg-u-hxy-si.mon.GLB"]]
        self.assertListEqual(self.dr.find_variables_per_theme(theme_id), var)
        self.assertListEqual(self.dr.find_variables_per_theme(theme_name), var)
        self.assertListEqual(self.dr.find_variables_per_theme(theme_target), var)

    def test_find_mips_per_theme(self):
        theme_id = "link::atmosphere"
        theme_name = "Atmosphere"
        theme_target = self.dr.find_element("data_request_themes", theme_id)
        mips = [self.dr.find_element("mips", id)
                for id in ["link::CMIP", "link::DAMIP", "link::DCPP", "link::FireMIP", "link::HighResMIP",
                           "link::LUMIP", "link::PMIP", "link::ScenarioMIP", "link::TIPMIP"]]
        self.assertListEqual(self.dr.find_mips_per_theme(theme_id), mips)
        self.assertListEqual(self.dr.find_mips_per_theme(theme_name), mips)
        self.assertListEqual(self.dr.find_mips_per_theme(theme_target), mips)

    def test_themes_per_opportunity(self):
        op_id = "link::Accurate assessment of land-atmosphere coupling"
        op_name = "Accurate assessment of land-atmosphere coupling"
        op_target = self.dr.find_element("opportunities", op_id)
        themes = [self.dr.find_element("data_request_themes", id)
                  for id in ["link::atmosphere", "link::land_landice"]]
        self.assertListEqual(self.dr.find_themes_per_opportunity(op_id), themes)
        self.assertListEqual(self.dr.find_themes_per_opportunity(op_name), themes)
        self.assertListEqual(self.dr.find_themes_per_opportunity(op_target), themes)

    def test_experiments_per_opportunity(self):
        op_id = "link::Accurate assessment of land-atmosphere coupling"
        op_name = "Accurate assessment of land-atmosphere coupling"
        op_target = self.dr.find_element("opportunities", op_id)
        exp = [self.dr.find_element("experiments", id)
               for id in ["link::esm-hist", "link::historical", "link::scen7-hc", "link::scen7-mc", "link::scen7-mlc",
                          "link::scen7-vlloc"]]
        self.assertListEqual(self.dr.find_experiments_per_opportunity(op_id), exp)
        self.assertListEqual(self.dr.find_experiments_per_opportunity(op_name), exp)
        self.assertListEqual(self.dr.find_experiments_per_opportunity(op_target), exp)

    def test_variables_per_opportunity(self):
        op_id = "link::Accurate assessment of land-atmosphere coupling"
        op_name = "Accurate assessment of land-atmosphere coupling"
        op_target = self.dr.find_element("opportunities", op_id)
        var = [self.dr.find_element("variables", id)
               for id in ["link::atmos.bldep.tpt-u-hxy-u.3hr.GLB", "link::atmos.hfls.tavg-u-hxy-u.3hr.GLB",
                          "link::atmos.hfss.tavg-u-hxy-u.3hr.GLB", "link::atmos.huss.tpt-h2m-hxy-u.3hr.GLB",
                          "link::atmos.pr.tavg-u-hxy-u.3hr.GLB", "link::atmos.ps.tpt-u-hxy-u.3hr.GLB",
                          "link::atmos.rlds.tavg-u-hxy-u.3hr.GLB", "link::atmos.rlus.tavg-u-hxy-u.3hr.GLB",
                          "link::atmos.ta.tpt-p6-hxy-air.3hr.GLB", "link::atmos.tas.tpt-h2m-hxy-u.3hr.GLB",
                          "link::land.hfdsl.tavg-u-hxy-lnd.3hr.GLB", "link::land.mrsol.tavg-d100cm-hxy-lnd.3hr.GLB",
                          "link::land.mrsol.tpt-d10cm-hxy-lnd.3hr.GLB", "link::land.srfrad.tavg-u-hxy-u.3hr.GLB",
                          "link::land.tran.tavg-u-hxy-u.3hr.GLB", "link::land.tslsi.tpt-u-hxy-u.3hr.GLB"]]
        self.assertListEqual(self.dr.find_variables_per_opportunity(op_id), var)
        self.assertListEqual(self.dr.find_variables_per_opportunity(op_name), var)
        self.assertListEqual(self.dr.find_variables_per_opportunity(op_target), var)

    def test_mips_per_opportunity(self):
        op_id = "link::Accurate assessment of land-atmosphere coupling"
        op_name = "Accurate assessment of land-atmosphere coupling"
        op_target = self.dr.find_element("opportunities", op_id)
        mips = [self.dr.find_element("mips", id)
                for id in ["link::CMIP", "link::DAMIP", "link::HighResMIP", "link::LUMIP", "link::ScenarioMIP"]]
        self.assertListEqual(self.dr.find_mips_per_opportunity(op_id), mips)
        self.assertListEqual(self.dr.find_mips_per_opportunity(op_name), mips)
        self.assertListEqual(self.dr.find_mips_per_opportunity(op_target), mips)

    def test_opportunities_per_variable(self):
        var_id = "link::ocean.zos.tavg-u-hxy-sea.day.GLB"
        var_name = "ocean.zos.tavg-u-hxy-sea.day.GLB"
        var_target = self.dr.find_element("variables", var_id)
        op = [self.dr.find_element("opportunities", id)
              for id in ["link::49", "link::68", "link::69", ]]
        self.assertListEqual(self.dr.find_opportunities_per_variable(var_id), op)
        self.assertListEqual(self.dr.find_opportunities_per_variable(var_name), op)
        self.assertListEqual(self.dr.find_opportunities_per_variable(var_target), op)

    def test_themes_per_variable(self):
        var_id = "link::ocean.zos.tavg-u-hxy-sea.day.GLB"
        var_name = "ocean.zos.tavg-u-hxy-sea.day.GLB"
        var_target = self.dr.find_element("variables", var_id)
        themes = [self.dr.find_element("data_request_themes", id)
                  for id in ["link::atmosphere", "link::earth_system", "link::impacts", "link::land_landice",
                             "link::ocean_seaice"]
                  ]
        self.assertListEqual(self.dr.find_themes_per_variable(var_id), themes)
        self.assertListEqual(self.dr.find_themes_per_variable(var_name), themes)
        self.assertListEqual(self.dr.find_themes_per_variable(var_target), themes)

    def test_mips_per_variable(self):
        var_id = "link::ocean.zos.tavg-u-hxy-sea.day.GLB"
        var_name = "ocean.zos.tavg-u-hxy-sea.day.GLB"
        var_target = self.dr.find_element("variables", var_id)
        mips = [self.dr.find_element("mips", id)
                for id in ["link::CMIP", "link::DAMIP", "link::DCPP", "link::FAFMIP", "link::FireMIP", "link::GeoMIP",
                           "link::HighResMIP", "link::ISMIP7", "link::OMIP", "link::PMIP", "link::SIMIP",
                           "link::SOFIAMIP", "link::ScenarioMIP", "link::TIPMIP"]]
        self.assertListEqual(self.dr.find_mips_per_variable(var_id), mips)
        self.assertListEqual(self.dr.find_mips_per_variable(var_name), mips)
        self.assertListEqual(self.dr.find_mips_per_variable(var_target), mips)

    def test_opportunities_per_experiment(self):
        exp_id = "link::scen7-hc-ext"
        exp_name = "scen7-hc-ext"
        exp_target = self.dr.find_element("experiments", exp_id)
        op = [self.dr.find_element("opportunities", id)
              for id in ["link::49", "link::68"]]
        self.assertListEqual(self.dr.find_opportunities_per_experiment(exp_id), op)
        self.assertListEqual(self.dr.find_opportunities_per_experiment(exp_name), op)
        self.assertListEqual(self.dr.find_opportunities_per_experiment(exp_target), op)

    def test_themes_per_experiment(self):
        exp_id = "link::scen7-hc-ext"
        exp_name = "scen7-hc-ext"
        exp_target = self.dr.find_element("experiments", exp_id)
        themes = [self.dr.find_element("data_request_themes", id)
                  for id in ["link::atmosphere", "link::earth_system", "link::impacts", "link::ocean_seaice"]]
        self.assertListEqual(self.dr.find_themes_per_experiment(exp_id), themes)
        self.assertListEqual(self.dr.find_themes_per_experiment(exp_name), themes)
        self.assertListEqual(self.dr.find_themes_per_experiment(exp_target), themes)

    def test_find_opportunities(self):
        vargrp_id = "link::landatm_coupling_3hr_medium"
        exp_id = "link::dcppB-forecast-cmip6"
        list_all = list()
        list_any = [self.dr.find_element("opportunities", id)
                    for id in ["1", "49", "68", "69"]
                    ]
        self.assertListEqual(self.dr.find_opportunities(operation="all", variable_group=vargrp_id,
                                                        experiments=[exp_id, ]), list_all)
        self.assertListEqual(self.dr.find_opportunities(operation="any", variable_group=vargrp_id,
                                                        experiments=[exp_id, ]), list_any)

    def test_find_experiments(self):
        op_id = "link::Accurate assessment of land-atmosphere coupling"
        expgrp_id = ["link::dcpp", "link::historical"]
        list_all = list()
        list_any = [self.dr.find_element("experiments", id)
                    for id in ["link::dcppB-forecast-cmip6", "link::esm-hist", "link::historical", "link::scen7-hc",
                               "link::scen7-mc", "link::scen7-mlc", "link::scen7-vlloc"]]
        self.assertListEqual(self.dr.find_experiments(operation="all", opportunities=op_id,
                                                      experiment_groups=expgrp_id), list_all)
        self.assertListEqual(self.dr.find_experiments(operation="any", opportunities=op_id,
                                                      experiment_groups=expgrp_id), list_any)

    def test_find_variables(self):
        table_id = "527f5ced-8c97-11ef-944e-41a8eb05f654"
        vars_id = ["atmos.pr.tavg-u-hxy-u.1hr.GLB", "atmos.psl.tpt-u-hxy-u.1hr.GLB",
                   "atmos.uas.tpt-h10m-hxy-u.1hr.GLB", "atmos.vas.tpt-h10m-hxy-u.1hr.GLB"]
        self.assertListEqual(self.dr.find_variables(operation="all", table_identifier=table_id),
                             [self.dr.find_element("variables", var_id) for var_id in vars_id])

        tshp_id = "a06034e5-bbca-11ef-9840-9de7167a7ecb"
        vars_id = ["atmos.tas.tmax-h2m-hxy-u.mon.GLB", "atmos.tas.tmin-h2m-hxy-u.mon.GLB"]
        self.assertListEqual(self.dr.find_variables(operation="all", temporal_shape=tshp_id),
                             [self.dr.find_element("variables", var_id) for var_id in vars_id])

        sshp_id = "a6563bca-8883-11e5-b571-ac72891c3257"
        vars_id = ["land.slthick.ti-sl-hxy-lnd.fx.GLB", ]
        self.assertListEqual(self.dr.find_variables(operation="all", spatial_shape=sshp_id),
                             [self.dr.find_element("variables", var_id) for var_id in vars_id])

        param_id = "00e77372e8b909d9a827a0790e991fd9"
        vars_id = ["land.orog.ti-u-hxy-u.fx.GLB", ]
        self.assertListEqual(self.dr.find_variables(operation="all", physical_parameter=param_id),
                             [self.dr.find_element("variables", var_id) for var_id in vars_id])

        realm_id = "ocnBgchem"
        vars_id = ["ocnBgchem.arag.tavg-d0m-hxy-sea.mon.GLB", "ocnBgchem.arag.tavg-ol-hxy-sea.mon.GLB",
                   "ocnBgchem.calc.tavg-d0m-hxy-sea.mon.GLB", "ocnBgchem.calc.tavg-ol-hxy-sea.mon.GLB",
                   "ocnBgchem.chl.tavg-op20bar-hxy-sea.day.GLB", "ocnBgchem.dissic.tavg-ol-hxy-sea.mon.GLB",
                   "ocnBgchem.o2.tavg-op20bar-hxy-sea.day.GLB", "ocnBgchem.ph.tavg-op20bar-hxy-sea.day.GLB",
                   "ocnBgchem.talk.tavg-ol-hxy-sea.mon.GLB"]
        self.assertListEqual(self.dr.find_variables(operation="all", modelling_realm=realm_id),
                             [self.dr.find_element("variables", var_id) for var_id in vars_id])

        bcv_id = "80ab7325-a698-11ef-914a-613c0433d878"
        vars_id = ["atmos.pr.tavg-u-hxy-u.3hr.GLB", ]
        self.assertListEqual(self.dr.find_variables(operation="all", **{"esm-bcv": bcv_id}),
                             [self.dr.find_element("variables", var_id) for var_id in vars_id])

        cf_std_id = "3ba6666e-8ca2-11ef-944e-41a8eb05f654"
        vars_id = ["atmos.prc.tavg-u-hxy-u.mon.GLB", ]
        self.assertListEqual(self.dr.find_variables(operation="all", cf_standard_name=cf_std_id),
                             [self.dr.find_element("variables", var_id) for var_id in vars_id])

        cell_methods_id = "a269a4c3-8c9b-11ef-944e-41a8eb05f654"
        vars_id = ["land.rootd.ti-u-hxy-lnd.fx.GLB", "land.slthick.ti-sl-hxy-lnd.fx.GLB"]
        self.assertListEqual(self.dr.find_variables(operation="all", cell_methods=cell_methods_id),
                             [self.dr.find_element("variables", var_id) for var_id in vars_id])

        cell_measure_id = "a269a4fb-8c9b-11ef-944e-41a8eb05f654"
        vars_id = ["seaIce.siu.tavg-u-hxy-si.day.GLB", "seaIce.siu.tavg-u-hxy-si.mon.GLB",
                   "seaIce.siv.tavg-u-hxy-si.day.GLB", "seaIce.siv.tavg-u-hxy-si.mon.GLB"]
        self.assertListEqual(self.dr.find_variables(operation="all", cell_measures=cell_measure_id),
                             [self.dr.find_element("variables", var_id) for var_id in vars_id])

    def test_find_priority_per_variable(self):
        var_id = "link::ocean.tos.tpt-u-hxy-sea.3hr.GLB"
        var = self.dr.find_element("variable", var_id)
        self.assertEqual(self.dr.find_priority_per_variable(var), 2)

    def test_cache_issue(self):
        with tempfile.TemporaryDirectory() as output_dir:
            self.dr.find_variables_per_opportunity(self.dr.get_opportunities()[0])
            self.dr.export_summary("variables", "opportunities",
                                   os.sep.join([output_dir, "var_per_op.csv"]))

    def test_export_summary(self):
        with tempfile.TemporaryDirectory() as output_dir:
            self.dr.export_summary("opportunities", "data_request_themes",
                                   os.sep.join([output_dir, "op_per_th.csv"]))
            self.dr.export_summary("variables", "opportunities",
                                   os.sep.join([output_dir, "var_per_op.csv"]))
            self.dr.export_summary("opportunities", "variables",
                                   os.sep.join([output_dir, "op_per_var.csv"]))
            self.dr.export_summary("experiments", "opportunities",
                                   os.sep.join([output_dir, "exp_per_op.csv"]))
            self.dr.export_summary("variables", "spatial_shape",
                                   os.sep.join([output_dir, "var_per_spsh.csv"]))

    def test_export_data(self):
        with tempfile.TemporaryDirectory() as output_dir:
            self.dr.export_data("opportunities",
                                os.sep.join([output_dir, "op.csv"]),
                                export_columns_request=["name", "lead_theme", "description"])
