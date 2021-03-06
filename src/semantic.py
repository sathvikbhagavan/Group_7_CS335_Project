from distutils.log import error
from typing import List, Union
import pydot
import csv
import pandas as pd
import pydot
import pickle
from lexer import *
from ply.lex import lex
from ply.yacc import yacc, NullLogger
import argparse

curr_param = []
tmp_func = []
output_cntr = 0
tmp_var_index = 0
string_to_temp_var_map = {}
register_type = {}
var_index = 0
errors_found = 0

precedence = (
    ("nonassoc", "IF"),
    ("nonassoc", "ELSE"),
)

# ------------------------ ------------------------
# ------------------------ ------------------------
# PARSER GRAMMAR
# ------------------------ ------------------------
# ------------------------ ------------------------


dtype_size = {
    "int": 4,
    "float": 4,
    "char": 1,
    "pointer_int": 4,
    "pointer_float": 4,
    "pointer_char": 4,
}

global_structs = {}


def get_stack_size(func_name):
    global stack_space
    total_size = 0
    for var in stack_space[func_name]:
        total_size += var["size"]

    return total_size


def p_start(p):
    """
    start : translation_unit
    """
    global errors_found
    p[0] = {}
    p[0]["code"] = []
    p[0]["data"] = cppStart(p[1]["data"])
    if "code" in p[1].keys():
        p[0]["code"] = p[1]["code"]
    if "instr" in p[1].keys():
        p[0]["instr"] = p[1]["instr"]

    if errors_found > 0:
        print(
            f"\nThere are {errors_found} errors detected. Not able to generate assembly code"
        )
        exit(2)

    filehandler = open("src/register_type.obj", "wb")
    pickle.dump(register_type, filehandler)
    with open("bin/3AC.code", "w") as f:
        for i in p[0]["code"]:
            if isinstance(i, list):
                f.write(i[0])
                f.write("\n")
            else:
                f.write(i)
                f.write("\n")
    with open("bin/mips.code", "w") as f:
        for i in p[0]["instr"]:
            if isinstance(i, list):
                f.write((" ").join(i))
                f.write("\n")
            else:
                f.write(i)
                f.write("\n")


def p_error(p):
    global errors_found
    if p is not None:
        print(f"Syntax error at token {p.value} at {driver.lexer.lineno}")
    else:
        print(f"Empty File!")
    errors_found += 1


