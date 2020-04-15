import struct

_bad_init_data = TypeError(
    "data must be a sequence of integers all in the range 0..255 or an integer")


class Frame:
    """A DALI frame.

    A Frame consists of one start bit, n data bits, and one stop
    condition.  The most significant bit is always transmitted first.

    Instances of this object are mutable.
    """

    def __init__(self, bits, data=0):
        """Initialise a Frame with the supplied number of data bits.

        :parameter bits: the number of data bits in the Frame
        :parameter data: initial data for the Frame as an integer or
        an iterable sequence of integers
        """
        if not isinstance(bits, int):
            raise TypeError(
                "Number of bits must be an integer")
        if bits < 1:
            raise ValueError(
                "Frames must contain at least 1 data bit")
        self._bits = bits
        if isinstance(data, int):
            self._data = data
        else:
            d = 0
            for b in data:
                if not isinstance(b, int):
                    raise _bad_init_data
                if b < 0 or b > 255:
                    raise _bad_init_data
                d = (d << 8) | b
            self._data = d
        if self._data < 0:
            raise ValueError(
                "Initial data must not be negative")
        if self._data.bit_length() > bits:
            raise ValueError(
                "Initial data will not fit in {} bits".format(bits))
        self._error = False

    @property
    def error(self):
        """Frame was received with a framing error."""
        return self._error

    def __len__(self):
        return self._bits

    def __eq__(self, other):
        try:
            return self._bits == other._bits and self._data == other._data
        except:
            return False

    def __ne__(self, other):
        try:
            return self._bits != other._bits or self._data != other._data
        except:
            return True

    def _readslice(self, key):
        """Check that a slice is valid, return indices

        The slice must have indices that are integers.  The indices
        must be in the range 0..(len(self)-1).
        """
        if not isinstance(key.start, int) or not isinstance(key.stop, int):
            raise TypeError("slice indices must be integers")
        if key.step not in (None, 1):
            raise TypeError("slice with step not supported")
        hi = max(key.start, key.stop)
        lo = min(key.start, key.stop)
        if hi < 0 or lo < 0:
            raise IndexError("slice indices must be >= 0")
        if hi >= self._bits or lo >= self._bits:
            raise IndexError("slice index out of range")
        return hi, lo

    def __getitem__(self, key):
        """Read a bit or group of bits from the frame

        If the key is an integer, return that bit as True or False or
        raise IndexError if the key is out of bounds.

        If the key is a slice, return that slice as an integer or
        raise IndexError if out of bounds.  We abuse the slice
        mechanism slightly such that slice(5,7) and slice(7,5) are
        treated the same.  Slices with a step or a negative index are
        not supported.
        """
        if isinstance(key, slice):
            hi, lo = self._readslice(key)
            d = self._data >> lo
            return d & ((1 << (hi + 1 - lo)) - 1)
        elif isinstance(key, int):
            if key < 0 or key >= self._bits:
                raise IndexError("index out of range")
            return (self._data & (1 << key)) != 0
        raise TypeError

    def __setitem__(self, key, value):
        """Write a bit or a group of bits to the frame

        If the key is an integer, set that bit to the truth value of
        value or raise IndexError if the key is out of bounds.

        If the key is a slice, value must be an integer that fits
        within the slice; set that slice to value or raise IndexError
        if out of bounds.  We abuse the slice mechanism slightly such
        that slice(5,7) and slice(7,5) are treated the same.  Slices
        with a step or a negative index are not supported.
        """
        if isinstance(key, slice):
            hi, lo = self._readslice(key)
            if not isinstance(value, int):
                raise TypeError("value must be an integer")
            if value.bit_length() > (hi + 1 - lo):
                raise ValueError("value will not fit in supplied slice")
            if value < 0:
                raise ValueError("value must not be negative")
            template = ((1 << hi + 1 - lo) - 1) << lo
            mask = ((1 << self._bits) - 1) ^ template
            self._data = self._data & mask | (value << lo)
        elif isinstance(key, int):
            if key < 0 or key >= self._bits:
                raise IndexError("index out of range")
            if value:
                self._data = self._data | (1 << key)
            else:
                self._data = self._data \
                    & (((1 << self._bits) - 1) ^ (1 << key))
        else:
            raise TypeError

    def __contains__(self, item):
        if item is True:
            return self._data != 0
        if item is False:
            return self._data != (1 << self._bits) - 1
        return False

    def __add__(self, other):
        try:
            return Frame(self._bits + other._bits,
                         self._data << other._bits | other._data)
        except:
            raise TypeError("Frame can only be added to another Frame")

    @property
    def as_integer(self):
        """The contents of the frame represented as an integer."""
        return self._data

    @property
    def as_byte_sequence(self):
        """The contents of the frame represented as a sequence.

        Returns a sequence of integers each in the range 0..255
        representing the data in the frame, with the most-significant
        bits first.  If the frame is not an exact multiple of 8 bits
        long, the first element in the sequence contains fewer than 8
        bits.
        """
        remaining = len(self)
        l = []
        d = self._data
        while remaining > 0:
            l.append(d & 0xff)
            d = d >> 8
            remaining = remaining - 8
        l.reverse()
        return l

    @property
    def pack(self):
        """The contents of the frame represented as a byte string.

        If the frame is not an exact multiple of 8 bits long, the
        first byte in the string will contain fewer than 8 bits.
        """
        s = self.as_byte_sequence
        return struct.pack("B" * len(s), *s)

    def pack_len(self, l):
        """The contents of the frame represented as a fixed length byte string.

        The least significant bit of the frame is aligned to the end
        of the byte string.  The start of the byte string is padded with zeroes.

        If the frame will not fit in the byte string, raises ValueError.
        """
        s = self.as_byte_sequence
        if len(s) > l:
            raise ValueError("Frame length {} will not fit in {} bytes".format(
                len(self), l))
        s = [0] * (l - len(s)) + s
        return struct.pack("B" * l, *s)

    def __str__(self):
        return "{}({},{})".format(self.__class__.__name__, len(self),
                                  self.as_byte_sequence)


class ForwardFrame(Frame):
    """A frame that can be transmitted as a command or message.

    Forward Frames with 16 data bits are used to communicate with
    control gear conformant to IEC 62386-102.  Forward Frames with 24
    data bits are used by and to communicate with control gear
    conformant to IEC 62386-103.  Forward Frames with 20 or 32 data
    bits are reserved and shall not be used.  Forward Frames with any
    other number of data bits are proprietary.
    """

    @property
    def is_reserved(self):
        return len(self) == 20 or len(self) == 32

    @property
    def is_proprietary(self):
        return len(self) not in (16, 20, 24, 32)


class BackwardFrame(Frame):
    """A response to a forward frame.

    Backward Frames always have 8 data bits and are used only as
    answers to Forward Frames.

    In some circumstances it is normal for a backward frame to be
    received with frame size or bit timing violations, when more than
    one unit responds to a forward frame.  In this case, create a
    BackwardFrameError instead.
    """

    def __init__(self, data):
        super().__init__(8, data)

    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self._data)

class BackwardFrameError(BackwardFrame):
    """A response to a forward frame received with a framing error.

    This occurs when multiple devices respond to a forward frame at
    once.  This is normal when a Query command with a yes/no response
    is addressed to a group or broadcast address.  It shall be
    interpreted as "more than one device responded Yes".
    """

    def __init__(self, data):
        super().__init__(data)
        self._error = True
