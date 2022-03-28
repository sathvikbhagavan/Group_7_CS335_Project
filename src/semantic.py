from typing import List, Union, TypeVar
import pydot
import csv
import pandas as pd
import pydot
from lexer import *
from ply.lex import lex
from ply.yacc import yacc, NullLogger
import argparse
import string


precedence = (
    ("nonassoc", "IF"),
    ("nonassoc", "ELSE"),
)

# ------------------------ ------------------------
# ------------------------ ------------------------
# PARSER GRAMMAR
# ------------------------ ------------------------
# ------------------------ ------------------------


def p_start(p):
    """
    start : translation_unit
    """
    p[0] = cppStart(p[1])


def p_error(p):
    print(f"Error at token: {p.value}")


def p_predefined_functions(p):
    """
    predefined_functions : INPUT
                        | OUTPUT
                        | SQUARE_ROOT
                        | SIN
                        | COS
                        | TAN
                        | STRING_COPY
                        | STRING_REVERSE
                        | STRING_LENGTH
                        | STRING_COMPARE
                        | WRITE
                        | READ
                        | OPEN
    """

    if p[1] in [
        "INPUT",
        "OUTPUT",
        "READ",
        "WRITE",
        "OPEN",
        "SIN",
        "COS",
        "TAN",
        "SQUARE_ROOT",
    ]:
        result = cppPredefFunc(p[1].lower())
    elif p[1] == "STRING_COPY":
        result = cppPredefFunc("strcpy")
    elif p[1] == "STRING_REVERSE":
        result = cppPredefFunc("strev")
    elif p[1] == "STRING_LENGTH":
        result = cppPredefFunc("strlen")
    elif p[1] == "STRING_COMPARE":
        result = cppPredefFunc("strcmp")

    p[0] = ("predefined_functions", result)


def p_primary_expression(p):
    """
    primary_expression : IDENTIFIER
        | constant
        | string
        | LEFT_PARENTHESIS expression RIGHT_PARENTHESIS
        | predefined_functions
    """
    result = ""
    if (
        p[1][0] == "constant"
        or p[1][0] == "string"
        or p[1][0] == "predefined_functions"
    ):
        result = p[1][1]
    elif p[1] == "(":
        result = p[2][1]
    else:
        result = cppId(p[1])

    p[0] = ("primary_expression", result)


def p_constant(p):
    """
    constant : NUMBER
        | DECIMAL_NUMBER
        | CHARACTER
        | TRUE
        | FALSE
        | NULL
    """

    if isinstance(p[1], int):
        result = cppConst(p[1], TypeVar("int"))
    elif p[1] in range(ord("a"), ord("z") + 1) or p[1] in range(ord("A"), ord("Z") + 1):
        result = cppConst(p[1], TypeVar("char"))
    elif p[1] == "true" or p[1] == "false":
        result = cppConst(p[1], TypeVar("bool"))
    else:
        result = cppConst(p[1], TypeVar("float"))

    p[0] = ("constant", result)


def p_string(p):
    """
    string : STRING_LITERAL
    """

    result = cppConst(p[1], TypeVar("string"))

    p[0] = ("string", result)


def p_postfix_expression(p):
    """
    postfix_expression : primary_expression
                       | postfix_expression LEFT_SQUARE_BRACKET expression RIGHT_SQUARE_BRACKET
                       | postfix_expression LEFT_PARENTHESIS RIGHT_PARENTHESIS
                       | postfix_expression LEFT_PARENTHESIS argument_expression_list RIGHT_PARENTHESIS
                       | postfix_expression DOT IDENTIFIER
                       | postfix_expression ARROW IDENTIFIER
                       | postfix_expression PLUS_PLUS
                       | postfix_expression MINUS_MINUS
    """
    result = None
    if p[1][0] == "primary_expression":
        result = cppPostfixExpr(p[1][1], None)

    elif p[1][0] == "postfix_expression":

        if len(p) == 5 and p[3][0] == "expression":
            result = cppPostfixExpr(p[1][1], cppOp("arr_index"), p[3][1])

        elif len(p) == 5 and p[3][0] == "argument_expression_list":
            if p[1][1].pf_expr.name in symboltab.functions.keys():
                len_params = symboltab.functions[p[1][1].pf_expr.name][1]
                len_args = len(p[3][1])
                if len_params == len_args:
                    result = cppPostfixExpr(p[1][1], cppOp("func_call"), p[3][1])
                else:
                    print(
                        f"Function {p[1][1].pf_expr.name} expects {len_params} args, but {len_args} were given at line {driver.lexer.lineno}.\n"
                    )

            else:
                print(
                    f"Function {p[1][1].pf_expr.name} called without declaration at line {driver.lexer.lineno}.\n"
                )
        elif p[2] == "." or p[2] == "->":

            result = cppPostfixExpr(p[1][1], cppOp(p[2]), cppId(p[3]))
        else:

            result = cppPostfixExpr(p[1][1], cppOp(p[2]), None)

    p[0] = ("postfix_expression", result)


def p_argument_expression_list(p):
    """
    argument_expression_list : assignment_expression
        | argument_expression_list COMMA assignment_expression
    """
    if p[1][0] == "assignment_expression":
        result = [p[1][1]]
    else:
        result = p[1][1] + [p[3][1]]

    p[0] = ("argument_expression_list", result)


# TODO: star for multiply vs pointer
def p_unary_expression(p):
    """
    unary_expression : postfix_expression
        | PLUS_PLUS unary_expression
        | MINUS_MINUS unary_expression
        | unary_operator cast_expression
        | SIZEOF unary_expression
        | SIZEOF LEFT_PARENTHESIS type_specifier RIGHT_PARENTHESIS
    """

    if p[1][0] == "postfix_expression":
        # result = cppUnExpr(p[1][1].pf_expr, p[1][1].pf_op)
        result = p[1][1]
    elif p[2][0] == "unary_expression":
        result = cppUnExpr(p[2][1], cppOp(p[1]))
    elif p[2][0] == "cast_expression":
        result = cppUnExpr(p[2][1], p[1][1])
    # elif p[2][1] == "unary_expression":
    #     result = cppUnExpr(p[2][1], p[1])
    elif p[2] == "(":
        result = cppUnExpr(p[3][1], cppOp(p[1]))

    p[0] = ("unary_expression", result)


def p_unary_operator(p):
    """
    unary_operator : AND
                   | STAR
                   | PLUS
                   | MINUS
                   | NOT
                   | TILDE
    """

    result = cppOp(p[1])

    p[0] = ("unary_operator", result)


def p_cast_expression(p):
    """
    cast_expression : unary_expression
        | LEFT_PARENTHESIS type_specifier RIGHT_PARENTHESIS cast_expression
    """

    if p[1] == "(":
        result = cppCastExpr(p[4][1], None, p[2][1])
    else:
        result = p[1][1]

    p[0] = ("cast_expression", result)


def p_multiplicative_expression(p):
    """
    multiplicative_expression : cast_expression
        | multiplicative_expression STAR cast_expression
        | multiplicative_expression DIVIDE cast_expression
        | multiplicative_expression MODULUS cast_expression
    """

    if p[1][0] == "multiplicative_expression":
        result = cppArithExpr(p[1][1], cppOp(p[2]), p[3][1])
    else:
        result = p[1][1]

    p[0] = ("multiplicative_expression", result)


def p_additive_expression(p):
    """
    additive_expression : multiplicative_expression
        | additive_expression PLUS multiplicative_expression
        | additive_expression MINUS multiplicative_expression
    """

    if p[1][0] == "multiplicative_expression":
        result = p[1][1]
    else:
        result = cppArithExpr(p[1][1], cppOp(p[2]), p[3][1])

    p[0] = ("additive_expression", result)


def p_shift_expression(p):
    """
    shift_expression : additive_expression
        | shift_expression LEFT_SHIFT additive_expression
        | shift_expression RIGHT_SHIFT additive_expression
    """

    if p[1][0] == "additive_expression":
        result = p[1][1]
    else:
        result = cppShiftExpr(p[1][1], cppOp(p[2]), p[3][1])

    p[0] = ("shift_expression", result)


def p_relational_expression(p):
    """
    relational_expression : shift_expression
        | relational_expression LESS_THAN shift_expression
        | relational_expression GREATER_THAN shift_expression
        | relational_expression LESS_THAN_EQUALS shift_expression
        | relational_expression GREATER_THAN_EQUALS shift_expression
    """
    if p[1][0] == "shift_expression":
        result = p[1][1]
    else:
        result = cppRelationExpr(p[1][1], cppOp(p[2]), p[3][1])

    p[0] = ("relational_expression", result)


def p_equality_expression(p):
    """
    equality_expression : relational_expression
        |  equality_expression EQUALS_EQUALS relational_expression
        |  equality_expression NOT_EQUALS relational_expression
    """

    if p[1][0] == "relational_expression":
        result = p[1][1]
    else:
        result = cppRelationExpr(p[1][1], cppOp(p[2]), p[3][1])

    p[0] = ("equality_expression", result)


def p_and_expression(p):
    """
    and_expression : equality_expression
        | and_expression AND equality_expression
    """

    if p[1][0] == "equality_expression":
        result = p[1][1]
    else:
        result = cppLogicExpr(p[1][1], cppOp(p[2]), p[3][1])

    p[0] = ("and_expression", result)


def p_xor_expression(p):
    """
    xor_expression : and_expression
        | xor_expression XOR and_expression
    """
    if p[1][0] == "and_expression":
        result = p[1][1]
    else:
        result = cppLogicExpr(p[1][1], cppOp(p[2]), p[3][1])

    p[0] = ("xor_expression", result)


def p_or_expression(p):
    """
    or_expression : xor_expression
        | or_expression OR xor_expression
    """

    if p[1][0] == "xor_expression":
        result = p[1][1]
    else:
        result = cppLogicExpr(p[1][1], cppOp(p[2]), p[3][1])

    p[0] = ("or_expression", result)


def p_logical_and_expression(p):
    """
    logical_and_expression : or_expression
        | logical_and_expression AND_AND or_expression
    """
    if p[1][0] == "or_expression":
        result = p[1][1]
    else:
        result = cppLogicExpr(p[1][1], cppOp(p[2]), p[3][1])

    p[0] = ("logical_and_expression", result)


def p_logical_or_expression(p):
    """
    logical_or_expression : logical_and_expression
        | logical_or_expression OR_OR logical_and_expression
    """
    if p[1][0] == "logical_and_expression":
        result = p[1][1]
    else:
        result = cppLogicExpr(p[1][1], cppOp(p[2]), p[3][1])

    p[0] = ("logical_or_expression", result)


def p_conditional_expression(p):
    """
    conditional_expression : logical_or_expression
        |  logical_or_expression QUESTION_MARK expression COLON conditional_expression
    """
    if p[1][0] == "logical_or_expression":
        result = p[1][1]
    else:
        result = cppCondExpr(p[1][1], p[3][1], p[5][1])

    p[0] = ("conditional_expression", result)


def p_assignment_expression(p):
    """
    assignment_expression : conditional_expression
        | unary_expression assignment_operator assignment_expression

    """

    if p[1][0] == "conditional_expression":
        result = p[1][1]
    else:
        result = cppAssignExpr(cppUnExpr(p[1][1], None), p[2][1], p[3][1])

    p[0] = ("assignment_expression", result)


