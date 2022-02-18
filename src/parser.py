precedence = (
    ("nonassoc", "IF"),
    ("nonassoc", "ELSE"),
)

def p_start(p):
    """
    start : translation_unit
    """
    p[0] = ["start"] + p[1:]



def p_error(p):
    print(f'Error at token: {p.value}')


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
    p[0] = ["predefined_functions"] + p[1:]

def p_primary_expression(p):
    """
    primary_expression : IDENTIFIER
        | constant
        | string
        | LEFT_PARENTHESIS expression RIGHT_PARENTHESIS
        | predefined_functions
    """
    p[0] = ["primary_expression"] + p[1:]


def p_constant(p):
    """
    constant : NUMBER
        | DECIMAL_NUMBER
        | CHARACTER
        | TRUE
        | FALSE
        | NULL
    """
    p[0] = ["constant"] + p[1:]


def p_string(p):
    """
    string : STRING_LITERAL
    """
    p[0] = ["string"] + p[1:]


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
    p[0] = ["postfix_expression"] + p[1:]


def p_argument_expression_list(p):
    """
    argument_expression_list : assignment_expression
        | argument_expression_list COMMA assignment_expression
    """
    p[0] = ["argument_expression_list"] + p[1:]


def p_unary_expression(p):
    """
    unary_expression : postfix_expression
        | PLUS_PLUS unary_expression
        | MINUS_MINUS unary_expression
        | unary_operator cast_expression
        | SIZEOF unary_expression
        | SIZEOF LEFT_PARENTHESIS type_specifier RIGHT_PARENTHESIS
    """
    p[0] = ["unary_expression"] + p[1:]


def p_unary_operator(p):
    """
    unary_operator : AND
                   | STAR
                   | PLUS
                   | MINUS
                   | NOT
                   | TILDE
    """
    p[0] = ["unary_operator"] + p[1:]


def p_cast_expression(p):
    """
    cast_expression : unary_expression
        | LEFT_PARENTHESIS type_specifier RIGHT_PARENTHESIS cast_expression
    """
    p[0] = ["cast_expression"] + p[1:]


def p_multiplicative_expression(p):
    """
    multiplicative_expression : cast_expression
        | multiplicative_expression STAR cast_expression
        | multiplicative_expression DIVIDE cast_expression
        | multiplicative_expression MODULUS cast_expression
    """
    p[0] = ["multiplicative_expression"] + p[1:]


def p_additive_expression(p):
    """
    additive_expression : multiplicative_expression
        | additive_expression PLUS multiplicative_expression
        | additive_expression MINUS multiplicative_expression
    """
    p[0] = ["additive_expression"] + p[1:]


def p_shift_expression(p):
    """
    shift_expression : additive_expression
        | shift_expression LEFT_SHIFT additive_expression
        | shift_expression RIGHT_SHIFT additive_expression
    """
    p[0] = ["shift_expression"] + p[1:]


def p_relational_expression(p):
    """
    relational_expression : shift_expression
        | relational_expression LESS_THAN shift_expression
        | relational_expression GREATER_THAN shift_expression
        | relational_expression LESS_THAN_EQUALS shift_expression
        | relational_expression GREATER_THAN_EQUALS shift_expression
    """
    p[0] = ["relational_expression"] + p[1:]


def p_equality_expression(p):
    """
    equality_expression : relational_expression
        |  equality_expression EQUALS_EQUALS relational_expression
        |  equality_expression NOT_EQUALS relational_expression
    """

    p[0] = ["equality_expression"] + p[1:]


def p_and_expression(p):
    """
    and_expression : equality_expression
        | and_expression AND equality_expression
    """

    p[0] = ["and_expression"] + p[1:]


def p_xor_expression(p):
    """
    xor_expression : and_expression
        | xor_expression XOR and_expression
    """

    p[0] = ["xor_expression"] + p[1:]


def p_or_expression(p):
    """
    or_expression : xor_expression
        | or_expression OR xor_expression
    """

    p[0] = ["or_expression"] + p[1:]


def p_logical_and_expression(p):
    """
    logical_and_expression : or_expression
        | logical_and_expression AND_AND or_expression
    """

    p[0] = ["logical_and_expression"] + p[1:]


def p_logical_or_expression(p):
    """
    logical_or_expression : logical_and_expression
        | logical_or_expression OR_OR logical_and_expression
    """

    p[0] = ["logical_or_expression"] + p[1:]


def p_conditional_expression(p):
    """
    conditional_expression : logical_or_expression
        |  logical_or_expression QUESTION_MARK expression COLON conditional_expression
    """

    p[0] = ["conditional_expression"] + p[1:]


def p_assignment_expression(p):
    """
    assignment_expression : conditional_expression
        | unary_expression assignment_operator assignment_expression

    """

    p[0] = ["assignment_expression"] + p[1:]


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

    p[0] = ["assignment_operator"] + p[1:]


