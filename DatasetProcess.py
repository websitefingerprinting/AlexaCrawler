import subprocess
import os
from os import makedirs
from os.path import join, abspath, dirname, pardir
import glob
import re
import argparse
import time
Pardir = abspath(join(dirname(__file__), pardir))

DumpDir = join( Pardir , "AlexaCrawler/dump")
def parse_arguments():

	parser = argparse.ArgumentParser(description='Crawl Alexa top websites and capture the traffic')

	parser.add_argument('dir',
						type=str,
						metavar='<batch dir>',
						help='bacth folders')
	parser.add_argument('-n',
						type=int,
						metavar='<num of web>',
						default =50,
						help='num of web')

	# Parse arguments
	args = parser.parse_args()
	return args

def init_directories(n):
    # Create a results dir if it doesn't exist yet
    if not os.path.exists(DumpDir):
        makedirs(DumpDir)

    # Define output directory
    timestamp = time.strftime('%m%d_%H%M')
    output_dir = join(DumpDir, 'dataset'+str(n)+'_'+timestamp)
    makedirs(output_dir)

    return output_dir

if __name__ == '__main__':
	args = parse_arguments()
	folders = args.dir
	raw = glob.glob(join(folders +"*", "*.pcap"))
	print("Total:{}".format(len(raw)))
	output_dir = init_directories(args.n)
	counter = [-1]*args.n
	# print(raw)
	for r in raw:
		filename = r.split("/")[-1].split(".pcap")[0]
		web_id,inst_id = filename.split("-")
		counter[int(web_id)] += 1
		new_inst_id = str(counter[int(web_id)])
		newfilename = web_id + "-" + new_inst_id + ".pcap"
		cmd = "cp " + r + " " +join(output_dir, newfilename)
		subprocess.call(cmd, shell=True)


