from os.path import join
import numpy as np
import subprocess
import argparse
from scapy.all import *

docker_home_path = '/home/docker'
host_home_path = '/home/jgongac'

def parse_arguments():
    parser = argparse.ArgumentParser(description='Filter out error or timeout pages.')

    parser.add_argument('dir',
                        type=str,
                        metavar='<dataset path>',
                        help='Path of dataset.')

    # Parse arguments
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_arguments()
    badlistdir = join(args.dir, 'bad.list')
    if not os.path.exists(badlistdir):
        print("Bad list not exists.")
        exit(0)
    subprocess.call("sudo chmod -R 777 "+args.dir, shell=True)
    with open(badlistdir,'r') as f:
        bad_websites = f.readlines()
    cnt = 0
    for w in bad_websites:
        w = w.rstrip('\n')
        w = w.replace(docker_home_path, host_home_path)
        subprocess.call("rm "+w, shell=True)
        cnt += 1
    print("Successfully removed {} traces.".format(cnt))