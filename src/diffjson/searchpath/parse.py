import ply.yacc
from .lex import tokens
from .pathtypes import *


def parse(pathstring, debug=False):
    p = ply.yacc.yacc(debug=debug, write_tables=False)
    return p.parse(pathstring, debug=debug)


# Location Path
def p_locationpath_separatorhonly(p):
    """locationpath : separator"""
    p[0] = LocationPath([LocationStep(NodenameRoot())] + p[1])


def p_locationpath_separator(p):
    """locationpath : separator locationsteps"""
    p[0] = LocationPath([LocationStep(NodenameRoot())] + p[1] + p[2])


def p_locationpath_forpredicates(p):
    """locationpath : locationsteps"""
    p[0] = LocationPath(p[1])


def p_locationpath_endwithdslash(p):
    """locationpath : locationsteps separator"""
    p[0] = LocationPath(p[1] + p[2])


# Separator
def p_separator_slash(p):
    """separator : SLASH"""
    p[0] = []


def p_separator_dslash(p):
    """separator : DSLASH
                 | DSLASH '[' predicates ']' separator"""
    if len(p) == 2:
        p[0] = [LocationStep(NodenameDescendant())]
    elif len(p) == 6:
        p[0] = [LocationStep(NodenameDescendant(), p[3])] + p[5]


# Location Steps
def p_locationsteps_single(p):
    """locationsteps : locationstep"""
    p[0] = [p[1]]


def p_locationsteps_separator(p):
    """locationsteps : locationsteps separator locationstep"""
    p[0] = p[1] + p[2] + [p[3]]


def p_locationsteps_indexlocationstep(p):
    """locationsteps : locationsteps indexlocationstep"""
    # For /hoge[1][1]
    p[0] = p[1] + [p[2]]


# Location Step
def p_locationstep_nodename(p):
    """locationstep : nodename"""
    p[0] = p[1]


def p_locationstep_nodenamewithpredicates(p):
    """locationstep : nodename '[' predicates ']'"""
    p[1].set_predicates(p[3])
    p[0] = p[1]


def p_locationstep_indexlocationstep(p):
    """locationstep : indexlocationstep"""
    p[0] = p[1]


# Locations Steps for Index ex.) /hoge[0][1]
def p_indexlocationstep_index(p):
    """indexlocationstep : nodenameindex"""
    p[0] = p[1]


def p_indexlocationstep_indexwithpredicates(p):
    """indexlocationstep : nodenameindex '[' predicates ']'"""
    p[1].set_predicates(p[3])
    p[0] = p[1]


# Nodename and Predicates
def p_nodename_nodenameasterisk(p):
    """nodename : NODENAMEASTERISK"""
    p[0] = LocationStep(NodenameAsterisk())


def p_nodename_nodenameparent(p):
    """nodename : NODENAMEPARENT"""
    p[0] = LocationStep(NodenameParent())


def p_nodename_nodenameself(p):
    """nodename : NODENAMESELF"""
    p[0] = LocationStep(NodenameSelf())


def p_nodename_nodenamekey(p):
    """nodename : NODENAMEKEY"""
    p[0] = LocationStep(NodenameKey(p[1]))


def p_nodenameindex(p):
    """nodenameindex : NODENAMEINDEX"""
    p[0] = LocationStep(NodenameIndex(p[1][1:-1]))


def p_predicates(p):
    """predicates : predicate
            | predicate ',' predicates"""
    if len(p) == 2:
        p[0] = Predicates([p[1]])
    elif len(p) == 4:
        p[0] = Predicates([p[1]]) + p[3]


def p_predicate(p):
    """predicate : locationpath '=' VALUE"""
    p[0] = Predicate(p[1], p[3][1:-1])


# Error
def p_error(p):
    raise Exception('YACC parse error, {}'.format(p))
