# system libraries
#from scipy.misc import toimage
#from easygui import diropenbox
from PIL import Image
from h5py import File
import numpy as np
import time, os, sys
from multiprocessing import Pool
#from Tkinter import *
import libtim
#from libtim.zern import fit_zernike

# TFI
from tfi_py.calc_phase import calc_phase
from tfi_py.mask import get_mask


def get_path(path):
    path_raw = os.path.join(path,r'raw')
    if not os.path.isdir(path_raw):
        try:
            os.mkdir(path_raw)
            print('Creating path \"'+path_raw+'\"')
        except:
            print('Failed creating path \"'+path_raw+'\"')
    
    imagep = r'images\wrapped'
    raw_filenames = os.listdir(path)
    for raw_filename in raw_filenames[:]:
        if 'meas_.h5' != raw_filename[:5]+raw_filename[10:]:
            raw_filenames.remove(raw_filename)

    path_images = os.path.join(path,imagep)
    if not os.path.isdir(path_images):
        try:
            os.makedirs(path_images)
            print('Creating path \"'+path_images+'\"')
        except:
            print('Failed creating path \"'+path_images+'\"')

    #print(raw_filenames)

    return path_raw, path_images, raw_filenames


def get_phase(args):
    
    filename = args[0]
    path = args[1]
    path_raw = args[2]
    path_images = args[3]
    mask = args[4]
    coord = args[5]

    file_in = os.path.join(path,filename)
    file_raw = os.path.join(path_raw,'raw_'+filename)
    image_phase = os.path.join(path_images,'wrapped'+filename[4:11]+'bmp')
    binary_phase = os.path.join(path_raw,'wrapped'+filename[4:11]+'dat')
    mod_arr = os.path.join(path_raw,'mod'+filename[4:11]+'dat')
    mod_image = os.path.join(path_images,'mod'+filename[4:11]+'bmp')
    qual_arr = os.path.join(path_raw,'qual'+filename[4:11]+'dat')
    qual_image = os.path.join(path_images,'qual'+filename[4:11]+'bmp')
    # Open meas file and grab dataset
    try:
        f = File(file_in, 'r')
    except:
        print('Corrupt h5 file: '+filename+' ignoring')
        return
    sub = f.get(r'measurement0/frames/frame_full/data')
    data = np.array(sub[coord[0]-1:coord[1]+1,coord[2]-1:coord[3]+1],'f')
    f.close()

    # Get phase
    phase, modulation, intensity = calc_phase(data)
    # Apply mask
    phase[~mask] = 0
    intensity[~mask] = 0
    modulation[~mask] = 0
    #phase = phase[coord[0]:coord[1],coord[2]:coord[3]]
    
    # Save phase
    phasei = Image.fromarray(phase)
    phasei.save(image_phase)
    phase.tofile(binary_phase)


    ave_mod = np.average(modulation[mask])
    ave_int = np.average(intensity[mask])
    '''
    if ave_mod < 0.6:
        print filename+' low mod:', ave_mod
    else:
        sys.stdout.write('.')
    '''
    return "%s,%f,%f\n" % (filename, ave_int, ave_mod)


def start(arg):
    path = r'C:\Users\jsaredy\Desktop\4 1_20130710'
    path_raw, path_images, filenames = get_path(path)
    first_file = os.path.join(path,filenames[0])
    mask,coord = get_mask(first_file, border=2)

    mask = mask[coord[0]:coord[1],coord[2]:coord[3]]
    #coord [0] = x_min, [1] = x_max, [2] = y_min, [3] = y_max

    A = []
    for filename in filenames:
        A.append((filename, path, path_raw, path_images, mask, coord))

    n_processes = int(arg)

    if n_processes == 0:
        imap1 = map(get_phase,A)
    else:
        pool = Pool(processes=n_processes)
        imap1 = pool.imap(get_phase,A)
        pool.close()
        pool.join()

    summary = ''
    for x in imap1:
        summary += x

    #print(summary)

if __name__ == '__main__':
    zz = time.clock()
    start(8)
    print(str(time.clock()-zz))
