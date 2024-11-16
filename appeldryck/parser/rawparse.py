from .baseparse import *


def p_element(p):
    '''element : starfield'''
    p[0] = p[1]

def p_spans_text(p):
    '''spans : TEXT spans
             | LBRACKET spans
             | NEWLINE spans
             | BREAK spans
             | BULLET spans
             | OCTOTHORPE spans
             | STAR spans'''
    p[0] = p[1] + p[2]



start = 'document'
raw_parser = yacc.yacc()
raw_parser.raw = True