def p_predefined_functions(p):
    """
    predefined_functions : INPUT
                        | output
                        | input
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
    result = ""
    p[0] = {}
    if p[1]["data"][0] == "output":
        result = p[1]["data"][1]
    elif p[1]["data"][0] == "input":
        result = p[1]["data"][1]

    p[0]["code"] = p[1]["code"]
    p[0]["instr"] = p[1]["instr"]
    if "place" in p[1].keys():
        p[0]["place"] = p[1]["place"]
    p[0]["data"] = ("predefined_functions", result)


def p_output(p):
    """output : OUTPUT LEFT_PARENTHESIS primary_expression RIGHT_PARENTHESIS"""
    p[0] = {}
    global output_cntr
    if isinstance(p[3]["data"][1], cppConst):
        if isinstance(p[3]["data"][1].val, str):
            p[0]["instr"] = [[f"outputstr{output_cntr}", str(p[3]["data"][1].val)]]
        else:
            p[0]["instr"] = [
                [f"outputstr{output_cntr}", '"' + str(p[3]["data"][1].val) + '"']
            ]
        output_cntr += 1
    else:
        p[0]["instr"] = p[3]["instr"] + [[f"outputvar", p[3]["place"]]]

    p[0]["code"] = p[3]["code"] + ["    output " + p[3]["place"]]
    p[0]["data"] = ("output", p[3]["data"][1])


def p_input(p):
    """input : INPUT LEFT_PARENTHESIS primary_expression RIGHT_PARENTHESIS"""
    global errors_found
    p[0] = {}
    if not isinstance(p[3]["data"][1], cppId):
        print(
            f"invalid parameter of type {p[3]['data'][1].__class__.__name__} in input function"
        )
        errors_found += 1
    p[0]["instr"] = p[3]["instr"] + [["input", p[3]["place"]]]
    p[0]["code"] = p[3]["code"] + ["    input " + p[3]["place"]]
    p[0]["data"] = ("input", p[3]["data"][1])


def p_primary_expression(p):
    """
    primary_expression : IDENTIFIER
        | constant
        | string
        | LEFT_PARENTHESIS expression RIGHT_PARENTHESIS
        | predefined_functions

    """
    #
    p[0] = {}
    result = ""
    if not isinstance(p[1], (str, int, float)) and (
        p[1]["data"][0] == "constant"
        or p[1]["data"][0] == "string"
        # or p[1]["data"][0] == "predefined_functions"
    ):
        result = p[1]["data"][1]
        p[0]["place"] = symboltab.add_temp_var(p[1]["data"][1]._type.typename)
        p[0]["code"] = ["    " + p[0]["place"] + " = " + str(p[1]["data"][1].val)]
        register_type[p[0]["place"]] = ("temp_reg", p[1]["data"][1]._type.typename)
        p[0]["instr"] = [
            ["constant_assignment", p[0]["place"], str(p[1]["data"][1].val)]
        ]
    elif p[1] == "(":
        result = p[2]["data"][1]

        if "code" in p[2].keys():
            p[0]["code"] = p[2]["code"]
            p[0]["instr"] = p[2]["instr"]
        if "place" in p[2].keys():
            p[0]["place"] = p[2]["place"]

    elif isinstance(p[1], dict) and p[1]["data"][0] == "predefined_functions":
        p[0]["code"] = p[1]["code"]
        p[0]["instr"] = p[1]["instr"]
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"]
        result = p[1]["data"][1]

    else:
        if p[1] in symboltab.get_current_scope().var_to_string_map.keys():
            p[0]["place"] = symboltab.get_current_scope().var_to_string_map[p[1]]
        else:
            p[0]["place"] = symboltab.add_temp_var("int")
        p[0]["code"] = []
        p[0]["instr"] = []
        if p[1] not in symboltab.get_current_scope().variables.keys():
            result = cppId(p[1])
        else:
            result = cppId(p[1], symboltab.get_current_scope().variables[p[1]])
    p[0]["data"] = ("primary_expression", result)


def p_constant(p):
    """
    constant : NUMBER
        | DECIMAL_NUMBER
        | CHARACTER
        | TRUE
        | FALSE
        | NULL
    """
    p[0] = {}

    if isinstance(p[1], int):
        result = cppConst(p[1], cppType("int"))
    elif isinstance(p[1], str) and len(p[1]) == 3:
        result = cppConst(ord(p[1][1]), cppType("char"))
    elif p[1] == "true" or p[1] == "false":
        result = cppConst(p[1], cppType("bool"))
    else:
        result = cppConst(p[1], cppType("float"))

    p[0]["data"] = ("constant", result)


def p_string(p):
    """
    string : STRING_LITERAL
    """
    p[0] = {}

    result = cppConst(p[1], cppType("string"))

    p[0]["data"] = ("string", result)


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
    global tmp_func
    global errors_found
    p[0] = {}
    result = None
    if p[1]["data"][0] == "primary_expression":
        result = cppPostfixExpr(p[1]["data"][1], None)
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"].copy()
            p[0]["instr"] = p[1]["instr"].copy()
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"]

    elif p[1]["data"][0] == "postfix_expression":

        if len(p) == 5 and p[3]["data"][0] == "expression":
            curr_scope = symboltab.get_current_scope()
            tempreg = curr_scope.var_to_string_map[p[1]["data"][1].pf_expr.name]
            array_size = curr_scope.string_to_var_map[tempreg][0].array_size
            array_type = curr_scope.string_to_var_map[tempreg][0]._type.typename
            neg_index = 0
            if p[3]["code"] != []:
                element_index = p[3]["code"][0].split(" = ")[1]

                if "." in element_index:
                    print(
                        f"Index {element_index} of type float invalid for array at line {driver.lexer.lineno}"
                    )
                    errors_found += 1
                if element_index.isnumeric() and array_size <= int(element_index):
                    print(
                        f"Index {element_index} out of bounds for array of size {array_size} at line {driver.lexer.lineno}"
                    )
                    errors_found += 1
                if element_index[1:].isnumeric() and int(element_index) < 0:
                    if int(element_index) < -int(array_size):
                        print(
                            f"Negative index {element_index} out of bounds for array of size {array_size} at line {driver.lexer.lineno}"
                        )
                        errors_found += 1
                    else:
                        neg_index = 1

            var1 = symboltab.add_temp_var("int")
            var2 = symboltab.add_temp_var("int")
            code = [
                "    "
                + var1
                + " = "
                + p[3]["place"]
                + " * "
                + str(dtype_size[array_type])
            ] + ["    " + var2 + " = " + str(dtype_size[array_type] * array_size)]
            register_type[var1] = ("temp_reg", "int")
            register_type[var2] = ("temp_reg", "int")
            instr = []
            instr.append(
                ["multiply_constant", var1, p[3]["place"], str(dtype_size[array_type])]
            )

            if neg_index:
                instr.append(
                    [
                        "constant_assignment",
                        var2,
                        str(dtype_size[array_type] * array_size),
                    ]
                )
                code = code + ["    " + var1 + " = " + var2 + " + " + var1]
                instr.append(["+", var1, var2, var1])
            else:
                # code = code + ["    " + var1 + " = " + var2 + " - " + var1]
                # instr.append(["-", var1, var2, var1])
                pass

            p[0]["code"] = p[1]["code"] + p[3]["code"] + code
            p[0]["instr"] = p[1]["instr"] + p[3]["instr"] + instr

            if isinstance(p[3]["data"][1][0], cppPostfixExpr):
                result = cppPostfixExpr(
                    p[1]["data"][1],
                    cppOp("arr_index"),
                    p[3]["data"][1][0].pf_expr,
                    None,
                )
            # elif isinstance(p[3]["data"][1][0], cppArithExpr):
            #     result = cppPostfixExpr(
            #         p[1]["data"][1],
            #         cppOp("arr_index"),
            #         p[3]["data"][1][0],
            #         None,
            #     )
            else:
                print(
                    f"Cannot handle expression type \"{(p[3]['data'][1][0]).__class__.__name__}\" for array offset at line {driver.lexer.lineno}"
                )
                errors_found += 1

        elif len(p) == 5 and p[3]["data"][0] == "argument_expression_list":

            if p[1]["data"][1].pf_expr.name in symboltab.functions.keys():
                len_params = symboltab.functions[p[1]["data"][1].pf_expr.name][1]
                len_args = len(p[3]["data"][1])
                if len_params == len_args:
                    sign_flag = 1
                    for i in range(len_params):
                        if p[3]["data"][1][
                            i
                        ].pf_expr._type.typename != symboltab.functions[
                            p[1]["data"][1].pf_expr.name
                        ][
                            2
                        ][
                            i
                        ].pdec_type.typename and (
                            p[3]["data"][1][i].pf_expr._type.typename
                            not in ["char", "int", "float"]
                            or symboltab.functions[p[1]["data"][1].pf_expr.name][2][
                                i
                            ].pdec_type.typename
                            not in ["char", "int", "float"]
                        ):
                            sign_flag = 0

                    if sign_flag == 1:

                        result = cppPostfixExpr(
                            p[1]["data"][1], cppOp("func_call"), None, p[3]["data"][1]
                        )
                        p[0]["place"] = symboltab.add_temp_var("int")
                        if p[1]["data"][1].pf_expr.name in symboltab.functions.keys():
                            type = symboltab.functions[p[1]["data"][1].pf_expr.name][0]
                            register_type[p[0]["place"]] = ("temp_reg", type)
                        func_call = p[1]["data"][1].pf_expr.name + "|"

                        stack = str(get_stack_size(p[1]["data"][1].pf_expr.name))
                        push_param, instr = [], "Push_param " + func_call[:-1] + " "
                        exp_sig = "FunCall " + func_call
                        i = 0
                        for var in p[3]["data"][1]:
                            if isinstance(var.pf_expr, cppId):
                                push_param.append(
                                    "    Push_param"
                                    + " : "
                                    + symboltab.get_current_scope().var_to_string_map[
                                        var.pf_expr.name
                                    ]
                                )
                                instr += (
                                    symboltab.get_current_scope().var_to_string_map[
                                        var.pf_expr.name
                                    ]
                                )
                                exp_sig += var.pf_expr._type.typename
                                exp_sig += ","
                            elif isinstance(var.pf_expr, cppConst):
                                if i < len(p[3]["code"]):
                                    reg = p[3]["code"][i].split(" = ")[0]
                                    i = i + 1
                                    push_param.append("    Push_param" + " :" + reg[3:])
                                    instr += reg[3:]
                                    exp_sig += var.pf_expr._type.typename
                                    exp_sig += ","
                        p[0]["code"] = (
                            p[1]["code"]
                            + p[3]["code"]
                            + push_param
                            + [
                                "    "
                                + p[0]["place"]
                                + " = "
                                + (
                                    exp_sig
                                    if exp_sig == "FunCall " + func_call
                                    else exp_sig[:-1]
                                )
                            ]
                        )
                        ###EMPTY INSTRUCTION  [["goto_func_call",func_call[:-1]]]
                        if symboltab.functions[func_call[:-1]][0] != "void":
                            p[0]["instr"] = (
                                p[1]["instr"]
                                + p[3]["instr"]
                                + [instr + " returnto " + p[0]["place"]]
                                # + [["Function_Return", p[0]["place"], func_call[:-1]]]
                            )
                        else:
                            p[0]["instr"] = p[1]["instr"] + p[3]["instr"] + [instr]
                        p[0]["code"] = p[0]["code"] + [
                            "    " + "Remove_from_stack : " + stack + " space"
                        ]
                        ###EMPTY INSTRUCTION
                else:
                    print(
                        f"Function {p[1]['data'][1].pf_expr.name} expects {len_params} args, but {len_args} were given at line {driver.lexer.lineno}"
                    )
                    errors_found += 1
            else:

                result = cppPostfixExpr(
                    p[1]["data"][1], cppOp("func_call"), None, p[3]["data"][1]
                )
                p[0]["place"] = symboltab.add_temp_var("int")
                func_call = p[1]["data"][1].pf_expr.name + "|"
                tmp_func.append(
                    (
                        p[1]["data"][1].pf_expr.name,
                        p[0]["place"],
                        len(p[3]["data"][1]),
                        driver.lexer.lineno,
                    )
                )
                # stack = str(get_stack_size(p[1]["data"][1].pf_expr.name))
                push_param, instr = [], "Push_param " + func_call[:-1] + " "
                exp_sig = "FunCall " + func_call
                i = 0
                for var in p[3]["data"][1]:
                    if isinstance(var.pf_expr, cppId):
                        push_param.append(
                            "    Push_param"
                            + " : "
                            + symboltab.get_current_scope().var_to_string_map[
                                var.pf_expr.name
                            ]
                        )
                        instr += symboltab.get_current_scope().var_to_string_map[
                            var.pf_expr.name
                        ]
                        exp_sig += var.pf_expr._type.typename
                        exp_sig += ","
                    elif isinstance(var.pf_expr, cppConst):
                        if i < len(p[3]["code"]):
                            reg = p[3]["code"][i].split(" = ")[0]
                            i = i + 1
                            push_param.append("    Push_param" + " :" + reg[3:])
                            instr += reg[3:]
                            exp_sig += var.pf_expr._type.typename
                            exp_sig += ","
                p[0]["code"] = (
                    p[1]["code"]
                    + p[3]["code"]
                    + push_param
                    + [
                        "    "
                        + p[0]["place"]
                        + " = "
                        + (
                            exp_sig
                            if exp_sig == "FunCall " + func_call
                            else exp_sig[:-1]
                        )
                    ]
                )
                # if 1 and symboltab.functions[func_call[:-1]][0] != "void":

                ####Recursion will be done only in non void functions
                p[0]["instr"] = (
                    p[1]["instr"]
                    + p[3]["instr"]
                    + [instr + " returnto " + p[0]["place"]]
                )
                # else:
                #     p[0]["instr"] = p[1]["instr"] + p[3]["instr"] + [instr]
                #     p[0]["code"] = p[0]["code"] + ["    " + "Remove_from_stack : " + stack + " space"]

            # else:
            #     print(
            #         f"Function {p[1]['data'][1].pf_expr.name} called without declaration at line {driver.lexer.lineno}"
            #     )
        elif p[2] == "." or p[2] == "->":
            _struct_type = (
                symboltab.get_current_scope()
                .variables[p[1]["data"][1].pf_expr.name]
                .typename.split("_")[0]
            )

            _name = p[1]["data"][1].pf_expr.name
            _var = p[3]

            _name = f"{_struct_type}_{_name}_{_var}"
            if _name in symboltab.get_current_scope().var_to_string_map.keys():
                p[0]["place"] = symboltab.get_current_scope().var_to_string_map[_name]
            else:
                p[0]["place"] = ""

            p[0]["code"] = []
            p[0]["instr"] = []
            result = cppPostfixExpr(p[1]["data"][1], cppOp(p[2]), None, cppId(p[3]))

        elif len(p) == 4:
            result = cppPostfixExpr(p[1]["data"][1], cppOp("func_call"), None, None)
            func_call = p[1]["data"][1].pf_expr.name + "|"
            stack = str(get_stack_size(p[1]["data"][1].pf_expr.name))
            exp_sig = "FunCall " + func_call
            p[0]["place"] = symboltab.add_temp_var("int")
            if p[1]["data"][1].pf_expr.name in symboltab.functions.keys():
                type = symboltab.functions[p[1]["data"][1].pf_expr.name][0]
                register_type[p[0]["place"]] = ("temp_reg", type)
            p[0]["code"] = p[1]["code"] + [
                "    "
                + p[0]["place"]
                + " = "
                + (exp_sig if exp_sig == "FunCall " + func_call else exp_sig[:-1])
            ]
            if symboltab.functions[func_call[:-1]][0] != "void":
                p[0]["instr"] = p[1]["instr"] + [
                    ["Function_Call", func_call[:-1], "returnto", p[0]["place"]]
                ]
            else:
                p[0]["instr"] = p[1]["instr"] + [["Function_Call", func_call[:-1]]]
            p[0]["code"] = p[0]["code"] + [
                "    " + "Remove_from_stack : " + stack + " space"
            ]
            ###EMPTY INSTRUCTION
            # p[0]["instr"] = [["Function_Related"]]
        else:
            result = cppPostfixExpr(p[1]["data"][1], cppOp(p[2]), None, None)
            var = symboltab.add_temp_var("int")
            register_type[var] = ("temp_reg", "int")
            if p[2] == "--":
                p[0]["code"] = (
                    p[1]["code"]
                    + ["    " + var + " = " + "1"]
                    + ["    " + p[1]["place"] + " = " + p[1]["place"] + " - " + var]
                )
                p[0]["instr"] = (
                    p[1]["instr"]
                    + [["constant_assignment", var, "1"]]
                    + [["-", p[1]["place"], p[1]["place"], var]]
                )

            elif p[2] == "++":
                p[0]["code"] = (
                    p[1]["code"]
                    + ["    " + var + " = " + "1"]
                    + ["    " + p[1]["place"] + " = " + p[1]["place"] + " + " + var]
                )
                p[0]["instr"] = (
                    p[1]["instr"]
                    + [["constant_assignment", var, "1"]]
                    + [["+", p[1]["place"], p[1]["place"], var]]
                )
    p[0]["data"] = ("postfix_expression", result)


def p_argument_expression_list(p):
    """
    argument_expression_list : assignment_expression
        | argument_expression_list COMMA assignment_expression
    """
    p[0] = {}

    if p[1]["data"][0] == "assignment_expression":
        result = [p[1]["data"][1]]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"]
            p[0]["instr"] = p[1]["instr"]
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"]
    else:
        result = p[1]["data"][1] + [p[3]["data"][1]]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"].copy() + p[3]["code"].copy()
            p[0]["instr"] = p[1]["instr"].copy() + p[3]["instr"].copy()
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"] + p[3]["place"]

    p[0]["data"] = ("argument_expression_list", result)


def p_unary_expression(p):
    """
    unary_expression : postfix_expression
        | PLUS_PLUS unary_expression
        | MINUS_MINUS unary_expression
        | unary_operator cast_expression
        | SIZEOF LEFT_PARENTHESIS type_specifier RIGHT_PARENTHESIS
    """
    # | SIZEOF unary_expression
    p[0] = {}

    if len(p) == 2:

        result = p[1]["data"][1]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"]
            p[0]["instr"] = p[1]["instr"]
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"]
    elif p[2]["data"][0] == "unary_expression":
        result = cppUnExpr(p[2]["data"][1], cppOp(p[1]))
        if "code" in p[2].keys() and "place" in p[2].keys():
            var = symboltab.add_temp_var("int")
            register_type[var] = ("temp_reg", "int")
            if p[1] == "--":
                p[0]["code"] = (
                    p[2]["code"]
                    + ["    " + var + " = " + "1"]
                    + ["    " + p[2]["place"] + " = " + p[2]["place"] + " - " + var]
                )
                p[0]["instr"] = (
                    p[2]["instr"]
                    + [["constant_assignment", var, "1"]]
                    + [["-", p[2]["place"], p[2]["place"], var]]
                )
            elif p[1] == "++":
                p[0]["code"] = (
                    p[2]["code"]
                    + ["    " + var + " = " + "1"]
                    + ["    " + p[2]["place"] + " = " + p[2]["place"] + " + " + var]
                )
                p[0]["instr"] = (
                    p[2]["instr"]
                    + [["constant_assignment", var, "1"]]
                    + [["+", p[2]["place"], p[2]["place"], var]]
                )
    elif p[2]["data"][0] == "cast_expression":
        if p[1]["data"][1].op == "-" or p[1]["data"][1].op == "+":
            pre = -1 if p[1]["data"][1].op == "-" else 1
            # temp = symboltab.add_temp_var(p[2]["data"][1].expr_type)
            if "place" not in p[0].keys():
                p[0]["place"] = symboltab.add_temp_var("int")
                register_type[p[0]["place"]] = (
                    "temp_reg",
                    p[2]["data"][1].pf_expr._type.typename,
                )
            p[0]["code"] = [
                "    " + p[0]["place"] + " = " + str(pre * p[2]["data"][1].pf_expr.val)
            ]
            p[0]["instr"] = [
                [
                    "constant_assignment",
                    p[0]["place"],
                    str(pre * p[2]["data"][1].pf_expr.val),
                ]
            ]

            if isinstance(p[2]["data"][1].expr_type, str):
                result = cppPostfixExpr(
                    cppConst(
                        pre * p[2]["data"][1].pf_expr.val,
                        cppType(p[2]["data"][1].expr_type),
                    ),
                    None,
                )
            elif isinstance(p[2]["data"][1].expr_type, cppType):
                result = cppPostfixExpr(
                    cppConst(
                        pre * p[2]["data"][1].pf_expr.val,
                        cppType(p[2]["data"][1].expr_type.typename),
                    ),
                    None,
                )

        elif p[1]["data"][1].op == "&":

            if "place" not in p[0].keys():
                p[0]["place"] = symboltab.add_temp_var("int")
                register_type[p[0]["place"]] = (
                    "temp_reg",
                    p[2]["data"][1].pf_expr._type.typename,
                )
                p[0]["code"] = ["    " + p[0]["place"] + " = & " + p[2]["place"]]
                p[0]["instr"] = [["address_assignment", p[0]["place"], p[2]["place"]]]
                result = cppUnExpr(p[2]["data"][1], p[1]["data"][1])
        elif p[1]["data"][1].op == "*":
            if "place" not in p[0].keys():
                ptr_reg = symboltab.get_current_scope().var_to_string_map[
                    p[2]["data"][1].pf_expr.name
                ]
                ptr_reg_type = p[2]["data"][1].pf_expr._type.typename.split("_")[1]
                p[0]["place"] = symboltab.add_temp_var(ptr_reg_type)
                register_type[p[0]["place"]] = ("temp_reg", ptr_reg_type)
                p[0]["code"] = ["    *" + p[0]["place"]]
                p[0]["instr"] = p[2]["instr"] + [
                    ["pointer_deref", p[0]["place"], ptr_reg]
                ]
                p[0]["code"] = p[2]["code"] + [
                    ["pointer_deref" + " " + p[0]["place"] + " " + ptr_reg]
                ]

            result = cppUnExpr(p[2]["data"][1], p[1]["data"][1])
        else:
            result = cppUnExpr(p[2]["data"][1], p[1]["data"][1])
    # elif p[2][1] == "unary_expression":
    #     result = cppUnExpr(p[2][1], p[1])
    elif p[2] == "(":
        result = cppUnExpr(p[3]["data"][1], cppOp(p[1]))

    p[0]["data"] = ("unary_expression", result)


def p_unary_operator(p):
    """
    unary_operator : AND
                   | STAR
                   | PLUS
                   | MINUS
                   | NOT
                   | TILDE
    """
    p[0] = {}

    result = cppOp(p[1])

    p[0]["data"] = ("unary_operator", result)


def p_cast_expression(p):
    """
    cast_expression : unary_expression
        | LEFT_PARENTHESIS type_specifier RIGHT_PARENTHESIS cast_expression
    """
    p[0] = {}

    if p[1] == "(":
        result = cppCastExpr(p[4]["data"][1], None, p[2]["data"][1])
        # p[0]["place"] = symboltab.add_temp_var(p[2])
        # if "place" in p[4].keys():
        #     p[0]["code"] = p[4]["code"]+[p[0]["place"]+" = "+p[1]["place"]+" "+p[2]+" "+p[3]["place"]]

    else:
        result = p[1]["data"][1]
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"]
            p[0]["instr"] = p[1]["instr"]

    p[0]["data"] = ("cast_expression", result)


def p_multiplicative_expression(p):
    """
    multiplicative_expression : cast_expression
        | multiplicative_expression STAR cast_expression
        | multiplicative_expression DIVIDE cast_expression
        | multiplicative_expression MODULUS cast_expression
    """
    p[0] = {}

    if p[1]["data"][0] == "multiplicative_expression":
        result = cppArithExpr(p[1]["data"][1], cppOp(p[2]), p[3]["data"][1])
        p[0]["place"] = symboltab.add_temp_var("int")
        register_type[p[0]["place"]] = symboltab.find_type(p[1]["place"], p[3]["place"])
        if "place" in p[1].keys() and "place" in p[3].keys():
            p[0]["instr"] = (
                p[1]["instr"]
                + p[3]["instr"]
                + [[p[2], p[0]["place"], p[1]["place"], p[3]["place"]]]
            )
            p[0]["code"] = (
                p[1]["code"]
                + p[3]["code"]
                + [
                    "    "
                    + p[0]["place"]
                    + " = "
                    + p[1]["place"]
                    + " "
                    + p[2]
                    + " "
                    + p[3]["place"]
                ]
            )

    else:
        result = p[1]["data"][1]
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"]
            p[0]["instr"] = p[1]["instr"]
    p[0]["data"] = ("multiplicative_expression", result)


def p_additive_expression(p):
    """
    additive_expression : multiplicative_expression
        | additive_expression PLUS multiplicative_expression
        | additive_expression MINUS multiplicative_expression
    """
    p[0] = {}

    if p[1]["data"][0] == "multiplicative_expression":
        result = p[1]["data"][1]
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"]
            p[0]["instr"] = p[1]["instr"]
    else:
        result = cppArithExpr(p[1]["data"][1], cppOp(p[2]), p[3]["data"][1])
        p[0]["place"] = symboltab.add_temp_var("int")
        if "place" not in p[1].keys():
            p[1]["place"] = symboltab.add_temp_var("int")
        if "place" not in p[3].keys():
            p[3]["place"] = symboltab.add_temp_var("int")

        register_type[p[0]["place"]] = symboltab.find_type(p[1]["place"], p[3]["place"])
        p[0]["code"] = (
            p[1]["code"]
            + p[3]["code"]
            + [
                "    "
                + p[0]["place"]
                + " = "
                + p[1]["place"]
                + " "
                + p[2]
                + " "
                + p[3]["place"]
            ]
        )
        p[0]["instr"] = (
            p[1]["instr"]
            + p[3]["instr"]
            + [[p[2], p[0]["place"], p[1]["place"], p[3]["place"]]]
        )

    p[0]["data"] = ("additive_expression", result)


def p_shift_expression(p):
    """
    shift_expression : additive_expression
        | shift_expression LEFT_SHIFT additive_expression
        | shift_expression RIGHT_SHIFT additive_expression
    """
    p[0] = {}

    if p[1]["data"][0] == "additive_expression":
        result = p[1]["data"][1]
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"]
            p[0]["instr"] = p[1]["instr"]
    else:
        result = cppShiftExpr(p[1]["data"][1], cppOp(p[2]), p[3]["data"][1])
        p[0]["place"] = symboltab.add_temp_var("int")
        if "place" in p[1].keys() and "place" in p[3].keys():
            p[0]["instr"] = (
                p[1]["instr"]
                + p[3]["instr"]
                + [[p[2], p[0]["place"], p[1]["place"], p[3]["place"]]]
            )
            p[0]["code"] = (
                p[1]["code"]
                + p[3]["code"]
                + [
                    p[0]["place"]
                    + " = "
                    + p[1]["place"]
                    + " "
                    + p[2]
                    + " "
                    + p[3]["place"]
                ]
            )
        register_type[p[0]["place"]] = symboltab.find_type(p[1]["place"], p[3]["place"])
    p[0]["data"] = ("shift_expression", result)


def p_relational_expression(p):
    """
    relational_expression : shift_expression
        | relational_expression LESS_THAN shift_expression
        | relational_expression GREATER_THAN shift_expression
        | relational_expression LESS_THAN_EQUALS shift_expression
        | relational_expression GREATER_THAN_EQUALS shift_expression
    """
    p[0] = {}

    if p[1]["data"][0] == "shift_expression":
        result = p[1]["data"][1]
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"]
            p[0]["instr"] = p[1]["instr"]
    else:
        result = cppRelationExpr(p[1]["data"][1], cppOp(p[2]), p[3]["data"][1])
        p[0]["place"] = symboltab.add_temp_var("int")
        if "place" in p[1].keys() and "place" in p[3].keys():
            p[0]["instr"] = (
                p[1]["instr"]
                + p[3]["instr"]
                + [[p[2], p[0]["place"], p[1]["place"], p[3]["place"]]]
            )
            p[0]["code"] = (
                p[1]["code"]
                + p[3]["code"]
                + [
                    "    "
                    + p[2]
                    + " "
                    + p[0]["place"]
                    + " "
                    + p[1]["place"]
                    + " "
                    + p[3]["place"]
                ]
            )
        register_type[p[0]["place"]] = symboltab.find_type(p[1]["place"], p[3]["place"])
    p[0]["data"] = ("relational_expression", result)


def p_equality_expression(p):
    """
    equality_expression : relational_expression
        |  equality_expression EQUALS_EQUALS relational_expression
        |  equality_expression NOT_EQUALS relational_expression
    """
    p[0] = {}

    if p[1]["data"][0] == "relational_expression":
        result = p[1]["data"][1]
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"]
            p[0]["instr"] = p[1]["instr"]
    else:
        result = cppRelationExpr(p[1]["data"][1], cppOp(p[2]), p[3]["data"][1])
        p[0]["place"] = symboltab.add_temp_var("int")
        if "place" in p[1].keys() and "place" in p[3].keys():
            p[0]["instr"] = (
                p[1]["instr"]
                + p[3]["instr"]
                + [[p[2], p[0]["place"], p[1]["place"], p[3]["place"]]]
            )
            p[0]["code"] = (
                p[1]["code"]
                + p[3]["code"]
                + [
                    "    "
                    + p[2]
                    + " "
                    + p[0]["place"]
                    + " "
                    + p[1]["place"]
                    + " "
                    + p[3]["place"]
                ]
            )
        register_type[p[0]["place"]] = symboltab.find_type(p[1]["place"], p[3]["place"])
    p[0]["data"] = ("equality_expression", result)


def p_and_expression(p):
    """
    and_expression : equality_expression
        | and_expression AND equality_expression
    """
    p[0] = {}

    if p[1]["data"][0] == "equality_expression":
        result = p[1]["data"][1]
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"]
            p[0]["instr"] = p[1]["instr"]
    else:
        result = cppLogicExpr(p[1]["data"][1], cppOp(p[2]), p[3]["data"][1])
        p[0]["place"] = symboltab.add_temp_var("int")
        if "place" in p[1].keys() and "place" in p[3].keys():
            p[0]["instr"] = (
                p[1]["instr"]
                + p[3]["instr"]
                + [[p[2], p[0]["place"], p[1]["place"], p[3]["place"]]]
            )
            p[0]["code"] = (
                p[1]["code"]
                + p[3]["code"]
                + [
                    "    "
                    + p[2]
                    + " "
                    + p[0]["place"]
                    + " "
                    + p[1]["place"]
                    + " "
                    + p[3]["place"]
                ]
            )
        register_type[p[0]["place"]] = symboltab.find_type(p[1]["place"], p[3]["place"])
    p[0]["data"] = ("and_expression", result)


def p_xor_expression(p):
    """
    xor_expression : and_expression
        | xor_expression XOR and_expression
    """
    p[0] = {}

    if p[1]["data"][0] == "and_expression":
        result = p[1]["data"][1]
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"]
            p[0]["instr"] = p[1]["instr"]
    else:
        result = cppLogicExpr(p[1]["data"][1], cppOp(p[2]), p[3]["data"][1])

        p[0]["place"] = symboltab.add_temp_var("int")
        if "place" in p[1].keys() and "place" in p[3].keys():
            p[0]["instr"] = (
                p[1]["instr"]
                + p[3]["instr"]
                + [[p[2], p[0]["place"], p[1]["place"], p[3]["place"]]]
            )

            p[0]["code"] = (
                p[1]["code"]
                + p[3]["code"]
                + [
                    "    "
                    + p[2]
                    + " "
                    + p[0]["place"]
                    + " "
                    + p[1]["place"]
                    + " "
                    + p[3]["place"]
                ]
            )
        register_type[p[0]["place"]] = symboltab.find_type(p[1]["place"], p[3]["place"])
    p[0]["data"] = ("xor_expression", result)


def p_or_expression(p):
    """
    or_expression : xor_expression
        | or_expression OR xor_expression
    """
    p[0] = {}

    if p[1]["data"][0] == "xor_expression":
        result = p[1]["data"][1]
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"]
            p[0]["instr"] = p[1]["instr"]
    else:
        result = cppLogicExpr(p[1]["data"][1], cppOp(p[2]), p[3]["data"][1])

        p[0]["place"] = symboltab.add_temp_var("int")
        if "place" in p[1].keys() and "place" in p[3].keys():
            p[0]["instr"] = (
                p[1]["instr"]
                + p[3]["instr"]
                + [[p[2], p[0]["place"], p[1]["place"], p[3]["place"]]]
            )
            p[0]["code"] = (
                p[1]["code"]
                + p[3]["code"]
                + [
                    "    "
                    + p[2]
                    + " "
                    + p[0]["place"]
                    + " "
                    + p[1]["place"]
                    + " "
                    + p[3]["place"]
                ]
            )
        register_type[p[0]["place"]] = symboltab.find_type(p[1]["place"], p[3]["place"])
    p[0]["data"] = ("or_expression", result)


def p_logical_and_expression(p):
    """
    logical_and_expression : or_expression
        | logical_and_expression AND_AND or_expression
    """
    p[0] = {}

    if p[1]["data"][0] == "or_expression":
        result = p[1]["data"][1]
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"]
            p[0]["instr"] = p[1]["instr"]
    else:
        result = cppLogicExpr(p[1]["data"][1], cppOp(p[2]), p[3]["data"][1])
        p[0]["place"] = symboltab.add_temp_var("int")
        if "place" in p[1].keys() and "place" in p[3].keys():
            p[0]["instr"] = (
                p[1]["instr"]
                + p[3]["instr"]
                + [[p[2], p[0]["place"], p[1]["place"], p[3]["place"]]]
            )
            p[0]["code"] = (
                p[1]["code"]
                + p[3]["code"]
                + [
                    "    "
                    + p[2]
                    + " "
                    + p[0]["place"]
                    + " "
                    + p[1]["place"]
                    + " "
                    + p[3]["place"]
                ]
            )
        register_type[p[0]["place"]] = symboltab.find_type(p[1]["place"], p[3]["place"])
    p[0]["data"] = ("logical_and_expression", result)


def p_logical_or_expression(p):
    """
    logical_or_expression : logical_and_expression
        | logical_or_expression OR_OR logical_and_expression
    """
    p[0] = {}

    if p[1]["data"][0] == "logical_and_expression":
        result = p[1]["data"][1]
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"]
            p[0]["instr"] = p[1]["instr"]
    else:
        result = cppLogicExpr(p[1]["data"][1], cppOp(p[2]), p[3]["data"][1])
        p[0]["place"] = symboltab.add_temp_var("int")
        if "place" in p[1].keys() and "place" in p[3].keys():
            p[0]["instr"] = (
                p[1]["instr"]
                + p[3]["instr"]
                + [[p[2], p[0]["place"], p[1]["place"], p[3]["place"]]]
            )
            p[0]["code"] = (
                p[1]["code"]
                + p[3]["code"]
                + [
                    "    "
                    + p[2]
                    + " "
                    + p[0]["place"]
                    + " "
                    + p[1]["place"]
                    + " "
                    + p[3]["place"]
                ]
            )
        register_type[p[0]["place"]] = symboltab.find_type(p[1]["place"], p[3]["place"])
    p[0]["data"] = ("logical_or_expression", result)


def p_conditional_expression(p):
    """
    conditional_expression : logical_or_expression
        |  logical_or_expression QUESTION_MARK expression COLON conditional_expression
    """
    p[0] = {}

    if p[1]["data"][0] == "logical_or_expression":
        result = p[1]["data"][1]
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"]
            p[0]["instr"] = p[1]["instr"]
    else:
        result = cppCondExpr(p[1]["data"][1], p[3]["data"][1], p[5]["data"][1])

    p[0]["data"] = ("conditional_expression", result)


def p_assignment_expression(p):
    """
    assignment_expression : conditional_expression
        | unary_expression assignment_operator assignment_expression

    """
    p[0] = {}
    curr_scope = symboltab.get_current_scope()
    if "place" in p[1].keys():
        p[0]["place"] = p[1]["place"]
    if p[1]["data"][0] == "conditional_expression":
        result = p[1]["data"][1]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"].copy()
            p[0]["instr"] = p[1]["instr"].copy()

    else:
        result = cppAssignExpr(
            cppUnExpr(p[1]["data"][1], None), p[2]["data"][1], p[3]["data"][1]
        )
        code, instr = [], []

        if "place" in p[3].keys():
            rhs = p[3]["place"]
            if p[2]["data"][1].op == "=":

                # Pointer deref
                if (
                    isinstance(p[1]["data"][1], cppUnExpr)
                    and p[1]["data"][1].un_op.op == "*"
                ):
                    code = ["    " + "*" + p[1]["place"] + " = " + str(rhs)]
                    instr.append(
                        [
                            "assignment_expression",
                            p[1]["place"],
                            str(rhs),
                        ]
                    )
                    code = ["    " + "*" + p[1]["place"] + " = " + str(rhs)]
                    instr.append(
                        [
                            "var_allocation_at_ptr",
                            curr_scope.var_to_string_map[
                                p[1]["data"][1].un_expr.pf_expr.name
                            ],
                            p[1]["place"],
                        ]
                    )
                elif (
                    isinstance(p[3]["data"][1], cppUnExpr)
                    and p[3]["data"][1].un_op.op == "*"
                ):
                    code = ["    " + "*" + p[3]["place"] + " = " + str(rhs)]
                    instr.append(
                        [
                            "assignment_expression",
                            p[1]["place"],
                            str(rhs),
                        ]
                    )
                # Array case
                elif isinstance(p[1]["data"][1].pf_expr, cppPostfixExpr):
                    if isinstance(p[1]["data"][1].pf_offset, cppId):
                        if (
                            p[1]["data"][1].pf_expr.pf_expr.name
                            in curr_scope.var_to_string_map.keys()
                        ):
                            code = [
                                "    "
                                + curr_scope.var_to_string_map[
                                    p[1]["data"][1].pf_expr.pf_expr.name
                                ]
                                + " "
                                + p[1]["instr"][-1][1]
                                + " = "
                                + str(rhs)
                            ]
                            instr.append(
                                [
                                    "assign_to_array",
                                    curr_scope.var_to_string_map[
                                        p[1]["data"][1].pf_expr.pf_expr.name
                                    ],
                                    p[1]["instr"][-1][1],
                                    str(rhs),
                                ]
                            )

                    elif (
                        isinstance(p[1]["data"][1], cppPostfixExpr)
                        and p[1]["data"][1].pf_op.op == "."
                    ):
                        _struct_type = (
                            symboltab.get_current_scope()
                            .variables[
                                p[1]["data"][1].pf_expr.pf_expr.name.split("_")[0]
                            ]
                            .typename.split("_")[0]
                        )

                        _name = p[1]["data"][1].pf_expr.pf_expr.name
                        _var = p[1]["data"][1].pf_id.name

                        _name = f"{_struct_type}_{_name}_{_var}"
                        code = ["    " + p[1]["place"] + " " + " = " + str(rhs)]
                        instr.append(
                            [
                                "assignment_expression",
                                p[1]["place"],
                                str(rhs),
                            ]
                        )
                    else:
                        if (
                            p[1]["data"][1].pf_expr.pf_expr.name
                            in curr_scope.var_to_string_map.keys()
                        ):
                            code = [
                                "    "
                                + curr_scope.var_to_string_map[
                                    p[1]["data"][1].pf_expr.pf_expr.name
                                ]
                                + " "
                                + p[1]["instr"][-1][1]
                                + " = "
                                + str(rhs)
                            ]

                            instr.append(
                                [
                                    "assign_to_array",
                                    curr_scope.var_to_string_map[
                                        p[1]["data"][1].pf_expr.pf_expr.name
                                    ],
                                    p[1]["instr"][-1][1],
                                    str(rhs),
                                ]
                            )
                elif (
                    isinstance(p[1]["data"][1], cppPostfixExpr)
                    and isinstance(p[3]["data"][1], cppUnExpr)
                    and p[3]["data"][1].un_op.op == "&"
                ):
                    code = [
                        "    "
                        + curr_scope.var_to_string_map[p[1]["data"][1].pf_expr.name]
                        + " = "
                        + str(rhs)
                    ]

                    instr.append(
                        [
                            "assignment_expression",
                            curr_scope.var_to_string_map[p[1]["data"][1].pf_expr.name],
                            str(rhs),
                        ]
                    )
                else:
                    if (
                        p[1]["data"][1].pf_expr.name
                        in curr_scope.var_to_string_map.keys()
                    ):
                        code = [
                            "    "
                            + curr_scope.var_to_string_map[p[1]["data"][1].pf_expr.name]
                            + " = "
                            + str(rhs)
                        ]
                        instr.append(
                            [
                                "assignment_expression",
                                curr_scope.var_to_string_map[
                                    p[1]["data"][1].pf_expr.name
                                ],
                                str(rhs),
                            ]
                        )
                # Add array case
            else:
                assigner = symboltab.add_temp_var("int")
                code = [
                    "    "
                    + assigner
                    + " = "
                    + curr_scope.var_to_string_map[p[1]["data"][1].pf_expr.name]
                    + " "
                    + p[2]["data"][1].op[0]
                    + " "
                    + str(rhs)
                ]
                register_type[assigner] = symboltab.find_type(
                    curr_scope.var_to_string_map[p[1]["data"][1].pf_expr.name], str(rhs)
                )
                instr.append(
                    [
                        p[2]["data"][1].op[0],
                        assigner,
                        curr_scope.var_to_string_map[p[1]["data"][1].pf_expr.name],
                        str(rhs),
                    ]
                )
                code = code + [
                    "    "
                    + curr_scope.var_to_string_map[p[1]["data"][1].pf_expr.name]
                    + " = "
                    + assigner
                ]
                instr.append(
                    [
                        "assignment_expression",
                        curr_scope.var_to_string_map[p[1]["data"][1].pf_expr.name],
                        assigner,
                    ]
                )

        else:
            if p[3]["data"][1] and p[3]["data"][1].pf_expr:
                var = curr_scope.var_to_string_map[p[3]["data"][1].pf_expr.pf_expr.name]
                if "place" in p[1].keys():
                    code = [
                        "    "
                        + p[1]["place"]
                        + " = "
                        + p[3]["instr"][-1][1]
                        + " "
                        + var
                    ]
                    instr.append(
                        ["assign_from_array", p[1]["place"], p[3]["instr"][-1][1], var]
                    )

                # register_type[var] = ("temp_reg", "int")

        if "code" in p[3].keys() and "code" in p[1].keys():

            p[0]["code"] = p[3]["code"].copy() + p[1]["code"].copy() + code
            p[0]["instr"] = p[3]["instr"].copy() + p[1]["instr"].copy() + instr

    p[0]["data"] = ("assignment_expression", result)


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
    p[0] = {}

    result = cppOp(p[1])
    p[0]["data"] = ("assignment_operator", result)


def p_expression(p):
    """
    expression : assignment_expression
        | expression COMMA assignment_expression
    """
    p[0] = {}
    if "place" in p[1].keys():
        p[0]["place"] = p[1]["place"]
    if p[1]["data"][0] == "assignment_expression":
        result = [p[1]["data"][1]]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"]
            p[0]["instr"] = p[1]["instr"]
    else:
        result = p[1]["data"][1] + [p[3]["data"][1]]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"] + p[2]["code"]
            p[0]["instr"] = p[1]["instr"] + p[2]["instr"]

    p[0]["data"] = ("expression", result)


def p_declaration(p):
    """
    declaration : type_specifier SEMICOLON
                | type_specifier init_declarators_list SEMICOLON
                | class_specifier
    """
    p[0] = {}

    if len(p) == 2:
        result = cppDeclaration(cppType(p[1]["data"][1].c_name.name), None)
    elif len(p) == 3:
        result = cppDeclaration(p[1]["data"][1], None)
    else:
        result = cppDeclaration(p[1]["data"][1], p[2]["data"][1])
    p[0]["data"] = ("declaration", result)


def p_init_declarators_list(p):
    """
    init_declarators_list : init_declarator
        | init_declarators_list COMMA init_declarator
    """
    p[0] = {}

    if p[1]["data"][0] == "init_declarator":
        result = [p[1]["data"][1]]
    else:
        result = p[1]["data"][1] + [p[3]["data"][1]]

    p[0]["data"] = ("init_declarators_list", result)


def p_init_declarator(p):
    """
    init_declarator : declarator EQUALS initializer
                    | declarator

    """
    p[0] = {}

    if len(p) == 2:
        result = cppInitDeclarator(p[1]["data"][1], None)
    else:
        result = cppInitDeclarator(p[1]["data"][1], p[3]["data"][1])

    p[0]["data"] = ("init_declarator", result)


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
    p[0] = {}

    if p[1] == "class":
        result = cppType(f"{p[1]}_class")
    elif isinstance(p[1], dict) and p[1]["data"][0] == "struct_specifier":
        result = cppType(f"{p[1]['data'][1].s_tag.name}_struct")

    else:
        result = cppType(p[1])

    p[0]["data"] = ("type_specifier", result)


def p_pointer(p):
    """
    pointer : STAR
            | STAR pointer
    """
    p[0] = {}
    p[0]["data"] = ("pointer", None)


def p_identifier_list(p):
    """
    identifier_list : IDENTIFIER
                    | identifier_list COMMA IDENTIFIER
    """
    p[0] = {}

    if len(p) == 2:
        result = [cppId(p[1])]
    else:
        result = p[1]["data"][1] + [cppId(p[3])]

    p[0]["data"] = ("identifier_list", result)


def p_specifier_list(p):
    """
    specifier_list : type_specifier specifier_list
                   | type_specifier
    """
    p[0] = {}

    if len(p) == 2:
        result = [p[1]["data"][1]]
    else:
        result = [p[1]["data"][1]] + p[2]["data"][1]

    p[0]["data"] = ("specifier_list", result)


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

    p[0] = {}

    result = cppDirectDeclarator(None, None, None, None, None, -1)
    if len(p) == 2:
        result = cppDirectDeclarator(cppId(p[1], None), None, None, None, None, 1)
    elif len(p) == 4:
        if p[1] == "(":
            result = cppDirectDeclarator(
                p[2]["data"][1].name, None, p[2]["data"][1], None, None, 2
            )
        elif p[2] == "[":

            result = cppDirectDeclarator(None, p[1]["data"][1], None, None, None, 4)
        elif p[2] == "(":
            result = cppDirectDeclarator(None, p[1]["data"][1], None, None, None, 7)

    elif len(p) == 5:
        if p[3]["data"][0] == "conditional_expression":
            result = cppDirectDeclarator(
                p[1]["data"][1].name, p[1]["data"][1], None, None, p[3]["data"][1], 3
            )
        if p[3]["data"][0] == "parameter_list":
            result = cppDirectDeclarator(
                None, p[1]["data"][1], None, p[3]["data"][1], None, 7
            )
        if p[3]["data"][0] == "identifier_list":
            result = cppDirectDeclarator(
                None, p[1]["data"][1], None, p[3]["data"][1], None, 6
            )

    p[0]["data"] = ("direct_declarator", result)


def p_declarator(p):
    """
    declarator : pointer direct_declarator
               | direct_declarator
    """
    p[0] = {}

    if p[1]["data"][0] == "pointer":
        result = cppDeclarator(p[2]["data"][1].name, p[2]["data"][1], None, True)
    else:
        result = cppDeclarator(p[1]["data"][1].name, p[1]["data"][1], None)

    p[0]["data"] = ("declarator", result)


def p_parameter_list(p):
    """
    parameter_list : parameter_declaration
                   | parameter_list COMMA parameter_declaration
    """
    p[0] = {}

    if p[1]["data"][0] == "parameter_declaration":
        result = [p[1]["data"][1]]
    else:
        result = p[1]["data"][1] + [p[3]["data"][1]]

    p[0]["data"] = ("parameter_list", result)


def p_parameter_declaration(p):
    """
    parameter_declaration : type_specifier declarator
                          | type_specifier abstract_declarator
                          | type_specifier
    """
    p[0] = {}
    global curr_param
    if len(p) > 2:
        symboltab.check_and_add_variable(p[2]["data"][1].name, p[1]["data"][1])
        curr_param.append(p[2]["data"][1].name.name)
        curr_scope = symboltab.get_current_scope()
        register_type[curr_scope.var_to_string_map[p[2]["data"][1].name.name]] = (
            "reg",
            p[1]["data"][1].typename,
        )
        result = cppParamDeclaration(p[1]["data"][1], p[2]["data"][1])
    else:
        result = cppParamDeclaration(p[1]["data"][1], None)

    p[0]["data"] = ("parameter_declaration", result)


# Structs
def p_struct_specifier(p):
    """
    struct_specifier : STRUCT IDENTIFIER LEFT_CURLY_BRACKET struct_declaration_list RIGHT_CURLY_BRACKET
                     | STRUCT LEFT_CURLY_BRACKET struct_declaration_list RIGHT_CURLY_BRACKET
                     | STRUCT IDENTIFIER LEFT_CURLY_BRACKET RIGHT_CURLY_BRACKET
                     | STRUCT LEFT_CURLY_BRACKET RIGHT_CURLY_BRACKET
                     | STRUCT IDENTIFIER
    """
    p[0] = {}

    if len(p) == 6:
        result = cppStruct(cppId(p[2]), cppId(p[2]), p[4]["data"][1])
        symboltab.cmpd_ctr += 1
    elif len(p) == 5 and p[2] == "{":
        result = cppStruct(None, None, p[3]["data"][1])
        symboltab.cmpd_ctr += 1
    elif len(p) == 5 and p[3] == "{":
        result = cppStruct(cppId(p[2]), cppId(p[2]), None)
        symboltab.cmpd_ctr += 1

    elif len(p) == 4:
        result = cppStruct(None, None, None)
        symboltab.cmpd_ctr += 1

    elif len(p) == 3:
        result = cppStruct(cppId(p[2]), cppId(p[2]), None, 1)
        # result = cppStruct(None, cppId(p[2]), None, 1)

    p[0]["data"] = ("struct_specifier", result)


def p_struct_declarator(p):
    """
    struct_declarator : declarator
                      | COLON conditional_expression
                      | declarator COLON conditional_expression
    """
    p[0] = {}

    if p[1]["data"][0] == "declarator":
        result = cppStructDeclarator(p[1]["data"][1], None)
    elif p[1] == "COLON":
        result = cppStructDeclarator(None, p[2]["data"][1])
    else:
        result = cppStructDeclarator(p[1]["data"][1], p[3]["data"][1])

    p[0]["data"] = ("struct_declarator", result)


def p_struct_declarator_list(p):
    """
    struct_declarator_list : struct_declarator
                           | struct_declarator_list COMMA struct_declarator
    """
    p[0] = {}

    if p[1]["data"][0] == "struct_declarator":
        result = [p[1]["data"][1]]
    else:
        result = p[1]["data"][1] + [p[3]["data"][1]]

    p[0]["data"] = ("struct_declarator_list", result)


def p_struct_declaration(p):
    """
    struct_declaration : specifier_list struct_declarator_list SEMICOLON
    """
    p[0] = {}

    result = cppStructDeclaration(p[1]["data"][1], p[2]["data"][1])

    p[0]["data"] = ("struct_declaration", result)


def p_struct_declaration_list(p):
    """
    struct_declaration_list : struct_declaration
                            | struct_declaration_list struct_declaration
    """
    p[0] = {}

    if p[1]["data"][0] == "struct_declaration":
        result = [p[1]["data"][1]]
    else:
        result = p[1]["data"][1] + [p[2]["data"][1]]

    p[0]["data"] = ("struct_declaration_list", result)


def p_class_head(p):
    """
    class_head : CLASS base_clause
               | CLASS
               | CLASS IDENTIFIER base_clause
               | CLASS IDENTIFIER
    """
    p[0] = {}

    result = {"c_name": None, "base_clause": None}
    if len(p) > 2:

        if isinstance(p[2], dict) and p[2]["data"][0] == "base_clause":
            result["base_clause"] = p[2]["data"][1]
        else:
            result["c_name"] = f"class_{p[2]}"
            if len(p) > 3:
                result["base_clause"] = p[3]["data"][1]

    p[0]["data"] = ("class_head", result)


def p_class_specifier(p):
    """
    class_specifier : class_head LEFT_CURLY_BRACKET member_list RIGHT_CURLY_BRACKET SEMICOLON
                    | class_head LEFT_CURLY_BRACKET RIGHT_CURLY_BRACKET SEMICOLON
    """
    p[0] = {}

    if p[3] == "}":
        result = cppClass(
            cppId(p[1]["data"][1]["c_name"]), None, p[1]["data"][1]["base_clause"]
        )
    else:
        result = cppClass(
            cppId(p[1]["data"][1]["c_name"]),
            p[3]["data"][1],
            p[1]["data"][1]["base_clause"],
        )

    p[0]["data"] = ("class_specifier", result)


def p_member_list(p):
    """
    member_list : member_access_list
                | access_list
                | member_list access_list
    """
    p[0] = {}

    if p[1]["data"][0] in ["member_access_list", "access_list"]:
        result = p[1]["data"][1]
    else:
        result = p[1]["data"][1] + p[2]["data"][1]

    p[0]["data"] = ("member_list", result)


def p_member_declarator(p):
    """
    member_declarator : init_declarator
    """
    p[0] = {}

    result = p[1]["data"][1]

    p[0]["data"] = ("member_declarator", result)


def p_member_declarator_list(p):
    """
    member_declarator_list : member_declarator
                           | member_declarator_list COMMA member_declarator
    """
    p[0] = {}

    if len(p) > 2:
        result = [p[1]["data"][1]] + p[3]["data"][1]
    else:
        result = [p[1]["data"][1]]

    p[0]["data"] = ("member_declarator_list", result)


def p_member_declaration(p):
    """
    member_declaration : type_specifier member_declarator_list SEMICOLON
                       | member_declarator_list SEMICOLON
                       | type_specifier SEMICOLON
                       | SEMICOLON
                       | function_definition
                       | class_specifier
    """
    p[0] = {}
    if len(p) == 2:
        if p[1] == ";":
            result = cppMemberDeclaration(None, None, None)
        elif p[1]["data"][0] == "function_definition":
            result = cppMemberDeclaration(
                p[1]["data"][1].func_type, p[1]["data"][1].func_param_list, "func"
            )
            if "code" in p[2].keys():
                p[0]["code"] = [p[1]["code"].copy()]
                p[0]["instr"] = [p[1]["instr"].copy()]
        elif p[1]["data"][0] == "class_specifier":
            result = cppMemberDeclaration(None, None, None)

    elif len(p) == 3:
        if p[1]["data"][0] == "member_declarator_list":
            result = cppMemberDeclaration(None, p[1]["data"][1], "var")
        else:
            result = cppMemberDeclaration(p[1]["data"][1], None, "var")

    else:
        result = cppMemberDeclaration(p[1]["data"][1], p[2]["data"][1], "var")

    p[0]["data"] = ("member_declaration", result)


def p_access_list(p):
    """
    access_list : access_specifier COLON member_access_list
                | access_specifier COLON
    """
    p[0] = {}

    if len(p) > 2:
        result = [p[1]["data"][1]] + p[3]["data"][1]
    else:
        result = [p[1]["data"][1]]

    p[0]["data"] = ("access_list", result)


def p_member_access_list(p):
    """
    member_access_list : member_declaration member_access_list
                       | member_declaration
    """
    p[0] = {}

    if len(p) == 3:
        result = [p[1]["data"][1]] + p[2]["data"][1]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"].copy() + p[2]["code"]
            p[0]["instr"] = p[1]["instr"].copy() + p[2]["instr"]
    else:
        result = [p[1]["data"][1]]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"].copy()
            p[0]["instr"] = p[1]["instr"].copy()

    p[0]["data"] = ("member_access_list", result)


def p_base_clause(p):
    """
    base_clause : COLON base_specifier_list
    """
    p[0] = {}

    result = p[2]["data"][1]

    p[0]["data"] = ("base_clause", result)


def p_base_specifier_list(p):
    """
    base_specifier_list : base_specifier
              | base_specifier_list COMMA base_specifier
    """
    p[0] = {}

    if p[1]["data"][0] == "base_specifier":
        result = [p[1]["data"][1]]
    else:
        result = p[1]["data"][1] + [p[3]["data"][1]]

    p[0]["data"] = ("base_specifier_list", result)


def p_base_specifier(p):
    """
    base_specifier : CLASS IDENTIFIER
                   | access_specifier CLASS IDENTIFIER
                   | IDENTIFIER
                   | access_specifier IDENTIFIER
    """
    p[0] = {}

    if p[1] == "class":
        result = cppBaseSpec(p[2].value, None)
    elif len(p) == 2:
        result = cppBaseSpec(p[1].value, None)
    elif p[1]["data"][0] == "access_specifier":
        if p[2] == "class":
            result = cppBaseSpec(p[3].value, p[1]["data"][1])
        else:
            result = cppBaseSpec(p[2].value, p[1]["data"][1])

    p[0]["data"] = ("base_specifier", result)


def p_access_specifier(p):
    """
    access_specifier : PRIVATE
                     | PUBLIC
    """
    p[0] = {}

    p[0]["data"] = ("access_specifier", p[1])


def p_abstract_declarator(p):
    """abstract_declarator : pointer
    | direct_abstract_declarator
    | pointer direct_abstract_declarator
    """
    p[0] = {}

    if len(p) == 2 and p[1]["data"][0] == "direct_abstract_declarator":
        result = p[1]["data"][1]
    elif len(p) == 3:
        result = cppPointer(
            p[2]["data"][1].dadec_name, cppType("direct_abstract_declarator")
        )
    else:
        result = cppPointer(None, None)

    p[0]["data"] = ("abstract_declarator", result)


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
    p[0] = {}

    if len(p) == 3:
        if p[1] == "[":
            result = cppDirectAbsDeclarator(None, None, None, None, None, 1)
        else:
            result = cppDirectAbsDeclarator(None, None, None, None, None, 5)

    elif len(p) == 4:
        if p[2]["data"][0] == "abstract_declarator":
            result = cppDirectAbsDeclarator(None, p[2]["data"][1], None, None, None, 0)
        elif p[2]["data"][0] == "conditional_expression":
            result = cppDirectAbsDeclarator(None, None, None, p[2]["data"][1], None, 2)
        elif p[1]["data"][0] == "direct_abstract_declarator":
            if p[2] == "[":
                result = cppDirectAbsDeclarator(
                    p[1]["data"][1], None, None, None, None, 3
                )
            else:
                result = cppDirectAbsDeclarator(
                    p[1]["data"][1], None, None, None, None, 7
                )
        elif p[2]["data"][0] == "parameter_list":
            result = cppDirectAbsDeclarator(None, None, None, None, p[2]["data"][1], 6)

    elif len(p) == 5:
        if p[3]["data"][0] == "parameter_list":
            result = cppDirectAbsDeclarator(
                p[1]["data"][1], None, None, None, p[2]["data"][1], 8
            )
        elif p[3]["data"][0] == "conditional_expression":
            result = cppDirectAbsDeclarator(
                p[1]["data"][1], None, None, p[2]["data"][1], None, 4
            )

    p[0]["data"] = ("direct_abstract_declarator", result)


def p_initializer(p):
    """
    initializer : LEFT_CURLY_BRACKET initializer_list RIGHT_CURLY_BRACKET
                | assignment_expression
    """
    p[0] = {}

    if p[1]["data"][0] == "assignment_expression":
        result = cppInitializer(p[1]["data"][1])
    else:
        result = cppInitializer(p[2]["data"][1])

    p[0]["data"] = ("initializer", result)


def p_initializer_list(p):
    """
    initializer_list : initializer_list COMMA initializer
                     | initializer
    """
    p[0] = {}

    if p[1]["data"][0] == "initializer":
        result = [p[1]["data"][1]]
    else:
        result = p[1]["data"][1] + [p[3]["data"][1]]

    p[0]["data"] = ("initializer_list", result)


def p_statement(p):
    """
    statement : compound_statement
              | expression_statement
              | selection_statement
              | iteration_statement
              | jump_statement
              | labeled_statement
    """
    p[0] = {}

    # if p[1]["data"][0] == "compound_statement":
    #     result = cppStmt("compound")
    # elif p[1]["data"][0] == "expression_statement":
    #     result = cppStmt("expr")
    # elif p[1]["data"][0] == "selection_statement":
    #     result = cppStmt("select")
    # elif p[1]["data"][0] == "iteration_statement":
    #     result = cppStmt("iterate")
    # elif p[1]["data"][0] == "jump_statement":
    #     result = cppStmt("jump")
    # elif p[1]["data"][0] == "labeled_statement":
    #     result = cppStmt("label")
    p[0]["data"] = ("statement", p[1]["data"][1])
    if "code" in p[1].keys():
        p[0]["code"] = p[1]["code"]
        p[0]["instr"] = p[1]["instr"]
        # p[0]["place"] = p[1]["place"]


def p_labeled_statement(p):
    """
    labeled_statement : IDENTIFIER COLON statement
    """
    p[0] = {}

    result = cppLabelStmt(cppId(p[1].value), p[3]["data"][1])

    p[0]["data"] = ("labeled_statement", result)


def p_compound_statement(p):
    """
    compound_statement : LEFT_CURLY_BRACKET declaration_list statement_list RIGHT_CURLY_BRACKET
                       | LEFT_CURLY_BRACKET declaration_list RIGHT_CURLY_BRACKET
                       | LEFT_CURLY_BRACKET statement_list RIGHT_CURLY_BRACKET
                       | LEFT_CURLY_BRACKET RIGHT_CURLY_BRACKET
    """
    p[0] = {}

    # symboltab.cmpd_ctr += 1
    if p[1] == "{" and p[2] == "}":
        result = cppCompoundStmt(None, None)
    elif p[2]["data"][0] == "declaration_list":
        if p[3] == "}":
            result = cppCompoundStmt(p[2]["data"][1], None)

        elif p[3]["data"][0] == "statement_list":

            result = cppCompoundStmt(p[2]["data"][1], p[3]["data"][1])
        curr_scope = symboltab.get_current_scope()
        lis_decl, instr = [], []
        for i in range(len(p[2]["data"][1])):
            if p[2]["data"][1][i] is not None:
                for j in range(len(p[2]["data"][1][i].initdecl_list)):
                    if p[2]["data"][1][i].initdecl_list[j].initializer:
                        if isinstance(
                            p[2]["data"][1][i]
                            .initdecl_list[j]
                            .initializer.init_expr.pf_expr,
                            cppConst,
                        ):
                            lis_decl.append(
                                "    "
                                + curr_scope.var_to_string_map[
                                    p[2]["data"][1][i]
                                    .initdecl_list[j]
                                    .declarator.name.name
                                ]
                                + " = "
                                + str(
                                    p[2]["data"][1][i]
                                    .initdecl_list[j]
                                    .initializer.init_expr.pf_expr.val
                                    if p[2]["data"][1][i].initdecl_list[j].initializer
                                    else "0"
                                )
                            )
                            if p[2]["data"][1][i].initdecl_list[j].initializer:
                                instr.append(
                                    [
                                        "constant_assignment",
                                        curr_scope.var_to_string_map[
                                            p[2]["data"][1][i]
                                            .initdecl_list[j]
                                            .declarator.name.name
                                        ],
                                        str(
                                            p[2]["data"][1][i]
                                            .initdecl_list[j]
                                            .initializer.init_expr.pf_expr.val
                                        ),
                                    ]
                                )
                            else:
                                instr.append(
                                    [
                                        "constant_assignment",
                                        curr_scope.var_to_string_map[
                                            p[2]["data"][1][i]
                                            .initdecl_list[j]
                                            .declarator.name.name
                                        ],
                                        "0",
                                    ]
                                )
                        else:
                            lis_decl.append(
                                "    "
                                + curr_scope.var_to_string_map[
                                    p[2]["data"][1][i]
                                    .initdecl_list[j]
                                    .declarator.name.name
                                ]
                                + " = "
                                + curr_scope.var_to_string_map[
                                    p[2]["data"][1][i]
                                    .initdecl_list[j]
                                    .initializer.init_expr.pf_expr.name
                                ]
                            )
                            instr.append(
                                [
                                    "assignment_expression",
                                    curr_scope.var_to_string_map[
                                        p[2]["data"][1][i]
                                        .initdecl_list[j]
                                        .declarator.name.name
                                    ],
                                    curr_scope.var_to_string_map[
                                        p[2]["data"][1][i]
                                        .initdecl_list[j]
                                        .initializer.init_expr.pf_expr.name
                                    ],
                                ]
                            )
                    else:
                        if (
                            p[2]["data"][1][i].initdecl_list[j].declarator.name.name
                            in curr_scope.var_to_string_map.keys()
                            and not "_"
                            in p[2]["data"][1][i]
                            .initdecl_list[j]
                            .declarator.name._type.typename
                        ):
                            lis_decl.append(
                                "    "
                                + curr_scope.var_to_string_map[
                                    p[2]["data"][1][i]
                                    .initdecl_list[j]
                                    .declarator.name.name
                                ]
                                + " = "
                                + "0"
                            )
                            instr.append(
                                [
                                    "constant_assignment",
                                    curr_scope.var_to_string_map[
                                        p[2]["data"][1][i]
                                        .initdecl_list[j]
                                        .declarator.name.name
                                    ],
                                    "0",
                                ]
                            )

        p[0]["code"] = lis_decl
        p[0]["instr"] = instr
        if p[3] != "}" and "code" in p[3].keys():
            p[0]["code"] = p[0]["code"] + p[3]["code"]
            p[0]["instr"] = p[0]["instr"] + p[3]["instr"]
    elif p[2]["data"][0] == "statement_list":
        if "code" in p[2].keys():
            p[0]["code"] = p[2]["code"]
            p[0]["instr"] = p[2]["instr"]
        result = cppCompoundStmt(None, p[2]["data"][1])

    # symboltab.remove_scope_from_stack()
    p[0]["data"] = ("compound_statement", result)


def p_declaration_list(p):
    """
    declaration_list : declaration_list declaration
                     | declaration
    """
    p[0] = {}

    if p[1]["data"][0] == "declaration_list":
        result = p[1]["data"][1] + [p[2]["data"][1]]
        if "code" in p[1].keys() and "code" in p[2].keys():
            p[0]["code"] = p[1]["code"] + p[2]["code"]
            p[0]["instr"] = p[1]["instr"] + p[2]["instr"]

    else:

        result = [p[1]["data"][1]]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"]
            p[0]["instr"] = p[1]["instr"]

    p[0]["data"] = ("declaration_list", result)


def p_statement_list(p):
    """
    statement_list : statement
                   | statement_list statement
    """
    p[0] = {}

    if p[1]["data"][0] == "statement_list":
        result = p[1]["data"][1] + [p[2]["data"][1]]
        if "code" in p[1].keys() and "code" in p[2].keys():
            p[0]["code"] = p[1]["code"] + p[2]["code"]
            p[0]["instr"] = p[1]["instr"] + p[2]["instr"]
        if "place" in p[2].keys():
            p[0]["place"] = p[2]["place"]
    else:
        result = [p[1]["data"][1]]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"]
            p[0]["instr"] = p[1]["instr"]
        if "place" in p[1].keys():
            p[0]["place"] = p[1]["place"]

    p[0]["data"] = ("statement_list", result)


def p_expression_statement(p):
    """
    expression_statement : expression SEMICOLON
                         | SEMICOLON
    """
    p[0] = {}
    if "place" in p[1].keys():
        p[0]["place"] = p[1]["place"]
    if "code" in p[1].keys():
        p[0]["code"] = p[1]["code"].copy()
        p[0]["instr"] = p[1]["instr"].copy()

    if p[1] != ";":
        p[0]["data"] = ("expression_statement", p[1]["data"][1])
    else:
        p[0]["data"] = ("expression_statement", None)


def p_selection_statement(p):
    """
    selection_statement : IF LEFT_PARENTHESIS expression RIGHT_PARENTHESIS statement %prec IF
                        | IF LEFT_PARENTHESIS expression RIGHT_PARENTHESIS statement ELSE statement
                        | ASSERT LEFT_PARENTHESIS expression RIGHT_PARENTHESIS SEMICOLON
    """
    p[0] = {}

    if len(p) == 6 and p[1] != "assert":
        result = cppSelectStmt(p[3]["data"][1], p[5]["data"][1], None)
        p[0]["after"] = symboltab.add_temp_var()
        p[0]["code"] = (
            p[3]["code"]
            + ["    ifz " + p[3]["place"] + " goto->" + p[0]["after"]]
            + p[5]["code"]
            + [p[0]["after"] + " : "]
        )

        p[0]["instr"] = (
            p[3]["instr"]
            + [["ifz", p[3]["place"], p[0]["after"]]]
            + p[5]["instr"]
            + [["Label", p[0]["after"]]]
        )

    # Assert Statement
    elif p[1] == "assert":
        result = cppSelectStmt(p[3]["data"][1], None, None)
        p[0]["after"] = symboltab.add_temp_var()
        p[0]["instr"] = (
            p[3]["instr"]
            + [["!", p[3]["place"]]]
            + [["ifz", p[3]["place"], p[0]["after"]]]
            + [["exit", str(driver.lexer.lineno)]]
            + [["Label", p[0]["after"]]]
        )
        p[0]["code"] = (
            p[3]["code"]
            + ["    not " + p[3]["place"]]
            + ["    ifz " + p[3]["place"] + " goto->" + p[0]["after"]]
            + ["    exit"]
            + [p[0]["after"] + " : "]
        )

    else:
        result = cppSelectStmt(p[3]["data"][1], p[5]["data"][1], p[7]["data"][1])
        p[0]["before"] = symboltab.add_temp_var()
        p[0]["else"] = symboltab.add_temp_var()
        p[0]["after"] = symboltab.add_temp_var()
        string = (
            ["    ifz " + p[3]["place"] + " goto->" + p[0]["else"]]
            + p[5]["code"]
            + ["goto->" + p[0]["after"]]
        )
        instr = (
            [["ifz", p[3]["place"], p[0]["else"]]]
            + p[5]["instr"]
            + [["ifgoto", p[0]["after"]]]
        )
        p[0]["code"] = (
            p[3]["code"]
            + [p[0]["before"] + " : "]
            + string
            + [p[0]["else"] + " : "]
            + p[7]["code"]
            + [p[0]["after"] + " : "]
        )
        p[0]["instr"] = (
            p[3]["instr"]
            + [["Label", p[0]["before"]]]
            + instr
            + [["Label", p[0]["else"]]]
            + p[7]["instr"]
            + [["Label", p[0]["after"]]]
        )
    p[0]["data"] = ("selection_statement", result)


def p_iteration_statement(p):
    """
    iteration_statement : WHILE LEFT_PARENTHESIS expression RIGHT_PARENTHESIS compound_statement
                        | FOR LEFT_PARENTHESIS expression_statement expression_statement expression RIGHT_PARENTHESIS compound_statement
                        | FOR LEFT_PARENTHESIS type_specifier expression_statement expression_statement expression RIGHT_PARENTHESIS compound_statement
                        | FOR LEFT_PARENTHESIS expression_statement expression_statement RIGHT_PARENTHESIS compound_statement
                        | FOR LEFT_PARENTHESIS type_specifier expression_statement expression_statement RIGHT_PARENTHESIS compound_statement
    """
    p[0] = {}

    result = None

    if p[1] == "while":
        result = cppIterateStmt("while", None, p[3]["data"][1], None, p[5]["data"][1])
        p[0]["begin"] = symboltab.add_temp_var("int")
        p[0]["continue"] = symboltab.add_temp_var("int")
        p[0]["after"] = symboltab.add_temp_var("int")
        string = (
            p[3]["code"]
            + ["    " + "ifz " + p[3]["place"] + " goto->" + p[0]["after"]]
            + p[5]["code"]
            + ["goto->" + p[0]["begin"]]
        )

        instr = (
            p[3]["instr"]
            + [["ifz", p[3]["place"], p[0]["after"]]]
            + p[5]["instr"]
            + [["ifgoto", p[0]["begin"]]]
        )
        string = [
            "    goto->" + p[0]["after"] if i == "    break" else i for i in string
        ]
        string = [
            "    goto->" + p[0]["begin"] if i == "    continue" else i for i in string
        ]
        instr1 = []
        for i in instr:
            if i[0] == "break":
                instr1.append(["ifgoto", p[0]["after"]])
            elif i[0] == "continue":
                instr1.append(["ifgoto", p[0]["begin"]])
            else:
                instr1.append(i)
        p[0]["code"] = [
            p[0]["begin"] + " : "
        ] + string  # + ["ifz " + p[5]["place"] + " goto->" + p[0]["after"]]
        # p[0]["code"] = p[0]["code"] + [p[0]["continue"] + " : "] + string + ["ifz " + p[5]["place"] + " goto->" + p[0]["after"]]
        p[0]["code"] = p[0]["code"] + [p[0]["after"] + " : "]
        p[0]["instr"] = [["Label", p[0]["begin"]]] + instr1 + [["Label", p[0]["after"]]]
    elif p[1] == "for":
        if p[3]["data"][0] == "expression_statement":
            if p[5] == ")":

                result = cppIterateStmt(
                    "for", p[3]["data"][1], p[4]["data"][1], None, p[6]["data"][1]
                )
            else:
                p[0]["begin"] = symboltab.add_temp_var("int")
                p[0]["after"] = symboltab.add_temp_var("int")
                string = (
                    p[4]["code"]
                    + ["    " + "ifz " + p[4]["place"] + " goto->" + p[0]["after"]]
                    + p[7]["code"]
                    + p[5]["code"]
                    + ["goto->" + p[0]["begin"]]
                )

                instr = (
                    p[4]["instr"]
                    + [["ifz", p[4]["place"], p[0]["after"]]]
                    + p[7]["instr"]
                    + p[5]["instr"]
                    + [["ifgoto", p[0]["begin"]]]
                )

                string = [
                    "    goto->" + p[0]["after"] if i == "    break" else i
                    for i in string
                ]
                string = [
                    "    goto->" + p[0]["begin"] if i == "    continue" else i
                    for i in string
                ]
                instr1 = []
                for i in instr:
                    if i[0] == "break":
                        instr1.append(["ifgoto", p[0]["after"]])
                    elif i[0] == "continue":
                        instr1.append(["ifgoto", p[0]["begin"]])
                    else:
                        instr1.append(i)

                p[0]["code"] = (
                    p[3]["code"] + [p[0]["begin"] + " : "] + string
                )  # + ["ifz " + p[5]["place"] + " goto->" + p[0]["after"]]
                # p[0]["code"] = p[0]["code"] + [p[0]["continue"] + " : "] + string + ["ifz " + p[5]["place"] + " goto->" + p[0]["after"]]
                p[0]["code"] = p[0]["code"] + [p[0]["after"] + " : "]
                p[0]["instr"] = (
                    p[3]["instr"]
                    + [["Label", p[0]["begin"]]]
                    + instr1
                    + [["Label", p[0]["after"]]]
                )
                result = cppIterateStmt(
                    "for",
                    p[3]["data"][1],
                    p[4]["data"][1],
                    p[5]["data"][1],
                    p[7]["data"][1],
                )
        else:

            if p[6] == ")":
                result = cppIterateStmt(
                    "for_init",
                    (p[3]["data"][1], p[4]["data"][1]),
                    p[5]["data"][1],
                    None,
                    p[7]["data"][1],
                )
            else:
                p[0]["begin"] = symboltab.add_temp_var("int")
                p[0]["after"] = symboltab.add_temp_var("int")
                string = (
                    p[5]["code"]
                    + ["    " + "ifz " + p[5]["place"] + " goto->" + p[0]["after"]]
                    + p[8]["code"]
                    + p[6]["code"]
                    + ["goto->" + p[0]["begin"]]
                )
                instr = (
                    p[5]["instr"]
                    + [["ifz", p[5]["place"], p[0]["after"]]]
                    + p[8]["instr"]
                    + p[6]["instr"]
                    + [["ifgoto", p[0]["begin"]]]
                )

                string = [
                    "    goto->" + p[0]["after"] if i == "    break" else i
                    for i in string
                ]
                string = [
                    "    goto->" + p[0]["begin"] if i == "    continue" else i
                    for i in string
                ]
                instr1 = []
                for i in instr:
                    if i[0] == "break":
                        instr1.append(["ifgoto", p[0]["after"]])
                    elif i[0] == "continue":
                        instr1.append(["ifgoto", p[0]["begin"]])
                    else:
                        instr1.append(i)

                p[0]["code"] = (
                    p[4]["code"] + [p[0]["begin"] + " : "] + string
                )  # + ["ifz " + p[5]["place"] + " goto->" + p[0]["after"]]
                # p[0]["code"] = p[0]["code"] + [p[0]["continue"] + " : "] + string + ["ifz " + p[5]["place"] + " goto->" + p[0]["after"]]
                p[0]["code"] = p[0]["code"] + [p[0]["after"] + " : "]
                p[0]["instr"] = (
                    p[4]["instr"]
                    + [["Label", p[0]["begin"]]]
                    + instr1
                    + [["Label", p[0]["after"]]]
                )
                result = cppIterateStmt(
                    "for_init",
                    (p[3]["data"][1], p[4]["data"][1]),
                    p[5]["data"][1],
                    p[6]["data"][1],
                    p[8]["data"][1],
                )

    p[0]["data"] = ("iteration_statement", result)


def p_jump_statement(p):
    """
    jump_statement : GOTO IDENTIFIER SEMICOLON
                   | BREAK SEMICOLON
                   | CONTINUE SEMICOLON
                   | RETURN SEMICOLON
                   | RETURN expression SEMICOLON
    """
    p[0] = {}

    result = cppJumpStmt("return", None)
    if p[1] == "goto":
        result = cppJumpStmt("goto", cppId(p[2].value))
        p[0]["code"] = ["goto->" + p[2]["place"]]
        p[0]["instr"] = [["ifgoto", p[2]["place"]]]
    elif p[1] == "break":
        result = cppJumpStmt("break", None)
        p[0]["code"] = ["    break"]
        p[0]["instr"] = [["break"]]
    elif p[1] == "continue":
        result = cppJumpStmt("continue", None)
        p[0]["code"] = ["    continue"]
        p[0]["instr"] = [["continue"]]
    elif p[1] == "return":
        if len(p) == 3:
            result = cppJumpStmt("return", None)
            # if "code" in p[2].keys():
            p[0]["code"] = ["    return"]
            p[0]["instr"] = [["return_nothing"]]
        else:
            result = cppJumpStmt("return", p[2]["data"][1][0])
            if "code" in p[2].keys():
                p[0]["code"] = p[2]["code"] + ["    return " + p[2]["place"]]
                p[0]["instr"] = p[2]["instr"] + [["return", p[2]["place"]]]

    p[0]["data"] = ("jump_statement", result)


def p_translation_unit(p):
    """
    translation_unit : translation_unit external_declaration
                     | external_declaration
    """
    p[0] = {}

    if len(p) == 2:

        result = [p[1]["data"][1]]
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"].copy()
            p[0]["instr"] = p[1]["instr"].copy()
    else:

        result = p[1]["data"][1] + [p[2]["data"][1]]
        p[0]["code"] = []
        p[0]["instr"] = []
        if "code" in p[1].keys():
            p[0]["code"] = p[1]["code"].copy()
            p[0]["instr"] = p[1]["instr"].copy()
        if "code" in p[2].keys():
            p[0]["code"] = p[0]["code"] + p[2]["code"].copy()
            p[0]["instr"] = p[0]["instr"] + p[2]["instr"].copy()
    p[0]["data"] = ("translation_unit", result)


def p_external_declaration(p):
    """
    external_declaration : function_definition
                         | declaration
    """
    p[0] = {}
    if "code" in p[1].keys():
        p[0]["code"] = p[1]["code"].copy()
        p[0]["instr"] = p[1]["instr"].copy()

    p[0]["data"] = ("external_declaration", p[1]["data"][1])


def p_function_definition(p):
    """
    function_definition : type_specifier declarator declaration_list compound_statement
                        | type_specifier declarator compound_statement
                        | declarator declaration_list compound_statement
                        | declarator compound_statement
    """
    global tmp_func, curr_param
    global errors_found
    p[0] = {}
    curr_scope = symboltab.get_current_scope()

    if p[1]["data"][0] == "type_specifier":
        ###recursion case and undefined function checking###
        for func in tmp_func:
            if p[2]["data"][1].name.name not in func[0]:
                print(
                    f"Undeclared function with name {func[0]} used inside {p[2]['data'][1].name.name} at line {driver.lexer.lineno}"
                )
                errors_found += 1
            else:
                ###recursion case###
                register_type[func[1]] = ("reg", p[1]["data"][1].typename)
                if (
                    p[3]["data"][0] == "compound_statement"
                    and len(p[2]["data"][1].ddecl.param_list) != func[2]
                ):
                    len_params = len(p[2]["data"][1].ddecl.param_list)
                    print(
                        f"Function {p[2]['data'][1].name.name} expects {len_params} args, but {func[2]} were given at line {func[3]} at {driver.lexer.lineno}"
                    )
                    errors_found += 1
                elif p[3]["data"][0] == "declaration_list" and func[2] > 0:
                    print(
                        f"Function {p[2]['data'][1].name.name} expects 0 args, but {func[2]} were given at line {func[3]} at {driver.lexer.lineno}"
                    )
                    errors_found += 1

        if p[3]["data"][0] == "declaration_list":
            result = cppFuncDef(
                p[1]["data"][1], p[2]["data"][1].name, p[3]["data"][1], p[4]["data"][1]
            )
        elif p[3]["data"][0] == "compound_statement":
            code = []
            if p[2]["data"][1].ddecl.param_list is not None:
                for i in p[2]["data"][1].ddecl.param_list:
                    code.append(curr_scope.var_to_string_map[i.pdec_param.name.name])
            result = cppFuncDef(p[1]["data"][1], p[2]["data"][1], p[3]["data"][1])
            if "code" in p[3].keys():
                stack = str(get_stack_size(p[2]["data"][1].name.name))
                p[0]["code"] = (
                    [p[2]["data"][1].name.name + " | " + " , ".join(code)]
                    + ["    Func_Start : Stack_space " + stack]
                    + p[3]["code"]
                    + ["    Func_End"]
                )
                if p[2]["data"][1].name.name == "main":
                    p[0]["instr"] = (
                        [
                            [
                                "Function_Label:",
                                p[2]["data"][1].name.name,
                                p[1]["data"][1].typename,
                            ]
                        ]
                        + [["Function_related"]]
                        + p[3]["instr"]
                        + [["main_end"]]
                    )
                else:
                    p[0]["instr"] = (
                        [
                            [
                                "Function_Label:",
                                p[2]["data"][1].name.name,
                                p[1]["data"][1].typename,
                            ]
                        ]
                        + [["Function_related"]]
                        + p[3]["instr"]
                        + [["Function_End"]]
                    )
    elif p[1]["data"][0] == "declarator":
        if p[2]["data"][0] == "declaration_list":
            result = cppFuncDef(
                None, p[1]["data"][1].name, p[2]["data"][1], p[3]["data"][1]
            )
        elif p[2]["data"][0] == "compound_statement":
            result = cppFuncDef(None, p[1]["data"][1].name, None, p[2]["data"][1])
    symboltab.cmpd_ctr += 1
    symboltab.remove_scope_from_stack()
    tmp_func, curr_param = (
        [],
        [],
    )  ### temp func empty to check recursion for next function
    p[0]["data"] = ("function_definition", result)


class scopeInitialiser:
    def __init__(
        self,
        scope_id=0,
        scope_name="Global",
        parent_scope=None,
        current_scope_depth=0,
    ) -> None:
        self.scope_id = scope_id
        self.parent = parent_scope
        self.scope_depth = current_scope_depth
        self.scope_name = scope_name
        self.variables = {}
        self.constants = {}
        self.pointers = {}
        self.structs = {}
        self.classes = {}
        self.temp_variables = {}
        self.var_to_string_map = parent_scope.var_to_string_map if parent_scope else {}
        self.string_to_var_map = parent_scope.string_to_var_map if parent_scope else {}

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
            len(self.scope_list), scope_name, curr_scope, curr_depth
        )
        self.scope_list.append(newscope)
        self.scope_stack.append(newscope)

    def check_and_add_variable(self, variable, varType):
        global var_index
        global errors_found
        curr_scope = self.get_current_scope()

        if curr_scope.find_variable(variable.name):
            print(
                f"Variable re-declared with name {variable.name} at line {driver.lexer.lineno}"
            )
            errors_found += 1
        else:
            curr_scope.variables[variable.name] = varType
            x = "reg" + str(var_index)  # + "@" + str(curr_scope.scope_id)

            curr_scope.var_to_string_map.update({variable.name: x})
            curr_scope.string_to_var_map.update(
                {x: (variable, curr_scope if curr_scope else "Global")}
            )
            var_index += 1

    def add_temp_var(self, typename="int"):

        global tmp_var_index
        global tmep_var_to_string_map, string_to_temp_var_map
        curr_scope = self.get_current_scope()

        x = "t_reg" + str(tmp_var_index)  # + "@" + str(curr_scope.scope_id)
        curr_scope.temp_variables[x] = cppType(typename)

        string_to_temp_var_map[x] = curr_scope if curr_scope else "Global"
        tmp_var_index += 1

        return x

    def find_type(self, str1, str2):
        if str1 in register_type.keys() and str2 in register_type.keys():
            if register_type[str1][1] == "float" or register_type[str2][1] == "float":
                return ("temp_reg", "float")
            elif register_type[str1][1] == "int" or register_type[str2][1] == "int":
                return ("temp_reg", "int")
            else:
                return ("temp_reg", "char")
        elif str1 in register_type.keys():
            return register_type[str1]
        elif str2 in register_type.keys():
            return register_type[str2]
        else:
            return ("temp_reg", "int")

    def check_undeclared_variable(self, variable):
        curr_scope = self.get_current_scope()
        found = False
        global errors_found
        while curr_scope:
            found = curr_scope.find_variable(variable.name)
            if found:
                break
            curr_scope = curr_scope.parent

        if not found:
            print(
                f"Undeclared variable used with name {variable.name} at line {driver.lexer.lineno}"
            )
            errors_found += 1

    def check_and_add_const(self, const, constType, constVal):
        curr_scope = self.get_current_scope()
        global errors_found
        if curr_scope.find_variable(const):
            print(
                f"Constant re-declared with name {const.name} at line {driver.lexer.lineno}"
            )
            errors_found += 1

        else:
            curr_scope.constants[const] = (constType, constVal)

    def check_and_add_struct(self, structTag: "cppId", structId: "cppId" = None):
        curr_scope = self.get_current_scope()
        global errors_found
        if curr_scope.find_struct(structId.name):
            print(
                f"Struct re-declared with same name {structId.name} at line {driver.lexer.lineno}"
            )
            errors_found += 1
        else:
            # self.add_scope_to_stack(str(structTag.name) + "_struct")
            curr_scope.structs[structId.name] = structTag

    def check_and_add_function(
        self, function_id, function_type, function_nparams, func_param_list, scope_id
    ):
        global errors_found
        if function_id.name in self.functions.keys():
            print(
                f"Function re-declared with name {function_id.name} at line no {driver.lexer.lineno}"
            )
            errors_found += 1
        else:
            # self.add_scope_to_stack(str(function_id.name) + "_function")

            self.functions[function_id.name] = (
                function_type.typename,
                function_nparams,
                func_param_list,
            )

    def check_and_add_class(self, className: "cppId"):
        curr_scope = self.get_current_scope()
        global errors_found
        if curr_scope.find_class(className):
            print(
                f"Class re-declared with same name {className} at line no {driver.lexer.lineno}"
            )
            errors_found += 1
        else:
            self.add_scope_to_stack(str(className.name))
            curr_scope.classes[className.name] = className

    def remove_scope_from_stack(self):
        if len(self.scope_stack) > 1:
            self.scope_stack = self.scope_stack[:-1]

    def savecsv(self):
        f = open("src/symboltable.csv", "w")
        writer = csv.writer(f)
        writer.writerow(
            [
                "entity_name",
                "entity_type",
                "entity_size",
                "scope_name",
                "parent_scope_name",
                "variable_alias",
            ]
        )

        for func in self.functions.keys():
            writer.writerow([func, "Function", self.functions[func], "Global", None])

        for scope in self.scope_list:
            if scope.scope_name == "Global":
                continue
            for var in scope.variables.keys():
                temp = scope.var_to_string_map[var]
                if isinstance(scope.variables[var], list):
                    scope.variables[var] = scope.variables[var][0]
                writer.writerow(
                    [
                        var,
                        scope.variables[var].typename,
                        dtype_size[scope.variables[var].typename]
                        * max(1, scope.string_to_var_map[temp][0].array_size),
                        "Variable",
                        scope.scope_name,
                        scope.parent.scope_name if scope.parent else None,
                        temp,
                    ]
                )

            # for var in scope.temp_variables.keys():
            #     writer.writerow(
            #         [
            #             var,
            #             scope.temp_variables[var].typename,
            #             4,
            #             "Temp_Variable",
            #             scope.scope_name,
            #             scope.parent.scope_name if scope.parent else None,
            #             var,
            #         ]
            #     )
            for struct in scope.structs.keys():
                writer.writerow(
                    [
                        struct,
                        None,
                        "Structure",
                        scope.scope_name,
                        scope.parent.scope_name if scope.parent else None,
                    ]
                )
            for cl in scope.classes.keys():
                writer.writerow(
                    [
                        cl,
                        None,
                        "Class",
                        scope.scope_name,
                        scope.parent.scope_name if scope.parent else None,
                    ]
                )
        f.close()


# ------------------------ ------------------------
# ------------------------ ------------------------
# PARSER
# ------------------------ ------------------------
# ------------------------ ------------------------


global_scope = scopeInitialiser()
symboltab = symbolTable(global_scope)

allowed_native_types = [
    "char",
    "float",
    "int",
    "pointer",
    "string",
    "struct",
    "void",
    "class",
]

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
    "bitwise_op": ["^", "&", "|", "~", ">>", "<<"],
    "boolean_op": ["&&", "||", "!"],
    "comparison_op": [">", "<", "==", ">=", "<=", "!="],
    "unary_op": ["++", "--", "sizeof", "~", "!", "&", "*", "+", "-"],
    "postfix_op": ["++", "--", ".", "->"],
}

operator_compat = {
    "+": ["int", "char", "float", "pointer_int", "pointer_float", "pointer_char"],
    "-": ["int", "char", "float", "pointer_int", "pointer_float", "pointer_char"],
    "*": ["int", "char", "float", "pointer_int", "pointer_char", "pointer_float"],
    "/": ["int", "char", "float"],
    "%": ["int"],
    "<<": ["int"],
    ">>": ["int"],
    "|": ["int"],
    "&": ["int", "float", "char"],
    "~": ["int"],
    "^": ["int"],
    "||": ["int", "char", "float"],
    "&&": ["int", "char", "float"],
    "!": ["int", "char", "float"],
    ">": ["int", "char", "float"],
    ">=": ["int", "char", "float"],
    "!=": ["int", "char", "float"],
    "<": ["int", "char", "float"],
    "<=": ["int", "char", "float"],
    "=": ["int", "char", "float", "pointer_int", "pointer_char", "pointer_float"],
    "++": ["int", "char", "float"],
    "--": ["int", "char", "float"],
    "+=": ["int", "char", "float"],
    "-=": ["int", "char", "float"],
    "*=": ["int", "char", "float"],
    "/=": ["int", "char", "float"],
    "func_call": ["int", "char", "float"],
    ".": ["int", "float", "char"],
    "==": ["int", "float", "char"],
    "arr_index": ["int"],
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
        global errors_found
        if len(self.typename.split("_")) > 1:
            if self.typename.split("_")[1] not in allowed_native_types:
                errors_found += 1
                print("Invalid type")
        else:
            if self.typename not in allowed_native_types:
                errors_found += 1
                print(f"Invalid type {self.typename} at {driver.lexer.lineno}")

    def add_class_type(self, class_name: str):
        if class_name not in allowed_native_types:
            allowed_native_types.append(str(class_name))
            return True

        return False

    @staticmethod
    def traverse(object):
        return [object.typename]


class cppNode:
    def __init__(self, node_type: cppType = None, node_name: "cppId" = None):
        self.node_type = node_type
        self.base_type = None
        self.node_name = node_name
        # self.check()

    def check(self):
        global errors_found
        if self.node_type.split("_")[
            1
        ] not in allowed_native_types or self.base_type not in allowed_native_types + [
            "struct",
            None,
        ]:
            errors_found += 1
            print(
                f"Incorrect type {self.node_type} / {self.base_type} at {driver.lexer.lineno}"
            )
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

        else:
            print(f"{type(object)} type not valid")

        return graph_list


class cppConst(cppNode):
    def __init__(
        self,
        val,
        _type: cppType,
    ):
        self.val = val
        self._type = _type

        super().__init__("constant_" + str(self._type.typename))

    @staticmethod
    def traverse(object):
        return ["Constant", object._type.traverse(object._type), object.val]


class cppId(cppNode):
    def __init__(self, name: str, _type: cppType = cppType("int"), array_size: int = 0):
        super().__init__("identifier_" + str(_type.typename if _type else "None"), name)
        self.array_size = array_size
        self.name = name
        self._type = _type
        global errors_found
        if not (self.name[0]).isalpha():
            errors_found += 1
            print(
                "Invalid identifier name, should start with alphabets at line {}".format(
                    driver.lexer.lineno
                ),
                end="",
            )
            return None

    @staticmethod
    def traverse(object):
        return ["Variable", object._type.traverse(object._type), object.name]


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
            lis = obj.elements[1]
            for x in lis:
                if x != [] and x != "" and x != None:
                    graph_list.append(x.traverse(x))

        return graph_list

    @staticmethod
    def gen_graph(object, graph):
        def generate_graph(graph, ast, node_index):

            if isinstance(ast, tuple):
                ast = [ast]

            if isinstance(ast, list):
                current_index = node_index
                graph.add_node(pydot.Node(node_index, label=str(ast[0]), shape="egg"))
                for x in ast[1:]:
                    if x != []:
                        if current_index == None:
                            continue
                        nd = pydot.Edge(node_index, current_index + 1)
                        graph.add_edge(nd)
                        current_index = generate_graph(graph, x, current_index + 1)
                return current_index

            elif isinstance(
                ast,
                (str, int, float, dict),
            ):
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
        generate_graph(graph, ast, 0)
        graph.get_node("0")[0].set_color("teal")
        return ast, graph


# ------------------------ ------------------------
# EXPRESSIONS
# ------------------------ ------------------------


class cppExpr(cppNode):
    def __init__(self, lhs: cppNode, op: cppOp, rhs: Union[cppNode, None]):

        # super().__init__("expression")
        self.lhs = lhs
        self.rhs = rhs

        self.op = op
        # self.op_compat_types = None

        # TODO: fix dict issues

        self.op_compat_types = (
            operator_compat[self.op.op] if self.op is not None else allowed_native_types
        )
        self.expr_type = None
        if lhs and lhs.node_type:
            if len(lhs.node_type.split("_")) > 1:
                self.expr_type = lhs.node_type.split("_")[-1]
            else:
                self.expr_type = lhs.node_type

        self.node_type = self.expr_type
        self.check()

    def check(self):
        global errors_found
        # Check lhs and rhs type compatible (binary exprs only)
        if not isinstance(self.rhs, list):
            if self.rhs is not None and self.lhs.expr_type != self.rhs.expr_type:
                pass
                # print("1766 ",self.rhs.pf_expr._type.typename,self.lhs.un_expr.pf_expr._type.typen)
                # # Typecasting; If not possible return False
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
                #         f"Types {self.lhs.expr_type} and {self.rhs.expr_type} incompatible, cannot typecast at {driver.lexer.lineno}"
                #     )
                #     return False
            #####NEED TO DISCUSS # print(f"Type mismatch on lhs and rhs at line {driver.lexer.lineno}")
        else:
            for s in self.rhs:
                if s is not None and self.lhs.expr_type != s.expr_type:

                    # Typecasting; If not possible return False
                    # TODO: int-float typecasting priority
                    if (
                        self.op.op != "cast"
                        and self.lhs.expr_type
                        and s.expr_type in typecast_compat[self.lhs.expr_type]
                    ):
                        s = cppCastExpr(s, self.lhs.expr_type)
                        self.expr_type = self.lhs.expr_type

                    # elif self.lhs.expr_type in typecast_compat[self.rhs.expr_type]:
                    #     self.lhs = cppCastExpr(self.lhs, self.rhs.expr_type)
                    #     self.expr_type = self.rhs.expr_type
                    ######NEED TO CHECK##########
                    # else:
                    #     # print(self.lhs.un_expr.name, "   ", s.un_expr)
                    #     print(
                    #         f"Types {self.lhs.expr_type} and {s.expr_type} incompatible, cannot typecast at {driver.lexer.lineno}"
                    #     )
                    #     return False

        if (
            self.op
            and self.op.op != "cast"
            and self.lhs
            and isinstance(self.lhs, cppId)
            and self.lhs.node_type.split("_")[1] not in self.op_compat_types
        ):
            print(
                f"Operator {self.op.op} not compatible with type {self.lhs.node_type.split('_')[1]} at {driver.lexer.lineno}"
            )
            errors_found += 1
            return False

        if (
            self.op
            and self.op.op != "cast"
            and self.lhs
            and isinstance(self.lhs, cppConst)
            and self.lhs.node_type.split("_")[1] not in self.op_compat_types
        ):
            print(
                f"Operator {self.op.op} not compatible with type {self.lhs.node_type.split('_')[1]} at {driver.lexer.lineno}"
            )
            errors_found += 1
            return False

        # Check op compatible with expr types (after typecasting success)
        elif (
            self.op
            and self.op.op != "cast"
            and self.lhs
            and not isinstance(self.lhs, cppId)
            and not isinstance(self.lhs, cppConst)
            and self.lhs.expr_type is not None
            and not isinstance(self.lhs.expr_type, str)
            and self.lhs.expr_type.typename not in self.op_compat_types
            and self.lhs.expr_type != ""
        ):
            print(
                f"Operator {self.op.op} not compatible with type {self.lhs.expr_type.typename} at {driver.lexer.lineno}"
            )

            errors_found += 1
            return False

        return True

    @staticmethod
    def traverse(object):
        return [
            object.lhs.traverse(object.lhs),
            object.op.traverse(object.op),
            object.rhs.traverse(object.rhs),
        ]


class cppPostfixExpr(cppExpr):
    def __init__(
        self,
        pf_expr: cppExpr,
        pf_op: cppOp,
        pf_offset: Union[cppId, cppConst] = None,
        pf_id: cppExpr = None,
    ):
        super().__init__(pf_expr, None, None)
        global global_structs
        global errors_found

        self.pf_expr = pf_expr
        self.pf_op = pf_op
        self.pf_id = pf_id
        self.pf_offset = pf_offset
        # if isinstance(self.pf_offset, cppArithExpr):
        #     pass
        # if isinstance(pf_offset, cppId):
        #     self.pf_offset = pf_offset.name
        # elif isinstance(pf_offset, cppConst):
        #     self.pf_offset = pf_offset.val
        self.expr_type = None
        if isinstance(self.pf_expr, cppConst):
            self.expr_type = self.pf_expr._type
        elif isinstance(self.pf_expr, cppId):
            if self.pf_expr.name in symboltab.get_current_scope().variables.keys():
                self.expr_type = cppType("int")
                self.expr_type.typename = (
                    symboltab.get_current_scope().variables[self.pf_expr.name].typename
                )
                self.pf_expr._type.typename = self.expr_type.typename

        elif isinstance(self.pf_expr, cppPostfixExpr):
            if self.pf_op and self.pf_op.op == ".":
                # struct_scope = None
                # for scope in symboltab.scope_list:
                #     print(scope.scope_name)
                #     if scope.scope_name == self.pf_expr.pf_expr.name + "_struct":
                #         struct_scope = scope
                #         break
                # if self
                struct_type = (
                    symboltab.get_current_scope()
                    .variables[self.pf_expr.pf_expr.name]
                    .typename.split("_")[0]
                )

                if struct_type in global_structs.keys():

                    if self.pf_id.name in global_structs[struct_type].keys():
                        self.expr_type = global_structs[struct_type][self.pf_id.name][0]
                    else:
                        print(
                            f"Invalid field {self.pf_id.name} for struct {self.pf_expr.pf_expr.name} at line {driver.lexer.lineno}"
                        )
                        errors_found += 1
                else:
                    print(
                        f"Struct {self.pf_expr.pf_expr.name} used without initialization at line {driver.lexer.lineno}"
                    )
                    errors_found += 1

        elif isinstance(self.pf_expr, cppExpr):
            self.expr_type = self.pf_expr.expr_type

        self.check_pf()

    def check_pf(self):
        global errors_found
        # Only int / float can have ++, --
        if (
            self.pf_op
            and self.pf_op.op in ["++", "--"]
            and self.pf_expr.expr_type.typename
            not in [
                "int",
                "float",
                "char",
            ]
            and self.pf_expr.expr_type != ""
        ):
            print(
                f"Invalid operator {self.pf_op.op} for type {self.pf_expr.expr_type.typename} at line {driver.lexer.lineno}"
            )
            errors_found += 1

        # Only pointer to struct can have -> op
        if (
            self.pf_op == "->"
            and self.pf_expr.expr_type == "pointer"
            and self.pf_expr.base_type != "struct"
        ):
            print(
                f"Invalid operator {self.pf_op.op} for pointer to type {self.pf_expr.expr_type.typename} at line {driver.lexer.lineno}"
            )
            errors_found += 1
            return False

        # invalid field name for struct
        if self.pf_op == "->" and self.pf_id is None:
            print(
                f"Invalid field {self.pf_id} to struct pointer {self.pf_expr} for '->' operator at line {driver.lexer.lineno}"
            )
            errors_found += 1
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
        #         f"Invalid field name {self.pf_id} to struct pointer {self.pf_expr} at line {driver.lexer.lineno}"
        #     )
        #     return False

        # Only struct can have . op

        if (
            self.pf_op
            and self.pf_op.op == "."
            and self.pf_expr.expr_type
            and self.pf_expr.expr_type.typename.split("_")[1] != "struct"
        ):
            print(
                f"Invalid type {self.pf_expr.expr_type.typename} for '.'operator at line {driver.lexer.lineno}"
            )
            errors_found += 1
            return False

        return True

    @staticmethod
    def traverse(object):
        graph_list = []
        # if isinstance(object.pf_expr, cppPostfixExpr):
        if object.pf_expr is not None:
            graph_list.append(object.pf_expr.traverse(object.pf_expr))
        if object.pf_op is not None:
            graph_list.append(object.pf_op.op)
        if object.pf_offset is not None:
            graph_list.append(object.pf_offset)

        return graph_list


class cppUnExpr(cppExpr):
    def __init__(self, un_expr: cppExpr, un_op: cppOp):

        super().__init__(un_expr, un_op, None)

        self.un_expr = un_expr
        self.un_op = un_op
        self.expr_type = self.un_expr.expr_type
        global errors_found

        if self.un_op and self.un_expr.expr_type and self.un_op.op == "&":
            if "pointer" not in self.expr_type.typename:
                self.expr_type.typename = "pointer_" + self.un_expr.expr_type.typename
            self.un_expr.expr_type.typename = self.expr_type.typename
            # if isinstance(self.un_expr, cppPostfixExpr):
            #     self.un_expr.pf_expr.expr_type.typename = self.expr_type.typename

        elif self.un_op and self.un_expr.expr_type and self.un_op.op == "*":
            if len(self.un_expr.expr_type.typename.split("_")) > 1:
                self.expr_type.typename = self.un_expr.expr_type.typename.split("_")[1]
            else:
                print(
                    f"Invalid type {self.un_expr.expr_type.typename} dereferenced at line {driver.lexer.lineno}"
                )
                errors_found += 1

        if (
            isinstance(self.un_expr, cppPostfixExpr)
            and self.un_expr.pf_op
            and self.un_expr.pf_op.op == "."
        ):
            self.un_expr.expr_type = self.un_expr.pf_id._type
            self.expr_type = self.un_expr.expr_type

        self.check_un()

    def check_un(self):
        global errors_found
        # Only int / float can have unary op, if & used for pointer then var should have been inited
        if isinstance(self.un_expr, cppCastExpr):
            if (
                self.un_op in ["!", "~"]
                and self.un_expr.expr_type != "int"
                and "int" not in typecast_compat[self.un_expr.expr_type]
            ):

                print(
                    f"Invalid type {self.un_expr.expr_type} for {self.un_op} operator at line {driver.lexer.lineno}"
                )
                errors_found += 1
                return False

            if self.un_op == "&" and not symboltab.get_current_scope().find_variable(
                self.un_expr.lhs.node_name
            ):
                print(
                    f"Variable {self.un_expr.lhs.node_name} referenced without initialization at line {driver.lexer.lineno}"
                )
                errors_found += 1
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
                    f"Invalid type {self.un_expr.expr_type} for {self.un_op} operator at line {driver.lexer.lineno}"
                )
                errors_found += 1
                return False

        if self.un_op == "*" and self.un_expr.expr_type != "pointer":
            print(
                f"Invalid de-referencing for a non-pointer expression {self.un_expr} at line {driver.lexer.lineno}"
            )
            errors_found += 1
            return False
            # elif self.un_op == SIZEOF and self.un_expr.expr_type not in allowed_native_types:
            #     print(f"Invalid type {self.un_expr.expr_type} for {self.un_op} operator at {driver.lexer.lineno}")
            #     return False

        return True

    @staticmethod
    def traverse(object):
        graph_list = []
        if object.un_expr is not None:
            graph_list.append(object.un_expr.traverse(object.un_expr))
        if object.un_op is not None:
            graph_list.append(object.un_op.op)

        return graph_list


class cppCastExpr(cppExpr):
    def __init__(
        self, cast_expr: cppUnExpr, new_type: cppType, init_type: cppType = None
    ):
        super().__init__(cast_expr, cppOp("cast"), None)

        self.cast_expr = cast_expr
        self.init_type = self.cast_expr.expr_type
        self.new_type = new_type
        self.expr_type = self.new_type

        if self.check_cast():
            if len(self.init_type.split("_")) > 1:
                if self.init_type.split("_")[0] == "constant":
                    self.cast_expr = cppConst(self.cast_expr.un_expr.lhs, self.new_type)

    def check_cast(self):
        global errors_found
        if self.new_type not in typecast_compat[self.init_type]:
            print(
                f"Invalid type {self.new_type} for typecasting variable of type {self.init_type} at line {driver.lexer.lineno}"
            )
            errors_found += 1
            return False

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

        self.cast_lhs = cast_lhs
        self.cast_rhs = cast_rhs
        self.cast_op = cast_op

        if isinstance(self.expr_type, str):
            self.expr_type = cppType(self.expr_type)

        if isinstance(self.lhs, cppPostfixExpr) and isinstance(self.lhs.pf_expr, cppId):
            self.lhs.expr_type = self.lhs.pf_expr._type

        elif isinstance(self.lhs, cppPostfixExpr) and isinstance(
            self.lhs.pf_expr, cppPostfixExpr
        ):
            if self.lhs.pf_op and self.lhs.pf_op.op == ".":
                if (
                    self.lhs.pf_expr.pf_expr._type.typename.split("_")[0]
                    in global_structs.keys()
                ):
                    self.lhs.expr_type = cppType(
                        global_structs[
                            self.lhs.pf_expr.pf_expr._type.typename.split("_")[0]
                        ][self.lhs.pf_id.name][0]
                    )

        if isinstance(self.rhs, cppPostfixExpr) and isinstance(self.rhs.pf_expr, cppId):
            self.rhs.expr_type = self.rhs.pf_expr._type

        elif isinstance(self.rhs, cppPostfixExpr) and isinstance(
            self.rhs.pf_expr, cppPostfixExpr
        ):
            if self.rhs.pf_op and self.rhs.pf_op.op == ".":
                if (
                    self.rhs.pf_expr.pf_expr._type.typename.split("_")[0]
                    in global_structs.keys()
                ):
                    self.rhs.expr_type = cppType(
                        global_structs[
                            self.rhs.pf_expr.pf_expr._type.typename.split("_")[0]
                        ][self.rhs.pf_id.name][0]
                    )

        self.check_arith()

    def check_arith(self):
        global errors_found
        if self.op.op not in operators["arithmetic_op"]:
            print(
                f"Invalid operator {self.op.op} for arithmetic expression at line {driver.lexer.lineno}"
            )
            errors_found += 1
            return False

        if (
            self.lhs.expr_type
            and self.lhs.expr_type.typename not in operator_compat[self.op.op]
            and self.lhs.expr_type.typename != ""
        ):
            print(
                f"Operator {self.op.op} not compatible with type {self.lhs.expr_type.typename} at line {driver.lexer.lineno}"
            )
            errors_found += 1
            return False

        if (
            self.rhs.expr_type
            and self.rhs.expr_type.typename not in operator_compat[self.op.op]
            and self.rhs.expr_type.typename != ""
        ):
            print(
                f"Operator {self.op.op} not compatible with type {self.rhs.expr_type.typename} at line {driver.lexer.lineno}"
            )
            errors_found += 1
            return False

        # if self.lhs.expr_type != self.rhs.expr_type:
        #     if self.rhs.expr_type not in typecast_compat[self.lhs.expr_type] and \
        #        self.lhs.expr_type not in typecast_compat[self.rhs.expr_type]:
        #         print(f"Invalid types {self.lhs.expr_type} and {self.rhs.expr_type} for arithmetic expression at {driver.lexer.lineno}")
        #         return False

        return True

    @staticmethod
    def traverse(object):
        graph_list = []
        if object.cast_lhs is not None:
            graph_list.append(object.cast_lhs.traverse(object.cast_lhs))
        if object.cast_op is not None:
            graph_list.append(object.cast_op.op)
        if object.cast_rhs is not None:
            graph_list.append(object.cast_rhs.traverse(object.cast_rhs))
        return graph_list


class cppShiftExpr(cppExpr):
    def __init__(
        self, shift_lhs: cppArithExpr, shift_op: cppOp, shift_rhs: cppArithExpr
    ):
        super().__init__(shift_lhs, shift_op, shift_rhs)

        self.shift_lhs = shift_lhs
        self.shift_rhs = shift_rhs
        self.shift_op = shift_op

        self.check_shift()

    def check_shift(self):
        return True

    def traverse(self):
        pass
        # return object.shift_lhs.traverse()


class cppRelationExpr(cppExpr):
    def __init__(self, rel_lhs: cppShiftExpr, rel_op: cppOp, rel_rhs: cppShiftExpr):
        super().__init__(rel_lhs, rel_op, rel_rhs)

        self.rel_lhs = rel_lhs
        self.rel_rhs = rel_rhs
        self.rel_op = rel_op

        self.check_relexpr()

    def check_relexpr(self):
        global errors_found
        if self.rel_op.op not in operators["comparison_op"]:
            print(
                f"Invalid operator {self.rel_op.op} for relational expression at line {driver.lexer.lineno}"
            )
            errors_found += 1
            return False

        # if self.rel_lhs.expr_type != self.rel_rhs.expr_type:
        #     print(
        #         f"Operator {self.rel_op} not compatible with different types {self.rel_lhs.expr_type} and {self.rel_rhs.expr_type} at {driver.lexer.lineno}"
        #     )
        # k_type = ""
        # for k, v in operators.items():
        #     if self.rel_op.op in v:
        #         k_type = k
        #         break

        if (
            self.rel_lhs
            and self.rel_lhs.expr_type
            and self.rel_lhs.expr_type.typename not in operator_compat[self.rel_op.op]
        ):
            print(
                f"Operator {self.rel_op.op} not compatible with type {self.rel_lhs.expr_type.typename} at line {driver.lexer.lineno}"
            )
            errors_found += 1
            return False

        elif (
            self.rel_rhs
            and self.rel_rhs.expr_type
            and self.rel_rhs.expr_type.typename not in operator_compat[self.rel_op.op]
        ):
            print(
                f"Operator {self.rel_op.op} not compatible with type {self.rel_rhs.expr_type.typename} at line {driver.lexer.lineno}"
            )
            errors_found += 1
            return False

        # if self.lhs.expr_type != self.rhs.expr_type:
        #     if self.rhs.expr_type not in typecast_compat[self.lhs.expr_type] and \
        #        self.lhs.expr_type not in typecast_compat[self.rhs.expr_type]:
        #         print(f"Invalid types {self.lhs.expr_type} and {self.rhs.expr_type} for relational expression at {driver.lexer.lineno}")
        #         return False

        return True

    @staticmethod
    def traverse(object):
        if isinstance(object, List):
            return [
                object[0].rel_op.op,
                object[0].rel_lhs.lhs.traverse(object[0].rel_lhs.lhs),
                object[0].rel_rhs.lhs.traverse(object[0].rel_rhs.lhs),
            ]
        else:
            return [
                object.rel_op.op,
                object.rel_lhs.lhs.traverse(object.rel_lhs.lhs),
                object.rel_rhs.lhs.traverse(object.rel_rhs.lhs),
            ]


class cppLogicExpr(cppExpr):
    def __init__(self, l_lhs: cppRelationExpr, l_op: cppOp, l_rhs: cppRelationExpr):
        super().__init__(l_lhs, l_op, l_rhs)

        self.l_lhs = l_lhs
        self.l_rhs = l_rhs
        self.l_op = l_op

        self.check_logic()

    def check_logic(self):
        global errors_found
        if (
            self.l_op.op not in operators["bitwise_op"]
            and self.l_op.op not in operators["boolean_op"]
        ):
            print(
                f"Invalid operator {self.l_op.op} for logical expression at line {driver.lexer.lineno}"
            )
            errors_found += 1
            return False

        # Single expression should have unary ops only
        if self.l_rhs is None and self.l_op.op not in ["!", "~"]:
            print(
                f"Invalid binary operator {self.l_op.op} for unary logical expression at line {driver.lexer.lineno}"
            )
            errors_found += 1
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

        self.unaryexpr = unaryexpr
        self.assign_op = assign_op
        self.assign_expr = assign_expr
        self.check_assign()
        global errors_found

        # if isinstance(self.unaryexpr.un_expr, cppPostfixExpr) and self.unaryexpr.un_expr.pf_op.op == ".":
        #     # check field memership
        #     _struct_type = None
        #     if self.unaryexpr.un_expr.pf_expr.pf_expr.name in symboltab.get_current_scope().variables.keys():
        #         _struct_type = symboltab.get_current_scope().variables[self.unaryexpr.un_expr.pf_expr.pf_expr.name].typename.split("_")[0]

        #     if self.unaryexpr.un_expr.pf_id.name not in global_structs[_struct_type].keys():
        #         print(f'Invalid field {self.unaryexpr.un_expr.pf_id.name} for struct object of type {_struct_type} at line {driver.lexer.lineno}')

        if (
            self.unaryexpr
            and self.assign_expr
            and self.unaryexpr.expr_type
            and self.assign_expr.expr_type
        ):
            if (
                isinstance(self.unaryexpr.expr_type, cppType)
                and isinstance(self.assign_expr.expr_type, cppType)
                and self.unaryexpr.expr_type.typename
                != self.assign_expr.expr_type.typename
            ):
                if (
                    "pointer" in self.unaryexpr.expr_type.typename
                    or "pointer" in self.assign_expr.expr_type.typename
                ):
                    errors_found += 1
                    print(
                        f"Type mismatch for assignment, got types {self.unaryexpr.expr_type.typename} and {self.assign_expr.expr_type.typename} at line {driver.lexer.lineno}"
                    )
            elif (
                isinstance(self.unaryexpr.expr_type, str)
                and isinstance(self.assign_expr.expr_type, str)
                and self.unaryexpr.expr_type != self.assign_expr.expr_type
            ):
                if (
                    "pointer" in self.unaryexpr.expr_type.typename
                    or "pointer" in self.assign_expr.expr_type.typename
                ):
                    errors_found += 1
                    print(
                        f"Type mismatch for assignment, got types {self.unaryexpr.expr_type} and {self.assign_expr.expr_type} at line {driver.lexer.lineno}"
                    )

            if isinstance(self.unaryexpr.un_expr, cppPostfixExpr) and isinstance(
                self.assign_expr, cppPostfixExpr
            ):
                if isinstance(self.unaryexpr.un_expr.pf_expr, cppId) and isinstance(
                    self.assign_expr.pf_expr, cppId
                ):
                    if (
                        "pointer" in self.unaryexpr.un_expr.pf_expr._type.typename
                        and "pointer" in self.assign_expr.pf_expr._type.typename
                    ):
                        if (
                            self.unaryexpr.un_expr.pf_expr._type.typename.split("_")[1]
                            != self.assign_expr.pf_expr._type.typename.split("_")[1]
                        ):
                            pass
                        else:
                            if (
                                self.assign_expr.pf_expr.name
                                in symboltab.get_current_scope().pointers.keys()
                            ):
                                symboltab.get_current_scope().pointers[
                                    self.unaryexpr.un_expr.pf_expr.name
                                ] = symboltab.get_current_scope().pointers[
                                    self.assign_expr.pf_expr.name
                                ]
                            else:
                                errors_found += 1
                                print(
                                    f"Cannot assign {self.unaryexpr.un_expr.pf_expr.name} to uninitialized pointer {self.assign_expr.pf_expr.name} at line {driver.lexer.lineno}"
                                )

        if isinstance(self.assign_expr, cppUnExpr):
            # p = &x
            if not symboltab.get_current_scope().find_variable(
                self.assign_expr.un_expr.pf_expr.name
            ):
                errors_found += 1
                print(
                    f"Pointer to variable {self.assign_expr.un_expr.pf_expr.name} referenced without initialization at line {driver.lexer.lineno}"
                )
            else:
                if isinstance(self.unaryexpr.un_expr, cppUnExpr):

                    # \*p = \*x case
                    if (
                        self.unaryexpr.un_expr.un_expr.pf_expr.name
                        not in symboltab.get_current_scope().pointers.keys()
                    ):
                        errors_found += 1
                        print(
                            f"Variable {self.unaryexpr.un_expr.un_expr.pf_expr.name} dereferenced without initialization as pointer at line {driver.lexer.lineno}"
                        )

                    elif (
                        self.assign_expr.un_expr.pf_expr.name
                        not in symboltab.get_current_scope().pointers.keys()
                    ):
                        errors_found += 1
                        print(
                            f"Variable {self.assign_expr.un_expr.pf_expr.name} dereferenced without initialization as pointer at line {driver.lexer.lineno}"
                        )
                    else:
                        symboltab.get_current_scope().pointers[
                            self.unaryexpr.un_expr.un_expr.pf_expr.name
                        ] = self.assign_expr.un_expr.pf_expr.name

                else:
                    symboltab.get_current_scope().pointers[
                        self.unaryexpr.un_expr.pf_expr.name
                    ] = self.assign_expr.un_expr.pf_expr.name

        elif isinstance(self.assign_expr, cppPostfixExpr):

            # \*p = 2 or \*p = x
            if (
                isinstance(self.unaryexpr.un_expr, cppUnExpr)
                and isinstance(self.unaryexpr.un_expr.un_expr, cppPostfixExpr)
                # and "pointer" in self.unaryexpr.expr_type.typename
                and self.unaryexpr.un_expr.un_expr.pf_expr.name
                not in symboltab.get_current_scope().pointers.keys()
            ):
                errors_found += 1
                print(
                    f"Cannot assign value to pointer {self.unaryexpr.un_expr.un_expr.pf_expr.name} without pointing to legitimate address at line {driver.lexer.lineno}"
                )
            if isinstance(self.assign_expr.pf_expr, cppId):
                if not symboltab.get_current_scope().find_variable(
                    self.assign_expr.pf_expr.name
                ):
                    if self.assign_expr.pf_expr.name not in curr_param:
                        errors_found += 1
                        print(
                            f"Variable {self.assign_expr.pf_expr.name} assigned without initialization at line {driver.lexer.lineno}"
                        )

    def check_assign(self):
        # Pointer cannot be assigned anything other than pointer / int
        global errors_found
        if (
            self.assign_op in operators["assignment_op"]
            and self.lhs.node_type == "pointer"
            and self.rhs.node_type not in ["int", "pointer"]
        ):
            errors_found += 1
            print(
                f"Pointer {self.unaryexpr} cannot be assigned to non-pointer / non-int {self.assign_expr} at line {driver.lexer.lineno}"
            )
            return False

        return True

    @staticmethod
    def traverse(object):
        graph_list = []
        if object.unaryexpr is not None:
            graph_list.append(object.unaryexpr.traverse(object.unaryexpr))
        if object.assign_op.op is not None:
            graph_list.append(object.assign_op.op)
        if object.assign_expr is not None:
            graph_list.append(object.assign_expr.traverse(object.assign_expr))
        return graph_list


# ------------------------ ------------------------
# DECLARATIONS, FUNCTIONS, CLASSES, STRUCTS
# ------------------------ ------------------------


class cppInitializer(cppNode):
    def __init__(self, init_expr: Union[cppAssignExpr, List["cppInitializer"]]):
        self.init_expr = init_expr
        self.check_init()

    def check_init(self):
        if isinstance(self.init_expr, cppAssignExpr):
            self.init_expr.check_assign()
        # elif isinstance(self.init_expr, list) and isinstance(
        #     self.init_expr[0], "cppInitializer"
        # ):
        #     for init in self.init_expr:
        #         if not init.check_init():
        #             return False

        return True


class cppAbsDeclarator(cppNode):
    def __init__(self, adec_dadec: "cppDirectAbsDeclarator"):
        super().__init__("abstract_declarator")

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
        self.name = name
        if self.name and arr_offset:
            self.name.array_size = arr_offset.pf_expr.val if arr_offset else None
        self.dec_declarator = dec_declarator
        self.dec_type = dec_type
        self.arr_offset = arr_offset
        self.dec_flag = dec_flag
        self.param_list = param_list
        if self.dec_flag == 7:
            self.name = self.dec_declarator.name
        if self.dec_flag == 3:
            self.name = self.dec_declarator.name

        self.check_ddecl()

    def check_ddecl(self):
        return True


class cppInitDeclarator(cppNode):
    def __init__(self, declarator: "cppDeclarator", initializer: cppInitializer):
        super().__init__("init_declarator")

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
            if isinstance(obj.initializer.init_expr.pf_expr, cppConst):
                result.append(
                    (obj.declarator.name.name, obj.initializer.init_expr.pf_expr.val)
                )
            elif isinstance(obj.initializer.init_expr.pf_expr, cppId):
                result.append(
                    (obj.declarator.name.name, obj.initializer.init_expr.pf_expr.name)
                )
        else:
            result.append((obj.declarator.name.name, None))
        return result


class cppInitDecls(cppNode):
    def __init__(self, init_decls: List[cppInitDeclarator]):
        super().__init__("init_declarators")

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

        self.name = name
        self.ddecl = ddecl
        if ddecl is not None:
            self.arr_offset = ddecl.arr_offset
        else:
            self.arr_offset = None

        self.is_pointer = is_pointer

    def check_decl(self):
        return True


# class cppDecSpec(cppNode):
#     def __init__(self):
#         if not super().__init__("declaration_specifier"):
#             return False


class cppDeclaration(cppNode):
    def __init__(
        self,
        decl_type: cppType,
        initdecl_list: cppInitDecls,
        add_to_symboltab: bool = True,
    ):
        super().__init__("declaration")

        if isinstance(decl_type, list):
            self.decl_type = decl_type[0]
        else:
            self.decl_type = decl_type
        self.initdecl_list = initdecl_list
        self.cmpd_idx = symboltab.cmpd_ctr
        self.add_to_symboltab = add_to_symboltab
        if symboltab.get_current_scope().scope_name == "Global" and initdecl_list:
            symboltab.add_scope_to_stack(f"cmpd_{symboltab.cmpd_ctr}")
        # elif (
        #     symboltab.get_current_scope().scope_name[5:] == str(symboltab.cmpd_ctr)
        # ):
        #     symboltab.add_scope_to_stack(f"cmpd_{symboltab.cmpd_ctr+1}")
        self.check_declaration()

    def check_declaration(self):
        global errors_found
        if self.initdecl_list is not None:
            for init in self.initdecl_list:
                # Void assignment invalid

                if self.decl_type == "void":
                    print(
                        f"Void variable {init.name} cannot be assigned a value at line {driver.lexer.lineno}"
                    )
                    errors_found += 1
                    return False

                # Array offset check
                if (
                    init.declarator.arr_offset
                    and init.declarator.arr_offset.pf_expr._type.typename != "int"
                ):
                    print(
                        f"Array size {init.declarator.arr_offset.pf_expr.val} must be of int type at line {driver.lexer.lineno}"
                    )
                    errors_found += 1
                    return False

                # Redeclaring variable
                if symboltab.get_current_scope().find_variable(init.declarator.name):
                    print(
                        f"Re-declared variable {init.declarator.name} at line {driver.lexer.lineno}"
                    )
                    errors_found += 1
                    return False

                if (
                    init.declarator.is_pointer
                    and "pointer" not in self.decl_type.typename
                ):
                    self.decl_type.typename = "pointer_" + self.decl_type.typename

                if self.add_to_symboltab:

                    if "struct" in self.decl_type.typename:
                        if (
                            self.decl_type.typename.split("_")[0]
                            in global_structs.keys()
                        ):
                            for element in global_structs[
                                self.decl_type.typename.split("_")[0]
                            ].keys():
                                _name = f"{self.decl_type.typename.split('_')[0]}_{init.declarator.name.name}_{element}"
                                _type = global_structs[
                                    self.decl_type.typename.split("_")[0]
                                ][element][0]
                                element_array_size = global_structs[
                                    self.decl_type.typename.split("_")[0]
                                ][element][1]
                                symboltab.check_and_add_variable(
                                    cppId(_name, cppType(_type), element_array_size),
                                    cppType(_type),
                                )

                                curr_scope = symboltab.get_current_scope()
                                reg_name = curr_scope.var_to_string_map[_name]
                                register_type[reg_name] = (
                                    "reg",
                                    _type,
                                    element_array_size,
                                )
                        else:
                            errors_found += 1
                            print(
                                f"Structure {self.decl_type.typename.split('_')[0]} does not exist at line {driver.lexer.lineno}"
                            )
                    symboltab.check_and_add_variable(
                        init.declarator.name, self.decl_type
                    )
                    curr_scope = symboltab.get_current_scope()
                    if init.declarator.name.array_size > 0:
                        reg_type = "reg_array"
                        register_type[
                            curr_scope.var_to_string_map[init.declarator.name.name]
                        ] = (
                            reg_type,
                            self.decl_type.typename,
                            init.declarator.name.array_size,
                        )
                    else:
                        reg_type = "reg"
                        if self.decl_type.typename.split("_")[0] == "pointer":
                            reg_type = (
                                f"reg_pointer_{self.decl_type.typename.split('_')[1]}"
                            )
                            register_type[
                                curr_scope.var_to_string_map[init.declarator.name.name]
                            ] = (
                                reg_type,
                                "int",
                                init.declarator.name.array_size,
                            )
                        else:
                            if self.decl_type.typename in ["int", "char", "float"]:
                                reg_type = "reg"
                                register_type[
                                    curr_scope.var_to_string_map[
                                        init.declarator.name.name
                                    ]
                                ] = (
                                    reg_type,
                                    self.decl_type.typename,
                                    init.declarator.name.array_size,
                                )

                    init.declarator.ddecl.dec_type = self.decl_type
                    init.declarator.name._type = self.decl_type
                    init.declarator.name.node_type = (
                        "identifier_" + self.decl_type.typename
                    )

                    # if init.declarator.is_pointer:
                    #     reg = curr_scope.var_to_string_map[init.declarator.name.name]
                    #     register_type[reg] = (
                    #         "reg",
                    #         init.declarator.name._type.typename,
                    #     )

        return True

    @staticmethod
    def traverse(object):
        graph_list = [object.decl_type.traverse(object.decl_type)]

        if object.initdecl_list is not None:

            for init_decls in object.initdecl_list:
                if init_decls.declarator.is_pointer:
                    graph_list[0][0] = "pointer_" + graph_list[0][0]
                if init_decls.declarator.arr_offset is not None:
                    if isinstance(init_decls.declarator.arr_offset.pf_expr, cppConst):
                        graph_list.append(
                            (
                                init_decls.traverse(init_decls),
                                init_decls.declarator.arr_offset.traverse(
                                    init_decls.declarator.arr_offset
                                )[0][2],
                            )
                        )
                else:
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
        global errors_found
        if self.stmt_type not in [
            "compound",
            "expr",
            "select",
            "iterate",
            "jump",
            "label",
        ]:
            errors_found += 1
            print(
                f"Invalid statement type {self.stmt_type} at line {driver.lexer.lineno}"
            )
            return False

        return True

    @staticmethod
    def traverse(object):
        return [object.stmt]


class cppCompoundStmt(cppStmt):
    def __init__(self, cmpd_decls: List[cppDeclaration], cmpd_stmts: List[cppStmt]):
        super().__init__("compound")

        self.cmpd_decls = cmpd_decls

        self.cmpd_stmts = cmpd_stmts
        self.stmt = [cmpd_decls, cmpd_stmts]

        self.idx = cmpd_decls[0].cmpd_idx if cmpd_decls is not None else 0

        # if self.cmpd_decls is not None:
        #     for decl in self.cmpd_decls:
        #         decl_type = decl.decl_type

        #         for dec_n in decl.initdecl_list:
        #             if dec_n.declarator.is_pointer:
        #                 decl_type = cppType(f"pointer_{decl_type.typename}")
        #             symboltab.check_and_add_variable(dec_n.declarator.name, decl_type)

        # symboltab.remove_scope_from_stack()

        self.check_cmpd()

    def check_cmpd(self):
        if self.cmpd_stmts:
            for ostm in self.cmpd_stmts:
                if not isinstance(
                    ostm, (cppCompoundStmt, cppIterateStmt, cppJumpStmt, cppSelectStmt)
                ):
                    for stm in ostm:

                        if isinstance(stm, cppPostfixExpr):
                            if isinstance(stm.pf_expr, cppId):
                                symboltab.check_undeclared_variable(stm.pf_expr)
                            elif not isinstance(stm.pf_expr, cppConst):
                                symboltab.check_undeclared_variable(stm.pf_expr.pf_expr)

                        elif isinstance(stm, cppAssignExpr):

                            if isinstance(
                                stm.unaryexpr.un_expr, cppUnExpr
                            ) and isinstance(
                                stm.unaryexpr.un_expr.un_expr.pf_expr, cppId
                            ):
                                symboltab.check_undeclared_variable(
                                    stm.unaryexpr.un_expr.un_expr.pf_expr
                                )
                            elif isinstance(stm.unaryexpr.un_expr.pf_expr, cppId):
                                symboltab.check_undeclared_variable(
                                    stm.unaryexpr.un_expr.pf_expr
                                )
                            elif isinstance(
                                stm.assign_expr, cppArithExpr
                            ) and isinstance(stm.assign_expr.cast_lhs.pf_expr, cppId):
                                symboltab.check_undeclared_variable(
                                    stm.assign_expr.cast_lhs.pf_expr
                                )
                            elif isinstance(
                                stm.assign_expr, cppArithExpr
                            ) and isinstance(
                                stm.assign_expr.cast_lhs.pf_expr.pf_expr, cppId
                            ):
                                symboltab.check_undeclared_variable(
                                    stm.assign_expr.cast_lhs.pf_expr.pf_expr
                                )

                            elif (
                                stm.assign_expr
                                and not isinstance(stm.assign_expr, cppPostfixExpr)
                                and isinstance(stm.assign_expr.un_expr.pf_expr, cppId)
                            ):
                                symboltab.check_undeclared_variable(
                                    stm.assign_expr.un_expr.pf_expr
                                )

                            elif isinstance(
                                stm.assign_expr, cppPostfixExpr
                            ) and isinstance(stm.assign_expr.pf_expr, cppId):
                                symboltab.check_undeclared_variable(
                                    stm.assign_expr.pf_expr
                                )

        return True

    @staticmethod
    def traverse(object):
        graph_list = ["Compound_Statement"]
        if object.cmpd_decls is not None:
            for cmpd_decl in object.cmpd_decls:
                graph_list.append(cmpd_decl.traverse(cmpd_decl))
        if object.cmpd_stmts is not None:
            for cmpd_stmt in object.cmpd_stmts:
                if isinstance(cmpd_stmt, List):
                    for s in cmpd_stmt:
                        graph_list.append(s.traverse(s))
                else:
                    graph_list.append(cmpd_stmt.traverse(cmpd_stmt))
        return graph_list


class cppExprStmt(cppStmt):
    def __init__(self, e_expr: cppExpr):
        super().__init__("expr")

        self.e_expr = e_expr
        self.stmt = [e_expr]
        self.check_exprstmt()

    def check_exprstmt(self):
        return isinstance(self.e_expr, cppExpr)

    @staticmethod
    def traverse(obj):
        return [obj.e_expr.traverse(obj.e_expr)]


class cppSelectStmt(cppStmt):
    def __init__(
        self,
        select_expr: cppExpr,
        select_if_stmt: cppStmt,
        select_else_stmt: cppStmt = None,
    ):
        super().__init__("select")

        self.select_expr = select_expr
        self.select_if_stmt = select_if_stmt
        self.select_else_stmt = select_else_stmt
        self.stmt = [select_expr, select_if_stmt, select_else_stmt]

    def check_selectstmt(self):
        return (
            isinstance(self.select_expr, cppExpr)
            and isinstance(self.select_if_stmt, cppStmt)
            and isinstance(self.select_else_stmt, cppStmt)
        )

    @staticmethod
    def traverse(object):
        graph_list = ["if", object.select_expr[0].traverse(object.select_expr)]
        if object.select_if_stmt is not None:
            graph_list.append(object.select_if_stmt.traverse(object.select_if_stmt))
        if object.select_else_stmt is not None:
            graph_list.append(object.select_else_stmt.traverse(object.select_else_stmt))

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

        self.iter_type = iter_type  # ['while', 'for', 'for_init']
        self.iter_init_stmt = iter_init_stmt
        self.iter_check_stmt = iter_check_stmt
        self.iter_update_expr = iter_update_expr

        self.body_stmt = body_stmt
        self.stmt = [iter_type, iter_init_stmt, iter_check_stmt, iter_update_expr]
        if self.iter_type == "for_init":
            i_type = self.iter_init_stmt[0]
            i_init = cppInitializer(self.iter_init_stmt[1])
            idx = 0
            for i, scope in enumerate(symboltab.scope_list):
                if scope.scope_name == f"cmpd_{body_stmt.idx}":
                    idx = i
                    break
            symboltab.scope_stack.append(symboltab.scope_list[idx])
            symboltab.check_and_add_variable(
                i_init.init_expr[0].unaryexpr.un_expr.pf_expr, i_type
            )
            symboltab.scope_stack.pop()

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
        graph_list = [object.iter_type]
        if object.iter_init_stmt is not None:
            graph_list.append(
                object.iter_init_stmt[0].traverse(object.iter_init_stmt[0])
            )
            if len(object.iter_init_stmt) > 1:
                for i in range(len(object.iter_init_stmt[1])):
                    if object.iter_init_stmt[1][i] is not None:
                        graph_list.append(
                            object.iter_init_stmt[1][i].traverse(
                                object.iter_init_stmt[1][i]
                            )
                        )
        if object.iter_check_stmt is not None:
            for s in object.iter_check_stmt:
                graph_list.append(s.traverse(s))
        if object.iter_update_expr is not None:
            for s in object.iter_update_expr:
                graph_list.append(s.traverse(s))

        graph_list.append(object.body_stmt.traverse(object.body_stmt))
        # return [
        #     object.iter_type,
        #     object.iter_init_stmt.traverse(object.iter_init_stmt),
        #     object.iter_check_stmt.traverse(object.iter_check_stmt),
        #     object.iter_update_expr.traverse(object.iter_update_expr),
        #     [],
        # ]
        return graph_list


class cppJumpStmt(cppStmt):
    def __init__(self, jump_type: str, jump_expr: cppExpr = None):
        super().__init__("jump")

        self.jump_type = jump_type
        self.jump_expr = jump_expr
        self.stmt = [jump_type, jump_expr]
        self.check_jumpstmt()

    def check_jumpstmt(self):
        global errors_found
        if self.jump_type not in ["break", "continue", "goto", "return"]:
            errors_found += 1
            print(f"Invalid statement {self.jump_type} at line {driver.lexer.lineno}")
            return False

        if self.jump_type == "break":
            scope = symboltab.get_current_scope()
            flag = False
            while scope:
                if scope.scope_name == "loop":
                    flag = True
                scope = scope.parent
            if not flag:
                # errors_found += 1
                # print(f"Break statement not within loop at line {driver.lexer.lineno}")
                return False

        elif self.jump_type == "continue":
            scope = symboltab.get_current_scope()
            flag = False
            while scope:
                if scope.scope_name == "loop":
                    flag = True
                scope = scope.parent
            if not flag:
                # errors_found += 1
                # print(
                #     f"Continue statement not within loop at line {driver.lexer.lineno}"
                # )
                return False

    @staticmethod
    def traverse(object):
        if object.jump_expr is not None:
            return [object.jump_type, object.jump_expr.traverse(object.jump_expr)]
        else:
            return [object.jump_type]


class cppLabelStmt(cppStmt):
    def __init__(self, label_id: cppId, label_stmt: cppStmt):
        super().__init__("label")

        self.label_id = label_id
        self.label_stmt = label_stmt
        self.stmt = [label_id, label_stmt]

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

        self.pdec_type = pdec_type
        self.pdec_param = pdec_param
        self.pdec_param.name._type = self.pdec_type

        self.check_pdec()

    def check_pdec(self):
        return True


stack_space = {}
saved_reg = {}


# def write_activation():
#     global stack_space
#     with open("activation_record.csv", "w") as f_w:
#         writer = csv.writer(f_w)
#         writer.writerow(
#             [
#                 "Function name",
#                 "Local / Param",
#                 "Variable name",
#                 "Variable size",
#                 "Old Stack pointer size",
#             ]
#         )
#         for func in stack_space.keys():
#             for var in stack_space[func]:
#                 writer.writerow([func, var["location"], var["name"], var["size"], 4])


class cppFuncDef(cppNode):
    def __init__(
        self,
        func_type: cppType,
        func_decl: cppDeclarator,
        func_stmt: cppCompoundStmt,
    ):
        global stack_space
        global errors_found
        super().__init__("function_definition")

        self.func_type = func_type
        self.func_name = func_decl.ddecl.name
        self.func_param_list = func_decl.ddecl.param_list
        self.func_stmt = func_stmt
        self.func_nparams = len(self.func_param_list) if self.func_param_list else 0

        self.scope_id = func_stmt.idx

        idx = 0
        for i, l_scope in enumerate(symboltab.scope_list):
            if l_scope.scope_name == f"cmpd_{self.scope_id}":
                idx = i
                break

        stack_space[self.func_name.name] = []
        saved_reg[self.func_name.name] = []

        # if os.path.exists("activation.csv"):
        #     os.remove("activation.csv")
        if self.func_param_list is not None:
            for prm in self.func_param_list:
                stack_space[self.func_name.name].append(
                    {
                        "name": prm.pdec_param.name.name,
                        "size": dtype_size[prm.pdec_type.typename],
                        "is_return": False,
                        "location": "param",
                    }
                )

        if self.func_stmt.cmpd_decls is not None:
            for decl in self.func_stmt.cmpd_decls:
                var_type = decl.decl_type
                for var in decl.initdecl_list:
                    stack_space[self.func_name.name].append(
                        {
                            "name": var.declarator.name.name,
                            "size": max(1, var.declarator.name.array_size)
                            * dtype_size[var_type.typename],
                            "is_return": False,
                            "location": "local",
                        }
                    )

        return_expr = None

        if self.func_stmt.cmpd_stmts is None:
            if self.func_type.typename != "void":
                errors_found += 1
                print(
                    f"Function of type {self.func_type.typename} at line {driver.lexer.lineno} should have a return statement"
                )
        else:
            if not (
                isinstance(self.func_stmt.cmpd_stmts[-1], cppJumpStmt)
                and self.func_stmt.cmpd_stmts[-1].jump_type == "return"
            ):
                if self.func_type.typename != "void":
                    errors_found += 1
                    print(
                        f"Function of type {self.func_type.typename} at line {driver.lexer.lineno} should have a return statement"
                    )
            else:
                if self.func_stmt.cmpd_stmts[-1].jump_expr is not None:
                    return_expr = self.func_stmt.cmpd_stmts[-1].jump_expr
                else:
                    if self.func_type.typename != "void":
                        errors_found += 1
                        print(
                            f"Function of type {self.func_type.typename} at line {driver.lexer.lineno} should have a return expression. \n"
                        )

        # Check return expr type
        if return_expr:
            if (
                isinstance(return_expr.expr_type, str)
                and return_expr.expr_type != self.func_type.typename
            ):
                # print(
                #     f"Return Types {return_expr.expr_type}, {self.func_type.typename} mismatch at line {driver.lexer.lineno}"
                # )
                pass
            elif (
                isinstance(return_expr.expr_type, cppType)
                and return_expr.expr_type.typename != self.func_type.typename
            ):
                # print(
                #     f"Return Types {return_expr.expr_type.typename}, {self.func_type.typename} mismatch at line {driver.lexer.lineno}"
                # )
                pass

        # symboltab.scope_stack.append(symboltab.scope_list[idx])
        # symboltab.add_scope_to_stack(self.func_name.name)
        symboltab.check_and_add_function(
            self.func_name,
            self.func_type,
            self.func_nparams,
            self.func_param_list,
            self.scope_id,
        )

        if self.func_param_list is not None:
            for param in self.func_param_list:
                p_type = param.pdec_type
                p_name = param.pdec_param.name
                symboltab.check_and_add_variable(p_name, p_type)
        # symboltab.scope_stack.pop()
        self.check_func_def()

    def check_func_def(self):
        return True

    @staticmethod
    def traverse(object):
        graph_list = [
            "Function_Declaration",
            object.func_type.traverse(object.func_type),
            object.func_name.name,
        ]
        if object.func_param_list is not None:
            for i in object.func_param_list:
                graph_list.append(i.pdec_param.name.traverse(i.pdec_param.name))
        graph_list.append(object.func_stmt.traverse(object.func_stmt))

        return graph_list


class cppBaseSpec(cppNode):
    def __init__(self, bspec_id: cppId, bspec_acc_spec: str):
        super().__init__("base_specifier")

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

        self.decl_type = decl_type
        self.memberdecl_list = memberdecl_list
        self.member_type = member_type
        self.member_access = member_access
        self.check_member_dec()

    def check_member_dec(self):
        global errors_found
        if self.member_type not in ["var", "func"]:
            errors_found += 1
            print(
                f"Member declaration of type {self.member_type} not valid at line {driver.lexer.lineno}"
            )
            return False

        for memb in self.memberdecl_list:
            # Void assignment invalid
            if self.decl_type == "void":
                errors_found += 1
                print(
                    f"Void variable {memb.name} cannot be assigned a value at line {driver.lexer.lineno}"
                )
                return False

            # Array offset check
            if (
                memb.declarator.arr_offset is not None
                and memb.declarator.arr_offset.node_type.split("_")[1] != "int"
            ):
                errors_found += 1
                print(
                    f"Array offset {memb.declarator.arr_offset} must be of int type at line {driver.lexer.lineno}"
                )
                return False

            # Redeclaring variable
            if symboltab.get_current_scope().find_variable(memb.declarator.name):
                errors_found += 1
                print(
                    f"Re-declared variable {memb.declarator.name} at line {driver.lexer.lineno}"
                )
                return False

            # symboltab.check_and_add_variable(memb.declarator.name, self.decl_type)

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
                self.f_local_vars.append(
                    (
                        f_init_decl.declarator.name,
                        f_dec_type,
                        f_init_decl.declarator.array_size,
                    )
                )

        for f_var in self.f_local_vars:
            symboltab.check_and_add_variable(f_var)

        # symboltab.remove_scope_from_stack()

        self.check_func()

    def check_func(self):
        return True

    @staticmethod
    def traverse(object):
        pass


class cppStructDeclarator(cppDeclarator):
    def __init__(self, s_declarator: cppDeclarator, s_con_expr: cppCondExpr = None):
        super().__init__(s_declarator.name)
        self.declarator = s_declarator
        self.s_con_expr = s_con_expr

        self.check_s_declarator()

    def check_s_declarator(self):
        return True


class cppStructDeclaration(cppDeclaration):
    def __init__(
        self, s_specifier: List[cppType], s_declarator_list: List[cppStructDeclarator]
    ):
        super().__init__(s_specifier, s_declarator_list, False)
        self.s_specifier = s_specifier
        self.s_declarator_list = s_declarator_list
        self.s_declaration_check()

    def s_declaration_check(self):
        return True

    @staticmethod
    def traverse(object):
        graph_list = []
        if object.s_declarator_list is not None:
            for d in object.s_declarator_list:
                graph_list.append(d.name.traverse(d.name))

        return graph_list


class cppStruct(cppNode):
    def __init__(
        self,
        s_tag: cppId,
        s_id: cppId,
        s_decls: List[cppStructDeclaration] = None,
        s_flag=0,
    ):
        super().__init__("struct")
        global global_structs
        global errors_found
        self.s_tag = s_tag
        self.s_id = s_id
        self.s_flag = s_flag
        self.s_decls = s_decls
        self.struct_size = 0

        # Initialize own scope
        if self.s_flag == 0:
            symboltab.check_and_add_struct(self.s_tag, self.s_id)

            # Extract variables from declarations to add to symboltable scope
            self.s_vars = []
            if self.s_id.name not in global_structs:
                global_structs[self.s_id.name] = {}
            if s_decls is not None:
                for s_decl in s_decls:
                    s_type = s_decl.decl_type

                    s_initdecl_list = s_decl.initdecl_list
                    for i, s_initdecl in enumerate(s_initdecl_list):
                        self.s_vars.append((s_initdecl.declarator.name, s_type))
                        global_structs[self.s_id.name][
                            s_initdecl.declarator.name.name
                        ] = (s_type.typename, s_initdecl.declarator.name.array_size)
                        self.struct_size += dtype_size[s_type.typename]

                for s_var in self.s_vars:
                    symboltab.check_and_add_variable(s_var[0], s_var[1])

            symboltab.remove_scope_from_stack()

            if f"{self.s_tag.name}_struct" not in dtype_size.keys():
                dtype_size[f"{self.s_tag.name}_struct"] = self.struct_size
            else:
                errors_found += 1
                print(
                    f"Redeclaring existing struct {self.s_tag.name} at {driver.lexer.lineno}"
                )
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
            for c_decl, c_var_access in self.c_vardecs:
                c_type = c_decl.decl_type

                c_initdecl_list = c_decl.memberdecl_list
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


driver = Parser(f"tests/test_{args['num']}_processed.cpp")

if args["mode"] == "parse":
    driver.run_parse()
    symboltab.savecsv()
    # write_activation()
    # print(driver.tree)
    # ast1 = cppStart.traverse(driver.tree["data"])
    # # print(ast)
    # graph = pydot.Dot("AST", graph_type="graph")
    # ast, graph = cppStart.gen_graph(driver.tree["data"], graph)
    # graph.write_png("src/AST.png")

elif args["mode"] == "lex":
    driver.run_lex()
    driver.print_tokens()
