#To calculate the mean time of webpage#
import logging
import argparse
import pandas as pd
import numpy as np
import glob
import os
import sys
import multiprocessing as mp

logger = logging.getLogger('mean')
def config_logger(args):
    # Set file
    log_file = sys.stdout
    if args.log != 'stdout':
        log_file = open(args.log, 'w')
    ch = logging.StreamHandler(log_file)

    # Set logging format
    LOG_FORMAT = "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
    ch.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(ch)

    # Set level format
    logger.setLevel(logging.INFO)

def parse_arguments():

    parser = argparse.ArgumentParser(description='Calculate overhead for a trace folder.')

    parser.add_argument('dir',
                        metavar='<traces path>',
                        help='Path to the directory with the traffic traces to be simulated.')

    parser.add_argument('-format',
                        metavar='<format>',
                        default = '.cell',
                        help='file format, default: "xx.cell" ')
    parser.add_argument('-mode',
                        metavar='<mode>',
                        type = int,
                        default = 1,
                        help='0: unmonitored pages, 1: monitored pages')
    parser.add_argument('--log',
                        type=str,
                        dest="log",
                        metavar='<log path>',
                        default='stdout',
                        help='path to the log file. It will print to stdout by default.')

    args = parser.parse_args()
    config_logger(args)

    return args

def calc_single_time(t):
    global fmt, mode
    logger.debug('Processing file {}'.format(t))
    label = t.split("/")[-1].split(fmt)[0]
    if mode:
        label = int(label.split("-")[0])
    else:
        label = int(label)

    with open(t,'r') as f:
        lines = f.readlines()
    nt = pd.Series(lines).str.slice(0,-1).str.split('\t',expand = True).astype("float")
    nt = np.array(nt)
    ntime = nt[abs(nt[:, 1]) == 1][:,0]
    # print(ntime.shape,len(ntime)*0.95)
    return (label, ntime[int(len(ntime)*0.95)])

def parallel(flist, n_jobs = 10):
    pool = mp.Pool(n_jobs)
    times  = pool.map(calc_single_time, flist)    
    return times

if __name__ == '__main__':
    global fmt, mode
    args = parse_arguments()
    flist = glob.glob(os.path.join(args.dir,'*'+args.format))
    fmt = args.format
    mode = args.mode
    # ovhds = []
    # for f in flist:
    #     overhead = calc_single_ovhd(f)
    #     ovhds.append(overhead)
    times = parallel(flist)
    filename = args.dir.rstrip("/").split("/")[-1] + ".npy"
    np.save(filename,times)
    print("Save to {}".format(filename))
 
    





