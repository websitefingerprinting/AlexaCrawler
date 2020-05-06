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
import numpy as np

from pyvirtualdisplay import Display


timeout = 100
padding_time = 2
n0 = 0
Pardir = abspath(join(dirname(__file__), pardir))
DumpDir = join( Pardir , "AlexaCrawler/dump")
logger = logging.getLogger("tcpdump")

WebListDir = './global_top_500_without_timeout_in_first_200.txt'
src = "144.202.49.171"

def config_logger():
    # Set file
    log_file = sys.stdout
    ch = logging.StreamHandler(log_file)

    # Set logging format
    LOG_FORMAT = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
    ch.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(ch)

    # Set level format
    logger.setLevel(logging.INFO)

def init_directories():
    # Create a results dir if it doesn't exist yet
    if not os.path.exists(DumpDir):
        makedirs(DumpDir)

    # Define output directory
    timestamp = time.strftime('%m%d_%H%M')
    output_dir = join(DumpDir, 'batch_'+timestamp)
    makedirs(output_dir)

    return output_dir



def parse_arguments():

    parser = argparse.ArgumentParser(description='Crawl Alexa top websites and capture the traffic')
    parser.add_argument('-m',
                        type=int,
                        metavar='<Num of instances>',
                        default=50,
                        help='Number of instances for each website.')

    # Parse arguments
    args = parser.parse_args()
    return args

# def page_has_loaded(driver):
#   page_state = driver.execute_script('return document.readyState;')
#   return page_state == 'complete'
# def find_element_by(self, selector, timeout=100,
#                   find_by=By.CSS_SELECTOR):
#   """Wait until the element matching the selector appears or timeout."""
#   return WebDriverWait(self, timeout).until(
#       EC.presence_of_element_located((find_by, selector)))


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
    driver.set_page_load_timeout(timeout)
    # logger.info("Firefox launch for {:.2f}s".format(time.time()-start))
    return driver

def crawl(url, filename):

    display = Display(visible=0, size=(1000, 800))
    display.start()
    driver = get_driver()
    try:
        #start tcpdump
        cmd = "sudo tcpdump host \("+src+"\) and tcp and greater 77 -w " + filename
        pro = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        start = time.time()
        driver.get(url)
        # driver.get_screenshot_as_file(filename.split('.')[0]+'.png')
        err = 0
    except:
        logger.warning("{} got timeout".format(url))
        err = 1
    finally:
        driver.quit()
        display.stop()
        finish = time.time()
        t = finish-start
        #wait for padding traffic
        logger.info("Load {:.2f} + {:.2f}s".format(t, padding_time))
        time.sleep(padding_time)
        #stop tcpdump
        subprocess.call("sudo killall tcpdump",shell=True)
        return err, t




if __name__ == "__main__":


    args = parse_arguments()
    config_logger()
    m = args.m
    with open(WebListDir,'r') as f:
        wlist = f.readlines()

    mylist = [  0,   1,   2,   3,   5,   6,   8,   9,  10,  11,  12,  13,  14,
        15,  16,  17,  18,  19,  20,  21,  22,  24,  25,  27,  30,  32,
        33,  34,  35,  36,  37,  39,  40,  41,  42,  44,  45,  46,  48,
        49,  50,  51,  53,  54,  56,  59,  61,  62,  63,  64,  66,  67,
        70,  71,  72,  73,  75,  76,  78,  79,  82,  83,  88,  89,  90,
        93,  96,  97,  98,  99, 100, 101, 103, 104, 105, 106, 107, 110,
       111, 112, 113, 114, 115, 116, 118, 119, 120, 121, 123, 126, 130,
       131, 132, 134, 135, 136, 137, 138, 141, 142]
    websites = []
    for ind in mylist[n0:]:
        websites.append("https://www."+wlist[ind][:-1])

    batch_dump_dir = init_directories()


    for i in range(m):
        for wid,website in enumerate(websites):
            wid = wid + n0
            filename = join(batch_dump_dir, str(wid)+'-' + str(i) + '.pcap')
            logger.info("{:d}-{:d}: {}".format(wid,i,website))
            #begin to crawl
            err, loading_time = crawl(website, filename)
            if err:
                log = open(join(batch_dump_dir,'timeouts.txt'),'a+')
                log.write(website+': '+str(wid)+'-' + str(i)+'\n')
                log.close()
            f = open(join(batch_dump_dir,'loading_times.txt'),'a+')
            f.write("{}:{:.2f}\n".format(wid,loading_time))
            f.close()

    subprocess.call("sudo killall tor",shell=True)
    logger.info("Tor killed!")

