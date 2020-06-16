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

ParsedDir = join(abspath(join(dirname(__file__), pardir)) , "AlexaCrawler/parsed")

def init_directories(path):
    # Create a results dir if it doesn't exist yet
    if not os.path.exists(path):
        makedirs(path)


def getTimestamp(pkt, t0):
    return float(pkt.time - t0)


def getDirection(pkt):
    if pkt.payload.src in My_Source_Ips:
        return 1
    else:
        return -1 

def parse_arguments():

    parser = argparse.ArgumentParser(description='Parse captured traffic.')

    parser.add_argument('dir',
                        type=str,
                        metavar='<dataset path>',
                        help='Path of dataset.')

    # Parse arguments
    args = parser.parse_args()
    return args



def insert(arr, dir):
    rho = {1: 0.02, -1: 0.006}
    gap = rho[dir] * 1.4

    diff = np.diff(arr[:,0])
    inds = np.where(diff>gap)
    # print(arr[inds])
    inds = inds[0]
    l = len(arr)
    for ind in inds:
        if ind +1 >= l:
            break
        t1 = arr[ind,0]
        t2 = arr[ind+1,0]
        # print(t2-t1, "dir", dir)
        n = int((t2-t1) / rho[dir])
        # print(n)
        for i in range(1,n):
            arr = np.concatenate((arr,[[t1+rho[dir]*i, dir*66666]]),0)
    arr = arr[arr[:, 0].argsort(kind="mergesort")]

    #delete close ones
    diff = np.diff(arr[:,0])
    inds = np.where(diff<=rho[dir]*0.1)
    for ind in inds:
        arr = np.delete(arr, ind, 0)
    return arr
def syn(fdir):
    global savedir
    fname = fdir.split('/')[-1]
    savefiledir = join(savedir, fname)

    with open(fdir,'r') as f:
        tmp = f.readlines()
        tmp = pd.Series(tmp).str.slice(0,-1).str.split('\t',expand = True).astype('float')
        tmp.columns = ['time','direction']
    raw_out = tmp[tmp.direction>0].values
    raw_in = tmp[tmp.direction<0].values

    syn_out = insert(raw_out, 1)
    syn_in = insert(raw_in, -1)

    #sort packets
    total_pkts_unsorted = np.concatenate((syn_out,syn_in),0)
    total_pkts0 = total_pkts_unsorted[total_pkts_unsorted[:,0].argsort(kind = "mergesort")]
    with open(savefiledir, 'w') as f:
        for pkt in total_pkts0:
            f.write("{:.6f}\t{:.0f}\n".format(pkt[0],pkt[1]))


if __name__ == "__main__":
    global savedir
    args = parse_arguments()
    filelist = glob.glob(join(args.dir,'*.cell'))

    savedir = args.dir.rstrip("/")+"_syn"
    init_directories(savedir)
    print("Output to {}".format(savedir))

    print("Totol:{}".format(len(filelist)))

    pool = mp.Pool(processes=6)
    pool.map(syn, filelist)
