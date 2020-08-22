business-rules
==============

[![CodeFactor](https://www.codefactor.io/repository/github/logfile-at/business-rules2/badge)](https://www.codefactor.io/repository/github/logfile-at/business-rules2)
[![Github version](https://img.shields.io/github/v/release/logfile-at/business-rules2?label=github&logo=github)](https://github.com/logfile-at/business-rules2/releases)
[![PyPI version](https://img.shields.io/pypi/v/business-rules2.svg?logo=pypi&logoColor=FFE873)](https://pypi.org/project/business-rules2/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/business-rules2.svg?logo=python&logoColor=FFE873)](https://pypi.org/project/business-rules2/)
[![PyPI downloads](https://pepy.tech/badge/business-rules2/month)](https://pepy.tech/project/business-rules2/month)
[![GitHub](https://img.shields.io/github/license/logfile-at/business-rules2.svg)](LICENSE)


As a software system grows in complexity and usage, it can become burdensome if
every change to the logic/behavior of the system also requires you to write and
deploy new code. The goal of this business rules engine is to provide a simple
interface allowing anyone to capture new rules and logic defining the behavior
of a system, and a way to then process those rules on the backend.

You might, for example, find this is a useful way for analysts to define
marketing logic around when certain customers or items are eligible for a
discount or to automate emails after users enter a certain state or go through
a particular sequence of events.


## Usage

### 1. Define Your set of variables

Variables represent values in your system, usually the value of some particular object.  You create rules by setting threshold conditions such that when a variable is computed that triggers the condition some action is taken.

You define all the available variables for a certain kind of object in your code, and then later dynamically set the conditions and thresholds for those.


**For example:**


```python
from business_rules2.variables import (
    BaseVariables,
    numeric_rule_variable,
    string_rule_variable,
    select_rule_variable
)

class Products():

    def __init__(self):
        self.stock_state = 0
        self.related_products = 2
        self.current_inventory = 3
        self.expire_in_days = 2


class ProductVariables(BaseVariables):

    def __init__(self, product):
        self.product = product

    @numeric_rule_variable
    def current_inventory(self):
        return self.product.current_inventory

    @numeric_rule_variable(label='Days until expiration')
    def expiration_days(self):
        return self.product.expire_in_days

    @string_rule_variable()
    def current_month(self):
        return datetime.datetime.now().strftime("%B")

```

### 2. Define your set of actions

These are the actions that are available to be taken when a condition is triggered.

For example:

```python
from business_rules2.fields import FIELD_NUMERIC
from business_rules2.actions import (
    BaseActions,
    rule_action
)

class ProductActions(BaseActions):

    def __init__(self, product):
        self.product = product

    @rule_action()
    def change_stock_state(self, stock_state):
        self.product.stock_state = stock_state

    @rule_action()
    def order_more(self, number_to_order):
        self.product.stock_state += number_to_order
```

### 3. Build the rules

#### Operators

**=** equal to

    * int
    * str

**>** greater than

    * int

**<** less than

    * int

**>=** greater than or equal to

    * int

**>=** less than or equal to

    * int

#### Keywords

    * startswith
    * endswid
    * in
    * not in
    * all in
    * one in
    * exactly one in
    * containedby
    * not containedby
    * matches
    * is
        * True
        * False
        * notblank

#### Example rules

```
rule "expired foods"
when
    expiration_days < 5 AND current_inventory > 20
then
    put_on_sale(sale_percentage=0.25, value=25)
end

rule "christmas time"
when
    current_inventory < 5 OR (current_month = 'December' AND current_inventory < 30)
then
    order_more(number_to_order=40)
end
```

### 4. Run your rules

```python
from business_rules2 import run_all

from business_rules2.parser import RuleParser


rules = """
rule "expired foods"
when
    expiration_days < 5 AND current_inventory > 20
then
    put_on_sale(sale_percentage=0.25, value=25)
end

rule "christmas time"
when
    current_inventory < 5 OR (current_month = 'December' AND current_inventory < 30)
then
    order_more(number_to_order=40)
end
"""

product = Products()
parser = RuleParser()
rules_translated = parser.parsestr(rules)

run_all(
    rule_list=rules_translated,
    defined_variables=ProductVariables(product),
    defined_actions=ProductActions(product),
    stop_on_first_trigger=True
)

```

## API

#### Variable Types and Decorators:

The type represents the type of the value that will be returned for the variable and is necessary since there are different available comparison operators for different types, and the front-end that's generating the rules needs to know which operators are available.

All decorators can optionally take a label:
- `label` - A human-readable label to show on the frontend. By default we just split the variable name on underscores and capitalize the words.

The available types and decorators are:

**numeric** - an integer, float, or python Decimal.

`@numeric_rule_variable` operators:

* `equal_to`
* `greater_than`
* `less_than`
* `greater_than_or_equal_to`
* `less_than_or_equal_to`

Note: to compare floating point equality we just check that the difference is less than some small epsilon

**string** - a python bytestring or unicode string.

`@string_rule_variable` operators:

* `equal_to`
* `starts_with`
* `ends_with`
* `contains`
* `matches_regex`
* `non_empty`

**boolean** - a True or False value.

`@boolean_rule_variable` operators:

* `is_true`
* `is_false`

**select** - a set of values, where the threshold will be a single item.

`@select_rule_variable` operators:

* `contains`
* `does_not_contain`

**select_multiple** - a set of values, where the threshold will be a set of items.

`@select_multiple_rule_variable` operators:

* `contains_all`
* `is_contained_by`
* `shares_at_least_one_element_with`
* `shares_exactly_one_element_with`
* `shares_no_elements_with`
