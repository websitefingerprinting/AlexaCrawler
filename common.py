from os.path import join, abspath, dirname, pardir
import logging
from os.path import expanduser
logger = logging.getLogger("crawler")


unmon_list = './sites/unmon_sites.txt'
mon_list = './sites/mon_sites.txt'
Pardir = abspath(join(dirname(__file__), pardir))
DumpDir = join( Pardir , "AlexaCrawler/dump")
ListDir = join( Pardir, "AlexaCrawler/list")
SendMailPyDir = join(Pardir, "AlexaCrawler/private/sendmail.py")
golang_communication_path = join(expanduser("~"), 'switch.txt')

TBB_PATH = '/home/docker/tor-browser_en-US/'

BROWSER_LAUNCH_TIMEOUT = 10
SOFT_VISIT_TIMEOUT = 70
HARD_VISIT_TIMEOUT = SOFT_VISIT_TIMEOUT + 10
MAXDUMPSIZE = 20000 #KB
GAP_BETWEEN_BATCHES = 2
GAP_BETWEEN_SITES = 5
GAP_AFTER_LAUNCH = 5
TCPDUMP_START_TIMEOUT = 2
My_Bridge_Ips = ['13.75.78.82', '52.175.31.228', '23.100.88.30','40.83.88.194','13.82.149.247']
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

