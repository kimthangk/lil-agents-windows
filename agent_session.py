from PyQt6.QtCore import QObject, QProcess, pyqtSignal


class AgentSession(QObject):
    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process = QProcess(self)
        self._process.readyReadStandardOutput.connect(self._on_stdout)
        self._process.readyReadStandardError.connect(self._on_stderr)
        self._process.finished.connect(self._on_finished)

    def _command(self) -> tuple[str, list[str]]:
        """Return (program, base_args). Input text is appended as the last arg."""
        raise NotImplementedError

    def send(self, text: str) -> None:
        if self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()
            self._process.waitForFinished(1000)
        program, args = self._command()
        self._process.start(program, args + [text])

    def stop(self) -> None:
        if self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()
            self._process.waitForFinished(1000)

    def _on_stdout(self) -> None:
        data = self._process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        self.output_received.emit(data)

    def _on_stderr(self) -> None:
        data = self._process.readAllStandardError().data().decode("utf-8", errors="replace")
        self.error_received.emit(data)

    def _on_finished(self) -> None:
        # Flush any remaining stdout/stderr before emitting finished
        remaining_out = self._process.readAllStandardOutput().data()
        if remaining_out:
            self.output_received.emit(remaining_out.decode("utf-8", errors="replace"))
        remaining_err = self._process.readAllStandardError().data()
        if remaining_err:
            self.error_received.emit(remaining_err.decode("utf-8", errors="replace"))
        self.finished.emit()
