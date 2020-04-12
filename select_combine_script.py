import subprocess
from os.path import join, abspath, dirname, pardir
Pardir = abspath(join(dirname(__file__), pardir))
pdir = join(Pardir, "AlexaCrawler/parsed")

mode = 'unmon'
params = [
# [20, 100, 0.5 , 6 ],
# [20, 100, 0.5 , 8 ],
# [20, 100, 0.5 , 4 ],
# [20, 100, 0.5 , 10],
[20, 100, 0.05, 6 ],
[20, 100, 1   , 6 ],
[20, 100, 2   , 6 ],
[20, 200, 0.5 , 6 ],
[20, 0  , 0.5 , 6 ],
[20, 300, 0.5 , 6 ],
]


d50 = [
"unmon_0304_2342/",
"unmon_0305_2310/",
"unmon_0310_1336/",
"unmon_0306_2315/",
"unmon_0308_0910/",
"unmon_0309_1421/",
]

d100 = [
"unmon_0327_1558/",
"unmon_0319_2225/",
"unmon_0322_0112/",
"unmon_0324_2233/",
"unmon_0325_1124/",
"unmon_0326_1049/",
]


for param, d1,d2 in zip(params, d50, d100):
	t, l , e, w = param[0],param[1],param[2],param[3]
	d1,d2 = join(pdir, d1),join(pdir, d2)
	cmd = "python3 selected_combine.py -dir " + d1 + " " + d2 + " " + " -t " \
	+ str(t) + " -l " + str(l) + " -e " + str(e) + " -w " + str(w) + " -mode " + mode
	# print(cmd)
	subprocess.call(cmd, shell = True)
	

