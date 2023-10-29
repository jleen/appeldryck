from .ply import lex

tokens = ('FUNC', 'STAR', 'LBRACE', 'RBRACE', 'NEWLINE', 'TEXT')

def t_FUNC(t):
    r'◊\w*'
    return t

def t_STAR(t):
    r'\*'
    return t

def t_LBRACE(t):
    r'{'
    return t

def t_RBRACE(t):
    r'}'
    return t

def t_NEWLINE(t):
    r'\n'
    t.lexer.lineno += 1
    return t

def t_TEXT(t):
    r'[^!\n]+'
    return t

def t_error(t):
    raise Exception(f'Unable to tokenize on line {t.lexer.lineno} at: {t.value[:20].splitlines()[0]}')

lexer = lex.lex()
