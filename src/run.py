from lexer.lexer import *
from ply.lex import lex
import argparse
import fileinput
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument('-n', '--num', type=int, required=True, help='test case number')
ap.add_argument('-s', '--save', required=False, help='save the output to csv file')

args = vars(ap.parse_args())

class Lexer:
    def __init__(self, file):
        self.file = file
        self.string = ''
        with open(file, 'r') as f:
            self.string = f.read()
        self.lexer = lex()
        self.tokens = []

    def find_column(self, token):
        line_start = self.string.rfind('\n', 0, token.lexpos) + 1
        return (token.lexpos - line_start) + 1
    
    def run(self):
        self.lexer.input(self.string)
        for token in self.lexer:
            self.tokens.append(token)


    def print_tokens(self):
        print('Token' + 20*' ' + 'Lexeme' + 19*' ' + 'Line#' + 20*' ' + 'Column#' )
        for i in range(len(self.tokens)):
            self.tokens[i].lexpos = self.find_column(self.tokens[i])
            print(f'{self.tokens[i].type}' + (25-len(f'{self.tokens[i].type}'))*' ' + \
                f'{self.tokens[i].value}'+ (25-len(f'{self.tokens[i].value}'))*' ' + \
                f'{self.tokens[i].lineno}' + (25-len(f'{self.tokens[i].lineno}'))*' ' + \
                f'{self.tokens[i].lexpos}')

    
    def print_to_csv(self):
        
        tokens_ = []
        for token in self.tokens:
            tokens_.append([token.type,token.value, token.lineno, token.lexpos+1])
        
        df = pd.DataFrame(data=tokens_, index=None, columns=None)
        df.to_csv(f"outputs/output_test_{args['num']}.csv", header=False)
        

lexer = Lexer(f"tests/lexer/test_{args['num']}.cpp")
lexer.run()
lexer.print_tokens()
if args['save']:
    lexer.print_to_csv()