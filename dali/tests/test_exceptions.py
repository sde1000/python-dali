import unittest
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
        # memory
        self.assertIsInstance(
            exceptions.MemoryError(),
            exceptions.DALIError
        )
        self.assertIsInstance(
            exceptions.MemoryLocationNotImplemented(),
            exceptions.MemoryError
        )
        self.assertIsInstance(
            exceptions.MemoryWriteError(),
            exceptions.MemoryError
        )
        self.assertIsInstance(
            exceptions.MemoryValueNotWriteable(),
            exceptions.MemoryWriteError
        )
        self.assertIsInstance(
            exceptions.MemoryLocationNotWriteable(),
            exceptions.MemoryWriteError
        )
        self.assertIsInstance(
            exceptions.MemoryWriteFailure(),
            exceptions.MemoryWriteError
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
