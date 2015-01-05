from . import idnadata
import unicodedata
import re
import sys

_virama_combining_class = 9
_alabel_prefix = b'xn--'
_unicode_dots_re = re.compile(u'[\u002e\u3002\uff0e\uff61]')

if sys.version_info[0] == 3:
    unicode = str
    unichr = chr

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
    return ord(cp) in idnadata.scripts[script]

def _punycode(s):
    return s.encode('punycode')

def _unot(s):
    return 'U+{0:04X}'.format(s)


def valid_label_length(label):

    if len(label) > 63:
        return False
    return True


def valid_string_length(label):

    if len(label) > 254:
        return False
    return True


def check_bidi(label, check_ltr=False):

    # Bidi rules should only be applied if string contains RTL characters
    bidi_label = False
    for (idx, cp) in enumerate(label, 1):
        direction = unicodedata.bidirectional(cp)
        if direction == '':
            # String likely comes from a newer version of Unicode
            raise IDNABidiError('Unknown directionality in label {} at position {}'.format(repr(label), idx))
        if direction in ['R', 'AL', 'AN']:
            bidi_label = True
            break
    if not bidi_label and not check_ltr:
        return True

    # Bidi rule 1
    direction = unicodedata.bidirectional(label[0])
    if direction in ['R', 'AL']:
        rtl = True
    elif direction == 'L':
        rtl = False
    else:
        raise IDNABidiError('First codepoint in label {} must be directionality L, R or AL'.format(repr(label)))

    valid_ending = False
    number_type = False
    for (idx, cp) in enumerate(label, 1):
        direction = unicodedata.bidirectional(cp)

        if rtl:
            # Bidi rule 2
            if not direction in ['R', 'AL', 'AN', 'EN', 'ES', 'CS', 'ET', 'ON', 'BN', 'NSM']:
                raise IDNABidiError('Invalid direction for codepoint at position {} in a right-to-left label'.format(idx))
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
                raise IDNABidiError('Invalid direction for codepoint at position {} in a left-to-right label'.format(idx))
            # Bidi rule 6
            if direction in ['L', 'EN']:
                valid_ending = True
            elif direction != 'NSM':
                valid_ending = False

    if not valid_ending:
        raise IDNABidiError('Label ends with illegal codepoint directionality')

    return True


def check_initial_combiner(label):

    if unicodedata.category(label[0])[0] == 'M':
        raise IDNAError('Label begins with an illegal combining character')
    return True


def check_hyphen_ok(label):

    if label[2:4] == '--':
        raise IDNAError('Label has disallowed hyphens in 3rd and 4th position')
    if label[0] == '-' or label[-1] == '-':
        raise IDNAError('Label must not start or end with a hyphen')
    return True


def check_nfc(label):

    if unicodedata.normalize('NFC', label) != label:
        raise IDNAError('Label must be in Normalization Form C')


def valid_contextj(label, pos):

    cp_value = ord(label[pos])

    if cp_value == 0x200c:

        if pos > 0:
            if _combining_class(ord(label[pos - 1])) == _virama_combining_class:
                return True

        ok = False
        for i in range(pos-1, -1, -1):
            joining_type = idnadata.joining_types.get(ord(label[i]))
            if joining_type == 'T':
                continue
            if joining_type in ['L', 'D']:
                ok = True
                break

        if not ok:
            return False

        ok = False
        for i in range(pos+1, len(label)):
            joining_type = idnadata.joining_types.get(ord(label[i]))
            if joining_type == 'T':
                continue
            if joining_type in ['R', 'D']:
                ok = True
                break
        return ok

    if cp_value == 0x200d:

        if pos > 0:
            if _combining_class(ord(label[pos - 1])) == _virama_combining_class:
                return True
        return False

    else:

        return False