def p_assignment_operator(p):
    """
    assignment_operator : EQUALS
        |  DIVIDE_EQUALS
        |  MULTIPLY_EQUALS
        |  MODULUS_EQUALS
        |  PLUS_EQUALS
        |  MINUS_EQUALS
        |  LEFT_SHIFT_EQUALS
        |  RIGHT_SHIFT_EQUALS
        |  AND_EQUALS
        |  OR_EQUALS
        |  XOR_EQUALS
    """

    result = cppOp(p[1])
    p[0] = ("assignment_operator", result)


def p_expression(p):
    """
    expression : assignment_expression
        | expression COMMA assignment_expression
    """

    if p[1][0] == "assignment_expression":
        result = [p[1][1]]
    else:
        result = p[1][1] + [p[3][1]]

    p[0] = ("expression", result)


def p_declaration(p):
    """
    declaration : type_specifier SEMICOLON
                | type_specifier init_declarators_list SEMICOLON
                | class_specifier
    """

    if len(p) == 1:
        result = cppDeclaration(cppType(p[1][1].c_name), None)
    elif len(p) == 2:
        result = cppDeclaration(p[1][1], None)
    else:
        result = cppDeclaration(p[1][1], p[2][1])

    p[0] = ("declaration", result)


def p_init_declarators_list(p):
    """
    init_declarators_list : init_declarator
        | init_declarators_list COMMA init_declarator
    """

    if p[1][0] == "init_declarator":
        result = [p[1][1]]
    else:
        result = p[1][1] + [p[3][1]]

    p[0] = ("init_declarators_list", result)


def p_init_declarator(p):
    """
    init_declarator : declarator EQUALS initializer
                    | declarator

    """

    if len(p) == 2:
        result = cppInitDeclarator(p[1][1], None)
    else:
        result = cppInitDeclarator(p[1][1], p[3][1])

    p[0] = ("init_declarator", result)


def p_type_specifier(p):
    """
    type_specifier : VOID
        | CHAR
        | INT
        | FLOAT
        | DOUBLE
        | STRING
        | BOOL
        | LONG_LONG_INT
        | UNSIGNED_INT
        | struct_specifier
        | CLASS IDENTIFIER
    """

    if p[1] == "CLASS":
        result = cppType(TypeVar(f"class_{p[1]}"))
    elif p[1][0] == "struct_specifier":
        result = cppType(TypeVar(f"struct_{p[1][1].s_tag}"))
    else:
        result = cppType(p[1])

    p[0] = ("type_specifier", result)


def p_pointer(p):
    """
    pointer : STAR
            | STAR pointer
    """

    p[0] = ("pointer", None)


def p_identifier_list(p):
    """
    identifier_list : IDENTIFIER
                    | identifier_list COMMA IDENTIFIER
    """

    if len(p) == 2:
        result = [cppId(p[1])]
    else:
        result = p[1][1] + [cppId(p[3])]

    p[0] = ("identifier_list", result)


def p_specifier_list(p):
    """
    specifier_list : type_specifier specifier_list
                   | type_specifier
    """
    if len(p) == 2:
        result = [p[1][1]]
    else:
        result = [p[1][1]] + p[2][1]

    p[0] = ("specifier_list", result)


# Parameters and declarations
def p_direct_declarator(p):
    """
    direct_declarator : IDENTIFIER
                      | MAIN
                      | LEFT_PARENTHESIS declarator RIGHT_PARENTHESIS
                      | direct_declarator LEFT_SQUARE_BRACKET conditional_expression RIGHT_SQUARE_BRACKET
                      | direct_declarator LEFT_SQUARE_BRACKET RIGHT_SQUARE_BRACKET
                      | direct_declarator LEFT_PARENTHESIS parameter_list RIGHT_PARENTHESIS
                      | direct_declarator LEFT_PARENTHESIS identifier_list RIGHT_PARENTHESIS
                      | direct_declarator LEFT_PARENTHESIS RIGHT_PARENTHESIS
    """

    # result = None
    # print(len(p))
    result = cppDirectDeclarator(None, None, None, None, None, -1)
    if len(p) == 2:
        result = cppDirectDeclarator(cppId(p[1]), None, None, None, None, 1)
    elif len(p) == 4:
        if p[1] == "(":
            result = cppDirectDeclarator(p[2][1].name, None, p[2][1], None, None, 2)
        elif p[2] == "[":
            result = cppDirectDeclarator(None, p[1][1], None, None, None, 4)
        elif p[2] == "(":
            result = cppDirectDeclarator(None, p[1][1], None, None, None, 7)

    elif len(p) == 5:
        if p[3][0] == "conditional_expression":
            result = cppDirectDeclarator(None, p[1][1], None, None, p[3][1], 3)
        if p[3][0] == "parameter_list":
            result = cppDirectDeclarator(None, p[1][1], None, p[3][1], None, 7)
        if p[3][0] == "identifier_list":
            result = cppDirectDeclarator(None, p[1][1], None, p[3][1], None, 6)

    # print(result)
    p[0] = ("direct_declarator", result)


def p_declarator(p):
    """
    declarator : pointer direct_declarator
               | direct_declarator
    """

    if p[1][0] == "pointer":
        result = cppDeclarator(p[2][1].name, None, None, True)
    else:
        # result = cppDeclarator(p[1][1].name, None)
        result = cppDeclarator(p[1][1].name, p[1][1], None)

    p[0] = ("declarator", result)


def p_parameter_list(p):
    """
    parameter_list : parameter_declaration
                   | parameter_list COMMA parameter_declaration
    """

    if p[1][0] == "parameter_declaration":
        result = [p[1][1]]
    else:
        result = p[1][1] + [p[3][1]]

    p[0] = ("parameter_list", result)


def p_parameter_declaration(p):
    """
    parameter_declaration : type_specifier declarator
                          | type_specifier abstract_declarator
                          | type_specifier
    """

    if len(p) > 1:
        result = cppParamDeclaration(p[1][1], p[2][1])
    else:
        result = cppParamDeclaration(p[1][1], None)

    p[0] = ("parameter_declaration", result)


# Structs
def p_struct_specifier(p):
    """
    struct_specifier : STRUCT IDENTIFIER LEFT_CURLY_BRACKET struct_declaration_list RIGHT_CURLY_BRACKET
                     | STRUCT LEFT_CURLY_BRACKET struct_declaration_list RIGHT_CURLY_BRACKET
                     | STRUCT IDENTIFIER LEFT_CURLY_BRACKET RIGHT_CURLY_BRACKET
                     | STRUCT LEFT_CURLY_BRACKET RIGHT_CURLY_BRACKET
                     | STRUCT IDENTIFIER
    """

    if len(p) == 6:
        result = cppStruct(cppId(p[2]), cppId(p[2]), p[4][1])
    elif len(p) == 5 and p[2] == "{":
        result = cppStruct(None, None, p[3][1])
    elif (len(p) == 5 and p[3] == "{") or len(p) == 3:
        result = cppStruct(cppId(p[2]), cppId(p[2]), None)
    elif len(p) == 4:
        result = cppStruct(None, None, None)

    p[0] = ("struct_specifier", result)


def p_struct_declarator(p):
    """
    struct_declarator : declarator
                      | COLON conditional_expression
                      | declarator COLON conditional_expression
    """

    if p[1][0] == "declarator":
        result = cppStructDeclarator(p[1][1], None)
    elif p[1] == "COLON":
        result = cppStructDeclarator(None, p[2][1])
    else:
        result = cppStructDeclarator(p[1][1], p[3][1])

    p[0] = ("struct_declarator", result)


def p_struct_declarator_list(p):
    """
    struct_declarator_list : struct_declarator
                           | struct_declarator_list COMMA struct_declarator
    """

    if p[1][0] == "struct_declarator":
        result = [p[1][1]]
    else:
        result = p[1][1] + [p[3][1]]

    p[0] = ("struct_declarator_list", result)


def p_struct_declaration(p):
    """
    struct_declaration : specifier_list struct_declarator_list SEMICOLON
    """

    result = cppStructDeclaration(p[1][1], p[2][1])

    p[0] = ("struct_declaration", result)


def p_struct_declaration_list(p):
    """
    struct_declaration_list : struct_declaration
                            | struct_declaration_list struct_declaration
    """

    if p[1][0] == "struct_declaration":
        result = [p[1][1]]
    else:
        result = p[1][1] + [p[2][1]]

    p[0] = ("struct_declaration_list", result)


# TODO: what is base clause doing in the end
def p_class_head(p):
    """
    class_head : CLASS base_clause
               | CLASS
               | CLASS IDENTIFIER base_clause
               | CLASS IDENTIFIER
    """

    result = {"c_name": None, "base_clause": None}
    if len(p) > 2:
        if p[2][0] == "base_clause":
            result["base_clause"] = p[2][1]
        else:
            result["c_name"] = p[2]
            if len(p) > 3:
                result["base_clause"] = p[3][1]

    p[0] = ("class_head", result)


def p_class_specifier(p):
    """
    class_specifier : class_head LEFT_CURLY_BRACKET member_list RIGHT_CURLY_BRACKET SEMICOLON
                    | class_head LEFT_CURLY_BRACKET RIGHT_CURLY_BRACKET SEMICOLON
    """

    if p[3] == "}":
        result = cppClass(cppId(p[1][1]["c_name"]), None, p[1][1]["base_clause"])
    else:
        result = cppClass(cppId(p[1][1]["c_name"]), p[3][1], p[1][1]["base_clause"])

    p[0] = ("class_specifier", result)


def p_member_list(p):
    """
    member_list : member_access_list
                | access_list
                | member_list access_list
    """

    if p[1][0] in ["member_access_list", "access_list"]:
        result = p[1][1]
    else:
        result = p[1][1] + p[2][1]

    p[0] = ("member_list", result)


def p_member_declarator(p):
    """
    member_declarator : init_declarator
    """

    result = p[1][1]

    p[0] = ("member_declarator", result)


def p_member_declarator_list(p):
    """
    member_declarator_list : member_declarator
                           | member_declarator_list COMMA member_declarator
    """

    if len(p) > 2:
        result = [p[1][1]] + p[3][1]
    else:
        result = [p[1][1]]

    p[0] = ("member_declarator_list", result)


# TODO
def p_member_declaration(p):
    """
    member_declaration : type_specifier member_declarator_list SEMICOLON
                       | member_declarator_list SEMICOLON
                       | type_specifier SEMICOLON
                       | SEMICOLON
                       | function_definition
                       | class_specifier
    """

    if len(p) == 2:
        if p[1] == "SEMICOLON":
            result = cppMemberDeclaration(None, None, None)
        elif p[1][0] == "function_definition":
            result = cppMemberDeclaration(
                p[1][1].func_type, p[1][1].func_param_list, "func"
            )
        elif p[1][0] == "class_specifier":
            result = cppMemberDeclaration(None, None, None)

    elif len(p) == 3:
        if p[1][0] == "member_declarator_list":
            result = cppMemberDeclaration(None, p[1][1], "var")
        else:
            result = cppMemberDeclaration(p[1][1], None, "var")

    else:
        result = cppMemberDeclaration(p[1][1], p[2][1], "var")

    p[0] = ("member_declaration", result)


