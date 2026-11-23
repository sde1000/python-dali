"""Tests for the firmware transfer sequences.

The sequences are driven by a fake bus that answers queries from a
table, so these check the order and content of the frames a driver
would transmit.
"""
from typing import Any, Optional
import unittest

from dali import address, firmware
from dali.command import Command
from dali.exceptions import DALISequenceError
from dali.firmware_sequences import (
    FindFirmwareUpdateTargets,
    FirmwareUpdate,
    RestartFirmwareUpdateTarget,
)
from dali.frame import BackwardFrame
from dali.sequences import progress, sleep


def _run(seq: Any,
         answers: Optional[dict[Any, Any]] = None,
         sent: Optional[list[Command]] = None
         ) -> tuple[list[Command], Any]:
    """Run a sequence against a fake bus.

    answers maps a command class to either a value to be answered every
    time, or a list of values answered in turn.  A value of None means
    "no backward frame", which is how a DALI unit says "No".  Returns
    the commands that were sent and the sequence's return value.

    Pass a list as sent to see what was transmitted by a sequence that
    is expected to raise.
    """
    answers = dict(answers or {})
    sent = [] if sent is None else sent
    response = None
    while True:
        try:
            cmd = seq.send(response)
        except StopIteration as r:
            return sent, r.value
        response = None
        if isinstance(cmd, (sleep, progress)):
            continue
        assert isinstance(cmd, Command)
        sent.append(cmd)
        if cmd.response is None:
            # Not a query; a driver returns None for these
            continue
        answer = answers.get(type(cmd))
        if isinstance(answer, list):
            answer = answer.pop(0) if answer else None
        response = cmd.response(
            None if answer is None else BackwardFrame(answer))


# An image of 10 bytes, transferred as two blocks of six bytes with the
# last two bytes padded
IMAGE = bytes(range(10))


