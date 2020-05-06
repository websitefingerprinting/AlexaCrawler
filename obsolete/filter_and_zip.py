import multiprocessing as mp 
import logging
import os
from os.path import join
import numpy as np
import subprocess
import argparse
from scapy.all import *
import glob
import subprocess


def parse_arguments():

	parser = argparse.ArgumentParser(description='Remove retransmission and ACKS')

	parser.add_argument('dir',
						type=str,
						metavar='<dataset path>',
						help='Path of dataset.')

	# Parse arguments
	args = parser.parse_args()
	return args


def clean(fdir):
	global pardir
	tmpname = fdir.split("/")[-1]
	tmpname  = "filter_"+tmpname
	tmpdir = join(pardir, tmpname)
	cmd = 'tshark -r '+ fdir +' -Y "not(tcp.analysis.retransmission or tcp.len == 0 )" -w ' + tmpdir
	subprocess.call(cmd, shell= True)
	subprocess.call("rm -f "+fdir,shell =True)
	subprocess.call("mv "+tmpdir+" "+fdir,shell=True)

if __name__ == "__main__":
	global pardir 
	args = parse_arguments()
	pardir = args.dir
	filelist = glob.glob(join(args.dir, '*.pcap'))
	pool = mp.Pool(processes=15)
	print("Filter..")
	pool.map(clean, filelist)
	print("Zip..")
	filename = pardir.rstrip('/')+'.zip'
	zipcmd = "zip -rq "+ filename + " " + pardir
	subprocess.call(zipcmd, shell=True)