def p_access_list(p):
    """
    access_list : access_specifier COLON member_access_list
                | access_specifier COLON
    """

    if len(p) > 2:
        result = [p[1][1]] + p[3][1]
    else:
        result = [p[1][1]]

    p[0] = ("access_list", result)


def p_member_access_list(p):
    """
    member_access_list : member_declaration member_access_list
                       | member_declaration
    """

    if len(p) > 1:
        result = [p[1][1]] + p[2][1]
    else:
        result = [p[1][1]]

    p[0] = ("member_access_list", result)


def p_base_clause(p):
    """
    base_clause : COLON base_specifier_list
    """

    result = p[2][1]

    p[0] = ("base_clause", result)


def p_base_specifier_list(p):
    """
    base_specifier_list : base_specifier
              | base_specifier_list COMMA base_specifier
    """

    if p[1][0] == "base_specifier":
        result = [p[1][1]]
    else:
        result = p[1][1] + [p[3][1]]

    p[0] = ("base_specifier_list", result)


def p_base_specifier(p):
    """
    base_specifier : CLASS IDENTIFIER
                   | access_specifier CLASS IDENTIFIER
                   | IDENTIFIER
                   | access_specifier IDENTIFIER
    """

    if p[1] == "class":
        result = cppBaseSpec(p[2].value, None)
    elif len(p) == 2:
        result = cppBaseSpec(p[1].value, None)
    elif p[1][0] == "access_specifier":
        if p[2] == "class":
            result = cppBaseSpec(p[3].value, p[1][1])
        else:
            result = cppBaseSpec(p[2].value, p[1][1])

    p[0] = ("base_specifier", result)


def p_access_specifier(p):
    """
    access_specifier : PRIVATE
                     | PUBLIC
    """

    p[0] = ("access_specifier", p[1])


def p_abstract_declarator(p):
    """abstract_declarator : pointer
    | direct_abstract_declarator
    | pointer direct_abstract_declarator
    """

    if len(p) == 2 and p[1][0] == "direct_abstract_declarator":
        result = p[1][1]
    elif len(p) == 3:
        result = cppPointer(p[2][1].dadec_name, cppType("direct_abstract_declarator"))
    else:
        result = cppPointer(None, None)

    p[0] = ("abstract_declarator", result)


def p_direct_abstract_declarator(p):
    """
    direct_abstract_declarator : LEFT_PARENTHESIS abstract_declarator RIGHT_PARENTHESIS
                               | LEFT_SQUARE_BRACKET RIGHT_SQUARE_BRACKET
                               | LEFT_SQUARE_BRACKET conditional_expression RIGHT_SQUARE_BRACKET
                               | direct_abstract_declarator LEFT_SQUARE_BRACKET RIGHT_SQUARE_BRACKET
                               | direct_abstract_declarator LEFT_SQUARE_BRACKET conditional_expression RIGHT_SQUARE_BRACKET
                               | LEFT_PARENTHESIS RIGHT_PARENTHESIS
                               | LEFT_PARENTHESIS parameter_list RIGHT_PARENTHESIS
                               | direct_abstract_declarator LEFT_PARENTHESIS RIGHT_PARENTHESIS
                               | direct_abstract_declarator LEFT_PARENTHESIS parameter_list RIGHT_PARENTHESIS
    """
    if len(p) == 3:
        if p[1] == "[":
            result = cppDirectAbsDeclarator(None, None, None, None, None, 1)
        else:
            result = cppDirectAbsDeclarator(None, None, None, None, None, 5)

    elif len(p) == 4:
        if p[2][0] == "abstract_declarator":
            result = cppDirectAbsDeclarator(None, p[2][1], None, None, None, 0)
        elif p[2][0] == "conditional_expression":
            result = cppDirectAbsDeclarator(None, None, None, p[2][1], None, 2)
        elif p[1][0] == "direct_abstract_declarator":
            if p[2] == "[":
                result = cppDirectAbsDeclarator(p[1][1], None, None, None, None, 3)
            else:
                result = cppDirectAbsDeclarator(p[1][1], None, None, None, None, 7)
        elif p[2][0] == "parameter_list":
            result = cppDirectAbsDeclarator(None, None, None, None, p[2][1], 6)

    elif len(p) == 5:
        if p[3][0] == "parameter_list":
            result = cppDirectAbsDeclarator(p[1][1], None, None, None, p[2][1], 8)
        elif p[3][0] == "conditional_expression":
            result = cppDirectAbsDeclarator(p[1][1], None, None, p[2][1], None, 4)

    p[0] = ("direct_abstract_declarator", result)


def p_initializer(p):
    """
    initializer : LEFT_CURLY_BRACKET initializer_list RIGHT_CURLY_BRACKET
                | assignment_expression
    """

    if p[1][0] == "assignment_expression":
        result = cppInitializer(p[1][1])
    else:
        result = cppInitializer(p[2][1])

    p[0] = ("initializer", result)


def p_initializer_list(p):
    """
    initializer_list : initializer_list COMMA initializer
                     | initializer
    """

    if p[1][0] == "initializer":
        result = [p[1][1]]
    else:
        result = p[1][1] + [p[3][1]]

    p[0] = ("initializer_list", result)


def p_statement(p):
    """
    statement : compound_statement
              | expression_statement
              | selection_statement
              | iteration_statement
              | jump_statement
              | labeled_statement
    """

    if p[1][0] == "compound_statement":
        result = cppStmt("compound")
    elif p[1][0] == "expression_statement":
        result = cppStmt("expr")
    elif p[1][0] == "selection_statement":
        result = cppStmt("select")
    elif p[1][0] == "iteration_statement":
        result = cppStmt("iterate")
    elif p[1][0] == "jump_statement":
        result = cppStmt("jump")
    elif p[1][0] == "labeled_statement":
        result = cppStmt("label")

    p[0] = ("statement", result)


def p_labeled_statement(p):
    """
    labeled_statement : IDENTIFIER COLON statement
    """

    result = cppLabelStmt(cppId(p[1].value), p[3][1])

    p[0] = ("labeled_statement", result)


def p_compound_statement(p):
    """
    compound_statement : LEFT_CURLY_BRACKET declaration_list statement_list RIGHT_CURLY_BRACKET
                       | LEFT_CURLY_BRACKET declaration_list RIGHT_CURLY_BRACKET
                       | LEFT_CURLY_BRACKET statement_list RIGHT_CURLY_BRACKET
                       | LEFT_CURLY_BRACKET RIGHT_CURLY_BRACKET
    """

    if p[2][0] == "declaration_list":
        if p[3][0] == "statement_list":
            result = cppCompoundStmt(p[2][1], p[3][1])
        else:
            result = cppCompoundStmt(p[2][1], None)
    elif p[2][0] == "statement_list":
        result = cppCompoundStmt(None, p[2][1])
    else:
        result = cppCompoundStmt(None, None)

    p[0] = ("compound_statement", result)


def p_declaration_list(p):
    """
    declaration_list : declaration_list declaration
                     | declaration
    """

    if p[1][0] == "declaration_list":
        result = p[1][1] + [p[2][1]]
    else:
        result = [p[1][1]]

    p[0] = ("declaration_list", result)


def p_statement_list(p):
    """
    statement_list : statement
                   | statement_list statement
    """

    if p[1][0] == "statement_list":
        result = p[1][1] + [p[2][1]]
    else:
        result = [p[1][1]]

    p[0] = ("statement_list", result)


def p_expression_statement(p):
    """
    expression_statement : expression SEMICOLON
                         | SEMICOLON
    """

    if p[1] != "SEMICOLON":
        p[0] = ("expression_statement", p[1][1])
    else:
        p[0] = ("expression_statement", None)


def p_selection_statement(p):
    """
    selection_statement : IF LEFT_PARENTHESIS expression RIGHT_PARENTHESIS statement %prec IF
                        | IF LEFT_PARENTHESIS expression RIGHT_PARENTHESIS statement ELSE statement
    """

    # print(len(p))
    if len(p) == 6:
        result = cppSelectStmt(p[3][1], p[5][1], None)
    else:
        result = cppSelectStmt(p[3][1], p[5][1], p[7][1])

    p[0] = ("selection_statement", result)


def p_iteration_statement(p):
    """
    iteration_statement : WHILE LEFT_PARENTHESIS expression RIGHT_PARENTHESIS compound_statement
                        | FOR LEFT_PARENTHESIS expression_statement expression_statement expression RIGHT_PARENTHESIS compound_statement
                        | FOR LEFT_PARENTHESIS type_specifier expression_statement expression_statement expression RIGHT_PARENTHESIS compound_statement
                        | FOR LEFT_PARENTHESIS expression_statement expression_statement RIGHT_PARENTHESIS compound_statement
                        | FOR LEFT_PARENTHESIS type_specifier expression_statement expression_statement RIGHT_PARENTHESIS compound_statement
    """
    result = None

    if p[1] == "while":
        result = cppIterateStmt("while", None, p[3][1], None, p[5][1])
    elif p[1] == "for":
        if p[3][0] == "expression_statement":
            if p[5] == ")":
                result = cppIterateStmt("for", p[3][1], p[4][1], None, p[6][1])
            else:
                result = cppIterateStmt("for", p[3][1], p[4][1], p[5][1], p[7][1])
        else:
            if p[6] == ")":
                result = cppIterateStmt(
                    "for_init", (p[3][1], p[4][1]), p[5][1], None, p[7][1]
                )
            else:
                result = cppIterateStmt(
                    "for_init", (p[3][1], p[4][1]), p[5][1], p[6][1], p[8][1]
                )

    p[0] = ("iteration_statement", result)


def p_jump_statement(p):
    """
    jump_statement : GOTO IDENTIFIER SEMICOLON
                   | BREAK SEMICOLON
                   | CONTINUE SEMICOLON
                   | RETURN SEMICOLON
                   | RETURN expression SEMICOLON
    """
    result = cppJumpStmt("return", None)
    if p[1] == "GOTO":
        result = cppJumpStmt("goto", cppId(p[2].value))
    elif p[1] == "BREAK":
        result = cppJumpStmt("break", None)
    elif p[1] == "CONTINUE":
        result = cppJumpStmt("continue", None)
    elif p[1] == "RETURN":
        if len(p) == 2:
            result = cppJumpStmt("return", None)
        else:
            result = cppJumpStmt("return", p[2][1])

    p[0] = ("jump_statement", result)


def p_translation_unit(p):
    """
    translation_unit : translation_unit external_declaration
                     | external_declaration
    """

    if len(p) == 2:
        result = [p[1][1]]
    else:
        result = p[1][1] + [p[2][1]]

    p[0] = ("translation_unit", result)


def p_external_declaration(p):
    """
    external_declaration : function_definition
                         | declaration
    """

    # if p[1][0] == "function_definition":
    #     result = p[1]
    # else:
    #     result =

    p[0] = ("external_declaration", p[1][1])


