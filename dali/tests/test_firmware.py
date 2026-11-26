import unittest

from dali import address
from dali import command
from dali import firmware
from dali import frame
from dali.exceptions import IncompatibleFrame


class TestFirmwareAddresses(unittest.TestCase):
    def test_encoding(self) -> None:
        """address bytes are encoded as in IEC 62386-105 Table 1

        Bit 24 selects the address space: 0 for control gear, 1 for
        control devices.
        """
        for addr, expected in (
                # bits 31..24 = 1111111x, broadcast
                (address.FirmwareGearBroadcast(), 0xFE),
                (address.FirmwareDeviceBroadcast(), 0xFF),
                # bits 31..24 = 1111110x, broadcast unaddressed
                (address.FirmwareGearBroadcastUnaddressed(), 0xFC),
                (address.FirmwareDeviceBroadcastUnaddressed(), 0xFD),
                # bits 31..24 = 0AAAAAAx, short addressing
                (address.FirmwareGearShort(0), 0x00),
                (address.FirmwareDeviceShort(0), 0x01),
                (address.FirmwareGearShort(1), 0x02),
                (address.FirmwareDeviceShort(1), 0x03),
                (address.FirmwareGearShort(63), 0x7E),
                (address.FirmwareDeviceShort(63), 0x7F),
        ):
            f = frame.ForwardFrame(32, 0)
            addr.add_to_frame(f)
            self.assertEqual(f[31:24], expected, f"{addr} encoded wrongly")

    def test_bit_24_selects_the_address_space(self) -> None:
        """the gear and device forms of one address differ only in bit 24"""
        for gear, device in (
                (address.FirmwareGearBroadcast(),
                 address.FirmwareDeviceBroadcast()),
                (address.FirmwareGearBroadcastUnaddressed(),
                 address.FirmwareDeviceBroadcastUnaddressed()),
                (address.FirmwareGearShort(37),
                 address.FirmwareDeviceShort(37)),
        ):
            fg = frame.ForwardFrame(32, 0)
            gear.add_to_frame(fg)
            fd = frame.ForwardFrame(32, 0)
            device.add_to_frame(fd)
            self.assertFalse(fg[24], f"{gear} set bit 24")
            self.assertTrue(fd[24], f"{device} cleared bit 24")
            self.assertEqual(fg[31:25], fd[31:25],
                             f"{gear} and {device} differ above bit 24")
            self.assertNotEqual(gear, device)

    def test_roundtrip(self) -> None:
        """firmware addresses survive address.from_frame()"""
        for addr in (address.FirmwareGearBroadcast(),
                     address.FirmwareDeviceBroadcast(),
                     address.FirmwareGearBroadcastUnaddressed(),
                     address.FirmwareDeviceBroadcastUnaddressed(),
                     address.FirmwareGearShort(0),
                     address.FirmwareDeviceShort(0),
                     address.FirmwareGearShort(37),
                     address.FirmwareDeviceShort(37),
                     address.FirmwareGearShort(63),
                     address.FirmwareDeviceShort(63)):
            f = frame.ForwardFrame(32, 0)
            addr.add_to_frame(f)
            self.assertEqual(address.from_frame(f), addr)

    def test_short_address_range(self) -> None:
        for cls in (address.FirmwareGearShort, address.FirmwareDeviceShort):
            self.assertRaises(ValueError, cls, -1)
            self.assertRaises(ValueError, cls, 64)
            self.assertRaises(ValueError, cls, None)

    def test_wrong_frame_size(self) -> None:
        """firmware addresses refuse to go into 16- and 24-bit frames"""
        for bits in (16, 24):
            f = frame.ForwardFrame(bits, 0)
            for addr in (address.FirmwareGearBroadcast(),
                         address.FirmwareDeviceBroadcast(),
                         address.FirmwareGearShort(1),
                         address.FirmwareDeviceShort(1)):
                self.assertRaises(
                    IncompatibleFrame, addr.add_to_frame, f)

    def test_special_frames_are_not_addressed(self) -> None:
        """the fixed address bytes of data transfer commands are not addresses

        0xcb and 0xbd fall into the "all other address byte values are
        reserved" row of Table 1, so they must not decode as addresses.
        """
        for b in (0xCB, 0xBD):
            f = frame.ForwardFrame(32, b << 24)
            self.assertIsNone(address.from_frame(f))

    def test_gear_and_device_addresses_ignore_32_bit_frames(self) -> None:
        f = frame.ForwardFrame(32, 0xFEFB0000)
        self.assertIsInstance(address.from_frame(f), address.FirmwareAddress)


