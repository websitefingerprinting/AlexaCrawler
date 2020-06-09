from os.path import join, abspath, dirname, pardir
WebListDir = './unmon_sites.txt'
Pardir = abspath(join(dirname(__file__), pardir))
DumpDir = join( Pardir , "AlexaCrawler/dump")
SOFT_VISIT_TIMEOUT = 60
HARD_VISIT_TIMEOUT = SOFT_VISIT_TIMEOUT + 20
GAP_BETWEEN_BATCHES = 2
GAP_BETWEEN_SITES = 8
GAP_AFTER_LAUNCH = 8
padding_time = 4
My_Bridge_Ips = ['13.75.78.82', '52.175.31.228', '52.175.49.114','40.83.88.194', '13.94.61.159']
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