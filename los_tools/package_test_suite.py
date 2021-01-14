import sys
import os
import unittest
import tempfile
from osgeo import gdal
import qgis  # pylint: disable=unused-import

try:
    from pip import main as pipmain
except ImportError:
    from pip._internal import main as pipmain

try:
    import coverage
except ImportError:
    pipmain(['install', 'coverage'])
    import coverage


def _run_tests(test_suite, package_name, with_coverage=False):
    """Core function to test a test suite."""
    count = test_suite.countTestCases()
    print('########')
    print('%s tests has been discovered in %s' % (count, package_name))
    print('Python GDAL : %s' % gdal.VersionInfo('VERSION_NUM'))
    print('########')
    if with_coverage:
        cov = coverage.Coverage(
            source=['/los_tools'],
            omit=['*/test/*'],
        )
        cov.start()

    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(test_suite)

    if with_coverage:
        cov.stop()
        cov.save()
        report = tempfile.NamedTemporaryFile(delete=False)
        cov.report(file=report)
        # Produce HTML reports in the `htmlcov` folder and open index.html
        # cov.html_report()
        report.close()
        with open(report.name, 'r') as fin:
            print(fin.read())


def test_package(package='los_tools'):
    test_loader = unittest.defaultTestLoader
    try:
        test_suite = test_loader.discover(package)
    except ImportError:
        test_suite = unittest.TestSuite()
    _run_tests(test_suite, package)


def test_environment():
    package = os.environ.get('TESTING_PACKAGE', 'los_tools')
    test_loader = unittest.defaultTestLoader
    test_suite = test_loader.discover(package)
    _run_tests(test_suite, package)


if __name__ == '__main__':
    test_package()
