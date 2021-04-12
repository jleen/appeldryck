import re
import sys

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
FUNC_RE = re.compile(r'◊(.+?){\n?((.|\n)+)\n?}', re.MULTILINE)
EVAL_RE = re.compile(r'◊{(.+)}◊', re.MULTILINE)


def apply_func(fn, arg, env):
    # TODO: Are lazy semantics actually what we want?
    ret = sys.modules['__main__'].__dict__[fn](arg)
    return eval_page(ret, env)['body']
    # TODO: What to do if meta variables get returned?


def parse_page(text):
    return eval_page(text, [])


def eval_page(text, env):
    parsed = { 'body': '' }
    for tok in parser.tokenize(text):
        if tok.type == 'TEXT':
            parsed['body'] += tok.value
        elif tok.type == 'VAR':
            v = VAR_RE.match(tok.value).group(1)
            parsed['body'] += env[v]
        elif tok.type == 'META':
            (k, v) = META_RE.match(tok.value).group(1, 2)
            parsed[k] = v
        elif tok.type == 'FUNC':
            (fn, arg) = FUNC_RE.match(tok.value).group(1, 2)
            parsed['body'] += apply_func(fn, arg, env)
        elif tok.type == 'EVAL':
            exp = EVAL_RE.match(tok.value).group(1)
            parsed['body'] += eval(exp, { 'refs': {'foo': 'bar'}})
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
