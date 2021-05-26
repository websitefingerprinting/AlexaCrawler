"""This is a script of count how many times front is triggered during one loading"""
import numpy as np
import os
import multiprocessing
import argparse
MON_SITE_NUM = 100
MON_INST_NUM = 100
UNMON_SITE_NUM = 90000

def parse_arguments():
    parser = argparse.ArgumentParser(description='Parse captured traffic.')

    parser.add_argument('dir',
                        type=str,
                        metavar='<dataset path>',
                        help='Path of dataset.')
    parser.add_argument('-u',
                        action='store_true',
                        default=False,
                        help='Do we count unmonitored ones? (default:is monitored, false)')
    parser.add_argument('--format',
                        type=str,
                        metavar='<parsed file suffix>',
                        default='.cell',
                        help='to save file as xx.suffix')
    parser.add_argument('--proc_num',
                        type=int,
                        metavar='<process num>',
                        default=20,
                        help='The num of parallel workers')
    # Parse arguments
    args = parser.parse_args()
    return args

def count_init(fdir):
    cnt = 0
    with open(fdir, 'r') as f:
        lines = f.readlines()
    for line in lines:
        if '[Init] Sampled' in line:
            cnt += 1
    if cnt <= 0:
        print("[WARNING] FRONT is not triggered in {}".format(fdir))
    return cnt


def parrallel(flist, n_jobs=20):
    with multiprocessing.Pool(n_jobs) as p:
        res = p.map(count_init, flist)
    return list(res)


if __name__ == "__main__":
    args = parse_arguments()
    flist_mon = []
    for i in range(MON_SITE_NUM):
        for j in range(MON_INST_NUM):
            if os.path.exists(os.path.join(args.dir, str(i) + "-" + str(j) + args.format)):
                flist_mon.append(os.path.join(args.dir, str(i) + '-' + str(j) + args.format))
    flist_unmon = []
    for i in range(UNMON_SITE_NUM):
        if os.path.exists(os.path.join(args.dir, str(i) + args.format)):
            flist_unmon.append(os.path.join(args.dir, str(i) + args.format))

    res_unmon = []
    if args.u:
        res_unmon = parrallel(flist_unmon, args.proc_num)
    res_mon = parrallel(flist_mon, args.proc_num)
    # print(res_mon, res_unmon)
    print("mean of mon: {:.2f}, mean of unmon:{:.2f}, mean of total: {:.2f}".format(np.mean(res_mon), np.mean(res_unmon), np.mean(res_mon + res_unmon)))