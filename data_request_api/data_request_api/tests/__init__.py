
import os

TEST_DATA_LOCATION = os.path.join(os.path.dirname(__file__), 'test_datasets')


def filepath(filename):
    """
    Return the full path of a file from the test_datasets directory
    """
    return os.path.join(TEST_DATA_LOCATION, filename)
