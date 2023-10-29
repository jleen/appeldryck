import importlib
import pprint
import sys

from .lex import lexer
from .parse import parser

def lex(text):
    reload()
    lexer.input(text)
    while True:
        t = lexer.token()
        if not t:
            break
        print(t)

def parse(text):
    reload()
    parse_internal(text)

def parse_internal(text):
    p = parser.parse(text)
    pprint.pp(p)

def reload():
    importlib.reload(sys.modules['parser.lex'])
    importlib.reload(sys.modules['parser.parse'])
    importlib.reload(sys.modules['parser.test'])


if __name__ == "__main__":
    parse_internal(open(sys.argv[1], mode='r').read())
