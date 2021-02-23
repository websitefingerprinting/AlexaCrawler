import subprocess
import os
import sys
from os import makedirs
import argparse
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from tbselenium.tbdriver import TorBrowserDriver
from tbselenium.utils import start_xvfb, stop_xvfb
import utils as ut
from common import *
from torcontroller import *
import logging
import math
import datetime
from gRPC import client
import glob

# do remember to change this when use host or docker container to crawl
TBB_PATH = '/home/docker/tor-browser_en-US/'


def config_logger(log_file):
    logger = logging.getLogger("crawler")
    # Set logging format
    LOG_FORMAT = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
    # Set file
    ch1 = logging.StreamHandler(sys.stdout)
    ch1.setFormatter(logging.Formatter(LOG_FORMAT))
    ch1.setLevel(logging.INFO)
    logger.addHandler(ch1)

    if log_file is not None:
        pardir = os.path.split(log_file)[0]
        f = open(log_file, "w")
        f.close()
        if not os.path.exists(pardir):
            os.makedirs(pardir)
        ch2 = logging.FileHandler(log_file)
        ch2.setFormatter(logging.Formatter(LOG_FORMAT))
        ch2.setLevel(logging.DEBUG)
        logger.addHandler(ch2)
    logger.setLevel(logging.INFO)
    return logger


def init_directories(mode, u):
    # Create a results dir if it doesn't exist yet
    if not os.path.exists(DumpDir):
        makedirs(DumpDir)

    # Define output directory
    timestamp = time.strftime('%m%d_%H%M%S')
    if u:
        output_dir = join(DumpDir, 'u' + mode + '_' + timestamp)
    else:
        output_dir = join(DumpDir, mode + '_' + timestamp)
    makedirs(output_dir)

    return output_dir


def parse_arguments():
    parser = argparse.ArgumentParser(description='Crawl Alexa top websites and capture the traffic')
    parser.add_argument('--start',
                        type=int,
                        metavar='<start ind>',
                        default=0,
                        help='Start from which site in the list (include this ind).')
    parser.add_argument('--end',
                        type=int,
                        metavar='<end ind>',
                        default=50,
                        help='End to which site in the list (exclude this ind).')
    parser.add_argument('--batch', '-b',
                        type=int,
                        metavar='<Num of batches>',
                        default=5,
                        help='Crawl batches, Tor restarts at each batch.')
    parser.add_argument('-m',
                        type=int,
                        metavar='<Num of instances in each batch>',
                        default=5,
                        help='Number of instances for each website in each batch to crawl. In unmon mode, for every m instances, restart tor.')
    parser.add_argument('--torrc',
                        type=str,
                        default=None,
                        help='Torrc file path.')
    parser.add_argument('--mode',
                        type=str,
                        required=True,
                        metavar='<parse mode>',
                        help='The type of dataset: clean, burst?.')
    parser.add_argument('--device',
                        type=str,
                        default='eth0',
                        help='Network device name.')
    parser.add_argument('-s',
                        action='store_true',
                        default=False,
                        help='Take a screenshot? (default:False)')
    parser.add_argument('-p',
                        action='store_false',
                        default=True,
                        help='Parse file after crawl? (default:true)')
    parser.add_argument('-c',
                        action='store_true',
                        default=False,
                        help='Whether use dumpcap to capture network traffic? (default: is false)')
    parser.add_argument('-w',
                        type=str,
                        default=None,
                        help='Self provided web list.')
    parser.add_argument('-u',
                        action='store_true',
                        default=False,
                        help='If crawl mon or umon sites (default is mon)')
    parser.add_argument('-l',
                        type=str,
                        default=None,
                        help='Crawl specific sites, given a list')
    parser.add_argument('--crawllog',
                        type=str,
                        metavar='<log path>',
                        default=None,
                        help='path to the crawler log file. It will print to stdout by default.')
    parser.add_argument('--tbblog',
                        type=str,
                        metavar='<log path>',
                        default=None,
                        help='path to the tbb log file. It will print to stdout by default.')
    parser.add_argument('--who',
                        type=str,
                        metavar='<email sender>',
                        default='',
                        help='The name of the sender that will send an email after finishing crawling.')
    # Parse arguments
    args = parser.parse_args()
    return args


