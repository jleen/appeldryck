from .ply import yacc

from .lex import tokens
from . import ast


#
# Document structure.
#

def p_document(p):
    'document : defs blanks blocks'
    if p.parser.raw and len(p[2]) > 0:
        p[0] = ast.Document(p[1], [ast.Raw([ast.Text(p[2])])] + p[3])
    else:
        p[0] = ast.Document(p[1], p[3])

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
        p[0] = [p[1], ast.Raw([ast.Text(p[2])])] + p[3]
    else:
        p[0] = [p[1]] + p[3]

def p_blocks_final(p):
    'blocks : block'
    p[0] = [p[1]]


#
# Itemized lists.
#

def p_block_itemized(p):
    'block : items'
    p[0] = ast.Itemized(p[1], ordered=False)

def p_items_list(p):
    'items : item items'
    p[0] = [p[1]] + p[2]

def p_items_base(p):
    'items : item'
    p[0] = [p[1]]

def p_item(p):
    'item : BULLET elements'
    p[0] = ast.Item(p[2])


#
# Headings.
#

def p_block_heading(p):
    'block : OCTOTHORPE elements'
    p[0] = ast.Heading(p[2], p[1].count('#'))


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
        p[0] = ast.Raw(elements)
    else:
        p[0] = ast.Paragraph(elements)

def p_elements_list(p):
    'elements : element elements'
    p[0] = p[1] + p[2]

def p_elements_empty(p):
    'elements : empty'
    p[0] = []

def p_element(p):
    '''element : starfield
               | starred'''
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
    'text : spans'
    # Recognize soft breaks at the beginning and end of a span,
    # so adjacent functions can suppress them if they elect to.
    # In the middle of a span, we can safely convert newlines to spaces.
    chars = p[1]
    if p.parser.raw:
        p[0] = [ast.Text(chars)]
    else:
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

def p_spans_text(p):
    '''spans : TEXT spans
             | LBRACKET spans
             | NEWLINE spans'''
    p[0] = p[1] + p[2]

def p_spans_empty(p):
    'spans : empty'
    p[0] = ''

def p_hardbreak(p):
    'hardbreak : HARDBREAK'
    p[0] = [ast.Break()]


#
# Starred text.
#

def p_starred(p):
    'starred : STAR starfields STAR'
    p[0] = [ast.Star(p[2])]


def p_starfields_list(p):
    'starfields : starfield starfields'
    p[0] = p[1] + p[2]

def p_starfields_base(p):
    'starfields : starfield'
    p[0] = p[1]

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
    raise Exception(f'Parse error on line {p.lineno}')


parser = yacc.yacc()
parser.raw = False
