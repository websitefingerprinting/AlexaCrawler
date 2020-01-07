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

src = '10.0.0.4'
dst = '13.94.61.159'
cell_size = 512
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
			ind = 0
			cell_num = 0			
			timestamp = getTimestamp(pkt,t0)
			direction = getDirection(pkt)
			b = pkt.load
			while ind < len(b):
				if b[ind:ind+1] == b'\x17' and b[ind+1:ind+3] == b'\x03\x03':
					message_len = int.from_bytes(b[ind+3:ind+5], 'big')
					cell_num += message_len
					ind += message_len + 5
				else:
					break				
			cell_num = cell_num // cell_size 
			cnt[direction] += cell_num       
			for _ in range(cell_num):
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



