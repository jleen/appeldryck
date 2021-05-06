import re
import sys

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
    # TODO: Are lazy semantics actually what we want?
    ret = sys.modules['__main__'].__dict__[fn](arg)
    return eval_page(ret, env)['body']
    # TODO: What to do if meta variables get returned?


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


def eval_text(text):
    # For now, just directly convert Markdown to HTML.
    # TODO: Convert to Appeldryck and execute tag functions.
    return marko.convert(text)


def eval_page(text, env):
    parsed = { 'body': '' }
    tokens = parser.tokenize(text)
    while True:
        try:
            tok = tokens.__next__()
        except StopIteration:
            break

        if tok.type == 'TEXT':
            parsed['body'] += eval_text(tok.value)
        elif tok.type == 'VAR':
            v = VAR_RE.match(tok.value).group(1)
            parsed['body'] += env[v]
        elif tok.type == 'META':
            (k, v) = META_RE.match(tok.value).group(1, 2)
            parsed[k] = v
        elif tok.type == 'FUNC_OPEN':
            fn = FUNC_RE.match(tok.value).group(1)
            arg = combine_until_close(tokens)
            parsed['body'] += apply_func(fn, arg, env)
        elif tok.type == 'EVAL_OPEN':
            exp = combine_until_close(tokens)
            parsed['body'] += eval(exp, { 'refs': {'foo': 'bar'}})
        elif tok.type == 'BRACE_OPEN':
            inner = combine_until_close(tokens)
            parsed['body'] += '{' + inner + '}'
        elif tok.type == 'BRACE_CLOSE':
            # Just in case we get a mismatched close paren. Harmless.
            parsed['body'] += tok.value

    return parsed


def render_page(template, env):
    page = eval_page(template, env)
    # TODO: What to do if meta variables get returned?
    return page


def dryck(page_filename, template_filename, out_filename):
    page = read_page(page_filename)
    template = read_file(template_filename)
    evaluated = render_page(template, page)
    print(evaluated['body'])
