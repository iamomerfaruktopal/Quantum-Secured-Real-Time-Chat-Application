"""Utilities for writing code that runs on Python 2 and 3"""

import sys
import types
import functools
import itertools
import operator
from io import StringIO, BytesIO
import _thread

# Python version compatibility flags
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
PY34 = sys.version_info[0:2] >= (3, 4)

# Add these lines at the top after imports
import operator
try:
    advance_iterator = next
except NameError:
    def advance_iterator(it):
        return it.next()
next = advance_iterator

class _MovedItems(types.ModuleType):
    """Lazy loading of moved objects"""
    __path__ = []  # mark as package

# Create the moves module first
sys.modules["six.moves"] = _MovedItems("six.moves")
moves = sys.modules["six.moves"]

class _LazyDescr(object):
    def __init__(self, name):
        self.name = name

    def __get__(self, obj, tp):
        result = self._resolve()
        setattr(obj, self.name, result)
        return result

class MovedModule(_LazyDescr):
    def __init__(self, name, old, new=None):
        super(MovedModule, self).__init__(name)
        self.old = old
        self.new = new or old
        self._resolved = None

    def _resolve(self):
        if self._resolved is None:
            self._resolved = __import__(self.new if PY3 else self.old)
        return self._resolved

    def __getattr__(self, attr):
        module = self._resolve()
        return getattr(module, attr)

    def __dir__(self):
        module = self._resolve()
        return dir(module)

class MovedAttribute(_LazyDescr):
    def __init__(self, name, old_mod, new_mod, old_attr=None, new_attr=None):
        super(MovedAttribute, self).__init__(name)
        self.old_mod = old_mod
        self.new_mod = new_mod
        self.old_attr = old_attr or name
        self.new_attr = new_attr or name

    def _resolve(self):
        module = __import__(self.new_mod if PY3 else self.old_mod)
        return getattr(module, self.new_attr if PY3 else self.old_attr)

_moved_attributes = [
    MovedModule("_thread", "thread", "_thread"),
    MovedModule("builtins", "__builtin__", "builtins"),
    MovedModule("configparser", "ConfigParser", "configparser"),
    MovedModule("copyreg", "copy_reg", "copyreg"),
    MovedModule("http_cookiejar", "cookielib", "http.cookiejar"),
    MovedModule("html_entities", "htmlentitydefs", "html.entities"),
    MovedModule("html_parser", "HTMLParser", "html.parser"),
    MovedModule("http_client", "httplib", "http.client"),
    MovedModule("queue", "Queue", "queue"),
    MovedModule("reprlib", "repr", "reprlib"),
    MovedModule("socketserver", "SocketServer", "socketserver"),
    MovedModule("tkinter", "Tkinter", "tkinter"),
    MovedModule("urllib_parse", "urlparse", "urllib.parse"),
    MovedModule("urllib_error", "urllib2", "urllib.error"),
    MovedModule("urllib", "urllib", "urllib.parse"),
    MovedModule("urllib_robotparser", "robotparser", "urllib.robotparser"),
]

# Add all the moved objects to six.moves
for attr in _moved_attributes:
    setattr(moves, attr.name, attr)

# Special handling for _thread
moves._thread = _thread

if PY3:
    string_types = str,
    integer_types = int,
    class_types = type,
    text_type = str
    binary_type = bytes

    MAXSIZE = sys.maxsize
    def get_unbound_function(unbound):
        return unbound

    create_bound_method = types.MethodType

    def create_unbound_method(func, cls):
        return func

    Iterator = object
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

    def get_unbound_function(unbound):
        return unbound.im_func

    def create_bound_method(func, obj):
        return types.MethodType(func, obj, obj.__class__)

    def create_unbound_method(func, cls):
        return types.MethodType(func, None, cls)

    class Iterator(object):
        def next(self):
            return type(self).__next__(self)

def u(s):
    return s

def b(s):
    return s.encode("latin-1")

unichr = chr
int2byte = lambda x: bytes((x,))

def byte2int(bs):
    return bs[0] if isinstance(bs, bytes) else ord(bs)

def indexbytes(buf, i):
    return buf[i] if isinstance(buf, bytes) else ord(buf[i])

iterbytes = lambda buf: (byte2int(b) for b in buf)

assertCountEqual = "assertCountEqual"

def ensure_binary(s, encoding='utf-8', errors='strict'):
    if isinstance(s, binary_type):
        return s
    return s.encode(encoding, errors)

def ensure_str(s, encoding='utf-8', errors='strict'):
    if not isinstance(s, (text_type, binary_type)):
        raise TypeError("not expecting type '%s'" % type(s))
    if isinstance(s, binary_type):
        s = s.decode(encoding, errors)
    return s

def ensure_text(s, encoding='utf-8', errors='strict'):
    if isinstance(s, binary_type):
        return s.decode(encoding, errors)
    elif isinstance(s, text_type):
        return s
    else:
        raise TypeError("not expecting type '%s'" % type(s))

def with_metaclass(meta, *bases):
    return meta("NewBase", bases, {})

def iteritems(d):
    return iter(d.items())

def iterkeys(d):
    return iter(d.keys())

def itervalues(d):
    return iter(d.values())

def add_metaclass(metaclass):
    """Class decorator for creating a class with a metaclass."""
    def wrapper(cls):
        orig_vars = cls.__dict__.copy()
        slots = orig_vars.get('__slots__')
        if slots is not None:
            if isinstance(slots, str):
                slots = [slots]
            for slots_var in slots:
                orig_vars.pop(slots_var)
        orig_vars.pop('__dict__', None)
        orig_vars.pop('__weakref__', None)
        if hasattr(cls, '__qualname__'):
            orig_vars['__qualname__'] = cls.__qualname__
        return metaclass(cls.__name__, cls.__bases__, orig_vars)
    return wrapper

def add_move(move):
    """Add an item to six.moves."""
    setattr(_MovedItems, move.name, move)

def remove_move(name):
    """Remove item from six.moves."""
    try:
        delattr(_MovedItems, name)
    except AttributeError:
        try:
            del moves.__dict__[name]
        except KeyError:
            raise AttributeError("no such move, %r" % (name,)) 