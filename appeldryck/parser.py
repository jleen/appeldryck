from ply import lex

class Lexer():
    # TODO
    tokens = ('FUNC_OPEN',
              'META',
              'VAR',
              'EVAL_OPEN',
              'BRACE_OPEN',
              'BRACE_CLOSE',
              'TEXT')


    def t_FUNC_OPEN(self, t):
        r'◊\w+{'
        return t


    def t_META(self, t):
        r'◊\w+\s*:\s*.*\n'
        return t


    def t_VAR(self, t):
        r'◊\w+'
        return t


    def t_EVAL_OPEN(self, t):
        r'◊{'
        return t


    def t_BRACE_OPEN(self, t):
        r'{'
        return t


    def t_BRACE_CLOSE(self, t):
        r'}'
        return t


    def t_TEXT(self, t):
        r'([^◊{}]|\n)+'
        return t


    def t_error(self, t):
        # TODO
        raise Exception('Uh oh: ' + str(t))


    def lexer(self):
        return lex.lex(module=self)


def tokenize(text):
    lexer = Lexer().lexer()
    lexer.input(text)
    while True:
        token = lexer.token()
        if not token:
            break
        yield token