def p_function_definition(p):
    """
    function_definition : type_specifier declarator declaration_list compound_statement
                        | type_specifier declarator compound_statement
                        | declarator declaration_list compound_statement
                        | declarator compound_statement
    """
    # if p[2][1].name is not None:
    # print(p[1][1].typename, p[2][1].name.name, p[3])
    if p[1][0] == "type_specifier":

        if p[3][0] == "declaration_list":
            result = cppFuncDef(p[1][1], p[2][1].name, p[3][1], p[4][1])
        elif p[3][0] == "compound_statement":
            result = cppFuncDef(p[1][1], p[2][1], p[3][1])
            # print(p[2][1].name)
    elif p[1][0] == "declarator":
        if p[2][0] == "declaration_list":
            result = cppFuncDef(None, p[1][1].name, p[2][1], p[3][1])
        elif p[2][0] == "compound_statement":
            result = cppFuncDef(None, p[1][1].name, None, p[2][1])

    p[0] = ("function_definition", result)


class scopeInitialiser:
    def __init__(
        self,
        scope_id=0,
        scope_name="Global",
        parent_scope_id=None,
        current_scope_depth=0,
    ) -> None:
        self.scope_id = scope_id
        self.parent_scope_id = parent_scope_id
        self.scope_depth = current_scope_depth
        self.scope_name = scope_name
        self.variables = {}
        self.constants = {}
        self.structs = {}
        self.classes = {}

    def find_variable(self, variable):
        return variable in self.variables.keys()

    def find_struct(self, struct):
        return struct in self.structs.keys()

    def find_class(self, classes):
        return classes in self.classes.keys()


class symbolTable:
    def __init__(self, global_scope) -> None:
        self.scope_list = [global_scope]
        self.scope_stack = [global_scope]
        self.functions = {}
        self.cmpd_ctr = 0

    def get_current_scope(self):
        assert len(self.scope_stack) >= 1
        return self.scope_stack[-1]

    def get_current_depth(self):
        assert len(self.scope_stack) >= 1
        return len(self.scope_stack)

    def add_scope_to_stack(self, scope_name):
        curr_depth = self.get_current_depth()
        curr_scope = self.get_current_scope()
        newscope = scopeInitialiser(
            len(self.scope_list), scope_name, curr_scope.scope_id, curr_depth
        )
        self.scope_list.append(newscope)
        self.scope_stack.append(newscope)

    def check_and_add_variable(self, variable, varType):
        curr_scope = self.get_current_scope()
        if curr_scope.find_variable(variable.name):

            print(
                f"Variable re-declared with name {variable.name} at line {driver.lexer.lineno}"
            )
        else:
            curr_scope.variables[variable.name] = varType
            # print(variable)

    def check_and_add_const(self, const, constType, constVal):
        curr_scope = self.get_current_scope()
        if curr_scope.find_variable(const):
            print(
                f"Constant re-declared with name {const.name} at line {driver.lexer.lineno}"
            )

        else:
            curr_scope.constants[const] = (constType, constVal)

    def check_and_add_struct(self, structTag: "cppId", structId: "cppId" = None):
        curr_scope = self.get_current_scope()

        if curr_scope.find_struct(structId):
            print(
                f"Struct re-declared with same name {structId.name} at line {driver.lexer.lineno}"
            )
        else:
            self.add_scope_to_stack(str(structTag.name) + "_struct")
            curr_scope.structs[structId.name] = structTag

    def check_and_add_function(
        self, function_id, function_type, function_nparams, scope_id
    ):
        if function_id.name in self.functions.keys():
            print(
                f"Function re-declared with name {function_id.name} at line no {driver.lexer.lineno}"
            )
        else:
            # self.add_scope_to_stack(str(function_id.name) + "_function")

            self.functions[function_id.name] = (
                function_type.typename,
                function_nparams,
            )

    def check_and_add_class(self, className: "cppId"):
        curr_scope = self.get_current_scope()

        if curr_scope.find_class(className):
            print(
                f"Class re-declared with same name {className} at line no {driver.lexer.lineno}"
            )
        else:
            self.add_scope_to_stack(str(className.name) + "_class")
            curr_scope.classes[className.name] = className

    def remove_scope_from_stack(self):
        self.scope_stack = self.scope_stack[:-1]

    def savecsv(self):
        f = open("symboltable.csv", "w")
        writer = csv.writer(f)
        writer.writerow(["entity_name", "entity_type", "scope_id", "scope_name"])

        for func in self.functions.keys():
            writer.writerow([func, self.functions[func], "Function", 0, "Global"])

        for scope in self.scope_list:
            for var in scope.variables.keys():
                writer.writerow(
                    [
                        var,
                        scope.variables[var].typename,
                        "Variable",
                        scope.scope_id,
                        scope.scope_name,
                    ]
                )
            for struct in scope.structs.keys():
                writer.writerow(
                    [
                        struct,
                        None,
                        "Structure",
                        scope.scope_id,
                        scope.scope_name,
                    ]
                )
            for cl in scope.classes.keys():
                writer.writerow(
                    [
                        cl,
                        None,
                        "Class",
                        scope.scope_id,
                        scope.scope_name,
                    ]
                )
        f.close()


# ------------------------ ------------------------
# ------------------------ ------------------------
# PARSER
# ------------------------ ------------------------
# ------------------------ ------------------------


errors = []

global_scope = scopeInitialiser()
symboltab = symbolTable(global_scope)

allowed_native_types = ["char", "float", "int", "pointer", "string", "struct", "void"]

precedence = (
    ("nonassoc", "IF"),
    ("nonassoc", "ELSE"),
)

typecast_compat = {
    "char": ["int"],
    "float": ["int"],
    "int": ["char", "float"],
    "pointer": ["int"],
}

operators = {
    "arithmetic_op": ["+", "-", "*", "/", "%"],
    "assignment_op": ["=", "+=", "-=", "*=", "/=", "&=", "|=", "^=", ">>=", "<<="],
    "bitwise_op": ["&", "|", "~", ">>", "<<"],
    "boolean_op": ["&&", "||", "!"],
    "comparison_op": [">", "<", "==", ">=", "<="],
    "unary_op": ["++", "--", "sizeof", "~", "!", "&", "*", "+", "-"],
    "postfix_op": ["++", "--", ".", "->"]
    # Class/CPP (string) specific ops?
}


# operator_compat = {
#     "arithmetic_op": ["char", "float", "int", "pointer"],
#     "assignment_op": ["char", "float", "int", "string", "pointer"],
#     "bitwise_op": ["int"],
#     "boolean_op": ["int"],
#     "comparison_op": ["char", "float", "int"],
#     "unary_op": ["char", "float", "int"],
#     "cast_op": ["char", "float", "int", "string", "pointer"],
#     # Class/CPP (string) specific ops?
# }

# type_op_compat = {
#     "char": ["arithmetic_op", "assignment_op", "comparison_op", "unary_op"],
#     "float": ["arithmetic_op", "assignment_op", "comparison_op", "unary_op"],
#     "int": [
#         "arithmetic_op",
#         "assignment_op",
#         "bitwise_op",
#         "boolean_op",
#         "comparison_op",
#         "unary_op",
#     ],
#     "pointer": ["assignment_op"],
#     "string": ["assignment_op"]
#     # Class/CPP (string) specific ops?
# }

operator_compat = {
    "+": ["int", "char", "float"],
    "-": ["int", "char", "float"],
    "*": ["int", "char", "float"],
    "/": ["int", "char", "float"],
    "%": ["int"],
    "<<": ["int"],
    ">>": ["int"],
    "|": ["int"],
    "&": ["int"],
    "~": ["int"],
    "^": ["int"],
    "||": ["int", "char", "float"],
    "&&": ["int", "char", "float"],
    "!": ["int", "char", "float"],
    ">": ["int", "char", "float"],
    ">=": ["int", "char", "float"],
    "<": ["int", "char", "float"],
    "<=": ["int", "char", "float"],
    "=": ["int", "char", "float"],
    "++": ["int", "char", "float"],
    "--": ["int", "char", "float"],
    "func_call": ["int", "char", "float"],
}

# ------------------------ ------------------------
# ------------------------ ------------------------
# SEMANTIC CHECKING AND AST
# ------------------------ ------------------------
# ------------------------ ------------------------


# ------------------------ ------------------------
# BASIC
# ------------------------ ------------------------


class cppType:
    def __init__(self, typename: str):
        self.typename = typename
        self.check()

    def check(self):
        if len(self.typename.split("_")) > 1:
            if self.typename.split("_")[1] not in allowed_native_types:
                raise Exception("Invalid type")
        else:
            if self.typename not in allowed_native_types:
                print(f"Invalid type {self.typename}.\n")

    def add_class_type(self, class_name: str):
        if class_name not in allowed_native_types:
            allowed_native_types.append(str(class_name))
            return True

        return False

    @staticmethod
    def traverse(object):
        return ["Variable Type:" + object.typename]


class cppNode:
    def __init__(self, node_type: cppType = None, node_name: "cppId" = None):
        self.node_type = node_type
        self.base_type = None
        self.node_name = node_name
        # self.check()

    def check(self):
        if self.node_type.split("_")[
            1
        ] not in allowed_native_types or self.base_type not in allowed_native_types + [
            "struct",
            None,
        ]:
            print(f"Incorrect type {self.node_type} / {self.base_type}.\n")
            return False

    @staticmethod
    def traverse(object):
        graph_list = []

        if (
            type(object) is float
            or type(object) is dict
            or type(object) is str
            or type(object) is tuple
            or type(object) is int
        ):

            graph_list.append(object)

        elif isinstance(object, cppNode):
            graph_list.append(str(object.__class__.__name__))
            my_list = [None, "", []]
            for attribute in object.__dict__:

                next = getattr(object, attribute)
                if not (next in my_list):  # or attribute in object.attr_ignore):
                    next_list = []
                    if isinstance(next, str):
                        next_list.append(next)
                    elif isinstance(next, list):
                        next_list.append(str(attribute))
                    else:
                        if not isinstance(next, bool) and not isinstance(next, int):
                            app = next.traverse(next)
                            if app is not None:
                                next_list = next_list + app
                    graph_list.append(next_list)

                # one more case can be added

        elif isinstance(object, list):

            for next in object:
                if next != [] and next != "" and next != None:
                    graph_list.append(next.traverse(next))

        # else:
        #     print
        #     print(f"{type(object)} type not valid")

        return graph_list


class cppConst(cppNode):
    def __init__(
        self,
        val: Union[
            TypeVar("char"), TypeVar("float"), TypeVar("int"), TypeVar("string")
        ],
        _type: cppType = int,
    ):
        self.val = val
        self._type = _type

        super().__init__("constant_" + str(self._type)[1:])

    @staticmethod
    def traverse(object):
        return ["Constant", object._type.traverse(object._type), object.val]


class cppId(cppNode):
    def __init__(self, name: str, _type: cppType = TypeVar("int")):
        super().__init__("identifier_" + str(_type)[1:], name)
        #     return False

        self.name = name
        self._type = _type

        if not (self.name[0]).isalpha():
            print(
                "Invalid identifier name, should start with alphabets at line {}".format(
                    driver.lexer.lineno
                ),
                end="",
            )
            return None

        # Symboltable check and add
        # print(f"name: {self.name}\n")
        # symboltab.check_and_add_variable(self.name, self._type)

    @staticmethod
    def traverse(object):
        pass


class cppIdList(cppId):
    def __init__(self, idl_names: List[cppId], idl_type: cppType):
        self.idl_names = idl_names
        self.idl_type = idl_type

        for id_name in self.idl_names:
            super().__init__(id_name, self.idl_type)


