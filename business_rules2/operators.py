from decimal import Decimal
import inspect
import re
from functools import wraps

from business_rules2.fields import (
    FIELD_TEXT,
    FIELD_NUMERIC,
    FIELD_NO_INPUT,
    FIELD_SELECT,
    FIELD_SELECT_MULTIPLE
)
from business_rules2.utils import fn_name_to_pretty_label, float_to_decimal

from typing import (
    Any,
    Match,
    Type,
    Text,
    Optional
)


class BaseType(object):

    export_in_rule_data: bool = False

    def __init__(self, value):
        self.value = self._assert_valid_value_and_cast(value)

    def _assert_valid_value_and_cast(self, value):
        raise NotImplementedError()

    @classmethod
    def get_all_operators(cls):
        methods = inspect.getmembers(cls)
        return [{'name': m[0],
                 'operator': m[1].operator,
                 'valid_value': m[1].valid_value,
                 'label': m[1].label,
                 'input_type': m[1].input_type}
                for m in methods if getattr(m[1], 'is_operator', False)]


def export_type(cls: Type[BaseType]) -> Type[BaseType]:
    """ Decorator to expose the given class to business_rules2.export_rule_data. """
    cls.export_in_rule_data = True
    return cls


def type_operator(input_type, operator, valid_value=None, label=None,
                  assert_type_for_arguments=True):
    """ Decorator to make a function into a type operator.

    - assert_type_for_arguments - if True this patches the operator function
      so that arguments passed to it will have _assert_valid_value_and_cast
      called on them to make type errors explicit.
    """
    def wrapper(func):
        func.is_operator = True
        func.label = label or fn_name_to_pretty_label(func.__name__)
        func.input_type = input_type
        func.operator = operator
        func.valid_value = valid_value

        @wraps(func)
        def inner(self, *args, **kwargs):
            if assert_type_for_arguments:
                args = [self._assert_valid_value_and_cast(arg) for arg in args]
                kwargs = dict((k, self._assert_valid_value_and_cast(v))
                              for k, v in kwargs.items())
            return func(self, *args, **kwargs)
        return inner
    return wrapper


@export_type
class StringType(BaseType):

    name = "string"

    def _assert_valid_value_and_cast(self, value):
        value: Text = value or ""
        if not isinstance(value, str):  # type: ignore
            raise AssertionError("{0} is not a valid string type.".
                                 format(value))
        return value

    @type_operator(FIELD_TEXT, '=')
    def equal_to(self, other_string: Text) -> bool:
        return self.value == other_string

    @type_operator(FIELD_TEXT, '~=', label="Equal To (case insensitive)")
    def equal_to_case_insensitive(self, other_string: Text) -> bool:
        return self.value.lower() == other_string.lower()

    @type_operator(FIELD_TEXT, 'startswith')
    def starts_with(self, other_string: Text) -> bool:
        return self.value.startswith(other_string)

    @type_operator(FIELD_TEXT, 'endswith')
    def ends_with(self, other_string: Text) -> bool:
        return self.value.endswith(other_string)

    @type_operator(FIELD_TEXT, 'in')
    def contains(self, other_string: Text) -> bool:
        return other_string in self.value

    @type_operator(FIELD_TEXT, 'matches')
    def matches_regex(self, regex) -> Optional[Match[Any]]:
        return re.search(regex, self.value)

    @type_operator(FIELD_NO_INPUT, 'is', valid_value='notblank')
    def non_empty(self) -> bool:
        return bool(self.value)


