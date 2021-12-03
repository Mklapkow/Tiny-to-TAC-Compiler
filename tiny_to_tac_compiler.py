"""
Tree-walking compiler for the Tiny programming language. 
Generates three-address code. Performs no error checking.

Myles Klapkowski, December 2021

"""

from tiny_parser import *
from pt_node import *
import sys

import pickle

class TinyCompiler:

    """
    Uncomment code and comment out equivalent to use pre-parsed pickle file.
    """
    # def __init__(self):

    def __init__(self, sourcepath):#Comment out when using pickle file
        """Create a compiler object for Tiny program with source at
        'sourcepath'.
        """
        self.parse_tree = TinyParser(sourcepath).parse_program() #Comment out when using pickle file

        # with (open("factorial_pt_kh.pkl", "rb")) as openfile: #Uncomment when using pickle file
        #     while True:
        #         try:
        #             self.parse_tree = pickle.load(openfile)
        #         except EOFError:
        #             break
        
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

    def __codegen_selection(self, root):
        """ Generate TAC for if statement represented by subtree 
       'root'.
        """
        skiptrue_label = self.__new_label()
        conditvar = self.__codegen_expression(root.children[0])
        print("if (%s) goto %s" % (conditvar, skiptrue_label))
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
        op = "="
        for c in root.children:
            if c.label == 'simple_expr':
                sevar = self.__codegen_simple_expr(c)   
                if len(root.children) > 2 and c == root.children[2] and root.children[1].label == 'comp_op':
                    print("%s := %s %s %s;" % (total_var, total_var, op, sevar))
                else:
                    print("%s := %s;" % (total_var, sevar))
            else:
                op = c.children[0].value
        return total_var

    def __codegen_simple_expr(self, root):
        """ Generate TAC for simple expression represented by subtree 'root'.
        """
        total_var = self.__new_var()
        print("%s := 0;" % total_var)
        op = "+"
        for c in root.children:
            if c.label == 'term':
                tvar = self.__codegen_term(c)
                if len(root.children) > 2 and c == root.children[2] and root.children[1].label == 'addop':
                    print("%s := %s %s %s;" % (total_var, total_var, op, tvar))
                else:
                    print("%s := %s;" % (total_var, tvar))
            else:
                op = c.children[0].value

        return total_var

    def __codegen_term(self, root):
        """ Generate TAC for subexpression represented by subtree 'root'.
        """
        total_var = self.__new_var()
        print("%s := 0;" % total_var)
        op = "*"
        for c in root.children:
            if c.label == 'factor':
                fvar = self.__codegen_factor(c)
                if len(root.children) > 2 and c == root.children[2] and root.children[1].label == 'mulop':
                    print("%s := %s %s %s;" % (total_var, total_var, op, fvar))
                # else:
                    print("%s := %s;" % (total_var, fvar))
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
        if len(root.children) >= 1 and root.children[0].label == 'leaf':
            varname = root.children[0].value
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
        if len(root.children) >= 1 and root.children[0].label == 'leaf':
            destvar = root.children[0].value
            rhsvar = self.__codegen_expression(root.children[1])
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
        self.__codegen_statement_seq(root.children[0])
        conditvar = self.__codegen_expression(root.children[1])
        print("if (%s) goto %s" % (conditvar, bottom_label))

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

    fpath = "fact.tny" #Change this to compile a different file. Comment out when using pickle file
    compiler = TinyCompiler(fpath) #Comment out when using pickle file

    # compiler = TinyCompiler() #Uncomment when using pickle file

    print("Compiler output:")
    print("-" * 25)
    compiler.translate()
    print("=" * 25)
    print()

