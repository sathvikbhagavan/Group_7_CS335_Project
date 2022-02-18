## Course Project for Group 7, Compiler Design (Spring 2022)

## Milestone 1  
Project specifications can be found in `~/docs/specs.pdf`. 

## Milestone 2 (lexer)

There are 6 testcases in  `~/tests/`. To run test `n`, run the following command in the main (`~/`) directory: 

```console
make lex_n
```
(`n = 1,2,...,6`)

Table with tokens, lexemes, line# and column# will be displayed.

## Milestone 3 (parser)

There are 6 testcases in  `~/tests/`. To run test `n`, run the following command in the main (`~/`) directory: 

```console
make parse_n
```
(`n = 1,2,...,6`)

The AST output (in string format) will be displayed on the terminal. The `~/parser.out` file contains all parser rules.

The the DOT file for generating automaton is at `~/utils/graph.dot`, and the automaton graph is at `~/docs/automaton.pdf`.
