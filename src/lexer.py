# from ply.lex import lex

# reserved keywords
reserved = {
    "void": "VOID",
    "char": "CHAR",
    "int": "INT",
    "float": "FLOAT",
    "double": "DOUBLE",
    "string": "STRING",
    "bool": "BOOL",
    "NULL": "NULL",
    "true": "TRUE",
    "false": "FALSE",
    "include": "INCLUDE",
    "define": "DEFINE",
    "main": "MAIN",
    "if": "IF",
    "else": "ELSE",
    "return": "RETURN",
    "for": "FOR",
    "while": "WHILE",
    "continue": "CONTINUE",
    "goto": "GOTO",
    "break": "BREAK",
    "input": "INPUT",
    "output": "OUTPUT",
    "struct": "STRUCT",
    "class": "CLASS",
    "public": "PUBLIC",
    "private": "PRIVATE",
    "this": "THIS",
    "sizeof": "SIZEOF",
    "open": "OPEN",
    "read": "READ",
    "write": "WRITE",
    "sin": "SIN",
    "cos": "COS",
    "tan": "TAN",
    "sqrt": "SQUARE_ROOT",
    "strcpy": "STRING_COPY",
    "strrev": "STRING_REVERSE",
    "strlen": "STRING_LENGTH",
    "strcmp": "STRING_COMPARE",
    "assert": "ASSERT"
}

# list of tokens
tokens = list(reserved.values()) + [
    "MULTILINE_COMMENT",
    "UNSIGNED_INT",
    "LONG_LONG_INT",
    # "ELSE_IF",
    "DECIMAL_NUMBER",
    "NUMBER",
    "STRING_LITERAL",
    "CHARACTER",
    "RIGHT_SHIFT_EQUALS",
    "LEFT_SHIFT_EQUALS",
    "PLUS_PLUS",
    "MINUS_MINUS",
    "DIVIDE_EQUALS",
    "MULTIPLY_EQUALS",
    "PLUS_EQUALS",
    "MINUS_EQUALS",
    "MODULUS_EQUALS",
    "AND_EQUALS",
    "OR_EQUALS",
    "XOR_EQUALS",
    "RIGHT_SHIFT",
    "LEFT_SHIFT",
    "LESS_THAN_EQUALS",
    "GREATER_THAN_EQUALS",
    "AND_AND",
    "OR_OR",
    "SCOPE_RESOLUTION",
    "ARROW",
    "NOT_EQUALS",
    "EQUALS_EQUALS",
    "PLUS",
    "MINUS",
    "STAR",
    "DIVIDE",
    "MODULUS",
    "LESS_THAN",
    "GREATER_THAN",
    "AND",
    "OR",
    "NOT",
    "EQUALS",
    "COMMA",
    "DOT",
    "HASH",
    "XOR",
    "QUESTION_MARK",
    "RIGHT_SQUARE_BRACKET",
    "LEFT_SQUARE_BRACKET",
    "RIGHT_PARENTHESIS",
    "LEFT_PARENTHESIS",
    "RIGHT_CURLY_BRACKET",
    "LEFT_CURLY_BRACKET",
    "SEMICOLON",
    "COLON",
    "TILDE",
    "IDENTIFIER",
]

t_ignore_SINGLE_LINE_COMMENT = r"//(.*)"
t_ignore_TABSPACE = r"[ \t]"

t_RIGHT_SHIFT_EQUALS = r">>="
t_LEFT_SHIFT_EQUALS = r"<<="

t_PLUS_PLUS = r"\+\+"
t_MINUS_MINUS = r"--"
t_DIVIDE_EQUALS = r"\/="
t_MULTIPLY_EQUALS = r"\*="
t_PLUS_EQUALS = r"\+="
t_MINUS_EQUALS = r"-="
t_MODULUS_EQUALS = r"%="
t_AND_EQUALS = "&="
t_OR_EQUALS = r"\|="
t_XOR_EQUALS = r"\^="
t_RIGHT_SHIFT = r">>"
t_LEFT_SHIFT = r"<<"
t_LESS_THAN_EQUALS = r"<="
t_GREATER_THAN_EQUALS = r">="
t_EQUALS_EQUALS = r"=="
t_ARROW = r"->"
t_SCOPE_RESOLUTION = "\:\:"
t_NOT_EQUALS = r"!="
t_AND_AND = r"&&"
t_OR_OR = r"\|\|"

t_PLUS = r"\+"
t_MINUS = r"-"
t_STAR = r"\*"
t_DIVIDE = r"/"
t_MODULUS = r"%"
t_LESS_THAN = r"<"
t_GREATER_THAN = r">"
t_AND = r"&"
t_OR = r"\|"
t_NOT = r"!"
t_TILDE = r"\~"
t_EQUALS = r"="
t_COMMA = r","
t_DOT = r"\."
t_HASH = r"\#"
t_XOR = "\^"
t_QUESTION_MARK = r"\?"

t_LEFT_SQUARE_BRACKET = r"\["
t_RIGHT_SQUARE_BRACKET = r"\]"
t_LEFT_CURLY_BRACKET = r"{"
t_RIGHT_CURLY_BRACKET = r"}"
t_RIGHT_PARENTHESIS = r"\)"
t_LEFT_PARENTHESIS = r"\("
t_SEMICOLON = r";"
t_COLON = r":"


def t_MULTILINE_COMMENT(t):
    r"\/\*(.|\n)*\*\/"
    t.lexer.lineno += len(t.value.split("\n")) - 1
    pass


def t_DECIMAL_NUMBER(t):
    r"\d+(\.\d+)((e|E)(\+|-)?\d+)?"
    t.value = float(t.value)
    return t


def t_NUMBER(t):
    r"\d+"
    t.value = int(t.value)
    return t


def t_STRING_LITERAL(t):
    r'("[^"]+")'
    t.type = "STRING_LITERAL"
    return t


def t_CHARACTER(t):
    r"\'.\'"
    t.type = "CHARACTER"
    return t


def t_UNSIGNED_INT(t):
    r"unsigned[ ]int"
    return t


def t_LONG_LONG_INT(t):
    r"long[ ]long[ ]int"
    return t


# def t_ELSE_IF(t):
#     r"else[ ]if"
#     return t


def t_IDENTIFIER(t):
    r"[a-zA-Z_][a-zA-Z0-9_]*"
    t.type = reserved.get(t.value, "IDENTIFIER")
    return t


def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


def t_error(t):
    print(f"Illegal Character found: {t.value[0]} at line {t.lineno}")
    t.lexer.skip(1)
