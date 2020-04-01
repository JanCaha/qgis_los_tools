import unittest
import os


def test_package():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.discover("test"))

    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(suite)


if __name__ == '__main__':
    test_package()
