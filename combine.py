import subprocess
import os
from os import makedirs
from os.path import join, abspath, dirname, pardir
import glob
import re
import argparse
import time

Pardir = abspath(join(dirname(__file__), pardir))


def parse_arguments():
    parser = argparse.ArgumentParser(description='Crawl Alexa top websites and capture the traffic')

    parser.add_argument('-dir',
                        nargs='+',
                        type=str,
                        metavar='<batch dir>',
                        dest='dirlist',
                        default=[],
                        help='bacth folders')
    parser.add_argument('-start',
                        type=int,
                        metavar='<start ind>',
                        default=0,
                        help='Start from which site in the list (include this ind).')
    parser.add_argument('-end',
                        type=int,
                        metavar='<end ind>',
                        default=100,
                        help='End to which site in the list (exclude this ind).')
    parser.add_argument('-d',
                        action='store_false',
                        default=True,
                        help='Delete original folders after the merge? (default:True)')
    parser.add_argument('-s',
                        action='store_true',
                        default=False,
                        help='Keep a copy of original screenshots? (default:False)')
    parser.add_argument('-u',
                        action='store_true',
                        default=False,
                        help='is monitored webpage or unmonitored? (default:is monitored, False)')
    parser.add_argument('-o',
                        default='./',
                        help='Output combined results to which parent folder? ')
    parser.add_argument('-gap',
                        type=int,
                        default=1,
                        help='Should be 1 in most cases, but if you represent one class with several webpages, '
                             'change it to the correct number.')
    parser.add_argument('-suffix',
                        type=str,
                        metavar='<suffix>',
                        default='.cell',
                        help='suffix of the file')

    # Parse arguments
    args = parser.parse_args()
    return args


def init_directories(start, end, gap, u):
    global DumpDir
    # Create a results dir if it doesn't exist yet
    if not os.path.exists(DumpDir):
        makedirs(DumpDir)
    if u:
        prefix = "u"
    else:
        prefix = ""
    # Define output directory
    timestamp = time.strftime('%m%d_%H%M%S')
    if gap != 1:
        output_dir = join(DumpDir, prefix + 'dataset' + str(start) + '_' + str(end) + '_' + str(gap) + '_' + timestamp)
    else:
        output_dir = join(DumpDir, prefix + 'dataset' + str(start) + '_' + str(end) + '_' + timestamp)
    makedirs(output_dir)

    return output_dir


if __name__ == '__main__':
    global DumpDir

    args = parse_arguments()
    if args.o:
        DumpDir = args.o
    else:
        # default
        DumpDir = join(Pardir, "AlexaCrawler/parsed")
    folders = list(set(args.dirlist))  # remove duplicates
    raw = []
    for folder in folders:
        raw += glob.glob(join(folder, "*" + args.suffix))
    print("Total:{}".format(len(raw)))
    output_dir = init_directories(args.start, args.end, args.gap, args.u)
    cls_num = args.end // args.gap
    counter = [0] * cls_num
    # print(raw)
    for r in raw:
        filename = r.split("/")[-1].split(args.suffix)[0]
        if args.u:
            web_id = filename
            newfilename = filename + args.suffix
        else:
            web_id, inst_id = filename.split("-")
            web_id = str(int(web_id) // args.gap)
            new_inst_id = str(counter[int(web_id)])
            newfilename = web_id + "-" + new_inst_id + args.suffix

        command = "cp "

        cmd = command + r + " " + join(output_dir, newfilename)
        subprocess.call(cmd, shell=True)

        origin_screen_dir = r.replace(args.suffix, ".png")
        if args.s and os.path.exists(origin_screen_dir):
            new_screen_dir = join(output_dir, newfilename).replace(args.suffix, ".png")
            cmd = command + origin_screen_dir + " " + new_screen_dir
            subprocess.call(cmd, shell=True)

        counter[int(web_id)] += 1
    for i in range(len(counter)):
        if counter[i] > 0 and not args.u:
            print("#{}:{}".format(i, counter[i]))
    print("Merged to {}".format(output_dir))

    if args.d:
        for folder in folders:
            subprocess.call("rm -r " + folder, shell=True)
        print("Remove original folders.")
