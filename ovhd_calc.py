# calc data overhead based on original and new dataset
import logging
import argparse
import pandas as pd
import numpy as np
import glob
import os
import sys
import multiprocessing as mp

import utils


NUM_MONITORED = 100
NUM_INST = 100
NUM_UNMONITORED = 50000

logger = utils.config_logger('ovhd')


def parse_arguments():
    parser = argparse.ArgumentParser(description='Calculate overhead for a trace folder.')

    parser.add_argument('--o_mon',
                        metavar='<traces path>',
                        help='undefended dataset')
    parser.add_argument('--o_unmon',
                        default=None,
                        metavar='<traces path>',
                        help='undefended dataset')

    parser.add_argument('--p_mon',
                        metavar='<new trace path>',
                        help='defended dataset')
    parser.add_argument('-p_unmon',
                        default=None,
                        metavar='<new trace path>',
                        help='defended dataset')

    parser.add_argument('--format',
                        metavar='<file suffix>',
                        default=".cell",
                        help='')
    parser.add_argument('--log',
                        type=str,
                        dest="log",
                        metavar='<log path>',
                        default='stdout',
                        help='path to the log file. It will print to stdout by default.')

    args = parser.parse_args()

    return args


def calc_single_ovhd(ff):
    if '-' in ff:
        original_dir, new_dir = undefended_mon_dir, defended_mon_dir
    else:
        original_dir, new_dir = undefended_unmon_dir, defended_unmon_dir
        
    original, new = os.path.join(original_dir, ff), os.path.join(new_dir, ff)
    nt = utils.load_trace(new)
    ot = utils.load_trace(original)

    if len(nt) < 50 or len(ot) < 50:
        return None, None, None, None

    new_real_trace = nt[abs(nt[:, 1]) == 1].copy()
    if len(new_real_trace) < 50:
        return None, None, None, None

    # compute data overhead
    n_total = len(nt)
    n_real = len(new_real_trace)
    n_dummy = n_total - n_real
    # compute time overhead
    index_99 = int(0.99 * len(ot))
    old_time = ot[index_99, 0]
    index_99 = int(0.99 * len(new_real_trace))
    new_time = new_real_trace[index_99, 0]
    return n_dummy, n_real, old_time, new_time


def parallel(flist, n_jobs=40):
    pool = mp.Pool(n_jobs)
    ovhds = pool.map(calc_single_ovhd, flist)
    return ovhds


if __name__ == '__main__':
    args = parse_arguments()
    undefended_mon_dir = args.o_mon
    undefended_unmon_dir = args.o_unmon if args.o_unmon else args.o_mon
    defended_mon_dir = args.p_mon
    defended_unmon_dir = args.p_unmon if args.p_unmon else args.p_mon

    flist = []
    for i in range(NUM_MONITORED):
        for j in range(NUM_INST):
            if os.path.exists(os.path.join(undefended_mon_dir, str(i) + "-" + str(j) + args.format)) and \
                    os.path.exists(os.path.join(defended_mon_dir, str(i) + "-" + str(j) + args.format)):
                flist.append(str(i) + "-" + str(j) + args.format)
    for i in range(NUM_UNMONITORED):
        if os.path.exists(os.path.join(undefended_unmon_dir, str(i) + args.format)) and \
                os.path.exists(os.path.join(defended_unmon_dir, str(i) + args.format)):
            flist.append(str(i) + args.format)
    logger.debug("In total {} files".format(len(flist)))
    # flist = glob.glob(os.path.join(args.dir,'*'+args.format))
    # ovhds = []
    # for f in flist:
    #     overhead = calc_single_ovhd(f)
    #     ovhds.append(overhead)
    ovhds = parallel(flist)
    ovhds = list(zip(*ovhds))

    n_dummys = sum(list(filter(None, ovhds[0])))
    n_reals = sum(list(filter(None, ovhds[1])))
    old_times = sum(list(filter(None, ovhds[2])))
    new_times = sum(list(filter(None, ovhds[3])))
    # print("Mean time: {:.4f}, {:.4f}".format(  otime / len(ovhds[2]), ntime/ len(ovhds[3]) ))
    # print("Data overhead {:.4f}".format( (nlen - olen)/olen*1.0))
    # print("Time overhead {:.4f}".format( (ntime - otime)/otime))
    print("{} {:.4f} {:.4f}".format(len(flist), n_dummys / n_reals * 1.0, (new_times - old_times) / old_times))
    # logger.info('total packets:           {:.4f} +- {:.4f}'.format(total.mean(), total.std()))
    # logger.info('Merge Padding overhead:  {:.4f} '.format(mpovhds))
    # logger.info('Random Padding overhead: {:.4f} '.format(rpovhds))
    # logger.info('total packets:           {:.4f} +- {:.4f}'.format(total.mean(), total.std()))
    # logger.info('Merge Padding overhead:  {:.4f} +- {:.4f}'.format(mpovhds.mean(), mpovhds.std()))
    # logger.info('Random Padding overhead: {:.4f} +- {:.4f}'.format(rpovhds.mean(), rpovhds.std()))
