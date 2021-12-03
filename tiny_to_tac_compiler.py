"""
Tree-walking compiler for the Tiny programming language. 
Generates three-address code. Performs no error checking. No attempt to optimize output code.

Myles Klapkowski, December 2021

Code throughout and example by Kieran Herley, June 2020
"""

from tiny_parser import *
from pt_node import *
import sys

import pickle

class TinyCompiler:

    """
    Uncomment code and comment out equivalent to use pre-parsed pickle file.
    """

    def __init__(self, filename):
        """Create a compiler object for Tiny program with source at
        'sourcepath'.
        """
        with (open(filename, "rb")) as openfile:
            while True:
                try:
                    self.parse_tree = pickle.load(openfile)
                except EOFError:
                    break

        self.__varcount = 0
        self.__labcount = 0
        self.outfilename = filename[:len(filename)-3] + "tac"
    
    def translate(self):
        """ Generate three-address code for the Tiny program represented
        by the parse-tree name 'parse_tree'. Output appears in standard
        output. 
        """
        
        self.outfile = open(self.outfilename, "w")
        self.__varcount, self.__labcount = 0, 0
        self.__codegen(self.parse_tree)
        self.outfile.write("halt;")

    def __codegen_selection(self, root):
        """ Generate TAC for if statement represented by subtree 
       'root'.
        """
        skiptrue_label = self.__new_label()
        conditvar = self.__codegen_expression(root.children[0])
        self.outfile.write("if (%s) goto %s\n" % (conditvar, skiptrue_label))
        self.__codegen(root.children[1])
        
        if len(root.children) <= 2:
            self.outfile.write("%s:\n" % skiptrue_label)
        else:
            skipfalse_label = self.__new_label()
            self.outfile.write("goto %s;\n" % skipfalse_label)
            self.outfile.write("%s:\n" % skiptrue_label)
            self.__codegen(root.children[2])
            self.outfile.write("%s:\n" % skipfalse_label)

    def __codegen_expression(self, root):
        """ Generate TAC for expression represented by subtree 'root'.
        """
        total_var = self.__new_var()
        self.outfile.write("%s := 0;\n" % total_var)
        op = "="
        for c in root.children:
            if c.label == 'simple_expr':
                sevar = self.__codegen_simple_expr(c)   
                if len(root.children) > 2 and c == root.children[2] and root.children[1].label == 'comp_op':
                    self.outfile.write("%s := %s %s %s;\n" % (total_var, total_var, op, sevar))
                else:
                    self.outfile.write("%s := %s;\n" % (total_var, sevar))
            else:
                op = c.children[0].value
        return total_var

    def __codegen_simple_expr(self, root):
        """ Generate TAC for simple expression represented by subtree 'root'.
        """
        total_var = self.__new_var()
        self.outfile.write("%s := 0;\n" % total_var)
        op = "+"
        for c in root.children:
            if c.label == 'term':
                tvar = self.__codegen_term(c)
                if len(root.children) > 2 and c == root.children[2] and root.children[1].label == 'addop':
                    self.outfile.write("%s := %s %s %s;\n" % (total_var, total_var, op, tvar))
                else:
                    self.outfile.write("%s := %s;\n" % (total_var, tvar))
            else:
                op = c.children[0].value

        return total_var

    def __codegen_term(self, root):
        """ Generate TAC for subexpression represented by subtree 'root'.
        """
        total_var = self.__new_var()
        self.outfile.write("%s := 0;\n" % total_var)
        op = "*"
        for c in root.children:
            if c.label == 'factor':
                fvar = self.__codegen_factor(c)
                if len(root.children) > 2 and c == root.children[2] and root.children[1].label == 'mulop':
                    self.outfile.write("%s := %s %s %s;\n" % (total_var, total_var, op, fvar))
                else:
                    self.outfile.write("%s := %s;\n" % (total_var, fvar))
            else:
                op = c.children[0].value
        return total_var

    def __codegen_factor(self, root):
        """ Generate TAC for subexpression represented by subtree 'root'.
        """
        for c in root.children:
            if c.label == 'leaf':
                fval = c.value
                if type(fval) == int:
                    var = self.__new_var()
                    self.outfile.write("%s := %d;\n" % (var, fval))
                    return var
                elif type(fval) == str:
                    var = self.__new_var()
                    self.outfile.write("%s := %s;\n" % (var, fval))
                    return var
            else:
                exprvar = self.__codegen_expression(root.children[0])
                return exprvar

    def __codegen_read(self, root):
        """ Generate TAC for read statement represented by subtree 'root'.
        """
        if len(root.children) >= 1 and root.children[0].label == 'leaf':
            varname = root.children[0].value
            self.outfile.write("%s := in;\n" % varname)

    def __codegen_write(self, root):
        """ Generate TAC for write statement represented by subtree 
        'root'.
        """
        exprvar = self.__codegen_expression(root.children[0])
        self.outfile.write("out := %s;\n" % exprvar)
    
    def __codegen_assign(self, root):
        """ Generate TAC for assignment statement represented by subtree 
        'root'.
        """
        if len(root.children) >= 1 and root.children[0].label == 'leaf':
            destvar = root.children[0].value
            rhsvar = self.__codegen_expression(root.children[1])
            self.outfile.write("%s := %s;\n" % (destvar, rhsvar))

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

        self.outfile.write("%s:\n" % top_label)
        self.__codegen_statement_seq(root.children[0])
        conditvar = self.__codegen_expression(root.children[1])
        self.outfile.write("if (%s) goto %s\n" % (conditvar, bottom_label))

        self.outfile.write("goto %s\n" % top_label)
        self.outfile.write("%s:\n" % bottom_label)

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

    filename = "fact_pt_kh.pkl"
    compiler = TinyCompiler(filename) 
    compiler.translate()
   