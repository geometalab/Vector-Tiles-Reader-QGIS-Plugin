# -*- coding: utf-8 -*-
#
# This code is licensed under the GPL 2.0 license.
#
import unittest
import coverage
import sys


def get_tests():
    from test_mbtiles_source import MbtileSourceTests
    from test_server_source import ServerSourceTests
    from test_tilehelper import TileHelperTests
    from test_filehelper import FileHelperTests
    from test_vtreader import VtReaderTests
    from test_tilejson import TileJsonTests
    from test_networkhelper import NetworkHelperTests

    tests = [
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
    cov = coverage.Coverage(omit=['*/usr/*',
                                  '*__init__.py',
                                  '*global_map_tiles*',
                                  '/vector-tiles-reader/tests/*',
                                  '/vector-tiles-reader/util/*',
                                  '/vector-tiles-reader/ext-libs/*',
                                  '/vector-tiles-reader/vtr_plugin.py'  # todo: remove from here when tests exist
                                  ])
    cov.start()
    complete_suite = unittest.TestSuite(get_tests())
    print("")
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(complete_suite)
    print("")
    cov.stop()
    cov.save()
    cov.html_report(directory='tests/htmlcov')
    print cov.report()


if __name__ == "__main__":
    run_all()
