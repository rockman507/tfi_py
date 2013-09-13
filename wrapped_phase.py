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




def get_path(path, filetype):
    path_raw = os.path.join(path,r'raw')
    if not os.path.isdir(path_raw):
        try:
            os.mkdir(path_raw)
            print 'Creating path \"'+path_raw+'\"'
        except:
            print 'Failed creating path \"'+path_raw+'\"'
    '''
    path_images = os.path.join(path,r'images\wrapped')
    if not os.path.isdir(path_images):
        try:
            os.makedirs(path_images)
            print 'Creating path \"'+path_images+'\"'
        except:
            print 'Failed creating path \"'+path_images+'\"'
    '''

    

    if filetype == 'h5':
        imagep = r'images\wrapped'
        raw_filenames = os.listdir(path)
        for raw_filename in raw_filenames[:]:
            if 'meas_.h5' <> raw_filename[:5]+raw_filename[10:]:
                raw_filenames.remove(raw_filename)

    if filetype == 'wrapped':
        imagep = r'images\surface'
        raw_filenames = os.listdir(path_raw)
        for raw_filename in raw_filenames[:]:
            if 'wrapped_.dat' <> raw_filename[:8]+raw_filename[13:]:
                raw_filenames.remove(raw_filename)

    if filetype == 'unwrapped':
        imagep = r'images\zernike'
        raw_filenames = os.listdir(path_raw)
        for raw_filename in raw_filenames[:]:
            if 'unwrapped_.dat' <> raw_filename[:10]+raw_filename[15:]:
                raw_filenames.remove(raw_filename)

    path_images = os.path.join(path,imagep)
    if not os.path.isdir(path_images):
        try:
            os.makedirs(path_images)
            print 'Creating path \"'+path_images+'\"'
        except:
            print 'Failed creating path \"'+path_images+'\"'

    print raw_filenames

    return path_raw, path_images, raw_filenames

#@profile
#def get_phase(filename, path, path_raw, path_images, mask, coord, deb):
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
        print 'Corrupt h5 file: '+filename+' ignoring'
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
    toimage(phase).save(image_phase)
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

    



if __name__ == '__main__':
    
    #path = diropenbox('Pick directory to process',default=r'c:\phase')
    path = r'C:\Users\jsaredy\Desktop\4 1_20130710'
    #path = r'C:\Users\jsaredy\Desktop\run3'
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

    for ii in xrange(1,14):
        zz = time.clock()
        for jj in xrange(10):
            pool = Pool(processes=ii)
            A=[]
            for filename in filenames:
                A.append((filename, path, path_raw, path_images, mask, coord))
            imap1 = pool.map(get_phase,A)
            #imap1 = map(get_phase,A)
            pool.close()
            
            for x in imap1:
                #t.set(str(i)+'/'+maxf)
                #win.update()
                #i+=1
                deb+= x
                #print x
        zz = time.clock()-zz
        print ('Process=%d, time=%f')%(ii,zz/10)


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


