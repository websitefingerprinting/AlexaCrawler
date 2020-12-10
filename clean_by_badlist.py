from os.path import join
import os
import numpy as np
import subprocess
import multiprocessing as mp
import argparse
from glob import glob
from itertools import compress
import re


def parse_arguments():
    parser = argparse.ArgumentParser(description='Filter out error or captcha check by screenshot')

    parser.add_argument('dir',
                        type=str,
                        metavar='<dataset path>',
                        help='Path of dataset.')

    # Parse arguments
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    args = parse_arguments()
    with open(join(args.dir, 'bad.list'), 'r') as f:
        l = f.readlines()
        for record in l:
            record_trace = record.rstrip("\n").split("\t")[0].replace("/home/docker/","/home/jgongac/")
            record_screenshot = record_trace.replace(".cell",".png")
            if os.path.exists(record_trace):
                subprocess.call("sudo rm "+record_trace,shell=True)
            if os.path.exists(record_screenshot):
                subprocess.call("sudo rm "+record_screenshot,shell=True)
