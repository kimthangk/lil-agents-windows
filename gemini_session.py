from agent_session import AgentSession


class GeminiSession(AgentSession):
    def _command(self) -> tuple[str, list[str]]:
        return "gemini", []
