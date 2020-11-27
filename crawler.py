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
import glob


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
    if args.u:
        output_dir = join(DumpDir, 'u' + mode + '_' + timestamp)
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
    parser.add_argument('-device',
                        type=str,
                        default='eth0',
                        help='Network device name.')
    parser.add_argument('-s',
                        action='store_true',
                        default=False,
                        help='Take a screenshot? (default:False)')
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
    parser.add_argument('-c',
                        action='store_true',
                        default=False,
                        help='Whether use dumpcap to capture network traffic? (default: is false)')
    parser.add_argument('-w',
                        type=str,
                        default=None,
                        help='Self provided web list.')
    parser.add_argument('-l',
                        type=str,
                        default=None,
                        help='Crawl specific unmon sites, given a list')
    parser.add_argument('-crawllog',
                        type=str,
                        metavar='<log path>',
                        default=None,
                        help='path to the crawler log file. It will print to stdout by default.')
    parser.add_argument('-tbblog',
                        type=str,
                        metavar='<log path>',
                        default=None,
                        help='path to the tbb log file. It will print to stdout by default.')
    # Parse arguments
    args = parser.parse_args()
    return args


def get_driver():
    global tbblog
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
    driver = TorBrowserDriver(tbb_path=cm.TBB_PATH, tor_cfg=1, pref_dict=ffprefs, \
                              tbb_logfile_path=tbblog,\
                              socks_port=9050, capabilities=caps)
    driver.set_page_load_timeout(SOFT_VISIT_TIMEOUT)
    return driver


def write_to_badlist(filename, reason):
    global batch_dump_dir
    with open(join(batch_dump_dir, 'bad.list'), 'a+') as f:
        f.write(filename + '\t' + reason + '\n')


def clean_up(take_screenshot):
    global batch_dump_dir
    ConnError = 1
    HasCaptcha = 1
    Timeout = 1
    OtherError = 1
    NoScreenshot = 1

    bad_list = set()
    if os.path.exists(join(batch_dump_dir, 'bad.list')):
        with open(join(batch_dump_dir, 'bad.list'), 'r') as f:
            tmp = f.readlines()
            for entry in tmp:
                entry = entry.rstrip('\n').split('\t')
                bad_list.add((entry[0], entry[1]))
    error_num = len(bad_list)
    if take_screenshot:
        trace_list = glob.glob(join(batch_dump_dir, "*.cell"))
        for trace in trace_list:
            screenshot_filename = trace.replace(".cell", ".png")
            if not os.path.exists(screenshot_filename):
                bad_list.add((trace, "NoScreenshot"))

    no_screenshot_num = len(bad_list) - error_num
    logger.info("Found {} (error) + {} (screenshot) bad loadings.".format(error_num, no_screenshot_num))
    removed_list = set()
    for bad_item in bad_list:
        w, reason = bad_item[0], bad_item[1]
        if w in removed_list:
            continue
        else:
            removed_list.add(w)
        if reason == 'ConnError' and ConnError:
            subprocess.call("rm " + w, shell=True)
        elif reason == 'HasCaptcha' and HasCaptcha:
            subprocess.call("rm " + w, shell=True)
        elif reason == 'Timeout' and Timeout:
            subprocess.call("rm " + w, shell=True)
        elif reason == 'OtherError' and OtherError:
            subprocess.call("rm " + w, shell=True)
        elif reason == 'NoScreenshot' and NoScreenshot:
            subprocess.call("rm " + w, shell=True)
        else:
            logger.warning("Unknown reason:{}".format(reason))


