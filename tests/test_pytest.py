"""
Module to test pytests and vscode testing tab
"""

# pylint: disable=C0111

from examples import inc_dec

def test_basic():
    assert 1 + 1 == 2

def test_increment():
    assert inc_dec.increment(3) == 4

def test_decrement():
    assert inc_dec.decrement(3) == 2
