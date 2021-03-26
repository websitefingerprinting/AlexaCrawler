import os
import subprocess
import sys
sys.path.append('./gRPC')
import argparse
import numpy as np
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from tbselenium.tbdriver import TorBrowserDriver
from tbselenium.utils import start_xvfb, stop_xvfb
import utils as ut
from common import *
from torcontroller import *
import datetime
# from gRPC import client
from common import ConnError, HasCaptcha, Timeout, OtherError
import utils

# do remember to change this when use host or docker container to crawl
TBB_PATH = '/home/jgongac/tor-browser_en-US/'


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
    parser.add_argument('--open',
                        type=int,
                        default=0,
                        help='Crawl monitored sites or unmonitored sites (default:0, monitored).')
    parser.add_argument('--offset',
                        type=int,
                        default=200,
                        help='Index of first unmonsite in the crawllist, before that is monsites.')
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
    parser.add_argument('--headless',
                        action='store_false',
                        default=True,
                        help='Whether to use xvfb, false by default. (Make sure use customed headless tbb if true)')
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
        self.headless = args.headless
        self.driver = None
        self.controller = controller
        self.outputdir = outputdir
        self.wlist = wlist
        self.s = args.s
        self.picked_inds = picked_inds
        self.gRPCClient = gRPCClient

        self.last_crawl_time = time.time()

        if self.headless:
            logger.info("Run in headless mode.")
        else:
            logger.info("Run in non-headless mode.")

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
        if self.headless:
            # actually this is not working since set_option is deprecated which is used in tbselenium
            # instead, export MOZ_HEADLESS=1 is working
            headless = True
        else:
            headless = False
        caps = DesiredCapabilities().FIREFOX
        caps['pageLoadStrategy'] = 'normal'
        driver = TorBrowserDriver(tbb_path=TBB_PATH, tor_cfg=1, pref_dict=ffprefs, \
                                  tbb_logfile_path=self.tbblog, \
                                  socks_port=9050, capabilities=caps, headless=headless)
        driver.profile.set_preference("dom.webdriver.enabled", False)
        driver.profile.set_preference('useAutomationExtension', False)
        driver.profile.update_preferences()
        logger.info("profile dir: {}".format(driver.profile.profile_dir))
        driver.set_page_load_timeout(SOFT_VISIT_TIMEOUT)
        return driver

    def crawl(self, url, filename):
        """This method corresponds to a single loading for url"""
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
                        driver.clean_up_profile_dirs()
                    time.sleep(sleeptime)
                    sleeptime += 10
                    continue
                else:
                    raise OSError("Fail to launch browser after {} tries".format(tries))
            break

        # try to crawl website
        try:
            with ut.timeout(HARD_VISIT_TIMEOUT):
                # err = self.gRPCClient.sendRequest(turn_on=True, file_path='{}.cell'.format(filename))
                err = None
                if err != None:
                    logger.error(err)
                    # send a stop record request anyway
                    # self.gRPCClient.sendRequest(turn_on=False, file_path='')
                    return err
                time.sleep(1)
                logger.info("Start capturing.")
                self.last_crawl_time = time.time()
                driver.get(url)
                time.sleep(1)
                if self.s:
                    driver.get_screenshot_as_file(filename + '.png')
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
            t = time.time() - self.last_crawl_time
            driver.quit()
            # We don't care about the err here since if something goes wrong, we will find it next time send a True
            # Request in next loop
            time.sleep(CRAWLER_DWELL_TIME)
            # self.gRPCClient.sendRequest(turn_on=False, file_path='')
            logger.info("Stop capturing, save to {}.cell.".format(filename))
            logger.info("Loaded {:.2f}s".format(t))
            time.sleep(np.random.uniform(0, GAP_BETWEEN_SITES_MAX))

    def crawl_mon(self):
        """This method corresponds to one crawl task over all the monitored websites"""
        # crawl monitored webpages, round-robin fashion, restart Tor every m visits of a whole list
        for bb in range(self.batch):
            with self.controller.launch():
                should_restart_tor = False
                logger.info("Start Tor and sleep {}s".format(GAP_AFTER_LAUNCH))
                time.sleep(GAP_AFTER_LAUNCH)
                for wid, website in enumerate(self.wlist):
                    if should_restart_tor:
                        break
                    wid = wid + self.start
                    if (self.picked_inds is not None) and (wid not in self.picked_inds):
                        continue
                    for mm in range(self.m):
                        i = bb * self.m + mm
                        filename = join(self.outputdir, str(wid) + '-' + str(i))
                        logger.info("{:d}-{:d}: {}".format(wid, i, website))
                        err = self.crawl(website, filename)
                        if err is not None:
                            logger.error("Grpc server break down. Try to restart Tor.")
                            should_restart_tor = True
                            break
                        # change identity
                        self.controller.change_identity()

                logger.info("Finish batch #{}, sleep {}s.".format(bb + 1, GAP_BETWEEN_BATCHES))
                time.sleep(GAP_BETWEEN_BATCHES)

    def crawl_unmon(self):
        """This method corresponds to one crawl task over all the unmonitored websites"""
        # crawl unmonitored webpages, round-robin fashion, restart Tor every m sites each once
        should_restart_tor = False
        for raw_wid, website in enumerate(self.wlist):
            if raw_wid % self.m == 0 or should_restart_tor:
                logger.info("Restart Tor now.")
                self.controller.restart_tor()
                should_restart_tor = False
                time.sleep(GAP_BETWEEN_BATCHES)

            assert self.controller.tor_process is not None
            wid2list = raw_wid + self.start
            wid2file = raw_wid + self.start - self.offset
            if (self.picked_inds is not None) and (wid2list not in self.picked_inds):
                continue
            filename = join(self.outputdir, str(wid2file))
            logger.info("{:d}: {}".format(wid2list, website))
            err = self.crawl(website, filename)
            if err is not None:
                logger.error("Grpc server break down. Try to restart Tor.")
                should_restart_tor = True
            else:
                self.controller.change_identity()


    def clean_up(self):
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
    logger = utils.config_logger(args.crawllog)
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

    outputdir = utils.init_directories(args.mode, args.u)
    controller = TorController(torrc_path=args.torrc)

    gRPCClient = None
    wfcrawler = WFCrawler(args, websites, controller, gRPCClient, outputdir, picked_inds=l_inds)


    try:
        logger.info(args)
        if args.open:
            wfcrawler.crawl_unmon()
        else:
            wfcrawler.crawl_mon()
        ut.sendmail(args.who, "'Crawler Message:Crawl done at {}!'".format(datetime.datetime.now()))
    except KeyboardInterrupt:
        sys.exit(-1)
    except Exception as e:
        ut.sendmail(args.who, "'Crawler Message: An error occurred:\n{}'".format(e))
    finally:
        # clean up bad webs
        wfcrawler.clean_up()


if __name__ == "__main__":
    main()