# TODO: checking id in symboltab?
class cppPointer(cppNode):
    def __init__(self, name: cppId, base_type: cppType = int):
        super().__init__("pointer")
        self.name = name
        self.base_type = base_type  # Can base type be pointer? (multi-pointers)

        self.check_ptr()

    def check_ptr(self):
        return True


# TODO: some bookkeeping required
class cppOp(cppNode):
    def __init__(self, op: str):
        super().__init__("operator")
        self.op = op
        self.allowed_ops = operators

    def check_assignop(self):
        if self.op not in self.allowed_ops["assignment_op"]:
            return False
        return True

    def check_pfop(self):
        if self.op not in self.allowed_ops["postfix_op"]:
            return False
        return True

    @staticmethod
    def traverse(object):
        return [object.op]


# units=elements
# _gen_dot=traverse
# dot_list=grpah_list
# tree=ast
# ast_new
class cppStart(cppNode):
    def __init__(self, elements):
        super().__init__("start")
        self.elements = elements
        # self.dot_attr = {'Start': self.elements}

    @staticmethod
    def traverse(obj):
        graph_list = ["Start"]

        if obj is not None:
            for x in obj.elements[1]:
                if x != [] and x != "" and x != None:
                    # print(x)
                    graph_list.append(x.traverse(x))

        return graph_list

    @staticmethod
    def gen_graph(object, graph):
        
        def generate_graph(graph, ast, node_index):

            woking_index = node_index
            if isinstance(ast, tuple):
                ast = [ast]
            if isinstance(ast, list):

                graph.add_node(pydot.Node(node_index, label=str(ast[0]), shape="egg"))

                for x in ast[1:]:
                    if x != []:
                        nd = pydot.Edge(node_index, woking_index + 1)
                        graph.add_edge(nd)
                        woking_index = generate_graph(graph, x, woking_index + 1)

                return woking_index

            elif isinstance(ast, str):
                nd = pydot.Node(
                    node_index,
                    label=str(ast),
                    color="cyan",
                )
                graph.add_node(nd)
                return node_index
            else:
                print(f"{type(ast)} type not valid")

        ast = object.traverse(object)
        print(ast)
        generate_graph(graph, ast, 0)
        graph.get_node("0")[0].set_color("teal")
        return ast, graph


# ------------------------ ------------------------
# EXPRESSIONS
# ------------------------ ------------------------


class cppExpr(cppNode):
    def __init__(self, lhs: cppNode, op: cppOp, rhs: Union[cppNode, None]):
        # if lhs:
        #     if len(lhs.node_type.split("_")) > 1:
        #         self.expr_type = ("expression_"+lhs.node_type).split("_")[1]
        #     else:
        #         self.expr_type = lhs.node_type

        # super().__init__("expression")
        self.lhs = lhs
        self.rhs = rhs

        self.op = op
        # self.op_compat_types =

        # TODO: fix dict issues

        self.op_compat_types = (
            operator_compat[self.op.op] if self.op is not None else allowed_native_types
        )
        self.expr_type = None

        if lhs and lhs.node_type:
            if len(lhs.node_type.split("_")) > 1:
                self.expr_type = lhs.node_type.split("_")[1]
            else:
                self.expr_type = lhs.node_type

        self.node_type = self.expr_type
        self.check()

    # TODO: add array handling as in grammar
    def check(self):

        # Check lhs and rhs type compatible (binary exprs only)
        if not isinstance(self.rhs, list):
            if self.rhs is not None and self.lhs.expr_type != self.rhs.expr_type:

                # # Typecasting; If not possible return False
                # # TODO: int-float typecasting priority
                # if (
                #     self.op.op != "cast"
                #     and self.rhs.expr_type in typecast_compat[self.lhs.expr_type]
                # ):
                #     self.rhs = cppCastExpr(self.rhs, self.lhs.expr_type)
                #     self.expr_type = self.lhs.expr_type

                # # elif self.lhs.expr_type in typecast_compat[self.rhs.expr_type]:
                # #     self.lhs = cppCastExpr(self.lhs, self.rhs.expr_type)
                # #     self.expr_type = self.rhs.expr_type

                # else:
                #     print(self.lhs.un_expr.name, "   ", self.rhs.un_expr)
                #     print(
                #         f"Types {self.lhs.expr_type} and {self.rhs.expr_type} incompatible, cannot typecast.\n"
                #     )
                #     return False
                print(f'Type mismatch on lhs and rhs at line {driver.lexer.lineno}')
        else:
            for s in self.rhs:
                if s is not None and self.lhs.expr_type != s.expr_type:
                    
                    # Typecasting; If not possible return False
                    # TODO: int-float typecasting priority
                    if (
                        self.op.op != "cast"
                        and s.expr_type in typecast_compat[self.lhs.expr_type]
                    ):
                        s = cppCastExpr(s, self.lhs.expr_type)
                        self.expr_type = self.lhs.expr_type

                    # elif self.lhs.expr_type in typecast_compat[self.rhs.expr_type]:
                    #     self.lhs = cppCastExpr(self.lhs, self.rhs.expr_type)
                    #     self.expr_type = self.rhs.expr_type

                    else:
                        print(self.lhs.un_expr.name, "   ", s.un_expr)
                        print(
                            f"Types {self.lhs.expr_type} and {s.expr_type} incompatible, cannot typecast.\n"
                        )
                        return False

        if (
            self.op
            and self.op.op != "cast"
            and self.lhs
            and isinstance(self.lhs, cppId)
            and self.lhs.node_type.split("_")[1] not in self.op_compat_types
        ):
            print(
                f"Operator {self.op} not compatible with type {self.lhs.node_type.split('_')[1]}.\n"
            )
            return False

        if (
            self.op
            and self.op.op != "cast"
            and self.lhs
            and isinstance(self.lhs, cppConst)
            and self.lhs.node_type.split("_")[1] not in self.op_compat_types
        ):
            print(
                f"Operator {self.op} not compatible with type {self.lhs.node_type.split('_')[1]}.\n"
            )
            return False

        # Check op compatible with expr types (after typecasting success)
        elif (
            self.op
            and self.op.op != "cast"
            and self.lhs
            and not isinstance(self.lhs, cppId)
            and not isinstance(self.lhs, cppConst)
            and self.lhs.expr_type not in self.op_compat_types
        ):
            print(
                f"Operator {self.op} not compatible with type {self.lhs.expr_type}.\n"
            )
            return False

        return True

    @staticmethod
    def traverse(object):
        return [object.lhs.traverse(object.lhs),object.op.traverse(object.op),object.rhs.traverse(object.rhs)]


# TODO: Array indexing and function call handling
class cppPostfixExpr(cppExpr):
    def __init__(self, pf_expr: cppExpr, pf_op: cppOp, pf_id: cppId = None):
        super().__init__(pf_expr, pf_op, pf_id)
        #     return False

        self.pf_expr = pf_expr
        self.pf_op = pf_op
        self.pf_id = pf_id
        # print(self.pf_op)
        self.check_pf()

    def check_pf(self):
        # Only int / float can have ++, --
        if (
            self.pf_op
            and self.pf_op.op in ["++", "--"]
            and self.pf_expr.expr_type
            not in [
                "int",
                "float",
            ]
        ):
            print(
                f"Invalid operator {self.pf_op} for type {self.pf_expr.expr_type} at line {driver.lexer.lineno}.\n"
            )

        # Only pointer to struct can have -> op
        if (
            self.pf_op == "->"
            and self.pf_expr.expr_type == "pointer"
            and self.pf_expr.base_type != "struct"
        ):
            print(
                f"Invalid operator {self.pf_op} for pointer to type {self.pf_expr.expr_type} at line {driver.lexer.lineno}.\n"
            )
            return False

        # invalid field name for struct
        if self.pf_op == "->" and self.pf_id is None:
            print(
                f"Invalid field {self.pf_id} to struct pointer {self.pf_expr} for '->' operator at line {driver.lexer.lineno}.\n"
            )
            return False

        # idx = 0
        # for i, scope_ in enumerate(symboltab.scope_list):
        #     if scope_.scope_name == self.pf_expr.lhs.name:
        #         idx = i
        #         break

        # if (self.pf_op == "->") and (
        #     not symboltab.scope_list[idx].find_variable(self.pf_id)
        # ):
        #     print(
        #         f"Invalid field name {self.pf_id} to struct pointer {self.pf_expr} at line {driver.lexer.lineno}.\n"
        #     )
        #     return False

        # # Only struct can have . op
        # if self.pf_op == "." and self.pf_expr.expr_type != "struct":
        #     print(
        #         f"Invalid type {self.pf_expr.expr_type} for '.'operator at line {driver.lexer.lineno}.\n"
        #     )
        #     return False

        return True

    @staticmethod
    def traverse(object):
        pass


class cppUnExpr(cppExpr):
    def __init__(self, un_expr: cppExpr, un_op: cppOp):

        super().__init__(un_expr, un_op, None)
        #     return False

        self.un_expr = un_expr
        self.un_op = un_op

        self.check_un()

    def check_un(self):

        # Only int / float can have unary op, if & used for pointer then var should have been inited
        if isinstance(self.un_expr, cppCastExpr):  # Why castExpr?
            if (
                self.un_op in ["!", "~"]
                and self.un_expr.expr_type != "int"
                and "int" not in typecast_compat[self.un_expr.expr_type]
            ):

                print(
                    f"Invalid type {self.un_expr.expr_type} for {self.un_op} operator at line {driver.lexer.lineno}.\n"
                )
                return False

            if self.un_op == "&" and not symboltab.get_curr_scope().find_variable(
                self.un_expr.lhs.node_name
            ):
                print(
                    f"Variable {self.un_expr.lhs.node_name} referenced without initialization at line {driver.lexer.lineno}.\n"
                )
                return False

        if (
            isinstance(self.un_expr, cppPostfixExpr)
            and self.un_expr.node_type == "identifier"
        ):
            if self.un_op in ["++", "--"] and self.un_expr.expr_type not in [
                "int",
                "float",
            ]:
                print(
                    f"Invalid type {self.un_expr.expr_type} for {self.un_op} operator at line {driver.lexer.lineno}.\n"
                )
                return False

        if self.un_op == "*" and self.un_expr.expr_type != "pointer":
            print(
                f"Invalid de-referencing for a non-pointer expression {self.un_expr} at line {driver.lexer.lineno}.\n"
            )
            return False
            # elif self.un_op == SIZEOF and self.un_expr.expr_type not in allowed_native_types:
            #     print(f"Invalid type {self.un_expr.expr_type} for {self.un_op} operator.\n")
            #     return False

        return True

    @staticmethod
    def traverse(object):
        pass


class cppCastExpr(cppExpr):
    def __init__(
        self, cast_expr: cppUnExpr, new_type: cppType, init_type: cppType = None
    ):
        super().__init__(cast_expr, cppOp("cast"), None)
        #     return False

        self.cast_expr = cast_expr
        self.init_type = self.cast_expr.expr_type
        self.new_type = new_type

        if self.check_cast():
            print("reached const typing")
            if len(self.init_type.split("_")) > 1:
                if self.init_type.split("_")[0] == "constant":
                    # print("reached const typing")
                    self.cast_expr = cppConst(self.cast_expr.un_expr.lhs, self.new_type)

    def check_cast(self):
        if self.new_type not in typecast_compat[self.init_type]:
            print(
                f"Invalid type {self.new_type} for typecasting variable of type {self.init_type} at line {driver.lexer.lineno}.\n"
            )
            return False

        print(self.init_type)

        return True

    @staticmethod
    def traverse(object):
        return [
            "Type Cast",
            object.new_type.traverse(object.new_type),
            object.cast_expr.traverse(object.cast_expr),
        ]


