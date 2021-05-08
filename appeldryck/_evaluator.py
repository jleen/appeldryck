import re
import sys
import uuid

import marko

from . import _parser as parser


class SuppressPageGenerationException(Exception):
    pass


def read_file(filename):
    with open(filename) as f:
        text = f.read()
        return text


def write_file(filename, text):
    with open(filename, 'w') as f:
        f.write(text)


def read_page(filename, env):
    raw_text = read_file(filename)
    env.filename = filename.split('.')[0]
    env.body = eval_page(raw_text, env)


VAR_RE  = re.compile(r'◊(.+)')
META_RE = re.compile(r'◊(.+?):\s*(.*)')
FUNC_RE = re.compile(r'◊(.+?){')
WIKI_RE = re.compile(r'\[\[(.+?)(\|(.*))?]]')


def apply_func(fn, args, env, eval_args=True):
    # TODO: What to do if meta variables get returned?
    if eval_args:
        parsed_args = [eval_page(arg, env, tight=True) for arg in args]
    else:
        parsed_args = args
    ret = fn(*parsed_args)
    return ret


def base_env():
    return sys.modules['__main__'].__dict__


def combine_until_close(tokens):
    depth = 1
    out = ''
    while depth > 0:
        tok = tokens.__next__()
        if tok.type in ['FUNC_OPEN', 'EVAL_OPEN', 'BRACE_OPEN']:
            depth += 1
        elif tok.type == 'BRACE_CLOSE':
            depth -= 1
        if depth > 0:
            out += tok.value
    return out


class DryckHtmlRenderer(marko.HTMLRenderer):
    pass


markdown = marko.Markdown(renderer=DryckHtmlRenderer)


def eval_arg(text):
    pass


def eval_text(text, tight):
    # For now, just directly convert Markdown to HTML.
    # TODO: Convert to Appeldryck and execute tag functions.
    parsed = markdown.parse(text)
    if tight:
        for child in parsed.children:
            child._tight = True
    return markdown.render(parsed)


def gensym():
    return str(uuid.uuid4())


def squirrel(nuts, nut):
    k = gensym()
    nuts[k] = nut
    return k


def eval_page(text, env, raw=False, tight=False) -> str:
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
            inner = combine_until_close(tokens)
            body += '{' + inner + '}'

        elif tok.type == 'BRACE_CLOSE':
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
            env.suppress = 'suppress'
            env.br = 'br'
            v = VAR_RE.match(tok.value).group(1)
            val = getattr(env, v)
            if callable(val):
                body += squirrel(nuts, apply_func(val, (), env))
            else:
                body += squirrel(nuts, val)

        elif tok.type == 'FUNC_OPEN':
            fn = FUNC_RE.match(tok.value).group(1)
            arg = combine_until_close(tokens)
            body += squirrel(nuts, apply_func(getattr(env, fn), (arg,), env))

        elif tok.type == 'EVAL_OPEN':
            exp = combine_until_close(tokens)
            env.refs = {'foo': 'bar'}
            body += squirrel(nuts, eval(exp, env.__dict__))

        elif tok.type == 'WIKI_LINK':
            # [[link|label]] serves as a syntactic sugar for calling ◊link.
            (dest, label) = WIKI_RE.match(tok.value).group(1, 3)
            if not label:
                label = dest
            body += squirrel(nuts,
                             apply_func(env.wiki_link, (dest, label), env,
                                        eval_args=False))

        else:
            raise Exception('Unknown token returned by parser ' + tok.type)

    # Evaluate Markdown while ◊'s are still squirreled.
    if not raw:
        body = eval_text(body, tight)

    # Substitute the evaluated ◊'s for the squirreled placeholders.
    for k, v in nuts.items():
        body = body.replace(k, v)

    return body


def render_page(template, env):
    return eval_page(template, env, raw=True)


def render(env, page_filename, template_filename, out_filename):
    env.__dict__.update(base_env())
    read_page(page_filename, env)
    template = read_file(template_filename)
    out = render_page(template, env)
    write_file(out_filename, out)
