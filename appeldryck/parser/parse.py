from .ply import yacc

from .lex import tokens
from . import ast


#
# Document structure.
#

def p_document(p):
    'document : defs blanks elements'
    defs = p[1]
    elements = p[3]
    p[0] = p[1] + p[3]
    # Suppress terminal soft break, so as not to annoy the programmer.
    if len(elements) > 0 and isinstance(elements[-1], ast.Soft):
        elements = elements[:-1]
    p[0] = ast.Document(defs, make_paragraphs(elements))

def make_paragraphs(elements):
    out = []
    block = []
    for element in elements:
        if isinstance(element, ast.Break):
            out.append(ast.Paragraph(block))
            block = []
        else:
            block.append(element)
    if len(block) > 0:
        out.append(ast.Paragraph(block))
    return out

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
    p[0] = ast.Def(p[1], p[2])


#
# Expression evaluation.
#

def p_eval(p):
    'eval : EVAL arg'
    p[0] = [ast.Eval(p[2])]

def p_arg(p):
    'arg : LBRACE ARG RBRACE'
    p[0] = p[2]


#
# Functional application.
#

def p_apply(p):
    'apply : FUNC arglist'
    p[0] = [ast.Apply(p[1], p[2])]

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
    p[0] = [ast.Link(dest, label)]


#
# Static text.
#

def p_text(p):
    'text : runs'
    # Recognize soft breaks at the beginning and end of a run,
    # so adjacent functions can suppress them if they elect to.
    # In the middle of a run, we can safely convert newlines to spaces.
    chars = p[1]
    out = []
    if chars.startswith('\n'):
        out.append(ast.Soft())
        chars = chars[1:]
    if chars.endswith('\n'):
        append_soft = True
        chars = chars[:-1]
    else:
        append_soft = False
    if len(chars) > 0:
        out.append(ast.Text(chars.replace('\n', ' ')))
    if append_soft:
        out.append(ast.Soft())
    p[0] = out

def p_runs_text(p):
    '''runs : TEXT runs
            | NEWLINE runs'''
    p[0] = p[1] + p[2]

def p_runs_empty(p):
    'runs : empty'
    p[0] = ''

def p_starred(p):
    'starred : STAR runs STAR'
    p[0] = [ast.Starred(p[2])]

def p_break(p):
    'break : BREAK'
    p[0] = [ast.Break()]


#
# Utilities.
#

def p_empty(p):
    'empty :'
    pass

def p_error(p):
    raise Exception('Nope')


parser = yacc.yacc()