class cppArithExpr(cppExpr):
    def __init__(self, cast_lhs: cppCastExpr, cast_op: cppOp, cast_rhs: cppCastExpr):
        super().__init__(cast_lhs, cast_op, cast_rhs)
        #     return False

        self.cast_lhs = cast_lhs
        self.cast_rhs = cast_rhs
        self.cast_op = cast_op

        self.check_arith()

    def check_arith(self):
        print(self.rhs.expr_type)
        print(self.lhs.expr_type)
        if self.op.op not in operators["arithmetic_op"]:
            print(
                f"Invalid operator {self.op.op} for arithmetic expression at line {driver.lexer.lineno}.\n"
            )
            return False

        if self.lhs.expr_type not in operator_compat[self.op.op]:
            print(
                f"Operator {self.op.op} not compatible with type {self.lhs.expr_type} at line {driver.lexer.lineno}.\n"
            )
            return False
        
        if self.rhs.expr_type not in operator_compat[self.op.op]:
            print(
                f"Operator {self.op.op} not compatible with type {self.rhs.expr_type} at line {driver.lexer.lineno}.\n"
            )
            return False

        # if self.lhs.expr_type != self.rhs.expr_type:
        #     if self.rhs.expr_type not in typecast_compat[self.lhs.expr_type] and \
        #        self.lhs.expr_type not in typecast_compat[self.rhs.expr_type]:
        #         print(f"Invalid types {self.lhs.expr_type} and {self.rhs.expr_type} for arithmetic expression.\n")
        #         return False

        return True

    @staticmethod
    def traverse(object):
        pass


class cppShiftExpr(cppExpr):
    def __init__(
        self, shift_lhs: cppArithExpr, shift_op: cppOp, shift_rhs: cppArithExpr
    ):
        super().__init__(shift_lhs, shift_op, shift_rhs)
        #     return False

        self.shift_lhs = shift_lhs
        self.shift_rhs = shift_rhs
        self.shift_op = shift_op

        self.check_shift()

    def check_shift(self):
        return True

    def traverse(self):
        pass


class cppRelationExpr(cppExpr):
    def __init__(self, rel_lhs: cppShiftExpr, rel_op: cppOp, rel_rhs: cppShiftExpr):
        super().__init__(rel_lhs, rel_op, rel_rhs)
        #     return False

        self.rel_lhs = rel_lhs
        self.rel_rhs = rel_rhs
        self.rel_op = rel_op

        self.check_relexpr()

    def check_relexpr(self):

        if self.rel_op.op not in operators["comparison_op"]:
            print(
                f"Invalid operator {self.rel_op} for relational expression at line {driver.lexer.lineno}.\n"
            )
            return False

        # if self.rel_lhs.expr_type != self.rel_rhs.expr_type:
        #     print(
        #         f"Operator {self.rel_op} not compatible with different types {self.rel_lhs.expr_type} and {self.rel_rhs.expr_type}.\n"
        #     )
        # k_type = ""
        # for k, v in operators.items():
        #     if self.rel_op.op in v:
        #         k_type = k
        #         break

        if (
            self.rel_lhs
            and self.rel_lhs.expr_type
            and self.rel_lhs.expr_type not in operator_compat[self.rel_op.op]
        ):
            print(
                f"Operator {self.rel_op} not compatible with type {self.rel_lhs.expr_type} at line.\n"
            )
            return False

        elif (
            self.rel_lhs
            and self.rel_lhs.expr_type
            and self.rel_rhs.expr_type not in operator_compat[self.rel_op.op]
        ):
            print(
                f"Operator {self.rel_op} not compatible with type {self.rel_rhs.expr_type} at line .\n"
            )
            return False

        # if self.lhs.expr_type != self.rhs.expr_type:
        #     if self.rhs.expr_type not in typecast_compat[self.lhs.expr_type] and \
        #        self.lhs.expr_type not in typecast_compat[self.rhs.expr_type]:
        #         print(f"Invalid types {self.lhs.expr_type} and {self.rhs.expr_type} for relational expression.\n")
        #         return False

        return True

    @staticmethod
    def traverse(object):
        pass


class cppLogicExpr(cppExpr):
    def __init__(self, l_lhs: cppRelationExpr, l_op: cppOp, l_rhs: cppRelationExpr):
        super().__init__(l_lhs, l_op, l_rhs)

        self.l_lhs = l_lhs
        self.l_rhs = l_rhs
        self.l_op = l_op

        self.check_logic()

    def check_logic(self):
        if (
            self.l_op not in operators["bitwise_op"]
            and self.l_op not in operators["boolean_op"]
        ):
            print(
                f"Invalid operator {self.l_op} for logical expression at line {driver.lexer.lineno}.\n"
            )
            return False

        # Single expression should have unary ops only
        if self.l_rhs is None and self.l_op not in ["!", "~"]:
            print(
                f"Invalid binary operator {self.l_op} for unary logical expression at line {driver.lexer.lineno}.\n"
            )
            return False

        return True

    @staticmethod
    def traverse(object):
        pass


class cppCondExpr(cppExpr):
    def __init__(self, con_lhs: cppLogicExpr, con_mid: cppExpr, con_rhs: cppLogicExpr):
        super().__init__(con_lhs, con_mid, con_rhs)

        self.con_lhs = con_lhs
        self.con_mid = con_mid
        self.con_rhs = con_rhs

        self.check_conexp()

    def check_conexp(self):
        return True

    @staticmethod
    def traverse(object):
        pass


class cppAssignExpr(cppExpr):
    def __init__(
        self, unaryexpr: cppUnExpr, assign_op: cppOp, assign_expr: "cppAssignExpr"
    ):
        super().__init__(unaryexpr, assign_op, assign_expr)
        #     return False

        self.unaryexpr = unaryexpr
        self.assign_op = assign_op
        self.assign_expr = assign_expr

        self.check_assign()

    def check_assign(self):
        # Pointer cannot be assigned anything other than pointer / int
        if (
            self.assign_op in operators["assignment_op"]
            and self.lhs.node_type == "pointer"
            and self.rhs.node_type not in ["int", "pointer"]
        ):
            print(
                f"Pointer {self.unaryexpr} cannot be assigned to non-pointer / non-int {self.assign_expr} at line {driver.lexer.lineno}.\n"
            )
            return False

        return True

    @staticmethod
    def traverse(object):
        pass


# ------------------------ ------------------------
# DECLARATIONS, FUNCTIONS, CLASSES, STRUCTS
# ------------------------ ------------------------


class cppInitializer(cppNode):
    def __init__(self, init_expr: Union[cppAssignExpr, List["cppInitializer"]]):
        self.init_expr = init_expr
        # TODO: If list of initializer, make new scope
        # TODO: checking list["type"]
        self.check_init()

    def check_init(self):
        if isinstance(self.init_expr, cppAssignExpr):
            self.init_expr.check_assign()
        # TODO
        # elif isinstance(self.init_expr, list) and isinstance(
        #     self.init_expr[0], "cppInitializer"
        # ):
        #     for init in self.init_expr:
        #         if not init.check_init():
        #             return False

        return True


# TODO
class cppAbsDeclarator(cppNode):
    def __init__(self, adec_dadec: "cppDirectAbsDeclarator"):
        super().__init__("abstract_declarator")
        #     return False

        self.check_adec()

    def check_adec(self):
        return True


class cppDirectAbsDeclarator(cppNode):
    def __init__(
        self,
        dadec: "cppDirectAbsDeclarator",
        adec: cppAbsDeclarator,
        dadec_name: cppId,
        dadec_con_exp: cppCondExpr,
        dadec_param_list: List["cppParamDeclaration"],
        dadec_flag: int = 0,
    ):

        super().__init__("direct_abstract_declarator")
        #     return False

        self.dadec = dadec
        self.adec = adec
        self.dadec_name = dadec_name
        self.dadec_con_exp = dadec_con_exp
        self.dadec_param_list = dadec_param_list
        self.dadec_flag = dadec_flag

        self.check_dadec()

    def check_dadec(self):
        return True


class cppDirectDeclarator(cppNode):
    def __init__(
        self,
        name: cppId,
        dec_declarator: "cppDirectDeclarator",
        dec_type: cppType,
        param_list: List["cppParamDeclaration"] = None,
        arr_offset: cppCondExpr = None,
        dec_flag: int = 0,
    ):
        super().__init__("direct_declarator")
        #     return False

        self.name = name
        self.dec_declarator = dec_declarator
        self.dec_type = dec_type
        self.arr_offset = arr_offset
        self.dec_flag = dec_flag
        self.param_list = param_list

        if self.dec_flag == 7:
            self.name = self.dec_declarator.name

        self.check_ddecl()
        # return None

    def check_ddecl(self):
        return True


class cppInitDeclarator(cppNode):
    def __init__(self, declarator: "cppDeclarator", initializer: cppInitializer):
        super().__init__("init_declarator")
        #     return False

        self.declarator = declarator
        self.initializer = initializer
        self.check_initdeclarator()

    def check_initdeclarator(self):
        if self.initializer is not None:
            if not self.initializer.check_init():
                return False

        # Declarator = initializer check (assign?)
        if self.initializer and isinstance(self.initializer.init_expr, cppAssignExpr):
            if symboltab.get_curr_scope().find_variable(self.declarator.name):
                self.initializer.init_expr.expr_type = (
                    symboltab.get_curr_scope().variables[self.declarator.name]
                )
            # Print error ?
            # else:
            # print(f"Declarator {self.declarator.name} not initialized")

        return True

    @staticmethod
    def traverse(obj):
        result = []
        if obj.initializer is not None:
            result.append(
                (obj.declarator.name.name, obj.initializer.init_expr.pf_expr.val)
            )
        else:
            result.append((obj.declarator.name.name, None))
        return result


class cppInitDecls(cppNode):
    def __init__(self, init_decls: List[cppInitDeclarator]):
        super().__init__("init_declarators")
        #     return False

        self.init_decls = init_decls
        self.check_initdecls()

    def check_initdecls(self):
        for init in self.init_decls:
            if not init.check_initdeclarator():
                return False

        return True

    # @staticmethod
    # def traverse(obj):
    #     result = []
    #     for dec in obj.init_decls:
    #         result.append([dec.declarator.name, dec.initializer])
    #     return result


class cppDeclarator(cppNode):
    def __init__(
        self,
        name: cppId,
        ddecl: cppDirectDeclarator = None,
        arr_offset: Union[cppId, cppConst] = None,
        is_pointer: bool = False,
    ):
        super().__init__("declarator")
        #     return False

        self.name = name
        self.arr_offset = arr_offset
        self.is_pointer = is_pointer
        self.ddecl = ddecl

    def check_decl(self):
        return True


# class cppDecSpec(cppNode):
#     def __init__(self):
#         if not super().__init__("declaration_specifier"):
#             return False


