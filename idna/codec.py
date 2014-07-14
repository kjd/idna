from idna.core import encode, decode, IDNAError
import codecs
import re

class Codec(codecs.Codec):

    def encode(self, data, errors='strict'):

        if errors != 'strict':
            raise IDNAError("Unsupported error handling \"{}\"".format(errors))

        if not data:
            return "", 0

        return encode(data), len(data)

    def decode(self, data, errors='strict'):

        if errors != 'strict':
            raise IDNAError("Unsupported error handling \"{}\"".format(errors))

        if not data:
            return u"", 0

        return decode(data), len(data)

class IncrementalEncoder(codecs.BufferedIncrementalEncoder):
    def _buffer_encode(self, data, errors, final):
        if errors != 'strict':
            raise IDNAError("Unsupported error handling \"{}\"".format(errors))

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
            raise IDNAError("Unsupported error handling \"{}\"".format(errors))

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
