"""
Class definition for parse-tree nodes.

Kieran Herley, June 2020
"""

class PTNode():
    """
    Implementation of generic parser-tree node.
    """
    
    def __init__(self, label, children, value = None):
        self.label = label
        self.value = value
        self.children = children
        
    def __str__(self):
        if self.value is None:
            return "[%s]" % (self.label)
        elif type(self.value) == str:
            return "[%s ('%s')]" % (self.label, self.value)
        else:
            return "[%s (%s)]" % (self.label, str(self.value))
    
    def dump(self, level = 0):
        print("   " * level + str(self))
        for c in reversed(self.children):
            c.dump(level + 1)
       
