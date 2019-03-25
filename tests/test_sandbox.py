from src.inboxingmail.sandbox import Sandbox


def test_thisisatest():
    sandbox = Sandbox("hello")
    assert sandbox.hey() == 'hello'
