# WFCrawler: a toolkit for crawling top ranking sites

This is the repository of WFCrawler. 
Similar as [Tor Browser Crawler](https://github.com/webfp/tor-browser-crawler), it crawls top sites and parses them into traces for Website Fingerprinting (WF) research. 
It is customized for [WFDefProxy](https://github.com/websitefingerprinting/wfdef), a pluggable transport which implements a bunch of WF defenses.

**Only for research purposed, please use carefully!**

## How to use?
We use `tbselenium` to launch the tor browser. 
We use `stem` to control Tor. 
To launch a crawl, use the cmd: `python crawler.py [args]`.
There are some key arguments:
* `-w`: to provide a path to the website list. If not specified, it will use the default path defined in `common.py`: `unmon_list` and `mon_list`.
* `--start`: to specify the start index of the website in the list
* `--end`: to specify the end index of the website in the list
* `--batch`, `-b`: the number of batches crawled. After crawling a batch, Tor will be restared. (Only useful when crawling monitored websites)
* `-m`: the number of instances per site in each batch. 
* `--open`: whether crawl the monitored sites or non-monitored sites.
* `--mode`: "clean" or "burst". Just for marking whether or not this is a defended dataset. Used for folder name initialization, 
* `--tbblog`: provide a path to save the logs of the browser.
* `--torrc`: provide the path of a torrc file


To help understand the parameters, we give two examples here:

### When we want to crawl a monitored dataset:
```
python crawler.py --start 0 --end 10 -m 3 -b 2 --open 0 --mode clean --tbblog /Users/example/crawl.log --torrc /Users/example/mytorrc
```
This command will crawl the websites indexed from 0 to **9** in the `mon_list` in a round-robin fashion: 0, 0, 0, ..., 9,9,9 (the first batch);(Tor will be restarted); 0,0,0,..., 9,9,9 (the second batch).
Since `m=3` and `b=2`, each website will be loaded 6 times in total.
The crawled traces will be saved as `0-0.cell, ..., 0-5.cell, ..., 9-0.cell, ..., 9-5.cell`.
The dataset is saved as `clean_[timestamp]`. 

### When we want to crawl a non-monitored dataset:
```
python crawler.py --start 200 --end 300 -m 50 --open 1 --mode clean -u --tbblog /Users/example/crawl.log --torrc /Users/example/mytorrc
```
This command will crawl the websites indexed from 200 to 299 in the `unmon_list`, each loaded once. 
Tor will be restarted every `m=50` websites. The dataset is saved as `uclean_[timestamp]`.
The crawled traces will be saved as `0.cell, ..., 99.cell`.
Note that we have a `--offset` parameter in the function and the default value is 200.
Therefore, when visiting the 200th website, the file name is `0.cell` (200 - offset). 

## How does it work?
The crawler uses gRPC to communicate with WFDefProxy. To start logging before a visit:
```angular2html
err = self.gRPCClient.sendRequest(turn_on=True, file_path='{}.cell'.format(filename)) (Line 180)
```
To end the logging after a visit:
```angular2html
self.gRPCClient.sendRequest(turn_on=False, file_path='') (Line 212)
```
Therefore, a raw trace will be saved as `[filename].cell`.

## Parse the collected traces
To parse the collected  traces into Wang's format, use `parseTLS.py`. Here is an example:
```angular2html
python parseTLS.py [path_to_dataset] -mode clean
```
The parameter definitions are similar as `crawler.py`. Please go and check it.

## Work with Tor Browser directly
The `master` branch works with Selenium + Tor. 
We also developed another branch `dev-tbb` which directly launches Tor Browser with command lines.
You should have a customized Tor Browser where you replace the default torrc file with yours and 
hopefully a [tampermonkey](https://www.tampermonkey.net) script to automatically close Tor Browser after each visit. 

Similar as before, the crawling process will be in a round-robin fashion. 
But we will not use gRPC anymore. 
Instead, each time we copy the log file of the pluggable transport (i.e., WFDefProxy) `/somewhere/pt_state/obfs4proxy.log` to the result folder.

To parse the raw traces, remember to use `parse_log.py` this time. The usage is similar as `parseTLS.py` though. 

## Tips and Tricks
You can modify some constants in `common.py`, such as 
```angular2html
gRPCAddr = "localhost:10086"
BROWSER_LAUNCH_TIMEOUT = 10
SOFT_VISIT_TIMEOUT = 80
HARD_VISIT_TIMEOUT = SOFT_VISIT_TIMEOUT + 10
GAP_BETWEEN_BATCHES = 5
CRAWLER_DWELL_TIME = 3
GAP_BETWEEN_SITES_MAX = 2
GAP_AFTER_LAUNCH = 5
```

## Versioning
The codes are tested in Python 3.7. 

## Acknowledgments 
Some of the codes are based on the following works. We thank respective authors for being kind to share their code:

[1] M. Juarez, S. Afroz, G. Acar, C. Diaz, R. Greenstadt, [Tor-Browser-Crawler ](https://github.com/webfp/tor-browser-crawler)

[2] Nate Mathews, [Tor-Browser-Crawler](https://github.com/notem/tor-browser-crawler)
