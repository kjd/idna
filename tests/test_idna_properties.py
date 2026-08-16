"""Property-based tests using Hypothesis.

The UTS #46 conformance suite covers known-answer cases; these tests explore
the input space for the failure class behind CVE-2024-3651 and
CVE-2026-45409 ("pathological input causes unexpected behaviour"). Each
property asserts an invariant that must hold for *any* input: the only
exception the public API raises is :class:`idna.IDNAError`, successful
output is well-formed, and the several routes to the same operation agree.

Set ``HYPOTHESIS_PROFILE=thorough`` to run 10,000 examples per property.
"""

from __future__ import annotations

import codecs
import os
import unicodedata
import unittest
import warnings
from typing import Any, Callable

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import idna
import idna.codec  # registers the "idna2008" codec
from idna.intranges import intranges_contain, intranges_from_list

settings.register_profile("idna", deadline=None, print_blob=True)
settings.register_profile(
    "thorough",
    max_examples=10_000,
    deadline=None,
    print_blob=True,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "idna"))


# --- Strategies ------------------------------------------------------------

# Characters that exercise the interesting rules in RFC 5891-5893 and
# UTS #46: label separators, joiners, combining marks, contextual-rule
# codepoints, hyphens/digits, "xn--" prefixes, and full-width/case variants.
_interesting = st.sampled_from(
    "abcxyzABCXYZ0189-_ "
    "xn--"
    ".。．｡"  # label separators
    "‌‍"  # ZWNJ, ZWJ (CONTEXTJ)
    "्̀̈ํ"  # combining marks / virama
    "·͵・"  # CONTEXTO: middle dot, keraia, katakana middle dot
    "αςбяकम中文カタひ"  # sample letters
    "ßẞσÅÅﬁ①Ａ"  # UTS #46 mapped/deviation chars
    "\U0001d400\U0001f600"  # supplementary plane
)
_bidi_range = st.characters(min_codepoint=0x0590, max_codepoint=0x08FF)  # RTL scripts, for bidi rules
_any_char = st.characters(exclude_categories=())  # includes surrogates and unassigned codepoints

_label = st.text(alphabet=st.one_of(_interesting, _bidi_range, _any_char, st.characters()), max_size=70)
_structured_domain = st.lists(_label, max_size=6).map(".".join)
_free_text = st.text(alphabet=st.one_of(_any_char, st.characters()), max_size=300)
_over_long = st.text(min_size=1000, max_size=1100)

domains = st.one_of(_structured_domain, _free_text, _over_long)
labels = st.text(alphabet=st.one_of(_interesting, _bidi_range, st.characters()), max_size=100)
ascii_domains = st.text(alphabet=st.characters(max_codepoint=0x7F), max_size=300)
binary = st.binary(max_size=300)
flags = st.booleans()
_STD3_ASCII = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-.")


def _run(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, idna.IDNAError | None]:
    """Return ``(result, None)`` or ``(None, error)``, letting anything else propagate."""
    with warnings.catch_warnings():
        # transitional=True is deprecated but still exercised deliberately.
        warnings.simplefilter("ignore", DeprecationWarning)
        try:
            return fn(*args, **kwargs), None
        except idna.IDNAError as err:
            return None, err


class OnlyIDNAErrorTests(unittest.TestCase):
    """The public API never raises anything except ``IDNAError`` for any input."""

    @given(domains, flags, flags, flags, flags)
    def test_encode(self, s: str, strict: bool, uts46: bool, std3_rules: bool, transitional: bool) -> None:
        _run(idna.encode, s, strict=strict, uts46=uts46, std3_rules=std3_rules, transitional=transitional)

    @given(st.one_of(domains, binary), flags, flags, flags, flags)
    def test_decode(self, s: str | bytes, strict: bool, uts46: bool, std3_rules: bool, display: bool) -> None:
        _run(idna.decode, s, strict=strict, uts46=uts46, std3_rules=std3_rules, display=display)

    @given(domains, flags, flags)
    def test_uts46_remap(self, s: str, std3_rules: bool, transitional: bool) -> None:
        _run(idna.uts46_remap, s, std3_rules=std3_rules, transitional=transitional)

    @given(labels)
    def test_label_helpers(self, label: str) -> None:
        for fn in (
            idna.alabel,
            idna.ulabel,
            idna.check_label,
            idna.check_bidi,
            idna.check_hyphen_ok,
            idna.check_initial_combiner,
            idna.check_nfc,
            idna.valid_label_length,
        ):
            _run(fn, label)
        _run(idna.ulabel, label.encode("utf-8", "surrogatepass"))

    @given(st.one_of(domains, binary), flags)
    def test_codec(self, s: str | bytes, final: bool) -> None:
        if isinstance(s, str):
            _run(s.encode, "idna2008")
            _run(codecs.getincrementalencoder("idna2008")().encode, s, final)
        else:
            _run(s.decode, "idna2008")
            _run(codecs.getincrementaldecoder("idna2008")().decode, s, final)