class cppDeclaration(cppNode):
    def __init__(self, decl_type: cppType, initdecl_list: cppInitDecls):
        super().__init__("declaration")
        #     return False

        self.decl_type = decl_type
        self.initdecl_list = initdecl_list
        self.check_declaration()

    def check_declaration(self):
        if self.initdecl_list is not None:
            for init in self.initdecl_list:
                # Void assignment invalid
                if self.decl_type == "void":
                    print(
                        f"Void variable {init.name} cannot be assigned a value at line {driver.lexer.lineno}.\n"
                    )
                    return False

                # Array offset check
                if (
                    init.declarator.arr_offset
                    and init.declarator.arr_offset.node_type.split("_")[1] != "int"
                ):
                    print(
                        f"Array offset {init.declarator.arr_offset} must be of int type at line {driver.lexer.lineno}.\n"
                    )
                    return False

                # Redeclaring variable
                if symboltab.get_current_scope().find_variable(init.declarator.name):
                    print(
                        f"Re-declared variable {init.declarator.name} at line {driver.lexer.lineno}.\n"
                    )
                    return False
                # TODO: removed for cppId frivolous object
                # symboltab.check_and_add_variable(init.declarator.name, self.decl_type)

        return True

    @staticmethod
    def traverse(object):
        graph_list = [object.decl_type.traverse(object.decl_type)]
        for init_decls in object.initdecl_list:
            graph_list += init_decls.traverse(init_decls)
        return graph_list


# ------------------------ ------------------------
# STATEMENTS
# ------------------------ ------------------------


class cppStmt(cppNode):
    def __init__(self, stmt_type: str):
        super().__init__("statement")
        #     return False

        self.stmt_type = stmt_type
        self.stmt = None

        self.check_stmt()

    def check_stmt(self):
        if self.stmt_type not in [
            "compound",
            "expr",
            "select",
            "iterate",
            "jump",
            "label",
        ]:
            print(
                f"Invalid statement type {self.stmt_type} at line {driver.lexer.lineno}.\n"
            )
            return False

        return True

    @staticmethod
    def traverse(object):
        return [object.stmt]


class cppCompoundStmt(cppStmt):
    def __init__(self, cmpd_decls: List[cppDeclaration], cmpd_stmts: List[cppStmt]):
        super().__init__("compound")
        #     return False

        self.cmpd_decls = cmpd_decls
        self.cmpd_stmts = cmpd_stmts
        self.stmt = [cmpd_decls,cmpd_stmts]
        self.cmpd_idx = symboltab.cmpd_ctr

        # TODO: Compound statement own scope
        # TODO: add variables in decls
        # TODO: checking return as last stmt
        symboltab.add_scope_to_stack(f"cmpd_{self.cmpd_idx}")
        symboltab.cmpd_ctr += 1

        if self.cmpd_decls is not None:
            for decl in self.cmpd_decls:
                decl_type = decl.decl_type

                for dec_n in decl.initdecl_list:
                    if dec_n.declarator.is_pointer:
                        decl_type = cppType(f"pointer_{decl_type.typename}")
                    symboltab.check_and_add_variable(dec_n.declarator.name, decl_type)
        # print(self.stmt)
        # symboltab.remove_scope_from_stack()

        self.check_cmpd()

    # TODO: add type checking consistently
    def check_cmpd(self):
        # return isinstance(self.cmpd_decls, list) and isinstance(
        #     self.cmpd_stmts, List[cppStmt]
        # )
        return True

    @staticmethod
    def traverse(object):
        # print(object.cmpd_decls,object.cmpd_stmts)
        graph_list = ["Compound_Statement"]
        if object.cmpd_decls is not None:
            for cmpd_decl in object.cmpd_decls:
                graph_list.append(cmpd_decl.traverse(cmpd_decl))
        if object.cmpd_stmts is not None:
            for cmpd_stmt in object.cmpd_stmts:
                # print(cmpd_stmt.traverse(cmpd_stmt))
                graph_list.append(cmpd_stmt.traverse(cmpd_stmt))
        return graph_list


class cppExprStmt(cppStmt):
    def __init__(self, e_expr: cppExpr):
        super().__init__("expr")
        #     return False

        self.e_expr = e_expr
        self.stmt = [e_expr]
        self.check_exprstmt()

    def check_exprstmt(self):
        return isinstance(self.e_expr, cppExpr)

    @staticmethod
    def traverse(obj):
        return [
            obj.e_expr.traverse(obj.e_expr)
       ]


class cppSelectStmt(cppStmt):
    def __init__(
        self,
        select_expr: cppExpr,
        select_if_stmt: cppStmt,
        select_else_stmt: cppStmt = None,
    ):
        super().__init__("select")
        #     return Fals

        self.select_expr = select_expr
        self.select_if_stmt = select_if_stmt
        self.select_else_stmt = select_else_stmt
        self.stmt = [select_expr,select_if_stmt,select_else_stmt]
    def check_selectstmt(self):
        return (
            isinstance(self.select_expr, cppExpr)
            and isinstance(self.select_if_stmt, cppStmt)
            and isinstance(self.select_else_stmt, cppStmt)
        )

    @staticmethod
    def traverse(object):
        graph_list =  ["if",object.select_expr.traverse(object.select_expr)]
        if object.select_if_stmt is not None:
            graph_list.append(object.if_stmt.traverse(object.if_stmt))
        if object.select_else_stmt is not None:
            graph_list.append(object.else_stmt.traverse(object.else_stmt))

        return graph_list

class cppIterateStmt(cppStmt):
    def __init__(
        self,
        iter_type: str,
        iter_init_stmt: cppExprStmt,
        iter_check_stmt: cppExprStmt,
        iter_update_expr: cppExpr,
        body_stmt: cppCompoundStmt,
    ):

        super().__init__("iterate")
        #     return False

        self.iter_type = iter_type  # ['while', 'for', 'for_init']
        self.iter_init_stmt = iter_init_stmt
        self.iter_check_stmt = iter_check_stmt
        self.iter_update_expr = iter_update_expr

        self.body_stmt = body_stmt
        self.stmt = [iter_type,iter_init_stmt,iter_check_stmt,iter_update_expr]
        # TODO: Initialize variable in loop statement and add to compound statement scope
        if self.iter_type == "for_init":
            i_type = self.iter_init_stmt[0]
            i_init = cppInitializer(self.iter_init_stmt[1])
            idx = 0
            for i, scope in enumerate(symboltab.scope_list):
                if scope.scope_name == f"cmpd_{body_stmt.cmpd_idx}":
                    idx = i
                    break
            symboltab.scope_stack.append(symboltab.scope_list[idx])
            symboltab.check_and_add_variable(
                i_init.init_expr[0].unaryexpr.un_expr.pf_expr, i_type
            )
            symboltab.scope_stack.pop()

            # filter(
            #     lambda scope: scope.scope_name == f"cmpd_{body_stmt.cmpd_idx}",
            #     symboltab.scope_list,
            # )[0].check_and_add_var(i_init.var.name)

        self.check_iterstmt()

    def check_iterstmt(self):
        return (
            isinstance(self.iter_init_stmt, cppExprStmt)
            and isinstance(self.iter_check_stmt, cppExprStmt)
            and isinstance(self.iter_update_expr, cppExpr)
            and isinstance(self.body_stmt, cppStmt)
        )

    @staticmethod
    def traverse(object):

        return [
            object.iter_type,
            object.iter_init_stmt.traverse(object.iter_init_stmt),
            object.iter_check_stmt.traverse(object.iter_check_stmt),
            object.iter_update_expr.traverse(object.iter_update_expr),
            [],
        ]


class cppJumpStmt(cppStmt):
    def __init__(self, jump_type: str, jump_expr: cppExpr = None):
        super().__init__("jump")
        #     return False

        self.jump_type = jump_type
        self.jump_expr = jump_expr
        self.stmt = [jump_type,jump_expr]
        self.check_jumpstmt()

    def check_jumpstmt(self):
        if self.jump_type not in ["break", "continue", "goto", "return"]:
            print(
                f"Invalid statement {self.jump_type} at line {driver.lexer.lineno}.\n"
            )
            return False

        if self.jump_type == "break":
            scope = symboltab.get_curr_scope()
            flag = False
            while scope:
                if scope.name == "loop":
                    flag = True
                scope = scope.parent
            if not flag:
                print(
                    f"Break statement not within loop at line {driver.lexer.lineno}.\n"
                )
                return False

        elif self.jump_type == "continue":
            scope = symboltab.get_curr_scope()
            flag = False
            while scope:
                if scope.name == "loop":
                    flag = True
                scope = scope.parent
            if not flag:
                print(
                    f"Continue statement not within loop at line {driver.lexer.lineno}.\n"
                )
                return False

    @staticmethod
    def traverse(object):
        pass


class cppLabelStmt(cppStmt):
    def __init__(self, label_id: cppId, label_stmt: cppStmt):
        super().__init__("label")
        #     return False

        self.label_id = label_id
        self.label_stmt = label_stmt
        self.stmt = [label_id,label_stmt]
        # TODO: add label to symbol table in the current scope

        self.check_labelstmt()

    def check_labelstmt(self):
        return isinstance(self.label_id, cppId) and isinstance(self.label_stmt, cppStmt)

    @staticmethod
    def traverse(object):
        pass


# ------------------------ ------------------------
# FUNCTIONS, CLASSES, STRUCTS
# ------------------------ ------------------------


# TODO: extract variable names from function arguments (unaryexpr)
class cppFuncArgs(cppNode):
    def __init__(self, funcargs: List[cppAssignExpr]):
        super().__init__("function_arguments")
        #     return False

        self.funcargs = funcargs
        self.check_funcargs()

    def check_funcargs(self):
        return True

    @staticmethod
    def traverse(object):
        pass


class cppParamDeclaration(cppNode):
    def __init__(
        self, pdec_type: cppType, pdec_param: Union[cppAbsDeclarator, cppDeclarator]
    ):
        super().__init__("param_declaration")
        #     return False

        self.pdec_type = pdec_type
        self.pdec_param = pdec_param

        self.check_pdec()

    def check_pdec(self):
        return True


class cppFuncDef(cppNode):
    def __init__(
        self,
        func_type: cppType,
        func_decl: cppDeclarator,
        func_stmt: cppCompoundStmt,
    ):
        super().__init__("function_definition")

        self.func_type = func_type
        self.func_name = func_decl.ddecl.name
        self.func_param_list = func_decl.ddecl.param_list
        self.func_stmt = func_stmt
        self.func_nparams = len(self.func_param_list) if self.func_param_list else 0
        # print("funcstmt", self.func_stmt.cmpd_stmts.)

        self.scope_id = func_stmt.cmpd_idx

        idx = 0
        for i, l_scope in enumerate(symboltab.scope_list):
            if l_scope.scope_name == f"cmpd_{self.scope_id}":
                idx = i
                break

        symboltab.scope_stack.append(symboltab.scope_list[idx])
        # print(self.func_param_list, self.func_name, self.func_type)

        symboltab.check_and_add_function(
            self.func_name, self.func_type, self.func_nparams, self.scope_id
        )
        if self.func_param_list is not None:
            for param in self.func_param_list:
                p_type = param.pdec_type
                p_name = param.pdec_param.name
                # print(p_name)
                symboltab.check_and_add_variable(p_name, p_type)
        symboltab.scope_stack.pop()
        self.check_func_def()

    def check_func_def(self):
        return True

    @staticmethod
    def traverse(object):
        return [
            "Function_Declaration",
            object.func_type.traverse(object.func_type),
            object.func_name.name,
            cppNode.traverse(object.func_param_list),
            object.func_stmt.traverse(object.func_stmt),
        ]