class WFCrawler:
    def __init__(self, args, wlist, controller, gRPCClient, outputdir, picked_inds=None):
        self.batch = args.batch
        self.batch = args.batch
        self.m = args.m
        self.start = args.start
        self.tbblog = args.tbblog
        self.driver = None
        self.controller = controller
        self.outputdir = outputdir
        self.wlist = wlist
        self.s = args.s
        self.picked_inds = picked_inds
        self.gRPCClient = gRPCClient

    def write_to_badlist(self, filename, url, reason):
        with open(join(self.outputdir, 'bad.list'), 'a+') as f:
            f.write(filename + '\t' + url + '\t' + reason + '\n')

    def get_driver(self):
        # profile = webdriver.FirefoxProfile()
        # profile.set_preference("network.proxy.type", 1)
        # profile.set_preference("network.proxy.socks", "127.0.0.1")
        # profile.set_preference("network.proxy.socks_port", 9050)
        # profile.set_preference("network.proxy.socks_version", 5)
        # profile.set_preference("browser.cache.disk.enable", False)
        # profile.set_preference("browser.cache.memory.enable", False)
        # profile.set_preference("browser.cache.offline.enable", False)
        # profile.set_preference("network.http.use-cache", False)
        # profile.set_preference("network.http.pipelining.max - optimistic - requests", 5000)
        # profile.set_preference("network.http.pipelining.maxrequests", 15000)
        # profile.set_preference("network.http.pipelining", False)
        #
        # profile.update_preferences()
        # opts = Options()
        # opts.headless = True
        # driver = webdriver.Firefox(firefox_profile=profile, options=opts)
        ffprefs = {
            # "browser.cache.disk.enable":False,
            # "browser.cache.memory.enable":False,
            # "browser.cache.offline.enable":False,
            # "network.http.use-cache": False,
            # "network.http.pipelining.max-optimistic-requests": 5000,
            # "network.http.pipelining.maxrequests": 15000,
            # "network.http.pipelining": False
        }
        caps = DesiredCapabilities().FIREFOX
        caps['pageLoadStrategy'] = 'normal'
        driver = TorBrowserDriver(tbb_path=TBB_PATH, tor_cfg=1, pref_dict=ffprefs, \
                                  tbb_logfile_path=self.tbblog, \
                                  socks_port=9050, capabilities=caps)
        driver.set_page_load_timeout(SOFT_VISIT_TIMEOUT)
        return driver

    def crawl(self, url, filename):
        # try to launch driver
        tries = 3
        sleeptime = 5
        for i in range(tries):
            pid = None
            try:
                # with ut.timeout(BROWSER_LAUNCH_TIMEOUT):
                driver = self.get_driver()
                pid = driver.service.process.pid
            except Exception as exc:
                if i < tries - 1:
                    logger.error("Fail to launch browser, retry {} times, Err msg:{}".format(tries - (i + 1), exc))
                    if pid:
                        logger.info("Kill remaining browser process")
                        ut.kill_all_children(pid)
                    time.sleep(sleeptime)
                    sleeptime += 10
                    continue
                else:
                    raise OSError("Fail to launch browser after {} tries".format(tries))
            break

        # try to crawl website
        try:
            with ut.timeout(HARD_VISIT_TIMEOUT):
                err = self.gRPCClient.sendRequest(turn_on='True', file_path='{}.cell'.format(filename))
                if err != None:
                    logger.error(err)
                    return
                time.sleep(0.05)  # the golang process scan the switch file every 50 millisecond
                logger.info("Start capturing.")
                start = time.time()
                driver.get(url)
                if self.s:
                    driver.get_screenshot_as_file(filename + '.png')
                time.sleep(1)
                if ut.check_conn_error(driver):
                    self.write_to_badlist(filename + '.cell', url, "ConnError")
                elif ut.check_captcha(driver.page_source.strip().lower()):
                    self.write_to_badlist(filename + '.cell', url, "HasCaptcha")
        except (ut.HardTimeoutException, TimeoutException):
            logger.warning("{} got timeout".format(url))
            self.write_to_badlist(filename + '.cell', url, "Timeout")
        except Exception as exc:
            logger.warning("Unknow error:{}".format(exc))
            self.write_to_badlist(filename + '.cell', url, "OtherError")
        finally:
            t = time.time() - start
            try:
                # kill firefox
                with ut.timeout(10):
                    driver.quit()
                    logger.info("Firefox quit successfully.")
            except Exception as exc:
                # if driver.quit() cann't kill, use pid instead
                logger.error("Error when kill firefox: {}".format(exc))
                ut.kill_all_children(pid)
                subprocess.call('rm -rf /tmp/*',
                                shell=True)  # since we use pid to kill firefox, we should clean up tmp too
                logger.info("Firefox killed by pid.")
            # We don't care about the err here since if something goes wrong, we will find it next time send a True
            # Request in next loop
            self.gRPCClient.sendRequest(turn_on='False', file_path='')
            logger.info("Stop capturing, save to {}.cell.".format(filename))
            logger.info("Loaded {:.2f}s".format(t))
            time.sleep(GAP_BETWEEN_SITES)

    def crawl_task(self):
        # crawl monitored webpages, round-robin fashion, restart Tor every m visits of a whole list
        for bb in range(self.batch):
            with self.controller.launch():
                logger.info("Start Tor and sleep {}s".format(GAP_AFTER_LAUNCH))
                time.sleep(GAP_AFTER_LAUNCH)
                for wid, website in enumerate(self.wlist):
                    wid = wid + self.start
                    if (self.picked_inds is not None) and (wid not in self.picked_inds):
                        continue
                    for mm in range(self.m):
                        i = bb * self.m + mm
                        filename = join(self.outputdir, str(wid) + '-' + str(i))
                        logger.info("{:d}-{:d}: {}".format(wid, i, website))
                        self.crawl(website, filename)
                        # change identity
                        self.controller.change_identity()
                logger.info("Finish batch #{}, sleep {}s.".format(bb, GAP_BETWEEN_BATCHES))
                time.sleep(GAP_BETWEEN_BATCHES)

    def clean_up(self):
        ConnError = 1
        HasCaptcha = 1
        Timeout = 1
        OtherError = 1

        err_type_cnt = {'ConnError': 0,
                        'HasCptcha': 0,
                        'Timeout': 0,
                        'OtherError': 0, }

        bad_list = set()
        if os.path.exists(join(self.outputdir, 'bad.list')):
            with open(join(self.outputdir, 'bad.list'), 'r') as f:
                tmp = f.readlines()
                for entry in tmp:
                    entry = entry.rstrip('\n').split('\t')
                    bad_list.add((entry[0], entry[1], entry[2]))
        error_num = len(bad_list)
        logger.info("Found {} bad (including Timeout) loadings.".format(error_num))
        removed_list = set()
        for bad_item in bad_list:
            w, url, reason = bad_item[0], bad_item[1], bad_item[2]
            if w in removed_list:
                continue
            else:
                removed_list.add(w)
            if reason == 'ConnError' and ConnError:
                err_type_cnt['ConnError'] += 1
                subprocess.call("rm " + w, shell=True)
            elif reason == 'HasCaptcha' and HasCaptcha:
                err_type_cnt['HasCptcha'] += 1
                subprocess.call("rm " + w, shell=True)
            elif reason == 'Timeout' and Timeout:
                err_type_cnt['Timeout'] += 1
                subprocess.call("rm " + w, shell=True)
            elif reason == 'OtherError' and OtherError:
                err_type_cnt['OtherError'] += 1
                subprocess.call("rm " + w, shell=True)
        logger.info(err_type_cnt)


