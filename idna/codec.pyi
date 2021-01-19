import codecs
from typing import Tuple

class Codec(codecs.Codec):
    def encode(self, data: str, errors: str = ...) -> Tuple[bytes, int]: ...
    def decode(self, data: bytes, errors: str = ...) -> Tuple[str, int]: ...

class IncrementalEncoder(codecs.BufferedIncrementalEncoder):
    def _buffer_encode(  # type: ignore
        self,
        data: str,
        errors: str,
        final: bool
    ) -> Tuple[str, int]: ...

class IncrementalDecoder(codecs.BufferedIncrementalDecoder):
    def _buffer_decode(  # type: ignore
        self,
        data: str,
        errors: str,
        final: bool
    ) -> Tuple[str, int]: ...

class StreamWriter(Codec, codecs.StreamWriter): ...
class StreamReader(Codec, codecs.StreamReader): ...

def getregentry() -> codecs.CodecInfo: ...
