import pytest
from agent_session import AgentSession


class EchoSession(AgentSession):
    """Concrete session that runs Python to echo its input."""
    def _command(self) -> tuple[str, list[str]]:
        import sys
        return sys.executable, ["-c", "import sys; print(sys.argv[1])"]


def test_command_returns_tuple():
    session = EchoSession()
    program, args = session._command()
    assert isinstance(program, str)
    assert isinstance(args, list)


def test_output_received_emits(qtbot):
    session = EchoSession()
    received = []
    session.output_received.connect(received.append)
    with qtbot.waitSignal(session.finished, timeout=5000):
        session.send("hello")
    assert any("hello" in chunk for chunk in received)


def test_stop_does_not_raise_when_not_running():
    session = EchoSession()
    session.stop()  # Should not raise


def test_send_kills_previous_process(qtbot):
    """Calling send() while a process is running should kill and restart."""
    session = EchoSession()
    with qtbot.waitSignal(session.finished, timeout=5000):
        session.send("first")
        # Immediately send again — should not raise or hang
        session.send("second")
