import inspect
import re
import uuid

from .parser import ast
from .parser.lex import lexer
from .parser.parse import parser


class DryckException(Exception):
    pass


class SuppressPageGenerationException(Exception):
    pass


def raw(f):
    """Decorator for a dryck function that should receive the raw (unevaluated)
    text of its argument. By default, arguments are evaluated before the
    function is applied."""
    f._dryck_raw = True
    return f


def block(f):
    """Decorator for a dryck function that should have its argument evaluated
    in block context instead of the default span context."""
    f._dryck_block = True
    return f


def indented(f):
    """Decorator for a dryck function whose output should be automatically
    indented to match the indent at which the function call appeared."""
    f._dryck_indented = True
    return f


def pyargs(f):
    """Decorator for a dryck function that takes Python expressions instead
    of text as its arguments."""
    f._dryck_pyargs = True
    return f


def get_func_props(fn):
    lazy = hasattr(fn, '_dryck_raw')
    block = hasattr(fn, '_dryck_block')
    indented = hasattr(fn, '_dryck_indented')
    pyargs = hasattr(fn, '_dryck_pyargs')
    return (lazy, block, indented, pyargs)


def apply_func(fn, args, env, raw, indent):
    # TODO: What to do if meta variables get returned?
    # Read function decorators.
    (lazy, block, indented, pyargs) = get_func_props(fn)

    if pyargs and lazy:
        raise Exception(f'Dryck function {fn} cannot be both pyargs and lazy')

    if pyargs:
        parsed_args = [eval(arg, env.__dict__)
                       for arg in args]
    elif not lazy:
        parsed_args = [eval_page(arg, env, tight=(not block), raw=raw, name=f'arg {i+1} of {fn.__name__}')
                       for (i, arg) in enumerate(args)]
    else:
        parsed_args = args

    ret = fn(*parsed_args)

    # TODO: Don't emit trailing whitespace!
    if indented:
        if len(ret) > 0 and ret[-1] == '\n':
            ret = ret[:-1]
        ret = ret.replace('\n', '\n' + indent)

    if not isinstance(ret, str):
        raise Exception(f'Expected {fn} to return str, but got {ret}')
    return ret


def combine_until_close(tokens, multi=False):
    depth = 1
    out = []
    current_out = ''
    while depth > 0:
        tok = tokens.__next__()
        if tok.type in ['FUNC_OPEN', 'EVAL_OPEN', 'BRACE_OPEN']:
            depth += 1
        elif tok.type == 'BRACE_CLOSE':
            depth -= 1
        elif tok.type == 'BRACE_CLOSE_OPEN':
            if depth == 1 and multi:
                # }{ at top depth means
                # to end the current arg and start a new one.
                out += [current_out]
                current_out = ''
            else:
                current_out += tok.value

        if depth > 0 and tok.type != 'BRACE_CLOSE_OPEN':
            current_out += tok.value
    out += [current_out]
    return out


def eval_text(elements, env, raw):
    text = ''

    for t in elements:

        if isinstance(t, ast.Eval):
            methods = {x: getattr(env, x) for x in dir(env)
                    if inspect.ismethod(getattr(env, x))}
            methods['__context__'] = env
            ret = eval(t.expr.rstrip(), env.__dict__, methods)
            if not isinstance(ret, str):
                raise Exception(f'Expected eval to return str, but got {ret}')
            text += ret

        elif isinstance(t, ast.Apply):
            # A ◊foo followed by one or more {expr}'s
            # is a function call with arguments.
            # A plain ◊foo with no args
            # can be either a variable or a nullary function call.
            indent = 0  # TODO: get_indent(text, tok)
            fn = getattr(env, t.func)
            if callable(fn):
                ret = apply_func(fn, t.args, env, raw, indent)
                # TODO: Handle props.
                props = get_func_props(fn)
                text += ret
            elif len(t.args) == 0:
                text += fn
            else:
                raise DryckException('Tried to pass args to a non-callable')

        elif isinstance(t, ast.Link):
            indent = 0  # TODO: get_indent(text, tok)
            text += apply_func(env.wiki_link, (t.dest, t.label), env, raw, indent)

        elif isinstance(t, ast.Text):
            text += t.text

        elif isinstance(t, ast.Soft):
            pass

        elif isinstance(t, ast.Star):
            text += env.em(eval_text(t.text, env, raw))

        elif isinstance(t, ast.Break):
            text += env.br()

        else:
            raise Exception('Bad element: ' + str(t))

    return text


def eval_page(text, env, raw=False, tight=False, name=None):
    body = ''

    # TODO: Use filename for error handling.
    lexer.lineno = 0
    parser.raw = raw  # TODO: Hahahaha.
    doc = parser.parse(text)

    if tight and len(doc.text) > 1:
        raise DryckException('Too many paragraphs in tight argument: ' + str(doc))

    try:
        # State manipulators.
        # These don't directly affect the final markup.
        # They put stuff into the environment.
        for md in doc.metatext:
            setattr(env, md.key, md.val)

        for p in doc.text:

            if isinstance(p, ast.Raw):
                text = eval_text(p.text, env, raw)
                body += text

            elif isinstance(p, ast.Paragraph):
                text = eval_text(p.text, env, raw)
                body += text if tight else env.p(text)

            elif isinstance(p, ast.Itemized):
                items = ''
                for item in p.items:
                    text = eval_text(item.text, env, raw)
                    items += env.li(text)
                body += env.ul(items)

            elif isinstance(p, ast.Heading):
                text = eval_text(p.text, env, raw)
                body += env.heading(p.level, text)

            else:
                raise Exception('Bad block: ' + str(p))


    except Exception as e:
        if type(e) == SuppressPageGenerationException:
            raise
        else:
            lineno = 0  # TODO
            col = 0  # TODO
            raise DryckException(f'Error on line {lineno} col {col}' +
                                 f' of {name}' if name else '') from e

    return body


WHITESPACE_RE = re.compile(r'[\t ]*')

# Based upon find_column from https://ply.readthedocs.io/en/latest/ply.html
def get_indent(text, tok):
    line_start = text.rfind('\n', 0, tok.lexpos) + 1
    candidate = text[line_start:tok.lexpos]
    return candidate if WHITESPACE_RE.match(candidate) else ''
