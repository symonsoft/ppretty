from functools import partial
from inspect import isroutine
from numbers import Number

import sys


def ppretty(obj, indent='    ', depth=4, width=72, seq_length=5,
            show_protected=False, show_private=False, show_static=False, show_properties=False, show_address=False,
            str_length=50):
    """Represents any python object in a human readable format.

    :param obj: An object to represent.
    :type obj: object
    :param indent: Fill string for indents. Default is '    '.
    :type indent: str
    :param depth: Depth of introspecion. Default is 4.
    :type depth: int
    :param width: Width of line in output string. It may be exceeded when representation doesn't fit. Default is 72.
    :type width: int
    :param seq_length: Maximum sequence length. Also, used for object's members enumeration. Default is 5.
    :type seq_length: int
    :param show_protected: Examine protected members. Default is False.
    :type show_protected: bool
    :param show_private: Examine private members. To take effect show_protected must be set to True. Default is False.
    :type show_private: bool
    :param show_static: Examine static members. Default is False.
    :type show_static: bool
    :param show_properties: Examine properties members. Default is False.
    :type show_properties: bool
    :param show_address: Show address. Default is False.
    :type show_address: bool
    :param str_length: Maximum string length. Default is 50.
    :type str_length: int

    :return: The final representation of the object.
    :rtype: str
    """

    seq_brackets = {list: ('[', ']'), tuple: ('(', ')'), set: ('set([', '])'), dict: ('{', '}')}
    seq_types = tuple(seq_brackets.keys())
    basestring_type = basestring if sys.version_info[0] < 3 else str

    def inspect_object(current_obj, current_depth, current_width, seq_type_descendant=False):
        inspect_nested_object = partial(inspect_object,
                                        current_depth=current_depth - 1,
                                        current_width=current_width - len(indent))

        # Basic types
        if isinstance(current_obj, Number):
            return [repr(current_obj)]

        # Strings
        if isinstance(current_obj, basestring_type):
            if len(current_obj) <= str_length:
                return [repr(current_obj)]
            return [repr(current_obj[:int(str_length / 2)] + '...' + current_obj[int((1 - str_length) / 2):])]

        # Class object
        if isinstance(current_obj, type):
            module = current_obj.__module__ + '.' if hasattr(current_obj, '__module__') else ''
            return ["<class '" + module + current_obj.__name__ + "'>"]

        # None
        if current_obj is None:
            return ['None']

        # Format block of lines
        def format_block(lines, open_bkt='', close_bkt=''):
            new_lines = []  # new_lines will be returned if width exceeded
            one_line = ''  # otherwise, one_line will be returned.
            if open_bkt:
                new_lines.append(open_bkt)
                one_line += open_bkt
            for line in lines:
                new_lines.append(indent + line)
                if len(one_line) <= current_width:
                    one_line += line
            if close_bkt:
                if lines:
                    new_lines.append(close_bkt)
                else:
                    new_lines[-1] += close_bkt
                one_line += close_bkt

            return [one_line] if len(one_line) <= current_width and one_line else new_lines

        class SkipElement(object):
            pass

        class ErrorAttr(object):
            def __init__(self, e):
                self.e = e

        def cut_seq(seq):
            if current_depth < 1:
                return [SkipElement()]
            if len(seq) <= seq_length:
                return seq
            elif seq_length > 1:
                seq = list(seq) if isinstance(seq, tuple) else seq
                return seq[:int(seq_length / 2)] + [SkipElement()] + seq[int((1 - seq_length) / 2):]
            return [SkipElement()]

        def format_seq(extra_lines):
            r = []
            items = cut_seq(obj_items)
            for n, i in enumerate(items, 1):
                if type(i) is SkipElement:
                    r.append('...')
                else:
                    if type(current_obj) is dict or seq_type_descendant and isinstance(current_obj, dict):
                        (k, v) = i
                        k = inspect_nested_object(k)
                        v = inspect_nested_object(v)
                        k[-1] += ': ' + v.pop(0)
                        r.extend(k)
                        r.extend(format_block(v))
                    elif type(current_obj) in seq_types or seq_type_descendant and isinstance(current_obj, seq_types):
                        r.extend(inspect_nested_object(i))
                    else:
                        (k, v) = i
                        k = [k]
                        v = inspect_nested_object(v) if type(v) is not ErrorAttr else ['<Error attribute: ' + type(v.e).__name__ + ': ' + v.e.message + '>']
                        k[-1] += ' = ' + v.pop(0)
                        r.extend(k)
                        r.extend(format_block(v))
                if n < len(items) or extra_lines:
                    r[-1] += ', '
            return format_block(r + extra_lines, *brackets)

        # Sequence types
        # Others objects are considered as sequence of members
        extra_lines = []
        if type(current_obj) in seq_types or seq_type_descendant and isinstance(current_obj, seq_types):
            if isinstance(current_obj, dict):
                obj_items = list(current_obj.items())
            else:
                obj_items = current_obj

            if seq_type_descendant:
                brackets = seq_brackets[[seq_type for seq_type in seq_types if isinstance(current_obj, seq_type)].pop()]
            else:
                brackets = seq_brackets[type(current_obj)]
        else:
            obj_items = []
            for k in sorted(dir(current_obj)):
                if not show_private and k.startswith('_') and '__' in k:
                    continue
                if not show_protected and k.startswith('_'):
                    continue
                try:
                    v = getattr(current_obj, k)
                    if isroutine(v):
                        continue
                    if not show_static and hasattr(type(current_obj), k) and v is getattr(type(current_obj), k):
                        continue
                    if not show_properties and hasattr(type(current_obj), k) and isinstance(
                            getattr(type(current_obj), k), property):
                        continue
                except Exception as e:
                    v = ErrorAttr(e)

                obj_items.append((k, v))

            if isinstance(current_obj, seq_types):
                # If object's class was inherited from one of basic sequence types
                extra_lines += inspect_nested_object(current_obj, seq_type_descendant=True)

            module = current_obj.__module__ + '.' if hasattr(current_obj, '__module__') else ''
            address = ' at ' + hex(id(current_obj)) + ' ' if show_address else ''
            brackets = (module + type(current_obj).__name__ + address + '(', ')')

        return format_seq(extra_lines)

    return '\n'.join(inspect_object(obj, depth, width))


if __name__ == '__main__':
    class B(object):
        def __init__(self, b):
            self.b = b

    class A(object):
        i = [-3, 4.5, ('6', B({'\x07': 8}))]

        def __init__(self, a):
            self.a = a

    class C(object):
        def __init__(self):
            self.a = {u'1': A(2), '9': [1000000000000000000000, 11, {(12, 13): {14, None}}], 15: [16, 17, 18, 19, 20]}
            self.b = 'd'
            self._c = C.D()
            self.e = C.D

        d = 'c'

        def foo(self):
            pass

        @property
        def bar(self):
            return 'e'

        class D(object):
            pass


    print(ppretty(C(), indent='    ', depth=8, width=41, seq_length=100,
                  show_static=True, show_protected=True, show_properties=True, show_address=True))
    print(ppretty(C(), depth=8, width=200, seq_length=4))

    class E(dict):
        def __init__(self):
            dict.__init__(self, yyy='xxx')
            self.www = 'Very long text Bla-Bla-Bla'

    print(ppretty(E(), str_length=19))

    print(ppretty({x: x for x in range(10)}))
