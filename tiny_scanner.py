import re
import sys
import traceback

# Define RE to capture TINY comments.

TOKENS_RE = re.compile(r"[a-z]+"
                       r"|[0-9]+"
                       r"|[(){}+*/;\-]"
                       r"|=|<=|<|>=|>")

#Define TINY's reserved words.
RESERVED_WORDS = {
    "if" : "IF", "then" : "THEN", "else" : "ELSE", 
    "end" : "END", "repeat" : "REPEAT", "until" : "UNTIL",
    "write" : "WRITE", "EOS" : "EOS"
}
#Define TINY's symbols.
SYMBOLS = {
    "(" : "RPAREN", ")" : "LPAREN", "+" : "PLUS", "-" : "MINUS",
    "*" : "TIMES", "/" : "OVER", "=" : "EQ", ";" : "SEMI", 
    "<" : "GT", ">" : "LT", "<=" : "LTOEQ", ">=" : "GTOEQ"}
    
LOGPAD = " " * 10

class TinyScanner:
    def __init__(self, fpath, verbose = False):
        try:
            self.__source = open(fpath, "r").read()
        except Exception:
            traceback.print_exc()
            sys.exit(-1)
    
        self.verbose = verbose

        self.__tokens = TOKENS_RE.findall(self.__source)
        self.__tokens.append("EOS")

        self.current = None
        self.advance()

    def advance(self):
        if self.has_more:
            self.current = self.__next_token()
            self.log_nopad("['%s']" % self.current.string)

    def has_more(self):
        return len(self.__tokens) > 0

    def __next_token(self):
        if self.current != "EOS":
            tkn = self.__tokens.pop(0)
            return TinyToken(tkn)
        else:
            return None

    def log_nopad(self, msg):
        if self.verbose:
            print(msg)

    def shriek(self, msg):
        self.log("*** TinyScanner %s" % msg, pad = False)
        sys.exit(-1)

    def log(self, msg, pad = True):
        if self.verbose:
            print("%s%s" % (LOGPAD if pad else "", msg))
    
    def match (self, expected):
        val = self.current.value
        if self.current.kind != expected:
            self.shriek("Expected '%s', saw '%s'." % (expected, self.current.string))

        self.advance()
        return val


class TinyToken:
    def __init__(self, tkn):

        tkn = str(tkn)
        self.string = tkn
        self.value = tkn

        if tkn.isalpha():
            self.spelling = tkn
            if tkn in RESERVED_WORDS:
                self.kind = RESERVED_WORDS[tkn]
            else:
                self.kind = "ID"
                self.value = tkn
        elif tkn.isdigit():
            self.kind = "INT"
            self.value = int(tkn)
        elif tkn in SYMBOLS:
            self.kind = SYMBOLS[tkn]
        else:
            self.shriek("Illegal symbol '%s'." % tkn)

    def __str__(self) :
        return ("[Token '%s' (%s)]" % (self.string, self.kind))

    
