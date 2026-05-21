"""Command-line interface for the :mod:`idna` package.

Invoked via ``python -m idna``. See :func:`main` for the entry point.
"""

import argparse
import sys
from typing import List, Optional

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
            "disable it."
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
        help="The domain name to convert.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for ``python -m idna``.

    :param argv: Argument list excluding the program name. Defaults to
        :data:`sys.argv` when ``None``.
    :returns: ``0`` on success, ``1`` if conversion fails.
    """
    args = _build_parser().parse_args(argv)
    mode = args.mode or ("decode" if _looks_like_alabel(args.domain) else "encode")
    uts46 = not args.strict

    try:
        if mode == "decode":
            print(decode(args.domain, uts46=uts46))
        else:
            print(encode(args.domain, uts46=uts46).decode("ascii"))
    except IDNAError as err:
        print(f"idna: {mode} failed: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
