import subprocess
import os
from os import makedirs
from os.path import join, abspath, dirname, pardir
import glob
import re
import argparse
import time
import numpy as np
Pardir = abspath(join(dirname(__file__), pardir))
selected_mon_list_file = join(Pardir, "AlexaCrawler/utils/selected_mon.npy")
selected_unmon_list_file = join(Pardir, "AlexaCrawler/utils/selected_unmon.npy")
targetdir = join(Pardir, "AlexaCrawler/dataset/")
selected_mon_list = np.load(selected_mon_list_file)
selected_unmon_list = np.load(selected_unmon_list_file)
DumpDir = join( Pardir , "AlexaCrawler/dataset")
def parse_arguments():

	parser = argparse.ArgumentParser(description='Crawl Alexa top websites and capture the traffic')

	parser.add_argument('-dir',
						nargs='+',
						type=str,
						metavar='<batch dir>',
						dest = 'dirlist',
						default = [],
						help='bacth folders')
	parser.add_argument('-mode',
						type=str,
						metavar='<mode>',
						default='mon',
						help='monitor or unmonitor:mon, unmon')	
	parser.add_argument('-dataset',
						type=str,
						metavar='<dataset type>',
						default='dp',
						help='clean or defended?:clean, dp, tamaraw')	
	parser.add_argument('-t',
						type=str,
						metavar='<T>',
						default='20',
						help='param T')	
	parser.add_argument('-e',
						type=str,
						metavar='<epsilon>',
						default='05',
						help='param epsilon')	
	parser.add_argument('-l',
						type=str,
						metavar='<L>',
						default='100',
						help='param L')	
	parser.add_argument('-w',
						type=str,
						metavar='<W>',
						default='6',
						help='param W')	

	parser.add_argument('-suffix',
						type=str,
						metavar='<suffix>',
						default='.cell',
						help='suffix of the file')

	# Parse arguments
	args = parser.parse_args()
	return args

def init_directories(mode, t, l, e, w):
    # Create a results dir if it doesn't exist yet
    if not os.path.exists(DumpDir):
        makedirs(DumpDir)

    # Define output directory
    # timestamp = time.strftime('%m%d_%H%M')
    if args.dataset == 'clean':
    	output_dir = join(DumpDir, mode+"_clean")
    elif args.dataset == 'tamaraw':
    	output_dir = join(DumpDir, mode+"_tamaraw")
    elif args.dataset == 'dp':
    	output_dir = join(DumpDir, mode+"_T"+t+"_L"+l+"_E"+e+"_W"+w)
    else:
    	raise ValueError("Wrong dataset type!")
    makedirs(output_dir)

    return output_dir

if __name__ == '__main__':
	args = parse_arguments()
	folders = args.dirlist
	output_dir = init_directories(args.mode, args.t, args.l, args.e, args.w)
	print("Mode:{}, Create fold {}".format(args.mode,output_dir))
	if args.mode == 'mon':
		selected_list = selected_mon_list
	else: 
		selected_list = selected_unmon_list
	for folder in folders:
		files = glob.glob(join(folder, "*"+args.suffix))
		for file in files:
			if args.mode == 'mon':
				tmp = file.split("/")[-1].split(args.suffix)[0]
				oldlabel = int(tmp.split("-")[0])
				oldinst  = int(tmp.split("-")[1])

				if oldlabel in selected_list:
					newlabel = np.where(selected_list==oldlabel)[0][0]
					newfiledir = join( output_dir, str(newlabel) + '-' + str(oldinst) +args.suffix)
					cmd = "cp " + file + " " + newfiledir
					# print(cmd)
					subprocess.call(cmd, shell = True) 
			else:
				oldlabel = int(file.split("/")[-1].split(args.suffix)[0])
				if oldlabel in selected_list:
					newlabel = np.where(selected_list==oldlabel)[0][0]
					newfiledir = join( output_dir, str(newlabel) +args.suffix)
					cmd = "cp " + file + " " + newfiledir
					# print(cmd)
					subprocess.call(cmd, shell = True) 
	
	if args.mode == 'unmon':
		tmp = output_dir.rstrip("/").split("/")[-1]
		mon_dir = join(targetdir, "mon_" + tmp.split("unmon_")[-1])
		cmd = "mv " + join(output_dir, "*") +  " " + mon_dir
		# print(cmd)
		
		subprocess.call(cmd,shell=True)
