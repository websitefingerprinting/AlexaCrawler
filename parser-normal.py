import multiprocessing as mp 
import logging
import os
from os import makedirs
from os.path import join, abspath, dirname, pardir
import numpy as np
import subprocess
import argparse
from scapy.all import *
import glob
#without parse packets, count pkts by bytes

src = '10.0.0.4'
dst = '13.75.95.89'
cellSize = 546
ParsedDir = join(abspath(join(dirname(__file__), pardir)) , "AlexaCrawler/parsed")

def init_directories(path):
	# Create a results dir if it doesn't exist yet
	if not os.path.exists(path):
		makedirs(path)


def getTimestamp(pkt, t0):
	return float(pkt.time - t0)



def getDirection(pkt):
	if pkt.payload.src == src:
		return 1
	elif pkt.payload.src == dst:
		return -1 
	else:
		raise ValueError("Wrong IP address!")


def parse_arguments():

	parser = argparse.ArgumentParser(description='Parse captured traffic.')

	parser.add_argument('dir',
						type=str,
						metavar='<dataset path>',
						help='Path of dataset.')
	parser.add_argument('-suffix',
						type=str,
						metavar='<parsed file suffix>',
						default='.cell',
						help='to save file as xx.suffix')

	# Parse arguments
	args = parser.parse_args()
	return args


def parse(fdir):
	global savedir, suffix
	savefiledir = join(savedir, fdir.split('/')[-1].split('.pcap')[0]+suffix) 
	packets = rdpcap(fdir)
	print(savefiledir)
	cnt = {1:0,-1:0}
	with open(savefiledir, 'w') as f:
		for i, pkt in enumerate(packets):
			#skip the first few noise packets
			if getDirection(pkt)>0 :
				start = i
				t0 = pkt.time
				print("Start from pkt no. {}".format(start))
				break
		for i, pkt in enumerate(packets[start:]):
			try:
				num_pkt = int(np.round( len(pkt.load)/cellSize ))
			except:
				continue
			timestamp = getTimestamp(pkt,t0)
			direction = getDirection(pkt)
			cnt[direction] += 1
			for _ in range(num_pkt):
				f.write("{:.4f}\t{:d}\n".format(timestamp, direction))
	if cnt[1] < 5 and cnt[-1]< 5:
		print("{} has too few packets:+{},-{}".format(savefiledir, cnt[1],cnt[-1]))

if __name__ == "__main__":
	global savedir, suffix
	args = parse_arguments()
	suffix = args.suffix
	filelist = glob.glob(join(args.dir, '*.pcap'))
	filename = args.dir.split("/")[-2]
	savedir = join(ParsedDir, filename)
	init_directories(savedir)

	# for f in filelist:
	# 	parse(f)

	pool = mp.Pool(processes=15)
	pool.map(parse, filelist)



