import unittest
try:
    from unittest import mock
except ImportError:
    import mock

from pymodbus.client.sync import ModbusSerialClient, ModbusTcpClient

from dali.address import Short
from dali.command import Command
from dali.driver.unipi import (
    DALI_NO_RESPONSE,
    RemoteArm,
    SyncUnipiDALIDriver,
    UnipiDALIDriver,
)
from dali.frame import BackwardFrame, ForwardFrame
from dali.gear.general import DAPC, Reset


class TestRemoteArm(unittest.TestCase):
    @mock.patch("dali.driver.unipi.pyRtu")
    @mock.patch("dali.driver.unipi.pySerial")
    def setUp(self, mock_tcp, mock_rtu):
        mock_tcp.return_value = mock.MagicMock(spec=ModbusTcpClient)
        mock_rtu.return_value = mock.MagicMock(spec=ModbusSerialClient)
        self.remote_arm_tcp = RemoteArm(host="http://localhost.lan")
        self.remote_arm_rtu = RemoteArm(host="/home")

    def test_init_serial(self):
        remote_arm = RemoteArm(host="/serial")
        self.assertIsInstance(remote_arm.pymc, ModbusSerialClient)
        self.assertEqual(remote_arm.unit, 1)

    def test_init_tcp(self):
        remote_arm = RemoteArm(host="http://localhost.lan")
        self.assertIsInstance(remote_arm.pymc, ModbusTcpClient)
        self.assertEqual(remote_arm.unit, 1)

    def test_close(self):
        self.remote_arm_tcp.close()
        self.assertEqual(self.remote_arm_tcp.pymc.close.called, True)

    def test_read_regs(self):
        self.remote_arm_tcp.read_regs(10, 5)
        self.remote_arm_tcp.pymc.read_holding_registers.assert_called_with(
            10, 5, unit=1
        )

    def test_read_regs_unit(self):
        self.remote_arm_tcp.read_regs(10, 5, unit=5)
        self.remote_arm_tcp.pymc.read_holding_registers.assert_called_with(
            10, 5, unit=5
        )

    def test_write_regs_list(self):
        self.remote_arm_tcp.write_regs(10, [1, 2], unit=10)
        self.remote_arm_tcp.pymc.write_registers.assert_called_with(10, [1, 2], unit=10)

    def test_write_regs_single(self):
        self.remote_arm_tcp.write_regs(10, 1)
        self.remote_arm_tcp.pymc.write_register.assert_called_with(10, 1, unit=1)

    def test_write_coil(self):
        self.remote_arm_tcp.write_coil(10, 1, unit=42)
        self.remote_arm_tcp.pymc.write_coil.assert_called_with(10, 1, unit=42)

    def test_reboot(self):
        self.remote_arm_tcp.reboot()
        self.remote_arm_tcp.pymc.write_coil.assert_called_with(1002, 1, unit=1)

    @mock.patch("dali.driver.unipi.RemoteArm.read_regs", return_value=[4])
    def test_vref(self, mock_read_regs):
        self.assertEqual(self.remote_arm_tcp.Vref(), 3.3)


