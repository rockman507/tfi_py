# system libraries
from scipy.misc import toimage
from easygui import diropenbox
from h5py import File
import numpy as np
import time, os, sys
from multiprocessing import Pool
#from Tkinter import *

# TFI
from calc_phase import calc_phase
from mask import get_mask
from wrapped_phase import get_phase, get_path



if __name__ == '__main__':
    
    #path = diropenbox('Pick directory to process',default=r'c:\phase')
    path = r'C:\Users\jsaredy\Desktop\4 1_20130710'
    path = r'C:\Users\jsaredy\Desktop\run3'
    path_raw, path_images, filenames = get_path(path, 'h5')
    first_file = os.path.join(path,filenames[0])
    mask,coord = get_mask(first_file, border=2)
    mask = mask[coord[0]:coord[1],coord[2]:coord[3]]

    #coord [0] = x_min, [1] = x_max, [2] = y_min, [3] = y_max
    deb = ''
    #for filename in filenames:
    #    deb = get_phase(filename, path, path_raw, path_images, mask, coord, deb)
    pool = Pool()
    A=[]
    for filename in filenames:
        A.append((filename, path, path_raw, path_images, mask, coord))
    zz = time.clock()
    imap1 = pool.imap(get_phase,A)
    #imap1 = map(get_phase,A)
    pool.close()
    pool.join()
    print str(time.clock()-zz)
    for x in imap1:
        deb+=x
    print str(time.clock()-zz)
    #print deb
    #print deb

    '''
    # Save mask
    mask = mask[x_min:x_max,y_min:y_max]
    mask.tofile(path+r'\mask.dat')

    #np.savetxt(r'mask_deb.csv', mask, delimiter=',', fmt='%d')
    #np.savetxt(r'phase_deb.csv', phase, delimiter=',', fmt='%d')

    f_debug = os.path.join(path,'debug.csv')
    try:
        f_debug = open(f_debug,'w')
        f_debug.write(deb)
        f_debug.close()
        print 'done'
    except:
        print 'Bad write to :'+f_debug
        print 'Dumping to %path%\debug.csv \n'
        print deb
        f_debug = open(r'debug.csv','w')
        f_debug.write(deb)
        f_debug.close()
        print 'done'
    '''


