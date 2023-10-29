from .ply import yacc

from .lex import tokens


#
# Document structure.
#

def p_document(p):
    'document : defs blanks elements'
    p[0] = p[1] + p[3]
    # Suppress terminal soft break, so as not to annoy the programmer.
    if p[0][-1][0] == 'soft':
        p[0] = p[0][:-1]

def p_defs_list(p):
    'defs : metadata defs'
    p[0] = [p[1]] + p[2]

def p_defs_empty(p):
    'defs : empty'
    p[0] = []

def p_blanks(p):
    '''blanks : NEWLINE blanks
              | empty'''
    pass

def p_elements_list(p):
    'elements : element elements'
    p[0] = p[1] + p[2]

def p_elements_empty(p):
    'elements : empty'
    p[0] = []

def p_element(p):
    '''element : eval
               | apply
               | link
               | starred
               | text
               | break'''
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
    p[0] = [['eval', p[2]]]

def p_arg(p):
    'arg : LBRACE ARG RBRACE'
    p[0] = p[2]


#
# Functional application.
#

def p_apply(p):
    'apply : FUNC arglist'
    p[0] = [['apply', p[1], p[2]]]

def p_arglist_list(p):
    'arglist : arg arglist'
    p[0] = [p[1]] + p[2]

def p_arglist_empty(p):
    'arglist : empty'
    p[0] = []


#
# Links.
#

def p_link(p):
    'link : LINK'
    (dest, label) = p[1]
    p[0] = [['link', dest, label]]


#
# Static text.
#

def p_text(p):
    'text : runs'
    # Recognize soft breaks at the beginning and end of a run,
    # so adjacent functions can suppress them if they elect to.
    # In the middle of a run, we can safely convert newlines to spaces.
    chars = p[1]
    ast = []
    if chars.startswith('\n'):
        ast += [['soft']]
        chars = chars[1:]
    if chars.endswith('\n'):
        append_soft = True
        chars = chars[:-1]
    else:
        append_soft = False
    if len(chars) > 0:
        ast += [['text', chars.replace('\n', ' ')]]
    if append_soft:
        ast += [['soft']]
    p[0] = ast

def p_runs_text(p):
    '''runs : TEXT runs
            | NEWLINE runs'''
    p[0] = p[1] + p[2]

def p_runs_empty(p):
    'runs : empty'
    p[0] = ''

def p_starred(p):
    'starred : STAR runs STAR'
    p[0] = [['starred', p[2]]]

def p_break(p):
    'break : BREAK'
    p[0] = [['break']]


#
# Utilities.
#

def p_empty(p):
    'empty :'
    pass

def p_error(p):
    raise Exception('Nope')


parser = yacc.yacc()
