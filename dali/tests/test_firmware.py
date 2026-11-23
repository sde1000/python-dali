import unittest

from dali import address
from dali import command
from dali import firmware
from dali import frame
from dali.exceptions import IncompatibleFrame


class TestFirmwareAddresses(unittest.TestCase):
    def test_encoding(self) -> None:
        """firmware addresses occupy the most significant byte"""
        for addr, expected in (
                (address.FirmwareBroadcast(), 0xFE),
                (address.FirmwareBroadcastUnaddressed(), 0xFC),
                (address.FirmwareShort(0), 0x00),
                (address.FirmwareShort(1), 0x02),
                (address.FirmwareShort(63), 0x7E),
        ):
            f = frame.ForwardFrame(32, 0)
            addr.add_to_frame(f)
            self.assertEqual(f[31:24], expected, f"{addr} encoded wrongly")

    def test_roundtrip(self) -> None:
        """firmware addresses survive address.from_frame()"""
        for addr in (address.FirmwareBroadcast(),
                     address.FirmwareBroadcastUnaddressed(),
                     address.FirmwareShort(0),
                     address.FirmwareShort(37),
                     address.FirmwareShort(63)):
            f = frame.ForwardFrame(32, 0)
            addr.add_to_frame(f)
            self.assertEqual(address.from_frame(f), addr)

    def test_short_address_range(self) -> None:
        self.assertRaises(ValueError, address.FirmwareShort, -1)
        self.assertRaises(ValueError, address.FirmwareShort, 64)
        self.assertRaises(ValueError, address.FirmwareShort, None)

    def test_wrong_frame_size(self) -> None:
        """firmware addresses refuse to go into 16- and 24-bit frames"""
        for bits in (16, 24):
            f = frame.ForwardFrame(bits, 0)
            self.assertRaises(
                IncompatibleFrame, address.FirmwareBroadcast().add_to_frame, f)
            self.assertRaises(
                IncompatibleFrame, address.FirmwareShort(1).add_to_frame, f)

    def test_special_frames_are_not_addressed(self) -> None:
        """the fixed address bytes of special commands are not addresses"""
        for b in (0xCB, 0xBD):
            f = frame.ForwardFrame(32, b << 24)
            self.assertIsNone(address.from_frame(f))

    def test_gear_and_device_addresses_ignore_32_bit_frames(self) -> None:
        f = frame.ForwardFrame(32, 0xFEFB0000)
        self.assertIsInstance(address.from_frame(f), address.FirmwareAddress)


