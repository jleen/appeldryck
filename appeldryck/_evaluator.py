import inspect
import os
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


def apply_func(fn, args, env, raw):
    # TODO: What to do if meta variables get returned?
    # Read function decorators.
    lazy = hasattr(fn, '_appeldryck_raw')
    block = hasattr(fn, '_appeldryck_block')

    if not lazy:
        parsed_args = [eval_page(arg, env, tight=(not block), raw=raw)
                       for arg in args]
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


class _DryckRenderer(marko.Renderer):
    '''Marko renderer to redirect tag rendering back to the user's functions.

    Should not be directly instantiated.
    Please call make_DryckRenderer to curry the env.

    This is about half the logic from marko.HTMLRenderer.
    The rest is in HtmlContext.
    '''

    def apply_wrap(self, fn, element, *args, slot=0):
        lazy = hasattr(fn, '_appeldryck_raw')
        block = hasattr(fn, '_appeldryck_block')
        if lazy:
            raise Exception(f'Markdown handler {fn} cannot be lazy')
        if block:
            raise Exception(f'Markdown handler {fn} cannot be block')

        if element:
            children = self.render_children(element)
            full_args = list(args)
            full_args[slot:slot] = [children]
            ret = fn(*full_args)
        else:
            ret = fn(*args)

        if not isinstance(ret, str):
            raise Exception(f'Expected {fn} to return str, but got {ret}')
        return ret

    def render_heading(self, element):
        return self.apply_wrap(self.env.heading,
                               element, element.level, slot=1)

    def render_paragraph(self, element):
        if element._tight:
            return self.render_children(element)
        else:
            return self.apply_wrap(self.env.p, element)

    def render_list(self, element):
        if element.ordered:
            start = element.start if element.start != 1 else None
            return self.apply_wrap(self.env.ol, element, start)
        else:
            return self.apply_wrap(self.env.ul, element)

    def render_list_item(self, element):
        return self.apply_wrap(self.env.li, element)

    def render_quote(self, element):
        return self.apply_wrap(self.env.blockquote, element)

    def render_fenced_code(self, element):
        raise Exception('Fenced code is not yet supported')

    def render_code_block(self, element):
        raise Exception('Code blocks are not yet supported')

    def render_thematic_break(self, element):
        return self.apply_wrap(self.env.hr, None)

    def render_emphasis(self, element):
        return self.apply_wrap(self.env.em, element)

    def render_strong_emphasis(self, element):
        return self.apply_wrap(self.env.strong, element)

    def render_html_block(self, element):
        raise Exception("Literal HTML doesn't seem like a good idea")

    def render_inline_html(self, element):
        raise Exception("Inline HTML doesn't seem like a good idea")

    def render_blank_line(self, element):
        return ''

    def render_link_ref_def(self, element):
        return ''

    def render_link(self, element):
        return self.apply_wrap(self.env.href,
                               element, element.dest, element.title, slot=1)

    def render_auto_link(self, element):
        return self.render_link(element)

    def render_image(self, element):
        raise Exception('Images are not yet supported')

    def render_raw_text(self, element):
        return self.env.escape(element.children)

    def render_line_break(self, element):
        if element.soft:
            return '\n'
        else:
            return self.apply_wrap(self.env.br, None)

    def render_code_span(self, element):
        raise Exception('Code spans are not yet supported')


def make_DryckRenderer(the_env):
    class DryckRenderer(_DryckRenderer):
        env = the_env
    return DryckRenderer


def eval_text(env, text, tight):
    # TODO: Unsquirrel before calling tag functions?
    renderer = make_DryckRenderer(env)
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
            body += '{' + eval_page(inner, env, raw, tight) + '}'

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
                body += squirrel(nuts, apply_func(val, (), env, raw))
            else:
                body += squirrel(nuts, val)

        elif tok.type == 'FUNC_OPEN':
            # A ◊foo followed by one or more {expr}'s
            # is a function call with arguments.
            func_name = FUNC_RE.match(tok.value).group(1)
            fn = getattr(env, func_name)
            args = combine_until_close(tokens, multi=True)
            ret = apply_func(fn, args, env, raw)
            # Squirrel the function's return value
            # so that it doesn't get evaluated as Markdown later.
            body += squirrel(nuts, ret)

        elif tok.type == 'EVAL_OPEN':
            # A ◊{foo} just evaluates foo.
            [exp] = combine_until_close(tokens)
            methods = {x: getattr(env, x) for x in dir(env)
                       if inspect.ismethod(getattr(env, x))}
            methods['__context__'] = env
            ret = eval(exp.rstrip(), env.__dict__, methods)
            if not isinstance(ret, str):
                raise Exception(f'Expected eval to return str, but got {ret}')
            body += squirrel(nuts, ret)

        elif tok.type == 'WIKI_LINK':
            # [[link|label]] serves as a syntactic sugar for calling ◊link.
            (dest, label) = WIKI_RE.match(tok.value).group(1, 3)
            if not label: label = dest
            ret = apply_func(env.wiki_link, (dest, label), env, raw)
            body += squirrel(nuts, ret)

        else:
            raise Exception('Unknown token returned by parser ' + tok.type)

    # Evaluate Markdown while ◊'s are still squirreled.
    # This is the only thing that 'raw' actually affects.
    # (It's unrelated to the @raw annotation, sigh.)
    if not raw:
        body = eval_text(env, body, tight)

    # Substitute the evaluated ◊'s for the squirreled placeholders.
    for k, v in nuts.items():
        body = body.replace(k, v)

    return body


def _render(env, filename, raw):
    try:
        # Evaluate the page markup and put it in the context.
        raw_text = Path(filename).read_text()
        env.body = eval_page(raw_text, env, raw)
        return env.body
    except SuppressPageGenerationException:
        # The page can cancel its own production.
        return None


def markup(env, filename):
    return _render(env, filename, False)


def preprocess(env, filename):
    return _render(env, filename, True)


def render(env, page_filename, template_filename=[], out_filename=None):
    # Add the global dict to the context, to keep simple projects simple.
    env.__dict__.update(sys.modules['__main__'].__dict__)

    if page_filename:
        # Add the page filename to the context.
        env.filename = os.path.splitext(page_filename)[0]

        if markup(env, page_filename) == None:
            return

    if not isinstance(template_filename, list):
        template_filename = [template_filename]

    for f in template_filename:
        preprocess(env, f)

    if out_filename:
        Path(out_filename).write_text(env.body)

    return env.body
