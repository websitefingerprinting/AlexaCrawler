from os.path import join
import os
import numpy as np
import subprocess
import multiprocessing as mp
import argparse
from PIL import Image
from pytesseract import image_to_string
from glob import glob
from itertools import compress
import re
keywords = ['accessdenied',
            'troubleshoot',
            'requestblock',
            'dnserror',
            'notarobot',
            'recaptcha',
            '[0-9][0-9][0-9]error',
            'error[0-9][0-9][0-9]',
            'oursystemshavedetectedunusualtraffic']

def parse_arguments():
    parser = argparse.ArgumentParser(description='Filter out error or captcha check by screenshot')

    parser.add_argument('dir',
                        type=str,
                        metavar='<dataset path>',
                        help='Path of dataset.')

    # Parse arguments
    args = parser.parse_args()
    return args

def check(fdir):
    txt = image_to_string(Image.open(fdir))
    txt = txt.replace(" ","").replace("\n"," ").lower()
    for keyword in keywords:
        if bool(re.search(keyword, txt)):
            return True
    return False

if __name__ == '__main__':
    args = parse_arguments()
    flist = glob(join(args.dir, "*.png"))
    # with mp.Pool(10) as p:
    #     filter = p.map(check, flist)
    filter = []
    for i,fdir in enumerate(flist):
        if i % 200 == 0:
            print("Complete {}/{}".format(i, len(flist)))
        filter.append(check(fdir))
    res = list(compress(flist, filter))
    subprocess.call("sudo chmod -R 777 "+args.dir, shell=True)
    cnt = 0
    for sdir in res:
        subprocess.call("rm "+sdir, shell=True)
        fdir = sdir.replace(".png",".cell")
        if os.path.exists(fdir):
            cnt += 1
            subprocess.call("rm " + fdir, shell=True)
    print("Remove {}/{} bad loadings.".format(cnt, len(flist)))
