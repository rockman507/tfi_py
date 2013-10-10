import numpy as np
from scipy.misc import toimage
import array, sys

def calc_phase (data):

    # Setup 9-pixels
    I1 = data[:-2,:-2] 
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
    modulation = np.sqrt((2*(I2+I8-I4-I6))**2+(4*I5-I1-I3-I7-I9)**2)/(2*intensity+.0001)
    modulation[modulation>1]=0
    #quality = np.array(modulation > 0.0, 'b')
    
    num = 2*(I2+I8-I4-I6)+.0001 #addition to avoid division by zero
    den = 4*I5-I1-I3-I7-I9+.0001 #addition to avoid division by zero

    # Create two masks when atan and acot need to be applied
    a = np.zeros(modulation.shape, 'b')
    a[::2,::2]=1
    a[1::2,1::2]=1
    a_mask = np.array(a,'bool')
    b = np.array(-a+1)
    a = a*np.arctan(num/den)
    b = b*np.arctan(den/num) #acot
    phase = np.array((a+b),'f')

    # Fix me some phase offsets
    phase[(~a_mask) & (phase<0) & (num>0)] += np.pi
    phase[(a_mask) & (phase<0) & (den>0)] += np.pi
    phase[(phase>0) & (phase<np.pi/2) & (num>0)] -= np.pi
    phase[:,::2] += np.pi
    phase[phase>=np.pi] -= 2*np.pi

    # Map phase [-2pi:2pi] -> [0,255] 
    phase = (phase/(2*np.pi)+0.5)*255
    phase = np.array(phase,'B')

    return phase, modulation, intensity
"""
if __name__ == '__main__':

    # data.bin is a test 500x500 float array
    print 'Opening data.bin'
    try:
        f = open(r'test_data\data.bin','rb')
        data = array.array('f')
        data.fromfile(f,250000)
        f.close()
        data = np.array(data)
        data.resize(500,500)
        try:
            sys.stdout.write('Trying calc_phase(data) ')
            phase, modulation, intensity = calc_phase(data)
            print 'passed'
            try:
                sys.stdout.write('Trying to display phase ')
                toimage(phase).show()
                print 'passed'
            except:
                print 'failed'
        except:
            print 'failed'
    except:
        print 'file read error'
"""
    
