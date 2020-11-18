import multiprocessing as mp
import logging
import os
from os import makedirs
from os.path import join, abspath, dirname, pardir
import numpy as np
import subprocess
import argparse
from scapy.all import *
import glob
from common import My_Source_Ips
import pandas as pd

CELL_SIZE = 512
# CELL+ TLS HEADER + MY HEADER
MY_CELL_SIZE = CELL_SIZE + 24
isDummy = 888
isReal = 1

captured_file_name = '.cell'
ParsedDir = join(abspath(join(dirname(__file__), pardir)), "AlexaCrawler/parsed")


def init_directories(path):
    # Create a results dir if it doesn't exist yet
    if not os.path.exists(path):
        makedirs(path)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Parse captured traffic.')

    parser.add_argument('dir',
                        type=str,
                        metavar='<dataset path>',
                        help='Path of dataset.')
    parser.add_argument('-mode',
                        type=str,
                        metavar='<parse mode>',
                        help='The type of dataset: clean, burst?.')
    parser.add_argument('-u',
                        action='store_true',
                        default=False,
                        help='is monitored webpage or unmonitored? (default:is monitored, false)')
    parser.add_argument('-s',
                        action='store_true',
                        default=False,
                        help='If use screenshot as sanity check?')
    parser.add_argument('-suffix',
                        type=str,
                        metavar='<parsed file suffix>',
                        default='.cell',
                        help='to save file as xx.suffix')
    parser.add_argument('-proc_num',
                        type=int,
                        metavar='<process num>',
                        default=2,
                        help='The num of parallel workers')
    # Parse arguments
    args = parser.parse_args()
    return args

def parse(fdir):
    global savedir, suffix, isunmon
    if isunmon:
        site = fdir.split("/")[-1].split(captured_file_name)[0]
        savefiledir = join(savedir, site+suffix)
    else:
        site,inst = fdir.split("/")[-1].split(captured_file_name)[0].split("-")
        savefiledir = join(savedir, site+"-"+inst+suffix)
    # Format: timestamp, realbytes, dummybytes
    # Task: turn tls -> cells, normalize timestamps
    res = []
    with open(fdir,"r") as f:
        tmp = f.readlines()
        if tmp[-1] == '\n':
            tmp = tmp[:-1]
        tmp = pd.Series(tmp)
    tmp = tmp.str.slice(0,-1).str.split(' +|\t',expand=True).astype(np.int64)
    trace = np.array(tmp)
    refTime = trace[0,0]


    lastTime = trace[0,0]
    lastDirection = np.sign(trace[0,1]+trace[0,2])
    lastRealBytes = 0
    lastDummyBytes = 0
    with open(savefiledir, 'w') as f:
        for tls in trace:
            curTime = tls[0]
            curDirection = np.sign(tls[1]+tls[2])
            if (curTime - lastTime)*1.0/1e6 < 1 and lastDirection == curDirection:
                lastRealBytes += tls[1]
                lastDummyBytes += tls[2]
                continue
            # else
            # print(lastTime, lastRealBytes, lastDummyBytes)
            relTime = (lastTime-refTime)/1e9
            for _ in range(int(np.round(abs(lastRealBytes)/MY_CELL_SIZE))):
                f.write('{:.4f}\t{:.0f}\n'.format(relTime, lastDirection))
            for _ in range(int(np.round(abs(lastDummyBytes)/MY_CELL_SIZE))):
                f.write('{:.4f}\t{:.0f}\n'.format(relTime, lastDirection*isDummy))
            lastTime = curTime
            lastDirection = curDirection
            lastRealBytes = tls[1]
            lastDummyBytes = tls[2]
        # print(lastTime, lastRealBytes, lastDummyBytes)
        relTime = (lastTime - refTime) / 1e9
        for _ in range(int(np.round(abs(lastRealBytes) / MY_CELL_SIZE))):
            f.write('{:.4f}\t{:.0f}\n'.format(relTime, lastDirection))
        for _ in range(int(np.round(abs(lastDummyBytes) / MY_CELL_SIZE))):
            f.write('{:.4f}\t{:.0f}\n'.format(relTime, lastDirection * isDummy))

def parse_clean(fdir):
    global savedir, suffix, isunmon
    if isunmon:
        site = fdir.split("/")[-1].split(captured_file_name)[0]
        savefiledir = join(savedir, site+suffix)
    else:
        site,inst = fdir.split("/")[-1].split(captured_file_name)[0].split("-")
        savefiledir = join(savedir, site+"-"+inst+suffix)
    # Format: timestamp, realbytes, dummybytes
    # Task: turn tls -> cells, normalize timestamps
    res = []
    with open(fdir,"r") as f:
        tmp = f.readlines()
        if tmp[-1] == '\n':
            tmp = tmp[:-1]
        tmp = pd.Series(tmp)
    tmp = tmp.str.slice(0,-1).str.split(' +|\t',expand=True).astype(np.int64)
    trace = np.array(tmp)
    refTime = trace[0,0]

    with open(savefiledir, 'w') as f:
        for tls in trace:
            t = (tls[0] - refTime)*1.0/1e9
            for _ in range(int(np.round(abs(tls[1])/MY_CELL_SIZE))):
                f.write('{:.4f}\t{:.0f}\n'.format(t, np.sign(tls[1])))

if __name__ == "__main__":
    global savedir, suffix, isunmon
    args = parse_arguments()
    suffix = args.suffix
    isunmon = args.u
    filename = args.dir.rstrip("/").split("/")[-1]
    savedir = join(ParsedDir, filename)
    init_directories(savedir)
    print("Parsed file in {}".format(savedir))
    if args.s:
        filelist_ = glob.glob(join(args.dir, '*.png'))
        filelist = []
        # Sanity check
        for f in filelist_:
            pcapfile = f.split(".png")[0] + captured_file_name
            if os.path.exists(pcapfile):
                filelist.append(pcapfile)
    else:
        filelist = glob.glob(join(args.dir, '*' + captured_file_name))

    # for f in filelist[:1]:
    #   parse(f)
    # print("Totol:{}".format(len(filelist)))
    if args.mode == 'clean':
        with mp.Pool(processes=args.proc_num) as p:
            p.map(parse_clean, filelist)
            p.close()
            p.join()
    elif args.mode == 'burst':
        with mp.Pool(processes=args.proc_num) as p:
            p.map(parse, filelist)
            p.close()
            p.join()

