import numpy as np
import numpy.ma as ma
from scipy.misc import toimage
import time


rad = 200

# Create radial grid
r0 = rad
r1 = rad
center = (r0/2.0, r1/2.0)

r0v = np.linspace(0-center[0], r0-center[0], r0).astype(np.float).reshape(-1,1)
r1v = np.linspace(0-center[1], r1-center[1], r1).astype(np.float).reshape(1,-1)

grid_rad = (r0v**2. + r1v**2.)**0.5
grid_mask = grid_rad > grid_rad[0].min()

# Create angular grid
rvec = ((np.arange(2*rad)-rad)/rad)
r0 = rvec.reshape(-1,1)
r1 = rvec.reshape(1,-1)
grid_ang = np.arctan2(r0, r1)

# Masked numpy arrays?
masked_rad = ma.array(grid_rad,mask=grid_mask)
masked_rad = masked_rad.filled(0)

# Make zernike indices
order = 30
zz = time.clock()
nm_truple = []
n = np.arange(0,order+1)
j=1
for ni in n:
    m = np.arange(ni%2,ni+1, step=2)
    for mi in  m:
        if mi == 0:
            nm_truple.append((ni,mi))
            j+=1
        else:
            nm_truple.append((ni,(-1)**j*mi))
            j+=1
            nm_truple.append((ni,(-1)**j*mi))
            j+=1
print(str(time.clock()-zz))
#print(nm_truple)


zz = time.clock()
nm_truple1 = []
ii = (order+1)*(order+2)/2
for j in range(1,int(ii+1)):
    n = 0
    j1 = j-1
    while (j1 > n):
        n += 1
        j1 -= n
    m = (-1)**j * ((n % 2) + 2 * int((j1+((n+1)%2)) / 2.0 ))
    nm_truple1.append((n,m))
print(str(time.clock()-zz))

#print(nm_truple1)
#print(len(nm_truple))
for i in range(int(ii)):
    if ~(nm_truple[i][0] == nm_truple1[i][0]) or ~(nm_truple[i][1] == nm_truple1[i][1]):
        print('BAD {} : {}'.format(nm_truple[i],nm_truple1[i]))