def p_expression(p):
    """
    expression : assignment_expression
        | expression COMMA assignment_expression
    """

    p[0] = ["expression"] + p[1:]


def p_declaration(p):
    """
    declaration : type_specifier SEMICOLON
                | type_specifier init_declarators_list SEMICOLON
                | class_specifier
    """

    p[0] = ["declaration"] + p[1:]


def p_init_declarators_list(p):
    """
    init_declarators_list : init_declarator
        | init_declarators_list COMMA init_declarator
    """

    p[0] = ["init_declarators_list"] + p[1:]


def p_init_declarator(p):
    """
    init_declarator : declarator EQUALS initializer
                    | declarator

    """

    p[0] = ["init_declarator"] + p[1:]


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
    p[0] = ["type_specifier"] + p[1:]


def p_pointer(p):
    """
    pointer : STAR
            | STAR pointer
    """
    p[0] = ["pointer"] + p[1:]


def p_identifier_list(p):
    """
    identifier_list : IDENTIFIER
                    | identifier_list COMMA IDENTIFIER
    """
    p[0] = ["identifier_list"] + p[1:]


def p_specifier_list(p):
    """
    specifier_list : type_specifier specifier_list
                   | type_specifier
    """
    p[0] = ["specifier_list"] + p[1:]


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
    p[0] = ["direct_declarator"] + p[1:]


def p_declarator(p):
    """
    declarator : pointer direct_declarator
               | direct_declarator
    """
    p[0] = ["declarator"] + p[1:]


def p_parameter_list(p):
    """
    parameter_list : parameter_declaration
                   | parameter_list COMMA parameter_declaration
    """
    p[0] = ["parameter_list"] + p[1:]


def p_parameter_declaration(p):
    """
    parameter_declaration : type_specifier declarator
                          | type_specifier abstract_declarator
                          | type_specifier
    """
    p[0] = ["parameter_declaration"] + p[1:]


# Structs
def p_struct_specifier(p):
    """
    struct_specifier : STRUCT IDENTIFIER LEFT_CURLY_BRACKET struct_declaration_list RIGHT_CURLY_BRACKET
                     | STRUCT LEFT_CURLY_BRACKET struct_declaration_list RIGHT_CURLY_BRACKET
                     | STRUCT IDENTIFIER LEFT_CURLY_BRACKET RIGHT_CURLY_BRACKET
                     | STRUCT LEFT_CURLY_BRACKET RIGHT_CURLY_BRACKET
                     | STRUCT IDENTIFIER
    """
    p[0] = ["struct_specifier"] + p[1:]


def p_struct_declarator(p):
    """
    struct_declarator : declarator
                      | COLON conditional_expression
                      | declarator COLON conditional_expression
    """
    p[0] = ["struct_declarator"] + p[1:]


def p_struct_declarator_list(p):
    """
    struct_declarator_list : struct_declarator
                           | struct_declarator_list COMMA struct_declarator
    """
    p[0] = ["struct_declarator_list"] + p[1:]


def p_struct_declaration(p):
    """
    struct_declaration : specifier_list struct_declarator_list SEMICOLON
    """
    p[0] = ["struct_declaration"] + p[1:]


def p_struct_declaration_list(p):
    """
    struct_declaration_list : struct_declaration
                            | struct_declaration_list struct_declaration
    """
    p[0] = ["struct_declaration_list"] + p[1:]


def p_class_head(p):
    """
    class_head : CLASS base_clause
               | CLASS
               | CLASS IDENTIFIER base_clause
               | CLASS IDENTIFIER
    """
    p[0] = ["class_head"] + p[1:]


def p_class_specifier(p):
    """
    class_specifier : class_head LEFT_CURLY_BRACKET member_list RIGHT_CURLY_BRACKET SEMICOLON
                    | class_head LEFT_CURLY_BRACKET RIGHT_CURLY_BRACKET SEMICOLON
    """
    p[0] = ["class_specifier"] + p[1:]


def p_member_list(p):
    """
    member_list : member_access_list
                | access_list
                | member_list access_list
    """
    p[0] = ["member_list"] + p[1:]


def p_member_declarator(p):
    """
    member_declarator : init_declarator
    """
    p[0] = ["member_declarator"] + p[1:]


def p_member_declarator_list(p):
    """
    member_declarator_list : member_declarator
                           | member_declarator_list COMMA member_declarator
    """
    p[0] = ["member_declarator_list"] + p[1:]


def p_member_declaration(p):
    """
    member_declaration : type_specifier member_declarator_list SEMICOLON
                       | member_declarator_list SEMICOLON
                       | type_specifier SEMICOLON
                       | SEMICOLON
                       | function_definition
                       | class_specifier
    """
    p[0] = ["member_declaration"] + p[1:]


def p_access_list(p):
    """
    access_list : access_specifier COLON member_access_list
                | access_specifier COLON
    """
    p[0] = ["access_list"] + p[1:]


