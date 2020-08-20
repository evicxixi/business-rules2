from collections import OrderedDict
import shlex

from pyparsing import (
    oneOf,
    Word,
    alphanums,
    nums,
    QuotedString,
    CaselessKeyword,
    infixNotation,
    opAssoc
)


class ExpressionParser():
    class ComparisonExpr:
        def __init__(self, tokens):
            self.tokens = tokens.asList()
            self.field = self.tokens[0]
            self.operator = self.tokens[1]
            self.value = self.tokens[2]

        def __str__(self):
            return "Comparison:('field': {}, 'operator': {}, 'value': {})".format(
                self.field,
                self.operator,
                self.value
            )

    def __init__(self) -> None:
        self._query = self._create_parser()

    def parse(self, text):
        return self._query.parseString(text).asList()[0]

    def describe(self, text):
        def create_description(result, indent=0):
            for x in result:
                if isinstance(x, list):
                    create_description(x, indent + 1)
                elif isinstance(x, self.ComparisonExpr):
                    print("{}{}".format("   " * indent, str(x)))
                else:
                    print("{}{}".format("   " * indent, x))
        create_description(self.parse(text))

    def _create_parser(self):

        OPERATORS = [
            '=',  # equal_to
            '>',  # greater_than
            '<',  # less_than
            '>=',  # greater_than_or_equal_to
            '<=',  # less_than_or_equal_to
            'startswith',  # starts_with
            'endswith',  # ends_with
            'in',  # contains, is_contained_by
            'matches'  # matches_regex
            'not in',  # does_not_contain, shares_no_elements_with
            'all in',  # contains_all
            'one in',  # shares_at_least_one_element_with
            'exactly one in',  # shares_exactly_one_element_with
            'is',  # is_true, is_false, non_empty
        ]

        AND = oneOf(['AND', 'and', '&'])
        OR = oneOf(['OR', 'or', '|'])
        FIELD = Word(alphanums + '_')
        OPERATOR = oneOf(OPERATORS)
        VALUE = (
            Word(nums + '-.') |
            QuotedString(quoteChar="'", unquoteResults=False)(alphanums) |
            QuotedString('[', endQuoteChar=']', unquoteResults=False)(alphanums + "'-.") |
            CaselessKeyword('true') |
            CaselessKeyword('false') |
            CaselessKeyword('notblank')
        )
        COMPARISON = FIELD + OPERATOR + VALUE

        QUERY = infixNotation(
            COMPARISON,
            [
                (AND, 2, opAssoc.LEFT,),
                (OR, 2, opAssoc.LEFT,),
            ]
        )

        COMPARISON.addParseAction(self.ComparisonExpr)

        return QUERY


class RuleParser():

    def __init__(self) -> None:
        self.expression_parser = ExpressionParser()

    def parsestr(self, text):
        rules = OrderedDict()
        rulename = None
        is_condition = False
        is_action = False
        ignore_line = False

        for line in text.split('\n'):
            ignore_line = False
            if line.lower().strip().startswith('rule'):
                is_condition = False
                is_action = False
                rulename = line.split(' ', 1)[1].strip("\"")
                rules[rulename] = {
                    'conditions': [],
                    'actions': []
                }
            if line.lower().strip().startswith('when'):
                ignore_line = True
                is_condition = True
                is_action = False
            if line.lower().strip().startswith('then'):
                ignore_line = True
                is_condition = False
                is_action = True
            if line.lower().strip().startswith('end'):
                ignore_line = True
                is_condition = False
                is_action = False
            if is_condition and not ignore_line:
                rules[rulename]['conditions'].append(line.strip())
            if is_action and not ignore_line:
                rules[rulename]['actions'].append(line.strip())
        rules_formated = [
            {
                'name': rule_name,
                'conditions': self.parse_conditions(rule_body['conditions']),
                'actions': self.parse_actions(rule_body['actions'])
            } for rule_name, rule_body in rules.items()
        ]
        return rules_formated

    def parse_conditions(self, conditions):
        return self.expression_parser.parse(conditions)

    def parse_actions(self, actions):
        parsed_actions = []
        for action in actions:
            func_name, func_args = action.strip().strip(")").rsplit("(", 1)
            args = [fa.strip(",").strip().split("=", 1) for fa in shlex.split(func_args)]
            parsed_actions.append({
                'name': func_name,
                'params': {arg[0]: arg[1] for arg in args}
            })
        return parsed_actions
