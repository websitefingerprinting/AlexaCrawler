from os.path import join, abspath, dirname, pardir
import psutil
import logging
logger = logging.getLogger("crawler")

unmon_list = './unmon_sites.txt'
mon_list = './mon_sites.txt'
Pardir = abspath(join(dirname(__file__), pardir))
DumpDir = join( Pardir , "AlexaCrawler/dump")
ListDir = join( Pardir, "AlexaCrawler/list")
SendMailPyDir = join(Pardir, "AlexaCrawler/private/sendmail.py")
SOFT_VISIT_TIMEOUT = 60
HARD_VISIT_TIMEOUT = SOFT_VISIT_TIMEOUT + 20
GAP_BETWEEN_BATCHES = 2
GAP_BETWEEN_SITES = 5
GAP_AFTER_LAUNCH = 8
TCPDUMP_START_TIMEOUT = 2
My_Bridge_Ips = ['13.75.78.82', '52.175.31.228', '23.100.88.30','40.83.88.194']
My_Source_Ips = {
'10.0.0.4',
'10.0.0.5',
'10.0.0.6',
'10.0.0.7',
'10.0.1.4',
'10.0.1.5',
'10.0.1.6',
'10.0.1.8',
'172.17.0.1',
'172.17.0.2',
'172.17.0.3',
'172.17.0.4',
'172.17.0.5',
'172.17.0.6',
'172.17.0.7',
'172.17.0.8',
}

class TcpdumpTimeoutError(Exception):
    pass

def is_tcpdump_running(p0):
    logger.debug("{}".format(psutil.Process(p0.pid).cmdline()))
    if "tshark" in psutil.Process(p0.pid).cmdline():
        return p0.returncode is None
    for proc in gen_all_children_procs(p0.pid):
        if "tshark" in proc.cmdline():
            logger.debug("{}".format(proc.cmdline()))
            return True
    return False

def gen_all_children_procs(parent_pid):
    """Iterator over the children of a process."""
    parent = psutil.Process(parent_pid)
    for child in parent.children(recursive=True):
        yield child