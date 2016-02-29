"""
Utility providing the equivalent of a frozenset of unsigned integers,
backed by the concatenation of the sorted integers into a `bytes`
that can be binary-searched.
"""

from __future__ import unicode_literals

import bisect
import struct

# the maximum unicode codepoint is 0x10FFFF == 1114111
MAX_UNSIGNED_INT = 2**32 - 1

# 32-bit unsigned integers in network order
FORMAT = b'!I'

def pack_int_list(ints):
    buf = []
    for int_ in ints:
        if not (0 <= int_ <= MAX_UNSIGNED_INT):
            raise ValueError(int_)
        buf.append((struct.pack(FORMAT, int_)))
    # sort in the Python 8-bit bytestring order (not the integer order)
    # to facilitate binary search --- any ordering would do.
    buf.sort()
    return b''.join(buf)


class _PackedIntList(object):

    def __init__(self, packed_data):
        self.packed_data = packed_data
        length = len(packed_data)
        if length % 4 != 0:
            raise ValueError
        self.length = length // 4

    def __getitem__(self, index):
        internal_index = index * 4
        return self.packed_data[internal_index:internal_index+4]

    def __len__(self):
        return self.length


class PackedIntSet(object):

    def __init__(self, packed_data):
        self._list = _PackedIntList(packed_data)

    def __len__(self):
        return len(self._list)

    def __contains__(self, int_):
        if not (0 <= int_ <= MAX_UNSIGNED_INT):
            raise ValueError(int_)
        packed_int = struct.pack(FORMAT, int_)
        # cf. https://docs.python.org/2/library/bisect.html#searching-sorted-lists
        index = bisect.bisect_left(self._list, packed_int)
        return index != len(self._list) and self._list[index] == packed_int
