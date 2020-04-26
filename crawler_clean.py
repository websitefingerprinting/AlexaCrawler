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
from stem import CircStatus
from stem.control import Controller
from pyvirtualdisplay import Display


timeout = 60
padding_time = 5

Pardir = abspath(join(dirname(__file__), pardir))
DumpDir = join( Pardir , "AlexaCrawler/dump")
logger = logging.getLogger("tcpdump")

WebListDir = './sites.txt'


def get_guard_ip():
    addresses = {}
    with Controller.from_port(port = 9051) as controller:
        controller.authenticate()

        for circ in sorted(controller.get_circuits()):
            if circ.status != CircStatus.BUILT:
                continue
            fingerprint, nickname = circ.path[0]
            desc = controller.get_network_status(fingerprint, None)
            address = desc.address if desc else None
            if address:
                addresses.add(address)

    return list(addresses)

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
    output_dir = join(DumpDir, 'clean_'+timestamp)
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
    parser.add_argument('-m',
                        type=int,
                        metavar='<Num of instances>',
                        default=15,
                        help='Number of instances for each website.')
    parser.add_argument('-s',
                        action='store_true', 
                        default=False,
                        help='Take a screenshot?')

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

def crawl(url, filename, guards, s):
    display = Display(visible=0, size=(1000, 800))
    display.start()
    driver = get_driver()
    src = ' or '.join(guards)
    try:
        #start tcpdump
        cmd = "sudo tcpdump host \("+src+"\) and tcp -i eth0 -w " + filename
        print(cmd)
        pro = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        start = time.time()
        driver.get(url)
        if s:
            driver.get_screenshot_as_file(join("./screenshots",filename.split('.')[0]+'.png'))
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
        #filter ACKs and retransmission
        cmd = 'tshark -r '+ filename +' -Y "not(tcp.analysis.retransmission or tcp.len == 0 )" -w ' + filename+".filtered"
        subprocess.call(cmd, shell= True)
        return err, t




if __name__ == "__main__":
    args = parse_arguments()
    config_logger()
    n0, n, m, s= args.n0, args.n, args.m, args.s
    with open(WebListDir,'r') as f:
        wlist = f.readlines()[n0:n0+n]
    websites = ["https://www."+w[:-1] for w in wlist]

    batch_dump_dir = init_directories()

    for i in range(m):
        guards = get_guard_ip()
        print(guards)
        for wid,website in enumerate(websites):
            wid = wid + n0
            filename = join(batch_dump_dir, str(wid)+'-' + str(i) + '.pcap')
            logger.info("{:d}-{:d}: {}".format(wid,i,website))
            #begin to crawl
            err, loading_time = crawl(website, filename, guards, s)
            if err:
                log = open(join(batch_dump_dir,'timeouts.txt'),'a+')
                log.write(website+': '+str(wid)+'-' + str(i)+'\n')
                log.close()
            f = open(join(batch_dump_dir,'loading_times.txt'),'a+')
            f.write("{}:{:.2f}\n".format(wid,loading_time))
            f.close()

    subprocess.call("sudo killall tor",shell=True)
    logger.info("Tor killed!")

