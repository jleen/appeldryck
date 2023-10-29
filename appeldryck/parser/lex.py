import re

from .ply import lex

tokens = ('METAEOL', 'FUNC', 'STAR', 'LBRACE', 'RBRACE', 'NEWLINE', 'TEXT')
states = (('meta', 'exclusive'),
          ('arg', 'exclusive'),
         )


#
# Metadata definitions.

# ◊metakey: metadata value<EOL>
#

def t_METATAG(t):
    r'(^|(?<=\n))◊\w*:\s*'
    t.lexer.begin('meta')
    t.value = re.match('◊(\w*):', t.value).group(1)
    return t

def t_meta_METAVAL(t):
    r'[^\n]+'
    return t

def t_meta_METAEOL(t):
    r'\n'
    t.lexer.lineno += 1
    t.lexer.begin('INITIAL')
    return t


#
# Python invocations.
#
# ◊func
# ◊func{arg}{arg}
# ◊{eval}
#

def t_FUNC(t):
    r'◊\w*'
    t.value = t.value[1:]
    return t

def t_EVAL(t):
    r'◊'
    return t

def t_INITIAL_arg_LBRACE(t):
    r'{'
    t.lexer.push_state('arg')
    return t

def t_arg_RBRACE(t):
    r'}'
    t.lexer.pop_state()
    return t

def t_arg_ARG(t):
    r'[^}]+'
    t.lexer.lineno += t.value.count('\n')
    return t


#
# Static markup.
#

def t_STAR(t):
    r'\*'
    return t

def t_NEWLINE(t):
    r'\n'
    t.lexer.lineno += 1
    return t

def t_TEXT(t):
    r'[^◊}\n]+'
    return t


#
# Errors.
#

def t_arg_error(t):
    raise Exception(f'Unable to tokenize on line {t.lexer.lineno} at: {t.value[:20].splitlines()[0]}')

def t_meta_error(t):
    raise Exception(f'Unable to tokenize on line {t.lexer.lineno} at: {t.value[:20].splitlines()[0]}')

def t_error(t):
    raise Exception(f'Unable to tokenize on line {t.lexer.lineno} at: {t.value[:20].splitlines()[0]}')


lexer = lex.lex()
