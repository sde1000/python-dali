import unittest
import sys
import os


import dali
from dali import exceptions


class TestExceptions(unittest.TestCase):

    def test_exceptions(self):
        """exception class hierarchy as expected"""
        # general
        self.assertIsInstance(exceptions.DALIError(), Exception)
        # address
        self.assertIsInstance(
            exceptions.AddressError(),
            exceptions.DALIError
        )
        self.assertIsInstance(
            exceptions.IncompatibleFrame(),
            exceptions.AddressError
        )
        # command
        self.assertIsInstance(
            exceptions.CommandError(),
            exceptions.DALIError
        )
        self.assertIsInstance(
            exceptions.MissingResponse(),
            exceptions.CommandError
        )
        self.assertIsInstance(
            exceptions.ResponseError(),
            exceptions.CommandError
        )
        # sequences
        self.assertIsInstance(
            exceptions.ProgramShortAddressFailure(0),
            exceptions.DALIError
        )
        # driver
        self.assertIsInstance(
            exceptions.DriverError(),
            exceptions.DALIError
        )
        self.assertIsInstance(
            exceptions.CommunicationError(),
            exceptions.DriverError
        )


if __name__ == '__main__':
    unittest.main()
