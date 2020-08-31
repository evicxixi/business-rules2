from business_rules2 import parser
from business_rules2.parser import ExpressionParser
from business_rules2.parser import RuleParser
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor
from parsimonious.nodes import Node
import re
import typing


class SyntaxCheck(grammar: str):

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

    def __init__(self, to_parse, grammar = grammar_text):
        self.grammar = Grammar(grammar)
        self.rules = to_parse
    
    def get_tree():
        visitor = NodeVisitor()
        visitor.grammar = self.grammar
        if(is_syntax_correct(visitor)):
            tree = grammar.parse(self.rules)
            return tree
        return None

    def is_syntax_correct(visitor):
        try:
            tree = grammar.parse(self.rules)
        except Error:
            return False
        return True





#visitor = NodeVisitor()
#visitor.grammar = grammar
#visitor.parse(test)
#tree = grammar.parse(test)

#print(tree)
#print(tree.children[2].children[1].text)
#visitor.generic_visit("name")