"""Tests for the machine-readable attributes carried by IDNAError."""

import codecs
import pickle
import re
import unittest
from pathlib import Path
from typing import get_args
from unittest import mock

import idna
import idna.codec
import idna.core


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

    def test_every_error_code_is_documented_and_raisable(self):
        """Each code has an input that produces it, and vice versa; the README
        table must list exactly this set."""
        r = "\u05d0"
        an = "\u0660"
        triggers = {
            "input_too_long": lambda: idna.encode("a" * 1025),
            "label_too_long": lambda: idna.alabel("a" * 64),
            "domain_too_long": lambda: idna.encode(".".join(["a" * 63] * 4)),
            "empty_label": lambda: idna.encode("a..b"),
            "empty_domain": lambda: idna.encode(""),
            "not_nfc": lambda: idna.alabel("e\u0301xample"),
            "hyphen_3_4": lambda: idna.alabel("ab--cd"),
            "hyphen_start_end": lambda: idna.alabel("-abc"),
            "leading_combiner": lambda: idna.alabel("\u0301abc"),
            "disallowed_codepoint": lambda: idna.alabel("abc\u0141"),
            "contextj": lambda: idna.alabel("a\u200cb"),
            "contexto": lambda: idna.alabel("a\xb7b"),
            "unknown_codepoint": self._unknown_codepoint,
            "bidi_rule_1": lambda: idna.check_bidi(an + r),
            "bidi_rule_2": lambda: idna.check_bidi(r + "a"),
            "bidi_rule_3": lambda: idna.check_bidi(r + "-"),
            "bidi_rule_4": lambda: idna.check_bidi(r + an + "0"),
            "bidi_rule_5": lambda: idna.alabel("a" + r),
            "bidi_rule_6": lambda: idna.check_bidi("a-", check_ltr=True),
            "bidi_unknown_direction": lambda: idna.check_bidi("a\u0378"),
            "invalid_alabel": lambda: idna.ulabel("xn--"),
            "invalid_ascii": lambda: idna.encode(b"\xff"),
            "invalid_utf8": lambda: idna.check_label(b"\xff"),
            "uts46_disallowed": lambda: idna.uts46_remap("a\x80"),
            "uts46_std3": lambda: idna.uts46_remap("a_b"),
            "unsupported_errors": lambda: codecs.encode("a", "idna2008", errors="ignore"),
        }
        codes = set(get_args(idna.core._ErrorCode))
        self.assertEqual(set(triggers), codes)
        for code, trigger in triggers.items():
            with self.subTest(code=code):
                with self.assertRaises(idna.IDNAError) as ctx:
                    trigger()
                self.assertEqual(ctx.exception.code, code)
        readme = Path(__file__).resolve().parent.parent / "README.md"
        if not readme.is_file():
            self.skipTest("README.md not present")
        documented = set()
        for first, last in re.findall(r"^\| `([a-z0-9_]+)`(?: \u2026 `([a-z0-9_]+)`)? \|", readme.read_text(), re.MULTILINE):
            if last:  # a `x_1` … `x_6` range row
                stem, lo = first.rsplit("_", 1)
                documented.update(f"{stem}_{i}" for i in range(int(lo), int(last.rsplit("_", 1)[1]) + 1))
            else:
                documented.add(first)
        documented.discard("code")  # the table header
        self.assertEqual(documented, codes)

    def _unknown_codepoint(self):
        with mock.patch("idna.core._combining_class", side_effect=ValueError):
            idna.check_label("a\u200cb")

    def test_unknown_codepoint_adjacent_to_joiner(self):
        unknown = mock.patch("idna.core._combining_class", side_effect=ValueError)
        with unknown, self.assertRaises(idna.IDNAError) as ctx:
            idna.check_label("a\u200cb")
        err = ctx.exception
        self.assertNotIsInstance(err, idna.InvalidCodepointContext)
        self.assertEqual(err.code, "unknown_codepoint")
        self.assertEqual((err.text, err.codepoint, err.position), ("a\u200cb", 0x200C, 2))

    def test_positional_attributes_default_to_none(self):
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
            self.assertIsNotNone(err.code)
            self.assertIsNone(err.text)
            self.assertIsNone(err.codepoint)
            self.assertIsNone(err.position)

    def test_construction_is_backwards_compatible(self):
        err = idna.IDNAError("just a message")
        self.assertEqual(str(err), "just a message")
        self.assertEqual(err.args, ("just a message",))
        self.assertIsNone(err.code)
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
        self.assertEqual(err.code, "disallowed_codepoint")
        self.assertEqual((err.text, err.codepoint, err.position), ("abc\u0141", 0x141, 4))


if __name__ == "__main__":
    unittest.main()
