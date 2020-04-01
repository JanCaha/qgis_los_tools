import unittest
import os

# import your test modules

# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

suite.addTests(loader.discover("test"))

# add tests to the test suite
# suite.addTests(loader.loadTestsFromModule())

# initialize a runner, pass it your suite and run it
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)
