import subprocess
import threading

from PyQt6.QtCore import QObject, pyqtSignal


class AgentSession(QObject):
    output_received = pyqtSignal(str)
    error_received = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._proc = None
        self._lock = threading.Lock()

    def _command(self) -> tuple[str, list[str]]:
        raise NotImplementedError

    def send(self, text: str) -> None:
        self.stop()
        program, args = self._command()
        try:
            self._proc = subprocess.Popen(
                [program] + args + [text],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            self.error_received.emit(f"Could not find '{program}'. Is it installed and on PATH?")
            return

        proc = self._proc
        threading.Thread(target=self._read_stdout, args=(proc,), daemon=True).start()
        threading.Thread(target=self._read_stderr, args=(proc,), daemon=True).start()
        threading.Thread(target=self._wait_finish, args=(proc,), daemon=True).start()

    def _read_stdout(self, proc) -> None:
        for chunk in iter(lambda: proc.stdout.read(256), b""):
            text = chunk.decode("utf-8", errors="replace")
            self.output_received.emit(text)
        proc.stdout.close()

    def _read_stderr(self, proc) -> None:
        for chunk in iter(lambda: proc.stderr.read(256), b""):
            text = chunk.decode("utf-8", errors="replace")
            self.error_received.emit(text)
        proc.stderr.close()

    def _wait_finish(self, proc) -> None:
        proc.wait()
        with self._lock:
            if self._proc is proc:
                self._proc = None
        self.finished.emit()

    def stop(self) -> None:
        with self._lock:
            proc = self._proc
            self._proc = None
        if proc and proc.poll() is None:
            proc.kill()
            proc.wait()
