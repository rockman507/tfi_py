# phase_unwrap_multi.py
# Jason Saredy
# Selects a directory with wrapped wavefront data and unwraps it using a
#   user selected c algorithm written by D. Ghiglia and M. Pritt

import numpy as np
import time
import os, re
import subprocess
from scipy.misc import toimage
#from easygui import diropenbox, fileopenbox, choicebox
import win32api
from wrapped_phase import get_path
import multiprocessing
from multiprocessing.pool import Pool
from PIL import Image
from pylab import cm

#os.system(r'C:\\flyn.exe -input C:\\calc2.dat -format float -output C:\\dump.dat -xsize 990 -ysize 1002 -bmask C:\\mask1.dat')
#os.system(r'C:\\flyn.exe -input C:\\wrapped.dat -format float -output C:\\dump2.dat -xsize 990 -ysize 1002 -bmask C:\\mask1.dat')



def unwrap_setup (path):
    
    path_size = os.path.join(path,r'size.dat')
    [row_size,col_size] = np.fromfile(path_size, dtype='int')

    f1 = os.path.join(path,r'debug.csv')
    f1 = open(f1,'r')
    data = f1.read()
    data = data.split('\n')
    f1.close()
    
    return row_size, col_size, data


def unwrap(args):
    
    filename = args[0]
    path = args[1]
    path_raw = args[2]
    path_images = args[3]
    algorithm_exe = args[4]
    row_size = args[5]
    col_size = args[6]
    win_show = args[7]

    # Setup output filenames
    mask_file = os.path.join(path,'mask.dat')
    wrapped_file = os.path.join(path_raw,filename)
    unwrapped_file = os.path.join(path_raw,'un'+filename)
    image_file = os.path.join(path_images,'surface_'+filename[8:13]+'.bmp')
    image_file_tiff = os.path.join(path_images,'surface_'+filename[8:13]+'.tiff')
    #qual_file = os.path.join(path_raw,'qual_'+filename[8:13]+'.dat')
    arg = ''
    #arg += r' -corr '+qual_file+r' -mode max_coor'
    #arg += r' -thresh yes'
    
    z = time.clock() # Start timer
    print(algorithm_exe)
    print(wrapped_file)
    # Open process call to c algorithm, uncomment su definitions to make process window hidden
    P = subprocess.Popen(r'"%s" -input %s -format byte -output %s -xsize %s -ysize %s -bmask %s %s' \
              % (algorithm_exe, wrapped_file, unwrapped_file, col_size, row_size, mask_file, arg), shell=not win_show)
    #P = subprocess.check_output([algorithm_exe, r" -input ", wrapped_file, r" -format byte -output ", unwrapped_file, r" -xsize ", str(ysize), r" -ysize ", str(xsize), r" -bmask ", mask_file, arg])
    #print(algorithm_exe, " -input ", wrapped_file, " -format byte -output ", unwrapped_file, " -xsize ", ysize, " -ysize ", xsize, " -bmask ", mask_file, arg)
    P.wait() # Wait until process completes before opening new process

    # Opens new surface file applying mask
    f2 = open(unwrapped_file, 'rb')
    fm = open(mask_file, 'rb')
    arr = np.fromfile(f2, dtype='f')
    mask = np.fromfile(fm, dtype='b')
    f2.close()
    fm.close()
    arr = arr*mask/(2*np.pi)
    rms = np.sqrt(np.mean(arr[mask==1]**2))
    arr.tofile(unwrapped_file,format='%f')
    arr.resize(int(row_size),int(col_size))
    mask.resize(int(row_size),int(col_size))

    # Saves surface image
    toimage(arr).save(image_file)
    tmparr = arr[mask==1]
    range1 = tmparr.max() - tmparr.min()
    arr -= tmparr.min()
    arr *= 1/range1
    arr *= 0.8
    arr += 0.1
    arr[mask==0]=0
    im = Image.fromarray(cm.spectral(arr,bytes=True))
    #im.show()

    im.save(image_file_tiff)
    
    return (','+str(rms))


if __name__ == '__main__':
    # Get path
    #path = diropenbox('Pick directory to process',default=r'd:\phase')
    path = r'C:\Users\jsaredy\Desktop\4 1_20130710'
    path = win32api.GetShortPathName(path)
    
    path_raw, path_images, filenames = get_path(path, filetype = 'wrapped')
    #algorithm_exe = fileopenbox('Pick algorithm exe to use',default=r'd:\phase')
    algorithm_exe = r'C:\phase\lpno_o2.exe'
    '''
    # Check if qual or mcut, both require mode to be choosen
    arg =''
    algorithm_exe = fileopenbox('Pick algorithm exe to use',default=r'd:\phase')
    if re.search('mcut',algorithm_exe) or re.search('qual',algorithm_exe):
        mode = choicebox('mcut and qual need a mode, choose mode below','Choose mode',\
                         ['min_grad','min_var','max_corr', 'max_pseu'])
        arg = ' -mode '+mode
    '''

    # Setup dimensions of array from %path%/debug.csv in col x row format
    row_size, col_size, data = unwrap_setup(path)

    # Setup mask
    mask_file = os.path.join(path,'mask.dat')
    if not os.path.exists(mask_file):
        mask_file = 'none'
    alg = re.split(r'\\',algorithm_exe)[-1]
    #i = 4
    i = 1
    data[3]+= ','+alg+' rms,'+alg+' time'

    A = []
    pool = Pool(processes=8)
    for filename in filenames:
        A.append((filename, path, path_raw, path_images, algorithm_exe, row_size, col_size, False))

    imap1 = pool.imap(unwrap,A)
    for i in imap1:
        print(i)
    pool.close()


    #time.sleep(10)
        
    f1 = os.path.join(path,r'debug.csv')
    f1 = open(f1,'w')
    for a in data:
        f1.write(a+'\n')
    f1.close()
