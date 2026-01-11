from PyQt6.QtCore import QThread, pyqtSignal

class WorkerThread(QThread):
    """
    Generic Worker Thread for running long tasks off the main thread.
    """
    finished = pyqtSignal(object) # Emits result
    error = pyqtSignal(str)       # Emits error message
    progress = pyqtSignal(str)    # Emits progress status

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
