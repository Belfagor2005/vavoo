import re
from six import unichr, iteritems  # ensure_str
from six.moves import html_entities
import sys
import functools
import itertools
import operator
import sys
import types
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

if PY3:
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes

    MAXSIZE = sys.maxsize
else:
    string_types = basestring,
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str

    if sys.platform.startswith("java"):
        # Jython always uses 32 bits.
        MAXSIZE = int((1 << 31) - 1)
    else:
        # It's possible to have sizeof(long) != sizeof(Py_ssize_t).
        class X(object):

            def __len__(self):
                return 1 << 31
        try:
            len(X())
        except OverflowError:
            # 32-bit
            MAXSIZE = int((1 << 31) - 1)
        else:
            # 64-bit
            MAXSIZE = int((1 << 63) - 1)
        del X

_UNICODE_MAP = {k: unichr(v) for k, v in iteritems(html_entities.name2codepoint)}
_ESCAPE_RE = re.compile("[&<>\"']")
_UNESCAPE_RE = re.compile(r"&\s*(#?)(\w+?)\s*;")  # Whitespace handling added due to "hand-assed" parsers of html pages
_ESCAPE_DICT = {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&apos;",
                }



def ensure_str(s, encoding='utf-8', errors='strict'):
    """Coerce *s* to `str`.

    For Python 2:
      - `unicode` -> encoded to `str`
      - `str` -> `str`

    For Python 3:
      - `str` -> `str`
      - `bytes` -> decoded to `str`
    """
    # Optimization: Fast return for the common case.
    if type(s) is str:
        return s
    if PY2 and isinstance(s, text_type):
        return s.encode(encoding, errors)
    elif PY3 and isinstance(s, binary_type):
        return s.decode(encoding, errors)
    elif not isinstance(s, (text_type, binary_type)):
        raise TypeError("not expecting type '%s'" % type(s))
    return s


def html_escape(value):
    return _ESCAPE_RE.sub(lambda match: _ESCAPE_DICT[match.group(0)], ensure_str(value).strip())


def html_unescape(value):
    return _UNESCAPE_RE.sub(_convert_entity, ensure_str(value).strip())


def _convert_entity(m):
    if m.group(1) == "#":
        try:
            return unichr(int(m.group(2)[1:], 16)) if m.group(2)[:1].lower() == "x" else unichr(int(m.group(2)))
        except ValueError:
            return "&#%s;" % m.group(2)
    return _UNICODE_MAP.get(m.group(2), "&%s;" % m.group(2))
