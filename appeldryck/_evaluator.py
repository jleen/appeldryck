import re
import sys
import uuid

from pathlib import Path

import marko

from . import _parser as parser


class SuppressPageGenerationException(Exception):
    pass


VAR_RE  = re.compile(r'◊(.+)')
META_RE = re.compile(r'◊(.+?):\s*(.*)')
FUNC_RE = re.compile(r'◊(.+?){')
WIKI_RE = re.compile(r'\[\[(.+?)(\|(.*))?]]')


def raw(f):
    f._appeldryck_raw = True
    return f


def block(f):
    f._appeldryck_block = True
    return f


def apply_func(fn, args, env):
    # TODO: What to do if meta variables get returned?
    # Read function decorators.
    raw = hasattr(fn, '_appeldryck_raw')
    block = hasattr(fn, '_appeldryck_block')

    if not hasattr(fn, '_appeldryck_raw'):
        parsed_args = [eval_page(arg, env, tight=(not block)) for arg in args]
    else:
        parsed_args = args
    ret = fn(*parsed_args)
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


class _DryckHtmlRenderer(marko.HTMLRenderer):
    '''Marko renderer to redirect tag rendering back to the user's functions.

    Should not be directly instantiated.
    Please call make_DryckHtmlRenderer to curry the env.
    '''
    def render_heading(self, heading):
        body = self.render_children(heading)
        fn = getattr(self.env, 'heading', None)
        if fn:
            return apply_func(fn, (heading.level, body), None)
        else:
            return f'<h{heading.level}>{body}</h{heading.level}>'


def make_DryckHtmlRenderer(the_env):
    class DryckHtmlRenderer(_DryckHtmlRenderer):
        env = the_env
    return DryckHtmlRenderer


def eval_text(env, text, tight):
    # TODO: Unsquirrel before calling tag functions?
    renderer = make_DryckHtmlRenderer(env)
    markdown = marko.Markdown(renderer=renderer)
    parsed = markdown.parse(text)
    if tight:
        for child in parsed.children:
            child._tight = True
    return markdown.render(parsed)


def squirrel(nuts, nut):
    '''Replace the given nut with a unique placeholder,
    and remember the placeholder and its translation.'''
    k = str(uuid.uuid4())
    nuts[k] = nut
    return k


def eval_page(text, env, raw=False, tight=False):
    body = ''
    nuts = {}

    tokens = parser.tokenize(text)

    while True:
        try:
            tok = tokens.__next__()
        except StopIteration:
            break

        # Plain old text.
        # These tokens just get passed through to the next parsing layer,
        # which is the Markdown parser.

        if tok.type == 'TEXT':
            body += tok.value

        elif tok.type == 'BRACE_OPEN':
            [inner] = combine_until_close(tokens)
            body += '{' + inner + '}'

        elif tok.type == 'BRACE_CLOSE' or tok.type == 'BRACE_CLOSE_OPEN':
            # Just in case we get a mismatched close paren. Harmless.
            body += tok.value

        # State manipulators.
        # These don't directly affect the final markup.
        # They put stuff into the environment.

        elif tok.type == 'META':
            (k, v) = META_RE.match(tok.value).group(1, 2)
            setattr(env, k, v)

        # Evaluated expressions.
        # These are evaluated in the order seen
        # (except for expressions within function arguments,
        # which are evaluated before application, in the usual way,
        # inside of apply_func).
        # Return values are considered final markup, *not* program code,
        # and thus are squirreled
        # so the Markdown parser doesn't evaluate them.

        elif tok.type == 'VAR':
            # A plain ◊foo with no args
            # can be either a variable or a nullary function call
            v = VAR_RE.match(tok.value).group(1)
            val = getattr(env, v)
            if callable(val):
                body += squirrel(nuts, apply_func(val, (), env))
            else:
                body += squirrel(nuts, val)

        elif tok.type == 'FUNC_OPEN':
            # A ◊foo followed by one or more {expr}'s
            # is a function call with arguments.
            func_name = FUNC_RE.match(tok.value).group(1)
            fn = getattr(env, func_name)
            args = combine_until_close(tokens, multi=True)
            ret = apply_func(fn, args, env)
            # Squirrel the function's return value
            # so that it doesn't get evaluated as Markdown later.
            body += squirrel(nuts, ret)

        elif tok.type == 'EVAL_OPEN':
            # A ◊{foo} just evaluates foo.
            [exp] = combine_until_close(tokens)
            body += squirrel(nuts, eval(exp, env.__dict__))

        elif tok.type == 'WIKI_LINK':
            # [[link|label]] serves as a syntactic sugar for calling ◊link.
            (dest, label) = WIKI_RE.match(tok.value).group(1, 3)
            if not label: label = dest
            ret = apply_func(env.wiki_link, (dest, label), env)
            body += squirrel(nuts, ret)

        else:
            raise Exception('Unknown token returned by parser ' + tok.type)

    # Evaluate Markdown while ◊'s are still squirreled.
    if not raw:
        body = eval_text(env, body, tight)

    # Substitute the evaluated ◊'s for the squirreled placeholders.
    for k, v in nuts.items():
        body = body.replace(k, v)

    return body


def render(env, page_filename, template_filename, out_filename):
    try:
        # Add the global dict to the context, to keep simple projects simple.
        env.__dict__.update(sys.modules['__main__'].__dict__)

        # Evaluate the page markup and put it in the context.
        raw_text = Path(page_filename).read_text()
        env.filename = page_filename.split('.')[0]
        env.body = eval_page(raw_text, env)

        # Evaluate the template in the completed context.
        template = Path(template_filename).read_text()
        out = eval_page(template, env, raw=True)

        Path(out_filename).write_text(out)

    except SuppressPageGenerationException:
        # The page can cancel its own production.
        pass
