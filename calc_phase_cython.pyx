from numpy import pi, array, sqrt, arctan, ones
import numpy as np
cimport numpy as np

def calc_phase_cython (data):

    #cdef np.ndarray[np.float, ndim=2] data1 = data
    
    
    # Setup 9-pixels
    #cdef np.ndarray[np.float, ndim=2] I1 = data[0:497,0:497]
    I1 = data[0:-2,0:-2]
    I2 = data[:-2,1:-1] 
    I3 = data[:-2,2:] 
    I4 = data[1:-1,:-2] 
    I5 = data[1:-1,1:-1] 
    I6 = data[1:-1,2:] 
    I7 = data[2:,:-2] 
    I8 = data[2:,1:-1] 
    I9 = data[2:,2:]

    # Intensity and modulation stolen from Jason by Jason
    intensity = I5 + 0.5*(I2+I4+I6+I8) + 0.25*(I1+I3+I5+I7+I9)
    
    #quality = np.array(modulation > 0.0, 'b')
    
    num = 2*(I2+I8-I4-I6)+.0001 #addition to avoid division by zero
    den = 4*I5-I1-I3-I7-I9+.0001 #addition to avoid division by zero

    modulation = sqrt(num**2+den**2)/(2*intensity+.0001)
    modulation[modulation>1]=0

    # Create two masks when atan and acot need to be applied  
    a_mask = ones(modulation.shape, 'bool')
    a_mask[::2,::2]=False
    a_mask[1::2,1::2]=False
    tmp1 = num/den
    tmp1[a_mask] = 1/tmp1[a_mask]
    phase = arctan(tmp1)

    # Fix me some phase offsets
    phase[(a_mask) & (phase<0) & (num>0)] += pi
    phase[(~a_mask) & (phase<0) & (den>0)] += pi
    phase[(phase>0) & (phase<pi/2) & (num>0)] -= pi
    phase[:,::2] += pi
    phase[phase>=pi] -= 2*pi

    # Map phase [-2pi:2pi] -> [0,255]
    cdef float t2 = 255/(2*pi)
    phase+=pi
    phase*=t2
    phase = array(phase,'B')

    return phase, modulation, intensity
