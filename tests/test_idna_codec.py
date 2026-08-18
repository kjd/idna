import codecs
import io
import unittest

import idna.codec

CODEC_NAME = "idna2008"

# (decoded, encoded) pairs derived from CPython's Lib/test/test_codecs.py
INCREMENTAL_TESTS = (
    ("python.org", b"python.org"),
    ("python.org.", b"python.org."),
    ("pyth\xf6n.org", b"xn--pythn-mua.org"),
    ("pyth\xf6n.org.", b"xn--pythn-mua.org."),
)


class IDNACodecTests(unittest.TestCase):
    def setUp(self):
        from . import test_idna

        self.idnatests = test_idna.IDNATests()
        self.idnatests.setUp()

    def testCodec(self):
        self.assertIs(codecs.lookup(CODEC_NAME).incrementalencoder, idna.codec.IncrementalEncoder)

    def testDirectDecode(self):
        self.idnatests.test_decode(decode=lambda obj: codecs.decode(obj, CODEC_NAME))

    def testIndirectDecode(self):
        self.idnatests.test_decode(decode=lambda obj: obj.decode(CODEC_NAME), skip_str=True)

    def testDirectEncode(self):
        self.idnatests.test_encode(encode=lambda obj: codecs.encode(obj, CODEC_NAME))

    def testIndirectEncode(self):
        self.idnatests.test_encode(encode=lambda obj: obj.encode(CODEC_NAME), skip_bytes=True)

    def testIncrementalDecoderNonASCII(self):
        # Non-ASCII bytes must surface as IDNAError, as they do from
        # idna.decode() and the one-shot codec, not as UnicodeDecodeError.
        decoder = codecs.getincrementaldecoder(CODEC_NAME)()
        self.assertRaises(idna.IDNAError, decoder.decode, b"\x80")
        self.assertRaises(idna.IDNAError, decoder.decode, b"\xc3\x9f", True)
        self.assertRaises(idna.IDNAError, b"\x80".decode, CODEC_NAME)

    def testStreamReader(self):
        def decode(obj):
            if isinstance(obj, str):
                obj = bytes(obj, "ascii")
            buffer = io.BytesIO(obj)
            stream = codecs.getreader(CODEC_NAME)(buffer)
            return stream.read()

        return self.idnatests.test_decode(decode=decode, skip_str=True)

    def testStreamWriter(self):
        def encode(obj):
            buffer = io.BytesIO()
            stream = codecs.getwriter(CODEC_NAME)(buffer)
            stream.write(obj)
            stream.flush()
            return buffer.getvalue()

        return self.idnatests.test_encode(encode=encode)

    def testIncrementalDecoder(self):
        for decoded, encoded in INCREMENTAL_TESTS:
            self.assertEqual(
                "".join(codecs.iterdecode((bytes([c]) for c in encoded), CODEC_NAME)),
                decoded,
            )

        decoder = codecs.getincrementaldecoder(CODEC_NAME)()
        self.assertEqual(
            decoder.decode(
                b"xn--xam",
            ),
            "",
        )
        self.assertEqual(
            decoder.decode(
                b"ple-9ta.o",
            ),
            "\xe4xample.",
        )
        self.assertEqual(decoder.decode(b"rg"), "")
        self.assertEqual(decoder.decode(b"", True), "org")

        decoder.reset()
        self.assertEqual(
            decoder.decode(
                b"xn--xam",
            ),
            "",
        )
        self.assertEqual(
            decoder.decode(
                b"ple-9ta.o",
            ),
            "\xe4xample.",
        )
        self.assertEqual(decoder.decode(b"rg."), "org.")
        self.assertEqual(decoder.decode(b"", True), "")

    def testIncrementalEncoder(self):
        for decoded, encoded in INCREMENTAL_TESTS:
            self.assertEqual(b"".join(codecs.iterencode(decoded, CODEC_NAME)), encoded)

        encoder = codecs.getincrementalencoder(CODEC_NAME)()
        self.assertEqual(encoder.encode("\xe4x"), b"")
        self.assertEqual(encoder.encode("ample.org"), b"xn--xample-9ta.")
        self.assertEqual(encoder.encode("", True), b"org")

        encoder.reset()
        self.assertEqual(encoder.encode("\xe4x"), b"")
        self.assertEqual(encoder.encode("ample.org."), b"xn--xample-9ta.org.")
        self.assertEqual(encoder.encode("", True), b"")

    def testIncrementalEncoderDomainLength(self):
        # The whole-domain limit applies to the accumulated output just as
        # idna.encode() applies it: 253 octets, or 254 with a trailing dot.
        for domain in ("a." * 126 + "a", "a." * 127, "\xe4." * 30 + "\xe4"):
            self.assertEqual(b"".join(codecs.iterencode(domain, CODEC_NAME)), idna.encode(domain))
        for domain in ("a." * 126 + "aa", "a." * 127 + "a", "\xe4." * 32):
            with self.assertRaises(idna.IDNAError):
                idna.encode(domain)
            with self.assertRaises(idna.IDNAError):
                b"".join(codecs.iterencode(domain, CODEC_NAME))

        # 254 octets is only acceptable if the trailing dot has arrived by
        # the time the input is final.
        encoder = codecs.getincrementalencoder(CODEC_NAME)()
        self.assertEqual(encoder.encode("a." * 126 + "aa"), b"a." * 126)
        with self.assertRaises(idna.IDNAError):
            encoder.encode("", True)
        encoder.reset()
        self.assertEqual(encoder.encode("a." * 126 + "a"), b"a." * 126)
        self.assertEqual(encoder.encode(".", True), b"a.")

    def testIncrementalDecoderDomainLength(self):
        for domain in (b"a." * 126 + b"a", b"a." * 127):
            self.assertEqual("".join(codecs.iterdecode((bytes([c]) for c in domain), CODEC_NAME)), idna.decode(domain))
        for domain in (b"a." * 127 + b"a", b"a." * 200):
            with self.assertRaises(idna.IDNAError):
                idna.decode(domain)
            with self.assertRaises(idna.IDNAError):
                "".join(codecs.iterdecode((bytes([c]) for c in domain), CODEC_NAME))
        decoder = codecs.getincrementaldecoder(CODEC_NAME)()
        with self.assertRaises(idna.IDNAError):
            decoder.decode(b"a." * 200)
        decoder.reset()
        self.assertEqual(decoder.decode(b"a." * 127, True), "a." * 127)

    def testIncrementalStateRoundTrip(self):
        # getstate()/setstate() carry the length accounting along with the
        # buffered partial label.
        encoder = codecs.getincrementalencoder(CODEC_NAME)()
        self.assertEqual(encoder.getstate(), 0)
        encoder.encode("a." * 126 + "a")
        state = encoder.getstate()
        encoder.reset()
        self.assertEqual(encoder.encode("", True), b"")
        encoder.setstate(state)
        with self.assertRaises(idna.IDNAError):
            encoder.encode("a", True)
        encoder.setstate(0)
        self.assertEqual(encoder.encode("a", True), b"a")

        decoder = codecs.getincrementaldecoder(CODEC_NAME)()
        self.assertEqual(decoder.getstate(), (b"", 0))
        decoder.decode(b"a." * 126 + b"a")
        state = decoder.getstate()
        decoder.reset()
        self.assertEqual(decoder.decode(b"", True), "")
        decoder.setstate(state)
        with self.assertRaises(idna.IDNAError):
            decoder.decode(b"aa", True)


if __name__ == "__main__":
    unittest.main()
