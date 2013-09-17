import numpy as np
from os.path import join
from os import listdir
from time import clock
from zern1 import fit_zernike
from scipy.misc import toimage
#cimport numpy as np
#import ctypes



#def get_zernike (filename, path, path_raw, path_images, temp, mask, size, modes):
def get_zernike (args):

    filename = args[0]
    path = args[1]
    path_raw = args[2]
    path_images = args[3]
    mask = args[4]
    size = args[5]
    modes = args[6]
    
    # Setup output filenames

    zz = clock()
    unwrapped_file = join(path_raw,filename)
    zernike_file = join(path_raw,'zernike_'+filename[10:15]+'.dat')
    image_file = join(path_images,'zernike_'+filename[10:15]+'.bmp')
    diff_image_file = join(path_images,'zernike_diff_'+filename[10:15]+'.bmp')
    

    # Get array
    if modes == 0:
        modes = 15
    unwrapped_file1 = open(unwrapped_file, 'rb')
    arr = np.fromfile(unwrapped_file, dtype='f')
    arr.resize(size)

    mask = ~mask

    # Calc zernike fit and apply mask
    err = []
    fitvec, fitrec, fitdiff = fit_zernike(arr, nmodes=modes, err=err)


    fitdiff = np.array(fitdiff, dtype='f')
    fitdiff[mask] = 0
    fitrec = np.array(fitrec, dtype='f')
    fitrec[mask] = 0

    fitdiff.tofile(zernike_file)
    toimage(fitrec).save(image_file)
    toimage(fitdiff).save(diff_image_file)

    try:
        piston = fitvec[0]
    except:
        piston = 0
    try:
        tilt = np.sqrt(fitvec[1]**2+fitvec[2]**2)
    except:
        tilt = 0
    try:
        astig = np.sqrt(fitvec[4]**2+fitvec[5]**2)
    except:
        astig = 0
    try:
        power = fitvec[3]
    except:
        power = 0
    try:
        sphere = fitvec[10]
    except:
        sphere = 0
    

    #print filename
    #temp+=str(piston)+','+str(tilt)+','+str(astig)+','+str(power)+','+str(sphere)+','+str(err[0])+','+str(err[1])+','+str(err[2])+'\n'
    #print err[0]
    #print str(clock()-zz)+' '+filename

    #return temp
    #print('{},{},{},{},{},{},{},{}'.format(piston, tilt, astig, power, sphere, err[0], err[1], err[2]))
    return '%f,%f,%f,%f,%f,%f,%f,%f\n' % (piston, tilt, astig, power, sphere, err[0], err[1], err[2])



'''
if __name__ == '__main__':
    # Get path
    tmpz = clock()
    #path = diropenbox('Pick directory to process',default=r'd:\phase')
    #path = win32api.GetShortPathName(path)
    #print path
    path = r'C:\DOCUME~1\jsaredy\Desktop\41_201~1'
    path_raw = join(path,r'raw')
    path_images = join(path,r'images')

    # Get mask and array size
    mask_path = join(path, r'mask.dat')
    mask_file = open(mask_path, 'rb')
    mask = np.fromfile(mask_file, dtype='bool')
    tmp = np.sqrt(mask.shape)[0]
    arr_size = tmp,tmp
    mask.resize(arr_size)
    #toimage(mask).show()

    # Get unwrapped arrays
    raw_filenames = listdir(path_raw)
    for raw_filename in raw_filenames[:]:
        if 'unwrapped_.dat' != raw_filename[:10]+raw_filename[15:]:
            raw_filenames.remove(raw_filename)
    temp = 'piston, tilt, astrig, power, sphere\n'           
    print(str(clock()-tmpz))
    for filename in raw_filenames:
        temp = get_zernike(filename, path, path_raw, path_images, temp, mask, arr_size, 15)
        break

    print(temp)
'''


