from business_rules2.parser import ExpressionParser
from business_rules2.parser import RuleParser


def test_general(text):
    rule_parser = RuleParser()
    out = rule_parser.parsestr(text)
    print(out)


def test_rules():

    text = """rule 'hallo'
    when
    cond1 < 10 AND cond2 > 6
    then
    action(var2=10)
    end
    """

    test_general(text)


def test_exceptions_name():

    text = """
    rul 'name'
    when
    cond1 < 10 AND cond2 > 6
    then
    action(var2=10)
    end
    """

    test_general(text)


def test_exceptions_when():

    text = """
    rule 'name'
    wh
    cond1 < 10 AND cond2 > 6
    then
    action(var2=10)
    end
    """

    test_general(text)


def test_exceptions_cond():

    text = """
    rule 'name'
    when
    cond110 AND cond2 > 6
    then
    action(var2=10)
    end
    """

    test_general(text)


def test_exceptions_then():

    text = """
    rule 'name'
    when
    cond1 < 10 AND cond2 > 6
    th
    action(var2=10)
    end
    """

    test_general(text)


def test_exceptions_action():

    text = """
    rule 'name'
    when
    cond1 < 10 AND cond2 > 6
    then
    action(var2=10)
    end
    """
    test_general(text)


def test_exceptions_end():

    text = """
    rule 'name'
    when
    cond1 < 10 AND cond2 > 6
    then
    action(var2=10)
    en
    """
    test_general(text)
