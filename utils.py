import signal
import random
import tempfile
import string
import shutil
from contextlib import contextmanager
import psutil
from common import SendMailPyDir
import subprocess
import logging
import sys
import os
from os import makedirs
from os.path import join
from common import DumpDir
import datetime


def make_tb_copy(tmpdir, src):
    """from https://github.com/pylls/padding-machines-for-tor/blob/master/collect-traces/client/exp/collect.py"""
    dst = os.path.join(tmpdir,
    ''.join(random.choices(string.ascii_uppercase + string.digits, k=24)))

    # ibus breaks on multiple copies that move location, need to ignore
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('ibus'))
    return dst


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
        line = line.rstrip('\n')
        if len(line) > 0:
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


def config_logger(log_file):
    logger = logging.getLogger("crawler")
    # Set logging format
    LOG_FORMAT = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
    # Set file
    ch1 = logging.StreamHandler(sys.stdout)
    ch1.setFormatter(logging.Formatter(LOG_FORMAT))
    ch1.setLevel(logging.INFO)
    logger.addHandler(ch1)

    if log_file is not None:
        pardir = os.path.split(log_file)[0]
        f = open(log_file, "w")
        f.close()
        if not os.path.exists(pardir):
            os.makedirs(pardir)
        ch2 = logging.FileHandler(log_file)
        ch2.setFormatter(logging.Formatter(LOG_FORMAT))
        ch2.setLevel(logging.DEBUG)
        logger.addHandler(ch2)
    logger.setLevel(logging.INFO)
    return logger


def init_directories(mode, u):
    # Create a results dir if it doesn't exist yet
    if not os.path.exists(DumpDir):
        makedirs(DumpDir)

    # Define output directory
    timestamp = datetime.datetime.now().strftime('%m%d_%H%M_%S%f')[:-4]
    if u:
        output_dir = join(DumpDir, 'u' + mode + '_' + timestamp)
    else:
        output_dir = join(DumpDir, mode + '_' + timestamp)
    makedirs(output_dir)

    return output_dir
