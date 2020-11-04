import signal
from contextlib import contextmanager
import psutil
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


def is_tcpdump_running(p0):
    if "dumpcap" in psutil.Process(p0.pid).cmdline():
        return p0.returncode is None
    for proc in gen_all_children_procs(p0.pid):
        if "dumpcap" in proc.cmdline():
            return True
    return False


def gen_all_children_procs(parent_pid):
    """Iterator over the children of a process."""
    parent = psutil.Process(parent_pid)
    for child in parent.children(recursive=True):
        yield child


def kill_all_children(parent_pid):
    """Kill all child process of a given parent."""
    for child in gen_all_children_procs(parent_pid):
        child.kill()


class TcpdumpTimeoutError(Exception):
    pass
