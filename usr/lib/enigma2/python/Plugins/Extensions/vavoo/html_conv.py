import re
import sys
import six
import types
from six import unichr, iteritems
from six.moves import html_entities

try:
    unicode
except NameError:
    unicode = str  # Python 3 fallback

try:
    basestring
except NameError:
    basestring = str  # fake definition for linter

try:
    long
except NameError:
    long = int  # fake definition for linter


if sys.version_info[0] < 3:
    string_types = (basestring,)
    integer_types = (int, long)
    text_type = unicode
else:
    string_types = (str,)
    integer_types = (int,)
    text_type = str


class_types = (type,) if six.PY3 else (type, types.ClassType)
# text_type = six.text_type  # unicode in Py2, str in Py3
binary_type = six.binary_type  # str in Py2, bytes in Py3
MAXSIZE = sys.maxsize  # Compatibile con entrambe le versioni

_UNICODE_MAP = {
    k: unichr(v) for k,
    v in iteritems(
        html_entities.name2codepoint)}
_ESCAPE_RE = re.compile("[&<>\"']")
_UNESCAPE_RE = re.compile(r"&\s*(#?)(\w+?)\s*;")
_ESCAPE_DICT = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&apos;",
}


def ensure_str(s, encoding="utf-8", errors="strict"):
    """Coerce *s* to `str`.

    - In Python 2:
      - `unicode` -> encoded to `str`
      - `str` -> `str`
    - In Python 3:
      - `str` -> `str`
      - `bytes` -> decoded to `str`
    """
    if isinstance(s, str):
        return s
    if isinstance(s, binary_type):
        return s.decode(encoding, errors)
    raise TypeError("not expecting type '%s'" % type(s))


def html_escape(value):
    return _ESCAPE_RE.sub(
        lambda match: _ESCAPE_DICT[match.group(0)], ensure_str(value).strip())


def html_unescape(value):
    return _UNESCAPE_RE.sub(_convert_entity, ensure_str(value).strip())


def _convert_entity(m):
    if m.group(1) == "#":
        try:
            return unichr(int(m.group(2)[1:], 16)) if m.group(
                2)[:1].lower() == "x" else unichr(int(m.group(2)))
        except ValueError:
            return "&#%s;" % m.group(2)
    return _UNICODE_MAP.get(m.group(2), "&%s;" % m.group(2))
