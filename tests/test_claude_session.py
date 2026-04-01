from claude_session import ClaudeSession


def test_command_uses_claude_binary():
    session = ClaudeSession()
    program, args = session._command()
    assert program == "claude"


def test_command_includes_print_flag():
    session = ClaudeSession()
    program, args = session._command()
    assert "-p" in args
