import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds):
    """From: http://stackoverflow.com/a/601168/1336939"""
    def signal_handler(signum, frame):
        raise Exception("Timed out!")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

class TimeoutException(Exception):
    pass


class HardTimeoutException(Exception):
    pass
