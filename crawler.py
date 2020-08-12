import subprocess
import os
import sys
from os import makedirs
import argparse
import time
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from pyvirtualdisplay import Display
import utils as ut
from common import *
from torcontroller import *
import logging
import math
import datetime


def config_logger(log_file):
    logger = logging.getLogger("crawler")
    # Set file
    if log_file is None:
        ch = logging.StreamHandler(sys.stdout)
    else:
        pardir = os.path.split(log_file)[0]
        if not os.path.exists(pardir):
            os.makedirs(pardir)
        ch = logging.FileHandler(log_file)

    # Set logging format
    LOG_FORMAT = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
    ch.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(ch)

    # Set level format
    logger.setLevel(logging.INFO)
    return logger


def init_directories(mode, u):
    # Create a results dir if it doesn't exist yet
    if not os.path.exists(DumpDir):
        makedirs(DumpDir)

    # Define output directory
    timestamp = time.strftime('%m%d_%H%M%S')
    if args.u:
        output_dir = join(DumpDir, 'u'+mode + '_' + timestamp)
    else:
        output_dir = join(DumpDir, mode + '_' + timestamp)
    makedirs(output_dir)

    return output_dir



def parse_arguments():
    parser = argparse.ArgumentParser(description='Crawl Alexa top websites and capture the traffic')

    parser.add_argument('-start',
                        type=int,
                        metavar='<start ind>',
                        default=0,
                        help='Start from which site in the list (include this ind).')
    parser.add_argument('-end',
                        type=int,
                        metavar='<end ind>',
                        default=50,
                        help='End to which site in the list (exclude this ind).')
    parser.add_argument('-b',
                        type=int,
                        metavar='<Num of batches>',
                        default=5,
                        help='Crawl batches, Tor restarts at each batch.')
    parser.add_argument('-m',
                        type=int,
                        metavar='<Num of instances in each batch>',
                        default=5,
                        help='Number of instances for each website in each batch to crawl. In unmon mode, for every m instances, restart tor.')
    parser.add_argument('-mode',
                        type=str,
                        required=True,
                        metavar='<parse mode>',
                        help='The type of dataset: clean, burst?.')
    parser.add_argument('-s',
                        action='store_false',
                        default=True,
                        help='Take a screenshot? (default:true)')
    parser.add_argument('-u',
                        action='store_true',
                        default=False,
                        help='is monitored webpage or unmonitored? (default:is monitored, false)')
    parser.add_argument('-p',
                        action='store_false',
                        default=True,
                        help='Parse file after crawl? (default:true)')
    parser.add_argument('-torrc',
                        type=str,
                        default=None,
                        help='Torrc file path.')
    parser.add_argument('-w',
                        type=str,
                        default=None,
                        help='Self provided web list.')
    parser.add_argument('-l',
                        type=str,
                        default=None,
                        help='Crawl specific unmon sites, given a list')
    parser.add_argument('-log',
                        type=str,
                        metavar='<log path>',
                        default=None,
                        help='path to the log file. It will print to stdout by default.')

    # Parse arguments
    args = parser.parse_args()
    return args


def get_driver():
    profile = webdriver.FirefoxProfile()
    profile.set_preference("network.proxy.type", 1)
    profile.set_preference("network.proxy.socks", "127.0.0.1")
    profile.set_preference("network.proxy.socks_port", 9050)
    profile.set_preference("network.proxy.socks_version", 5)
    profile.set_preference("browser.cache.disk.enable", False)
    profile.set_preference("browser.cache.memory.enable", False)
    profile.set_preference("browser.cache.offline.enable", False)
    profile.set_preference("network.http.use-cache", False)
    profile.update_preferences()
    driver = webdriver.Firefox(firefox_profile=profile)
    driver.set_page_load_timeout(SOFT_VISIT_TIMEOUT)
    return driver


def crawl(url, filename, guards, s):
    try:
        with ut.timeout(HARD_VISIT_TIMEOUT):
            driver = get_driver()
            src = ' or '.join(guards)
            # start tcpdump
            # cmd = "tcpdump host \(" + src + "\) and tcp -i eth0 -w " + filename+'.pcap'
            pcap_filter="tcp and (host " + src + ") and not tcp port 22 and not tcp port 20 "
            cmd = 'dumpcap -P -a duration:{} -a filesize:{} -i eth0 -s 0 -f \'{}\' -w {}' \
                .format(HARD_VISIT_TIMEOUT, MAXDUMPSIZE,
                        pcap_filter, filename+'.pcap')
            logger.info(cmd)
            pro = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            tcpdump_timeout = TCPDUMP_START_TIMEOUT  # in seconds
            while tcpdump_timeout > 0 and not is_tcpdump_running(pro):
                time.sleep(0.1)
                tcpdump_timeout -= 0.1
            if tcpdump_timeout < 0:
                raise TcpdumpTimeoutError()
            logger.info("Launch dumpcap in {:.2f}s".format(TCPDUMP_START_TIMEOUT-tcpdump_timeout))
            start = time.time()
            driver.get(url)
            if s:
                driver.get_screenshot_as_file(filename + '.png')
    except (ut.HardTimeoutException, TimeoutException):
        logger.warning("{} got timeout".format(url))
    except TcpdumpTimeoutError :
        logger.warning("Fail to launch tmpdump")
    except Exception as exc:
        logger.warning("Unknow error:{}".format(exc))
    finally:
        #post visit
        #Log loading time
        if 'driver' in locals():
            #avoid exception happens before driver is declared and assigned
            # which triggers exception here
            driver.quit()
        if 'start' in locals():
            #avoid exception happens before start is declared and assigned
            # which triggers exception here
            t = time.time() - start
            logger.info("Load {:.2f}s".format(t))
            with open(filename + '.time', 'w') as f:
                f.write("{:.4f}".format(t))
        time.sleep(GAP_BETWEEN_SITES)
        subprocess.call("killall dumpcap", shell=True)
        logger.info("Sleep {}s and capture killed, capture {} Bytes.".format(GAP_BETWEEN_SITES,os.path.getsize(filename+".pcap")))


        # filter ACKs and retransmission
        if os.path.exists(filename + '.pcap'):
            cmd = 'tshark -r ' + filename + '.pcap' + ' -Y "not(tcp.analysis.retransmission or tcp.len == 0 )" -w ' + filename + ".pcap.filtered"
            subprocess.call(cmd, shell=True)
            # remove raw pcapfile
            cmd = 'rm ' + filename + '.pcap'
            subprocess.call(cmd, shell=True)
        else:
            logger.warning("{} not captured for site {}".format(filename+'.pcap',url))

