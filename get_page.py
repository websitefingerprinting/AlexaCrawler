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
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import numpy as np

from pyvirtualdisplay import Display



Pardir = abspath(join(dirname(__file__), pardir))
DumpDir = join( Pardir , "AlexaCrawler/test")
logger = logging.getLogger("tcpdump")

WebListDir = './web100_without_timeout.txt'
# src_ip = "10.79.119.9"

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
    output_dir = DumpDir
    return output_dir
# class TimeoutError(Exception):
# 	pass

# def _sig_alarm(sig, tb):
# 	raise TimeoutError("timeout")


def parse_arguments():

	parser = argparse.ArgumentParser(description='Crawl Alexa top websites and capture the traffic')

	parser.add_argument('-i',
						type=int,
						metavar='<ith page>',
						default=0,
						help='i-th page')

	# Parse arguments
	args = parser.parse_args()
	return args

def page_has_loaded(driver):
	page_state = driver.execute_script('return document.readyState;')
	return page_state == 'complete'

def crawl(url,  timeout = 100):
	profile = webdriver.FirefoxProfile()
	profile.DEFAULT_PREFERENCES['frozen']['javascript.enabled'] = False
	profile.set_preference("network.proxy.type", 1)
	profile.set_preference("network.proxy.socks", "127.0.0.1")
	profile.set_preference("network.proxy.socks_port", 9050)
	profile.set_preference("network.proxy.socks_version", 5)
	profile.update_preferences()
	driver = webdriver.Firefox(firefox_profile=profile)
	driver.set_page_load_timeout(timeout)
   
	try:
		logger.info("Start!")
		lasttime = time.time()
		driver.get(url)
		logger.info("Finish!")
		logger.info("Internal: {:2f}".format(time.time()- lasttime))
		driver.quit()
		return 0
	except:
		logger.warning("{} got timeout".format(url))
		logger.info("Finish with error!")
		driver.quit()
		return 1
	return 1




if __name__ == "__main__":

	display = Display(visible=0, size=(800, 600))
	display.start()

	args = parse_arguments()
	config_logger()
	with open(WebListDir,'r') as f:
		w = f.readlines()[args.i]
	website = "https://www."+w

	batch_dump_dir = init_directories()


	# tor_proc = subprocess.Popen("tor -f "+ join(Pardir, 'tor-config', "obfs4-client"), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)		
	# time.sleep(20)

	tag = time.strftime('%H%M%S')
	filename = join(batch_dump_dir, str(args.i)+'-' +tag+ '.pcap')
	logger.info("{:d}-{}: {}".format(args.i, tag ,website))
	# cmd = "sudo tcpdump host "+ src_ip+ " and \(13.75.95.89\) and tcp and greater 67 -w " + filename
	cmd = "sudo tcpdump host \(13.75.95.89\) and tcp and greater 67 -w " + filename
	#start tcpdump
	pro = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	time.sleep(1)
	#begin to crawl
	now = time.time()
	crawl(website)
	finish = time.time()
	#wait for padding traffic
	padding_time = 10
	time.sleep(padding_time)
	logger.info("Load {:.4f} + {:.4f}s".format(finish-now, padding_time))
	#stop tcpdump
	subprocess.call("sudo killall tcpdump",shell=True)
			

	subprocess.call("sudo killall tor",shell=True)
	logger.info("Tor killed!")

