from ply import lex

# TODO: This almost certainly isn't quite right.
# We probably misreport an error early in the block
# at the line number of the end of the block.
def track_lines(t):
    t.lexer.lineno += t.value.count('\n')


# From https://ply.readthedocs.io/en/latest/ply.html#error-handling 
def find_column(input, token):
    line_start = input.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1
    

class Lexer():
    # TODO
    tokens = ('FUNC_OPEN',
              'META',
              'VAR',
              'EVAL_OPEN',
              'WIKI_LINK',
              'BRACE_OPEN',
              'BRACE_CLOSE',
              'BRACE_CLOSE_OPEN',
              'TEXT')


    def t_FUNC_OPEN(self, t):
        r'◊\w+{'
        return t


    def t_META(self, t):
        r'◊\w+\s*:\s*.*\n'
        track_lines(t)
        return t


    def t_VAR(self, t):
        r'◊\w+'
        return t


    def t_WIKI_LINK(self, t):
        r'\[\[.*?\]\](?!])'
        return t


    def t_EVAL_OPEN(self, t):
        r'◊{'
        return t


    def t_BRACE_CLOSE_OPEN(self, t):
        r'}(\n\s*)?{'
        track_lines(t)
        return t


    def t_BRACE_OPEN(self, t):
        r'{'
        return t


    def t_BRACE_CLOSE(self, t):
        r'}'
        return t


    def t_TEXT(self, t):
        r'(\[?[^[◊{}]|\n)+'
        track_lines(t)
        return t


    def t_error(self, t):
        # TODO
        raise Exception('Somehow, a parse error: ' + str(t))


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