@export_type
class NumericType(BaseType):
    EPSILON = Decimal('0.000001')

    name = "numeric"

    @staticmethod
    def _assert_valid_value_and_cast(value):
        if isinstance(value, float):
            # In python 2.6, casting float to Decimal doesn't work
            return float_to_decimal(value)
        if isinstance(value, int):
            return Decimal(value)
        if isinstance(value, Decimal):
            return value
        else:
            raise AssertionError("{0} is not a valid numeric type.".
                                 format(value))

    @type_operator(FIELD_NUMERIC, '=')
    def equal_to(self, other_numeric) -> bool:
        return abs(self.value - other_numeric) <= self.EPSILON

    @type_operator(FIELD_NUMERIC, '>')
    def greater_than(self, other_numeric) -> bool:
        return (self.value - other_numeric) > self.EPSILON

    @type_operator(FIELD_NUMERIC, '>=')
    def greater_than_or_equal_to(self, other_numeric) -> bool:
        return self.greater_than(other_numeric) or self.equal_to(other_numeric)

    @type_operator(FIELD_NUMERIC, '<')
    def less_than(self, other_numeric) -> bool:
        return (other_numeric - self.value) > self.EPSILON

    @type_operator(FIELD_NUMERIC, '>=')
    def less_than_or_equal_to(self, other_numeric) -> bool:
        return self.less_than(other_numeric) or self.equal_to(other_numeric)


@export_type
class BooleanType(BaseType):

    name = "boolean"

    def _assert_valid_value_and_cast(self, value):
        if type(value) != bool:
            raise AssertionError("{0} is not a valid boolean type".
                                 format(value))
        return value

    @type_operator(FIELD_NO_INPUT, 'is', valid_value=True)
    def is_true(self) -> bool:
        return self.value

    @type_operator(FIELD_NO_INPUT, 'is', valid_value=False)
    def is_false(self) -> bool:
        return not self.value


@export_type
class SelectType(BaseType):

    name = "select"

    def _assert_valid_value_and_cast(self, value):
        if not hasattr(value, '__iter__'):
            raise AssertionError("{0} is not a valid select type".
                                 format(value))
        return value

    @staticmethod
    def _case_insensitive_equal_to(value_from_list, other_value):
        if isinstance(value_from_list, str) and isinstance(other_value, str):
            return value_from_list.lower() == other_value.lower()
        else:
            return value_from_list == other_value

    @type_operator(FIELD_SELECT, 'in', assert_type_for_arguments=False)
    def contains(self, other_value) -> bool:
        for val in self.value:
            if self._case_insensitive_equal_to(val, other_value):
                return True
        return False

    @type_operator(FIELD_SELECT, 'not in', assert_type_for_arguments=False)
    def does_not_contain(self, other_value) -> bool:
        for val in self.value:
            if self._case_insensitive_equal_to(val, other_value):
                return False
        return True


@export_type
class SelectMultipleType(BaseType):

    name = "select_multiple"

    def _assert_valid_value_and_cast(self, value) -> bool:
        if not hasattr(value, '__iter__'):
            raise AssertionError("{0} is not a valid select multiple type".
                                 format(value))
        return value

    @type_operator(FIELD_SELECT_MULTIPLE, 'all in')
    def contains_all(self, other_value) -> bool:
        select = SelectType(self.value)
        for other_val in other_value:
            if not select.contains(other_val):
                return False
        return True

    @type_operator(FIELD_SELECT_MULTIPLE, 'containedby')
    def is_contained_by(self, other_value) -> bool:
        other_select_multiple = SelectMultipleType(other_value)
        return other_select_multiple.contains_all(self.value)

    @type_operator(FIELD_SELECT_MULTIPLE, 'one in')
    def shares_at_least_one_element_with(self, other_value) -> bool:
        select = SelectType(self.value)
        for other_val in other_value:
            if select.contains(other_val):
                return True
        return False

    @type_operator(FIELD_SELECT_MULTIPLE, 'exactly one in')
    def shares_exactly_one_element_with(self, other_value) -> bool:
        found_one = False
        select = SelectType(self.value)
        for other_val in other_value:
            if select.contains(other_val):
                if found_one:
                    return False
                found_one = True
        return found_one

    @type_operator(FIELD_SELECT_MULTIPLE, 'not containedby')
    def shares_no_elements_with(self, other_value) -> bool:
        return not self.shares_at_least_one_element_with(other_value)