def main():
    args = parse_arguments()
    assert args.end > args.start

    if args.u:
        web_list_dir = unmon_list
    else:
        web_list_dir = mon_list
    if args.w:
        web_list_dir = args.w
    with open(web_list_dir, 'r') as f:
        wlist = f.readlines()[args.start: args.end]
    websites = []
    for w in wlist:
        if "https" not in w:
            websites.append("https://" + w.rstrip("\n"))
        else:
            websites.append(w.rstrip("\n"))
    assert len(websites) > 0
    if args.l:
        l_inds = ut.pick_specific_webs(args.l)
        assert len(l_inds) > 0
    else:
        l_inds = None

    outputdir = init_directories(args.mode, args.u)
    controller = TorController(torrc_path=args.torrc)

    gRPCClient = client.GRPCClient(cm.gRPCAddr)
    wfcrawler = WFCrawler(args, websites, controller, gRPCClient, outputdir, picked_inds=l_inds)

    xvfb_display = start_xvfb(1280, 800)
    try:
        logger = config_logger(args.crawllog)
        logger.info(args)
        wfcrawler.crawl_task()
        ut.sendmail(args.who, "'Crawler Message:Crawl done at {}!'".format(datetime.datetime.now()))
    except KeyboardInterrupt:
        sys.exit(-1)
    except Exception as e:
        ut.sendmail(args.who, "'Crawler Message: An error occurred:\n{}'".format(e))
    finally:
        stop_xvfb(xvfb_display)
        # clean up bad webs
        wfcrawler.clean_up()


if __name__ == "__main__":
    main()