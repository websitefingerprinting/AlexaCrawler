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

src = '192.168.0.151'
dst = '65.49.20.10'
CELL_SIZE = 512
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
	try:
		with open(savefiledir, 'w') as f:
			for i, pkt in enumerate(packets):
				#skip the first few noise packets
				if getDirection(pkt)>0 :
					start = i
					t0 = pkt.time
					print("Start from pkt no. {}".format(start))
					break

			for i, pkt in enumerate(packets[start:]):
				b = raw(pkt.payload.payload.payload)
				byte_ind = b.find(b'\x17\x03\x03')
				while byte_ind != -1 and byte_ind < len(b):
					if b[byte_ind:byte_ind + 3] == b'\x17\x03\x03':
						TLS_LEN = int.from_bytes(b[byte_ind+3:byte_ind+5], 'big')
						cur_time = getTimestamp(pkt,t0)
						cur_dir = getDirection(pkt)
						#complete TLS record
						cell_num = TLS_LEN /CELL_SIZE
						cell_num = int(np.round(cell_num))
					 
						for i in range(cell_num):
							f.write("{:.6f}\t{:d}\n".format(cur_time, cur_dir))
						byte_ind += TLS_LEN + 5
					else:
						#What happened here?
						break
	except:
		print("Error in {}".format(fdir.split('/')[-1]))





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