class TestUnipiDALIDriver(unittest.TestCase):
    def test_construct_length_16(self):
        driver = UnipiDALIDriver()
        command = DAPC(Short(1), 2)
        self.assertEqual(driver.construct(command), (512, 514))

    def test_construct_length_16_config(self):
        driver = UnipiDALIDriver()
        command = Reset(Short(1))
        self.assertEqual(driver.construct(command), (2560, 800))

    def test_construct_length_24(self):
        driver = UnipiDALIDriver()
        mock_command = mock.MagicMock(spec=Command)
        mock_frame = mock.MagicMock(spec=ForwardFrame)
        mock_frame.__len__.return_value = 24
        mock_frame.as_byte_sequence = (1, 2, 3)
        mock_command.frame = mock_frame
        mock_command.sendtwice = False
        self.assertEqual(driver.construct(mock_command), (769, 515))

    def test_construct_length_24_config(self):
        driver = UnipiDALIDriver()
        mock_command = mock.MagicMock(spec=Command)
        mock_frame = mock.MagicMock(spec=ForwardFrame)
        mock_frame.__len__.return_value = 24
        mock_frame.as_byte_sequence = (1, 2, 3)
        mock_command.frame = mock_frame
        mock_command.sendtwice = True
        self.assertEqual(driver.construct(mock_command), (2817, 515))

    def test_construct_non_standard_length(self):
        driver = UnipiDALIDriver()
        mock_command = mock.MagicMock(spec=Command)
        mock_frame = mock.MagicMock(spec=ForwardFrame)
        mock_frame.__len__.return_value = 1
        with self.assertRaises(ValueError):
            driver.construct(mock_command)

    def test_extract_forward_frame(self):
        driver = UnipiDALIDriver()
        frame = driver.extract([0x200, 0x11])
        self.assertIsInstance(frame, ForwardFrame)
        self.assertEqual(frame.as_integer, 17)

    def test_extract_backward_frame(self):
        driver = UnipiDALIDriver()
        frame = driver.extract([0x100, 0x11])
        self.assertIsInstance(frame, BackwardFrame)
        self.assertEqual(frame.as_integer, 17)

    def test_extract_no_response(self):
        driver = UnipiDALIDriver()
        self.assertEqual(driver.extract([0x1111]), DALI_NO_RESPONSE)

    def test_get_serial_number_init(self):
        driver = UnipiDALIDriver()
        self.assertEqual(driver._get_sn(), 1)

    def test_get_serial_number(self):
        driver = UnipiDALIDriver()
        driver._next_sn = 1
        self.assertEqual(driver._get_sn(), 2)

    def test_get_serial_number_random(self):
        driver = UnipiDALIDriver()
        driver._next_sn = 5
        self.assertEqual(driver._get_sn(), 6)

    def test_get_serial_number_overflows(self):
        driver = UnipiDALIDriver()
        driver._next_sn = 255
        self.assertEqual(driver._get_sn(), 1)


class TestSyncUnipiDALIDriver(unittest.TestCase):
    @mock.patch("dali.driver.unipi.RemoteArm")
    def setUp(self, mock_backend):
        self.sync_driver = SyncUnipiDALIDriver()
        self.mock_backend = self.sync_driver.backend

    def test_send_simple_command(self):
        mock_command = mock.MagicMock(spec=Command)
        mock_frame = mock.MagicMock(spec=ForwardFrame)
        mock_frame.__len__.return_value = 16
        mock_frame.as_byte_sequence = (1, 2)
        mock_command.frame = mock_frame
        mock_command.sendtwice = False
        self.mock_backend.read_regs.return_value = (1,)

        self.assertEqual(self.sync_driver.send(mock_command), DALI_NO_RESPONSE)

    def test_send_with_response(self):
        mock_command = mock.MagicMock(spec=Command)
        mock_frame = mock.MagicMock(spec=ForwardFrame)
        mock_frame.__len__.return_value = 16
        mock_frame.as_byte_sequence = (1, 2)
        mock_command.frame = mock_frame
        mock_command.sendtwice = False
        mock_command._response = 1
        mock_command.response.return_value = "foo"
        self.mock_backend.read_regs.side_effect = [(1,), (2,), (3, 0x100, 0x11)]

        self.assertEqual(self.sync_driver.send(mock_command), "foo")

    def test_send_with_compare_response(self):
        mock_command = mock.MagicMock(spec=Command)
        mock_frame = mock.MagicMock(spec=ForwardFrame)
        mock_frame.__len__.return_value = 16
        mock_frame.as_byte_sequence = (1, 2)
        mock_command.frame = mock_frame
        mock_command.sendtwice = False
        mock_command._response = 1
        mock_command._cmdval = 0xA9
        self.mock_backend.read_regs.side_effect = [(1,), (2,), (3, 0x200, 0x11), (4,)]

        self.sync_driver.send(mock_command)
        mock_command.response.assert_called_with(BackwardFrame(0xFF))
