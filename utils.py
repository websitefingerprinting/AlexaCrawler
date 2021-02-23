import signal
from contextlib import contextmanager
import psutil
from common import SendMailPyDir


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
        try:
            child.kill()
        except psutil.NoSuchProcess:
            continue
    psutil.Process(parent_pid).kill()


class TcpdumpTimeoutError(Exception):
    pass


def pick_specific_webs(listdir):
    l = []
    with open(listdir, "r") as f:
        lines = f.readlines()
    for line in lines:
        line = int(line.split("\n")[0])
        l.append(line)
    return l


# from https://github.com/onionpop/tor-browser-crawler/blob/master/tbcrawler/crawler.py
def is_connection_error_page(page_source):
    """Check if we get a connection error, i.e. 'Problem loading page'."""
    return "entity connectionFailure.title" in page_source


def has_captcha(page_source):
    keywords = ['recaptcha_submit',
                'manual_recaptcha_challenge_field']
    return any(keyword in page_source for keyword in keywords)


def check_conn_error(driver):
    if driver.current_url == "about:newtab":
        print('Stuck in about:newtab')
        return True
    if is_connection_error_page(driver.page_source.strip().lower()):
        print('Connection Error')
        return True
    return False


def check_captcha(page_source):
    if has_captcha(page_source):
        print('captcha found')
        return True
    return False

def sendmail(who, msg):
    cmd = "python3 " + SendMailPyDir + " -m " + msg + " -w " + who
    subprocess.call(cmd, shell=True)
