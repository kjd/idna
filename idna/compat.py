#
# This is a compatibility module for the IDNA 2003 support in Python's standard library.
# Replace
#     import encodings.idna
# with
#     import idna.compat as encodings.idna
# in order to easily use IDNA 2008 instead of IDNA 2003.
# Some functions are derived from the Python standard library.
#

from idna.core import *
import codecs
import re

dots = re.compile(u"[\u002E\u3002\uFF0E\uFF61]")


def ToASCII(label):
    return alabel(label)

def ToUnicode(label):
    return ulabel(label)

def nameprep(s):
    raise NotImplementedError("IDNA 2008 does not utilise nameprep protocol")

class Codec(codecs.Codec):

    def encode(self, data, errors='strict'):

        if errors != 'strict':
            raise UnicodeError("unsupported error handling "+errors)

        if not data:
            return "", 0

        return encode(data), len(data)

    def decode(self, data, errors='strict'):

        if errors != 'strict':
            raise UnicodeError("Unsupported error handling "+errors)

        if not data:
            return u"", 0

        return decode(data), len(data)

class IncrementalEncoder(codecs.BufferedIncrementalEncoder):
    def _buffer_encode(self, data, errors, final):
        if errors != 'strict':
            # IDNA is quite clear that implementations must be strict
            raise UnicodeError("unsupported error handling "+errors)

        if not data:
            return ("", 0)

        labels = dots.split(data)
        trailing_dot = u''
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
            result.append(ToASCII(label))
            if size:
                size += 1
            size += len(label)

        # Join with U+002E
        result = ".".join(result) + trailing_dot
        size += len(trailing_dot)
        return (result, size)

class IncrementalDecoder(codecs.BufferedIncrementalDecoder):
    def _buffer_decode(self, data, errors, final):
        if errors != 'strict':
            raise UnicodeError("Unsupported error handling "+errors)

        if not data:
            return (u"", 0)

        # IDNA allows decoding to operate on Unicode strings, too.
        if isinstance(data, unicode):
            labels = dots.split(data)
        else:
            # Must be ASCII string
            data = str(data)
            unicode(data, "ascii")
            labels = data.split(".")

        trailing_dot = u''
        if labels:
            if not labels[-1]:
                trailing_dot = u'.'
                del labels[-1]
            elif not final:
                # Keep potentially unfinished label until the next call
                del labels[-1]
                if labels:
                    trailing_dot = u'.'

        result = []
        size = 0
        for label in labels:
            result.append(ToUnicode(label))
            if size:
                size += 1
            size += len(label)

        result = u".".join(result) + trailing_dot
        size += len(trailing_dot)
        return (result, size)


class StreamWriter(Codec, codecs.StreamWriter):
    pass

class StreamReader(Codec, codecs.StreamReader):
    pass

### encodings module API

def getregentry():
    return codecs.CodecInfo(
        name='idna',
        encode=Codec().encode,
        decode=Codec().decode,
        incrementalencoder=IncrementalEncoder,
        incrementaldecoder=IncrementalDecoder,
        streamwriter=StreamWriter,
        streamreader=StreamReader,
    )
