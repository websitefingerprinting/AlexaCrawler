import glob
import os
from os.path import join
import argparse
import numpy as np
import subprocess


def split_ds(flist, weight):
    np.random.shuffle(flist)
    res = []

    weight = np.array(weight) / sum(weight)
    weight = np.cumsum(weight)
    weight = (weight * len(flist)).astype(int)
    start = 0
    for end in weight:
        print(start, end)
        res.append(flist[start:end])
        start = end
    return res


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
    ratio = [9, 9, 2]
    mon_list = glob.glob(join(args.p_mon, '*' + args.format))
    unmon_list = []
    if args.p_unmon:
        unmon_list = glob.glob(join(args.p_unmon, '*' + args.format))
    print("In total {} + {} instances".format(len(mon_list), len(unmon_list)))

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    attack_train_dir = join(args.output, 'attack_train')
    split_train_dir = join(args.output, 'split_train')
    evaluation_dir = join(args.output, 'evaluation')
    os.makedirs(attack_train_dir, exist_ok=True)
    os.makedirs(split_train_dir, exist_ok=True)
    os.makedirs(evaluation_dir, exist_ok=True)

    attack_train, split_train, evaluation = split_ds(mon_list + unmon_list, ratio)
    copy(attack_train, attack_train_dir)
    copy(split_train, split_train_dir)
    copy(evaluation, evaluation_dir)


