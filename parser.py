import multiprocessing as mp 
import logging
import os
from os import makedirs
from os.path import join, abspath, dirname, pardir
import numpy as np
import subprocess
import argparse
from scapy.all import *
import glob
from common import My_Source_Ips



CELL_SIZE = 512
#CELL+ TLS HEADER + MY HEADER
MY_CELL_SIZE = CELL_SIZE + 31 + 3
isDummy = 888
isReal = 1

captured_file_name = '.pcap.filtered'
ParsedDir = join(abspath(join(dirname(__file__), pardir)) , "AlexaCrawler/parsed")

def init_directories(path):
    # Create a results dir if it doesn't exist yet
    if not os.path.exists(path):
        makedirs(path)


def getTimestamp(pkt, t0):
    return float(pkt.time - t0)


def getDirection(pkt):
    if pkt.payload.src in My_Source_Ips:
        return 1
    else:
        return -1 

def parse_arguments():

    parser = argparse.ArgumentParser(description='Parse captured traffic.')

    parser.add_argument('dir',
                        type=str,
                        metavar='<dataset path>',
                        help='Path of dataset.')
    parser.add_argument('-mode',
                        type=str,
                        metavar='<parse mode>',
                        help='The type of dataset: clean, burst?.')
    parser.add_argument('-m',
                        action='store_true', 
                        default=False,
                        help='The type of dataset: is mon or unmon?.')
    parser.add_argument('-s',
                        action='store_true', 
                        default=False,
                        help='If use screenshot as sanity check?')
    parser.add_argument('-suffix',
                        type=str,
                        metavar='<parsed file suffix>',
                        default='.cell',
                        help='to save file as xx.suffix')

    # Parse arguments
    args = parser.parse_args()
    return args



def clean_parse(fdir):
    global savedir, suffix, ismon
    if ismon:
        site,inst = fdir.split("/")[-1].split(".pcap")[0].split("-")
        savefiledir = join(savedir, site+"-"+inst+suffix) 
    else:
        site = fdir.split("/")[-1].split(".pcap")[0]
        savefiledir = join(savedir, site+suffix)
    packets = rdpcap(fdir)
    if len(packets) < 50:
        print("[WARN] {} has too few packets, skip!".format(fdir))
        return
    try:
        with open(savefiledir, 'w') as f:
            start = 0
            t0 = packets[0].time
            # for i, pkt in enumerate(packets):
            #     #skip the first few noise packets
            #     if getDirection(pkt)>0 :
            #         start = i
            #         t0 = pkt.time
            #         print("Start from pkt no. {}".format(start))
            #         break

            for i, pkt in enumerate(packets[start:]):
                b = raw(pkt.payload.payload.payload)
                byte_ind = b.find(b'\x17\x03\x03')
                while byte_ind != -1 and byte_ind < len(b):
                    if b[byte_ind:byte_ind + 3] == b'\x17\x03\x03':
                        TLS_LEN = int.from_bytes(b[byte_ind+3:byte_ind+5], 'big')
                        cur_time = getTimestamp(pkt,t0)
                        cur_dir = getDirection(pkt)
                        #complete TLS record
                        cell_num = TLS_LEN /CELL_SIZE
                        cell_num = int(np.round(cell_num))
                     
                        for i in range(cell_num):
                            f.write("{:.6f}\t{:d}\n".format(cur_time, cur_dir))
                        byte_ind += TLS_LEN + 5
                    else:
                        #What happened here?
                        break
    except Exception as e:
        print("Error in {}, {} ".format(fdir.split('/')[-1], e))