def p_member_access_list(p):
    """
    member_access_list : member_declaration member_access_list
                       | member_declaration
    """
    p[0] = ["member_access_list"] + p[1:]


def p_base_clause(p):
    """
    base_clause : COLON base_specifier_list
    """
    p[0] = ["base_clause"] + p[1:]


def p_base_specifier_list(p):
    """
    base_specifier_list : base_specifier
              | base_specifier_list COMMA base_specifier
    """
    p[0] = ["base_specifier_list"] + p[1:]


def p_base_specifier(p):
    """
    base_specifier : CLASS IDENTIFIER
                   | access_specifier CLASS IDENTIFIER
                   | IDENTIFIER
                   | access_specifier IDENTIFIER
    """
    p[0] = ["base_specifier"] + p[1:]


def p_access_specifier(p):
    """
    access_specifier : PRIVATE
                     | PUBLIC
    """
    p[0] = ["access_specifier"] + p[1:]


def p_abstract_declarator(p):
    """abstract_declarator : pointer
    | direct_abstract_declarator
    | pointer direct_abstract_declarator
    """
    p[0] = ["abstract_declarator"] + p[1:]


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
    p[0] = ["direct_abstract_declarator"] + p[1:]


def p_initializer(p):
    """
    initializer : LEFT_CURLY_BRACKET initializer_list RIGHT_CURLY_BRACKET
                | assignment_expression
    """
    p[0] = ["initializer"] + p[1:]


def p_initializer_list(p):
    """
    initializer_list : initializer_list COMMA initializer
                     | initializer
    """
    p[0] = ["initializer_list"] + p[1:]


def p_statement(p):
    """
    statement : compound_statement
              | expression_statement
              | selection_statement
              | iteration_statement
              | jump_statement
              | labeled_statement
    """
    p[0] = ["statement"] + p[1:]


def p_labeled_statement(p):
    """
    labeled_statement : IDENTIFIER COLON statement
    """
    p[0] = ["labeled_statement"] + p[1:]


def p_compound_statement(p):
    """
    compound_statement : LEFT_CURLY_BRACKET declaration_list statement_list RIGHT_CURLY_BRACKET
                       | LEFT_CURLY_BRACKET declaration_list RIGHT_CURLY_BRACKET
                       | LEFT_CURLY_BRACKET statement_list RIGHT_CURLY_BRACKET
                       | LEFT_CURLY_BRACKET RIGHT_CURLY_BRACKET
    """
    p[0] = ["compound_statement"] + p[1:]


def p_declaration_list(p):
    """
    declaration_list : declaration_list declaration
                     | declaration
    """
    p[0] = ["declaration_list"] + p[1:]


def p_statement_list(p):
    """
    statement_list : statement
                   | statement_list statement
    """
    p[0] = ["statement_list"] + p[1:]


def p_expression_statement(p):
    """
    expression_statement : expression SEMICOLON
                         | SEMICOLON
    """
    p[0] = ["expression_statement"] + p[1:]


def p_selection_statement(p):
    """
    selection_statement : IF LEFT_PARENTHESIS expression RIGHT_PARENTHESIS statement %prec IF
                        | IF LEFT_PARENTHESIS expression RIGHT_PARENTHESIS statement ELSE statement
    """
    p[0] = ["selection_statement"] + p[1:]


def p_iteration_statement(p):
    """
    iteration_statement : WHILE LEFT_PARENTHESIS expression RIGHT_PARENTHESIS statement
                        | FOR LEFT_PARENTHESIS expression_statement expression_statement expression RIGHT_PARENTHESIS statement
                        | FOR LEFT_PARENTHESIS type_specifier expression_statement expression_statement expression RIGHT_PARENTHESIS statement
                        | FOR LEFT_PARENTHESIS expression_statement expression_statement RIGHT_PARENTHESIS statement
                        | FOR LEFT_PARENTHESIS type_specifier expression_statement expression_statement RIGHT_PARENTHESIS statement
    """
    p[0] = ["iteration_statement"] + p[1:]


def p_jump_statement(p):
    """
    jump_statement : GOTO IDENTIFIER SEMICOLON
                   | BREAK SEMICOLON
                   | CONTINUE SEMICOLON
                   | RETURN SEMICOLON
                   | RETURN expression SEMICOLON
    """
    p[0] = ["jump_statement"] + p[1:]


def p_translation_unit(p):
    """
    translation_unit : translation_unit external_declaration
                     | external_declaration
    """
    p[0] = ["translation_unit"] + p[1:]


def p_external_declaration(p):
    """
    external_declaration : function_definition
                         | declaration
    """
    p[0] = ["external_declaration"] + p[1:]


def p_function_definition(p):
    """
    function_definition : type_specifier declarator declaration_list compound_statement
                        | type_specifier declarator compound_statement
                        | declarator declaration_list compound_statement
                        | declarator compound_statement
    """
    p[0] = ["function_definition"] + p[1:]