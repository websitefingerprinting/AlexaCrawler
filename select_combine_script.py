import subprocess
from os.path import join, abspath, dirname, pardir
Pardir = abspath(join(dirname(__file__), pardir))
pdir = join(Pardir, "AlexaCrawler/parsed")

mode = 'mon'
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
"dataset0_49_0113_1203/",
"dataset0_49_0114_1533/",
"dataset0_49_0116_1204/",
"dataset0_49_0117_1622/",
"dataset0_49_0119_2217/",
"dataset0_49_0124_1242/",
"dataset0_49_0125_1144/",
"dataset0_49_0127_1832/",
"dataset0_49_0131_1520/",
"dataset0_49_0202_1834/",
]

d100 = [
"dataset50_99_0207_1427/",
"dataset50_99_0209_2345/",
"dataset50_99_0209_2347/",
"dataset50_99_0211_1250/",
"dataset50_99_0211_1208/",
"dataset50_99_0212_1250/",
"dataset50_99_0212_1249/",
"dataset50_99_0213_1715/",
"dataset50_99_0213_2103/",
"dataset50_99_0215_1432/",
]

d150 = [
"dataset100_149_0216_1150/",
"dataset100_149_0216_1133/",
"None/",
"dataset100_149_0218_1422/",
"dataset100_149_0218_1940/",
"dataset100_149_0220_1412/",
"dataset100_149_0220_0014/",
"dataset100_149_0221_1651/",
"dataset100_149_0301_1040/",
"dataset100_149_0229_2241/",
]

for param, d1,d2,d3 in zip(params, d50,d100,d150):
	if d3 == "None/":
		continue
	t, l , e, w = param[0],param[1],param[2],param[3]
	d1,d2,d3 = join(pdir, d1),join(pdir, d2), join(pdir, d3)
	cmd = "python3 selected_combine.py -dir " + d1 + " " + d2 + " " + d3 + " -t " \
	+ str(t) + " -l " + str(l) + " -e " + str(e) + " -w " + str(w) + " -mode " + mode
	# print(cmd)
	subprocess.call(cmd, shell = True)

