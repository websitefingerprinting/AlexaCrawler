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

ParsedDir = join(abspath(join(dirname(__file__), pardir)) , "AlexaCrawler/parsed")
def init_directories(outputdir):
	# Create a results dir if it doesn't exist yet
	if not os.path.exists(outputdir):
		makedirs(outputdir)



def parse_arguments():

	parser = argparse.ArgumentParser(description='Pick good examples.')

	parser.add_argument('dir',
						type=str,
						metavar='<dataset path>',
						help='Path of dataset.')
	parser.add_argument('-m',
						type=int,
						default=100,
						metavar='<Num of examples wanted>',
						help='Num of examples wanted out of all.')
	parser.add_argument('-suffix',
						type=str,
						metavar='<parsed file suffix>',
						default='.cell',
						help='to save file as xx.suffix')
	# Parse arguments
	args = parser.parse_args()
	return args


def analyse(fdir):
	with open(fdir , 'r') as f:
		l = len(f.readlines())
	name = fdir.split("/")[-1]
	if '-' in name:
		label = int(name.split("-")[0])
	else:
		label = -1
	return [label, fdir, l]

if __name__ == "__main__":
	args = parse_arguments()
	filelist = glob.glob(join(args.dir, '*'+args.suffix))
	outputdir = args.dir.rstrip("/") + "_picked/"
	init_directories(outputdir)
	pool = mp.Pool(processes=15)
	info = pool.map(analyse, filelist)
	info = pd.DataFrame(info,columns = ['label','fdir','l'])
	maxlabel = info.label.max()+1
	print("max",maxlabel)
	info.sort_values(['label','l'], ascending = [True,True],inplace=True)
	grouped = info.groupby('label')
	counter = [0]*maxlabel
	for name, group in grouped:
		length = len(group)
		if length > args.m:
			selected = group.iloc[length//2+args.m//2 - args.m :length//2+args.m//2,:].fdir
			print("[{},{}] out of [0,{}]".format(length//2+args.m//2 - args.m, length//2+args.m//2,length))
		else:
			selected = group.fdir
		for f in selected:
			oldname = f.split("/")[-1].split(args.suffix)[0]
			#mon
			label = int(oldname.split("-")[0])
			instnum = counter[label]
			counter[label] += 1
			newname = str(label) + "-" + str(instnum) + args.suffix
			cmd = "cp " + f + " " + join(outputdir, newname)

			subprocess.call(cmd, shell= True)








