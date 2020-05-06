import signal
from contextlib import contextmanager
import sys
import logging
@contextmanager
def timeout(seconds):
    """From: http://stackoverflow.com/a/601168/1336939"""
    def signal_handler(signum, frame):
        raise HardTimeoutException("Hard Timed out after {}s!".format(seconds))

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

