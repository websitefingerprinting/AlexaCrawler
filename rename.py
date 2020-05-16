import subprocess
import os
from os import makedirs
from os.path import join, abspath, dirname, pardir
import glob
import re
import argparse
import time

MON_SITE_NUM = 100
def parse_arguments():

    parser = argparse.ArgumentParser(description='Crawl Alexa top websites and capture the traffic')

    parser.add_argument('dir',
                        type=str,
                        metavar='<batch dir>',
                        help='bacth folders')
    parser.add_argument('-m',
                        action='store_true', 
                        default=False,
                        help='The type of dataset: is mon or unmon?.')
    parser.add_argument('-n0',
                        type = int,
                        default=0,
                        help='initial index.')
    parser.add_argument('-format',
                        type=str,
                        metavar='<file suffix>',
                        default = '.cell',
                        help='bacth folders')  
    # Parse arguments
    args = parser.parse_args()
    return args



if __name__ == '__main__':
    args = parse_arguments()
    l = []
    cnt = 0
    flist = []
    if args.m:
        #mon page
        for i in range(MON_SITE_NUM):
            flist_cls = glob.glob(join(args.dir, str(i) +  '-' + '*'+args.format))
            if len(flist_cls) > 0:
                l.append(i)
                flist.append(flist_cls)
                cnt += len(flist_cls)
        print("Total {} webs".format(cnt))
        assert len(l) == len(flist)
        for new_index, old_label in enumerate(l):
            new_label  = new_index + args.n0
            if new_label == old_label:
                continue
            flist_cls = flist[new_index]
            for f in flist_cls:
                filename = f.split("/")[-1].split(args.format)[0]
                old_label_, old_inst = filename.split("-")
                assert int(old_label_) == old_label
                new_f = join(args.dir, str(new_label)+'-'+old_inst+args.format)
                cmd = "mv " + f + " " + new_f
                subprocess.call(cmd, shell = True)




