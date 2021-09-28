import subprocess
import os
from os.path import join
import numpy as np

undefended = [
    'udataset0_14000_0909_131435',
    'udataset14000_28000_0913_140751',
    'udataset28000_41000_0917_134236',
    'udataset41000_53000_0921_113335',
    'udataset53000_60000_0924_220701',
]

tamaraw = [
    'udataset0_14000_0910_142747',
    'udataset14000_28000_0914_164409',
    'udataset28000_41000_0918_133455',
    'udataset41000_53000_0922_153343',
    'udataset53000_60000_0925_110045',
]

front = [
    'udataset0_14000_0911_145839',
    'udataset14000_28000_0915_171955',
    'udataset28000_41000_0919_170332',
    'udataset41000_53000_0924_110452',
    'udataset53000_60000_0926_111457',
]

wfgan = [
    'udataset0_14000_0912_154122',
    'udataset14000_28000_0916_170452',
    'udataset28000_41000_0920_151238',
    'udataset41000_53000_0924_111719',
    'udataset53000_60000_0926_232930',
]

par_dir = '/ssd/jgongac/AlexaCrawler/parsed'
output_dir = '/ssd/jgongac/AlexaCrawler/parsed'
start = 0
end = 60000


def combine_script(flist):
    flist_str = ' '.join(flist)
    cmd = 'python3 /ssd/jgongac/AlexaCrawler/combine.py -dir {} -start {} -end {} -o {} -u -d'.format(
        flist_str, start, end, output_dir
    )
    print(cmd)
    print()
    subprocess.call(cmd, shell=True)


def check_list(flist):
    new_list = []
    for fname in flist:
        if not os.path.exists(join(par_dir, fname)):
            assert FileExistsError(par_dir, fname)
        new_list.append(join(par_dir, fname))
    return new_list


# first check existence
undefended_abs = check_list(undefended)
tamaraw_abs = check_list(tamaraw)
front_abs = check_list(front)
wfgan_abs = check_list(wfgan)

# make sure did not mistakenly use the same folder for some defenses
assert len(np.unique(undefended + tamaraw + front + wfgan)) == len(undefended) + len(tamaraw) + len(front) + len(wfgan)

# combine
combine_script(undefended_abs)
combine_script(tamaraw_abs)
combine_script(front_abs)
combine_script(wfgan_abs)
