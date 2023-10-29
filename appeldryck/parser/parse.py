from .ply import yacc

from .lex import tokens


#
# Document structure.
#

def p_document_list(p):
    'document : element document'
    p[0] = [p[1]] + p[2]

def p_document_empty(p):
    'document : empty'
    p[0] = []

def p_element(p):
    '''element : metadata
               | eval
               | apply
               | text'''
    p[0] = p[1]


#
# Metadata declarations.
#

def p_metadata(p):
    '''metadata : METATAG METAVAL
                | METATAG METAVAL METAEOL'''
    p[0] = ['metadata', p[1], p[2]]


#
# Expression evaluation.
#

def p_eval(p):
    'eval : EVAL arg'
    p[0] = ['eval', p[2]]

def p_arg(p):
    'arg : LBRACE ARG RBRACE'
    p[0] = p[2]

#
# Functional application.
#
def p_apply(p):
    'apply : FUNC arglist'
    p[0] = ['apply', p[1], p[2]]

def p_arglist_list(p):
    'arglist : arg arglist'
    p[0] = [p[1]] + p[2]

def p_arglist_empty(p):
    'arglist : empty'
    p[0] = []

#
# Static text.
#
def p_text(p):
    'text : runs'
    p[0] = ['text', p[1]]

def p_runs_text(p):
    '''runs : TEXT runs
            | STAR runs
            | NEWLINE runs'''
    p[0] = p[1] + p[2]

def p_runs_empty(p):
    'runs : empty'
    p[0] = ''


#
# Utilities.
#

def p_empty(p):
    'empty :'
    pass

def p_error(p):
    raise Exception('Nope')


parser = yacc.yacc()
