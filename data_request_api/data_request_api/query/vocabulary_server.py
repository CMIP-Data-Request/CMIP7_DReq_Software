#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vocabulary server.
"""

from __future__ import division, print_function, unicode_literals, absolute_import

import copy
from collections import defaultdict

from data_request_api.utilities.logger import get_logger
from data_request_api.utilities.tools import read_json_file


def is_link_id_or_value(elt):
    """
    Check if the input value is a link and transform it into a value if so
    :param elt: element to be transformed into a value
    :return: not link version oof elt
    """
    if isinstance(elt, ConstantValueObj):
        elt = str(elt)
    if isinstance(elt, str) and elt.startswith("link::"):
        return True, elt.replace("link::", "")
    else:
        return False, elt


def build_link_from_id(elt):
    """
    Check if the input value is already a link and transform it if not
    :param elt: element to be transformed into a link
    :return: link version of elt
    """
    if isinstance(elt, ConstantValueObj):
        elt = str(elt)
    if not isinstance(elt, str) or elt.startswith("link::"):
        return elt
    else:
        return f"link::{elt}"


def to_plural(element_type):
    if not element_type.endswith("s"):
        if element_type.endswith("y"):
            element_type = element_type.rstrip("y") + "ies"
        else:
            element_type += "s"
    return element_type


def to_singular(element_type):
    if element_type.endswith("ies"):
        element_type = element_type[0:-3] + "y"
    elif element_type.endswith("s"):
        element_type = element_type[0:-1]
    return element_type


class VocabularyServer(object):
    """
    Class to generate a Vocabulary Server from a json file.
    """

    def __init__(self, input_database, **kwargs):
        self.vocabulary_server = copy.deepcopy(input_database)
        self.version = self.vocabulary_server.pop("version")
        self.check_infinite_loop()

    @classmethod
    def from_input(cls, input_database):
        """
        Generate VocabularyServer from a json file
        :param input_database: json file name
        :return:
        """
        content = read_json_file(input_database)
        return cls(content)

    def alias(self, element_type):
        """
        Find the real element_type if aliased
        :param element_type: input kind of element
        :return:
        """
        element_type_dict = dict(
            keyword="glossary",
            lead_theme="data_request_themes",
            dimension="coordinates_and_dimensions",
            coordinate="coordinates_and_dimensions",
            extra_dimension="coordinates_and_dimensions",
            frequency="cmip7_frequency",
            max_priority_level="priority_level",
            primary_modelling_realm="modelling_realm",
            structure="structure_title",
            table="cmip6_tables_identifier",
            table_identifier="cmip6_tables_identifier",
            reference="docs_for_opportunity",
            theme="data_request_themes"
        )
        return element_type_dict.get(element_type, element_type)

    def check_infinite_loop(self):
        """
        Check that there is no infinite loop in the vocabulary server.
        Raise an error if at least one is found.
        """
        logger = get_logger()
        # Build the call dict
        call_dict = defaultdict(set)
        for key in self.vocabulary_server:
            for id in self.vocabulary_server[key]:
                for elt in self.vocabulary_server[key][id]:
                    if isinstance(self.vocabulary_server[key][id][elt], list) and \
                            any(is_link_id_or_value(subelt)[0] for subelt in self.vocabulary_server[key][id][elt]):
                        call_dict[key].add(elt)
                    elif not (isinstance(self.vocabulary_server[key][id][elt], list)) and \
                            is_link_id_or_value(self.vocabulary_server[key][id][elt])[0]:
                        call_dict[key].add(elt)

        # Implement the function to be used
        def follow_loop(current_key, former_keys=list()):
            logger = get_logger()
            found = False
            alias_key, _ = self.get_element_type_ids(current_key)
            if alias_key in former_keys:
                logger.error(f"Infinite loop found: {former_keys + [current_key, ]}")
                found = True
            else:
                for next_key in sorted(list(call_dict[alias_key])):
                    found = found or follow_loop(next_key, former_keys + [alias_key, ])
            return found

        # Follow the call dict to check if there is infinite loop
        found = any(follow_loop(key) for key in sorted(list(call_dict)))
        if found:
            logger.critical("Infinite loop found in vocabulary server, see former error messages.")
            raise ValueError("Infinite loop found in vocabulary server, see former error messages.")

    def get_element_type(self, element_type):
        logger = get_logger()
        element_type = to_singular(element_type)
        element_type = self.alias(element_type)
        if element_type not in self.vocabulary_server:
            element_type = to_plural(element_type)
        if element_type in self.vocabulary_server:
            return element_type
        else:
            logger.error(f"Could not find element type {element_type} in the vocabulary server.")
            raise ValueError(f"Could not find element type {element_type} in the vocabulary server.")

    def get_element_type_ids(self, element_type):
        """
        Get elements corresponding a a specific kind
        :param element_type:
        :return:
        """
        element_type = self.get_element_type(element_type)
        return element_type, sorted(list(self.vocabulary_server[element_type]))

    def get_element(self, element_type, element_id, element_key=None, default=False, id_type="id"):
        """
        Get an element corresponding to an element_id (corresponding to attribute id_type) of a kind element_type.
        If element_key is specified, get the corresponding attribute.
        If no element found, return default.
        :param element_type:
        :param element_id:
        :param element_key:
        :param default:
        :param id_type:
        :return:
        """
        logger = get_logger()
        is_id, element_id = is_link_id_or_value(element_id)
        if is_id or id_type != "id":
            element_type, element_type_ids = self.get_element_type_ids(element_type)
            found = False
            if id_type in ["id", ] and element_id in element_type_ids:
                value = self.vocabulary_server[element_type][element_id]
                found = True
            elif isinstance(id_type, str):
                if element_id is None:
                    raise ValueError("None element_id found")
                value = list()
                for (key, val) in self.vocabulary_server[element_type].items():
                    val = val.get(id_type)
                    if (isinstance(val, list) and element_id in val) or element_id == val:
                        value.append(key)
                if len(value) == 1:
                    found = True
                    element_id = value[0]
                    value = self.vocabulary_server[element_type][element_id]
                elif len(value) > 1:
                    logger.error(f"id_type {id_type} provided is not unique for element type {element_type} and "
                                 f"value {element_key}.")
                    raise ValueError(f"id_type {id_type} provided is not unique for element type {element_type} "
                                     f"and value {element_key}.")
            if found:
                if element_key is not None:
                    if element_key in value:
                        value = value.get(element_key)
                    else:
                        logger.error(f"Could not find key {element_key} of id {element_id} of type {element_type} "
                                     f"in the vocabulary server.")
                        raise ValueError(f"Could not find key {element_key} of id {element_id} of type "
                                         f"{element_type} in the vocabulary server.")
                elif isinstance(value, dict):
                    value["id"] = element_id
                return value
            elif default is not False:
                logger.debug(f"Could not find {id_type} {element_id} of type {element_type}"
                             f" in the vocabulary server.")
                return default
            else:
                logger.error(f"Could not find {id_type} {element_id} of type {element_type} "
                             f"in the vocabulary server.")
                raise ValueError(f"Could not find {id_type} {element_id} of type {element_type} "
                                 f"in the vocabulary server.")
        elif element_id in ["???", None]:
            logger.critical(f"Undefined id of type {element_type}")
            return element_id
        else:
            return element_id


class ConstantValueObj(object):
    """
    Constant object which return the same value each time an attribute is asked.
    It is used to avoid discrepancies between objects and strings.
    """

    def __init__(self, value="undef"):
        self.value = value

    def __getattr__(self, item):
        return self.value

    def __str__(self):
        return str(self.value)

    def __hash__(self):
        return hash(self.value)

    def __copy__(self):
        return ConstantValueObj(self.value)

    def __eq__(self, other):
        return str(self) == str(other)

    def __gt__(self, other):
        return str(self) > str(other)

    def __lt__(self, other):
        return str(self) < str(other)

    def __deepcopy__(self, memodict={}):
        return self.__copy__()

    def __len__(self):
        return len(str(self))

    def __iter__(self):
        return iter(list())

    def __next__(self):
        raise StopIteration
