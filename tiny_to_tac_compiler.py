"""
Tree-walking compiler for the Tiny programming language. 
Generates three-address code. Performs no error checking.

Myles Klapkowski, December 2021

To Do:
1) build out compiler infastructure based on kroc compiler
2) add tiny components and test code

"""

from tiny_parser import *
from pt_node import *
import sys

import pickle

class TinyCompiler:

    # def __init__(self, sourcepath):
    def __init__(self):
        """Create a compiler object for Tiny program with source at
        'sourcepath'.
        """
        
        with (open("readwrite_pt_kh.pkl", "rb")) as openfile:
            while True:
                try:
                    self.parse_tree = pickle.load(openfile)
                except EOFError:
                    break
        self.__varcount = 0
        self.__labcount = 0
    
    def translate(self):
        """ Generate three-address code for the Tiny program represented
        by the parse-tree name 'parse_tree'. Output appears in standard
        output. 
        """
        self.__varcount, self.__labcount = 0, 0
        self.__codegen(self.parse_tree)
        print("halt;")

    def __codegen_if(self, root):
        """ Generate TAC for if statement represented by subtree 'root'.
        """
        conditvar = self.__new_var()
        e1var = self.__codegen_expression(root.children[0])

        if len(root.children) == 1:
            print("%s := %s;" % (conditvar, e1var))
        else:
            relop = root.children[1].value
            e2var = self.__codegen_expression(root.children[2])
            print("%s := %s %s %s;" % (conditvar, e1var, relop, e2var))

        return conditvar

    def __codegen_selection(self, root):
        """ Generate TAC for if statement represented by subtree 
       'root'.
        """
        skiptrue_label = self.__new_label()
        conditvar = self.__codegen_condition(root.children[0])
        print("if (%s == 0) goto %s" % (conditvar, skiptrue_label))
        self.__codegen(root.children[1])
        
        if len(root.children) <= 2:
            print("%s:" % skiptrue_label)
        else:
            skipfalse_label = self.__new_label()
            print("goto %s;" % skipfalse_label)
            print("%s:" % skiptrue_label)
            self.__codegen(root.children[2])
            print("%s:" % skipfalse_label)

    def __codegen_expression(self, root):
        """ Generate TAC for expression represented by subtree 'root'.
        """
        total_var = self.__new_var()
        print("%s := 0;" % total_var)
        op = "+"
        for c in root.children:
            if c.label == "term":
                tvar = self.__codegen_term(c)
                print()
                print("%s := %s %s %s;" % (total_var, total_var, op, tvar))
            else:
                op = c.value
        return total_var

    def __codegen_term(self, root):
        """ Generate TAC for subexpression represented by subtree 'root'.
        """
        total_var = self.__new_var()
        print("%s := 1;" % total_var)
        op = "*"
        for c in root.children:
            if c.label == "factor":
                fvar = self.__codegen_factor(c)
                print("%s := %s %s %s;" % (total_var, total_var, op, fvar))
            else:
                op = c.value
        return total_var

    def __codegen_factor(self, root):
        """ Generate TAC for subexpression represented by subtree 'root'.
        """
        fval = root.value
        if type(fval) == int:
            var = self.__new_var()
            print("%s := %d;" % (var, fval))
            return var
        elif type(fval) == str:
            var = self.__new_var()
            print("%s := %s;" % (var, fval))
            return var
        else:
            exprvar = self.__codegen_expression(root.children[0])
            return exprvar

    def __codegen_read(self, root):
        """ Generate TAC for read statement represented by subtree 'root'.
        """
        varname = root.value
        print("%s := in;" % varname)

    def __codegen_write(self, root):
        """ Generate TAC for write statement represented by subtree 
        'root'.
        """
        exprvar = self.__codegen_expression(root.children[0])
        print("out := %s;" % exprvar)
    
    def __codegen_assign(self, root):
        """ Generate TAC for assignment statement represented by subtree 
        'root'.
        """
        destvar = root.value
        rhsvar = self.__codegen_expression(root.children[0])
        print("%s := %s;" % (destvar, rhsvar))

    def __new_var(self):
        """ Generate and return fresh temporray variable name.
        """
        self.__varcount += 1
        return "t%d" % self.__varcount

    def __new_label(self):
        """ Generate and return fresh label name.
        """
        self.__labcount += 1
        return "l%d" % self.__labcount

    def __codegen_repeat(self, root):
        """ Generate TAC for a repeat statement represented by subtree 
        'root'.
        """
        top_label = self.__new_label()
        bottom_label = self.__new_label()

        print("%s:" % top_label)
        conditvar = self.__codegen_if(root.children[0])
        print("if (%s == 0) goto %s" % (conditvar, bottom_label))

        self.__codegen(root.children[1])
        print("goto %s" % top_label)
        print("%s:" % bottom_label)

    def __codegen_statement_seq(self, root):
        """ Generate TAC for statement sequence represented by subtree 
        'root'.
        """
        for c in root.children:
            self.__codegen(c)

    def __codegen(self, root):
        """ Generate TAC for onstruct represented by subtree 
        'root'.
        """
        label = root.label
        children = root.children
        value = root.value

        actions = {
        "ifstmt" : self.__codegen_selection,
        "readstmt" : self.__codegen_read,
        "writestmt" : self.__codegen_write,
        "assignstmt" : self.__codegen_assign,
        "repeatstmt" : self.__codegen_repeat,
        "stmtseq" : self.__codegen_statement_seq
        }
        if label in actions:
            actions[label](root)
        else:
            self.__codegen(children[0])

if __name__ == "__main__":

    # fpath = "primes.krc" #REMEBER TO CHANGE THIS
    # compiler = TinyCompiler(fpath)
    compiler = TinyCompiler()
    print("Compiler output:")
    print("-" * 25)
    compiler.translate()
    print("=" * 25)
    print()

