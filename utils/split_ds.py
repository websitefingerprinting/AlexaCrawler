import glob
import os
from os.path import join
import argparse
import numpy as np
import subprocess


def split_one_class(flist, weight):
    np.random.shuffle(flist)
    res = []

    weight = np.array(weight) / sum(weight)
    weight = np.cumsum(weight)
    weight = (weight * len(flist)).astype(int)
    start = 0
    for end in weight:
        res.append(flist[start:end])
        start = end
    return res


def split_ds(fdir, weight, class_num, format='.cell', unmon_dir=None):
    attack_train, split_train, evaluation = [], [], []
    for i in range(class_num):
        flist_cls = glob.glob(join(fdir, '{}-*{}'.format(i, format)))
        res = split_one_class(flist_cls, weight)
        attack_train += res[0]
        split_train += res[1]
        evaluation += res[2]
    if unmon_dir:
        flist_cls = glob.glob(join(unmon_dir, '*{}'.format(format)))
        # in case the directory includes mon instances
        flist_cls_filtered = []
        for fname in flist_cls:
            if '-' not in fname:
                flist_cls_filtered.append(fname)
        res = split_one_class(flist_cls_filtered, weight)
        attack_train += res[0]
        split_train += res[1]
        evaluation += res[2]
    return attack_train, split_train, evaluation


def copy(flist, dst):
    for fdir in flist:
        cmd = "cp {} {}".format(fdir, dst)
        subprocess.call(cmd, shell=True)


def parse_arguments():
    parser = argparse.ArgumentParser(description='One-time script for splitting the dataset')
    parser.add_argument('--p_mon',
                        metavar='<new trace path>',
                        help='defended dataset')
    parser.add_argument('--p_unmon',
                        default=None,
                        metavar='<new trace path>',
                        help='defended dataset')
    parser.add_argument('--class_num',
                        default=100,
                        type=int,
                        help='Class number (exclude unmon class)')
    parser.add_argument('--output',
                        default='./',
                        help='Output results to which folder')
    parser.add_argument('--format',
                        metavar='<file suffix>',
                        default=".cell",
                        help='')
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_arguments()
    # attack_train, split_train, evalulation
    ratio = [9, 2, 9]

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    attack_train_dir = join(args.output, 'attack_train')
    split_train_dir = join(args.output, 'split_train')
    evaluation_dir = join(args.output, 'evaluation')
    os.makedirs(attack_train_dir, exist_ok=True)
    os.makedirs(split_train_dir, exist_ok=True)
    os.makedirs(evaluation_dir, exist_ok=True)

    attack_train, split_train, evaluation = split_ds(args.p_mon, ratio, args.class_num, unmon_dir=args.p_unmon)
    copy(attack_train, attack_train_dir)
    copy(split_train, split_train_dir)
    copy(evaluation, evaluation_dir)