def fast_burst_parse(fdir):
    global savedir, suffix, ismon
    if ismon:
        site,inst = fdir.split("/")[-1].split(".pcap")[0].split("-")
        savefiledir = join(savedir, site+"-"+inst+suffix) 
    else:
        site = fdir.split("/")[-1].split(".pcap")[0]
        savefiledir = join(savedir, site+suffix)

    try:
        # #remove acks and retransmissions
        # cmd = 'tshark -r '+ fdir+ ' -Y "not(tcp.analysis.retransmission or tcp.len == 0 )" -w '+ fdir
        # subprocess.call(cmd, shell=True)
        packets = rdpcap(fdir)
        if len(packets) < 50:
            print("[WARN] {} has too few packets, skip!".format(fdir))
            return
        # print(savefiledir)
        start = 0
        t0 = packets[0].time
        # for i, pkt in enumerate(packets):
        #     #skip the first few noise packets
        #     if  getDirection(pkt)>0:
        #         start = i
        #         t0 = pkt.time
        #         # print("Start from pkt no. {}".format(start))
        #         break

        

        in_pkts_raw = []
        in_pkts = []
        out_pkts = []
        for i,pkt in enumerate(packets[start:]):
            payload = pkt.load
            dire = getDirection(pkt)
            t = getTimestamp(pkt, t0)
            if dire == 1:
                #outgoing packet, only one case: 612 bytes (546 payload)
                if len(payload) == MY_CELL_SIZE:
                    if payload[0] == 0:
                        out_pkts.append([t, isReal])
                    elif payload[0] == 1 or payload[0] == 2:
                        out_pkts.append([t, isDummy])
                    else:
                        raise ValueError("FORMAT ERROR: {},{} pkt ,payload:{}".format(fdir, start+i,payload))
                else:
                    # rarely happen, several outgoing together, probably congestion?
                    for b in range(0, len(payload), MY_CELL_SIZE):
                        pkttype = isDummy if payload[b] else isReal
                        out_pkts.append([t, pkttype])   
                    # print("[WARN] Several outgoing: {},{} pkt ,len of payload:{}".format(fdir,start+i, len(payload)))
            else:
                #incoming ones are more complicated, first collect raw packets
                in_pkts_raw.append([t, payload])

        if len(out_pkts) < 2 or len(in_pkts_raw) < 5:
            #I just pick two random number here. 
            #If too few packets there, return
            print("[WARN] {} has too few packets: {}+{}, skip!".format(fdir,len(out_pkts),len(in_pkts_raw)))
            return

        #process incoming ones 
        ind = 0
        while ind < len(in_pkts_raw):
            base_pkt = in_pkts_raw[ind]
            base_time = base_pkt[0]
            base_payload = base_pkt[1]
            while ind < len(in_pkts_raw)-1 and len(base_payload) % MY_CELL_SIZE != 0:
                #fragment
                ind += 1
                tmp_pkt = in_pkts_raw[ind]
                base_payload += tmp_pkt[1]

            for b in range(0, len(base_payload), MY_CELL_SIZE):
                pkttype = isDummy if base_payload[b] else isReal
                in_pkts.append([base_time, pkttype * (-1)])         
            ind += 1

        #sort packets
        total_pkts_unsorted = np.array(in_pkts + out_pkts)
        total_pkts0 = total_pkts_unsorted[total_pkts_unsorted[:,0].argsort(kind = "mergesort")]

        #Cut off last few packets (1s away from their predecessor)
        total_pkts1 = total_pkts0[1:]
        time_diffs = total_pkts1[:,0] - total_pkts0[:-1,0]
        tmp = np.where(time_diffs > 1)[0]
        if len(tmp) == 0:
            cut_off_ind = len(total_pkts0)
        else:
            cut_off_ind = tmp[-1]
            # print("{}: cut off at {}/{}".format(fdir, cut_off_ind,len(total_pkts0)))

        with open(savefiledir, 'w') as f:
            for pkt in total_pkts0[:cut_off_ind]:
                f.write("{:.6f}\t{:.0f}\n".format(pkt[0],pkt[1]))   
    except Exception as e:
        print("Error in {}, {} ".format(fdir.split('/')[-1], e))

if __name__ == "__main__":
    global savedir, suffix, ismon
    args = parse_arguments()
    suffix = args.suffix
    ismon = args.m
    # filelist = glob.glob(join(args.dir,'*_*_*' ,'capture.pcap.filtered'))
    if args.s:
        filelist_ = glob.glob(join(args.dir,'*.png'))
        filelist = []
        #Sanity check
        for f in filelist_:
            pcapfile = f.split(".png")[0] + captured_file_name
            if os.path.exists(pcapfile):
                filelist.append(pcapfile)
    else:
        filelist =  glob.glob(join(args.dir,'*'+captured_file_name))         

    filename = args.dir.rstrip("/").split("/")[-1]
    savedir = join(ParsedDir, filename)
    init_directories(savedir)
    print("Parsed file in {}".format(savedir))
    # for f in filelist:
    #   parse(f)
    print("Totol:{}".format(len(filelist)))

    pool = mp.Pool(processes=2)
    if args.mode == 'clean':
        # pool.map(clean_parse, filelist)
        pool.map(clean_parse, filelist)
    elif args.mode == 'burst':
        pool.map(fast_burst_parse, filelist)
    else:
        raise ValueError('Wrong mode:{}'.format(args.mode))

    # zipcmd = "zip -rq " + savedir.rstrip("/") + ".zip" + " " + savedir
    # print(zipcmd)
    # subprocess.call(zipcmd, shell=True)

