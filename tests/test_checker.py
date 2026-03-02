from app.core.checker import check_numeric, check_text, check_multiple_choice


def test_check_numeric_integer():
    assert check_numeric("5", 5)[0] is True
    assert check_numeric("5", 6)[0] is False


def test_check_numeric_fraction_and_mixed():
    assert check_numeric("1/2", "1/2")[0] is True
    assert check_numeric("3 1/4", "13/4")[0] is True


def test_check_text():
    assert check_text("Ответ", "ответ")[0] is True
    assert check_text("ёлка", "елка")[0] is True


def test_check_multiple_choice():
    assert check_multiple_choice([1], [1])[0] is True
    assert check_multiple_choice([1, 2], [2, 1])[0] is True
    assert check_multiple_choice([1], [1, 2])[0] is False

