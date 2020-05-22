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


def config_logger():
    logger = logging.getLogger("tcpdump")
    # Set file
    log_file = sys.stdout
    ch = logging.StreamHandler(log_file)

    # Set logging format
    LOG_FORMAT = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
    ch.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(ch)

    # Set level format
    logger.setLevel(logging.INFO)
    return logger


def init_directories(mode):
    # Create a results dir if it doesn't exist yet
    if not os.path.exists(DumpDir):
        makedirs(DumpDir)

    # Define output directory
    timestamp = time.strftime('%m%d_%H%M%S')
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
                        help='Number of instances for each website in each batch to crawl.')
    parser.add_argument('-mode',
                        type=str,
                        required=True,
                        metavar='<parse mode>',
                        help='The type of dataset: clean, burst?.')
    parser.add_argument('-s',
                        action='store_false',
                        default=True,
                        help='Take a screenshot? (default:true)')
    parser.add_argument('-p',
                        action='store_false',
                        default=True,
                        help='Parse file after crawl? (default:true)')
    parser.add_argument('-timeout',
                        type=int,
                        default=None,
                        help='Change timeout value.')
    parser.add_argument('-torrc',
                        type=str,
                        default=None,
                        help='Torrc file path.')
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
            display = Display(visible=0, size=(1000, 800))
            display.start()
            driver = get_driver()
            src = ' or '.join(guards)
            # start tcpdump
            cmd = "tcpdump host \(" + src + "\) and tcp -i eth0 -w " + filename
            pro = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            start = time.time()
            driver.get(url)
            if s:
                driver.get_screenshot_as_file(filename.split('.')[0] + '.png')
            driver.quit()
            finish = time.time()
            t = finish - start
            # wait for padding traffic
            logger.info("Load {:.2f} + {:.2f}s".format(t, GAP_BETWEEN_SITES))
    except (ut.HardTimeoutException, TimeoutException):
        logger.warning("{} got timeout".format(url))
    except Exception as exc:
        logger.warning("Unknow error:{}".format(exc))
    finally:
        display.stop()
        time.sleep(GAP_BETWEEN_SITES)
        # stop tcpdump
        # pro.kill()
        subprocess.call("killall tcpdump", shell=True)
        logger.info("Kill tcpdump.")
        # filter ACKs and retransmission
        cmd = 'tshark -r ' + filename + ' -Y "not(tcp.analysis.retransmission or tcp.len == 0 )" -w ' + filename + ".filtered"
        subprocess.call(cmd, shell=True)


if __name__ == "__main__":
    args = parse_arguments()
    logger = config_logger()
    print(args)
    start, end, m, s, b = args.start, args.end, args.m, args.s, args.b
    torrc_path = args.torrc

    if args.timeout and args.timeout > 0:
        SOFT_VISIT_TIMEOUT = args.timeout

    with open(WebListDir, 'r') as f:
        wlist = f.readlines()[start:end]
    websites = ["https://www." + w[:-1] for w in wlist]

    batch_dump_dir = init_directories(args.mode)

    controller = TorController(torrc_path=torrc_path)
    for bb in range(b):
        with controller.launch():
            logger.info("Start Tor and sleep {}s".format(GAP_AFTER_LAUNCH))
            time.sleep(GAP_AFTER_LAUNCH)
            guards = controller.get_guard_ip()
            # print(guards)
            for mm in range(m):
                i = bb * m + mm
                for wid, website in enumerate(websites):
                    wid = wid + start
                    filename = join(batch_dump_dir, str(wid) + '-' + str(i) + '.pcap')
                    logger.info("{:d}-{:d}: {}".format(wid, i, website))
                    # begin to crawl
                    crawl(website, filename, guards, s)
            logger.info("Finish batch #{}, sleep {}s.".format(bb, GAP_BETWEEN_BATCHES))
            time.sleep(GAP_BETWEEN_BATCHES)

    # subprocess.call("sudo killall tor",shell=True)
    # logger.info("Tor killed!")
    if args.p:
        # parse raw traffic
        logger.info("Parsing the traffic...")
        if args.mode == 'clean':
            # use sanity check
            cmd = "python3 parser.py " + batch_dump_dir + " -s -m -mode clean"
            subprocess.call(cmd, shell=True)

        elif args.mode == 'burst':
            cmd = "python3 parser.py " + batch_dump_dir + " -m -mode burst"
            subprocess.call(cmd, shell=True)
        else:
            pass
