from business_rules2 import parser
from business_rules2.parser import ExpressionParser
from business_rules2.parser import RuleParser
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from parsimonious.nodes import Node
from parsimonious.exceptions import VisitationError
import re
import typing


class SyntaxCheck():

    grammar = None
    grammar_text= """
    rule = name when expression then action end
    name = ~"\s?rule\s*\'(\w+)\'"
    when = ~"\s?when\s?"
    expression = ~"\s?" condition ~"(OR|AND)\s"(condition ~"\s?")*
    then = ~"\s?then\s?"
    condition = ~"\s?([a-z0-9A-Z_]+)\s?([=|>(=)?|<(=)?])\s?([a-z0-9A-Z_]+)\s?"
    action = ~"\s?([a-z0-9A-Z_]+)\(" assignment (~",\s?" assignment)* ~"\)\s?"
    assignment = ~"\s?([a-z0-9A-Z_]+)\=([a-z0-9A-Z_]+)\s?"
    end = ~"\s?end\s?"
    """
    rules = None
    visitor = None
    tree = None

    def __init__(self, to_parse, grammar = grammar_text):
        self.grammar = Grammar(grammar)
        self.rules = to_parse
        self.visitor = NodeVisitor()
        self.visitor.grammar = self.grammar
        print("hier")

    def is_syntax_correct(self):
        try:
            self.tree = self.visitor.parse(self.rules)
        #find a way to throw the exception to inform the user where
        #the syntax-error happend
        except VisitationError:
            return False
        return True
    
    def get_tree(self):
        
        if(self.is_syntax_correct()):
            return self.tree
        return None

    def get_correct_syntax(self):
        
        operators = ["<", ">", "<=", ">=", "="]
        rules_help = ""
        last_c = ""
        next_c = ""
        count = 0
        text = self.rules

        for c in text:

            #save store the chars before and next the current char
            if count == 0:
                last_c = None
                next_c = text[1]
            elif count == len(text)-1:
                last_c = text[count-1]
                next_c = None
            else:
                last_c = text[count-1]
                next_c = text[count+1]
                
            count = count + 1
            
            #correct whitesapces
            if c in operators:
                if last_c != " ":
                    rules_help = rules_help + " "
                    
                rules_help = rules_help + c
                
                if next_c != " ":
                    rules_help = rules_help + " "
            else:
                rules_help = rules_help + c
                
        return rules_help