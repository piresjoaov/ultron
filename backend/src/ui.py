import time
import threading
import itertools

class Spinner:
    def __init__(self, message="Assistant: "):
        self.message = message
        self.stop_event = threading.Event()
        self.thread = None

    def _spin(self):
        for char in itertools.cycle("|/-\\"):
            if self.stop_event.is_set():
                break
            print(f"\r{self.message}{char}", end="", flush=True)
            time.sleep(0.1)
        print(f"\r{self.message} ", end="", flush=True)
        print(f"\r{self.message}", end="", flush=True)

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()

    def stop(self):
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join()