def pick_specific_webs(listdir):
    l = []
    with open(listdir,"r") as f:
        lines = f.readlines()
    for line in lines:
        line = int(line.split("\n")[0])
        l.append(line)
    return l


def main(args):
    global  batch_dump_dir
    start, end, m, s, b = args.start, args.end, args.m, args.s, args.b
    assert end>start
    torrc_path = args.torrc
    u = args.u
    l = args.l

    if u:
        WebListDir = unmon_list
    else:
        WebListDir = mon_list
    if args.w:
        WebListDir = args.w
    with open(WebListDir, 'r') as f:
        wlist = f.readlines()[start:end]
    websites = []
    for w in wlist:
        if "https" not in w:
             websites.append("https://www." + w.rstrip("\n"))
        else:
            websites.append(w.rstrip("\n"))
    if u and l:
        l_inds = pick_specific_webs(l)
    if l:
        assert len(l_inds) > 0
    batch_dump_dir = init_directories(args.mode,args.u)
    controller = TorController(torrc_path=torrc_path)
    if u:
        #crawl unmonitored webpages, restart Tor every m pages
        b = math.ceil((end-start)/m)
        for bb in range(b):
            with controller.launch():
                logger.info("Start Tor and sleep {}s".format(GAP_AFTER_LAUNCH))
                time.sleep(GAP_AFTER_LAUNCH)
                guards = controller.get_guard_ip()
                # print(guards)
                for mm in range(m):
                    i = bb * m + mm
                    if i >= len(websites):
                        break
                    website = websites[i]
                    wid = i + start
                    if l:
                        if wid not in l_inds:
                            continue
                    filename = join(batch_dump_dir, str(wid))
                    logger.info("{:d}: {}".format(wid, website))
                    # begin to crawl
                    crawl(website, filename, guards, s)
                logger.info("Finish batch #{}, sleep {}s.".format(bb, GAP_BETWEEN_BATCHES))
                time.sleep(GAP_BETWEEN_BATCHES)
    else:
        #crawl monitored webpages, round-robin fashion, restart Tor every m visits of a whole list
        for bb in range(b):
            with controller.launch():
                logger.info("Start Tor and sleep {}s".format(GAP_AFTER_LAUNCH))
                time.sleep(GAP_AFTER_LAUNCH)
                guards = controller.get_guard_ip()
                # print(guards)
                for wid, website in enumerate(websites):
                    wid = wid + start
                    for mm in range(m):
                        i = bb * m + mm
                        filename = join(batch_dump_dir, str(wid) + '-' + str(i) )
                        logger.info("{:d}-{:d}: {}".format(wid, i, website))
                        # begin to crawl
                        crawl(website, filename, guards, s)
                logger.info("Finish batch #{}, sleep {}s.".format(bb, GAP_BETWEEN_BATCHES))
                time.sleep(GAP_BETWEEN_BATCHES)

    # subprocess.call("sudo killall tor",shell=True)
    # logger.info("Tor killed!")


def sendmail(msg):
    cmd = "python3 "+SendMailPyDir+" -m "+msg
    subprocess.call(cmd,shell=True)
if __name__ == "__main__":
    global  batch_dump_dir
    try:
        args = parse_arguments()
        logger = config_logger(args.log)
        logger.info(args)
        display = Display(visible=0, size=(1000, 800))
        display.start()
        main(args)
        msg = "'Crawler Message:Crawl done at {}!'".format(datetime.datetime.now())
        sendmail(msg)
    except KeyboardInterrupt:
        sys.exit(-1)
    except Exception as e:
        msg = "'Crawler Message: An error occurred:\n{}'".format(e)
        sendmail(msg)
    finally:
        display.stop()
        if args.p:
            # parse raw traffic
            logger.info("Parsing the traffic...")
            if args.u:
                suffix = " -u"
            else:
                suffix = ""
            if args.mode == 'clean':
                # use sanity check
                cmd = "python3 parser.py " + batch_dump_dir + " -s -mode clean " + suffix
                subprocess.call(cmd, shell=True)

            elif args.mode == 'burst':
                cmd = "python3 parser.py " + batch_dump_dir + " -mode burst " + suffix
                subprocess.call(cmd, shell=True)
            else:
                pass
