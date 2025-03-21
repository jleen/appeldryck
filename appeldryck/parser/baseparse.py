from .ply import yacc

from .lex import tokens
from . import ast


#
# Document structure.
#

def p_document(p):
    'document : defs blanks blocks'
    if p.parser.raw and len(p[2]) > 0:
        # TODO: Ideally we should merge the spans for 2 and 3.
        p[0] = ast.Document(p.linespan(0), p.lexspan(0), p[1], [ast.Raw(p.linespan(2), p.lexspan(2), [ast.Text(p.linespan(2), p.lexspan(2), p[2])])] + p[3])
    else:
        p[0] = ast.Document(p.linespan(0), p.lexspan(0), p[1], p[3])

def p_defs_list(p):
    'defs : metadata defs'
    p[0] = [p[1]] + p[2]

def p_defs_empty(p):
    'defs : empty'
    p[0] = []

def p_blanks(p):
    '''blanks : NEWLINE blanks
              | empty'''
    p[0] = (len(p[1]) * '\n') if p[1] else ''

def p_blocks_list(p):
    'blocks : block BREAK blocks'
    if p.parser.raw:
        p[0] = [p[1], ast.Raw(p.linespan(0), p.lexspan(0), [ast.Text(p.linespan(0), p.lexspan(0), p[2])])] + p[3]
    else:
        p[0] = [p[1]] + p[3]

def p_blocks_final(p):
    'blocks : block'
    p[0] = [p[1]]


#
# Text elements.
#

def p_block_elements(p):
    'block : elements'
    # Suppress terminal soft break, so as not to annoy the programmer.
    elements = p[1]
    if len(elements) > 0 and isinstance(elements[-1], ast.Soft):
        elements = elements[:-1]
    if p.parser.raw:
        p[0] = ast.Raw(p.linespan(0), p.lexspan(0), elements)
    else:
        p[0] = ast.Paragraph(p.linespan(0), p.lexspan(0), elements)

def p_elements_list(p):
    'elements : element elements'
    p[0] = p[1] + p[2]

def p_elements_empty(p):
    'elements : empty'
    p[0] = []


#
# Metadata declarations.
#

def p_metadata(p):
    '''metadata : METATAG METAVAL
                | METATAG METAVAL METAEOL'''
    p[0] = ast.Def(p.linespan(0), p.lexspan(0), p[1], p[2])


#
# Expression evaluation.
#

def p_eval(p):
    'eval : EVAL arg'
    p[0] = [ast.Eval(p.linespan(0), p.lexspan(0), p[2])]

def p_arg(p):
    'arg : LBRACE argcomps RBRACE'
    p[0] = p[2]

def p_argcomps_list(p):
    'argcomps : argcomp argcomps'
    p[0] = p[1] + p[2]

def p_argcomps_empty(p):
    'argcomps : empty'
    p[0] = ''

def p_argcomp_flat(p):
    'argcomp : ARG'
    p[0] = p[1]

def p_argcomp_balanced(p):
    'argcomp : LBRACE argcomps RBRACE'
    p[0] = '{' + p[2] + '}'


#
# Functional application.
#

def p_apply(p):
    'apply : FUNC arglist'
    p[0] = [ast.Apply(p.linespan(0), p.lexspan(0), p[1], p[2])]

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
    p[0] = [ast.Link(p.linespan(0), p.lexspan(0), dest, label)]


#
# Static text.
#

def p_text(p):
    'text : spans'
    # Recognize soft breaks at the beginning and end of a span,
    # so adjacent functions can suppress them if they elect to.
    # In the middle of a span, we can safely convert newlines to spaces.
    chars = p[1]
    if p.parser.raw:
        p[0] = [ast.Text(p.linespan(0), p.lexspan(0), chars)]
    else:
        out = []
        if chars.startswith('\n'):
            out.append(ast.Soft(p.linespan(0), p.lexspan(0)))
            chars = chars[1:]
        if chars.endswith('\n'):
            append_soft = True
            chars = chars[:-1]
        else:
            append_soft = False
        if len(chars) > 0:
            out.append(ast.Text(p.linespan(0), p.lexspan(0), chars.replace('\n', ' ')))
        if append_soft:
            out.append(ast.Soft(p.linespan(0), p.lexspan(0)))
        p[0] = out

def p_spans_empty(p):
    'spans : empty'
    p[0] = ''

def p_hardbreak(p):
    'hardbreak : HARDBREAK'
    p[0] = [ast.Break(p.linespan(0), p.lexspan(0))]

def p_starfield(p):
    '''starfield : eval
                 | apply
                 | link
                 | hardbreak
                 | text'''
    p[0] = p[1]

#
# Utilities.
#

def p_empty(p):
    'empty :'
    pass

def p_error(p):
    raise Exception(f'Parse error on line {p.lineno}: {p}')
