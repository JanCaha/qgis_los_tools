import unittest
import os

from los_tools.test.test_tool_limit_angles_vector import LimitAnglesAlgorithmTest


def test_package():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.discover("test"))

    print('########')
    print("%s tests has been found." % (suite.countTestCases()))
    print('########')

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)


if __name__ == '__main__':
    test_package()
