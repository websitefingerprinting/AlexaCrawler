import os
import subprocess
import sys

import common

sys.path.append('./gRPC')
import argparse
import tempfile
import numpy as np
import utils as ut
from common import *
from torcontroller import *
import datetime
from gRPC import client
from common import ConnError, HasCaptcha, Timeout, OtherError
import utils

# do remember to change this when use host or docker container to crawl
TBB_PATH = '/home/docker/tor-browser_en-US/'


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
                        help='Number of instances for each website in each batch to crawl. In unmon mode, for every m '
                             'instances, restart tor.')
    parser.add_argument('--open',
                        type=int,
                        default=0,
                        help='Crawl monitored sites or unmonitored sites (default:0, monitored).')
    parser.add_argument('--offset',
                        type=int,
                        default=200,
                        help='Index of first unmonsite in the crawllist, before that is monsites.')
    # parser.add_argument('--torrc',
    #                     type=str,
    #                     default=None,
    #                     help='Torrc file path.')
    parser.add_argument('--mode',
                        type=str,
                        required=True,
                        metavar='<parse mode>',
                        help='The type of dataset: clean, burst?.')
    parser.add_argument('-s',
                        action='store_true',
                        default=False,
                        help='Take a screenshot? (default:False)')
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
    def __init__(self, args, wlist, gRPCClient, outputdir, picked_inds=None):
        self.batch = args.batch
        self.m = args.m
        self.offset = args.offset
        self.start = args.start
        self.end = args.end
        self.headless = args.headless
        self.driver = None
        self.outputdir = outputdir
        self.wlist = wlist
        self.s = args.s
        self.picked_inds = picked_inds
        self.gRPCClient = gRPCClient
        self.tbblog = args.tbblog
        self.last_crawl_time = time.time()

        if self.headless:
            logger.info("Run in headless mode.")
        else:
            logger.info("Run in non-headless mode.")

        self.tmpdir = tempfile.mkdtemp()
        dst = utils.make_tb_copy(self.tmpdir, TBB_PATH)
        self.tbbdir = dst

        # from https://github.com/pylls/padding-machines-for-tor/blob/master/collect-traces/client/exp/collect.py
        logger.info("Two warm up visits for fresh consensus and whatnot update checks")
        err = self.warm_up("https://duckduckgo.com")
        err = self.warm_up("https://duckduckgo.com")
        if err is not None:
            logger.error("Fail to launch TBB:{}".format(err))
            raise ConnectionError
        else:
            logger.info("No error in warm up")
        # clean up two warm up logs
        pt_log_dir = join(self.tbbdir, "Browser/TorBrowser/Data/Tor/pt_state/obfs4proxy.log")
        subprocess.call("rm {}".format(pt_log_dir), shell=True)

    def write_to_badlist(self, filename, url, reason):
        with open(join(self.outputdir, 'bad.list'), 'a+') as f:
            f.write(filename + '\t' + url + '\t' + reason + '\n')

    def warm_up(self, url):
        """test crawl function"""
        err = None
        try:
            with ut.timeout(HARD_VISIT_TIMEOUT):
                tb = os.path.join(self.tbbdir, "Browser", "firefox")
                if self.headless:
                    cmd = f"timeout -k 2 {str(cm.SOFT_VISIT_TIMEOUT)} {tb} --headless {url}"
                else:
                    cmd = f"timeout -k 2 {str(cm.SOFT_VISIT_TIMEOUT)} {tb} {url}"
                if self.tbblog:
                    cmd += " >> {}".format(self.tbblog)
                logger.info(f"{cmd}")
                subprocess.check_call(cmd, shell=True)
        except Exception as exc:
            logger.warning("Unknow error:{}".format(exc))
            err = exc
        finally:
            time.sleep(np.random.uniform(0, GAP_BETWEEN_SITES_MAX))
        return err

    def crawl(self, url, filename):
        """This method corresponds to a single loading for url"""
        # try to crawl website
        tb = utils.make_tb_copy(self.tmpdir, self.tbbdir)
        try:
            with ut.timeout(HARD_VISIT_TIMEOUT):
                # err = self.gRPCClient.sendRequest(turn_on=True, file_path='{}.cell'.format(filename))
                # if err is not None:
                #     logger.error(err)
                #     # send a stop record request anyway
                #     self.gRPCClient.sendRequest(turn_on=False, file_path='')
                #     return err
                # time.sleep(1)
                tb_firefox = os.path.join(tb, "Browser", "firefox")
                url = url.replace("'", "\\'")
                url = url.replace(";", "\;")
                logger.info("Start capturing.")
                self.last_crawl_time = time.time()
                if self.headless:
                    cmd = f"timeout -k 2 {str(cm.SOFT_VISIT_TIMEOUT)} {tb_firefox} --headless {url}"
                else:
                    cmd = f"timeout -k 2 {str(cm.SOFT_VISIT_TIMEOUT)} {tb_firefox} {url}"
                if self.tbblog:
                    cmd += " >> {}".format(self.tbblog)
                logger.info(f"{cmd}")
                subprocess.check_call(cmd, shell=True)
        except subprocess.CalledProcessError as exc:
            logger.error(
                "Got error in cmd, return code:{}, cmd:{}, output:{}".format(exc.returncode, exc.cmd, exc.output))
            self.write_to_badlist(filename + '.cell', url, "Timeout")
        except ut.HardTimeoutException:
            logger.warning("{} got timeout".format(url))
            self.write_to_badlist(filename + '.cell', url, "Timeout")
        except Exception as exc:
            logger.warning("Unknow error:{}".format(exc))
            self.write_to_badlist(filename + '.cell', url, "OtherError")
        finally:
            t = time.time() - self.last_crawl_time
            self.gRPCClient.sendRequest(turn_on=False, file_path='')
            logger.info("Stop capturing {}, save to {}.cell.".format(url, filename))
            logger.info("Loaded {:.2f}s".format(t))

            # copy log from TBB dir to result dir
            pt_log_dir = join(tb, "Browser/TorBrowser/Data/Tor/pt_state/obfs4proxy.log")
            subprocess.call("cp {} {}.cell".format(pt_log_dir, filename), shell=True)
            subprocess.call("chmod -R 777 {}.cell".format(filename), shell=True)

            # clean our TB copy
            shutil.rmtree(tb)
            time.sleep(np.random.uniform(0, GAP_BETWEEN_SITES_MAX))
            time.sleep(CRAWLER_DWELL_TIME)

    def crawl_mon(self):
        """This method corresponds to one crawl task over all the monitored websites"""
        # crawl monitored webpages, round-robin fashion
        for bb in range(self.batch):
            for wid, website in enumerate(self.wlist):
                wid = wid + self.start
                if (self.picked_inds is not None) and (wid not in self.picked_inds):
                    continue
                for mm in range(self.m):
                    i = bb * self.m + mm
                    filename = join(self.outputdir, str(wid) + '-' + str(i))
                    logger.info("{:d}-{:d}: {}".format(wid, i, website))
                    self.crawl(website, filename)
            logger.info("Finish batch #{}, sleep {}s.".format(bb + 1, GAP_BETWEEN_BATCHES))
            time.sleep(GAP_BETWEEN_BATCHES)

    def crawl_unmon(self):
        """This method corresponds to one crawl task over all the unmonitored websites"""
        # crawl unmonitored webpages, round-robin fashion
        for raw_wid, website in enumerate(self.wlist):
            wid2list = raw_wid + self.start
            wid2file = raw_wid + self.start - self.offset
            if (self.picked_inds is not None) and (wid2list not in self.picked_inds):
                continue
            filename = join(self.outputdir, str(wid2file))
            logger.info("{:d}: {}".format(wid2list, website))
            self.crawl(website, filename)

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

    wfcrawler = None
    try:
        gRPCClient = client.GRPCClient(cm.gRPCAddr)
        wfcrawler = WFCrawler(args, websites, gRPCClient, outputdir, picked_inds=l_inds)
        logger.info(args)
        # give bridge some time since several dockers launch at nearly the same time.
        time.sleep(common.GAP_AFTER_LAUNCH)
        if args.open:
            wfcrawler.crawl_unmon()
        else:
            wfcrawler.crawl_mon()
        ut.sendmail(args.who, "'Crawler Message:Crawl done at {}!'".format(datetime.datetime.now()))
    except KeyboardInterrupt:
        sys.exit(-1)
    except Exception as e:
        logger.error(e)
        ut.sendmail(args.who, "'An error occurred'")
    finally:
        # clean up bad webs
        if wfcrawler:
            wfcrawler.clean_up()
            shutil.rmtree(wfcrawler.tmpdir)


if __name__ == "__main__":
    main()
