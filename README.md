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


## Milestone 4 (semantics)

There are 5 testcases in  `~/tests/semantic`. To run test `n`, run the following command in the main (`~/`) directory: 

```console
make semantic_n
```
(`n = 1,2,...,5`)

symboltable.csv will get created and get saved in main (`~/`) directory.

## Milestone 6 (Final Destination)

There are 16 testcases in  `~/tests/`. To run test `n`, run the following command in the main (`~/`) directory: 

```console
./compile.sh n
```
(`n = 1,2,...,16`)

mips.s will get created and saved in bin (`~/bin/`) directory in case of no error in compilation.