class TestFirmwareCommands(unittest.TestCase):
    def test_tridonic_encoding(self) -> None:
        """commands encode as the constants in Tridonic's d2cmddef.py"""
        bcast = address.FirmwareBroadcast()
        # D105_* | (DALI32_ADR_BROADCAST << 24)
        for cls, expected in (
                (firmware.StartFirmwareTransfer, 0xFEFB0000),
                (firmware.RestartFirmware, 0xFEFB0100),
                (firmware.EnableFirmwareRestart, 0xFEFB0200),
                (firmware.FinishFirmwareUpdate, 0xFEFB0300),
                (firmware.CancelFirmwareUpdate, 0xFEFB0400),
                (firmware.QueryFirmwareUpdateFeatures, 0xFEFB0500),
                (firmware.QueryFirmwareRestartEnabled, 0xFEFB0600),
                (firmware.QueryFirmwareUpdateReceiverReady, 0xFEFB0700),
                (firmware.QueryBlockFault, 0xFEFB0800),
                (firmware.QueryFirmwareUpdateVersion, 0xFEFB0900),
                (firmware.QueryBlock0Accepted, 0xFEFB0A00),
        ):
            self.assertEqual(cls(bcast).frame.as_integer, expected,
                             f"{cls.__name__} encoded wrongly")

    def test_special_command_encoding(self) -> None:
        """D105_BEGIN_BLOCK and D105_TRANSFER_BLOCK_DATA carry 24 bits"""
        self.assertEqual(
            firmware.BeginBlock(0x000001).frame.as_integer, 0xCB000001)
        self.assertEqual(
            firmware.TransferBlockData(0xAABBCC).frame.as_integer, 0xBDAABBCC)

    def test_special_command_data_range(self) -> None:
        self.assertRaises(ValueError, firmware.BeginBlock, -1)
        self.assertRaises(ValueError, firmware.BeginBlock, 0x1000000)
        self.assertRaises(ValueError, firmware.TransferBlockData, None)

    def test_integer_destination(self) -> None:
        """commands accept an integer destination as a short address"""
        self.assertEqual(firmware.StartFirmwareTransfer(5).destination,
                         address.FirmwareShort(5))
        self.assertRaises(ValueError, firmware.StartFirmwareTransfer, 64)

    def test_rejects_other_address_families(self) -> None:
        """control gear and control device addresses are not accepted"""
        self.assertRaises(ValueError,
                          firmware.StartFirmwareTransfer, address.Broadcast())
        self.assertRaises(ValueError,
                          firmware.StartFirmwareTransfer, address.DeviceShort(3))

    def test_frame_size(self) -> None:
        """all firmware transfer commands use 32-bit frames"""
        for cmd in (firmware.StartFirmwareTransfer(address.FirmwareBroadcast()),
                    firmware.BeginBlock(0),
                    firmware.TransferBlockData(0xFFFFFF)):
            self.assertEqual(len(cmd.frame), 32)
            self.assertIsInstance(cmd.frame, frame.ForwardFrame)

    def test_decode(self) -> None:
        """32-bit frames decode to the expected command classes"""
        for raw, cls in (
                (0xFEFB0000, firmware.StartFirmwareTransfer),
                (0xFCFB0400, firmware.CancelFirmwareUpdate),
                (0x0AFB0A00, firmware.QueryBlock0Accepted),
                (0xCB000123, firmware.BeginBlock),
                (0xBDAABBCC, firmware.TransferBlockData),
                # 0xff is not an opcode we know
                (0x02FBFF00, firmware.UnknownFirmwareCommand),
                # the marker byte is wrong
                (0x12345678, firmware.UnknownFirmwareCommand),
                # the last byte of an addressed command must be zero
                (0xFEFB0001, firmware.UnknownFirmwareCommand),
        ):
            c = command.from_frame(frame.ForwardFrame(32, raw))
            self.assertIsInstance(c, cls, f"0x{raw:08x} decoded as {c}")

    def test_decoded_destination(self) -> None:
        c = command.from_frame(frame.ForwardFrame(32, 0x0AFB0A00))
        assert isinstance(c, firmware._AddressedFirmwareCommand)
        self.assertEqual(c.destination, address.FirmwareShort(5))

    def test_block_data_is_never_an_addressed_command(self) -> None:
        """block payload that looks like a marker byte still decodes as data"""
        for addrbyte, cls in ((0xCB, firmware.BeginBlock),
                              (0xBD, firmware.TransferBlockData)):
            c = command.from_frame(
                frame.ForwardFrame(32, (addrbyte << 24) | 0xFB0000))
            self.assertIsInstance(c, cls)
            assert isinstance(c, firmware._SpecialFirmwareCommand)
            self.assertEqual(c.data, 0xFB0000)

    def test_queries(self) -> None:
        """queries expect a response, other commands do not"""
        bcast = address.FirmwareBroadcast()
        for cls in (firmware.QueryFirmwareUpdateFeatures,
                    firmware.QueryFirmwareRestartEnabled,
                    firmware.QueryFirmwareUpdateReceiverReady,
                    firmware.QueryBlockFault,
                    firmware.QueryFirmwareUpdateVersion,
                    firmware.QueryBlock0Accepted):
            self.assertTrue(cls(bcast).is_query, f"{cls.__name__} is not a query")
        for other in (firmware.StartFirmwareTransfer,
                      firmware.RestartFirmware,
                      firmware.EnableFirmwareRestart,
                      firmware.FinishFirmwareUpdate,
                      firmware.CancelFirmwareUpdate):
            self.assertFalse(other(bcast).is_query,
                             f"{other.__name__} is a query")
        self.assertFalse(firmware.BeginBlock(0).is_query)
        self.assertFalse(firmware.TransferBlockData(0).is_query)

    def test_devicetype_is_none(self) -> None:
        """32-bit frames are never preceded by EnableDeviceType"""
        for cls in firmware._FirmwareCommand._firmwarecommands:
            self.assertIsNone(cls.devicetype)


if __name__ == '__main__':
    unittest.main()
