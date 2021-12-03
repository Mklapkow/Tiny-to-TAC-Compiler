"""
Tree-Building Parser for Tiny programming language.
Returns the root of the parse tree. No attempt to optimize tree.

Myles Klapkowski, November 2021
"""

from tiny_scanner import *
from pt_node import *
import sys

import pickle

class TinyParser:

    def __init__(self, sourcepath):
        self.__scanner = TinyScanner(sourcepath, verbose = True)

    def parse_program(self):
        """Parse tokens matching the following production:
        <program> -> <stmtseq>
        """
        self.__scanner.log("Parsing <program> -> <stmtseq>")
        c = self.parse_stmtseq()
        return PTNode("program", [c])
        
    def parse_stmtseq(self):
        """Parse tokens matching the following production:
        <stmtseq> -> <statement>
        """

        self.__scanner.log("Parsing <stmtseq> -> <statement>")

        c = self.parse_statement()
        children = [c]

        while self.__scanner.current.kind in {"ID", "READ", "WRITE", 
        "IF", "REPEAT", "UNTIL"}:
            children.append(self.parse_statement())

        return PTNode("stmtseq", children)
    
    def parse_statement(self):
        """ Parse tokens matching following production:
            <statement> -> 
                <ifstmt>
                |  <repeatstmt>
                |  <assignstmt>
                |  <readstmt>
                |  <writestmt>
        """

        self.__scanner.log("Parsing <statement>"
                        "<ifstmt>  |  <repeatstmt>"
                        "|  <assignstmt> |  <readstmt>" 
                        "|  <writestmt>")
        
        if self.__scanner.current.kind == "ID":
            c = self.parse_assignstmt
        elif self.__scanner.current.kind == "IF":
            c = self.parse_ifstmt()
        elif self.__scanner.current.kind in {"REPEAT", "UNTIL"}:
            c = self.parse_repeatstmt()
        elif self.__scanner.current.kind == "READ":
            c = self.parse_readstmt()
        elif self.__scanner.current.kind == "WRITE":
            c = self.parse_writestmt()
        return PTNode("statement", [c])

    def parse_assignstmt(self):
        """Parse tokens matching following productions:
            <assignstmt> -> 
                ID <exp>
        """
        self.__scanner.log("Parsing <assignstmt> -> ID <exp>")
        id = self.__scanner.match("ID")
        e = self.parse_exp()
        return PTNode("assignstmt", [e], value = id)


    def parse_ifstmt(self):
        """Parse tokens matching following productions:
            <ifstmt> -> 
                IF <exp> THEN <stmtseq> END
                | IF <exp> THEN <stmtseq> ELSE <stmtseq> END
        """

        self.__scanner.log(
            "Parsing  <ifstmt> -> IF <exp> THEN <stmteq> END | IF <exp> THEN <stmtseq> ELSE <stmtseq> END"
        )
        self.__scanner.match("IF")
        c = self.parse_exp()
        self.__scanner.match("THEN")
        s = self.parse_stmtseq()
        if self.__scanner.current.kind == "END":
            self.__scanner.match("END")
            return PTNode("ifstmt", [c,s])
        elif self.__scanner.current.kind == "ELSE":
            self.__scanner.match("ELSE")
            e = self.parse_stmtseq()
            self.__scanner.match("END")
            return PTNode("ifstmt", [c,s,e])
        else:
            self.__scanner.shriek("Lost in the if statements.")
    
    def parse_repeatstmt(self):
        """Parse tokens matching following productions:
            <repeatstmt> -> REPEAT <stmtseq> UNTIL <exp>
        """

        self.__scanner.log(
            "Parsing <repeatstmt> -> REPEAT <stmtseq> UNTIL <exp>"
            )
        self.__scanner.match("REPEAT")
        s = self.parse_stmtseq()
        self.__scanner.match("UNTIL")
        e = self.parse_exp()

        return PTNode("repeatstmt", [s,e])


    def parse_readstmt(self):
        """Parse tokens matching following productions:
            <readstmt> -> READ ID
        """

        self.__scanner.log("Parsing <readstmt> -> READ ID")
        self.__scanner.match("READ")
        varname = self.__scanner.current.value
        self.__scanner.match("ID")
        return PTNode("readstmt", [], value = varname)

    def parse_writestmt(self):
        """Parse tokens matching following productions:
            <writestmt> -> WRITE <exp>
        """

        self.__scanner.log("Parsing <writestmt> -> WRITE <exp>")
        self.__scanner.match("WRITE")
        e = self.parse_exp()
        return PTNode("write_stmt", [e])

    def parse_exp(self):
        """Parse tokens matching following productions:
            <exp> -> 
                <simple-expr> <comp-op> <simple-expr>
                | <simple-expr>
        """
        self.__scanner.log("Parsing <exp> -> <simple-expr> <comp-op> <simple-expr> | <simple-expr>")
        s = self.parse_simple_expr()
        children = [s]
        while self.__scanner.current.kind in {"LT", "EQ", "GT"}:
            c = self.parse_comp_op()
            children.append(c)
            s = self.parse_simple_expr()
            children.append(s)
        return PTNode("exp", children)

    def parse_simple_expr(self):
        """Parse tokens matching following productions:
            <simple_expr> -> <simple-expr> <addop> <term> | <term>
        """

        self.__scanner.log("Parsing <simple_expr> -> <simple-expr> <addop> <term> | <term>")
        t = self.parse_term()
        children = [t]
        while self.__scanner.current.kind in {"PLUS", "MINUS"}:
            a = self.parse_addop()
            children.append(a)
            t = self.parse_term()
            children.append(t)
        return PTNode("simple-expr", children)    


    def parse_comp_op(self):
        """Parse tokens matching following productions:
            <comp-op> -> LT | EQ | GT
        """
        self.__scanner.log("Parsing <comp-op> -> LT | EQ")
        return PTNode("comp-op", [], value = self.__scanner.current.value)
    
    def parse_addop(self):
        """Parse tokens matching following productions:
            <addop> -> PLUS | MINUS
        """

        self.__scanner.log("Parsing <addop> -> PLUSE | MINUS")
        r = PTNode("addop", [], value=self.__scanner.current.value)

        if self.__scanner.current.kind in {"PLUS", "MINUS"}:
            self.__scanner.advance()
        return r
    
    def parse_term(self):
        """Parse tokens matching following productions:
            <term> -> <term> <mulop> <factor> | <factor>
        """

        self.__scanner.log("Parsing <term> -> <term> <mulop> <factor> | <factor>")
        f = self.parse_factor()
        children = [f]
        while self.__scanner.current.kind in {"TIMES", "OVER"}:
            m = self.parse_mulop()
            children.append(m)
            f = self.parse_factor()
            children.append(f)
        return PTNode("term", children)    
    
    def parse_mulop(self):
        """Parse tokens matching following productions:
            <mulop> -> TIMES | OVER
        """

        self.__scanner.log("Parsing <mulop> -> TIMES | OVER")
        r = PTNode("mulop", [], value = self.__scanner.current.value)
        if self.__scanner.current.kind in {"TIMES", "OVER"}:
            self.__scanner.advance()
        return r
    
    def parse_factor(self):
        """Parse tokens matching following productions:
            <factor> -> LPAREN <exp> RPAREN | INT | ID
        """

        self.__scanner.log(
            "Parsing <factor> -> LPAREN <exp> RPAREN | INT | ID"
        )

        if self.__scanner.current.kind == "LPAREN":
            self.__scanner.match("LPAREN")
            e = self.parse_exp()
            self.__scanner.match("RPAREN")
            return PTNode("factor", [e])
        elif self.__scanner.current.kind in {"ID", "INT"}:
            val = self.__scanner.current.value
            self.__scanner.advance()
            return PTNode("factor", [], val)
        else:
            self.__scanner.shriek("How did we even get here?")
    
    if __name__ == "main":

        fpath = "onetoten.py"

        # parser = TinyParser(fpath)
        # ptroot = parser.parse_program()
        print("Parse tree:")
        print("-" * 25)
        # ptroot.dump()
        print("=" * 25)
        print()
