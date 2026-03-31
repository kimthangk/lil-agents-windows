from gemini_session import GeminiSession


def test_command_uses_gemini_binary():
    session = GeminiSession()
    program, args = session._command()
    assert program == "gemini"


def test_command_has_no_extra_flags():
    session = GeminiSession()
    program, args = session._command()
    assert args == []
