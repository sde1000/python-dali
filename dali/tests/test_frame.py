import os
import sys
import unittest


import dali
from dali import frame


class TestFrame(unittest.TestCase):

    def test_frame_bits(self):
        """frames can only be initialised with an appropriate number of bits"""
        self.assertRaises(TypeError, frame.Frame, None)
        self.assertRaises(TypeError, frame.Frame, "wibble")
        self.assertRaises(TypeError, frame.Frame, 16.0)
        self.assertRaises(ValueError, frame.Frame, 0)
        self.assertRaises(ValueError, frame.Frame, 16, 0x1ffff)
        self.assertRaises(ValueError, frame.Frame, 16, -1)
        self.assertEqual(len(frame.Frame(16, 0xffff)), 16)
        self.assertEqual(len(frame.Frame(256, 1 << 255)), 256)

    def test_frame_init_data(self):
        """frames can be initialised with integer or iterable data"""
        self.assertEqual(
            frame.Frame(16, 0xffff),
            frame.Frame(16, (0xff, 0xff))
        )
        self.assertNotEqual(
            frame.Frame(16, 0xffff),
            frame.Frame(16, (0xff, 0xfe))
        )
        self.assertEqual(
            frame.Frame(16, 0xffff),
            frame.Frame(16, (0, 0, 0xff, 0xff))
        )

    def test_comparisons(self):
        """frame comparisons"""
        self.assertNotEqual(frame.Frame(24, 1), 1)
        self.assertNotEqual(frame.Frame(24, 1), frame.Frame(16, 1))
        self.assertEqual(frame.Frame(1), frame.Frame(1))
        self.assertEqual(frame.Frame(1) == frame.Frame(2), False)
        self.assertEqual(frame.Frame(1) != frame.Frame(2), True)

    def test_read(self):
        """frames return correct values when read using index"""
        # Frame will be 0001 0010 0011 0100 0101 0110
        # Index:        3210 9876 5432 1098 7654 3210
        f = frame.Frame(24, (0x12, 0x34, 0x56))
        self.assertEqual(f[0], False)
        self.assertEqual(f[1], True)
        self.assertEqual(f[20], True)
        self.assertRaises(IndexError, lambda: f[24])
        self.assertRaises(IndexError, lambda: f[-1])
        self.assertRaises(TypeError, lambda: f['wibble'])
        self.assertRaises(TypeError, lambda: f[3:0:2])
        self.assertRaises(IndexError, lambda: f[24:20])
        self.assertEqual(f[3:0], 6)
        self.assertEqual(f[7:4], 5)
        self.assertEqual(f[4:7], 5)
        self.assertEqual(f[23:20], 1)
        self.assertEqual(f[2:0], 6)
        self.assertEqual(f[0:0], 0)
        self.assertEqual(f[1:1], 1)
        self.assertEqual(f[2:1], 3)
        self.assertEqual(f[17:10], int("10001101", 2))

    def test_write(self):
        """writing to frames works correctly using indices and slices"""
        f = frame.Frame(24)
        f[1] = True
        self.assertEqual(f[23:0], 2)
        f[2] = True
        self.assertEqual(f[23:0], 6)
        f[1] = False
        self.assertEqual(f[23:0], 4)
        f[0] = 'yes'
        self.assertEqual(f[23:0], 5)
        f[2] = 0
        self.assertEqual(f[23:0], 1)
        with self.assertRaises(IndexError):
            f[24] = True
        with self.assertRaises(IndexError):
            f[-24] = True
        with self.assertRaises(TypeError):
            f['wobble'] = False
        with self.assertRaises(TypeError):
            f[4:3:2] = 2
        # Test large frame that stores data as a long
        f = frame.Frame(256)
        f[200] = True
        f[202] = True
        self.assertEqual(f[202:199], 10)
        f = frame.Frame(24)
        f[7:4] = 0xf
        self.assertEqual(f[23:0], 0xf0)
        f[4:4] = 0
        self.assertEqual(f[23:0], 0xe0)
        f[20:23] = 0xa
        self.assertEqual(f[23:0], 0xa000e0)
        with self.assertRaises(ValueError):
            f[3:0] = 0x10
        with self.assertRaises(TypeError):
            f[20:20] = 'wibble'
        with self.assertRaises(IndexError):
            f[24:20] = 10
        with self.assertRaises(ValueError):
            f[7:4] = -2

    def test_add(self):
        """frame concatenation works as expected"""
        self.assertEqual(
            frame.Frame(16, 0x1234) + frame.Frame(16, 0x5678),
            frame.Frame(32, 0x12345678)
        )
        self.assertRaises(TypeError, lambda: frame.Frame(8, 0xff) + 1)
        self.assertRaises(TypeError, lambda: 1 + frame.Frame(8, 0xff))

    def test_as_integer(self):
        """returning frame as integer works as expected"""
        self.assertEqual(frame.Frame(32, 0x12345678).as_integer, 0x12345678)

    def test_as_byte_sequence(self):
        """constructing frames from byte sequence works as expected"""
        f = frame.Frame(29, 0x12345678)
        self.assertEqual(frame.Frame(29, f.as_byte_sequence), f)

    def test_pack(self):
        """frame packing return expected byte strings"""
        f = frame.Frame(28, 0x2345678)
        self.assertEqual(f.pack, b'\x02\x34\x56\x78')
        f = frame.Frame(16, 0xaa55)
        self.assertEqual(f.pack, b'\xaa\x55')

    def test_pack_len(self):
        """frame packing with length returns expected byte strings"""
        f = frame.Frame(28, 0x2345678)
        self.assertRaises(ValueError, lambda: f.pack_len(3))
        self.assertEqual(f.pack_len(4), b'\x02\x34\x56\x78')
        self.assertEqual(f.pack_len(5), b'\x00\x02\x34\x56\x78')
        f = frame.Frame(16, 0xaa55)
        self.assertRaises(ValueError, lambda: f.pack_len(0))
        self.assertEqual(f.pack_len(2), b'\xaa\x55')
        self.assertEqual(f.pack_len(4), b'\x00\x00\xaa\x55')

    def test_contains(self):
        """frame __contains__ method works as expected"""
        self.assertTrue(True in frame.Frame(16, 0xaa55))
        self.assertTrue(False in frame.Frame(16, 0xaa55))
        self.assertFalse(True in frame.Frame(16, 0))
        self.assertFalse(False in frame.Frame(16, 0xffff))
        self.assertFalse('wibble' in frame.Frame(16))

    def test_str(self):
        """frame objects can be converted to strings"""
        self.assertIsInstance(
            str(frame.Frame(123, 0x12345)),
            str)


if __name__ == '__main__':
    unittest.main()
