import multiprocessing as mp
import logging
import os
from os import makedirs
from os.path import join, abspath, dirname, pardir
import numpy as np
import subprocess
import argparse
import glob
import pandas as pd

ParsedDir = join(abspath(join(dirname(__file__), pardir)), "AlexaCrawler/parsed")
NUM_MONITORED = 100
NUM_MONINST = 100
NUM_UNMONITORED = 10000


def init_directories(outputdir):
    # Create a results dir if it doesn't exist yet
    if not os.path.exists(outputdir):
        makedirs(outputdir)


def parse_arguments():
    parser = argparse.ArgumentParser(description='Trim the noisy traces.')

    parser.add_argument('-dir',
                        type=str,
                        required=True,
                        metavar='<dataset path>',
                        help='Path of dataset.')
    parser.add_argument('-a',
                        default=True,
                        action='store_false',
                        help='Analyse the cut position in the tail or trim the traces?(default: analyse)')
    parser.add_argument('-head',
                        default=False,
                        action='store_true',
                        help='Trim head to the first true outgoing')
    parser.add_argument('-tail',
                        default=0,
                        type=float,
                        help='Cut off the last t seconds.')
    parser.add_argument('-format',
                        type=str,
                        metavar='<File suffix>',
                        default='.cell',
                        help='Input file format')
    # Parse arguments
    args = parser.parse_args()
    return args


def read_trace(fdir):
    '''return trace as a nx2-d np array'''
    with open(fdir, "r") as f:
        trace = f.readlines()
    trace = np.array(pd.Series(trace).str.slice(0, -1).str.split("\t", expand=True).astype(float))
    return trace


def trim(fdir):
    global trim_head, trim_tail_time, outputdir
    trace = read_trace(fdir)
    if trim_head:
        first_out_index = np.where(trace[:, 1] == 1)[0][0]
        trace = trace[first_out_index:].copy()
    if trim_tail_time > 0:
        # make sure the trimmed trace is at least 1-sec long.
        trimmed_time = max(trace[-1, 0] - trim_tail_time, 1)
        trace = trace[trace[:, 0] <= trimmed_time].copy()
    fname = fdir.split("/")[-1]
    with open(join(outputdir, fname), 'w') as f:
        for pkt in trace:
            f.write("{:.4f}\t{:d}\n".format(pkt[0], pkt[1]))


def trim_elapsed(pkts, t):
    '''compute the time gap between the real stop point and the cut point'''
    real_pkts = pkts[abs(pkts[:,1]) == 1].copy()
    end_time = real_pkts[int(0.99*len(real_pkts)), 0]
    cut_time = pkts[-1, 0] - t

    total_pkts_len = len(real_pkts)
    dummy_pkts = pkts[abs(pkts[:,1])>1].copy()
    trimmed_dummy_len = len(dummy_pkts) - len(dummy_pkts[dummy_pkts[:,0]<cut_time])

    # print("end:{:.4f}, cut:{:.4f}".format(end_time,cut_time))
    return cut_time - end_time, trimmed_dummy_len, total_pkts_len


def ana(fdir):
    global trim_tail_time
    '''Analyse if cut potision in the end is good or not'''
    '''we analyze 1,2,..,up to trim_tail_time seconds'''
    assert trim_tail_time >= 0
    trace = read_trace(fdir)
    out_trace = trace[trace[:, 1] > 0]
    in_trace = trace[trace[:, 1] < 0]
    res = []
    for t in range(0,int(trim_tail_time)+1):
        out_elapsed,trimmed_dummy_len_out, total_pkts_len_out = trim_elapsed(out_trace, t)
        in_elapsed,trimmed_dummy_len_in, total_pkts_len_in = trim_elapsed(in_trace, t)
        trimmed_dummy_len = trimmed_dummy_len_out + trimmed_dummy_len_in
        total_pkts_len = total_pkts_len_out + total_pkts_len_in
        res.append((t,out_elapsed,in_elapsed,trimmed_dummy_len,total_pkts_len ))
    return res


if __name__ == "__main__":
    global trim_head, trim_tail_time, outputdir
    args = parse_arguments()
    trim_head, trim_tail_time = args.head, args.tail

    flist = []
    for i in range(NUM_MONITORED):
        for j in range(NUM_MONINST):
            if os.path.exists(os.path.join(args.dir, str(i) + "-" + str(j) + args.format)):
                flist.append(os.path.join(args.dir, str(i) + "-" + str(j) + args.format))
    for i in range(NUM_UNMONITORED):
        if os.path.exists(os.path.join(args.dir, str(i) + args.format)):
            flist.append(os.path.join(args.dir, str(i) + args.format))
    outputdir = args.dir.rstrip("/") + "_trimmed/"
    print(outputdir)
    init_directories(outputdir)
    pool = mp.Pool(processes=15)
    if args.a:
        res = pool.map(ana, flist)
        # print(res)
        with open(join(outputdir, 'analyze.txt'), 'w') as f:
            #starting from 0s to trim_tail_time s, report out then in
            for inst in res:
                for item in inst[:-1]:
                    f.write("{}\t{:.4f}\t{:.4f}\t{}\t{}\t".format(item[0],item[1],item[2],item[3],item[4]))
                item = inst[-1]
                f.write("{}\t{:.4f}\t{:.4f}\t{}\t{}\n".format(item[0],item[1],item[2],item[3],item[4]))
    else:
        pool.map(trim, flist)
