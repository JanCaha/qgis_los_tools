import unittest


def test_package():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.discover("test"))

    print("################################")
    print("Tests for LOS TOOLS Plugin runned from the Test Suite.")
    print("%s tests has been found." % (suite.countTestCases()))
    print("################################")

    runner = unittest.TextTestRunner(verbosity=3)
    runner.run(suite)


if __name__ == '__main__':
    test_package()
