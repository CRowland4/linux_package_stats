"""Class for custom CLI animations."""
import constants as cons
import threading
import time


# P: Unless there's a clear reason to choose OOP, I always learn towards FP, and originally wrote this without a class.
#    After writing it I thought it would actually be cleaner as a class, and comparing this to the previous version, I'm
#    happy with that choice.

class Animation:
    def __init__(self, action: callable, time_delay: float = cons.ANIMATION_DELAY):
        self.action = action
        self.time_delay = time_delay
        self._run_flag = False
        self._thread = threading.Thread(target=self._animation)

    def start(self) -> None:
        self._run_flag = True
        self._thread.start()
        return

    def stop(self) -> None:
        self._run_flag = False
        return

    def _animation(self) -> None:
        while self._run_flag:
            self.action()
            time.sleep(self.time_delay)

        return
