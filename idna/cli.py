"""Command-line interface for the :mod:`idna` package.

Invoked via ``python -m idna``. See :func:`main` for the entry point.
"""

import argparse
import sys
from typing import IO, Iterable, List, Optional

from . import IDNAError, decode, encode
from .core import _alabel_prefix, _unicode_dots_re
from .package_data import __version__


def _looks_like_alabel(s: str) -> bool:
    """Return True if any label in ``s`` carries the ``xn--`` ACE prefix."""
    prefix = _alabel_prefix.decode("ascii")
    return any(label.lower().startswith(prefix) for label in _unicode_dots_re.split(s))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m idna",
        description=(
            "Convert a domain name between its Unicode (U-label) and "
            "ASCII-compatible (A-label) forms. With no mode flag, the "
            "direction is chosen automatically: inputs containing an "
            "xn-- label are decoded, otherwise the input is encoded. "
            "UTS #46 mapping is applied by default; pass --strict to "
            "disable it. When no domains are given on the command line "
            "and stdin is piped, one domain per line is read from stdin."
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-e",
        "--encode",
        dest="mode",
        action="store_const",
        const="encode",
        help="Encode the input to its ASCII A-label form.",
    )
    mode.add_argument(
        "-d",
        "--decode",
        dest="mode",
        action="store_const",
        const="decode",
        help="Decode the input from its ASCII A-label form.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Disable the default UTS #46 mapping and apply IDNA 2008 rules verbatim.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"idna {__version__}",
    )
    parser.add_argument(
        "domain",
        nargs="*",
        help="One or more domain names to convert. Omit to read from stdin.",
    )
    return parser


def _convert(domain: str, mode: Optional[str], uts46: bool) -> str:
    """Apply the requested conversion to ``domain``, picking a mode if needed."""
    chosen = mode or ("decode" if _looks_like_alabel(domain) else "encode")
    if chosen == "decode":
        return decode(domain, uts46=uts46)
    return encode(domain, uts46=uts46).decode("ascii")


def _iter_stdin(stream: IO[str]) -> Iterable[str]:
    """Yield non-empty stripped lines from ``stream``, ignoring blanks."""
    for line in stream:
        stripped = line.strip()
        if stripped:
            yield stripped


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for ``python -m idna``.

    :param argv: Argument list excluding the program name. Defaults to
        :data:`sys.argv` when ``None``.
    :returns: ``0`` on success, ``1`` if any conversion fails.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)
    uts46 = not args.strict

    if args.domain:
        domains: Iterable[str] = args.domain
    elif not sys.stdin.isatty():
        domains = _iter_stdin(sys.stdin)
    else:
        parser.error("a domain argument is required when stdin is a terminal")

    failed = False
    for domain in domains:
        try:
            print(_convert(domain, args.mode, uts46))
        except IDNAError as err:
            mode = args.mode or ("decode" if _looks_like_alabel(domain) else "encode")
            print(f"idna: {mode} failed for {domain!r}: {err}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