def crawl_without_cap(url, filename, s):
    # try to launch driver
    tries = 5
    for i in range(tries):
        try:
            pid = None
            # with ut.timeout(BROWSER_LAUNCH_TIMEOUT):
            driver = get_driver()
            pid = driver.service.process.pid
        except Exception as exc:
            if i < tries - 1:
                logger.error("Fail to launch browser, retry {} times, Err msg:{}".format(tries - (i + 1), exc))
                if pid:
                    logger.info("Kill remaining browser process")
                    ut.kill_all_children(pid)
                time.sleep(5)
                continue
            else:
                raise OSError("Fail to launch browser after {} tries".format(tries))
        break

    # try to crawl website
    try:
        with ut.timeout(HARD_VISIT_TIMEOUT):
            with open(golang_communication_path, 'w') as f:
                f.write('StartRecord\n')
                f.write('{}.cell'.format(filename))
            time.sleep(0.05)  # the golang process scan the switch file every 50 millisecond
            logger.info("Start capturing.")
            start = time.time()
            driver.get(url)
            if s:
                driver.get_screenshot_as_file(filename + '.png')
            time.sleep(1)
            if ut.check_conn_error(driver):
                write_to_badlist(filename + '.cell', "ConnError")
            elif ut.check_captcha(driver.page_source.strip().lower()):
                write_to_badlist(filename + '.cell', "HasCaptcha")
    except (ut.HardTimeoutException, TimeoutException):
        logger.warning("{} got timeout".format(url))
        write_to_badlist(filename + '.cell', "Timeout")
    except Exception as exc:
        logger.warning("Unknow error:{}".format(exc))
        write_to_badlist(filename + '.cell', "OtherError")
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
            # subprocess.call('rm -rf /tmp/*', shell=True)  # since we use pid to kill firefox, we should clean up tmp too
            logger.info("Firefox killed by pid.")
        with open(golang_communication_path, 'w') as f:
            f.write('StopRecord')
        logger.info("Stop capturing, save to {}.cell.".format(filename))
        logger.info("Loaded {:.2f}s".format(t))
        time.sleep(GAP_BETWEEN_SITES)


def crawl(url, filename, guards, s, device):
    try:
        with ut.timeout(HARD_VISIT_TIMEOUT):
            driver = get_driver()
            src = ' or '.join(guards)
            # start tcpdump
            # cmd = "tcpdump host \(" + src + "\) and tcp -i eth0 -w " + filename+'.pcap'
            pcap_filter = "tcp and (host " + src + ") and not tcp port 22 and not tcp port 20 "
            cmd = 'dumpcap -P -a duration:{} -a filesize:{} -i {} -s 0 -f \'{}\' -w {}' \
                .format(HARD_VISIT_TIMEOUT, MAXDUMPSIZE, device,
                        pcap_filter, filename + '.pcap')
            logger.info(cmd)
            pro = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            tcpdump_timeout = TCPDUMP_START_TIMEOUT  # in seconds
            while tcpdump_timeout > 0 and not ut.is_tcpdump_running(pro):
                time.sleep(0.1)
                tcpdump_timeout -= 0.1
            if tcpdump_timeout < 0:
                raise ut.TcpdumpTimeoutError()
            logger.info("Launch dumpcap in {:.2f}s".format(TCPDUMP_START_TIMEOUT - tcpdump_timeout))
            start = time.time()
            driver.get(url)
            time.sleep(1)
            if s:
                driver.get_screenshot_as_file(filename + '.png')
    except (ut.HardTimeoutException, TimeoutException):
        logger.warning("{} got timeout".format(url))
    except ut.TcpdumpTimeoutError:
        logger.warning("Fail to launch dumpcap")
    except Exception as exc:
        logger.warning("Unknow error:{}".format(exc))
    finally:
        # post visit
        # Log loading time
        if 'driver' in locals():
            # avoid exception happens before driver is declared and assigned
            # which triggers exception here
            driver.quit()
        if 'start' in locals():
            # avoid exception happens before start is declared and assigned
            # which triggers exception here
            t = time.time() - start
            logger.info("Load {:.2f}s".format(t))
            # with open(filename + '.time', 'w') as f:
            #     f.write("{:.4f}".format(t))
        time.sleep(GAP_BETWEEN_SITES)
        ut.kill_all_children(pro.pid)
        pro.kill()
        # subprocess.call("killall dumpcap", shell=True)
        logger.info("Sleep {}s and capture killed, capture {:.2f} MB.".format(GAP_BETWEEN_SITES,
                                                                              os.path.getsize(filename + ".pcap") / (
                                                                                      1024 * 1024)))

        # filter ACKs and retransmission
        if os.path.exists(filename + '.pcap'):
            cmd = 'tshark -r ' + filename + '.pcap' + ' -Y "not(tcp.analysis.retransmission or tcp.len == 0 )" -w ' + filename + ".pcap.filtered"
            subprocess.call(cmd, shell=True)
            # remove raw pcapfile
            cmd = 'rm ' + filename + '.pcap'
            subprocess.call(cmd, shell=True)
        else:
            logger.warning("{} not captured for site {}".format(filename + '.pcap', url))