def valid_contexto(label, pos, exception=False):

    cp_value = ord(label[pos])

    if cp_value == 0x00b7:
        if 0 < pos < len(label)-1:
            if ord(label[pos - 1]) == 0x006c and ord(label[pos + 1]) == 0x006c:
                return True
        return False

    elif cp_value == 0x0375:
        if pos < len(label)-1 and len(label) > 1:
            return _is_script(label[pos + 1], 'Greek')
        return False

    elif cp_value == 0x05f3 or cp_value == 0x05f4:
        if pos > 0:
            return _is_script(label[pos - 1], 'Hebrew')
        return False

    elif cp_value == 0x30fb:
        for cp in label:
            if cp == u'\u30fb':
                continue
            if not _is_script(cp, 'Hiragana') and not _is_script(cp, 'Katakana') and not _is_script(cp, 'Han'):
                return False
        return True

    elif 0x660 <= cp_value <= 0x669:
        for cp in label:
            if 0x6f0 <= ord(cp) <= 0x06f9:
                return False
        return True

    elif 0x6f0 <= cp_value <= 0x6f9:
        for cp in label:
            if 0x660 <= ord(cp) <= 0x0669:
                return False
        return True


def check_label(label):

    if isinstance(label, (bytes, bytearray)):
        label = label.decode('utf-8')
    if len(label) == 0:
        raise IDNAError('Empty Label')

    check_nfc(label)
    check_hyphen_ok(label)
    check_initial_combiner(label)

    for (pos, cp) in enumerate(label):
        cp_value = ord(cp)
        if cp_value in idnadata.codepoint_classes['PVALID']:
            continue
        elif cp_value in idnadata.codepoint_classes['CONTEXTJ']:
            if not valid_contextj(label, pos):
                raise InvalidCodepointContext('Joiner {} not allowed at position {} in {}'.format(_unot(cp_value), pos+1, repr(label)))
        elif cp_value in idnadata.codepoint_classes['CONTEXTO']:
            if not valid_contexto(label, pos):
                raise InvalidCodepointContext('Codepoint {} not allowed at position {}'.format(_unot(cp_value), pos+1, repr(label)))
        else:
            raise InvalidCodepoint('Codepoint {} at position {} of {} not allowed'.format(_unot(cp_value), pos+1, repr(label)))

    check_bidi(label)


def alabel(label):

    try:
        label = label.encode('ascii')
        try:
            ulabel(label)
        except:
            raise IDNAError('The label {} is not a valid A-label'.format(label))
        if not valid_label_length(label):
            raise IDNAError('Label too long')
        return label
    except UnicodeError:
        pass

    if not label:
        raise IDNAError('No Input')

    label = unicode(label)
    check_label(label)
    label = _punycode(label)
    label = _alabel_prefix + label

    if not valid_label_length(label):
        raise IDNAError('Label too long')

    return label


def ulabel(label):

    if not isinstance(label, (bytes, bytearray)):
        try:
            label = label.encode('ascii')
        except UnicodeError:
            check_label(label)
            return label

    label = label.lower()
    if label.startswith(_alabel_prefix):
        label = label[len(_alabel_prefix):]
    else:
        check_label(label)
        return label.decode('ascii')

    label = label.decode('punycode')
    check_label(label)
    return label


def encode(s, strict=False):

    trailing_dot = False
    result = []
    if strict:
        labels = s.split('.')
    else:
        labels = _unicode_dots_re.split(s)
    if labels[-1] == '':
        labels = labels[0:-1]
        trailing_dot = True
    if not labels:
        raise IDNAError('Empty domain')
    for label in labels:
        result.append(alabel(label))
    if trailing_dot:
        result.append(b'')
    return b'.'.join(result)


def decode(s, strict=False):

    trailing_dot = False
    result = []
    if isinstance(s, (bytes, bytearray)):
        labels = s.split(b'.')
    else:
        if not strict:
            labels = _unicode_dots_re.split(s)
        else:
            labels = s.split(u'.')
    if not labels[-1]:
        labels = labels[0:-1]
        trailing_dot = True
    if not labels:
        raise IDNAError('Empty domain')
    for label in labels:
        result.append(ulabel(label))
    if trailing_dot:
        result.append(u'')
    return u'.'.join(result)
