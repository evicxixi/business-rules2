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


class Comparison:

    def __init__(self, name, has_value=True, field_types=None, values=None):
        self.name = name
        self.has_value = has_value
        self.field_types = field_types
        self.values = values


class ComparisonExpr:

    OPERATORS = {
        '=': {
            int: Comparison('equal_to'),
            str: Comparison('equal_to')
        },
        '>': {
            int: Comparison('greater_than')
        },
        '<': {
            int: Comparison('less_than')
        },
        '>=': {
            int: Comparison('greater_than_or_equal_to')
        },
        '<=': {
            int: Comparison('less_than_or_equal_to')
        },
        'startswith': {
            str: Comparison('starts_with')
        },
        'endswith': {
            str: Comparison('ends_with')
        },
        'in': {
            str: Comparison('contains'),
            list: Comparison('contains')
        },
        'containedby': {
            list: Comparison('is_contained_by')
        },
        'matches': {
            str: Comparison('matches_regex')
        },
        'not in': {
            list: Comparison('does_not_contain')
        },
        'not containedby': {
            list: Comparison('shares_no_elements_with')
        },
        'all in': {
            list: Comparison('contains_all')
        },
        'one in': {
            list: Comparison('shares_at_least_one_element_with')
        },
        'exactly one in': {
            list: Comparison('shares_exactly_one_element_with')
        },
        'is': {
            str: Comparison('non_empty', values=['notblank'], has_value=False),
            bool: {
                True: Comparison('is_true', has_value=False),
                False: Comparison('is_false', has_value=False)
            }
        }
    }

    def __init__(self, tokens):
        self.tokens = tokens.asList()
        self.field = self.tokens[0]
        self.operator = self.tokens[1]
        self.value = self._parse_value(self.tokens[2])

    @staticmethod
    def _parse_value(value):
        if value == 'notblank' or value.startswith("'"):
            return value
        if value.startswith("["):
            return value
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
        if '.' in value:
            return float(value)
        return int(value)

    def convert(self):
        compare_method = self.OPERATORS[self.operator]
        for value_type, value_comparison in compare_method.items():
            if isinstance(self.value, value_type):
                if isinstance(value_comparison, dict):
                    operator = value_comparison[self.value].name
                else:
                    operator = value_comparison.name
                return {
                    "name": self.field,
                    "operator": operator,
                    "value": self.value
                }

    def __str__(self):
        return "Comparison:('field': {}, 'operator': {}, 'value': {}, type: {})".format(
            self.field,
            self.operator,
            self.value,
            type(self.value)
        )


class LogicExpr:

    AND = ['AND', 'and', '&']
    OR = ['OR', 'or', '|']

    def __init__(self, operator):
        self.operator = 'AND' if operator.asList()[0] in self.AND else 'OR'

    def __str__(self):
        return "Operator:({})".format(self.operator)


class ExpressionParser():

    def __init__(self) -> None:
        self._query = self._create_parser()

    def parse(self, text):
        return self._query.parseString(text).asList()[0]

    def translate(self, rules):
        operator = 'all'
        conditions = {}
        expressions = []
        # find opeator
        for entry in rules:
            if isinstance(entry, LogicExpr):
                if entry.operator == 'AND':
                    operator = 'all'
                else:
                    operator = 'any'
            elif isinstance(entry, list):
                expressions.append(self.translate(entry))
            elif isinstance(entry, ComparisonExpr):
                expressions.append(entry.convert())
            else:
                raise ValueError()
        conditions[operator] = expressions
        return conditions

    def describe(self, text):
        def create_description(result, indent=0):
            for x in result:
                if isinstance(x, list):
                    create_description(x, indent + 1)
                elif isinstance(x, ComparisonExpr):
                    print("{}{}".format("   " * indent, str(x)))
                elif isinstance(x, LogicExpr):
                    print("{}{}".format("   " * indent, str(x)))
                else:
                    print("{}{}".format("   " * indent, x))
        create_description(self.parse(text))

    def _create_parser(self):

        OPERATORS = ComparisonExpr.OPERATORS.keys()

        AND = oneOf(LogicExpr.AND)
        OR = oneOf(LogicExpr.OR)
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

        COMPARISON.addParseAction(ComparisonExpr)
        AND.addParseAction(LogicExpr)
        OR.addParseAction(LogicExpr)

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
        return self.expression_parser.parse("".join(conditions))

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
