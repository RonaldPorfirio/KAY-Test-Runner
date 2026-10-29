"""Regression context: add(2, 3) must return 5."""

from calculator import add

def test_add():
    assert add(2, 3) == 5
