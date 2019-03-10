import sys
from qgis.testing import unittest
from qgis.utils import iface  # noqa # dont remove! is required for testing (iface wont be found otherwise)

from plugin.vtr_plugin import VtrPlugin


class VtrPluginTests(unittest.TestCase):
    """
    Tests for util.file_helper
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_plugin_creation(self):
        global iface
        p = VtrPlugin(iface)
        p.initGui()
        self.assertTrue(p is not None)


def suite():
    s = unittest.makeSuite(VtrPluginTests, "test")
    return s


# run all tests using unittest skipping nose or testplugin
def run_all():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())


if __name__ == "__main__":
    run_all()
