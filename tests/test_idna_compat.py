#!/usr/bin/env python

import unittest
import sys

sys.path.append('..')
import idna.compat

class IDNACompatTests(unittest.TestCase):

    def testToASCII(self):
        pass

    def testToUnicode(self):
        pass

    def testnameprep(self):
        self.assertRaises(NotImplementedError, idna.compat.nameprep, "a")

if __name__ == '__main__':
    unittest.main()