def main(args):
    global batch_dump_dir, tbblog
    tbblog = args.tbblog
    start, end, m, s, b = args.start, args.end, args.m, args.s, args.b
    assert end > start
    torrc_path = args.torrc
    device = args.device
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
        l_inds = ut.pick_specific_webs(l)
        assert len(l_inds) > 0

    batch_dump_dir = init_directories(args.mode, args.u)
    controller = TorController(torrc_path=torrc_path)

    logger.info("Reset switch file.")
    with open(golang_communication_path, 'w') as f:
        f.write('StopRecord')
    if u:
        # crawl unmonitored webpages, restart Tor every m pages
        b = math.ceil((end - start) / m)
        for bb in range(b):
            with controller.launch():
                logger.info("Start Tor and sleep {}s".format(GAP_AFTER_LAUNCH))
                time.sleep(GAP_AFTER_LAUNCH)
                if args.c:
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
                    if args.c:
                        crawl(website, filename, guards, s, device)
                    else:
                        crawl_without_cap(website, filename, s)
                logger.info("Finish batch #{}, sleep {}s.".format(bb, GAP_BETWEEN_BATCHES))
                time.sleep(GAP_BETWEEN_BATCHES)
    else:
        # crawl monitored webpages, round-robin fashion, restart Tor every m visits of a whole list
        for bb in range(b):
            with controller.launch():
                logger.info("Start Tor and sleep {}s".format(GAP_AFTER_LAUNCH))
                time.sleep(GAP_AFTER_LAUNCH)
                if args.c:
                    guards = controller.get_guard_ip()
                # print(guards)
                for wid, website in enumerate(websites):
                    wid = wid + start
                    for mm in range(m):
                        i = bb * m + mm
                        filename = join(batch_dump_dir, str(wid) + '-' + str(i))
                        logger.info("{:d}-{:d}: {}".format(wid, i, website))
                        # begin to crawl
                        if args.c:
                            crawl(website, filename, guards, s, device)
                        else:
                            crawl_without_cap(website, filename, s)
                logger.info("Finish batch #{}, sleep {}s.".format(bb, GAP_BETWEEN_BATCHES))
                time.sleep(GAP_BETWEEN_BATCHES)


def sendmail(msg):
    cmd = "python3 " + SendMailPyDir + " -m " + msg
    subprocess.call(cmd, shell=True)


if __name__ == "__main__":
    try:
        xvfb_display = start_xvfb(1280, 800)
        args = parse_arguments()
        logger = config_logger(args.crawllog)
        logger.info(args)
        main(args)
        msg = "'Crawler Message:Crawl done at {}!'".format(datetime.datetime.now())
        sendmail(msg)
    except KeyboardInterrupt:
        sys.exit(-1)
    except Exception as e:
        msg = "'Crawler Message: An error occurred:\n{}'".format(e)
        sendmail(msg)
    finally:
        stop_xvfb(xvfb_display)
        # clean up bad webs
        clean_up(args.s)
    # pydir = join(Pardir, "AlexaCrawler", "clean.py")
    # clean_cmd = "python3 " + pydir + " " + batch_dump_dir
    # subprocess.call(clean_cmd, shell=True)
    # logger.info("Clean up bad loads.")
    # subprocess.call("sudo killall tor", shell=True)
    # logger.info("Tor killed!")
    # if args.p and args.c:
    #     # parse raw traffic
    #     logger.info("Parsing the traffic...")
    #     if args.u:
    #         suffix = " -u"
    #     else:
    #         suffix = ""
    #     if args.mode == 'clean':
    #         # use sanity check
    #         cmd = "python3 parser.py " + batch_dump_dir + " -s -mode clean -proc_num 1" + suffix
    #         subprocess.call(cmd, shell=True)
    #
    #     elif args.mode == 'burst':
    #         cmd = "python3 parser.py " + batch_dump_dir + " -mode burst -proc_num 1" + suffix
    #         subprocess.call(cmd, shell=True)
    #     else:
    #         pass
