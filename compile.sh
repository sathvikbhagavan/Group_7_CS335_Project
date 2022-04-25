#!/bin/bash

python3 src/preprocessing.py -n $1

python3 src/semantic.py -n $1

if [ $? -eq 2 ]
then
    echo "Compilation failed"
else
    python3 src/mips_gen.py
fi

rm "tests/test_$1_processed.cpp"