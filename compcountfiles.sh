#!/bin/bash

# Compile the c/countfiles program
gcc -c c/countfiles.c -o c/countfiles.o
gcc -c parser/argparser.c -o parser/argparser.o
gcc -o c/countfiles c/countfiles.o parser/argparser.o