class TestFirmwareUpdate(unittest.TestCase):
    def test_unverified_update_frame_sequence(self) -> None:
        """a broadcast update sends start, blocks, finish and restart"""
        seq = FirmwareUpdate(address.FirmwareBroadcast(), IMAGE, block_size=6)
        sent, blocks = _run(seq)

        self.assertEqual(blocks, 2)
        self.assertEqual(
            [type(c) for c in sent],
            [firmware.StartFirmwareTransfer,
             firmware.BeginBlock,
             firmware.TransferBlockData, firmware.TransferBlockData,
             firmware.BeginBlock,
             firmware.TransferBlockData, firmware.TransferBlockData,
             firmware.FinishFirmwareUpdate,
             firmware.EnableFirmwareRestart,
             firmware.RestartFirmware])
        # Block numbers count from zero
        self.assertEqual([c.data for c in sent
                          if isinstance(c, firmware.BeginBlock)], [0, 1])
        # The image is transferred three bytes at a time, and the final
        # frame is padded
        self.assertEqual([c.data for c in sent
                          if isinstance(c, firmware.TransferBlockData)],
                         [0x000102, 0x030405, 0x060708, 0x09FFFF])

    def test_padding_byte_is_configurable(self) -> None:
        seq = FirmwareUpdate(address.FirmwareBroadcast(), IMAGE,
                             block_size=6, padding=0x00)
        sent, _ = _run(seq)
        data = [c.data for c in sent
                if isinstance(c, firmware.TransferBlockData)]
        self.assertEqual(data[-1], 0x090000)

    def test_block_size_that_is_not_a_multiple_of_three(self) -> None:
        """a block is always a whole number of frames"""
        seq = FirmwareUpdate(address.FirmwareBroadcast(), b"\x01\x02\x03\x04",
                             block_size=4)
        sent, blocks = _run(seq)
        self.assertEqual(blocks, 1)
        self.assertEqual([c.data for c in sent
                          if isinstance(c, firmware.TransferBlockData)],
                         [0x010203, 0x04FFFF])

    def test_verified_update_of_a_short_address(self) -> None:
        """a short address is queried about the image and each block"""
        seq = FirmwareUpdate(address.FirmwareShort(3), IMAGE, block_size=6)
        sent, blocks = _run(seq, {
            firmware.QueryFirmwareUpdateFeatures: 0x01,
            firmware.QueryBlock0Accepted: 0xFF,
            firmware.QueryBlockFault: None,  # No fault
            firmware.QueryFirmwareUpdateReceiverReady: 0xFF,
            firmware.QueryFirmwareRestartEnabled: 0xFF,
        })

        self.assertEqual(blocks, 2)
        self.assertEqual(
            [type(c) for c in sent],
            [firmware.QueryFirmwareUpdateFeatures,
             firmware.StartFirmwareTransfer,
             firmware.BeginBlock,
             firmware.TransferBlockData, firmware.TransferBlockData,
             firmware.QueryBlock0Accepted,
             firmware.QueryBlockFault,
             firmware.QueryFirmwareUpdateReceiverReady,
             firmware.BeginBlock,
             firmware.TransferBlockData, firmware.TransferBlockData,
             firmware.QueryBlockFault,
             firmware.QueryFirmwareUpdateReceiverReady,
             firmware.FinishFirmwareUpdate,
             firmware.EnableFirmwareRestart,
             firmware.QueryFirmwareRestartEnabled,
             firmware.RestartFirmware])
        # Every addressed command went to the address we asked for
        for cmd in sent:
            if isinstance(cmd, firmware._AddressedFirmwareCommand):
                self.assertEqual(cmd.destination, address.FirmwareShort(3))

    def test_integer_destination_is_a_short_address(self) -> None:
        seq = FirmwareUpdate(3, IMAGE, block_size=6, verify=False)
        sent, _ = _run(seq)
        assert isinstance(sent[0], firmware._AddressedFirmwareCommand)
        self.assertEqual(sent[0].destination, address.FirmwareShort(3))

    def test_faulty_block_is_retried(self) -> None:
        seq = FirmwareUpdate(address.FirmwareShort(3), b"\x01\x02\x03",
                             block_size=3, retries=2, restart=False)
        sent, blocks = _run(seq, {
            firmware.QueryFirmwareUpdateFeatures: 0x01,
            firmware.QueryBlock0Accepted: 0xFF,
            # Fault, fault, then success
            firmware.QueryBlockFault: [0xFF, 0xFF, None],
            firmware.QueryFirmwareUpdateReceiverReady: 0xFF,
        })

        self.assertEqual(blocks, 1)
        self.assertEqual(
            len([c for c in sent if isinstance(c, firmware.BeginBlock)]), 3)
        self.assertNotIn(firmware.CancelFirmwareUpdate,
                         [type(c) for c in sent])

    def test_update_is_cancelled_when_every_retry_is_faulty(self) -> None:
        seq = FirmwareUpdate(address.FirmwareShort(3), b"\x01\x02\x03",
                             block_size=3, retries=1)
        with self.assertRaises(DALISequenceError):
            sent, _ = _run(seq, {
                firmware.QueryFirmwareUpdateFeatures: 0x01,
                firmware.QueryBlock0Accepted: 0xFF,
                firmware.QueryBlockFault: 0xFF,  # Always faulty
            })

    def test_cancel_is_sent_after_a_failure(self) -> None:
        sent: list[Command] = []
        seq = FirmwareUpdate(address.FirmwareShort(3), b"\x01\x02\x03",
                             block_size=3, retries=0)
        with self.assertRaises(DALISequenceError):
            _run(seq, {
                firmware.QueryFirmwareUpdateFeatures: 0x01,
                firmware.QueryBlock0Accepted: 0xFF,
                firmware.QueryBlockFault: 0xFF,
            }, sent)
        self.assertIsInstance(sent[-1], firmware.CancelFirmwareUpdate)

    def test_rejected_block_0_is_not_retried(self) -> None:
        """a unit that refuses the image is not asked again"""
        sent: list[Command] = []
        seq = FirmwareUpdate(address.FirmwareShort(3), IMAGE,
                             block_size=6, retries=3)
        with self.assertRaises(DALISequenceError):
            _run(seq, {
                firmware.QueryFirmwareUpdateFeatures: 0x01,
                firmware.QueryBlock0Accepted: None,  # "No"
            }, sent)
        self.assertEqual(
            len([c for c in sent if isinstance(c, firmware.BeginBlock)]), 1)
        self.assertIsInstance(sent[-1], firmware.CancelFirmwareUpdate)

    def test_silent_unit_fails_the_features_query(self) -> None:
        """verification notices a unit that does not support the update"""
        with self.assertRaises(DALISequenceError):
            _run(FirmwareUpdate(address.FirmwareShort(3), IMAGE,
                                block_size=6))

    def test_receiver_that_never_becomes_ready_times_out(self) -> None:
        """a unit that stops answering is not mistaken for a busy one"""
        sent: list[Command] = []
        seq = FirmwareUpdate(address.FirmwareShort(3), b"\x01\x02\x03",
                             block_size=3, ready_poll_interval=0.01,
                             ready_poll_timeout=0.05)
        with self.assertRaises(DALISequenceError):
            _run(seq, {
                firmware.QueryFirmwareUpdateFeatures: 0x01,
                firmware.QueryBlock0Accepted: 0xFF,
                firmware.QueryBlockFault: None,
                firmware.QueryFirmwareUpdateReceiverReady: None,
            }, sent)
        self.assertGreater(
            len([c for c in sent
                 if isinstance(c,
                               firmware.QueryFirmwareUpdateReceiverReady)]), 1)
        self.assertIsInstance(sent[-1], firmware.CancelFirmwareUpdate)

    def test_restart_can_be_skipped(self) -> None:
        seq = FirmwareUpdate(address.FirmwareBroadcast(), IMAGE,
                             block_size=6, restart=False)
        sent, _ = _run(seq)
        self.assertIsInstance(sent[-1], firmware.FinishFirmwareUpdate)

    def test_bad_arguments(self) -> None:
        for kwargs in ({"block_size": 0},
                       {"block_size": 6, "padding": 256},
                       {"block_size": 6, "padding": -1}):
            with self.assertRaises(ValueError):
                _run(FirmwareUpdate(address.FirmwareBroadcast(),
                                    IMAGE, **kwargs))  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            _run(FirmwareUpdate(address.FirmwareBroadcast(), b"",
                                block_size=6))
        with self.assertRaises(ValueError):
            _run(FirmwareUpdate(
                "not an address",  # type: ignore[arg-type]
                IMAGE, block_size=6))

    def test_closing_the_sequence_does_not_yield(self) -> None:
        """a driver that abandons the sequence must not get a cancel frame

        The driver closes the generator in a finally block; yielding
        during a close would raise RuntimeError.
        """
        seq = FirmwareUpdate(address.FirmwareBroadcast(), IMAGE, block_size=6)
        next(seq)
        seq.close()


