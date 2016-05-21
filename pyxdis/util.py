# This comes from Python's dis.py

from pyxdis import PYTHON3
if PYTHON3:
    from io import StringIO
    def code2num(code, i):
        return code[i]
else:
    from StringIO import StringIO
    def code2num(code, i):
        return ord(code[i])

# The inspect module interrogates this dictionary to build its
# list of CO_* constants. It is also used by pretty_flags to
# turn the co_flags field into a human readable list.
COMPILER_FLAG_NAMES = {
    0x0001: "OPTIMIZED",
    0x0002: "NEWLOCALS",
    0x0004: "VARARGS",
    0x0008: "VARKEYWORDS",
    0x0010: "NESTED",
    0x0020: "GENERATOR",
    0x0040: "NOFREE",
    # These are in Python 3.x
    0x0080: "COROUTINE",
    0x0100: "ITERABLE_COROUTINE",

    # These are used only in Python 2.x */
    0x01000: "GENERATOR_ALLOWED",
    0x02000: "FUTURE_DIVISION",
    0x04000: "ABSOLUTE_IMPORT",
    0x08000: "FUTURE_WITH_STATEMENT",
    0x10000: "FUTURE_PRINT_FUNCTION",
    0x20000: "FUTURE_UNICODE_LITERALS",
    0x40000: "FUTURE_BARRY_AS_DBFL",
}

def pretty_flags(flags):
    """Return pretty representation of code flags."""
    names = []
    for i in range(32):
        flag = 1<<i
        if flags & flag:
            names.append(COMPILER_FLAG_NAMES.get(flag, hex(flag)))
            flags ^= flag
            if not flags:
                break
    else:
        names.append(hex(flags))
    return ", ".join(names)

def format_code_info(co, version):
    lines = []
    lines.append("# Method Name:       %s" % co.co_name)
    lines.append("# Filename:          %s" % co.co_filename)
    lines.append("# Argument count:    %s" % co.co_argcount)
    if version >= 3.0:
        lines.append("# Kw-only arguments: %s" % co.co_kwonlyargcount)
    lines.append("# Number of locals:  %s" % co.co_nlocals)
    lines.append("# Stack size:        %s" % co.co_stacksize)
    lines.append("# Flags:             %s" % pretty_flags(co.co_flags))
    if co.co_consts:
        lines.append("# Constants:")
        for i_c in enumerate(co.co_consts):
            lines.append("# %4d: %r" % i_c)
    if co.co_names:
        lines.append("# Names:")
        for i_n in enumerate(co.co_names):
            lines.append("%4d: %s" % i_n)
    if co.co_varnames:
        lines.append("# Variable names:")
        for i_n in enumerate(co.co_varnames):
            lines.append("# %4d: %s" % i_n)
    if co.co_freevars:
        lines.append("# Free variables:")
        for i_n in enumerate(co.co_freevars):
            lines.append("%4d: %s" % i_n)
    if co.co_cellvars:
        lines.append("# Cell variables:")
        for i_n in enumerate(co.co_cellvars):
            lines.append("# %4d: %s" % i_n)
    return "\n".join(lines)

def findlabels(code, opc):
    """Detect all offsets in a byte code which are jump targets.

    Return the list of offsets.

    """
    labels = []
    # enumerate() is not an option, since we sometimes process
    # multiple elements on a single pass through the loop
    n = len(code)
    i = 0
    while i < n:
        op = code2num(code, i)
        i = i+1
        if op >= opc.HAVE_ARGUMENT:
            arg = code2num(code, i) + code2num(code, i+1)*256
            i = i+2
            label = -1
            if op in opc.hasjrel:
                label = i+arg
            elif op in opc.hasjabs:
                label = arg
            if label >= 0:
                if label not in labels:
                    labels.append(label)
    return labels

def _try_compile(source, name):
    """Attempts to compile the given source, first as an expression and
       then as a statement if the first approach fails.

       Utility function to accept strings in functions that otherwise
       expect code objects
    """
    try:
        c = compile(source, name, 'eval')
    except SyntaxError:
        c = compile(source, name, 'exec')
    return c


def dis(x=None):
    """Disassemble classes, methods, functions, generators, or code.
    """
    if x is None:
        distb()
        return
    if hasattr(x, '__func__'):  # Method
        x = x.__func__
    if hasattr(x, '__code__'):  # Function
        x = x.__code__
    if hasattr(x, 'gi_code'):  # Generator
        x = x.gi_code
    if hasattr(x, '__dict__'):  # Class or module
        items = sorted(x.__dict__.items())
        for name, x1 in items:
            if isinstance(x1, _have_code):
                print("Disassembly of %s:" % name, file)
                try:
                    dis(x1, file)
                except TypeError as msg:
                    print("Sorry:", msg)
                print(file)
    elif isinstance(x, (bytes, bytearray)): # Raw bytecode
        _disassemble_bytes(x, file)
    else:
        raise TypeError("don't know how to disassemble %s objects" %
                        type(x).__name__)


def get_code_object(x):
    """Helper to handle methods, functions, generators, strings and raw code objects"""
    if hasattr(x, '__func__'): # Method
        x = x.__func__
    if hasattr(x, '__code__'): # Function
        x = x.__code__
    if hasattr(x, 'gi_code'):  # Generator
        x = x.gi_code
    if isinstance(x, str):     # Source code
        x = _try_compile(x, "<disassembly>")
    if hasattr(x, 'co_code'):  # Code object
        return x
    raise TypeError("don't know how to disassemble %s objects" %
                    type(x).__name__)

def code_info(x):
    """Formatted details of methods, functions, or code."""
    return format_code_info(get_code_object(x))

def show_code(co):
    """Print details of methods, functions, or code to *file*.

    If *file* is not provided, the output is printed on stdout.
    """
    print(code_info(co))