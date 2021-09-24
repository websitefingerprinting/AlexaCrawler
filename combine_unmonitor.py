import subprocess
import os
from os import makedirs
from os.path import join, abspath, dirname, pardir
import glob
import re
import argparse
import time

Pardir = abspath(join(dirname(__file__), pardir))

DumpDir = join(Pardir, "AlexaCrawler/dump")


def parse_arguments():
    parser = argparse.ArgumentParser(description='Crawl Alexa top websites and capture the traffic')

    parser.add_argument('-dir',
                        nargs='+',
                        type=str,
                        metavar='<batch dir>',
                        dest='dirlist',
                        default=[],
                        help='bacth folders')
    parser.add_argument('-suffix',
                        type=str,
                        metavar='<suffix>',
                        default='.pcap',
                        help='suffix of the file')

    # Parse arguments
    args = parser.parse_args()
    return args


def init_directories():
    # Create a results dir if it doesn't exist yet
    if not os.path.exists(DumpDir):
        makedirs(DumpDir)

    # Define output directory
    timestamp = time.strftime('%m%d_%H%M')
    output_dir = join(DumpDir, 'unmon_' + timestamp)
    makedirs(output_dir)

    return output_dir


if __name__ == '__main__':
    args = parse_arguments()
    folders = args.dirlist
    output_dir = init_directories()
    for folder in folders:
        cmd = "mv " + folder + "/*" + args.suffix + " " + output_dir
        # print(cmd)
        subprocess.call(cmd, shell=True)
    total = glob.glob(output_dir + "/*" + args.suffix)
    print("Merged to {}, total {}".format(output_dir, len(total)))
