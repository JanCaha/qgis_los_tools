import unittest
import os

from los_tools.test.test_tool_limit_angles_vector import LimitAnglesAlgorithmTest


def test_package():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # suite.addTests(loader.discover("test"))
    # suite.addTests(loader.loadTestsFromTestCase(LimitAnglesAlgorithmTest))

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)


if __name__ == '__main__':
    test_package()
