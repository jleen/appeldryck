import re
import sys
import uuid

import marko

from . import parser


class SuppressPageGenerationException(Exception):
    pass


def read_file(filename):
    with open(filename) as f:
        text = f.read()
        return text


def write_file(filename, text):
    with open(filename, 'w') as f:
        f.write(text)


def read_page(filename):
    raw_text = read_file(filename)
    page = parse_page(raw_text)
    page['filename'] = filename.split('.')[0]
    return page


VAR_RE  = re.compile(r'◊(.+)')
META_RE = re.compile(r'◊(.+?):\s*(.*)')
FUNC_RE = re.compile(r'◊(.+?){')


def apply_func(fn, arg, env):
    # TODO: What to do if meta variables get returned?
    parsed_arg = eval_page(arg, env, tight=True)['body']
    ret = sys.modules['__main__'].__dict__[fn](parsed_arg)
    return ret


def parse_page(text):
    return eval_page(text, [])


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
    print([type(c) for c in parsed.children])
    print(markdown.render(parsed))
    print('---')
    return markdown.render(parsed)


def gensym():
    return str(uuid.uuid4())


def squirrel(nuts, nut):
    k = gensym()
    nuts[k] = nut
    return k


def eval_page(text, env, raw=False, tight=False):
    parsed = {}
    body = ''
    nuts = {}

    tokens = parser.tokenize(text)

    while True:
        try:
            tok = tokens.__next__()
        except StopIteration:
            break

        if tok.type == 'TEXT':
            body += tok.value

        elif tok.type == 'VAR':
            v = VAR_RE.match(tok.value).group(1)
            body += squirrel(nuts, env[v])

        elif tok.type == 'META':
            (k, v) = META_RE.match(tok.value).group(1, 2)
            parsed[k] = v

        elif tok.type == 'FUNC_OPEN':
            fn = FUNC_RE.match(tok.value).group(1)
            arg = combine_until_close(tokens)
            body += squirrel(nuts, apply_func(fn, arg, env))

        elif tok.type == 'EVAL_OPEN':
            exp = combine_until_close(tokens)
            body += squirrel(nuts,
                                       eval(exp, { 'refs': {'foo': 'bar'}}))

        elif tok.type == 'BRACE_OPEN':
            inner = combine_until_close(tokens)
            body += '{' + inner + '}'

        elif tok.type == 'BRACE_CLOSE':
            # Just in case we get a mismatched close paren. Harmless.
            body += tok.value

    # Evaluate Markdown while ◊'s are still squirreled.
    if not raw:
        body = eval_text(body, tight)

    # Substitute the evaluated ◊'s for the squirreled placeholders.
    for k, v in nuts.items():
        body = body.replace(k, v)

    parsed['body'] = body
    return parsed


def render_page(template, env):
    page = eval_page(template, env, raw=True)
    # TODO: What to do if meta variables get returned?
    return page


def dryck(page_filename, template_filename, out_filename):
    page = read_page(page_filename)
    template = read_file(template_filename)
    evaluated = render_page(template, page)
    print(evaluated['body'])