class cppBaseSpec(cppNode):
    def __init__(self, bspec_id: cppId, bspec_acc_spec: str):
        super().__init__("base_specifier")
        #     return False

        self.bspec_id = bspec_id
        self.bspec_acc_spec = bspec_acc_spec

        self.bspec_check()

    def bspec_check(self):
        return True


class cppMemberDeclaration(cppNode):
    def __init__(
        self,
        decl_type: cppType,
        memberdecl_list: Union[cppInitDecls, List[cppFuncDef]],
        member_type: str,
        member_access: str = None,
    ):
        super().__init__("member_declaration")
        #     return False

        self.decl_type = decl_type
        self.memberdecl_list = memberdecl_list
        self.member_type = member_type
        self.member_access = member_access

        self.check_member_dec()

    def check_member_dec(self):
        if self.member_type not in ["var", "func"]:
            print(f"Member declaration of type {self.member_type} not valid.\n")
            return False

        for memb in self.memberdecl_list:
            # Void assignment invalid
            if self.decl_type == "void":
                print(
                    f"Void variable {memb.name} cannot be assigned a value at line {driver.lexer.lineno}.\n"
                )
                return False

            # Array offset check
            if memb.declarator.arr_offset.node_type.split("_")[1] != "int":
                print(
                    f"Array offset {memb.declarator.arr_offset} must be of int type at line {driver.lexer.lineno}.\n"
                )
                return False

            # Redeclaring variable
            if symboltab.get_curr_scope().find_variable(memb.name):
                print(
                    f"Re-declared variable {memb.name} at line {driver.lexer.lineno}.\n"
                )
                return False

            symboltab.get_curr_scope().check_and_add_variable(memb.name, self.decl_type)

        return True


class cppFunction(cppNode):
    def __init__(
        self,
        f_name: cppId,
        f_param_decls: List[cppParamDeclaration],
        f_cmpd_stmt: cppCompoundStmt,
        f_return: cppId,
        f_return_type: cppType,
        f_parent_class: "cppClass" = None,
        f_permission=0,  # Public: 0, Protected: 1, Private: 2
    ):
        super().__init__("function")
        #     return Fals

        self.f_name = f_name
        self.f_param_decls = f_param_decls
        self.f_permission = f_permission
        self.f_cmpd_stmt = f_cmpd_stmt

        self.f_decls = self.f_cmpd_stmt.cmpd_decls
        self.f_stmts = self.f_cmpd_stmt.cmpd_stmts

        self.f_parent_class = f_parent_class

        self.f_return_type = f_return_type
        self.f_return = f_return

        symboltab.check_and_add_function(f_name)

        self.f_local_vars = []
        for f_decl in self.f_decls:
            f_dec_type = f_decl.decl_type
            for f_init_decl in f_decl:
                self.f_local_vars.append((f_init_decl.declarator.name, f_dec_type))

        for f_var in self.f_local_vars:
            symboltab.check_and_add_variable(f_var)

        symboltab.remove_scope_from_stack()

        self.check_func()

    def check_func(self):
        return True

    @staticmethod
    def traverse(object):
        pass


class cppStructDeclarator(cppNode):
    def __init__(self, s_declarator: cppDeclarator, s_con_expr: cppCondExpr):
        super().__init__("struct_declarator")
        #     return False

        self.s_declarator = s_declarator
        self.s_con_expr = s_con_expr

        self.check_s_declarator()

    def check_s_declarator(self):
        return True


# TODO:
class cppStructDeclaration(cppDeclaration):
    def __init__(
        self, s_declaration: List[cppType], s_declarator_list: List[cppStructDeclarator]
    ):
        super().__init__("struct")
        self.s_declaration = s_declaration
        self.s_declarator_list = s_declarator_list

        self.s_declaration_check()

    def s_declaration_check(self):
        return True


class cppStruct(cppNode):
    def __init__(self, s_tag: cppId, s_id: cppId, s_decls: List[cppDeclaration] = None):
        super().__init__("struct")
        #     return False

        self.s_tag = s_tag
        self.s_id = s_id
        self.s_decls = s_decls

        # Initialize own scope
        symboltab.check_and_add_struct(self.s_tag, self.s_id)

        # Extract variables from declarations to add to symboltable scope
        self.s_vars = []
        for s_decl in s_decls:
            s_type = s_decl.decl_type

            s_initdecl_list = s_decl.initdecl_list
            for s_initdecl in s_initdecl_list:
                self.s_vars.append((s_initdecl.declarator.name, s_type))

        for s_var in self.s_vars:
            symboltab.check_and_add_variable(s_var[0], s_var[1])

        symboltab.remove_scope_from_stack()

        self.check_struct()

    def check_struct(self):
        return True

    @staticmethod
    def traverse(object):
        pass


class cppClass(cppNode):
    def __init__(
        self,
        c_name: cppId,
        c_members: List[cppMemberDeclaration],
        c_parents: "cppBaseSpec" = None,
    ):
        self.c_name = c_name
        self.c_members = c_members
        self.c_parents = c_parents

        self.private, self.c_vardecs, self.c_funcdefs = None, None, None
        if self.c_members is not None:
            self.private = [
                member for member in c_members if member.member_access == "private"
            ]

            # Find var declarations vs function definitions and add to c_vardec, c_funcdec
            self.c_vardecs = [
                (member, member.member_access)
                for member in c_members
                if member.member_type == "var"
            ]

            self.c_funcdefs = [
                (member, member.member_access)
                for member in c_members
                if member.member_type == "func"
            ]

        symboltab.check_and_add_class(self.c_name)
        self.add_c_vars()
        self.add_c_funcs()

        symboltab.remove_scope_from_stack()

    def add_c_vars(self):
        self.c_vars = []

        if self.c_vardecs is not None:
            for c_decl, c_var_access in self.c_vardec:
                c_type = c_decl.decl_type

                c_initdecl_list = c_decl.initdecl_list
                for c_initdecl in c_initdecl_list:
                    self.c_vars.append((c_initdecl.declarator.name, c_type))

        for c_var in self.c_vars:
            symboltab.check_and_add_variable(c_var[0], c_var[1])

    def add_c_funcs(self):
        self.c_funcs = []

        if self.c_funcdefs is not None:
            for c_funcdef, c_func_access in self.c_funcdefs:
                self.c_funcs.append((c_funcdef.func_name.name, c_funcdef.func_type))

                # Permission and inheritance, return variable id
                c_func_obj = cppFunction(
                    c_funcdef.func_name,
                    c_funcdef.func_param_list,
                    c_funcdef.func_stmt,
                    None,
                    c_funcdef.func_type,
                    None,
                    c_func_access,
                )

        # for c_func in self.c_funcs:
        #     symboltab.check_and_add_function(c_func[0], c_func[1])

    def check(self):
        return True
        # Symtable check
        # Inheritance checks

    @staticmethod
    def traverse(object):
        pass


class cppPredefFunc(cppFunction):
    def __init__(self, predef_fname: cppId):
        self.f_name = predef_fname

        super().__init__()


class cppStringFunc(cppFunction):
    def __init__(
        self,
        strf_name: cppId,
        strf_stmts: List[cppStmt],
        strf_return: cppId,
        strf_return_type: cppId,
        strf_args: List[cppFuncArgs],
    ):

        self.strf_name = strf_name
        self.strf_stmts = strf_stmts
        self.strf_return = strf_return
        self.strf_return_type = strf_return_type
        self.strf_args = strf_args

        super().__init__()
        #     "string",
        #     self.strf_name,
        #     self.strf_stmts,
        #     self.strf_return,
        #     self.strf_return_type,
        #     self.strf_args,
        # ):
        #     return False

        self.check_strfunc()

    def check_strfunc(self):
        pass


class cppMathFunc(cppFunction):
    def __init__(
        self,
        mathf_name: cppId,
        mathf_stmts: List[cppStmt],
        mathf_return: cppId,
        mathf_return_type: cppId,
        mathf_args: List[cppFuncArgs],
    ):

        self.mathf_name = mathf_name
        self.mathf_stmts = mathf_stmts
        self.mathf_return = mathf_return
        self.mathf_return_type = mathf_return_type
        self.mathf_args = mathf_args

        super().__init__()
        #     "float",  # only float valued functions
        #     self.mathf_name,
        #     self.mathf_stmts,
        #     self.mathf_return,
        #     self.mathf_return_type,
        #     self.mathf_args,
        # ):
        #     return False

        self.check_mathfunc()

    def check_mathfunc(self):
        pass


ap = argparse.ArgumentParser()
ap.add_argument("-n", "--num", type=int, required=True, help="test case number")
ap.add_argument("-s", "--save", required=False, help="save the output to csv file")
ap.add_argument("-m", "--mode", type=str, help="lexer or parser", default="parse")

args = vars(ap.parse_args())


class Parser:
    def __init__(self, file):
        self.file = file
        self.string = ""
        with open(file, "r") as f:
            self.string = f.read()
        self.lexer = lex()
        self.parser = yacc(debug=1, errorlog=NullLogger())
        self.tokens = []

    def find_column(self, token):
        line_start = self.string.rfind("\n", 0, token.lexpos) + 1
        return (token.lexpos - line_start) + 1

    def run_lex(self):
        self.lexer.input(self.string)
        for token in self.lexer:
            self.tokens.append(token)

    def run_parse(self):
        self.tree = self.parser.parse(self.string)

    def print_tokens(self):
        print("Token" + 20 * " " + "Lexeme" + 19 * " " + "Line#" + 20 * " " + "Column#")
        for i in range(len(self.tokens)):
            self.tokens[i].lexpos = self.find_column(self.tokens[i])
            print(
                f"{self.tokens[i].type}"
                + (25 - len(f"{self.tokens[i].type}")) * " "
                + f"{self.tokens[i].value}"
                + (25 - len(f"{self.tokens[i].value}")) * " "
                + f"{self.tokens[i].lineno}"
                + (25 - len(f"{self.tokens[i].lineno}")) * " "
                + f"{self.tokens[i].lexpos}"
            )

    def print_ast(self):
        print("AST is: ")
        print(self.ast)

    def print_to_csv(self):

        tokens_ = []
        for token in self.tokens:
            tokens_.append([token.type, token.value, token.lineno, token.lexpos + 1])

        df = pd.DataFrame(data=tokens_, index=None, columns=None)
        df.to_csv(f"outputs/output_test_{args['num']}.csv", header=False)


driver = Parser(f"tests/semantic/test_{args['num']}.cpp")

if args["mode"] == "parse":
    driver.run_parse()
    symboltab.savecsv()
    # ast1 = cppStart.traverse(driver.tree)
    # print(ast)
    # graph = pydot.Dot("AST", graph_type="graph")
    # ast, graph = cppStart.gen_graph(driver.tree, graph)
    # graph.write_png("AST.png")

elif args["mode"] == "lex":
    driver.run_lex()
    driver.print_tokens()