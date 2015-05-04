"""Tests for UTS46 code."""

import gzip
import os.path
import re
import sys
import unittest

import idna

narrow_unicode = False
if sys.version_info[0] == 2:
    try:
        a = unichr(0x10000)
    except ValueError:
        narrow_unicode = True
else:
    unichr = chr

_RE_UNICODE = re.compile(r"\\u([0-9a-fA-F]{4})")
_RE_SURROGATE = re.compile(r"[\uD800-\uDBFF][\uDC00-\uDFFF]")


def unicode_fixup(string):
    """Replace backslash-u-XXXX with appropriate unicode characters."""
    return _RE_SURROGATE.sub(lambda match: unichr(
        (ord(match.group(0)[0]) - 0xd800) * 0x400 +
        ord(match.group(0)[1]) - 0xdc00 + 0x10000),
        _RE_UNICODE.sub(lambda match: unichr(int(match.group(1), 16)), string))


def parse_idna_test_table(inputstream):
    """Parse IdnaTest.txt and return a list of tuples."""
    tests = []
    for lineno, line in enumerate(inputstream):
        line = line.decode("utf8").strip()
        if "#" in line:
            line = line.split("#", 1)[0]
        if not line:
            continue
        #if line.find("\\u200C") > 0 or line.find("\\u200D") > 0:
        #    continue
        fields = (lineno + 1,) + tuple(unicode_fixup(field.strip())
            for field in line.split(";"))
        tests.append(fields)
    return tests


class TestUTS46(unittest.TestCase):
    """Tests for UTS46 code."""
    def setUp(self):
        self.tests = parse_idna_test_table(gzip.open(
            os.path.join(os.path.dirname(__file__), "IdnaTest.txt.gz"), "rb"))

    @unittest.skipIf(narrow_unicode, "Can't test unless using 4-byte Unicode")
    @unittest.skipUnless(getattr(unittest.TestCase, 'subTest', False), "Can't test without unittest.subTest support")
    def test_process(self):
        """Test idna.decode() and idna.decode() against IdnaTest.txt."""
        for test in self.tests:
            lineno, types, value, to_unicode, to_ascii = test[:5]
            nv8 = test[5] if len(test) > 5 else None
            if not to_unicode:
                to_unicode = value
            if not to_ascii:
                to_ascii = to_unicode
            with self.subTest("decode", lineno=lineno, value=value,
                    expected=to_unicode):
                try:
                    output = idna.decode(value, strict=True)
                    if to_unicode[0] == "[":
                        self.fail("Expected error from decode")
                    self.assertEqual(output, to_unicode)
                except (UnicodeError, ValueError) as exc:
                    if to_unicode[0] != "[" and not nv8:
                        self.fail("decode failed with {!r}".format(exc))
            for transitional in {
                    "B": (True, False),
                    "T": (True,),
                    "N": (False,),
                    }[types]:
                with self.subTest("encode", lineno=lineno,
                        transitional=transitional, value=value,
                        expected=to_ascii):
                    try:
                        output = idna.encode(value, strict=True,
                            transitional=transitional).decode("ascii")
                        if to_ascii[0] == "[":
                            self.fail("Expected error from encode")
                        self.assertEqual(output, to_ascii)
                    except (UnicodeError, ValueError) as exc:
                        if to_ascii[0] != "[" and not nv8:
                            self.fail("encode failed with {!r}".format(exc))
