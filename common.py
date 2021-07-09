from os.path import join, abspath, dirname, pardir
import logging
logger = logging.getLogger("crawler")

unmon_list = './sites/Tranco_23Dec_21Jan_2021_top30k_filtered_cp.list'
mon_list = './sites/Tranco_23Dec_21Jan_2021_top30k_filtered_cp.list'
Pardir = abspath(join(dirname(__file__), pardir))
DumpDir = join( Pardir , "AlexaCrawler/dump")
ListDir = join( Pardir, "AlexaCrawler/list")
SendMailPyDir = join(Pardir, "AlexaCrawler/private/sendmail.py")

# crawl remarks
ConnError = 1
HasCaptcha = 1
Timeout = 0
OtherError = 1


gRPCAddr = "localhost:10086"
BROWSER_LAUNCH_TIMEOUT = 10
SOFT_VISIT_TIMEOUT = 90
HARD_VISIT_TIMEOUT = SOFT_VISIT_TIMEOUT + 10
MAXDUMPSIZE = 20000 #KB
GAP_BETWEEN_BATCHES = 5
CRAWLER_DWELL_TIME = 3
GAP_BETWEEN_SITES_MAX = 2
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