class TestFirmwareCommands(unittest.TestCase):
    def test_command_encoding(self) -> None:
        """commands encode as "address 0xfb opcode 0x00", Table 6

        The opcodes are those of Table 6, sent to the control gear
        broadcast address of Table 1.
        """
        bcast = address.FirmwareGearBroadcast()
        for cls, expected in (
                (firmware.StartFirmwareTransfer, 0xFEFB0000),
                (firmware.RestartFirmware, 0xFEFB0100),
                (firmware.EnableRestart, 0xFEFB0200),
                (firmware.FinishFirmwareUpdate, 0xFEFB0300),
                (firmware.CancelFirmwareUpdate, 0xFEFB0400),
                (firmware.QueryFirmwareUpdateFeatures, 0xFEFB0500),
                (firmware.QueryFirmwareRestartEnabled, 0xFEFB0600),
                (firmware.QueryFirmwareUpdateReceiverReady, 0xFEFB0700),
                (firmware.QueryBlockIncompleteOrFault, 0xFEFB0800),
                (firmware.QueryFirmwareTransferVersion, 0xFEFB0900),
                (firmware.QueryBlock0Accepted, 0xFEFB0A00),
        ):
            self.assertEqual(cls(bcast).frame.as_integer, expected,
                             f"{cls.__name__} encoded wrongly")

    def test_control_device_commands_set_bit_24(self) -> None:
        """the same command to the device address space differs by bit 24"""
        gear = firmware.StartFirmwareTransfer(address.FirmwareGearShort(3))
        device = firmware.StartFirmwareTransfer(address.FirmwareDeviceShort(3))
        self.assertEqual(gear.frame.as_integer, 0x06FB0000)
        self.assertEqual(device.frame.as_integer, 0x07FB0000)

    def test_no_command_is_sent_twice(self) -> None:
        """neither Table 6 nor Table 7 marks any command "send twice" """
        bcast = address.FirmwareGearBroadcast()
        for cls in (firmware.StartFirmwareTransfer,
                    firmware.RestartFirmware,
                    firmware.EnableRestart,
                    firmware.FinishFirmwareUpdate,
                    firmware.CancelFirmwareUpdate,
                    firmware.QueryFirmwareUpdateFeatures,
                    firmware.QueryBlock0Accepted):
            self.assertFalse(cls(bcast).sendtwice,
                             f"{cls.__name__} is marked send twice")
        self.assertFalse(firmware.BeginBlock(0).sendtwice)
        self.assertFalse(firmware.TransferBlockData(0).sendtwice)

    def test_special_command_encoding(self) -> None:
        """BEGIN BLOCK and TRANSFER BLOCK DATA carry 24 bits, Table 7"""
        self.assertEqual(
            firmware.BeginBlock(0x000001).frame.as_integer, 0xCB000001)
        self.assertEqual(
            firmware.TransferBlockData(0xAABBCC).frame.as_integer, 0xBDAABBCC)

    def test_special_command_data_range(self) -> None:
        self.assertRaises(ValueError, firmware.BeginBlock, -1)
        self.assertRaises(ValueError, firmware.BeginBlock, 0x1000000)
        self.assertRaises(ValueError, firmware.TransferBlockData, None)

    def test_integer_destination_is_rejected(self) -> None:
        """a bare integer does not say which address space is meant"""
        self.assertRaises(ValueError, firmware.StartFirmwareTransfer, 5)
        self.assertRaises(ValueError, firmware.StartFirmwareTransfer, 64)

    def test_rejects_other_address_families(self) -> None:
        """control gear and control device addresses are not accepted"""
        self.assertRaises(ValueError,
                          firmware.StartFirmwareTransfer, address.Broadcast())
        self.assertRaises(
            ValueError, firmware.StartFirmwareTransfer, address.DeviceShort(3))

    def test_frame_size(self) -> None:
        """all firmware transfer commands use 32-bit frames"""
        gear = address.FirmwareGearBroadcast()
        device = address.FirmwareDeviceBroadcast()
        for cmd in (firmware.StartFirmwareTransfer(gear),
                    firmware.StartFirmwareTransfer(device),
                    firmware.BeginBlock(0),
                    firmware.TransferBlockData(0xFFFFFF)):
            self.assertEqual(len(cmd.frame), 32)
            self.assertIsInstance(cmd.frame, frame.ForwardFrame)

    def test_decode(self) -> None:
        """32-bit frames decode to the expected command classes"""
        for raw, cls in (
                (0xFEFB0000, firmware.StartFirmwareTransfer),
                (0xFFFB0000, firmware.StartFirmwareTransfer),
                (0xFCFB0400, firmware.CancelFirmwareUpdate),
                (0xFDFB0400, firmware.CancelFirmwareUpdate),
                (0x0AFB0A00, firmware.QueryBlock0Accepted),
                (0x0BFB0A00, firmware.QueryBlock0Accepted),
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
        """bit 24 of a decoded frame picks the address space"""
        gear = command.from_frame(frame.ForwardFrame(32, 0x0AFB0A00))
        assert isinstance(gear, firmware._AddressedFirmwareCommand)
        self.assertEqual(gear.destination, address.FirmwareGearShort(5))

        device = command.from_frame(frame.ForwardFrame(32, 0x0BFB0A00))
        assert isinstance(device, firmware._AddressedFirmwareCommand)
        self.assertEqual(device.destination, address.FirmwareDeviceShort(5))

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
        bcast = address.FirmwareGearBroadcast()
        for cls in (firmware.QueryFirmwareUpdateFeatures,
                    firmware.QueryFirmwareRestartEnabled,
                    firmware.QueryFirmwareUpdateReceiverReady,
                    firmware.QueryBlockIncompleteOrFault,
                    firmware.QueryFirmwareTransferVersion,
                    firmware.QueryBlock0Accepted):
            self.assertTrue(cls(bcast).is_query,
                            f"{cls.__name__} is not a query")
        for other in (firmware.StartFirmwareTransfer,
                      firmware.RestartFirmware,
                      firmware.EnableRestart,
                      firmware.FinishFirmwareUpdate,
                      firmware.CancelFirmwareUpdate):
            self.assertFalse(other(bcast).is_query,
                             f"{other.__name__} is a query")
        self.assertFalse(firmware.BeginBlock(0).is_query)
        self.assertFalse(firmware.TransferBlockData(0).is_query)

    def test_devicetype_is_ignored(self) -> None:
        """32-bit frames are never preceded by EnableDeviceType

        Whatever device type was last enabled has no bearing on a 32-bit
        frame, so decoding one must not depend on it.
        """
        f = frame.ForwardFrame(32, 0x0AFB0700)
        for devicetype in (0, 6, 8):
            c = command.from_frame(f, devicetype=devicetype)
            self.assertIsInstance(
                c, firmware.QueryFirmwareUpdateReceiverReady,
                f"decoded as {c} with device type {devicetype} enabled")


if __name__ == '__main__':
    unittest.main()
