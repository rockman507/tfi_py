import numpy as np
cimport numpy as np
cimport cython
from libc.math cimport sqrt, fmod, atan, M_PI, M_PI_2

ctypedef np.uint8_t DTYPE_t

@cython.boundscheck(False)
@cython.wraparound(False)
@cython.cdivision(True)
def calc_phase (np.ndarray[np.float32_t, ndim=2] data):
    
    cdef int xlen , ylen
    cdef unsigned int i, j
    cdef float t2 = 255/(2*M_PI)
    
    ylen = data.shape[0]-2
    xlen = data.shape[1]-2
    
    cdef np.ndarray[np.float_t, ndim=2] intensity = np.empty((ylen,xlen))
    cdef np.ndarray[np.float_t, ndim=2] modulation = np.empty((ylen,xlen))
    cdef np.ndarray[np.float_t, ndim=2] num = np.empty((ylen,xlen))
    cdef np.ndarray[np.float_t, ndim=2] den = np.empty((ylen,xlen))
    cdef np.ndarray[np.float_t, ndim=2] phase1 = np.empty((ylen,xlen))
    cdef np.ndarray[np.uint8_t, ndim=2] phase = np.empty((ylen,xlen), np.uint8)

    for i in xrange(ylen):
        for j in xrange(xlen):
            intensity[i,j] = (data[i+1,j+1] + 0.5*(data[i,j+1]+data[i+1,j]+data[i+1,j+2]+data[i+2,j+1])+0.25*(data[i,j]\
                +data[i,j+2]+data[i+1,j+1]+data[i+2,j]+data[i+2,j+2]))
            num[i,j] = (2*(data[i,j+1]-data[i+1,j]-data[i+1,j+2]+data[i+2,j+1])+1e-6)
            den[i,j] = (4*data[i+1,j+1]-data[i,j]-data[i,j+2]-data[i+2,j]-data[i+2,j+2]+1e-6)
            modulation[i,j] = (sqrt(num[i,j]*num[i,j]+den[i,j]*den[i,j])/(2*intensity[i,j]+1e-6))
            if fmod(i,2) == fmod(j,2):
                phase1[i,j] = (atan(num[i,j]/den[i,j]))
                if (phase1[i,j] < 0) and (den[i,j] > 0):
                    phase1[i,j] += M_PI
            else:
                phase1[i,j] = atan(den[i,j]/num[i,j])
                if (phase1[i,j] < 0) and (num[i,j] > 0):
                    phase1[i,j] += M_PI
            if (phase1[i,j] > 0 and phase1[i,j] < M_PI_2) and num[i,j] > 0:
                phase1[i,j] -= M_PI
            if fmod(j,2)==0:
                phase1[i,j] += M_PI
            if phase1[i,j] >= M_PI:
                phase1[i,j] -= 2*M_PI
            phase1[i,j] = ((phase1[i,j]+M_PI)*t2)
            phase[i,j] = <DTYPE_t>phase1[i,j]

    return phase, modulation, intensity