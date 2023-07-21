"""
Module to test pytests and vscode testing tab
"""

from main import inc_dec

def test_increment():
    assert inc_dec.increment(3) == 4

def test_decrement():
    assert inc_dec.decrement(3) == 2
