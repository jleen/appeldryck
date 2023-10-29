import importlib
import sys

from .lex import lexer

def lex(text):
    reload()
    lexer.input(text)
    while True:
        t = lexer.token()
        if not t:
            break
        print(t)

def reload():
    importlib.reload(sys.modules['parser.lex'])
    importlib.reload(sys.modules['parser.test'])
