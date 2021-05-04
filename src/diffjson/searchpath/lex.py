import ply.lex


tokens = [
    'VALUE',
    'DSLASH',
    'SLASH',
    'NODENAMEASTERISK',
    'NODENAMEPARENT',
    'NODENAMESELF',
    'NODENAMEINDEX',
    'NODENAMEKEY',
]

literals = ['[', ']', '=', ',']
t_VALUE = '(\'[^\']+\')|(\"[^\"]+\")'
t_DSLASH = '//'
t_SLASH = '/'
t_NODENAMEASTERISK = '\\*'
t_NODENAMEPARENT = '\\.\\.'
t_NODENAMESELF = '\\.'
t_NODENAMEKEY = '[-_@\\w][-_@\\.\\w]*'
t_NODENAMEINDEX = '\\[[0-9]+\\]'


def t_error(t):
    raise Exception('Parse error, {}', t)


lexer = ply.lex.lex()
