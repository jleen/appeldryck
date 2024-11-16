from .baseparse import *


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

def p_element(p):
    '''element : starfield
               | starred'''
    p[0] = p[1]

def p_spans_text(p):
    '''spans : TEXT spans
             | LBRACKET spans
             | NEWLINE spans'''
    p[0] = p[1] + p[2]


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


start = 'document'
parser = yacc.yacc()
parser.raw = False
