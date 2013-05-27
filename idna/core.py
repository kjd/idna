import idnadata
import unicodedata
import re

_virama_combining_class = 9
_alabel_prefix = "xn--"


class IDNAError(UnicodeError):
    """ Base exception for all IDNA-encoding related problems """
    pass


class IDNABidiError(IDNAError):
    """ Exception when bidirectional requirements are not satisfied """
    pass


class InvalidCodepoint(IDNAError):
    """ Exception when a disallowed or unallocated codepoint is used """
    pass


class InvalidCodepointContext(IDNAError):
    """ Exception when the codepoint is not valid in the context it is used """
    pass


def _combining_class(cp):
    return unicodedata.combining(unichr(cp))


def _is_script(cp, script):
    return cp in idnadata.scripts[script]


def _punycode(s):
    return s.encode('punycode')


def valid_label_length(label):
    if len(label) > 63:
        return False
    return True


def valid_string_length(label):
    if len(label) > 254:
        return False
    return True


def check_bidi(label):
    # Bidi rule 1
    direction = unicodedata.bidirectional(label[0])
    if direction in ['R', 'AL']:
        rtl = True
    elif direction == 'L':
        rtl = False
    else:
        raise IDNABidiError('First codepoint in label must be directionality L, R or AL')

    valid_ending = False
    number_type = False
    for cp in label:
        direction = unicodedata.bidirectional(cp)

        if rtl:
            # Bidi rule 2
            if not direction in ['R', 'AL', 'AN', 'EN', 'ES', 'CS', 'ET', 'ON', 'BN', 'NSM']:
                raise IDNABidiError('Invalid direction for codepoint in a right-to-left label')
            # Bidi rule 3
            if direction in ['R', 'AL', 'EN', 'AN']:
                valid_ending = True
            elif direction != 'NSM':
                valid_ending = False
            # Bidi rule 4
            if direction in ['AN', 'EN']:
                if not number_type:
                    number_type = direction
                else:
                    if number_type != direction:
                        raise IDNABidiError('Can not mix numeral types in a right-to-left label')
        else:
            # Bidi rule 5
            if not direction in ['L', 'EN', 'ES', 'CS', 'ET', 'ON', 'BN', 'NSM']:
                raise IDNABidiError('Invalid direction for codepoint in a left-to-right label')
            # Bidi rule 6
            if direction in ['L', 'EN']:
                valid_ending = True
            elif direction != 'NSM':
                valid_ending = False

    if not valid_ending:
        raise IDNABidiError('Label ends with illegal codepoint directionality')

    return True


def check_initial_combiner(label):
    if unicodedata.category(label[0])[0] == 'C':
        raise IDNAError('Label begins with an illegal combining character')
    return True


def check_hyphen_ok(label):
    if label[2:2] == '--':
        raise IDNAError('Label has disallowed hyphens in 3rd and 4th position')
    if label[0] == '-' or label[-1] == '-':
        raise IDNAError('Label must not start or end with a hyphen')
    return True


def valid_contextj(label, pos):

    if label[pos] == 0x200c:

        if pos > 0:
            if _combining_class(label[pos - 1]) == _virama_combining_class:
                return True

        ok = False
        for i in range(pos-1, -1, -1):
            joining_type = idnadata.joining_types.get(label[i])
            if joining_type == 'T':
                continue
            if joining_type in ['L', 'D']:
                ok = True
                break

        if not ok:
            return False

        ok = False
        for i in range(pos+1, len(label)):
            joining_type = idnadata.joining_types.get(label[i])
            if joining_type == 'T':
                continue
            if joining_type in ['R', 'D']:
                ok = True
                break
        return ok

    if label[pos] == 0x200d:

        if pos > 0:
            if _combining_class(label[pos - 1]) == _virama_combining_class:
                return True
        return False

    else:

        return False


def valid_contexto(label, pos, exception=False):

    if label[pos] == 0x00b7:
        if 0 < pos < len(label)-1:
            if label[pos - 1] == 0x006c and label[pos + 1] == 0x006c:
                return True
        return False

    elif label[pos] == 0x0375:
        if pos < len(label) and len(label) > 2:
            return _is_script(label[pos + 1], 'Greek')
        return False

    elif label[pos] == 0x05f3 or label[pos] == 0x05f4:
        if pos > 0:
            return _is_script(label[pos - 1], 'Hebrew')
        return False

    elif label[pos] == 0x30fb:
        for cp in label:
            if not _is_script(cp, "Hiragana") and not _is_script(cp, "Katakana") and not _is_script(cp, "Han"):
                return False
        return True

    elif 0x660 <= label[pos] <= 0x669:
        for cp in label:
            if 0x6f0 <= cp <= 0x06f9:
                return False
        return True

    elif 0x6f0 <= label[pos] <= 0x6f9:
        for cp in label:
            if 0x660 <= cp <= 0x0669:
                return False
        return True


def check_label(label):

    check_hyphen_ok(label)
    check_initial_combiner(label)

    for pos in range(0, len(label)):
        cp = ord(label[pos])
        if cp in idnadata.codepoint_classes['PVALID']:
            continue
        elif cp in idnadata.codepoint_classes['CONTEXTJ']:
            if not valid_contextj(label, pos):
                raise InvalidCodepointContext('Joiner {} not allowed at position {}'.format(hex(cp), pos))
        elif cp in idnadata.codepoint_classes['CONTEXTO']:
            if not valid_contexto(label, pos):
                raise InvalidCodepointContext('Codepoint {} not allowed at position {}'.format(hex(cp), pos))
        else:
            raise InvalidCodepoint('Codepoint {} at position {}  not allowed'.format(hex(cp), pos))

    check_bidi(label)


def alabel(label):

    try:
        label = label.encode("ascii")
        return label
    except UnicodeError:
        pass

    if not label:
        raise IDNAError("No Input")

    label = unicode(label)
    check_label(label)
    label = _punycode(label)
    label = _alabel_prefix + label

    if not valid_label_length(label):
        raise IDNAError("Label too long")

    return label


def ulabel(label):

    try:
        label = label.encode("ascii")
    except UnicodeError:
        try:
            check_label(label)
        except:
            raise IDNAError('Label not an IDNA-valid label')
        return label

    label = label.lower()
    if label.startswith(_alabel_prefix):
        label = label[len(_alabel_prefix):]
    else:
        return label

    label = label.decode("punycode")
    check_label(label)
    return label

def encode(s, strict=False):

    result = []
    if strict:
        labels = '.'.split(s)
    else:
        labels = re.compile(u'[\u002e\u3002\uff0e\uff61]').split(s)
    for label in labels:
        result.append(alabel(label))
    return '.'.join(result)

def decode(s, strict=False):

    result = []
    if strict:
        labels = '.'.split(s)
    else:
        labels = re.compile(u'[\u002e\u3002\uff0e\uff61]').split(s)
    for label in labels:
        result.append(ulabel(label))
    return u'.'.join(result)
