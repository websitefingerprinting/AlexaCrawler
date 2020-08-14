import os
from os import makedirs
import argparse
from common import *

UNMON_NUM = 10000

def init_directories(name):
	# Create a results dir if it doesn't exist yet
	if not os.path.exists(ListDir):
		makedirs(ListDir)

	# Define output directory
	output_dir = join(ListDir, name+".list")
	# makedirs(output_dir)

	return output_dir
def parse_arguments():

	parser = argparse.ArgumentParser(description='Pick good examples.')

	parser.add_argument('dir',
						type=str,
						metavar='<dataset path>',
						help='Path of dataset.')
	parser.add_argument('-format',
						type=str,
						metavar='<suffix>',
						default='.cell',
						help='suffix of files')
	parser.add_argument('-i',
						default=False,
						action='store_true',
						help='Count file in or not in the range. (default: not)')
	# Parse arguments
	args = parser.parse_args()
	return args

if __name__ == '__main__':
	args = parse_arguments()
	name = args.dir.rstrip('/').split('/')[-1]
	outputdir  = init_directories(name)
	l = []
	for i in range(UNMON_NUM):
		fname = join(args.dir, str(i)+args.format)
		if args.i:
			if os.path.exists(fname):
				l.append(i)
		else:
			if not os.path.exists(fname):
				l.append(i)

	with open(outputdir,"w") as f:
		for i in l:
			f.write("{:d}\n".format(i))
	print("Output to {}".format(outputdir))