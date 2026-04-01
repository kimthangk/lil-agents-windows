from agent_session import AgentSession


class ClaudeSession(AgentSession):
    def _command(self) -> tuple[str, list[str]]:
        return "claude", ["-p"]
