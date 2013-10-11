from scipy.misc import toimage
import numpy as np
import os
import time
from h5py import File
from tfi_py.mask import get_mask
from tfi_py.calc_phase import calc_phase


# Open txt file of wrapped phase surface data from 4Sight
path = r'C:\etafilcon20130523\run1'
file = os.path.join(path,r'wrapped_4sight.txt')
file_in = open(file, 'r')

# Ignore header information
for i in range(12):
    file_in.readline()

# Read file stripping EOF '\n' and then split into lines
aa = file_in.read().rstrip()
aa = aa.split('\n')
file_in.close()

# Split each line into numbers removing EOL ','
a1 = []
for t in aa:
    t = t.rstrip(',')
    a1.append(t.split(','))

# Create empty array of size rows x columns
columns = len(a1[0])
rows = len(a1)
t1 = np.empty([rows,columns])

# Assign array, converting each 25 digit number to a proper float
for row in range(rows):
    for column in range(columns):
        try:
            t1[row][column] = float(a1[row][column])
        except:
            t1[row][column] = 0.0

# Get mask
file_ = r'C:\etafilcon20130523\run1\meas_00001.h5'
border = 2
mask, coord = get_mask(file_, border=2)
mask = mask[coord[0]:coord[1], coord[2]:coord[3]]

# Get wrapped phase via python algorithm
f = File(file_, 'r')
sub = f.get(r'measurement0/frames/frame_full/data')
data = np.array(sub[coord[0]-1:coord[1]+1,coord[2]-1:coord[3]+1],'f')
f.close()
phase, modulation, intensity = calc_phase(data)

# Apply mask
t2 = t1[coord[0]:coord[1],coord[2]:coord[3]]
t2[~mask] = 0
phase[~mask] = 0

# Map 4sight wrapped phase to [0,255] unsigned byte
t3 = t2 - (t2.max()+t2.min())/2
t3 = (t3 / ((t3.max() - t3.min())) +0.5)*255
t3[~mask] = 0
phase_4sight = np.array(t3,'B')

min_shift = 0
diff = phase-phase_4sight
min_rms = np.sqrt(np.mean(diff[mask]**2))
phase_temp = np.array(phase,'B')

min_rms=100

for i in range(500):
    phase_temp += 1
    diff = np.array(phase_temp,'f')-np.array(phase_4sight,'f')
    rms = np.sqrt(np.mean(diff[mask]**2))
    if rms < min_rms:
        print('{}, {}'.format(i,rms))
        min_rms = rms


#np.sqrt(np.mean(phase[mask]**2))
