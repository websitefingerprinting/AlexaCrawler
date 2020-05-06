import subprocess
import os
from os import makedirs
from os.path import join, abspath, dirname, pardir
import time
import logging
import sys
import argparse
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import numpy as np
from stem import CircStatus
from stem.control import Controller
from pyvirtualdisplay import Display
import utils as ut
from common import *
from torcontroller import *

logger = logging.getLogger("tcpdump")


def init_directories(mode):
    # Create a results dir if it doesn't exist yet
    if not os.path.exists(DumpDir):
        makedirs(DumpDir)

    # Define output directory
    timestamp = time.strftime('%m%d_%H%M%S')
    output_dir = join(DumpDir, mode+'_'+timestamp)
    makedirs(output_dir)

    return output_dir



def parse_arguments():

    parser = argparse.ArgumentParser(description='Crawl Alexa top websites and capture the traffic')

    parser.add_argument('-n',
                        type=int,
                        metavar='<Top N websites>',
                        default=50,
                        help='Top N websites to be crawled.')
    parser.add_argument('-n0',
                        type=int,
                        metavar='<start page>',
                        default=0,
                        help='Crawl n0 to n0+n-1 webpages')
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
                        type = int,
                        default=None,
                        help='Change timeout value.')
    parser.add_argument('-torrc',
                        type = str,
                        default=None,
                        help='Torrc file path.')
    # Parse arguments
    args = parser.parse_args()
    return args


def get_driver():
    start = time.time()
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
    # logger.info("Firefox launch for {:.2f}s".format(time.time()-start))
    return driver

def crawl(url, filename, guards, s):
    try:
        with ut.timeout(HARD_VISIT_TIMEOUT):
            display = Display(visible=0, size=(1000, 800))
            display.start()
            driver = get_driver()
            src = ' or '.join(guards)
            #start tcpdump
            cmd = "sudo tcpdump host \("+src+"\) and tcp -i eth0 -w " + filename
            print(cmd)
            pro = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            start = time.time()
            driver.get(url)
            if s:
                driver.get_screenshot_as_file(filename.split('.')[0]+'.png')
            driver.quit()
            finish = time.time()
            t = finish-start
            #wait for padding traffic
            logger.info("Load {:.2f} + {:.2f}s".format(t, padding_time))
    except (ut.HardTimeoutException, TimeoutException):
        logger.warning("{} got timeout".format(url))
    except Exception as exc:
        logger.warning("Unknow error:{}".format(exc))
    finally:
        display.stop()
        time.sleep(padding_time)
        #stop tcpdump
        subprocess.call("sudo killall tcpdump",shell=True)
        #filter ACKs and retransmission
        cmd = 'tshark -r '+ filename +' -Y "not(tcp.analysis.retransmission or tcp.len == 0 )" -w ' + filename+".filtered"
        subprocess.call(cmd, shell= True)


if __name__ == "__main__":
    args = parse_arguments()
    ut.config_logger()
    print(args)
    n0, n, m, s, b = args.n0, args.n, args.m, args.s, args.b
    torrc_path = arg.torrc
    if args.timeout and args.timeout > 0:
        SOFT_VISIT_TIMEOUT = args.timeout

    with open(WebListDir,'r') as f:
        wlist = f.readlines()[n0:n0+n]
    websites = ["https://www."+w[:-1] for w in wlist]

    batch_dump_dir = init_directories(args.mode)

    controller = TorController(torrc_path=torrc_path)
    for bb in range(b)
        with controller.launch():
            guards = controller.get_guard_ip()         
            # print(guards)
            for mm in range(m):
                i = bb*m + mm
                for wid,website in enumerate(websites):
                    wid = wid + n0
                    filename = join(batch_dump_dir, str(wid)+'-' + str(i) + '.pcap')
                    logger.info("{:d}-{:d}: {}".format(wid,i,website))
                    #begin to crawl
                    crawl(website, filename, guards, s)
            time.sleep(gap_between_batches)

    # subprocess.call("sudo killall tor",shell=True)
    # logger.info("Tor killed!")

    #parse raw traffic
    # logger.info("Parsing the traffic...")
    # cmd = "python3 parser.py "+batch_dump_dir + " -m -mode "+ args.mode
    # subprocess.call(cmd, shell = True) 
