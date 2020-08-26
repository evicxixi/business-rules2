from business_rules2.fields import FIELD_NO_INPUT
from business_rules2.parser import RuleParser
from business_rules2.variables import BaseVariables
from business_rules2.actions import BaseActions

from typing import (
    Any,
    Dict,
    List,
    Text,
    Optional,
    Union
)


def run_all(
    rule_list: Union[Text, Dict[Text, Any], List[Dict[Text, Any]]],
    defined_variables: BaseVariables,
    defined_actions: BaseActions,
    stop_on_first_trigger: bool = False
) -> bool:

    if isinstance(rule_list, list):
        parsed_rules = rule_list
    elif isinstance(rule_list, dict):
        parsed_rules = [rule_list]
    elif isinstance(rule_list, str):
        parsed_rules = RuleParser().parsestr(rule_list)
    else:
        raise ValueError('Rules can not be pasred! Invalid rules')

    rule_was_triggered = False
    for rule in parsed_rules:
        result = run(rule, defined_variables, defined_actions)
        if result:
            rule_was_triggered = True
            if stop_on_first_trigger:
                return True
    return rule_was_triggered


def run(
    rule: Union[Text, Dict[Text, Any]],
    defined_variables: BaseVariables,
    defined_actions: BaseActions
) -> bool:
    rule_parsed: Optional[Dict[Text, Any]] = None
    if isinstance(rule, str):
        rules: List[Dict[Text, Any]] = RuleParser().parsestr(rule)
        if len(rules) == 1:
            rule_parsed = rules[0]
    elif isinstance(rule, dict):  # type: ignore
        rule_parsed = rule
    if not rule_parsed:
        raise ValueError()

    conditions, actions = rule_parsed['conditions'], rule_parsed['actions']
    rule_triggered = check_conditions_recursively(conditions, defined_variables)
    if rule_triggered:
        do_actions(actions, defined_actions)
        return True
    return False


def check_conditions_recursively(conditions, defined_variables):
    keys = list(conditions.keys())
    if keys == ['all']:
        assert len(conditions['all']) >= 1
        for condition in conditions['all']:
            if not check_conditions_recursively(condition, defined_variables):
                return False
        return True

    elif keys == ['any']:
        assert len(conditions['any']) >= 1
        for condition in conditions['any']:
            if check_conditions_recursively(condition, defined_variables):
                return True
        return False

    else:
        # help prevent errors - any and all can only be in the condition dict
        # if they're the only item
        assert not ('any' in keys or 'all' in keys)
        return check_condition(conditions, defined_variables)


def check_condition(condition, defined_variables):
    """ Checks a single rule condition - the condition will be made up of
    variables, values, and the comparison operator. The defined_variables
    object must have a variable defined for any variables in this condition.
    """
    name, op, value = condition['name'], condition['operator'], condition['value']
    operator_type = _get_variable_value(defined_variables, name)
    return _do_operator_comparison(operator_type, op, value)


def _get_variable_value(defined_variables, name):
    """ Call the function provided on the defined_variables object with the
    given name (raise exception if that doesn't exist) and casts it to the
    specified type.

    Returns an instance of operators.BaseType
    """
    def fallback(*args, **kwargs):
        raise AssertionError(
            "Variable {0} is not defined in class {1}".format(
                name, defined_variables.__class__.__name__
            )
        )
    method = getattr(defined_variables, name, fallback)
    val = method()
    return method.field_type(val)


def _do_operator_comparison(operator_type, operator_name, comparison_value):
    """ Finds the method on the given operator_type and compares it to the
    given comparison_value.

    operator_type should be an instance of operators.BaseType
    comparison_value is whatever python type to compare to
    returns a bool
    """
    def fallback(*args, **kwargs):
        raise AssertionError("Operator {0} does not exist for type {1}".format(
            operator_name, operator_type.__class__.__name__))
    method = getattr(operator_type, operator_name, fallback)
    if getattr(method, 'input_type', '') == FIELD_NO_INPUT:
        return method()
    return method(comparison_value)


def do_actions(actions, defined_actions):
    for action in actions:
        method_name = action['name']

        def fallback(*args, **kwargs):
            raise AssertionError(
                "Action {0} is not defined in class {1}".format(
                    method_name,
                    defined_actions.__class__.__name__
                )
            )
        params = action.get('params') or {}
        method = getattr(defined_actions, method_name, fallback)
        method(**params)
