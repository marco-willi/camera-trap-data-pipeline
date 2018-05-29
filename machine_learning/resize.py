#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import matplotlib.image as mpimg
import scipy.misc
import numpy as np
import os
import glob
from multiprocessing import Process
import multiprocessing

src_dir= "/home/packerc/shared/albums/SER/"
dst_dir= "/home/packerc/shared/machine_learning/data/images/SER/"

def divide(t,n,i):
    length=t/(n+0.0)
    #print length,(i-1)*length,i*length
    return int(round((i-1)*length)),int(round(i*length))

def do_chunk(pid,filelist, lock):
    #print(filelist)
    for co,row in enumerate(filelist):
      try:
        if co%500==0:
          print("Process "+str(pid),co)
          sys.stdout.flush()
        img=mpimg.imread(src_dir+row)
        img=scipy.misc.imresize(img[0:-100,:],(256,256))
        path=dst_dir+str(row[:row.rfind('/')])
        lock.acquire()
        if not os.path.exists(path):
          os.makedirs(path)
        lock.release()
        mpimg.imsave(dst_dir+row,img)
      except:
        print 'Severe Error for'+row
        #raise
    print("Process "+str(pid)+"  is done")

if __name__ == '__main__':
    try:
      allfiles=[]
      """for path, subdirs, files in os.walk(src_dir):
        for f in files:
          if f.endswith(".JPG") or f.endswith(".jpg"):
            allfiles.append(os.path.join(path,f))
            if len(allfiles)%10000==0:
              print(len(allfiles))"""
      with open("/panfs/roc/groups/5/packerc/shared/machine_learning/anorouzz/season7.csv") as f:
        for line in f.readlines():
          fields= line.split(",")
          allfiles.append(fields[0])

      total_records=len(allfiles)
      print(total_records)
      total_processors= 24
      lock = multiprocessing.Lock()
      #print(total_records)
      for i in range(1,total_processors+1):
        st,ln=divide(total_records,total_processors,i)
        p1 = Process(target=do_chunk, args=(i,allfiles[st:ln],lock))
        p1.start()
    except:
      raise
