import numpy as np
import pandas as pd
import os
from os.path import join
import argparse
import multiprocessing
import subprocess

'''This script is to remove outliers in the dataset based on the method in CUMUL paper'''
'''Only for monitored dataset format. The traces should be parsed into cell sequences'''


def parse_arguments():
    parser = argparse.ArgumentParser(description='Remove outliers in the dataset.')
    parser.add_argument('--dir',
                        type=str,
                        metavar='<dataset path>',
                        help='Path of dataset.')
    parser.add_argument('--start', '-s',
                        type=int,
                        metavar='<start ind>',
                        default=0,
                        help='Start from which site in the list (include this ind).')
    parser.add_argument('--end', '-e',
                        type=int,
                        metavar='<end ind>',
                        default=100,
                        help='End to which site in the list (exclude this ind).')
    parser.add_argument('-m',
                        type=int,
                        default=100,
                        metavar='<Num of examples wanted>',
                        help='The number of instances for each class')
    parser.add_argument('-n',
                        type=int,
                        default=120,
                        help='The number of instances we have at most for each class')
    parser.add_argument('--format',
                        type=str,
                        default='.cell',
                        help='to save file as xx."format"')
    # Parse arguments
    args = parser.parse_args()
    return args


def init_directories(original_dir):
    # Define output directory
    outputdir = original_dir.rstrip('/') + '_filtered'
    if not os.path.exists(outputdir):
        os.makedirs(outputdir)
    return outputdir


def get_incoming_num(fdir):
    with open(fdir, 'r') as f:
        tmp = f.readlines()
    trace = pd.Series(tmp).str.slice(0, -1).str.split('\t', expand=True).astype(float)
    if len(trace) == 0:
        print("[Warning] No packet in trace {}".format(fdir))
        return 0

    trace = np.array(trace)[:, 1]
    return len(trace[trace == -1])


def detect_outliers(flist):
    if len(flist) == 0:
        return []
    num_incoming_list = []
    for fdir in flist:
        num_incoming_list.append(get_incoming_num(fdir))
    num_incoming_list = np.array(num_incoming_list)
    Q3 = np.percentile(num_incoming_list, 75)
    Q1 = np.percentile(num_incoming_list, 25)

    lower_bound = Q1 - 1.5 * (Q3 - Q1)
    upper_bound = Q3 + 1.5 * (Q3 - Q1)
    flist = np.array(flist)
    assert len(flist) == len(num_incoming_list)
    outliers = flist[(num_incoming_list <= lower_bound) | (num_incoming_list >= upper_bound)]
    # for outlier in outliers:
    #     print(get_incoming_num(outlier), lower_bound, upper_bound)
    return list(outliers)


def parallel(flist, n_workers=80):
    with multiprocessing.Pool(n_workers) as p:
        res = p.map(detect_outliers, flist)
    return res


if __name__ == '__main__':
    args = parse_arguments()
    flist = []
    total_file_num = 0
    for i in range(args.start, args.end):
        flist_cls = []
        for j in range(args.n):
            fdir = join(args.dir, '{}-{}{}'.format(i, j, args.format))
            if os.path.exists(fdir):
                flist_cls.append(fdir)
                total_file_num += 1
        if len(flist_cls) == 0:
            print("[Warning] no trace for class {}".format(i))
        flist.append(flist_cls)

    res = parallel(flist)
    assert len(res) == len(flist)
    assert len(flist) == args.end - args.start
    flattened_res = []
    for cls in range(len(res)):
        flattened_res.extend(res[cls])
    print("Found {}/{} = {:.2f}% outliers.".format(len(flattened_res), total_file_num,
                                                   len(flattened_res) / total_file_num * 100))

    dst_dir = init_directories(args.dir)
    for flist_cls in flist:
        if len(flist_cls) == 0:
            continue
        cnt = 0
        cls_id_int = -1
        for fdir in flist_cls:
            if fdir in flattened_res:
                continue
            cls_ind = fdir.split('/')[-1].split(args.format)[0].split('-')[0]
            if cls_id_int < 0:
                cls_id_int = int(cls_ind)
            assert cls_id_int == int(cls_ind)
            dst_fdir = join(dst_dir, '{}-{}{}'.format(cls_ind, cnt, args.format))
            subprocess.call('cp ' + fdir + ' ' + dst_fdir, shell=True)
            cnt += 1
        if cls_id_int != -1 and cnt < args.m:
            # have this class of file but not enough, copy some from the same class
            print("[Warning] {:-2d}:{:-3d}, pad {} outliers.".format(cls_id_int, cnt, args.m - cnt))
            res_cls = res[cls_id_int - args.start].copy()
            np.random.shuffle(res_cls)
            for k in range(args.m - cnt):
                dst_fdir = join(dst_dir, '{}-{}{}'.format(str(cls_id_int), cnt, args.format))
                # print('cp ' + res_cls[k] + ' ' + dst_fdir)
                subprocess.call('cp ' + res_cls[k] + ' ' + dst_fdir, shell=True)
                cnt += 1
        assert cnt >= args.m
