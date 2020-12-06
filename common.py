from os.path import join, abspath, dirname, pardir
import logging
logger = logging.getLogger("crawler")


unmon_list = './sites/unmon_sites_1m.list'
mon_list = './sites/good_mon_sites.list'
Pardir = abspath(join(dirname(__file__), pardir))
DumpDir = join( Pardir , "AlexaCrawler/dump")
ListDir = join( Pardir, "AlexaCrawler/list")
SendMailPyDir = join(Pardir, "AlexaCrawler/private/sendmail.py")



BROWSER_LAUNCH_TIMEOUT = 10
SOFT_VISIT_TIMEOUT = 70
HARD_VISIT_TIMEOUT = SOFT_VISIT_TIMEOUT + 10
MAXDUMPSIZE = 20000 #KB
GAP_BETWEEN_BATCHES = 5
GAP_BETWEEN_SITES = 6
GAP_AFTER_LAUNCH = 5
TCPDUMP_START_TIMEOUT = 2
My_Bridge_Ips = ['40.117.188.85', '13.82.149.247']
My_Source_Ips = {
'10.0.0.4',
'10.0.2.4',
'10.0.2.5',
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

