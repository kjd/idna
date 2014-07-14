from idna.core import *
from idna.codec import *

dots = re.compile(u"[\u002E\u3002\uFF0E\uFF61]")

def ToASCII(label):
    return alabel(label)

def ToUnicode(label):
    return ulabel(label)

def nameprep(s):
    raise NotImplementedError("IDNA 2008 does not utilise nameprep protocol")