class TestRestart(unittest.TestCase):
    def test_restart_is_enabled_first(self) -> None:
        sent, _ = _run(
            RestartFirmwareUpdateTarget(address.FirmwareShort(5)),
            {firmware.QueryFirmwareRestartEnabled: 0xFF})
        self.assertEqual([type(c) for c in sent],
                         [firmware.EnableFirmwareRestart,
                          firmware.QueryFirmwareRestartEnabled,
                          firmware.RestartFirmware])

    def test_restart_that_is_not_enabled_raises(self) -> None:
        with self.assertRaises(DALISequenceError):
            _run(RestartFirmwareUpdateTarget(address.FirmwareShort(5)))

    def test_restart_without_verification(self) -> None:
        sent, _ = _run(
            RestartFirmwareUpdateTarget(address.FirmwareShort(5),
                                        verify=False))
        self.assertEqual([type(c) for c in sent],
                         [firmware.EnableFirmwareRestart,
                          firmware.RestartFirmware])


class TestFindFirmwareUpdateTargets(unittest.TestCase):
    def test_only_units_that_answer_are_returned(self) -> None:
        sent, found = _run(
            FindFirmwareUpdateTargets(addresses=(0, 1, 2)),
            {firmware.QueryFirmwareUpdateFeatures: [None, 0x03, None],
             firmware.QueryFirmwareUpdateVersion: [0x02]})

        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].address, 1)
        self.assertEqual(found[0].features, 3)
        self.assertEqual(found[0].version, 2)
        # The version is only asked for once the features query answered
        self.assertEqual(
            len([c for c in sent
                 if isinstance(c, firmware.QueryFirmwareUpdateVersion)]), 1)

    def test_all_short_addresses_are_scanned_by_default(self) -> None:
        sent, found = _run(FindFirmwareUpdateTargets())
        self.assertEqual(found, [])
        self.assertEqual(len(sent), 64)
        assert isinstance(sent[-1], firmware._AddressedFirmwareCommand)
        self.assertEqual(sent[-1].destination, address.FirmwareShort(63))

    def test_a_unit_that_does_not_report_a_version(self) -> None:
        _, found = _run(
            FindFirmwareUpdateTargets(addresses=(7,)),
            {firmware.QueryFirmwareUpdateFeatures: 0x01})
        self.assertEqual(found[0].version, None)


if __name__ == '__main__':
    unittest.main()
