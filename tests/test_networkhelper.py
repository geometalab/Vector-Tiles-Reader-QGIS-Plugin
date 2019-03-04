from qgis.testing import unittest
from util.network_helper import *


class NetworkHelperTests(unittest.TestCase):
    """
    Tests for util.network_helper
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_url_exists(self):
        exists, error, _ = url_exists("https://travis-ci.org/")
        self.assertTrue(exists)
        self.assertIsNone(error)

    def test_url_exists_not(self):
        exists, error, _ = url_exists("https://traaadsfadsfadssfdsfdsfdsvis-ci.org/")
        self.assertFalse(exists)
