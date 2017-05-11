from __future__ import absolute_import
from __future__ import unicode_literals
import unittest
import sys
import os


try:
    import dali
except ImportError:
    # Realign paths, and try import again
    # Since pyCharm's unittest runner fails on relative imports
    path = os.path
    PACKAGE_PARENT = '../..'
    SCRIPT_DIR = path.dirname(
        path.realpath(path.join(os.getcwd(), path.expanduser(__file__)))
    )
    sys.path.append(path.normpath(path.join(SCRIPT_DIR, PACKAGE_PARENT)))


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
        # bus
        self.assertIsInstance(
            exceptions.BusError(),
            exceptions.DALIError
        )
        self.assertIsInstance(
            exceptions.BadDevice(),
            exceptions.BusError
        )
        self.assertIsInstance(
            exceptions.DeviceAlreadyBound(),
            exceptions.BusError
        )
        self.assertIsInstance(
            exceptions.DuplicateDevice(),
            exceptions.BusError
        )
        self.assertIsInstance(
            exceptions.NoFreeAddress(),
            exceptions.BusError
        )
        self.assertIsInstance(
            exceptions.NotConnected(),
            exceptions.BusError
        )
        self.assertIsInstance(
            exceptions.ProgramShortAddressFailure(0),
            exceptions.BusError
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
