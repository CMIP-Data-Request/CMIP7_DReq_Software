'''
https://gist.github.com/matthew-mizielinski/643ca1841dc760edf230473a8b81d396
'''

import copy
import json
import hashlib


def set_checksum(dictionary, overwrite=True):
    """
    Calculate the checksum for the ``dictionary``, then add the
    value to ``dictionary`` under the ``checksum`` key. ``dictionary``
    is modified in place.

    Parameters
    ----------
    dictionary: dict
        The dictionary to set the checksum to.
    overwrite: bool
        Overwrite the existing checksum (default True).

    Raises
    ------
    RuntimeError
        If the ``checksum`` key already exists and ``overwrite`` is
        False.
    """
    if 'checksum' in dictionary:
        if not overwrite:
            raise RuntimeError('Checksum already exists.')
        del dictionary['checksum']
    checksum = _checksum(dictionary)
    dictionary['checksum'] = checksum


def validate_checksum(dictionary):
    """
    Validate the checksum in the ``dictionary``.

    Parameters
    ----------
    dictionary: dict
        The dictionary containing the ``checksum`` to validate.

    Raises
    ------
    KeyError
        If the ``checksum`` key does not exist.
    RuntimeError
        If the ``checksum`` value is invalid.
    """
    if 'checksum' not in dictionary:
        raise KeyError('No checksum to validate')
    dictionary_copy = copy.deepcopy(dictionary)
    del dictionary_copy['checksum']
    checksum = _checksum(dictionary_copy)
    if dictionary['checksum'] != checksum:
        msg = ('Expected checksum   "{}"\n'
               'Calculated checksum "{}"').format(dictionary['checksum'],
                                                  checksum)
        raise RuntimeError(msg)


def _checksum(obj):
    obj_str = json.dumps(obj, sort_keys=True)
    checksum_hex = hashlib.md5(obj_str.encode('utf8')).hexdigest()
    return 'md5: {}'.format(checksum_hex)
