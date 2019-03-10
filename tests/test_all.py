# -*- coding: utf-8 -*-
#
# This code is licensed under the GPL 2.0 license.
#
from qgis.testing import unittest
import coverage
import sys


def get_tests():
    from tests.test_vtr_plugin import VtrPluginTests

    from tests.test_mbtiles_source import MbtileSourceTests
    from tests.test_server_source import ServerSourceTests
    from tests.test_tilehelper import TileHelperTests
    from tests.test_filehelper import FileHelperTests
    from tests.test_vtreader import VtReaderTests
    from tests.test_tilejson import TileJsonTests
    from tests.test_networkhelper import NetworkHelperTests

    tests = [
        unittest.TestLoader().loadTestsFromTestCase(VtrPluginTests),
        unittest.TestLoader().loadTestsFromTestCase(MbtileSourceTests),
        unittest.TestLoader().loadTestsFromTestCase(ServerSourceTests),
        unittest.TestLoader().loadTestsFromTestCase(TileHelperTests),
        unittest.TestLoader().loadTestsFromTestCase(FileHelperTests),
        unittest.TestLoader().loadTestsFromTestCase(TileJsonTests),
        unittest.TestLoader().loadTestsFromTestCase(NetworkHelperTests),
        unittest.TestLoader().loadTestsFromTestCase(VtReaderTests),
    ]
    return tests


# run all tests using unittest skipping nose or testplugin
def run_all():
    cov = coverage.Coverage(
        omit=[
            "*/usr/*",
            "*__init__.py",
            "*global_map_tiles*",
            "/tests_directory/tests/*",
            "/tests_directory/ext-libs/*",
            # "/tests_directory/vtr_plugin.py",  # todo: remove from here when tests exist
        ]
    )
    cov.start()
    complete_suite = unittest.TestSuite(get_tests())
    print("")
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(complete_suite)
    print("")
    cov.stop()
    cov.save()
    cov.html_report(directory="/tests_directory/htmlcov")
    print(cov.report())


if __name__ == "__main__":
    run_all()
