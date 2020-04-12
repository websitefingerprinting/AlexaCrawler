import multiprocessing as mp 
import logging
import os
from os import makedirs
from os.path import join, abspath, dirname, pardir
import numpy as np
import subprocess
import argparse
import glob
import pandas as pd
import time
ParsedDir = join(abspath(join(dirname(__file__), pardir)) , "AlexaCrawler/parsed")
UNMON_NUM = 10000
def init_directories():
	timestamp = time.strftime('%m%d_%H%M')
	outputdir = join(ParsedDir, "picked_"+timestamp)
	# Create a results dir if it doesn't exist yet
	if not os.path.exists(outputdir):
		makedirs(outputdir)
	return outputdir


def parse_arguments():

	parser = argparse.ArgumentParser(description='Pick good examples from multiple unmon sample.')

	parser.add_argument('-dir',
						nargs='+',
						type=str,
						metavar='<batch dir>',
						dest = 'dirlist',
						default = [],
						help='bacth folders')
	parser.add_argument('-suffix',
						type=str,
						metavar='<parsed file suffix>',
						default='.cell',
						help='to save file as xx.suffix')
	# Parse arguments
	args = parser.parse_args()
	return args


def analyse(fdir):
	global folders, outputdir
	maxlen = -1
	picked = 0
	for i,folder in enumerate(folders):
		path = join(folder, fdir)
		if os.path.exists(path):
			with open(path,'r') as f:
				l = len(f.readlines())
			if l > maxlen:
				maxlen = l
				picked = i
	if maxlen > 0 :
		cmd = "cp " + join(folders[picked], fdir) + " "+outputdir
		subprocess.call(cmd, shell = True)
	# print(cmd)
	
if __name__ == "__main__":
	global folders, outputdir
	args = parse_arguments()
	folders = args.dirlist
	flist = []
	for i in range(UNMON_NUM):
		flist.append(str(i)+args.suffix)
	outputdir = init_directories()
	pool = mp.Pool(processes=15)
	pool.map(analyse, flist)
	print("Output to {}".format(outputdir))

	