class OutputShapeTests(unittest.TestCase):
    @given(domains, flags, flags, flags)
    def test_encode_output_is_bounded_ascii(self, s: str, strict: bool, uts46: bool, std3_rules: bool) -> None:
        result, err = _run(idna.encode, s, strict=strict, uts46=uts46, std3_rules=std3_rules)
        if err is not None:
            return
        self.assertIsInstance(result, bytes)
        result.decode("ascii")
        self.assertLessEqual(len(result), 254)
        for label in result.rstrip(b".").split(b"."):
            self.assertTrue(0 < len(label) <= 63)

    @given(domains, flags, flags)
    def test_uts46_remap_output_is_nfc_and_idempotent(self, s: str, std3_rules: bool, transitional: bool) -> None:
        out, err = _run(idna.uts46_remap, s, std3_rules=std3_rules, transitional=transitional)
        if err is not None:
            return
        self.assertTrue(unicodedata.is_normalized("NFC", out))
        # Non-transitional mapping is idempotent. Transitional mapping is
        # not: deviation handling applies to the input, not to mapping
        # output, so e.g. U+1E9E maps to U+00DF which a second transitional
        # pass would turn into "ss". A non-transitional pass over
        # transitional output must still be a fixed point.
        self.assertEqual(idna.uts46_remap(out, std3_rules=std3_rules, transitional=False), out)
        if std3_rules:
            # UTS #46 §4.1 UseSTD3ASCIIRules: only LDH ASCII (plus the label
            # separator) may survive mapping.
            self.assertTrue(all(c in _STD3_ASCII for c in out if c.isascii()), out)
        else:
            # Turning the rules on must never change a result, only reject it.
            strict, err = _run(idna.uts46_remap, s, std3_rules=True, transitional=transitional)
            self.assertTrue(err is not None or strict == out)


class RoundTripTests(unittest.TestCase):
    @given(domains, flags, flags)
    def test_encode_decode_encode(self, s: str, uts46: bool, std3_rules: bool) -> None:
        encoded, err = _run(idna.encode, s, uts46=uts46, std3_rules=std3_rules)
        if err is not None:
            return
        decoded = idna.decode(encoded)  # anything encode() produced must decode
        # ulabel() lowercases ASCII labels while alabel() preserves case, so the
        # round trip is exact only up to ASCII case.
        self.assertEqual(idna.encode(decoded), encoded.lower())
        # display=True only changes behaviour for labels that fail to decode
        self.assertEqual(idna.decode(encoded, display=True), decoded)

    @given(labels)
    def test_alabel_ulabel(self, label: str) -> None:
        encoded, err = _run(idna.alabel, label)
        if err is not None:
            return
        self.assertEqual(idna.alabel(idna.ulabel(encoded)), encoded.lower())


class DifferentialTests(unittest.TestCase):
    """Different routes to the same operation must agree."""

    @staticmethod
    def _assert_same_outcome(test: unittest.TestCase, a: tuple[Any, Any], b: tuple[Any, Any]) -> None:
        (a_result, a_err), (b_result, b_err) = a, b
        test.assertEqual(a_err is None, b_err is None, f"{a_err!r} vs {b_err!r}")
        test.assertEqual(a_result, b_result)

    @given(ascii_domains)
    def test_strict_is_irrelevant_for_ascii(self, s: str) -> None:
        self._assert_same_outcome(self, _run(idna.encode, s, strict=True), _run(idna.encode, s, strict=False))
        self._assert_same_outcome(self, _run(idna.decode, s, strict=True), _run(idna.decode, s, strict=False))

    @given(domains)
    def test_codec_encode_matches_core(self, s: str) -> None:
        if not s:
            return  # the codec short-circuits empty input where core raises "Empty domain"
        self._assert_same_outcome(self, _run(s.encode, "idna2008"), _run(idna.encode, s))

    @given(binary)
    def test_codec_decode_matches_core(self, b: bytes) -> None:
        if not b:
            return
        self._assert_same_outcome(self, _run(b.decode, "idna2008"), _run(idna.decode, b))

    @given(domains, st.lists(st.integers(min_value=0, max_value=300), max_size=8))
    def test_incremental_encoder_matches_one_shot(self, s: str, cuts: list[int]) -> None:
        if not s:
            return  # see test_codec_encode_matches_core
        one_shot, err = _run(idna.encode, s)
        encoder = codecs.getincrementalencoder("idna2008")()
        chunks = _split(s, cuts)

        def incremental() -> bytes:
            out = b"".join(encoder.encode(chunk) for chunk in chunks)
            return out + encoder.encode("", final=True)

        self._assert_same_outcome(self, (one_shot, err), _run(incremental))

    @given(binary, st.lists(st.integers(min_value=0, max_value=300), max_size=8))
    def test_incremental_decoder_matches_one_shot(self, b: bytes, cuts: list[int]) -> None:
        if not b:
            return  # see test_codec_decode_matches_core
        one_shot, err = _run(idna.decode, b)
        decoder = codecs.getincrementaldecoder("idna2008")()
        chunks = _split(b, cuts)

        def incremental() -> str:
            out = "".join(decoder.decode(chunk) for chunk in chunks)
            return out + decoder.decode(b"", final=True)

        self._assert_same_outcome(self, (one_shot, err), _run(incremental))


def _split(data: Any, cuts: list[int]) -> list[Any]:
    """Split ``data`` at the given (unordered, possibly repeated) offsets."""
    points = [0, *sorted(min(c, len(data)) for c in cuts), len(data)]
    return [data[i:j] for i, j in zip(points, points[1:])]


class IntrangesTests(unittest.TestCase):
    @given(st.sets(st.integers(min_value=0, max_value=0x10FFFF)), st.integers(min_value=0, max_value=0x10FFFF))
    def test_membership_matches_set(self, members: set[int], probe: int) -> None:
        ranges = intranges_from_list(sorted(members))
        self.assertEqual(intranges_contain(probe, ranges), probe in members)
        for member in members:
            self.assertTrue(intranges_contain(member, ranges))
