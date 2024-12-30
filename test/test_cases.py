from utz.case import dash_case, snake_case, camel_case

dash = 'aaa-bb-c'
snake = 'aaa_bb_c'
camel = 'AaaBbC'


def test_dash_case():
    assert dash_case(dash) == dash
    assert dash_case(snake) == dash
    assert dash_case(camel) == dash


def test_snake_case():
    assert snake_case(dash) == snake
    assert snake_case(snake) == snake
    assert snake_case(camel) == snake


def test_camel_case():
    assert camel_case(dash) == camel
    assert camel_case(snake) == camel
    assert camel_case(camel) == camel
