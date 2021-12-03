# Tiny-to-TAC-Compiler

tiny_Parser.py: This file can be used to generated a parse tree in the form of a pickle file 
that is suitible for the tiny-to-tac compiler. Change the variable "fpath" in the __init__ 
function to the appropriate .tny file of your choice.

tiny_to_tac_compiler: This file can be used to generate a .tac file from the parse tree of 
a .tny file. This parse tree should be the output of tiny_Parser.py or in the style of the 
example .pkl files given. The .tac file will output to the same directory that 
tiny_to_tac_compiler.py is run from.
