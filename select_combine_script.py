import subprocess
from os.path import join, abspath, dirname, pardir
Pardir = abspath(join(dirname(__file__), pardir))
pdir = join(Pardir, "AlexaCrawler/parsed")

mode = 'unmon'
params = [
[20, 100, 0.5 , 6 ],
[20, 100, 0.5 , 8 ],
[20, 100, 0.5 , 4 ],
[20, 100, 0.5 , 10],
[20, 100, 0.05, 6 ],
[20, 100, 1   , 6 ],
[20, 100, 2   , 6 ],
[20, 200, 0.5 , 6 ],
[20, 0  , 0.5 , 6 ],
[20, 300, 0.5 , 6 ],
]


d50 = [
"unmon_0303_1342/",
"unmon_0303_1536/",
"unmon_0303_1901/",
"unmon_0305_1747/",
]

d100 = [
"unmon_0315_2254/",
"unmon_0316_2158/",
"unmon_0314_2218/",
"unmon_0317_2001/",
]


for param, d1,d2 in zip(params, d50, d100):
	t, l , e, w = param[0],param[1],param[2],param[3]
	d1,d2 = join(pdir, d1),join(pdir, d2)
	cmd = "python3 selected_combine.py -dir " + d1 + " " + d2 + " " + " -t " \
	+ str(t) + " -l " + str(l) + " -e " + str(e) + " -w " + str(w) + " -mode " + mode
	# print(cmd)
	subprocess.call(cmd, shell = True)
	

