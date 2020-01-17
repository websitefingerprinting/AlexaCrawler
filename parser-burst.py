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
dst1 = '13.75.95.89'
dst2 = '13.94.61.159'
dst3 = '52.175.53.148'
isDummy = 888
isReal = 1
pktSize = 612
#header 3 bytes
cellSize = 543 + 3 
ParsedDir = join(abspath(join(dirname(__file__), pardir)) , "AlexaCrawler/parsed")

def init_directories(path):
	# Create a results dir if it doesn't exist yet
	if not os.path.exists(path):
		makedirs(path)


def getTimestamp(pkt, t0):
	return float(pkt.time - t0)

def getPktType(pkt):
	return isDummy if pkt.load[0] else isReal

def getDirection(pkt):
	if pkt.payload.src == src:
		return 1
	elif (pkt.payload.src == dst1) or (pkt.payload.src == dst2) or (pkt.payload.src == dst3):
		return -1 
	else:
		raise ValueError("Wrong IP address!")

def correct_format(payload, b):
	if len(payload[b:]) <= 3:
		return False
	if payload[b] != 0 and payload[b] != 1:
		return False
	if int.from_bytes(payload[b+1:b+2],'big') > cellSize - 3:
		return False
	return True
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
	id_ = fdir.split('/')[-1].split('.pcap')[0]
	savefiledir = join(savedir, id_+suffix) 
	packets = rdpcap(fdir)
	# print(savefiledir)
	cnt = {1:0,-1:0}
	pkts = []
	for i, pkt in enumerate(packets):
		#skip the first few noise packets
		if  len(pkt) >= pktSize and getDirection(pkt)>0:
			start = i
			t0 = pkt.time
			# print("Start from pkt no. {}".format(start))
			break

	for i,pkt in enumerate(packets[start:]):
		#retransmission
		if len(pkt) < pktSize:
			print("{}: SKIP Pkt {}".format(id_,start+i))
			continue
		elif len(pkt) == pktSize:
			#one cell 
			timestamp = getTimestamp(pkt,t0)
			pkttype = getPktType(pkt)
			direction = getDirection(pkt)
			cnt[direction] += 1
			# f.write( "{:.4f}\t{:d}\n".format(timestamp, pkttype * direction))		
			pkts.append([timestamp,pkttype * direction ])			
		else:
			#len(pkt) > pktSize
			if getDirection(pkt) > 0 :
				#This can be very rare to happen, several outgoing packets got retransmitted
				#Treat them as all real packets
				num_pkt = np.math.ceil( len(pkt)/pktSize )
				timestamp = getTimestamp(pkt,t0)
				direction = getDirection(pkt)
				cnt[direction] += 1
				for _ in range(num_pkt):
					pkts.append([timestamp,isReal * direction])
					# f.write("{:.4f}\t{:d}\n".format(timestamp, isReal * direction))
			else:
				#multiple incoming cells
				payload = pkt.load
				timestamp = getTimestamp(pkt,t0)
				if correct_format(payload, 0) and len(payload)%cellSize != 0:
					raise ValueError("BUG: {}: pkt {}".format(id_,i+start))
				for b in range(0, len(payload), cellSize):
					if not correct_format(payload, b):
						print("{}: SKIP Pkt {}".format(id_, start+i))
						break
					pkttype = isDummy if payload[b] else isReal
					cnt[-1] += 1
					# f.write("{:.4f}\t{:d}\n".format(timestamp, pkttype * (-1))) 
					pkts.append([timestamp, pkttype * (-1)])


	if cnt[1] < 5 and cnt[-1]< 5:
		print("{} has too few packets:+{},-{}".format(savefiledir, cnt[1],cnt[-1]))

	pkts_array1 = np.array(pkts)
	pkts_array2 = pkts_array1[1:]
	time_diffs = pkts_array2[:,0] - pkts_array1[:-1,0]
	tmp = np.where(time_diffs > 1)[0]
	if len(tmp) == 0:
		cut_off_ind = len(pkts)
	else:
		cut_off_ind = tmp[-1]
	print("{}: cut off at {}/{}".format(id_, cut_off_ind,len(pkts)))
	with open(savefiledir, 'w') as f:
		for pkt in pkts[:cut_off_ind]:
			f.write("{:.6f}\t{:d}\n".format(pkt[0],pkt[1])) 



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



