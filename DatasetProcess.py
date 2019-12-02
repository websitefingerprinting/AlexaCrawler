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
	parser.add_argument('-n0',
						type=int,
						metavar='<start page>',
						default=0,
						help='Crawl n0 to n0+n-1 webpages')
	parser.add_argument('-suffix',
						type=str,
						metavar='<suffix>',
						default='.pcap',
						help='suffix of the file')

	# Parse arguments
	args = parser.parse_args()
	return args

def init_directories(n,n0):
    # Create a results dir if it doesn't exist yet
    if not os.path.exists(DumpDir):
        makedirs(DumpDir)

    # Define output directory
    timestamp = time.strftime('%m%d_%H%M')
    output_dir = join(DumpDir, 'dataset'+str(n0)+'_'+str(n+n0-1)+'_'+timestamp)
    makedirs(output_dir)

    return output_dir

if __name__ == '__main__':
	args = parse_arguments()
	folders = args.dir
	raw = glob.glob(join(folders +"*", "*"+args.suffix))
	print("Total:{}".format(len(raw)))
	output_dir = init_directories(args.n,args.n0)
	counter = [-1]*(args.n+args.n0)
	# print(raw)
	for r in raw:
		filename = r.split("/")[-1].split(args.suffix)[0]
		web_id,inst_id = filename.split("-")
		counter[int(web_id)] += 1
		new_inst_id = str(counter[int(web_id)])
		newfilename = web_id + "-" + new_inst_id + args.suffix
		cmd = "mv " + r + " " +join(output_dir, newfilename)
		subprocess.call(cmd, shell=True)


