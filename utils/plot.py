import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(description='Trim the noisy traces.')

    parser.add_argument('-dir',
                        type=str,
                        required=True,
                        metavar='<dataset path>',
                        help='Path of dataset.')
    # Parse arguments
    args = parser.parse_args()
    return args

if __name__ == '__main__':
    args = parse_arguments()
    with open(args.dir,'r') as f:
        lines = f.readlines()
    arr = np.array(pd.Series(lines).str.slice(0,-1).str.split("\t",expand=True).astype(float))
    print(arr.shape)
    out_arr = arr[:,1::5]
    in_arr = arr[:,2::5]
    trimmed_arr = arr[:,3::5]
    total_arr = arr[:,4::5]
    print(out_arr.shape)
    bad_cut_rate_out = (out_arr>0).sum(axis=0)/len(out_arr)
    bad_cut_rate_in = (in_arr > 0).sum(axis=0) / len(in_arr)
    print(bad_cut_rate_out,bad_cut_rate_in)
    print((bad_cut_rate_out+bad_cut_rate_in)/2)
    print(trimmed_arr[:,4],total_arr[:,4])
    print(trimmed_arr[:,4].sum()/total_arr[:,4].sum())
    # out_arr_mean = out_arr.mean(axis=0)
    # out_arr_std = out_arr.std(axis=0)
    # in_arr_mean =in_arr.mean(axis=0)
    # in_arr_std = in_arr.std(axis=0)
    # print(out_arr_mean, in_arr_mean)

    # x = 5 - np.arange(0,out_arr.shape[1],1)
    # plt.xticks(x)
    # plt.plot(x, out_arr_mean, 'r--', x, in_arr_mean,'bs-',x, list([0]*(out_arr.shape[1])),'-')

    # plt.show()