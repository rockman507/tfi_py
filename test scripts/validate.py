from scipy.misc import toimage
import numpy as np
import os
import time

path = r'C:\etafilcon20130523\run1\text'
file = os.path.join(path,r'text_00001.txt')

file_in = open(file, 'r')
aa = file_in.read().rstrip()
aa = aa.split('\n')
file_in.close()

a1 = []

for t in aa:
    a1.append(t.split(' '))

columns = len(a1[0])
rows = len(a1)

t1 = np.empty([rows,columns])

for row in range(rows):
    for column in range(columns):
        t1[row][column] = float(a1[row][column])

t1[t1 > 5000]=0

