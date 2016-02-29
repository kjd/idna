#!/usr/bin/env python

from __future__ import unicode_literals

import unittest
import sys

sys.path.append('..')

from idna.intset import PackedIntSet
from idna.intset import pack_int_list

class IDNACodecTests(unittest.TestCase):

    def _test_set_functionality(self, ints, disjoint_ints):
        intset = PackedIntSet(pack_int_list(ints))
        for int_ in ints:
            self.assertIn(int_, intset)
        for int_ in disjoint_ints:
            self.assertNotIn(int_, intset)

    def test_intset(self):
        self._test_set_functionality([1, 23, 5867, 9999, 10001], [0, 2, 44, 58, 99999999])

    def test_intset_even_length(self):
        self._test_set_functionality([9999, 23], [0, 2, 44, 58, 99999999])

    def test_singleton(self):
        self._test_set_functionality([23], [0, 2, 44, 58, 99999999])

    def test_empty(self):
        self._test_set_functionality([], [0, 2, 44, 58, 99999999])

    def test_big(self):
        self._test_set_functionality(range(10000), range(10001, 20000))
