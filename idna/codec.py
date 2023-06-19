from .core import encode, decode, alabel, ulabel, IDNAError
import codecs
import re
from typing import Tuple, Optional

_unicode_dots_re = re.compile('[\u002e\u3002\uff0e\uff61]')

class Codec(codecs.Codec):

    def encode(self, data: str, errors: str = 'strict') -> Tuple[bytes, int]:
        if errors != 'strict':
            raise IDNAError('Unsupported error handling \"{}\"'.format(errors))

        if not data:
            return b"", 0

        return encode(data), len(data)

    def decode(self, data: bytes, errors: str = 'strict') -> Tuple[str, int]:
        if errors != 'strict':
            raise IDNAError('Unsupported error handling \"{}\"'.format(errors))

        if not data:
            return '', 0

        return decode(data), len(data)

class IncrementalEncoder(codecs.BufferedIncrementalEncoder):
    def _buffer_encode(self, data: str, errors: str, final: bool) -> Tuple[bytes, int]:
        if errors != 'strict':
            raise IDNAError('Unsupported error handling \"{}\"'.format(errors))

        if not data:
            return b'', 0

        labels = _unicode_dots_re.split(data)
        trailing_dot = b''
        if labels:
            if not labels[-1]:
                trailing_dot = b'.'
                del labels[-1]
            elif not final:
                # Keep potentially unfinished label until the next call
                del labels[-1]
                if labels:
                    trailing_dot = b'.'

        result = []
        size = 0
        for label in labels:
            result.append(alabel(label))
            if size:
                size += 1
            size += len(label)

        # Join with U+002E
        result_bytes = b'.'.join(result) + trailing_dot
        size += len(trailing_dot)
        return result_bytes, size

class IncrementalDecoder(codecs.BufferedIncrementalDecoder):
    def _buffer_decode(self, data: bytes, errors: str, final: bool) -> Tuple[str, int]:  # type: ignore
        if errors != 'strict':
            raise IDNAError('Unsupported error handling \"{}\"'.format(errors))

        if not data:
            return ('', 0)

        labels = data.replace(b'\u3002', b'.').replace(b'\uff0e', b'.').replace(b'\uff61', b'.').split(b'.')
        trailing_dot = ''
        if labels:
            if not labels[-1]:
                trailing_dot = '.'
                del labels[-1]
            elif not final:
                # Keep potentially unfinished label until the next call
                del labels[-1]
                if labels:
                    trailing_dot = '.'

        result = []
        size = 0
        for label in labels:
            result.append(ulabel(label))
            if size:
                size += 1
            size += len(label)

        result_str = '.'.join(result) + trailing_dot
        size += len(trailing_dot)
        return (result_str, size)


class StreamWriter(Codec, codecs.StreamWriter):
    pass


class StreamReader(Codec, codecs.StreamReader):
    pass


def getregentry(name: str) -> Optional[codecs.CodecInfo]:
    if name != 'idna' and name != 'idna2008':
        return None

    # Compatibility as a search_function for codecs.register()
    return codecs.CodecInfo(
        name='idna2008',
        encode=Codec().encode,  # type: ignore
        decode=Codec().decode,  # type: ignore
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamwriter=StreamWriter,
        streamreader=StreamReader,
    )

codecs.register(getregentry)
