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

src1 = '10.0.0.4'
src2 = '10.0.0.5'
src3 = '10.0.0.6'
src4 = '10.0.0.7'
# dst1 = '52.175.52.248'
# dst2 = '13.94.61.159'
# dst3 = '52.175.53.148'
# dst4 = '52.175.21.5'
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


def getDirection(pkt):
	if (pkt.payload.src == src1) or (pkt.payload.src == src2) or (pkt.payload.src == src3) or (pkt.payload.src == src4):
		return 1
	else:
		return -1 
	# else:
	# 	raise ValueError("Wrong IP address!")

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

	# #remove acks and retransmissions
	# cmd = 'tshark -r '+ fdir+ ' -Y "not(tcp.analysis.retransmission or tcp.len == 0 )" -w '+ fdir
	# subprocess.call(cmd, shell=True)
	packets = rdpcap(fdir)
	# print(savefiledir)

	for i, pkt in enumerate(packets):
		#skip the first few noise packets
		if  getDirection(pkt)>0:
			start = i
			t0 = pkt.time
			# print("Start from pkt no. {}".format(start))
			break

	

	in_pkts_raw = []
	in_pkts = []
	out_pkts = []
	for i,pkt in enumerate(packets[start:]):
		payload = pkt.load
		dire = getDirection(pkt)
		t = getTimestamp(pkt, t0)
		if dire == 1:
			#outgoing packet, only one case: 612 bytes (546 payload)
			if len(payload) == cellSize:
				if payload[0] == 0:
					out_pkts.append([t, isReal])
				elif payload[0] == 1:
					out_pkts.append([t, isDummy])
				else:
					raise ValueError("FORMAT ERROR: {},{} pkt ,payload:{}".format(id_, start+i,payload))
			else:
				# rarely happen, several outgoing together, probably congestion?
				for b in range(0, len(payload), cellSize):
					pkttype = isDummy if payload[b] else isReal
					out_pkts.append([t, pkttype])	
				print("[WARN] Several outgoing: {},{} pkt ,len of payload:{}".format(id_,start+i, len(payload)))
		else:
			#incoming ones are more complicated, first collect raw packets
			in_pkts_raw.append([t, payload])

	#process incoming ones 
	ind = 0
	while ind < len(in_pkts_raw):
		base_pkt = in_pkts_raw[ind]
		base_time = base_pkt[0]
		base_payload = base_pkt[1]
		while ind < len(in_pkts_raw)-1 and len(base_payload) % cellSize != 0:
			#fragment
			ind += 1
			tmp_pkt = in_pkts_raw[ind]
			base_payload += tmp_pkt[1]

		for b in range(0, len(base_payload), cellSize):
			pkttype = isDummy if base_payload[b] else isReal
			in_pkts.append([base_time, pkttype * (-1)])			
		ind += 1

	#sort packets
	total_pkts_unsorted = np.array(in_pkts + out_pkts)
	total_pkts0 = total_pkts_unsorted[total_pkts_unsorted[:,0].argsort(kind = "mergesort")]

	#Cut off last few packets (1s away from their predecessor)
	total_pkts1 = total_pkts0[1:]
	time_diffs = total_pkts1[:,0] - total_pkts0[:-1,0]
	tmp = np.where(time_diffs > 1)[0]
	if len(tmp) == 0:
		cut_off_ind = len(total_pkts0)
	else:
		cut_off_ind = tmp[-1]
		print("{}: cut off at {}/{}".format(id_, cut_off_ind,len(total_pkts0)))
	with open(savefiledir, 'w') as f:
		for pkt in total_pkts0[:cut_off_ind]:
			f.write("{:.6f}\t{:.0f}\n".format(pkt[0],pkt[1])) 	




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



