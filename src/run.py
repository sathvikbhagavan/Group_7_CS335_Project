from lexer import *
from parser import *
from ply.lex import lex
from ply.yacc import yacc, NullLogger
import argparse
import fileinput
import pandas as pd
import pydot

ap = argparse.ArgumentParser()
ap.add_argument('-n', '--num', type=int, required=True, help='test case number')
ap.add_argument('-s', '--save', required=False, help='save the output to csv file')
ap.add_argument('-m', '--mode', type=str, help='lexer or parser', default='parse')

args = vars(ap.parse_args())

class Parser:
    def __init__(self, file):
        self.file = file
        self.string = ''
        with open(file, 'r') as f:
            self.string = f.read()
        self.lexer = lex()
        self.parser = yacc(debug=1, errorlog=NullLogger())
        self.tokens = []

    def find_column(self, token):
        line_start = self.string.rfind('\n', 0, token.lexpos) + 1
        return (token.lexpos - line_start) + 1

    def run_lex(self):
        self.lexer.input(self.string)
        for token in self.lexer:
            self.tokens.append(token)
    
    def run_parse(self):
        self.ast = self.parser.parse(self.string)

    def print_tokens(self):
        print('Token' + 20*' ' + 'Lexeme' + 19*' ' + 'Line#' + 20*' ' + 'Column#' )
        for i in range(len(self.tokens)):
            self.tokens[i].lexpos = self.find_column(self.tokens[i])
            print(f'{self.tokens[i].type}' + (25-len(f'{self.tokens[i].type}'))*' ' + \
                f'{self.tokens[i].value}'+ (25-len(f'{self.tokens[i].value}'))*' ' + \
                f'{self.tokens[i].lineno}' + (25-len(f'{self.tokens[i].lineno}'))*' ' + \
                f'{self.tokens[i].lexpos}')
    
    def print_ast(self):
        print('AST is: ')
        print(self.ast)

    
    def print_to_csv(self):
        
        tokens_ = []
        for token in self.tokens:
            tokens_.append([token.type,token.value, token.lineno, token.lexpos+1])
        
        df = pd.DataFrame(data=tokens_, index=None, columns=None)
        df.to_csv(f"outputs/output_test_{args['num']}.csv", header=False)
        

driver = Parser(f"tests/test_{args['num']}.cpp")

if args['mode'] == 'parse':
    driver.run_parse()
    driver.print_ast()

elif args['mode'] == 'lex':
    driver.run_lex()
    driver.print_tokens()