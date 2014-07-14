#!/usr/bin/env python

import unittest
import sys

sys.path.append('..')
import idna.codec
import codecs

class IDNACodecTests(unittest.TestCase):
    
    def testCodec(self):
        pass

    def testIncrementalDecoder(self):

        # Tests derived from Python standard library test/test_codecs.py

        incremental_tests = (
            (u"python.org", "python.org"),
            (u"python.org.", "python.org."),
            (u"pyth\xf6n.org", "xn--pythn-mua.org"),
            (u"pyth\xf6n.org.", "xn--pythn-mua.org."),
        )

        for decoded, encoded in incremental_tests:
            self.assertEqual("".join(codecs.iterdecode(encoded, "idna")),
                 decoded)


        decoder = codecs.getincrementaldecoder("idna")()
        self.assertEqual(decoder.decode("xn--xam", ), u"")
        self.assertEqual(decoder.decode("ple-9ta.o", ), u"\xe4xample.")
        self.assertEqual(decoder.decode(u"rg"), u"")
        self.assertEqual(decoder.decode(u"", True), u"org")

        decoder.reset()
        self.assertEqual(decoder.decode("xn--xam", ), u"")
        self.assertEqual(decoder.decode("ple-9ta.o", ), u"\xe4xample.")
        self.assertEqual(decoder.decode("rg."), u"org.")
        self.assertEqual(decoder.decode("", True), u"")


    def testIncrementalEncoder(self):

        # Tests derived from Python standard library test/test_codecs.py

        incremental_tests = (
            (u"python.org", "python.org"),
            (u"python.org.", "python.org."),
            (u"pyth\xf6n.org", "xn--pythn-mua.org"),
            (u"pyth\xf6n.org.", "xn--pythn-mua.org."),
        )
        for decoded, encoded in incremental_tests:
            self.assertEqual("".join(codecs.iterencode(decoded, "idna")),
                             encoded)

        encoder = codecs.getincrementalencoder("idna")()
        self.assertEqual(encoder.encode(u"\xe4x"), "")
        self.assertEqual(encoder.encode(u"ample.org"), "xn--xample-9ta.")
        self.assertEqual(encoder.encode(u"", True), "org")

        encoder.reset()
        self.assertEqual(encoder.encode(u"\xe4x"), "")
        self.assertEqual(encoder.encode(u"ample.org."), "xn--xample-9ta.org.")
        self.assertEqual(encoder.encode(u"", True), "")

if __name__ == '__main__':
    unittest.main()
