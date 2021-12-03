"""
Tree-building parser for Kroc programming language. Returns
a complete parse tree. No attempt to optimize tree.

Kieran Herley, June 2020.
"""

from kroc_scanner import *
from pt_node import *
import sys

import pickle


class KrocParser:
    
    def __init__(self, sourcepath):
        self.__scanner = KrocScanner(sourcepath, verbose = True)
   
    def parse_program(self):
        """ Parse tokens matching following production:
        <program> -> <statement_list>
        """
        self.__scanner.log("Parsing <program> -> <statement_list>")
        c = self.parse_statement_list()
        return PTNode("program", [c])

    def parse_statement_list(self):     
        """ Parse tokens matching following production:
        <statement_list> -> {<statement>}
        """
        self.__scanner.log("Parsing <statement_list> -> {<statement>}")
        
        c = self.parse_statement()
        children = [c]
        while self.__scanner.current.kind in {"ID", "READ", "WRITE", "WHILE", 
                                    "IF"}:
            children.append(self.parse_statement())
            
        return PTNode("statement_list", children)
    
    def parse_statement(self):     
        """ Parse tokens matching following production:
                <statement> -> 
                    <simple_stmt>  | <compound_stmt>
                    | <selection_stmt>|  <iteration_stmt>
        """
    
        self.__scanner.log("Parsing <statement> ->" 
                    "<simple_stmt>  | <compound_stmt>"
                    "| <selection_stmt>|  <iteration_stmt>")
        

        if self.__scanner.current.kind in {"ID", "READ", "WRITE"}:
            c = self.parse_simple_stmt()
        elif self.__scanner.current.kind == "WHILE":
            c = self.parse_iteration_stmt()
        elif self.__scanner.current.kind == "IF":
            c = self.parse_selection_stmt()
        else:
            c = self.parse_compound_stmt()
        return PTNode("statement", [c])
    
    
    def parse_compound_stmt(self):     
        """ Parse tokens matching following production:
                <compound_stmt> -> CLPAREN <statement_list> CRPAREN
        """
        self.__scanner.log(
            "Parsing <compound_stmt> -> CLPAREN <statement_list> CRPAREN")
        self.__scanner.match("CLPAREN")
        c = self.parse_statement_list()
        self.__scanner.match("CRPAREN")
        return PTNode("compound_stmt", [c])
        
    def parse_simple_stmt(self):     
        """ Parse tokens matching following production:
                <simple_stmt> -> 
                    <assign_stmt> SEMI | <read_stmt> SEMI 
                    | <write_stmt> SEMI| SEMI
        """
        self.__scanner.log("Parsing <simple_stmt> ->" 
                    "<assign_stmt> SEMI | <read_stmt> SEMI" 
                    "| <write_stmt> SEMI| SEMI")
        
        if self.__scanner.current.kind == "ID":
            c = self.parse_assign_stmt()
        elif self.__scanner.current.kind == "READ":
            c= self.parse_read_stmt()
        elif self.__scanner.current.kind == "WRITE":
            c= self.parse_write_stmt()
        self.__scanner.match("SEMI")
        return PTNode("simple_stmt", [c])
    
    def parse_selection_stmt(self):     
        """ Parse tokens matching following production:
                <selection_stmt> -> 
                    IF LPAREN <condition> RPAREN <statement> 
                    |  IF LPAREN <simple_expression> RPAREN 
                            ELSE <statement>
        """
        self.__scanner.log("Parsing <selection_stmt> ->" 
                    "IF LPAREN <condition> RPAREN <statement> "
                    "|  IF LPAREN <simple_expression> RPAREN "
                    "      ELSE <statement>")
        
        self.__scanner.match("IF")
        self.__scanner.match("LPAREN")
        c = self.parse_condition()
        self.__scanner.match("RPAREN")
        s1 = self.parse_statement()
        children = [c, s1] 
        if self.__scanner.current.kind == "ELSE":
            self.__scanner.match("ELSE")
            s2 = self.parse_statement()
            children.append(s2)
        return PTNode("selection_stmt", children)    
    
    
    def parse_iteration_stmt(self):     
        """ Parse tokens matching following production:
                <iteration_stmt> -> 
                    WHILE LPAREN <condition> RPAREN <statement>
        """
        self.__scanner.log("Parsing <iteration_stmt> ->" 
                    " WHILE LPAREN <condition> RPAREN <statement>")
        self.__scanner.match("WHILE")
        self.__scanner.match("LPAREN")
        c = self.parse_condition()
        self.__scanner.match("RPAREN")
        s = self.parse_statement()
        return PTNode("iteration_stmt", [c, s]) 

    def parse_read_stmt(self):     
        """ Parse tokens matching following production:
                <read_stmt>  -> READ ID
        """
        self.__scanner.log("Parsing <read_stmt>  -> READ ID")
        self.__scanner.match("READ")
        varname = self.__scanner.current.value
        self.__scanner.match("ID")
        return PTNode("read_stmt", [], value = varname) 
        

    def parse_write_stmt(self):     
        """ Parse tokens matching following production:
                <write_stmt>  -> WRITE <exp>
        """
        self.__scanner.log("Parsing <write_stmt>  -> WRITE <exp>")
        self.__scanner.match("WRITE")
        e = self.parse_expression()
        return PTNode("write_stmt", [e]) 

    def parse_assign_stmt(self):     
        """ Parse tokens matching following production:
                <assign_stmt> ->  ID ASSIGN <expression>
        """
        self.__scanner.log("Parsing <assign_stmt> ->  ID ASSIGN <expression>")
        identifier = self.__scanner.match("ID")
        self.__scanner.match("ASSIGN")
        e = self.parse_expression()
        return PTNode("assign_stmt", [e], value = identifier) 

    def parse_condition(self):     
        """ Parse tokens matching following production:
                <condition> -> <expression> <relop> <expression> 
                    | <expression>
        """
        self.__scanner.log(
            "Parsing <condition> -> <expression> <relop> <expression>" 
                    "| <expression>")
        
        children = [self.parse_expression()]
        if self.__scanner.current.kind in {"EQ", 
                "NOTEQ", "LT", "LTE", "GT", "GTE"}:
            r = self.parse_relop()
            children.append(r)
            self.__scanner.advance()
            e = self.parse_expression()
            children.append(e)
        return PTNode("condition", children)     
    

    def parse_relop(self):     
        """ Parse tokens matching following production:
                <relop> -> LTE | LT | GT | GTE| EQ | NOTEQ
        """
        self.__scanner.log(
            "Parsing <relop> -> LTE | LT | GT | GTE| EQ | NOTEQ")
        return PTNode("relop", [], value = self.__scanner.current.value)

    def parse_expression(self):     
        """ Parse tokens matching following production:
                <expression> -> <term> {<addop> <term>}
        """
        self.__scanner.log("Parsing <expression> -> <term> {<addop> <term>}")
        
        t = self.parse_term()
        children = [t]
        while self.__scanner.current.kind in {"PLUS", "MINUS"}:
            a = self.parse_addop()
            children.append(a)
            t = self.parse_term()
            children.append(t)
        return PTNode("expression", children)        

    def parse_addop(self):     
        """ Parse tokens matching following production:
                <addop> ->   PLUS | MINUS
        """
        self.__scanner.log("Parsing <addop> ->   PLUS | MINUS")
        r = PTNode("addop",  [], value = self.__scanner.current.value)
        
        if self.__scanner.current.kind in {"PLUS", "MINUS"}:
            self.__scanner.advance()
        return r

    def parse_term(self):     
        """ Parse tokens matching following production:
                <term> -> <factor> {<mulop> <factor>}
        """
        self.__scanner.log("Parsing <term> -> <factor> {<mulop> <factor>}")
    
        f = self.parse_factor()
        children = [f]
        while self.__scanner.current.kind in {"TIMES", "OVER"}:
            m = self.parse_mulop()
            children.append(m)
            f = self.parse_factor()
            children.append(f)
        return PTNode("term", children) 

    def parse_mulop(self):     
        """ Parse tokens matching following production:
                <mulop> -> TIMES| OVER
        """
        self.__scanner.log("Parsing <mulop> -> TIMES| OVER")
        r = PTNode("mulop",  [], value = self.__scanner.current.value)
        if self.__scanner.current.kind in {"TIMES", "OVER"}:
            self.__scanner.advance()
        return r

    def parse_factor(self):     
        """ Parse tokens matching following production:
                <factor> -> LPAREN <expression> RPAREN | ID | NUM
        """
        self.__scanner.log(
            "Parsing <factor> -> LPAREN <expression> RPAREN | ID | INT")
    
        if self.__scanner.current.kind == "LPAREN":
            self.__scanner.match("LPAREN")
            c = self.parse_expression()
            self.__scanner.match("RPAREN")
            return PTNode("factor", [c])
        elif self.__scanner.current.kind in {"ID", "INT"}:
            val = self.__scanner.current.value
            self.__scanner.advance()
            return PTNode("factor", [], val)
        else:
            self.__scanner.shriek("I'm lost . . .")
            
if __name__ == "__main__":

    fpath = "dangle.krc"
  
    parser = KrocParser(fpath)
    ptroot = parser.parse_program()

    print("Parse tree:")
    print("-" * 25)
    ptroot.dump()
    print("=" * 25)
    print()
    
   



   
   
             
