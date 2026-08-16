"""Tests for the machine-readable attributes carried by IDNAError."""

import pickle
import re
import unittest
from unittest import mock

import idna


class ErrorAttributeTests(unittest.TestCase):
    def _cases(self):
        """(trigger, expected class, expected text, codepoint, position)"""
        r = "\u05d0"  # R
        an = "\u0660"  # AN
        nsm = "\u0610"  # NSM
        return [
            (lambda: idna.alabel("abc\u0141"), idna.InvalidCodepoint, "abc\u0141", 0x141, 4),
            (lambda: idna.alabel("a\u200cb"), idna.InvalidCodepointContext, "a\u200cb", 0x200C, 2),
            (lambda: idna.alabel("a\xb7b"), idna.InvalidCodepointContext, "a\xb7b", 0xB7, 2),
            (lambda: idna.alabel("\u0301abc"), idna.IDNAError, "\u0301abc", 0x301, 1),
            (lambda: idna.check_bidi("a\u0378"), idna.IDNABidiError, "a\u0378", 0x378, 2),
            (lambda: idna.check_bidi(an + r), idna.IDNABidiError, an + r, 0x660, 1),  # rule 1
            (lambda: idna.check_bidi(r + "a"), idna.IDNABidiError, r + "a", 0x61, 2),  # rule 2
            (lambda: idna.check_bidi(r + "-" + nsm), idna.IDNABidiError, r + "-" + nsm, 0x2D, 2),  # rule 3
            (lambda: idna.check_bidi(r + an + "0"), idna.IDNABidiError, r + an + "0", 0x30, 3),  # rule 4
            (lambda: idna.alabel("a" + r), idna.IDNABidiError, "a" + r, 0x5D0, 2),  # rule 5
            (lambda: idna.check_bidi("a-", check_ltr=True), idna.IDNABidiError, "a-", 0x2D, 2),  # rule 6
            (lambda: idna.uts46_remap("a\x80"), idna.InvalidCodepoint, "a\x80", 0x80, 2),
            (lambda: idna.uts46_remap("a_b"), idna.InvalidCodepoint, "a_b", 0x5F, 2),
            (lambda: idna.uts46_remap("a\uff3fb"), idna.InvalidCodepoint, "a\uff3fb", 0xFF3F, 2),
            (lambda: idna.encode("a_b", uts46=True, std3_rules=True), idna.InvalidCodepoint, "a_b", 0x5F, 2),
        ]

    def test_attributes_are_populated(self):
        for trigger, exc_class, text, codepoint, position in self._cases():
            with self.subTest(text=text):
                with self.assertRaises(exc_class) as ctx:
                    trigger()
                err = ctx.exception
                self.assertEqual(err.text, text)
                self.assertEqual(err.codepoint, codepoint)
                self.assertEqual(err.position, position)
                # position indexes text and names the codepoint ...
                self.assertEqual(ord(err.text[err.position - 1]), err.codepoint)
                # ... and agrees with the message where the message quotes one
                match = re.search(r"position (\d+)", str(err))
                if match:
                    self.assertEqual(int(match.group(1)), err.position)

    def test_unknown_codepoint_adjacent_to_joiner(self):
        unknown = mock.patch("idna.core._combining_class", side_effect=ValueError)
        with unknown, self.assertRaises(idna.IDNAError) as ctx:
            idna.check_label("a\u200cb")
        err = ctx.exception
        self.assertNotIsInstance(err, idna.InvalidCodepointContext)
        self.assertEqual((err.text, err.codepoint, err.position), ("a\u200cb", 0x200C, 2))

    def test_attributes_default_to_none(self):
        for trigger in (
            lambda: idna.encode("a..b"),
            lambda: idna.encode(""),
            lambda: idna.alabel("a" * 64),
            lambda: idna.alabel("ab--cd"),
            lambda: idna.alabel("-abc"),
            lambda: idna.ulabel("xn--"),
            lambda: idna.encode(b"\xff"),
        ):
            with self.assertRaises(idna.IDNAError) as ctx:
                trigger()
            err = ctx.exception
            self.assertIsNone(err.text)
            self.assertIsNone(err.codepoint)
            self.assertIsNone(err.position)

    def test_construction_is_backwards_compatible(self):
        err = idna.IDNAError("just a message")
        self.assertEqual(str(err), "just a message")
        self.assertEqual(err.args, ("just a message",))
        self.assertIsNone(err.text)
        self.assertEqual(idna.IDNAError().args, ())
        self.assertEqual(idna.InvalidCodepoint("a", "b").args, ("a", "b"))

    def test_message_remains_sole_positional_argument(self):
        with self.assertRaises(idna.InvalidCodepoint) as ctx:
            idna.alabel("abc\u0141")
        self.assertEqual(ctx.exception.args, ("Codepoint U+0141 at position 4 of 'abc\u0141' not allowed",))

    def test_attributes_survive_pickle(self):
        with self.assertRaises(idna.InvalidCodepoint) as ctx:
            idna.alabel("abc\u0141")
        err = pickle.loads(pickle.dumps(ctx.exception))
        self.assertIsInstance(err, idna.InvalidCodepoint)
        self.assertEqual(str(err), str(ctx.exception))
        self.assertEqual((err.text, err.codepoint, err.position), ("abc\u0141", 0x141, 4))


if __name__ == "__main__":
    unittest.main()
