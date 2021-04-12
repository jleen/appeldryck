from .ply import lex

# TODO
tokens = ('X',)


def t_FUNC(t):
    r'◊\w+{(.|\n)+?}}'
    return t


def t_META(t):
    r'◊\w+\s*:\s*.*\n'
    return t


def t_VAR(t):
    r'◊\w+'
    return t


def t_EVAL(t):
    r'◊{([^◊]|\n)+}◊'
    # TODO: Would be nice to somehow match braces inside the Python
    # so we don't need the terminal lozenge.
    return t


def t_TEXT(t):
    r'([^◊]|\n)+'
    return t


def t_error(t):
    # TODO
    raise Exception('Uh oh: ' + str(t))


lexer = lex.lex()


def tokenize(text):
    lexer.input(text)
    while True:
        token = lexer.token()
        if not token:
            break
        yield token
