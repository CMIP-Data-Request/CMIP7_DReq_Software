#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test vocabulary_server.py
"""
from __future__ import print_function, division, unicode_literals, absolute_import

import copy
import unittest

from data_request_api.utilities.tools import read_json_input_file_content
from data_request_api.query.vocabulary_server import VocabularyServer, is_link_id_or_value, build_link_from_id, \
    to_plural, to_singular
from data_request_api.tests import filepath


class TestLinks(unittest.TestCase):

    def test_is_link_or_value(self):
        self.assertEqual(is_link_id_or_value("test"), (False, "test"))
        self.assertEqual(is_link_id_or_value(None), (False, None))
        self.assertEqual(is_link_id_or_value(5), (False, 5))
        self.assertEqual(is_link_id_or_value("link::test"), (True, "test"))

    def test_build_link_from_id(self):
        self.assertEqual(build_link_from_id(None), None)
        self.assertEqual(build_link_from_id(6), 6)
        self.assertEqual(build_link_from_id("test"), "link::test")
        self.assertEqual(build_link_from_id("link::test"), "link::test")


class TestChangeNumber(unittest.TestCase):
    def setUp(self):
        self.vs_file = filepath("VS_release_not-consolidate_content.json")

    def test_to_singular(self):
        vs = VocabularyServer.from_input(self.vs_file)
        self.assertEqual(to_singular("opportunities"), "opportunity")
        self.assertEqual(to_singular("variables_groups"), "variables_group")
        self.assertEqual(to_singular("variables_group"), "variables_group")

    def test_to_plural(self):
        vs = VocabularyServer.from_input(self.vs_file)
        self.assertEqual(to_plural("opportunity"), "opportunities")
        self.assertEqual(to_plural("variables_groups"), "variables_groups")
        self.assertEqual(to_plural("variables_group"), "variables_groups")


class TestVocabularyServer(unittest.TestCase):
    def setUp(self):
        self.vs_file = filepath("VS_release_not-consolidate_content.json")
        self.vs_content = read_json_input_file_content(self.vs_file)
        self.vs_content_infinite_loop = copy.deepcopy(self.vs_content)
        self.vs_content_infinite_loop["cell_methods"]["a269a4d7-8c9b-11ef-944e-41a8eb05f654"]["variables"] = "link::0facb764-817d-11e6-b80b-5404a60d96b5"

    def test_init(self):
        with self.assertRaises(TypeError):
            VocabularyServer()

        content_no_version = copy.deepcopy(self.vs_content)
        del content_no_version["version"]
        with self.assertRaises(KeyError):
            VocabularyServer(content_no_version)

        obj = VocabularyServer(self.vs_content)
        obj = VocabularyServer(self.vs_content, an_attrib="a_value")

        with self.assertRaises(ValueError):
            VocabularyServer(self.vs_content_infinite_loop)

        with self.assertRaises(TypeError):
            VocabularyServer.from_input(self.vs_content)

        obj = VocabularyServer.from_input(self.vs_file)

    def test_get_element(self):
        vs = VocabularyServer.from_input(self.vs_file)

        elt = vs.get_element(element_type="my_type", element_id="test")
        self.assertEqual(elt, "test")
        elt = vs.get_element(element_type="my_type", element_id="???")
        self.assertEqual(elt, "???")
        elt = vs.get_element(element_type="my_type", element_id=None)
        self.assertEqual(elt, None)

        with self.assertRaises(ValueError):
            elt = vs.get_element(element_type="my_type", element_id="test", id_type="type")
        with self.assertRaises(ValueError):
            elt = vs.get_element(element_type="variable_comment", element_id="test", id_type="type")

        elt = vs.get_element(element_type="mips", element_id="TIPMIP", id_type="name")
        target_dict = {
            "mip_abstract": "TIPMIP is an international intercomparison project that aims to systematically advance our"
                            " understanding of nonlinear dynamics in various Earth system components, and assess the "
                            "associated uncertainties and risks. At present, no MIP exists which focuses specifically "
                            "on identifying and evaluating the risks of tipping dynamics in the Earth system. Filling "
                            "this gap, TIPMIP will shed light on critical processes currently underrepresented in other"
                            " MIPs and in Earth system models.\n\nWhat are tipping elements?\nTipping elements are "
                            "components of the Earth system highly susceptible to reaching a critical threshold \u2013 "
                            "a tipping point \u2013 beyond which amplifying feedbacks can result in abrupt and/or "
                            "irreversible changes in response to anthropogenic climate change. Crossing a tipping point"
                            " can lead the systems to transition to an alternative state, often with reduced resilience"
                            " to perturbations and recovery. Once triggered, the tipping of one of these elements can "
                            "have far-reaching impacts on the global climate, ecosystems and humankind. Therefore, "
                            "understanding the dynamics of tipping elements and associated risks is crucial for "
                            "developing effective strategies to mitigate and adapt to the impacts of global "
                            "environmental change.\n\nWhy is this project important?\nOur current scientific knowledge "
                            "of tipping dynamics in the Earth system involves a broad range of uncertainties on (i) "
                            "which components of the climate system and biosphere might show tipping behaviour, (ii) if"
                            " so, at which forcing levels the critical thresholds are located, (iii) which feedback "
                            "processes they are associated with, and (iv) if and how potential tipping cascades might "
                            "evolve. These uncertainties have numerous sources, for instance connected to:\n-finding "
                            "the \u201cright\u201d level of complexity regarding certain processes within and between "
                            "Earth system components; \n-the representation of all relevant biophysical processes on "
                            "the required timescales in Earth system models (in part, so far limited due to "
                            "computational constraints);\n-the implementation of certain processes and feedbacks in the"
                            " models; and\n-the limitations on observational data availability for long time horizons."
                            "\n\nProject aims\nTIPMIP specifically aims to answer the following questions:\n-What is "
                            "the risk of crossing potential tipping points in the cryosphere, biosphere and core "
                            "circulation systems at different levels of ongoing climate and land-use change?\n-What are"
                            " the key biophysical processes and feedbacks associated with these risks?\n-What are the "
                            "characteristics (spatial and time scales, abrupt or gradual, etc.) of Earth system tipping"
                            " elements?\n-How does the forcing rate affect short- and long-term impacts of changes in "
                            "the ice sheets, permafrost, ocean circulation, tropical and boreal forests?\n-Are the "
                            "respective impacts reversible, and if so, on which timescales?\n-How do interactions "
                            "between elements affect the overall stability of the Earth system?\n\nTypes of experiments"
                            " \nInitially, we envision three major types of experiments for TIPMIP, all of which will "
                            "be designed for the assessment of potential key tipping elements including the Greenland "
                            "Ice Sheet, Antarctic Ice Sheet, Atlantic Meridional Overturning Circulation (AMOC), "
                            "tropical forests, boreal forests, and permafrost - in both fully coupled ESM as well as "
                            "stand-alone model simulations.\n\n-Baseline experiments (ramp-up experiments) to analyze "
                            "the historical and projected response of potential tipping elements to different climate "
                            "change scenarios;\n-Commitment experiments to assess the long-term consequences of "
                            "surpassing different temperature and CO2 levels;\n-Reversibility experiments to probe "
                            "potential hysteresis behaviour;\n-Rate experiments to assess the impact of different "
                            "forcing rates on tipping.\n\nThese \u2018see what happens\u2019 experiments will be "
                            "complemented by an additional set of \u2018make it happen\u2019-experiments, which apply "
                            "additional forcings (e.g., land-use change, freshwater input etc.) tailored to the "
                            "individual tipping elements. This allows for \u2018what if it happens\u2019 assessments, "
                            "in which the impact of fully collapsed tipping elements can be studied.",
            "mip_long_name": "Tipping Point Modelling Intercomparison Project",
            "mip_website": "https://www.tipmip.org",
            "name": "TIPMIP",
            "id": "TIPMIP",
            "uid": "527f5c6c-8c97-11ef-944e-41a8eb05f654"
        }
        self.assertDictEqual(elt, target_dict)
        obj = vs.get_element(element_type="mips", element_id="link::TIPMIP")
        self.assertDictEqual(elt, target_dict)

        with self.assertRaises(ValueError):
            obj = vs.get_element(element_type="mips", element_id="link::80ab737a-a698-11ef-914a-613c0433d878")

        obj = vs.get_element(element_type="mips", element_id="link::80ab737a-a698-11ef-914a-613c0433d878", default=None)
        self.assertIsNone(obj)

        with self.assertRaises(ValueError):
            obj = vs.get_element(element_type="mips", element_id=None, id_type="name")

        with self.assertRaises(ValueError):
            obj = vs.get_element(element_type="mips", element_id="undef", id_type="name")

        obj = vs.get_element(element_type="mips", element_id="link::TIPMIP", element_key="mip_long_name")
        self.assertEqual(obj, "Tipping Point Modelling Intercomparison Project")

        with self.assertRaises(ValueError):
            obj = vs.get_element(element_type="mips", element_id="link::TIPMIP", element_key="long_name")
